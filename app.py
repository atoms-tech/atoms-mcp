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
app = mcp.http_app(path="/api/mcp", stateless_http=True)

# WORKAROUND: Manually patch the session manager to ensure stateless mode
# This is needed because stateless_http parameter isn't propagating correctly
try:
    # Access the HTTP handler from the app routes
    for route in app.routes:
        if hasattr(route, 'app') and hasattr(route.app, 'session_manager'):
            route.app.session_manager.stateless = True
            print("✅ Patched session_manager.stateless = True")
        elif hasattr(route, 'endpoint'):
            # Try to find session manager in endpoint
            endpoint = route.endpoint
            if hasattr(endpoint, '__self__') and hasattr(endpoint.__self__, 'session_manager'):
                endpoint.__self__.session_manager.stateless = True
                print("✅ Patched endpoint session_manager.stateless = True")
except Exception as e:
    print(f"⚠️  Could not patch session_manager: {e}")

# Vercel will import the 'app' variable
__all__ = ["app"]
