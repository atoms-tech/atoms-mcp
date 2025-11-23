"""Shared JWT token validation utilities.

Consolidates common JWT decoding and validation logic used across:
- tools/base.py - Tool-level auth validation
- auth/session_middleware.py - Middleware-level session extraction
- infrastructure/auth_composite.py - HTTP transport layer validation
- infrastructure/mock_adapters.py - Mock/test validation
"""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def decode_jwt_claims(token: str, verify_signature: bool = False) -> Dict[str, Any]:
    """Decode JWT token and return claims.
    
    Args:
        token: JWT token string
        verify_signature: Whether to verify signature (default: False)
        
    Returns:
        Dictionary of JWT claims
        
    Raises:
        ValueError: If token cannot be decoded
    """
    try:
        import jwt
        return jwt.decode(token, options={"verify_signature": verify_signature})
    except Exception as e:
        logger.warning(f"Failed to decode JWT: {e}")
        raise ValueError(f"Invalid JWT token: {e}") from e


def extract_user_id(claims: Dict[str, Any]) -> Optional[str]:
    """Extract user ID from JWT claims.
    
    Tries multiple claim names in order:
    1. 'sub' (standard JWT claim)
    2. 'user_id' (custom claim)
    3. 'id' (alternative)
    4. 'user.id' (nested user object)
    5. 'uid' (Supabase uses 'uid' in some contexts)
    
    Args:
        claims: JWT claims dictionary
        
    Returns:
        User ID string or None if not found
    """
    # Try standard JWT claim first
    user_id = claims.get('sub')
    if user_id:
        return str(user_id)
    
    # Try custom claims
    user_id = claims.get('user_id') or claims.get('id') or claims.get('uid')
    if user_id:
        return str(user_id)
    
    # Try nested user object
    user_obj = claims.get('user', {})
    if isinstance(user_obj, dict):
        user_id = user_obj.get('id')
        if user_id:
            return str(user_id)
    
    return None


def extract_user_info(claims: Dict[str, Any], token: str) -> Dict[str, Any]:
    """Extract user information from JWT claims.
    
    Args:
        claims: JWT claims dictionary
        token: Original JWT token string (for RLS context)
        
    Returns:
        Dictionary with user_id, username, email, auth_type, access_token
    """
    user_id = extract_user_id(claims)
    
    return {
        "user_id": user_id,
        "username": claims.get("email") or claims.get("username"),
        "email": claims.get("email"),
        "auth_type": "authkit_jwt",
        "access_token": token,  # Pass token to Supabase for RLS
        "user_metadata": {
            "role": claims.get("role"),
            "org_id": claims.get("org_id"),
            "email_verified": claims.get("email_verified"),
        }
    }


def is_token_expired(claims: Dict[str, Any]) -> bool:
    """Check if JWT token is expired.
    
    Args:
        claims: JWT claims dictionary
        
    Returns:
        True if token is expired, False otherwise
    """
    import time
    
    if "exp" not in claims:
        return False  # No expiry claim, assume not expired
    
    exp_timestamp = claims["exp"]
    current_time = int(time.time())
    
    return exp_timestamp < current_time


def get_token_expiry_info(claims: Dict[str, Any]) -> Dict[str, Any]:
    """Get token expiry information.
    
    Args:
        claims: JWT claims dictionary
        
    Returns:
        Dictionary with expiry information:
        - expires_at: Unix timestamp
        - expires_in_seconds: Seconds until expiry (negative if expired)
        - is_expired: Boolean
        - expires_in_minutes: Minutes until expiry (for display)
    """
    import time
    
    current_time = int(time.time())
    expires_at = claims.get("exp")
    
    if expires_at is None:
        return {
            "expires_at": None,
            "expires_in_seconds": None,
            "is_expired": False,
            "expires_in_minutes": None,
        }
    
    expires_in_seconds = expires_at - current_time
    expires_in_minutes = max(0, expires_in_seconds // 60)
    
    return {
        "expires_at": expires_at,
        "expires_in_seconds": expires_in_seconds,
        "is_expired": expires_in_seconds < 0,
        "expires_in_minutes": expires_in_minutes,
    }
