"""Tests for dependency checking (non-destructive)."""

from winmedia.services.dependency_checker import run_checks


def test_run_checks_returns_report() -> None:
    report = run_checks()
    assert report.python_version
    assert report.platform
    assert report.items
    names = {i.name for i in report.items}
    assert "PySide6" in names or any(i.kind == "python" for i in report.items)
    # Summary should be readable and never crash.
    lines = report.summary_lines()
    assert any("Platform:" in line for line in lines)
