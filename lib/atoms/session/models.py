"""
Session and Token Models

Comprehensive data models for session lifecycle management, token tracking,
device fingerprinting, and audit logging.
"""

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any
from uuid import uuid4


class SessionState(str, Enum):
    """Session lifecycle states."""

    ACTIVE = "active"
    IDLE = "idle"
    EXPIRED = "expired"
    REVOKED = "revoked"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"


class AuditAction(str, Enum):
    """Audit log action types."""

    # Session actions
    SESSION_CREATED = "session_created"
    SESSION_ACCESSED = "session_accessed"
    SESSION_REFRESHED = "session_refreshed"
    SESSION_EXPIRED = "session_expired"
    SESSION_REVOKED = "session_revoked"
    SESSION_TERMINATED = "session_terminated"

    # Token actions
    TOKEN_ISSUED = "token_issued"
    TOKEN_REFRESHED = "token_refreshed"
    TOKEN_ROTATED = "token_rotated"
    TOKEN_REVOKED = "token_revoked"
    TOKEN_VALIDATED = "token_validated"
    TOKEN_INTROSPECTED = "token_introspected"

    # Security actions
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    INVALID_DEVICE = "invalid_device"
    IP_CHANGE_DETECTED = "ip_change_detected"
    SESSION_HIJACK_ATTEMPT = "session_hijack_attempt"

    # Authentication actions
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    FORCED_LOGOUT = "forced_logout"


@dataclass
class DeviceFingerprint:
    """
    Device fingerprinting for session security.

    Tracks device characteristics to detect session hijacking
    and unauthorized access attempts.
    """

    fingerprint_id: str = field(default_factory=lambda: str(uuid4()))
    user_agent: str | None = None
    accept_language: str | None = None
    screen_resolution: str | None = None
    timezone: str | None = None
    platform: str | None = None
    device_memory: int | None = None
    hardware_concurrency: int | None = None
    color_depth: int | None = None
    pixel_ratio: float | None = None
    touch_support: bool = False
    canvas_fingerprint: str | None = None
    webgl_fingerprint: str | None = None
    audio_fingerprint: str | None = None
    fonts: list[str] = field(default_factory=list)
    plugins: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_seen: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary with datetime serialization."""
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        data["last_seen"] = self.last_seen.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DeviceFingerprint":
        """Create from dictionary with datetime parsing."""
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if "last_seen" in data and isinstance(data["last_seen"], str):
            data["last_seen"] = datetime.fromisoformat(data["last_seen"])
        return cls(**data)

    def matches(self, other: "DeviceFingerprint", threshold: float = 0.8) -> bool:
        """
        Check if another fingerprint matches this one.

        Args:
            other: Another device fingerprint
            threshold: Similarity threshold (0.0-1.0)

        Returns:
            True if fingerprints match above threshold
        """
        if not other:
            return False

        # Critical fields that must match exactly
        critical_fields = ["user_agent", "platform", "timezone"]
        for field_name in critical_fields:
            if getattr(self, field_name) != getattr(other, field_name):
                return False

        # Score other fields
        total_fields = 0
        matching_fields = 0

        comparable_fields = [
            "accept_language", "screen_resolution", "color_depth",
            "pixel_ratio", "touch_support", "device_memory",
            "hardware_concurrency", "canvas_fingerprint",
            "webgl_fingerprint", "audio_fingerprint"
        ]

        for field_name in comparable_fields:
            val1 = getattr(self, field_name)
            val2 = getattr(other, field_name)
            if val1 is not None and val2 is not None:
                total_fields += 1
                if val1 == val2:
                    matching_fields += 1

        if total_fields == 0:
            return False

        similarity = matching_fields / total_fields
        return similarity >= threshold


@dataclass
class TokenRefreshRecord:
    """
    Token refresh tracking with rotation support.

    Maintains complete history of token refreshes including
    rotation tracking and grace periods.
    """

    record_id: str = field(default_factory=lambda: str(uuid4()))
    session_id: str = ""
    user_id: str = ""

    # Token information
    old_access_token_hash: str | None = None
    new_access_token_hash: str = ""
    old_refresh_token_hash: str | None = None
    new_refresh_token_hash: str = ""

    # Timing
    refreshed_at: datetime = field(default_factory=datetime.utcnow)
    old_token_expires_at: datetime | None = None
    new_token_expires_at: datetime | None = None
    grace_period_ends_at: datetime | None = None

    # Metadata
    refresh_reason: str = "proactive"  # proactive, expired, user_requested, forced
    rotation_enabled: bool = True
    rotation_count: int = 0

    # Security
    ip_address: str | None = None
    user_agent: str | None = None
    device_fingerprint_id: str | None = None

    # Status
    is_successful: bool = True
    error_message: str | None = None
    retry_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary with datetime serialization."""
        data = asdict(self)
        data["refreshed_at"] = self.refreshed_at.isoformat()
        if self.old_token_expires_at:
            data["old_token_expires_at"] = self.old_token_expires_at.isoformat()
        if self.new_token_expires_at:
            data["new_token_expires_at"] = self.new_token_expires_at.isoformat()
        if self.grace_period_ends_at:
            data["grace_period_ends_at"] = self.grace_period_ends_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TokenRefreshRecord":
        """Create from dictionary with datetime parsing."""
        datetime_fields = [
            "refreshed_at", "old_token_expires_at",
            "new_token_expires_at", "grace_period_ends_at"
        ]
        for field_name in datetime_fields:
            if field_name in data and isinstance(data[field_name], str):
                data[field_name] = datetime.fromisoformat(data[field_name])
        return cls(**data)


