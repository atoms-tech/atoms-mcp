"""Fixtures for integration workspace tests.

Provides call_mcp fixture for integration tests that need real database access.
"""

import pytest
import pytest_asyncio
import time
from typing import Tuple, Dict, Any


@pytest_asyncio.fixture
async def call_mcp(mcp_client_http):
    """Provide call_mcp helper for integration tests.

    This fixture wraps the HTTP client to provide timing information
    and consistent response handling for integration tests.

    mcp_client_http is already a callable function that calls tools,
    so we just wrap it to add timing information.
    """
    async def _call(tool_name: str, params: Dict[str, Any]) -> Tuple[Dict[str, Any], float]:
        """Call a tool and return result with timing."""
        start = time.time()
        try:
            # mcp_client_http is already the call_tool function
            result = await mcp_client_http(tool_name, params)
            elapsed = time.time() - start

            # Result should already be a dict with success/data/error structure
            if isinstance(result, dict):
                return result, elapsed
            else:
                return {"data": result}, elapsed
        except Exception as e:
            elapsed = time.time() - start
            return {"success": False, "error": str(e)}, elapsed

    return _call

