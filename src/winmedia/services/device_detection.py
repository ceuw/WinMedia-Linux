"""USB/storage device detection and safe validation (Phase 2).

IMPORTANT SAFETY RULES:
- Never identify a device as removable based solely on its /dev/sdX name.
- Never perform destructive operations (no format, no partition write, no dd).
- Reject system disks and devices hosting critical mount points.
- Revalidation must occur immediately before any future destructive operation
  (Phase 4); selection-time validation here is informational only.
"""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Mount points that indicate a disk must never be used as installation target.
CRITICAL_MOUNTPOINTS = {"/", "/boot", "/boot/efi", "/home", "/usr", "/var"}

LSBLK_COLUMNS = [
    "NAME",
    "PATH",
    "TYPE",
    "SIZE",
    "RM",
    "HOTPLUG",
    "RO",
    "TRAN",
    "VENDOR",
    "MODEL",
    "SERIAL",
    "FSTYPE",
    "FSVER",
    "LABEL",
    "UUID",
    "PTTYPE",
    "PTUUID",
    "MOUNTPOINT",
    "MOUNTPOINTS",
    "PKNAME",
]


@dataclass(frozen=True)
class SafetyFlag:
    """A safety or compatibility concern for a device."""

    level: str  # "info", "warning", "error"
    code: str
    message: str


@dataclass
class DeviceInfo:
    """Information about a top-level storage device (read-only)."""

    name: str
    path: str
    size_bytes: int
    model: str = ""
    vendor: str = ""
    serial: str = ""
    tran: str = ""
    pttype: str = ""
    ptuuid: str = ""
    is_removable: bool = False
    is_hotplug: bool = False
    is_read_only: bool = False
    mountpoints: list[str] = field(default_factory=list)
    filesystems: list[str] = field(default_factory=list)
    children: list[dict[str, Any]] = field(default_factory=list)
    flags: list[SafetyFlag] = field(default_factory=list)

    @property
    def display_name(self) -> str:
        parts = [p for p in [self.vendor.strip(), self.model.strip()] if p]
        label = " ".join(parts) if parts else self.name
        return f"{label} ({self.path})" if self.path else label

    @property
    def size_human(self) -> str:
        return format_bytes(self.size_bytes)

    @property
    def has_errors(self) -> bool:
        return any(f.level == "error" for f in self.flags)

    @property
    def has_warnings(self) -> bool:
        return any(f.level == "warning" for f in self.flags)

    def stable_id(self) -> str:
        """Return a best-effort stable identifier for UI tracking."""
        for value in (self.ptuuid, self.serial):
            if value and value.strip():
                return f"{self.path}|{value.strip()}"
        return self.path or self.name


@dataclass
class ScanResult:
    """Result of a device scan."""

    devices: list[DeviceInfo] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    scanned: bool = False


def format_bytes(size: int) -> str:
    """Format a byte count for display."""
    if size < 0:
        return "unknown"
    units = ["B", "KiB", "MiB", "GiB", "TiB"]
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{size} B"


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes"}


def _collect_mountpoints(node: dict[str, Any]) -> list[str]:
    points: list[str] = []
    mp = node.get("mountpoint")
    if isinstance(mp, str) and mp:
        points.append(mp)
    mps = node.get("mountpoints")
    if isinstance(mps, list):
        for item in mps:
            if isinstance(item, str) and item:
                points.append(item)
    for child in node.get("children") or []:
        if isinstance(child, dict):
            points.extend(_collect_mountpoints(child))
    # Preserve order, remove duplicates
    seen: set[str] = set()
    out: list[str] = []
    for p in points:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def _collect_filesystems(node: dict[str, Any]) -> list[str]:
    fs: list[str] = []
    fstype = node.get("fstype")
    if isinstance(fstype, str) and fstype:
        fs.append(fstype)
    for child in node.get("children") or []:
        if isinstance(child, dict):
            fs.extend(_collect_filesystems(child))
    seen: set[str] = set()
    out: list[str] = []
    for item in fs:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def assess_device_safety(device: DeviceInfo) -> list[SafetyFlag]:
    """Return safety flags for a device. Read-only assessment."""
    flags: list[SafetyFlag] = []
    mounts = set(device.mountpoints)
    critical = sorted(mounts & CRITICAL_MOUNTPOINTS)
    if critical:
        flags.append(
            SafetyFlag(
                "error",
                "system-disk",
                f"System/critical mount points detected ({', '.join(critical)}). "
                "This device must not be used as an installation target.",
            )
        )
    if mounts and not critical:
        flags.append(
            SafetyFlag(
                "warning",
                "mounted",
                f"Mounted partitions detected ({', '.join(sorted(mounts))}). "
                "Future operations would require unmounting with explicit confirmation.",
            )
        )
    if not device.is_removable and device.tran != "usb":
        flags.append(
            SafetyFlag(
                "warning",
                "not-removable",
                "Device is not reported as removable/USB by sysfs. "
                "Selection is allowed for review only; destructive operations remain unimplemented.",
            )
        )
    else:
        flags.append(
            SafetyFlag(
                "info",
                "removable-hint",
                "Device is reported as removable/hotplug or USB transport (not inferred from name).",
            )
        )
    if device.is_read_only:
        flags.append(
            SafetyFlag("error", "read-only", "Device is read-only and cannot be written.")
        )
    if device.size_bytes <= 0:
        flags.append(SafetyFlag("warning", "unknown-size", "Device size is unknown."))
    return flags


