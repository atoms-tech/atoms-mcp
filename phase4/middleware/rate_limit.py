"""Rate limiting middleware for token operations."""

from __future__ import annotations

import os
from datetime import datetime, timedelta

from utils.logging_setup import get_logger

from ..storage import StorageBackend, get_storage_backend

logger = get_logger(__name__)


class RateLimiter:
    """Rate limiter for authentication operations.

    Implements sliding window rate limiting with exponential backoff
    for failed attempts.
    """

    def __init__(
        self,
        storage: StorageBackend | None = None,
        window_seconds: int | None = None,
        max_requests: int | None = None,
    ):
        """Initialize rate limiter.

        Args:
            storage: Storage backend
            window_seconds: Time window in seconds
            max_requests: Maximum requests per window
        """
        self.storage = storage or get_storage_backend()

        # Configuration
        self.window_seconds = window_seconds or int(
            os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60")
        )
        self.max_requests = max_requests or int(
            os.getenv("RATE_LIMIT_REFRESH_PER_MINUTE", "10")
        )

        # Backoff configuration
        self.enable_backoff = os.getenv("ENABLE_RATE_LIMIT_BACKOFF", "true").lower() == "true"
        self.backoff_multiplier = float(os.getenv("BACKOFF_MULTIPLIER", "2.0"))
        self.max_backoff_seconds = int(os.getenv("MAX_BACKOFF_SECONDS", "3600"))

    async def check_limit(
        self,
        identifier: str,
        operation: str = "token_refresh",
    ) -> tuple[bool, int | None]:
        """Check if operation is within rate limit.

        Args:
            identifier: User ID or session ID
            operation: Operation type

        Returns:
            (is_allowed, retry_after_seconds)
        """
        key = f"rate_limit:{operation}:{identifier}"

        # Check if in backoff period
        if self.enable_backoff:
            backoff_until = await self._get_backoff(identifier, operation)
            if backoff_until:
                now = datetime.utcnow()
                if now < backoff_until:
                    retry_after = int((backoff_until - now).total_seconds())
                    logger.warning(
                        f"Rate limit backoff for {identifier}: {retry_after}s remaining"
                    )
                    return False, retry_after

        # Get current count
        current = await self.storage.get(key) or 0

        if current >= self.max_requests:
            # Limit exceeded
            retry_after = await self._calculate_retry_after(key)

            # Set backoff if enabled
            if self.enable_backoff:
                await self._set_backoff(identifier, operation, retry_after)

            logger.warning(
                f"Rate limit exceeded for {identifier}: {current}/{self.max_requests}"
            )
            return False, retry_after

        # Increment counter
        new_count = await self.storage.incr(key)

        # Set expiration on first request
        if new_count == 1:
            await self.storage.expire(key, self.window_seconds)

        logger.debug(
            f"Rate limit check passed for {identifier}: {new_count}/{self.max_requests}"
        )
        return True, None

    async def record_success(
        self,
        identifier: str,
        operation: str = "token_refresh",
    ) -> None:
        """Record successful operation, reset backoff.

        Args:
            identifier: User ID or session ID
            operation: Operation type
        """
        if self.enable_backoff:
            await self._clear_backoff(identifier, operation)

    async def record_failure(
        self,
        identifier: str,
        operation: str = "token_refresh",
    ) -> None:
        """Record failed operation, increase backoff.

        Args:
            identifier: User ID or session ID
            operation: Operation type
        """
        if not self.enable_backoff:
            return

        # Increment failure count
        failure_key = f"rate_limit:failures:{operation}:{identifier}"
        failures = await self.storage.incr(failure_key)

        # Calculate backoff duration
        backoff_seconds = min(
            int(self.backoff_multiplier ** failures),
            self.max_backoff_seconds
        )

        # Set backoff
        await self._set_backoff(identifier, operation, backoff_seconds)

        logger.warning(
            f"Rate limit failure recorded for {identifier}: "
            f"{failures} failures, {backoff_seconds}s backoff"
        )

    async def get_remaining(
        self,
        identifier: str,
        operation: str = "token_refresh",
    ) -> int:
        """Get remaining requests in current window.

        Args:
            identifier: User ID or session ID
            operation: Operation type

        Returns:
            Number of remaining requests
        """
        key = f"rate_limit:{operation}:{identifier}"
        current = await self.storage.get(key) or 0
        return max(0, self.max_requests - current)

    async def reset(
        self,
        identifier: str,
        operation: str = "token_refresh",
    ) -> None:
        """Reset rate limit for identifier.

        Args:
            identifier: User ID or session ID
            operation: Operation type
        """
        key = f"rate_limit:{operation}:{identifier}"
        await self.storage.delete(key)

        if self.enable_backoff:
            await self._clear_backoff(identifier, operation)

        logger.info(f"Rate limit reset for {identifier}")

    async def _calculate_retry_after(self, key: str) -> int:
        """Calculate retry-after seconds.

        Args:
            key: Rate limit key

        Returns:
            Seconds until retry allowed
        """
        ttl = await self.storage.ttl(key)
        return ttl if ttl else self.window_seconds

    async def _get_backoff(
        self,
        identifier: str,
        operation: str
    ) -> datetime | None:
        """Get backoff expiration time.

        Args:
            identifier: User ID or session ID
            operation: Operation type

        Returns:
            Backoff expiration time if in backoff
        """
        backoff_key = f"rate_limit:backoff:{operation}:{identifier}"
        backoff_data = await self.storage.get(backoff_key)

        if backoff_data and isinstance(backoff_data, dict):
            backoff_until = backoff_data.get("until")
            if backoff_until:
                return datetime.fromisoformat(backoff_until)

        return None

    async def _set_backoff(
        self,
        identifier: str,
        operation: str,
        seconds: int
    ) -> None:
        """Set backoff period.

        Args:
            identifier: User ID or session ID
            operation: Operation type
            seconds: Backoff duration in seconds
        """
        backoff_key = f"rate_limit:backoff:{operation}:{identifier}"
        backoff_until = datetime.utcnow() + timedelta(seconds=seconds)

        await self.storage.set(
            backoff_key,
            {
                "until": backoff_until.isoformat(),
                "seconds": seconds,
                "set_at": datetime.utcnow().isoformat(),
            },
            expire=seconds
        )

    async def _clear_backoff(
        self,
        identifier: str,
        operation: str
    ) -> None:
        """Clear backoff period.

        Args:
            identifier: User ID or session ID
            operation: Operation type
        """
        backoff_key = f"rate_limit:backoff:{operation}:{identifier}"
        failure_key = f"rate_limit:failures:{operation}:{identifier}"

        await self.storage.delete(backoff_key)
        await self.storage.delete(failure_key)


class GlobalRateLimiter:
    """Global rate limiter for system-wide protection."""

    def __init__(
        self,
        storage: StorageBackend | None = None,
        max_requests_per_second: int | None = None,
    ):
        """Initialize global rate limiter.

        Args:
            storage: Storage backend
            max_requests_per_second: Global limit
        """
        self.storage = storage or get_storage_backend()
        self.max_rps = max_requests_per_second or int(
            os.getenv("GLOBAL_MAX_RPS", "1000")
        )

    async def check_limit(self) -> bool:
        """Check global rate limit.

        Returns:
            True if allowed
        """
        # Use current second as key
        now = datetime.utcnow()
        key = f"global_rate:{now.strftime('%Y%m%d%H%M%S')}"

        count = await self.storage.incr(key)

        # Set 2-second expiry
        if count == 1:
            await self.storage.expire(key, 2)

        return count <= self.max_rps
