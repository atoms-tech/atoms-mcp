#!/usr/bin/env python3
"""Generate valid AuthKit tokens for testing.

This script generates JWT-compatible tokens that can be used for integration testing
without going through the full OAuth flow. Tokens can be passed as Bearer tokens to
the MCP server.

IMPORTANT: Unsigned tokens (alg: "none") only work when:
  1. ATOMS_TEST_MODE=true environment variable is set
  2. The MCP server uses HybridAuthProvider with unsigned JWT verification enabled

Usage:
    # Generate token for specific user
    python scripts/generate_authkit_token.py \
        --email kooshapari@kooshapari.com \
        --name "Test User" \
        --duration 3600  # 1 hour

    # Output as environment variable (for CI/CD)
    python scripts/generate_authkit_token.py --output env
    
    # Output as JSON
    python scripts/generate_authkit_token.py --output json
    
    # Decode token to see claims
    python scripts/generate_authkit_token.py --decode
    
    # Or with environment variables:
    export AUTHKIT_EMAIL="kooshapari@kooshapari.com"
    export AUTHKIT_USER_ID="test-user-id"
    export AUTHKIT_TOKEN_DURATION="3600"
    python scripts/generate_authkit_token.py

Integration Testing:
    # For integration tests, set ATOMS_TEST_MODE in your environment
    export ATOMS_TEST_MODE=true
    export ATOMS_TEST_AUTH_TOKEN=$(python scripts/generate_authkit_token.py)
    
    # Then run integration tests
    python cli.py test run --scope integration --env prod

System Requirements:
    - Python 3.10+
    - No external dependencies (uses only stdlib: base64, json, uuid, time)
"""

import json
import base64
import time
import sys
import os
import uuid
from typing import Dict, Any
import argparse


def create_unsigned_jwt(claims: Dict[str, Any]) -> str:
    """Create an unsigned JWT token (valid only in test mode).
    
    Unsigned tokens use alg: "none" and are only accepted when ATOMS_TEST_MODE=true.
    
    Args:
        claims: JWT payload claims
        
    Returns:
        JWT token string in format: header.payload.signature
    """
    # Create header
    header = {"alg": "none", "typ": "JWT"}
    header_b64 = base64.urlsafe_b64encode(
        json.dumps(header).encode()
    ).decode().rstrip("=")
    
    # Create payload
    payload_b64 = base64.urlsafe_b64encode(
        json.dumps(claims).encode()
    ).decode().rstrip("=")
    
    # No signature for unsigned JWT (empty string)
    signature = ""
    
    return f"{header_b64}.{payload_b64}.{signature}"


def create_authkit_compatible_jwt(
    email: str,
    user_id: str = None,
    name: str = None,
    duration_seconds: int = 3600
) -> str:
    """Create an AuthKit-compatible JWT token.
    
    This generates a token that mimics AuthKit's JWT structure and can be used
    to test the MCP server's authentication without going through WorkOS.
    
    Args:
        email: User email address
        user_id: Unique user ID (auto-generated if not provided)
        name: User's full name
        duration_seconds: Token expiration duration in seconds (default: 1 hour)
        
    Returns:
        JWT token that can be passed as Bearer token
    """
    now = int(time.time())
    user_id = user_id or str(uuid.uuid4())
    
    # Create JWT claims matching AuthKit/FastMCP structure
    claims = {
        "sub": user_id,  # Subject (user ID)
        "email": email,
        "email_verified": True,
        "aud": "fastmcp-mcp-server",  # Audience (our MCP server)
        "iss": "authkit-test-generator",  # Issuer
        "iat": now,  # Issued at
        "exp": now + duration_seconds,  # Expiration
        "name": name or email.split("@")[0],
        "given_name": name.split()[0] if name else email.split("@")[0],
        "family_name": name.split()[-1] if name and len(name.split()) > 1 else "",
    }
    
    # Remove empty fields
    claims = {k: v for k, v in claims.items() if v}
    
    return create_unsigned_jwt(claims)


def create_bearer_token_headers(token: str) -> Dict[str, str]:
    """Create HTTP headers with Bearer token."""
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }


def main():
    """CLI interface for token generation."""
    parser = argparse.ArgumentParser(
        description="Generate AuthKit test tokens for MCP server integration tests"
    )
    parser.add_argument(
        "--email",
        default=os.getenv("AUTHKIT_EMAIL", "kooshapari@kooshapari.com"),
        help="User email address (env: AUTHKIT_EMAIL)"
    )
    parser.add_argument(
        "--user-id",
        default=os.getenv("AUTHKIT_USER_ID"),
        help="User ID (auto-generated if not provided, env: AUTHKIT_USER_ID)"
    )
    parser.add_argument(
        "--name",
        default=os.getenv("AUTHKIT_NAME"),
        help="User's full name (env: AUTHKIT_NAME)"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=int(os.getenv("AUTHKIT_TOKEN_DURATION", "3600")),
        help="Token duration in seconds (default: 3600, env: AUTHKIT_TOKEN_DURATION)"
    )
    parser.add_argument(
        "--output",
        choices=["token", "headers", "env", "json"],
        default="token",
        help="Output format (default: token)"
    )
    parser.add_argument(
        "--decode",
        action="store_true",
        help="Decode and display token claims"
    )
    
    args = parser.parse_args()
    
    # Generate token
    token = create_authkit_compatible_jwt(
        email=args.email,
        user_id=args.user_id,
        name=args.name,
        duration_seconds=args.duration
    )
    
    # Decode if requested
    if args.decode:
        parts = token.split(".")
        if len(parts) == 3:
            try:
                payload_b64 = parts[1]
                # Add padding if needed
                padding = 4 - (len(payload_b64) % 4)
                if padding != 4:
                    payload_b64 += "=" * padding
                payload_json = base64.urlsafe_b64decode(payload_b64).decode()
                claims = json.loads(payload_json)
                print("Token Claims:")
                print(json.dumps(claims, indent=2))
                print()
            except Exception as e:
                print(f"Error decoding token: {e}", file=sys.stderr)
    
    # Output in requested format
    if args.output == "token":
        print(token)
    elif args.output == "headers":
        headers = create_bearer_token_headers(token)
        print(json.dumps(headers, indent=2))
    elif args.output == "env":
        print(f"ATOMS_TEST_AUTH_TOKEN={token}")
    elif args.output == "json":
        print(json.dumps({
            "token": token,
            "email": args.email,
            "user_id": args.user_id or "auto-generated",
            "duration_seconds": args.duration,
            "expires_at": int(time.time()) + args.duration
        }, indent=2))
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
