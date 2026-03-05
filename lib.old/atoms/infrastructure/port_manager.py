"""
Port Management for Atoms MCP Server

This module provides utilities for managing port allocation using KINFRA.
"""

import logging
from typing import TYPE_CHECKING, Any, cast

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    ProcessCleanupConfig = Any  # type: ignore[assignment, misc, valid-type]
    SmartPortAllocator = Any  # type: ignore[assignment, misc]
    PortRegistry = Any  # type: ignore[assignment, misc]
    cleanup_before_startup: Any  # type: ignore[assignment, misc]
    PHENO_SDK_AVAILABLE: bool = True
else:
    try:
        from pheno.infra.async_utils import run_async_safely
        from pheno.infra.port_allocator import SmartPortAllocator
        from pheno.infra.port_registry import PortRegistry
        from pheno.infra.process_cleanup import ProcessCleanupConfig, cleanup_before_startup

        PHENO_SDK_AVAILABLE = True
    except ImportError:
        PHENO_SDK_AVAILABLE = False
        run_async_safely = None  # type: ignore[assignment]

        # Fallback definitions when pheno-sdk is unavailable
        class ProcessCleanupConfig:  # type: ignore[no-redef]
            """Fallback ProcessCleanupConfig when pheno-sdk is unavailable."""

        class SmartPortAllocator:  # type: ignore[no-redef]
            """Fallback SmartPortAllocator when pheno-sdk is unavailable."""

        class PortRegistry:  # type: ignore[no-redef]
            """Fallback PortRegistry when pheno-sdk is unavailable."""

        def cleanup_before_startup():
            """Fallback cleanup function when pheno-sdk is unavailable."""


class AtomsPortManager:
    """Port manager for Atoms MCP Server using pheno-sdk."""

    SERVICE_NAME = "atoms-mcp-server"

    def __init__(self, base_port: int = 50000, max_ports: int = 100, port_file: str = "/tmp/atoms_ports.json"):
        self.base_port = base_port
        self.max_ports = max_ports
        self.port_file = port_file
        self.registry = None
        self.allocator = None
        self._allocated_port = None

        if PHENO_SDK_AVAILABLE:
            try:
                self.registry = cast("Any", PortRegistry())  # type: ignore[call-arg, misc]
                # type: ignore[misc] - SmartPortAllocator is Any in TYPE_CHECKING mode, causing Any(...) error
                self.allocator = SmartPortAllocator(self.registry)  # type: ignore[call-arg, misc]
                logger.info("🔧 pheno-sdk port management initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize pheno-sdk port management: {e}")
                # Don't modify the global PHENO_SDK_AVAILABLE here

    @classmethod
    def get_port_manager(cls) -> "AtomsPortManager":
        """Get the global port manager instance."""
        if not hasattr(cls, "_instance"):
            cls._instance = cls()  # type: ignore[attr-defined]
        return cls._instance  # type: ignore[attr-defined]

    def allocate_port(
        self, preferred_port: int | None = None, cleanup_config: Any | None = None  # type: ignore[assignment]
    ) -> int:
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
            if PHENO_SDK_AVAILABLE and cleanup_config and run_async_safely:
                try:
                    cleanup_stats = run_async_safely(cleanup_before_startup(self.SERVICE_NAME, cleanup_config))
                    logger.info(f"🧹 Process cleanup completed: {cleanup_stats}")
                except RuntimeError as e:
                    if "async context" in str(e):
                        logger.warning("⚠️  Process cleanup skipped (already in async context)")
                    else:
                        raise

            # Allocate port using pheno-sdk
            port = self.allocator.allocate_port(self.SERVICE_NAME, preferred_port)
            self._allocated_port = port
            logger.info(f"🔧 pheno-sdk allocated port {port} for {self.SERVICE_NAME}")
        except Exception as e:
            # Fallback to default port
            default_port = preferred_port or 8000
            logger.warning(f"pheno-sdk port allocation failed: {e}, using default port {default_port}")
            return default_port
        else:
            return port

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
        except Exception as e:
            logger.warning(f"Failed to release port: {e}")
            return False
        else:
            if result:
                logger.info(f"🔧 Released port for {self.SERVICE_NAME}")
            return result


# Module-level storage container
class _PortManagerContainer:
    """Container for module-level port manager state."""

    def __init__(self) -> None:
        self._value: AtomsPortManager | None = None

    def get(self) -> AtomsPortManager:
        """Get the port manager instance."""
        if self._value is None:
            self._value = AtomsPortManager()
        return self._value


_port_manager_container = _PortManagerContainer()


def get_port_manager() -> AtomsPortManager:
    """Get the global port manager instance.

    Returns:
        AtomsPortManager instance
    """
    return _port_manager_container.get()


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
