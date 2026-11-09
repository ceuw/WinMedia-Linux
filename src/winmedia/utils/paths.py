"""Application paths (config, cache, logs)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "winmedia-linux"


def _home() -> Path:
    return Path.home()


def config_dir() -> Path:
    """Return the user configuration directory."""
    if sys.platform.startswith("linux"):
        base = Path(os.environ.get("XDG_CONFIG_HOME", _home() / ".config"))
    elif sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", _home() / "AppData" / "Roaming"))
    else:
        base = _home() / ".config"
    path = base / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def cache_dir() -> Path:
    """Return the user cache directory."""
    if sys.platform.startswith("linux"):
        base = Path(os.environ.get("XDG_CACHE_HOME", _home() / ".cache"))
    elif sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", _home() / "AppData" / "Local"))
    else:
        base = _home() / ".cache"
    path = base / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def log_dir() -> Path:
    """Return the directory for application logs."""
    path = cache_dir() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def log_file() -> Path:
    """Return the default log file path."""
    return log_dir() / "winmedia.log"
