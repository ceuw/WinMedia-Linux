# HANDOFF — WinMedia Linux (next session)

> **Start here.** Read `AGENTS.md` (project contract/safety rules), then `LOG.md` and this file. Do not enable destructive disk writes or claim bootability without verified Linux hardware testing.

## Repo / environment
- **Local path (this session):** `C:\Users\Ritam\Desktop\myApp`
- **Git:** `main` tracks `origin/main` — `https://github.com/ceuw/WinMedia-Linux.git` (HTTPS)
- **Current baseline:** safety-gated foundation; tests **31 passed** (`pytest -q`).
- **Release/tag:** `v0.1.0` tag exists on origin; **GitHub Release published** — https://github.com/ceuw/WinMedia-Linux/releases/tag/v0.1.0
- **GitHub issues (tracking):** [#1](https://github.com/ceuw/WinMedia-Linux/issues/1) official Microsoft ISO download resolution; [#2](https://github.com/ceuw/WinMedia-Linux/issues/2) guarded destructive USB creation on verified Linux hardware; [#3](https://github.com/ceuw/WinMedia-Linux/issues/3) boot/media verification workflow.
- **License:** MIT (`LICENSE`, `pyproject.toml`, `README.md`).
- **Dev environment used recently:** Windows + Python 3.14, PySide6, `.venv` at project root (gitignored). **Target platform is Linux.**

## Current state (safety-gated)
Implemented and test-verified:
- PySide6 app shell, sidebar navigation, dark/light themes, structured logging, dependency checker.
- **Read-only USB detection** (Linux `lsblk --json --bytes`): device info, safety flags, review-only selection. Removable/USB hints from sysfs/transport, **never** `/dev/sdX` name alone. No disk writes.
- **ISO management:** local ISO selection/inspection; resumable HTTP(S) downloader (`.part`/Range, progress/speed/ETA, cancel) with explicit source-responsibility warnings; streaming SHA-256 + optional expected-hash comparison with clear non-authenticity messaging.
- **USB creation planning (guarded):** validation, system-disk/identity/mount/read-only checks, WIM/FAT32/boot planning notes, explicit confirmation (type target device path), **fail-closed `execute_guarded()`**. **No automatic formatting/writing. Real destructive execution not enabled** in this build.
- **Docs:** professional `README.md`; `AGENTS.md` requires **frequent `LOG.md` updates** and **very frequent GitHub pushes**.

## Intentionally NOT done / safety gates (do not “fix” by making unsafe)
- **Automatic official Microsoft ISO endpoint resolution:** not fully automated. Must use official Microsoft sources only; no hardcoded expiring URLs; no third-party substitution. (Issue #1)
- **Destructive USB writes** (partition/format/copy/boot setup): **fail-closed/disabled** pending verified Linux hardware testing with disposable media. Never auto-format, never run without explicit confirmation + device revalidation + system-disk rejection. Use argument arrays (`subprocess.run`), no stored passwords. (Issue #2)
- **Bootability:** **not claimed** without appropriate verification on target hardware/firmware. (Issue #3)

## Run / test
```powershell
cd C:\Users\Ritam\Desktop\myApp
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m winmedia --smoke-test
.\.venv\Scripts\python.exe -m winmedia
```
Linux (target): use a venv, install deps, run on X11/Wayland; system tools reported in Settings.

## If continuing development
- Follow `AGENTS.md`: **update `LOG.md` frequently** and **push to GitHub very frequently** after each meaningful, tested checkpoint. Keep `HANDOFF.md` current.
- Run relevant tests; commit and `git push origin main` (report hash/branch/push status/issues).
- Validate detection and (if ever enabled) writes on **real Linux + disposable USB media** only. Keep destructive paths fail-closed until proven safe.
- Key files: `src/winmedia/services/device_detection.py`, `core/downloader.py`, `core/verifier.py`, `core/iso_manager.py`, `core/usb_manager.py` (+ partition/boot/wim helpers), `gui/*_page.py`, `tests/*`.
