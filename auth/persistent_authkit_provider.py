"""Simple AuthKit Provider for standard OAuth 2.1 with PKCE.

Uses FastMCP's built-in AuthKitProvider without customization.
SessionMiddleware extracts JWT and sets user context.
"""

from __future__ import annotations

from fastmcp.server.auth.providers.workos import AuthKitProvider


class PersistentAuthKitProvider(AuthKitProvider):
    """AuthKit provider using standard OAuth 2.1 with PKCE.

    No custom endpoints needed - AuthKit handles everything.
    SessionMiddleware extracts JWT and provides user context to tools.
    """

    def __init__(self, **kwargs):
        """Initialize with standard AuthKit configuration."""
        super().__init__(**kwargs)
