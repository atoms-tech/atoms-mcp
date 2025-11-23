"""E2E test configuration - organized fixtures.

This conftest imports fixtures from modular sub-packages:
- fixtures.client: MCP HTTP client fixtures
- fixtures.scenarios: Workflow scenarios and test data
- fixtures.monitoring: Performance tracking and disaster recovery

All authentication fixtures are in tests/conftest.py (root)
"""

import os
import pytest
import pytest_asyncio

# Import all fixtures from submodules to make them available to tests
from tests.e2e.fixtures.client import mcp_client, end_to_end_client
from tests.e2e.fixtures.scenarios import (
    workflow_scenarios,
    test_data_setup,
    test_data_with_relationships,
)
from tests.e2e.fixtures.monitoring import (
    e2e_performance_tracker,
    e2e_test_cleanup,
    disaster_recovery_scenario,
)


@pytest_asyncio.fixture
async def e2e_auth_token():
    """Get authenticated token for e2e tests.

    Uses WorkOS User Management API (password grant) to authenticate.
    This is the standard, reliable way to get JWT tokens for testing.
    """
    import logging

    logger = logging.getLogger(__name__)

    # Use WorkOS User Management (password grant) - always available
    from tests.utils.workos_auth import authenticate_with_workos

    email = os.getenv("ATOMS_TEST_EMAIL", "kooshapari@kooshapari.com")
    password = os.getenv("ATOMS_TEST_PASSWORD", "ASD3on54_Pax90")

    logger.info(f"🔐 Attempting WorkOS authentication for {email}...")
    token = await authenticate_with_workos(email, password)
    if token:
        logger.info(f"✅ Got WorkOS token for {email}")
        return token

    # Fallback: try environment variable
    if os.getenv("ATOMS_TEST_AUTH_TOKEN"):
        logger.info("✅ Using ATOMS_TEST_AUTH_TOKEN from environment")
        return os.getenv("ATOMS_TEST_AUTH_TOKEN")

    # No token available - skip e2e tests
    logger.warning("⚠️  No authentication token available for e2e tests")
    logger.warning("   Set ATOMS_TEST_EMAIL, ATOMS_TEST_PASSWORD, or ATOMS_TEST_AUTH_TOKEN")
    pytest.skip("No authentication token available for e2e tests")


__all__ = [
    "mcp_client",
    "end_to_end_client",
    "e2e_auth_token",
    "workflow_scenarios",
    "test_data_setup",
    "test_data_with_relationships",
    "e2e_performance_tracker",
    "e2e_test_cleanup",
    "disaster_recovery_scenario",
]
