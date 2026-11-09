"""HTTP(S) file download engine (Phase 3).

This module provides generic, resumable downloads with progress callbacks.
It does NOT resolve official Microsoft download URLs. Callers/UI must ensure
sources comply with project policy (official Microsoft sources only; never
silently substitute third-party ISOs).
"""

from __future__ import annotations

import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

ProgressCallback = Callable[[int, int | None, float | None], None]  # read, total, bytes_per_sec
CHUNK_SIZE = 1024 * 256


@dataclass(frozen=True)
class DownloadResult:
    """Outcome of a download attempt."""

    path: Path
    bytes_downloaded: int
    total_bytes: int | None
    resumed: bool
    completed: bool
    message: str


class DownloadCancelled(Exception):
    """Raised when a download is cancelled."""


class DownloadError(Exception):
    """Raised for download failures."""


def _safe_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme.lower() not in {"http", "https"}:
        raise DownloadError("Only http/https URLs are allowed.")
    if not parsed.netloc:
        raise DownloadError("URL is missing a host.")
    return url


def download_file(
    url: str,
    destination: str | Path,
    *,
    resume: bool = True,
    timeout: float = 30.0,
    progress: ProgressCallback | None = None,
    cancel_event: threading.Event | None = None,
    user_agent: str = "WinMedia-Linux/0.1",
) -> DownloadResult:
    """Download a file to destination (writes <destination>.part, then renames).

    Non-destructive to existing unrelated files except the destination/part path.
    """
    url = _safe_url(url)
    dest = Path(destination).expanduser()
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_name(dest.name + ".part")

    existing = 0
    if resume and part.exists():
        try:
            existing = part.stat().st_size
        except OSError:
            existing = 0
    mode = "ab" if existing > 0 else "wb"

    headers = {"User-Agent": user_agent}
    if existing > 0:
        headers["Range"] = f"bytes={existing}-"
    req = urllib.request.Request(url, headers=headers, method="GET")

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = getattr(resp, "status", 200)
            # If server ignored Range, restart.
            resumed = existing > 0 and status == 206
            if existing > 0 and status == 200:
                existing = 0
                mode = "wb"
                resumed = False
            elif existing > 0 and status != 206:
                raise DownloadError(f"Unexpected HTTP status for resume: {status}")

            total = None
            clen = resp.headers.get("Content-Length")
            if clen is not None:
                try:
                    total = int(clen) + (existing if resumed else 0)
                except ValueError:
                    total = None
            # Content-Range: bytes start-end/total
            cr = resp.headers.get("Content-Range")
            if cr and "/" in cr:
                try:
                    total = int(cr.rsplit("/", 1)[1])
                except ValueError:
                    pass

            read = existing
            start_t = time.monotonic()
            last_t = start_t
            last_read = read
            with part.open(mode) as f:
                while True:
                    if cancel_event and cancel_event.is_set():
                        raise DownloadCancelled("Download cancelled.")
                    chunk = resp.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    f.write(chunk)
                    read += len(chunk)
                    now = time.monotonic()
                    bps = None
                    dt = now - last_t
                    if dt >= 0.25:
                        bps = (read - last_read) / dt if dt > 0 else None
                        last_t = now
                        last_read = read
                    if progress:
                        progress(read, total, bps)
    except DownloadCancelled:
        return DownloadResult(
            path=dest, bytes_downloaded=existing, total_bytes=None, resumed=existing > 0,
            completed=False, message="Download cancelled. Partial data kept in .part file for possible resume."
        )
    except urllib.error.HTTPError as exc:
        raise DownloadError(f"HTTP error {exc.code}: {exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise DownloadError(f"Network error: {exc.reason}") from exc
    except TimeoutError as exc:
        raise DownloadError(f"Timed out: {exc}") from exc
    except OSError as exc:
        raise DownloadError(f"File/network I/O error: {exc}") from exc

    try:
        part.replace(dest)
    except OSError as exc:
        raise DownloadError(f"Failed to finalize downloaded file: {exc}") from exc

    return DownloadResult(
        path=dest,
        bytes_downloaded=read,
        total_bytes=total,
        resumed=existing > 0 and resumed,
        completed=True,
        message="Download completed.",
    )
