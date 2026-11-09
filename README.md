# WinMedia Linux

WinMedia Linux is a **Linux-native** desktop application for creating Windows installation media, inspired by Microsoft's Windows Media Creation Tool.

> **Status: Implementation complete (safety-gated)** — the GUI foundation, themes, logging, dependency checks, read-only USB detection, local ISO selection, SHA-256 verification, a resumable download engine (with explicit source-responsibility warnings), and **USB creation planning/validation** are implemented with tests. **Automatic official Microsoft ISO download resolution is not fully automated** (official-source policy enforced; no third-party substitution). **Destructive USB write execution is fail-closed/safety-gated** in this build and requires verified Linux hardware testing before enabling real disk writes. No devices are formatted/modified automatically. Bootability is **not claimed** without appropriate verification.

## Goals / implementation status

- **Official Windows ISO sources**: policy enforced (official Microsoft sources only; never silently substitute third-party ISOs). Automatic endpoint resolution is **not fully automated**; advanced explicit-URL download is available with prominent user-responsibility warnings.
- **Local ISO selection**: implemented.
- **SHA-256 verification**: local streaming calculation + optional user-provided checksum comparison implemented. Not a standalone authenticity proof.
- **USB device detection**: read-only Linux `lsblk`-based detection, safety flags, and review-only selection implemented (sysfs/transport properties; **not** inferred from `/dev/sdX` names).
- **Bootable USB creation**: planning/validation, explicit confirmation (type target device path), system-disk/identity/mount/read-only checks, and fail-closed guarded execution implemented. **Real destructive writes are safety-gated/not enabled in this build** pending verified Linux hardware testing. Large-WIM/FAT32 planning notes included. Bootability is **not claimed** without verification.

## Safety

WinMedia Linux is designed with data safety as a priority:

- The application does **not** run as root for normal startup.
- Future destructive disk operations will **never** run automatically.
- Users will see the selected device model/path/capacity and must give explicit confirmation before any format/write operation.
- System disks will be rejected by design.

## Requirements

- Python **3.11+**
- **PySide6** (Qt for Python)
- A graphical desktop session for normal use (X11/Wayland on Linux; Windows/macOS can run the Phase 1 UI for development)

Linux system tools (checked in Settings; needed in later phases): `lsblk`, `udisksctl`/UDisks2, `parted`, `blkid`, `mount`/`umount`, `wimlib-imagex` (wimtools).

## Installation (development)

```bash
# From the project root
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows PowerShell

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
# or editable install with dev tools:
python -m pip install -e .[dev]
```

## Launch

```bash
# If installed editable / scripts available:
winmedia

# Or directly:
python -m winmedia

# Smoke test (creates UI, exits automatically; useful for checks)
QT_QPA_PLATFORM=offscreen python -m winmedia --smoke-test  # Linux/headless
python -m winmedia --smoke-test                             # Windows/macOS
```

## Tests

```bash
python -m pytest
```

GUI smoke tests use `pytest-qt` and may run offscreen depending on the environment.

## Project layout

See `AGENTS.md` for the full development contract and architecture guidance. Source code lives under `src/winmedia/` with separation between `gui/`, `core/`, `services/`, and `utils/`.

## License

GPL-3.0-or-later (see `LICENSE`).
