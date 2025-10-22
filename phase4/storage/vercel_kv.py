"""Vercel KV storage backend implementation."""

from __future__ import annotations

import json
import os
from typing import Any

import httpx

from utils.logging_setup import get_logger

from .base import StorageBackend

logger = get_logger(__name__)


class VercelKVBackend(StorageBackend):
    """Vercel KV storage backend for serverless deployment.

    Uses Vercel's KV storage service for persistent data.
    Ideal for Vercel deployments with global edge caching.
    """

    def __init__(
        self,
        url: str | None = None,
        token: str | None = None,
    ):
        """Initialize Vercel KV backend.

        Args:
            url: Vercel KV URL
            token: Vercel KV token
        """
        self.url = url or os.getenv("VERCEL_KV_URL", "")
        self.token = token or os.getenv("VERCEL_KV_TOKEN", "")

        if not self.url or not self.token:
            raise ValueError("Vercel KV URL and token required")

        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    async def _request(
        self,
        method: str,
        command: list[Any]
    ) -> Any:
        """Execute KV command via REST API.

        Args:
            method: HTTP method
            command: Redis command as list

        Returns:
            Command result
        """
        async with httpx.AsyncClient() as client:
            try:
                # Vercel KV uses Redis protocol over HTTP
                url = f"{self.url}/pipeline"

                response = await client.post(
                    url,
                    headers=self.headers,
                    json=[command],
                    timeout=5.0,
                )

                response.raise_for_status()
                result = response.json()

                # Pipeline returns array of results
                return result[0]["result"] if result else None

            except httpx.HTTPStatusError as e:
                logger.error(f"Vercel KV request failed: {e}")
                raise
            except Exception as e:
                logger.error(f"Vercel KV error: {e}")
                raise

    async def get(self, key: str) -> Any | None:
        """Get value by key."""
        result = await self._request("POST", ["GET", key])

        if result is None:
            return None

        # Try to deserialize JSON
        try:
            return json.loads(result)
        except (json.JSONDecodeError, TypeError):
            return result

    async def set(
        self,
        key: str,
        value: Any,
        expire: int | None = None
    ) -> None:
        """Set value with optional expiration."""
        # Serialize to JSON if not string
        if not isinstance(value, str):
            value = json.dumps(value)

        command = ["SET", key, value]

        if expire:
            command.extend(["EX", expire])

        await self._request("POST", command)

    async def delete(self, key: str) -> bool:
        """Delete key from storage."""
        result = await self._request("POST", ["DEL", key])
        return bool(result)

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        result = await self._request("POST", ["EXISTS", key])
        return bool(result)

    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration on existing key."""
        result = await self._request("POST", ["EXPIRE", key, ttl])
        return bool(result)

    async def ttl(self, key: str) -> int | None:
        """Get remaining TTL for key."""
        result = await self._request("POST", ["TTL", key])

        # Redis returns -2 for non-existent, -1 for no expiry
        if result == -2:
            return None
        if result == -1:
            return None

        return result

    async def scan(
        self,
        pattern: str,
        count: int = 100
    ) -> list[str]:
        """Scan for keys matching pattern."""
        # Vercel KV supports SCAN command
        cursor = 0
        keys: list[str] = []

        while True:
            result = await self._request(
                "POST",
                ["SCAN", cursor, "MATCH", pattern, "COUNT", count]
            )

            if result:
                cursor = result[0]
                batch_keys: Any = result[1] or []
                if isinstance(batch_keys, list):
                    keys.extend(batch_keys)

                if cursor == 0 or len(keys) >= count:
                    break
            else:
                break

        return keys[:count]

    async def mget(self, keys: list[str]) -> dict[str, Any]:
        """Get multiple keys at once."""
        if not keys:
            return {}

        results = await self._request("POST", ["MGET"] + keys)

        # Map results to keys
        key_values = {}
        for i, key in enumerate(keys):
            if i < len(results) and results[i] is not None:
                try:
                    key_values[key] = json.loads(results[i])
                except (json.JSONDecodeError, TypeError):
                    key_values[key] = results[i]

        return key_values

    async def mset(
        self,
        items: dict[str, Any],
        expire: int | None = None
    ) -> None:
        """Set multiple keys at once."""
        if not items:
            return

        # Build MSET command
        mset_args = []
        for key, value in items.items():
            if not isinstance(value, str):
                value = json.dumps(value)
            mset_args.extend([key, value])

        await self._request("POST", ["MSET"] + mset_args)

        # Set expiration if needed
        if expire:
            # Need to set expiry individually
            pipeline = []
            for key in items:
                pipeline.append(["EXPIRE", key, expire])

            # Execute pipeline
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{self.url}/pipeline",
                    headers=self.headers,
                    json=pipeline,
                    timeout=5.0,
                )

    async def incr(
        self,
        key: str,
        amount: int = 1
    ) -> int:
        """Increment numeric value."""
        if amount == 1:
            return await self._request("POST", ["INCR", key])
        else:
            return await self._request("POST", ["INCRBY", key, amount])

    async def decr(
        self,
        key: str,
        amount: int = 1
    ) -> int:
        """Decrement numeric value."""
        if amount == 1:
            return await self._request("POST", ["DECR", key])
        else:
            return await self._request("POST", ["DECRBY", key, amount])

    async def add_to_set(
        self,
        key: str,
        *values: str
    ) -> int:
        """Add values to a set using Redis SADD."""
        if not values:
            return 0

        return await self._request("POST", ["SADD", key] + list(values))

    async def remove_from_set(
        self,
        key: str,
        *values: str
    ) -> int:
        """Remove values from a set using Redis SREM."""
        if not values:
            return 0

        return await self._request("POST", ["SREM", key] + list(values))

    async def get_set_members(self, key: str) -> set[Any]:
        """Get all members of a set using Redis SMEMBERS."""
        result = await self._request("POST", ["SMEMBERS", key])
        return set(result) if result else set()

    async def lock_acquire(
        self,
        lock_name: str,
        timeout: int = 10,
        blocking: bool = True
    ) -> bool:
        """Acquire a distributed lock using Redis SET NX."""
        lock_key = f"lock:{lock_name}"

        # Try to acquire lock with SET NX EX
        result = await self._request(
            "POST",
            ["SET", lock_key, "1", "NX", "EX", timeout]
        )

        if result == "OK":
            return True

        if not blocking:
            return False

        # Simple blocking implementation - in production use Redlock
        import asyncio
        for _ in range(timeout * 10):  # Try for timeout seconds
            await asyncio.sleep(0.1)

            result = await self._request(
                "POST",
                ["SET", lock_key, "1", "NX", "EX", timeout]
            )

            if result == "OK":
                return True

        return False

    async def lock_release(self, lock_name: str) -> bool:
        """Release a distributed lock."""
        lock_key = f"lock:{lock_name}"
        return await self.delete(lock_key)
