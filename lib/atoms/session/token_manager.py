"""
Token Manager

Comprehensive token lifecycle management including proactive refresh,
rotation, introspection, and error recovery with exponential backoff.
"""

import asyncio
import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import httpx

from .models import AuditAction, AuditLog, Session, TokenRefreshRecord
from .storage.base import StorageBackend

logger = logging.getLogger(__name__)


class TokenRefreshError(Exception):
    """Raised when token refresh fails."""
    pass


class TokenValidationError(Exception):
    """Raised when token validation fails."""
    pass


@dataclass
class RetryConfig:
    """Configuration for exponential backoff retry logic."""

    max_retries: int = 3
    initial_delay: float = 1.0
    max_delay: float = 30.0
    exponential_base: float = 2.0
    jitter: bool = True


@dataclass
class RefreshConfig:
    """Configuration for token refresh behavior."""

    proactive_refresh_minutes: int = 5
    rotation_enabled: bool = True
    grace_period_minutes: int = 5
    introspection_enabled: bool = True
    audit_enabled: bool = True


class TokenManager:
    """
    Manages token lifecycle including refresh, rotation, and validation.

    Features:
    - Proactive token refresh (default 5 minutes before expiry)
    - Automatic refresh token rotation with grace periods
    - Token introspection for validation
    - Exponential backoff retry logic
    - Comprehensive error recovery
    - Audit logging
    """

    def __init__(
        self,
        storage: StorageBackend,
        token_endpoint: str,
        introspection_endpoint: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        refresh_config: RefreshConfig | None = None,
        retry_config: RetryConfig | None = None,
    ):
        """
        Initialize token manager.

        Args:
            storage: Storage backend for sessions and tokens
            token_endpoint: OAuth2 token endpoint URL
            introspection_endpoint: Optional token introspection endpoint
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            refresh_config: Token refresh configuration
            retry_config: Retry configuration
        """
        self.storage = storage
        self.token_endpoint = token_endpoint
        self.introspection_endpoint = introspection_endpoint
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_config = refresh_config or RefreshConfig()
        self.retry_config = retry_config or RetryConfig()

        self._http_client: httpx.AsyncClient | None = None

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                timeout=30.0,
                follow_redirects=True,
            )
        return self._http_client

    async def close(self):
        """Close HTTP client and cleanup resources."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    def _hash_token(self, token: str) -> str:
        """Create secure hash of token for storage."""
        return hashlib.sha256(token.encode()).hexdigest()

    async def _execute_with_retry(
        self,
        operation: callable,
        operation_name: str,
    ) -> Any:
        """
        Execute operation with exponential backoff retry.

        Args:
            operation: Async operation to execute
            operation_name: Name for logging

        Returns:
            Operation result

        Raises:
            TokenRefreshError: If all retries exhausted
        """
        last_error = None

        for attempt in range(self.retry_config.max_retries):
            try:
                return await operation()
            except Exception as e:
                last_error = e

                if attempt < self.retry_config.max_retries - 1:
                    # Calculate delay with exponential backoff
                    delay = min(
                        self.retry_config.initial_delay * (
                            self.retry_config.exponential_base ** attempt
                        ),
                        self.retry_config.max_delay
                    )

                    # Add jitter if enabled
                    if self.retry_config.jitter:
                        import random
                        delay = delay * (0.5 + random.random() * 0.5)

                    logger.warning(
                        f"{operation_name} attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"{operation_name} failed after {self.retry_config.max_retries} attempts"
                    )

        raise TokenRefreshError(
            f"{operation_name} failed after {self.retry_config.max_retries} attempts: {last_error}"
        )

    async def refresh_token(
        self,
        session: Session,
        force: bool = False,
        reason: str = "proactive",
    ) -> tuple[Session, TokenRefreshRecord]:
        """
        Refresh access token with rotation support.

        Args:
            session: Session to refresh
            force: Force refresh even if not needed
            reason: Reason for refresh (for audit trail)

        Returns:
            Tuple of (updated session, refresh record)

        Raises:
            TokenRefreshError: If refresh fails
        """
        # Check if refresh is needed
        if not force and not session.needs_refresh(
            self.refresh_config.proactive_refresh_minutes
        ):
            logger.debug(f"Session {session.session_id} does not need refresh yet")
            raise TokenRefreshError("Token does not need refresh yet")

        if not session.refresh_token:
            raise TokenRefreshError("No refresh token available")

        logger.info(
            f"Refreshing token for session {session.session_id} (reason: {reason})"
        )

        # Create refresh record
        record = TokenRefreshRecord(
            session_id=session.session_id,
            user_id=session.user_id,
            old_access_token_hash=self._hash_token(session.access_token),
            old_refresh_token_hash=self._hash_token(session.refresh_token),
            old_token_expires_at=session.access_token_expires_at,
            refresh_reason=reason,
            rotation_enabled=self.refresh_config.rotation_enabled,
            rotation_count=session.refresh_count,
            ip_address=session.ip_address,
            user_agent=session.user_agent,
            device_fingerprint_id=(
                session.device_fingerprint.fingerprint_id
                if session.device_fingerprint else None
            ),
        )

        # Execute refresh with retry
        async def _do_refresh():
            client = await self._get_http_client()

            data = {
                "grant_type": "refresh_token",
                "refresh_token": session.refresh_token,
            }

            if self.client_id:
                data["client_id"] = self.client_id
            if self.client_secret:
                data["client_secret"] = self.client_secret

            response = await client.post(
                self.token_endpoint,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code != 200:
                error_data = response.json() if response.text else {}
                raise TokenRefreshError(
                    f"Token refresh failed: {response.status_code} - "
                    f"{error_data.get('error', 'unknown error')}"
                )

            return response.json()

        try:
            token_data = await self._execute_with_retry(
                _do_refresh,
                "Token refresh"
            )

            # Update session with new tokens
            session.access_token = token_data["access_token"]

            # Handle refresh token rotation
            if "refresh_token" in token_data:
                # New refresh token provided - rotation enabled
                session.refresh_token = token_data["refresh_token"]
                record.new_refresh_token_hash = self._hash_token(
                    session.refresh_token
                )

                # Set grace period for old refresh token
                if self.refresh_config.grace_period_minutes > 0:
                    record.grace_period_ends_at = datetime.utcnow() + timedelta(
                        minutes=self.refresh_config.grace_period_minutes
                    )
            else:
                # No rotation - keep existing refresh token
                record.new_refresh_token_hash = record.old_refresh_token_hash

            # Update token hashes and expiry
            record.new_access_token_hash = self._hash_token(session.access_token)

            if "expires_in" in token_data:
                session.access_token_expires_at = datetime.utcnow() + timedelta(
                    seconds=token_data["expires_in"]
                )
                record.new_token_expires_at = session.access_token_expires_at

            # Update scopes if provided
            if "scope" in token_data:
                session.scopes = token_data["scope"].split()

            # Update ID token if provided
            if "id_token" in token_data:
                session.id_token = token_data["id_token"]

            # Mark refresh as successful
            record.is_successful = True
            session.mark_refreshed(record.record_id)

            # Store updated session and refresh record
            await self.storage.save_session(session)
            await self.storage.save_refresh_record(record)

            # Audit log
            if self.refresh_config.audit_enabled:
                await self._create_audit_log(
                    action=AuditAction.TOKEN_REFRESHED,
                    session=session,
                    details=f"Token refreshed successfully (reason: {reason})",
                    metadata={
                        "refresh_record_id": record.record_id,
                        "rotation_enabled": record.rotation_enabled,
                    }
                )

            logger.info(
                f"Successfully refreshed token for session {session.session_id}"
            )

            return session, record

        except Exception as e:
            # Mark refresh as failed
            record.is_successful = False
            record.error_message = str(e)
            record.retry_count = self.retry_config.max_retries

            # Store failed record for audit
            await self.storage.save_refresh_record(record)

            # Audit log
            if self.refresh_config.audit_enabled:
                await self._create_audit_log(
                    action=AuditAction.TOKEN_REFRESHED,
                    session=session,
                    details=f"Token refresh failed: {e}",
                    is_success=False,
                    error_message=str(e),
                    metadata={"refresh_record_id": record.record_id}
                )

            logger.error(
                f"Failed to refresh token for session {session.session_id}: {e}"
            )
            raise

    async def introspect_token(
        self,
        token: str,
        token_type_hint: str = "access_token",
    ) -> dict[str, Any]:
        """
        Introspect token to validate and get metadata.

        Args:
            token: Token to introspect
            token_type_hint: Type of token (access_token or refresh_token)

        Returns:
            Introspection response data

        Raises:
            TokenValidationError: If introspection fails
        """
        if not self.introspection_endpoint:
            raise TokenValidationError("Token introspection not configured")

        logger.debug(f"Introspecting {token_type_hint}")

        async def _do_introspect():
            client = await self._get_http_client()

            data = {
                "token": token,
                "token_type_hint": token_type_hint,
            }

            if self.client_id:
                data["client_id"] = self.client_id
            if self.client_secret:
                data["client_secret"] = self.client_secret

            response = await client.post(
                self.introspection_endpoint,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code != 200:
                raise TokenValidationError(
                    f"Token introspection failed: {response.status_code}"
                )

            return response.json()

        try:
            result = await self._execute_with_retry(
                _do_introspect,
                "Token introspection"
            )

            logger.debug(f"Token introspection result: active={result.get('active')}")
            return result

        except Exception as e:
            logger.error(f"Token introspection failed: {e}")
            raise TokenValidationError(f"Token introspection failed: {e}")

    async def validate_token(
        self,
        session: Session,
        check_expiry: bool = True,
    ) -> bool:
        """
        Validate token using introspection or local checks.

        Args:
            session: Session to validate
            check_expiry: Whether to check expiry time

        Returns:
            True if token is valid
        """
        # Check local expiry first if enabled
        if check_expiry and session.access_token_expires_at:
            if datetime.utcnow() >= session.access_token_expires_at:
                logger.debug(f"Token expired for session {session.session_id}")
                return False

        # Use introspection if enabled and available
        if self.refresh_config.introspection_enabled and self.introspection_endpoint:
            try:
                result = await self.introspect_token(session.access_token)
                return result.get("active", False)
            except TokenValidationError as e:
                logger.warning(f"Introspection validation failed: {e}")
                # Fall back to local validation

        # Local validation - check if we have a token
        return bool(session.access_token)

    async def get_refresh_history(
        self,
        session_id: str,
        limit: int = 10,
    ) -> list[TokenRefreshRecord]:
        """
        Get refresh history for a session.

        Args:
            session_id: Session ID
            limit: Maximum number of records to return

        Returns:
            List of refresh records
        """
        return await self.storage.get_refresh_history(session_id, limit)

    async def _create_audit_log(
        self,
        action: AuditAction,
        session: Session | None = None,
        details: str = "",
        is_success: bool = True,
        error_message: str | None = None,
        metadata: dict[str, Any] | None = None,
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
            is_success=is_success,
            error_message=error_message,
            metadata=metadata or {},
        )

        await self.storage.save_audit_log(log)

    async def __aenter__(self):
        """Context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.close()
