"""Qt stylesheets for dark and light themes."""

from __future__ import annotations

from dataclasses import dataclass

DARK = "dark"
LIGHT = "light"
DEFAULT_THEME = DARK


@dataclass(frozen=True)
class ThemePalette:
    """Color tokens used by stylesheets."""

    name: str
    bg: str
    surface: str
    surface_alt: str
    border: str
    text: str
    text_muted: str
    accent: str
    accent_hover: str
    accent_text: str
    sidebar: str
    sidebar_hover: str
    sidebar_active: str
    danger: str
    success: str


PALETTES: dict[str, ThemePalette] = {
    DARK: ThemePalette(
        name=DARK,
        bg="#121417",
        surface="#1b1f24",
        surface_alt="#232933",
        border="#2f3742",
        text="#e8edf2",
        text_muted="#a7b1bc",
        accent="#4f8cff",
        accent_hover="#6aa0ff",
        accent_text="#ffffff",
        sidebar="#171b20",
        sidebar_hover="#222831",
        sidebar_active="#263245",
        danger="#ff6b6b",
        success="#4cd27a",
    ),
    LIGHT: ThemePalette(
        name=LIGHT,
        bg="#f4f6f8",
        surface="#ffffff",
        surface_alt="#f0f3f6",
        border="#d7dee6",
        text="#18212b",
        text_muted="#566575",
        accent="#2563eb",
        accent_hover="#3b82f6",
        accent_text="#ffffff",
        sidebar="#eef2f6",
        sidebar_hover="#e3e9f0",
        sidebar_active="#dbeafe",
        danger="#dc2626",
        success="#16a34a",
    ),
}


def available_themes() -> list[str]:
    return [DARK, LIGHT]


def build_stylesheet(theme: str) -> str:
    """Return a complete application stylesheet for the requested theme."""
    p = PALETTES.get(theme, PALETTES[DEFAULT_THEME])
    return f"""
    * {{ font-family: "Segoe UI", "Noto Sans", "Ubuntu", sans-serif; }}
    QMainWindow, QWidget#Root {{
        background: {p.bg};
        color: {p.text};
        font-size: 14px;
    }}
    QLabel {{ color: {p.text}; }}
    QLabel[class="muted"] {{ color: {p.text_muted}; }}
    QLabel[class="title"] {{ font-size: 26px; font-weight: 600; }}
    QLabel[class="subtitle"] {{ font-size: 15px; color: {p.text_muted}; }}
    QLabel[class="section"] {{ font-size: 16px; font-weight: 600; }}
    QLabel[class="badge"] {{
        background: {p.surface_alt};
        color: {p.text_muted};
        border: 1px solid {p.border};
        border-radius: 10px;
        padding: 4px 10px;
        font-size: 12px;
    }}
    QFrame[class="card"] {{
        background: {p.surface};
        border: 1px solid {p.border};
        border-radius: 14px;
    }}
    QFrame[class="sidebar"] {{
        background: {p.sidebar};
        border-right: 1px solid {p.border};
    }}
    QPushButton[class="nav"] {{
        text-align: left;
        padding: 12px 14px;
        border: none;
        border-radius: 10px;
        background: transparent;
        color: {p.text};
        font-size: 14px;
    }}
    QPushButton[class="nav"]:hover {{ background: {p.sidebar_hover}; }}
    QPushButton[class="nav"][active="true"] {{
        background: {p.sidebar_active};
        color: {p.accent};
        font-weight: 600;
    }}
    QPushButton[class="primary"] {{
        background: {p.accent};
        color: {p.accent_text};
        border: none;
        border-radius: 10px;
        padding: 10px 16px;
        font-weight: 600;
    }}
    QPushButton[class="primary"]:hover {{ background: {p.accent_hover}; }}
    QPushButton[class="primary"]:disabled {{
        background: {p.surface_alt};
        color: {p.text_muted};
    }}
    QPushButton[class="secondary"] {{
        background: {p.surface_alt};
        color: {p.text};
        border: 1px solid {p.border};
        border-radius: 10px;
        padding: 10px 16px;
    }}
    QPushButton[class="secondary"]:hover {{ border-color: {p.accent}; }}
    QComboBox, QLineEdit {{
        background: {p.surface_alt};
        color: {p.text};
        border: 1px solid {p.border};
        border-radius: 10px;
        padding: 8px 10px;
    }}
    QComboBox:focus, QLineEdit:focus {{ border-color: {p.accent}; }}
    QTextEdit, QPlainTextEdit {{
        background: {p.surface_alt};
        color: {p.text};
        border: 1px solid {p.border};
        border-radius: 12px;
        padding: 10px;
        selection-background-color: {p.accent};
    }}
    QScrollArea {{ border: none; background: transparent; }}
    QScrollBar:vertical {{
        background: transparent; width: 10px; margin: 4px;
    }}
    QScrollBar::handle:vertical {{
        background: {p.border}; border-radius: 5px; min-height: 24px;
    }}
    QStatusBar {{
        background: {p.surface};
        color: {p.text_muted};
        border-top: 1px solid {p.border};
    }}
    """
