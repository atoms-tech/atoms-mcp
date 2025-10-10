"""
Fixed window rate limiter implementation.

Provides simple fixed-window rate limiting with optional Redis support.
Tracks requests in fixed time windows aligned to window boundaries.

Extracted from zen-mcp-server/utils/advanced_ratelimit.py
"""

from __future__ import annotations

import time
import asyncio
import logging
from typing import Dict, Optional
from collections import defaultdict

try:
    import redis
except ImportError:
    redis = None

from .base import RateLimiterBase

logger = logging.getLogger(__name__)


class FixedWindowRateLimiter(RateLimiterBase):
    """
    Fixed window rate limiter with optional Redis support.

    Tracks requests in fixed time windows aligned to window boundaries.
    Simple and memory-efficient but can allow bursts at window boundaries.

    Features:
    - Fixed time windows
    - Optional Redis for distributed limiting
    - Memory fallback when Redis unavailable
    - Per-user tracking
    - Async-safe with locking

    Examples:
        >>> # In-memory rate limiter
        >>> limiter = FixedWindowRateLimiter(
        ...     window_seconds=60,
        ...     max_requests=100
        ... )
        >>>
        >>> # With Redis for distributed limiting
        >>> import redis
        >>> client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        >>> limiter = FixedWindowRateLimiter(
        ...     window_seconds=60,
        ...     max_requests=100,
        ...     redis_client=client
        ... )
        >>>
        >>> # Check if request is allowed
        >>> if await limiter.acquire("user123"):
        ...     # Process request
        ...     pass
        ... else:
        ...     # Rate limited
        ...     pass
    """

    def __init__(
        self,
        window_seconds: int = 60,
        max_requests: int = 60,
        redis_client: Optional[redis.Redis] = None,
        redis_key_prefix: str = "ratelimit:fixed:",
        logger_instance: Optional[logging.Logger] = None
    ):
        """
        Initialize fixed window rate limiter.

        Args:
            window_seconds: Duration of each window in seconds
            max_requests: Maximum requests allowed per window
            redis_client: Optional Redis client for distributed limiting
            redis_key_prefix: Prefix for Redis keys (default: "ratelimit:fixed:")
            logger_instance: Optional logger instance (uses module logger if not provided)

        Examples:
            >>> # Basic in-memory limiter
            >>> limiter = FixedWindowRateLimiter(60, 100)
            >>>
            >>> # With Redis
            >>> import redis
            >>> r = redis.Redis(decode_responses=True)
            >>> limiter = FixedWindowRateLimiter(60, 100, redis_client=r)
        """
        super().__init__()  # Initialize base class
        self.window_seconds = window_seconds
        self.max_requests = max_requests
        self.redis_client = redis_client
        self.redis_key_prefix = redis_key_prefix
        self.memory_store: Dict[str, Dict] = defaultdict(dict)
        self.lock = asyncio.Lock()
        self.logger = logger_instance or logger

    async def acquire(self, user_id: str, tokens: int = 1) -> bool:
        """
        Acquire tokens from the fixed window.

        Args:
            user_id: User identifier
            tokens: Number of tokens to acquire (default: 1)

        Returns:
            True if tokens acquired, False if rate limited

        Examples:
            >>> limiter = FixedWindowRateLimiter(60, 100)
            >>> if await limiter.acquire("user123"):
            ...     print("Request allowed")
            ... else:
            ...     print("Rate limited")
        """
        now = int(time.time())
        window_start = (now // self.window_seconds) * self.window_seconds

        if self.redis_client:
            try:
                return await self._redis_acquire(user_id, tokens, window_start)
            except Exception as e:
                self.logger.debug(f"Redis error in fixed window acquire: {e}, using memory fallback")
                return await self._memory_acquire(user_id, tokens, window_start)
        else:
            return await self._memory_acquire(user_id, tokens, window_start)

    async def _redis_acquire(self, user_id: str, tokens: int, window_start: int) -> bool:
        """Acquire tokens using Redis."""
        key = f"{self.redis_key_prefix}{user_id}:{window_start}"

        # Use pipeline for atomic operations
        pipe = self.redis_client.pipeline()
        pipe.get(key)
        pipe.incr(key, tokens)
        pipe.expire(key, self.window_seconds)
        results = pipe.execute()

        current_count = int(results[0] or 0)
        new_count = int(results[1])

        if new_count <= self.max_requests:
            return True
        else:
            # Exceeded limit, rollback
            self.redis_client.decr(key, tokens)
            self.logger.warning(
                f"Rate limit exceeded for user {user_id}: "
                f"{new_count} requests in window"
            )
            return False

    async def _memory_acquire(self, user_id: str, tokens: int, window_start: int) -> bool:
        """Acquire tokens using memory fallback."""
        async with self.lock:
            key = f"{user_id}:{window_start}"

            current_count = self.memory_store[key].get("count", 0)
            new_count = current_count + tokens

            if new_count <= self.max_requests:
                self.memory_store[key] = {
                    "count": new_count,
                    "expires": window_start + self.window_seconds
                }

                # Clean expired entries
                await self._cleanup_memory_store()
                return True
            else:
                self.logger.warning(
                    f"Rate limit exceeded for user {user_id}: "
                    f"{new_count} requests in window"
                )
                return False

    async def wait_if_needed(
        self,
        user_id: str,
        tokens: int = 1,
        max_wait: float = 30.0
    ) -> None:
        """
        Wait until tokens are available or timeout.

        Args:
            user_id: User identifier
            tokens: Number of tokens needed
            max_wait: Maximum seconds to wait

        Raises:
            TimeoutError: If max_wait exceeded without acquiring tokens

        Examples:
            >>> limiter = FixedWindowRateLimiter(60, 100)
            >>> try:
            ...     await limiter.wait_if_needed("user123", max_wait=10.0)
            ...     print("Tokens acquired")
            ... except TimeoutError:
            ...     print("Timeout waiting for tokens")
        """
        start = time.time()

        while time.time() - start < max_wait:
            if await self.acquire(user_id, tokens):
                return

            # Calculate time until next window
            now = int(time.time())
            window_start = (now // self.window_seconds) * self.window_seconds
            window_end = window_start + self.window_seconds
            wait_time = min(window_end - now, 1.0)

            await asyncio.sleep(wait_time)

        raise TimeoutError(
            f"Rate limit wait exceeded {max_wait}s for user {user_id}"
        )

    def get_remaining(self, user_id: str) -> Optional[int]:
        """
        Get remaining requests in current window.

        Args:
            user_id: User identifier

        Returns:
            Number of remaining requests, or None if unavailable

        Examples:
            >>> limiter = FixedWindowRateLimiter(60, 100)
            >>> remaining = limiter.get_remaining("user123")
            >>> if remaining is not None:
            ...     print(f"Remaining: {remaining}")
        """
        now = int(time.time())
        window_start = (now // self.window_seconds) * self.window_seconds

        if self.redis_client:
            try:
                key = f"{self.redis_key_prefix}{user_id}:{window_start}"
                count = self.redis_client.get(key)
                count = int(count) if count else 0
                return max(0, self.max_requests - count)
            except Exception as e:
                self.logger.debug(f"Redis error getting remaining: {e}")
                return None
        else:
            key = f"{user_id}:{window_start}"
            count = self.memory_store.get(key, {}).get("count", 0)
            return max(0, self.max_requests - count)

    def get_reset_time(self, user_id: str) -> int:
        """
        Get timestamp when the current window resets.

        Args:
            user_id: User identifier

        Returns:
            Unix timestamp when window resets

        Examples:
            >>> limiter = FixedWindowRateLimiter(60, 100)
            >>> reset_time = limiter.get_reset_time("user123")
            >>> print(f"Window resets at: {reset_time}")
        """
        now = int(time.time())
        window_start = (now // self.window_seconds) * self.window_seconds
        return window_start + self.window_seconds

    async def _cleanup_memory_store(self):
        """Clean up expired entries from memory store."""
        now = int(time.time())
        keys_to_remove = []

        for key, data in self.memory_store.items():
            if isinstance(data, dict) and "expires" in data:
                if data["expires"] < now:
                    keys_to_remove.append(key)

        for key in keys_to_remove:
            del self.memory_store[key]

    def reset(self, user_id: Optional[str] = None) -> None:
        """
        Reset rate limiter state.

        Args:
            user_id: User to reset, or None to reset all users

        Examples:
            >>> limiter = FixedWindowRateLimiter(60, 100)
            >>> limiter.reset("user123")  # Reset specific user
            >>> limiter.reset()  # Reset all users
        """
        if self.redis_client and user_id:
            # Delete all Redis keys for this user
            pattern = f"{self.redis_key_prefix}{user_id}:*"
            try:
                for key in self.redis_client.scan_iter(match=pattern):
                    self.redis_client.delete(key)
            except Exception as e:
                self.logger.debug(f"Error resetting Redis keys: {e}")

        if user_id is None:
            self.memory_store.clear()
        else:
            # Remove all memory entries for this user
            keys_to_remove = [k for k in self.memory_store.keys() if k.startswith(f"{user_id}:")]
            for key in keys_to_remove:
                del self.memory_store[key]
