"""
Atoms Session Management Module

Provides comprehensive session and token management for OAuth2/OIDC flows.
Includes token refresh, rotation, revocation, and security features.
"""

from .models import (
    SessionState,
    Session,
    TokenRefreshRecord,
    DeviceFingerprint,
    AuditLog,
    AuditAction,
)
from .token_manager import TokenManager, TokenRefreshError, TokenValidationError
from .session_manager import SessionManager, SessionError, SessionExpiredError
from .revocation import RevocationService, RevocationError
from .security import SecurityService, RateLimitError, SuspiciousActivityError

__all__ = [
    # Models
    "SessionState",
    "Session",
    "TokenRefreshRecord",
    "DeviceFingerprint",
    "AuditLog",
    "AuditAction",
    # Token Management
    "TokenManager",
    "TokenRefreshError",
    "TokenValidationError",
    # Session Management
    "SessionManager",
    "SessionError",
    "SessionExpiredError",
    # Revocation
    "RevocationService",
    "RevocationError",
    # Security
    "SecurityService",
    "RateLimitError",
    "SuspiciousActivityError",
]

__version__ = "1.0.0"
