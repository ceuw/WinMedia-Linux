# Architecture (Phase 1)

## Overview

WinMedia Linux uses a modular structure:

- `gui/` — PySide6 UI (windows, pages, styles). No disk/system side effects.
- `core/` — business logic for ISO/USB/verification (Phase 1: stubs).
- `services/` — system integration (dependency checks implemented; device detection/privilege stubs).
- `utils/` — logging, paths, validators.

## Phase 1 status

Implemented: application shell, sidebar navigation, dark/light themes, dependency checker, structured logging.
Not implemented: official ISO download, USB detection, partitioning/formatting, bootable media creation, verification workflows.

## Safety boundaries

All future disk operations must go through a dedicated, validated layer with explicit user confirmation and device revalidation, per `AGENTS.md`.
