"""WorkOS AuthKit integration with Supabase authentication proxy.

This service acts as a bridge between WorkOS AuthKit (OAuth 2.0 server) 
and Supabase Auth (user credential storage), enabling OAuth 2.0 PKCE + DCR
compliance while maintaining existing user data in Supabase.
"""

from __future__ import annotations

import os
import logging
import hashlib
import base64
import secrets
from typing import Dict, Any, Optional, Union
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

try:
    import workos
    from workos import WorkOS
    WORKOS_AVAILABLE = True
except ImportError:
    logger.warning("WorkOS package not installed. Install with: pip install workos")
    WORKOS_AVAILABLE = False
    
    # Mock WorkOS class for development
    class WorkOS:
        def __init__(self, api_key=None, client_id=None, base_url=None):
            self.user_management = MockUserManagement()
    
    class MockUserManagement:
        def create_session(self, user_id):
            return MockSession()
        
        def get_user_by_email(self, email):
            raise Exception("User not found")
        
        def create_user(self, email, first_name="", last_name="", email_verified=True):
            return MockUser(email)
    
    class MockSession:
        def __init__(self):
            self.access_token = f"wos_test_{secrets.token_urlsafe(16)}"
            self.refresh_token = f"wos_refresh_{secrets.token_urlsafe(16)}"
    
    class MockUser:
        def __init__(self, email):
            self.id = f"user_{secrets.token_urlsafe(8)}"
            self.email = email

try:
    from supabase import Client
    from ..supabase_client import get_supabase
    SUPABASE_AVAILABLE = True
except ImportError:
    logger.warning("Supabase client not available")
    SUPABASE_AVAILABLE = False
    class Client:
        pass
    def get_supabase():
        return None


