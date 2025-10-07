"""Persistent AuthKit Provider with AuthKit JWT session management.

Uses AuthKit's built-in session management via JWTs.
No separate session persistence needed.
"""

from __future__ import annotations

import logging
from typing import Any, Optional
import aiohttp
from fastmcp.server.auth.providers.workos import AuthKitProvider
from starlette.responses import JSONResponse, RedirectResponse
from starlette.routing import Route

logger = logging.getLogger(__name__)


# Vercel serverless: create fresh session per request to avoid event loop issues
# No global session - each request gets its own lifecycle
def _create_http_session() -> aiohttp.ClientSession:
    """Create fresh aiohttp session for this request (Vercel-safe pattern).

    Vercel serverless functions have ephemeral event loops.
    Creating a new session per request prevents:
    - Event loop closed errors
    - Connection pool exhaustion
    - Stale connection reuse across cold starts
    """
    connector = aiohttp.TCPConnector(
        limit=10,  # Lower limit for serverless (short-lived)
        limit_per_host=5,
        ttl_dns_cache=60,  # Shorter TTL for serverless
        force_close=True  # Clean closure for serverless
    )
    timeout = aiohttp.ClientTimeout(total=30, connect=10)
    return aiohttp.ClientSession(
        connector=connector,
        timeout=timeout,
        raise_for_status=False  # Manual status checking
    )


class PersistentAuthKitProvider(AuthKitProvider):
    """AuthKit provider that uses JWT-based session management.

    Sessions are managed entirely by AuthKit/WorkOS via JWTs.
    No separate session table needed.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_routes(self, mcp_path: str, mcp_endpoint) -> list[Route]:
        """Get auth routes with custom OAuth completion handler."""
        # Get standard routes from parent
        routes = super().get_routes(mcp_path, mcp_endpoint)

        # Add custom OAuth completion endpoint
        async def session_aware_auth_complete(request):
            """Handle OAuth completion and redirect to client.

            Vercel-optimized: Creates fresh aiohttp session per request
            to avoid event loop closure issues in serverless environments.
            """
            # Create fresh session for this request (Vercel serverless pattern)
            session = _create_http_session()

            try:
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

                if not external_auth_id:
                    logger.error("❌ Missing external_auth_id in request")
                    resp = JSONResponse(
                        {"error": "external_auth_id required"},
                        status_code=400
                    )
                    resp.headers["Access-Control-Allow-Origin"] = "*"
                    return resp

                # Get Supabase JWT from Authorization header
                auth_header = request.headers.get("authorization", "")
                if not auth_header.startswith("Bearer "):
                    logger.error("Missing Bearer token in Authorization header")
                    resp = JSONResponse(
                        {"error": "Authorization header required"},
                        status_code=401
                    )
                    resp.headers["Access-Control-Allow-Origin"] = "*"
                    return resp

                bearer_token = auth_header.split(" ", 1)[1].strip()

                # Verify with Supabase to get user info
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

                # Verify with Supabase (using fresh session)
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

                # OAuth complete - redirect browser to client callback
                logger.info(f"✅ OAuth complete for user {user['id']}")

                redirect_uri = result.get("redirect_uri")
                if redirect_uri:
                    logger.info(f"🔄 Redirecting to client callback: {redirect_uri}")
                    # IMPORTANT: Must use 302 redirect to send browser back to client's callback
                    redirect_resp = RedirectResponse(url=redirect_uri, status_code=302)
                    redirect_resp.headers["Access-Control-Allow-Origin"] = "*"
                    return redirect_resp
                else:
                    # Fallback if no redirect_uri
                    json_resp = JSONResponse({
                        "success": True,
                        "message": "OAuth complete but no redirect_uri",
                        "user_id": user["id"]
                    })
                    json_resp.headers["Access-Control-Allow-Origin"] = "*"
                    return json_resp
                else:
                    # Fallback: return JSON
                    json_resp = JSONResponse({
                        "success": True,
                        "user_id": user["id"]
                    })
                    json_resp.headers["Access-Control-Allow-Origin"] = "*"
                    return json_resp

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
            finally:
                # Always close session to prevent event loop issues (Vercel serverless)
                if session and not session.closed:
                    await session.close()

        # Handle OPTIONS for CORS
        async def auth_complete_options(request):
            resp = JSONResponse({}, status_code=204)
            resp.headers["Access-Control-Allow-Origin"] = "*"
            resp.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
            resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            return resp

        # Add Standalone Connect endpoints at ROOT path (not under mcp_path)
        # AuthKit calls these directly from browser redirect
        routes.extend([
            Route("/auth/complete", session_aware_auth_complete, methods=["POST"]),
            Route("/auth/complete", auth_complete_options, methods=["OPTIONS"]),
            # Also add under mcp_path for backward compatibility
            Route(f"{mcp_path}/auth/complete", session_aware_auth_complete, methods=["POST"]),
            Route(f"{mcp_path}/auth/complete", auth_complete_options, methods=["OPTIONS"]),
        ])

        return routes
