"""
Tests for Security Service

Comprehensive test suite for rate limiting, hijacking detection, and security monitoring.
"""

from datetime import datetime, timedelta

import pytest

from ..models import AuditAction, AuditLog, DeviceFingerprint, Session
from ..security import RateLimitError, RateLimitRule, SecurityService
from ..storage.base import InMemoryStorage


@pytest.fixture
async def storage():
    """Create in-memory storage for testing."""
    return InMemoryStorage()


@pytest.fixture
async def security_service(storage):
    """Create security service for testing."""
    return SecurityService(
        storage=storage,
        enable_rate_limiting=True,
        enable_hijacking_detection=True,
    )


@pytest.mark.asyncio
async def test_rate_limiting_within_limit(security_service):
    """Test rate limiting when within limit."""
    # Should pass first few requests
    for _ in range(5):
        result = await security_service.check_rate_limit(
            rule_name="token_refresh",
            key="user_123",
        )
        assert result is True


@pytest.mark.asyncio
async def test_rate_limiting_exceeded(security_service):
    """Test rate limiting when limit exceeded."""
    # Exhaust limit
    for _ in range(10):
        await security_service.check_rate_limit(
            rule_name="token_refresh",
            key="user_123",
        )

    # Next request should fail
    with pytest.raises(RateLimitError):
        await security_service.check_rate_limit(
            rule_name="token_refresh",
            key="user_123",
        )


@pytest.mark.asyncio
async def test_rate_limiting_per_key(security_service):
    """Test rate limiting is per key."""
    # Exhaust limit for user1
    for _ in range(10):
        await security_service.check_rate_limit(
            rule_name="token_refresh",
            key="user_1",
        )

    # user_1 should be rate limited
    with pytest.raises(RateLimitError):
        await security_service.check_rate_limit(
            rule_name="token_refresh",
            key="user_1",
        )

    # user_2 should still work
    result = await security_service.check_rate_limit(
        rule_name="token_refresh",
        key="user_2",
    )
    assert result is True


@pytest.mark.asyncio
async def test_add_custom_rate_limit_rule(security_service):
    """Test adding custom rate limit rule."""
    rule = RateLimitRule(
        name="custom_rule",
        max_requests=5,
        window_seconds=60,
        exponential_backoff=True,
    )

    security_service.add_rate_limit_rule(rule)

    # Should enforce custom rule
    for _ in range(5):
        await security_service.check_rate_limit(
            rule_name="custom_rule",
            key="test_key",
        )

    with pytest.raises(RateLimitError):
        await security_service.check_rate_limit(
            rule_name="custom_rule",
            key="test_key",
        )


@pytest.mark.asyncio
async def test_detect_session_hijacking_same_device(security_service):
    """Test hijacking detection with same device."""
    fingerprint = DeviceFingerprint(
        user_agent="Mozilla/5.0",
        platform="MacIntel",
        timezone="America/New_York",
    )

    session = Session(
        session_id="session_123",
        user_id="user_123",
        access_token="token",
        device_fingerprint=fingerprint,
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0",
    )

    # Same device - should not be suspicious
    is_suspicious, risk_score, reasons = await security_service.detect_session_hijacking(
        session=session,
        current_ip="192.168.1.100",
        current_fingerprint=fingerprint,
        current_user_agent="Mozilla/5.0",
    )

    assert is_suspicious is False
    assert risk_score == 0.0
    assert len(reasons) == 0


@pytest.mark.asyncio
async def test_detect_session_hijacking_different_ip(security_service):
    """Test hijacking detection with different IP."""
    fingerprint = DeviceFingerprint(
        user_agent="Mozilla/5.0",
        platform="MacIntel",
        timezone="America/New_York",
    )

    session = Session(
        session_id="session_123",
        user_id="user_123",
        access_token="token",
        device_fingerprint=fingerprint,
        ip_address="192.168.1.100",
    )

    # Different IP - should be suspicious
    is_suspicious, risk_score, reasons = await security_service.detect_session_hijacking(
        session=session,
        current_ip="10.0.0.1",
        current_fingerprint=fingerprint,
    )

    assert is_suspicious is True
    assert risk_score > 0.0
    assert any("IP address changed" in r for r in reasons)


@pytest.mark.asyncio
async def test_detect_session_hijacking_different_device(security_service):
    """Test hijacking detection with different device."""
    original_fingerprint = DeviceFingerprint(
        user_agent="Mozilla/5.0",
        platform="MacIntel",
        timezone="America/New_York",
    )

    different_fingerprint = DeviceFingerprint(
        user_agent="Different Browser",
        platform="Windows",
        timezone="Europe/London",
    )

    session = Session(
        session_id="session_123",
        user_id="user_123",
        access_token="token",
        device_fingerprint=original_fingerprint,
        ip_address="192.168.1.100",
    )

    # Different device - should be suspicious
    is_suspicious, risk_score, reasons = await security_service.detect_session_hijacking(
        session=session,
        current_ip="192.168.1.100",
        current_fingerprint=different_fingerprint,
    )

    assert is_suspicious is True
    assert risk_score > 0.0
    assert any("fingerprint mismatch" in r.lower() for r in reasons)


@pytest.mark.asyncio
async def test_detect_suspicious_activity(security_service, storage):
    """Test suspicious activity detection."""
    user_id = "user_123"

    # Create multiple failed login attempts
    for i in range(5):
        log = AuditLog(
            action=AuditAction.LOGIN_FAILURE,
            user_id=user_id,
            timestamp=datetime.utcnow() - timedelta(minutes=i),
        )
        await storage.save_audit_log(log)

    # Should detect suspicious activity
    is_suspicious, risk_score, reasons = await security_service.detect_suspicious_activity(
        user_id=user_id,
        activity_type="login",
    )

    assert is_suspicious is True
    assert risk_score > 0.0
    assert any("failed login" in r.lower() for r in reasons)


@pytest.mark.asyncio
async def test_security_summary(security_service, storage):
    """Test getting security summary."""
    user_id = "user_123"

    # Create various audit logs
    actions = [
        AuditAction.LOGIN_SUCCESS,
        AuditAction.LOGIN_FAILURE,
        AuditAction.SESSION_CREATED,
        AuditAction.SUSPICIOUS_ACTIVITY,
    ]

    for action in actions:
        log = AuditLog(
            action=action,
            user_id=user_id,
            is_suspicious=(action == AuditAction.SUSPICIOUS_ACTIVITY),
            risk_score=0.8 if action == AuditAction.SUSPICIOUS_ACTIVITY else 0.0,
        )
        await storage.save_audit_log(log)

    # Get summary
    summary = await security_service.get_security_summary(
        user_id=user_id,
        hours=24,
    )

    assert summary["total_events"] == 4
    assert summary["suspicious_events"] == 1
    assert summary["failed_logins"] == 1
    assert summary["successful_logins"] == 1


@pytest.mark.asyncio
async def test_log_security_event(security_service, storage):
    """Test logging security events."""
    await security_service.log_security_event(
        event_type="login_success",
        user_id="user_123",
        session_id="session_123",
        details="User logged in successfully",
        risk_score=0.0,
    )

    # Verify log was created
    logs = await storage.get_user_audit_logs("user_123")
    assert len(logs) == 1
    assert logs[0].action == AuditAction.LOGIN_SUCCESS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
