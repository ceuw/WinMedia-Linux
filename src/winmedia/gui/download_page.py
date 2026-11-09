"""Windows ISO download/selection and verification page (Phase 3 partial)."""

from __future__ import annotations

import logging
import threading
from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, Qt, QThreadPool, Signal, Slot
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from winmedia.core.downloader import DownloadCancelled, DownloadError, DownloadResult, download_file
from winmedia.core.iso_manager import IsoInfo, inspect_iso
from winmedia.core.verifier import VerificationResult, normalize_sha256, verify_sha256

logger = logging.getLogger(__name__)


def _fmt_bytes(n: int | None) -> str:
    if n is None:
        return "?"
    size = float(n)
    for unit in ["B", "KiB", "MiB", "GiB", "TiB"]:
        if size < 1024 or unit == "TiB":
            return f"{int(size)} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{n} B"


def _fmt_eta(seconds: float | None) -> str:
    if seconds is None or seconds < 0 or seconds > 60 * 60 * 24 * 7:
        return "ETA: --"
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    if h:
        return f"ETA: {h}h {m:02d}m"
    if m:
        return f"ETA: {m}m {sec:02d}s"
    return f"ETA: {sec}s"


class _VerifySignals(QObject):
    progress = Signal(int, int)  # read, total (0 total => unknown)
    finished = Signal(object)
    error = Signal(str)


class _VerifyWorker(QRunnable):
    """Calculate/verify SHA-256 off the UI thread."""

    def __init__(self, path: Path, expected: str | None) -> None:
        super().__init__()
        self.path = path
        self.expected = expected
        self.signals = _VerifySignals()

    @Slot()
    def run(self) -> None:
        try:
            def progress(read: int, total: int | None) -> None:
                try:
                    self.signals.progress.emit(read, total if total is not None else 0)
                except RuntimeError:
                    pass

            result = verify_sha256(self.path, expected=self.expected, progress=progress)
            try:
                self.signals.finished.emit(result)
            except RuntimeError:
                logger.debug("Verify worker finished after UI teardown")
        except Exception as exc:  # pragma: no cover
            logger.exception("Verification failed")
            try:
                self.signals.error.emit(str(exc))
            except RuntimeError:
                logger.debug("Verify worker error signal skipped after UI teardown")


class _DownloadSignals(QObject):
    progress = Signal(int, int, float)  # read, total, bytes_per_sec (-1 unknown)
    finished = Signal(object)
    error = Signal(str)


class _DownloadWorker(QRunnable):
    """Download a file off the UI thread."""

    def __init__(self, url: str, destination: Path, cancel_event: threading.Event) -> None:
        super().__init__()
        self.url = url
        self.destination = destination
        self.cancel_event = cancel_event
        self.signals = _DownloadSignals()

    @Slot()
    def run(self) -> None:
        try:
            def progress(read: int, total: int | None, bps: float | None) -> None:
                try:
                    self.signals.progress.emit(read, total or 0, bps if bps is not None else -1.0)
                except RuntimeError:
                    pass

            result = download_file(
                self.url,
                self.destination,
                resume=True,
                progress=progress,
                cancel_event=self.cancel_event,
            )
            try:
                self.signals.finished.emit(result)
            except RuntimeError:
                logger.debug("Download worker finished after UI teardown")
        except (DownloadError, DownloadCancelled) as exc:
            try:
                self.signals.error.emit(str(exc))
            except RuntimeError:
                pass
        except Exception as exc:  # pragma: no cover
            logger.exception("Download failed")
            try:
                self.signals.error.emit(str(exc))
            except RuntimeError:
                pass