class WorkOSSupabaseAuthProxy:
    """Authentication proxy that bridges WorkOS AuthKit and Supabase Auth."""
    
    def __init__(self):
        if not WORKOS_AVAILABLE:
            logger.warning("WorkOS package not available, using mock implementation")
        
        # Initialize WorkOS client
        self.workos = WorkOS(
            api_key=os.getenv("WORKOS_API_KEY"),
            client_id=os.getenv("WORKOS_CLIENT_ID"),
            base_url=os.getenv("WORKOS_API_URL", "https://api.workos.com")
        )
        
        # Supabase client for credential validation
        self.supabase = get_supabase() if SUPABASE_AVAILABLE else None
        
        # In-memory stores (use Redis in production)
        self.pkce_challenges = {}
        self.auth_codes = {}
        self.client_registrations = {}
        
    async def validate_supabase_credentials(
        self, 
        email: str, 
        password: str
    ) -> Dict[str, Any]:
        """Validate email/password against Supabase Auth."""
        if not self.supabase:
            return {"success": False, "error": "Supabase not available"}
        
        try:
            # Method 1: Try direct Supabase authentication
            auth_response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if auth_response.user:
                # Log WorkOS event
                try:
                    self.supabase.rpc('log_workos_event', {
                        'user_id': auth_response.user.id,
                        'event_type': 'email_password_auth',
                        'event_data': {'email': email, 'source': 'workos_proxy'}
                    }).execute()
                except:
                    pass  # Don't fail if logging fails
                
                return {
                    "success": True,
                    "user": {
                        "id": auth_response.user.id,
                        "email": auth_response.user.email,
                        "user_metadata": auth_response.user.user_metadata or {},
                        "app_metadata": auth_response.user.app_metadata or {}
                    }
                }
            else:
                return {"success": False, "error": "Invalid credentials"}
                
        except Exception as e:
            logger.error(f"Supabase auth failed: {e}")
            
            # Method 2: Fallback to RPC function for validation
            try:
                response = self.supabase.rpc('validate_user_credentials', {
                    'user_email': email,
                    'check_password': password
                }).execute()
                
                if response.data:
                    return response.data
                else:
                    return {"success": False, "error": "Authentication failed"}
                    
            except Exception as rpc_error:
                logger.error(f"RPC validation failed: {rpc_error}")
                return {"success": False, "error": str(e)}
    
    async def validate_oauth_provider(
        self, 
        provider: str, 
        code: str, 
        redirect_uri: str
    ) -> Dict[str, Any]:
        """Validate OAuth provider code against Supabase."""
        if not self.supabase:
            return {"success": False, "error": "Supabase not available"}
        
        try:
            # Exchange OAuth code with Supabase
            auth_response = self.supabase.auth.exchange_code_for_session(code)
            
            if auth_response.user:
                return {
                    "success": True,
                    "user": {
                        "id": auth_response.user.id,
                        "email": auth_response.user.email,
                        "user_metadata": auth_response.user.user_metadata or {},
                        "app_metadata": auth_response.user.app_metadata or {},
                        "provider": provider
                    }
                }
            else:
                return {"success": False, "error": f"OAuth {provider} validation failed"}
                
        except Exception as e:
            logger.error(f"OAuth {provider} validation failed: {e}")
            return {"success": False, "error": str(e)}
    
    def generate_pkce_challenge(self) -> Dict[str, str]:
        """Generate PKCE code verifier and challenge."""
        # Generate random code verifier (43-128 characters)
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        
        # Create code challenge using SHA256
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode('utf-8')).digest()
        ).decode('utf-8').rstrip('=')
        
        return {
            "code_verifier": code_verifier,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256"
        }
    
    def store_pkce_challenge(
        self, 
        code_challenge: str, 
        client_id: str, 
        redirect_uri: str,
        state: Optional[str] = None
    ) -> str:
        """Store PKCE challenge for later verification."""
        challenge_id = secrets.token_urlsafe(32)
        
        self.pkce_challenges[challenge_id] = {
            "code_challenge": code_challenge,
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(minutes=10)
        }
        
        return challenge_id
    
    def verify_pkce_challenge(
        self, 
        challenge_id: str, 
        code_verifier: str
    ) -> bool:
        """Verify PKCE code verifier against stored challenge."""
        if challenge_id not in self.pkce_challenges:
            return False
        
        challenge_data = self.pkce_challenges[challenge_id]
        
        # Check expiration
        if datetime.utcnow() > challenge_data["expires_at"]:
            del self.pkce_challenges[challenge_id]
            return False
        
        # Verify code verifier
        expected_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode('utf-8')).digest()
        ).decode('utf-8').rstrip('=')
        
        is_valid = expected_challenge == challenge_data["code_challenge"]
        
        if is_valid:
            # Clean up used challenge
            del self.pkce_challenges[challenge_id]
        
        return is_valid
    
    def generate_authorization_code(
        self, 
        user_id: str, 
        client_id: str,
        challenge_id: str
    ) -> str:
        """Generate authorization code for OAuth flow."""
        auth_code = secrets.token_urlsafe(32)
        
        self.auth_codes[auth_code] = {
            "user_id": user_id,
            "client_id": client_id,
            "challenge_id": challenge_id,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(minutes=10)
        }
        
        return auth_code
    
    async def exchange_code_for_tokens(
        self, 
        auth_code: str, 
        code_verifier: str,
        client_id: str
    ) -> Dict[str, Any]:
        """Exchange authorization code for access tokens."""
        if auth_code not in self.auth_codes:
            return {"success": False, "error": "Invalid authorization code"}
        
        code_data = self.auth_codes[auth_code]
        
        # Check expiration
        if datetime.utcnow() > code_data["expires_at"]:
            del self.auth_codes[auth_code]
            return {"success": False, "error": "Authorization code expired"}
        
        # Verify client ID
        if client_id != code_data["client_id"]:
            return {"success": False, "error": "Client ID mismatch"}
        
        # Verify PKCE
        if not self.verify_pkce_challenge(code_data["challenge_id"], code_verifier):
            return {"success": False, "error": "Invalid PKCE verification"}
        
        try:
            # Create WorkOS session for the user
            session = self.workos.user_management.create_session(
                user_id=code_data["user_id"]
            )
            
            # Clean up used code
            del self.auth_codes[auth_code]
            
            return {
                "success": True,
                "access_token": session.access_token,
                "refresh_token": session.refresh_token,
                "token_type": "Bearer",
                "expires_in": 3600
            }
            
        except Exception as e:
            logger.error(f"Token exchange failed: {e}")
            return {"success": False, "error": "Token generation failed"}
    
    def register_dynamic_client(
        self, 
        client_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Register OAuth client dynamically (DCR)."""
        try:
            # Generate client credentials
            client_id = f"mcp_{secrets.token_urlsafe(16)}"
            client_secret = secrets.token_urlsafe(32)
            
            # Store client registration
            self.client_registrations[client_id] = {
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uris": client_data.get("redirect_uris", []),
                "client_name": client_data.get("client_name", "MCP Client"),
                "grant_types": client_data.get("grant_types", ["authorization_code"]),
                "response_types": client_data.get("response_types", ["code"]),
                "token_endpoint_auth_method": client_data.get("token_endpoint_auth_method", "client_secret_post"),
                "created_at": datetime.utcnow()
            }
            
            return {
                "success": True,
                "client_id": client_id,
                "client_secret": client_secret,
                "client_id_issued_at": int(datetime.utcnow().timestamp()),
                "client_secret_expires_at": 0,  # Never expires
                "redirect_uris": client_data.get("redirect_uris", []),
                "grant_types": client_data.get("grant_types", ["authorization_code"]),
                "response_types": client_data.get("response_types", ["code"]),
                "client_name": client_data.get("client_name", "MCP Client"),
                "token_endpoint_auth_method": client_data.get("token_endpoint_auth_method", "client_secret_post")
            }
            
        except Exception as e:
            logger.error(f"Dynamic client registration failed: {e}")
            return {"success": False, "error": "Client registration failed"}
    
    def validate_client(self, client_id: str, client_secret: Optional[str] = None) -> bool:
        """Validate OAuth client credentials."""
        if client_id not in self.client_registrations:
            return False
        
        if client_secret:
            return self.client_registrations[client_id]["client_secret"] == client_secret
        
        return True
    
    async def create_workos_user_from_supabase(self, supabase_user: Dict[str, Any]) -> str:
        """Create or get WorkOS user ID from Supabase user data."""
        try:
            user_email = supabase_user["email"]
            
            # Check if user already exists in WorkOS
            try:
                workos_user = self.workos.user_management.get_user_by_email(
                    email=user_email
                )
                workos_user_id = workos_user.id
            except:
                # User doesn't exist, create new one
                workos_user = self.workos.user_management.create_user(
                    email=user_email,
                    first_name=supabase_user.get("user_metadata", {}).get("first_name", ""),
                    last_name=supabase_user.get("user_metadata", {}).get("last_name", ""),
                    email_verified=True
                )
                workos_user_id = workos_user.id
            
            # Link WorkOS user with Supabase user
            if self.supabase:
                try:
                    self.supabase.rpc('link_workos_user', {
                        'workos_user_id': workos_user_id,
                        'user_email': user_email
                    }).execute()
                    
                    # Log the linking event
                    self.supabase.rpc('log_workos_event', {
                        'user_id': supabase_user["id"],
                        'event_type': 'workos_user_linked',
                        'event_data': {'workos_user_id': workos_user_id, 'email': user_email},
                        'workos_user_id': workos_user_id
                    }).execute()
                except Exception as link_error:
                    logger.warning(f"Failed to link WorkOS user in Supabase: {link_error}")
            
            return workos_user_id
                
        except Exception as e:
            logger.error(f"Failed to create/get WorkOS user: {e}")
            raise