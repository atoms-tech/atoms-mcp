"""Embedding cache service using Upstash Redis.

Caches embeddings to reduce Vertex AI API calls.
Uses SHA-256 hash of text as cache key for space efficiency.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import List, Optional, Any

logger = logging.getLogger(__name__)


class EmbeddingCache:
    """Cache for embeddings using Upstash Redis.
    
    Implements cache-aside pattern:
    1. Check cache for embedding
    2. If miss, compute embedding
    3. Cache result with TTL
    """
    
    # Cache key patterns
    CACHE_PREFIX = "embed"
    STATS_PREFIX = "embed:stats"
    
    # Default TTL: 24 hours
    DEFAULT_TTL = 86400
    
    def __init__(self, redis_client: Optional[Any] = None):
        """Initialize cache with optional Redis client.
        
        Args:
            redis_client: upstash_redis.asyncio.Redis instance or None for in-memory
        """
        self.redis = redis_client
        self._memory_store: dict[str, List[float]] = {}  # In-memory fallback
    
    def _make_key(self, text: str, model: str) -> str:
        """Create cache key from text and model.
        
        Uses SHA-256 hash to keep keys short and consistent.
        
        Args:
            text: Text to embed
            model: Model name (e.g., "gemini-embedding-001")
            
        Returns:
            Cache key string
        """
        # Normalize text: strip whitespace, lowercase
        normalized = text.strip().lower()
        
        # Hash for uniqueness and consistency
        text_hash = hashlib.sha256(normalized.encode()).hexdigest()
        
        # Include first 50 chars of text for debugging
        preview = normalized[:50].replace(" ", "_")
        
        return f"{self.CACHE_PREFIX}:{model}:{text_hash}:{preview}"
    
    async def get(
        self,
        text: str,
        model: str = "gemini-embedding-001"
    ) -> Optional[List[float]]:
        """Get cached embedding for text.
        
        Args:
            text: Text that was embedded
            model: Model name
            
        Returns:
            Embedding vector or None if not cached
        """
        key = self._make_key(text, model)
        
        # Try memory store first (no Redis)
        if not self.redis and key in self._memory_store:
            return self._memory_store[key]
        
        if not self.redis:
            return None
        
        try:
            cached = await self.redis.get(key)
            
            if cached is None:
                return None
            
            # Parse JSON embedding
            if isinstance(cached, str):
                embedding = json.loads(cached)
            else:
                embedding = cached
            
            # Track cache hit
            await self._record_stat("hits")
            
            logger.debug(f"Cache hit for embedding (key: {key})")
            return embedding
        
        except Exception as e:
            logger.warning(f"Error getting embedding from cache: {e}")
            return None
    
    async def set(
        self,
        text: str,
        embedding: List[float],
        model: str = "gemini-embedding-001",
        ttl: int = DEFAULT_TTL
    ) -> bool:
        """Cache an embedding.
        
        Args:
            text: Text that was embedded
            embedding: Embedding vector
            model: Model name
            ttl: Time to live in seconds
            
        Returns:
            True if caching succeeded, False otherwise
        """
        if not text or not text.strip() or not embedding:
            return False
        
        key = self._make_key(text, model)
        
        # Store in memory first
        if not self.redis:
            self._memory_store[key] = embedding
            return True
        
        try:
            # Store as JSON
            json_embedding = json.dumps(embedding)
            
            await self.redis.setex(key, ttl, json_embedding)
            
            logger.debug(f"Cached embedding (key: {key}, ttl: {ttl}s)")
            return True
        
        except Exception as e:
            logger.warning(f"Error caching embedding: {e}")
            return False
    
    async def get_or_none(
        self,
        text: str,
        model: str = "gemini-embedding-001"
    ) -> Optional[List[float]]:
        """Alias for get() - returns None if not cached."""
        return await self.get(text, model)
    
    async def clear(
        self,
        text: str,
        model: str = "gemini-embedding-001"
    ) -> None:
        """Clear a specific embedding from cache.
        
        Args:
            text: Text whose embedding to clear
            model: Model name
        """
        key = self._make_key(text, model)
        
        # Clear from memory store
        if not self.redis:
            self._memory_store.pop(key, None)
            return
        
        try:
            await self.redis.delete(key)
            logger.info(f"Cleared embedding from cache (key: {key})")
        except Exception as e:
            logger.warning(f"Error clearing embedding: {e}")
    
    async def _record_stat(self, stat_type: str) -> None:
        """Record cache statistics for monitoring.
        
        Args:
            stat_type: Type of stat (hits, misses, etc.)
        """
        if not self.redis:
            return
        
        key = f"{self.STATS_PREFIX}:{stat_type}"
        
        try:
            await self.redis.incr(key)
            # Set expiry on stats: 24 hours
            await self.redis.expire(key, 86400)
        except Exception as e:
            logger.warning(f"Failed to record stat {stat_type}: {e}")
    
    async def track_miss(self) -> None:
        """Track cache miss."""
        await self._record_stat("misses")
    
    async def get_stats(self) -> dict[str, int]:
        """Get cache statistics.
        
        Returns:
            Dict with hits, misses, and hit_ratio
        """
        if not self.redis:
            return {"hits": 0, "misses": 0, "hit_ratio": 0.0}
        
        try:
            hits = int(await self.redis.get(f"{self.STATS_PREFIX}:hits") or 0)
            misses = int(await self.redis.get(f"{self.STATS_PREFIX}:misses") or 0)
            
            total = hits + misses
            hit_ratio = (hits / total * 100) if total > 0 else 0
            
            return {
                "hits": hits,
                "misses": misses,
                "total": total,
                "hit_ratio": round(hit_ratio, 2)
            }
        except Exception as e:
            logger.warning(f"Error getting cache stats: {e}")
            return {"hits": 0, "misses": 0, "hit_ratio": 0.0}


# Global instance
_embedding_cache: Optional[EmbeddingCache] = None


async def get_embedding_cache() -> EmbeddingCache:
    """Get or create global embedding cache.
    
    Returns:
        EmbeddingCache instance
        
    Note: Falls back to in-memory if Upstash Redis is not configured or fails to connect.
    """
    global _embedding_cache
    
    if _embedding_cache is None:
        # Try to get Redis client
        redis_client = None
        import os
        upstash_configured = bool(
            os.getenv("UPSTASH_REDIS_REST_URL") and os.getenv("UPSTASH_REDIS_REST_TOKEN")
        )
        
        if upstash_configured:
            try:
                from infrastructure.upstash_provider import get_upstash_redis
                redis_client = await get_upstash_redis()
                if redis_client:
                    # Test connection
                    await redis_client.ping()
                    logger.info("✅ Connected to Upstash Redis for embedding cache")
                else:
                    logger.warning("Upstash Redis configured but failed to initialize for embedding cache, using in-memory")
            except Exception as e:
                logger.error(f"Failed to connect to Upstash Redis for embedding cache: {e}")
                logger.warning("Falling back to in-memory embedding cache")
        else:
            logger.debug("Upstash Redis not configured, using in-memory embedding cache")
        
        _embedding_cache = EmbeddingCache(redis_client)
        backend = "Upstash Redis" if redis_client else "in-memory"
        logger.info(f"Initialized embedding cache ({backend})")
    
    return _embedding_cache


async def reset_embedding_cache():
    """Reset the global embedding cache instance."""
    global _embedding_cache
    _embedding_cache = None
