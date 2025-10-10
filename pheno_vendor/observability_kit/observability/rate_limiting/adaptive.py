"""
Adaptive rate limiter implementation.

Provides intelligent rate limiting that adapts based on user behavior.
Applies penalties for aggressive usage and allows gradual recovery for good behavior.

Extracted from zen-mcp-server/utils/advanced_ratelimit.py
"""

from __future__ import annotations

import time
import asyncio
import logging
from typing import Dict, Optional
from collections import defaultdict

from .base import RateLimiterBase
from .sliding_window import SlidingWindowRateLimiter

logger = logging.getLogger(__name__)


class AdaptiveRateLimiter(RateLimiterBase):
    """
    Adaptive rate limiter that adjusts limits based on user behavior.

    Uses a base sliding window limiter and applies dynamic adjustment factors.
    Penalizes aggressive usage patterns and allows gradual recovery for
    well-behaved clients.

    Features:
    - Behavior-based limit adjustment
    - Penalty for aggressive usage (< 10% remaining capacity)
    - Gradual recovery for good behavior (> 80% remaining capacity)
    - Per-user adaptive factors
    - Configurable penalty and recovery rates
    - Async-safe with locking

    Examples:
        >>> # Create adaptive limiter
        >>> limiter = AdaptiveRateLimiter(
        ...     window_seconds=60,
        ...     max_requests=100,
        ...     penalty_factor=0.8,    # Reduce limit by 20% on penalty
        ...     recovery_factor=1.05   # Increase by 5% on recovery
        ... )
        >>>
        >>> # Check if request is allowed (adapts automatically)
        >>> if await limiter.acquire("user123"):
        ...     # Process request
        ...     pass
        ... else:
        ...     # Rate limited
        ...     pass
        >>>
        >>> # Get current adaptive factor
        >>> factor = limiter.get_adaptive_factor("user123")
        >>> print(f"Current adjustment: {factor:.2f}x")
    """

    def __init__(
        self,
        window_seconds: int = 60,
        max_requests: int = 60,
        penalty_factor: float = 0.8,
        recovery_factor: float = 1.05,
        min_factor: float = 0.1,
        max_factor: float = 1.0,
        penalty_threshold: float = 0.1,
        recovery_threshold: float = 0.8,
        logger_instance: Optional[logging.Logger] = None
    ):
        """
        Initialize adaptive rate limiter.

        Args:
            window_seconds: Time window in seconds
            max_requests: Base maximum requests per window
            penalty_factor: Multiplier to apply on penalty (default: 0.8 = 20% reduction)
            recovery_factor: Multiplier to apply on recovery (default: 1.05 = 5% increase)
            min_factor: Minimum adaptive factor (default: 0.1 = 10% of base limit)
            max_factor: Maximum adaptive factor (default: 1.0 = 100% of base limit)
            penalty_threshold: Apply penalty when remaining < this ratio (default: 0.1)
            recovery_threshold: Apply recovery when remaining > this ratio (default: 0.8)
            logger_instance: Optional logger instance (uses module logger if not provided)

        Examples:
            >>> # Aggressive penalty settings
            >>> limiter = AdaptiveRateLimiter(
            ...     window_seconds=60,
            ...     max_requests=100,
            ...     penalty_factor=0.7,    # 30% reduction on penalty
            ...     recovery_factor=1.02   # Slow recovery
            ... )
            >>>
            >>> # Lenient settings
            >>> limiter = AdaptiveRateLimiter(
            ...     window_seconds=60,
            ...     max_requests=100,
            ...     penalty_factor=0.9,    # Only 10% reduction
            ...     recovery_factor=1.1    # Fast recovery
            ... )
        """
        super().__init__()  # Initialize base class
        self.window_seconds = window_seconds
        self.max_requests = max_requests
        self.penalty_factor = penalty_factor
        self.recovery_factor = recovery_factor
        self.min_factor = min_factor
        self.max_factor = max_factor
        self.penalty_threshold = penalty_threshold
        self.recovery_threshold = recovery_threshold
        self.logger = logger_instance or logger

        # Base limiter (using sliding window)
        self.base_limiter = SlidingWindowRateLimiter(
            window_seconds=window_seconds,
            max_requests=max_requests,
            logger=self.logger
        )

        # Adaptive factors for each user
        self.adaptive_factors: Dict[str, float] = defaultdict(lambda: 1.0)
        self.lock = asyncio.Lock()

        # Statistics
        self.stats = {
            "total_penalties": 0,
            "total_recoveries": 0,
            "active_penalties": 0
        }

    async def acquire(self, user_id: str, tokens: int = 1) -> bool:
        """
        Acquire tokens with adaptive limit adjustment.

        Args:
            user_id: User identifier
            tokens: Number of tokens to acquire (default: 1)

        Returns:
            True if tokens acquired, False if rate limited

        Examples:
            >>> limiter = AdaptiveRateLimiter(60, 100)
            >>> if await limiter.acquire("user123"):
            ...     print("Request allowed")
            ... else:
            ...     print("Rate limited (possibly penalized)")
        """
        async with self.lock:
            # Get current adaptive factor
            factor = self.adaptive_factors[user_id]

            # Calculate effective limit
            effective_limit = int(self.max_requests * factor)
            effective_limit = max(1, effective_limit)  # At least 1 request

            # Temporarily adjust base limiter's max_requests
            original_max = self.base_limiter.max_requests
            self.base_limiter.max_requests = effective_limit

            # Try to acquire from base limiter
            allowed = await self.base_limiter.acquire(user_id, tokens)

            # Restore original limit
            self.base_limiter.max_requests = original_max

            # Apply adaptive adjustment based on remaining capacity
            remaining = self.base_limiter.get_remaining(user_id)
            await self._apply_adaptive_adjustment(user_id, remaining, effective_limit, allowed)

            return allowed

    async def _apply_adaptive_adjustment(
        self,
        user_id: str,
        remaining: int,
        effective_limit: int,
        was_allowed: bool
    ):
        """Apply adaptive factor adjustments based on behavior."""
        if effective_limit == 0:
            return

        remaining_ratio = remaining / effective_limit

        current_factor = self.adaptive_factors[user_id]
        previous_factor = current_factor

        # Apply penalty if remaining capacity is low (< 10% by default)
        if remaining_ratio < self.penalty_threshold:
            if current_factor > self.min_factor:
                self.adaptive_factors[user_id] = max(
                    self.min_factor,
                    current_factor * self.penalty_factor
                )
                self.stats["total_penalties"] += 1
                if previous_factor == 1.0:
                    self.stats["active_penalties"] += 1
                self.logger.info(
                    f"Applied adaptive penalty to {user_id}: "
                    f"{previous_factor:.2f} -> {self.adaptive_factors[user_id]:.2f}"
                )

        # Apply recovery if remaining capacity is high (> 80% by default)
        elif remaining_ratio > self.recovery_threshold:
            if current_factor < self.max_factor:
                self.adaptive_factors[user_id] = min(
                    self.max_factor,
                    current_factor * self.recovery_factor
                )
                self.stats["total_recoveries"] += 1
                if self.adaptive_factors[user_id] == 1.0 and previous_factor < 1.0:
                    self.stats["active_penalties"] -= 1
                self.logger.debug(
                    f"Applied adaptive recovery to {user_id}: "
                    f"{previous_factor:.2f} -> {self.adaptive_factors[user_id]:.2f}"
                )

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
            >>> limiter = AdaptiveRateLimiter(60, 100)
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

            await asyncio.sleep(0.1)

        raise TimeoutError(
            f"Rate limit wait exceeded {max_wait}s for user {user_id}"
        )

    def get_remaining(self, user_id: str) -> Optional[int]:
        """
        Get remaining requests with adaptive adjustment.

        Args:
            user_id: User identifier

        Returns:
            Number of remaining requests based on adaptive limit

        Examples:
            >>> limiter = AdaptiveRateLimiter(60, 100)
            >>> remaining = limiter.get_remaining("user123")
            >>> if remaining is not None:
            ...     print(f"Remaining (adaptive): {remaining}")
        """
        factor = self.adaptive_factors[user_id]
        effective_limit = int(self.max_requests * factor)

        # Get remaining from base limiter
        base_remaining = self.base_limiter.get_remaining(user_id)
        if base_remaining is None:
            return None

        # Adjust based on effective limit
        return min(base_remaining, effective_limit)

    def get_adaptive_factor(self, user_id: str) -> float:
        """
        Get current adaptive factor for a user.

        Args:
            user_id: User identifier

        Returns:
            Current adaptive factor (1.0 = normal, < 1.0 = penalized)

        Examples:
            >>> limiter = AdaptiveRateLimiter(60, 100)
            >>> factor = limiter.get_adaptive_factor("user123")
            >>> print(f"Current factor: {factor:.2f}x")
            >>> if factor < 1.0:
            ...     print("User is currently penalized")
        """
        return self.adaptive_factors[user_id]

    def get_effective_limit(self, user_id: str) -> int:
        """
        Get effective rate limit for a user.

        Args:
            user_id: User identifier

        Returns:
            Current effective limit based on adaptive factor

        Examples:
            >>> limiter = AdaptiveRateLimiter(60, 100)
            >>> effective = limiter.get_effective_limit("user123")
            >>> base = 100
            >>> print(f"Effective limit: {effective}/{base}")
        """
        factor = self.adaptive_factors[user_id]
        return max(1, int(self.max_requests * factor))

    def reset_adaptive_factor(self, user_id: str):
        """
        Reset adaptive factor for a user to 1.0 (normal).

        Args:
            user_id: User identifier

        Examples:
            >>> limiter = AdaptiveRateLimiter(60, 100)
            >>> limiter.reset_adaptive_factor("user123")
            >>> assert limiter.get_adaptive_factor("user123") == 1.0
        """
        if user_id in self.adaptive_factors:
            old_factor = self.adaptive_factors[user_id]
            del self.adaptive_factors[user_id]
            if old_factor < 1.0:
                self.stats["active_penalties"] -= 1
            self.logger.info(f"Reset adaptive factor for {user_id}")

    def get_statistics(self) -> Dict:
        """
        Get adaptive rate limiter statistics.

        Returns:
            Dictionary containing statistics about penalties and recoveries

        Examples:
            >>> limiter = AdaptiveRateLimiter(60, 100)
            >>> stats = limiter.get_statistics()
            >>> print(f"Total penalties: {stats['total_penalties']}")
            >>> print(f"Active penalties: {stats['active_penalties']}")
        """
        return {
            **self.stats,
            "total_users": len(self.adaptive_factors),
            "penalized_users": sum(1 for f in self.adaptive_factors.values() if f < 1.0),
            "average_factor": sum(self.adaptive_factors.values()) / len(self.adaptive_factors)
            if self.adaptive_factors
            else 1.0,
        }

    def reset(self, user_id: Optional[str] = None) -> None:
        """
        Reset rate limiter state.

        Args:
            user_id: User to reset, or None to reset all users

        Examples:
            >>> limiter = AdaptiveRateLimiter(60, 100)
            >>> limiter.reset("user123")  # Reset specific user
            >>> limiter.reset()  # Reset all users
        """
        if user_id is None:
            # Reset all
            self.adaptive_factors.clear()
            self.base_limiter.reset()
            self.stats["active_penalties"] = 0
        else:
            # Reset specific user
            if user_id in self.adaptive_factors:
                if self.adaptive_factors[user_id] < 1.0:
                    self.stats["active_penalties"] -= 1
                del self.adaptive_factors[user_id]
            self.base_limiter.reset(user_id)
