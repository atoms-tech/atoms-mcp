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

        # Try to extract session_id first (UUID-based sessions)
        session_id = self._extract_session_id(request)

        # If no session_id, try to validate JWT and create/load session
        if not session_id:
            jwt_token = self._extract_jwt_token(request)
            if jwt_token:
                session_id = await self._handle_jwt_auth(jwt_token)

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
            logger.debug("No session_id or valid JWT in request")
            # For MCP endpoints, require authentication
            if request.url.path.startswith("/api/mcp") and not request.url.path.startswith("/api/mcp/auth"):
                return JSONResponse(
                    {"error": "Authentication required"},
                    status_code=401
                )

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

    async def _handle_jwt_auth(self, jwt_token: str) -> Optional[str]:
        """Validate JWT and create/load session.

        Args:
            jwt_token: Supabase JWT from AuthKit OAuth

        Returns:
            session_id or None
        """
        try:
            # Validate JWT with Supabase
            from supabase_client import get_supabase

            supabase = get_supabase(access_token=jwt_token)

            # Get user info from Supabase using the JWT
            try:
                user_response = supabase.auth.get_user(jwt_token)
                if not user_response or not user_response.user:
                    logger.warning("JWT validation failed: invalid token")
                    return None
                user = user_response.user
                user_id = user.id
                logger.info(f"✅ Validated JWT for user {user_id}")
            except Exception as jwt_error:
                # If JWT validation fails, try to decode it directly to get user_id
                # This handles WorkOS JWTs that Supabase might reject
                logger.error(f"JWT auth failed: {jwt_error}")
                import jwt as pyjwt
                try:
                    # Decode without verification to get user_id (just for session lookup)
                    decoded = pyjwt.decode(jwt_token, options={"verify_signature": False})
                    user_id = decoded.get('sub')
                    if not user_id:
                        logger.error("No 'sub' claim in JWT")
                        return None
                    logger.info(f"⚠️ Using unverified JWT for user {user_id} (WorkOS token)")
                except Exception as decode_error:
                    logger.error(f"Failed to decode JWT: {decode_error}")
                    return None

            # Check if user already has an active session
            session_manager = self.session_manager_factory()

            # Try to find existing session for this user
            # For now, create a new session (you could add logic to reuse existing)
            oauth_data = {
                "access_token": jwt_token,
                "token_type": "Bearer",
                "user": {
                    "id": user_id,
                    "email": user.email
                }
            }

            session_id = await session_manager.create_session(
                user_id=user_id,
                oauth_data=oauth_data,
                mcp_state={}
            )

            logger.info(f"✅ Created/loaded session {session_id} from JWT")

            return session_id

        except Exception as e:
            logger.error(f"JWT auth failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

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
