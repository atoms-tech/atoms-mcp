"""In-memory storage adapter for testing.

Provides file/blob storage operations using in-memory storage.
"""

from __future__ import annotations

from typing import Dict, Optional

try:
    from ..adapters import StorageAdapter
except ImportError:
    from infrastructure.adapters import StorageAdapter


class InMemoryStorageAdapter(StorageAdapter):
    """In-memory storage adapter for testing.
    
    Provides file/blob storage operations using in-memory storage.
    """
    
    def __init__(self):
        """Initialize in-memory storage adapter."""
        self._buckets: Dict[str, Dict[str, bytes]] = {}

    async def upload(
        self,
        bucket: str,
        path: str,
        data: bytes,
        *,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> str:
        """Upload data to storage bucket."""
        self._buckets.setdefault(bucket, {})[path] = data
        return self.get_public_url(bucket, path)

    async def download(self, bucket: str, path: str) -> bytes:
        """Download data from storage bucket."""
        return self._buckets.get(bucket, {}).get(path, b"")

    async def delete(self, bucket: str, path: str) -> bool:
        """Delete data from storage bucket."""
        return bool(self._buckets.get(bucket, {}).pop(path, None))

    def get_public_url(self, bucket: str, path: str) -> str:
        """Get public URL for stored file."""
        return f"mem://{bucket}/{path}"
