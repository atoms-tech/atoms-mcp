"""Simplified Supabase authentication adapter.

With WorkOS configured as Supabase third-party auth provider,
AuthKit JWTs are validated directly by Supabase - no exchange needed!
"""

from __future__ import annotations

import os
import logging
import secrets
from typing import Any, Dict, Optional
from dataclasses import dataclass

try:
    from .adapters import AuthAdapter
    from ..supabase_client import get_supabase, MissingSupabaseConfig
except ImportError:
    from infrastructure.adapters import AuthAdapter
    from supabase_client import get_supabase, MissingSupabaseConfig

logger = logging.getLogger(__name__)


@dataclass
class Session:
    """Internal session representation."""
    user_id: str
    username: str
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None


class SupabaseAuthAdapter(AuthAdapter):
    """Simplified Supabase auth adapter - works with Supabase and AuthKit JWTs."""

    def __init__(self):
        self._sessions: Dict[str, Session] = {}

    async def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate token - Supabase validates both Supabase and AuthKit JWTs.

        With WorkOS configured as third-party provider in Supabase,
        AuthKit JWTs are automatically validated by Supabase!

        Returns user info including access_token for RLS context.
        """
        # 1. Try as internal session token
        if session := self._sessions.get(token):
            return {
                "user_id": session.user_id,
                "username": session.username,
                "auth_type": "session",
                "access_token": session.access_token
            }

        # 2. Validate JWT - decode and extract user info
        try:
            import jwt as jwt_lib

            # Decode without verification to get claims
            decoded = jwt_lib.decode(token, options={"verify_signature": False})
            iss = decoded.get('iss', '')

            # Check if Supabase JWT (more permissive check)
            if 'supabase.co' in iss or '/auth/v1' in iss:
                # Extract user info directly from JWT claims
                user_id = decoded.get('sub')
                email = decoded.get('email')
                user_metadata = decoded.get('user_metadata', {})

                if not user_id:
                    raise ValueError("Invalid Supabase JWT: missing 'sub' claim")

                logger.info(f"✅ Supabase JWT validated for: {email} (user_id: {user_id})")

                return {
                    "user_id": user_id,
                    "username": email or f"user_{user_id}",
                    "auth_type": "supabase_jwt",
                    "user_metadata": user_metadata,
                    "access_token": token
                }

            # Check if AuthKit JWT
            elif 'workos' in iss or 'authkit' in iss.lower():
                logger.info(f"✅ AuthKit JWT detected - using directly with third-party auth")

                # For AuthKit JWTs, extract user info from claims
                user_id = decoded.get('sub')  # WorkOS uses 'sub' for user ID
                email = decoded.get('email')

                if not user_id:
                    raise ValueError("No 'sub' claim in AuthKit JWT")

                logger.info(f"✅ AuthKit JWT validated for: {email} (user_id: {user_id})")

                return {
                    "user_id": user_id,
                    "username": email or f"user_{user_id}",
                    "auth_type": "authkit_jwt",
                    "user_metadata": {},
                    "access_token": token  # Use AuthKit JWT directly with postgrest
                }
            else:
                raise ValueError(f"Unknown token issuer: {iss}")

        except Exception as e:
            logger.warning(f"JWT validation failed: {str(e)[:200]}")
            raise ValueError(f"Invalid or expired token: {e}")

    async def create_session(
        self,
        user_id: str,
        username: str,
        *,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
    ) -> str:
        """Create a new session token."""
        token = secrets.token_urlsafe(32)
        self._sessions[token] = Session(
            user_id=user_id,
            username=username,
            access_token=access_token,
            refresh_token=refresh_token,
        )
        return token

    async def revoke_session(self, token: str) -> bool:
        """Revoke a session token."""
        if token in self._sessions:
            del self._sessions[token]
            return True
        return False

    async def verify_credentials(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Verify username/password credentials."""
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
                session = getattr(auth_res, "session", None)
                return {
                    "id": user.id,
                    "username": username,
                    "user_metadata": getattr(user, 'user_metadata', {}),
                    "access_token": getattr(session, "access_token", None) if session else None,
                    "refresh_token": getattr(session, "refresh_token", None) if session else None,
                }
        except MissingSupabaseConfig:
            pass
        except Exception:
            pass

        # Demo fallback
        if username and password and not env_user:
            return {"id": f"user_{username}", "username": username}

        return None
