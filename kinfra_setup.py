#!/usr/bin/env python3
"""
KINFRA Setup for Atoms MCP Server (Local-Only Deployment).

This module configures KINFRA (from pheno-sdk) for the atoms-mcp-prod project.
It provides port allocation, health checks, and service management capabilities.

Key Features:
- Port allocation with preference from settings
- Local-only mode (no tunnel) by default
- Health check endpoints
- Graceful cleanup on shutdown

Usage:
    from kinfra_setup import setup_kinfra, cleanup_kinfra

    # Initialize KINFRA
    kinfra, service_mgr = setup_kinfra()

    # Use the allocated port
    port = kinfra.get_service_port("atoms-mcp")

    # Cleanup on shutdown
    cleanup_kinfra(kinfra, service_mgr)
"""

import atexit
import logging
import os
import signal
import sys
from pathlib import Path
from typing import Optional, Tuple

# Import settings first
try:
    from config.settings import get_settings
except ImportError:
    # Fallback if running standalone
    def get_settings():
        class FallbackSettings:
            class kinfra:
                enabled = True
                project_name = "atoms-mcp"
                preferred_port = 8100
                enable_tunnel = False
                enable_fallback = False
                config_dir = None
        return FallbackSettings()
    print("⚠️  Using fallback settings (config.settings not available)")

# Add pheno-sdk to path
PHENO_SDK_PATH = Path(__file__).parent.parent / "pheno-sdk" / "src"

if not PHENO_SDK_PATH.exists():
    print(f"❌ KINFRA path not found: {PHENO_SDK_PATH}")
    print(f"   Please ensure pheno-sdk is available at: {PHENO_SDK_PATH}")
    print(f"\n   To install pheno-sdk:")
    print(f"   cd {Path(__file__).parent.parent / 'pheno-sdk'}")
    print(f"   pip install -e .")
    sys.exit(1)

# Add pheno-sdk src to path BEFORE importing
if str(PHENO_SDK_PATH) not in sys.path:
    sys.path.insert(0, str(PHENO_SDK_PATH))

# Import KINFRA components
try:
    from pheno.kits.infra.kinfra import KInfra
    from pheno.kits.infra.service_manager import ServiceManager, ServiceConfig
    from pheno.kits.infra.exceptions import PortAllocationError, KInfraError

except ImportError as e:
    # Fallback message if imports fail
    print(f"❌ KINFRA import failed: {e}")
    print(f"   Ensure pheno-sdk is available at: {PHENO_SDK_PATH}")
    import traceback
    traceback.print_exc()
    raise

logger = logging.getLogger(__name__)

# Global instances
_kinfra_instance: Optional[KInfra] = None
_service_manager: Optional[ServiceManager] = None
_cleanup_registered = False


def setup_kinfra(
    project_name: Optional[str] = None,
    preferred_port: Optional[int] = None,
    enable_tunnel: Optional[bool] = None,
    enable_fallback: Optional[bool] = None,
    config_dir: Optional[str] = None,
) -> Tuple[KInfra, ServiceManager]:
    """Initialize KINFRA for Atoms MCP Server.

    This function sets up:
    - KInfra instance for port management
    - ServiceManager for lifecycle management
    - Port allocation with preferred port from settings
    - Health check configuration
    - Cleanup handlers

    Args:
        project_name: Service name (default: from settings)
        preferred_port: Preferred port number (default: from settings)
        enable_tunnel: Enable CloudFlare tunnel (default: from settings)
        enable_fallback: Enable fallback pages (default: from settings)
        config_dir: Custom config directory (default: from settings)

    Returns:
        Tuple of (KInfra instance, ServiceManager instance)

    Raises:
        PortAllocationError: If port allocation fails
        KInfraError: If KINFRA initialization fails

    Example:
        >>> kinfra, service_mgr = setup_kinfra()
        >>> port = kinfra.get_service_port("atoms-mcp")
        >>> print(f"Atoms MCP running on port {port}")
    """
    global _kinfra_instance, _service_manager, _cleanup_registered

    # Load settings and apply defaults
    settings = get_settings()

    if project_name is None:
        project_name = settings.kinfra.project_name
    if preferred_port is None:
        preferred_port = settings.kinfra.preferred_port
    if enable_tunnel is None:
        enable_tunnel = settings.kinfra.enable_tunnel
    if enable_fallback is None:
        enable_fallback = settings.kinfra.enable_fallback
    if config_dir is None:
        config_dir = settings.kinfra.config_dir

    logger.info(f"🚀 Initializing KINFRA for {project_name}")

    # Check if KINFRA is enabled
    if not settings.kinfra.enabled:
        logger.warning("⚠️  KINFRA is disabled in settings, returning None")
        return None, None

    # Create KINFRA instance
    try:
        kinfra = KInfra(
            domain="atoms.kooshapari.com",  # Default domain (not used without tunnel)
            config_dir=config_dir
        )
        _kinfra_instance = kinfra
        logger.info("✅ KINFRA instance created")
    except Exception as e:
        logger.error(f"❌ Failed to create KINFRA instance: {e}")
        raise KInfraError(f"KINFRA initialization failed: {e}") from e

    # Allocate port for the service
    try:
        port = kinfra.allocate_port(project_name, preferred_port=preferred_port)
        logger.info(f"✅ Port allocated: {port} (preferred: {preferred_port})")
    except Exception as e:
        logger.error(f"❌ Port allocation failed: {e}")
        raise PortAllocationError(f"Failed to allocate port for {project_name}: {e}") from e

    # Create ServiceManager
    try:
        service_mgr = ServiceManager(
            kinfra=kinfra,
            enable_fallback_layer=enable_fallback,
            enable_resource_management=False  # Not needed for MCP server
        )
        _service_manager = service_mgr
        logger.info("✅ ServiceManager created")
    except Exception as e:
        logger.error(f"❌ ServiceManager creation failed: {e}")
        raise KInfraError(f"ServiceManager initialization failed: {e}") from e

    # Register cleanup handlers (only once)
    if not _cleanup_registered:
        atexit.register(_cleanup_on_exit)
        signal.signal(signal.SIGTERM, _cleanup_on_signal)
        signal.signal(signal.SIGINT, _cleanup_on_signal)
        _cleanup_registered = True
        logger.info("✅ Cleanup handlers registered")

    # Log final configuration
    logger.info(f"""
    ╔════════════════════════════════════════════════════════╗
    ║           KINFRA Configuration for {project_name:12}        ║
    ╠════════════════════════════════════════════════════════╣
    ║  Service Name:    {project_name:32} ║
    ║  Port:            {port:32} ║
    ║  Tunnel:          {'Enabled' if enable_tunnel else 'Disabled':32} ║
    ║  Fallback:        {'Enabled' if enable_fallback else 'Disabled':32} ║
    ║  Config Dir:      {config_dir or '~/.kinfra':32} ║
    ╚════════════════════════════════════════════════════════╝
    """)

    return kinfra, service_mgr


