"""Phase 4: Token Refresh and Session Management.

This package provides advanced authentication features including:
- Proactive token refresh with rotation
- Multi-session management
- Token revocation with audit trails
- Security middleware for rate limiting and anti-hijacking
"""

from .middleware import RateLimiter, SecurityMiddleware, SessionValidator
from .models import DeviceInfo, Session, TokenPair
from .services import RevocationService, SessionManager, TokenRefreshService
from .storage import get_storage_backend

__version__ = "4.0.0"

__all__ = [
    # Models
    "Session",
    "TokenPair",
    "DeviceInfo",

    # Services
    "TokenRefreshService",
    "SessionManager",
    "RevocationService",

    # Storage
    "get_storage_backend",

    # Middleware
    "RateLimiter",
    "SessionValidator",
    "SecurityMiddleware",
]
