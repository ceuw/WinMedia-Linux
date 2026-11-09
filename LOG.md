# WinMedia Linux — Development Log

This log tracks what has been implemented, what is in progress, and what remains. It is updated frequently as work is completed and pushed to Git.

> **Safety contract**: follow `AGENTS.md`. No automatic disk formatting/writes, no root required for normal startup, no fake “complete” functionality, official Microsoft sources only for Windows downloads, and no claim of USB bootability without appropriate verification.

## Status summary (updated 2026-11-09)

| Area | Status | Notes |
|---|---|---|
| Phase 1 Foundation | **Done** | Project structure, PySide6 GUI shell, sidebar nav, dark/light themes (dark default), structured logging, dependency checker, tests, docs. |
| Phase 2 USB detection | **Done (read-only)** | Linux `lsblk --json` scan, device info, safety flags, selection UI. Removable/USB hint from sysfs/transport, **never** from `/dev/sdX` name alone. No disk writes. Needs real Linux hardware validation. |
| Phase 3 ISO management | **Partial → in progress** | Local ISO selection/inspection and streaming SHA-256 calculation + optional expected-hash comparison implemented. Generic/resumable download engine & UI integration planned; **automatic official Microsoft endpoint resolution is not fully automated** (must remain official-only, no hardcoded expiring URLs, no third-party substitution). |
| Phase 4 Bootable USB | **In progress (safety-first)** | Planning/validation architecture and guarded execution design to be implemented with strict confirmations, system-disk rejection, device revalidation, and Linux-tool checks. **No automatic formatting/writing.** Destructive execution requires explicit user confirmation and a supported Linux environment; mock-tested. |
| Phase 5 Polish/packaging | **Planned** | Final UX/error recovery notes, docs, packaging metadata verification. |

## Completed

### 2026-11-09 — Phase 1 (commit `28124b6`, pushed)
- Created `src`-layout package `winmedia` with `gui/`, `core/`, `services/`, `utils/`.
- Added `pyproject.toml`, `requirements.txt`, `.gitignore`, `LICENSE` (GPL-3.0-or-later notice), `README.md`, initial `docs/*`.
- Implemented modern PySide6 main window with sidebar navigation: Home, Download Windows, Create Bootable USB, Settings.
- Implemented dark/light QSS themes (dark default), responsive layout/cards/buttons.
- Implemented non-destructive dependency checker with Linux install hints; Settings runs checks off UI thread.
- Implemented structured logging and app path helpers.
- Added tests (`validators`, `dependency_checker`, `paths`, GUI smoke). Installed deps and verified startup/smoke test.

### 2026-11-09 — Phase 2 read-only detection (commit `3f4ea85`, pushed)
- Replaced device detection stub with read-only Linux `lsblk` scanner/parser and safety assessment.
- Flags system/critical mounts, mounted partitions, read-only devices, and non-removable/non-USB hints; uses sysfs/transport properties (not path names).
- Updated USB page with background refresh, device list/details, safety flags, and review-only selection. **Create action remains disabled (Phase 4).**
- Added `tests/test_device_detection.py`. All tests passing at time of commit (14 total).

### 2026-11-09 — Phase 3 partial: local ISO + SHA-256 (commit `0a17d22`, pushed)
- Implemented local ISO inspection (`core.iso_manager`) and streaming SHA-256 calculation/comparison (`core.verifier`).
- Updated Download page: local file selection, background hash calculation with progress, optional expected checksum comparison, explicit messaging that local hash ≠ authenticity proof. Official Microsoft auto-download remains not automated.
- Added `tests/test_iso_manager.py`, `tests/test_verifier.py`. All tests passing (22 total).
- Created `.venv` for development; tests verified in venv.

### 2026-11-09 — Logging/process
- Added this `LOG.md` to make progress explicit and support frequent updates/pushes.

## In progress / planned next (to finish responsibly)

1. **LOG maintenance** — update this file after each meaningful increment; commit/push frequently.
2. **Download engine (Phase 3)** — implement a safe HTTP downloader core: destination selection, resumable Range support where available, progress/speed/ETA, cancellation, timeout/error handling, temp/partial file handling. Integrate with UI. Keep **official Microsoft-only** policy explicit. If full official endpoint resolution is not verified/implemented, provide clear status and do not silently use unofficial sources; any user-supplied URL path (if added) must carry prominent warnings and never be presented as the official Microsoft workflow.
3. **Shared app state** — keep selected ISO/device state consistent across pages (non-destructive).
4. **Bootable USB planning/execution (Phase 4, safety-first)** — implement:
   - plan builder (source ISO, target device, partition/FS/boot mode options) with validation;
   - explicit confirmation UI showing model/path/capacity and exact planned actions;
   - system-disk/mount/critical checks and **revalidation immediately before execution**;
   - Linux-only guarded execution via external tools (`parted`, `mkfs.*`, `mount`, `umount`, `wimlib-imagex`/copy logic as appropriate) using argument arrays; privilege via system mechanisms where feasible — **no stored passwords**;
   - large `install.wim` handling plan (split for FAT32 when appropriate);
   - dry-run/preview and robust error reporting;
   - mock-based tests for planning/validation/command construction. **No destructive tests on real disks.** Real bootability requires Linux hardware verification (cannot be fully claimed from this Windows dev environment).
5. **Polish & docs** — finalize README/architecture/troubleshooting, record known limitations, ensure dependency/packaging metadata is coherent.
6. **Git discipline** — run relevant tests, commit meaningful increments, push to configured remote after each milestone/increment (reporting hash/branch/status/issues).

## Known limitations / honesty notes

- **Official Microsoft download automation**: not fully implemented. Must not hardcode temporary/unauthorized URLs or use third-party ISOs.
- **Destructive USB creation**: safety-critical and Linux-dependent. Implementation will be guarded and mock-tested, but **real-world bootability and hardware behavior require validation on Linux with disposable media**. This project must not claim success without appropriate verification.
- **Current dev environment**: Windows; Linux system tools/device behavior are partially simulated via mocks/checks.
- **PySide6 metapackage** pulls large Qt addons (WebEngine/PDF) in this environment; acceptable for dev, but packaging may be optimized later.
