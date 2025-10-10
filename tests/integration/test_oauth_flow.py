#!/usr/bin/env python3
"""Test AuthKit OAuth flow to get real session token."""

import asyncio
import os
import sys

# Load environment variables
from dotenv import load_dotenv

load_dotenv()
load_dotenv(".env.local", override=True)

# Add tests to path
sys.path.append("tests")

from tests.auth_helper import automate_oauth_login_with_retry, get_last_flow_result


async def test_oauth():
    """Test OAuth flow and get session token."""

    # Construct OAuth URL
    authkit_domain = os.getenv("FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN", "https://decent-hymn-17-staging.authkit.app")
    client_id = os.getenv("WORKOS_CLIENT_ID")
    base_url = os.getenv("FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL", "https://mcp.atoms.tech")

    if not client_id:
        print("❌ WORKOS_CLIENT_ID not found in environment")
        return False

    import urllib.parse
    redirect_uri = f"{base_url}/auth/callback"
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid profile email"
    }
    oauth_url = f"{authkit_domain}/oauth/authorize?" + urllib.parse.urlencode(params)

    print("🔐 Starting OAuth flow with AuthKit...")
    print(f"OAuth URL: {oauth_url}")
    print(f"Client ID: {client_id}")

    try:
        success = await automate_oauth_login_with_retry(
            oauth_url=oauth_url,
            provider="authkit",
            max_retries=2
        )

        if success:
            flow_result = get_last_flow_result()
            if flow_result:
                print("✅ OAuth successful!")
                print(f"Session token: {getattr(flow_result, 'session_token', 'Not available')}")
                print(f"Flow result: {flow_result}")
                return True
            print("❌ OAuth succeeded but no flow result available")
            return False
        print("❌ OAuth failed")
        return False

    except Exception as e:
        print(f"❌ OAuth error: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_oauth())
    sys.exit(0 if success else 1)
