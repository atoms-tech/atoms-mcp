"""Fixtures for infrastructure unit tests.

Provides mocks for:
- Database adapter (Supabase)
- Authentication adapter
- Rate limiter
- RLS context
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import Dict


@pytest.fixture
def database_mock():
    """Mock database adapter for testing data operations."""
    mock_db = AsyncMock()
    mock_db.query = AsyncMock(return_value=[])
    mock_db.execute = AsyncMock(return_value={"success": True})
    mock_db.transaction = AsyncMock()
    mock_db.get_by_id = AsyncMock(return_value=None)
    mock_db.create = AsyncMock(return_value={"id": "test-id"})
    mock_db.update = AsyncMock(return_value={"success": True})
    mock_db.delete = AsyncMock(return_value={"success": True})
    return mock_db


@pytest.fixture
def auth_mock():
    """Mock authentication provider."""
    mock_auth = AsyncMock()
    mock_auth.verify_token = AsyncMock(return_value=True)
    mock_auth.get_user = AsyncMock(return_value={
        "id": "test-user-id",
        "email": "test@example.com"
    })
    mock_auth.create_session = AsyncMock(return_value="session-token")
    mock_auth.revoke_token = AsyncMock(return_value=True)
    return mock_auth


@pytest.fixture
def supabase_client_mock():
    """Mock Supabase client."""
    mock_client = MagicMock()
    mock_client.table = MagicMock()
    mock_client.auth = MagicMock()
    mock_client.storage = MagicMock()
    mock_client.from_ = MagicMock()  # from_ is used for table queries
    return mock_client


@pytest.fixture
def rate_limiter_mock():
    """Mock rate limiter for testing rate limiting."""
    mock_limiter = AsyncMock()
    mock_limiter.check = AsyncMock(return_value=True)
    mock_limiter.is_limited = AsyncMock(return_value=False)
    mock_limiter.record = AsyncMock()
    mock_limiter.reset = AsyncMock()
    return mock_limiter


@pytest.fixture
def rls_context_mock() -> Dict[str, str]:
    """Mock Row-Level Security context."""
    return {
        "auth.uid()": "test-user-id",
        "auth.jwt()": "test-jwt-token",
        "auth.email()": "test@example.com",
    }


@pytest.fixture
def transaction_mock():
    """Mock database transaction."""
    mock_transaction = AsyncMock()
    mock_transaction.__aenter__ = AsyncMock(return_value=mock_transaction)
    mock_transaction.__aexit__ = AsyncMock(return_value=None)
    mock_transaction.commit = AsyncMock()
    mock_transaction.rollback = AsyncMock()
    return mock_transaction
