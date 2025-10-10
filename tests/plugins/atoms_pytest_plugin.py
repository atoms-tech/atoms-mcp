"""
Atoms MCP Pytest Plugin

Integrates AtomsMCPTestRunner features into pytest execution:
- Rich progress display with live stats
- Multiple reporters (JSON, Markdown, Console, FunctionalityMatrix)
- Auth validation before tests
- Performance metrics tracking
- Category-based execution
- Cache management

This plugin extends the generic MCPPytestPlugin base class with
Atoms-specific tool name extraction logic.
"""


try:
    from mcp_qa.execution.pytest_plugin import MCPPytestPlugin, create_pytest_addoption
except ImportError:
    raise ImportError(
        "mcp-QA package not found. Please install it with: pip install -e ../pheno-sdk/mcp-QA"
    )


class AtomsPytestPlugin(MCPPytestPlugin):
    """
    Atoms-specific pytest plugin that extends MCPPytestPlugin.

    Adds Atoms-specific tool name extraction logic while inheriting
    all generic MCP testing features from the base class.
    """

    def _extract_tool_name(self, item) -> str:
        """
        Extract tool name from test item using Atoms-specific logic.

        First tries to get tool name from the test registry, then falls back
        to inferring from test name patterns.
        """
        # Try to get from test registry
        try:
            from tests.framework.decorators import get_test_registry
            registry = get_test_registry()
            test_info = registry.get_tests().get(item.name, {})
            return test_info.get("tool_name", "unknown")
        except:
            pass

        # Try to extract from test name
        test_name = item.name.lower()
        if "workspace" in test_name:
            return "workspace_tool"
        if "entity" in test_name:
            return "entity_tool"
        if "query" in test_name:
            return "query_tool"
        if "relationship" in test_name:
            return "relationship_tool"
        if "workflow" in test_name:
            return "workflow_tool"

        return "unknown"


# Create pytest hooks using factory function from base class
pytest_addoption = create_pytest_addoption(group_name="atoms")


def pytest_configure(config):
    """Register the plugin."""
    config.pluginmanager.register(AtomsPytestPlugin(), "atoms_pytest_plugin")


__all__ = ["AtomsPytestPlugin", "pytest_addoption", "pytest_configure"]
