"""Tests for read-only device detection and safety assessment."""

from __future__ import annotations

import json

import pytest

from winmedia.services import device_detection
from winmedia.services.device_detection import (
    DeviceInfo,
    SafetyFlag,
    assess_device_safety,
    format_bytes,
    parse_lsblk_json,
    scan_devices,
)


SAMPLE_LSBLK = {
    "blockdevices": [
        {
            "name": "sda",
            "path": "/dev/sda",
            "type": "disk",
            "size": 256060514304,
            "rm": False,
            "hotplug": False,
            "ro": False,
            "tran": "sata",
            "vendor": "ACME",
            "model": "SYSTEM-SSD",
            "serial": "SYS123",
            "fstype": None,
            "pttype": "gpt",
            "ptuuid": "pt-sys",
            "mountpoint": None,
            "mountpoints": [None],
            "children": [
                {
                    "name": "sda1",
                    "path": "/dev/sda1",
                    "type": "part",
                    "size": 536870912,
                    "rm": False,
                    "fstype": "vfat",
                    "mountpoint": "/boot/efi",
                    "mountpoints": ["/boot/efi"],
                },
                {
                    "name": "sda2",
                    "path": "/dev/sda2",
                    "type": "part",
                    "size": 255523647488,
                    "rm": False,
                    "fstype": "ext4",
                    "mountpoint": "/",
                    "mountpoints": ["/"],
                },
            ],
        },
        {
            "name": "sdb",
            "path": "/dev/sdb",
            "type": "disk",
            "size": 16008609792,
            "rm": True,
            "hotplug": True,
            "ro": False,
            "tran": "usb",
            "vendor": "USB",
            "model": "FLASH-DRIVE",
            "serial": "USB999",
            "fstype": None,
            "pttype": "dos",
            "ptuuid": "pt-usb",
            "mountpoint": None,
            "mountpoints": [None],
            "children": [
                {
                    "name": "sdb1",
                    "path": "/dev/sdb1",
                    "type": "part",
                    "size": 16007561216,
                    "rm": True,
                    "fstype": "vfat",
                    "mountpoint": None,
                    "mountpoints": [None],
                }
            ],
        },
        {
            "name": "loop0",
            "path": "/dev/loop0",
            "type": "loop",
            "size": 12345,
            "rm": False,
        },
    ]
}


def test_format_bytes() -> None:
    assert format_bytes(0) == "0 B"
    assert "GiB" in format_bytes(16008609792)
    assert format_bytes(-1) == "unknown"


def test_parse_lsblk_json_filters_disks_and_collects_info() -> None:
    devices = parse_lsblk_json(json.dumps(SAMPLE_LSBLK))
    assert [d.name for d in devices] == ["sda", "sdb"]
    sys_disk = devices[0]
    assert "/" in sys_disk.mountpoints
    assert "/boot/efi" in sys_disk.mountpoints
    assert sys_disk.has_errors  # system mount points
    usb = devices[1]
    assert usb.is_removable is True
    assert usb.tran == "usb"
    assert usb.size_bytes == 16008609792
    assert "vfat" in usb.filesystems
    assert not usb.has_errors


def test_assess_device_safety_rejects_critical_mounts() -> None:
    dev = DeviceInfo(
        name="x", path="/dev/x", size_bytes=1, mountpoints=["/home/user", "/"]
    )
    flags = assess_device_safety(dev)
    assert any(f.code == "system-disk" and f.level == "error" for f in flags)


def test_assess_device_safety_warns_mounted_noncritical() -> None:
    dev = DeviceInfo(
        name="x",
        path="/dev/x",
        size_bytes=1,
        is_removable=True,
        tran="usb",
        mountpoints=["/media/usb"],
    )
    flags = assess_device_safety(dev)
    assert any(f.code == "mounted" and f.level == "warning" for f in flags)
    assert not any(f.code == "system-disk" for f in flags)


def test_assess_device_safety_read_only_error() -> None:
    dev = DeviceInfo(name="x", path="/dev/x", size_bytes=1, is_read_only=True)
    flags = assess_device_safety(dev)
    assert any(f.code == "read-only" and f.level == "error" for f in flags)


def test_removable_not_inferred_from_name() -> None:
    # Non-removable, non-USB transport: should NOT be treated as removable hint.
    dev = DeviceInfo(
        name="sdb", path="/dev/sdb", size_bytes=100, is_removable=False, tran="sata"
    )
    flags = assess_device_safety(dev)
    assert any(f.code == "not-removable" for f in flags)
    assert not any(f.code == "removable-hint" for f in flags)


def test_scan_devices_non_linux(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(device_detection.sys, "platform", "win32")
    result = scan_devices()
    assert not result.scanned
    assert result.errors
    assert "Linux" in result.errors[0]


def test_scan_devices_lsblk_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(device_detection.sys, "platform", "linux")
    monkeypatch.setattr(device_detection.shutil, "which", lambda _: None)
    result = scan_devices()
    assert not result.scanned
    assert any("lsblk" in e for e in result.errors)


def test_scan_devices_parses_mocked_lsblk(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(device_detection.sys, "platform", "linux")
    monkeypatch.setattr(device_detection.shutil, "which", lambda _: "/bin/lsblk")

    class Proc:
        returncode = 0
        stdout = json.dumps(SAMPLE_LSBLK)
        stderr = ""

    def fake_run(cmd, **kwargs):
        assert cmd[0] == "/bin/lsblk"
        assert "--json" in cmd
        assert "--bytes" in cmd
        assert kwargs.get("check") is False
        return Proc()

    monkeypatch.setattr(device_detection.subprocess, "run", fake_run)
    result = scan_devices()
    assert result.scanned
    assert not result.errors
    assert len(result.devices) == 2
    assert result.devices[1].is_removable is True
