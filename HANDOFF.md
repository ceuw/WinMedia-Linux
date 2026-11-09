# HANDOFF — WinMedia Linux (next session)

> **Start here.** Read `AGENTS.md` (project contract/safety rules), then `LOG.md` and this file. Do not enable destructive disk writes or claim bootability without verified Linux hardware testing.

## Repo / environment
- **Path (this session)**: `C:\Users\Ritam\Desktop\myApp`
- **Git**: repo on `main`, remote `origin` = `https://github.com/ceuw/WinMedia-Linux.git` (HTTPS). Commits pushed frequently.
- **Latest pushed commits (at handoff prep)**: `3b65b56 docs: fix and clarify README`, `bd7628c docs: finalize development log and project status`, plus prior feature commits (see `git log --oneline -10`).
- **Tag pushed**: `v0.1.0` (points to the v0.1.0 release commit; tag exists on origin). **GitHub Release object not created here** — `gh` was installed at `C:\Program Files\GitHub CLI\gh.exe` but `gh auth login` was required and interactive auth was not completed in this agent session.
- **Dev environment used**: Windows + Python 3.14, PySide6 6.12.0, `.venv` at project root (gitignored). Target platform is **Linux**.

## Current state (safety-gated, finalized baseline)
Implemented and test-verified (**31 pytest tests passing**; GUI smoke test OK):
- PySide6 app shell, sidebar nav, dark/light themes, structured logging, dependency checker.
- **Read-only USB detection** (Linux `lsblk --json --bytes`): device info, safety flags, review-only selection. Removable/USB hints from sysfs/transport, **never** `/dev/sdX` name alone. No disk writes.
- **ISO management**: local ISO selection/inspection; resumable HTTP(S) downloader (`.part`/Range, progress/speed/ETA, cancel) with explicit source-responsibility warnings; streaming SHA-256 + optional expected-hash comparison with clear non-authenticity messaging.
- **USB creation planning (guarded)**: validation, system-disk/identity/mount/read-only checks, WIM/FAT32/boot planning notes, explicit confirmation (type target device path), **fail-closed `execute_guarded()`**. **No automatic formatting/writing. Real destructive execution not enabled** in this build.

## Intentionally NOT done / safety gates (do not “fix” by making unsafe)
- **Automatic official Microsoft ISO endpoint resolution**: not fully automated. Must use official Microsoft sources only; no hardcoded expiring URLs; no third-party substitution.
- **Destructive USB writes** (partition/format/copy/boot setup): **fail-closed/disabled** pending verified Linux hardware testing with disposable media. Never auto-format, never run without explicit confirmation + device revalidation + system-disk rejection. Use argument arrays (`subprocess.run`), no stored passwords.
- **Bootability**: **not claimed** without appropriate verification on target hardware/firmware.

## Run / test
```powershell
cd C:\Users\Ritam\Desktop\myApp
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m winmedia --smoke-test
.\.venv\Scripts\python.exe -m winmedia
```
Linux (target): use a venv, install deps, run on X11/Wayland; system tools reported in Settings.

## Pending user/admin action
1. **GitHub Release**: tag `v0.1.0` is pushed. After `gh auth login`, create the release:
   ```powershell
   & "C:\Program Files\GitHub CLI\gh.exe" auth login
   & "C:\Program Files\GitHub CLI\gh.exe" release create v0.1.0 --repo ceuw/WinMedia-Linux --title "v0.1.0 — Safety-gated foundation release" --notes-file "C:\Users\Ritam\AppData\Local\Temp\opencode\winmedia-release-notes.md"
   ```
   (Regenerate notes from README/LOG if the temp file is gone; keep safety limitations explicit.)

## If continuing development
- Update `LOG.md` + `HANDOFF.md` after meaningful work; run relevant tests; commit and `git push origin main` (report hash/branch/push status/issues per `AGENTS.md`).
- Validate detection and (if ever enabled) writes on **real Linux + disposable USB media** only. Keep destructive paths fail-closed until proven safe.
- Key files: `src/winmedia/services/device_detection.py`, `core/downloader.py`, `core/verifier.py`, `core/iso_manager.py`, `core/usb_manager.py` (+ partition/boot/wim helpers), `gui/*_page.py`, `tests/*`.
