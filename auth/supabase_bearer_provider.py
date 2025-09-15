"""Supabase Bearer Auth provider for FastMCP using auth/v1/user endpoint.

This is the correct approach for Supabase authentication as Supabase doesn't 
expose native OAuth 2.1 endpoints. Instead, we validate tokens using the
auth/v1/user endpoint.

Based on: https://medium.com/@dimi/tutorial-how-to-use-supabase-auth-with-your-fastmcp-server-6fb826573d98
"""

from __future__ import annotations

import os
import logging
import httpx
from typing import Optional

try:
    from fastmcp.server.auth import TokenVerifier, AccessToken, TokenInvalidException
    from pydantic import AnyHttpUrl
except ImportError:
    logger = logging.getLogger(__name__)
    logger.error("FastMCP auth imports failed - Bearer auth disabled")
    # Create stubs for development
    class TokenVerifier:
        def __init__(self, **kwargs): pass
    class AccessToken:
        def __init__(self, **kwargs): pass
    class TokenInvalidException(Exception):
        pass
    AnyHttpUrl = str

logger = logging.getLogger(__name__)


class SupabaseTokenVerifier(TokenVerifier):
    """Supabase Bearer Auth provider using auth/v1/user endpoint for token validation.
    
    This validates Supabase JWTs by making a request to the auth/v1/user endpoint
    with the provided token. If the token is valid, Supabase returns user information.
    If invalid, it returns an error.
    
    Setup Requirements:
    1. Set NEXT_PUBLIC_SUPABASE_URL environment variable
    2. Optionally set NEXT_PUBLIC_SUPABASE_ANON_KEY (for additional validation)
    3. No OAuth configuration needed - just works with Supabase JWTs
    """
    
    def __init__(
        self,
        supabase_url: Optional[str] = None,
        anon_key: Optional[str] = None,
        timeout: float = 10.0
    ):
        self.supabase_url = supabase_url or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        if not self.supabase_url:
            raise ValueError("Supabase URL required: set NEXT_PUBLIC_SUPABASE_URL or pass supabase_url")
        
        # Remove trailing slash
        self.supabase_url = self.supabase_url.rstrip('/')
        
        # Optional anon key for additional validation
        self.anon_key = anon_key or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
        
        # HTTP client for validation requests
        self.timeout = timeout
        
        logger.info(f"Configured Supabase Bearer Auth with URL: {self.supabase_url}")
        
        super().__init__()
    
    async def verify(self, token: str) -> Optional[AccessToken]:
        """Validate token by calling Supabase auth/v1/user endpoint.
        
        Args:
            token: The Bearer token to validate (Supabase JWT)
            
        Returns:
            AccessToken if valid, None if invalid
            
        Raises:
            TokenInvalidException if token is explicitly invalid
        """
        
        try:
            # Prepare headers for Supabase request
            headers = {
                "Authorization": f"Bearer {token}",
                "apikey": self.anon_key or "",  # Include anon key if available
                "Content-Type": "application/json"
            }
            
            # Make request to Supabase auth/v1/user endpoint
            user_endpoint = f"{self.supabase_url}/auth/v1/user"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.debug(f"Validating token with Supabase endpoint: {user_endpoint}")
                
                response = await client.get(user_endpoint, headers=headers)
                
                if response.status_code == 200:
                    # Token is valid - extract user info
                    user_data = response.json()
                    user_id = user_data.get("id")
                    email = user_data.get("email")
                    
                    logger.info(f"Successfully validated token for user: {email} ({user_id})")
                    
                    # Create AccessToken with user information
                    return AccessToken(
                        token=token,
                        user_id=user_id,
                        email=email,
                        metadata={
                            "supabase_user": user_data,
                            "provider": "supabase"
                        }
                    )
                
                elif response.status_code == 401:
                    # Token is invalid/expired
                    logger.warning("Token validation failed: 401 Unauthorized")
                    raise TokenInvalidException("Invalid or expired token")
                
                else:
                    # Other error
                    logger.error(f"Token validation failed with status {response.status_code}: {response.text}")
                    return None
                    
        except TokenInvalidException:
            # Re-raise token invalid exceptions
            raise
        except Exception as e:
            logger.error(f"Error validating token with Supabase: {e}")
            return None


def create_supabase_bearer_provider(
    supabase_url: Optional[str] = None,
    anon_key: Optional[str] = None
) -> Optional[SupabaseTokenVerifier]:
    """Create a Supabase Bearer Auth provider.
    
    Args:
        supabase_url: Supabase project URL  
        anon_key: Supabase anon key (optional)
        
    Returns:
        SupabaseBearerAuthProvider instance or None if not configured
        
    Environment Variables:
        NEXT_PUBLIC_SUPABASE_URL: Supabase project URL (required)
        NEXT_PUBLIC_SUPABASE_ANON_KEY: Supabase anon key (optional)
    """
    
    try:
        provider = SupabaseTokenVerifier(
            supabase_url=supabase_url,
            anon_key=anon_key
        )
        logger.info("Successfully created Supabase Bearer Auth provider")
        return provider
        
    except ValueError as e:
        logger.warning(f"Supabase Bearer Auth not configured: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to create Supabase Bearer Auth provider: {e}")
        return None