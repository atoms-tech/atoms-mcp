"""Server authentication setup.

Configures FastMCP authentication with hybrid provider supporting OAuth and Bearer tokens.
"""

import os
import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)


def resolve_base_url() -> str:
    """Resolve the base URL for OAuth resource."""
    base_url_raw = os.getenv("FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL")
    logger.info(f"🔍 DEBUG: Raw FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL from env: '{base_url_raw}'")
    print(f"🔍 DEBUG: Raw BASE_URL from env: '{base_url_raw}'")

    base_url = base_url_raw

    # Clean up the URL (remove /api/mcp or /mcp suffix if present)
    if base_url:
        base_url = base_url.rstrip("/")
        if base_url.endswith("/api/mcp"):
            base_url = base_url[: -len("/api/mcp")]
            logger.info("🔍 DEBUG: Stripped /api/mcp suffix")
        elif base_url.endswith("/mcp"):
            base_url = base_url[: -len("/mcp")]
            logger.info("🔍 DEBUG: Stripped /mcp suffix")

    # Fallback if not set
    if not base_url:
        host = os.getenv("ATOMS_FASTMCP_HOST", "127.0.0.1")
        port = os.getenv("ATOMS_FASTMCP_PORT", "8000")
        base_url = f"http://{host}:{port}"
        logger.warning(f"⚠️  FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL not set, using fallback: {base_url}")

    logger.info(f"✅ Resolved base URL for OAuth resource: {base_url}")
    print(f"🌐 AUTH BASE URL -> {base_url}")
    return base_url


def create_auth_provider(base_url: str) -> Any:
    """Create hybrid authentication provider supporting OAuth and Bearer tokens."""
    # Configure hybrid authentication (OAuth + Bearer tokens)
    authkit_domain = os.getenv("FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN")
    if not authkit_domain:
        raise ValueError("FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN required")

    # Get optional bearer token configuration
    internal_token = os.getenv("ATOMS_INTERNAL_TOKEN")
    
    # For development/testing: auto-enable test E2E token if in test mode
    if not internal_token and os.getenv("ATOMS_TEST_MODE", "").lower() == "true":
        internal_token = "test-e2e-token-for-atoms-mcp"
        logger.info("🧪 Test mode enabled: using E2E test token for internal authentication")
    
    authkit_client_id = os.getenv("WORKOS_CLIENT_ID")

    # Construct AuthKit JWKS URI from domain
    authkit_jwks_uri = None
    if authkit_domain:
        # AuthKit JWKS endpoint is at /.well-known/jwks.json
        authkit_jwks_uri = f"{authkit_domain}/.well-known/jwks.json"

    # Use hybrid auth provider supporting both OAuth and Bearer tokens
    try:
        from services.auth.hybrid_auth_provider import create_hybrid_auth_provider
    except ImportError:
        from ..services.auth.hybrid_auth_provider import create_hybrid_auth_provider  # type: ignore[no-redef]

    auth_provider = create_hybrid_auth_provider(
        authkit_domain=authkit_domain,
        base_url=base_url,
        internal_token=internal_token,
        authkit_client_id=authkit_client_id,
        authkit_jwks_uri=authkit_jwks_uri
    )

    logger.info("✅ Hybrid authentication configured:")
    logger.info(f"  - OAuth (AuthKit): {authkit_domain}")
    if internal_token:
        logger.info("  - Internal bearer token: enabled")
    if authkit_client_id and authkit_jwks_uri:
        logger.info("  - AuthKit JWT: enabled")

    print("✅ Hybrid authentication configured: OAuth + Bearer tokens")
    return auth_provider
