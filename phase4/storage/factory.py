"""Storage backend factory."""

import os
from typing import Optional

from .base import StorageBackend
from utils.logging_setup import get_logger

logger = get_logger(__name__)

# Global storage instance
_storage_backend: Optional[StorageBackend] = None


def get_storage_backend(force_new: bool = False) -> StorageBackend:
    """Get or create storage backend instance.

    Args:
        force_new: Force creation of new instance

    Returns:
        Storage backend instance

    Raises:
        ValueError: Invalid storage provider
    """
    global _storage_backend

    if _storage_backend and not force_new:
        return _storage_backend

    provider = os.getenv("STORAGE_PROVIDER", "vercel_kv").lower()

    logger.info(f"Initializing storage backend: {provider}")

    if provider == "vercel_kv":
        from .vercel_kv import VercelKVBackend
        _storage_backend = VercelKVBackend()

    elif provider == "redis":
        from .redis import RedisBackend
        _storage_backend = RedisBackend()

    elif provider == "supabase":
        from .supabase import SupabaseBackend
        _storage_backend = SupabaseBackend()

    elif provider == "memory":
        # For testing only
        from .memory import MemoryBackend
        _storage_backend = MemoryBackend()

    else:
        raise ValueError(f"Unknown storage provider: {provider}")

    logger.info(f"Storage backend initialized: {provider}")
    return _storage_backend


def reset_storage_backend() -> None:
    """Reset global storage backend instance.

    Used primarily for testing.
    """
    global _storage_backend
    _storage_backend = None