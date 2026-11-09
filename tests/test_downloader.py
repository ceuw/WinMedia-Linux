"""Tests for the generic HTTP downloader (no real network)."""

from __future__ import annotations

import io
import threading
from pathlib import Path

import pytest

from winmedia.core.downloader import DownloadCancelled, DownloadError, download_file


class FakeResponse:
    def __init__(self, data: bytes, status: int = 200, headers: dict[str, str] | None = None):
        self._bio = io.BytesIO(data)
        self.status = status
        self.headers = headers or {"Content-Length": str(len(data))}

    def read(self, n: int = -1) -> bytes:
        return self._bio.read(n)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_download_file_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    payload = b"windows-iso-bytes" * 100
    dest = tmp_path / "out.iso"

    def fake_urlopen(req, timeout=None):
        assert req.full_url == "https://example.test/file.iso"
        return FakeResponse(payload, status=200)

    monkeypatch.setattr("winmedia.core.downloader.urllib.request.urlopen", fake_urlopen)
    result = download_file("https://example.test/file.iso", dest)
    assert result.completed
    assert dest.read_bytes() == payload
    assert not dest.with_name("out.iso.part").exists()


def test_download_rejects_non_http(tmp_path: Path) -> None:
    with pytest.raises(DownloadError):
        download_file("file:///etc/passwd", tmp_path / "x")


def test_download_resume(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    full = b"abcdefghij"
    part = tmp_path / "out.iso.part"
    part.write_bytes(full[:4])  # existing partial
    dest = tmp_path / "out.iso"

    def fake_urlopen(req, timeout=None):
        assert req.headers.get("Range") == "bytes=4-"
        return FakeResponse(full[4:], status=206, headers={
            "Content-Length": str(len(full) - 4),
            "Content-Range": f"bytes 4-{len(full)-1}/{len(full)}",
        })

    monkeypatch.setattr("winmedia.core.downloader.urllib.request.urlopen", fake_urlopen)
    result = download_file("https://example.test/file.iso", dest, resume=True)
    assert result.completed
    assert dest.read_bytes() == full


def test_download_cancel(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    payload = b"x" * (1024 * 512)
    dest = tmp_path / "out.iso"
    cancel = threading.Event()
    calls = {"n": 0}

    class SlowResponse(FakeResponse):
        def read(self, n: int = -1) -> bytes:
            calls["n"] += 1
            if calls["n"] > 1:
                cancel.set()
            return super().read(n)

    monkeypatch.setattr(
        "winmedia.core.downloader.urllib.request.urlopen",
        lambda req, timeout=None: SlowResponse(payload, 200),
    )
    result = download_file("https://example.test/file.iso", dest, cancel_event=cancel)
    assert not result.completed
    assert "cancelled" in result.message.lower()
    assert dest.with_name("out.iso.part").exists()
