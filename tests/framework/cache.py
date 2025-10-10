"""
Atoms MCP Test Cache - Implementation specific to Atoms MCP

This module extends the generic BaseTestCache from mcp-QA with Atoms-specific
tool dependencies and framework file mappings.
"""


from mcp_qa.testing.test_cache import BaseTestCache

# Atoms-specific dependency mapping: tool -> framework files it depends on
TOOL_DEPENDENCIES = {
    "entity_tool": [
        "tools/base.py",
        "tools/entity_resolver.py",
        "tools/entity.py",
        "infrastructure/factory.py",
        "errors.py",
    ],
    "entity": [
        "tools/base.py",
        "tools/entity_resolver.py",
        "infrastructure/factory.py",
        "errors.py",
    ],
    "query_tool": [
        "tools/base.py",
        "tools/query.py",
        "infrastructure/factory.py",
        "errors.py",
    ],
    "search_term": [
        "tools/base.py",
        "infrastructure/factory.py",
        "errors.py",
    ],
    "workspace_tool": [
        "tools/base.py",
        "tools/workspace.py",
        "infrastructure/factory.py",
        "errors.py",
    ],
    "workspace": [
        "tools/base.py",
        "infrastructure/factory.py",
        "errors.py",
    ],
    "relationship_tool": [
        "tools/base.py",
        "tools/relationship.py",
        "infrastructure/factory.py",
        "errors.py",
    ],
    "relationship": [
        "tools/base.py",
        "infrastructure/factory.py",
        "errors.py",
    ],
    "workflow_tool": [
        "tools/base.py",
        "tools/workflow.py",
        "infrastructure/factory.py",
        "errors.py",
    ],
    "workflow": [
        "tools/base.py",
        "infrastructure/factory.py",
        "errors.py",
    ],
}

# Atoms framework files that affect all tests
FRAMEWORK_CORE_FILES = [
    "tests/framework/__init__.py",
    "tests/framework/decorators.py",
    "tests/framework/adapters.py",
    "tests/framework/factories.py",
    "tests/framework/validators.py",
    "tests/framework/patterns.py",
]


class TestCache(BaseTestCache):
    """Atoms-specific test cache implementation."""

    def __init__(self, cache_file: str = ".atoms_test_cache.json"):
        """
        Initialize Atoms test cache.

        Args:
            cache_file: Name of the cache file
        """
        super().__init__(cache_file=cache_file)

    def get_tool_dependencies(self) -> dict[str, list[str]]:
        """Get Atoms-specific tool dependency mappings."""
        return TOOL_DEPENDENCIES

    def get_framework_files(self) -> list[str]:
        """Get Atoms-specific framework core files."""
        return FRAMEWORK_CORE_FILES


# Usage Example:
# ===============
#
# from framework.cache import TestCache
# from pathlib import Path
#
# # Initialize cache
# cache = TestCache()
#
# # Before running a test, check if it should be skipped
# test_file = Path(__file__)
# if cache.should_skip("test_entity_create", "entity_tool", test_file):
#     print("Skipping test - cached result is still valid")
#     return
#
# # Run the test
# start = time.time()
# try:
#     run_test()
#     status = "passed"
#     error = None
# except Exception as e:
#     status = "failed"
#     error = str(e)
# duration = time.time() - start
#
# # Record the result
# cache.record("test_entity_create", "entity_tool", status, duration, error, test_file)
#
# # Get cache statistics
# stats = cache.get_stats()
# print(f"Total cached: {stats['total_cached']}, Passed: {stats['passed']}")
#
# # Clear cache for a specific tool when you make changes
# cache.clear_tool("entity_tool")
#
# # Or invalidate based on file changes (useful for file watchers)
# cache.invalidate_by_file(Path("tools/entity.py"))
#
# # Get detailed reason why a test cannot be skipped (for debugging)
# reason = cache.get_invalidation_reason("test_entity_create", "entity_tool", test_file)
# if reason:
#     print(f"Test must run: {reason}")
