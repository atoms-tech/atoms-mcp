"""Supabase OAuth provider using FastMCP's OAuth Proxy pattern.

This enables full OAuth 2.1 + DCR compatibility with Supabase by bridging
the gap between MCP's Dynamic Client Registration expectations and Supabase's
OAuth implementation.
"""

from __future__ import annotations

import os
import logging
from typing import Optional

try:
    from fastmcp.server.auth import OAuthProxy
    from fastmcp.server.auth.providers.jwt import JWTVerifier
    from pydantic import AnyHttpUrl
except ImportError:
    logger = logging.getLogger(__name__)
    logger.error("FastMCP OAuth imports failed - OAuth Proxy disabled")
    # Create stubs for development
    class OAuthProxy:
        def __init__(self, **kwargs): pass
    class JWTVerifier:
        def __init__(self, **kwargs): pass
    AnyHttpUrl = str

logger = logging.getLogger(__name__)


class SupabaseOAuthProvider(OAuthProxy):
    """Supabase OAuth provider using OAuth Proxy pattern.
    
    This provides full OAuth 2.1 + DCR compatibility by presenting a DCR-compliant
    interface to MCP clients while using Supabase's OAuth endpoints behind the scenes.
    
    Setup Requirements:
    1. Get OAuth client secret via Supabase CLI:
       ```
       supabase login
       supabase secrets list --project-ref your-project-ref
       ```
    2. Configure redirect URI in Supabase: {base_url}/auth/callback
    3. Set environment variables:
       - NEXT_PUBLIC_SUPABASE_URL
       - SUPABASE_OAUTH_CLIENT_SECRET
    """
    
    def __init__(
        self,
        base_url: str,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        supabase_url: Optional[str] = None,
        required_scopes: Optional[list[str]] = None,
        redirect_path: str = "/auth/callback"
    ):
        # Get Supabase configuration
        supabase_url = supabase_url or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        if not supabase_url:
            raise ValueError("Supabase URL required: set NEXT_PUBLIC_SUPABASE_URL or pass supabase_url")
        
        # Default client ID to project reference if not provided
        if not client_id:
            # Extract project ref from URL (e.g., "ydogoylwenufckscqijp" from "https://ydogoylwenufckscqijp.supabase.co")
            import urllib.parse
            parsed = urllib.parse.urlparse(supabase_url)
            if parsed.hostname and parsed.hostname.endswith('.supabase.co'):
                client_id = parsed.hostname.split('.')[0]
            else:
                client_id = os.getenv("SUPABASE_OAUTH_CLIENT_ID")
        
        if not client_id:
            raise ValueError("Client ID required: set SUPABASE_OAUTH_CLIENT_ID or ensure URL format is https://PROJECT.supabase.co")
        
        # Client secret is required for OAuth
        client_secret = client_secret or os.getenv("SUPABASE_OAUTH_CLIENT_SECRET")
        if not client_secret:
            raise ValueError("Client secret required: set SUPABASE_OAUTH_CLIENT_SECRET")
        
        # Supabase OAuth endpoints
        authorization_endpoint = f"{supabase_url}/auth/v1/authorize"
        token_endpoint = f"{supabase_url}/auth/v1/token"
        
        # Create JWT verifier for Supabase tokens
        token_verifier = JWTVerifier(
            jwks_uri=f"{supabase_url}/auth/v1/.well-known/jwks.json",
            issuer=f"{supabase_url}/auth/v1",
            audience=["authenticated"],
            algorithm="RS256",
            required_scopes=required_scopes or []
        )
        
        logger.info(f"Creating Supabase OAuth Proxy with client_id: {client_id}")
        logger.info(f"Authorization endpoint: {authorization_endpoint}")
        logger.info(f"Token endpoint: {token_endpoint}")
        logger.info(f"JWKS endpoint: {token_verifier.jwks_uri}")
        logger.info(f"Redirect URI: {base_url}{redirect_path}")
        
        super().__init__(
            upstream_authorization_endpoint=authorization_endpoint,
            upstream_token_endpoint=token_endpoint,
            upstream_client_id=client_id,
            upstream_client_secret=client_secret,
            token_verifier=token_verifier,
            base_url=base_url,
            redirect_path=redirect_path,
            # Supabase supports PKCE
            forward_pkce=True,
            # Use client_secret_post for Supabase compatibility
            token_endpoint_auth_method="client_secret_post",
            # Standard OAuth scopes for Supabase
            valid_scopes=["openid", "profile", "email"],
            # Supabase-specific parameters
            extra_authorize_params={
                "response_type": "code",
                "access_type": "offline"
            },
            extra_token_params=None
        )


def create_supabase_oauth_provider(
    base_url: Optional[str] = None,
    required_scopes: Optional[list[str]] = None
) -> Optional[SupabaseOAuthProvider]:
    """Create a Supabase OAuth provider with OAuth Proxy for DCR compatibility.
    
    Args:
        base_url: Public URL of your FastMCP server
        required_scopes: List of required OAuth scopes
        
    Returns:
        SupabaseOAuthProvider instance or None if not configured
        
    Environment Variables:
        NEXT_PUBLIC_SUPABASE_URL: Supabase project URL
        SUPABASE_OAUTH_CLIENT_ID: OAuth client ID (optional, auto-detected from URL)
        SUPABASE_OAUTH_CLIENT_SECRET: OAuth client secret (required)
        ATOMS_FASTMCP_BASE_URL: Server base URL (if not passed as parameter)
    """
    
    # Get base URL from environment if not provided
    if not base_url:
        base_url = os.getenv("ATOMS_FASTMCP_BASE_URL")
        if not base_url:
            # Try to construct from host/port
            host = os.getenv("ATOMS_FASTMCP_HOST", "127.0.0.1")
            port = os.getenv("ATOMS_FASTMCP_PORT", "8000")
            transport = os.getenv("ATOMS_FASTMCP_TRANSPORT", "stdio")
            
            if transport == "http":
                base_url = f"http://{host}:{port}"
    
    if not base_url:
        logger.warning("No base URL configured - OAuth Proxy requires public URL")
        return None
    
    try:
        provider = SupabaseOAuthProvider(
            base_url=base_url,
            required_scopes=required_scopes
        )
        logger.info("Successfully created Supabase OAuth Proxy provider")
        return provider
        
    except ValueError as e:
        logger.warning(f"Supabase OAuth not configured: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to create Supabase OAuth provider: {e}")
        return None