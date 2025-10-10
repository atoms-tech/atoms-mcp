"""Abstract base class for storage adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Optional


class StorageAdapter(ABC):
    """Abstract interface for file storage services."""
    
    @abstractmethod
    async def upload(
        self,
        bucket: str,
        path: str,
        data: bytes,
        *,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """Upload a file.
        
        Args:
            bucket: Storage bucket name
            path: File path within bucket
            data: File data
            content_type: MIME type
            metadata: Additional metadata
            
        Returns:
            Public URL or file identifier
        """
        pass
    
    @abstractmethod
    async def download(self, bucket: str, path: str) -> bytes:
        """Download a file.
        
        Args:
            bucket: Storage bucket name
            path: File path within bucket
            
        Returns:
            File data
        """
        pass
    
    @abstractmethod
    async def delete(self, bucket: str, path: str) -> bool:
        """Delete a file.
        
        Args:
            bucket: Storage bucket name
            path: File path within bucket
            
        Returns:
            True if deleted, False if not found
        """
        pass
    
    @abstractmethod
    def get_public_url(self, bucket: str, path: str) -> str:
        """Get public URL for a file.
        
        Args:
            bucket: Storage bucket name
            path: File path within bucket
            
        Returns:
            Public URL
        """
        pass

