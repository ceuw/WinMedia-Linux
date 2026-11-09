"""Application entry point."""

from __future__ import annotations

import argparse
import logging
import os
import sys

from winmedia import __version__
from winmedia.utils.logging_config import setup_logging

logger = logging.getLogger(__name__)


def _has_display() -> bool:
    """Best-effort check for a graphical environment."""
    if sys.platform == "win32" or sys.platform == "darwin":
        return True
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="winmedia",
        description="WinMedia Linux (Phase 1 foundation) - GUI application.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Create the UI, process events briefly, and exit (for automated checks).",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity (default: INFO).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the WinMedia Linux application."""
    args = _build_parser().parse_args(argv)
    log_path = setup_logging(getattr(logging, args.log_level))
    logger.info("Starting WinMedia Linux v%s", __version__)
    logger.info("Log file: %s", log_path)

    if os.name != "nt" and hasattr(os, "geteuid"):
        try:
            if os.geteuid() == 0:
                logger.warning(
                    "Running as root is not recommended for the GUI. "
                    "Elevated privileges should only be used for specific operations when implemented."
                )
        except Exception:  # pragma: no cover
            pass

    try:
        from PySide6.QtCore import QTimer
        from PySide6.QtWidgets import QApplication

        from winmedia.gui.main_window import MainWindow
    except Exception as exc:
        logger.exception("Failed to import GUI dependencies")
        print(
            "WinMedia Linux could not start because GUI dependencies are unavailable.\n"
            f"Details: {exc}\n"
            "Install dependencies with: python -m pip install -r requirements.txt",
            file=sys.stderr,
        )
        return 1

    if not args.smoke_test and not _has_display():
        logger.error("No graphical display detected (DISPLAY/WAYLAND_DISPLAY not set).")
        print(
            "No graphical display detected. Run on a Linux desktop session, "
            "or use --smoke-test with QT_QPA_PLATFORM=offscreen if Qt supports it.",
            file=sys.stderr,
        )
        return 1

    app = QApplication(sys.argv if argv is None else [sys.argv[0], *argv])
    app.setApplicationName("WinMedia Linux")
    app.setApplicationVersion(__version__)
    window = MainWindow()
    window.show()

    if args.smoke_test:
        logger.info("Smoke test mode: scheduling exit")
        QTimer.singleShot(250, app.quit)

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
