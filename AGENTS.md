# AGENTS.md

# WinMedia Linux — AI Agent Instructions

## 1. Project Overview

**Project Name:** WinMedia Linux  
**Purpose:** Build a Linux-native application that provides functionality similar to Microsoft's Windows Media Creation Tool.

WinMedia Linux enables users to:

- Download official Windows installation ISOs.
- Create bootable Windows USB installation drives.
- Automatically detect removable USB storage devices.
- Prepare USB drives for UEFI and Legacy BIOS installation.
- Handle Windows installation files larger than FAT32's 4GB file limit.
- Verify ISO integrity using SHA-256 checksums.
- Provide a simple, beginner-friendly graphical interface.

The application must work natively on Linux without requiring Wine, Windows, or a virtual machine.

## 2. Core Development Principles

All AI coding agents must follow these principles:

1. Prioritize reliability and data safety.
2. Keep the application Linux-native.
3. Prefer simple, maintainable implementations.
4. Never execute destructive disk operations without explicit user confirmation.
5. Never silently format or overwrite a storage device.
6. Use official Microsoft sources for Windows installation downloads.
7. Never distribute modified or unauthorized Windows installation images.
8. Keep the GUI responsive during downloads and disk operations.
9. Provide clear progress indicators and meaningful error messages.
10. Document important architectural decisions.

## 3. Technology Stack

### Primary Language
- Python 3.11+

### GUI Framework
- PySide6 (Qt)

### System Integration
- UDisks2
- udisksctl
- lsblk
- blkid
- parted
- util-linux
- mount / umount

### ISO and File Processing
- Python hashlib
- Python requests or httpx
- Python subprocess
- Python pathlib
- wimlib-imagex (for WIM splitting where appropriate)

### Testing
- pytest
- pytest-qt
- unittest.mock

### Packaging
- PyInstaller (optional)
- AppImage (optional)
- Debian packages
- RPM packages

Do not assume every dependency is installed. Detect missing dependencies and explain how to install them.

## 4. Suggested Project Structure

Maintain a modular architecture.

```text
winmedia-linux/
├── AGENTS.md
├── README.md
├── LICENSE
├── pyproject.toml
├── requirements.txt
│
├── src/
│   └── winmedia/
│       ├── __init__.py
│       ├── main.py
│       │
│       ├── core/
│       │   ├── downloader.py
│       │   ├── iso_manager.py
│       │   ├── usb_manager.py
│       │   ├── partition_manager.py
│       │   ├── bootloader.py
│       │   ├── wim_handler.py
│       │   └── verifier.py
│       │
│       ├── gui/
│       │   ├── main_window.py
│       │   ├── download_page.py
│       │   ├── usb_page.py
│       │   ├── progress_page.py
│       │   ├── settings_page.py
│       │   └── styles.py
│       │
│       ├── services/
│       │   ├── device_detection.py
│       │   ├── privilege_manager.py
│       │   └── dependency_checker.py
│       │
│       └── utils/
│           ├── logging_config.py
│           ├── validators.py
│           └── paths.py
│
├── tests/
│   ├── test_downloader.py
│   ├── test_usb_manager.py
│   ├── test_iso_manager.py
│   └── test_verifier.py
│
├── assets/
│   ├── icons/
│   └── images/
│
└── docs/
    ├── architecture.md
    ├── installation.md
    └── troubleshooting.md
```

Agents may adjust this structure when necessary, but must preserve clear separation between GUI, business logic, and system operations.

## 5. Functional Requirements

### 5.1 Windows ISO Downloader

Implement a downloader that:

- Supports Windows 10 and Windows 11 where official downloads remain available.
- Uses official Microsoft download endpoints.
- Supports resumable downloads when the source permits HTTP range requests.
- Displays download progress, speed, and estimated remaining time.
- Validates downloaded files.
- Handles expired download URLs.
- Allows users to select a download destination.
- Never silently substitutes third-party ISO sources.

Microsoft download URLs can expire. Resolve fresh official download links when needed instead of hardcoding temporary URLs.

### 5.2 USB Device Detection

Implement automatic USB detection.

Display:

- Device name.
- Manufacturer and model, when available.
- Total capacity.
- Available filesystem.
- Mount status.
- Device path.
- Removable-device status.

Use stable device identifiers where possible.

Do not identify a device as removable based solely on its `/dev/sdX` name.

