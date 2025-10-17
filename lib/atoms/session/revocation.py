"""
Token Revocation Service

Comprehensive token revocation with immediate invalidation, cascading revocation,
revocation lists with TTL, and complete audit trails.
"""

import asyncio
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Set
from dataclasses import dataclass
from uuid import uuid4

from .models import Session, SessionState, AuditLog, AuditAction
from .storage.base import StorageBackend


logger = logging.getLogger(__name__)


class RevocationError(Exception):
    """Raised when token revocation fails."""
    pass


@dataclass
class RevocationRecord:
    """Record of a token revocation event."""

    revocation_id: str
    token_hash: str
    token_type: str  # access_token, refresh_token, id_token
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    revoked_at: datetime = None
    expires_at: Optional[datetime] = None  # When to remove from revocation list
    reason: str = "user_logout"
    revoked_by: Optional[str] = None  # User or system that triggered revocation
    cascaded_from: Optional[str] = None  # Parent revocation ID if cascaded
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.revoked_at is None:
            self.revoked_at = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "revocation_id": self.revocation_id,
            "token_hash": self.token_hash,
            "token_type": self.token_type,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "revoked_at": self.revoked_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "reason": self.reason,
            "revoked_by": self.revoked_by,
            "cascaded_from": self.cascaded_from,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RevocationRecord":
        """Create from dictionary."""
        if "revoked_at" in data and isinstance(data["revoked_at"], str):
            data["revoked_at"] = datetime.fromisoformat(data["revoked_at"])
        if "expires_at" in data and data["expires_at"] and isinstance(data["expires_at"], str):
            data["expires_at"] = datetime.fromisoformat(data["expires_at"])
        return cls(**data)


