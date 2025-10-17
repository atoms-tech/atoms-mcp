"""
Session Manager

Comprehensive session lifecycle management including multi-session support,
device fingerprinting, timeout enforcement, and cleanup.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import uuid4

from .models import (
    Session,
    SessionState,
    DeviceFingerprint,
    AuditLog,
    AuditAction,
)
from .storage.base import StorageBackend
from .token_manager import TokenManager


logger = logging.getLogger(__name__)


class SessionError(Exception):
    """Base exception for session errors."""
    pass


class SessionExpiredError(SessionError):
    """Raised when session has expired."""
    pass


class SessionNotFoundError(SessionError):
    """Raised when session is not found."""
    pass


class DeviceValidationError(SessionError):
    """Raised when device validation fails."""
    pass


class SessionManager:
    """
    Manages session lifecycle with security features.

    Features:
    - Multi-session support per user
    - Device fingerprinting and validation
    - IP address tracking and validation
    - Idle and absolute timeout enforcement
    - Automatic session cleanup
    - Comprehensive audit logging
    """

    def __init__(
        self,
        storage: StorageBackend,
        token_manager: Optional[TokenManager] = None,
        default_idle_timeout_minutes: int = 30,
        default_absolute_timeout_minutes: int = 480,
        max_sessions_per_user: int = 5,
        device_validation_enabled: bool = True,
        device_match_threshold: float = 0.8,
        ip_validation_enabled: bool = False,
        audit_enabled: bool = True,
    ):
        """
        Initialize session manager.

        Args:
            storage: Storage backend for sessions
            token_manager: Optional token manager for refresh
            default_idle_timeout_minutes: Default idle timeout
            default_absolute_timeout_minutes: Default absolute timeout
            max_sessions_per_user: Maximum concurrent sessions per user
            device_validation_enabled: Enable device fingerprint validation
            device_match_threshold: Device matching threshold (0.0-1.0)
            ip_validation_enabled: Enable IP address validation
            audit_enabled: Enable audit logging
        """
        self.storage = storage
        self.token_manager = token_manager
        self.default_idle_timeout_minutes = default_idle_timeout_minutes
        self.default_absolute_timeout_minutes = default_absolute_timeout_minutes
        self.max_sessions_per_user = max_sessions_per_user
        self.device_validation_enabled = device_validation_enabled
        self.device_match_threshold = device_match_threshold
        self.ip_validation_enabled = ip_validation_enabled
        self.audit_enabled = audit_enabled

        # Background task for cleanup
        self._cleanup_task: Optional[asyncio.Task] = None

    async def create_session(
        self,
        user_id: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        id_token: Optional[str] = None,
        token_type: str = "Bearer",
        expires_in: Optional[int] = None,
        scopes: Optional[List[str]] = None,
        device_fingerprint: Optional[DeviceFingerprint] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        provider: str = "openrouter",
    ) -> Session:
        """
        Create new session with security tracking.

        Args:
            user_id: User identifier
            access_token: OAuth2 access token
            refresh_token: OAuth2 refresh token
            id_token: OIDC ID token
            token_type: Token type (usually "Bearer")
            expires_in: Token expiry in seconds
            scopes: List of granted scopes
            device_fingerprint: Device fingerprint for security
            ip_address: Client IP address
            user_agent: Client user agent
            metadata: Additional metadata
            provider: OAuth provider name

        Returns:
            Created session

        Raises:
            SessionError: If session creation fails
        """
        logger.info(f"Creating session for user {user_id}")

        # Check session limit for user
        user_sessions = await self.get_user_sessions(user_id)
        active_sessions = [
            s for s in user_sessions
            if s.state == SessionState.ACTIVE and not s.is_expired()
        ]

        if len(active_sessions) >= self.max_sessions_per_user:
            logger.warning(
                f"User {user_id} has {len(active_sessions)} active sessions, "
                f"limit is {self.max_sessions_per_user}"
            )
            # Terminate oldest session
            oldest = min(active_sessions, key=lambda s: s.created_at)
            await self.terminate_session(oldest.session_id, reason="session_limit")

        # Create session
        session = Session(
            session_id=str(uuid4()),
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            id_token=id_token,
            token_type=token_type,
            scopes=scopes or [],
            device_fingerprint=device_fingerprint,
            ip_address=ip_address,
            user_agent=user_agent,
            idle_timeout_minutes=self.default_idle_timeout_minutes,
            absolute_timeout_minutes=self.default_absolute_timeout_minutes,
            metadata=metadata or {},
            provider=provider,
        )

        # Set token expiry
        if expires_in:
            session.access_token_expires_at = datetime.utcnow() + timedelta(
                seconds=expires_in
            )

        # Save session
        await self.storage.save_session(session)

        # Audit log
        if self.audit_enabled:
            await self._create_audit_log(
                action=AuditAction.SESSION_CREATED,
                session=session,
                details=f"Session created for user {user_id}",
                metadata={
                    "provider": provider,
                    "has_refresh_token": refresh_token is not None,
                    "has_device_fingerprint": device_fingerprint is not None,
                }
            )

        logger.info(f"Created session {session.session_id} for user {user_id}")
        return session

    async def get_session(
        self,
        session_id: str,
        validate_device: bool = True,
        device_fingerprint: Optional[DeviceFingerprint] = None,
        ip_address: Optional[str] = None,
    ) -> Session:
        """
        Get session with optional device validation.

        Args:
            session_id: Session identifier
            validate_device: Whether to validate device fingerprint
            device_fingerprint: Current device fingerprint
            ip_address: Current IP address

        Returns:
            Session object

        Raises:
            SessionNotFoundError: If session not found
            SessionExpiredError: If session expired
            DeviceValidationError: If device validation fails
        """
        session = await self.storage.get_session(session_id)
        if not session:
            raise SessionNotFoundError(f"Session {session_id} not found")

        # Check if expired
        if session.is_expired():
            await self._handle_expired_session(session)
            raise SessionExpiredError(f"Session {session_id} has expired")

        # Validate device if enabled
        if (
            validate_device
            and self.device_validation_enabled
            and device_fingerprint
            and session.device_fingerprint
        ):
            if not session.device_fingerprint.matches(
                device_fingerprint,
                self.device_match_threshold
            ):
                await self._handle_device_mismatch(session, device_fingerprint)
                raise DeviceValidationError("Device fingerprint mismatch")

        # Validate IP if enabled
        if self.ip_validation_enabled and ip_address and session.ip_address:
            if ip_address != session.ip_address:
                await self._handle_ip_change(session, ip_address)

        # Update access time
        session.update_access(ip_address)
        await self.storage.save_session(session)

        # Audit log
        if self.audit_enabled:
            await self._create_audit_log(
                action=AuditAction.SESSION_ACCESSED,
                session=session,
                details="Session accessed",
            )

        return session

    async def get_user_sessions(
        self,
        user_id: str,
        include_expired: bool = False,
    ) -> List[Session]:
        """
        Get all sessions for a user.

        Args:
            user_id: User identifier
            include_expired: Include expired sessions

        Returns:
            List of sessions
        """
        sessions = await self.storage.get_user_sessions(user_id)

        if not include_expired:
            sessions = [s for s in sessions if not s.is_expired()]

        return sessions

    async def refresh_session(
        self,
        session_id: str,
        force: bool = False,
    ) -> Session:
        """
        Refresh session tokens.

        Args:
            session_id: Session identifier
            force: Force refresh even if not needed

        Returns:
            Updated session

        Raises:
            SessionError: If refresh fails
        """
        if not self.token_manager:
            raise SessionError("Token manager not configured")

        session = await self.get_session(session_id, validate_device=False)

        try:
            session, record = await self.token_manager.refresh_token(
                session,
                force=force,
            )

            logger.info(f"Refreshed session {session_id}")
            return session

        except Exception as e:
            logger.error(f"Failed to refresh session {session_id}: {e}")
            raise SessionError(f"Session refresh failed: {e}")

    async def update_session(
        self,
        session_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        device_fingerprint: Optional[DeviceFingerprint] = None,
    ) -> Session:
        """
        Update session metadata and device fingerprint.

        Args:
            session_id: Session identifier
            metadata: Metadata to update
            device_fingerprint: Updated device fingerprint

        Returns:
            Updated session
        """
        session = await self.get_session(session_id, validate_device=False)

        if metadata:
            session.metadata.update(metadata)

        if device_fingerprint:
            session.device_fingerprint = device_fingerprint

        await self.storage.save_session(session)

        logger.debug(f"Updated session {session_id}")
        return session

    async def terminate_session(
        self,
        session_id: str,
        reason: str = "user_logout",
    ):
        """
        Terminate session immediately.

        Args:
            session_id: Session identifier
            reason: Reason for termination
        """
        session = await self.storage.get_session(session_id)
        if not session:
            return

        session.state = SessionState.TERMINATED
        await self.storage.save_session(session)

        # Audit log
        if self.audit_enabled:
            await self._create_audit_log(
                action=AuditAction.SESSION_TERMINATED,
                session=session,
                details=f"Session terminated: {reason}",
                metadata={"reason": reason}
            )

        logger.info(f"Terminated session {session_id} (reason: {reason})")

    async def terminate_user_sessions(
        self,
        user_id: str,
        except_session_id: Optional[str] = None,
        reason: str = "user_logout_all",
    ):
        """
        Terminate all sessions for a user.

        Args:
            user_id: User identifier
            except_session_id: Optional session ID to keep active
            reason: Reason for termination
        """
        sessions = await self.get_user_sessions(user_id)

        for session in sessions:
            if session.session_id != except_session_id:
                await self.terminate_session(session.session_id, reason)

        logger.info(
            f"Terminated all sessions for user {user_id} "
            f"(except {except_session_id})"
        )

    async def cleanup_expired_sessions(
        self,
        batch_size: int = 100,
    ) -> int:
        """
        Clean up expired sessions.

        Args:
            batch_size: Number of sessions to process per batch

        Returns:
            Number of sessions cleaned up
        """
        logger.info("Starting expired session cleanup")

        cleaned = 0
        sessions = await self.storage.get_all_sessions(limit=batch_size)

        for session in sessions:
            if session.is_expired() and session.state == SessionState.ACTIVE:
                session.state = SessionState.EXPIRED
                await self.storage.save_session(session)
                cleaned += 1

                # Audit log
                if self.audit_enabled:
                    await self._create_audit_log(
                        action=AuditAction.SESSION_EXPIRED,
                        session=session,
                        details="Session expired during cleanup",
                    )

        logger.info(f"Cleaned up {cleaned} expired sessions")
        return cleaned

    async def start_cleanup_task(
        self,
        interval_minutes: int = 15,
    ):
        """
        Start background cleanup task.

        Args:
            interval_minutes: Cleanup interval in minutes
        """
        if self._cleanup_task:
            logger.warning("Cleanup task already running")
            return

        async def cleanup_loop():
            while True:
                try:
                    await asyncio.sleep(interval_minutes * 60)
                    await self.cleanup_expired_sessions()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in cleanup task: {e}")

        self._cleanup_task = asyncio.create_task(cleanup_loop())
        logger.info(f"Started cleanup task (interval: {interval_minutes} minutes)")

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

    async def _handle_expired_session(self, session: Session):
        """Handle expired session."""
        session.state = SessionState.EXPIRED
        await self.storage.save_session(session)

        if self.audit_enabled:
            await self._create_audit_log(
                action=AuditAction.SESSION_EXPIRED,
                session=session,
                details="Session expired",
            )

    async def _handle_device_mismatch(
        self,
        session: Session,
        current_fingerprint: DeviceFingerprint,
    ):
        """Handle device fingerprint mismatch."""
        if self.audit_enabled:
            await self._create_audit_log(
                action=AuditAction.INVALID_DEVICE,
                session=session,
                details="Device fingerprint mismatch detected",
                is_suspicious=True,
                risk_score=0.8,
                metadata={
                    "stored_fingerprint": (
                        session.device_fingerprint.to_dict()
                        if session.device_fingerprint else None
                    ),
                    "current_fingerprint": current_fingerprint.to_dict(),
                }
            )

    async def _handle_ip_change(
        self,
        session: Session,
        new_ip: str,
    ):
        """Handle IP address change."""
        if self.audit_enabled:
            await self._create_audit_log(
                action=AuditAction.IP_CHANGE_DETECTED,
                session=session,
                details=f"IP changed from {session.ip_address} to {new_ip}",
                is_suspicious=True,
                risk_score=0.5,
                metadata={
                    "old_ip": session.ip_address,
                    "new_ip": new_ip,
                }
            )

    async def _create_audit_log(
        self,
        action: AuditAction,
        session: Optional[Session] = None,
        details: str = "",
        is_suspicious: bool = False,
        risk_score: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Create and store audit log entry."""
        log = AuditLog(
            action=action,
            action_details=details,
            session_id=session.session_id if session else None,
            user_id=session.user_id if session else None,
            ip_address=session.ip_address if session else None,
            user_agent=session.user_agent if session else None,
            device_fingerprint_id=(
                session.device_fingerprint.fingerprint_id
                if session and session.device_fingerprint else None
            ),
            is_suspicious=is_suspicious,
            risk_score=risk_score,
            metadata=metadata or {},
        )

        await self.storage.save_audit_log(log)

    async def __aenter__(self):
        """Context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.stop_cleanup_task()
