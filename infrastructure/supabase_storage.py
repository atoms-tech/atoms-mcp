"""Supabase storage adapter implementation."""

from __future__ import annotations

import os
from typing import Dict, Optional

from .adapters import StorageAdapter
from ..supabase_client import get_supabase
from ..errors import normalize_error, ApiError


class SupabaseStorageAdapter(StorageAdapter):
    """Supabase-based storage adapter."""
    
    def __init__(self):
        self._client = None
    
    def _get_client(self):
        """Get Supabase client, cached."""
        if self._client is None:
            self._client = get_supabase()
        return self._client
    
    async def upload(
        self,
        bucket: str,
        path: str,
        data: bytes,
        *,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """Upload a file to Supabase storage."""
        try:
            client = self._get_client()
            storage = client.storage.from_(bucket)
            
            file_options = {}
            if content_type:
                file_options["content-type"] = content_type
            if metadata:
                file_options.update(metadata)
            
            result = storage.upload(path, data, file_options=file_options)
            
            if hasattr(result, 'error') and result.error:
                raise ApiError(
                    "STORAGE_ERROR", 
                    f"Failed to upload file: {result.error}",
                    details=str(result.error)
                )
            
            # Return public URL
            return self.get_public_url(bucket, path)
        
        except Exception as e:
            raise normalize_error(e, f"Failed to upload file to {bucket}/{path}")
    
    async def download(self, bucket: str, path: str) -> bytes:
        """Download a file from Supabase storage."""
        try:
            client = self._get_client()
            storage = client.storage.from_(bucket)
            
            result = storage.download(path)
            
            if hasattr(result, 'error') and result.error:
                raise ApiError(
                    "STORAGE_ERROR",
                    f"Failed to download file: {result.error}",
                    details=str(result.error)
                )
            
            return result
        
        except Exception as e:
            raise normalize_error(e, f"Failed to download file from {bucket}/{path}")
    
    async def delete(self, bucket: str, path: str) -> bool:
        """Delete a file from Supabase storage."""
        try:
            client = self._get_client()
            storage = client.storage.from_(bucket)
            
            result = storage.remove([path])
            
            if hasattr(result, 'error') and result.error:
                return False
            
            return True
        
        except Exception:
            return False
    
    def get_public_url(self, bucket: str, path: str) -> str:
        """Get public URL for a file in Supabase storage."""
        base_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        if not base_url:
            raise ApiError("CONFIG", "Missing NEXT_PUBLIC_SUPABASE_URL")
        
        return f"{base_url}/storage/v1/object/public/{bucket}/{path}"