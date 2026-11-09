"""ISO integrity verification (Phase 3).

SHA-256 is calculated locally. A match with a user-provided or officially
published checksum can indicate integrity, but this module must not claim the
ISO is authentic solely because a hash was calculated or compared.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

ProgressCallback = Callable[[int, int | None], None]
_HEX_RE = re.compile(r"^[0-9a-fA-F]{64}$")


@dataclass(frozen=True)
class VerificationResult:
    """Result of a hash calculation/comparison."""

    calculated_sha256: str
    expected_sha256: str | None
    matches: bool | None
    message: str


def normalize_sha256(value: str) -> str | None:
    """Normalize a SHA-256 hex digest; return None if invalid/empty."""
    v = value.strip().lower()
    if not v:
        return None
    if not _HEX_RE.fullmatch(v):
        return None
    return v


def calculate_sha256(
    path: str | Path, progress: ProgressCallback | None = None, chunk_size: int = 1024 * 1024
) -> str:
    """Calculate SHA-256 for a file by streaming its contents."""
    p = Path(path)
    total = None
    try:
        total = p.stat().st_size
    except OSError:
        total = None
    h = hashlib.sha256()
    read = 0
    with p.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
            read += len(chunk)
            if progress:
                progress(read, total)
    return h.hexdigest()


def verify_sha256(
    path: str | Path,
    expected: str | None = None,
    progress: ProgressCallback | None = None,
) -> VerificationResult:
    """Calculate local SHA-256 and optionally compare to an expected digest."""
    calculated = calculate_sha256(path, progress=progress)
    expected_norm = normalize_sha256(expected or "")
    if expected and expected_norm is None:
        return VerificationResult(
            calculated_sha256=calculated,
            expected_sha256=None,
            matches=None,
            message=(
                "Local SHA-256 calculated. The provided expected value is not a valid "
                "64-character SHA-256 hex digest, so no comparison was performed."
            ),
        )
    if expected_norm is None:
        return VerificationResult(
            calculated_sha256=calculated,
            expected_sha256=None,
            matches=None,
            message=(
                "Local SHA-256 calculated. No expected checksum was provided, so this "
                "is not an independent authenticity verification."
            ),
        )
    matches = calculated.lower() == expected_norm
    if matches:
        msg = (
            "Local SHA-256 matches the provided expected checksum. "
            "This confirms the file matches that checksum; it does not by itself "
            "prove the ISO is an official Microsoft image unless the expected "
            "checksum came from a trusted Microsoft source."
        )
    else:
        msg = (
            "Local SHA-256 does NOT match the provided expected checksum. "
            "The file may be incomplete, corrupted, or different from the expected image."
        )
    return VerificationResult(
        calculated_sha256=calculated,
        expected_sha256=expected_norm,
        matches=matches,
        message=msg,
    )
