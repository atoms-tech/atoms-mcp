"""
Rate limiting module for observability-kit.

Provides comprehensive rate limiting algorithms and advanced features:
- Fixed window, sliding window, token bucket, leaky bucket, adaptive algorithms
- Whitelist/blacklist support
- Violation tracking
- Redis support for distributed limiting
- Memory fallback when Redis unavailable

Extracted from atoms_mcp-old/infrastructure/rate_limiter.py and
zen-mcp-server/utils/advanced_ratelimit.py
"""

from .base import (
    RateLimiterBase,
    ViolationType,
    RateLimitViolation,
)
from .token_bucket import TokenBucketRateLimiter
from .sliding_window import SlidingWindowRateLimiter
from .fixed_window import FixedWindowRateLimiter
from .leaky_bucket import LeakyBucketRateLimiter
from .adaptive import AdaptiveRateLimiter
from .advanced_limiter import (
    AdvancedRateLimiter,
    LimitAlgorithm,
    LimitScope,
    RateLimit,
    RateLimitResult,
    get_rate_limiter,
    check_rate_limit,
)

__all__ = [
    # Base classes and types
    "RateLimiterBase",
    "ViolationType",
    "RateLimitViolation",

    # Basic limiters
    "TokenBucketRateLimiter",
    "SlidingWindowRateLimiter",
    "FixedWindowRateLimiter",
    "LeakyBucketRateLimiter",
    "AdaptiveRateLimiter",

    # Advanced limiter
    "AdvancedRateLimiter",
    "LimitAlgorithm",
    "LimitScope",
    "RateLimit",
    "RateLimitResult",
    "get_rate_limiter",
    "check_rate_limit",
]

