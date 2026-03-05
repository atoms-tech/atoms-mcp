"""
Infrastructure layer for Atoms MCP.

This layer provides concrete implementations of infrastructure concerns:
- Configuration management
- Logging
- Error handling
- Dependency injection
- Caching
- Serialization

All implementations work without optional dependencies and follow
the ports defined in the domain layer.
"""

from .cache import (
    InMemoryCacheProvider,
    RedisCacheProvider,
    create_cache_provider,
)
from .config import (
    CacheBackend,
    CacheSettings,
    DatabaseSettings,
    LogFormat,
    LogLevel,
    LoggingSettings,
    MCPServerSettings,
    PhenoSDKSettings,
    Settings,
    VertexAISettings,
    WorkOSSettings,
    get_settings,
    reset_settings,
)
from .di import (
    AdapterProvider,
    CacheProvider,
    Container,
    LoggerProvider,
    RepositoryProvider,
    Scope,
    ServiceProvider,
    create_full_dependency_graph,
    get_container,
    inject,
    reset_container,
)
from .errors import (
    ApplicationException,
    CacheException,
    ConfigurationException,
    EntityNotFoundException,
    ErrorCode,
    RelationshipConflictException,
    RepositoryException,
    ValidationException,
    WorkflowException,
    create_error_response,
    exception_to_http_status,
    handle_application_exception,
    handle_generic_exception,
    log_exception,
)
from .logging import (
    JSONFormatter,
    StdLibLogger,
    TextFormatter,
    clear_request_context,
    get_logger,
    get_request_context,
    set_request_context,
    setup_logging,
)
from .serialization import (
    DomainJSONEncoder,
    deserialize_from_cache,
    dumps,
    dumps_pretty,
    is_json,
    loads,
    safe_dumps,
    safe_loads,
    serialize_for_cache,
)

__all__ = [
    # Config
    "Settings",
    "DatabaseSettings",
    "VertexAISettings",
    "WorkOSSettings",
    "PhenoSDKSettings",
    "CacheSettings",
    "LoggingSettings",
    "MCPServerSettings",
    "LogLevel",
    "LogFormat",
    "CacheBackend",
    "get_settings",
    "reset_settings",
    # Logging
    "StdLibLogger",
    "get_logger",
    "setup_logging",
    "set_request_context",
    "clear_request_context",
    "get_request_context",
    "JSONFormatter",
    "TextFormatter",
    # Errors
    "ApplicationException",
    "EntityNotFoundException",
    "RelationshipConflictException",
    "ValidationException",
    "RepositoryException",
    "CacheException",
    "WorkflowException",
    "ConfigurationException",
    "ErrorCode",
    "create_error_response",
    "exception_to_http_status",
    "handle_application_exception",
    "handle_generic_exception",
    "log_exception",
    # DI
    "Container",
    "Scope",
    "get_container",
    "inject",
    "reset_container",
    "LoggerProvider",
    "CacheProvider",
    "RepositoryProvider",
    "ServiceProvider",
    "AdapterProvider",
    "create_full_dependency_graph",
    # Cache
    "InMemoryCacheProvider",
    "RedisCacheProvider",
    "create_cache_provider",
    # Serialization
    "DomainJSONEncoder",
    "dumps",
    "dumps_pretty",
    "loads",
    "safe_dumps",
    "safe_loads",
    "serialize_for_cache",
    "deserialize_from_cache",
    "is_json",
]
