"""Persistent AuthKit Provider with Supabase session storage.

Extends FastMCP's AuthKitProvider to persist OAuth sessions in Supabase,
enabling stateless serverless deployments.
"""

from __future__ import annotations

import logging
import asyncio
from typing import Any, Optional
import aiohttp
from fastmcp.server.auth.providers.workos import AuthKitProvider
from starlette.responses import JSONResponse
from starlette.routing import Route

logger = logging.getLogger(__name__)


# Global aiohttp session for connection pooling across requests
_http_session: Optional[aiohttp.ClientSession] = None


def _get_http_session() -> aiohttp.ClientSession:
    """Get shared aiohttp session with connection pooling.

    Recreates the session when the current request runs on a new event loop.
    Vercel/AWS style runtimes spin up and tear down loops between invocations,
    so we must avoid reusing a session bound to a closed loop.
    """

    global _http_session

    # Always bind the session to the currently running loop.
    loop = asyncio.get_running_loop()
    needs_new_session = False

    if _http_session is None:
        needs_new_session = True
    else:
        session_loop = getattr(_http_session, "_loop", None)

        # ClientSession.closed only flips when close() is awaited; also guard
        # against reusing sessions that belong to a different or closed loop.
        if _http_session.closed:
            needs_new_session = True
        elif session_loop is not loop:
            needs_new_session = True
        elif session_loop and session_loop.is_closed():
            needs_new_session = True

    if needs_new_session:
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=30, ttl_dns_cache=300)
        _http_session = aiohttp.ClientSession(connector=connector)

    return _http_session


