"""Storage backend abstractions for Phase 4."""

from .base import StorageBackend
from .factory import get_storage_backend

__all__ = [
    "StorageBackend",
    "get_storage_backend",
]