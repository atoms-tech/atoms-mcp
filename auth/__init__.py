"""Auth Module: Authentication and Session Management.

This module provides authentication and session management for the Atoms MCP
Server. It implements a hybrid auth provider supporting both OAuth PKCE flow
and Bearer token authentication.

Components:
    1. SessionMiddleware: FastMCP middleware for session management
       - Extracts tokens from requests
       - Validates tokens
       - Manages session context
       - Handles token refresh

    2. SessionManager: Session lifecycle management
       - Create sessions
       - Validate sessions
       - Refresh tokens
       - Revoke sessions
       - Manage session state

    3. Auth Provider: Hybrid authentication
       - OAuth PKCE flow
       - Bearer token validation
       - Token introspection
       - Session persistence

Authentication Flows:
    1. OAuth PKCE Flow:
       - Agent initiates OAuth flow
       - User authenticates
       - Agent receives authorization code
       - Agent exchanges code for tokens
       - Session created with tokens

    2. Bearer Token Flow:
       - Agent provides Bearer token
       - Token validated against auth provider
       - Session created with token
       - Token refreshed as needed

Session Management:
    - Sessions stored in Redis
    - Tokens cached for performance
    - Automatic token refresh
    - Session expiration handling
    - Concurrent session support

Example:
    Using auth in tools:

    >>> from auth import get_session_context, get_session_token
    >>> session = get_session_context()
    >>> token = get_session_token()
    >>> # Use token for API calls
    >>> result = await api_call(token)

Note:
    - All auth operations are async
    - Sessions are stored in Redis
    - Tokens are validated on each request
    - Session context is thread-local
    - Auth is transparent to tools

See Also:
    - session_middleware.py: Middleware implementation
    - session_manager.py: Session manager implementation
    - provider.py: Auth provider implementation
    - tools/: Tools that use auth
"""

from .session_middleware import (
    SessionMiddleware,
    get_session_context,
    get_session_token,
    mark_session_modified,
    update_session_state,
)
from .session_manager import SessionManager, create_session_manager

__all__ = [
    "SessionMiddleware",
    "SessionManager",
    "create_session_manager",
    "get_session_context",
    "get_session_token",
    "mark_session_modified",
    "update_session_state",
]
