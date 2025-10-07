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
                # Log request details for debugging
                logger.info(f"🔧 /auth/complete called")
                logger.info(f"   Method: {request.method}")
                logger.info(f"   Content-Type: {request.headers.get('content-type')}")
                logger.info(f"   Headers: {dict(request.headers)}")

                # Get request data - try both form and JSON
                data = {}

                # Try form data first (browser POST from AuthKit)
                try:
                    form_data = await request.form()
                    data = {k: v for k, v in form_data.items()}
                    if data:
                        logger.info(f"✅ Parsed form data: {list(data.keys())}")
                except Exception as form_error:
                    logger.info(f"   No form data: {form_error}")

                # Try JSON if no form data
                if not data:
                    try:
                        data = await request.json()
                        logger.info(f"✅ Parsed JSON data: {list(data.keys())}")
                    except Exception as json_error:
                        logger.info(f"   No JSON data: {json_error}")

                # Try query params as last resort
                if not data:
                    data = {k: v for k, v in request.query_params.items()}
                    if data:
                        logger.info(f"✅ Got data from query params: {list(data.keys())}")

                if not data:
                    logger.error(f"❌ No data in request (form, JSON, or query params)")
                    resp = JSONResponse(
                        {"error": "No data provided", "details": "Expected external_auth_id in form, JSON, or query params"},
                        status_code=400
                    )
                    resp.headers["Access-Control-Allow-Origin"] = "*"
                    return resp

                # Extract pending_authentication_token (from AuthKit Allow form)
                pending_auth_token = data.get("pending_authentication_token")
                authorization_session_id = data.get("authorization_session_id")
                redirect_uri = data.get("redirect_uri")
                state = data.get("state")
                client_id = data.get("client_id")

                logger.info(f"🔧 OAuth approval data:")
                logger.info(f"   pending_authentication_token: {pending_auth_token[:20] if pending_auth_token else None}...")
                logger.info(f"   authorization_session_id: {authorization_session_id}")
                logger.info(f"   redirect_uri: {redirect_uri}")
                logger.info(f"   state: {state}")
                logger.info(f"   client_id: {client_id}")

                if not pending_auth_token or not authorization_session_id:
                    logger.error("❌ Missing required fields from AuthKit")
                    resp = JSONResponse(
                        {"error": "Missing required fields", "details": "Need pending_authentication_token and authorization_session_id"},
                        status_code=400
                    )
                    resp.headers["Access-Control-Allow-Origin"] = "*"
                    return resp

                # Complete OAuth with WorkOS using pending_authentication_token
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

                logger.info(f"Completing WorkOS OAuth with pending_authentication_token")

                # Use WorkOS complete endpoint with pending_authentication_token
                complete_url = f"{workos_url}/user_management/authenticate"
                payload = {
                    "pending_authentication_token": pending_auth_token,
                    "grant_type": "urn:workos:oauth:grant-type:organization-selection"
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

                # OAuth complete - extract user and redirect to client
                user_data = result.get("user", {})
                logger.info(f"✅ OAuth complete for user {user_data.get('email')}")
                logger.info(f"   WorkOS result: {list(result.keys())}")

                # Get redirect_uri from form data or WorkOS result
                final_redirect_uri = redirect_uri or result.get("redirect_uri")

                if final_redirect_uri:
                    logger.info(f"🔄 Redirecting to client callback: {final_redirect_uri}")
                    # IMPORTANT: Must use 302 redirect to send browser back to client's callback
                    redirect_resp = RedirectResponse(url=final_redirect_uri, status_code=302)
                    redirect_resp.headers["Access-Control-Allow-Origin"] = "*"
                    return redirect_resp
                else:
                    # Fallback if no redirect_uri
                    logger.warning("No redirect_uri available")
                    json_resp = JSONResponse({
                        "success": True,
                        "message": "OAuth complete but no redirect_uri",
                        "user": user_data
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
