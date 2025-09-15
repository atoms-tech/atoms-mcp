"""Adapter factory for creating infrastructure adapters based on environment."""

from __future__ import annotations

import os
from typing import Dict, Any

from .adapters import AuthAdapter, DatabaseAdapter, StorageAdapter, RealtimeAdapter
from .supabase_auth import SupabaseAuthAdapter
from .supabase_db import SupabaseDatabaseAdapter
from .supabase_storage import SupabaseStorageAdapter
from .supabase_realtime import SupabaseRealtimeAdapter


class AdapterFactory:
    """Factory for creating infrastructure adapters."""
    
    def __init__(self):
        self._adapters: Dict[str, Any] = {}
        self._backend_type = os.getenv("ATOMS_BACKEND_TYPE", "supabase").lower()
    
    def get_auth_adapter(self) -> AuthAdapter:
        """Get authentication adapter."""
        if "auth" not in self._adapters:
            if self._backend_type == "supabase":
                self._adapters["auth"] = SupabaseAuthAdapter()
            elif self._backend_type == "dotnet":
                # TODO: Implement .NET auth adapter
                raise NotImplementedError(".NET auth adapter not yet implemented")
            elif self._backend_type == "hybrid":
                # TODO: Implement hybrid auth (e.g., Supabase auth + .NET data)
                raise NotImplementedError("Hybrid auth adapter not yet implemented")
            else:
                raise ValueError(f"Unknown backend type: {self._backend_type}")
        
        return self._adapters["auth"]
    
    def get_database_adapter(self) -> DatabaseAdapter:
        """Get database adapter."""
        if "database" not in self._adapters:
            if self._backend_type == "supabase":
                self._adapters["database"] = SupabaseDatabaseAdapter()
            elif self._backend_type == "dotnet":
                # TODO: Implement .NET database adapter
                raise NotImplementedError(".NET database adapter not yet implemented")
            elif self._backend_type == "hybrid":
                # TODO: Implement hybrid database adapter
                raise NotImplementedError("Hybrid database adapter not yet implemented")
            else:
                raise ValueError(f"Unknown backend type: {self._backend_type}")
        
        return self._adapters["database"]
    
    def get_storage_adapter(self) -> StorageAdapter:
        """Get storage adapter."""
        if "storage" not in self._adapters:
            if self._backend_type == "supabase":
                self._adapters["storage"] = SupabaseStorageAdapter()
            elif self._backend_type == "dotnet":
                # TODO: Implement .NET storage adapter
                raise NotImplementedError(".NET storage adapter not yet implemented")
            elif self._backend_type == "hybrid":
                # Could use Supabase storage with .NET data, for example
                self._adapters["storage"] = SupabaseStorageAdapter()
            else:
                raise ValueError(f"Unknown backend type: {self._backend_type}")
        
        return self._adapters["storage"]
    
    def get_realtime_adapter(self) -> RealtimeAdapter:
        """Get realtime adapter."""
        if "realtime" not in self._adapters:
            if self._backend_type == "supabase":
                self._adapters["realtime"] = SupabaseRealtimeAdapter()
            elif self._backend_type == "dotnet":
                # TODO: Implement .NET realtime adapter (SignalR?)
                raise NotImplementedError(".NET realtime adapter not yet implemented")
            elif self._backend_type == "hybrid":
                # TODO: Implement hybrid realtime adapter
                raise NotImplementedError("Hybrid realtime adapter not yet implemented")
            else:
                raise ValueError(f"Unknown backend type: {self._backend_type}")
        
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