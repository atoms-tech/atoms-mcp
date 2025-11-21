#!/usr/bin/env python3
"""Get AuthKit JWT token via direct email/password authentication.

This script authenticates directly with WorkOS User Management using
email/password credentials and attempts to get a JWT token for bearer auth.

Usage:
    python scripts/get_authkit_token_direct.py
    
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


async def get_token_direct():
    """Authenticate directly with WorkOS using email/password and get JWT token."""
    email = os.getenv("ATOMS_TEST_EMAIL", "kooshapari@kooshapari.com")
    password = os.getenv("ATOMS_TEST_PASSWORD", "ASD3on54_Pax90")
    workos_api_key = os.getenv("WORKOS_API_KEY")
    workos_client_id = os.getenv("WORKOS_CLIENT_ID")
    workos_api_url = os.getenv("WORKOS_API_URL", "https://api.workos.com").strip().rstrip("/")
    
    if not workos_api_key or not workos_client_id:
        print("❌ WORKOS_API_KEY and WORKOS_CLIENT_ID required")
        return None
    
    print(f"🔐 Authenticating directly as: {email}")
    print(f"🔑 Client ID: {workos_client_id}")
    print()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Step 1: Get or create user
        print("Step 1: Looking up user...")
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
        
        # Step 2: Authenticate with password using WorkOS User Management
        # Try the authenticate endpoint
        print(f"\nStep 2: Authenticating with password...")
        
        # Method 1: Try authenticate endpoint (if it exists)
        authenticate_response = await client.post(
            f"{workos_api_url}/user_management/authenticate",
            json={
                "email": email,
                "password": password,
                "client_id": workos_client_id,
            },
            headers={
                "Authorization": f"Bearer {workos_api_key}",
                "Content-Type": "application/json",
            },
        )
        
        if authenticate_response.status_code == 200:
            auth_data = authenticate_response.json()
            token = auth_data.get("access_token") or auth_data.get("token") or auth_data.get("accessToken")
            if token:
                print(f"✅ Got token from authenticate endpoint!")
                print(f"\nToken (first 50 chars): {token[:50]}...")
                print(f"\n✅ Set this as your ATOMS_TEST_AUTH_TOKEN:")
                print(f"export ATOMS_TEST_AUTH_TOKEN=\"{token}\"")
                return token
            else:
                print(f"⚠️  Authentication succeeded but no token in response")
                print(f"Response keys: {list(auth_data.keys())}")
                print(f"Response: {auth_data}")
        
        # Method 2: Try user-specific authenticate endpoint
        print(f"\nTrying user-specific authenticate endpoint...")
        user_auth_response = await client.post(
            f"{workos_api_url}/user_management/users/{user_id}/authenticate",
            json={"password": password},
            headers={
                "Authorization": f"Bearer {workos_api_key}",
                "Content-Type": "application/json",
            },
        )
        
        if user_auth_response.status_code == 200:
            auth_data = user_auth_response.json()
            token = auth_data.get("access_token") or auth_data.get("token") or auth_data.get("session_token")
            if token:
                print(f"✅ Got token from user authenticate endpoint!")
                print(f"\nToken (first 50 chars): {token[:50]}...")
                print(f"\n✅ Set this as your ATOMS_TEST_AUTH_TOKEN:")
                print(f"export ATOMS_TEST_AUTH_TOKEN=\"{token}\"")
                return token
            else:
                print(f"⚠️  Authentication succeeded but no token in response")
                print(f"Response keys: {list(auth_data.keys())}")
                print(f"Response: {auth_data}")
        
        # Method 3: Try WorkOS Python SDK (if available)
        try:
            from workos import WorkOSClient
            workos_client = WorkOSClient(api_key=workos_api_key)
            
            print(f"\nTrying WorkOS Python SDK...")
            
            # Check available methods
            um_methods = [m for m in dir(workos_client.user_management) if not m.startswith('_')]
            print(f"Available User Management methods: {um_methods[:10]}")
            
            # Try different authentication methods
            auth_result = None
            token = None
            
            # Method 3a: Try authenticate_with_password (if exists)
            if hasattr(workos_client.user_management, 'authenticate_with_password'):
                print("Trying authenticate_with_password...")
                try:
                    # Try with just email and password first
                    auth_result = workos_client.user_management.authenticate_with_password(
                        email=email,
                        password=password,
                    )
                    print("✅ authenticate_with_password succeeded!")
                except Exception as e:
                    print(f"authenticate_with_password failed: {e}")
                    # Try with client_id if first attempt failed
                    try:
                        auth_result = workos_client.user_management.authenticate_with_password(
                            email=email,
                            password=password,
                            client_id=workos_client_id,
                        )
                        print("✅ authenticate_with_password succeeded with client_id!")
                    except Exception as e2:
                        print(f"authenticate_with_password with client_id also failed: {e2}")
            
            # Method 3b: Try authenticate_with_email_and_password (if exists)
            if not auth_result and hasattr(workos_client.user_management, 'authenticate_with_email_and_password'):
                print("Trying authenticate_with_email_and_password...")
                try:
                    auth_result = workos_client.user_management.authenticate_with_email_and_password(
                        email=email,
                        password=password,
                        client_id=workos_client_id,
                    )
                except Exception as e:
                    print(f"authenticate_with_email_and_password failed: {e}")
            
            # Extract token from result
            if auth_result:
                print(f"Auth result type: {type(auth_result)}")
                print(f"Auth result attributes: {[a for a in dir(auth_result) if not a.startswith('_')]}")
                
                # Try different ways to get token
                if hasattr(auth_result, 'access_token'):
                    token = auth_result.access_token
                elif hasattr(auth_result, 'token'):
                    token = auth_result.token
                elif hasattr(auth_result, 'accessToken'):
                    token = auth_result.accessToken
                elif hasattr(auth_result, 'user'):
                    user = auth_result.user
                    if hasattr(user, 'access_token'):
                        token = user.access_token
                    elif hasattr(user, 'token'):
                        token = user.token
                
                # Check if result is a dict-like object
                if not token and hasattr(auth_result, '__dict__'):
                    result_dict = auth_result.__dict__
                    token = result_dict.get('access_token') or result_dict.get('token')
            
            if token:
                print(f"✅ Got token via WorkOS SDK!")
                print(f"\nToken (first 50 chars): {token[:50]}...")
                print(f"\n✅ Set this as your ATOMS_TEST_AUTH_TOKEN:")
                print(f"export ATOMS_TEST_AUTH_TOKEN=\"{token}\"")
                return token
            else:
                print(f"⚠️  SDK authentication succeeded but no token found")
                if auth_result:
                    print(f"Result: {auth_result}")
        except ImportError:
            print("WorkOS Python SDK not available")
        except AttributeError as e:
            print(f"WorkOS SDK method not available: {e}")
        except Exception as e:
            print(f"WorkOS SDK authentication failed: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"\n❌ Could not get token via direct authentication")
        print(f"WorkOS AuthKit requires OAuth flow for JWT tokens.")
        print(f"Use scripts/get_authkit_token_oauth.py for OAuth flow instead.")
        return None


if __name__ == "__main__":
    token = asyncio.run(get_token_direct())
    if token:
        sys.exit(0)
    else:
        sys.exit(1)
