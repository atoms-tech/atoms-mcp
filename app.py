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

# Create ASGI application with custom path
# This is the proper way to deploy FastMCP on Vercel per docs
app = mcp.http_app(path="/api/mcp")

# Add health check endpoint for Vercel monitoring
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    """Health check endpoint for monitoring."""
    return JSONResponse({
        "status": "healthy",
        "service": "atoms-mcp-server",
        "transport": "http"
    })

# Vercel will import the 'app' variable
__all__ = ["app"]
