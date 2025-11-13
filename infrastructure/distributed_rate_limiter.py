"""Distributed rate limiter using Upstash Redis.

Replaces in-memory rate limiting for production deployments where multiple
Vercel replicas need to share rate limit state.
"""

from __future__ import annotations

import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class DistributedRateLimiter:
    """Distributed rate limiter using Upstash Redis as backend.
    
    Uses sliding window algorithm for per-user rate limiting.
    Falls back to in-memory if Redis unavailable.
    """
    
    def __init__(self, redis_client: Optional[Any] = None):
        """Initialize with optional Redis client.
        
        Args:
            redis_client: upstash_redis.asyncio.Redis instance or None for in-memory
        """
        self.redis = redis_client
        self.in_memory: Dict[str, Dict[str, Any]] = {}
        
        # Rate limit configs per operation type
        self.limits = {
            "default": {"requests": 120, "window": 60},      # 120 req/min
            "search": {"requests": 30, "window": 60},        # 30 searches/min
            "create": {"requests": 50, "window": 60},        # 50 creates/min
            "update": {"requests": 50, "window": 60},        # 50 updates/min
            "delete": {"requests": 20, "window": 60},        # 20 deletes/min
            "auth": {"requests": 10, "window": 60},          # 10 auth attempts/min
        }
    
    async def check_rate_limit(
        self,
        user_id: str,
        operation_type: str = "default"
    ) -> Dict[str, Any]:
        """Check if user is within rate limit.
        
        Args:
            user_id: User identifier
            operation_type: Type of operation (default, search, create, etc.)
            
        Returns:
            Dict with allowed (bool), limit info, and retry_after if blocked
        """
        if not user_id:
            return {"allowed": False, "error": "Missing user_id"}
        
        limit_config = self.limits.get(operation_type, self.limits["default"])
        max_requests = limit_config["requests"]
        window_seconds = limit_config["window"]
        
        key = f"rl:{user_id}:{operation_type}"
        now = int(time.time())
        
        try:
            if self.redis:
                return await self._check_redis(key, max_requests, window_seconds, now)
            else:
                return await self._check_memory(key, max_requests, window_seconds, now)
        except Exception as e:
            logger.warning(f"Rate limit check failed: {e}, allowing request")
            # Fail open - allow request if rate limiter fails
            return {
                "allowed": True,
                "limit": max_requests,
                "window_seconds": window_seconds,
                "current_count": 0,
                "remaining": max_requests,
                "warning": "Rate limiter unavailable"
            }
    
    async def _check_redis(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
        now: int
    ) -> Dict[str, Any]:
        """Check rate limit using Redis.
        
        Uses INCR with expiry for atomic sliding window counting.
        """
        try:
            # Increment counter
            count = await self.redis.incr(key)
            
            # Set expiry on first request in window
            if count == 1:
                await self.redis.expire(key, window_seconds)
            
            if count > max_requests:
                logger.warning(
                    f"Rate limit exceeded: {count}/{max_requests} "
                    f"(key: {key})"
                )
                return {
                    "allowed": False,
                    "limit": max_requests,
                    "window_seconds": window_seconds,
                    "current_count": count,
                    "retry_after": window_seconds,
                    "error": f"Rate limit exceeded. Max {max_requests} requests per {window_seconds}s"
                }
            
            return {
                "allowed": True,
                "limit": max_requests,
                "window_seconds": window_seconds,
                "current_count": count,
                "remaining": max_requests - count
            }
        
        except Exception as e:
            logger.error(f"Redis rate limit check failed: {e}")
            # Fail open
            raise
    
    async def _check_memory(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
        now: int
    ) -> Dict[str, Any]:
        """Check rate limit using in-memory storage.
        
        Used as fallback when Redis unavailable.
        """
        if key not in self.in_memory:
            self.in_memory[key] = {
                "count": 0,
                "window_start": now
            }
        
        bucket = self.in_memory[key]
        
        # Reset window if expired
        if now - bucket["window_start"] > window_seconds:
            bucket["count"] = 0
            bucket["window_start"] = now
        
        bucket["count"] += 1
        
        if bucket["count"] > max_requests:
            logger.warning(
                f"Rate limit exceeded: {bucket['count']}/{max_requests} "
                f"(key: {key}, in-memory)"
            )
            return {
                "allowed": False,
                "limit": max_requests,
                "window_seconds": window_seconds,
                "current_count": bucket["count"],
                "retry_after": window_seconds,
                "error": f"Rate limit exceeded. Max {max_requests} requests per {window_seconds}s"
            }
        
        return {
            "allowed": True,
            "limit": max_requests,
            "window_seconds": window_seconds,
            "current_count": bucket["count"],
            "remaining": max_requests - bucket["count"]
        }
    
    async def get_remaining(
        self,
        user_id: str,
        operation_type: str = "default"
    ) -> int:
        """Get remaining requests for user in current window.
        
        Args:
            user_id: User identifier
            operation_type: Type of operation
            
        Returns:
            Number of remaining requests
        """
        if not user_id:
            return 0
        
        limit_config = self.limits.get(operation_type, self.limits["default"])
        max_requests = limit_config["requests"]
        
        key = f"rl:{user_id}:{operation_type}"
        
        try:
            if self.redis:
                count = await self.redis.get(key)
                current = int(count) if count else 0
            else:
                bucket = self.in_memory.get(key, {})
                current = bucket.get("count", 0)
            
            return max(0, max_requests - current)
        except Exception as e:
            logger.warning(f"Failed to get remaining requests: {e}")
            return max_requests
    
    async def reset_user(self, user_id: str, operation_type: str = "default") -> None:
        """Reset rate limit for a user (admin only).
        
        Args:
            user_id: User identifier
            operation_type: Type of operation
        """
        key = f"rl:{user_id}:{operation_type}"
        
        try:
            if self.redis:
                await self.redis.delete(key)
            else:
                self.in_memory.pop(key, None)
            
            logger.info(f"Reset rate limit for user {user_id}")
        except Exception as e:
            logger.warning(f"Failed to reset rate limit: {e}")
    
    async def get_stats(self, user_id: str) -> Dict[str, Any]:
        """Get rate limit stats for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dict with stats for each operation type
        """
        stats = {}
        
        for op_type in self.limits:
            remaining = await self.get_remaining(user_id, op_type)
            limit_config = self.limits[op_type]
            
            stats[op_type] = {
                "limit": limit_config["requests"],
                "window_seconds": limit_config["window"],
                "remaining": remaining,
                "used": limit_config["requests"] - remaining
            }
        
        return stats


# Global instance
_rate_limiter: Optional[DistributedRateLimiter] = None


async def get_distributed_rate_limiter() -> DistributedRateLimiter:
    """Get or create global distributed rate limiter.
    
    Returns:
        DistributedRateLimiter instance
    """
    global _rate_limiter
    
    if _rate_limiter is None:
        # Try to get Redis client
        redis_client = None
        try:
            from .upstash_provider import get_upstash_redis
            redis_client = await get_upstash_redis()
        except Exception as e:
            logger.warning(f"Failed to get Upstash Redis: {e}")
        
        _rate_limiter = DistributedRateLimiter(redis_client)
        logger.info(
            f"Initialized distributed rate limiter "
            f"({'Upstash Redis' if redis_client else 'in-memory'})"
        )
    
    return _rate_limiter


async def reset_rate_limiter():
    """Reset the global rate limiter instance."""
    global _rate_limiter
    _rate_limiter = None
