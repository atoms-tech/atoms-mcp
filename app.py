"""ASGI application for Vercel deployment.

This creates a proper ASGI app export that Vercel can import.
Following FastMCP documentation: https://docs.fastmcp.com/deployment/self-hosted
"""

from __future__ import annotations

import anyio
from starlette.responses import JSONResponse

# Setup structured logging before other imports
from utils.logging_setup import get_logger, setup_logging

setup_logging(level="INFO", use_color=False, use_timestamps=True)  # No color for Vercel logs
logger = get_logger(__name__)

from server import create_consolidated_server  # noqa: E402

logger.info("🚀 Starting Atoms MCP Server (environment=vercel)")

# Create the FastMCP server instance
mcp = create_consolidated_server()

# Add root route handler
@mcp.custom_route("/", methods=["GET"])
async def root(request):
    """Root endpoint with service information."""
    return JSONResponse({
        "service": "Atoms MCP Server",
        "version": "1.0.0",
        "endpoints": {
            "mcp": "/api/mcp",
            "health": "/health",
            "auth_start": "/auth/start",
            "auth_complete": "/auth/complete"
        },
        "status": "running"
    })

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
from starlette.middleware.gzip import GZipMiddleware  # noqa: E402

# Wrap with compression only
app = GZipMiddleware(_base_app, minimum_size=500)  # Compress responses >500 bytes

# CRITICAL FIX for Vercel serverless:
# The issue is that MCP's stateless mode still requires a task group, which is
# normally created in the lifespan context. But in Vercel serverless, the lifespan
# doesn't persist across invocations, so we need to ensure the task group is
# recreated for each request.

# Patch the StreamableHTTPSessionManager directly
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager  # noqa: E402

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
StreamableHTTPSessionManager.handle_request = _patched_handle_request  # type: ignore[assignment]
print("✅ Patched StreamableHTTPSessionManager.handle_request for serverless deployment")

# Vercel will import the 'app' variable
__all__ = ["app"]
