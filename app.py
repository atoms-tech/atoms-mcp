"""ASGI application for Vercel deployment.

This creates a proper ASGI app export that Vercel can import.
Following FastMCP documentation: https://docs.fastmcp.com/deployment/self-hosted
"""

from __future__ import annotations
import os
import sys
import traceback
import anyio
from contextlib import asynccontextmanager
from starlette.responses import JSONResponse, PlainTextResponse

# Add the current directory to Python path for Vercel serverless environment
# This ensures that imports like 'infrastructure', 'tools', etc. work correctly
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
# Also add /var/task explicitly for Vercel
if '/var/task' not in sys.path and os.path.exists('/var/task'):
    sys.path.insert(0, '/var/task')

# Try to create the FastMCP server instance with error handling
server_creation_error = None
try:
    from server import create_consolidated_server
    mcp = create_consolidated_server()
    print("✅ Server created successfully with tools", file=sys.stderr)
except Exception as e:
    # If server creation fails, create a minimal error app
    server_creation_error = str(e)
    print(f"❌ ERROR: Failed to create server: {e}", file=sys.stderr)
    traceback.print_exc()

    # Create a minimal FastMCP instance for error reporting
    from fastmcp import FastMCP
    mcp = FastMCP("atoms-mcp-error", dependencies=[])
    print("⚠️  Created error MCP instance (no tools)", file=sys.stderr)

# Add root route handler
@mcp.custom_route("/", methods=["GET"])
async def root(request):
    """Root endpoint with service information."""
    try:
        response_data = {
            "service": "Atoms MCP Server",
            "version": "1.0.0",
            "endpoints": {
                "mcp": "/api/mcp",
                "health": "/health",
                "auth_start": "/auth/start",
                "auth_complete": "/auth/complete"
            },
            "status": "running" if not server_creation_error else "degraded"
        }
        if server_creation_error:
            response_data["error"] = server_creation_error
            response_data["warning"] = "Server created with error - tools may not be available"
        return JSONResponse(response_data)
    except Exception as e:
        return PlainTextResponse(f"Error: {e}\n{traceback.format_exc()}", status_code=500)

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
_base_app = mcp.http_app(path="/api/mcp", stateless_http=True)

# Add compression middleware
# NOTE: SessionMiddleware is NOT needed - FastMCP's AuthKitProvider handles auth
from starlette.middleware.gzip import GZipMiddleware

# Wrap with compression only
app = GZipMiddleware(_base_app, minimum_size=500)  # Compress responses >500 bytes

# CRITICAL FIX for Vercel serverless:
# The issue is that MCP's stateless mode still requires a task group, which is
# normally created in the lifespan context. But in Vercel serverless, the lifespan
# doesn't persist across invocations, so we need to ensure the task group is
# recreated for each request.

# Patch the StreamableHTTPSessionManager directly
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
import inspect

# Store the original handle_request method
_original_handle_request = StreamableHTTPSessionManager.handle_request

# Create a wrapper that ensures task group exists
async def _patched_handle_request(self, scope, receive, send):
    """Wrapper that creates a task group if needed for serverless environments."""
    if self._task_group is None:
        # Create a temporary task group for this request
        async with anyio.create_task_group() as tg:
            self._task_group = tg
            try:
                await _original_handle_request(self, scope, receive, send)
            finally:
                # Clear the task group after request completes
                self._task_group = None
    else:
        # Task group already exists (from lifespan or previous request)
        await _original_handle_request(self, scope, receive, send)

# Monkey patch the class method
StreamableHTTPSessionManager.handle_request = _patched_handle_request
print("✅ Patched StreamableHTTPSessionManager.handle_request for serverless deployment")

# Vercel will import the 'app' variable
__all__ = ["app"]
