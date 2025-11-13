"""Adapter factory for creating infrastructure adapters based on environment.

Supports:
- Supabase backend (live and mock)
- AuthKit authentication with Bearer tokens
- Service mode selection via environment variables
"""

from __future__ import annotations

import os
import json
from typing import Dict, Any, Optional

try:
    from .adapters import AuthAdapter, DatabaseAdapter, StorageAdapter, RealtimeAdapter
    from .supabase_auth import SupabaseAuthAdapter
    from .supabase_db import SupabaseDatabaseAdapter
    from .supabase_storage import SupabaseStorageAdapter
    from .supabase_realtime import SupabaseRealtimeAdapter
    from .mock_adapters import (
        InMemoryDatabaseAdapter, InMemoryAuthAdapter, 
        InMemoryStorageAdapter, InMemoryRealtimeAdapter,
        HttpMcpClient
    )
    from .mock_config import get_service_config, ServiceMode
except ImportError:
    from infrastructure.adapters import AuthAdapter, DatabaseAdapter, StorageAdapter, RealtimeAdapter
    from infrastructure.supabase_auth import SupabaseAuthAdapter
    from infrastructure.supabase_db import SupabaseDatabaseAdapter
    from infrastructure.supabase_storage import SupabaseStorageAdapter
    from infrastructure.supabase_realtime import SupabaseRealtimeAdapter
    from infrastructure.mock_adapters import (
        InMemoryDatabaseAdapter, InMemoryAuthAdapter,
        InMemoryStorageAdapter, InMemoryRealtimeAdapter,
        HttpMcpClient
    )
    from infrastructure.mock_config import get_service_config, ServiceMode


class AdapterFactory:
    """Factory for creating infrastructure adapters.

    Adds selection for mock vs live using ServiceConfig.
    """
    
    def __init__(self) -> None:
        self._adapters: Dict[str, Any] = {}
        self._backend_type = os.getenv("ATOMS_BACKEND_TYPE", "supabase").lower()
        self._config = get_service_config()
    
    def get_auth_adapter(self) -> AuthAdapter:
        """Get authentication adapter (AuthKit + Bearer tokens via Supabase or mock)."""
        if "auth" not in self._adapters:
            if self._config.is_service_mock("authkit"):
                self._adapters["auth"] = InMemoryAuthAdapter()
            else:
                # Live mode: use SupabaseAuthAdapter (which handles AuthKit + Bearer token validation)
                self._adapters["auth"] = SupabaseAuthAdapter()
        
        return self._adapters["auth"]
    
    def get_database_adapter(self) -> DatabaseAdapter:
        """Get database adapter (Supabase or in-memory mock)."""
        if "database" not in self._adapters:
            if self._config.is_service_mock("supabase"):
                seed = _load_mock_seed(self._config.supabase.get("mock_data_file"))
                self._adapters["database"] = InMemoryDatabaseAdapter(seed_data=seed)
            else:
                # Live mode: use Supabase
                self._adapters["database"] = SupabaseDatabaseAdapter()
        
        return self._adapters["database"]
    
    def get_storage_adapter(self) -> StorageAdapter:
        """Get storage adapter (Supabase or in-memory mock)."""
        if "storage" not in self._adapters:
            if self._config.is_service_mock("supabase"):
                self._adapters["storage"] = InMemoryStorageAdapter()
            else:
                # Live mode: use Supabase
                self._adapters["storage"] = SupabaseStorageAdapter()
        
        return self._adapters["storage"]
    
    def get_realtime_adapter(self) -> RealtimeAdapter:
        """Get realtime adapter (Supabase or in-memory mock)."""
        if "realtime" not in self._adapters:
            if self._config.is_service_mock("supabase"):
                self._adapters["realtime"] = InMemoryRealtimeAdapter()
            else:
                # Live mode: use Supabase
                self._adapters["realtime"] = SupabaseRealtimeAdapter()
        
        return self._adapters["realtime"]
    
    def get_all_adapters(self) -> Dict[str, Any]:
        """Get all adapters as a dictionary."""
        return {
            "auth": self.get_auth_adapter(),
            "database": self.get_database_adapter(),
            "storage": self.get_storage_adapter(),
            "realtime": self.get_realtime_adapter()
        }
    
    def get_backend_type(self) -> str:
        """Get the current backend type."""
        return self._backend_type


def _load_mock_seed(path: Optional[str]) -> Dict[str, Any]:
    if not path:
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


# Global factory instance
_factory = None


def get_adapters() -> Dict[str, Any]:
    """Get adapters using the global factory instance."""
    global _factory
    if _factory is None:
        _factory = AdapterFactory()
    return _factory.get_all_adapters()


def get_adapter_factory() -> AdapterFactory:
    """Get the global adapter factory instance."""
    global _factory
    if _factory is None:
        _factory = AdapterFactory()
    return _factory


def reset_factory():
    """Reset the global factory (useful for testing)."""
    global _factory
    _factory = None