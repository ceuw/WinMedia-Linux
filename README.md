# WinMedia Linux

WinMedia Linux is a **Linux-native** desktop application for creating Windows installation media, inspired by Microsoft's Windows Media Creation Tool.

> **Status: Implementation complete (safety-gated)** — GUI, themes, logging, dependency checks, read-only USB detection, local ISO selection, SHA-256 verification, a resumable download engine (with explicit source-responsibility warnings), and USB creation planning/validation are implemented with tests. **Automatic official Microsoft ISO endpoint resolution is not fully automated** (official-source policy enforced; no third-party ISO substitution). **Destructive USB write execution is fail-closed/safety-gated** in this build and requires verified Linux hardware testing before enabling real disk writes. No devices are formatted or modified automatically. **Bootability is not claimed** without appropriate verification.

## Implementation status

- **Official Windows ISO sources**: official Microsoft sources only; never silently substitute third-party ISOs. Automatic endpoint resolution is **not fully automated**. Advanced explicit-URL download is available with prominent user-responsibility warnings and confirmation.
- **Local ISO selection**: implemented.
- **SHA-256 verification**: local streaming calculation + optional user-provided checksum comparison. A match does **not** by itself prove the image is an official Microsoft ISO.
- **USB device detection** (Linux): read-only `lsblk`-based detection, safety flags, and review-only selection. Removable/USB hints come from sysfs/transport properties — **never** inferred from `/dev/sdX` names alone.
- **Bootable USB creation**: planning/validation, explicit confirmation (type target device path), system-disk/identity/mount/read-only checks, and fail-closed guarded execution. Real destructive writes are **not enabled** in this build pending verified Linux hardware testing. Large-WIM/FAT32 planning notes are included.

## Safety

- The application does **not** run as root for normal startup.
- Destructive disk operations are **never** automatic.
- Before any future real write operation, the user must see device model/path/capacity and give explicit confirmation; the device must be revalidated.
- System disks and critical mount targets are rejected by design.
- See `AGENTS.md` for the full safety/development contract and `LOG.md` for progress/limitations.

## Requirements

- Python **3.11+**
- **PySide6** (Qt for Python)
- A graphical desktop session for normal use (X11/Wayland on Linux; Windows/macOS can run the UI for development/testing, but Linux is the target platform)

Linux system tools (reported in **Settings → Dependency check**): `lsblk`, `udisksctl`/UDisks2, `parted`, `blkid`, `mount`/`umount`, `wimlib-imagex` (wimtools). These are needed for Linux device detection and future USB operations.

## Installation (development)

```bash
# From the project root
python -m venv .venv

# Activate the virtual environment
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell:
# .\.venv\Scripts\Activate.ps1
# Windows cmd:
# .venv\Scripts\activate.bat

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
# or editable install with dev tools:
python -m pip install -e .[dev]
```

## Launch

```bash
# Recommended (works without editable scripts):
python -m winmedia

# If installed editable:
winmedia

# Smoke test (creates UI, exits automatically; useful for checks)
python -m winmedia --smoke-test
# Headless Linux (if supported by Qt):
QT_QPA_PLATFORM=offscreen python -m winmedia --smoke-test
```

## Tests

```bash
python -m pytest -q
```

GUI smoke tests use `pytest-qt` (offscreen where supported).

## Project layout

Source code lives under `src/winmedia/` with separation between `gui/`, `core/`, `services/`, and `utils/`. See `AGENTS.md` (development contract), `docs/architecture.md`, and `LOG.md`.

## License

GPL-3.0-or-later (see `LICENSE`).
