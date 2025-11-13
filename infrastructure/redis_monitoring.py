"""Redis monitoring and metrics tracking.

Monitors cache performance, rate limiting, and other Redis-backed features.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class RedisMetrics:
    """Track Redis metrics for observability and optimization."""
    
    def __init__(self, redis_client: Optional[Any] = None):
        """Initialize metrics tracker.
        
        Args:
            redis_client: Upstash Redis client (optional)
        """
        self.redis = redis_client
        self.local_stats = {
            "embedding_cache_hits": 0,
            "embedding_cache_misses": 0,
            "token_cache_hits": 0,
            "token_cache_misses": 0,
            "rate_limit_checks": 0,
            "rate_limit_exceeded": 0,
        }
    
    async def get_all_metrics(self) -> Dict[str, Any]:
        """Get comprehensive metrics across all Redis backends.
        
        Returns:
            Dict with metrics from all systems
        """
        try:
            metrics = {
                "timestamp": self._get_timestamp(),
                "embedding_cache": await self._get_embedding_cache_stats(),
                "token_cache": await self._get_token_cache_stats(),
                "rate_limiting": await self._get_rate_limit_stats(),
                "redis_status": await self._get_redis_status(),
            }
            
            return metrics
        except Exception as e:
            logger.warning(f"Error collecting metrics: {e}")
            return {"error": str(e)}
    
    async def _get_embedding_cache_stats(self) -> Dict[str, Any]:
        """Get embedding cache statistics."""
        if not self.redis:
            return {"backend": "none"}
        
        try:
            from services.embedding_cache import get_embedding_cache
            cache = await get_embedding_cache()
            stats = await cache.get_stats()
            
            return {
                "backend": "upstash_redis",
                "hits": stats.get("hits", 0),
                "misses": stats.get("misses", 0),
                "total": stats.get("total", 0),
                "hit_ratio": stats.get("hit_ratio", 0.0),
                "api_calls_saved": int(stats.get("hits", 0) * 0.02),  # ~$0.02 per call
            }
        except Exception as e:
            logger.warning(f"Error getting embedding cache stats: {e}")
            return {"error": str(e)}
    
    async def _get_token_cache_stats(self) -> Dict[str, Any]:
        """Get token cache statistics."""
        if not self.redis:
            return {"backend": "none"}
        
        try:
            from services.auth.token_cache import get_token_cache
            cache = await get_token_cache()
            stats = await cache.get_stats()
            
            return {
                "backend": "upstash_redis",
                "hits": stats.get("hits", 0),
                "misses": stats.get("misses", 0),
                "validations": stats.get("validations", 0),
                "total_attempts": stats.get("total_attempts", 0),
                "hit_ratio": stats.get("hit_ratio", 0.0),
                "jwks_calls_saved": int(stats.get("hits", 0)),
            }
        except Exception as e:
            logger.warning(f"Error getting token cache stats: {e}")
            return {"error": str(e)}
    
    async def _get_rate_limit_stats(self) -> Dict[str, Any]:
        """Get rate limiting statistics."""
        if not self.redis:
            return {"backend": "memory"}
        
        try:
            from infrastructure.distributed_rate_limiter import get_distributed_rate_limiter
            await get_distributed_rate_limiter()  # Verify it initializes
            
            return {
                "backend": "upstash_redis",
                "status": "active",
                "exceeded_count": self.local_stats.get("rate_limit_exceeded", 0),
            }
        except Exception as e:
            logger.warning(f"Error getting rate limit stats: {e}")
            return {"error": str(e)}
    
    async def _get_redis_status(self) -> Dict[str, Any]:
        """Get Redis connection status."""
        if not self.redis:
            return {
                "connected": False,
                "backend": "none",
                "reason": "Not configured"
            }
        
        try:
            await self.redis.ping()
            return {
                "connected": True,
                "backend": "upstash_redis",
                "latency_ms": "< 50 (typical)",
            }
        except Exception as e:
            logger.warning(f"Redis health check failed: {e}")
            return {
                "connected": False,
                "backend": "upstash_redis",
                "error": str(e)
            }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()
    
    def track_rate_limit_exceeded(self) -> None:
        """Track rate limit exceeded event."""
        self.local_stats["rate_limit_exceeded"] += 1
    
    def track_rate_limit_check(self) -> None:
        """Track rate limit check."""
        self.local_stats["rate_limit_checks"] += 1


# Global instance
_metrics: Optional[RedisMetrics] = None


async def get_redis_metrics() -> RedisMetrics:
    """Get or create global Redis metrics instance.
    
    Returns:
        RedisMetrics instance
    """
    global _metrics
    
    if _metrics is None:
        redis_client = None
        try:
            from infrastructure.upstash_provider import get_upstash_redis
            redis_client = await get_upstash_redis()
        except Exception as e:
            logger.warning(f"Failed to get Upstash Redis for metrics: {e}")
        
        _metrics = RedisMetrics(redis_client)
    
    return _metrics


async def reset_redis_metrics():
    """Reset the global metrics instance."""
    global _metrics
    _metrics = None
