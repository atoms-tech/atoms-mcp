"""
Sliding window rate limiter implementation.

Provides precise rate limiting by tracking individual requests within a time window.

Extracted from atoms_mcp-old/infrastructure/rate_limiter.py (lines 98-166)
"""

from __future__ import annotations

import time
import asyncio
import logging
from typing import Dict
from collections import deque

from .base import RateLimiterBase

logger = logging.getLogger(__name__)


class SlidingWindowRateLimiter(RateLimiterBase):
    """
    Sliding window rate limiter for tracking recent requests.
    
    Tracks individual request timestamps within a sliding time window.
    More precise than token bucket but uses more memory.
    
    Features:
    - Precise request tracking
    - Sliding time window
    - Per-user tracking
    - Async-safe with locking
    
    Examples:
        >>> limiter = SlidingWindowRateLimiter(
        ...     window_seconds=60,
        ...     max_requests=100
        ... )
        >>> 
        >>> # Check if request is allowed
        >>> if await limiter.check_limit("user123"):
        ...     # Process request
        ...     pass
        ... else:
        ...     # Rate limited
        ...     pass
        >>> 
        >>> # Check remaining capacity
        >>> remaining = limiter.get_remaining("user123")
        >>> print(f"Remaining: {remaining}")
    """

    def __init__(
        self,
        window_seconds: int = 60,
        max_requests: int = 60,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize sliding window rate limiter.

        Args:
            window_seconds: Time window in seconds
            max_requests: Maximum requests allowed in window
            logger: Optional logger instance (uses module logger if not provided)
        
        Examples:
            >>> # 100 requests per minute
            >>> limiter = SlidingWindowRateLimiter(60, 100)
            >>> 
            >>> # 10 requests per 5 seconds
            >>> limiter = SlidingWindowRateLimiter(5, 10)
        """
        super().__init__()  # Initialize base class
        self.window_seconds = window_seconds
        self.max_requests = max_requests
        self.windows: Dict[str, deque] = {}  # user_id -> deque of timestamps
        self.lock = asyncio.Lock()
        self.logger = logger or globals()['logger']

    async def check_limit(self, user_id: str) -> bool:
        """
        Check if request is within rate limit.

        Args:
            user_id: User identifier

        Returns:
            True if within limit, False if rate limited
        
        Examples:
            >>> limiter = SlidingWindowRateLimiter(60, 100)
            >>> if await limiter.check_limit("user123"):
            ...     print("Request allowed")
            ... else:
            ...     print("Rate limited")
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
                self.logger.warning(
                    f"Rate limit exceeded for user {user_id}: "
                    f"{len(window)} requests in {self.window_seconds}s window"
                )
                return False

    async def acquire(self, user_id: str, tokens: int = 1) -> bool:
        """
        Acquire tokens (alias for check_limit for compatibility).
        
        Note: This implementation treats each token as a separate request.
        For tokens > 1, it will make multiple entries in the window.

        Args:
            user_id: User identifier
            tokens: Number of tokens to acquire

        Returns:
            True if tokens acquired, False if rate limited
        
        Examples:
            >>> limiter = SlidingWindowRateLimiter(60, 100)
            >>> if await limiter.acquire("user123", tokens=5):
            ...     print("5 tokens acquired")
        """
        # For sliding window, we check if we can add 'tokens' requests
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

            # Check if we can add 'tokens' requests
            if len(window) + tokens <= self.max_requests:
                for _ in range(tokens):
                    window.append(now)
                return True
            else:
                self.logger.warning(
                    f"Rate limit exceeded for user {user_id}: "
                    f"requested {tokens}, available {self.max_requests - len(window)}"
                )
                return False

    async def wait_if_needed(
        self,
        user_id: str,
        tokens: int = 1,
        max_wait: float = 30.0
    ) -> None:
        """
        Wait until capacity is available or timeout.

        Args:
            user_id: User identifier
            tokens: Number of tokens needed
            max_wait: Maximum seconds to wait

        Raises:
            TimeoutError: If max_wait exceeded
        
        Examples:
            >>> limiter = SlidingWindowRateLimiter(60, 100)
            >>> try:
            ...     await limiter.wait_if_needed("user123", max_wait=10.0)
            ...     print("Capacity available")
            ... except TimeoutError:
            ...     print("Timeout waiting for capacity")
        """
        start = time.time()

        while time.time() - start < max_wait:
            if await self.acquire(user_id, tokens):
                return

            # Wait a bit before retrying
            await asyncio.sleep(0.1)

        raise TimeoutError(
            f"Rate limit wait exceeded {max_wait}s for user {user_id}"
        )

    def get_remaining(self, user_id: str) -> int:
        """
        Get remaining requests in current window.

        Args:
            user_id: User identifier

        Returns:
            Number of remaining requests
        
        Examples:
            >>> limiter = SlidingWindowRateLimiter(60, 100)
            >>> remaining = limiter.get_remaining("user123")
            >>> print(f"Remaining requests: {remaining}")
        """
        if user_id not in self.windows:
            return self.max_requests

        now = time.time()
        cutoff = now - self.window_seconds
        window = self.windows[user_id]

        # Count requests in current window
        recent_count = sum(1 for ts in window if ts >= cutoff)
        return max(0, self.max_requests - recent_count)

    def reset(self, user_id: Optional[str] = None) -> None:
        """
        Reset rate limiter state.
        
        Args:
            user_id: User to reset, or None to reset all users
        
        Examples:
            >>> limiter = SlidingWindowRateLimiter(60, 100)
            >>> limiter.reset("user123")  # Reset specific user
            >>> limiter.reset()  # Reset all users
        """
        if user_id is None:
            self.windows.clear()
        elif user_id in self.windows:
            del self.windows[user_id]

