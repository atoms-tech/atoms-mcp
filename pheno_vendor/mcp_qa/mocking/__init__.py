"""
MCP-QA Mocking - Mock MCP Servers and Tools

Provides:
- MockMCPServer for unit testing
- MockTool, MockResource, MockPrompt builders
- Response builders for common scenarios
"""

from mcp_qa.mocking.server import MockMCPServer
from mcp_qa.mocking.tools import MockTool
from mcp_qa.mocking.resources import MockResource
from mcp_qa.mocking.prompts import MockPrompt
from mcp_qa.mocking.builders import (
    build_success_response,
    build_error_response,
    build_list_response,
)

__all__ = [
    "MockMCPServer",
    "MockTool",
    "MockResource",
    "MockPrompt",
    "build_success_response",
    "build_error_response",
    "build_list_response",
]
