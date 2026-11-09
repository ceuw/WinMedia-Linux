"""Windows ISO download page (Phase 3 - UI placeholder)."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout, QWidget

from winmedia.core.downloader import NOT_IMPLEMENTED_MESSAGE


class DownloadPage(QWidget):
    """Placeholder page for official Windows ISO downloads."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        title = QLabel("Download Windows")
        title.setProperty("class", "title")
        subtitle = QLabel(
            "Download official Windows installation images from Microsoft. "
            "This feature is planned and not yet implemented."
        )
        subtitle.setProperty("class", "subtitle")
        subtitle.setWordWrap(True)

        card = QFrame()
        card.setProperty("class", "card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(12)
        badge = QLabel("Not implemented yet")
        badge.setProperty("class", "badge")
        badge.setAlignment(Qt.AlignLeft)
        badge.setMaximumWidth(180)
        msg = QLabel(NOT_IMPLEMENTED_MESSAGE)
        msg.setWordWrap(True)
        details = QLabel(
            "When implemented (Phase 3), this page will use official Microsoft "
            "download sources only, show progress, support resumable downloads "
            "where available, and verify downloads. No third-party ISO sources "
            "will be substituted."
        )
        details.setProperty("class", "muted")
        details.setWordWrap(True)
        btn = QPushButton("Check for official downloads")
        btn.setProperty("class", "primary")
        btn.setEnabled(False)
        btn.setToolTip("Disabled: download workflow is not implemented yet.")
        card_layout.addWidget(badge, 0, Qt.AlignLeft)
        card_layout.addWidget(msg)
        card_layout.addWidget(details)
        card_layout.addWidget(btn, 0, Qt.AlignLeft)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(card)
        layout.addStretch(1)
