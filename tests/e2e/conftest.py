"""E2E test configuration - organized fixtures.

This conftest imports fixtures from modular sub-packages:
- fixtures.client: MCP HTTP client fixtures
- fixtures.scenarios: Workflow scenarios and test data
- fixtures.monitoring: Performance tracking and disaster recovery

All authentication fixtures are in tests/conftest.py (root)
"""

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

__all__ = [
    "mcp_client",
    "end_to_end_client",
    "workflow_scenarios",
    "test_data_setup",
    "test_data_with_relationships",
    "e2e_performance_tracker",
    "e2e_test_cleanup",
    "disaster_recovery_scenario",
]
