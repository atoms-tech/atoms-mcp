"""AuthKit Provider for Standalone Connect with Supabase.

Supabase is configured to accept AuthKit tokens via third-party auth.
The pending_authentication_token from AuthKit contains the authenticated user.
"""

from __future__ import annotations

import os

import aiohttp
from fastmcp.server.auth.providers.workos import AuthKitProvider
from mcp_qa.utils import MetricsCollector, decode_jwt
from starlette.responses import JSONResponse, RedirectResponse
from starlette.routing import Route

from utils.logging_setup import get_logger

logger = get_logger(__name__)
metrics = MetricsCollector()


def _create_http_session() -> aiohttp.ClientSession:
    """Create fresh aiohttp session."""
    connector = aiohttp.TCPConnector(limit=100, limit_per_host=30, ttl_dns_cache=300)
    return aiohttp.ClientSession(connector=connector)


class PersistentAuthKitProvider(AuthKitProvider):
    """AuthKit provider for Standalone Connect with Supabase third-party auth."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_routes(self, mcp_path: str, mcp_endpoint) -> list[Route]:
        """Get auth routes with Standalone Connect completion."""
        routes = super().get_routes(mcp_path, mcp_endpoint)

        async def standalone_auth_complete(request):
            """Handle Standalone Connect OAuth completion."""
            session = _create_http_session()
            metrics.increment("auth_completion_attempts")

            try:
                with metrics.timer("auth_completion_duration"):
                    logger.info("🔧 /auth/complete called")
                logger.info(f"   Content-Type: {request.headers.get('content-type')}")

                # Parse form data from AuthKit
                try:
                    form_data = await request.form()
                    data = {k: v for k, v in form_data.items()}
                    logger.info(f"✅ Form data keys: {list(data.keys())}")
                except Exception as e:
                    logger.error(f"❌ Parse error: {e}")
                    return JSONResponse({"error": "Invalid form"}, status_code=400)

                pending_auth_token = data.get("pending_authentication_token")
                redirect_uri = data.get("redirect_uri")

                if not pending_auth_token:
                    logger.error("❌ No pending_authentication_token")
                    return JSONResponse({"error": "pending_authentication_token required"}, status_code=400)

                logger.info(f"   Token: {pending_auth_token[:20]}...")
                logger.info(f"   redirect_uri: {redirect_uri}")

                # Decode token to get user info (AuthKit encodes user in the token)
                try:
                    with metrics.timer("jwt_decode_duration"):
                        # Use consolidated JWT utils from pheno-sdk
                        decoded = decode_jwt(pending_auth_token, verify_signature=False)
                    logger.info(f"✅ Decoded token claims: {list(decoded.keys())}")

                    # Extract user from token
                    user = decoded.get("user") or decoded
                    external_auth_id = decoded.get("external_auth_id") or decoded.get("sub") or user.get("id")

                    logger.info(f"   User email: {user.get('email')}")
                    logger.info(f"   external_auth_id: {external_auth_id}")

                except Exception as e:
                    logger.error(f"❌ Failed to decode token: {e}")
                    return JSONResponse(
                        {"error": "Invalid token", "details": str(e)},
                        status_code=400
                    )

                # Complete with AuthKit
                workos_url = os.getenv("WORKOS_API_URL", "https://api.workos.com").strip().rstrip("/")
                workos_key = os.getenv("WORKOS_API_KEY", "").strip()

                if not workos_key:
                    logger.error("❌ WORKOS_API_KEY not set")
                    return JSONResponse({"error": "Not configured"}, status_code=500)

                complete_url = f"{workos_url}/authkit/oauth2/complete"
                payload = {
                    "pending_authentication_token": pending_auth_token,
                    "external_auth_id": external_auth_id,
                    "user": {
                        "id": user.get("id"),
                        "email": user.get("email")
                    }
                }

                logger.info("📡 Calling AuthKit complete...")

                async with session.post(
                    complete_url,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {workos_key}",
                        "Content-Type": "application/json"
                    }
                ) as resp:
                    text = await resp.text()
                    logger.info(f"   Status: {resp.status}")
                    logger.info(f"   Body: {text[:300]}")

                    if resp.status >= 400:
                        logger.error(f"❌ AuthKit failed: {text}")
                        return JSONResponse(
                            {"error": "AuthKit completion failed", "details": text},
                            status_code=resp.status
                        )

                    result = await resp.json() if text else {}
                    logger.info("✅ Success")

                # Redirect to client callback
                final_redirect = result.get("redirect_uri") or redirect_uri

                if not final_redirect:
                    logger.error("❌ No redirect_uri")
                    return JSONResponse({"error": "No redirect_uri"}, status_code=500)

                logger.info(f"🔄 Redirecting to: {final_redirect}")
                metrics.increment("auth_completion_success")
                return RedirectResponse(url=final_redirect, status_code=302)

            except Exception as e:
                logger.error(f"❌ Exception: {e}")
                metrics.increment("auth_completion_errors")
                import traceback
                logger.error(traceback.format_exc())
                return JSONResponse(
                    {"error": "Internal error", "details": str(e)},
                    status_code=500
                )
            finally:
                await session.close()

        async def auth_complete_options(request):
            """CORS OPTIONS handler."""
            resp = JSONResponse({}, status_code=204)
            resp.headers["Access-Control-Allow-Origin"] = "*"
            resp.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
            resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
            return resp

        routes.extend([
            Route("/auth/complete", standalone_auth_complete, methods=["POST"]),
            Route("/auth/complete", auth_complete_options, methods=["OPTIONS"]),
        ])

        return routes
