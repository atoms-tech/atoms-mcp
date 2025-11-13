"""Atoms MCP CLI - Command-line interface for Atoms MCP Server.

Usage:
    atoms run       - Start the MCP server
    atoms --help    - Show this help message
"""

import sys
import typer
from typing import Optional

app = typer.Typer(
    name="atoms",
    help="Atoms MCP Server - FastMCP server for Atoms platform",
    pretty_exceptions_show_locals=False,
)


@app.command()
def run(
    host: str = typer.Option("0.0.0.0", help="Host to bind server to"),
    port: int = typer.Option(8000, help="Port to run server on"),
    debug: bool = typer.Option(False, help="Enable debug mode"),
):
    """Start the Atoms MCP Server.
    
    Starts a FastMCP server that provides MCP tools for:
    - Entity management (organizations, projects, documents, requirements, tests)
    - Workspace navigation
    - Entity relationships
    - Queries and search
    - Workflow automation
    
    Example:
        atoms run --port 8001 --debug
    """
    from server import main
    
    # Set environment for server startup
    if debug:
        import os
        os.environ["DEBUG"] = "true"
    
    print(f"🚀 Starting Atoms MCP Server on {host}:{port}")
    if debug:
        print("🔧 Debug mode enabled")
    
    main()


@app.command()
def health() -> None:
    """Check if the server is running and healthy."""
    import subprocess
    import os
    
    try:
        # Try to connect to running server
        import httpx
        client = httpx.Client(timeout=5.0)
        response = client.get("http://localhost:8000/health", timeout=5.0)
        
        if response.status_code == 200:
            print("✅ Server is healthy")
            sys.exit(0)
        else:
            print(f"⚠️  Server returned: {response.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Server is not responding: {e}")
        sys.exit(1)


@app.command()
def version() -> None:
    """Show version information."""
    print("Atoms MCP Server v0.1.0")
    print("FastMCP-based consolidated MCP server")


def main():
    """CLI entry point."""
    app()


if __name__ == "__main__":
    main()
