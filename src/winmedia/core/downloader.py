"""Official Windows ISO download workflow (Phase 3 - not implemented).

Safety/behavior requirements (future): use official Microsoft sources only,
support resumable downloads when available, handle expired URLs, and never
silently substitute third-party ISOs.
"""

from __future__ import annotations

NOT_IMPLEMENTED_MESSAGE = (
    "Windows ISO download is not implemented yet (planned for Phase 3). "
    "No files are downloaded."
)
