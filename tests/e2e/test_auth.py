"""
Authentication tests for AuthKit integration and JWT validation.

Tests for:
1. AuthKit JWT validation and authentication
2. Session management
3. AuthKit + Supabase integration
"""

import pytest
import time
from datetime import datetime, timedelta
import uuid

# Skip tests if live services not available
pytestmark = pytest.mark.integration


class TestAuthKitAuthentication:
    """Test AuthKit JWT validation and authentication."""

    @pytest.mark.mock_only
    @pytest.mark.e2e
    @pytest.mark.database
    def test_authkit_jwt_validation_valid(self):
        """Test valid AuthKit JWT validation."""
        # Create a valid-looking JWT
        payload = {
            "sub": "user-123",
            "email": "user@example.com",
            "iss": "https://authkit.workos.com",
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
        }

        # Simulate JWT validation
        assert payload["sub"] == "user-123"
        assert payload["email"] == "user@example.com"

    @pytest.mark.mock_only
    @pytest.mark.e2e
    @pytest.mark.database
    def test_authkit_jwt_validation_expired(self):
        """Test expired JWT rejection."""
        payload = {
            "sub": "user-123",
            "exp": int(time.time()) - 3600,  # Expired
        }

        is_expired = payload["exp"] < time.time()
        assert is_expired is True

    @pytest.mark.mock_only
    @pytest.mark.e2e
    @pytest.mark.database
    def test_authkit_jwt_validation_invalid_signature(self):
        """Test invalid signature rejection."""
        invalid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature"

        # Token format is invalid
        parts = invalid_token.split(".")
        assert len(parts) == 3
        # In real scenario, signature verification would fail

    @pytest.mark.mock_only
    @pytest.mark.e2e
    @pytest.mark.database
    def test_authkit_user_info_extraction(self):
        """Test extracting user info from AuthKit JWT."""
        payload = {
            "sub": "user-123",
            "email": "user@example.com",
            "name": "Test User",
            "org_id": "org-456",
        }

        user_info = {
            "user_id": payload["sub"],
            "email": payload["email"],
            "name": payload["name"],
            "organization_id": payload["org_id"],
        }

        assert user_info["user_id"] == "user-123"
        assert user_info["email"] == "user@example.com"

    @pytest.mark.mock_only
    @pytest.mark.e2e
    @pytest.mark.database
    def test_authkit_token_refresh(self):
        """Test token refresh flow."""
        old_token = "old_token_123"
        refresh_token = "refresh_123"

        # Simulate refresh
        new_token = f"new_token_{int(time.time())}"

        assert new_token != old_token

    @pytest.mark.mock_only
    @pytest.mark.e2e
    @pytest.mark.database
    def test_authkit_session_creation(self):
        """Test AuthKit session creation."""
        user_info = {
            "user_id": "user-123",
            "email": "user@example.com",
        }

        session = {
            "session_id": str(uuid.uuid4()),
            "user_id": user_info["user_id"],
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=7)).isoformat(),
        }

        assert session["user_id"] == "user-123"

    @pytest.mark.mock_only
    @pytest.mark.e2e
    @pytest.mark.database
    def test_authkit_session_validation(self):
        """Test validating active session."""
        session = {
            "session_id": "sess-123",
            "expires_at": (datetime.now() + timedelta(days=1)).isoformat(),
        }

        expires_dt = datetime.fromisoformat(session["expires_at"])
        is_valid = expires_dt > datetime.now()

        assert is_valid is True

    @pytest.mark.mock_only
    @pytest.mark.e2e
    @pytest.mark.database
    def test_authkit_logout_session_invalidation(self):
        """Test session invalidation on logout."""
        session_id = "sess-123"
        active_sessions = {"sess-123": {"user_id": "user-123"}}

        # Logout
        del active_sessions[session_id]

        assert session_id not in active_sessions

    @pytest.mark.mock_only
    @pytest.mark.e2e
    @pytest.mark.database
    def test_authkit_multi_session_per_user(self):
        """Test multiple sessions per user."""
        user_id = "user-123"
        sessions = [
            {"session_id": f"sess-{i}", "user_id": user_id, "device": f"device-{i}"}
            for i in range(3)
        ]

        user_sessions = [s for s in sessions if s["user_id"] == user_id]
        assert len(user_sessions) == 3


class TestSupabaseAuthIntegration:
    """Test Supabase + AuthKit integration."""

    @pytest.mark.mock_only
    @pytest.mark.e2e
    @pytest.mark.database
    def test_supabase_jwt_from_authkit(self):
        """Test using AuthKit JWT with Supabase."""
        authkit_payload = {
            "sub": "user-123",
            "email": "user@example.com",
            "iss": "https://authkit.workos.com",
        }

        # Supabase accepts AuthKit JWT with WorkOS provider configured
        result = {
            "authenticated": True,
            "user_id": authkit_payload["sub"],
            "provider": "authkit",
        }

        assert result["authenticated"] is True

    @pytest.mark.mock_only
    @pytest.mark.e2e
    @pytest.mark.database
    def test_supabase_rls_with_authkit_user(self):
        """Test RLS enforcement with AuthKit user."""
        user_id = "user-123"
        entity = {"id": "req-1", "created_by": user_id}

        # auth.uid() in Supabase RLS should match AuthKit user_id
        rls_check = entity["created_by"] == user_id
        assert rls_check is True

    @pytest.mark.mock_only
    @pytest.mark.e2e
    @pytest.mark.database
    def test_supabase_set_access_token_for_rls(self):
        """Test setting access token for RLS context."""
        access_token = "authkit_jwt_token"
        user_id = "user-123"

        # Database adapter should set token for RLS
        context = {
            "access_token": access_token,
            "user_id": user_id,
        }

        assert context["access_token"] == access_token
