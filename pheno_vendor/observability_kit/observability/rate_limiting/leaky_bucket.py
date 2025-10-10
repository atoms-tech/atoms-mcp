"""
Leaky bucket rate limiter implementation.

Provides smooth rate limiting using the leaky bucket algorithm.
Requests leak out at a constant rate, allowing precise control over throughput.

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


class LeakyBucketRateLimiter(RateLimiterBase):
    """
    Leaky bucket rate limiter with optional Redis support.

    Requests fill the bucket and leak out at a constant rate. Provides
    smooth rate limiting with burst capacity while preventing sustained overload.

    Features:
    - Constant leak rate
    - Burst capacity
    - Optional Redis for distributed limiting
    - Memory fallback when Redis unavailable
    - Per-user tracking
    - Async-safe with locking

    Examples:
        >>> # In-memory rate limiter
        >>> limiter = LeakyBucketRateLimiter(
        ...     leak_rate=100,  # 100 requests per minute
        ...     capacity=150    # Allow bursts up to 150
        ... )
        >>>
        >>> # With Redis for distributed limiting
        >>> import redis
        >>> client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        >>> limiter = LeakyBucketRateLimiter(
        ...     leak_rate=100,
        ...     capacity=150,
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
        leak_rate: float,
        capacity: int,
        window_seconds: int = 60,
        redis_client: Optional[redis.Redis] = None,
        redis_key_prefix: str = "ratelimit:leaky:",
        logger_instance: Optional[logging.Logger] = None
    ):
        """
        Initialize leaky bucket rate limiter.

        Args:
            leak_rate: Rate at which requests leak from bucket (per minute)
            capacity: Maximum bucket capacity (allows bursts)
            window_seconds: Time window for leak rate calculation (default: 60)
            redis_client: Optional Redis client for distributed limiting
            redis_key_prefix: Prefix for Redis keys (default: "ratelimit:leaky:")
            logger_instance: Optional logger instance (uses module logger if not provided)

        Examples:
            >>> # 100 requests/min with 150 burst capacity
            >>> limiter = LeakyBucketRateLimiter(100, 150)
            >>>
            >>> # With Redis
            >>> import redis
            >>> r = redis.Redis(decode_responses=True)
            >>> limiter = LeakyBucketRateLimiter(100, 150, redis_client=r)
        """
        super().__init__()  # Initialize base class
        self.leak_rate = leak_rate / window_seconds  # Convert to per-second rate
        self.capacity = capacity
        self.window_seconds = window_seconds
        self.redis_client = redis_client
        self.redis_key_prefix = redis_key_prefix
        self.memory_store: Dict[str, Dict] = defaultdict(dict)
        self.lock = asyncio.Lock()
        self.logger = logger_instance or logger

    async def acquire(self, user_id: str, tokens: int = 1) -> bool:
        """
        Acquire tokens from the leaky bucket.

        Args:
            user_id: User identifier
            tokens: Number of tokens to acquire (default: 1)

        Returns:
            True if tokens acquired, False if rate limited

        Examples:
            >>> limiter = LeakyBucketRateLimiter(100, 150)
            >>> if await limiter.acquire("user123"):
            ...     print("Request allowed")
            ... else:
            ...     print("Rate limited")
        """
        now = time.time()

        if self.redis_client:
            try:
                return await self._redis_acquire(user_id, tokens, now)
            except Exception as e:
                self.logger.debug(f"Redis error in leaky bucket acquire: {e}, using memory fallback")
                return await self._memory_acquire(user_id, tokens, now)
        else:
            return await self._memory_acquire(user_id, tokens, now)

    async def _redis_acquire(self, user_id: str, tokens: int, now: float) -> bool:
        """Acquire tokens using Redis with Lua script for atomicity."""
        key = f"{self.redis_key_prefix}{user_id}"

        # Lua script for atomic leaky bucket operation
        lua_script = """
        local key = KEYS[1]
        local capacity = tonumber(ARGV[1])
        local leak_rate = tonumber(ARGV[2])
        local request_size = tonumber(ARGV[3])
        local now = tonumber(ARGV[4])

        local bucket = redis.call('HMGET', key, 'level', 'last_leak')
        local level = tonumber(bucket[1]) or 0
        local last_leak = tonumber(bucket[2]) or now

        -- Calculate leaked amount
        local elapsed = now - last_leak
        local leaked = elapsed * leak_rate
        level = math.max(0, level - leaked)

        -- Check if request fits
        local allowed = (level + request_size) <= capacity
        if allowed then
            level = level + request_size
        end

        -- Update bucket
        redis.call('HMSET', key, 'level', level, 'last_leak', now)
        redis.call('EXPIRE', key, 3600)

        return {allowed and 1 or 0, level, capacity}
        """

        result = self.redis_client.eval(
            lua_script,
            1,
            key,
            self.capacity,
            self.leak_rate,
            tokens,
            now
        )

        allowed = bool(result[0])
        current_level = float(result[1])

        if not allowed:
            self.logger.warning(
                f"Rate limit exceeded for user {user_id}: "
                f"bucket level {current_level:.2f}/{self.capacity}"
            )

        return allowed

    async def _memory_acquire(self, user_id: str, tokens: int, now: float) -> bool:
        """Acquire tokens using memory fallback."""
        async with self.lock:
            key = user_id

            if key not in self.memory_store:
                self.memory_store[key] = {
                    "level": 0,
                    "last_leak": now,
                    "capacity": self.capacity
                }

            bucket = self.memory_store[key]

            # Leak tokens
            elapsed = now - bucket["last_leak"]
            leaked = elapsed * self.leak_rate
            bucket["level"] = max(0, bucket["level"] - leaked)
            bucket["last_leak"] = now

            # Check if request fits
            if (bucket["level"] + tokens) <= self.capacity:
                bucket["level"] += tokens
                return True
            else:
                self.logger.warning(
                    f"Rate limit exceeded for user {user_id}: "
                    f"bucket level {bucket['level']:.2f}/{self.capacity}"
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
            >>> limiter = LeakyBucketRateLimiter(100, 150)
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

            # Calculate wait time based on leak rate
            remaining = await self._get_current_level(user_id)
            if remaining is not None:
                # Wait for enough tokens to leak
                space_needed = max(0, (remaining + tokens) - self.capacity)
                wait_time = min(space_needed / self.leak_rate, 1.0)
            else:
                wait_time = 0.1

            await asyncio.sleep(max(wait_time, 0.1))

        raise TimeoutError(
            f"Rate limit wait exceeded {max_wait}s for user {user_id}"
        )

    async def _get_current_level(self, user_id: str) -> Optional[float]:
        """Get current bucket level."""
        now = time.time()

        if self.redis_client:
            try:
                key = f"{self.redis_key_prefix}{user_id}"
                bucket = self.redis_client.hmget(key, 'level', 'last_leak')
                if bucket[0] is not None:
                    level = float(bucket[0])
                    last_leak = float(bucket[1] or now)
                    elapsed = now - last_leak
                    leaked = elapsed * self.leak_rate
                    return max(0, level - leaked)
            except Exception as e:
                self.logger.debug(f"Redis error getting level: {e}")

        # Memory fallback
        key = user_id
        if key in self.memory_store:
            bucket = self.memory_store[key]
            elapsed = now - bucket["last_leak"]
            leaked = elapsed * self.leak_rate
            return max(0, bucket["level"] - leaked)

        return None

    def get_remaining(self, user_id: str) -> Optional[int]:
        """
        Get remaining capacity in the bucket.

        Args:
            user_id: User identifier

        Returns:
            Number of remaining capacity, or None if unavailable

        Examples:
            >>> limiter = LeakyBucketRateLimiter(100, 150)
            >>> remaining = limiter.get_remaining("user123")
            >>> if remaining is not None:
            ...     print(f"Remaining capacity: {remaining}")
        """
        now = time.time()

        if self.redis_client:
            try:
                key = f"{self.redis_key_prefix}{user_id}"
                bucket = self.redis_client.hmget(key, 'level', 'last_leak')
                if bucket[0] is not None:
                    level = float(bucket[0])
                    last_leak = float(bucket[1] or now)
                    elapsed = now - last_leak
                    leaked = elapsed * self.leak_rate
                    current_level = max(0, level - leaked)
                    return int(self.capacity - current_level)
            except Exception as e:
                self.logger.debug(f"Redis error getting remaining: {e}")
                return None
        else:
            key = user_id
            if key in self.memory_store:
                bucket = self.memory_store[key]
                elapsed = now - bucket["last_leak"]
                leaked = elapsed * self.leak_rate
                current_level = max(0, bucket["level"] - leaked)
                return int(self.capacity - current_level)
            else:
                return int(self.capacity)

    def get_time_until_available(self, user_id: str, tokens: int) -> Optional[float]:
        """
        Calculate time until tokens become available.

        Args:
            user_id: User identifier
            tokens: Number of tokens needed

        Returns:
            Seconds until tokens available, or None if unavailable now or unknown

        Examples:
            >>> limiter = LeakyBucketRateLimiter(100, 150)
            >>> wait_time = limiter.get_time_until_available("user123", 10)
            >>> if wait_time is not None:
            ...     print(f"Wait {wait_time:.2f} seconds")
        """
        remaining = self.get_remaining(user_id)
        if remaining is None:
            return None

        if remaining >= tokens:
            return 0.0

        space_needed = tokens - remaining
        return space_needed / self.leak_rate

    def reset(self, user_id: Optional[str] = None) -> None:
        """
        Reset rate limiter state.

        Args:
            user_id: User to reset, or None to reset all users

        Examples:
            >>> limiter = LeakyBucketRateLimiter(100, 150)
            >>> limiter.reset("user123")  # Reset specific user
            >>> limiter.reset()  # Reset all users
        """
        if self.redis_client and user_id:
            key = f"{self.redis_key_prefix}{user_id}"
            try:
                self.redis_client.delete(key)
            except Exception as e:
                self.logger.debug(f"Error resetting Redis key: {e}")

        if user_id is None:
            self.memory_store.clear()
        elif user_id in self.memory_store:
            del self.memory_store[user_id]
