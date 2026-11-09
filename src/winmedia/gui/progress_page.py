"""Reusable progress display placeholder (Phase 3/4 integration)."""

from __future__ import annotations

from PySide6.QtWidgets import QFrame, QLabel, QProgressBar, QVBoxLayout, QWidget


class ProgressCard(QFrame):
    """A simple progress card; not wired to real operations in Phase 1."""

    def __init__(self, title: str = "Progress", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("class", "card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        self.title_label = QLabel(title)
        self.title_label.setProperty("class", "section")
        self.status_label = QLabel("No operation in progress.")
        self.status_label.setProperty("class", "muted")
        self.status_label.setWordWrap(True)
        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        self.bar.setTextVisible(True)
        layout.addWidget(self.title_label)
        layout.addWidget(self.status_label)
        layout.addWidget(self.bar)
