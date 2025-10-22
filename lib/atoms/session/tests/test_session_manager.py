"""
Tests for Session Manager

Comprehensive test suite for session lifecycle management.
"""

from datetime import datetime, timedelta

import pytest

from ..models import DeviceFingerprint, SessionState
from ..session_manager import SessionExpiredError, SessionManager
from ..storage.base import InMemoryStorage


@pytest.fixture
async def storage():
    """Create in-memory storage for testing."""
    return InMemoryStorage()


@pytest.fixture
async def session_manager(storage):
    """Create session manager for testing."""
    return SessionManager(storage=storage)


@pytest.mark.asyncio
async def test_create_session(session_manager):
    """Test session creation."""
    session = await session_manager.create_session(
        user_id="user123",
        access_token="access_token_123",
        refresh_token="refresh_token_123",
        expires_in=3600,
    )

    assert session.user_id == "user123"
    assert session.access_token == "access_token_123"
    assert session.refresh_token == "refresh_token_123"
    assert session.state == SessionState.ACTIVE
    assert session.access_token_expires_at is not None


@pytest.mark.asyncio
async def test_get_session(session_manager):
    """Test getting session."""
    # Create session
    session = await session_manager.create_session(
        user_id="user123",
        access_token="access_token_123",
    )

    # Get session
    retrieved = await session_manager.get_session(session.session_id)

    assert retrieved.session_id == session.session_id
    assert retrieved.user_id == session.user_id


@pytest.mark.asyncio
async def test_session_expiry(session_manager):
    """Test session expiry handling."""
    # Create expired session
    session = await session_manager.create_session(
        user_id="user123",
        access_token="access_token_123",
    )

    # Manually expire it
    session.created_at = datetime.utcnow() - timedelta(hours=10)
    session.last_accessed_at = datetime.utcnow() - timedelta(hours=2)
    await session_manager.storage.save_session(session)

    # Try to get - should raise expired error
    with pytest.raises(SessionExpiredError):
        await session_manager.get_session(session.session_id)


@pytest.mark.asyncio
async def test_device_validation(session_manager):
    """Test device fingerprint validation."""
    # Create fingerprint
    fingerprint = DeviceFingerprint(
        user_agent="Mozilla/5.0",
        platform="MacIntel",
        timezone="America/New_York",
    )

    # Create session with fingerprint
    session = await session_manager.create_session(
        user_id="user123",
        access_token="access_token_123",
        device_fingerprint=fingerprint,
    )

    # Should succeed with matching fingerprint
    retrieved = await session_manager.get_session(
        session.session_id,
        device_fingerprint=fingerprint,
    )
    assert retrieved is not None

    # Should fail with different fingerprint
    different_fingerprint = DeviceFingerprint(
        user_agent="Different Browser",
        platform="Windows",
        timezone="Europe/London",
    )

    from ..session_manager import DeviceValidationError
    with pytest.raises(DeviceValidationError):
        await session_manager.get_session(
            session.session_id,
            device_fingerprint=different_fingerprint,
        )


@pytest.mark.asyncio
async def test_multi_session_support(session_manager):
    """Test multiple sessions per user."""
    user_id = "user123"

    # Create multiple sessions
    sessions = []
    for i in range(3):
        session = await session_manager.create_session(
            user_id=user_id,
            access_token=f"access_token_{i}",
        )
        sessions.append(session)

    # Get all user sessions
    user_sessions = await session_manager.get_user_sessions(user_id)

    assert len(user_sessions) == 3


@pytest.mark.asyncio
async def test_session_limit(session_manager):
    """Test session limit enforcement."""
    user_id = "user123"
    session_manager.max_sessions_per_user = 2

    # Create sessions up to limit
    for i in range(3):
        await session_manager.create_session(
            user_id=user_id,
            access_token=f"access_token_{i}",
        )

    # Should only have max_sessions_per_user active sessions
    user_sessions = await session_manager.get_user_sessions(user_id)
    active_sessions = [s for s in user_sessions if s.state == SessionState.ACTIVE]

    assert len(active_sessions) <= session_manager.max_sessions_per_user


@pytest.mark.asyncio
async def test_terminate_session(session_manager):
    """Test session termination."""
    session = await session_manager.create_session(
        user_id="user123",
        access_token="access_token_123",
    )

    # Terminate
    await session_manager.terminate_session(session.session_id)

    # Should be terminated
    terminated = await session_manager.storage.get_session(session.session_id)
    assert terminated.state == SessionState.TERMINATED


@pytest.mark.asyncio
async def test_terminate_user_sessions(session_manager):
    """Test terminating all user sessions."""
    user_id = "user123"

    # Create multiple sessions
    sessions = []
    for i in range(3):
        session = await session_manager.create_session(
            user_id=user_id,
            access_token=f"access_token_{i}",
        )
        sessions.append(session)

    # Terminate all except first
    await session_manager.terminate_user_sessions(
        user_id,
        except_session_id=sessions[0].session_id,
    )

    # Check states
    for i, session in enumerate(sessions):
        retrieved = await session_manager.storage.get_session(session.session_id)
        if i == 0:
            assert retrieved.state == SessionState.ACTIVE
        else:
            assert retrieved.state == SessionState.TERMINATED


@pytest.mark.asyncio
async def test_cleanup_expired_sessions(session_manager):
    """Test cleanup of expired sessions."""
    # Create some sessions
    sessions = []
    for i in range(3):
        session = await session_manager.create_session(
            user_id=f"user{i}",
            access_token=f"access_token_{i}",
        )
        sessions.append(session)

    # Expire some sessions
    for i in [0, 2]:
        sessions[i].created_at = datetime.utcnow() - timedelta(hours=10)
        sessions[i].last_accessed_at = datetime.utcnow() - timedelta(hours=2)
        await session_manager.storage.save_session(sessions[i])

    # Run cleanup
    cleaned = await session_manager.cleanup_expired_sessions()

    assert cleaned == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
