"""Tests for mock adapter implementations.

Tests that the in-memory mock adapters work correctly for unit testing.
"""

import pytest
from unittest.mock import AsyncMock


class TestMockAdapters:
    """Test that the mock adapters work correctly."""

    @pytest.mark.asyncio
    async def test_database_mock_operations(self, database_mock):
        """Test basic database operations with the mock adapter."""
        # Test empty query
        database_mock.query.return_value = []
        results = await database_mock.query("test_table")
        assert results == []

        # Test create operation
        database_mock.create.return_value = {"id": "1", "name": "Test Item"}
        result = await database_mock.create("test_table", {"name": "Test Item"})
        assert result["id"] == "1"
        assert result["name"] == "Test Item"

        # Test query with results
        database_mock.query.return_value = [{"id": "1", "name": "Test Item"}]
        results = await database_mock.query("test_table")
        assert len(results) == 1
        assert results[0]["name"] == "Test Item"

        # Test update operation
        database_mock.update.return_value = {"success": True}
        result = await database_mock.update("test_table", {"name": "Updated"}, {"id": "1"})
        assert result["success"] is True

        # Test delete operation
        database_mock.delete.return_value = {"success": True}
        result = await database_mock.delete("test_table", {"id": "1"})
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_auth_mock_operations(self, auth_mock):
        """Test basic auth operations with the mock adapter."""
        # Test session creation
        auth_mock.create_session.return_value = "session-token-123"
        token = await auth_mock.create_session("user-123", "test@example.com")
        assert token == "session-token-123"

        # Test token verification
        auth_mock.verify_token.return_value = True
        is_valid = await auth_mock.verify_token(token)
        assert is_valid is True

        # Test get user info
        auth_mock.get_user.return_value = {"id": "user-123", "email": "test@example.com"}
        user_info = await auth_mock.get_user(token)
        assert user_info["id"] == "user-123"
        assert user_info["email"] == "test@example.com"

        # Test token revocation
        auth_mock.revoke_token.return_value = True
        revoked = await auth_mock.revoke_token(token)
        assert revoked is True

    @pytest.mark.asyncio
    async def test_rate_limiter_mock(self, rate_limiter_mock):
        """Test rate limiter mock operations."""
        # Test rate limit check (not limited)
        rate_limiter_mock.check.return_value = True
        can_proceed = await rate_limiter_mock.check("user-123", "test-action")
        assert can_proceed is True

        # Test is_limited check
        rate_limiter_mock.is_limited.return_value = False
        is_limited = await rate_limiter_mock.is_limited("user-123", "test-action")
        assert is_limited is False

        # Test record operation
        rate_limiter_mock.record.return_value = None
        result = await rate_limiter_mock.record("user-123", "test-action")
        assert result is None

        # Test reset
        rate_limiter_mock.reset.return_value = None
        result = await rate_limiter_mock.reset("user-123")
        assert result is None

    def test_rls_context_mock(self, rls_context_mock):
        """Test RLS context mock."""
        assert rls_context_mock["auth.uid()"] == "test-user-id"
        assert rls_context_mock["auth.email()"] == "test@example.com"
        assert rls_context_mock["auth.jwt()"] == "test-jwt-token"

    @pytest.mark.asyncio
    async def test_transaction_mock(self, transaction_mock):
        """Test database transaction mock."""
        # Test transaction context manager
        async with transaction_mock as txn:
            assert txn is transaction_mock

        # Test commit
        result = await transaction_mock.commit()
        assert result is None

        # Test rollback
        result = await transaction_mock.rollback()
        assert result is None

    @pytest.mark.asyncio
    async def test_supabase_client_mock(self, supabase_client_mock):
        """Test Supabase client mock."""
        # Test table access
        table_ref = supabase_client_mock.table("test_table")
        assert table_ref is not None

        # Test auth access
        auth_ref = supabase_client_mock.auth
        assert auth_ref is not None

        # Test storage access
        storage_ref = supabase_client_mock.storage
        assert storage_ref is not None

        # Test from_ access
        query_ref = supabase_client_mock.from_("test_table")
        assert query_ref is not None
