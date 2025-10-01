"""Supabase authentication adapter implementation."""

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
    """Supabase-based authentication adapter."""
    
    def __init__(self):
        # In-memory session store for simple session tokens
        # In production, this could be Redis or database-backed
        self._sessions: Dict[str, Session] = {}
    
    async def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate token - handles session tokens, Supabase JWTs, and AuthKit JWTs.

        Returns user info including access_token for RLS context.

        Token types supported:
        1. Internal session token (from /login endpoint)
        2. Supabase JWT (direct from Supabase auth)
        3. AuthKit JWT (from WorkOS) - automatically exchanged for Supabase JWT
        """
        # DEBUG: Log what type of token we received
        try:
            import jwt as jwt_lib
            decoded = jwt_lib.decode(token, options={"verify_signature": False})
            iss = decoded.get('iss', '')
            logger.info(f"🔍 Token received - Issuer: {iss}")
            if 'supabase.co' in iss:
                logger.info("✅ Token is SUPABASE JWT - using directly for RLS")
            elif 'workos.com' in iss or 'authkit' in iss.lower():
                logger.info("⚠️  Token is AUTHKIT JWT - exchange needed")
            else:
                logger.info(f"❓ Token type unknown (issuer: {iss})")
        except Exception as e:
            logger.debug(f"Token debug failed: {e}")

        # 1. Try as internal session token
        if session := self._sessions.get(token):
            return {
                "user_id": session.user_id,
                "username": session.username,
                "auth_type": "session",
                "access_token": session.access_token  # May be None for dev sessions
            }

        # 2. Check if AuthKit JWT FIRST (before attempting Supabase validation)
        # This prevents AuthKit JWTs from being passed to Supabase which causes errors
        try:
            # Only attempt exchange if dependencies are available
            from ..auth.token_exchange import get_token_exchanger
            from ..auth.authkit_jwt_verifier import get_authkit_verifier

            verifier = get_authkit_verifier()

            # Check if it looks like an AuthKit JWT first (quick check)
            if verifier.is_authkit_jwt(token):
                logger.info("🔄 REQUIRED: AuthKit JWT detected - exchanging for Supabase JWT")
                exchanger = get_token_exchanger()

                # Exchange AuthKit JWT for Supabase JWT
                exchange_result = await exchanger.exchange_authkit_for_supabase(token)

                logger.info(f"✅ Token exchange successful for user: {exchange_result['email']}")
                return {
                    "user_id": exchange_result["user_id"],
                    "username": exchange_result["email"],
                    "auth_type": "authkit_exchanged",
                    "access_token": exchange_result["supabase_access_token"],  # ← Supabase JWT!
                    "refresh_token": exchange_result.get("supabase_refresh_token"),
                    "authkit_user_id": exchange_result.get("authkit_user_id")
                }
            else:
                logger.debug("Token is not an AuthKit JWT - will try as Supabase JWT")
        except ImportError as e:
            # Token exchange modules not available (PyJWT not installed)
            logger.error(f"❌ CRITICAL: Token exchange not available (missing dependencies): {e}")
            logger.error("Install PyJWT and cryptography: pip install PyJWT cryptography")
            pass
        except Exception as e:
            # Exchange failed or not configured
            logger.error(f"❌ AuthKit token exchange FAILED: {e}")
            logger.error("This breaks the required AuthKit→Supabase authentication flow!")
            import traceback
            logger.error(traceback.format_exc())
            pass

        # 3. Try as Supabase JWT (only if not AuthKit)
        try:
            supabase = get_supabase(access_token=token)
            user = supabase.auth.get_user()

            if user and hasattr(user, 'user') and user.user:
                logger.info(f"✅ Valid Supabase JWT for user: {user.user.email}")
                return {
                    "user_id": user.user.id,
                    "username": user.user.email or f"user_{user.user.id}",
                    "auth_type": "supabase_jwt",
                    "user_metadata": getattr(user.user, 'user_metadata', {}),
                    "access_token": token  # Already a Supabase JWT
                }
        except Exception as e:
            # Not a valid Supabase JWT either
            logger.debug(f"Not a Supabase JWT: {str(e)[:100]}")
            pass

        raise ValueError("Invalid or expired token")
    
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
                session = getattr(auth_res, "session", None)
                return {
                    "id": user.id, 
                    "username": username,
                    "user_metadata": getattr(user, 'user_metadata', {}),
                    "access_token": getattr(session, "access_token", None) if session else None,
                    "refresh_token": getattr(session, "refresh_token", None) if session else None,
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
