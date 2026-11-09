"""Check runtime dependencies and report missing components.

This module performs non-destructive checks only. It does not install software.
"""

from __future__ import annotations

import importlib.util
import platform
import shutil
import sys
from dataclasses import dataclass, field


@dataclass(frozen=True)
class DependencyStatus:
    """Status of a single dependency."""

    name: str
    kind: str  # "python" or "system"
    required_for: str
    available: bool
    detail: str = ""
    install_hint: str = ""


@dataclass
class DependencyReport:
    """Aggregated dependency check results."""

    platform: str
    python_version: str
    items: list[DependencyStatus] = field(default_factory=list)

    @property
    def missing(self) -> list[DependencyStatus]:
        return [i for i in self.items if not i.available]

    @property
    def ok(self) -> list[DependencyStatus]:
        return [i for i in self.items if i.available]

    def summary_lines(self) -> list[str]:
        lines = [
            f"Platform: {self.platform}",
            f"Python: {self.python_version}",
            f"Available: {len(self.ok)} / {len(self.items)} checked dependencies",
        ]
        if self.missing:
            lines.append("")
            lines.append("Missing components:")
            for item in self.missing:
                lines.append(f"- {item.name} ({item.kind}): {item.required_for}")
                if item.install_hint:
                    lines.append(f"  Install hint: {item.install_hint}")
        return lines


def _check_python_module(module: str, required_for: str) -> DependencyStatus:
    spec = importlib.util.find_spec(module)
    if spec is None:
        hint = f"python -m pip install {module}"
        if module == "PySide6":
            hint = "python -m pip install PySide6  (or install your distro's python3-pyside6 package)"
        return DependencyStatus(
            name=module,
            kind="python",
            required_for=required_for,
            available=False,
            detail="Python module not found.",
            install_hint=hint,
        )
    origin = getattr(spec, "origin", "") or "built-in/namespace"
    return DependencyStatus(
        name=module,
        kind="python",
        required_for=required_for,
        available=True,
        detail=f"Found ({origin}).",
    )


def _check_command(command: str, required_for: str, hint: str) -> DependencyStatus:
    path = shutil.which(command)
    if path:
        return DependencyStatus(
            name=command,
            kind="system",
            required_for=required_for,
            available=True,
            detail=f"Found at {path}.",
        )
    return DependencyStatus(
        name=command,
        kind="system",
        required_for=required_for,
        available=False,
        detail="Command not found in PATH.",
        install_hint=hint,
    )


def run_checks() -> DependencyReport:
    """Run dependency checks for the current environment."""
    report = DependencyReport(
        platform=f"{platform.system()} {platform.release()} ({platform.machine()})",
        python_version=sys.version.split()[0],
    )

    report.items.append(_check_python_module("PySide6", "Graphical user interface"))

    is_linux = sys.platform.startswith("linux")
    linux_note = "" if is_linux else " (Linux target; not expected on this platform)"

    system_checks = [
        ("lsblk", "USB/storage device detection (Phase 2)", "Debian/Ubuntu: util-linux (usually installed). Fedora: util-linux."),
        ("udisksctl", "Safe device operations via UDisks2 (Phase 2+)", "Debian/Ubuntu: sudo apt install udisks2. Fedora: sudo dnf install udisks2."),
        ("parted", "Partition preparation (Phase 4)", "Debian/Ubuntu: sudo apt install parted. Fedora: sudo dnf install parted."),
        ("blkid", "Filesystem identification (Phase 2+)", "Debian/Ubuntu: util-linux. Fedora: util-linux."),
        ("mount", "Mount operations (Phase 4)", "Provided by util-linux on most Linux systems."),
        ("umount", "Unmount operations (Phase 4)", "Provided by util-linux on most Linux systems."),
        ("wimlib-imagex", "Splitting large install.wim files for FAT32 compatibility (Phase 4)", "Debian/Ubuntu: sudo apt install wimtools. Fedora: sudo dnf install wimlib-utils."),
    ]
    for cmd, why, hint in system_checks:
        status = _check_command(cmd, why + linux_note, hint)
        report.items.append(status)

    return report
