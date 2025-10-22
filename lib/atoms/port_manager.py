"""
Port Management for Atoms MCP Server

This module provides utilities for managing port allocation using KINFRA.
"""

import logging

logger = logging.getLogger(__name__)

# Import pheno-sdk port allocation
try:
    from pheno.infra.port_allocator import SmartPortAllocator
    from pheno.infra.port_registry import PortRegistry
    from pheno.infra.process_cleanup import ProcessCleanupConfig, cleanup_before_startup
    PHENO_SDK_AVAILABLE = True
except ImportError:
    PHENO_SDK_AVAILABLE = False


class AtomsPortManager:
    """Port manager for Atoms MCP Server using pheno-sdk."""

    SERVICE_NAME = "atoms-mcp-server"

    def __init__(self):
        self.registry = None
        self.allocator = None
        self._allocated_port = None

        if PHENO_SDK_AVAILABLE:
            try:
                self.registry = PortRegistry()
                self.allocator = SmartPortAllocator(self.registry)
                logger.info("🔧 pheno-sdk port management initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize pheno-sdk port management: {e}")
                # Don't modify the global PHENO_SDK_AVAILABLE here

    def allocate_port(self, preferred_port: int | None = None, cleanup_config: ProcessCleanupConfig | None = None) -> int:
        """Allocate a port for the Atoms MCP server.

        Args:
            preferred_port: Preferred port number (optional)
            cleanup_config: Optional process cleanup configuration

        Returns:
            Allocated port number
        """
        if not PHENO_SDK_AVAILABLE or not self.allocator:
            # Fallback to default port
            default_port = preferred_port or 8000
            logger.warning(f"pheno-sdk not available, using default port {default_port}")
            return default_port

        try:
            # Perform process cleanup before allocation
            if PHENO_SDK_AVAILABLE:
                cleanup_stats = cleanup_before_startup(self.SERVICE_NAME, cleanup_config)
                logger.info(f"🧹 Process cleanup completed: {cleanup_stats}")

            # Allocate port using pheno-sdk
            port = self.allocator.allocate_port(self.SERVICE_NAME, preferred_port)
            self._allocated_port = port
            logger.info(f"🔧 pheno-sdk allocated port {port} for {self.SERVICE_NAME}")
            return port
        except Exception as e:
            # Fallback to default port
            default_port = preferred_port or 8000
            logger.warning(f"pheno-sdk port allocation failed: {e}, using default port {default_port}")
            return default_port

    def get_allocated_port(self) -> int | None:
        """Get the currently allocated port.

        Returns:
            Allocated port number or None if not allocated
        """
        if not PHENO_SDK_AVAILABLE or not self.allocator:
            return self._allocated_port

        try:
            return self.allocator.get_service_port(self.SERVICE_NAME)
        except Exception as e:
            logger.warning(f"Failed to get allocated port: {e}")
            return self._allocated_port

    def release_port(self) -> bool:
        """Release the allocated port.

        Returns:
            True if port was released successfully
        """
        if not PHENO_SDK_AVAILABLE or not self.allocator:
            return False

        try:
            result = self.allocator.release_port(self.SERVICE_NAME)
            if result:
                logger.info(f"🔧 Released port for {self.SERVICE_NAME}")
            return result
        except Exception as e:
            logger.warning(f"Failed to release port: {e}")
            return False


# Global port manager instance
_port_manager = None


def get_port_manager() -> AtomsPortManager:
    """Get the global port manager instance.

    Returns:
        AtomsPortManager instance
    """
    global _port_manager
    if _port_manager is None:
        _port_manager = AtomsPortManager()
    return _port_manager


def allocate_atoms_port(preferred_port: int | None = None, cleanup_config=None) -> int:
    """Allocate a port for the Atoms MCP server.

    Args:
        preferred_port: Preferred port number (optional)
        cleanup_config: Optional process cleanup configuration

    Returns:
        Allocated port number
    """
    return get_port_manager().allocate_port(preferred_port, cleanup_config)


def get_atoms_port() -> int | None:
    """Get the currently allocated port for Atoms MCP server.

    Returns:
        Allocated port number or None if not allocated
    """
    return get_port_manager().get_allocated_port()


def release_atoms_port() -> bool:
    """Release the allocated port for Atoms MCP server.

    Returns:
        True if port was released successfully
    """
    return get_port_manager().release_port()
