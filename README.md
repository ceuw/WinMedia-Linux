# WinMedia Linux

WinMedia Linux is a **Linux-native** desktop application for creating Windows installation media, inspired by Microsoft's Windows Media Creation Tool.

> **Status: Phase 1 (Foundation)** — the GUI foundation, navigation, themes, logging, and dependency checks are implemented. **Windows ISO download and bootable USB creation are not implemented yet.** No USB devices are scanned, formatted, or modified in this phase.

## Goals

- Download **official** Windows 10/11 installation ISOs from Microsoft (planned).
- Create bootable Windows USB drives with UEFI/BIOS compatibility considerations (planned).
- Detect removable USB devices safely (planned).
- Handle large Windows installation files (e.g., FAT32 `install.wim` limits) using safe approaches (planned).
- Verify ISO integrity with SHA-256 (planned).

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
