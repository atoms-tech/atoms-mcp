"""FastMCP-compatible auth provider factory.

This module provides HybridAuthProviderFactory that FastMCP can instantiate
via the FASTMCP_SERVER_AUTH environment variable.

The factory creates a CompositeAuthProvider that supports both:
- Bearer tokens (for internal clients)
- OAuth flow (for external clients like IDEs)
"""

from __future__ import annotations

import os
import logging
from typing import Any

logger = logging.getLogger(__name__)


def HybridAuthProviderFactory(**kwargs: Any) -> Any:
    """Factory function that creates CompositeAuthProvider for FastMCP.
    
    This function is called by FastMCP when FASTMCP_SERVER_AUTH is set to
    this module path. It returns a CompositeAuthProvider instance configured
    with environment variables.
    
    Args:
        **kwargs: Additional arguments (ignored, we use env vars)
        
    Returns:
        CompositeAuthProvider instance configured from environment variables
    """
    try:
        # Import here to avoid circular dependencies
        from infrastructure.auth_composite import CompositeAuthProvider
    except ImportError:
        # Fallback for different import contexts
        try:
            from .infrastructure.auth_composite import CompositeAuthProvider
        except ImportError:
            # Last resort: absolute import
            import sys
            import os as os_module
            current_dir = os_module.path.dirname(os_module.path.abspath(__file__))
            parent_dir = os_module.path.dirname(current_dir)
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)
            from infrastructure.auth_composite import CompositeAuthProvider
    
    # Get configuration from environment variables
    authkit_domain = os.getenv("FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN", "").strip()
    base_url = os.getenv("FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL", "http://localhost:8000").strip()
    required_scopes_str = os.getenv("FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_REQUIRED_SCOPES", "openid,profile,email")
    required_scopes = [s.strip() for s in required_scopes_str.split(",") if s.strip()]
    
    if not authkit_domain:
        raise ValueError(
            "FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN environment variable is required"
        )
    
    logger.info(
        f"🔐 HybridAuthProviderFactory creating CompositeAuthProvider:\n"
        f"  - Domain: {authkit_domain}\n"
        f"  - Base URL: {base_url}\n"
        f"  - Required scopes: {required_scopes}"
    )
    
    # Create and return CompositeAuthProvider
    return CompositeAuthProvider(
        authkit_domain=authkit_domain,
        base_url=base_url,
        required_scopes=required_scopes,
    )