def get_allocated_port(project_name: str = PROJECT_NAME) -> Optional[int]:
    """Get the allocated port for the service.

    Args:
        project_name: Service name (default: "atoms-mcp")

    Returns:
        Allocated port number, or None if not allocated

    Example:
        >>> port = get_allocated_port()
        >>> if port:
        ...     print(f"Port: {port}")
    """
    if _kinfra_instance is None:
        logger.warning("KINFRA not initialized. Call setup_kinfra() first.")
        return None

    return _kinfra_instance.get_service_port(project_name)


def health_check(project_name: str = PROJECT_NAME) -> dict:
    """Perform a health check on the service.

    Args:
        project_name: Service name (default: "atoms-mcp")

    Returns:
        Dictionary with health check results

    Example:
        >>> status = health_check()
        >>> print(f"Healthy: {status['healthy']}")
    """
    if _kinfra_instance is None:
        return {
            "service_name": project_name,
            "status": "not_initialized",
            "healthy": False,
            "message": "KINFRA not initialized"
        }

    return _kinfra_instance.health_check(project_name)


def cleanup_kinfra(
    kinfra: Optional[KInfra] = None,
    service_mgr: Optional[ServiceManager] = None,
    project_name: str = PROJECT_NAME
) -> None:
    """Clean up KINFRA resources.

    This function:
    - Releases allocated ports
    - Stops any running tunnels
    - Cleans up service manager
    - Resets global instances

    Args:
        kinfra: KInfra instance to clean up (uses global if None)
        service_mgr: ServiceManager instance to clean up (uses global if None)
        project_name: Service name to clean up (default: "atoms-mcp")

    Example:
        >>> cleanup_kinfra()
    """
    global _kinfra_instance, _service_manager

    logger.info(f"🧹 Cleaning up KINFRA for {project_name}")

    # Use provided instances or fall back to globals
    kinfra_to_cleanup = kinfra or _kinfra_instance
    service_mgr_to_cleanup = service_mgr or _service_manager

    # Cleanup service manager
    if service_mgr_to_cleanup:
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(service_mgr_to_cleanup.shutdown())
            else:
                loop.run_until_complete(service_mgr_to_cleanup.shutdown())
            logger.info("✅ ServiceManager cleaned up")
        except Exception as e:
            logger.warning(f"⚠️  ServiceManager cleanup warning: {e}")

    # Cleanup KINFRA
    if kinfra_to_cleanup:
        try:
            kinfra_to_cleanup.cleanup(project_name)
            logger.info("✅ KINFRA cleaned up")
        except Exception as e:
            logger.warning(f"⚠️  KINFRA cleanup warning: {e}")

    # Reset global instances
    _kinfra_instance = None
    _service_manager = None

    logger.info("✅ Cleanup complete")


def _cleanup_on_exit():
    """Cleanup handler for normal program exit."""
    cleanup_kinfra()


def _cleanup_on_signal(signum, frame):
    """Cleanup handler for signal interrupts."""
    logger.info(f"📡 Received signal {signum}, cleaning up...")
    cleanup_kinfra()
    # Re-raise the signal
    signal.signal(signum, signal.SIG_DFL)
    os.kill(os.getpid(), signum)


# Export public API
__all__ = [
    "setup_kinfra",
    "cleanup_kinfra",
    "get_allocated_port",
    "health_check",
    "KInfra",
    "ServiceManager",
    "ServiceConfig",
    "PortAllocationError",
    "KInfraError",
]


if __name__ == "__main__":
    # Test the setup
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    print("\n" + "="*60)
    print("KINFRA Setup Test for Atoms MCP")
    print("="*60 + "\n")

    try:
        kinfra, service_mgr = setup_kinfra()
        port = get_allocated_port()
        health = health_check()

        print(f"\n✅ Setup successful!")
        print(f"   Port: {port}")
        print(f"   Health: {health}")

        # Cleanup
        cleanup_kinfra()
        print("\n✅ Cleanup successful!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
