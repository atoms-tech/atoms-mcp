#!/usr/bin/env python3
"""Authenticate with WorkOS/AuthKit and get a real JWT token.

This script helps you get a real AuthKit JWT token by:
1. Authenticating with WorkOS using your credentials
2. Attempting to get an AuthKit token (if WorkOS API supports it)
3. Or providing instructions on how to get one via OAuth flow

Usage:
    python scripts/authenticate_and_get_token.py
    
Environment variables:
    - WORKOS_API_KEY (required)
    - WORKOS_CLIENT_ID (required)
    - ATOMS_TEST_EMAIL (default: kooshapari@kooshapari.com)
    - ATOMS_TEST_PASSWORD (default: ASD3on54_Pax90)
"""

import os
import sys
import asyncio
import httpx
import json
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
        pass  # python-dotenv not available

async def main():
    """Authenticate and get AuthKit token."""
    email = os.getenv("ATOMS_TEST_EMAIL", "kooshapari@kooshapari.com")
    password = os.getenv("ATOMS_TEST_PASSWORD", "ASD3on54_Pax90")
    workos_api_key = os.getenv("WORKOS_API_KEY")
    workos_client_id = os.getenv("WORKOS_CLIENT_ID")
    workos_api_url = os.getenv("WORKOS_API_URL", "https://api.workos.com").strip().rstrip("/")
    
    if not workos_api_key or not workos_client_id:
        print("❌ WORKOS_API_KEY and WORKOS_CLIENT_ID required")
        print("   Set them in your environment or .env file")
        return None
    
    print(f"🔐 Authenticating as: {email}")
    print(f"🔑 Using WorkOS Client ID: {workos_client_id}")
    print()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Step 1: Get or create user
        print("Step 1: Looking up user in WorkOS...")
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
        
        # Step 2: Try to authenticate and get a token
        print("\nStep 2: Attempting to authenticate...")
        
        # WorkOS AuthKit requires OAuth flow, but let's try WorkOS User Management
        # to see if it returns any token we can use
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
            token = auth_data.get("access_token") or auth_data.get("token")
            if token:
                print(f"✅ Got token from WorkOS authentication!")
                print(f"\nToken (first 50 chars): {token[:50]}...")
                print(f"\n✅ Set this as your ATOMS_TEST_AUTH_TOKEN:")
                print(f"export ATOMS_TEST_AUTH_TOKEN=\"{token}\"")
                return token
            else:
                print("⚠️  Authentication succeeded but no token in response")
                print(f"Response: {json.dumps(auth_data, indent=2)}")
        else:
            print(f"⚠️  Authentication failed: {authenticate_response.status_code}")
            print(authenticate_response.text)
        
        # Step 3: AuthKit requires OAuth flow
        print("\n⚠️  AuthKit requires OAuth flow - cannot get token directly")
        print("\nTo get a real AuthKit JWT token:")
        print("1. Visit your AuthKit authorization URL")
        print("2. Complete OAuth login")
        print("3. Extract access_token from the response")
        print("4. Set: export ATOMS_TEST_AUTH_TOKEN=\"your-token\"")
        print("\nOr use:")
        print("- ATOMS_INTERNAL_TOKEN (if configured on server)")
        print("- Unsigned JWT (if ATOMS_TEST_MODE=true on server)")
        
        return None

if __name__ == "__main__":
    token = asyncio.run(main())
    if token:
        sys.exit(0)
    else:
        sys.exit(1)
