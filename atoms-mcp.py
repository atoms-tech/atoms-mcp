#!/usr/bin/env python3
"""Atoms MCP CLI - Deployment and server management."""

import asyncio
import sys
from pathlib import Path

# Add lib to path so we can import from lib.atoms
sys.path.insert(0, str(Path(__file__).parent / "lib"))

from lib.atoms.deployment import deploy_atoms_to_vercel
from lib.atoms.server import start_atoms_server


def main() -> int:
    """Main CLI entry point."""
    args = sys.argv[1:]

    if not args:
        print("Usage: atoms-mcp.py <command> [options]")
        print("\nCommands:")
        print("  deploy --preview    Deploy to Vercel preview")
        print("  deploy --prod       Deploy to Vercel production")
        print("  server              Start local server")
        return 1

    command = args[0]

    if command == "deploy":
        # Handle deployment
        environment = "preview"
        if "--prod" in args or "--production" in args:
            environment = "production"

        print(f"Deploying to {environment}...")
        result = asyncio.run(deploy_atoms_to_vercel(environment=environment))
        return 0 if result else 1

    if command == "server" or command == "start":
        # Handle server start
        verbose = "--verbose" in args or "-v" in args
        no_tunnel = "--no-tunnel" in args

        port = None
        if "--port" in args:
            idx = args.index("--port")
            if idx + 1 < len(args):
                port = int(args[idx + 1])

        return start_atoms_server(port=port, verbose=verbose, no_tunnel=no_tunnel)

    print(f"Unknown command: {command}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
