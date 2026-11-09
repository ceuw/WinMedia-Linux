"""Tests for local ISO inspection (non-destructive)."""

from pathlib import Path

from winmedia.core.iso_manager import inspect_iso


def test_inspect_iso_existing_file(tmp_path: Path) -> None:
    p = tmp_path / "win11.iso"
    p.write_bytes(b"fake iso")
    info = inspect_iso(p)
    assert info.valid_selection
    assert info.exists and info.is_file and info.readable
    assert info.has_iso_extension
    assert info.size_bytes == len(b"fake iso")


def test_inspect_iso_missing(tmp_path: Path) -> None:
    info = inspect_iso(tmp_path / "missing.iso")
    assert not info.valid_selection
    assert not info.exists
    assert info.error


def test_inspect_iso_directory(tmp_path: Path) -> None:
    info = inspect_iso(tmp_path)
    assert not info.valid_selection
    assert info.exists
    assert not info.is_file
