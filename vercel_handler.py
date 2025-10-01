"""Vercel serverless handler for Atoms MCP Server.

This adapts the FastMCP server to work as a Vercel serverless function.
"""

from server import create_consolidated_server
from starlette.applications import Starlette
from starlette.routing import Mount

# Create the FastMCP server
mcp_server = create_consolidated_server()

# Get the underlying Starlette app
# FastMCP wraps a Starlette app when using HTTP transport
app = mcp_server._app if hasattr(mcp_server, '_app') else mcp_server

# Vercel expects an 'app' or 'handler' export
handler = app
