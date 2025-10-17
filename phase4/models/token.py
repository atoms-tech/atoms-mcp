"""Token models for authentication."""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, Any


class TokenType(Enum):
    """Token type enumeration."""
    ACCESS = "access_token"
    REFRESH = "refresh_token"
    ID_TOKEN = "id_token"


@dataclass
class TokenPair:
    """Represents an access/refresh token pair.

    Attributes:
        access_token: JWT access token
        refresh_token: Optional refresh token
        access_expires_in: Access token expiration in seconds
        refresh_expires_in: Refresh token expiration in seconds
        scope: Token scope/permissions
        token_type: Token type (Bearer)
        issued_at: When tokens were issued
    """

    access_token: str
    access_expires_in: int = 3600  # 1 hour default
    refresh_token: Optional[str] = None
    refresh_expires_in: Optional[int] = 604800  # 7 days default
    scope: str = "openid profile email"
    token_type: str = "Bearer"
    issued_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def access_expires_at(self) -> datetime:
        """Get access token expiration time."""
        return self.issued_at + timedelta(seconds=self.access_expires_in)

    @property
    def refresh_expires_at(self) -> Optional[datetime]:
        """Get refresh token expiration time."""
        if self.refresh_token and self.refresh_expires_in:
            return self.issued_at + timedelta(seconds=self.refresh_expires_in)
        return None

    def to_response(self) -> Dict[str, Any]:
        """Convert to OAuth2 token response format.

        Returns:
            OAuth2 compliant response
        """
        response = {
            "access_token": self.access_token,
            "token_type": self.token_type,
            "expires_in": self.access_expires_in,
            "scope": self.scope,
        }

        if self.refresh_token:
            response["refresh_token"] = self.refresh_token

        return response


@dataclass
class RefreshTokenRotation:
    """Manages refresh token rotation with grace period.

    Attributes:
        current_token: Current valid refresh token
        previous_token: Previous token (for grace period)
        rotation_count: Number of rotations performed
        grace_period_seconds: Grace period for race conditions
        last_rotation: When last rotation occurred
    """

    current_token: str
    previous_token: Optional[str] = None
    rotation_count: int = 0
    grace_period_seconds: int = 60  # 1 minute grace
    last_rotation: datetime = field(default_factory=datetime.utcnow)

    def rotate(self) -> str:
        """Rotate to a new refresh token.

        Returns:
            New refresh token
        """
        # Move current to previous
        self.previous_token = self.current_token

        # Generate new token
        self.current_token = self._generate_refresh_token()

        # Update metadata
        self.rotation_count += 1
        self.last_rotation = datetime.utcnow()

        return self.current_token

    def is_valid(self, token: str) -> bool:
        """Check if a token is valid (current or within grace period).

        Args:
            token: Token to validate

        Returns:
            True if token is valid
        """
        # Check current token
        if self._secure_compare(token, self.current_token):
            return True

        # Check previous token within grace period
        if self.previous_token and self._secure_compare(token, self.previous_token):
            grace_end = self.last_rotation + timedelta(
                seconds=self.grace_period_seconds
            )
            return datetime.utcnow() < grace_end

        return False

    def invalidate_previous(self) -> None:
        """Invalidate the previous token."""
        self.previous_token = None

    @staticmethod
    def _generate_refresh_token() -> str:
        """Generate a secure refresh token.

        Returns:
            Cryptographically secure token
        """
        # Generate 32 bytes of random data
        token_bytes = secrets.token_bytes(32)
        # Convert to URL-safe base64
        return secrets.token_urlsafe(32)

    @staticmethod
    def _secure_compare(a: str, b: str) -> bool:
        """Constant-time string comparison to prevent timing attacks.

        Args:
            a: First string
            b: Second string

        Returns:
            True if strings match
        """
        return secrets.compare_digest(a, b)


@dataclass
class TokenMetadata:
    """Metadata for token tracking and auditing.

    Attributes:
        token_hash: SHA256 hash of the token
        token_type: Type of token
        user_id: Associated user ID
        session_id: Associated session ID
        client_id: OAuth client ID
        issued_at: Issue timestamp
        expires_at: Expiration timestamp
        used_at: Last usage timestamp
        use_count: Number of times used
        revoked: Whether token is revoked
        revoked_at: Revocation timestamp
        revocation_reason: Why token was revoked
    """

    token_hash: str
    token_type: TokenType
    user_id: str
    session_id: str
    client_id: Optional[str] = None
    issued_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    used_at: Optional[datetime] = None
    use_count: int = 0
    revoked: bool = False
    revoked_at: Optional[datetime] = None
    revocation_reason: Optional[str] = None

    @staticmethod
    def hash_token(token: str) -> str:
        """Create SHA256 hash of token for storage.

        Args:
            token: Token to hash

        Returns:
            Hex-encoded hash
        """
        return hashlib.sha256(token.encode()).hexdigest()

    def record_use(self) -> None:
        """Record token usage."""
        self.use_count += 1
        self.used_at = datetime.utcnow()

    def revoke(self, reason: Optional[str] = None) -> None:
        """Revoke the token.

        Args:
            reason: Revocation reason
        """
        self.revoked = True
        self.revoked_at = datetime.utcnow()
        self.revocation_reason = reason or "Manual revocation"

    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() >= self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if token is valid (not revoked or expired)."""
        return not self.revoked and not self.is_expired

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage.

        Returns:
            Dictionary representation
        """
        return {
            "token_hash": self.token_hash,
            "token_type": self.token_type.value,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "client_id": self.client_id,
            "issued_at": self.issued_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "used_at": self.used_at.isoformat() if self.used_at else None,
            "use_count": self.use_count,
            "revoked": self.revoked,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
            "revocation_reason": self.revocation_reason,
        }