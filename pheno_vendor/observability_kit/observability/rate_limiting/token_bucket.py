"""
Token bucket rate limiter implementation.

Provides smooth rate limiting with burst capacity using the token bucket algorithm.

Extracted from atoms_mcp-old/infrastructure/rate_limiter.py (lines 14-96)
"""

from __future__ import annotations

import time
import asyncio
import logging
from typing import Dict, Optional

from .base import RateLimiterBase

logger = logging.getLogger(__name__)


class TokenBucketRateLimiter(RateLimiterBase):
    """
    Token bucket rate limiter with per-user tracking.
    
    The token bucket algorithm allows for smooth rate limiting with burst capacity.
    Tokens are added to the bucket at a constant rate, and requests consume tokens.
    
    Features:
    - Smooth rate limiting
    - Burst capacity
    - Per-user tracking
    - Async-safe with locking
    
    Examples:
        >>> limiter = TokenBucketRateLimiter(
        ...     requests_per_minute=60,
        ...     burst_size=120
        ... )
        >>> 
        >>> # Try to acquire tokens
        >>> if await limiter.acquire("user123"):
        ...     # Process request
        ...     pass
        ... else:
        ...     # Rate limited
        ...     pass
        >>> 
        >>> # Wait for tokens
        >>> await limiter.wait_if_needed("user123", max_wait=10.0)
    """

    def __init__(
        self,
        requests_per_minute: int = 60,
        burst_size: Optional[int] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize token bucket rate limiter.

        Args:
            requests_per_minute: Sustained rate limit (tokens per minute)
            burst_size: Maximum burst size (defaults to 2x sustained rate)
            logger: Optional logger instance (uses module logger if not provided)
        
        Examples:
            >>> # 60 requests/min with 120 burst
            >>> limiter = TokenBucketRateLimiter(60, 120)
            >>> 
            >>> # 100 requests/min with default burst (200)
            >>> limiter = TokenBucketRateLimiter(100)
        """
        super().__init__()  # Initialize base class
        self.rate = requests_per_minute / 60.0  # tokens per second
        self.burst_size = burst_size or (requests_per_minute * 2)
        self.buckets: Dict[str, Dict] = {}  # user_id -> {tokens, last_update}
        self.lock = asyncio.Lock()
        self.logger = logger or globals()['logger']

    async def acquire(self, user_id: str, tokens: int = 1) -> bool:
        """
        Acquire tokens from the bucket.

        Args:
            user_id: User identifier
            tokens: Number of tokens to acquire

        Returns:
            True if tokens acquired, False if rate limited
        
        Examples:
            >>> limiter = TokenBucketRateLimiter(60)
            >>> if await limiter.acquire("user123"):
            ...     print("Request allowed")
            ... else:
            ...     print("Rate limited")
        """
        async with self.lock:
            now = time.time()

            # Initialize bucket for new user
            if user_id not in self.buckets:
                self.buckets[user_id] = {
                    "tokens": self.burst_size,
                    "last_update": now
                }

            bucket = self.buckets[user_id]

            # Add tokens based on time elapsed
            elapsed = now - bucket["last_update"]
            bucket["tokens"] = min(
                self.burst_size,
                bucket["tokens"] + (elapsed * self.rate)
            )
            bucket["last_update"] = now

            # Check if enough tokens available
            if bucket["tokens"] >= tokens:
                bucket["tokens"] -= tokens
                return True
            else:
                self.logger.warning(
                    f"Rate limit exceeded for user {user_id} "
                    f"(requested: {tokens}, available: {bucket['tokens']:.2f})"
                )
                return False

    async def wait_if_needed(
        self,
        user_id: str,
        tokens: int = 1,
        max_wait: float = 30.0
    ) -> None:
        """
        Wait until tokens are available or max_wait reached.

        Args:
            user_id: User identifier
            tokens: Number of tokens needed
            max_wait: Maximum seconds to wait

        Raises:
            TimeoutError: If max_wait exceeded
        
        Examples:
            >>> limiter = TokenBucketRateLimiter(60)
            >>> try:
            ...     await limiter.wait_if_needed("user123", tokens=5, max_wait=10.0)
            ...     print("Tokens acquired")
            ... except TimeoutError:
            ...     print("Timeout waiting for tokens")
        """
        start = time.time()

        while time.time() - start < max_wait:
            if await self.acquire(user_id, tokens):
                return

            # Calculate wait time needed
            bucket = self.buckets.get(user_id, {})
            needed_tokens = tokens - bucket.get("tokens", 0)
            wait_time = min(needed_tokens / self.rate, 1.0)

            await asyncio.sleep(wait_time)

        raise TimeoutError(
            f"Rate limit wait exceeded {max_wait}s for user {user_id}"
        )

    def get_remaining(self, user_id: str) -> int:
        """
        Get remaining tokens for a user.
        
        Args:
            user_id: User identifier
        
        Returns:
            Number of remaining tokens (rounded down)
        
        Examples:
            >>> limiter = TokenBucketRateLimiter(60)
            >>> remaining = limiter.get_remaining("user123")
            >>> print(f"Remaining tokens: {remaining}")
        """
        if user_id not in self.buckets:
            return int(self.burst_size)
        
        bucket = self.buckets[user_id]
        now = time.time()
        elapsed = now - bucket["last_update"]
        
        # Calculate current tokens
        current_tokens = min(
            self.burst_size,
            bucket["tokens"] + (elapsed * self.rate)
        )
        
        return int(current_tokens)

    def reset(self, user_id: Optional[str] = None) -> None:
        """
        Reset rate limiter state.
        
        Args:
            user_id: User to reset, or None to reset all users
        
        Examples:
            >>> limiter = TokenBucketRateLimiter(60)
            >>> limiter.reset("user123")  # Reset specific user
            >>> limiter.reset()  # Reset all users
        """
        if user_id is None:
            self.buckets.clear()
        elif user_id in self.buckets:
            del self.buckets[user_id]

