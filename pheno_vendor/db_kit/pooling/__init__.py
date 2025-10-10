"""
Connection pooling module for db-kit.

Provides HTTP connection pooling with health monitoring and resource management.
"""

from .connection_pool import (
    AsyncConnectionPool,
    SyncConnectionPool,
    ConnectionPoolConfig,
    ConnectionStats,
)

from .pool_manager import (
    ConnectionPoolManager,
    get_pool_manager,
    get_provider_pool,
    cleanup_all_pools,
)

__all__ = [
    # Connection pools
    "AsyncConnectionPool",
    "SyncConnectionPool",
    "ConnectionPoolConfig",
    "ConnectionStats",

    # Pool manager
    "ConnectionPoolManager",
    "get_pool_manager",
    "get_provider_pool",
    "cleanup_all_pools",
]
