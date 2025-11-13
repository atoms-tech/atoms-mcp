"""Test framework and utilities for atoms-mcp-prod tests.

Provides:
- mcp_test: Decorator for MCP tool tests
- DataGenerator: Test data factories
- Validators: Response validation helpers
"""

import functools
from typing import Any, Callable, Optional, Dict
from .data_generators import DataGenerator
from .validators import ResponseValidator, FieldValidator

__all__ = [
    "mcp_test",
    "DataGenerator",
    "ResponseValidator",
    "FieldValidator",
    "validators",
]


def mcp_test(
    tool_name: str,
    category: str = "general",
    priority: int = 5,
    markers: Optional[list[str]] = None,
) -> Callable:
    """Decorator for MCP tool tests.
    
    Adds metadata to test functions for better organization and filtering.
    
    Args:
        tool_name: Name of the MCP tool being tested (e.g., "entity_tool")
        category: Test category (e.g., "entity_create", "entity_list")
        priority: Priority level (1-10, higher = more important)
        markers: Additional pytest markers to apply
    
    Example:
        @mcp_test(tool_name="entity_tool", category="entity_create", priority=9)
        async def test_create_organization(client):
            result = await client.call_tool("entity_tool", {...})
            assert result["success"]
    """
    def decorator(func: Callable) -> Callable:
        # Store metadata on function
        func._mcp_test_meta = {
            "tool_name": tool_name,
            "category": category,
            "priority": priority,
            "markers": markers or [],
        }

        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            return await func(*args, **kwargs)

        # Copy metadata to wrapper
        wrapper._mcp_test_meta = func._mcp_test_meta
        return wrapper

    return decorator


# Make validators accessible as a module
class validators:
    """Validators module re-export for convenience."""
    FieldValidator = FieldValidator
    ResponseValidator = ResponseValidator
