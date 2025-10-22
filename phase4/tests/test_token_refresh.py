"""Tests for token refresh service."""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from phase4.models import RefreshTokenRotation, TokenPair
from phase4.services.token_refresh import TokenRefreshService
from phase4.storage.base import StorageBackend


class MockStorageBackend(StorageBackend):
    """Mock storage backend for testing."""

    def __init__(self):
        self.data = {}

    async def get(self, key: str):
        return self.data.get(key)

    async def set(self, key: str, value, expire=None):
        self.data[key] = value

    async def delete(self, key: str):
        return self.data.pop(key, None) is not None

    async def exists(self, key: str):
        return key in self.data

    async def expire(self, key: str, ttl: int):
        return True

    async def ttl(self, key: str):
        return 3600

    async def scan(self, pattern: str, count: int = 100):
        return [k for k in self.data.keys() if pattern.replace("*", "") in k][:count]

    async def mget(self, keys):
        return {k: self.data.get(k) for k in keys}

    async def mset(self, items, expire=None):
        self.data.update(items)

    async def incr(self, key: str, amount: int = 1):
        self.data[key] = self.data.get(key, 0) + amount
        return self.data[key]

    async def decr(self, key: str, amount: int = 1):
        self.data[key] = self.data.get(key, 0) - amount
        return self.data[key]


@pytest.fixture
def mock_storage():
    """Provide mock storage backend."""
    return MockStorageBackend()


@pytest.fixture
def token_service(mock_storage):
    """Provide token refresh service with mock storage."""
    service = TokenRefreshService(storage=mock_storage)
    service.workos_api_key = "test_api_key"
    return service


@pytest.fixture
def sample_token_pair():
    """Provide sample token pair."""
    return TokenPair(
        access_token="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyXzEyMyIsImV4cCI6MTcwMDAwMDAwMH0.test",
        refresh_token="refresh_token_123",
        access_expires_in=3600,
        refresh_expires_in=604800,
    )


@pytest.mark.asyncio
async def test_validate_refresh_token_valid(token_service, mock_storage):
    """Test validation of valid refresh token."""
    # Setup
    refresh_token = "valid_refresh_token"
    session_id = "session_123"

    # Token not revoked
    mock_storage.data = {}

    # Should not raise
    await token_service._validate_refresh_token(refresh_token, session_id)


@pytest.mark.asyncio
async def test_validate_refresh_token_revoked(token_service, mock_storage):
    """Test validation of revoked refresh token."""
    # Setup
    refresh_token = "revoked_token"
    token_hash = "hash_" + refresh_token  # Simplified hash

    # Mark token as revoked
    mock_storage.data[f"revoked:{token_hash}"] = {
        "revoked_at": datetime.utcnow().isoformat()
    }

    # Mock hash function
    with patch("phase4.models.token.TokenMetadata.hash_token", return_value=token_hash):
        with pytest.raises(ValueError, match="revoked"):
            await token_service._validate_refresh_token(refresh_token)


@pytest.mark.asyncio
async def test_handle_rotation_new_session(token_service, mock_storage):
    """Test refresh token rotation for new session."""
    # Setup
    old_token = "old_refresh_token"
    new_tokens = TokenPair(
        access_token="new_access",
        refresh_token=None,  # Will be generated
        access_expires_in=3600,
        refresh_expires_in=604800,
    )
    session_id = "session_456"

    # Execute
    result = await token_service._handle_rotation(
        old_token,
        new_tokens,
        session_id
    )

    # Assert
    assert result.refresh_token is not None
    assert result.refresh_token != old_token

    # Check rotation state was stored
    rotation_key = f"rotation:{session_id}"
    assert rotation_key in mock_storage.data
    rotation_data = mock_storage.data[rotation_key]
    assert rotation_data["current_token"] == result.refresh_token
    assert rotation_data["rotation_count"] == 1


@pytest.mark.asyncio
async def test_handle_rotation_existing_session(token_service, mock_storage):
    """Test refresh token rotation for existing session."""
    # Setup
    old_token = "old_refresh_token"
    session_id = "session_789"

    # Existing rotation state
    existing_rotation = RefreshTokenRotation(
        current_token=old_token,
        rotation_count=2
    )
    mock_storage.data[f"rotation:{session_id}"] = existing_rotation.__dict__

    new_tokens = TokenPair(
        access_token="new_access",
        refresh_token="new_refresh_token",
        access_expires_in=3600,
        refresh_expires_in=604800,
    )

    # Execute
    result = await token_service._handle_rotation(
        old_token,
        new_tokens,
        session_id
    )

    # Assert
    assert result.refresh_token == "new_refresh_token"

    # Check rotation count incremented
    rotation_data = mock_storage.data[f"rotation:{session_id}"]
    assert rotation_data["rotation_count"] == 3
    assert rotation_data["previous_token"] == old_token


