"""Auth utilities for Atoms MCP."""

from .session_middleware import (
    SessionMiddleware,
    get_session_context,
    get_session_token,
    mark_session_modified,
    update_session_state,
)

# Note: SessionManager is now part of config/session.py
# Import here for backward compatibility
try:
    from config.session import SessionManager, create_session_manager
except ImportError:
    # Fallback for tests or minimal setups
    SessionManager = None
    create_session_manager = None

__all__ = [
    "SessionMiddleware",
    "SessionManager",
    "create_session_manager",
    "get_session_context",
    "get_session_token",
    "mark_session_modified",
    "update_session_state",
]
