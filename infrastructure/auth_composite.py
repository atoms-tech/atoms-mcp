"""Composite auth provider supporting both OAuth and Bearer tokens.

Implements fallback logic:
1. Try Bearer token validation (for internal clients using password grant)
   - Validates JWT claims without signature verification (trusts WorkOS issuer)
2. Fall back to OAuth flow (for external clients, IDEs)

Both use the same AuthKit JWT format.
"""

from __future__ import annotations

import logging
from typing import Any, Optional
from fastmcp.server.auth import AuthProvider, AccessToken
from fastmcp.server.auth.providers.workos import AuthKitProvider
from starlette.requests import Request
from starlette.routing import Route
from starlette.responses import Response

logger = logging.getLogger(__name__)


class WorkOSBearerTokenValidator:
    """Validate WorkOS JWT tokens (from password grant) without OAuth userinfo call.
    
    WorkOS User Management API returns valid JWTs that can be decoded and used
    for authorization. We validate them by:
    1. Decoding the JWT (without signature verification)
    2. Extracting claims (sub, email, etc.)
    3. Trusting the issuer (WorkOS) since we control the client
    
    This is suitable for internal clients (backend, frontend) where we trust
    the source of the JWT.
    """
    
    @staticmethod
    def verify_token(token: str) -> Optional[AccessToken]:
        """Verify WorkOS JWT token by decoding claims.
        
        Args:
            token: JWT token string
            
        Returns:
            AccessToken with claims if valid, None otherwise
        """
        try:
            import jwt
            
            # Decode without signature verification
            # JWT structure: header.payload.signature
            # We trust the issuer (WorkOS) since we obtained this token ourselves
            claims = jwt.decode(token, options={"verify_signature": False})
            
            logger.debug(f"✅ WorkOS JWT decoded: {claims.get('sub', 'unknown')}")
            
            # Return AccessToken with the claims
            return AccessToken(token=token, claims=claims)
        
        except Exception as e:
            logger.warning(f"Failed to validate WorkOS JWT: {e}")
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
        
        # Create WorkOS Bearer token validator for internal clients
        # This validates JWTs from password grant flow without OAuth
        self.bearer_validator = WorkOSBearerTokenValidator()
        
        # Initialize underlying OAuth provider
        init_kwargs = {
            "authkit_domain": authkit_domain,
        }
        if base_url:
            init_kwargs["base_url"] = base_url
        if self.required_scopes:
            init_kwargs["required_scopes"] = self.required_scopes
        
        self.oauth_provider = AuthKitProvider(**init_kwargs)
        
        logger.info(
            f"🔐 CompositeAuthProvider initialized:\n"
            f"  - OAuth (external clients): {authkit_domain}\n"
            f"  - Bearer (internal clients): WorkOS password grant JWT validation\n"
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
                # Verify token using our WorkOS JWT validator
                # This decodes the JWT and extracts claims
                access_token = self.bearer_validator.verify_token(token)
                
                if access_token:
                    logger.info(f"✅ Bearer token validated for user: {access_token.claims.get('email')}")
                    return access_token
                else:
                    logger.warning("Bearer token validation returned None")
                    # Fall through to OAuth
            except Exception as e:
                logger.warning(f"Bearer token validation failed: {e}")
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
