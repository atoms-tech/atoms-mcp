"""
Advanced rate limiter combining multiple algorithms.

Provides a comprehensive rate limiting solution with:
- Multiple algorithms (fixed window, sliding window, token bucket, leaky bucket, adaptive)
- Whitelist/blacklist support
- Violation tracking and statistics
- Redis support for distributed limiting
- Memory fallback when Redis unavailable

Extracted from zen-mcp-server/utils/advanced_ratelimit.py
"""

from __future__ import annotations

import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Set
from datetime import datetime, timezone, timedelta

try:
    import redis
except ImportError:
    redis = None

from .base import RateLimiterBase, ViolationType, RateLimitViolation
from .fixed_window import FixedWindowRateLimiter
from .sliding_window import SlidingWindowRateLimiter
from .token_bucket import TokenBucketRateLimiter
from .leaky_bucket import LeakyBucketRateLimiter
from .adaptive import AdaptiveRateLimiter

logger = logging.getLogger(__name__)


class LimitAlgorithm(str, Enum):
    """Rate limiting algorithms."""

    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"
    ADAPTIVE = "adaptive"


class LimitScope(str, Enum):
    """Rate limiting scopes."""

    GLOBAL = "global"
    IP = "ip"
    USER = "user"
    API_KEY = "api_key"
    ENDPOINT = "endpoint"
    COMBINED = "combined"


@dataclass
class RateLimit:
    """Rate limit configuration."""

    name: str
    algorithm: LimitAlgorithm
    scope: LimitScope
    max_requests: int
    window_seconds: int
    burst_allowance: int = 0
    recovery_time_seconds: int = 300
    enabled: bool = True
    penalty_multiplier: float = 1.0
    whitelist: Set[str] = field(default_factory=set)
    blacklist: Set[str] = field(default_factory=set)


