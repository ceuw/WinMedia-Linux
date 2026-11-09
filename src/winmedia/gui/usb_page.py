"""Create bootable USB page (Phase 2/4 - UI placeholder)."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout, QWidget

from winmedia.core.usb_manager import NOT_IMPLEMENTED_MESSAGE


class UsbPage(QWidget):
    """Placeholder page for bootable USB creation."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        title = QLabel("Create Bootable USB")
        title.setProperty("class", "title")
        subtitle = QLabel(
            "Prepare Windows installation media on a removable USB drive. "
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
        badge.setMaximumWidth(180)
        msg = QLabel(NOT_IMPLEMENTED_MESSAGE)
        msg.setWordWrap(True)
        safety = QLabel(
            "Safety notice: when implemented, WinMedia Linux will never format or "
            "overwrite a device automatically. It will show the device model, path, "
            "and capacity and require explicit confirmation before any destructive "
            "operation. System disks will be rejected."
        )
        safety.setProperty("class", "muted")
        safety.setWordWrap(True)
        btn = QPushButton("Create installation media")
        btn.setProperty("class", "primary")
        btn.setEnabled(False)
        btn.setToolTip("Disabled: USB creation is not implemented. No disk operations are performed.")
        card_layout.addWidget(badge, 0, Qt.AlignLeft)
        card_layout.addWidget(msg)
        card_layout.addWidget(safety)
        card_layout.addWidget(btn, 0, Qt.AlignLeft)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(card)
        layout.addStretch(1)
