"""USB/storage device detection (Phase 2 - not implemented).

IMPORTANT: This module must never identify a device as removable based solely on
its /dev/sdX name, and must never perform destructive operations.
"""

from __future__ import annotations

# Phase 2 placeholder. No device scanning or disk operations are performed.
NOT_IMPLEMENTED_MESSAGE = (
    "USB device detection is not implemented yet (planned for Phase 2). "
    "No disks are scanned or modified."
)
