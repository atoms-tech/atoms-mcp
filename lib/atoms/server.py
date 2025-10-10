"""
Atoms MCP Specific Server Management

This is the Atoms-specific layer for server management.
Uses platform-agnostic base classes from pheno-sdk.
"""

import subprocess
import sys
from pathlib import Path


class AtomsServerManager:
    """Atoms MCP specific server manager.

    This wraps the server startup logic with Atoms-specific configuration.
    """

    # Atoms-specific defaults
    DEFAULT_PORT = 50002
    DEFAULT_DOMAIN = "atomcp.kooshapari.com"
    PROJECT_NAME = "atoms_mcp"

    def __init__(
        self,
        port: int | None = None,
        verbose: bool = False,
        no_tunnel: bool = False,
        logger=None
    ):
        self.port = port or self.DEFAULT_PORT
        self.verbose = verbose
        self.no_tunnel = no_tunnel
        self.logger = logger

    def start(self) -> int:
        """Start Atoms MCP server.

        This delegates to start_server.py which has all the KInfra integration.

        Returns:
            Exit code (0 for success)
        """
        # Build command to run start_server.py
        cmd = [
            sys.executable,
            str(Path(__file__).parent.parent.parent / "start_server.py")
        ]

        if self.port:
            cmd.extend(["--port", str(self.port)])
        if self.verbose:
            cmd.append("--verbose")
        if self.no_tunnel:
            cmd.append("--no-tunnel")

        # Run start_server.py
        result = subprocess.run(cmd, check=False)
        return result.returncode


def start_atoms_server(
    port: int | None = None,
    verbose: bool = False,
    no_tunnel: bool = False,
    logger=None
) -> int:
    """Start Atoms MCP server (convenience function).

    This is the function called by atoms-mcp.py CLI.

    Args:
        port: Port to run on (default: 50002)
        verbose: Enable verbose logging
        no_tunnel: Disable CloudFlare tunnel
        logger: Optional logger instance

    Returns:
        Exit code (0 for success)
    """
    manager = AtomsServerManager(
        port=port,
        verbose=verbose,
        no_tunnel=no_tunnel,
        logger=logger
    )

    return manager.start()

