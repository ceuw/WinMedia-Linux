# Architecture (safety-gated completion)

## Overview

WinMedia Linux uses a modular structure:

- `gui/` — PySide6 UI (windows, pages, styles). No disk/system side effects.
- `core/` — business logic for ISO, download, verification, and USB planning/execution guards.
- `services/` — system integration (dependency checks, read-only device detection, privilege stub).
- `utils/` — logging, paths, validators.

## Implemented

- App shell, sidebar navigation, dark/light themes (dark default), structured logging, dependency checker.
- **Read-only device detection** (`services.device_detection`): Linux `lsblk --json --bytes` parsing, safety flags (system/critical mounts, mounted partitions, read-only, removable/USB hints via sysfs/transport, never `/dev/sdX` name inference).
- **ISO management**: local selection/inspection; resumable HTTP(S) download engine (`urllib`, `.part` resume/progress/cancel); streaming SHA-256 calculation + optional expected-hash comparison with explicit non-authenticity messaging.
- **Phase 4 planning/guards** (`core.usb_manager` and helpers): request validation, device identity/mount/system-disk/read-only checks, WIM/FAT32/partition/boot planning notes, plan preview, explicit confirmation token (target path), and **fail-closed** `execute_guarded()` (dry-run ok; real destructive execution refused in this build pending verified Linux hardware testing).
- **GUI**: Download & Verify page (official auto-download not automated; advanced explicit-URL download with warnings/confirmation/progress), USB page (scan/select, plan preview, guarded creation request).

## Not fully enabled / limitations

- Automatic **official Microsoft** ISO endpoint resolution is not implemented. Official-source policy must be preserved.
- **Destructive disk writes** (partition/format/copy/boot setup) are not enabled by default; Linux tool execution requires verified hardware testing. Never claim bootability without verification.
- Linux device/runtime behavior requires validation on real Linux systems/disposable media.

## Safety boundaries

All disk operations must go through validated, explicitly confirmed, revalidated execution paths per `AGENTS.md`. No auto-format/write. No root for normal startup. No stored passwords.

## Safety boundaries

All future disk operations must go through a dedicated, validated layer with explicit user confirmation and device revalidation, per `AGENTS.md`.
