#!/usr/bin/env python3
"""
Atoms MCP Package Entry Point

Delegates to atoms-mcp.py unified CLI for all operations.
"""
import sys
from pathlib import Path

if __name__ == "__main__":
    # Get the directory of this package
    package_dir = Path(__file__).parent

    # Import and run the unified CLI
    atoms_mcp_cli = package_dir / "atoms-mcp.py"

    if atoms_mcp_cli.exists():
        # Import and run atoms-mcp.py
        import importlib.util
        spec = importlib.util.spec_from_file_location("atoms_mcp_cli", atoms_mcp_cli)
        cli_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cli_module)
        sys.exit(cli_module.main())
    else:
        # Fallback to old behavior if atoms-mcp.py not found
        from .server import main
        main()

