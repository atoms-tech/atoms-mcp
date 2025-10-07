"""AuthKit Provider for Standalone Connect with Supabase.

Since Supabase has third-party auth configured to accept AuthKit tokens,
we only need AuthKit JWTs - no separate Supabase verification needed.
"""

from __future__ import annotations

import logging
import os
import aiohttp
from fastmcp.server.auth.providers.workos import AuthKitProvider
from starlette.responses import JSONResponse, RedirectResponse
from starlette.routing import Route

logger = logging.getLogger(__name__)


def _create_http_session() -> aiohttp.ClientSession:
    """Create fresh aiohttp session for this request."""
    connector = aiohttp.TCPConnector(limit=100, limit_per_host=30, ttl_dns_cache=300)
    return aiohttp.ClientSession(connector=connector)


class PersistentAuthKitProvider(AuthKitProvider):
    """AuthKit provider for Standalone Connect.

    Flow:
    1. Client → AuthKit OAuth
    2. AuthKit → Supabase login (atoms.tech)
    3. User authenticates with Supabase
    4. Browser → /auth/complete with pending_authentication_token
    5. We complete AuthKit OAuth
    6. Redirect to client callback
    7. Client gets AuthKit JWT
    8. AuthKit JWT works with Supabase (third-party auth configured)
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_routes(self, mcp_path: str, mcp_endpoint) -> list[Route]:
        """Get auth routes with Standalone Connect completion."""
        routes = super().get_routes(mcp_path, mcp_endpoint)

        async def standalone_auth_complete(request):
            """Handle Standalone Connect OAuth completion.

            Called when user clicks 'Allow' on AuthKit consent page.
            """
            session = _create_http_session()

            try:
                logger.info(f"🔧 /auth/complete called")
                logger.info(f"   Method: {request.method}")
                logger.info(f"   Content-Type: {request.headers.get('content-type')}")
                logger.info(f"   Headers: {list(request.headers.keys())}")
                logger.info(f"   Cookies: {list(request.cookies.keys())}")

                # Parse form data from AuthKit's Allow form
                data = {}
                try:
                    form_data = await request.form()
                    data = {k: v for k, v in form_data.items()}
                    logger.info(f"✅ Form data keys: {list(data.keys())}")
                except Exception as e:
                    logger.error(f"❌ Failed to parse form data: {e}")
                    return JSONResponse(
                        {"error": "Invalid form data", "details": str(e)},
                        status_code=400
                    )

                # Extract required fields
                pending_auth_token = data.get("pending_authentication_token")
                redirect_uri = data.get("redirect_uri")

                logger.info(f"   pending_authentication_token: {pending_auth_token[:20] if pending_auth_token else None}...")
                logger.info(f"   redirect_uri: {redirect_uri}")

                if not pending_auth_token:
                    logger.error("❌ Missing pending_authentication_token")
                    return JSONResponse(
                        {"error": "pending_authentication_token required"},
                        status_code=400
                    )

                # Complete AuthKit OAuth
                workos_url = os.getenv("WORKOS_API_URL", "https://api.workos.com").strip().rstrip("/")
                workos_key = os.getenv("WORKOS_API_KEY", "").strip()

                if not workos_key:
                    logger.error("❌ WORKOS_API_KEY not configured")
                    return JSONResponse({"error": "WorkOS not configured"}, status_code=500)

                # Try to decode pending_authentication_token to get user info
                logger.info(f"📡 Attempting to decode pending_authentication_token...")

                user_info = None
                external_auth_id = None

                # Try decoding as JWT
                try:
                    import jwt
                    decoded = jwt.decode(pending_auth_token, options={"verify_signature": False})
                    logger.info(f"✅ Decoded token: {list(decoded.keys())}")
                    user_info = decoded.get("user")
                    external_auth_id = decoded.get("external_auth_id") or decoded.get("sub")
                except Exception as e:
                    logger.info(f"   Token not a JWT: {e}")

                # If no user from token, try cookies
                if not user_info:
                    logger.info(f"   Checking cookies for user info...")
                    all_cookies = request.cookies
                    logger.info(f"   Available cookies: {list(all_cookies.keys())}")

                    for cookie_name, cookie_value in all_cookies.items():
                        if 'auth-token' in cookie_name or cookie_name.startswith('sb-'):
                            try:
                                import json
                                cookie_data = json.loads(cookie_value)
                                if isinstance(cookie_data, list) and len(cookie_data) > 0:
                                    user_info = cookie_data[0].get('user')
                                elif isinstance(cookie_data, dict):
                                    user_info = cookie_data.get('user')

                                if user_info:
                                    logger.info(f"✅ Found user in cookie: {cookie_name}")
                                    break
                            except:
                                continue

                # If still no user, use query params or create placeholder
                if not user_info:
                    logger.warning("⚠️  No user in token or cookies, using query params or placeholder")
                    # Check query params
                    user_email = request.query_params.get("email")
                    user_id = request.query_params.get("user_id")

                    if user_email and user_id:
                        user_info = {"id": user_id, "email": user_email}
                        external_auth_id = user_id
                        logger.info(f"✅ Got user from query params")
                    else:
                        logger.error("❌ Cannot determine user identity")
                        return JSONResponse(
                            {"error": "User identity required", "details": "No user in token, cookies, or query params"},
                            status_code=401
                        )

                # Complete AuthKit OAuth
                logger.info(f"📡 Completing AuthKit OAuth...")

                complete_url = f"{workos_url}/authkit/oauth2/complete"
                payload = {
                    "pending_authentication_token": pending_auth_token,
                    "external_auth_id": external_auth_id or user_info.get("id"),
                    "user": {
                        "id": user_info.get("id"),
                        "email": user_info.get("email"),
                        "first_name": user_info.get("user_metadata", {}).get("first_name") if user_info.get("user_metadata") else None,
                        "last_name": user_info.get("user_metadata", {}).get("last_name") if user_info.get("user_metadata") else None
                    }
                }

                logger.info(f"   Calling: {complete_url}")
                logger.info(f"   Payload keys: {list(payload.keys())}")

                async with session.post(
                    complete_url,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {workos_key}",
                        "Content-Type": "application/json"
                    }
                ) as resp:
                    response_text = await resp.text()
                    logger.info(f"   Response status: {resp.status}")
                    logger.info(f"   Response body: {response_text[:200]}")

                    if resp.status >= 400:
                        logger.error(f"❌ AuthKit completion failed ({resp.status}): {response_text}")
                        return JSONResponse(
                            {"error": "AuthKit completion failed", "status": resp.status, "details": response_text},
                            status_code=resp.status
                        )

                    result = resp.json() if response_text else {}
                    logger.info(f"✅ AuthKit completion success")
                    logger.info(f"   Result keys: {list(result.keys())}")

                # Get redirect_uri from AuthKit response or form data
                final_redirect_uri = result.get("redirect_uri") or redirect_uri

                if not final_redirect_uri:
                    logger.error("❌ No redirect_uri available")
                    return JSONResponse(
                        {"error": "No redirect_uri"},
                        status_code=500
                    )

                logger.info(f"🔄 Redirecting to client callback: {final_redirect_uri}")

                # Redirect browser to client callback with authorization code
                return RedirectResponse(url=final_redirect_uri, status_code=302)

            except Exception as e:
                logger.error(f"❌ Exception in /auth/complete: {e}")
                import traceback
                logger.error(traceback.format_exc())
                return JSONResponse(
                    {"error": "Internal server error", "details": str(e), "type": type(e).__name__},
                    status_code=500
                )
            finally:
                await session.close()

        async def auth_complete_options(request):
            """Handle OPTIONS for CORS."""
            resp = JSONResponse({}, status_code=204)
            resp.headers["Access-Control-Allow-Origin"] = "*"
            resp.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
            resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            return resp

        # Add Standalone Connect endpoints at ROOT path
        routes.extend([
            Route("/auth/complete", standalone_auth_complete, methods=["POST"]),
            Route("/auth/complete", auth_complete_options, methods=["OPTIONS"]),
        ])

        return routes
