"""WIM inspection/splitting helpers (Phase 4).

Large `install.wim` files (>4 GiB) are incompatible with FAT32. Future
execution may split them using `wimlib-imagex` when available. This module
provides planning helpers; actual splitting is Linux/tool dependent.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

FAT32_MAX_FILE_BYTES = 4 * 1024 * 1024 * 1024 - 1  # 4 GiB - 1


@dataclass(frozen=True)
class WimPlan:
    """Plan for handling Windows image files."""

    needs_split: bool
    reason: str
    tool_available: bool
    tool_name: str = "wimlib-imagex"


def wimlib_available() -> bool:
    return shutil.which("wimlib-imagex") is not None


def plan_wim_handling(install_wim_size: int | None, target_filesystem: str) -> WimPlan:
    """Return a non-destructive plan for handling install.wim."""
    fs = (target_filesystem or "").lower()
    if install_wim_size is None:
        return WimPlan(
            needs_split=fs == "fat32",
            reason="install.wim size unknown; FAT32 targets may require splitting if >4GiB.",
            tool_available=wimlib_available(),
        )
    if fs == "fat32" and install_wim_size > FAT32_MAX_FILE_BYTES:
        return WimPlan(
            needs_split=True,
            reason=f"install.wim is {_fmt(install_wim_size)}; FAT32 requires files <= ~4GiB.",
            tool_available=wimlib_available(),
        )
    return WimPlan(
        needs_split=False,
        reason="No WIM split required for the selected filesystem/known size.",
        tool_available=wimlib_available(),
    )


def _fmt(n: int) -> str:
    size = float(n)
    for unit in ["B", "KiB", "MiB", "GiB", "TiB"]:
        if size < 1024 or unit == "TiB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return f"{n} B"
