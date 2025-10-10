"""DB-Kit: Universal database abstraction with RLS and multi-tenancy."""

from .client import Database
from .adapters.base import DatabaseAdapter
from .adapters.supabase import SupabaseAdapter
from .adapters.postgres import PostgreSQLAdapter
from .adapters.neon import NeonAdapter

# Storage
from .storage import StorageAdapter, SupabaseStorageAdapter

# Realtime
from .realtime import RealtimeAdapter, SupabaseRealtimeAdapter

from .supabase_client import get_supabase, MissingSupabaseConfig

# Connection pooling
from .pooling import (
    AsyncConnectionPool,
    SyncConnectionPool,
    ConnectionPoolConfig,
    ConnectionStats,
    ConnectionPoolManager,
    get_pool_manager,
    get_provider_pool,
    cleanup_all_pools,
)

__version__ = "0.1.0"

__all__ = [
    # Database
    "Database",
    "DatabaseAdapter",
    "SupabaseAdapter",
    "PostgreSQLAdapter",
    "NeonAdapter",

    # Storage
    "StorageAdapter",
    "SupabaseStorageAdapter",

    # Realtime
    "RealtimeAdapter",
    "SupabaseRealtimeAdapter",

    # Supabase client
    "get_supabase",
    "MissingSupabaseConfig",

    # Connection pooling
    "AsyncConnectionPool",
    "SyncConnectionPool",
    "ConnectionPoolConfig",
    "ConnectionStats",
    "ConnectionPoolManager",
    "get_pool_manager",
    "get_provider_pool",
    "cleanup_all_pools",
]
