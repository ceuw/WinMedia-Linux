"""Lightweight GUI smoke test (offscreen when supported)."""

import os

import pytest

# Prefer offscreen to allow running in headless environments.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6")


def test_main_window_constructs(qtbot) -> None:
    from winmedia.gui.main_window import MainWindow

    window = MainWindow()
    qtbot.addWidget(window)
    assert window.windowTitle().startswith("WinMedia Linux")
    assert window.stack.count() == 4
    window.navigate(1)
    assert window.stack.currentIndex() == 1
    window.navigate(3)
    assert window.stack.currentIndex() == 3
