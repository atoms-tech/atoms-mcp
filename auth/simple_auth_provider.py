"""Simple authentication provider that provides login endpoints for MCP clients.

This creates a /auth/login endpoint that MCP clients can use to authenticate
by providing username/password, which are then validated against Supabase.
"""

from __future__ import annotations

import os
import logging
import httpx
from typing import Optional, Dict, Any

try:
    from fastmcp.server.auth import AuthProvider, AccessToken, TokenInvalidException
    from fastmcp import FastMCP
    from starlette.requests import Request
    from starlette.responses import JSONResponse
except ImportError:
    logger = logging.getLogger(__name__)
    logger.error("FastMCP auth imports failed - Simple auth disabled")
    # Create stubs for development
    class AuthProvider:
        def __init__(self, **kwargs): pass
    class AccessToken:
        def __init__(self, **kwargs): pass
    class TokenInvalidException(Exception):
        pass

logger = logging.getLogger(__name__)


class SupabaseSimpleAuthProvider(AuthProvider):
    """Simple authentication provider with login endpoint for MCP clients.
    
    Provides:
    - POST /auth/login - Username/password login that returns Supabase JWT
    - Token validation using Supabase auth/v1/user endpoint
    
    MCP Client Flow:
    1. Client calls POST /auth/login with username/password
    2. Server validates with Supabase auth.signInWithPassword()
    3. Server returns Supabase JWT
    4. Client uses JWT for all subsequent tool calls
    """
    
    def __init__(
        self,
        supabase_url: Optional[str] = None,
        anon_key: Optional[str] = None,
        timeout: float = 10.0
    ):
        self.supabase_url = supabase_url or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        if not self.supabase_url:
            raise ValueError("Supabase URL required: set NEXT_PUBLIC_SUPABASE_URL")
        
        self.supabase_url = self.supabase_url.rstrip('/')
        self.anon_key = anon_key or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
        if not self.anon_key:
            raise ValueError("Supabase anon key required: set NEXT_PUBLIC_SUPABASE_ANON_KEY")
        
        self.timeout = timeout
        
        logger.info(f"Configured Supabase Simple Auth with URL: {self.supabase_url}")
        
        super().__init__()
    
    def setup_routes_sync(self, mcp_server: FastMCP) -> None:
        """Setup authentication routes on the FastMCP server (synchronous version)."""
        
        @mcp_server.custom_route("/auth/login", methods=["POST"])
        async def login_endpoint(request: Request) -> JSONResponse:
            """Login endpoint for MCP clients."""
            try:
                body = await request.json()
                email = body.get("email") or body.get("username")
                password = body.get("password")
                
                if not email or not password:
                    return JSONResponse(
                        {"error": "Email and password required"}, 
                        status_code=400
                    )
                
                # Authenticate with Supabase
                jwt_token = await self._authenticate_with_supabase(email, password)
                
                if jwt_token:
                    return JSONResponse({
                        "access_token": jwt_token,
                        "token_type": "bearer",
                        "message": "Login successful"
                    })
                else:
                    return JSONResponse(
                        {"error": "Invalid credentials"}, 
                        status_code=401
                    )
                    
            except Exception as e:
                logger.error(f"Login error: {e}")
                return JSONResponse(
                    {"error": "Login failed"}, 
                    status_code=500
                )
        
        @mcp_server.custom_route("/auth/status", methods=["GET"])
        async def auth_status(request: Request) -> JSONResponse:
            """Check authentication status."""
            auth_header = request.headers.get("Authorization", "")
            
            if not auth_header.startswith("Bearer "):
                return JSONResponse({"authenticated": False})
            
            token = auth_header[7:]  # Remove "Bearer "
            
            try:
                user_info = await self._validate_token(token)
                if user_info:
                    return JSONResponse({
                        "authenticated": True,
                        "user": {
                            "id": user_info.get("id"),
                            "email": user_info.get("email")
                        }
                    })
                else:
                    return JSONResponse({"authenticated": False})
            except Exception:
                return JSONResponse({"authenticated": False})
    
    async def setup_routes(self, mcp_server: FastMCP) -> None:
        """Setup authentication routes on the FastMCP server."""
        
        @mcp_server.custom_route("/auth/login", methods=["POST"])
        async def login_endpoint(request: Request) -> JSONResponse:
            """Login endpoint for MCP clients."""
            try:
                body = await request.json()
                email = body.get("email") or body.get("username")
                password = body.get("password")
                
                if not email or not password:
                    return JSONResponse(
                        {"error": "Email and password required"}, 
                        status_code=400
                    )
                
                # Authenticate with Supabase
                jwt_token = await self._authenticate_with_supabase(email, password)
                
                if jwt_token:
                    return JSONResponse({
                        "access_token": jwt_token,
                        "token_type": "bearer",
                        "message": "Login successful"
                    })
                else:
                    return JSONResponse(
                        {"error": "Invalid credentials"}, 
                        status_code=401
                    )
                    
            except Exception as e:
                logger.error(f"Login error: {e}")
                return JSONResponse(
                    {"error": "Login failed"}, 
                    status_code=500
                )
        
        @mcp_server.custom_route("/auth/status", methods=["GET"])
        async def auth_status(request: Request) -> JSONResponse:
            """Check authentication status."""
            auth_header = request.headers.get("Authorization", "")
            
            if not auth_header.startswith("Bearer "):
                return JSONResponse({"authenticated": False})
            
            token = auth_header[7:]  # Remove "Bearer "
            
            try:
                user_info = await self._validate_token(token)
                if user_info:
                    return JSONResponse({
                        "authenticated": True,
                        "user": {
                            "id": user_info.get("id"),
                            "email": user_info.get("email")
                        }
                    })
                else:
                    return JSONResponse({"authenticated": False})
            except Exception:
                return JSONResponse({"authenticated": False})
    
    async def _authenticate_with_supabase(self, email: str, password: str) -> Optional[str]:
        """Authenticate user with Supabase and return JWT."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Use Supabase auth API
                auth_url = f"{self.supabase_url}/auth/v1/token?grant_type=password"
                
                headers = {
                    "apikey": self.anon_key,
                    "Content-Type": "application/json"
                }
                
                data = {
                    "email": email,
                    "password": password
                }
                
                response = await client.post(auth_url, headers=headers, json=data)
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("access_token")
                else:
                    logger.warning(f"Supabase auth failed: {response.status_code} {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Supabase authentication error: {e}")
            return None
    
    async def _validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate token using Supabase auth/v1/user endpoint."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {
                    "Authorization": f"Bearer {token}",
                    "apikey": self.anon_key
                }
                
                user_url = f"{self.supabase_url}/auth/v1/user"
                response = await client.get(user_url, headers=headers)
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return None
                    
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return None
    
    async def verify(self, token: str) -> Optional[AccessToken]:
        """Verify token for FastMCP (required by AuthProvider)."""
        user_data = await self._validate_token(token)
        
        if user_data:
            return AccessToken(
                token=token,
                user_id=user_data.get("id"),
                email=user_data.get("email"),
                metadata={"supabase_user": user_data}
            )
        else:
            raise TokenInvalidException("Invalid or expired token")


def create_supabase_simple_auth_provider(
    supabase_url: Optional[str] = None,
    anon_key: Optional[str] = None
) -> Optional[SupabaseSimpleAuthProvider]:
    """Create a Supabase Simple Auth provider.
    
    This provides /auth/login endpoint for MCP clients.
    """
    try:
        provider = SupabaseSimpleAuthProvider(
            supabase_url=supabase_url,
            anon_key=anon_key
        )
        logger.info("Successfully created Supabase Simple Auth provider")
        return provider
        
    except ValueError as e:
        logger.warning(f"Supabase Simple Auth not configured: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to create Supabase Simple Auth provider: {e}")
        return None