@dataclass
class RateLimitResult:
    """Result of rate limit check."""

    allowed: bool
    limit_name: str
    remaining_requests: int
    reset_time: datetime
    retry_after_seconds: Optional[int] = None
    violation: Optional[RateLimitViolation] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class AdvancedRateLimiter:
    """
    Advanced rate limiter with multiple algorithms and adaptive behavior.

    Combines multiple rate limiting algorithms with comprehensive features:
    - Multiple algorithms for different use cases
    - Whitelist/blacklist support
    - Violation tracking
    - Statistics and monitoring
    - Redis support for distributed limiting
    - Memory fallback when Redis unavailable

    Examples:
        >>> # Create advanced limiter with Redis
        >>> import redis
        >>> client = redis.Redis(decode_responses=True)
        >>> limiter = AdvancedRateLimiter(redis_client=client)
        >>>
        >>> # Add custom rate limit
        >>> limit = RateLimit(
        ...     name="api_limit",
        ...     algorithm=LimitAlgorithm.SLIDING_WINDOW,
        ...     scope=LimitScope.USER,
        ...     max_requests=100,
        ...     window_seconds=60
        ... )
        >>> limiter.add_limit(limit)
        >>>
        >>> # Check rate limit
        >>> result = limiter.check_rate_limit("api_limit", "user123")
        >>> if result.allowed:
        ...     # Process request
        ...     pass
        ... else:
        ...     print(f"Rate limited. Retry after {result.retry_after_seconds}s")
    """

    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
        init_default_limits: bool = True,
        logger_instance: Optional[logging.Logger] = None
    ):
        """
        Initialize the advanced rate limiter.

        Args:
            redis_client: Optional Redis client for distributed limiting
            init_default_limits: Whether to initialize default limits
            logger_instance: Optional logger instance

        Examples:
            >>> # With Redis
            >>> import redis
            >>> r = redis.Redis(decode_responses=True)
            >>> limiter = AdvancedRateLimiter(redis_client=r)
            >>>
            >>> # Without default limits
            >>> limiter = AdvancedRateLimiter(init_default_limits=False)
        """
        self.redis_client = redis_client
        self.logger = logger_instance or logger
        self.limits: Dict[str, RateLimit] = {}
        self.limiters: Dict[str, RateLimiterBase] = {}
        self.statistics = {
            "total_requests": 0,
            "total_violations": 0,
            "violations_by_type": {},
        }

        if init_default_limits:
            self._init_default_limits()

    def _init_default_limits(self):
        """Initialize default rate limit configurations."""
        default_limits = [
            # Global API limits
            RateLimit(
                name="global_api",
                algorithm=LimitAlgorithm.SLIDING_WINDOW,
                scope=LimitScope.GLOBAL,
                max_requests=10000,
                window_seconds=3600,
                burst_allowance=500,
            ),
            # Per-IP limits
            RateLimit(
                name="ip_requests",
                algorithm=LimitAlgorithm.TOKEN_BUCKET,
                scope=LimitScope.IP,
                max_requests=1000,
                window_seconds=3600,
                burst_allowance=50,
            ),
            # Per-user limits
            RateLimit(
                name="user_requests",
                algorithm=LimitAlgorithm.SLIDING_WINDOW,
                scope=LimitScope.USER,
                max_requests=5000,
                window_seconds=3600,
                burst_allowance=100,
            ),
            # API key limits
            RateLimit(
                name="api_key_requests",
                algorithm=LimitAlgorithm.FIXED_WINDOW,
                scope=LimitScope.API_KEY,
                max_requests=10000,
                window_seconds=3600,
                burst_allowance=200,
            ),
            # Endpoint-specific limits
            RateLimit(
                name="mcp_endpoint",
                algorithm=LimitAlgorithm.LEAKY_BUCKET,
                scope=LimitScope.ENDPOINT,
                max_requests=500,
                window_seconds=60,
                burst_allowance=25,
            ),
            # Anti-abuse patterns
            RateLimit(
                name="burst_protection",
                algorithm=LimitAlgorithm.ADAPTIVE,
                scope=LimitScope.IP,
                max_requests=100,
                window_seconds=60,
                burst_allowance=10,
            ),
        ]

        for limit in default_limits:
            self.add_limit(limit)

    def add_limit(self, rate_limit: RateLimit):
        """
        Add a rate limit configuration.

        Args:
            rate_limit: Rate limit configuration to add

        Examples:
            >>> limiter = AdvancedRateLimiter()
            >>> limit = RateLimit(
            ...     name="custom_limit",
            ...     algorithm=LimitAlgorithm.SLIDING_WINDOW,
            ...     scope=LimitScope.USER,
            ...     max_requests=50,
            ...     window_seconds=60
            ... )
            >>> limiter.add_limit(limit)
        """
        self.limits[rate_limit.name] = rate_limit

        # Create appropriate limiter instance
        limiter = self._create_limiter(rate_limit)
        self.limiters[rate_limit.name] = limiter

        self.logger.info(f"Added rate limit: {rate_limit.name} ({rate_limit.algorithm.value})")

    def _create_limiter(self, rate_limit: RateLimit) -> RateLimiterBase:
        """Create limiter instance based on algorithm."""
        if rate_limit.algorithm == LimitAlgorithm.FIXED_WINDOW:
            return FixedWindowRateLimiter(
                window_seconds=rate_limit.window_seconds,
                max_requests=rate_limit.max_requests,
                redis_client=self.redis_client,
                logger_instance=self.logger
            )
        elif rate_limit.algorithm == LimitAlgorithm.SLIDING_WINDOW:
            return SlidingWindowRateLimiter(
                window_seconds=rate_limit.window_seconds,
                max_requests=rate_limit.max_requests,
                logger=self.logger
            )
        elif rate_limit.algorithm == LimitAlgorithm.TOKEN_BUCKET:
            requests_per_minute = (rate_limit.max_requests / rate_limit.window_seconds) * 60
            return TokenBucketRateLimiter(
                requests_per_minute=int(requests_per_minute),
                burst_size=rate_limit.max_requests + rate_limit.burst_allowance,
                logger=self.logger
            )
        elif rate_limit.algorithm == LimitAlgorithm.LEAKY_BUCKET:
            leak_rate = (rate_limit.max_requests / rate_limit.window_seconds) * 60
            return LeakyBucketRateLimiter(
                leak_rate=leak_rate,
                capacity=rate_limit.max_requests + rate_limit.burst_allowance,
                window_seconds=rate_limit.window_seconds,
                redis_client=self.redis_client,
                logger_instance=self.logger
            )
        elif rate_limit.algorithm == LimitAlgorithm.ADAPTIVE:
            return AdaptiveRateLimiter(
                window_seconds=rate_limit.window_seconds,
                max_requests=rate_limit.max_requests,
                logger_instance=self.logger
            )
        else:
            # Default to fixed window
            return FixedWindowRateLimiter(
                window_seconds=rate_limit.window_seconds,
                max_requests=rate_limit.max_requests,
                redis_client=self.redis_client,
                logger_instance=self.logger
            )

    def check_rate_limit(
        self,
        limit_name: str,
        scope_value: str,
        request_weight: int = 1,
        context: Optional[Dict[str, Any]] = None
    ) -> RateLimitResult:
        """
        Check if a request should be rate limited.

        Args:
            limit_name: Name of the rate limit to check
            scope_value: Value for the scope (IP, user ID, API key, etc.)
            request_weight: Weight of the request (default 1)
            context: Additional context for the request

        Returns:
            RateLimitResult indicating if request is allowed

        Examples:
            >>> limiter = AdvancedRateLimiter()
            >>> result = limiter.check_rate_limit("api_limit", "user123")
            >>> if result.allowed:
            ...     print(f"Request allowed. Remaining: {result.remaining_requests}")
            ... else:
            ...     print(f"Rate limited. Reset at: {result.reset_time}")
        """
        if limit_name not in self.limits:
            return RateLimitResult(
                allowed=True,
                limit_name=limit_name,
                remaining_requests=-1,
                reset_time=datetime.now(timezone.utc),
                metadata={"error": "Limit configuration not found"},
            )

        rate_limit = self.limits[limit_name]
        limiter = self.limiters[limit_name]
        context = context or {}

        # Update statistics
        self.statistics["total_requests"] += 1

        # Check blacklist
        if scope_value in rate_limit.blacklist or limiter.is_blacklisted(scope_value):
            violation = limiter.record_violation(
                user_id=scope_value,
                violation_type=ViolationType.ABUSE_PATTERN,
                requests_count=request_weight,
                limit_value=0,
                metadata={"reason": "blacklisted"}
            )
            self.statistics["total_violations"] += 1
            return RateLimitResult(
                allowed=False,
                limit_name=limit_name,
                remaining_requests=0,
                reset_time=datetime.now(timezone.utc) + timedelta(seconds=rate_limit.recovery_time_seconds),
                violation=violation,
            )

        # Check whitelist
        if scope_value in rate_limit.whitelist or limiter.is_whitelisted(scope_value):
            return RateLimitResult(
                allowed=True,
                limit_name=limit_name,
                remaining_requests=-1,
                reset_time=datetime.now(timezone.utc),
                metadata={"reason": "whitelisted"},
            )

        # Skip if disabled
        if not rate_limit.enabled:
            return RateLimitResult(
                allowed=True,
                limit_name=limit_name,
                remaining_requests=-1,
                reset_time=datetime.now(timezone.utc),
                metadata={"reason": "disabled"},
            )

        # Check with appropriate limiter (async wrapper)
        import asyncio
        try:
            # Run async acquire in sync context
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Already in async context
                future = asyncio.ensure_future(limiter.acquire(scope_value, request_weight))
                allowed = loop.run_until_complete(future)
            else:
                allowed = asyncio.run(limiter.acquire(scope_value, request_weight))
        except RuntimeError:
            # Fallback for sync context
            allowed = asyncio.run(limiter.acquire(scope_value, request_weight))

        remaining = limiter.get_remaining(scope_value) or 0

        if not allowed:
            violation = limiter.record_violation(
                user_id=scope_value,
                violation_type=ViolationType.HARD_LIMIT,
                requests_count=request_weight,
                limit_value=rate_limit.max_requests,
                metadata=context
            )
            self.statistics["total_violations"] += 1
            self.statistics["violations_by_type"][ViolationType.HARD_LIMIT.value] = \
                self.statistics["violations_by_type"].get(ViolationType.HARD_LIMIT.value, 0) + 1

            return RateLimitResult(
                allowed=False,
                limit_name=limit_name,
                remaining_requests=0,
                reset_time=datetime.now(timezone.utc) + timedelta(seconds=rate_limit.window_seconds),
                retry_after_seconds=rate_limit.window_seconds,
                violation=violation,
            )

        return RateLimitResult(
            allowed=True,
            limit_name=limit_name,
            remaining_requests=remaining,
            reset_time=datetime.now(timezone.utc) + timedelta(seconds=rate_limit.window_seconds),
        )

    def add_to_whitelist(self, limit_name: str, scope_value: str):
        """
        Add scope value to whitelist for a specific limit.

        Args:
            limit_name: Name of the rate limit
            scope_value: Value to whitelist

        Examples:
            >>> limiter = AdvancedRateLimiter()
            >>> limiter.add_to_whitelist("api_limit", "admin_user")
        """
        if limit_name in self.limits:
            self.limits[limit_name].whitelist.add(scope_value)
            if limit_name in self.limiters:
                self.limiters[limit_name].add_to_whitelist(scope_value)
            self.logger.info(f"Added {scope_value} to whitelist for {limit_name}")

    def add_to_blacklist(self, limit_name: str, scope_value: str):
        """
        Add scope value to blacklist for a specific limit.

        Args:
            limit_name: Name of the rate limit
            scope_value: Value to blacklist

        Examples:
            >>> limiter = AdvancedRateLimiter()
            >>> limiter.add_to_blacklist("api_limit", "abusive_user")
        """
        if limit_name in self.limits:
            self.limits[limit_name].blacklist.add(scope_value)
            if limit_name in self.limiters:
                self.limiters[limit_name].add_to_blacklist(scope_value)
            self.logger.warning(f"Added {scope_value} to blacklist for {limit_name}")

    def get_violations(self, limit_name: Optional[str] = None) -> list[RateLimitViolation]:
        """
        Get violations from limiters.

        Args:
            limit_name: Optional limit name to filter by

        Returns:
            List of violations

        Examples:
            >>> limiter = AdvancedRateLimiter()
            >>> violations = limiter.get_violations()
            >>> print(f"Total violations: {len(violations)}")
        """
        violations = []
        if limit_name and limit_name in self.limiters:
            violations = self.limiters[limit_name].get_violations()
        else:
            for limiter in self.limiters.values():
                violations.extend(limiter.get_violations())
        return violations

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get rate limiter statistics.

        Returns:
            Dictionary containing statistics

        Examples:
            >>> limiter = AdvancedRateLimiter()
            >>> stats = limiter.get_statistics()
            >>> print(f"Total requests: {stats['total_requests']}")
            >>> print(f"Total violations: {stats['total_violations']}")
        """
        return {
            **self.statistics,
            "active_limits": len(self.limits),
            "total_violations": sum(
                limiter.get_violation_count() for limiter in self.limiters.values()
            ),
        }


# Global rate limiter instance
_rate_limiter_instance: Optional[AdvancedRateLimiter] = None


def get_rate_limiter() -> AdvancedRateLimiter:
    """Get the global advanced rate limiter instance."""
    global _rate_limiter_instance
    if _rate_limiter_instance is None:
        _rate_limiter_instance = AdvancedRateLimiter()
    return _rate_limiter_instance


def check_rate_limit(
    limit_name: str,
    scope_value: str,
    request_weight: int = 1,
    context: Optional[Dict[str, Any]] = None
) -> RateLimitResult:
    """Convenience function to check rate limit using the global limiter."""
    return get_rate_limiter().check_rate_limit(limit_name, scope_value, request_weight, context)
