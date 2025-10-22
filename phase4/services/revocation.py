"""Token and session revocation service."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from utils.logging_setup import get_logger

from ..models import TokenMetadata, TokenType
from ..storage import StorageBackend, get_storage_backend
from .audit import AuditService

logger = get_logger(__name__)


class RevocationService:
    """Handles token and session revocation.

    Features:
    - Immediate token revocation
    - Cascading session termination
    - Revocation list management
    - Audit trail for all revocations
    """

    def __init__(
        self,
        storage: StorageBackend | None = None,
        audit_service: AuditService | None = None,
    ):
        """Initialize revocation service.

        Args:
            storage: Storage backend
            audit_service: Audit service
        """
        self.storage = storage or get_storage_backend()
        self.audit = audit_service or AuditService()

    async def revoke_token(
        self,
        token: str,
        is_refresh: bool = False,
        reason: str | None = None,
        cascade: bool = True,
    ) -> datetime:
        """Revoke a token immediately.

        Args:
            token: Token to revoke
            is_refresh: Whether this is a refresh token
            reason: Revocation reason
            cascade: Whether to revoke related tokens/sessions

        Returns:
            Revocation timestamp
        """
        # Hash token for storage
        token_hash = TokenMetadata.hash_token(token)
        revoked_at = datetime.utcnow()

        # Store in revocation list
        revocation_key = f"revoked:{token_hash}"
        revocation_data = {
            "revoked_at": revoked_at.isoformat(),
            "reason": reason or "Manual revocation",
            "token_type": "refresh_token" if is_refresh else "access_token",
        }

        # Store with long TTL (7 days)
        await self.storage.set(
            revocation_key,
            revocation_data,
            expire=86400 * 7
        )

        # Get token metadata if available
        token_type = TokenType.REFRESH if is_refresh else TokenType.ACCESS
        metadata_key = f"token:{token_type.value}:{token_hash}"
        metadata = await self.storage.get(metadata_key)

        session_id = None
        user_id = None

        if metadata:
            # Update metadata to mark as revoked
            metadata["revoked"] = True
            metadata["revoked_at"] = revoked_at.isoformat()
            metadata["revocation_reason"] = reason

            await self.storage.set(metadata_key, metadata)

            session_id = metadata.get("session_id")
            user_id = metadata.get("user_id")

        # Cascade revocation if needed
        if cascade and session_id:
            await self._cascade_revocation(session_id, reason)

        # Audit the revocation
        await self.audit.log_token_revoked(
            token_hash=token_hash,
            token_type=token_type.value,
            reason=reason,
            session_id=session_id,
            user_id=user_id,
        )

        logger.info(
            f"Token revoked: type={token_type.value}, "
            f"session={session_id}, reason={reason}"
        )

        return revoked_at

    async def revoke_session_tokens(
        self,
        session_id: str,
        reason: str | None = None,
    ) -> int:
        """Revoke all tokens for a session.

        Args:
            session_id: Session ID
            reason: Revocation reason

        Returns:
            Number of tokens revoked
        """
        # Get session data
        session_key = f"session:{session_id}"
        session_data = await self.storage.get(session_key)

        if not session_data:
            logger.warning(f"Session {session_id} not found for revocation")
            return 0

        revoked = 0

        # Revoke access token
        if "access_token" in session_data:
            await self.revoke_token(
                session_data["access_token"],
                is_refresh=False,
                reason=reason,
                cascade=False
            )
            revoked += 1

        # Revoke refresh token
        if "refresh_token" in session_data:
            await self.revoke_token(
                session_data["refresh_token"],
                is_refresh=True,
                reason=reason,
                cascade=False
            )
            revoked += 1

        logger.info(f"Revoked {revoked} tokens for session {session_id}")
        return revoked

    async def revoke_user_tokens(
        self,
        user_id: str,
        reason: str | None = None,
        except_session: str | None = None,
    ) -> int:
        """Revoke all tokens for a user.

        Args:
            user_id: User ID
            reason: Revocation reason
            except_session: Session to exclude

        Returns:
            Number of tokens revoked
        """
        # Get user sessions
        sessions_key = f"user_sessions:{user_id}"
        sessions_data: Any = await self.storage.get(sessions_key) or []
        session_ids: list[str] = sessions_data if isinstance(sessions_data, list) else []

        revoked = 0

        for session_id in session_ids:
            if session_id != except_session:
                count = await self.revoke_session_tokens(session_id, reason)
                revoked += count

        logger.info(f"Revoked {revoked} tokens for user {user_id}")
        return revoked

    async def is_token_revoked(self, token: str) -> bool:
        """Check if token is revoked.

        Args:
            token: Token to check

        Returns:
            True if revoked
        """
        token_hash = TokenMetadata.hash_token(token)
        return await self.storage.is_token_revoked(token_hash)

    async def get_revocation_list(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        """Get list of revoked tokens.

        Args:
            limit: Maximum items to return
            offset: Offset for pagination

        Returns:
            List of revocation records
        """
        # Scan for revoked tokens
        pattern = "revoked:*"
        keys = await self.storage.scan(pattern, count=limit)

        revocations = []

        for key in keys[offset:offset + limit]:
            data = await self.storage.get(key)
            if data:
                token_hash = key.replace("revoked:", "")
                revocations.append({
                    "token_hash": token_hash,
                    **data
                })

        # Sort by revocation time
        revocations.sort(
            key=lambda x: x.get("revoked_at", ""),
            reverse=True
        )

        return revocations

    async def cleanup_expired_revocations(self) -> int:
        """Clean up old revocation records.

        Returns:
            Number of records cleaned
        """
        # This would be called by a scheduled job
        # Revocation records auto-expire via TTL

        pattern = "revoked:*"
        keys = await self.storage.scan(pattern, count=1000)

        cleaned = 0

        for key in keys:
            ttl = await self.storage.ttl(key)

            # If no TTL set, set it to 7 days
            if ttl is None:
                await self.storage.expire(key, 86400 * 7)
                cleaned += 1

        logger.info(f"Cleaned up {cleaned} revocation records")
        return cleaned

    async def _cascade_revocation(
        self,
        session_id: str,
        reason: str | None = None
    ) -> None:
        """Cascade revocation to related tokens and sessions.

        Args:
            session_id: Session ID
            reason: Revocation reason
        """
        # Revoke all tokens for the session
        await self.revoke_session_tokens(session_id, reason)

        # Mark session as revoked
        session_key = f"session:{session_id}"
        session_data = await self.storage.get(session_key)

        if session_data:
            session_data["is_active"] = False
            session_data["revoked_at"] = datetime.utcnow().isoformat()
            session_data["revocation_reason"] = reason

            await self.storage.set(session_key, session_data)
