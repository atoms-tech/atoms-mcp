"""Rate limiter for API calls with sliding window and token bucket algorithms."""

from __future__ import annotations

import time
import asyncio
from typing import Dict, Optional
from collections import deque
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token bucket rate limiter with per-user tracking."""

    def __init__(
        self,
        requests_per_minute: int = 60,
        burst_size: Optional[int] = None
    ):
        """Initialize rate limiter.

        Args:
            requests_per_minute: Sustained rate limit
            burst_size: Maximum burst size (defaults to 2x sustained rate)
        """
        self.rate = requests_per_minute / 60.0  # tokens per second
        self.burst_size = burst_size or (requests_per_minute * 2)
        self.buckets: Dict[str, Dict] = {}  # user_id -> {tokens, last_update}
        self.lock = asyncio.Lock()

    async def acquire(self, user_id: str, tokens: int = 1) -> bool:
        """Acquire tokens from the bucket.

        Args:
            user_id: User identifier
            tokens: Number of tokens to acquire

        Returns:
            True if tokens acquired, False if rate limited
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
                logger.warning(f"Rate limit exceeded for user {user_id}")
                return False

    async def wait_if_needed(self, user_id: str, tokens: int = 1, max_wait: float = 30.0):
        """Wait until tokens are available or max_wait reached.

        Args:
            user_id: User identifier
            tokens: Number of tokens needed
            max_wait: Maximum seconds to wait

        Raises:
            TimeoutError: If max_wait exceeded
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

        raise TimeoutError(f"Rate limit wait exceeded {max_wait}s for user {user_id}")


class SlidingWindowRateLimiter:
    """Sliding window rate limiter for tracking recent requests."""

    def __init__(self, window_seconds: int = 60, max_requests: int = 60):
        """Initialize sliding window rate limiter.

        Args:
            window_seconds: Time window in seconds
            max_requests: Maximum requests allowed in window
        """
        self.window_seconds = window_seconds
        self.max_requests = max_requests
        self.windows: Dict[str, deque] = {}  # user_id -> deque of timestamps
        self.lock = asyncio.Lock()

    async def check_limit(self, user_id: str) -> bool:
        """Check if request is within rate limit.

        Args:
            user_id: User identifier

        Returns:
            True if within limit, False if rate limited
        """
        async with self.lock:
            now = time.time()
            cutoff = now - self.window_seconds

            # Initialize window for new user
            if user_id not in self.windows:
                self.windows[user_id] = deque()

            window = self.windows[user_id]

            # Remove old timestamps outside window
            while window and window[0] < cutoff:
                window.popleft()

            # Check if within limit
            if len(window) < self.max_requests:
                window.append(now)
                return True
            else:
                logger.warning(
                    f"Rate limit exceeded for user {user_id}: "
                    f"{len(window)} requests in {self.window_seconds}s window"
                )
                return False

    def get_remaining(self, user_id: str) -> int:
        """Get remaining requests in current window.

        Args:
            user_id: User identifier

        Returns:
            Number of remaining requests
        """
        if user_id not in self.windows:
            return self.max_requests

        now = time.time()
        cutoff = now - self.window_seconds
        window = self.windows[user_id]

        # Count requests in current window
        recent_count = sum(1 for ts in window if ts >= cutoff)
        return max(0, self.max_requests - recent_count)
