"""Comprehensive test configuration with mock and live service support."""

import pytest
import os
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any, Optional


class MockServiceFactory:
    """Factory for creating mock services."""

    @staticmethod
    def create_mock_database() -> Mock:
        """Create mock database service."""
        db = Mock()
        db.connect = Mock(return_value=True)
        db.execute = Mock(return_value={"success": True})
        db.query = Mock(return_value=[{"id": "1", "name": "test"}])
        db.close = Mock(return_value=True)
        return db

    @staticmethod
    def create_mock_cache() -> Mock:
        """Create mock cache service."""
        cache_data = {}

        def mock_set(key, value, ttl=None):
            cache_data[key] = value
            return True

        def mock_get(key):
            return cache_data.get(key)

        def mock_delete(key):
            if key in cache_data:
                del cache_data[key]
            return True

        def mock_clear():
            cache_data.clear()
            return True

        cache = Mock()
        cache.connect = Mock(return_value=True)
        cache.get = Mock(side_effect=mock_get)
        cache.set = Mock(side_effect=mock_set)
        cache.delete = Mock(side_effect=mock_delete)
        cache.clear = Mock(side_effect=mock_clear)
        return cache

    @staticmethod
    def create_mock_auth() -> Mock:
        """Create mock auth service."""
        auth = Mock()
        auth.validate_token = Mock(return_value={"user_id": "user-1", "valid": True})
        auth.get_user = Mock(return_value={"id": "user-1", "email": "test@example.com"})
        auth.create_session = Mock(return_value={"session_id": "sess-1"})
        return auth

    @staticmethod
    def create_mock_search() -> Mock:
        """Create mock search service."""
        search = Mock()
        search.index = Mock(return_value=True)
        search.search = Mock(return_value=[{"id": "1", "score": 0.95}])
        search.delete = Mock(return_value=True)
        return search


class LiveServiceFactory:
    """Factory for creating live service connections."""

    @staticmethod
    def create_live_database() -> Optional[Any]:
        """Create live database connection."""
        if os.getenv("USE_LIVE_SERVICES") != "true":
            return None
        
        try:
            import psycopg2
            conn = psycopg2.connect(
                host=os.getenv("DB_HOST", "localhost"),
                port=os.getenv("DB_PORT", "5432"),
                database=os.getenv("DB_NAME", "test_db"),
                user=os.getenv("DB_USER", "postgres"),
                password=os.getenv("DB_PASSWORD", "")
            )
            return conn
        except Exception as e:
            pytest.skip(f"Live database not available: {e}")

    @staticmethod
    def create_live_cache() -> Optional[Any]:
        """Create live cache connection."""
        if os.getenv("USE_LIVE_SERVICES") != "true":
            return None
        
        try:
            import redis
            conn = redis.Redis(
                host=os.getenv("CACHE_HOST", "localhost"),
                port=int(os.getenv("CACHE_PORT", "6379")),
                db=0
            )
            conn.ping()
            return conn
        except Exception as e:
            pytest.skip(f"Live cache not available: {e}")

    @staticmethod
    def create_live_auth() -> Optional[Any]:
        """Create live auth service."""
        if os.getenv("USE_LIVE_SERVICES") != "true":
            return None
        
        try:
            from auth.providers import get_auth_provider
            return get_auth_provider()
        except Exception as e:
            pytest.skip(f"Live auth not available: {e}")


@pytest.fixture(scope="session")
def service_mode():
    """Determine service mode (mock or live)."""
    return os.getenv("SERVICE_MODE", "mock")


@pytest.fixture
def mock_database():
    """Provide mock database."""
    return MockServiceFactory.create_mock_database()


@pytest.fixture
def mock_cache():
    """Provide mock cache."""
    return MockServiceFactory.create_mock_cache()


@pytest.fixture
def mock_auth():
    """Provide mock auth."""
    return MockServiceFactory.create_mock_auth()


@pytest.fixture
def mock_search():
    """Provide mock search."""
    return MockServiceFactory.create_mock_search()


@pytest.fixture
def live_database():
    """Provide live database."""
    return LiveServiceFactory.create_live_database()


@pytest.fixture
def live_cache():
    """Provide live cache."""
    return LiveServiceFactory.create_live_cache()


@pytest.fixture
def live_auth():
    """Provide live auth."""
    return LiveServiceFactory.create_live_auth()


@pytest.fixture
def database(service_mode, mock_database, live_database):
    """Provide database (mock or live based on mode)."""
    if service_mode == "live":
        return live_database
    return mock_database


@pytest.fixture
def cache(service_mode, mock_cache, live_cache):
    """Provide cache (mock or live based on mode)."""
    if service_mode == "live":
        return live_cache
    return mock_cache


@pytest.fixture
def auth(service_mode, mock_auth, live_auth):
    """Provide auth (mock or live based on mode)."""
    if service_mode == "live":
        return live_auth
    return mock_auth


@pytest.fixture
def search(service_mode, mock_search):
    """Provide search service."""
    return mock_search


@pytest.fixture
def test_context() -> Dict[str, Any]:
    """Provide test context."""
    return {
        "user_id": "test-user-1",
        "org_id": "test-org-1",
        "project_id": "test-project-1",
        "workspace_id": "test-workspace-1"
    }


@pytest.fixture
def test_entity() -> Dict[str, Any]:
    """Provide test entity."""
    return {
        "id": "entity-1",
        "type": "requirement",
        "name": "Test Requirement",
        "description": "Test description",
        "status": "active"
    }


@pytest.fixture
def test_relationship() -> Dict[str, Any]:
    """Provide test relationship."""
    return {
        "source_id": "entity-1",
        "target_id": "entity-2",
        "type": "depends_on",
        "metadata": {"priority": "high"}
    }


@pytest.fixture
def e2e_auth_token():
    """Get authenticated token for e2e/live service tests.

    Uses WorkOS User Management API (password grant) to authenticate.
    This is the standard, reliable way to get JWT tokens for testing.
    """
    import logging
    import asyncio

    logger = logging.getLogger(__name__)

    # Use WorkOS User Management (password grant) - always available
    from tests.utils.workos_auth import authenticate_with_workos

    email = os.getenv("ATOMS_TEST_EMAIL", "kooshapari@kooshapari.com")
    password = os.getenv("ATOMS_TEST_PASSWORD", "ASD3on54_Pax90")

    logger.info(f"🔐 Attempting WorkOS authentication for {email}...")

    try:
        token = asyncio.run(authenticate_with_workos(email, password))
        if token:
            logger.info(f"✅ Got WorkOS token for {email}")
            return token
    except Exception as e:
        logger.warning(f"⚠️  WorkOS authentication failed: {e}")

    # Fallback: try environment variable
    if os.getenv("ATOMS_TEST_AUTH_TOKEN"):
        logger.info("✅ Using ATOMS_TEST_AUTH_TOKEN from environment")
        return os.getenv("ATOMS_TEST_AUTH_TOKEN")

    # No token available - return None (tests will skip)
    logger.warning("⚠️  No authentication token available for e2e/live tests")
    logger.warning("   Set ATOMS_TEST_EMAIL, ATOMS_TEST_PASSWORD, or ATOMS_TEST_AUTH_TOKEN")
    return None

