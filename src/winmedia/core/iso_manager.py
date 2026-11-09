"""ISO selection and inspection helpers (Phase 3)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from winmedia.utils.validators import has_iso_extension, is_readable_file


@dataclass(frozen=True)
class IsoInfo:
    """Read-only information about a local ISO file."""

    path: Path
    exists: bool
    is_file: bool
    readable: bool
    has_iso_extension: bool
    size_bytes: int | None
    error: str = ""

    @property
    def valid_selection(self) -> bool:
        return self.exists and self.is_file and self.readable and self.error == ""

    @property
    def size_human(self) -> str:
        if self.size_bytes is None:
            return "unknown"
        size = float(self.size_bytes)
        for unit in ["B", "KiB", "MiB", "GiB", "TiB"]:
            if size < 1024 or unit == "TiB":
                if unit == "B":
                    return f"{int(size)} {unit}"
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{self.size_bytes} B"


def inspect_iso(path: str | Path) -> IsoInfo:
    """Inspect a local path as a potential ISO. Non-destructive."""
    p = Path(path).expanduser()
    try:
        exists = p.exists()
    except OSError as exc:
        return IsoInfo(
            path=p,
            exists=False,
            is_file=False,
            readable=False,
            has_iso_extension=has_iso_extension(p),
            size_bytes=None,
            error=str(exc),
        )
    if not exists:
        return IsoInfo(
            path=p,
            exists=False,
            is_file=False,
            readable=False,
            has_iso_extension=has_iso_extension(p),
            size_bytes=None,
            error="File does not exist.",
        )
    try:
        is_file = p.is_file()
        readable = is_readable_file(p)
        size_bytes = p.stat().st_size if is_file else None
    except OSError as exc:
        return IsoInfo(
            path=p,
            exists=True,
            is_file=False,
            readable=False,
            has_iso_extension=has_iso_extension(p),
            size_bytes=None,
            error=str(exc),
        )
    error = ""
    if not is_file:
        error = "Selected path is not a file."
    elif not readable:
        error = "File is not readable."
    return IsoInfo(
        path=p,
        exists=True,
        is_file=is_file,
        readable=readable,
        has_iso_extension=has_iso_extension(p),
        size_bytes=size_bytes,
        error=error,
    )
