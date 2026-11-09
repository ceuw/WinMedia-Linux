"""Tests for non-destructive validation helpers."""

from pathlib import Path

from winmedia.utils.validators import has_iso_extension, is_readable_file


def test_has_iso_extension_case_insensitive() -> None:
    assert has_iso_extension(Path("windows.ISO"))
    assert has_iso_extension(Path("/tmp/Win11.iso"))
    assert not has_iso_extension(Path("image.img"))
    assert not has_iso_extension(Path("noext"))


def test_is_readable_file(tmp_path: Path) -> None:
    f = tmp_path / "sample.iso"
    f.write_bytes(b"test")
    assert is_readable_file(f)
    assert not is_readable_file(tmp_path / "missing.iso")
    assert not is_readable_file(tmp_path)
