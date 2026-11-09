"""Boot compatibility planning (Phase 4). Non-destructive planning only."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BootPlan:
    """Intended boot compatibility notes (actual implementation is Linux/tool dependent)."""

    mode: str
    warnings: list[str]
    requires_verification: bool = True


def plan_boot(mode: str) -> BootPlan:
    m = (mode or "").lower()
    warnings: list[str] = []
    if m == "legacy":
        warnings.append("Legacy BIOS support depends on target firmware and bootloader setup.")
    if m == "uefi":
        warnings.append("UEFI bootability depends on partition/filesystem layout and boot files.")
    if m == "hybrid":
        warnings.append("Hybrid media is best-effort; do not assume bootability without verification.")
    warnings.append("Do not claim USB bootability without appropriate verification on target hardware.")
    return BootPlan(mode=m, warnings=warnings)
