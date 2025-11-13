"""End-to-end tests for Atoms MCP.

This package contains end-to-end integration tests organized by functionality:

- test_auth: Authentication and JWT validation tests
- test_database: Database operations and RLS tests
- test_crud: CRUD operation tests with auth context
- test_performance: Performance and load tests
- test_resilience: Error recovery and resilience tests
- test_scenarios: End-to-end integration scenario tests
"""

# Import all test modules to ensure they're discoverable
# This ensures pytest can find all tests when running on the e2e package

from . import test_auth
from . import test_database
from . import test_crud
from . import test_performance
from . import test_resilience
from . import test_scenarios

__all__ = [
    'test_auth',
    'test_database',
    'test_crud',
    'test_performance',
    'test_resilience',
    'test_scenarios',
]
