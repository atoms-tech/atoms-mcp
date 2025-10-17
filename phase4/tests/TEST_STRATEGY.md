# Phase 4 Testing Strategy

## Overview

Comprehensive testing strategy for Phase 4 token refresh and session management implementation, covering unit tests, integration tests, performance tests, and security tests.

## Test Categories

### 1. Unit Tests

#### Token Refresh Service Tests
```python
# tests/unit/test_token_refresh.py
- test_refresh_valid_token
- test_refresh_expired_token
- test_refresh_with_rotation
- test_refresh_without_rotation
- test_proactive_refresh_triggers
- test_refresh_rate_limiting
- test_refresh_token_metadata_storage
```

#### Session Manager Tests
```python
# tests/unit/test_session_manager.py
- test_create_session
- test_get_session
- test_update_session_activity
- test_session_expiration
- test_session_idle_timeout
- test_multi_session_support
- test_session_limit_enforcement
- test_device_binding
- test_ip_validation
```

#### Revocation Service Tests
```python
# tests/unit/test_revocation.py
- test_revoke_access_token
- test_revoke_refresh_token
- test_cascade_revocation
- test_revocation_list_management
- test_is_token_revoked_check
- test_cleanup_expired_revocations
```

#### Storage Backend Tests
```python
# tests/unit/test_storage.py
- test_get_set_operations
- test_expiration_handling
- test_atomic_operations
- test_set_operations
- test_scan_patterns
- test_distributed_locking
```

### 2. Integration Tests

#### End-to-End Token Flow Tests
```python
# tests/integration/test_token_flow.py
- test_complete_refresh_flow
- test_token_rotation_flow
- test_multi_device_session_flow
- test_revocation_propagation
- test_rate_limiting_integration
```

#### API Endpoint Tests
```python
# tests/integration/test_endpoints.py
- test_refresh_endpoint
- test_revoke_endpoint
- test_introspect_endpoint
- test_sessions_list_endpoint
- test_session_terminate_endpoint
```

### 3. Performance Tests

#### Load Testing
```python
# tests/performance/test_load.py
- test_concurrent_refresh_requests
- test_session_creation_rate
- test_storage_operation_throughput
- test_rate_limiter_performance
```

#### Latency Tests
```python
# tests/performance/test_latency.py
- test_token_refresh_p95_latency
- test_session_lookup_p95_latency
- test_revocation_p95_latency
```

### 4. Security Tests

#### Token Security Tests
```python
# tests/security/test_token_security.py
- test_token_rotation_security
- test_refresh_token_reuse_prevention
- test_token_hijacking_prevention
- test_timing_attack_resistance
```

#### Session Security Tests
```python
# tests/security/test_session_security.py
- test_session_fixation_prevention
- test_device_change_detection
- test_ip_change_handling
- test_suspicious_activity_detection
```

## Test Fixtures

### Base Test Fixtures
```python
# phase4/tests/fixtures.py

import pytest
from typing import AsyncGenerator
from phase4.storage.memory import MemoryBackend
from phase4.services import TokenRefreshService, SessionManager
from phase4.models import TokenPair, DeviceInfo

@pytest.fixture
async def storage_backend() -> AsyncGenerator[MemoryBackend, None]:
    """Provide in-memory storage for testing."""
    backend = MemoryBackend()
    yield backend
    await backend.clear()

@pytest.fixture
async def token_service(storage_backend) -> TokenRefreshService:
    """Provide token refresh service."""
    return TokenRefreshService(storage=storage_backend)

@pytest.fixture
async def session_manager(storage_backend) -> SessionManager:
    """Provide session manager."""
    return SessionManager(storage=storage_backend)

@pytest.fixture
def sample_token_pair() -> TokenPair:
    """Provide sample token pair."""
    return TokenPair(
        access_token="test_access_token",
        refresh_token="test_refresh_token",
        access_expires_in=3600,
        refresh_expires_in=604800,
    )

@pytest.fixture
def sample_device_info() -> DeviceInfo:
    """Provide sample device info."""
    return DeviceInfo.from_user_agent(
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
    )
```

## Test Implementation Examples

