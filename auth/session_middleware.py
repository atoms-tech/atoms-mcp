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
        """Load session before request, save after request."""
        global _request_session_context

        # Reset session context for this request
        _request_session_context.clear()

        # Extract session_id from header or cookie
        session_id = self._extract_session_id(request)

        if session_id:
            logger.debug(f"Processing request with session_id: {session_id}")

            # Load session from Supabase
            session_manager = self.session_manager_factory()
            session_data = await session_manager.get_session(session_id)

            if session_data:
                # Store in request-scoped context
                _request_session_context["session_id"] = session_id
                _request_session_context["user_id"] = session_data["user_id"]
                _request_session_context["oauth_data"] = session_data["oauth_data"]
                _request_session_context["mcp_state"] = session_data.get("mcp_state", {})

                logger.debug(f"✅ Loaded session for user {session_data['user_id']}")

                # Extend session on activity
                await session_manager.extend_session(session_id)
            else:
                logger.warning(f"Session {session_id} not found or expired")
                # Return 401 for invalid sessions on MCP endpoints
                if request.url.path.startswith("/api/mcp"):
                    return JSONResponse(
                        {"error": "Session expired or invalid"},
                        status_code=401
                    )
        else:
            logger.debug("No session_id in request")

        # Process request
        response = await call_next(request)

        # Optionally save updated MCP state after request
        # (if tools modified the session context)
        if session_id and _request_session_context.get("_modified"):
            session_manager = self.session_manager_factory()
            await session_manager.update_session(
                session_id,
                mcp_state=_request_session_context.get("mcp_state")
            )
            logger.debug(f"✅ Saved updated session state for {session_id}")

        return response

    def _extract_session_id(self, request: Request) -> Optional[str]:
        """Extract session_id from request headers or cookies.

        Priority:
        1. X-MCP-Session-ID header
        2. mcp_session_id cookie
        3. Authorization header (if it's a session ID, not JWT)

        Args:
            request: Starlette request

        Returns:
            session_id or None
        """
        # Check custom header first
        session_id = request.headers.get("x-mcp-session-id")
        if session_id:
            return session_id

        # Check cookie
        session_id = request.cookies.get("mcp_session_id")
        if session_id:
            return session_id

        # Check Authorization header (only if it looks like a UUID, not a JWT)
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]
            # Simple heuristic: UUIDs are 36 chars with dashes, JWTs are much longer
            if len(token) == 36 and token.count("-") == 4:
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
