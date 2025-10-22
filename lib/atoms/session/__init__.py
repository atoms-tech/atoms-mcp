"""
Atoms Session Management Module

Provides comprehensive session and token management for OAuth2/OIDC flows.
Includes token refresh, rotation, revocation, and security features.
"""

from .models import (
    AuditAction,
    AuditLog,
    DeviceFingerprint,
    Session,
    SessionState,
    TokenRefreshRecord,
)
from .revocation import RevocationError, RevocationService
from .security import RateLimitError, SecurityService, SuspiciousActivityError
from .session_manager import SessionError, SessionExpiredError, SessionManager
from .token_manager import TokenManager, TokenRefreshError, TokenValidationError

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
