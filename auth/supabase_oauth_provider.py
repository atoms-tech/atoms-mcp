"""Supabase OAuth 2.1 proxy provider for FastMCP.

Provides OAuth 2.1 compliant endpoints that bridge FastMCP clients with Supabase authentication.
"""

from __future__ import annotations

import logging
import os
import secrets
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx
from starlette.datastructures import URL
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, Response

try:
    # Try relative import first (when running as module)
    from ..supabase_client import get_supabase, MissingSupabaseConfig
except ImportError:
    # Fall back to absolute import (when running directly)
    from supabase_client import get_supabase, MissingSupabaseConfig

logger = logging.getLogger(__name__)


@dataclass
class AuthorizationEntry:
    """Stores authorization code metadata for token exchange."""
    code: str
    redirect_uri: str
    state: Optional[str]
    created_at: float
    access_token: str
    refresh_token: Optional[str]
    expires_in: int
    token_type: str
    user_id: str
    user_email: Optional[str]


class SupabaseOAuthProvider:
    """OAuth 2.1 proxy that bridges FastMCP clients with Supabase authentication."""

    def __init__(self, *, base_url: str, client_id: Optional[str] = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.client_id = client_id or os.getenv("ATOMS_OAUTH_CLIENT_ID", "atoms-mcp-client")
        self._auth_codes: Dict[str, AuthorizationEntry] = {}

        try:
            self._supabase = get_supabase()
        except MissingSupabaseConfig:
            logger.warning("Supabase not configured - OAuth provider disabled")
            self._supabase = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def is_enabled(self) -> bool:
        return self._supabase is not None

    def setup_routes(self, server: FastMCP) -> None:  # type: ignore[name-defined]
        """Register OAuth endpoints on the FastMCP server."""
        if not self.is_enabled():
            return

        @server.custom_route("/.well-known/oauth-authorization-server", methods=["GET"])  # type: ignore[attr-defined]
        async def discovery_endpoint(_request: Request) -> Response:
            return JSONResponse(self._discovery_document())

        @server.custom_route("/.well-known/jwks.json", methods=["GET"])  # type: ignore[attr-defined]
        async def jwks_endpoint(_request: Request) -> Response:
            return JSONResponse(self._get_jwks())

        @server.custom_route("/auth/authorize", methods=["GET", "POST"])  # type: ignore[attr-defined]
        async def authorize_endpoint(request: Request) -> Response:
            if request.method == "GET":
                return JSONResponse({
                    "error": "authorization_endpoint",
                    "error_description": "This endpoint requires POST with credentials"
                }, status_code=400)
            return await self._handle_login_submission(request)

        @server.custom_route("/auth/token", methods=["POST"])  # type: ignore[attr-defined]
        async def token_endpoint(request: Request) -> Response:
            return await self._handle_token_exchange(request)

        @server.custom_route("/auth/callback", methods=["GET"])  # type: ignore[attr-defined]
        async def callback_endpoint(request: Request) -> Response:
            return await self._handle_oauth_callback(request)

    # ------------------------------------------------------------------
    # Core OAuth functionality
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Endpoint helpers
    # ------------------------------------------------------------------
    def _discovery_document(self) -> Dict[str, Any]:
        return {
            "issuer": self.base_url,
            "authorization_endpoint": f"{self.base_url}/auth/authorize",
            "token_endpoint": f"{self.base_url}/auth/token",
            "jwks_uri": f"{self.base_url}/.well-known/jwks.json",
            "grant_types_supported": ["authorization_code"],
            "response_types_supported": ["code"],
            "scopes_supported": ["openid", "profile", "email"],
        }


    async def _handle_login_submission(self, request: Request) -> Response:
        form = await request.form()
        email = (form.get("email") or "").strip()
        password = form.get("password")
        redirect_uri = form.get("redirect_uri")
        state = form.get("state") or None

        if not email or not password or not redirect_uri:
            return self._login_error("Missing required fields", request)

        if not self._supabase:
            return self._login_error("Supabase not configured", request)

        try:
            auth_res = self._supabase.auth.sign_in_with_password({
                "email": email,
                "password": password,
            })
            session = getattr(auth_res, "session", None)
            if not session or not getattr(session, "access_token", None):
                raise ValueError("Invalid Supabase response")

            code = secrets.token_urlsafe(32)
            entry = AuthorizationEntry(
                code=code,
                redirect_uri=redirect_uri,
                state=state,
                created_at=time.time(),
                access_token=session.access_token,
                refresh_token=getattr(session, "refresh_token", None),
                expires_in=int(getattr(session, "expires_in", 3600) or 3600),
                token_type=getattr(session, "token_type", "bearer"),
                user_id=getattr(session.user, "id", email),
                user_email=email,
            )
            self._auth_codes[code] = entry

            redirect_url = self._build_redirect_url(redirect_uri, code=code, state=state)
            return RedirectResponse(url=str(redirect_url), status_code=302)

        except Exception as exc:
            logger.warning("Supabase login failed: %s", exc)
            return self._login_error("Invalid credentials", request)

    async def _handle_token_exchange(self, request: Request) -> Response:
        form = await request.form()
        if form.get("grant_type") != "authorization_code":
            return JSONResponse({"error": "unsupported_grant_type"}, status_code=400)

        code = form.get("code")
        redirect_uri = form.get("redirect_uri")
        client_id = form.get("client_id")

        entry = self._auth_codes.get(code, None)
        if not entry:
            return JSONResponse({"error": "invalid_grant", "error_description": "Unknown authorization code"}, status_code=400)

        if entry.redirect_uri and redirect_uri and entry.redirect_uri != redirect_uri:
            return JSONResponse({"error": "invalid_grant", "error_description": "redirect_uri mismatch"}, status_code=400)

        if client_id and client_id != self.client_id:
            return JSONResponse({"error": "unauthorized_client"}, status_code=400)

        # Consume the code
        self._auth_codes.pop(code, None)

        return JSONResponse({
            "access_token": entry.access_token,
            "token_type": entry.token_type or "bearer",
            "expires_in": entry.expires_in,
            "refresh_token": entry.refresh_token,
            "scope": "openid profile email",
            "user": {
                "id": entry.user_id,
                "email": entry.user_email,
            }
        })

    async def _handle_oauth_callback(self, request: Request) -> Response:
        """Handle OAuth callback and automatically exchange code for token"""
        params = request.query_params
        code = params.get("code")
        state = params.get("state")
        error = params.get("error")
        
        if error:
            return JSONResponse({
                "error": "oauth_error",
                "error_description": f"OAuth Error: {error}"
            }, status_code=400)
            
        if not code:
            return JSONResponse({
                "error": "missing_code",
                "error_description": "No authorization code received"
            }, status_code=400)
            
        # Exchange code for token
        try:
            token_data = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": f"{self.base_url}/auth/callback",
                "client_id": self.client_id
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/auth/token",
                    data=token_data,
                    timeout=10
                )
                
            if response.status_code == 200:
                token_response = response.json()
                return JSONResponse({
                    "success": True,
                    "message": "OAuth flow completed successfully",
                    "code": code,
                    "state": state,
                    "token_response": token_response
                })
            else:
                return JSONResponse({
                    "error": "token_exchange_failed",
                    "error_description": f"Token exchange failed: {response.text}"
                }, status_code=400)
                
        except Exception as e:
            return JSONResponse({
                "error": "token_exchange_error",
                "error_description": f"Token exchange error: {e}"
            }, status_code=500)



    def _build_redirect_url(self, redirect_uri: str, *, code: str, state: Optional[str]) -> URL:
        """Build redirect URL with authorization code"""
        url = URL(redirect_uri)
        base_url = f"{url.scheme}://{url.netloc}{url.path}"
        
        query_params = []
        if url.query:
            query_params.append(url.query)
        query_params.append(f"code={code}")
        if state:
            query_params.append(f"state={state}")
        
        final_url = f"{base_url}?{'&'.join(query_params)}"
        return URL(final_url)

    def _get_jwks(self) -> Dict[str, Any]:
        """Get JWKS for OAuth compliance - try real Supabase JWKS first"""
        try:
            # Try to get real Supabase JWKS
            supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
            if supabase_url:
                # Extract project ID from URL (e.g., https://ycosngzmdrjwsrtpgtyc.supabase.co)
                project_id = supabase_url.split("//")[1].split(".")[0]
                jwks_url = f"https://{project_id}.supabase.co/auth/v1/.well-known/jwks.json"
                
                logger.info(f"Fetching real JWKS from: {jwks_url}")
                
                # Fetch real JWKS synchronously (this is called from endpoint)
                import httpx
                with httpx.Client() as client:
                    response = client.get(jwks_url, timeout=10)
                    if response.status_code == 200:
                        jwks_data = response.json()
                        keys = jwks_data.get('keys', [])
                        if keys:
                            logger.info(f"Successfully fetched real Supabase JWKS with {len(keys)} keys")
                            return jwks_data
                        else:
                            logger.warning(f"Supabase JWKS returned empty keys array - asymmetric JWT signing not enabled")
                    else:
                        logger.warning(f"Supabase JWKS returned {response.status_code}: {response.text}")
        except Exception as e:
            logger.warning(f"Failed to fetch real Supabase JWKS: {e}")
        
        # Fallback to mock JWKS if real one fails
        logger.info("Using mock JWKS as fallback")
        return {
            "keys": [
                {
                    "kty": "RSA",
                    "kid": "atoms-mcp-key-1",
                    "use": "sig",
                    "alg": "RS256",
                    "n": "mock-key-for-oauth-compliance",
                    "e": "AQAB"
                }
            ]
        }


# Avoid circular import at runtime
from fastmcp import FastMCP  # noqa: E402  # type: ignore  # isort: skip


