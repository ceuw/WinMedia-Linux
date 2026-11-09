"""Bootable USB creation planning and guarded execution scaffolding (Phase 4).

SAFETY: No automatic formatting/writing. Execution is Linux-only, requires
explicit confirmation, system-disk rejection, mount checks, and device
revalidation immediately before any destructive step. This module provides
planning/validation and guarded command construction; real hardware behavior
must be verified on Linux with disposable media.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from winmedia.core.bootloader import plan_boot
from winmedia.core.partition_manager import plan_partitioning
from winmedia.core.wim_handler import plan_wim_handling
from winmedia.services.device_detection import CRITICAL_MOUNTPOINTS, DeviceInfo

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UsbCreationRequest:
    source_iso: Path
    target_device_path: str
    target_stable_id: str
    boot_mode: str = "uefi"  # uefi|legacy|hybrid
    partition_scheme: str = "gpt"  # gpt|mbr
    filesystem: str = "fat32"  # fat32|ntfs
    install_wim_size: int | None = None
    dry_run: bool = True


@dataclass
class PlanReport:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)
    confirmation_token: str = ""  # what user must acknowledge (device path)


def validate_request(req: UsbCreationRequest, device: DeviceInfo | None) -> PlanReport:
    """Validate a creation request against known device info (non-destructive)."""
    report = PlanReport(ok=True)
    if not sys.platform.startswith("linux"):
        report.warnings.append("Actual USB creation execution is only supported on Linux.")
    if not req.source_iso:
        report.ok = False
        report.errors.append("No source ISO selected.")
    elif not req.source_iso.exists():
        report.ok = False
        report.errors.append(f"Source ISO does not exist: {req.source_iso}")
    elif not req.source_iso.is_file():
        report.ok = False
        report.errors.append("Source ISO path is not a file.")
    if not req.target_device_path:
        report.ok = False
        report.errors.append("No target device selected.")

    if device is None:
        report.ok = False
        report.errors.append("Target device information is unavailable. Refresh devices and reselect.")
    else:
        if req.target_stable_id and device.stable_id() != req.target_stable_id:
            report.ok = False
            report.errors.append(
                "Target device identity changed since selection. Revalidate and select again."
            )
        if device.path != req.target_device_path:
            report.ok = False
            report.errors.append("Target device path mismatch. Revalidate and select again.")
        critical = sorted(set(device.mountpoints) & CRITICAL_MOUNTPOINTS)
        if critical:
            report.ok = False
            report.errors.append(
                f"Refusing target: critical mount points detected ({', '.join(critical)})."
            )
        if device.mountpoints and not critical:
            report.warnings.append(
                f"Device has mounted partitions ({', '.join(device.mountpoints)}). "
                "Execution would require explicit unmount steps and confirmation."
            )
        if device.is_read_only:
            report.ok = False
            report.errors.append("Target device is read-only.")
        if device.has_errors:
            report.errors.extend([f.message for f in device.flags if f.level == "error"])
            report.ok = False
        for f in device.flags:
            if f.level == "warning":
                report.warnings.append(f.message)

    part = plan_partitioning(scheme=req.partition_scheme, filesystem=req.filesystem, boot_mode=req.boot_mode)
    boot = plan_boot(req.boot_mode)
    wim = plan_wim_handling(req.install_wim_size, req.filesystem)
    report.warnings.extend(part.notes)
    report.warnings.extend(boot.warnings)
    report.warnings.append(wim.reason)
    if wim.needs_split and not wim.tool_available:
        report.warnings.append(
            "wimlib-imagex not found; FAT32+large WIM handling will fail on Linux unless installed."
        )

    report.steps = build_plan_steps(req, device)
    report.confirmation_token = req.target_device_path
    if report.errors:
        report.ok = False
    return report


def build_plan_steps(req: UsbCreationRequest, device: DeviceInfo | None) -> list[str]:
    """Build a human-readable, non-executing plan."""
    dev = device.display_name if device else req.target_device_path
    steps = [
        f"Source ISO: {req.source_iso}",
        f"Target device: {dev} ({req.target_device_path})",
        f"Boot mode: {req.boot_mode}; partition scheme: {req.partition_scheme}; filesystem: {req.filesystem}",
        "SAFETY: explicit confirmation required; revalidate device immediately before execution.",
        "SAFETY: reject if system/critical mounts or device identity changes.",
    ]
    if req.dry_run:
        steps.append("Mode: DRY RUN / plan preview (no disk writes).")
    else:
        steps.append("Mode: EXECUTION REQUESTED (Linux-only, guarded; will fail closed if checks fail).")
    steps.extend([
        "Planned high-level steps (Linux): unmount target partitions if needed (authorized),",
        "  partition/reformat target (destructive), create filesystem(s), copy ISO contents,",
        "  handle large install.wim (split for FAT32 when required/tool available), apply boot support as feasible, sync/unmount, verify.",
        "Bootability must be verified on target hardware; do not assume success.",
    ])
    return steps


def execute_guarded(req: UsbCreationRequest, device: DeviceInfo | None) -> tuple[bool, str]:
    """Guarded execution entry point.

    This implementation is intentionally fail-closed. It performs validation and
    refuses to run destructive operations unless on Linux with all safety checks
    passing and required tools present. Full destructive disk writing is a
    high-risk operation; real execution should only proceed after thorough Linux
    hardware testing. For now, returns a clear refusal/plan status.
    """
    report = validate_request(req, device)
    if not report.ok:
        return False, "Plan validation failed:\n- " + "\n- ".join(report.errors)
    if req.dry_run:
        return True, "Dry run: validation passed. No disk operations performed.\n\n" + "\n".join(report.steps)
    if not sys.platform.startswith("linux"):
        return False, "Execution refused: bootable USB creation is only supported on Linux."
    # Fail closed: destructive implementation requires privileged, device-specific
    # operations and extensive real-hardware verification. Do not execute blindly.
    missing = [t for t in ("lsblk", "parted", "wipefs", "mkfs.vfat", "mount", "umount") if shutil.which(t) is None]
    if missing:
        return False, "Execution refused: required Linux tools missing: " + ", ".join(missing)
    return False, (
        "Execution refused by safety gate: destructive disk operations are not enabled "
        "in this build without verified Linux hardware testing. Validation/plan passed, "
        "but no disk was modified. See LOG.md for status."
    )
