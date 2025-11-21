"""Supabase authentication adapter for AuthKit JWTs.

This adapter validates AuthKit JWTs and uses them with Supabase for RLS context.
AuthKit JWTs are validated via FastMCP's JWTVerifier at the server level.
"""

from __future__ import annotations

import os
import logging
import secrets
from typing import Any, Dict, Optional
from dataclasses import dataclass

import jwt as jwt_lib

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
    """Supabase auth adapter for AuthKit JWTs only.

    Validates AuthKit JWTs and extracts user info for Supabase RLS context.
    Note: JWT signature verification happens at the FastMCP server level via JWTVerifier.
    """

    def __init__(self):
        self._sessions: Dict[str, Session] = {}

    async def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate AuthKit JWT token.

        Note: JWT signature verification happens at the FastMCP server level
        via JWTVerifier. This method extracts user info from already-verified tokens.
        
        Uses caching to reduce redundant processing.

        Returns user info including access_token for RLS context.
        """
        # 1. Try cache first (Upstash Redis)
        try:
            from services.auth.token_cache import get_token_cache
            token_cache = await get_token_cache()
            cached_claims = await token_cache.get(token)
            
            if cached_claims:
                logger.debug(f"Token cache hit for user {cached_claims.get('user_id')}")
                return cached_claims
        except Exception as e:
            logger.debug(f"Token cache check failed: {e}")
        
        # 2. Try as internal session token
        if session := self._sessions.get(token):
            result = {
                "user_id": session.user_id,
                "username": session.username,
                "auth_type": "session",
                "access_token": session.access_token
            }
            
            # Cache result
            try:
                from services.auth.token_cache import get_token_cache
                token_cache = await get_token_cache()
                cache_ttl = int(os.getenv("CACHE_TTL_TOKEN", "3600"))
                await token_cache.set(token, result, cache_ttl)
            except Exception as e:
                logger.debug(f"Failed to cache token: {e}")
            
            return result

        # 3. Validate AuthKit JWT - extract user info
        # Note: Signature verification happens at FastMCP server level via JWTVerifier
        try:
            # Decode JWT to extract claims (signature already verified by JWTVerifier)
            decoded = jwt_lib.decode(token, options={"verify_signature": False})
            iss = decoded.get('iss', '')

            # Only accept AuthKit/WorkOS JWTs
            if 'workos' in iss or 'authkit' in iss.lower():
                logger.debug("✅ AuthKit JWT detected")

                # Extract user info from claims
                user_id = decoded.get('sub')  # WorkOS uses 'sub' for user ID
                email = decoded.get('email')
                name = decoded.get('name')
                email_verified = decoded.get('email_verified', False)
                role = decoded.get('role')  # Supabase RLS role claim (should be "authenticated")
                user_role = decoded.get('user_role')  # User's organization role (optional)

                if not user_id:
                    raise ValueError("No 'sub' claim in AuthKit JWT")

                # Log role information for debugging
                if role:
                    logger.debug(f"JWT role claim: {role} (for Supabase RLS)")
                if user_role:
                    logger.debug(f"JWT user_role claim: {user_role} (organization role)")

                logger.info(f"✅ AuthKit JWT validated for: {email} (user_id: {user_id})")

                result = {
                    "user_id": user_id,
                    "username": email or f"user_{user_id}",
                    "auth_type": "authkit_jwt",
                    "user_metadata": {
                        "name": name,
                        "email_verified": email_verified,
                        "role": role,  # Supabase RLS role
                        "user_role": user_role  # Organization role (if present)
                    },
                    "access_token": token  # Use AuthKit JWT directly with Supabase postgrest
                }
                
                # Cache result
                try:
                    from services.auth.token_cache import get_token_cache
                    token_cache = await get_token_cache()
                    cache_ttl = int(os.getenv("CACHE_TTL_TOKEN", "3600"))
                    await token_cache.set(token, result, cache_ttl)
                except Exception as e:
                    logger.debug(f"Failed to cache token: {e}")
                
                return result
            else:
                raise ValueError(f"Unsupported token issuer: {iss}. Only AuthKit/WorkOS JWTs are supported.")

        except Exception as e:
            logger.warning(f"AuthKit JWT validation failed: {str(e)[:200]}")
            raise ValueError(f"Invalid or expired AuthKit JWT: {e}")

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
