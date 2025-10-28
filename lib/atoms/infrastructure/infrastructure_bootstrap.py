"""Bootstrap infrastructure components for Atoms MCP application.

Thin wrapper around pheno-sdk's GenericServiceOrchestrator.
All generic code lives in pheno-sdk for reusability across services.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

logger = logging.getLogger(__name__)


class InfrastructureBootstrapError(Exception):
    """Raised when infrastructure bootstrap fails."""


class AtomsInfrastructureBootstrap:
    """Bootstraps and manages infrastructure for Atoms MCP application.

    Thin wrapper around pheno-sdk's GenericServiceOrchestrator.
    """

    def __init__(self):
        """Initialize infrastructure bootstrap."""
        self._port: int | None = None
        self._tunnel_info: dict[str, Any] | None = None
        self._initialized = False

        # Import infrastructure components from pheno-sdk
        try:
            from pheno.infra.service_orchestrator import GenericServiceOrchestrator
            self.infra_manager = GenericServiceOrchestrator("atoms-mcp-server")
        except ImportError:
            logger.warning("pheno-sdk not available, falling back to basic startup")
            self.infra_manager = None

        logger.info("Infrastructure bootstrap initialized")

    async def initialize(self) -> None:
        """Initialize all infrastructure components."""
        if self._initialized:
            logger.debug("Infrastructure already initialized")
            return

        logger.info("Initializing Atoms MCP infrastructure...")

        try:
            # Allocate port
            if self.infra_manager:
                self._port = await self.infra_manager.allocate_port()
                logger.info(f"✓ Port allocated: {self._port}")

            self._initialized = True
            logger.info("✓ Infrastructure successfully initialized")

        except Exception as e:
            logger.exception(f"✗ Infrastructure initialization failed: {e}")
            raise InfrastructureBootstrapError(f"Failed to initialize infrastructure: {e}") from e

    async def setup_tunnel(self, enable_tunnel: bool = False) -> dict[str, Any] | None:
        """Setup tunnel for the service if enabled."""
        if not enable_tunnel or not self.infra_manager:
            return None

        try:
            tunnel_info = await self.infra_manager.setup_tunnel(self._port)
            if tunnel_info:
                self._tunnel_info = {
                    "tunnel_id": tunnel_info.tunnel_id,
                    "public_url": tunnel_info.public_url,
                    "local_port": self._port,
                    "status": tunnel_info.status.value,
                }
                logger.info(f"✓ Tunnel ready: {tunnel_info.public_url}")
                return self._tunnel_info
        except Exception as e:
            logger.exception(f"Tunnel setup failed: {e}")
            # Don't fail startup - tunnel is optional
            return None

    async def shutdown(self) -> None:
        """Shutdown all infrastructure components."""
        if not self._initialized:
            logger.debug("Infrastructure not initialized, skipping shutdown")
            return

        logger.info("Shutting down Atoms MCP infrastructure...")

        try:
            # Teardown tunnel
            if self._tunnel_info and self.infra_manager:
                try:
                    await self.infra_manager.teardown_tunnel()
                    logger.info("✓ Tunnel closed")
                except Exception as e:
                    logger.exception(f"Error tearing down tunnel: {e}")

            # Stop service
            if self.infra_manager:
                try:
                    await self.infra_manager.stop()
                    logger.info("✓ Service stopped")
                except Exception as e:
                    logger.exception(f"Error stopping service: {e}")

            self._initialized = False
            logger.info("✓ Infrastructure successfully shut down")

        except Exception as e:
            logger.exception(f"✗ Error during infrastructure shutdown: {e}")

    @asynccontextmanager
    async def lifespan_context(
        self, enable_tunnel: bool = False
    ) -> AsyncGenerator[None, None]:
        """Async context manager for application lifespan."""
        await self.initialize()
        await self.setup_tunnel(enable_tunnel)

        try:
            yield
        finally:
            await self.shutdown()

    async def health_check(self) -> dict[str, Any]:
        """Perform health check on infrastructure."""
        health = {
            "initialized": self._initialized,
            "port_allocated": self._port is not None,
            "port": self._port,
            "tunnel_active": self._tunnel_info is not None,
        }

        if self._tunnel_info:
            health["tunnel_info"] = self._tunnel_info

        return health

    @property
    def port(self) -> int | None:
        """Get the allocated port."""
        return self._port

    @property
    def tunnel_info(self) -> dict[str, Any] | None:
        """Get tunnel information."""
        return self._tunnel_info


# Global singleton bootstrap instance
_bootstrap_instance: AtomsInfrastructureBootstrap | None = None


# Bootstrap functions removed - not used anywhere in the codebase
