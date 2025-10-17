"""Session model for multi-session management."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, Any

from .device import DeviceInfo
from .token import TokenPair


class SessionStatus(Enum):
    """Session status enumeration."""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    IDLE = "idle"


@dataclass
class Session:
    """Represents an authenticated user session.

    Attributes:
        session_id: Unique session identifier
        user_id: User identifier from auth provider
        access_token: Current access token
        refresh_token: Refresh token for obtaining new access tokens
        expires_at: When the access token expires
        refresh_expires_at: When the refresh token expires
        created_at: Session creation timestamp
        last_activity: Last activity timestamp
        device_info: Device/browser information
        ip_address: Client IP address
        is_active: Whether session is currently active
        revoked_at: Revocation timestamp if revoked
        revocation_reason: Reason for revocation
        metadata: Additional session metadata
    """

    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    access_token: str = ""
    refresh_token: str = ""
    expires_at: datetime = field(default_factory=datetime.utcnow)
    refresh_expires_at: datetime = field(default_factory=datetime.utcnow)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    device_info: Optional[DeviceInfo] = None
    ip_address: str = ""
    is_active: bool = True
    revoked_at: Optional[datetime] = None
    revocation_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def status(self) -> SessionStatus:
        """Get current session status."""
        if not self.is_active:
            return SessionStatus.REVOKED

        now = datetime.utcnow()

        if self.revoked_at:
            return SessionStatus.REVOKED

        if now >= self.refresh_expires_at:
            return SessionStatus.EXPIRED

        # Check idle timeout (30 minutes by default)
        idle_timeout = timedelta(minutes=30)
        if now - self.last_activity > idle_timeout:
            return SessionStatus.IDLE

        return SessionStatus.ACTIVE

    @property
    def access_token_expired(self) -> bool:
        """Check if access token is expired."""
        return datetime.utcnow() >= self.expires_at

    @property
    def refresh_token_expired(self) -> bool:
        """Check if refresh token is expired."""
        return datetime.utcnow() >= self.refresh_expires_at

    @property
    def should_refresh(self, buffer_seconds: int = 300) -> bool:
        """Check if token should be refreshed proactively.

        Args:
            buffer_seconds: Refresh buffer before expiration

        Returns:
            True if token should be refreshed
        """
        if self.access_token_expired:
            return True

        buffer = timedelta(seconds=buffer_seconds)
        return datetime.utcnow() >= (self.expires_at - buffer)

    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()

    def update_tokens(self, token_pair: TokenPair) -> None:
        """Update session with new token pair.

        Args:
            token_pair: New token pair
        """
        self.access_token = token_pair.access_token

        if token_pair.refresh_token:
            self.refresh_token = token_pair.refresh_token

        now = datetime.utcnow()
        self.expires_at = now + timedelta(seconds=token_pair.access_expires_in)

        if token_pair.refresh_expires_in:
            self.refresh_expires_at = now + timedelta(
                seconds=token_pair.refresh_expires_in
            )

        self.update_activity()

    def revoke(self, reason: Optional[str] = None) -> None:
        """Revoke the session.

        Args:
            reason: Revocation reason
        """
        self.is_active = False
        self.revoked_at = datetime.utcnow()
        self.revocation_reason = reason or "User initiated"

    def matches_device(self, device_info: DeviceInfo) -> bool:
        """Check if session matches device info.

        Args:
            device_info: Device info to compare

        Returns:
            True if device matches
        """
        if not self.device_info:
            return True

        return (
            self.device_info.device_id == device_info.device_id
            or (
                self.device_info.user_agent == device_info.user_agent
                and self.device_info.device_type == device_info.device_type
            )
        )

    def matches_ip(self, ip_address: str, strict: bool = False) -> bool:
        """Check if session matches IP address.

        Args:
            ip_address: IP address to compare
            strict: Whether to enforce strict matching

        Returns:
            True if IP matches or validation disabled
        """
        if not strict:
            return True

        # In production, consider IP range matching for mobile networks
        return self.ip_address == ip_address

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "expires_at": self.expires_at.isoformat(),
            "refresh_expires_at": self.refresh_expires_at.isoformat(),
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "device_info": (
                self.device_info.to_dict() if self.device_info else None
            ),
            "ip_address": self.ip_address,
            "is_active": self.is_active,
            "status": self.status.value,
            "revoked_at": (
                self.revoked_at.isoformat() if self.revoked_at else None
            ),
            "revocation_reason": self.revocation_reason,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Session:
        """Create session from dictionary.

        Args:
            data: Dictionary data

        Returns:
            Session instance
        """
        # Parse datetime fields
        for field_name in ["expires_at", "refresh_expires_at", "created_at", "last_activity"]:
            if field_name in data and isinstance(data[field_name], str):
                data[field_name] = datetime.fromisoformat(data[field_name])

        if "revoked_at" in data and data["revoked_at"]:
            data["revoked_at"] = datetime.fromisoformat(data["revoked_at"])

        # Parse device info
        if "device_info" in data and data["device_info"]:
            from .device import DeviceInfo
            data["device_info"] = DeviceInfo.from_dict(data["device_info"])

        # Remove non-model fields
        data.pop("status", None)

        return cls(**data)