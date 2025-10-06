"""Pytest configuration and shared fixtures."""

import os
import sys
import pytest
import pytest_asyncio
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env files
from dotenv import load_dotenv
load_dotenv()
load_dotenv(".env.local", override=True)


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (require server running)"
    )
    config.addinivalue_line(
        "markers", "http: marks tests that call MCP via HTTP"
    )


@pytest.fixture(scope="session")
def check_server_running():
    """Check if MCP server is running on localhost:8000."""
    import httpx

    try:
        response = httpx.get("http://127.0.0.1:8000/health", timeout=2.0)
        if response.status_code == 200:
            return True
    except:
        pass

    pytest.skip("MCP server not running on http://127.0.0.1:8000")


@pytest.fixture(scope="session")
def shared_supabase_jwt():
    """Get Supabase JWT once and reuse to avoid rate limits."""
    from supabase import create_client

    url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    key = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

    if not url or not key:
        pytest.skip("Supabase not configured")

    client = create_client(url, key)

    # Try to reuse existing session first
    try:
        auth_response = client.auth.sign_in_with_password({
            "email": "kooshapari@kooshapari.com",
            "password": "118118"
        })

        if auth_response.session:
            return auth_response.session.access_token
    except Exception as e:
        pytest.skip(f"Could not authenticate: {e}")

    pytest.skip("No session obtained")
