"""
Base rate limiter interface.

Provides abstract base class for rate limiting implementations with
violation tracking and whitelist/blacklist support.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Set, Deque, Any, Dict
from collections import deque
from uuid import uuid4


class ViolationType(str, Enum):
    """Types of rate limit violations."""

    SOFT_LIMIT = "soft_limit"
    HARD_LIMIT = "hard_limit"
    BURST_LIMIT = "burst_limit"
    ABUSE_PATTERN = "abuse_pattern"


@dataclass
class RateLimitViolation:
    """Rate limit violation record."""

    violation_id: str
    user_id: str
    violation_type: ViolationType
    timestamp: datetime
    requests_count: int
    limit_value: int
    metadata: Dict[str, Any] = field(default_factory=dict)


class RateLimiterBase(ABC):
    """
    Abstract base class for rate limiters.

    Rate limiters control the rate of requests/operations to prevent
    abuse and ensure fair resource allocation.

    Features:
    - Token/request acquisition
    - Violation tracking
    - Whitelist/blacklist support
    - Statistics

    Examples:
        >>> class MyRateLimiter(RateLimiterBase):
        ...     async def acquire(self, user_id: str, tokens: int = 1) -> bool:
        ...         # Check whitelist/blacklist
        ...         if self.is_blacklisted(user_id):
        ...             self.record_violation(user_id, ViolationType.ABUSE_PATTERN, 0, 0)
        ...             return False
        ...         if self.is_whitelisted(user_id):
        ...             return True
        ...         # Implementation
        ...         return True
    """

    def __init__(self):
        """Initialize base rate limiter with violation tracking."""
        self._violations: Deque[RateLimitViolation] = deque(maxlen=1000)
        self._whitelist: Set[str] = set()
        self._blacklist: Set[str] = set()

    @abstractmethod
    async def acquire(self, user_id: str, tokens: int = 1) -> bool:
        """
        Attempt to acquire tokens from the rate limiter.

        Args:
            user_id: Identifier for the user/client
            tokens: Number of tokens to acquire (default: 1)

        Returns:
            True if tokens were acquired, False if rate limited

        Examples:
            >>> limiter = MyRateLimiter()
            >>> if await limiter.acquire("user123"):
            ...     # Process request
            ...     pass
            ... else:
            ...     # Rate limited
            ...     pass
        """
        pass

    @abstractmethod
    async def wait_if_needed(
        self,
        user_id: str,
        tokens: int = 1,
        max_wait: float = 30.0
    ) -> None:
        """
        Wait until tokens are available or timeout.

        Args:
            user_id: Identifier for the user/client
            tokens: Number of tokens needed
            max_wait: Maximum seconds to wait

        Raises:
            TimeoutError: If max_wait exceeded without acquiring tokens

        Examples:
            >>> limiter = MyRateLimiter()
            >>> try:
            ...     await limiter.wait_if_needed("user123", max_wait=10.0)
            ...     # Process request
            ... except TimeoutError:
            ...     # Timeout waiting for rate limit
            ...     pass
        """
        pass

    def get_remaining(self, user_id: str) -> Optional[int]:
        """
        Get remaining capacity for a user (if supported).

        Args:
            user_id: Identifier for the user/client

        Returns:
            Number of remaining requests/tokens, or None if not supported

        Examples:
            >>> limiter = MyRateLimiter()
            >>> remaining = limiter.get_remaining("user123")
            >>> if remaining is not None:
            ...     print(f"Remaining: {remaining}")
        """
        return None

    # Whitelist/Blacklist Methods

    def add_to_whitelist(self, user_id: str) -> None:
        """
        Add user to whitelist (unlimited access).

        Args:
            user_id: User identifier to whitelist

        Examples:
            >>> limiter = MyRateLimiter()
            >>> limiter.add_to_whitelist("admin_user")
        """
        self._whitelist.add(user_id)

    def remove_from_whitelist(self, user_id: str) -> None:
        """
        Remove user from whitelist.

        Args:
            user_id: User identifier to remove

        Examples:
            >>> limiter = MyRateLimiter()
            >>> limiter.remove_from_whitelist("admin_user")
        """
        self._whitelist.discard(user_id)

    def add_to_blacklist(self, user_id: str) -> None:
        """
        Add user to blacklist (no access).

        Args:
            user_id: User identifier to blacklist

        Examples:
            >>> limiter = MyRateLimiter()
            >>> limiter.add_to_blacklist("abusive_user")
        """
        self._blacklist.add(user_id)

    def remove_from_blacklist(self, user_id: str) -> None:
        """
        Remove user from blacklist.

        Args:
            user_id: User identifier to remove

        Examples:
            >>> limiter = MyRateLimiter()
            >>> limiter.remove_from_blacklist("abusive_user")
        """
        self._blacklist.discard(user_id)

    def is_whitelisted(self, user_id: str) -> bool:
        """
        Check if user is whitelisted.

        Args:
            user_id: User identifier

        Returns:
            True if user is whitelisted

        Examples:
            >>> limiter = MyRateLimiter()
            >>> if limiter.is_whitelisted("admin_user"):
            ...     print("User has unlimited access")
        """
        return user_id in self._whitelist

    def is_blacklisted(self, user_id: str) -> bool:
        """
        Check if user is blacklisted.

        Args:
            user_id: User identifier

        Returns:
            True if user is blacklisted

        Examples:
            >>> limiter = MyRateLimiter()
            >>> if limiter.is_blacklisted("abusive_user"):
            ...     print("User is blocked")
        """
        return user_id in self._blacklist

    # Violation Tracking Methods

    def record_violation(
        self,
        user_id: str,
        violation_type: ViolationType,
        requests_count: int,
        limit_value: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> RateLimitViolation:
        """
        Record a rate limit violation.

        Args:
            user_id: User identifier
            violation_type: Type of violation
            requests_count: Number of requests made
            limit_value: The limit that was exceeded
            metadata: Additional violation metadata

        Returns:
            The created violation record

        Examples:
            >>> limiter = MyRateLimiter()
            >>> violation = limiter.record_violation(
            ...     "user123",
            ...     ViolationType.HARD_LIMIT,
            ...     150,
            ...     100,
            ...     {"endpoint": "/api/data"}
            ... )
        """
        violation = RateLimitViolation(
            violation_id=str(uuid4()),
            user_id=user_id,
            violation_type=violation_type,
            timestamp=datetime.now(timezone.utc),
            requests_count=requests_count,
            limit_value=limit_value,
            metadata=metadata or {}
        )
        self._violations.append(violation)
        return violation

    def get_violations(
        self,
        user_id: Optional[str] = None,
        violation_type: Optional[ViolationType] = None,
        since: Optional[datetime] = None
    ) -> list[RateLimitViolation]:
        """
        Get recorded violations with optional filtering.

        Args:
            user_id: Filter by user (optional)
            violation_type: Filter by violation type (optional)
            since: Filter by timestamp (optional)

        Returns:
            List of violations matching filters

        Examples:
            >>> limiter = MyRateLimiter()
            >>> # Get all violations
            >>> all_violations = limiter.get_violations()
            >>>
            >>> # Get violations for specific user
            >>> user_violations = limiter.get_violations(user_id="user123")
            >>>
            >>> # Get recent hard limit violations
            >>> from datetime import datetime, timedelta, timezone
            >>> recent = datetime.now(timezone.utc) - timedelta(hours=1)
            >>> hard_violations = limiter.get_violations(
            ...     violation_type=ViolationType.HARD_LIMIT,
            ...     since=recent
            ... )
        """
        violations = list(self._violations)

        if user_id:
            violations = [v for v in violations if v.user_id == user_id]

        if violation_type:
            violations = [v for v in violations if v.violation_type == violation_type]

        if since:
            violations = [v for v in violations if v.timestamp >= since]

        return violations

    def get_violation_count(
        self,
        user_id: Optional[str] = None,
        violation_type: Optional[ViolationType] = None,
        since: Optional[datetime] = None
    ) -> int:
        """
        Get count of violations with optional filtering.

        Args:
            user_id: Filter by user (optional)
            violation_type: Filter by violation type (optional)
            since: Filter by timestamp (optional)

        Returns:
            Number of violations matching filters

        Examples:
            >>> limiter = MyRateLimiter()
            >>> count = limiter.get_violation_count(user_id="user123")
            >>> print(f"User has {count} violations")
        """
        return len(self.get_violations(user_id, violation_type, since))

    def clear_violations(self, user_id: Optional[str] = None) -> None:
        """
        Clear violation records.

        Args:
            user_id: Clear violations for specific user, or all if None

        Examples:
            >>> limiter = MyRateLimiter()
            >>> limiter.clear_violations("user123")  # Clear for user
            >>> limiter.clear_violations()  # Clear all
        """
        if user_id is None:
            self._violations.clear()
        else:
            self._violations = deque(
                (v for v in self._violations if v.user_id != user_id),
                maxlen=self._violations.maxlen
            )

