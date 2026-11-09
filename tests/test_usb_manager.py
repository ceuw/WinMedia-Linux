"""Tests for USB creation planning/validation (non-destructive)."""

from pathlib import Path

from winmedia.core.usb_manager import UsbCreationRequest, execute_guarded, validate_request
from winmedia.services.device_detection import DeviceInfo, SafetyFlag


def _usb_device() -> DeviceInfo:
    dev = DeviceInfo(
        name="sdb",
        path="/dev/sdb",
        size_bytes=16_000_000_000,
        vendor="USB",
        model="Drive",
        serial="ABC",
        tran="usb",
        is_removable=True,
    )
    dev.flags = []
    return dev


def test_validate_request_ok(tmp_path: Path) -> None:
    iso = tmp_path / "win.iso"
    iso.write_bytes(b"iso")
    dev = _usb_device()
    req = UsbCreationRequest(
        source_iso=iso,
        target_device_path=dev.path,
        target_stable_id=dev.stable_id(),
        dry_run=True,
    )
    report = validate_request(req, dev)
    assert report.ok
    assert not report.errors
    assert report.confirmation_token == "/dev/sdb"


def test_validate_request_rejects_system_disk(tmp_path: Path) -> None:
    iso = tmp_path / "win.iso"
    iso.write_bytes(b"iso")
    dev = DeviceInfo(name="sda", path="/dev/sda", size_bytes=1, mountpoints=["/"])
    dev.flags = [SafetyFlag("error", "system-disk", "critical")]
    req = UsbCreationRequest(source_iso=iso, target_device_path="/dev/sda", target_stable_id=dev.stable_id())
    report = validate_request(req, dev)
    assert not report.ok
    assert any("critical" in e.lower() or "system" in e.lower() or "refusing" in e.lower() for e in report.errors)


def test_validate_request_rejects_identity_change(tmp_path: Path) -> None:
    iso = tmp_path / "win.iso"
    iso.write_bytes(b"iso")
    dev = _usb_device()
    req = UsbCreationRequest(
        source_iso=iso, target_device_path=dev.path, target_stable_id="wrong-id"
    )
    report = validate_request(req, dev)
    assert not report.ok
    assert any("identity changed" in e.lower() for e in report.errors)


def test_execute_guarded_dry_run(tmp_path: Path) -> None:
    iso = tmp_path / "win.iso"
    iso.write_bytes(b"iso")
    dev = _usb_device()
    req = UsbCreationRequest(
        source_iso=iso, target_device_path=dev.path, target_stable_id=dev.stable_id(), dry_run=True
    )
    ok, msg = execute_guarded(req, dev)
    assert ok
    assert "No disk operations performed" in msg or "dry run" in msg.lower()


def test_execute_guarded_refuses_execution(tmp_path: Path) -> None:
    iso = tmp_path / "win.iso"
    iso.write_bytes(b"iso")
    dev = _usb_device()
    req = UsbCreationRequest(
        source_iso=iso, target_device_path=dev.path, target_stable_id=dev.stable_id(), dry_run=False
    )
    ok, msg = execute_guarded(req, dev)
    # Fail-closed on non-Linux or by safety gate
    assert not ok
    assert "refused" in msg.lower() or "not enabled" in msg.lower() or "linux" in msg.lower()
