"""Hybrid authentication provider supporting both OAuth and Bearer tokens.

This provider enables the same MCP server to handle:
1. OAuth (AuthKit) for public clients
2. Bearer tokens for internal services (atomsAgent)
3. Supabase JWTs for frontend token forwarding (optional)
"""

from __future__ import annotations

import os
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
        supabase_jwt_secret: Optional[str] = None,
        supabase_project_id: Optional[str] = None
    ):
        """Initialize hybrid auth provider.
        
        Args:
            oauth_provider: AuthKit provider for OAuth flow
            internal_token: Static token for internal services
            supabase_jwt_secret: Supabase JWT secret for frontend tokens
            supabase_project_id: Supabase project ID for issuer validation
        """
        self.oauth_provider = oauth_provider
        
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
        
        # Setup Supabase JWT verifier
        self.supabase_jwt_verifier = None
        if supabase_jwt_secret and supabase_project_id:
            self.supabase_jwt_verifier = JWTVerifier(
                public_key=supabase_jwt_secret,
                issuer=f"https://{supabase_project_id}.supabase.co/auth/v1",
                audience="authenticated",
                algorithm="HS256"
            )
            logger.info("✅ Supabase JWT authentication enabled")
    
    async def authenticate(self, request) -> Optional[Dict[str, Any]]:
        """Authenticate request using OAuth or Bearer token.
        
        Flow:
        1. Check for Authorization: Bearer <token> header
        2. If present, try bearer token verification
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
            
            # Try internal token first
            if self.internal_token_verifier:
                try:
                    result = await self.internal_token_verifier.verify_token(token)
                    logger.info("✅ Authenticated via internal bearer token")
                    return result
                except Exception as e:
                    logger.debug(f"Internal token verification failed: {e}")
            
            # Try Supabase JWT
            if self.supabase_jwt_verifier:
                try:
                    result = await self.supabase_jwt_verifier.verify_token(token)
                    logger.info(f"✅ Authenticated via Supabase JWT: {result.get('email')}")
                    return result
                except Exception as e:
                    logger.debug(f"Supabase JWT verification failed: {e}")
            
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
        return self.internal_token_verifier is not None or self.supabase_jwt_verifier is not None


def create_hybrid_auth_provider(
    authkit_domain: str,
    base_url: str,
    internal_token: Optional[str] = None,
    supabase_jwt_secret: Optional[str] = None,
    supabase_project_id: Optional[str] = None
) -> HybridAuthProvider:
    """Factory function to create hybrid auth provider.
    
    Args:
        authkit_domain: AuthKit domain for OAuth
        base_url: Base URL for OAuth callbacks
        internal_token: Static token for internal services
        supabase_jwt_secret: Supabase JWT secret
        supabase_project_id: Supabase project ID
        
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
        supabase_jwt_secret=supabase_jwt_secret,
        supabase_project_id=supabase_project_id
    )

