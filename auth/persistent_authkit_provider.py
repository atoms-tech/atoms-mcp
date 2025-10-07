"""AuthKit Provider for Standalone Connect with Supabase.

Supabase is configured as a third-party auth provider to accept AuthKit tokens.
This provider handles the Standalone Connect flow: Login → Allow → Complete.
"""

from __future__ import annotations

import logging
import os
from typing import Any
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

    Handles OAuth flow with Supabase login:
    1. Client → AuthKit → Supabase login (atoms.tech)
    2. User authenticates with Supabase
    3. Supabase → AuthKit → /auth/complete (this endpoint)
    4. Complete WorkOS OAuth → redirect to client callback
    5. Client exchanges code for AuthKit token
    6. AuthKit token works with Supabase (third-party auth configured)
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_routes(self, mcp_path: str, mcp_endpoint) -> list[Route]:
        """Get auth routes with Standalone Connect completion."""
        routes = super().get_routes(mcp_path, mcp_endpoint)

        async def standalone_auth_complete(request):
            """Handle Standalone Connect OAuth completion.

            Called when user clicks 'Allow' on AuthKit consent page.
            Completes WorkOS OAuth and redirects to client callback.
            """
            session = _create_http_session()

            try:
                logger.info(f"🔧 /auth/complete called")
                logger.info(f"   Method: {request.method}")
                logger.info(f"   Content-Type: {request.headers.get('content-type')}")

                # Parse form data from AuthKit's Allow form
                data = {}
                try:
                    form_data = await request.form()
                    data = {k: v for k, v in form_data.items()}
                    logger.info(f"✅ Form data: {list(data.keys())}")
                except Exception as e:
                    logger.error(f"Failed to parse form data: {e}")
                    return JSONResponse(
                        {"error": "Invalid form data", "details": str(e)},
                        status_code=400
                    )

                # Extract AuthKit form fields
                pending_auth_token = data.get("pending_authentication_token")
                auth_session_id = data.get("authorization_session_id")
                redirect_uri = data.get("redirect_uri")
                state = data.get("state")

                logger.info(f"   pending_authentication_token: {pending_auth_token[:20] if pending_auth_token else None}...")
                logger.info(f"   authorization_session_id: {auth_session_id}")
                logger.info(f"   redirect_uri: {redirect_uri}")
                logger.info(f"   state: {state}")

                if not pending_auth_token:
                    logger.error("❌ Missing pending_authentication_token")
                    return JSONResponse(
                        {"error": "pending_authentication_token required"},
                        status_code=400
                    )

                # Complete WorkOS OAuth using pending_authentication_token
                workos_url = os.getenv("WORKOS_API_URL", "https://api.workos.com").strip().rstrip("/")
                workos_key = os.getenv("WORKOS_API_KEY", "").strip()

                if not workos_key:
                    logger.error("WORKOS_API_KEY not configured")
                    return JSONResponse({"error": "WorkOS not configured"}, status_code=500)

                logger.info(f"📡 Calling WorkOS authenticate endpoint...")

                # Call WorkOS /user_management/authenticate
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
                    }
                ) as resp:
                    if resp.status >= 400:
                        text = await resp.text()
                        logger.error(f"WorkOS authenticate failed ({resp.status}): {text}")
                        return JSONResponse(
                            {"error": "WorkOS authentication failed", "status": resp.status, "details": text},
                            status_code=resp.status
                        )

                    result = await resp.json()
                    logger.info(f"✅ WorkOS authenticate success")
                    logger.info(f"   Response keys: {list(result.keys())}")

                # Get redirect_uri from WorkOS response or form data
                final_redirect_uri = result.get("redirect_uri") or redirect_uri

                if not final_redirect_uri:
                    logger.error("❌ No redirect_uri available")
                    return JSONResponse(
                        {"error": "No redirect_uri", "details": "Neither WorkOS nor form provided redirect_uri"},
                        status_code=500
                    )

                logger.info(f"🔄 Redirecting to: {final_redirect_uri}")

                # Redirect browser to client callback
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
