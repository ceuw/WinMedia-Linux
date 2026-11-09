# Architecture (Phase 1–3 progress)

## Overview

WinMedia Linux uses a modular structure:

- `gui/` — PySide6 UI (windows, pages, styles). No disk/system side effects.
- `core/` — business logic for ISO/USB/verification (stubs; future implementation).
- `services/` — system integration (dependency checks, read-only device detection via Linux `lsblk`, privilege stub).
- `utils/` — logging, paths, validators.

## Current status

Implemented:
- Application shell, sidebar navigation, dark/light themes, dependency checker, structured logging.
- **Read-only device detection** (`services.device_detection`): parses `lsblk --json --bytes` on Linux, collects disk info (size, vendor/model, transport, partition table, filesystems, mount points), applies safety flags (reject/flag system/critical mounts, mounted partitions, read-only, non-removable hints). Removable/USB hints come from sysfs/transport fields, **never** from `/dev/sdX` names.
- **USB page UI**: refreshes scan off the UI thread, displays devices and safety details, allows selection for review only. The "Create installation media" action remains disabled.
- **ISO management/verification** (`core.iso_manager`, `core.verifier`): local ISO selection/inspection and streaming SHA-256 calculation in a worker. Optional comparison against a user-provided expected digest. Results clearly state local calculation and do not claim authenticity from hash alone.

Not implemented:
- Automatic official Microsoft ISO download resolution/workflow (must use official sources only when implemented; no third-party substitution).
- Partitioning, formatting, bootloader/media creation, WIM splitting, any destructive disk operations (Phase 4+).

## Safety boundaries

All future disk operations must go through a dedicated, validated layer with explicit user confirmation and device revalidation, per `AGENTS.md`. Detection/selection is informational only.

## Safety boundaries

All future disk operations must go through a dedicated, validated layer with explicit user confirmation and device revalidation, per `AGENTS.md`.
