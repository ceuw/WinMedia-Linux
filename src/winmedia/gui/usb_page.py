"""Create bootable USB page (Phase 2 detection UI; Phase 4 creation not implemented)."""

from __future__ import annotations

import logging

from PySide6.QtCore import QObject, QRunnable, Qt, QThreadPool, Signal, Slot
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

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
    """Device detection/selection UI. No disk operations are performed."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._pool = QThreadPool.globalInstance()
        self._devices: list[DeviceInfo] = []
        self._selected: DeviceInfo | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        title = QLabel("Create Bootable USB")
        title.setProperty("class", "title")
        subtitle = QLabel(
            "Detect removable storage devices (read-only). Bootable USB creation is "
            "not implemented yet — no devices are formatted or modified."
        )
        subtitle.setProperty("class", "subtitle")
        subtitle.setWordWrap(True)

        top = QHBoxLayout()
        top.setSpacing(10)
        self.refresh_btn = QPushButton("Refresh devices")
        self.refresh_btn.setProperty("class", "secondary")
        self.refresh_btn.clicked.connect(self.refresh_devices)
        self.status = QLabel("No scan performed yet.")
        self.status.setProperty("class", "muted")
        self.status.setWordWrap(True)
        top.addWidget(self.refresh_btn, 0, Qt.AlignLeft)
        top.addWidget(self.status, 1)

        content = QHBoxLayout()
        content.setSpacing(14)

        list_card = QFrame()
        list_card.setProperty("class", "card")
        list_layout = QVBoxLayout(list_card)
        list_layout.setContentsMargins(16, 16, 16, 16)
        list_layout.setSpacing(10)
        list_title = QLabel("Detected disks")
        list_title.setProperty("class", "section")
        self.list = QListWidget()
        self.list.itemSelectionChanged.connect(self._on_selection_changed)
        list_layout.addWidget(list_title)
        list_layout.addWidget(self.list, 1)

        detail_card = QFrame()
        detail_card.setProperty("class", "card")
        detail_layout = QVBoxLayout(detail_card)
        detail_layout.setContentsMargins(16, 16, 16, 16)
        detail_layout.setSpacing(10)
        detail_title = QLabel("Device details & safety")
        detail_title.setProperty("class", "section")
        self.details = QLabel(
            "Select a device to view details. Detection uses system-reported "
            "properties (not /dev/sdX names). This is read-only."
        )
        self.details.setProperty("class", "muted")
        self.details.setWordWrap(True)
        self.details.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.details.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.create_btn = QPushButton("Create installation media")
        self.create_btn.setProperty("class", "primary")
        self.create_btn.setEnabled(False)
        self.create_btn.setToolTip(
            "Disabled: bootable USB creation is not implemented (Phase 4). "
            "No disk operations are performed."
        )
        safety_note = QLabel(
            "Safety: future creation will require explicit confirmation, show "
            "model/path/capacity, reject system disks, and revalidate the device "
            "before any destructive operation."
        )
        safety_note.setProperty("class", "muted")
        safety_note.setWordWrap(True)
        detail_layout.addWidget(detail_title)
        detail_layout.addWidget(self.details, 1)
        detail_layout.addWidget(self.create_btn, 0, Qt.AlignLeft)
        detail_layout.addWidget(safety_note)

        content.addWidget(list_card, 2)
        content.addWidget(detail_card, 3)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addLayout(top)
        layout.addLayout(content, 1)

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
        if not self._devices:
            self.status.setText("No disk devices found.")
            return
        for dev in self._devices:
            flags = []
            if dev.has_errors:
                flags.append("safety/error")
            elif dev.has_warnings:
                flags.append("warning")
            label = f"{dev.display_name} — {dev.size_human}"
            if flags:
                label += f" [{', '.join(flags)}]"
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, dev.stable_id())
            self.list.addItem(item)
        extra = f" ({len(result.errors)} issue(s))" if result.errors else ""
        self.status.setText(f"Found {len(self._devices)} disk device(s){extra}. Read-only scan.")

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
            self.details.setText(
                "Select a device to view details. Detection uses system-reported "
                "properties (not /dev/sdX names). This is read-only."
            )
            return
        lines = [
            f"<b>Name</b>: {dev.display_name}",
            f"<b>Path</b>: {dev.path}",
            f"<b>Size</b>: {dev.size_human} ({dev.size_bytes} bytes)",
            f"<b>Transport</b>: {dev.tran or 'unknown'}",
            f"<b>Removable/USB hint</b>: {'yes' if dev.is_removable else 'no'} (sysfs/transport, not path name)",
            f"<b>Read-only</b>: {'yes' if dev.is_read_only else 'no'}",
            f"<b>Partition table</b>: {dev.pttype or 'unknown'}",
            f"<b>Filesystems</b>: {', '.join(dev.filesystems) if dev.filesystems else 'none detected'}",
            f"<b>Mount points</b>: {', '.join(dev.mountpoints) if dev.mountpoints else 'none'}",
            "",
            "<b>Safety/validation flags</b>:",
        ]
        if dev.flags:
            for f in dev.flags:
                lines.append(f"- [{f.level}] {f.message}")
        else:
            lines.append("- No flags.")
        lines.append("")
        lines.append(
            "<i>Selection is for review only. 'Create installation media' is disabled "
            "(Phase 4 not implemented). No disk operations are performed.</i>"
        )
        self.details.setText("<br>".join(lines))
