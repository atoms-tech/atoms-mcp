# Rate Limiting Migration Guide

## Overview

Advanced rate limiting features have been extracted from `zen-mcp-server/utils/advanced_ratelimit.py` into the `observability-kit` package for better reusability and maintainability.

## What's New

### New Rate Limiting Algorithms

1. **Fixed Window** (`FixedWindowRateLimiter`)
   - Simple fixed-window rate limiting
   - Memory-efficient
   - Optional Redis support

2. **Leaky Bucket** (`LeakyBucketRateLimiter`)
   - Constant leak rate
   - Smooth rate limiting
   - Burst capacity support

3. **Adaptive** (`AdaptiveRateLimiter`)
   - Behavior-based adjustment
   - Automatic penalty/recovery
   - Prevents abuse patterns

### Enhanced Features

- **Violation Tracking**: Track and analyze rate limit violations
- **Whitelist/Blacklist**: Flexible access control
- **Redis Support**: Distributed rate limiting with automatic memory fallback
- **Comprehensive Statistics**: Monitor rate limiting effectiveness

## Migration Steps

### For zen-mcp-server Users

The zen-mcp-server now uses a compatibility layer that automatically imports from observability-kit:

```python
# Old import (still works via compatibility layer)
from utils.advanced_ratelimit import get_rate_limiter, AdvancedRateLimiter

# New import (recommended for new code)
from utils.advanced_ratelimit_compat import get_rate_limiter, AdvancedRateLimiter

# Or use observability-kit directly
from observability.rate_limiting import (
    AdvancedRateLimiter,
    LimitAlgorithm,
    LimitScope,
    RateLimit,
    check_rate_limit,
)
```

### For New Projects

Install observability-kit and use the rate limiting module:

```python
from observability.rate_limiting import (
    # Advanced limiter
    AdvancedRateLimiter,
    LimitAlgorithm,
    LimitScope,
    RateLimit,
    RateLimitResult,

    # Basic limiters
    FixedWindowRateLimiter,
    SlidingWindowRateLimiter,
    TokenBucketRateLimiter,
    LeakyBucketRateLimiter,
    AdaptiveRateLimiter,

    # Support classes
    ViolationType,
    RateLimitViolation,
)
```

## Usage Examples

### Basic Fixed Window Limiter

```python
from observability.rate_limiting import FixedWindowRateLimiter

limiter = FixedWindowRateLimiter(
    window_seconds=60,
    max_requests=100
)

if await limiter.acquire("user123"):
    # Process request
    pass
else:
    # Rate limited
    pass
```

### Leaky Bucket with Redis

```python
import redis
from observability.rate_limiting import LeakyBucketRateLimiter

redis_client = redis.Redis(decode_responses=True)

limiter = LeakyBucketRateLimiter(
    leak_rate=100,  # 100 requests per minute
    capacity=150,   # Allow bursts up to 150
    redis_client=redis_client
)

if await limiter.acquire("user123"):
    # Process request
    pass
```

### Adaptive Rate Limiting

```python
from observability.rate_limiting import AdaptiveRateLimiter

limiter = AdaptiveRateLimiter(
    window_seconds=60,
    max_requests=100,
    penalty_factor=0.8,    # Reduce by 20% on penalty
    recovery_factor=1.05   # Increase by 5% on recovery
)

if await limiter.acquire("user123"):
    # Process request
    factor = limiter.get_adaptive_factor("user123")
    print(f"Current adjustment: {factor:.2f}x")
```

### Advanced Limiter with Multiple Algorithms

```python
from observability.rate_limiting import (
    AdvancedRateLimiter,
    LimitAlgorithm,
    LimitScope,
    RateLimit,
)

limiter = AdvancedRateLimiter()

# Add custom limits
limiter.add_limit(RateLimit(
    name="api_limit",
    algorithm=LimitAlgorithm.SLIDING_WINDOW,
    scope=LimitScope.USER,
    max_requests=1000,
    window_seconds=3600,
    burst_allowance=100
))

# Check rate limit
result = limiter.check_rate_limit("api_limit", "user123")
if result.allowed:
    print(f"Remaining: {result.remaining_requests}")
else:
    print(f"Rate limited. Retry after {result.retry_after_seconds}s")
```

