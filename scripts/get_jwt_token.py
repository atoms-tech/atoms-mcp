#!/usr/bin/env python3
"""Get JWT token from WorkOS credentials and output to stdout.

This script authenticates with WorkOS User Management using email/password
and outputs the JWT access token to stdout (for use in scripts/pipes).

Usage:
    python scripts/get_jwt_token.py
    TOKEN=$(python scripts/get_jwt_token.py)
    
Environment variables:
    - WORKOS_API_KEY (required)
    - WORKOS_CLIENT_ID (required)
    - ATOMS_TEST_EMAIL (optional, defaults to kooshapari@kooshapari.com)
    - ATOMS_TEST_PASSWORD (optional, defaults to ASD3on54_Pax90)
    - WORKOS_API_URL (optional, defaults to https://api.workos.com)

Exit codes:
    0: Success (token printed to stdout)
    1: Error (error message printed to stderr)
"""

import os
import sys
import asyncio
import httpx
from pathlib import Path

# Load .env file if it exists
env_file = Path(".env")
if env_file.exists():
    try:
        from dotenv import dotenv_values
        env_vars = dotenv_values(".env")
        for k, v in env_vars.items():
            if v and k not in os.environ:
                os.environ[k] = v
    except ImportError:
        pass


async def get_jwt_token() -> str | None:
    """Authenticate with WorkOS and get JWT access token.
    
    Returns:
        JWT token string if successful, None otherwise
    """
    email = os.getenv("ATOMS_TEST_EMAIL", "kooshapari@kooshapari.com")
    password = os.getenv("ATOMS_TEST_PASSWORD", "ASD3on54_Pax90")
    workos_api_key = os.getenv("WORKOS_API_KEY")
    workos_client_id = os.getenv("WORKOS_CLIENT_ID")
    workos_api_url = os.getenv("WORKOS_API_URL", "https://api.workos.com").strip().rstrip("/")
    
    if not workos_api_key or not workos_client_id:
        print("❌ WORKOS_API_KEY and WORKOS_CLIENT_ID required", file=sys.stderr)
        return None
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Try WorkOS User Management authenticate endpoint
            response = await client.post(
                f"{workos_api_url}/user_management/authenticate",
                json={
                    "client_id": workos_client_id,
                    "client_secret": workos_api_key,
                    "grant_type": "password",
                    "email": email,
                    "password": password,
                },
                headers={"Content-Type": "application/json"},
            )
            
            if response.status_code == 200:
                data = response.json()
                access_token = data.get("access_token")
                if access_token:
                    return access_token
                else:
                    print(
                        f"❌ No access_token in response: {list(data.keys())}",
                        file=sys.stderr
                    )
                    return None
            else:
                # Try WorkOS Python SDK as fallback
                try:
                    from workos import WorkOSClient
                    workos_client = WorkOSClient(api_key=workos_api_key)
                    
                    if hasattr(workos_client.user_management, 'authenticate_with_password'):
                        auth_result = workos_client.user_management.authenticate_with_password(
                            email=email,
                            password=password,
                        )
                        
                        # Extract token from result
                        if hasattr(auth_result, 'access_token'):
                            return auth_result.access_token
                        elif hasattr(auth_result, 'token'):
                            return auth_result.token
                        elif hasattr(auth_result, '__dict__'):
                            result_dict = auth_result.__dict__
                            return result_dict.get('access_token') or result_dict.get('token')
                except ImportError:
                    pass
                except Exception as e:
                    print(f"⚠️  WorkOS SDK fallback failed: {e}", file=sys.stderr)
                
                print(
                    f"❌ Authentication failed ({response.status_code}): {response.text[:200]}",
                    file=sys.stderr
                )
                return None
                
    except httpx.RequestError as e:
        print(f"❌ Request error: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        return None


def main():
    """Main entry point - outputs token to stdout or error to stderr."""
    token = asyncio.run(get_jwt_token())
    if token:
        print(token, end='')
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
