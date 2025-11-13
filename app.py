"""ASGI application for Vercel deployment.

This creates a proper ASGI app export that Vercel can import.
Following FastMCP documentation: https://docs.fastmcp.com/deployment/self-hosted
"""

from __future__ import annotations
import logging
import os
import sys
import traceback
import anyio
from typing import Any
from starlette.middleware.gzip import GZipMiddleware
from starlette.responses import JSONResponse, PlainTextResponse, Response

logger = logging.getLogger(__name__)

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
async def root(request: Any) -> Response:
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
async def health_check(request: Any) -> Response:
    """Health check endpoint for monitoring."""
    return JSONResponse({
        "status": "healthy",
        "service": "atoms-mcp-server",
        "transport": "http"
    })

# Add debug endpoint to list registered tools
@mcp.custom_route("/debug/tools", methods=["GET"])
async def debug_tools(request: Any) -> Response:
    """Debug endpoint to list registered tools."""
    try:
        tools = await mcp.get_tools()
        tool_info = []
        for tool_name in tools:
            tool = mcp.get_tool(tool_name) if hasattr(mcp, 'get_tool') else None
            tool_info.append({
                "name": tool_name,
                "enabled": tool.enabled if tool and hasattr(tool, 'enabled') else True,
                "tags": list(tool.tags) if tool and hasattr(tool, 'tags') else []
            })
        return JSONResponse({
            "total_tools": len(tools),
            "tools": tool_info,
            "server_creation_error": server_creation_error
        })
    except Exception as e:
        return JSONResponse({
            "error": str(e),
            "traceback": traceback.format_exc()
        }, status_code=500)

# Add embedding queue processing endpoint for Vercel Cron
@mcp.custom_route("/api/embeddings/process-queue", methods=["POST", "GET"])
async def process_embedding_queue_route(request: Any) -> Response:
    """Process embedding queue - called by Vercel Cron."""
    try:
        # Import here to avoid startup issues if embedding service fails
        from api.process_embedding_queue import process_embedding_queue_endpoint

        # Get cron secret from request (if POST with JSON body)
        cron_secret = None
        if request.method == "POST":
            try:
                body = await request.json()
                cron_secret = body.get("secret")
            except Exception:
                pass
        else:
            # GET request - read from query param
            cron_secret = request.query_params.get("secret")

        # Process queue
        result = await process_embedding_queue_endpoint(
            batch_size=20,
            cron_secret=cron_secret or ""  # type: ignore[arg-type]
        )

        return JSONResponse(result)

    except Exception as e:
        logger.error(f"Error processing embedding queue: {e}")
        return JSONResponse({
            "error": "Internal Error",
            "message": str(e)
        }, status_code=500)

# Create ASGI application with custom path
# CRITICAL: stateless_http=True is REQUIRED for serverless environments like Vercel
_base_app = mcp.http_app(path="/api/mcp", stateless_http=True)

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
async def _patched_handle_request(self: Any, scope: Any, receive: Any, send: Any) -> None:
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
StreamableHTTPSessionManager.handle_request = _patched_handle_request  # type: ignore[method-assign]
print("✅ Patched StreamableHTTPSessionManager.handle_request for serverless deployment")

# Vercel will import the 'app' variable
__all__ = ["app"]
