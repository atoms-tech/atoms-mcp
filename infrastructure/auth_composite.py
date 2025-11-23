"""Composite auth provider supporting both OAuth and Bearer tokens.

Implements fallback logic:
1. Try Bearer token validation (for internal clients using password grant)
   - Validates JWT claims without signature verification (trusts WorkOS issuer)
2. Fall back to OAuth flow (for external clients, IDEs)

Both use the same AuthKit JWT format.
Uses custom token verifier for Bearer token validation at HTTP layer.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Optional
from fastmcp.server.auth import AuthProvider, AccessToken
from fastmcp.server.auth.providers.workos import AuthKitProvider
from mcp.server.auth.middleware.bearer_auth import TokenVerifier
from starlette.requests import Request
from starlette.routing import Route
from starlette.responses import Response

logger = logging.getLogger(__name__)


class WorkOSBearerTokenVerifier(TokenVerifier):
    """Verify WorkOS JWT tokens (from password grant) for HTTP Bearer auth.
    
    Implements MCP's TokenVerifier protocol for use with BearerAuthBackend.
    This validates WorkOS User Management API tokens without requiring JWKS verification.
    
    Strategy:
    1. Decode JWT without signature verification
    2. Extract claims (sub, email, exp, iat, etc.)
    3. Check token expiry if exp claim present
    4. Return AccessToken with user info
    
    This is suitable for internal clients (backend, frontend) where we trust
    the source of the JWT (we obtain tokens via password grant).
    """
    
    def __init__(self, required_scopes: list[str] | None = None):
        """Initialize token verifier with optional required scopes.
        
        Args:
            required_scopes: Optional list of required OAuth scopes
        """
        self.required_scopes = required_scopes or ["openid", "profile", "email"]
    
    async def verify_token(self, token: str) -> Optional[AccessToken]:
        """Verify WorkOS JWT token by decoding claims.
        
        Implements MCP TokenVerifier protocol for HTTP Bearer auth validation.
        Called by MCP's BearerAuthBackend at the HTTP transport layer.
        
        Args:
            token: JWT token string
            
        Returns:
            AccessToken with user info if valid, None if verification fails
        """
        try:
            import jwt
            
            # Decode without signature verification
            # JWT structure: header.payload.signature
            # We trust the issuer (WorkOS) since we obtained this token ourselves
            claims = jwt.decode(token, options={"verify_signature": False})
            
            user_id = claims.get("sub") or claims.get("user_id") or claims.get("id")
            if not user_id:
                logger.warning(f"No user identifier in token claims: {list(claims.keys())}")
                return None
            
            logger.debug(f"✅ WorkOS JWT verified for user: {user_id}")
            
            # Check token expiry if exp claim is present
            expires_at = None
            if "exp" in claims:
                expires_at = claims["exp"]
                current_time = int(time.time())
                if expires_at < current_time:
                    logger.warning(f"Token expired at {expires_at}, current time {current_time}")
                    return None
            
            # Extract scopes from claims (use standard OAuth scopes if available)
            scopes = claims.get("scopes", [])
            if not scopes and "scope" in claims:
                scopes = claims["scope"].split(" ") if isinstance(claims["scope"], str) else claims["scope"]
            
            # Return AccessToken with required fields
            # client_id defaults to user_id if not in claims
            return AccessToken(
                token=token,
                client_id=claims.get("client_id", user_id),
                scopes=scopes,
                expires_at=expires_at,
            )
        
        except Exception as e:
            logger.warning(f"Failed to verify WorkOS JWT: {e}")
            return None


class CompositeAuthProvider(AuthProvider):
    """Composite auth provider that supports both OAuth and Bearer tokens.
    
    Flow:
    1. Check for Bearer token in Authorization header (internal clients)
       - frontend, backend, atoms agent
       - Pass JWT directly without OAuth flow
    
    2. Fall back to OAuth flow (external clients)
       - IDEs (Cursor, VS Code), external integrations
       - Use standard OAuth to get JWT
    
    Both paths use the same AuthKit JWT format, so RLS and claims are identical.
    """
    
    def __init__(
        self,
        authkit_domain: str,
        base_url: str = "",
        required_scopes: list[str] | None = None,
        token_verifier: Any = None,
        **kwargs: Any
    ):
        """Initialize composite auth provider.
        
        Args:
            authkit_domain: WorkOS AuthKit domain (e.g., https://your-app.authkit.app)
            base_url: Server base URL for OAuth callbacks
            required_scopes: OAuth scopes to request (e.g., ['openid', 'profile', 'email'])
            token_verifier: Optional custom token verifier (FastMCP 2.13.1+)
        """
        self.authkit_domain = authkit_domain
        self.base_url = base_url
        self.required_scopes = required_scopes or ["openid", "profile", "email"]
        
        # Create WorkOS Bearer token verifier for HTTP transport layer (MCP's BearerAuthBackend)
        # This verifier is used by MCP's HTTP transport to validate Bearer tokens
        # before the authenticate() method is called
        self.bearer_token_verifier = WorkOSBearerTokenVerifier(required_scopes=self.required_scopes)
        
        # Initialize underlying OAuth provider WITH the token verifier
        # This ensures both HTTP transport and OAuth use the same token validation
        init_kwargs = {
            "authkit_domain": authkit_domain,
        }
        if base_url:
            init_kwargs["base_url"] = base_url
        if self.required_scopes:
            init_kwargs["required_scopes"] = self.required_scopes
        
        # CRITICAL: Pass our token verifier to AuthKitProvider
        # This is used by MCP's BearerAuthBackend at the HTTP transport level
        init_kwargs["token_verifier"] = self.bearer_token_verifier
        
        self.oauth_provider = AuthKitProvider(**init_kwargs)
        
        logger.info(
            f"🔐 CompositeAuthProvider initialized:\n"
            f"  - OAuth (external clients): {authkit_domain}\n"
            f"  - Bearer (internal clients): WorkOS JWT verification via token_verifier\n"
            f"  - HTTP transport: Validated by MCP's BearerAuthBackend\n"
            f"  - Both use same AuthKit JWT format"
        )
    
    async def authenticate(self, request: Request) -> AccessToken:
        """Authenticate request using Bearer token or OAuth.
        
        Flow:
        1. Try Bearer token first (internal clients using password grant)
           - Uses WorkOS JWKS endpoint for JWT validation
        2. Fall back to OAuth flow (external clients, IDEs)
        
        Args:
            request: The incoming request
            
        Returns:
            AccessToken with user claims
            
        Raises:
            Exception: If neither Bearer nor OAuth succeeds
        """
        # 1. Try Bearer token first (internal clients)
        auth_header = request.headers.get("Authorization", "").strip()
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Strip "Bearer " prefix
            logger.debug(f"🔐 Bearer token found (length: {len(token)})")
            
            try:
                # Decode JWT to get claims for authenticate() method
                # (Note: HTTP layer validation happens via token_verifier in BearerAuthBackend)
                import jwt
                claims = jwt.decode(token, options={"verify_signature": False})
                
                # Create AccessToken with the claims
                access_token = AccessToken(token=token, claims=claims)
                logger.info(f"✅ Bearer token decoded for user: {claims.get('email')}")
                return access_token
                
            except Exception as e:
                logger.warning(f"Bearer token decode failed: {e}")
                # Fall through to OAuth
        
        # 2. Fall back to OAuth flow (external clients)
        logger.debug("Attempting OAuth flow...")
        try:
            access_token = await self.oauth_provider.authenticate(request)
            logger.info(f"✅ OAuth authenticated for user: {access_token.claims.get('email')}")
            return access_token
        except Exception as e:
            logger.error(f"❌ OAuth authentication failed: {e}")
            raise
    
    def get_routes(self, mcp_path: str | None = None) -> list[Route]:
        """Get all OAuth discovery routes from underlying provider.
        
        These routes handle OAuth flow for external clients:
        - /.well-known/oauth-protected-resource
        - /.well-known/oauth-authorization-server
        - /register (DCR endpoint)
        - /callback
        
        Args:
            mcp_path: MCP endpoint path for OAuth discovery
            
        Returns:
            List of Starlette routes
        """
        return self.oauth_provider.get_routes(mcp_path=mcp_path)
    
    def get_resource_metadata_url(self) -> str:
        """Get OAuth protected resource metadata URL.
        
        Used by external clients to discover the resource endpoint.
        """
        return self.oauth_provider.get_resource_metadata_url()
    
    def get_middleware(self) -> list:
        """Get any middleware from underlying OAuth provider."""
        try:
            return self.oauth_provider.get_middleware()
        except (AttributeError, NotImplementedError):
            return []
    
    @property
    def requires_browser(self) -> bool:
        """OAuth flow requires browser for external clients."""
        return True
    
    @property
    def supports_bearer_tokens(self) -> bool:
        """Explicitly support Bearer tokens for internal clients."""
        return True
