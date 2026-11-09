"""Partition/format planning (Phase 4). Non-destructive planning only."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PartitionPlan:
    """Describes intended partition layout (not executed)."""

    scheme: str  # gpt|mbr
    filesystem: str  # fat32|ntfs
    boot_mode: str  # uefi|legacy|hybrid (best-effort; compatibility varies)
    notes: list[str]


def plan_partitioning(*, scheme: str, filesystem: str, boot_mode: str) -> PartitionPlan:
    notes: list[str] = []
    fs = filesystem.lower()
    sch = scheme.lower()
    mode = boot_mode.lower()
    if fs == "fat32":
        notes.append("FAT32 is broadly UEFI-friendly but cannot store files >4GiB.")
    if fs == "ntfs":
        notes.append("NTFS can store large files; pure UEFI firmware support varies without extra boot handling.")
    if mode == "hybrid":
        notes.append("Hybrid UEFI+Legacy compatibility is complex and hardware-dependent; verify on target systems.")
    if sch == "mbr" and mode == "uefi":
        notes.append("UEFI typically prefers GPT; MBR+UEFI combinations may be unsupported.")
    return PartitionPlan(scheme=sch, filesystem=fs, boot_mode=mode, notes=notes)
