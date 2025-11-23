"""Infrastructure Module: Adapters for External Services.

This module provides adapters for external services used by the Atoms MCP Server.
Adapters implement the adapter pattern to abstract external service details from
the business logic layer. All external service calls go through adapters.

Adapters Provided:
    1. Database Adapter: Supabase PostgreSQL database
       - Entity CRUD operations
       - Relationship management
       - Query execution
       - Transaction support

    2. Auth Adapter: OAuth and Bearer token authentication
       - OAuth PKCE flow
       - Bearer token validation
       - Token refresh
       - Session management

    3. Storage Adapter: File storage
       - Store documents
       - Retrieve documents
       - Delete documents
       - Manage file metadata

    4. Realtime Adapter: Real-time updates
       - Subscribe to entity changes
       - Broadcast updates
       - Handle disconnections

Architecture:
    The adapter pattern provides:
    - Abstraction: Hide external service details
    - Testability: Easy to mock for testing
    - Flexibility: Easy to swap implementations
    - Consistency: Uniform interface for all adapters
    - Error Handling: Centralized error handling

Design Principles:
    - Adapter Pattern: Each adapter wraps an external service
    - Dependency Injection: Adapters are injected into services
    - Error Handling: Adapters handle service-specific errors
    - Logging: Adapters log all operations
    - Retry Logic: Adapters implement retry strategies

Example:
    Using adapters in services:

    >>> from infrastructure import DatabaseAdapter
    >>> db = DatabaseAdapter(supabase_url, supabase_key)
    >>> entity = await db.get_entity('ent_123')
    >>> print(entity)
    {'id': 'ent_123', 'title': 'My Entity', ...}

Note:
    - All adapters are async
    - Adapters handle connection pooling
    - Adapters implement error recovery
    - Adapters log all operations
    - Adapters are independent of business logic

See Also:
    - adapters.py: Adapter implementations
    - factory.py: Adapter factory
    - services/: Services that use adapters
"""

try:
    from .adapters import (
        AuthAdapter,
        DatabaseAdapter,
        StorageAdapter,
        RealtimeAdapter
    )
    from .factory import get_adapters
    from .mocks import (
        InMemoryDatabaseAdapter,
        InMemoryStorageAdapter,
        InMemoryAuthAdapter,
        InMemoryRealtimeAdapter,
        HttpMcpClient,
    )
except ImportError:
    from infrastructure.adapters import (
        AuthAdapter,
        DatabaseAdapter,
        StorageAdapter,
        RealtimeAdapter
    )
    from infrastructure.factory import get_adapters
    from infrastructure.mocks import (
        InMemoryDatabaseAdapter,
        InMemoryStorageAdapter,
        InMemoryAuthAdapter,
        InMemoryRealtimeAdapter,
        HttpMcpClient,
    )

__all__ = [
    "AuthAdapter",
    "DatabaseAdapter",
    "StorageAdapter",
    "RealtimeAdapter",
    "get_adapters",
    "InMemoryDatabaseAdapter",
    "InMemoryStorageAdapter",
    "InMemoryAuthAdapter",
    "InMemoryRealtimeAdapter",
    "HttpMcpClient",
]