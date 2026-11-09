"""Settings and diagnostics page."""

from __future__ import annotations

import logging

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from winmedia.gui.styles import available_themes
from winmedia.services.dependency_checker import DependencyReport, run_checks

logger = logging.getLogger(__name__)


class _WorkerSignals(QObject):
    finished = Signal(object)
    error = Signal(str)


class _DependencyWorker(QRunnable):
    """Run dependency checks off the UI thread."""

    def __init__(self) -> None:
        super().__init__()
        self.signals = _WorkerSignals()

    @Slot()
    def run(self) -> None:
        try:
            report = run_checks()
            try:
                self.signals.finished.emit(report)
            except RuntimeError:
                logger.debug("Dependency worker finished after UI teardown")
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Dependency check failed")
            try:
                self.signals.error.emit(str(exc))
            except RuntimeError:
                logger.debug("Dependency worker error signal skipped after UI teardown")


class SettingsPage(QWidget):
    """Application settings and dependency diagnostics."""

    theme_changed = Signal(str)

    def __init__(self, current_theme: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._pool = QThreadPool.globalInstance()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        title = QLabel("Settings")
        title.setProperty("class", "title")
        subtitle = QLabel("Appearance and system dependency diagnostics.")
        subtitle.setProperty("class", "subtitle")
        subtitle.setWordWrap(True)

        appearance = QFrame()
        appearance.setProperty("class", "card")
        app_layout = QVBoxLayout(appearance)
        app_layout.setContentsMargins(20, 20, 20, 20)
        app_layout.setSpacing(10)
        app_title = QLabel("Appearance")
        app_title.setProperty("class", "section")
        row = QHBoxLayout()
        row.setSpacing(12)
        theme_label = QLabel("Theme")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems([t.title() for t in available_themes()])
        idx = max(0, available_themes().index(current_theme) if current_theme in available_themes() else 0)
        self.theme_combo.setCurrentIndex(idx)
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        row.addWidget(theme_label)
        row.addWidget(self.theme_combo, 1)
        row.addStretch(1)
        note = QLabel("Dark theme is the default. Theme changes apply immediately.")
        note.setProperty("class", "muted")
        note.setWordWrap(True)
        app_layout.addWidget(app_title)
        app_layout.addLayout(row)
        app_layout.addWidget(note)

        deps = QFrame()
        deps.setProperty("class", "card")
        deps_layout = QVBoxLayout(deps)
        deps_layout.setContentsMargins(20, 20, 20, 20)
        deps_layout.setSpacing(10)
        deps_title = QLabel("Dependency check")
        deps_title.setProperty("class", "section")
        deps_note = QLabel(
            "Checks are non-destructive. Missing Linux system tools are expected "
            "on non-Linux development environments."
        )
        deps_note.setProperty("class", "muted")
        deps_note.setWordWrap(True)
        self.refresh_btn = QPushButton("Refresh dependency check")
        self.refresh_btn.setProperty("class", "secondary")
        self.refresh_btn.clicked.connect(self.refresh_dependencies)
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setMinimumHeight(220)
        self.output.setPlainText("Running dependency check...")
        deps_layout.addWidget(deps_title)
        deps_layout.addWidget(deps_note)
        deps_layout.addWidget(self.refresh_btn, 0, Qt.AlignLeft)
        deps_layout.addWidget(self.output)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(appearance)
        layout.addWidget(deps)
        layout.addStretch(1)

        self.refresh_dependencies()

    def _on_theme_changed(self, label: str) -> None:
        theme = label.lower()
        if theme in available_themes():
            self.theme_changed.emit(theme)

    @Slot()
    def refresh_dependencies(self) -> None:
        self.refresh_btn.setEnabled(False)
        self.output.setPlainText("Running dependency check...")
        worker = _DependencyWorker()
        worker.signals.finished.connect(self._on_report)
        worker.signals.error.connect(self._on_error)
        self._pool.start(worker)

    @Slot(object)
    def _on_report(self, report: DependencyReport) -> None:
        self.output.setPlainText("\n".join(report.summary_lines()))
        self.refresh_btn.setEnabled(True)

    @Slot(str)
    def _on_error(self, message: str) -> None:
        self.output.setPlainText(f"Dependency check failed: {message}")
        self.refresh_btn.setEnabled(True)
