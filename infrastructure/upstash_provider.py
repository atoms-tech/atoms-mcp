"""Upstash Redis provider for distributed caching and state management.

Provides a unified interface for Upstash Redis with fallback to in-memory storage.
Integrates with FastMCP's py-key-value-aio storage abstraction.
"""

from __future__ import annotations

import os
import json
import logging
from typing import Any, Optional, Dict
import asyncio

logger = logging.getLogger(__name__)


class UpstashKVWrapper:
    """Wrapper to make Upstash SDK conform to py-key-value-aio KVStore interface.
    
    This wrapper converts the Upstash HTTP SDK into a compatible key-value store
    for use with FastMCP's response caching and other storage backends.
    """
    
    def __init__(self, redis):
        """Initialize with Upstash Redis client.
        
        Args:
            redis: upstash_redis.asyncio.Redis instance
        """
        self.redis = redis
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get a JSON value from Redis.
        
        Args:
            key: The key to retrieve
            
        Returns:
            Parsed JSON dict or None if key doesn't exist
        """
        try:
            val = await self.redis.get(key)
            if val is None:
                return None
            
            # Upstash returns string, parse if needed
            if isinstance(val, str):
                return json.loads(val)
            return val
        except Exception as e:
            logger.warning(f"Error getting key {key} from Upstash: {e}")
            return None
    
    async def set(self, key: str, value: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """Set a JSON value in Redis.
        
        Args:
            key: The key to set
            value: Dict to store (will be JSON encoded)
            ttl: Optional TTL in seconds
        """
        try:
            json_value = json.dumps(value)
            if ttl:
                await self.redis.setex(key, ttl, json_value)
            else:
                await self.redis.set(key, json_value)
        except Exception as e:
            logger.warning(f"Error setting key {key} in Upstash: {e}")
    
    async def delete(self, key: str) -> None:
        """Delete a key from Redis.
        
        Args:
            key: The key to delete
        """
        try:
            await self.redis.delete(key)
        except Exception as e:
            logger.warning(f"Error deleting key {key} from Upstash: {e}")
    
    async def close(self) -> None:
        """Close the Redis connection."""
        try:
            if hasattr(self.redis, 'close'):
                await self.redis.close()
        except Exception as e:
            logger.warning(f"Error closing Upstash connection: {e}")


async def get_upstash_store() -> Any:
    """Get Upstash Redis store with fallback to in-memory.
    
    Returns:
        Either UpstashKVWrapper (if UPSTASH_REDIS_REST_URL set) or MemoryStore
    """
    upstash_url = os.getenv("UPSTASH_REDIS_REST_URL")
    upstash_token = os.getenv("UPSTASH_REDIS_REST_TOKEN")
    
    if upstash_url and upstash_token:
        try:
            from upstash_redis.asyncio import Redis
            
            redis = Redis(url=upstash_url, token=upstash_token)
            
            # Test connection
            await redis.ping()
            logger.info("✅ Connected to Upstash Redis")
            
            return UpstashKVWrapper(redis)
        except Exception as e:
            logger.warning(f"Failed to connect to Upstash Redis: {e}, falling back to in-memory")
    
    # Fallback to in-memory storage
    logger.info("Using in-memory storage (Upstash not configured)")
    try:
        from key_value.aio.stores.memory import MemoryStore
        return MemoryStore()
    except ImportError:
        # Minimal fallback if py-key-value-aio not available
        logger.warning("py-key-value-aio not installed, using basic in-memory dict")
        return _BasicInMemoryStore()


class _BasicInMemoryStore:
    """Minimal in-memory store fallback if py-key-value-aio not available."""
    
    def __init__(self):
        self.data: Dict[str, Any] = {}
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get value from memory."""
        return self.data.get(key)
    
    async def set(self, key: str, value: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """Set value in memory."""
        self.data[key] = value
    
    async def delete(self, key: str) -> None:
        """Delete value from memory."""
        self.data.pop(key, None)
    
    async def close(self) -> None:
        """Close (no-op for in-memory)."""
        pass


# Global store instance
_upstash_store: Optional[Any] = None


async def get_upstash_redis() -> Optional[Any]:
    """Get the Upstash Redis client directly.
    
    Returns:
        upstash_redis.asyncio.Redis instance or None if not configured
    """
    upstash_url = os.getenv("UPSTASH_REDIS_REST_URL")
    upstash_token = os.getenv("UPSTASH_REDIS_REST_TOKEN")
    
    if not (upstash_url and upstash_token):
        return None
    
    try:
        from upstash_redis.asyncio import Redis
        return Redis(url=upstash_url, token=upstash_token)
    except Exception as e:
        logger.warning(f"Failed to initialize Upstash Redis: {e}")
        return None


async def initialize_upstash_store() -> Any:
    """Initialize the global Upstash store."""
    global _upstash_store
    if _upstash_store is None:
        _upstash_store = await get_upstash_store()
    return _upstash_store


async def get_cache_store() -> Any:
    """Get the global cache store (Upstash or in-memory)."""
    global _upstash_store
    if _upstash_store is None:
        _upstash_store = await get_upstash_store()
    return _upstash_store


async def close_upstash_store() -> None:
    """Close the Upstash store connection."""
    global _upstash_store
    if _upstash_store:
        await _upstash_store.close()
        _upstash_store = None
