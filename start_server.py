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
from config import get_settings  # noqa: E402
from server.env import load_env_files  # noqa: E402

# Import pheno-sdk port allocation
try:
    from pheno.infra.port_allocator import SmartPortAllocator
    from pheno.infra.port_registry import PortRegistry
    from pheno.infra.process_cleanup import ProcessCleanupConfig, cleanup_before_startup
    PHENO_SDK_AVAILABLE = True
except ImportError:
    PHENO_SDK_AVAILABLE = False

def allocate_port_with_pheno_sdk(service_name: str = "atoms-mcp-server") -> int:
    """Allocate a port using pheno-sdk's smart port allocator.

    Args:
        service_name: Name of the service for port allocation

    Returns:
        Allocated port number
    """
    if not PHENO_SDK_AVAILABLE:
        # Fallback to default port if pheno-sdk not available
        return 8000

    try:
        # Perform process cleanup before port allocation
        cleanup_config = ProcessCleanupConfig(
            cleanup_related_services=True,
            cleanup_tunnels=True,
            grace_period=2.0,
        )
        cleanup_stats = cleanup_before_startup(service_name, cleanup_config)
        print(f"🧹 Process cleanup completed: {cleanup_stats}")

        # Create port allocator and registry
        registry = PortRegistry()
        allocator = SmartPortAllocator(registry)

        # Allocate port for the service
        port = allocator.allocate_port(service_name)
        print(f"🔧 pheno-sdk allocated port {port} for service '{service_name}'")
        return port

    except Exception as e:
        print(f"⚠️  pheno-sdk port allocation failed: {e}")
        print("   Falling back to default port 8000")
        return 8000


if __name__ == "__main__":
    """Run the server locally for development."""
    import argparse

    import uvicorn

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Atoms MCP Server")
    parser.add_argument("--port", type=int, help="Port to bind to")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--no-tunnel", action="store_true", help="Disable Cloudflare tunnel")
    args = parser.parse_args()

    # Configuration from environment or defaults
    load_env_files()
    settings = get_settings()

    host = settings.server.host

    # Determine port - command line arg takes precedence
    if args.port:
        port = args.port
    elif PHENO_SDK_AVAILABLE and not hasattr(settings.server, 'force_port'):
        port = allocate_port_with_pheno_sdk()
    else:
        port = settings.server.port

    reload = settings.server.reload_server

    print(f"Starting Atoms MCP Server on {host}:{port}")
    print(f"MCP Endpoint: http://{host}:{port}/api/mcp")
    print(f"Health Check: http://{host}:{port}/health")

    if PHENO_SDK_AVAILABLE:
        print("🔧 Port allocated by pheno-sdk smart port allocator")

    uvicorn.run(
        "start_server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )
