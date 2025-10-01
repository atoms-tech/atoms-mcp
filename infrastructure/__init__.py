"""Infrastructure abstraction layer for atoms_fastmcp.

This module provides abstract interfaces for all infrastructure services
(auth, database, storage, realtime) to enable easy swapping of backends.
"""

try:
    from .adapters import (
        AuthAdapter,
        DatabaseAdapter,
        StorageAdapter,
        RealtimeAdapter
    )
    from .factory import get_adapters
except ImportError:
    from infrastructure.adapters import (
        AuthAdapter,
        DatabaseAdapter,
        StorageAdapter,
        RealtimeAdapter
    )
    from infrastructure.factory import get_adapters

__all__ = [
    "AuthAdapter",
    "DatabaseAdapter", 
    "StorageAdapter",
    "RealtimeAdapter",
    "get_adapters"
]