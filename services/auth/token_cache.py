"""Token cache service for auth tokens.

Caches validated JWT claims to reduce AuthKit JWKS validation calls.
Uses token hash as cache key for security.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class TokenCache:
    """Cache for validated JWT token claims.
    
    Stores decoded JWT claims with TTL to avoid re-validating
    the same tokens repeatedly.
    """
    
    CACHE_PREFIX = "auth:token"
    STATS_PREFIX = "auth:token:stats"
    
    # Default TTL: 1 hour
    DEFAULT_TTL = 3600
    
    def __init__(self, redis_client: Optional[Any] = None):
        """Initialize token cache with optional Redis client.
        
        Args:
            redis_client: upstash_redis.asyncio.Redis instance or None for in-memory
        """
        self.redis = redis_client
        self._memory_store: dict[str, dict[str, Any]] = {}  # In-memory fallback
    
    def _make_key(self, token: str) -> str:
        """Create cache key from token hash.
        
        Uses SHA-256 hash of token to avoid storing actual tokens.
        
        Args:
            token: JWT token string
            
        Returns:
            Cache key string
        """
        # Hash token for security
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        return f"{self.CACHE_PREFIX}:{token_hash}"
    
    async def get(self, token: str) -> Optional[Dict[str, Any]]:
        """Get cached claims for token.
        
        Args:
            token: JWT token
            
        Returns:
            Decoded claims dict or None if not cached
        """
        if not token:
            return None
        
        key = self._make_key(token)
        
        # Try memory store first
        if not self.redis and key in self._memory_store:
            return self._memory_store[key]
        
        if not self.redis:
            return None
        
        try:
            cached = await self.redis.get(key)
            
            if cached is None:
                return None
            
            # Parse JSON claims
            if isinstance(cached, str):
                claims = json.loads(cached)
            else:
                claims = cached
            
            # Track hit
            await self._record_stat("hits")
            
            logger.debug(f"Token cache hit (user: {claims.get('user_id', 'unknown')})")
            return claims
        
        except Exception as e:
            logger.warning(f"Error getting token from cache: {e}")
            return None
    
    async def set(
        self,
        token: str,
        claims: Dict[str, Any],
        ttl: int = DEFAULT_TTL
    ) -> bool:
        """Cache validated token claims.
        
        Args:
            token: JWT token (not stored, only hash used)
            claims: Decoded JWT claims
            ttl: Time to live in seconds
            
        Returns:
            True if caching succeeded
        """
        if not token or not claims:
            return False
        
        key = self._make_key(token)
        
        # Store in memory first
        if not self.redis:
            self._memory_store[key] = claims
            return True
        
        try:
            # Store claims as JSON (never store raw token)
            json_claims = json.dumps(claims)
            
            await self.redis.setex(key, ttl, json_claims)
            
            logger.debug(f"Cached token claims (user: {claims.get('user_id')}, ttl: {ttl}s)")
            return True
        
        except Exception as e:
            logger.warning(f"Error caching token: {e}")
            return False
    
    async def invalidate(self, token: str) -> None:
        """Remove token from cache (logout, etc.).
        
        Args:
            token: JWT token to invalidate
        """
        if not token:
            return
        
        key = self._make_key(token)
        
        # Clear from memory store
        if not self.redis:
            self._memory_store.pop(key, None)
            return
        
        try:
            await self.redis.delete(key)
            logger.info("Token invalidated from cache")
        except Exception as e:
            logger.warning(f"Error invalidating token: {e}")
    
    async def _record_stat(self, stat_type: str) -> None:
        """Record cache statistics.
        
        Args:
            stat_type: Type of stat (hits, misses, validations, etc.)
        """
        if not self.redis:
            return
        
        key = f"{self.STATS_PREFIX}:{stat_type}"
        
        try:
            await self.redis.incr(key)
            # Expire stats daily
            await self.redis.expire(key, 86400)
        except Exception as e:
            logger.warning(f"Failed to record stat {stat_type}: {e}")
    
    async def track_validation(self) -> None:
        """Track that a token had to be validated (cache miss)."""
        await self._record_stat("validations")
    
    async def track_miss(self) -> None:
        """Track cache miss."""
        await self._record_stat("misses")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dict with cache performance metrics
        """
        if not self.redis:
            return {"hits": 0, "misses": 0, "validations": 0, "hit_ratio": 0.0}
        
        try:
            hits = int(await self.redis.get(f"{self.STATS_PREFIX}:hits") or 0)
            misses = int(await self.redis.get(f"{self.STATS_PREFIX}:misses") or 0)
            validations = int(await self.redis.get(f"{self.STATS_PREFIX}:validations") or 0)
            
            total = hits + misses
            hit_ratio = (hits / total * 100) if total > 0 else 0
            
            return {
                "hits": hits,
                "misses": misses,
                "validations": validations,
                "total_attempts": total,
                "hit_ratio": round(hit_ratio, 2)
            }
        except Exception as e:
            logger.warning(f"Error getting token cache stats: {e}")
            return {"hits": 0, "misses": 0, "validations": 0, "hit_ratio": 0.0}


# Global instance
_token_cache: Optional[TokenCache] = None


async def get_token_cache() -> TokenCache:
    """Get or create global token cache.
    
    Returns:
        TokenCache instance
        
    Note: Falls back to in-memory if Upstash Redis is not configured or fails to connect.
    """
    global _token_cache
    
    if _token_cache is None:
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
                    logger.info("✅ Connected to Upstash Redis for token cache")
                else:
                    logger.warning("Upstash Redis configured but failed to initialize for token cache, using in-memory")
            except Exception as e:
                logger.error(f"Failed to connect to Upstash Redis for token cache: {e}")
                logger.warning("Falling back to in-memory token cache")
        else:
            logger.debug("Upstash Redis not configured, using in-memory token cache")
        
        _token_cache = TokenCache(redis_client)
        backend = "Upstash Redis" if redis_client else "in-memory"
        logger.info(f"Initialized token cache ({backend})")
    
    return _token_cache


async def reset_token_cache():
    """Reset the global token cache instance."""
    global _token_cache
    _token_cache = None
