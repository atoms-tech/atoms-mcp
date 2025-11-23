"""In-memory auth adapter for testing.

Provides AuthKit + Bearer token validation using in-memory storage.
"""

from __future__ import annotations

import json
import uuid
import time
import base64
from typing import Any, Dict, Optional

try:
    from ..adapters import AuthAdapter
except ImportError:
    from infrastructure.adapters import AuthAdapter


class InMemoryAuthAdapter(AuthAdapter):
    """Mock AuthKit authentication adapter with Bearer token support.
    
    Supports:
    - Bearer token validation (AuthKit JWT pattern)
    - Session creation and revocation
    - Custom mock users for testing
    - Multiple concurrent sessions
    """
    
    def __init__(self, *, default_user: Optional[Dict[str, Any]] = None):
        """Initialize in-memory auth adapter.
        
        Args:
            default_user: Optional default user info for mock tokens
        """
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._tokens: Dict[str, Dict[str, Any]] = {}  # Bearer token -> user info
        self._revoked_tokens: set = set()
        self._token_counter = 0
        
        # Default mock user (mimics AuthKit user structure)
        # Use valid UUID format for compatibility with database operations
        self._default_user = default_user or {
            "user_id": "12345678-1234-1234-1234-123456789012",
            "email": "mock@example.com",
            "email_verified": True,
            "name": "Mock User",
            "given_name": "Mock",
            "family_name": "User",
        }

    async def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate Bearer token and return user info.
        
        Supports:
        - Session tokens (from create_session)
        - Bearer tokens (mock JWT format)
        - Test tokens (any non-empty string in test mode)
        """
        if not token:
            raise ValueError("Invalid token: empty")
        
        # Check if it's a known session token
        if token in self._sessions:
            session = self._sessions[token]
            if session.get("revoked_at"):
                raise ValueError("Session token has been revoked")
            return session["user_info"]
        
        # Check if it's a known Bearer token
        if token in self._tokens:
            token_data = self._tokens[token]
            if token in self._revoked_tokens:
                raise ValueError("Bearer token has been revoked")
            if token_data.get("expires_at") and token_data["expires_at"] < time.time():
                raise ValueError("Bearer token has expired")
            return token_data["user_info"]
        
        # In mock mode, accept any non-empty token as a valid Bearer token
        # This allows tests to pass custom tokens without pre-registering them
        return {
            **self._default_user,
            "access_token": token,
            "auth_type": "mock_bearer",
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,  # 1 hour expiry
        }

    async def create_session(
        self,
        user_id: str,
        username: str,
        *,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
    ) -> str:
        """Create a new session (returns Bearer token style string).
        
        Args:
            user_id: User identifier from AuthKit
            username: User's email/username
            access_token: Optional Supabase/AuthKit access token
            refresh_token: Optional refresh token
            
        Returns:
            Session Bearer token (can be used for API calls)
        """
        self._token_counter += 1
        session_id = f"session_{self._token_counter}_{uuid.uuid4().hex[:8]}"
        
        user_info = {
            "user_id": user_id,
            "email": username,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "auth_type": "authkit",
            "iat": int(time.time()),
            "exp": int(time.time()) + 86400,  # 24 hour expiry
        }
        
        self._sessions[session_id] = {
            "user_info": user_info,
            "created_at": time.time(),
            "revoked_at": None,
        }
        
        return session_id

    async def revoke_session(self, token: str) -> bool:
        """Revoke a session token.
        
        Args:
            token: Session token to revoke
            
        Returns:
            True if token was revoked, False if not found
        """
        if token in self._sessions:
            self._sessions[token]["revoked_at"] = time.time()
            return True
        if token in self._tokens:
            self._revoked_tokens.add(token)
            return True
        return False

    async def verify_credentials(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Verify username/password credentials (mock implementation).
        
        In mock mode, any non-empty username/password is valid.
        """
        if username and password:
            return {
                "user_id": f"user_{username}_{uuid.uuid4().hex[:8]}",
                "email": username,
                "name": username.split("@")[0],
                "auth_type": "password",
            }
        return None
    
    def _create_bearer_token(self, user_id: str, username: str) -> str:
        """Create a mock Bearer token (JWT-like structure for testing).
        
        Format: base64(header).base64(payload).base64(signature)
        """
        self._token_counter += 1
        token_id = self._token_counter
        
        payload = {
            "user_id": user_id,
            "email": username,
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
            "iss": "mock-authkit",
            "sub": user_id,
        }
        
        # Simulate JWT structure (not cryptographically valid, just for testing)
        header = base64.b64encode(b'{"alg":"HS256","typ":"JWT"}').decode().rstrip("=")
        payload_b64 = base64.b64encode(json.dumps(payload).encode()).decode().rstrip("=")
        signature = base64.b64encode(f"sig_{token_id}".encode()).decode().rstrip("=")
        
        token = f"{header}.{payload_b64}.{signature}"
        
        user_info = {
            "user_id": user_id,
            "email": username,
            "auth_type": "bearer",
            "iat": payload["iat"],
            "exp": payload["exp"],
        }
        
        self._tokens[token] = {
            "user_info": user_info,
            "expires_at": payload["exp"],
        }
        
        return token
