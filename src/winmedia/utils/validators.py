"""Input validation helpers (non-destructive)."""

from __future__ import annotations

from pathlib import Path


def is_readable_file(path: Path) -> bool:
    """Return True if path exists and is a readable file."""
    try:
        return path.is_file()
    except OSError:
        return False


def has_iso_extension(path: Path) -> bool:
    """Return True if the path looks like an ISO image by extension."""
    return path.suffix.lower() == ".iso"
