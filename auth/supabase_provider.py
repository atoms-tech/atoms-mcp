"""Supabase authentication provider for FastMCP."""

from __future__ import annotations

import logging
from typing import Optional

try:
    from fastmcp.server.auth.auth import AuthProvider, AccessToken
except ImportError:
    # Fallback if import structure is different
    try:
        from fastmcp.auth import AuthProvider, AccessToken
    except ImportError:
        # If FastMCP auth is not available, create minimal stubs
        class AuthProvider:
            async def verify_token(self, token: str) -> Optional["AccessToken"]:
                pass
        
        class AccessToken:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)

from ..infrastructure.factory import get_adapters

logger = logging.getLogger(__name__)


class SupabaseAuthProvider(AuthProvider):
    """Authentication provider that validates Supabase JWTs and session tokens."""
    
    def __init__(self):
        self._adapters = None
    
    def _get_auth_adapter(self):
        """Get the auth adapter, cached."""
        if self._adapters is None:
            self._adapters = get_adapters()
        return self._adapters["auth"]
    
    async def verify_token(self, token: str) -> Optional[AccessToken]:
        """Verify a bearer token (Supabase JWT or session token).
        
        Args:
            token: The token to verify
            
        Returns:
            AccessToken if valid, None if invalid
        """
        try:
            auth_adapter = self._get_auth_adapter()
            user_info = await auth_adapter.validate_token(token)
            
            # Create AccessToken with user information
            access_token = AccessToken(
                subject=user_info["user_id"],
                username=user_info.get("username"),
                auth_type=user_info.get("auth_type", "unknown"),
                user_metadata=user_info.get("user_metadata", {}),
                # Standard JWT claims
                sub=user_info["user_id"],
                aud=["atoms-fastmcp"],
                iss="atoms-fastmcp-supabase"
            )
            
            return access_token
            
        except ValueError as e:
            logger.debug(f"Token validation failed: {e}")
            return None
        except Exception as e:
            logger.warning(f"Unexpected error during token validation: {e}")
            return None