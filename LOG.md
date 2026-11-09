# WinMedia Linux — Development Log

This log tracks what has been implemented, what is in progress, and what remains. It is updated frequently as work is completed and pushed to Git.

> **Safety contract**: follow `AGENTS.md`. No automatic disk formatting/writes, no root required for normal startup, no fake “complete” functionality, official Microsoft sources only for Windows downloads, and no claim of USB bootability without appropriate verification.

## Status summary (finalized 2026-11-09, safety-gated)

| Area | Status | Notes |
|---|---|---|
| Phase 1 Foundation | **Done** | Project structure, PySide6 GUI shell, sidebar nav, dark/light themes (dark default), structured logging, dependency checker, tests, docs. |
| Phase 2 USB detection | **Done (read-only)** | Linux `lsblk --json` scan, device info, safety flags, selection UI. Removable/USB hint from sysfs/transport, **never** from `/dev/sdX` name alone. No disk writes. Needs real Linux hardware validation. |
| Phase 3 ISO management | **Done (safety constraints apply)** | Local ISO selection/inspection, streaming SHA-256 calculation + optional expected-hash comparison, resumable HTTP(S) download engine/UI with explicit official-source/user-responsibility warnings. **Automatic official Microsoft endpoint resolution is not fully automated** (must remain official-only, no hardcoded expiring URLs, no third-party substitution). |
| Phase 4 Bootable USB | **Done (planning/guarded)** | Planning/validation, explicit confirmation (typed target path), system-disk/identity/mount/read-only checks, revalidation-aware design, and fail-closed guarded execution. **No automatic formatting/writing.** Real destructive writes are **not enabled** pending verified Linux hardware testing. Bootability **not claimed** without verification. |
| Phase 5 Polish/packaging | **Done (baseline)** | Docs/README/architecture updated, known limitations recorded, tests passing, venv workflow documented. |

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

### 2026-11-09 — Download engine (core)
- Implemented `core.downloader` (stdlib `urllib`, http/https only): `.part` temp file, resume via HTTP `Range` when supported, progress callback (bytes/total/speed), cancellation, timeouts, safe final rename. No official Microsoft URL resolution; callers must follow official-source policy.
- Added `tests/test_downloader.py` (mocked HTTP, no network).

### 2026-11-09 — Download UI integration (Phase 3 partial)
- Integrated advanced explicit-URL download in GUI with destination picker, source-responsibility confirmation, progress/speed/ETA, and cancel. **Warning labels state user must ensure URL is an official Microsoft source; not the automated official workflow.** Official auto-resolution remains unimplemented.
- Wrapped navigation pages in scroll areas for accessibility/polish.
- All 26 tests pass.

### 2026-11-09 — Phase 4 planning/guarded execution core (safety-first)
- Implemented planning/validation in `core.usb_manager`, `partition_manager`, `bootloader`, `wim_handler`: validates source ISO, target identity/path match, rejects system/critical mounts and read-only targets, surfaces warnings (mounts, non-removable hints, WIM/FAT32 constraints), builds human-readable plan steps.
- `execute_guarded()` is **fail-closed**: dry-run reports validation with no disk writes; non-dry-run execution is refused on non-Linux and by an explicit safety gate in this build (no destructive writes enabled without verified Linux hardware testing). No automatic formatting/writing.
- Added `tests/test_usb_manager.py` (planning, safety rejection, identity mismatch, dry-run, execution refusal). All 31 tests pass.

### 2026-11-09 — Phase 4 USB GUI + project completion (safety-gated)
- Integrated USB page: ISO selection, detected device selection, boot/scheme/FS options, plan preview (dry run), explicit confirmation by typing target device path, and guarded creation request. UI clearly states destructive execution is fail-closed/safety-gated.
- Updated README/architecture to reflect safety-gated completion, limitations (official Microsoft auto-download not fully automated; destructive writes not enabled pending verified Linux hardware testing; bootability not claimed).
- Full test suite: **31 passed** (`pytest -q`).

### 2026-11-09 — Finalized
- Working tree clean; full test suite **31 passed**; GUI smoke test passed.
- Project finalized in a **safety-gated** state: safe UI/detection/ISO/verification/planning workflows implemented; destructive USB execution and official bootability remain intentionally gated/unclaimed pending verified Linux hardware validation.

### 2026-11-09 — Release, docs, tracking, and maintenance
- **GitHub Release published**: `v0.1.0 - Safety-gated foundation release` created for existing tag `v0.1.0` on `ceuw/WinMedia-Linux` (https://github.com/ceuw/WinMedia-Linux/releases/tag/v0.1.0).
- **README rewritten** (`facd7ec`): professional GitHub presentation with accurate safety/status, limitations, usage, testing, layout, and disclaimer. Tests: **31 passed**.
- **GitHub issues created** (tracking known safety-gated work): [#1](https://github.com/ceuw/WinMedia-Linux/issues/1) verified official Microsoft ISO download resolution; [#2](https://github.com/ceuw/WinMedia-Linux/issues/2) guarded destructive USB creation on verified Linux hardware; [#3](https://github.com/ceuw/WinMedia-Linux/issues/3) boot/media verification workflow (no unverified bootability claims).
- **License changed to MIT** (`5b58dbf`): `LICENSE`, `pyproject.toml` metadata/classifier, and `README.md` updated. Historical `LOG.md` entry noting the original GPL notice was left unchanged for accuracy. Tests: **31 passed**.
- **Process/docs updated**: `AGENTS.md` reinforced to require **frequent `LOG.md` updates** and **very frequent pushes to GitHub**; `HANDOFF.md` and `LOG.md` refreshed to current repo/release/issue/license state.

## Maintenance (if continuing)

- Keep `LOG.md` and `HANDOFF.md` updated for any future changes and push frequently.
- Validate on real Linux hardware/disposable USB media before enabling any destructive execution path.
- Implement verified official Microsoft download endpoint resolution only if it can be done reliably and in compliance with source policy (no hardcoded expiring URLs, no third-party substitution).
- Add stronger post-write verification/boot checks when execution is implemented on Linux.
- Optional: shared app state across pages, packaging optimization (PySide6 footprint), deeper Linux integration tests.

## Known limitations / honesty notes

- **Official Microsoft download automation**: not fully automated. Must not hardcode temporary/unauthorized URLs or use third-party ISOs.
- **Destructive USB creation**: fail-closed/safety-gated in this build. **Real-world bootability and hardware behavior require validation on Linux with disposable media**. Do not claim success without appropriate verification.
- **Current dev environment**: Windows; Linux system tools/device behavior are partially simulated via mocks/checks.
- **PySide6 metapackage** pulls large Qt addons (WebEngine/PDF) in this environment; acceptable for dev, but packaging may be optimized later.
