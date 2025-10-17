"""Token refresh service with proactive refresh and rotation."""

from __future__ import annotations

import asyncio
import os
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any

import httpx
import jwt
from fastmcp.server.dependencies import get_access_token

from ..models import TokenPair, RefreshTokenRotation, TokenMetadata, TokenType
from ..storage import StorageBackend, get_storage_backend
from .audit import AuditService
from utils.logging_setup import get_logger

logger = get_logger(__name__)


class TokenRefreshService:
    """Manages token refresh with rotation and proactive refresh.

    Features:
    - Proactive token refresh before expiration
    - Refresh token rotation with grace period
    - Automatic retry with exponential backoff
    - Audit logging of all operations
    """

    def __init__(
        self,
        storage: Optional[StorageBackend] = None,
        audit_service: Optional[AuditService] = None,
    ):
        """Initialize token refresh service.

        Args:
            storage: Storage backend for tokens
            audit_service: Audit service for logging
        """
        self.storage = storage or get_storage_backend()
        self.audit = audit_service or AuditService()

        # Configuration from environment
        self.access_expires_in = int(os.getenv("ACCESS_TOKEN_EXPIRES_IN", "3600"))
        self.refresh_expires_in = int(os.getenv("REFRESH_TOKEN_EXPIRES_IN", "604800"))
        self.rotation_enabled = os.getenv("REFRESH_TOKEN_ROTATION", "true").lower() == "true"
        self.refresh_buffer = int(os.getenv("REFRESH_BUFFER_SECONDS", "300"))
        self.workos_api_url = os.getenv("WORKOS_API_URL", "https://api.workos.com")
        self.workos_api_key = os.getenv("WORKOS_API_KEY", "")

    async def refresh_token(
        self,
        refresh_token: str,
        session_id: Optional[str] = None,
        force_rotation: bool = False,
    ) -> TokenPair:
        """Refresh access token using refresh token.

        Args:
            refresh_token: Current refresh token
            session_id: Optional session ID for tracking
            force_rotation: Force refresh token rotation

        Returns:
            New token pair

        Raises:
            ValueError: Invalid refresh token
            RuntimeError: Refresh operation failed
        """
        try:
            # Validate refresh token
            await self._validate_refresh_token(refresh_token, session_id)

            # Call AuthKit token refresh endpoint
            new_tokens = await self._call_authkit_refresh(refresh_token)

            # Handle rotation if enabled
            if self.rotation_enabled or force_rotation:
                new_tokens = await self._handle_rotation(
                    refresh_token,
                    new_tokens,
                    session_id
                )

            # Store token metadata
            await self._store_token_metadata(new_tokens, session_id)

            # Audit the refresh
            await self.audit.log_token_refresh(
                session_id=session_id,
                old_token_hash=TokenMetadata.hash_token(refresh_token),
                new_token_hash=TokenMetadata.hash_token(new_tokens.access_token),
                rotation=self.rotation_enabled or force_rotation,
            )

            logger.info(f"Token refreshed for session {session_id}")
            return new_tokens

        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            await self.audit.log_token_refresh_failure(
                session_id=session_id,
                error=str(e)
            )
            raise

    async def proactive_refresh(
        self,
        access_token: str,
        refresh_token: str,
        session_id: Optional[str] = None,
    ) -> Optional[TokenPair]:
        """Proactively refresh token if approaching expiration.

        Args:
            access_token: Current access token
            refresh_token: Current refresh token
            session_id: Optional session ID

        Returns:
            New token pair if refreshed, None otherwise
        """
        try:
            # Check if token needs refresh
            if not self._should_refresh(access_token):
                return None

            logger.info(f"Proactive refresh triggered for session {session_id}")
            return await self.refresh_token(refresh_token, session_id)

        except Exception as e:
            logger.warning(f"Proactive refresh failed: {e}")
            # Don't raise - let it fail gracefully
            return None

    async def _validate_refresh_token(
        self,
        refresh_token: str,
        session_id: Optional[str] = None
    ) -> None:
        """Validate refresh token before use.

        Args:
            refresh_token: Token to validate
            session_id: Optional session ID

        Raises:
            ValueError: Token is invalid or revoked
        """
        # Check if token is revoked
        token_hash = TokenMetadata.hash_token(refresh_token)
        is_revoked = await self.storage.is_token_revoked(token_hash)

        if is_revoked:
            raise ValueError("Refresh token has been revoked")

        # Check rotation if session provided
        if session_id and self.rotation_enabled:
            rotation_key = f"rotation:{session_id}"
            rotation_data = await self.storage.get(rotation_key)

            if rotation_data:
                rotation = RefreshTokenRotation(**rotation_data)
                if not rotation.is_valid(refresh_token):
                    raise ValueError("Invalid refresh token for rotation")

    async def _call_authkit_refresh(self, refresh_token: str) -> TokenPair:
        """Call AuthKit API to refresh tokens.

        Args:
            refresh_token: Refresh token

        Returns:
            New token pair

        Raises:
            RuntimeError: API call failed
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.workos_api_url}/sso/token",
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": refresh_token,
                        "client_id": os.getenv("WORKOS_CLIENT_ID"),
                        "client_secret": os.getenv("WORKOS_CLIENT_SECRET"),
                    },
                    headers={
                        "Authorization": f"Bearer {self.workos_api_key}",
                    },
                    timeout=10.0,
                )

                response.raise_for_status()
                data = response.json()

                return TokenPair(
                    access_token=data["access_token"],
                    refresh_token=data.get("refresh_token", refresh_token),
                    access_expires_in=data.get("expires_in", self.access_expires_in),
                    refresh_expires_in=self.refresh_expires_in,
                    scope=data.get("scope", "openid profile email"),
                    token_type=data.get("token_type", "Bearer"),
                )

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    raise ValueError("Invalid or expired refresh token")
                raise RuntimeError(f"Token refresh failed: {e}")
            except Exception as e:
                raise RuntimeError(f"Token refresh failed: {e}")

    async def _handle_rotation(
        self,
        old_refresh_token: str,
        new_tokens: TokenPair,
        session_id: Optional[str] = None,
    ) -> TokenPair:
        """Handle refresh token rotation.

        Args:
            old_refresh_token: Previous refresh token
            new_tokens: New token pair
            session_id: Session ID for tracking

        Returns:
            Token pair with rotated refresh token
        """
        if not session_id:
            return new_tokens

        rotation_key = f"rotation:{session_id}"

        # Get or create rotation tracker
        rotation_data = await self.storage.get(rotation_key)

        if rotation_data:
            rotation = RefreshTokenRotation(**rotation_data)
        else:
            rotation = RefreshTokenRotation(current_token=old_refresh_token)

        # Generate new refresh token if not provided
        if not new_tokens.refresh_token or new_tokens.refresh_token == old_refresh_token:
            new_tokens.refresh_token = rotation.rotate()
        else:
            # Use provided new token
            rotation.previous_token = rotation.current_token
            rotation.current_token = new_tokens.refresh_token
            rotation.rotation_count += 1
            rotation.last_rotation = datetime.utcnow()

        # Store rotation state
        await self.storage.set(
            rotation_key,
            rotation.__dict__,
            expire=self.refresh_expires_in
        )

        # Invalidate old token after grace period
        asyncio.create_task(self._invalidate_after_grace(
            rotation_key,
            rotation.grace_period_seconds
        ))

        return new_tokens

    async def _invalidate_after_grace(self, rotation_key: str, grace_seconds: int):
        """Invalidate previous token after grace period.

        Args:
            rotation_key: Rotation storage key
            grace_seconds: Grace period in seconds
        """
        await asyncio.sleep(grace_seconds)

        try:
            rotation_data = await self.storage.get(rotation_key)
            if rotation_data:
                rotation = RefreshTokenRotation(**rotation_data)
                rotation.invalidate_previous()
                await self.storage.set(
                    rotation_key,
                    rotation.__dict__,
                    expire=self.refresh_expires_in
                )
        except Exception as e:
            logger.error(f"Failed to invalidate previous token: {e}")

    async def _store_token_metadata(
        self,
        token_pair: TokenPair,
        session_id: Optional[str] = None
    ) -> None:
        """Store token metadata for tracking.

        Args:
            token_pair: Token pair to store
            session_id: Associated session ID
        """
        if not session_id:
            return

        # Decode token for user info
        try:
            decoded = jwt.decode(
                token_pair.access_token,
                options={"verify_signature": False}
            )
            user_id = decoded.get("sub") or decoded.get("user_id")
        except Exception:
            user_id = "unknown"

        # Store access token metadata
        access_meta = TokenMetadata(
            token_hash=TokenMetadata.hash_token(token_pair.access_token),
            token_type=TokenType.ACCESS,
            user_id=user_id,
            session_id=session_id,
            expires_at=token_pair.access_expires_at,
        )

        await self.storage.set(
            f"token:access:{access_meta.token_hash}",
            access_meta.to_dict(),
            expire=token_pair.access_expires_in
        )

        # Store refresh token metadata
        if token_pair.refresh_token:
            refresh_meta = TokenMetadata(
                token_hash=TokenMetadata.hash_token(token_pair.refresh_token),
                token_type=TokenType.REFRESH,
                user_id=user_id,
                session_id=session_id,
                expires_at=token_pair.refresh_expires_at,
            )

            await self.storage.set(
                f"token:refresh:{refresh_meta.token_hash}",
                refresh_meta.to_dict(),
                expire=token_pair.refresh_expires_in
            )

    def _should_refresh(self, access_token: str) -> bool:
        """Check if token should be refreshed.

        Args:
            access_token: Access token to check

        Returns:
            True if should refresh
        """
        try:
            # Decode without verification to check expiry
            decoded = jwt.decode(
                access_token,
                options={"verify_signature": False}
            )

            exp = decoded.get("exp")
            if not exp:
                return False

            # Check if approaching expiration
            expiry_time = datetime.fromtimestamp(exp)
            buffer = timedelta(seconds=self.refresh_buffer)
            return datetime.utcnow() >= (expiry_time - buffer)

        except Exception:
            # If can't decode, probably should refresh
            return True