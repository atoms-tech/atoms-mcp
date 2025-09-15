"""Supabase authentication provider for FastMCP using proper JWT verification."""

from __future__ import annotations

import os
import logging
from typing import Optional

try:
    from fastmcp.server.auth import JWTVerifier, TokenVerifier, RemoteAuthProvider
    from pydantic import AnyHttpUrl
except ImportError:
    logger = logging.getLogger(__name__)
    logger.error("FastMCP auth imports failed - authentication disabled")
    # Create stubs for development
    class JWTVerifier:
        def __init__(self, **kwargs): pass
    class TokenVerifier:
        def __init__(self, **kwargs): pass
    class RemoteAuthProvider:
        def __init__(self, **kwargs): pass
    AnyHttpUrl = str

logger = logging.getLogger(__name__)


def create_supabase_jwt_verifier(
    base_url: Optional[str] = None,
    required_scopes: Optional[list[str]] = None
) -> Optional[JWTVerifier]:
    """Create a proper JWT verifier for Supabase tokens.
    
    Uses Supabase's JWKS endpoint for asymmetric JWT verification.
    Returns None if Supabase is not configured (development mode).
    """
    supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    if not supabase_url:
        logger.warning("No Supabase URL configured - authentication disabled")
        return None
    
    try:
        # Supabase JWKS endpoint
        jwks_uri = f"{supabase_url}/auth/v1/.well-known/jwks.json"
        
        # Create JWT verifier with Supabase configuration
        jwt_verifier = JWTVerifier(
            jwks_uri=jwks_uri,
            issuer=f"{supabase_url}/auth/v1",  # Supabase auth issuer
            audience=["authenticated"],  # Standard Supabase audience
            algorithm="RS256",  # Supabase uses RS256 for asymmetric keys
            required_scopes=required_scopes or [],
            base_url=base_url
        )
        
        logger.info(f"Configured Supabase JWT verification with JWKS: {jwks_uri}")
        return jwt_verifier
        
    except Exception as e:
        logger.error(f"Failed to create Supabase JWT verifier: {e}")
        return None


# Note: Supabase does not support OAuth Dynamic Client Registration (DCR)
# which is required for FastMCP's RemoteAuthProvider. For full OAuth support,
# you would need to implement a custom OAuth Proxy or use a DCR-compliant
# provider like WorkOS AuthKit.


# For backward compatibility - alias to the JWT verifier
SupabaseAuthProvider = create_supabase_jwt_verifier