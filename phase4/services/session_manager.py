"""Session management service for multi-session handling."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any

from utils.logging_setup import get_logger

from ..models import DeviceInfo, Session, SessionStatus, TokenPair
from ..storage import StorageBackend, get_storage_backend
from .audit import AuditService
from .token_refresh import TokenRefreshService

logger = get_logger(__name__)


class SessionManager:
    """Manages user sessions across devices.

    Features:
    - Multi-session support per user
    - Session lifecycle management
    - Device tracking and validation
    - Automatic session cleanup
    - Session activity tracking
    """

    def __init__(
        self,
        storage: StorageBackend | None = None,
        audit_service: AuditService | None = None,
        token_service: TokenRefreshService | None = None,
    ):
        """Initialize session manager.

        Args:
            storage: Storage backend
            audit_service: Audit service
            token_service: Token refresh service
        """
        self.storage = storage or get_storage_backend()
        self.audit = audit_service or AuditService()
        self.token_service = token_service or TokenRefreshService(storage, audit_service)

        # Configuration
        self.max_sessions = int(os.getenv("MAX_SESSIONS_PER_USER", "10"))
        self.idle_timeout = int(os.getenv("SESSION_IDLE_TIMEOUT", "1800"))  # 30 min
        self.absolute_timeout = int(os.getenv("SESSION_ABSOLUTE_TIMEOUT", "86400"))  # 24h
        self.enable_binding = os.getenv("ENABLE_SESSION_BINDING", "true").lower() == "true"

    async def create_session(
        self,
        user_id: str,
        token_pair: TokenPair,
        device_info: DeviceInfo | None = None,
        ip_address: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Session:
        """Create a new session for user.

        Args:
            user_id: User identifier
            token_pair: Initial token pair
            device_info: Device information
            ip_address: Client IP address
            metadata: Additional metadata

        Returns:
            Created session

        Raises:
            ValueError: Max sessions exceeded
        """
        # Check session limit
        await self._enforce_session_limit(user_id)

        # Create session
        session = Session(
            user_id=user_id,
            access_token=token_pair.access_token,
            refresh_token=token_pair.refresh_token or "",
            expires_at=token_pair.access_expires_at,
            refresh_expires_at=token_pair.refresh_expires_at or datetime.utcnow(),
            device_info=device_info,
            ip_address=ip_address or "",
            metadata=metadata or {},
        )

        # Store session
        await self._store_session(session)

        # Add to user's session list
        await self._add_user_session(user_id, session.session_id)

        # Audit
        await self.audit.log_session_created(
            session_id=session.session_id,
            user_id=user_id,
            device_info=device_info,
            ip_address=ip_address,
        )

        logger.info(f"Session created: {session.session_id} for user {user_id}")
        return session

    async def get_session(
        self,
        session_id: str,
        validate: bool = True,
    ) -> Session | None:
        """Get session by ID.

        Args:
            session_id: Session identifier
            validate: Whether to validate session status

        Returns:
            Session if found and valid
        """
        session_data = await self.storage.get(f"session:{session_id}")

        if not session_data:
            return None

        session = Session.from_dict(session_data)

        if validate:
            # Check if session is still valid
            if session.status != SessionStatus.ACTIVE:
                logger.warning(f"Session {session_id} is not active: {session.status}")
                return None

            # Update activity if active
            session.update_activity()
            await self._store_session(session)

        return session

    async def get_user_sessions(
        self,
        user_id: str,
        active_only: bool = True,
    ) -> list[Session]:
        """Get all sessions for a user.

        Args:
            user_id: User identifier
            active_only: Only return active sessions

        Returns:
            List of user sessions
        """
        # Get session IDs
        session_ids = await self._get_user_session_ids(user_id)

        sessions = []
        for session_id in session_ids:
            session = await self.get_session(session_id, validate=False)
            if session:
                if not active_only or session.status == SessionStatus.ACTIVE:
                    sessions.append(session)

        # Sort by last activity
        sessions.sort(key=lambda s: s.last_activity, reverse=True)

        return sessions

    async def validate_session(
        self,
        session_id: str,
        device_info: DeviceInfo | None = None,
        ip_address: str | None = None,
    ) -> tuple[bool, str | None]:
        """Validate session with security checks.

        Args:
            session_id: Session to validate
            device_info: Current device info
            ip_address: Current IP address

        Returns:
            (is_valid, error_message)
        """
        session = await self.get_session(session_id, validate=False)

        if not session:
            return False, "Session not found"

        # Check session status
        if session.status != SessionStatus.ACTIVE:
            return False, f"Session {session.status.value}"

        # Check idle timeout
        idle_delta = datetime.utcnow() - session.last_activity
        if idle_delta.total_seconds() > self.idle_timeout:
            await self.terminate_session(session_id, "Idle timeout")
            return False, "Session idle timeout"

        # Check absolute timeout
        absolute_delta = datetime.utcnow() - session.created_at
        if absolute_delta.total_seconds() > self.absolute_timeout:
            await self.terminate_session(session_id, "Absolute timeout")
            return False, "Session absolute timeout"

        # Check device binding
        if self.enable_binding and device_info:
            if not session.matches_device(device_info):
                # Suspicious device change
                await self.audit.log_suspicious_activity(
                    session_id=session_id,
                    reason="Device mismatch",
                    details={
                        "expected": session.device_info.to_dict() if session.device_info else None,
                        "actual": device_info.to_dict(),
                    },
                )

                if session.device_info and session.device_info.is_suspicious_change(device_info):
                    await self.terminate_session(session_id, "Suspicious device change")
                    return False, "Session terminated due to device change"

        # Check IP binding
        if self.enable_binding and ip_address:
            if not session.matches_ip(ip_address, strict=False):
                # Log IP change but don't terminate yet
                await self.audit.log_session_ip_change(
                    session_id=session_id,
                    old_ip=session.ip_address,
                    new_ip=ip_address,
                )

        # Check if token needs refresh
        if session.should_refresh():
            try:
                new_tokens = await self.token_service.refresh_token(
                    session.refresh_token,
                    session_id
                )
                session.update_tokens(new_tokens)
                await self._store_session(session)
            except Exception as e:
                logger.error(f"Token refresh failed during validation: {e}")
                # Don't fail validation, let it expire naturally

        return True, None

    async def update_session_tokens(
        self,
        session_id: str,
        token_pair: TokenPair,
    ) -> None:
        """Update session with new tokens.

        Args:
            session_id: Session to update
            token_pair: New token pair
        """
        session = await self.get_session(session_id, validate=False)

        if not session:
            raise ValueError(f"Session {session_id} not found")

        session.update_tokens(token_pair)
        await self._store_session(session)

        await self.audit.log_session_tokens_updated(
            session_id=session_id,
            user_id=session.user_id,
        )

    async def terminate_session(
        self,
        session_id: str,
        reason: str | None = None,
    ) -> None:
        """Terminate a specific session.

        Args:
            session_id: Session to terminate
            reason: Termination reason
        """
        session = await self.get_session(session_id, validate=False)

        if not session:
            return

        # Revoke the session
        session.revoke(reason)
        await self._store_session(session)

        # Revoke associated tokens
        if session.access_token:
            await self._revoke_token(session.access_token)
        if session.refresh_token:
            await self._revoke_token(session.refresh_token)

        # Remove from user's active sessions
        await self._remove_user_session(session.user_id, session_id)

        # Audit
        await self.audit.log_session_terminated(
            session_id=session_id,
            user_id=session.user_id,
            reason=reason,
        )

        logger.info(f"Session terminated: {session_id}, reason: {reason}")

    async def terminate_all_user_sessions(
        self,
        user_id: str,
        except_session: str | None = None,
        reason: str | None = None,
    ) -> int:
        """Terminate all sessions for a user.

        Args:
            user_id: User whose sessions to terminate
            except_session: Session to keep active
            reason: Termination reason

        Returns:
            Number of sessions terminated
        """
        sessions = await self.get_user_sessions(user_id, active_only=False)

        terminated = 0
        for session in sessions:
            if session.session_id != except_session:
                await self.terminate_session(session.session_id, reason)
                terminated += 1

        logger.info(f"Terminated {terminated} sessions for user {user_id}")
        return terminated

    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions.

        Returns:
            Number of sessions cleaned up
        """
        # This would be called periodically by a cron job
        # For serverless, might use a scheduled function

        cleaned = 0

        # Get all session keys (would need to implement pattern search in storage)
        # For now, this is a placeholder

        logger.info(f"Cleaned up {cleaned} expired sessions")
        return cleaned

    async def _store_session(self, session: Session) -> None:
        """Store session in backend.

        Args:
            session: Session to store
        """
        # Calculate TTL based on refresh token expiry
        ttl = int((session.refresh_expires_at - datetime.utcnow()).total_seconds())
        ttl = max(ttl, 0)  # Ensure non-negative

        await self.storage.set(
            f"session:{session.session_id}",
            session.to_dict(),
            expire=ttl if ttl > 0 else None,
        )

    async def _add_user_session(self, user_id: str, session_id: str) -> None:
        """Add session to user's session list.

        Args:
            user_id: User ID
            session_id: Session ID to add
        """
        key = f"user_sessions:{user_id}"
        sessions_data: Any = await self.storage.get(key) or []
        sessions: list[str] = sessions_data if isinstance(sessions_data, list) else []

        if session_id not in sessions:
            sessions.append(session_id)

        await self.storage.set(key, sessions)

    async def _remove_user_session(self, user_id: str, session_id: str) -> None:
        """Remove session from user's session list.

        Args:
            user_id: User ID
            session_id: Session ID to remove
        """
        key = f"user_sessions:{user_id}"
        sessions_data: Any = await self.storage.get(key) or []
        sessions: list[str] = sessions_data if isinstance(sessions_data, list) else []

        if session_id in sessions:
            sessions.remove(session_id)

        await self.storage.set(key, sessions)

    async def _get_user_session_ids(self, user_id: str) -> list[str]:
        """Get all session IDs for a user.

        Args:
            user_id: User ID

        Returns:
            List of session IDs
        """
        key = f"user_sessions:{user_id}"
        sessions_data: Any = await self.storage.get(key) or []
        return sessions_data if isinstance(sessions_data, list) else []

    async def _enforce_session_limit(self, user_id: str) -> None:
        """Enforce maximum session limit per user.

        Args:
            user_id: User ID

        Raises:
            ValueError: If limit exceeded and can't clean up
        """
        sessions = await self.get_user_sessions(user_id, active_only=True)

        if len(sessions) >= self.max_sessions:
            # Try to clean up inactive sessions first
            for session in sessions:
                if session.status != SessionStatus.ACTIVE:
                    await self.terminate_session(
                        session.session_id,
                        "Cleanup for new session"
                    )

            # Check again
            sessions = await self.get_user_sessions(user_id, active_only=True)

            if len(sessions) >= self.max_sessions:
                # Terminate oldest session
                oldest = min(sessions, key=lambda s: s.last_activity)
                await self.terminate_session(
                    oldest.session_id,
                    "Max sessions reached"
                )

    async def _revoke_token(self, token: str) -> None:
        """Revoke a token.

        Args:
            token: Token to revoke
        """
        from ..models import TokenMetadata

        token_hash = TokenMetadata.hash_token(token)
        await self.storage.set(
            f"revoked:{token_hash}",
            {"revoked_at": datetime.utcnow().isoformat()},
            expire=86400 * 7,  # Keep for 7 days
        )
