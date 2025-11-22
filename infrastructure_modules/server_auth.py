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


class HybridAuthProviderFactory:
    """Factory class for HybridAuthProvider that FastMCP can instantiate.

    FastMCP calls server_auth_class() with no arguments, so we need a factory
    that can be instantiated without arguments and returns the configured provider.
    """

    def __init__(self):
        """Initialize by creating the actual auth provider."""
        base_url = resolve_base_url()
        self._provider = create_auth_provider(base_url)

    def __getattr__(self, name):
        """Delegate all attribute access to the actual provider."""
        return getattr(self._provider, name)

    async def authenticate(self, request):
        """Delegate authenticate to the actual provider."""
        return await self._provider.authenticate(request)

    async def verify_token(self, token: str):
        """Delegate verify_token to the actual provider."""
        return await self._provider.verify_token(token)


def create_auth_provider(base_url: str) -> Any:
    """Create authentication provider based on FASTMCP_SERVER_AUTH configuration."""
    # Check which auth provider is configured
    auth_provider_class = os.getenv("FASTMCP_SERVER_AUTH", "fastmcp.server.auth.providers.workos.AuthKitProvider")
    print(f"🔐 create_auth_provider called with auth_provider_class={auth_provider_class}")
    logger.info(f"🔐 create_auth_provider called with auth_provider_class={auth_provider_class}")

    authkit_domain = os.getenv("FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN")
    if not authkit_domain:
        raise ValueError("FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN required")

    authkit_client_id = os.getenv("WORKOS_CLIENT_ID")

    # Construct AuthKit JWKS URI from domain
    authkit_jwks_uri = None
    if authkit_domain:
        # AuthKit JWKS endpoint is at /.well-known/jwks.json
        authkit_jwks_uri = f"{authkit_domain}/.well-known/jwks.json"

    # Use HybridAuthProvider if configured
    if "HybridAuthProvider" in auth_provider_class:
        logger.info("✅ Using HybridAuthProvider (OAuth + Bearer tokens + WorkOS User Management)")
        try:
            from services.auth.hybrid_auth_provider import create_hybrid_auth_provider
        except ImportError:
            from ..services.auth.hybrid_auth_provider import create_hybrid_auth_provider  # type: ignore[no-redef]

        auth_provider = create_hybrid_auth_provider(
            authkit_domain=authkit_domain,
            base_url=base_url,
            internal_token=None,  # NO static tokens - only real AuthKit JWTs
            authkit_client_id=authkit_client_id,
            authkit_jwks_uri=authkit_jwks_uri,
        )
        logger.info("✅ Hybrid authentication configured:")
        logger.info(f"  - OAuth (AuthKit): {authkit_domain}")
        logger.info(f"  - Bearer tokens: enabled (WorkOS User Management + AuthKit JWTs)")
        logger.info(f"  - Static/internal tokens: DISABLED")
        return auth_provider

    # Default: Use RemoteAuthProvider with WorkOS token verifier
    logger.info("✅ Using RemoteAuthProvider with WorkOSTokenVerifier")
    try:
        from fastmcp.server.auth import RemoteAuthProvider
        from pydantic import AnyHttpUrl
        from services.auth.workos_token_verifier import WorkOSTokenVerifier
    except ImportError:
        from fastmcp.server.auth import RemoteAuthProvider  # type: ignore[no-redef]
        from pydantic import AnyHttpUrl  # type: ignore[no-redef]
        from ..services.auth.workos_token_verifier import WorkOSTokenVerifier  # type: ignore[no-redef]

    # Create WorkOS token verifier (handles AuthKit OAuth + WorkOS User Management)
    token_verifier = WorkOSTokenVerifier(
        jwks_uri=authkit_jwks_uri,
        issuer=authkit_domain,  # Primary issuer (AuthKit OAuth)
        audience=authkit_client_id,
    )

    # Create RemoteAuthProvider with WorkOS token verifier
    auth_provider = RemoteAuthProvider(
        token_verifier=token_verifier,
        authorization_servers=[AnyHttpUrl(authkit_domain)],
        base_url=base_url,
    )

    logger.info("✅ Remote OAuth authentication configured:")
    logger.info(f"  - OAuth (AuthKit): {authkit_domain}")
    logger.info(f"  - Token verifier: WorkOSTokenVerifier")
    logger.info(f"    - AuthKit OAuth tokens: enabled")
    logger.info(f"    - WorkOS User Management tokens: enabled")
    logger.info(f"    - Static/internal tokens: DISABLED (AuthKit only)")
    return auth_provider
