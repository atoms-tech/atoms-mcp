"""
KInfra - Cross-platform infrastructure library for dynamic port allocation and secure tunneling.

This library provides seamless port management and tunneling capabilities for services,
with automatic conflict resolution and tunnel synchronization.
"""

from typing import Dict, List, Optional

from .exceptions import KInfraError, PortAllocationError, ServiceConflictError, ServiceError, TunnelError
from .fallback_server import FallbackServer, run_fallback_server
from .kinfra import KInfra
from .orchestrator import ServiceOrchestrator, OrchestratorConfig
from .port_registry import PortRegistry, ServiceInfo
from .proxy_server import SmartProxyServer, UpstreamConfig, run_smart_proxy
from .resource_manager import ResourceManager
from . import adapters
from . import templates
from . import middleware_helpers
from .service_manager import (ServiceManager, ServiceConfig, ServiceStatus,
                               ResourceConfig, ResourceStatus)
from .smart_allocator import SmartPortAllocator
from .smart_infra_manager import SmartInfraManager, get_smart_infra_manager
from .tunnel_sync import TunnelInfo, TunnelManager

# Export utility functions for backward compatibility and convenience
from .utils.process import (
    is_port_free,
    get_port_occupant,
    terminate_process,
    kill_processes_on_port,
    cleanup_orphaned_processes,
)
from .utils.health import (
    check_http_health,
    check_tcp_health,
    check_tunnel_health,
)
from .utils.dns import (
    dns_safe_slug,
)

__version__ = "1.0.0"
__all__ = [
    "KInfra",
    "PortRegistry",
    "ServiceInfo",
    "SmartPortAllocator",
    "SmartInfraManager",
    "get_smart_infra_manager",
    "TunnelManager",
    "TunnelInfo",
    "ServiceManager",
    "ServiceConfig",
    "ServiceStatus",
    "ResourceConfig",
    "ResourceStatus",
    "ServiceOrchestrator",
    "OrchestratorConfig",
    "FallbackServer",
    "run_fallback_server",
    "SmartProxyServer",
    "UpstreamConfig",
    "run_smart_proxy",
    "ResourceManager",
    "adapters",
    "templates",
    "middleware_helpers",
    "KInfraError",
    "PortAllocationError",
    "TunnelError",
    "ServiceConflictError",
    "ServiceError",
    "cleanup_environment",
    # Utility functions
    "is_port_free",
    "get_port_occupant",
    "terminate_process",
    "kill_processes_on_port",
    "cleanup_orphaned_processes",
    "check_http_health",
    "check_tcp_health",
    "check_tunnel_health",
    "dns_safe_slug",
]

# Convenience functions for common operations
def allocate_port(service_name: str, preferred_port: int = None) -> int:
    """Allocate a port for a service with smart conflict resolution."""
    kinfra = KInfra()
    return kinfra.allocate_port(service_name, preferred_port)

def start_tunnel(service_name: str, port: int, domain: str = "kooshapari.com") -> TunnelInfo:
    """Start a tunnel for a service."""
    kinfra = KInfra()
    return kinfra.start_tunnel(service_name, port, domain)

def get_service_url(service_name: str) -> str:
    """Get the public URL for a service."""
    kinfra = KInfra()
    return kinfra.get_service_url(service_name)

def cleanup(service_name: str) -> None:
    """Clean up resources for a service."""
    kinfra = KInfra()
    kinfra.cleanup(service_name)


def cleanup_environment(
    grace_period: float = 3.0,
    force_kill: bool = True,
    exclude_pids: Optional[List[int]] = None,
) -> Dict[str, int]:
    """Run comprehensive cleanup via a temporary KInfra instance."""

    kinfra = KInfra()
    return kinfra.cleanup_environment(
        grace_period=grace_period,
        force_kill=force_kill,
        exclude_pids=exclude_pids,
    )
