"""Mock adapters for in-memory testing: Supabase + AuthKit Bearer tokens.

This submodule provides complete in-memory implementations of:
- InMemoryDatabaseAdapter: Supabase-compatible database operations
- InMemoryStorageAdapter: File/blob storage operations
- InMemoryAuthAdapter: AuthKit + Bearer token validation
- InMemoryRealtimeAdapter: Realtime subscriptions and events
- HttpMcpClient: HTTP client for local/hosted MCP servers

All adapters are fully functional for unit/integration testing.
"""

from __future__ import annotations

from .database import InMemoryDatabaseAdapter
from .storage import InMemoryStorageAdapter
from .auth import InMemoryAuthAdapter
from .realtime import InMemoryRealtimeAdapter
from .client import HttpMcpClient

__all__ = [
    "InMemoryDatabaseAdapter",
    "InMemoryStorageAdapter",
    "InMemoryAuthAdapter",
    "InMemoryRealtimeAdapter",
    "HttpMcpClient",
]