def _node_to_device(node: dict[str, Any]) -> DeviceInfo:
    size = node.get("size")
    try:
        size_bytes = int(size) if size is not None else -1
    except (TypeError, ValueError):
        size_bytes = -1
    tran = (node.get("tran") or "") if isinstance(node.get("tran"), str) else ""
    rm = _truthy(node.get("rm"))
    hotplug = _truthy(node.get("hotplug"))
    # Conservative removable hint: sysfs flags or USB transport. Never use name.
    is_removable = rm or hotplug or tran.lower() == "usb"
    device = DeviceInfo(
        name=str(node.get("name") or ""),
        path=str(node.get("path") or ""),
        size_bytes=size_bytes,
        model=str(node.get("model") or ""),
        vendor=str(node.get("vendor") or ""),
        serial=str(node.get("serial") or ""),
        tran=tran,
        pttype=str(node.get("pttype") or ""),
        ptuuid=str(node.get("ptuuid") or ""),
        is_removable=is_removable,
        is_hotplug=hotplug,
        is_read_only=_truthy(node.get("ro")),
        mountpoints=_collect_mountpoints(node),
        filesystems=_collect_filesystems(node),
        children=[c for c in (node.get("children") or []) if isinstance(c, dict)],
    )
    device.flags = assess_device_safety(device)
    return device


def parse_lsblk_json(payload: str) -> list[DeviceInfo]:
    """Parse `lsblk --json` output into device models."""
    data = json.loads(payload)
    devices_raw = data.get("blockdevices") if isinstance(data, dict) else None
    if not isinstance(devices_raw, list):
        raise ValueError("lsblk JSON missing 'blockdevices' list")
    result: list[DeviceInfo] = []
    for node in devices_raw:
        if not isinstance(node, dict):
            continue
        if str(node.get("type") or "").lower() != "disk":
            continue
        result.append(_node_to_device(node))
    return result


def scan_devices() -> ScanResult:
    """Scan storage devices using lsblk (Linux). Read-only, non-destructive."""
    if not sys.platform.startswith("linux"):
        return ScanResult(
            errors=[
                "Device detection is only supported on Linux. "
                "This environment can display the UI, but cannot scan Linux block devices."
            ]
        )
    lsblk = shutil.which("lsblk")
    if not lsblk:
        return ScanResult(
            errors=[
                "lsblk was not found. Install util-linux and ensure lsblk is in PATH."
            ]
        )
    cmd = [
        lsblk,
        "--json",
        "--bytes",
        "--output",
        ",".join(LSBLK_COLUMNS),
    ]
    try:
        proc = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        logger.exception("Failed to run lsblk")
        return ScanResult(errors=[f"Failed to run lsblk: {exc}"])

    if proc.returncode != 0:
        msg = (proc.stderr or proc.stdout or "").strip() or f"exit code {proc.returncode}"
        logger.warning("lsblk failed: %s", msg)
        return ScanResult(errors=[f"lsblk failed: {msg}"])

    try:
        devices = parse_lsblk_json(proc.stdout)
    except Exception as exc:
        logger.exception("Failed to parse lsblk output")
        return ScanResult(errors=[f"Failed to parse lsblk output: {exc}"])

    logger.info("Scanned %d disk device(s)", len(devices))
    return ScanResult(devices=devices, scanned=True)
