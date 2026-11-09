"""Bootable USB creation orchestration (Phase 4 - not implemented).

Safety requirements (future): never format or overwrite without explicit
confirmation, revalidate devices before writing, and reject system disks.
"""

from __future__ import annotations

NOT_IMPLEMENTED_MESSAGE = (
    "Bootable USB creation is not implemented yet (planned for Phase 4). "
    "No disks are formatted or modified."
)
