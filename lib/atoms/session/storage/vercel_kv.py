"""
Vercel KV Storage Backend

Production-ready Vercel KV (Upstash Redis) storage implementation
optimized for serverless environments with edge network support.
"""

import json
import logging
import os
from typing import Optional, List, Dict, Any
from datetime import datetime

try:
    from upstash_redis import Redis
    UPSTASH_AVAILABLE = True
except ImportError:
    UPSTASH_AVAILABLE = False
    Redis = None

from .base import StorageBackend
from ..models import Session, TokenRefreshRecord, AuditLog
from ..revocation import RevocationRecord


logger = logging.getLogger(__name__)


class VercelKVStorage(StorageBackend):
    """
    Vercel KV storage backend using Upstash Redis.

    Features:
    - Serverless-optimized HTTP-based Redis client
    - Global edge network for low latency
    - Automatic connection management
    - Built-in retry logic
    - TTL-based automatic cleanup

    Environment Variables:
    - KV_REST_API_URL: Upstash REST API URL
    - KV_REST_API_TOKEN: Upstash REST API token
    """

    def __init__(
        self,
        rest_api_url: Optional[str] = None,
        rest_api_token: Optional[str] = None,
        redis_client: Optional[Redis] = None,
        key_prefix: str = "atoms:session:",
        default_ttl_hours: int = 24,
    ):
        """
        Initialize Vercel KV storage.

        Args:
            rest_api_url: Upstash REST API URL (or from env)
            rest_api_token: Upstash REST API token (or from env)
            redis_client: Optional existing Redis client
            key_prefix: Prefix for all keys
            default_ttl_hours: Default TTL for stored data
        """
        if not UPSTASH_AVAILABLE:
            raise ImportError(
                "upstash-redis package not installed. "
                "Install with: pip install upstash-redis"
            )

        self.rest_api_url = rest_api_url or os.getenv("KV_REST_API_URL")
        self.rest_api_token = rest_api_token or os.getenv("KV_REST_API_TOKEN")
        self.key_prefix = key_prefix
        self.default_ttl_hours = default_ttl_hours

        if redis_client:
            self._client = redis_client
        elif self.rest_api_url and self.rest_api_token:
            self._client = Redis(
                url=self.rest_api_url,
                token=self.rest_api_token,
            )
        else:
            raise ValueError(
                "Must provide either redis_client or both rest_api_url and rest_api_token"
            )

        logger.info(f"Initialized Vercel KV storage with prefix '{key_prefix}'")

    def _key(self, *parts: str) -> str:
        """Generate prefixed key."""
        return self.key_prefix + ":".join(parts)

    async def save_session(self, session: Session):
        """Save session to Vercel KV."""
        key = self._key("session", session.session_id)

        # Serialize session
        data = json.dumps(session.to_dict())

        # Calculate TTL
        if session.expires_at:
            ttl = int((session.expires_at - datetime.utcnow()).total_seconds())
            ttl = max(ttl, 60)  # Minimum 1 minute
        else:
            ttl = self.default_ttl_hours * 3600

        # Store session with TTL
        self._client.setex(key, ttl, data)

        # Add to user sessions index
        user_key = self._key("user_sessions", session.user_id)
        self._client.sadd(user_key, session.session_id)
        self._client.expire(user_key, ttl)

        logger.debug(f"Saved session {session.session_id} with TTL {ttl}s")

    async def get_session(self, session_id: str) -> Optional[Session]:
        """Get session from Vercel KV."""
        key = self._key("session", session_id)

        data = self._client.get(key)
        if not data:
            return None

        session_dict = json.loads(data)
        return Session.from_dict(session_dict)

    async def delete_session(self, session_id: str):
        """Delete session from Vercel KV."""
        # Get session to find user_id
        session = await self.get_session(session_id)
        if not session:
            return

        # Delete session
        session_key = self._key("session", session_id)
        self._client.delete(session_key)

        # Remove from user sessions index
        user_key = self._key("user_sessions", session.user_id)
        self._client.srem(user_key, session_id)

        logger.debug(f"Deleted session {session_id}")

    async def get_user_sessions(self, user_id: str) -> List[Session]:
        """Get all sessions for user from Vercel KV."""
        user_key = self._key("user_sessions", user_id)

        # Get session IDs
        session_ids = self._client.smembers(user_key)
        if not session_ids:
            return []

        # Fetch sessions
        sessions = []
        for session_id in session_ids:
            # Handle both string and bytes
            sid = session_id if isinstance(session_id, str) else session_id.decode()
            session = await self.get_session(sid)
            if session:
                sessions.append(session)

        return sessions

    async def get_all_sessions(self, limit: int = 100) -> List[Session]:
        """Get all sessions from Vercel KV."""
        # Scan for session keys
        sessions = []
        pattern = self._key("session", "*")

        cursor = 0
        while len(sessions) < limit:
            result = self._client.scan(cursor, match=pattern, count=100)

            # Handle different return formats
            if isinstance(result, tuple):
                cursor, keys = result
            else:
                cursor = result.get("cursor", 0)
                keys = result.get("keys", [])

            for key in keys:
                if len(sessions) >= limit:
                    break

                # Extract session ID from key
                key_str = key if isinstance(key, str) else key.decode()
                data = self._client.get(key_str)
                if data:
                    session_dict = json.loads(data)
                    sessions.append(Session.from_dict(session_dict))

            if cursor == 0:
                break

        return sessions

    async def save_refresh_record(self, record: TokenRefreshRecord):
        """Save refresh record to Vercel KV."""
        # Store record
        record_key = self._key("refresh_record", record.record_id)
        data = json.dumps(record.to_dict())
        ttl = self.default_ttl_hours * 3600

        self._client.setex(record_key, ttl, data)

        # Add to session history
        history_key = self._key("refresh_history", record.session_id)
        self._client.lpush(history_key, record.record_id)
        self._client.ltrim(history_key, 0, 99)  # Keep last 100
        self._client.expire(history_key, ttl)

        logger.debug(f"Saved refresh record {record.record_id}")

    async def get_refresh_history(
        self,
        session_id: str,
        limit: int = 10,
    ) -> List[TokenRefreshRecord]:
        """Get refresh history from Vercel KV."""
        history_key = self._key("refresh_history", session_id)

        # Get record IDs
        record_ids = self._client.lrange(history_key, 0, limit - 1)
        if not record_ids:
            return []

        # Fetch records
        records = []
        for record_id in record_ids:
            rid = record_id if isinstance(record_id, str) else record_id.decode()
            record_key = self._key("refresh_record", rid)
            data = self._client.get(record_key)
            if data:
                record_dict = json.loads(data)
                records.append(TokenRefreshRecord.from_dict(record_dict))

        return records

    async def save_revocation_record(self, record: RevocationRecord):
        """Save revocation record to Vercel KV."""
        # Store record
        record_key = self._key("revocation", record.token_hash)
        data = json.dumps(record.to_dict())

        # Calculate TTL
        if record.expires_at:
            ttl = int((record.expires_at - datetime.utcnow()).total_seconds())
            ttl = max(ttl, 60)
        else:
            ttl = self.default_ttl_hours * 3600

        self._client.setex(record_key, ttl, data)

        # Add to session revocations index
        if record.session_id:
            session_key = self._key("session_revocations", record.session_id)
            self._client.sadd(session_key, record.token_hash)
            self._client.expire(session_key, ttl)

        logger.debug(f"Saved revocation record for token hash {record.token_hash[:8]}...")

    async def get_revocation_record(
        self,
        token_hash: str,
    ) -> Optional[RevocationRecord]:
        """Get revocation record from Vercel KV."""
        key = self._key("revocation", token_hash)

        data = self._client.get(key)
        if not data:
            return None

        record_dict = json.loads(data)
        return RevocationRecord.from_dict(record_dict)

    async def get_session_revocations(
        self,
        session_id: str,
    ) -> List[RevocationRecord]:
        """Get session revocations from Vercel KV."""
        session_key = self._key("session_revocations", session_id)

        # Get token hashes
        token_hashes = self._client.smembers(session_key)
        if not token_hashes:
            return []

        # Fetch records
        records = []
        for token_hash in token_hashes:
            th = token_hash if isinstance(token_hash, str) else token_hash.decode()
            record = await self.get_revocation_record(th)
            if record:
                records.append(record)

        return records

    async def cleanup_expired_revocations(
        self,
        batch_size: int = 100,
    ) -> int:
        """Clean up expired revocations from Vercel KV."""
        # Vercel KV/Upstash automatically removes expired keys via TTL
        # This is a no-op for Vercel KV
        return 0

    async def save_audit_log(self, log: AuditLog):
        """Save audit log to Vercel KV."""
        # Store log
        log_key = self._key("audit_log", log.log_id)
        data = json.dumps(log.to_dict())
        ttl = self.default_ttl_hours * 3600

        self._client.setex(log_key, ttl, data)

        # Add to session logs
        if log.session_id:
            session_key = self._key("session_logs", log.session_id)
            self._client.lpush(session_key, log.log_id)
            self._client.ltrim(session_key, 0, 999)  # Keep last 1000
            self._client.expire(session_key, ttl)

        # Add to user logs
        if log.user_id:
            user_key = self._key("user_logs", log.user_id)
            self._client.lpush(user_key, log.log_id)
            self._client.ltrim(user_key, 0, 999)  # Keep last 1000
            self._client.expire(user_key, ttl)

        logger.debug(f"Saved audit log {log.log_id}")

    async def get_audit_logs(
        self,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[AuditLog]:
        """Get audit logs from Vercel KV."""
        # Determine which index to use
        if session_id:
            index_key = self._key("session_logs", session_id)
        elif user_id:
            index_key = self._key("user_logs", user_id)
        else:
            # No filtering - not efficient in KV
            return []

        # Get log IDs
        log_ids = self._client.lrange(index_key, 0, limit - 1)
        if not log_ids:
            return []

        # Fetch logs
        logs = []
        for log_id in log_ids:
            lid = log_id if isinstance(log_id, str) else log_id.decode()
            log_key = self._key("audit_log", lid)
            data = self._client.get(log_key)
            if data:
                log_dict = json.loads(data)
                logs.append(AuditLog.from_dict(log_dict))

        return logs

    async def get_user_audit_logs(
        self,
        user_id: str,
        limit: int = 100,
    ) -> List[AuditLog]:
        """Get user audit logs from Vercel KV."""
        return await self.get_audit_logs(user_id=user_id, limit=limit)

    async def close(self):
        """Close Vercel KV connection."""
        # Upstash Redis client doesn't require explicit cleanup
        logger.debug("Vercel KV storage closed (no cleanup needed)")
