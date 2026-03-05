"""Atoms MCP server management."""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any

from .port_manager import allocate_atoms_port, release_atoms_port

logger = logging.getLogger(__name__)


class AtomsServerManager:
    """Manages Atoms MCP server lifecycle."""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.server_process: asyncio.subprocess.Process | None = None
        self.port: int | None = None

    async def start_server(self, port: int | None = None) -> int:
        """Start the Atoms MCP server."""
        if self.server_process:
            raise RuntimeError("Server is already running")

        self.port = port or allocate_atoms_port()

        # Start server process (placeholder implementation)
        logger.info(f"Starting Atoms MCP server on port {self.port}")

        # In a real implementation, this would start the actual server
        # For now, we'll just simulate it
        self.server_process = await asyncio.create_subprocess_exec(
            "python",
            "-c",
            "import time; time.sleep(3600)",  # Placeholder
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        return self.port

    async def stop_server(self) -> None:
        """Stop the Atoms MCP server."""
        if not self.server_process:
            return

        logger.info("Stopping Atoms MCP server")
        self.server_process.terminate()
        await self.server_process.wait()
        self.server_process = None

        if self.port:
            release_atoms_port(self.port)
            self.port = None

    async def restart_server(self, port: int | None = None) -> int:
        """Restart the Atoms MCP server."""
        await self.stop_server()
        return await self.start_server(port)

    @property
    def is_running(self) -> bool:
        """Check if server is running."""
        return self.server_process is not None and self.server_process.returncode is None


async def start_atoms_server(port: int | None = None, config: dict[str, Any] | None = None) -> AtomsServerManager:
    """Start an Atoms MCP server and return the manager."""
    manager = AtomsServerManager(config)
    await manager.start_server(port)
    return manager


@asynccontextmanager
async def managed_atoms_server(port: int | None = None, config: dict[str, Any] | None = None):
    """Context manager for Atoms MCP server."""
    manager = await start_atoms_server(port, config)
    try:
        yield manager
    finally:
        await manager.stop_server()
