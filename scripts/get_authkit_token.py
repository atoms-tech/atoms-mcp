#!/usr/bin/env python3
"""Get a real AuthKit JWT token by authenticating with WorkOS.

This script authenticates with WorkOS using email/password and attempts
to get an AuthKit JWT token for E2E testing.

Usage:
    python scripts/get_authkit_token.py
    
Environment variables required:
    - WORKOS_API_KEY
    - WORKOS_CLIENT_ID
    - ATOMS_TEST_EMAIL (default: kooshapari@kooshapari.com)
    - ATOMS_TEST_PASSWORD (default: ASD3on54_Pax90)
"""

import os
import sys
import asyncio
import httpx
import json

async def get_authkit_token():
    """Authenticate with WorkOS and get AuthKit JWT token."""
    email = os.getenv("ATOMS_TEST_EMAIL", "kooshapari@kooshapari.com")
    password = os.getenv("ATOMS_TEST_PASSWORD", "ASD3on54_Pax90")
    workos_api_key = os.getenv("WORKOS_API_KEY")
    workos_client_id = os.getenv("WORKOS_CLIENT_ID")
    workos_api_url = os.getenv("WORKOS_API_URL", "https://api.workos.com").strip().rstrip("/")
    
    if not workos_api_key or not workos_client_id:
        print("❌ WORKOS_API_KEY and WORKOS_CLIENT_ID required")
        return None
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Step 1: Get or create user
        print(f"🔍 Looking up user: {email}")
        users_response = await client.get(
            f"{workos_api_url}/user_management/users",
            params={"email": email},
            headers={
                "Authorization": f"Bearer {workos_api_key}",
                "Content-Type": "application/json",
            },
        )
        
        user_id = None
        if users_response.status_code == 200:
            users_data = users_response.json()
            users_list = users_data.get("data", [])
            
            if users_list:
                user_id = users_list[0].get("id")
                print(f"✅ Found user: {user_id}")
            else:
                print(f"📝 Creating user: {email}")
                create_response = await client.post(
                    f"{workos_api_url}/user_management/users",
                    json={
                        "email": email,
                        "password": password,
                        "email_verified": True,
                    },
                    headers={
                        "Authorization": f"Bearer {workos_api_key}",
                        "Content-Type": "application/json",
                    },
                )
                
                if create_response.status_code == 201:
                    user_data = create_response.json()
                    user_id = user_data.get("id")
                    print(f"✅ Created user: {user_id}")
                else:
                    print(f"❌ Failed to create user: {create_response.status_code}")
                    print(create_response.text)
                    return None
        
        if not user_id:
            print("❌ Could not get or create user")
            return None
        
        # Step 2: Authenticate with password to get token
        print(f"\n🔐 Authenticating user {user_id} with password...")
        authenticate_response = await client.post(
            f"{workos_api_url}/user_management/users/{user_id}/authenticate",
            json={"password": password},
            headers={
                "Authorization": f"Bearer {workos_api_key}",
                "Content-Type": "application/json",
            },
        )
        
        if authenticate_response.status_code == 200:
            auth_data = authenticate_response.json()
            
            # Try to extract token from various possible fields
            token = (
                auth_data.get("access_token") or
                auth_data.get("token") or
                auth_data.get("session_token") or
                auth_data.get("jwt") or
                auth_data.get("id_token") or
                (auth_data.get("session", {}) or {}).get("access_token") or
                (auth_data.get("session", {}) or {}).get("token")
            )
            
            if token:
                print(f"✅ Got token from WorkOS authentication!")
                
                # Validate it's a JWT (has 3 parts separated by dots)
                if isinstance(token, str) and len(token.split(".")) == 3:
                    print(f"✅ Token is a valid JWT format")
                    print(f"\nToken (first 50 chars): {token[:50]}...")
                    print(f"\n💡 Set this as your ATOMS_TEST_AUTH_TOKEN:")
                    print(f"export ATOMS_TEST_AUTH_TOKEN=\"{token}\"")
                    return token
                else:
                    print(f"⚠️  Token doesn't appear to be a JWT")
                    print(f"Token: {token[:100]}...")
            else:
                print("⚠️  Authentication succeeded but no token in response")
                print(f"Response keys: {list(auth_data.keys())}")
                print(f"Response: {json.dumps(auth_data, indent=2)}")
        else:
            print(f"❌ Authentication failed: {authenticate_response.status_code}")
            print(authenticate_response.text)
        
        # If we get here, authentication didn't return a token
        print("\n⚠️  WorkOS User Management API authentication doesn't return JWT tokens directly.")
        print("   AuthKit JWTs require OAuth flow.")
        print("\n   Options:")
        print("   1. Use OAuth flow: python scripts/get_authkit_token_oauth.py")
        print("   2. Use ATOMS_INTERNAL_TOKEN (if configured on server)")
        print("   3. Use unsigned JWT (if ATOMS_TEST_MODE=true on server)")
        
        return None

if __name__ == "__main__":
    token = asyncio.run(get_authkit_token())
    if token:
        print(f"\n✅ AuthKit Token:\n{token}")
        sys.exit(0)
    else:
        print("\n❌ Could not get AuthKit token")
        sys.exit(1)
