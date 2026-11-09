"""Tests for SHA-256 calculation and comparison."""

from pathlib import Path

from winmedia.core.verifier import calculate_sha256, normalize_sha256, verify_sha256


def test_normalize_sha256() -> None:
    good = "a" * 64
    assert normalize_sha256(good) == good
    assert normalize_sha256("A" * 64) == good
    assert normalize_sha256(" " + good + "\n") == good
    assert normalize_sha256("") is None
    assert normalize_sha256("abc") is None
    assert normalize_sha256("z" * 64) is None


def test_calculate_sha256_and_progress(tmp_path: Path) -> None:
    p = tmp_path / "test.bin"
    p.write_bytes(b"hello winmedia" * 1000)
    calls: list[tuple[int, int | None]] = []

    def progress(read: int, total: int | None) -> None:
        calls.append((read, total))

    digest = calculate_sha256(p, progress=progress)
    assert len(digest) == 64
    assert calls
    assert calls[-1][0] == p.stat().st_size
    assert calls[-1][1] == p.stat().st_size
    assert calculate_sha256(p) == digest


def test_verify_sha256_match(tmp_path: Path) -> None:
    p = tmp_path / "test.iso"
    p.write_bytes(b"content")
    expected = calculate_sha256(p)
    result = verify_sha256(p, expected=expected)
    assert result.matches is True
    assert result.expected_sha256 == expected
    assert "matches" in result.message.lower()
    assert "authentic" in result.message.lower() or "official" in result.message.lower()


def test_verify_sha256_mismatch(tmp_path: Path) -> None:
    p = tmp_path / "test.iso"
    p.write_bytes(b"content")
    result = verify_sha256(p, expected="b" * 64)
    assert result.matches is False
    assert "NOT match" in result.message


def test_verify_sha256_no_expected(tmp_path: Path) -> None:
    p = tmp_path / "test.iso"
    p.write_bytes(b"content")
    result = verify_sha256(p)
    assert result.matches is None
    assert len(result.calculated_sha256) == 64
    assert "not an independent authenticity verification" in result.message
