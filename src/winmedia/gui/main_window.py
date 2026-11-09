"""Main application window with sidebar navigation."""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from winmedia import __version__
from winmedia.gui.download_page import DownloadPage
from winmedia.gui.settings_page import SettingsPage
from winmedia.gui.styles import DEFAULT_THEME, build_stylesheet
from winmedia.gui.usb_page import UsbPage

logger = logging.getLogger(__name__)


class _HomePage(QWidget):
    """Home/overview page."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        hero = QFrame()
        hero.setProperty("class", "card")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(24, 24, 24, 24)
        hero_layout.setSpacing(10)
        badge = QLabel(f"Phase 1 Foundation  •  v{__version__}")
        badge.setProperty("class", "badge")
        badge.setMaximumWidth(220)
        title = QLabel("WinMedia Linux")
        title.setProperty("class", "title")
        subtitle = QLabel(
            "A Linux-native tool for downloading official Windows installation images "
            "and creating bootable USB media. Designed for reliability, clarity, and data safety."
        )
        subtitle.setProperty("class", "subtitle")
        subtitle.setWordWrap(True)
        hero_layout.addWidget(badge, 0, Qt.AlignLeft)
        hero_layout.addWidget(title)
        hero_layout.addWidget(subtitle)

        cards = QHBoxLayout()
        cards.setSpacing(14)
        cards.addWidget(
            self._info_card(
                "Safe by design",
                "Destructive disk operations are never automatic. Future USB workflows will "
                "require explicit confirmation and device revalidation.",
            ),
            1,
        )
        cards.addWidget(
            self._info_card(
                "Official sources",
                "Windows ISO downloads will use official Microsoft sources only. No third-party "
                "ISO substitution is performed.",
            ),
            1,
        )
        cards.addWidget(
            self._info_card(
                "Current status",
                "Phase 1 provides the application foundation, navigation, themes, logging, and "
                "dependency checks. Download and USB creation are not implemented yet.",
            ),
            1,
        )

        note = QLabel(
            "Use the sidebar to explore planned features. No USB devices are scanned, formatted, "
            "or modified in this phase."
        )
        note.setProperty("class", "muted")
        note.setWordWrap(True)

        layout.addWidget(hero)
        layout.addLayout(cards)
        layout.addWidget(note)
        layout.addStretch(1)

    @staticmethod
    def _info_card(title: str, body: str) -> QFrame:
        card = QFrame()
        card.setProperty("class", "card")
        l = QVBoxLayout(card)
        l.setContentsMargins(18, 18, 18, 18)
        l.setSpacing(8)
        t = QLabel(title)
        t.setProperty("class", "section")
        b = QLabel(body)
        b.setProperty("class", "muted")
        b.setWordWrap(True)
        l.addWidget(t)
        l.addWidget(b)
        l.addStretch(1)
        return card


class MainWindow(QMainWindow):
    """Primary application window."""

    def __init__(self) -> None:
        super().__init__()
        self._theme = DEFAULT_THEME
        self.setWindowTitle(f"WinMedia Linux v{__version__}")
        self.resize(1100, 720)
        self.setMinimumSize(920, 620)

        root = QWidget()
        root.setObjectName("Root")
        self.setCentralWidget(root)
        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.sidebar = QFrame()
        self.sidebar.setProperty("class", "sidebar")
        self.sidebar.setFixedWidth(240)
        side = QVBoxLayout(self.sidebar)
        side.setContentsMargins(14, 18, 14, 14)
        side.setSpacing(8)
        brand = QLabel("WinMedia Linux")
        brand.setProperty("class", "section")
        brand.setContentsMargins(10, 4, 10, 12)
        side.addWidget(brand)

        self._nav_buttons: list[QPushButton] = []
        self.stack = QStackedWidget()

        self.home_page = _HomePage()
        self.download_page = DownloadPage()
        self.usb_page = UsbPage()
        self.settings_page = SettingsPage(current_theme=self._theme)
        self.settings_page.theme_changed.connect(self.apply_theme)

        pages = [
            ("Home", self.home_page),
            ("Download Windows", self.download_page),
            ("Create Bootable USB", self.usb_page),
            ("Settings", self.settings_page),
        ]
        for i, (label, widget) in enumerate(pages):
            self.stack.addWidget(widget)
            btn = QPushButton(label)
            btn.setProperty("class", "nav")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _=False, idx=i: self.navigate(idx))
            self._nav_buttons.append(btn)
            side.addWidget(btn)

        side.addStretch(1)
        foot = QLabel("Linux-native • No root required to launch")
        foot.setProperty("class", "muted")
        foot.setWordWrap(True)
        foot.setContentsMargins(10, 0, 10, 0)
        side.addWidget(foot)

        outer.addWidget(self.sidebar)
        outer.addWidget(self.stack, 1)

        self.statusBar().showMessage("Ready. Phase 1 foundation — download/USB features not implemented.")
        self.apply_theme(self._theme)
        self.navigate(0)
        logger.info("Main window initialized (theme=%s)", self._theme)

    @Slot(int)
    def navigate(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self._nav_buttons):
            btn.setProperty("active", i == index)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    @Slot(str)
    def apply_theme(self, theme: str) -> None:
        self._theme = theme
        self.setStyleSheet(build_stylesheet(theme))
        # Re-polish nav to keep active state visible after global stylesheet change.
        self.navigate(self.stack.currentIndex())
        self.statusBar().showMessage(f"Theme: {theme.title()}")
        logger.info("Theme applied: %s", theme)
