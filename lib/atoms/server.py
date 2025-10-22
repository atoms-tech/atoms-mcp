"""
Atoms MCP Specific Server Management

This is the Atoms-specific layer for server management.
Uses platform-agnostic base classes from pheno-sdk.
"""

import subprocess
import sys
from pathlib import Path

# Import pheno-sdk port allocation
try:
    from pheno.infra.port_allocator import SmartPortAllocator
    from pheno.infra.port_registry import PortRegistry
    from pheno.infra.process_cleanup import ProcessCleanupConfig, cleanup_before_startup
    PHENO_SDK_AVAILABLE = True
except ImportError:
    PHENO_SDK_AVAILABLE = False


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
        # Use pheno-sdk port allocation if no port specified
        if port is None and PHENO_SDK_AVAILABLE:
            try:
                # Perform process cleanup before port allocation
                cleanup_config = ProcessCleanupConfig(
                    cleanup_related_services=True,
                    cleanup_tunnels=True,
                    grace_period=2.0,
                )
                cleanup_stats = cleanup_before_startup("atoms-mcp-server", cleanup_config)
                if logger:
                    logger.info(f"🧹 Process cleanup completed: {cleanup_stats}")

                registry = PortRegistry()
                allocator = SmartPortAllocator(registry)
                self.port = allocator.allocate_port("atoms-mcp-server")
                if logger:
                    logger.info(f"🔧 pheno-sdk allocated port {self.port} for atoms-mcp-server")
            except Exception as e:
                if logger:
                    logger.warning(f"pheno-sdk port allocation failed: {e}, using default port {self.DEFAULT_PORT}")
                self.port = self.DEFAULT_PORT
        else:
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