### Whitelist/Blacklist

```python
from observability.rate_limiting import AdvancedRateLimiter

limiter = AdvancedRateLimiter()

# Whitelist a user (unlimited access)
limiter.add_to_whitelist("api_limit", "admin_user")

# Blacklist a user (no access)
limiter.add_to_blacklist("api_limit", "abusive_user")
```

### Violation Tracking

```python
from observability.rate_limiting import AdvancedRateLimiter, ViolationType
from datetime import datetime, timedelta, timezone

limiter = AdvancedRateLimiter()

# Get violations
violations = limiter.get_violations()

# Filter violations
recent = datetime.now(timezone.utc) - timedelta(hours=1)
recent_violations = limiter.get_violations(
    user_id="user123",
    violation_type=ViolationType.HARD_LIMIT,
    since=recent
)

# Get statistics
stats = limiter.get_statistics()
print(f"Total violations: {stats['total_violations']}")
```

## API Compatibility

### Class Name Changes

| Old Name | New Name | Notes |
|----------|----------|-------|
| `LimitViolation` | `RateLimitViolation` | Both names supported for compatibility |
| N/A | `FixedWindowRateLimiter` | New algorithm |
| N/A | `LeakyBucketRateLimiter` | New algorithm |
| N/A | `AdaptiveRateLimiter` | New algorithm |

### Method Compatibility

All existing methods from `AdvancedRateLimiter` are preserved:
- `check_rate_limit()`
- `add_limit()`
- `add_to_whitelist()`
- `add_to_blacklist()`
- `get_statistics()`

New methods available on base limiters:
- `get_remaining()` - Get remaining capacity
- `get_violations()` - Get violation records
- `record_violation()` - Record a violation
- `clear_violations()` - Clear violation records
- `is_whitelisted()` / `is_blacklisted()` - Check lists

## Breaking Changes

### None for zen-mcp-server

The compatibility layer ensures no breaking changes for zen-mcp-server. All existing code will continue to work.

### For Direct Imports (if applicable)

- `LimitViolation` is now `RateLimitViolation` (old name still works as alias)
- Base limiters now require calling `super().__init__()` if extending

## Testing

Run the test suite to ensure everything works:

```bash
# Test observability-kit
cd pheno-sdk/observability-kit
pytest tests/test_advanced_rate_limiting.py -v

# Run examples
python examples/advanced_rate_limiting.py
```

## Performance Notes

- **Memory Usage**: Adaptive limiter maintains per-user factors in memory
- **Redis**: Optional Redis support provides distributed limiting with automatic fallback
- **Violation Tracking**: Limited to last 1000 violations (configurable in base class)

## Troubleshooting

### ImportError: No module named 'observability'

Ensure observability-kit is installed:
```bash
cd pheno-sdk/observability-kit
pip install -e .
```

### Redis Connection Issues

Rate limiters automatically fall back to memory-based limiting if Redis is unavailable:
```python
# This will use Redis if available, memory fallback otherwise
limiter = FixedWindowRateLimiter(
    window_seconds=60,
    max_requests=100,
    redis_client=redis_client  # Optional
)
```

### Type Compatibility

If using type hints, import from the new location:
```python
from observability.rate_limiting import (
    RateLimitResult,
    RateLimitViolation,
    LimitAlgorithm,
)
```

## Future Enhancements

Planned features:
- [ ] Distributed rate limiting coordination
- [ ] Time-based whitelist/blacklist (temporary)
- [ ] Custom violation handlers
- [ ] Integration with metrics systems
- [ ] Rate limit templates

## Support

For issues or questions:
1. Check the examples in `examples/advanced_rate_limiting.py`
2. Review tests in `tests/test_advanced_rate_limiting.py`
3. See the main README at the root of observability-kit