### 5.3 Bootable USB Creation

Support:

- UEFI booting.
- Legacy BIOS booting where technically supported.
- GPT partitioning.
- MBR partitioning.
- FAT32.
- NTFS-based installation media where necessary.

The application should select an appropriate configuration based on user preferences and compatibility.

### 5.4 Windows Large File Handling

FAT32 cannot store individual files larger than 4GB.

Implement safe handling for oversized Windows installation files.

Preferred approach:

- Detect oversized `install.wim` files.
- Split them into `.swm` segments using `wimlib-imagex` when appropriate.
- Preserve the original Windows installation files.
- Verify the resulting segments.
- Ensure Windows Setup can recognize the split installation image.

Alternative boot-media approaches may be considered for NTFS and UEFI compatibility.

Never assume that copying an ISO's contents to a USB drive automatically produces a bootable Windows installer.

### 5.5 ISO Verification

Implement SHA-256 verification.

- Calculate the SHA-256 digest of downloaded ISOs.
- Compare it with a trusted checksum when Microsoft provides one.
- Clearly distinguish between a locally calculated checksum and an independently verified official checksum.
- Never claim that an ISO is authentic solely because a hash was calculated.

### 5.6 GUI Requirements

The application must have a modern, polished interface.

Design goals:

- Simple navigation.
- Dark and light themes.
- Clear typography.
- Large, understandable controls.
- Responsive progress indicators.
- USB device selection.
- Download progress.
- Operation summaries.
- Friendly error messages.

Avoid clutter and unnecessary technical terminology.

The GUI must remain responsive during all long-running operations.

Use Qt worker threads or appropriate asynchronous execution.

## 6. Critical Disk Safety Rules

These rules are mandatory.

1. Never format a disk automatically.
2. Never overwrite a device without explicit confirmation.
3. Display the selected device model, path, and capacity before destructive operations.
4. Never assume `/dev/sda` is a USB device.
5. Reject system disks and mounted root filesystems.
6. Check mounted partitions before beginning disk operations.
7. Revalidate the device immediately before writing.
8. Handle device disconnection safely.
9. Avoid shell command construction using unsanitized user input.
10. Prefer argument arrays with `subprocess.run()` over shell execution.
11. Do not run the entire application as root.
12. Request elevated permissions only for the operations that need them.
13. Clearly communicate that creating installation media erases the selected USB drive.
14. Log failures without exposing sensitive user information.

Use a separate disk-operation layer with explicit validation and confirmation.

## 7. Privilege Management

Do not require root privileges for normal application startup.

Use Linux authorization mechanisms such as:

- UDisks2.
- Polkit.
- Authorized system utilities.

Never store administrator passwords.

Never attempt to bypass system security policies.

If elevated privileges are unavailable, explain the issue and provide a safe recovery path.

## 8. Error Handling

Handle at least these situations:

- Internet unavailable.
- Microsoft download URL expired.
- Download interrupted.
- Insufficient disk space.
- Corrupted ISO.
- USB device disconnected.
- USB device mounted.
- Unsupported partition layout.
- Missing dependencies.
- Permission denied.
- Formatting failure.
- File-copy failure.
- WIM splitting failure.
- Verification mismatch.

All exceptions must be handled appropriately.

Provide actionable error messages instead of exposing raw tracebacks to normal users.

Keep detailed diagnostic information in application logs.

## 9. Testing Requirements

Every major component must have tests.

Prioritize:

- ISO download handling.
- Interrupted download recovery.
- SHA-256 calculation.
- Device identification.
- Partition-layout validation.
- Large WIM file handling.
- Privilege-management behavior.
- Error handling.

Never perform destructive testing on real user disks.

Use mocks, temporary files, loop devices, and disposable virtual disks.

## 10. Coding Standards

- Follow PEP 8.
- Use type hints.
- Use meaningful function and variable names.
- Add docstrings to public classes and functions.
- Keep functions focused.
- Avoid unnecessary dependencies.
- Use pathlib for filesystem paths.
- Use structured logging.
- Never commit credentials, tokens, or personal information.
- Do not duplicate existing functionality.
- Keep dependencies documented.

Prefer readable code over clever abstractions.

## 11. Development Workflow

Before implementing a feature:

