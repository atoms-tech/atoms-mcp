"""Base storage backend interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class StorageBackend(ABC):
    """Abstract base class for storage backends.

    All storage implementations must implement this interface
    to ensure compatibility with the Phase 4 system.
    """

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        """Get value by key.

        Args:
            key: Storage key

        Returns:
            Value if exists, None otherwise
        """
        pass

    @abstractmethod
    async def set(
        self,
        key: str,
        value: Any,
        expire: int | None = None
    ) -> None:
        """Set value with optional expiration.

        Args:
            key: Storage key
            value: Value to store
            expire: TTL in seconds
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete key from storage.

        Args:
            key: Storage key

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists.

        Args:
            key: Storage key

        Returns:
            True if exists
        """
        pass

    @abstractmethod
    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration on existing key.

        Args:
            key: Storage key
            ttl: TTL in seconds

        Returns:
            True if expiration set
        """
        pass

    @abstractmethod
    async def ttl(self, key: str) -> int | None:
        """Get remaining TTL for key.

        Args:
            key: Storage key

        Returns:
            TTL in seconds, None if no expiry
        """
        pass

    @abstractmethod
    async def scan(
        self,
        pattern: str,
        count: int = 100
    ) -> list[str]:
        """Scan for keys matching pattern.

        Args:
            pattern: Key pattern (e.g., "session:*")
            count: Maximum keys to return

        Returns:
            List of matching keys
        """
        pass

    @abstractmethod
    async def mget(self, keys: list[str]) -> dict[str, Any]:
        """Get multiple keys at once.

        Args:
            keys: List of keys

        Returns:
            Dict of key-value pairs
        """
        pass

    @abstractmethod
    async def mset(
        self,
        items: dict[str, Any],
        expire: int | None = None
    ) -> None:
        """Set multiple keys at once.

        Args:
            items: Dict of key-value pairs
            expire: TTL in seconds for all keys
        """
        pass

    @abstractmethod
    async def incr(
        self,
        key: str,
        amount: int = 1
    ) -> int:
        """Increment numeric value.

        Args:
            key: Storage key
            amount: Increment amount

        Returns:
            New value after increment
        """
        pass

    @abstractmethod
    async def decr(
        self,
        key: str,
        amount: int = 1
    ) -> int:
        """Decrement numeric value.

        Args:
            key: Storage key
            amount: Decrement amount

        Returns:
            New value after decrement
        """
        pass

    async def is_token_revoked(self, token_hash: str) -> bool:
        """Check if token is revoked.

        Args:
            token_hash: SHA256 hash of token

        Returns:
            True if revoked
        """
        return await self.exists(f"revoked:{token_hash}")

    async def add_to_set(
        self,
        key: str,
        *values: str
    ) -> int:
        """Add values to a set.

        Args:
            key: Set key
            values: Values to add

        Returns:
            Number of values added
        """
        current = await self.get(key) or set()
        if not isinstance(current, set):
            current = set(current) if isinstance(current, list) else {current}

        original_size = len(current)
        current.update(values)
        await self.set(key, list(current))

        return len(current) - original_size

    async def remove_from_set(
        self,
        key: str,
        *values: str
    ) -> int:
        """Remove values from a set.

        Args:
            key: Set key
            values: Values to remove

        Returns:
            Number of values removed
        """
        current = await self.get(key) or set()
        if not isinstance(current, set):
            current = set(current) if isinstance(current, list) else {current}

        original_size = len(current)
        current.difference_update(values)
        await self.set(key, list(current))

        return original_size - len(current)

    async def get_set_members(self, key: str) -> set[Any]:
        """Get all members of a set.

        Args:
            key: Set key

        Returns:
            Set of values
        """
        current = await self.get(key) or []
        if isinstance(current, set):
            return current
        return set(current) if isinstance(current, list) else {current}

    async def lock_acquire(
        self,
        lock_name: str,
        timeout: int = 10,
        blocking: bool = True
    ) -> bool:
        """Acquire a distributed lock.

        Args:
            lock_name: Lock identifier
            timeout: Lock timeout in seconds
            blocking: Whether to wait for lock

        Returns:
            True if lock acquired
        """
        # Simple implementation, override for better distributed locking
        lock_key = f"lock:{lock_name}"

        if not blocking:
            if await self.exists(lock_key):
                return False

        # Set lock with timeout
        existing = await self.get(lock_key)
        if existing is None:
            await self.set(lock_key, "locked", expire=timeout)
            return True

        return False

    async def lock_release(self, lock_name: str) -> bool:
        """Release a distributed lock.

        Args:
            lock_name: Lock identifier

        Returns:
            True if lock released
        """
        lock_key = f"lock:{lock_name}"
        return await self.delete(lock_key)