class PersistentAuthKitProvider(AuthKitProvider):
    """AuthKitProvider with Supabase-backed session persistence.

    This provider extends AuthKitProvider to:
    1. Create sessions in Supabase after OAuth completes
    2. Return session_id to clients for subsequent requests
    3. Work with SessionMiddleware to load sessions on each request

    Example:
        ```python
        from auth.persistent_authkit_provider import PersistentAuthKitProvider

        auth = PersistentAuthKitProvider(
            authkit_domain="https://your-app.authkit.app",
            base_url="https://your-server.com",
            session_ttl_hours=24
        )

        mcp = FastMCP("My App", auth=auth)
        ```
    """

    def __init__(
        self,
        *,
        authkit_domain: str,
        base_url: str,
        required_scopes: list[str] | None = None,
        token_verifier: Any = None,
        session_ttl_hours: int = 24,
    ):
        """Initialize persistent AuthKit provider.

        Args:
            authkit_domain: WorkOS AuthKit domain
            base_url: Public URL of this MCP server
            required_scopes: Optional required scopes
            token_verifier: Optional token verifier
            session_ttl_hours: Session TTL in hours (default: 24)
        """
        super().__init__(
            authkit_domain=authkit_domain,
            base_url=base_url,
            required_scopes=required_scopes,
            token_verifier=token_verifier,
        )
        self.session_ttl_hours = session_ttl_hours

    def get_routes(
        self,
        mcp_path: str | None = None,
        mcp_endpoint: Any | None = None,
    ) -> list[Route]:
        """Get OAuth routes with session persistence endpoints.

        Extends parent to add session-aware OAuth completion endpoint.
        """
        # Get standard routes from parent
        routes = super().get_routes(mcp_path, mcp_endpoint)

        # Add custom session-aware OAuth completion endpoint
        async def session_aware_auth_complete(request):
            """Handle OAuth completion with session creation."""
            try:
                from supabase_client import get_supabase
                from auth.session_manager import create_session_manager

                # Get request data
                try:
                    data = await request.json()
                except Exception as e:
                    logger.error(f"Failed to parse request body: {e}")
                    resp = JSONResponse(
                        {"error": "Invalid request body", "details": str(e)},
                        status_code=400
                    )
                    resp.headers["Access-Control-Allow-Origin"] = "*"
                    return resp

                external_auth_id = data.get("external_auth_id")
                logger.info(f"🔧 OAuth complete: external_auth_id={external_auth_id}")
                print(f"🔧 OAuth complete: external_auth_id={external_auth_id}")

                if not external_auth_id:
                    logger.error("❌ Missing external_auth_id in request")
                    print("❌ Missing external_auth_id in request")
                    resp = JSONResponse(
                        {"error": "external_auth_id required"},
                        status_code=400
                    )
                    resp.headers["Access-Control-Allow-Origin"] = "*"
                    return resp

                # Get Supabase JWT from Authorization header
                auth_header = request.headers.get("authorization", "")
                logger.info(f"🔧 Auth header present: {bool(auth_header)}")
                print(f"🔧 Auth header present: {bool(auth_header)}")
                if not auth_header.startswith("Bearer "):
                    logger.error("Missing Bearer token in Authorization header")
                    resp = JSONResponse(
                        {"error": "Authorization header required"},
                        status_code=401
                    )
                    resp.headers["Access-Control-Allow-Origin"] = "*"
                    return resp

                bearer_token = auth_header.split(" ", 1)[1].strip()

                # Verify with Supabase
                import os
                supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL", "").strip().rstrip("/")
                supabase_key = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY", "").strip()

                if not supabase_url or not supabase_key:
                    logger.error("Supabase env vars not configured")
                    resp = JSONResponse(
                        {"error": "Supabase not configured"},
                        status_code=500
                    )
                    resp.headers["Access-Control-Allow-Origin"] = "*"
                    return resp

                session = _get_http_session()
                async with session.get(
                        f"{supabase_url}/auth/v1/user",
                        headers={
                            "Authorization": f"Bearer {bearer_token}",
                            "apikey": supabase_key
                        },
                    ) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            logger.error(f"Supabase verification failed ({resp.status}): {error_text}")
                            json_resp = JSONResponse(
                                {"error": "Invalid Supabase token", "details": error_text},
                                status_code=401
                            )
                            json_resp.headers["Access-Control-Allow-Origin"] = "*"
                            return json_resp
                        user = await resp.json()

                # Complete OAuth with WorkOS
                workos_url = os.getenv("WORKOS_API_URL", "https://api.workos.com").strip().rstrip("/")
                workos_key = os.getenv("WORKOS_API_KEY", "").strip()

                if not workos_key:
                    logger.error("WORKOS_API_KEY not configured")
                    resp = JSONResponse(
                        {"error": "WorkOS not configured"},
                        status_code=500
                    )
                    resp.headers["Access-Control-Allow-Origin"] = "*"
                    return resp

                logger.info(f"Completing WorkOS OAuth for user {user.get('email')}")

                complete_url = f"{workos_url}/authkit/oauth2/complete"
                payload = {
                    "external_auth_id": external_auth_id,
                    "user": {"id": user["id"], "email": user["email"]},
                }

                session = _get_http_session()
                async with session.post(
                        complete_url,
                        json=payload,
                        headers={
                            "Authorization": f"Bearer {workos_key}",
                            "Content-Type": "application/json"
                        },
                    ) as resp:
                        if resp.status >= 400:
                            text = await resp.text()
                            logger.error(f"WorkOS completion failed ({resp.status}): {text}")
                            json_resp = JSONResponse(
                                {"error": "WorkOS failed", "status": resp.status, "body": text},
                                status_code=400
                            )
                            json_resp.headers["Access-Control-Allow-Origin"] = "*"
                            return json_resp
                        result = await resp.json()

                # AuthKit manages sessions via JWT - no need for mcp_sessions table
                logger.info(f"✅ OAuth complete for user {user['id']}, JWT issued by Supabase")
                print(f"✅ OAuth complete for user {user['id']}, JWT issued by Supabase")

                # Get the redirect URI from WorkOS result
                redirect_uri = result.get("redirect_uri")

                if redirect_uri:
                    # Redirect to client's callback URL to complete OAuth flow
                    from starlette.responses import RedirectResponse

                    logger.info(f"🔄 Redirecting to client callback: {redirect_uri}")

                    redirect_resp = RedirectResponse(url=redirect_uri, status_code=302)
                    redirect_resp.headers["Access-Control-Allow-Origin"] = "*"
                    return redirect_resp
                else:
                    # Fallback: return JSON for non-standard OAuth flows
                    json_resp = JSONResponse({
                        "success": True,
                        "user_id": user["id"],
                        "redirect_uri": result.get("redirect_uri")
                    })
                    json_resp.headers["Access-Control-Allow-Origin"] = "*"
                    return json_resp

            except Exception as e:
                import sys
                import traceback
                error_msg = f"OAuth completion failed: {e}"
                stack_trace = traceback.format_exc()

                # Write to stderr for Vercel to capture
                print(f"❌ OAuth ERROR: {error_msg}", file=sys.stderr)
                print(stack_trace, file=sys.stderr)

                logger.error(error_msg)
                logger.error(stack_trace)

                resp = JSONResponse({
                    "error": "OAuth completion failed",
                    "details": str(e),
                    "type": type(e).__name__,
                    "traceback": stack_trace
                }, status_code=500)
                resp.headers["Access-Control-Allow-Origin"] = "*"
                return resp

        except Exception as e:
            logger.error(f"Unhandled exception in /auth/complete: {e}")
            import traceback
            logger.error(traceback.format_exc())
            resp = JSONResponse({
                "error": "Internal server error",
                "details": str(e),
                "type": type(e).__name__
            }, status_code=500)
            resp.headers["Access-Control-Allow-Origin"] = "*"
            return resp

        # Handle OPTIONS for CORS
        async def auth_complete_options(request):
            resp = JSONResponse({}, status_code=204)
            resp.headers["Access-Control-Allow-Origin"] = "*"
            resp.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
            resp.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
            return resp

        # Add the session-aware auth complete routes
        routes.append(
            Route(
                "/auth/complete",
                endpoint=session_aware_auth_complete,
                methods=["POST"]
            )
        )
        routes.append(
            Route(
                "/auth/complete",
                endpoint=auth_complete_options,
                methods=["OPTIONS"]
            )
        )

        # Also add at /api/mcp/auth/complete for Vercel-style routing
        routes.append(
            Route(
                "/api/mcp/auth/complete",
                endpoint=session_aware_auth_complete,
                methods=["POST"]
            )
        )
        routes.append(
            Route(
                "/api/mcp/auth/complete",
                endpoint=auth_complete_options,
                methods=["OPTIONS"]
            )
        )

        return routes