@dataclass
class Session:
    """
    Comprehensive session model with lifecycle management.

    Tracks complete session state including tokens, device information,
    security metadata, and lifecycle timestamps.
    """

    session_id: str = field(default_factory=lambda: str(uuid4()))
    user_id: str = ""

    # Token storage
    access_token: str = ""
    refresh_token: str | None = None
    id_token: str | None = None
    token_type: str = "Bearer"

    # Token metadata
    access_token_expires_at: datetime | None = None
    refresh_token_expires_at: datetime | None = None
    scopes: list[str] = field(default_factory=list)

    # Session state
    state: SessionState = SessionState.ACTIVE

    # Device and security
    device_fingerprint: DeviceFingerprint | None = None
    ip_address: str | None = None
    user_agent: str | None = None

    # Timing
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_accessed_at: datetime = field(default_factory=datetime.utcnow)
    last_refreshed_at: datetime | None = None
    expires_at: datetime | None = None

    # Timeout configuration
    idle_timeout_minutes: int = 30
    absolute_timeout_minutes: int = 480  # 8 hours

    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)
    provider: str = "openrouter"

    # Refresh tracking
    refresh_count: int = 0
    last_refresh_record_id: str | None = None

    def __post_init__(self):
        """Initialize computed fields."""
        if not self.expires_at:
            self.expires_at = self.created_at + timedelta(
                minutes=self.absolute_timeout_minutes
            )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary with proper serialization."""
        data = {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "id_token": self.id_token,
            "token_type": self.token_type,
            "access_token_expires_at": (
                self.access_token_expires_at.isoformat()
                if self.access_token_expires_at else None
            ),
            "refresh_token_expires_at": (
                self.refresh_token_expires_at.isoformat()
                if self.refresh_token_expires_at else None
            ),
            "scopes": self.scopes,
            "state": self.state.value,
            "device_fingerprint": (
                self.device_fingerprint.to_dict()
                if self.device_fingerprint else None
            ),
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "created_at": self.created_at.isoformat(),
            "last_accessed_at": self.last_accessed_at.isoformat(),
            "last_refreshed_at": (
                self.last_refreshed_at.isoformat()
                if self.last_refreshed_at else None
            ),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "idle_timeout_minutes": self.idle_timeout_minutes,
            "absolute_timeout_minutes": self.absolute_timeout_minutes,
            "metadata": self.metadata,
            "provider": self.provider,
            "refresh_count": self.refresh_count,
            "last_refresh_record_id": self.last_refresh_record_id,
        }
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Session":
        """Create from dictionary with proper parsing."""
        # Parse datetime fields
        datetime_fields = [
            "access_token_expires_at", "refresh_token_expires_at",
            "created_at", "last_accessed_at", "last_refreshed_at", "expires_at"
        ]
        for field_name in datetime_fields:
            if field_name in data and isinstance(data[field_name], str):
                data[field_name] = datetime.fromisoformat(data[field_name])

        # Parse state enum
        if "state" in data and isinstance(data["state"], str):
            data["state"] = SessionState(data["state"])

        # Parse device fingerprint
        if "device_fingerprint" in data and isinstance(data["device_fingerprint"], dict):
            data["device_fingerprint"] = DeviceFingerprint.from_dict(
                data["device_fingerprint"]
            )

        return cls(**data)

    def is_active(self) -> bool:
        """Check if session is currently active."""
        return self.state == SessionState.ACTIVE

    def is_expired(self) -> bool:
        """Check if session has expired."""
        if self.state in [SessionState.EXPIRED, SessionState.REVOKED, SessionState.TERMINATED]:
            return True

        now = datetime.utcnow()

        # Check absolute timeout
        if self.expires_at and now > self.expires_at:
            return True

        # Check idle timeout
        idle_deadline = self.last_accessed_at + timedelta(
            minutes=self.idle_timeout_minutes
        )
        if now > idle_deadline:
            return True

        return False

    def needs_refresh(self, buffer_minutes: int = 5) -> bool:
        """
        Check if access token needs refresh.

        Args:
            buffer_minutes: Minutes before expiry to trigger refresh

        Returns:
            True if token should be refreshed
        """
        if not self.access_token_expires_at:
            return False

        now = datetime.utcnow()
        refresh_deadline = self.access_token_expires_at - timedelta(
            minutes=buffer_minutes
        )

        return now >= refresh_deadline

    def update_access(self, ip_address: str | None = None):
        """Update last access timestamp and IP."""
        self.last_accessed_at = datetime.utcnow()
        if ip_address:
            self.ip_address = ip_address

    def mark_refreshed(self, refresh_record_id: str):
        """Mark session as refreshed."""
        self.last_refreshed_at = datetime.utcnow()
        self.refresh_count += 1
        self.last_refresh_record_id = refresh_record_id


@dataclass
class AuditLog:
    """
    Comprehensive audit logging for security and compliance.

    Tracks all session and token operations with complete context
    for security monitoring and forensic analysis.
    """

    log_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Action details
    action: AuditAction = AuditAction.SESSION_ACCESSED
    action_details: str = ""

    # Context
    session_id: str | None = None
    user_id: str | None = None

    # Security context
    ip_address: str | None = None
    user_agent: str | None = None
    device_fingerprint_id: str | None = None

    # Request context
    request_id: str | None = None
    endpoint: str | None = None
    http_method: str | None = None

    # Result
    is_success: bool = True
    error_code: str | None = None
    error_message: str | None = None

    # Additional metadata
    metadata: dict[str, Any] = field(default_factory=dict)

    # Security flags
    is_suspicious: bool = False
    risk_score: float = 0.0  # 0.0 - 1.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary with proper serialization."""
        return {
            "log_id": self.log_id,
            "timestamp": self.timestamp.isoformat(),
            "action": self.action.value,
            "action_details": self.action_details,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "device_fingerprint_id": self.device_fingerprint_id,
            "request_id": self.request_id,
            "endpoint": self.endpoint,
            "http_method": self.http_method,
            "is_success": self.is_success,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "metadata": self.metadata,
            "is_suspicious": self.is_suspicious,
            "risk_score": self.risk_score,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AuditLog":
        """Create from dictionary with proper parsing."""
        if "timestamp" in data and isinstance(data["timestamp"], str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        if "action" in data and isinstance(data["action"], str):
            data["action"] = AuditAction(data["action"])
        return cls(**data)

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
