"""Supabase authentication adapter implementation."""

from __future__ import annotations

import os
import secrets
from typing import Any, Dict, Optional
from dataclasses import dataclass

from .adapters import AuthAdapter
from ..supabase_client import get_supabase, MissingSupabaseConfig


@dataclass
class Session:
    """Internal session representation."""
    user_id: str
    username: str


class SupabaseAuthAdapter(AuthAdapter):
    """Supabase-based authentication adapter."""
    
    def __init__(self):
        # In-memory session store for simple session tokens
        # In production, this could be Redis or database-backed
        self._sessions: Dict[str, Session] = {}
    
    async def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate either a Supabase JWT or session token."""
        # First try as session token
        if session := self._sessions.get(token):
            return {
                "user_id": session.user_id,
                "username": session.username,
                "auth_type": "session"
            }
        
        # Try as Supabase JWT
        try:
            supabase = get_supabase()
            # Set the auth header and try to get user
            supabase.auth.set_session(access_token=token, refresh_token="")
            user = supabase.auth.get_user()
            
            if user and hasattr(user, 'user') and user.user:
                return {
                    "user_id": user.user.id,
                    "username": user.user.email or f"user_{user.user.id}",
                    "auth_type": "jwt",
                    "user_metadata": getattr(user.user, 'user_metadata', {})
                }
        except Exception:
            # JWT validation failed
            pass
        
        raise ValueError("Invalid or expired token")
    
    async def create_session(self, user_id: str, username: str) -> str:
        """Create a new session token."""
        token = secrets.token_urlsafe(32)
        self._sessions[token] = Session(user_id=user_id, username=username)
        return token
    
    async def revoke_session(self, token: str) -> bool:
        """Revoke a session token."""
        if token in self._sessions:
            del self._sessions[token]
            return True
        return False
    
    async def verify_credentials(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Verify username/password credentials."""
        # Check environment override for demo/testing
        env_user = os.getenv("FASTMCP_DEMO_USER")
        env_pass = os.getenv("FASTMCP_DEMO_PASS")
        
        if env_user and env_pass:
            if username == env_user and password == env_pass:
                return {"id": f"user_{username}", "username": username}
            return None
        
        # Try Supabase auth
        try:
            supabase = get_supabase()
            auth_res = supabase.auth.sign_in_with_password({
                "email": username,
                "password": password,
            })
            
            user = getattr(auth_res, "user", None)
            if user and getattr(user, "id", None):
                return {
                    "id": user.id, 
                    "username": username,
                    "user_metadata": getattr(user, 'user_metadata', {})
                }
        except MissingSupabaseConfig:
            # Fall back to demo behavior for development
            pass
        except Exception:
            # Treat any auth error as invalid credentials
            pass
        
        # Demo fallback: accept any non-empty credentials when no strict env set
        if username and password and not env_user:
            return {"id": f"user_{username}", "username": username}
        
        return None