@pytest.mark.asyncio
async def test_proactive_refresh_needed(token_service, mock_storage):
    """Test proactive refresh when token is approaching expiration."""
    # Create token that expires in 4 minutes (less than 5 minute buffer)
    exp_time = int((datetime.utcnow() + timedelta(minutes=4)).timestamp())
    access_token = f"eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyXzEyMyIsImV4cCI6{exp_time}.test"
    refresh_token = "valid_refresh"

    # Mock the refresh call
    with patch.object(token_service, "_call_authkit_refresh") as mock_call:
        mock_call.return_value = TokenPair(
            access_token="new_access",
            refresh_token="new_refresh",
            access_expires_in=3600,
            refresh_expires_in=604800,
        )

        # Execute
        result = await token_service.proactive_refresh(
            access_token,
            refresh_token,
            "session_123"
        )

        # Assert
        assert result is not None
        assert result.access_token == "new_access"
        mock_call.assert_called_once()


@pytest.mark.asyncio
async def test_proactive_refresh_not_needed(token_service):
    """Test proactive refresh when token has plenty of time left."""
    # Create token that expires in 1 hour
    exp_time = int((datetime.utcnow() + timedelta(hours=1)).timestamp())
    access_token = f"eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyXzEyMyIsImV4cCI6{exp_time}.test"
    refresh_token = "valid_refresh"

    # Execute
    result = await token_service.proactive_refresh(
        access_token,
        refresh_token,
        "session_123"
    )

    # Assert - should not refresh
    assert result is None


@pytest.mark.asyncio
async def test_refresh_token_success(token_service, mock_storage):
    """Test successful token refresh flow."""
    # Setup
    refresh_token = "valid_refresh"
    session_id = "session_123"

    # Mock AuthKit API call
    with patch.object(token_service, "_call_authkit_refresh") as mock_call:
        mock_call.return_value = TokenPair(
            access_token="new_access_token",
            refresh_token="new_refresh_token",
            access_expires_in=3600,
            refresh_expires_in=604800,
        )

        # Mock audit
        with patch.object(token_service.audit, "log_token_refresh") as mock_audit:
            # Execute
            result = await token_service.refresh_token(
                refresh_token,
                session_id
            )

            # Assert
            assert result.access_token == "new_access_token"
            assert result.refresh_token == "new_refresh_token"

            # Verify audit was called
            mock_audit.assert_called_once()


@pytest.mark.asyncio
async def test_refresh_token_invalid_token(token_service, mock_storage):
    """Test refresh with invalid token."""
    # Setup
    refresh_token = "invalid_token"
    session_id = "session_123"

    # Mock validation to fail
    with patch.object(token_service, "_validate_refresh_token") as mock_validate:
        mock_validate.side_effect = ValueError("Invalid refresh token")

        # Mock audit
        with patch.object(token_service.audit, "log_token_refresh_failure") as mock_audit:
            # Execute and assert
            with pytest.raises(ValueError, match="Invalid refresh token"):
                await token_service.refresh_token(
                    refresh_token,
                    session_id
                )

            # Verify audit was called
            mock_audit.assert_called_once()


@pytest.mark.asyncio
async def test_store_token_metadata(token_service, mock_storage):
    """Test storing token metadata."""
    # Setup
    token_pair = TokenPair(
        access_token="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyXzQ1NiIsInVzZXJfaWQiOiJ1c2VyXzQ1NiJ9.test",
        refresh_token="refresh_789",
        access_expires_in=3600,
        refresh_expires_in=604800,
    )
    session_id = "session_abc"

    # Execute
    await token_service._store_token_metadata(token_pair, session_id)

    # Assert - check metadata was stored
    stored_keys = list(mock_storage.data.keys())
    access_meta_keys = [k for k in stored_keys if k.startswith("token:access:")]
    refresh_meta_keys = [k for k in stored_keys if k.startswith("token:refresh:")]

    assert len(access_meta_keys) == 1
    assert len(refresh_meta_keys) == 1

    # Check metadata content
    access_meta = mock_storage.data[access_meta_keys[0]]
    assert access_meta["session_id"] == session_id
    assert access_meta["user_id"] == "user_456"


@pytest.mark.asyncio
async def test_refresh_with_rotation_enabled(token_service, mock_storage):
    """Test refresh with rotation enabled."""
    # Setup
    token_service.rotation_enabled = True
    refresh_token = "current_refresh"
    session_id = "session_rot"

    # Mock AuthKit API
    with patch.object(token_service, "_call_authkit_refresh") as mock_call:
        mock_call.return_value = TokenPair(
            access_token="new_access",
            refresh_token=None,  # Will trigger generation
            access_expires_in=3600,
            refresh_expires_in=604800,
        )

        # Execute
        result = await token_service.refresh_token(
            refresh_token,
            session_id,
            force_rotation=True
        )

        # Assert
        assert result.refresh_token is not None
        assert result.refresh_token != refresh_token

        # Check rotation state
        rotation_key = f"rotation:{session_id}"
        assert rotation_key in mock_storage.data
