"""Create bootable USB page (Phase 2 detection + Phase 4 guarded planning UI)."""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, Qt, QThreadPool, Signal, Slot
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from winmedia.core.iso_manager import inspect_iso
from winmedia.core.usb_manager import UsbCreationRequest, execute_guarded, validate_request
from winmedia.services.device_detection import DeviceInfo, ScanResult, scan_devices

logger = logging.getLogger(__name__)


class _ScanSignals(QObject):
    finished = Signal(object)
    error = Signal(str)


class _ScanWorker(QRunnable):
    """Scan devices off the UI thread (read-only)."""

    def __init__(self) -> None:
        super().__init__()
        self.signals = _ScanSignals()

    @Slot()
    def run(self) -> None:
        try:
            result = scan_devices()
            try:
                self.signals.finished.emit(result)
            except RuntimeError:
                logger.debug("Scan worker finished after UI teardown")
        except Exception as exc:  # pragma: no cover
            logger.exception("Device scan failed")
            try:
                self.signals.error.emit(str(exc))
            except RuntimeError:
                logger.debug("Scan worker error signal skipped after UI teardown")


class UsbPage(QWidget):
    """Device detection/selection and guarded USB creation planning. No auto writes."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._pool = QThreadPool.globalInstance()
        self._devices: list[DeviceInfo] = []
        self._selected: DeviceInfo | None = None
        self._iso_path: Path | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(14)

        title = QLabel("Create Bootable USB")
        title.setProperty("class", "title")
        subtitle = QLabel(
            "Read-only device detection is available. Creation planning requires explicit "
            "confirmation and is safety-gated; destructive writes are not auto-executed."
        )
        subtitle.setProperty("class", "subtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(self._build_detection_card())
        layout.addWidget(self._build_plan_card(), 1)

    def _build_detection_card(self) -> QFrame:
        card = QFrame()
        card.setProperty("class", "card")
        l = QVBoxLayout(card)
        l.setContentsMargins(16, 16, 16, 16)
        l.setSpacing(10)
        top = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh devices")
        self.refresh_btn.setProperty("class", "secondary")
        self.refresh_btn.clicked.connect(self.refresh_devices)
        self.status = QLabel("No scan performed yet.")
        self.status.setProperty("class", "muted")
        self.status.setWordWrap(True)
        top.addWidget(self.refresh_btn, 0, Qt.AlignLeft)
        top.addWidget(self.status, 1)
        content = QHBoxLayout()
        content.setSpacing(12)
        self.list = QListWidget()
        self.list.itemSelectionChanged.connect(self._on_selection_changed)
        self.details = QLabel("Select a device to view details (read-only).")
        self.details.setProperty("class", "muted")
        self.details.setWordWrap(True)
        self.details.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.details.setTextInteractionFlags(Qt.TextSelectableByMouse)
        left = QVBoxLayout()
        lt = QLabel("Detected disks")
        lt.setProperty("class", "section")
        left.addWidget(lt)
        left.addWidget(self.list, 1)
        right = QVBoxLayout()
        rt = QLabel("Device details & safety")
        rt.setProperty("class", "section")
        right.addWidget(rt)
        right.addWidget(self.details, 1)
        content.addLayout(left, 2)
        content.addLayout(right, 3)
        l.addLayout(top)
        l.addLayout(content)
        return card

    def _build_plan_card(self) -> QFrame:
        card = QFrame()
        card.setProperty("class", "card")
        l = QVBoxLayout(card)
        l.setContentsMargins(16, 16, 16, 16)
        l.setSpacing(8)
        t = QLabel("Creation plan (guarded)")
        t.setProperty("class", "section")
        warn = QLabel(
            "Safety: this will ERASE the selected target when executed on a supported Linux system. "
            "WinMedia never formats automatically. You must review the plan and type the target "
            "device path to confirm. Destructive execution is fail-closed/safety-gated in this build."
        )
        warn.setProperty("class", "muted")
        warn.setWordWrap(True)

        iso_row = QHBoxLayout()
        self.iso_edit = QLineEdit()
        self.iso_edit.setPlaceholderText("Source Windows ISO path")
        self.iso_edit.textChanged.connect(self._on_iso_changed)
        iso_browse = QPushButton("Browse ISO...")
        iso_browse.setProperty("class", "secondary")
        iso_browse.clicked.connect(self.browse_iso)
        iso_row.addWidget(self.iso_edit, 1)
        iso_row.addWidget(iso_browse)

        opts = QHBoxLayout()
        opts.setSpacing(8)
        self.boot_combo = QComboBox()
        self.boot_combo.addItems(["UEFI", "Legacy", "Hybrid (best-effort)"])
        self.scheme_combo = QComboBox()
        self.scheme_combo.addItems(["GPT", "MBR"])
        self.fs_combo = QComboBox()
        self.fs_combo.addItems(["FAT32", "NTFS"])
        opts.addWidget(QLabel("Boot:"))
        opts.addWidget(self.boot_combo)
        opts.addWidget(QLabel("Scheme:"))
        opts.addWidget(self.scheme_combo)
        opts.addWidget(QLabel("FS:"))
        opts.addWidget(self.fs_combo)
        opts.addStretch(1)

        confirm_row = QHBoxLayout()
        self.confirm_edit = QLineEdit()
        self.confirm_edit.setPlaceholderText("Type target device path to confirm (e.g., /dev/sdb)")
        confirm_row.addWidget(QLabel("Confirm target:"))
        confirm_row.addWidget(self.confirm_edit, 1)

        btns = QHBoxLayout()
        self.preview_btn = QPushButton("Preview plan (dry run)")
        self.preview_btn.setProperty("class", "secondary")
        self.preview_btn.clicked.connect(self.preview_plan)
        self.create_btn = QPushButton("Request creation (guarded)")
        self.create_btn.setProperty("class", "primary")
        self.create_btn.clicked.connect(self.request_creation)
        self.create_btn.setToolTip(
            "Requires valid plan + explicit confirmation. Destructive execution is safety-gated."
        )
        btns.addWidget(self.preview_btn)
        btns.addWidget(self.create_btn)
        btns.addStretch(1)

        self.plan_output = QPlainTextEdit()
        self.plan_output.setReadOnly(True)
        self.plan_output.setPlaceholderText("Plan preview/results will appear here.")
        self.plan_output.setMaximumBlockCount(4000)

        l.addWidget(t)
        l.addWidget(warn)
        l.addLayout(iso_row)
        l.addLayout(opts)
        l.addLayout(confirm_row)
        l.addLayout(btns)
        l.addWidget(self.plan_output, 1)
        return card

    @Slot()
    def browse_iso(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Windows ISO", str(Path.home()), "ISO images (*.iso);;All files (*)"
        )
        if path:
            self.iso_edit.setText(path)

    @Slot()
    def _on_iso_changed(self, text: str) -> None:
        p = Path(text).expanduser() if text.strip() else None
        self._iso_path = p if p and p.exists() and p.is_file() else None

    @Slot()
    def refresh_devices(self) -> None:
        self.refresh_btn.setEnabled(False)
        self.status.setText("Scanning devices (read-only)...")
        self.list.clear()
        self._devices = []
        self._selected = None
        self._render_details(None)
        worker = _ScanWorker()
        worker.signals.finished.connect(self._on_scan_finished)
        worker.signals.error.connect(self._on_scan_error)
        self._pool.start(worker)

    @Slot(object)
    def _on_scan_finished(self, result: ScanResult) -> None:
        self.refresh_btn.setEnabled(True)
        if result.errors and not result.devices:
            self.status.setText(result.errors[0])
            return
        self._devices = result.devices
        for dev in self._devices:
            flags = " [safety/error]" if dev.has_errors else (" [warning]" if dev.has_warnings else "")
            item = QListWidgetItem(f"{dev.display_name} — {dev.size_human}{flags}")
            item.setData(Qt.UserRole, dev.stable_id())
            self.list.addItem(item)
        self.status.setText(
            f"Found {len(self._devices)} disk device(s). Read-only scan." if self._devices else "No disk devices found."
        )

    @Slot(str)
    def _on_scan_error(self, message: str) -> None:
        self.refresh_btn.setEnabled(True)
        self.status.setText(f"Scan failed: {message}")

    def _on_selection_changed(self) -> None:
        items = self.list.selectedItems()
        if not items:
            self._selected = None
            self._render_details(None)
            return
        stable = items[0].data(Qt.UserRole)
        dev = next((d for d in self._devices if d.stable_id() == stable), None)
        self._selected = dev
        self._render_details(dev)

    def _render_details(self, dev: DeviceInfo | None) -> None:
        if dev is None:
            self.details.setText("Select a device to view details (read-only).")
            return
        lines = [
            f"<b>Device</b>: {dev.display_name}",
            f"<b>Path</b>: {dev.path}",
            f"<b>Size</b>: {dev.size_human}",
            f"<b>Transport/removable hint</b>: {dev.tran or 'unknown'} / {'yes' if dev.is_removable else 'no'} (sysfs/transport, not path name)",
            f"<b>Mounts</b>: {', '.join(dev.mountpoints) if dev.mountpoints else 'none'}",
            "<b>Flags</b>:",
        ]
        for f in dev.flags:
            lines.append(f"- [{f.level}] {f.message}")
        self.details.setText("<br>".join(lines))

    def _current_request(self, dry_run: bool) -> UsbCreationRequest | None:
        iso_text = self.iso_edit.text().strip()
        if not iso_text:
            return None
        iso = Path(iso_text).expanduser()
        boot = {"UEFI": "uefi", "Legacy": "legacy", "Hybrid (best-effort)": "hybrid"}.get(
            self.boot_combo.currentText(), "uefi"
        )
        return UsbCreationRequest(
            source_iso=iso,
            target_device_path=self._selected.path if self._selected else "",
            target_stable_id=self._selected.stable_id() if self._selected else "",
            boot_mode=boot,
            partition_scheme=self.scheme_combo.currentText().lower(),
            filesystem=self.fs_combo.currentText().lower(),
            dry_run=dry_run,
        )

    def _show_report(self, header: str, ok: bool, msg: str, report=None) -> None:
        parts = [header, msg]
        if report:
            if report.warnings:
                parts.append("\nWarnings:\n- " + "\n- ".join(report.warnings))
            if report.errors:
                parts.append("\nErrors:\n- " + "\n- ".join(report.errors))
            if report.steps:
                parts.append("\nPlan:\n- " + "\n- ".join(report.steps))
        self.plan_output.setPlainText("\n".join(parts))

    @Slot()
    def preview_plan(self) -> None:
        req = self._current_request(dry_run=True)
        if not req:
            self.plan_output.setPlainText("Select a source ISO and target device first.")
            return
        report = validate_request(req, self._selected)
        ok, msg = execute_guarded(req, self._selected)
        self._show_report("DRY RUN / PREVIEW", ok, msg, report)

    @Slot()
    def request_creation(self) -> None:
        req = self._current_request(dry_run=False)
        if not req:
            QMessageBox.warning(self, "Missing information", "Select a source ISO and target device.")
            return
        report = validate_request(req, self._selected)
        if not report.ok:
            self._show_report("VALIDATION FAILED", False, "Cannot proceed.", report)
            return
        typed = self.confirm_edit.text().strip()
        if typed != req.target_device_path:
            QMessageBox.warning(
                self,
                "Confirmation required",
                f"To proceed, type the exact target device path: {req.target_device_path}\n"
                "This confirms you understand the selected device may be erased by a real execution.",
            )
            return
        detail = (
            f"Target: {self._selected.display_name if self._selected else req.target_device_path}\n"
            f"Path: {req.target_device_path}\n"
            f"Size: {self._selected.size_human if self._selected else 'unknown'}\n"
            f"Source ISO: {req.source_iso}\n\n"
            "This requests guarded creation. Destructive execution is fail-closed in this build "
            "(no disk writes without verified Linux hardware testing). Continue?"
        )
        reply = QMessageBox.critical(
            self, "Confirm USB creation request", detail,
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        ok, msg = execute_guarded(req, self._selected)
        self._show_report("CREATION REQUEST (GUARDED)", ok, msg, report)
        if not ok:
            QMessageBox.information(self, "Safety gate", msg)
