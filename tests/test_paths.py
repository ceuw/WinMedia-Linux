"""Tests for application path helpers."""

from pathlib import Path

from winmedia.utils import paths


def test_paths_create_directories() -> None:
    cfg = paths.config_dir()
    cache = paths.cache_dir()
    logs = paths.log_dir()
    assert isinstance(cfg, Path) and cfg.exists()
    assert isinstance(cache, Path) and cache.exists()
    assert isinstance(logs, Path) and logs.exists()
    assert paths.log_file().name == "winmedia.log"
