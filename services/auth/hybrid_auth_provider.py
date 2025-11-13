"""Hybrid authentication provider supporting both OAuth and Bearer tokens.

This provider enables the same MCP server to handle:
1. OAuth (AuthKit) for public clients - full OAuth flow
2. Bearer tokens for internal services (atomsAgent) - static token
3. AuthKit JWTs for frontend token forwarding - validates AuthKit JWT from frontend/backend
"""

from __future__ import annotations

import logging
from typing import Optional, Dict, Any
from fastmcp.server.auth import AuthProvider
from fastmcp.server.auth.providers.workos import AuthKitProvider
from fastmcp.server.auth.providers.jwt import StaticTokenVerifier, JWTVerifier

logger = logging.getLogger(__name__)


class HybridAuthProvider(AuthProvider):
    """Hybrid auth provider supporting OAuth and Bearer tokens simultaneously."""

    def __init__(
        self,
        oauth_provider: AuthKitProvider,
        internal_token: Optional[str] = None,
        authkit_client_id: Optional[str] = None,
        authkit_jwks_uri: Optional[str] = None
    ):
        """Initialize hybrid auth provider.

        Args:
            oauth_provider: AuthKit provider for OAuth flow
            internal_token: Static token for internal services
            authkit_client_id: AuthKit client ID for JWT audience validation
            authkit_jwks_uri: AuthKit JWKS URI for JWT verification
        """
        self.oauth_provider = oauth_provider

        # Expose ALL attributes from OAuth provider for FastMCP compatibility
        # This ensures HybridAuthProvider is a drop-in replacement for AuthKitProvider
        self.base_url = oauth_provider.base_url
        self.required_scopes = getattr(oauth_provider, 'required_scopes', [])
        self.authkit_domain = getattr(oauth_provider, 'authkit_domain', None)
        self.resource_server_url = getattr(oauth_provider, 'resource_server_url', None)
        self.authorization_servers = getattr(oauth_provider, 'authorization_servers', [])

        # Setup internal token verifier
        self.internal_token_verifier = None
        if internal_token:
            self.internal_token_verifier = StaticTokenVerifier(
                tokens={
                    internal_token: {
                        "client_id": "internal-service",
                        "scopes": ["read:data", "write:data", "admin:users"]
                    }
                },
                required_scopes=["read:data"]
            )
            logger.info("✅ Internal bearer token authentication enabled")

        # Setup AuthKit JWT verifier for frontend/backend tokens
        self.authkit_jwt_verifier = None
        if authkit_jwks_uri and authkit_client_id:
            self.authkit_jwt_verifier = JWTVerifier(
                jwks_uri=authkit_jwks_uri,
                audience=authkit_client_id,
                # AuthKit issuer will be validated from JWKS
            )
            logger.info("✅ AuthKit JWT authentication enabled")
    
    async def authenticate(self, request) -> Optional[Dict[str, Any]]:
        """Authenticate request using OAuth or Bearer token.

        Flow:
        1. Check for Authorization: Bearer <token> header
        2. If present, try bearer token verification:
           a. Try internal static token (for system services)
           b. Try AuthKit JWT (from frontend/backend)
        3. If not present or verification fails, fall back to OAuth

        Args:
            request: HTTP request object

        Returns:
            Authentication context dict or None
        """
        # Check for Bearer token
        auth_header = request.headers.get("Authorization", "")

        if auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "").strip()

            # Try internal token first (for system services)
            if self.internal_token_verifier:
                try:
                    result = await self.internal_token_verifier.verify_token(token)
                    logger.info("✅ Authenticated via internal bearer token")
                    return result
                except Exception as e:
                    logger.debug(f"Internal token verification failed: {e}")

            # Try AuthKit JWT (from frontend/backend)
            if self.authkit_jwt_verifier:
                try:
                    result = await self.authkit_jwt_verifier.verify_token(token)
                    logger.info(f"✅ Authenticated via AuthKit JWT: {result.get('sub')}")
                    return result
                except Exception as e:
                    logger.debug(f"AuthKit JWT verification failed: {e}")

            # Bearer token provided but verification failed
            logger.warning("Bearer token provided but verification failed")
            return None

        # No bearer token, fall back to OAuth
        logger.debug("No bearer token, using OAuth flow")
        return await self.oauth_provider.authenticate(request)
    
    async def get_authorization_url(self, request) -> str:
        """Get OAuth authorization URL (delegates to OAuth provider)."""
        return await self.oauth_provider.get_authorization_url(request)
    
    async def handle_callback(self, request) -> Optional[Dict[str, Any]]:
        """Handle OAuth callback (delegates to OAuth provider)."""
        return await self.oauth_provider.handle_callback(request)
    
    @property
    def requires_browser(self) -> bool:
        """OAuth requires browser, but bearer tokens don't."""
        return True  # OAuth is available
    
    @property
    def supports_bearer_tokens(self) -> bool:
        """Indicate that bearer tokens are supported."""
        return self.internal_token_verifier is not None or self.authkit_jwt_verifier is not None

    def get_routes(self, mcp_path: Optional[str] = None):
        """Get OAuth discovery routes from the underlying OAuth provider.

        This is CRITICAL for MCP clients to discover OAuth endpoints.
        The HybridAuthProvider must expose the same routes as AuthKitProvider.

        Args:
            mcp_path: The MCP endpoint path (passed by FastMCP, but not used by AuthKitProvider)
        """
        # Delegate to the OAuth provider to get all OAuth discovery routes
        # Note: AuthKitProvider.get_routes() doesn't accept parameters, so we ignore mcp_path
        # FastMCP may pass mcp_path in newer versions, but AuthKitProvider doesn't use it
        return self.oauth_provider.get_routes()

    def get_resource_metadata_url(self):
        """Get the resource metadata URL from the underlying OAuth provider."""
        return self.oauth_provider.get_resource_metadata_url()

    def get_middleware(self):
        """Get middleware from the underlying OAuth provider.

        This method may be called by newer versions of FastMCP.
        If the OAuth provider doesn't have this method, return an empty list.
        """
        if hasattr(self.oauth_provider, 'get_middleware'):
            return self.oauth_provider.get_middleware()
        return []

    def _get_resource_url(self, mcp_path: str):
        """Get the resource URL for the given MCP path.

        This method may be called by newer versions of FastMCP.
        Delegate to the OAuth provider if it has this method.
        """
        if hasattr(self.oauth_provider, '_get_resource_url'):
            return self.oauth_provider._get_resource_url(mcp_path)
        # Fallback: construct from base_url and mcp_path
        return f"{self.base_url.rstrip('/')}{mcp_path}"


def create_hybrid_auth_provider(
    authkit_domain: str,
    base_url: str,
    internal_token: Optional[str] = None,
    authkit_client_id: Optional[str] = None,
    authkit_jwks_uri: Optional[str] = None
) -> HybridAuthProvider:
    """Factory function to create hybrid auth provider.

    Args:
        authkit_domain: AuthKit domain for OAuth
        base_url: Base URL for OAuth callbacks
        internal_token: Static token for internal services
        authkit_client_id: AuthKit client ID for JWT validation
        authkit_jwks_uri: AuthKit JWKS URI for JWT verification

    Returns:
        Configured HybridAuthProvider
    """
    # Create OAuth provider
    oauth_provider = AuthKitProvider(
        authkit_domain=authkit_domain,
        base_url=base_url
    )

    # Create hybrid provider
    return HybridAuthProvider(
        oauth_provider=oauth_provider,
        internal_token=internal_token,
        authkit_client_id=authkit_client_id,
        authkit_jwks_uri=authkit_jwks_uri
    )

