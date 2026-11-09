"""Windows ISO download/selection and verification page (Phase 3 partial)."""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, Qt, QThreadPool, Signal, Slot
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from winmedia.core.iso_manager import IsoInfo, inspect_iso
from winmedia.core.verifier import VerificationResult, normalize_sha256, verify_sha256

logger = logging.getLogger(__name__)


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


class DownloadPage(QWidget):
    """ISO selection and local SHA-256 verification; official download not automated."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._pool = QThreadPool.globalInstance()
        self._iso: IsoInfo | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(14)

        title = QLabel("Download & Verify Windows ISO")
        title.setProperty("class", "title")
        subtitle = QLabel(
            "Select a local Windows ISO and calculate its SHA-256. "
            "Automatic official Microsoft download resolution is not implemented yet."
        )
        subtitle.setProperty("class", "subtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        layout.addWidget(self._build_official_card())
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
            "resolve fresh/expiring links as needed, show progress, support resumable downloads "
            "where available, and never substitute third-party ISOs. Automatic resolution is "
            "not wired up in this build."
        )
        msg.setProperty("class", "muted")
        msg.setWordWrap(True)
        btn = QPushButton("Check for official downloads")
        btn.setProperty("class", "primary")
        btn.setEnabled(False)
        btn.setToolTip("Disabled: official download workflow is not implemented.")
        l.addLayout(head)
        l.addWidget(msg)
        l.addWidget(btn, 0, Qt.AlignLeft)
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
            "Calculates a local SHA-256 digest. You may optionally paste an expected "
            "checksum (64 hex chars) from a trusted source. A match does not by itself "
            "prove the image is an official Microsoft ISO."
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
        self.progress.setTextVisible(True)
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
    def browse_iso(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Windows ISO",
            str(Path.home()),
            "ISO images (*.iso);;All files (*)",
        )
        if not path:
            return
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
        self.progress.setRange(0, 0)  # indeterminate until we know total
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
