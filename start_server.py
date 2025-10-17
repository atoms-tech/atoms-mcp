#!/usr/bin/env python3
"""
Atoms MCP Server Entry Point

This module serves as the application entry point for Vercel serverless deployment.
It imports and exports the FastMCP application instance for use by Vercel's Python runtime.

Usage:
    - Local: python start_server.py
    - Vercel: Configured via vercel.json to use this as entry point
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import the FastMCP app from app.py
from app import app
from config import get_settings
from server.env import load_env_files

if __name__ == "__main__":
    """Run the server locally for development."""
    import uvicorn

    # Configuration from environment or defaults
    load_env_files()
    settings = get_settings()

    host = settings.host
    port = settings.port
    reload = settings.reload_server

    print(f"Starting Atoms MCP Server on {host}:{port}")
    print(f"MCP Endpoint: http://{host}:{port}/api/mcp")
    print(f"Health Check: http://{host}:{port}/health")

    uvicorn.run(
        "start_server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )
