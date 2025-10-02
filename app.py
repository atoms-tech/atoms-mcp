"""ASGI application for Vercel deployment.

This creates a proper ASGI app export that Vercel can import.
Following FastMCP documentation: https://docs.fastmcp.com/deployment/self-hosted
"""

from __future__ import annotations
import os
import anyio
from contextlib import asynccontextmanager
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

# CRITICAL FIX for Vercel serverless:
# The issue is that MCP's stateless mode still requires a task group, which is
# normally created in the lifespan context. But in Vercel serverless, the lifespan
# doesn't persist across invocations, so we need to ensure the task group is
# recreated for each request.

# Find the session manager and wrap it to auto-create task groups
session_manager = None
for route in app.routes:
    if hasattr(route, 'endpoint') and hasattr(route.endpoint, '__self__'):
        endpoint = route.endpoint.__self__
        if hasattr(endpoint, 'session_manager'):
            session_manager = endpoint.session_manager
            break

if session_manager:
    # Store the original handle_request method
    original_handle_request = session_manager.handle_request

    # Create a wrapper that ensures task group exists
    async def handle_request_with_task_group(scope, receive, send):
        """Wrapper that creates a task group if needed for serverless environments."""
        if session_manager._task_group is None:
            # Create a temporary task group for this request
            async with anyio.create_task_group() as tg:
                session_manager._task_group = tg
                try:
                    await original_handle_request(scope, receive, send)
                finally:
                    # Don't clear it here - let it be reused if possible
                    pass
        else:
            # Task group already exists (from lifespan or previous request)
            await original_handle_request(scope, receive, send)

    # Replace the method
    session_manager.handle_request = handle_request_with_task_group
    print("✅ Patched session_manager to auto-create task groups for serverless")
else:
    print("⚠️  Could not find session_manager to patch")

# Vercel will import the 'app' variable
__all__ = ["app"]