1. Inspect the existing project.
2. Read this AGENTS.md file.
3. Understand the existing architecture.
4. Identify affected components.
5. Plan the implementation.
6. Implement incrementally.
7. Add or update tests.
8. Run the relevant test suite.
9. Update documentation.

Do not rewrite functioning components without a clear reason.

Do not introduce unnecessary architectural complexity.

## 12. MVP Development Roadmap

Build in the following order.

### Phase 1 — Foundation
- Create project structure.
- Configure Python environment.
- Set up PySide6.
- Create main application window.
- Implement dependency detection.

### Phase 2 — USB Detection
- Detect connected storage devices.
- Display device information.
- Implement safe device validation.
- Implement device selection.

### Phase 3 — ISO Management
- Implement ISO file selection.
- Implement official Windows download workflow.
- Add download progress.
- Add SHA-256 verification.

### Phase 4 — Bootable Media
- Implement partition preparation.
- Implement ISO extraction.
- Handle oversized WIM files.
- Implement boot compatibility.
- Verify resulting installation media.

### Phase 5 — Polish
- Add dark/light themes.
- Improve progress screens.
- Add error recovery.
- Improve accessibility.
- Add application packaging.

## 13. Definition of Done

A feature is complete only when:

- It works on supported Linux distributions.
- It has appropriate error handling.
- It does not violate disk safety requirements.
- Its tests pass.
- Its documentation is updated.
- It does not break existing functionality.

## 14. Agent Behavior

AI agents working on this repository must:

- Treat this document as the project's development contract.
- Prioritize user data safety over convenience.
- Avoid implementing fake or placeholder functionality as if it were complete.
- Clearly identify unimplemented features.
- Never claim USB bootability without an appropriate verification process.
- Explain significant technical trade-offs.
- Ask for clarification before making major architectural changes.
- Keep the project maintainable and extensible.

## 15. Git and GitHub Workflow

GitHub is the primary remote repository for WinMedia Linux.

AI coding agents must maintain the project in Git throughout development.

### Repository Management

- Use Git for all project development.
- Keep the local repository synchronized with the configured GitHub remote.
- Use the existing GitHub repository if one is already configured.
- Never create a new remote repository without explicit user permission.
- Never overwrite existing remote history.
- Never force-push unless explicitly authorized by the user.

### Commit Policy

After completing each meaningful development task:

1. Review all modified files.
2. Check for accidental secrets, credentials, API keys, and personal information.
3. Run relevant tests.
4. Review the Git diff.
5. Create a meaningful commit.
6. Push the commit to the configured GitHub remote.

Use descriptive commit messages following Conventional Commits where practical.

Examples:

- `feat: create initial PySide6 application`
- `feat: add sidebar navigation`
- `feat: implement dark and light themes`
- `feat: add USB device detection`
- `fix: handle interrupted ISO downloads`
- `test: add USB detection tests`
- `docs: update installation instructions`

### Push Policy

- Push completed and tested work to GitHub regularly.
- Do not wait until the entire project is finished.
- Keep the default branch clean and usable.
- Never push broken or knowingly incomplete commits as production-ready.
- Clearly identify unfinished features in commit messages and documentation.
- If pushing fails, explain the reason and preserve all local commits.
- Never discard local changes to resolve synchronization issues.

### Git Safety

- Never commit `.env` files containing secrets.
- Never commit passwords, tokens, private keys, or credentials.
- Maintain an appropriate `.gitignore`.
- Never use `git reset --hard` to discard user changes.
- Never use `git clean -fd` without explicit permission.
- Never rewrite shared Git history.
- Never force-push without explicit permission.

### Development Checkpoints

Push after completing each meaningful milestone:

1. Initial project structure.
2. GUI foundation.
3. Navigation and themes.
4. USB detection.
5. ISO download functionality.
6. ISO verification.
7. Bootable USB creation.
8. Testing and packaging.

### Final Requirement

The GitHub repository must remain an up-to-date representation of the working project.

After every successful push, report:

- What was implemented.
- Commit hash.
- Branch name.
- Push status.
- Any remaining issues.

**Important:** If GitHub authentication or remote configuration is missing, ask the user to configure it. Never attempt to bypass authentication or invent repository credentials.

## Final Project Goal

Create a reliable, beautiful, beginner-friendly Linux application that makes creating Windows installation media as effortless as using Microsoft's Windows Media Creation Tool.

**The experience should be simple. The engineering should be robust. The user's data must always be safe.**