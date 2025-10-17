"""
Tests for Token Manager

Comprehensive test suite for token refresh, rotation, and introspection.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from ..token_manager import TokenManager, TokenRefreshError
from ..models import Session, TokenRefreshRecord
from ..storage.base import InMemoryStorage


@pytest.fixture
async def storage():
    """Create in-memory storage for testing."""
    return InMemoryStorage()


@pytest.fixture
async def token_manager(storage):
    """Create token manager for testing."""
    return TokenManager(
        storage=storage,
        token_endpoint="https://test.com/token",
        client_id="test_client",
        client_secret="test_secret",
    )


@pytest.fixture
def mock_session():
    """Create mock session for testing."""
    return Session(
        session_id="session_123",
        user_id="user_123",
        access_token="old_access_token",
        refresh_token="refresh_token",
        access_token_expires_at=datetime.utcnow() + timedelta(minutes=2),
    )


@pytest.mark.asyncio
async def test_needs_refresh(mock_session):
    """Test checking if token needs refresh."""
    # Should need refresh (within 5 minute buffer)
    assert mock_session.needs_refresh(buffer_minutes=5) is True

    # Should not need refresh (outside buffer)
    assert mock_session.needs_refresh(buffer_minutes=1) is False


@pytest.mark.asyncio
async def test_refresh_token_success(token_manager, mock_session):
    """Test successful token refresh."""
    # Mock HTTP response
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json = MagicMock(return_value={
        "access_token": "new_access_token",
        "refresh_token": "new_refresh_token",
        "expires_in": 3600,
        "token_type": "Bearer",
    })

    with patch.object(
        token_manager,
        "_get_http_client",
        return_value=AsyncMock(post=AsyncMock(return_value=mock_response))
    ):
        session, record = await token_manager.refresh_token(mock_session)

        assert session.access_token == "new_access_token"
        assert session.refresh_token == "new_refresh_token"
        assert record.is_successful is True
        assert record.rotation_enabled is True


@pytest.mark.asyncio
async def test_refresh_token_without_rotation(token_manager, mock_session):
    """Test token refresh without rotation."""
    # Mock response without new refresh token
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json = MagicMock(return_value={
        "access_token": "new_access_token",
        "expires_in": 3600,
    })

    with patch.object(
        token_manager,
        "_get_http_client",
        return_value=AsyncMock(post=AsyncMock(return_value=mock_response))
    ):
        session, record = await token_manager.refresh_token(mock_session)

        assert session.access_token == "new_access_token"
        # Refresh token should remain the same
        assert session.refresh_token == "refresh_token"
        assert record.is_successful is True


@pytest.mark.asyncio
async def test_refresh_token_failure(token_manager, mock_session):
    """Test token refresh failure."""
    # Mock error response
    mock_response = AsyncMock()
    mock_response.status_code = 401
    mock_response.json = MagicMock(return_value={
        "error": "invalid_grant",
        "error_description": "Invalid refresh token",
    })
    mock_response.text = '{"error": "invalid_grant"}'

    with patch.object(
        token_manager,
        "_get_http_client",
        return_value=AsyncMock(post=AsyncMock(return_value=mock_response))
    ):
        with pytest.raises(TokenRefreshError):
            await token_manager.refresh_token(mock_session)


@pytest.mark.asyncio
async def test_refresh_token_retry(token_manager, mock_session):
    """Test token refresh with retry logic."""
    # First attempt fails, second succeeds
    fail_response = AsyncMock()
    fail_response.status_code = 500
    fail_response.json = MagicMock(return_value={"error": "server_error"})
    fail_response.text = '{"error": "server_error"}'

    success_response = AsyncMock()
    success_response.status_code = 200
    success_response.json = MagicMock(return_value={
        "access_token": "new_access_token",
        "expires_in": 3600,
    })

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=[fail_response, success_response])

    with patch.object(token_manager, "_get_http_client", return_value=mock_client):
        session, record = await token_manager.refresh_token(mock_session)

        assert session.access_token == "new_access_token"
        assert mock_client.post.call_count == 2


@pytest.mark.asyncio
async def test_get_refresh_history(token_manager, storage):
    """Test getting refresh history."""
    session_id = "session_123"

    # Create some refresh records
    for i in range(5):
        record = TokenRefreshRecord(
            session_id=session_id,
            user_id="user_123",
            new_access_token_hash=f"hash_{i}",
            new_refresh_token_hash=f"hash_{i}",
        )
        await storage.save_refresh_record(record)

    # Get history
    history = await token_manager.get_refresh_history(session_id, limit=3)

    assert len(history) == 3
    # Should be in reverse chronological order
    assert history[0].new_access_token_hash == "hash_4"


@pytest.mark.asyncio
async def test_validate_token_expired(token_manager):
    """Test validating expired token."""
    session = Session(
        session_id="session_123",
        user_id="user_123",
        access_token="access_token",
        access_token_expires_at=datetime.utcnow() - timedelta(minutes=5),
    )

    is_valid = await token_manager.validate_token(session)
    assert is_valid is False


@pytest.mark.asyncio
async def test_validate_token_valid(token_manager):
    """Test validating valid token."""
    session = Session(
        session_id="session_123",
        user_id="user_123",
        access_token="access_token",
        access_token_expires_at=datetime.utcnow() + timedelta(hours=1),
    )

    is_valid = await token_manager.validate_token(session)
    assert is_valid is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
