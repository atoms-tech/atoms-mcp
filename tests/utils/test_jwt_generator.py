"""Generate test JWTs with proper scopes for E2E tests.

This creates self-signed JWTs that the MCP server will accept for testing.
Used when real WorkOS tokens don't have proper scopes.
"""

import jwt
import time
import os
from typing import Optional, Dict, Any


def create_test_jwt(
    user_id: str = "test-user-123",
    email: str = "test@example.com",
    scopes: Optional[list] = None,
    expires_in: int = 3600,
) -> str:
    """Create a test JWT with proper scopes for MCP server.

    Args:
        user_id: User ID (sub claim)
        email: User email
        scopes: List of scopes (defaults to required scopes)
        expires_in: Token lifetime in seconds

    Returns:
        Signed JWT token string
    """
    if scopes is None:
        # Default scopes that MCP server expects
        scopes = [
            "entity:read",
            "entity:write",
            "relationship:read",
            "relationship:write",
            "workspace:read",
            "workflow:execute",
        ]

    now = int(time.time())
    
    payload = {
        "sub": user_id,
        "email": email,
        "iat": now,
        "exp": now + expires_in,
        "iss": "https://test.example.com",
        "aud": "mcp-test",
        "scope": " ".join(scopes),  # Scopes as space-separated string
        "scopes": scopes,  # Also include as array for flexibility
    }

    # Use a test secret - this is NOT secure, only for testing
    # In real scenario, server would verify against WorkOS public keys
    secret = os.getenv("TEST_JWT_SECRET", "test-secret-do-not-use-in-prod")
    
    token = jwt.encode(payload, secret, algorithm="HS256")
    return token


def create_admin_jwt(
    user_id: str = "admin-123",
    email: str = "admin@example.com",
) -> str:
    """Create an admin test JWT with all scopes.

    Args:
        user_id: Admin user ID
        email: Admin email

    Returns:
        Admin JWT token
    """
    # Admin has all scopes
    all_scopes = [
        "entity:read",
        "entity:write",
        "entity:delete",
        "relationship:read",
        "relationship:write",
        "relationship:delete",
        "workspace:read",
        "workspace:write",
        "workflow:execute",
        "admin:read",
        "admin:write",
    ]
    
    return create_test_jwt(user_id, email, all_scopes)


def verify_test_jwt(token: str) -> Dict[str, Any]:
    """Verify and decode a test JWT.

    Args:
        token: JWT token string

    Returns:
        Decoded payload dictionary

    Raises:
        jwt.InvalidTokenError: If token is invalid or expired
    """
    secret = os.getenv("TEST_JWT_SECRET", "test-secret-do-not-use-in-prod")
    
    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            audience="mcp-test"
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise jwt.InvalidTokenError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise jwt.InvalidTokenError(f"Invalid token: {e}")
