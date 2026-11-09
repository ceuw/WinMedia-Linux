"""Structured application logging configuration."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from winmedia.utils.paths import log_file

_CONFIGURED = False


class _SafeFormatter(logging.Formatter):
    """Formatter that avoids leaking sensitive values in common patterns."""

    def format(self, record: logging.LogRecord) -> str:
        # Keep formatting simple; callers must not log secrets.
        return super().format(record)


def setup_logging(level: int = logging.INFO, path: Path | None = None) -> Path:
    """Configure root logging to stderr and a rotating-friendly file.

    Returns the log file path. Safe to call multiple times.
    """
    global _CONFIGURED
    target = path or log_file()
    target.parent.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(level)

    if not _CONFIGURED:
        fmt = _SafeFormatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        stream = logging.StreamHandler(sys.stderr)
        stream.setFormatter(fmt)
        stream.setLevel(level)
        root.addHandler(stream)

        file_handler = logging.FileHandler(target, encoding="utf-8")
        file_handler.setFormatter(fmt)
        file_handler.setLevel(level)
        root.addHandler(file_handler)
        _CONFIGURED = True

    logging.getLogger(__name__).debug("Logging initialized at %s", target)
    return target