### Unit Test Example
```python
# tests/unit/test_token_refresh.py

import pytest
from datetime import datetime, timedelta
from phase4.services import TokenRefreshService
from phase4.models import TokenPair

@pytest.mark.asyncio
async def test_refresh_valid_token(token_service, sample_token_pair):
    """Test refreshing a valid token."""
    # Setup
    session_id = "test_session_123"

    # Execute
    new_tokens = await token_service.refresh_token(
        sample_token_pair.refresh_token,
        session_id
    )

    # Assert
    assert new_tokens.access_token != sample_token_pair.access_token
    assert new_tokens.expires_in == 3600
    assert new_tokens.token_type == "Bearer"

@pytest.mark.asyncio
async def test_refresh_with_rotation(token_service, sample_token_pair):
    """Test token refresh with rotation enabled."""
    # Setup
    token_service.rotation_enabled = True
    session_id = "test_session_456"

    # Execute
    new_tokens = await token_service.refresh_token(
        sample_token_pair.refresh_token,
        session_id,
        force_rotation=True
    )

    # Assert
    assert new_tokens.refresh_token != sample_token_pair.refresh_token

    # Old refresh token should fail
    with pytest.raises(ValueError, match="Invalid refresh token"):
        await token_service.refresh_token(
            sample_token_pair.refresh_token,
            session_id
        )
```

### Integration Test Example
```python
# tests/integration/test_token_flow.py

import pytest
import httpx
from phase4.endpoints import app

@pytest.mark.asyncio
async def test_complete_refresh_flow():
    """Test complete token refresh flow."""
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        # Initial token refresh
        response = await client.post(
            "/auth/token/refresh",
            json={
                "refresh_token": "valid_refresh_token",
                "session_id": "session_123"
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Use new tokens
        new_access = data["access_token"]
        new_refresh = data.get("refresh_token")

        # Refresh again with new token
        response = await client.post(
            "/auth/token/refresh",
            json={
                "refresh_token": new_refresh or "valid_refresh_token",
                "session_id": "session_123"
            }
        )

        assert response.status_code == 200
```

### Performance Test Example
```python
# tests/performance/test_load.py

import asyncio
import pytest
from phase4.services import TokenRefreshService

@pytest.mark.asyncio
async def test_concurrent_refresh_requests(token_service):
    """Test handling concurrent refresh requests."""

    async def refresh_task(session_id: str):
        return await token_service.refresh_token(
            "test_refresh_token",
            session_id
        )

    # Create 100 concurrent refresh tasks
    tasks = [
        refresh_task(f"session_{i}")
        for i in range(100)
    ]

    start = asyncio.get_event_loop().time()
    results = await asyncio.gather(*tasks, return_exceptions=True)
    duration = asyncio.get_event_loop().time() - start

    # Check results
    successful = sum(1 for r in results if not isinstance(r, Exception))

    assert successful > 0
    assert duration < 5.0  # Should complete within 5 seconds

    # Calculate throughput
    throughput = successful / duration
    assert throughput > 10  # At least 10 requests per second
```

## Test Configuration

### pytest.ini
```ini
[tool:pytest]
testpaths = phase4/tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
markers =
    unit: Unit tests
    integration: Integration tests
    performance: Performance tests
    security: Security tests
    slow: Slow running tests
```

### Test Environment Variables
```bash
# .env.test
STORAGE_PROVIDER=memory
ACCESS_TOKEN_EXPIRES_IN=60
REFRESH_TOKEN_EXPIRES_IN=300
REFRESH_TOKEN_ROTATION=true
REFRESH_BUFFER_SECONDS=10
MAX_SESSIONS_PER_USER=5
SESSION_IDLE_TIMEOUT=120
RATE_LIMIT_REFRESH_PER_MINUTE=20
ENABLE_AUDIT_LOGGING=true
```

## CI/CD Integration

### GitHub Actions Workflow
```yaml
# .github/workflows/phase4-tests.yml
name: Phase 4 Tests

on:
  push:
    paths:
      - 'phase4/**'
      - 'tests/**'
  pull_request:
    paths:
      - 'phase4/**'
      - 'tests/**'

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        uv sync
        pip install pytest pytest-asyncio pytest-cov

    - name: Run unit tests
      run: pytest phase4/tests/unit -v --cov=phase4

    - name: Run integration tests
      run: pytest phase4/tests/integration -v

    - name: Run security tests
      run: pytest phase4/tests/security -v

    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

## Test Coverage Goals

- **Unit Tests**: 90% code coverage
- **Integration Tests**: All critical paths covered
- **Performance Tests**: Meet latency targets
- **Security Tests**: All OWASP recommendations covered

## Test Execution

### Run All Tests
```bash
pytest phase4/tests -v
```

### Run Specific Categories
```bash
# Unit tests only
pytest phase4/tests -m unit

# Integration tests
pytest phase4/tests -m integration

# Performance tests
pytest phase4/tests -m performance

# Security tests
pytest phase4/tests -m security
```

### Run with Coverage
```bash
pytest phase4/tests --cov=phase4 --cov-report=html
```

## Monitoring Test Results

### Key Metrics to Track
- Test pass rate
- Code coverage percentage
- Performance test latencies
- Security test findings
- Flaky test frequency

### Test Reports
- Generate HTML coverage reports
- Performance test results dashboard
- Security scan reports
- Test trend analysis