"""
Tests for Revocation Service

Comprehensive test suite for token revocation and cascading.
"""

import pytest
from datetime import datetime, timedelta

from ..revocation import RevocationService, RevocationRecord
from ..models import Session, SessionState
from ..storage.base import InMemoryStorage


@pytest.fixture
async def storage():
    """Create in-memory storage for testing."""
    return InMemoryStorage()


@pytest.fixture
async def revocation_service(storage):
    """Create revocation service for testing."""
    return RevocationService(
        storage=storage,
        enable_cascading=True,
    )


@pytest.fixture
def mock_session():
    """Create mock session for testing."""
    return Session(
        session_id="session_123",
        user_id="user_123",
        access_token="access_token_123",
        refresh_token="refresh_token_123",
        id_token="id_token_123",
    )


@pytest.mark.asyncio
async def test_revoke_token(revocation_service):
    """Test revoking a single token."""
    record = await revocation_service.revoke_token(
        token="access_token",
        token_type="access_token",
        session_id="session_123",
        user_id="user_123",
        reason="test_revocation",
    )

    assert record.token_type == "access_token"
    assert record.reason == "test_revocation"
    assert record.is_successful is True


@pytest.mark.asyncio
async def test_is_revoked(revocation_service):
    """Test checking if token is revoked."""
    token = "test_token"

    # Should not be revoked initially
    is_revoked = await revocation_service.is_revoked(token)
    assert is_revoked is False

    # Revoke token
    await revocation_service.revoke_token(
        token=token,
        token_type="access_token",
    )

    # Should be revoked now
    is_revoked = await revocation_service.is_revoked(token, check_storage=True)
    assert is_revoked is True


@pytest.mark.asyncio
async def test_revoke_session(revocation_service, mock_session):
    """Test revoking entire session."""
    records = await revocation_service.revoke_session(
        session=mock_session,
        reason="user_logout",
    )

    # Should revoke all 3 tokens (access, refresh, id)
    assert len(records) == 3

    token_types = {r.token_type for r in records}
    assert token_types == {"access_token", "refresh_token", "id_token"}

    # Session should be marked as revoked
    assert mock_session.state == SessionState.REVOKED


@pytest.mark.asyncio
async def test_revoke_user_sessions(revocation_service, storage):
    """Test revoking all user sessions."""
    user_id = "user_123"

    # Create multiple sessions
    sessions = []
    for i in range(3):
        session = Session(
            session_id=f"session_{i}",
            user_id=user_id,
            access_token=f"access_token_{i}",
            refresh_token=f"refresh_token_{i}",
        )
        sessions.append(session)
        await storage.save_session(session)

    # Revoke all except first
    records = await revocation_service.revoke_user_sessions(
        user_id=user_id,
        except_session_id=sessions[0].session_id,
        reason="logout_all",
    )

    # Should revoke 2 sessions * 2 tokens each = 4 tokens
    assert len(records) == 4


@pytest.mark.asyncio
async def test_cascade_revocation(revocation_service, storage):
    """Test cascading revocation from refresh token."""
    session = Session(
        session_id="session_123",
        user_id="user_123",
        access_token="access_token",
        refresh_token="refresh_token",
        id_token="id_token",
    )
    await storage.save_session(session)

    # Revoke refresh token with cascade
    records = await revocation_service.revoke_with_cascade(
        refresh_token=session.refresh_token,
        session_id=session.session_id,
        user_id=session.user_id,
        reason="refresh_token_compromised",
    )

    # Should revoke all 3 tokens
    assert len(records) == 3

    # Check cascade relationships
    parent_record = records[0]
    assert parent_record.token_type == "refresh_token"

    for record in records[1:]:
        assert record.cascaded_from == parent_record.revocation_id


@pytest.mark.asyncio
async def test_get_revocation_record(revocation_service):
    """Test getting revocation record."""
    token = "test_token"

    # Revoke token
    original_record = await revocation_service.revoke_token(
        token=token,
        token_type="access_token",
    )

    # Retrieve record
    retrieved_record = await revocation_service.get_revocation_record(token)

    assert retrieved_record is not None
    assert retrieved_record.revocation_id == original_record.revocation_id


@pytest.mark.asyncio
async def test_get_session_revocations(revocation_service, mock_session, storage):
    """Test getting all revocations for a session."""
    await storage.save_session(mock_session)

    # Revoke session
    await revocation_service.revoke_session(mock_session)

    # Get session revocations
    revocations = await revocation_service.get_session_revocations(
        mock_session.session_id
    )

    assert len(revocations) == 3


@pytest.mark.asyncio
async def test_revocation_ttl(storage):
    """Test revocation record TTL."""
    record = RevocationRecord(
        revocation_id="rev_123",
        token_hash="token_hash",
        token_type="access_token",
        expires_at=datetime.utcnow() + timedelta(hours=1),
    )

    await storage.save_revocation_record(record)

    # Should be retrievable
    retrieved = await storage.get_revocation_record(record.token_hash)
    assert retrieved is not None

    # Simulate expiry
    record.expires_at = datetime.utcnow() - timedelta(hours=1)
    await storage.save_revocation_record(record)

    # Should still be retrievable (cleanup happens separately)
    retrieved = await storage.get_revocation_record(record.token_hash)
    assert retrieved is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
