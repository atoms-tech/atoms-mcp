"""Session middleware for FastMCP with Supabase-backed session persistence.

This middleware intercepts requests to load OAuth state from Supabase sessions,
enabling stateless serverless deployments.
"""

from __future__ import annotations

import logging
from typing import Optional, Dict, Any
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

logger = logging.getLogger(__name__)

# Global context to store session data for the current request
# This is reset on each request and used by tools to access OAuth tokens
_request_session_context: Dict[str, Any] = {}


class SessionMiddleware(BaseHTTPMiddleware):
    """Middleware to load/save MCP sessions from Supabase."""

    def __init__(self, app, session_manager_factory):
        """Initialize middleware.

        Args:
            app: ASGI app
            session_manager_factory: Callable that returns SessionManager instance
        """
        super().__init__(app)
        self.session_manager_factory = session_manager_factory

    async def dispatch(self, request: Request, call_next) -> Response:
        """Extract JWT and set user context - AuthKit manages sessions."""
        global _request_session_context

        # Reset session context for this request
        _request_session_context.clear()

        # Extract JWT token from request (AuthKit JWT)
        jwt_token = self._extract_jwt_token(request)

        if jwt_token:
            # Decode JWT to get user info (AuthKit already validated it)
            import jwt as pyjwt
            try:
                decoded = pyjwt.decode(jwt_token, options={"verify_signature": False})
                user_id = decoded.get('sub')

                if user_id:
                    # Store user context from JWT claims
                    _request_session_context["user_id"] = user_id
                    _request_session_context["access_token"] = jwt_token
                    _request_session_context["oauth_data"] = {
                        "access_token": jwt_token,
                        "user": {
                            "id": user_id,
                            "email": decoded.get('email'),
                            "role": decoded.get('role', 'authenticated')
                        }
                    }

                    logger.debug(f"✅ Set user context from JWT for user {user_id}")
                else:
                    logger.warning("No user_id in JWT")
            except Exception as e:
                logger.error(f"Failed to decode JWT: {e}")

        # Check if MCP endpoint requires auth
        if request.url.path.startswith("/api/mcp") and not request.url.path.startswith("/api/mcp/auth"):
            if not _request_session_context.get("user_id"):
                return JSONResponse(
                    {"error": "Authentication required"},
                    status_code=401
                )

        # Process request
        response = await call_next(request)

        # Session state is managed by AuthKit JWT - no persistence needed
        return response

    def _extract_jwt_token(self, request: Request) -> Optional[str]:
        """Extract JWT token from Authorization header.

        Returns:
            JWT token string or None
        """
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]
            # If it's longer than UUID (36 chars), it's likely a JWT
            if len(token) > 36:
                return token
        return None


def get_session_context() -> Dict[str, Any]:
    """Get the current request's session context.

    This is called by server.py to access OAuth tokens within tool handlers.

    Returns:
        Session context dict with oauth_data, user_id, etc.
    """
    return _request_session_context.copy()


def get_session_token() -> Optional[str]:
    """Get the OAuth access token from current session context.

    Returns:
        Access token or None
    """
    oauth_data = _request_session_context.get("oauth_data", {})
    return oauth_data.get("access_token") or oauth_data.get("token")


def mark_session_modified() -> None:
    """Mark session as modified to trigger save after request."""
    _request_session_context["_modified"] = True


def update_session_state(key: str, value: Any) -> None:
    """Update MCP state in current session and mark as modified.

    Args:
        key: State key
        value: State value
    """
    if "mcp_state" not in _request_session_context:
        _request_session_context["mcp_state"] = {}

    _request_session_context["mcp_state"][key] = value
    mark_session_modified()
