"""
Storage Backends for Session Management

Provides abstract storage interface and implementations for various backends.
"""

from .base import StorageBackend
from .memory import InMemoryStorage

try:
    from .vercel_kv import VercelKVStorage
except ImportError:
    VercelKVStorage = None

try:
    from .redis import RedisStorage
except ImportError:
    RedisStorage = None


__all__ = [
    "StorageBackend",
    "InMemoryStorage",
    "VercelKVStorage",
    "RedisStorage",
]
