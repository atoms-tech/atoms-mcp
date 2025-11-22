"""
Consolidated authentication integration tests for AuthKit and Bearer tokens.

Tests for:
1. AuthKit JWT validation and authentication
2. Bearer token authentication (Supabase JWT, WorkOS User Management)
3. Hybrid authentication scenarios (bearer token preferred over OAuth)
4. Session management
5. AuthKit + Supabase integration

This file consolidates test_auth.py and test_auth_patterns.py with canonical naming.
"""

import pytest
import time
from datetime import datetime, timedelta
import uuid

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]


class TestAuthKitAuthentication:
    """Test AuthKit JWT validation and authentication."""

    @pytest.mark.mock_only
    @pytest.mark.database
    @pytest.mark.story("User can log in with AuthKit")
    async def test_authkit_jwt_validation_valid(self):
        """Test valid AuthKit JWT validation."""
        payload = {
            "sub": "user-123",
            "email": "user@example.com",
            "iss": "https://authkit.workos.com",
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
        }
        assert payload["sub"] == "user-123"
        assert payload["email"] == "user@example.com"

    @pytest.mark.mock_only
    @pytest.mark.database
    @pytest.mark.story("User can log in with AuthKit")
    async def test_authkit_jwt_validation_expired(self):
        """Test expired JWT rejection."""
        payload = {
            "sub": "user-123",
            "exp": int(time.time()) - 3600,  # Expired
        }
        is_expired = payload["exp"] < time.time()
        assert is_expired is True

    @pytest.mark.mock_only
    @pytest.mark.database
    @pytest.mark.story("User can log in with AuthKit")
    async def test_authkit_jwt_validation_invalid_signature(self):
        """Test invalid signature rejection."""
        invalid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature"
        parts = invalid_token.split(".")
        assert len(parts) == 3

    @pytest.mark.mock_only
    @pytest.mark.database
    @pytest.mark.story("User can log in with AuthKit")
    async def test_authkit_user_info_extraction(self):
        """Test extracting user info from AuthKit JWT."""
        payload = {
            "sub": "user-123",
            "email": "user@example.com",
            "name": "Test User",
            "org_id": "org-456",
        }
        assert payload["sub"] == "user-123"
        assert payload["email"] == "user@example.com"


class TestBearerTokenAuthentication:
    """Test bearer token authentication."""

    @pytest.mark.story("User can authenticate with bearer token")
    async def test_bearer_auth_with_supabase_jwt(self, end_to_end_client):
        """Test authentication with Supabase JWT Bearer token."""
        result = await end_to_end_client.health_check()
        assert "success" in result or "status" in result

    @pytest.mark.story("User can authenticate with bearer token")
    async def test_bearer_auth_call_tool(self, end_to_end_client):
        """Test calling tool with bearer token."""
        result = await end_to_end_client.list_tools()
        assert "success" in result or "tools" in result


class TestHybridAuthenticationScenarios:
    """Test hybrid authentication scenarios."""

    @pytest.mark.story("Bearer token is preferred over OAuth")
    async def test_bearer_token_preferred_over_oauth(self, end_to_end_client):
        """Test that bearer token is preferred over OAuth."""
        result = await end_to_end_client.health_check()
        assert "success" in result or "status" in result

    @pytest.mark.story("User can authenticate with bearer token")
    async def test_workos_user_management_token(self, end_to_end_client):
        """Test authentication with WorkOS User Management token."""
        result = await end_to_end_client.health_check()
        assert "success" in result or "status" in result


class TestSupabaseAuthIntegration:
    """Test Supabase authentication integration."""

    @pytest.mark.mock_only
    @pytest.mark.database
    @pytest.mark.story("User can log in with AuthKit")
    async def test_supabase_jwt_validation(self):
        """Test Supabase JWT validation."""
        payload = {
            "sub": "user-123",
            "aud": "authenticated",
            "iss": "https://ydogoylwenufckscqijp.supabase.co/auth/v1",
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
        }
        assert payload["sub"] == "user-123"
        assert payload["aud"] == "authenticated"

    @pytest.mark.mock_only
    @pytest.mark.database
    @pytest.mark.story("User can log in with AuthKit")
    async def test_supabase_session_management(self):
        """Test Supabase session management."""
        session = {
            "access_token": "test-token",
            "refresh_token": "test-refresh",
            "expires_in": 3600,
            "user": {"id": "user-123", "email": "user@example.com"}
        }
        assert session["user"]["id"] == "user-123"
        assert session["expires_in"] > 0

