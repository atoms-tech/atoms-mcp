"""
MCP-QA Framework - Core Testing Framework Components

Provides:
- TestCache for intelligent test result caching
- @mcp_test decorator for test registration
- Test discovery and organization
- Test execution utilities
"""

from mcp_qa.framework.cache import TestCache
from mcp_qa.framework.decorators import (
    mcp_test,
    require_auth,
    skip_if,
    timeout,
    retry,
    cache_result,
    get_test_registry,
)
from mcp_qa.framework.discovery import (
    discover_tests,
    organize_tests,
    filter_tests,
)

__all__ = [
    # Cache
    "TestCache",

    # Decorators
    "mcp_test",
    "require_auth",
    "skip_if",
    "timeout",
    "retry",
    "cache_result",
    "get_test_registry",

    # Discovery
    "discover_tests",
    "organize_tests",
    "filter_tests",
]
