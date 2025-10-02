"""ASGI application for Vercel deployment.

This creates a proper ASGI app export that Vercel can import.
Following FastMCP documentation: https://docs.fastmcp.com/deployment/self-hosted
"""

from __future__ import annotations
import os
from starlette.responses import JSONResponse
from server import create_consolidated_server

# Create the FastMCP server instance
mcp = create_consolidated_server()

# Add health check endpoint for Vercel monitoring
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    """Health check endpoint for monitoring."""
    return JSONResponse({
        "status": "healthy",
        "service": "atoms-mcp-server",
        "transport": "http"
    })

# Create ASGI application with custom path
# CRITICAL: stateless_http=True is REQUIRED for serverless environments like Vercel
# This tells the MCP StreamableHTTPSessionManager to not maintain task groups between requests
# Without this, you get "Task group is not initialized" errors in serverless functions
app = mcp.http_app(path="/api/mcp", stateless_http=True)

# Vercel will import the 'app' variable
__all__ = ["app"]
