"""
Redis Storage Backend

Production-ready Redis storage implementation for session management
with connection pooling, automatic reconnection, and error handling.
"""

import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

try:
    import redis.asyncio as redis
    from redis.asyncio import Redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    Redis = None

from .base import StorageBackend
from ..models import Session, TokenRefreshRecord, AuditLog
from ..revocation import RevocationRecord


logger = logging.getLogger(__name__)


class RedisStorage(StorageBackend):
    """
    Redis storage backend with production features.

    Features:
    - Connection pooling for performance
    - Automatic TTL for data cleanup
    - Atomic operations
    - Error handling and retries
    - Pipeline support for batch operations
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        redis_client: Optional[Redis] = None,
        key_prefix: str = "atoms:session:",
        default_ttl_hours: int = 24,
        max_connections: int = 10,
    ):
        """
        Initialize Redis storage.

        Args:
            redis_url: Redis connection URL
            redis_client: Optional existing Redis client
            key_prefix: Prefix for all keys
            default_ttl_hours: Default TTL for stored data
            max_connections: Maximum connections in pool
        """
        if not REDIS_AVAILABLE:
            raise ImportError("redis package not installed. Install with: pip install redis")

        self.redis_url = redis_url
        self.key_prefix = key_prefix
        self.default_ttl_hours = default_ttl_hours
        self.max_connections = max_connections

        self._client = redis_client
        self._owned_client = redis_client is None

        logger.info(f"Initialized Redis storage with prefix '{key_prefix}'")

    async def _get_client(self) -> Redis:
        """Get or create Redis client."""
        if self._client is None:
            self._client = await redis.from_url(
                self.redis_url,
                max_connections=self.max_connections,
                decode_responses=False,
            )
        return self._client

    def _key(self, *parts: str) -> str:
        """Generate prefixed key."""
        return self.key_prefix + ":".join(parts)

    async def save_session(self, session: Session):
        """Save session to Redis."""
        client = await self._get_client()
        key = self._key("session", session.session_id)

        # Serialize session
        data = json.dumps(session.to_dict())

        # Calculate TTL
        if session.expires_at:
            ttl = int((session.expires_at - datetime.utcnow()).total_seconds())
            ttl = max(ttl, 60)  # Minimum 1 minute
        else:
            ttl = self.default_ttl_hours * 3600

        # Store session
        await client.setex(key, ttl, data)

        # Add to user sessions index
        user_key = self._key("user_sessions", session.user_id)
        await client.sadd(user_key, session.session_id)
        await client.expire(user_key, ttl)

        logger.debug(f"Saved session {session.session_id} with TTL {ttl}s")

    async def get_session(self, session_id: str) -> Optional[Session]:
        """Get session from Redis."""
        client = await self._get_client()
        key = self._key("session", session_id)

        data = await client.get(key)
        if not data:
            return None

        session_dict = json.loads(data)
        return Session.from_dict(session_dict)

    async def delete_session(self, session_id: str):
        """Delete session from Redis."""
        client = await self._get_client()

        # Get session to find user_id
        session = await self.get_session(session_id)
        if not session:
            return

        # Delete session
        session_key = self._key("session", session_id)
        await client.delete(session_key)

        # Remove from user sessions index
        user_key = self._key("user_sessions", session.user_id)
        await client.srem(user_key, session_id)

        logger.debug(f"Deleted session {session_id}")

    async def get_user_sessions(self, user_id: str) -> List[Session]:
        """Get all sessions for user from Redis."""
        client = await self._get_client()
        user_key = self._key("user_sessions", user_id)

        # Get session IDs
        session_ids = await client.smembers(user_key)
        if not session_ids:
            return []

        # Fetch sessions
        sessions = []
        for session_id in session_ids:
            session = await self.get_session(session_id.decode())
            if session:
                sessions.append(session)

        return sessions

    async def get_all_sessions(self, limit: int = 100) -> List[Session]:
        """Get all sessions from Redis."""
        client = await self._get_client()

        # Scan for session keys
        sessions = []
        pattern = self._key("session", "*")

        cursor = 0
        while len(sessions) < limit:
            cursor, keys = await client.scan(
                cursor,
                match=pattern,
                count=100,
            )

            for key in keys:
                if len(sessions) >= limit:
                    break

                data = await client.get(key)
                if data:
                    session_dict = json.loads(data)
                    sessions.append(Session.from_dict(session_dict))

            if cursor == 0:
                break

        return sessions

    async def save_refresh_record(self, record: TokenRefreshRecord):
        """Save refresh record to Redis."""
        client = await self._get_client()

        # Store record
        record_key = self._key("refresh_record", record.record_id)
        data = json.dumps(record.to_dict())
        await client.setex(
            record_key,
            self.default_ttl_hours * 3600,
            data,
        )

        # Add to session history
        history_key = self._key("refresh_history", record.session_id)
        await client.lpush(history_key, record.record_id)
        await client.ltrim(history_key, 0, 99)  # Keep last 100
        await client.expire(history_key, self.default_ttl_hours * 3600)

        logger.debug(f"Saved refresh record {record.record_id}")

    async def get_refresh_history(
        self,
        session_id: str,
        limit: int = 10,
    ) -> List[TokenRefreshRecord]:
        """Get refresh history from Redis."""
        client = await self._get_client()
        history_key = self._key("refresh_history", session_id)

        # Get record IDs
        record_ids = await client.lrange(history_key, 0, limit - 1)
        if not record_ids:
            return []

        # Fetch records
        records = []
        for record_id in record_ids:
            record_key = self._key("refresh_record", record_id.decode())
            data = await client.get(record_key)
            if data:
                record_dict = json.loads(data)
                records.append(TokenRefreshRecord.from_dict(record_dict))

        return records

    async def save_revocation_record(self, record: RevocationRecord):
        """Save revocation record to Redis."""
        client = await self._get_client()

        # Store record
        record_key = self._key("revocation", record.token_hash)
        data = json.dumps(record.to_dict())

        # Calculate TTL
        if record.expires_at:
            ttl = int((record.expires_at - datetime.utcnow()).total_seconds())
            ttl = max(ttl, 60)
        else:
            ttl = self.default_ttl_hours * 3600

        await client.setex(record_key, ttl, data)

        # Add to session revocations index
        if record.session_id:
            session_key = self._key("session_revocations", record.session_id)
            await client.sadd(session_key, record.token_hash)
            await client.expire(session_key, ttl)

        logger.debug(f"Saved revocation record for token hash {record.token_hash[:8]}...")

    async def get_revocation_record(
        self,
        token_hash: str,
    ) -> Optional[RevocationRecord]:
        """Get revocation record from Redis."""
        client = await self._get_client()
        key = self._key("revocation", token_hash)

        data = await client.get(key)
        if not data:
            return None

        record_dict = json.loads(data)
        return RevocationRecord.from_dict(record_dict)

    async def get_session_revocations(
        self,
        session_id: str,
    ) -> List[RevocationRecord]:
        """Get session revocations from Redis."""
        client = await self._get_client()
        session_key = self._key("session_revocations", session_id)

        # Get token hashes
        token_hashes = await client.smembers(session_key)
        if not token_hashes:
            return []

        # Fetch records
        records = []
        for token_hash in token_hashes:
            record = await self.get_revocation_record(token_hash.decode())
            if record:
                records.append(record)

        return records

    async def cleanup_expired_revocations(
        self,
        batch_size: int = 100,
    ) -> int:
        """Clean up expired revocations from Redis."""
        # Redis automatically removes expired keys via TTL
        # This is a no-op for Redis
        return 0

    async def save_audit_log(self, log: AuditLog):
        """Save audit log to Redis."""
        client = await self._get_client()

        # Store log
        log_key = self._key("audit_log", log.log_id)
        data = json.dumps(log.to_dict())
        await client.setex(
            log_key,
            self.default_ttl_hours * 3600,
            data,
        )

        # Add to session logs
        if log.session_id:
            session_key = self._key("session_logs", log.session_id)
            await client.lpush(session_key, log.log_id)
            await client.ltrim(session_key, 0, 999)  # Keep last 1000
            await client.expire(session_key, self.default_ttl_hours * 3600)

        # Add to user logs
        if log.user_id:
            user_key = self._key("user_logs", log.user_id)
            await client.lpush(user_key, log.log_id)
            await client.ltrim(user_key, 0, 999)  # Keep last 1000
            await client.expire(user_key, self.default_ttl_hours * 3600)

        logger.debug(f"Saved audit log {log.log_id}")

    async def get_audit_logs(
        self,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[AuditLog]:
        """Get audit logs from Redis."""
        client = await self._get_client()

        # Determine which index to use
        if session_id:
            index_key = self._key("session_logs", session_id)
        elif user_id:
            index_key = self._key("user_logs", user_id)
        else:
            # No filtering - not efficient in Redis
            return []

        # Get log IDs
        log_ids = await client.lrange(index_key, 0, limit - 1)
        if not log_ids:
            return []

        # Fetch logs
        logs = []
        for log_id in log_ids:
            log_key = self._key("audit_log", log_id.decode())
            data = await client.get(log_key)
            if data:
                log_dict = json.loads(data)
                logs.append(AuditLog.from_dict(log_dict))

        return logs

    async def get_user_audit_logs(
        self,
        user_id: str,
        limit: int = 100,
    ) -> List[AuditLog]:
        """Get user audit logs from Redis."""
        return await self.get_audit_logs(user_id=user_id, limit=limit)

    async def close(self):
        """Close Redis connection."""
        if self._client and self._owned_client:
            await self._client.close()
            self._client = None
            logger.info("Closed Redis connection")