class RevocationService:
    """
    Manages token revocation with comprehensive tracking.

    Features:
    - Immediate token invalidation
    - Cascading revocation (revoking refresh token revokes all access tokens)
    - Revocation list with TTL for cleanup
    - Complete audit trail
    - Batch revocation support
    - Revocation verification
    """

    def __init__(
        self,
        storage: StorageBackend,
        revocation_list_ttl_hours: int = 24,
        enable_cascading: bool = True,
        audit_enabled: bool = True,
    ):
        """
        Initialize revocation service.

        Args:
            storage: Storage backend for revocation records
            revocation_list_ttl_hours: TTL for revocation list entries
            enable_cascading: Enable cascading revocation
            audit_enabled: Enable audit logging
        """
        self.storage = storage
        self.revocation_list_ttl_hours = revocation_list_ttl_hours
        self.enable_cascading = enable_cascading
        self.audit_enabled = audit_enabled

        # In-memory cache for fast lookups
        self._revocation_cache: Set[str] = set()
        self._cache_lock = asyncio.Lock()

        # Background cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None

    def _hash_token(self, token: str) -> str:
        """Create secure hash of token."""
        return hashlib.sha256(token.encode()).hexdigest()

    async def revoke_token(
        self,
        token: str,
        token_type: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        reason: str = "user_logout",
        revoked_by: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> RevocationRecord:
        """
        Revoke a single token.

        Args:
            token: Token to revoke
            token_type: Type of token (access_token, refresh_token, id_token)
            session_id: Associated session ID
            user_id: Associated user ID
            reason: Reason for revocation
            revoked_by: Who triggered revocation
            metadata: Additional metadata

        Returns:
            Revocation record

        Raises:
            RevocationError: If revocation fails
        """
        token_hash = self._hash_token(token)

        logger.info(
            f"Revoking {token_type} for session {session_id} "
            f"(reason: {reason})"
        )

        # Create revocation record
        record = RevocationRecord(
            revocation_id=str(uuid4()),
            token_hash=token_hash,
            token_type=token_type,
            session_id=session_id,
            user_id=user_id,
            reason=reason,
            revoked_by=revoked_by,
            metadata=metadata or {},
        )

        # Set TTL for revocation list
        record.expires_at = datetime.utcnow() + timedelta(
            hours=self.revocation_list_ttl_hours
        )

        # Store revocation record
        await self.storage.save_revocation_record(record)

        # Add to cache
        async with self._cache_lock:
            self._revocation_cache.add(token_hash)

        # Audit log
        if self.audit_enabled:
            await self._create_audit_log(
                action=AuditAction.TOKEN_REVOKED,
                session_id=session_id,
                user_id=user_id,
                details=f"Token revoked: {token_type} (reason: {reason})",
                metadata={
                    "revocation_id": record.revocation_id,
                    "token_type": token_type,
                    "reason": reason,
                }
            )

        logger.info(
            f"Revoked {token_type} (revocation_id: {record.revocation_id})"
        )

        return record

    async def revoke_session(
        self,
        session: Session,
        reason: str = "user_logout",
        revoked_by: Optional[str] = None,
    ) -> List[RevocationRecord]:
        """
        Revoke all tokens for a session.

        Args:
            session: Session to revoke
            reason: Reason for revocation
            revoked_by: Who triggered revocation

        Returns:
            List of revocation records
        """
        logger.info(f"Revoking session {session.session_id} (reason: {reason})")

        records = []

        # Revoke access token
        if session.access_token:
            record = await self.revoke_token(
                session.access_token,
                "access_token",
                session_id=session.session_id,
                user_id=session.user_id,
                reason=reason,
                revoked_by=revoked_by,
            )
            records.append(record)

        # Revoke refresh token
        if session.refresh_token:
            record = await self.revoke_token(
                session.refresh_token,
                "refresh_token",
                session_id=session.session_id,
                user_id=session.user_id,
                reason=reason,
                revoked_by=revoked_by,
            )
            records.append(record)

        # Revoke ID token
        if session.id_token:
            record = await self.revoke_token(
                session.id_token,
                "id_token",
                session_id=session.session_id,
                user_id=session.user_id,
                reason=reason,
                revoked_by=revoked_by,
            )
            records.append(record)

        # Update session state
        session.state = SessionState.REVOKED
        await self.storage.save_session(session)

        logger.info(
            f"Revoked session {session.session_id} ({len(records)} tokens)"
        )

        return records

    async def revoke_user_sessions(
        self,
        user_id: str,
        except_session_id: Optional[str] = None,
        reason: str = "user_logout_all",
        revoked_by: Optional[str] = None,
    ) -> List[RevocationRecord]:
        """
        Revoke all sessions for a user.

        Args:
            user_id: User identifier
            except_session_id: Optional session ID to keep active
            reason: Reason for revocation
            revoked_by: Who triggered revocation

        Returns:
            List of all revocation records
        """
        logger.info(
            f"Revoking all sessions for user {user_id} "
            f"(except {except_session_id})"
        )

        all_records = []
        sessions = await self.storage.get_user_sessions(user_id)

        for session in sessions:
            if session.session_id != except_session_id:
                records = await self.revoke_session(
                    session,
                    reason=reason,
                    revoked_by=revoked_by,
                )
                all_records.extend(records)

        logger.info(
            f"Revoked {len(sessions)} sessions for user {user_id} "
            f"({len(all_records)} tokens)"
        )

        return all_records

    async def revoke_with_cascade(
        self,
        refresh_token: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        reason: str = "refresh_token_revoked",
        revoked_by: Optional[str] = None,
    ) -> List[RevocationRecord]:
        """
        Revoke refresh token and cascade to related access tokens.

        Args:
            refresh_token: Refresh token to revoke
            session_id: Associated session ID
            user_id: Associated user ID
            reason: Reason for revocation
            revoked_by: Who triggered revocation

        Returns:
            List of all revocation records
        """
        if not self.enable_cascading:
            record = await self.revoke_token(
                refresh_token,
                "refresh_token",
                session_id=session_id,
                user_id=user_id,
                reason=reason,
                revoked_by=revoked_by,
            )
            return [record]

        logger.info(
            f"Revoking refresh token with cascade for session {session_id}"
        )

        # Revoke refresh token first
        parent_record = await self.revoke_token(
            refresh_token,
            "refresh_token",
            session_id=session_id,
            user_id=user_id,
            reason=reason,
            revoked_by=revoked_by,
        )

        records = [parent_record]

        # Get session to revoke associated tokens
        if session_id:
            session = await self.storage.get_session(session_id)
            if session:
                # Revoke access token
                if session.access_token:
                    access_record = await self.revoke_token(
                        session.access_token,
                        "access_token",
                        session_id=session_id,
                        user_id=user_id,
                        reason=f"cascaded_from_refresh_token",
                        revoked_by=revoked_by,
                        metadata={"cascaded_from": parent_record.revocation_id}
                    )
                    access_record.cascaded_from = parent_record.revocation_id
                    records.append(access_record)

                # Revoke ID token
                if session.id_token:
                    id_record = await self.revoke_token(
                        session.id_token,
                        "id_token",
                        session_id=session_id,
                        user_id=user_id,
                        reason=f"cascaded_from_refresh_token",
                        revoked_by=revoked_by,
                        metadata={"cascaded_from": parent_record.revocation_id}
                    )
                    id_record.cascaded_from = parent_record.revocation_id
                    records.append(id_record)

                # Update session state
                session.state = SessionState.REVOKED
                await self.storage.save_session(session)

        logger.info(
            f"Cascading revocation complete: {len(records)} tokens revoked"
        )

        return records

    async def is_revoked(
        self,
        token: str,
        check_storage: bool = True,
    ) -> bool:
        """
        Check if token is revoked.

        Args:
            token: Token to check
            check_storage: Whether to check storage (slower but more reliable)

        Returns:
            True if token is revoked
        """
        token_hash = self._hash_token(token)

        # Check cache first
        async with self._cache_lock:
            if token_hash in self._revocation_cache:
                return True

        # Check storage if requested
        if check_storage:
            record = await self.storage.get_revocation_record(token_hash)
            if record:
                # Add to cache
                async with self._cache_lock:
                    self._revocation_cache.add(token_hash)
                return True

        return False

    async def get_revocation_record(
        self,
        token: str,
    ) -> Optional[RevocationRecord]:
        """
        Get revocation record for token.

        Args:
            token: Token to lookup

        Returns:
            Revocation record if found
        """
        token_hash = self._hash_token(token)
        return await self.storage.get_revocation_record(token_hash)

    async def get_session_revocations(
        self,
        session_id: str,
    ) -> List[RevocationRecord]:
        """
        Get all revocations for a session.

        Args:
            session_id: Session identifier

        Returns:
            List of revocation records
        """
        return await self.storage.get_session_revocations(session_id)

    async def cleanup_expired_revocations(
        self,
        batch_size: int = 100,
    ) -> int:
        """
        Clean up expired revocation records.

        Args:
            batch_size: Number of records to process per batch

        Returns:
            Number of records cleaned up
        """
        logger.info("Starting revocation list cleanup")

        cleaned = await self.storage.cleanup_expired_revocations(batch_size)

        # Clear cache
        async with self._cache_lock:
            self._revocation_cache.clear()

        logger.info(f"Cleaned up {cleaned} expired revocation records")
        return cleaned

    async def start_cleanup_task(
        self,
        interval_hours: int = 1,
    ):
        """
        Start background cleanup task.

        Args:
            interval_hours: Cleanup interval in hours
        """
        if self._cleanup_task:
            logger.warning("Cleanup task already running")
            return

        async def cleanup_loop():
            while True:
                try:
                    await asyncio.sleep(interval_hours * 3600)
                    await self.cleanup_expired_revocations()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in cleanup task: {e}")

        self._cleanup_task = asyncio.create_task(cleanup_loop())
        logger.info(f"Started cleanup task (interval: {interval_hours} hours)")

    async def stop_cleanup_task(self):
        """Stop background cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            logger.info("Stopped cleanup task")

    async def _create_audit_log(
        self,
        action: AuditAction,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        details: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Create and store audit log entry."""
        log = AuditLog(
            action=action,
            action_details=details,
            session_id=session_id,
            user_id=user_id,
            metadata=metadata or {},
        )

        await self.storage.save_audit_log(log)

    async def __aenter__(self):
        """Context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.stop_cleanup_task()