class DownloadPage(QWidget):
    """ISO download (advanced explicit URL), local selection, and SHA-256 verification."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._pool = QThreadPool.globalInstance()
        self._iso: IsoInfo | None = None
        self._download_cancel: threading.Event | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(14)

        title = QLabel("Download & Verify Windows ISO")
        title.setProperty("class", "title")
        subtitle = QLabel(
            "Local ISO selection and SHA-256 verification are available. "
            "Automatic official Microsoft download resolution is not implemented."
        )
        subtitle.setProperty("class", "subtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        layout.addWidget(self._build_official_card())
        layout.addWidget(self._build_advanced_download_card())
        layout.addWidget(self._build_select_card())
        layout.addWidget(self._build_verify_card(), 1)

    def _build_official_card(self) -> QFrame:
        card = QFrame()
        card.setProperty("class", "card")
        l = QVBoxLayout(card)
        l.setContentsMargins(18, 18, 18, 18)
        l.setSpacing(8)
        head = QHBoxLayout()
        t = QLabel("Official download (Microsoft)")
        t.setProperty("class", "section")
        badge = QLabel("Not automated")
        badge.setProperty("class", "badge")
        badge.setMaximumWidth(140)
        head.addWidget(t)
        head.addStretch(1)
        head.addWidget(badge)
        msg = QLabel(
            "When implemented, this app will use official Microsoft download sources only, "
            "resolve fresh/expiring links as needed, and never substitute third-party ISOs. "
            "Automatic resolution is not wired up in this build."
        )
        msg.setProperty("class", "muted")
        msg.setWordWrap(True)
        btn = QPushButton("Check for official downloads")
        btn.setProperty("class", "primary")
        btn.setEnabled(False)
        l.addLayout(head)
        l.addWidget(msg)
        l.addWidget(btn, 0, Qt.AlignLeft)
        return card

    def _build_advanced_download_card(self) -> QFrame:
        card = QFrame()
        card.setProperty("class", "card")
        l = QVBoxLayout(card)
        l.setContentsMargins(18, 18, 18, 18)
        l.setSpacing(8)
        head = QHBoxLayout()
        t = QLabel("Advanced: download from explicit URL")
        t.setProperty("class", "section")
        badge = QLabel("User responsibility")
        badge.setProperty("class", "badge")
        badge.setMaximumWidth(160)
        head.addWidget(t)
        head.addStretch(1)
        head.addWidget(badge)
        warn = QLabel(
            "Warning: you are responsible for ensuring the URL points to an official "
            "Microsoft Windows ISO. WinMedia does not verify URL authenticity and will "
            "never silently substitute third-party ISOs. This is not the automated "
            "official Microsoft workflow."
        )
        warn.setProperty("class", "muted")
        warn.setWordWrap(True)
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("https://... (official Microsoft ISO URL)")
        dest_row = QHBoxLayout()
        self.dest_edit = QLineEdit()
        self.dest_edit.setPlaceholderText("Destination file (e.g., ~/Downloads/Windows.iso)")
        self.dest_browse = QPushButton("Browse...")
        self.dest_browse.setProperty("class", "secondary")
        self.dest_browse.clicked.connect(self.browse_destination)
        dest_row.addWidget(self.dest_edit, 1)
        dest_row.addWidget(self.dest_browse)
        ctrl = QHBoxLayout()
        self.dl_start = QPushButton("Download")
        self.dl_start.setProperty("class", "primary")
        self.dl_start.clicked.connect(self.start_download)
        self.dl_cancel = QPushButton("Cancel")
        self.dl_cancel.setProperty("class", "secondary")
        self.dl_cancel.clicked.connect(self.cancel_download)
        self.dl_cancel.setEnabled(False)
        self.dl_status = QLabel("Ready.")
        self.dl_status.setProperty("class", "muted")
        self.dl_status.setWordWrap(True)
        ctrl.addWidget(self.dl_start)
        ctrl.addWidget(self.dl_cancel)
        ctrl.addWidget(self.dl_status, 1)
        self.dl_progress = QProgressBar()
        self.dl_progress.setRange(0, 100)
        self.dl_progress.setValue(0)
        self.dl_progress.setVisible(False)
        l.addLayout(head)
        l.addWidget(warn)
        l.addWidget(self.url_edit)
        l.addLayout(dest_row)
        l.addLayout(ctrl)
        l.addWidget(self.dl_progress)
        return card

    def _build_select_card(self) -> QFrame:
        card = QFrame()
        card.setProperty("class", "card")
        l = QVBoxLayout(card)
        l.setContentsMargins(18, 18, 18, 18)
        l.setSpacing(8)
        t = QLabel("Local ISO file")
        t.setProperty("class", "section")
        row = QHBoxLayout()
        self.browse_btn = QPushButton("Select ISO...")
        self.browse_btn.setProperty("class", "secondary")
        self.browse_btn.clicked.connect(self.browse_iso)
        self.path_label = QLabel("No file selected.")
        self.path_label.setProperty("class", "muted")
        self.path_label.setWordWrap(True)
        self.path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        row.addWidget(self.browse_btn, 0, Qt.AlignLeft)
        row.addWidget(self.path_label, 1)
        self.info_label = QLabel("")
        self.info_label.setProperty("class", "muted")
        self.info_label.setWordWrap(True)
        l.addWidget(t)
        l.addLayout(row)
        l.addWidget(self.info_label)
        return card

    def _build_verify_card(self) -> QFrame:
        card = QFrame()
        card.setProperty("class", "card")
        l = QVBoxLayout(card)
        l.setContentsMargins(18, 18, 18, 18)
        l.setSpacing(8)
        t = QLabel("Integrity verification (SHA-256)")
        t.setProperty("class", "section")
        note = QLabel(
            "Calculates a local SHA-256 digest. Optional expected checksum comparison "
            "does not by itself prove the image is an official Microsoft ISO."
        )
        note.setProperty("class", "muted")
        note.setWordWrap(True)
        row = QHBoxLayout()
        self.expected_edit = QLineEdit()
        self.expected_edit.setPlaceholderText("Expected SHA-256 (optional, 64 hex characters)")
        self.verify_btn = QPushButton("Calculate SHA-256")
        self.verify_btn.setProperty("class", "primary")
        self.verify_btn.clicked.connect(self.start_verification)
        self.verify_btn.setEnabled(False)
        row.addWidget(self.expected_edit, 1)
        row.addWidget(self.verify_btn)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setVisible(False)
        self.result = QPlainTextEdit()
        self.result.setReadOnly(True)
        self.result.setPlaceholderText("Verification results will appear here.")
        self.result.setMaximumBlockCount(2000)
        l.addWidget(t)
        l.addWidget(note)
        l.addLayout(row)
        l.addWidget(self.progress)
        l.addWidget(self.result, 1)
        return card

    @Slot()
    def browse_destination(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save ISO as", str(Path.home() / "Downloads" / "Windows.iso"),
            "ISO images (*.iso);;All files (*)",
        )
        if path:
            self.dest_edit.setText(path)

    @Slot()
    def start_download(self) -> None:
        url = self.url_edit.text().strip()
        dest = self.dest_edit.text().strip()
        if not url or not dest:
            QMessageBox.warning(self, "Missing information", "Provide both a URL and destination file.")
            return
        if not (url.startswith("https://") or url.startswith("http://")):
            QMessageBox.warning(self, "Invalid URL", "Only http/https URLs are allowed.")
            return
        reply = QMessageBox.question(
            self,
            "Confirm download source",
            "You are responsible for ensuring this URL is an official Microsoft source. "
            "WinMedia does not verify URL authenticity.\n\nContinue with download?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        self._download_cancel = threading.Event()
        self.dl_start.setEnabled(False)
        self.dl_cancel.setEnabled(True)
        self.dl_progress.setVisible(True)
        self.dl_progress.setRange(0, 0)
        self.dl_status.setText("Starting download...")
        worker = _DownloadWorker(url, Path(dest).expanduser(), self._download_cancel)
        worker.signals.progress.connect(self._on_dl_progress)
        worker.signals.finished.connect(self._on_dl_finished)
        worker.signals.error.connect(self._on_dl_error)
        self._pool.start(worker)

    @Slot()
    def cancel_download(self) -> None:
        if self._download_cancel:
            self._download_cancel.set()
            self.dl_status.setText("Cancelling...")

    @Slot(int, int, float)
    def _on_dl_progress(self, read: int, total: int, bps: float) -> None:
        if total > 0:
            self.dl_progress.setRange(0, 100)
            self.dl_progress.setValue(min(100, int(read * 100 / total)))
            eta = ((total - read) / bps) if bps > 0 else None
            speed = f"{_fmt_bytes(int(bps))}/s" if bps > 0 else ""
            self.dl_status.setText(f"{_fmt_bytes(read)} / {_fmt_bytes(total)} {speed} {_fmt_eta(eta)}".strip())
        else:
            self.dl_progress.setRange(0, 0)
            speed = f"{_fmt_bytes(int(bps))}/s" if bps > 0 else ""
            self.dl_status.setText(f"{_fmt_bytes(read)} downloaded {speed}".strip())

    @Slot(object)
    def _on_dl_finished(self, result: DownloadResult) -> None:
        self._finish_download()
        self.dl_status.setText(result.message)
        if result.completed and result.path.exists():
            self._set_iso_path(str(result.path))

    @Slot(str)
    def _on_dl_error(self, message: str) -> None:
        self._finish_download()
        self.dl_status.setText(f"Download failed: {message}")

    def _finish_download(self) -> None:
        self.dl_start.setEnabled(True)
        self.dl_cancel.setEnabled(False)
        self.dl_progress.setVisible(False)
        self.dl_progress.setRange(0, 100)
        self.dl_progress.setValue(0)
        self._download_cancel = None

    def _set_iso_path(self, path: str) -> None:
        self._iso = inspect_iso(path)
        self.path_label.setText(str(self._iso.path))
        if self._iso.valid_selection:
            extra = "" if self._iso.has_iso_extension else " (note: extension is not .iso)"
            self.info_label.setText(f"Size: {self._iso.size_human}{extra}")
            self.verify_btn.setEnabled(True)
        else:
            self.info_label.setText(f"Cannot use file: {self._iso.error}")
            self.verify_btn.setEnabled(False)
        self.result.setPlainText("")

    @Slot()
    def browse_iso(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Windows ISO", str(Path.home()),
            "ISO images (*.iso);;All files (*)",
        )
        if path:
            self._set_iso_path(path)

    @Slot()
    def start_verification(self) -> None:
        if not self._iso or not self._iso.valid_selection:
            self.result.setPlainText("Select a valid local ISO file first.")
            return
        expected = self.expected_edit.text().strip() or None
        if expected and normalize_sha256(expected) is None:
            self.result.setPlainText(
                "The expected checksum is not a valid 64-character SHA-256 hex digest. "
                "Clear the field or enter a valid digest."
            )
            return
        self.verify_btn.setEnabled(False)
        self.browse_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        self.result.setPlainText("Calculating local SHA-256...")
        worker = _VerifyWorker(self._iso.path, expected)
        worker.signals.progress.connect(self._on_progress)
        worker.signals.finished.connect(self._on_verified)
        worker.signals.error.connect(self._on_verify_error)
        self._pool.start(worker)

    @Slot(int, int)
    def _on_progress(self, read: int, total: int) -> None:
        if total > 0:
            self.progress.setRange(0, 100)
            self.progress.setValue(min(100, int(read * 100 / total)))
        else:
            self.progress.setRange(0, 0)

    @Slot(object)
    def _on_verified(self, result: VerificationResult) -> None:
        self._finish_verification()
        lines = [
            f"Calculated SHA-256 (local): {result.calculated_sha256}",
            f"Expected SHA-256: {result.expected_sha256 or '(none provided)'}",
            f"Match: {'yes' if result.matches is True else 'no' if result.matches is False else 'n/a'}",
            "",
            result.message,
        ]
        self.result.setPlainText("\n".join(lines))

    @Slot(str)
    def _on_verify_error(self, message: str) -> None:
        self._finish_verification()
        self.result.setPlainText(f"Verification failed: {message}")

    def _finish_verification(self) -> None:
        self.progress.setVisible(False)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.verify_btn.setEnabled(bool(self._iso and self._iso.valid_selection))
        self.browse_btn.setEnabled(True)
