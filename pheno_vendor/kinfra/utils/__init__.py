"""
KInfra Utilities - Common utilities extracted from various KInfra modules.

This package contains reusable utility functions for:
- Process management (port checking, process termination)
- Health checking (HTTP/TCP health probes)
- DNS utilities (DNS-safe slug generation)
"""

from .process import (
    is_port_free,
    get_port_occupant,
    terminate_process,
    kill_processes_on_port,
    cleanup_orphaned_processes,
)
from .health import (
    check_http_health,
    check_tcp_health,
)
from .dns import (
    dns_safe_slug,
)

__all__ = [
    # Process utilities
    'is_port_free',
    'get_port_occupant',
    'terminate_process',
    'kill_processes_on_port',
    'cleanup_orphaned_processes',
    # Health check utilities
    'check_http_health',
    'check_tcp_health',
    # DNS utilities
    'dns_safe_slug',
]
