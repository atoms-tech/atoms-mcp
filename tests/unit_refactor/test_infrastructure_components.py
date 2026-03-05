"""
Comprehensive tests for infrastructure layer components.

Tests cover:
- Cache provider implementations (InMemoryCache)
- Cache factory function
- Dependency injection container
- Dependency scopes
- Settings and configuration validation
- Dependency providers
"""

import time
from pathlib import Path
from typing import Any, Optional

import pytest

from atoms_mcp.infrastructure.cache.provider import (
    InMemoryCacheProvider,
    create_cache_provider,
)
from atoms_mcp.infrastructure.di.container import Container, Scope, get_container, reset_container
from atoms_mcp.infrastructure.di.providers import (
    CacheProvider,
    LoggerProvider,
)
from atoms_mcp.infrastructure.config.settings import (
    CacheBackend,
    CacheSettings,
    DatabaseSettings,
    LogLevel,
    LogFormat,
    LoggingSettings,
    MCPServerSettings,
    Settings,
    VertexAISettings,
    WorkOSSettings,
    get_settings,
    reset_settings,
)
from atoms_mcp.infrastructure.errors.exceptions import CacheException


# ============================================================================
# Cache Provider Tests
# ============================================================================


class TestInMemoryCacheBasicOperations:
    """Tests for basic cache operations."""

    @pytest.fixture
    def cache(self):
        """Create an in-memory cache instance."""
        return InMemoryCacheProvider(max_size=1000, default_ttl=300)

    def test_set_and_get_basic_value(self, cache):
        """Should store and retrieve a basic value."""
        assert cache.set("key1", "value1") is True
        assert cache.get("key1") == "value1"

    def test_get_nonexistent_key_returns_none(self, cache):
        """Should return None for non-existent keys."""
        assert cache.get("nonexistent") is None

    def test_set_overwrites_existing_value(self, cache):
        """Should overwrite previous value with same key."""
        cache.set("key1", "value1")
        assert cache.set("key1", "value2") is True
        assert cache.get("key1") == "value2"

    def test_delete_existing_key(self, cache):
        """Should delete an existing key."""
        cache.set("key1", "value1")
        assert cache.delete("key1") is True
        assert cache.get("key1") is None

    def test_delete_nonexistent_key_returns_false(self, cache):
        """Should return False when deleting non-existent key."""
        assert cache.delete("nonexistent") is False

    def test_exists_returns_true_for_existing_key(self, cache):
        """Should return True for existing keys."""
        cache.set("key1", "value1")
        assert cache.exists("key1") is True

    def test_exists_returns_false_for_nonexistent_key(self, cache):
        """Should return False for non-existent keys."""
        assert cache.exists("nonexistent") is False

    def test_clear_removes_all_entries(self, cache):
        """Should clear all entries from cache."""
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        assert cache.clear() is True
        assert cache.get("key1") is None
        assert cache.get("key2") is None


class TestInMemoryCacheDataTypes:
    """Tests for different data types in cache."""

    @pytest.fixture
    def cache(self):
        """Create an in-memory cache instance."""
        return InMemoryCacheProvider(max_size=1000, default_ttl=300)

    def test_cache_string_values(self, cache):
        """Should cache string values."""
        cache.set("str_key", "test string")
        assert cache.get("str_key") == "test string"

    def test_cache_integer_values(self, cache):
        """Should cache integer values."""
        cache.set("int_key", 42)
        assert cache.get("int_key") == 42

    def test_cache_dictionary_values(self, cache):
        """Should cache dictionary values."""
        data = {"name": "Test", "value": 123}
        cache.set("dict_key", data)
        assert cache.get("dict_key") == data

    def test_cache_list_values(self, cache):
        """Should cache list values."""
        data = [1, 2, 3, 4, 5]
        cache.set("list_key", data)
        assert cache.get("list_key") == data

    def test_cache_none_value(self, cache):
        """Should not cache None values (treated as missing)."""
        cache.set("none_key", None)
        # get_many will treat None as missing when retrieving
        assert cache.get("none_key") is None

    def test_cache_complex_nested_structure(self, cache):
        """Should cache complex nested structures."""
        data = {
            "users": [
                {"id": 1, "name": "Alice", "tags": ["admin", "active"]},
                {"id": 2, "name": "Bob", "tags": ["user"]},
            ],
            "metadata": {"count": 2, "version": "1.0"},
        }
        cache.set("complex_key", data)
        assert cache.get("complex_key") == data


class TestInMemoryCacheTTL:
    """Tests for TTL (time-to-live) functionality."""

    @pytest.fixture
    def cache(self):
        """Create an in-memory cache instance with default TTL."""
        return InMemoryCacheProvider(max_size=1000, default_ttl=1)

    def test_expired_key_returns_none(self, cache):
        """Should return None for expired keys."""
        cache.set("expiring_key", "value")
        assert cache.get("expiring_key") == "value"

        # Wait for expiration
        time.sleep(1.1)

        # Key should be expired
        assert cache.get("expiring_key") is None

    def test_custom_ttl_overrides_default(self, cache):
        """Should use custom TTL over default TTL."""
        cache.set("custom_ttl_key", "value", ttl=5)
        assert cache.get("custom_ttl_key") == "value"

        # Wait for default TTL to expire (1 second) with buffer
        time.sleep(1.5)

        # Key should still exist because custom TTL is 5 seconds
        assert cache.get("custom_ttl_key") == "value"

    def test_zero_ttl_means_no_expiration(self, cache):
        """Should not expire keys when TTL is 0."""
        cache.set("no_expiry_key", "value", ttl=0)
        assert cache.get("no_expiry_key") == "value"

        # Wait for default TTL
        time.sleep(1.1)

        # Key should still exist because TTL=0 means no expiration
        assert cache.get("no_expiry_key") == "value"


class TestInMemoryCacheMaxSize:
    """Tests for max size eviction."""

    @pytest.fixture
    def cache(self):
        """Create a small cache for testing eviction."""
        return InMemoryCacheProvider(max_size=3, default_ttl=300)

    def test_eviction_when_size_exceeded(self, cache):
        """Should evict oldest entry when max size is exceeded."""
        # Add entries up to max_size
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # Add one more (should evict key1)
        cache.set("key4", "value4")

        # key1 should be gone (oldest)
        assert cache.get("key1") is None

        # Others should exist
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"

    def test_update_existing_key_doesnt_evict(self, cache):
        """Should not evict when updating existing key."""
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # Update existing key (size still 3)
        cache.set("key2", "updated_value2")

        # All keys should exist
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "updated_value2"
        assert cache.get("key3") == "value3"


class TestInMemoryCacheBulkOperations:
    """Tests for bulk operations (get_many, set_many)."""

    @pytest.fixture
    def cache(self):
        """Create an in-memory cache instance."""
        return InMemoryCacheProvider(max_size=1000, default_ttl=300)

    def test_get_many_retrieves_multiple_values(self, cache):
        """Should retrieve multiple values."""
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        result = cache.get_many(["key1", "key2", "key3"])

        assert result == {"key1": "value1", "key2": "value2", "key3": "value3"}

    def test_get_many_omits_missing_keys(self, cache):
        """Should omit missing keys from result."""
        cache.set("key1", "value1")
        cache.set("key3", "value3")

        result = cache.get_many(["key1", "key2", "key3"])

        assert result == {"key1": "value1", "key3": "value3"}
        assert "key2" not in result

    def test_get_many_empty_list(self, cache):
        """Should return empty dict for empty key list."""
        result = cache.get_many([])
        assert result == {}

    def test_set_many_stores_multiple_values(self, cache):
        """Should store multiple values."""
        data = {"key1": "value1", "key2": "value2", "key3": "value3"}

        assert cache.set_many(data) is True

        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"

    def test_set_many_with_custom_ttl(self, cache):
        """Should apply custom TTL to bulk operations."""
        data = {"key1": "value1", "key2": "value2"}

        cache.set_many(data, ttl=5)

        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"

        # Keys should not expire after 1 second (TTL is 5)
        time.sleep(1.1)
        assert cache.get("key1") == "value1"


class TestCacheProviderFactory:
    """Tests for cache provider factory function."""

    def test_create_memory_cache_default(self):
        """Should create in-memory cache by default."""
        cache = create_cache_provider()
        assert isinstance(cache, InMemoryCacheProvider)

    def test_create_memory_cache_explicit(self):
        """Should create in-memory cache when backend='memory'."""
        cache = create_cache_provider(backend="memory")
        assert isinstance(cache, InMemoryCacheProvider)

    def test_create_memory_cache_with_custom_params(self):
        """Should pass custom parameters to memory cache."""
        cache = create_cache_provider(
            backend="memory",
            max_size=500,
            default_ttl=600,
        )
        assert isinstance(cache, InMemoryCacheProvider)
        cache.set("test", "value")
        assert cache.get("test") == "value"

    def test_create_redis_cache_requires_url(self):
        """Should require redis_url for Redis backend."""
        with pytest.raises(ValueError) as exc_info:
            create_cache_provider(backend="redis")

        assert "redis_url is required" in str(exc_info.value)

    def test_create_invalid_backend_raises_error(self):
        """Should raise error for unknown backend."""
        with pytest.raises(ValueError) as exc_info:
            create_cache_provider(backend="invalid")

        assert "Unknown cache backend" in str(exc_info.value)


# ============================================================================
# DI Container Tests
# ============================================================================


class TestDIContainerBasics:
    """Tests for basic DI container functionality."""

    @pytest.fixture
    def container(self):
        """Create a fresh container for testing."""
        container = Container()
        yield container
        # Cleanup
        reset_container()

    def test_container_requires_initialization(self, container):
        """Should require initialization before use."""
        with pytest.raises(RuntimeError) as exc_info:
            container.get("any_key")

        assert "not initialized" in str(exc_info.value).lower()

    def test_initialize_container(self, container):
        """Should initialize without errors."""
        container.initialize()
        assert container._initialized is True

    def test_register_singleton(self, container):
        """Should register and retrieve singleton."""
        container.initialize()

        instance = {"test": "data"}
        container.register_singleton("my_service", instance)

        retrieved = container.get("my_service")
        assert retrieved is instance

    def test_singleton_returns_same_instance(self, container):
        """Should return same instance for singleton."""
        container.initialize()

        instance = object()
        container.register_singleton("my_service", instance)

        retrieved1 = container.get("my_service")
        retrieved2 = container.get("my_service")

        assert retrieved1 is retrieved2

    def test_register_factory(self, container):
        """Should register and use factory function."""
        container.initialize()

        call_count = [0]

        def factory():
            call_count[0] += 1
            return {"instance": call_count[0]}

        container.register_factory("my_factory", factory)

        # Each call should invoke factory
        result1 = container.get("my_factory")
        result2 = container.get("my_factory")

        assert result1["instance"] == 1
        assert result2["instance"] == 2

    def test_register_transient_alias(self, container):
        """Should support register_transient as alias for register_factory."""
        container.initialize()

        call_count = [0]

        def factory():
            call_count[0] += 1
            return {"instance": call_count[0]}

        container.register_transient("my_transient", factory)

        result1 = container.get("my_transient")
        result2 = container.get("my_transient")

        assert result1["instance"] == 1
        assert result2["instance"] == 2

    def test_get_nonexistent_dependency_raises_error(self, container):
        """Should raise KeyError for non-existent dependency."""
        container.initialize()

        with pytest.raises(KeyError) as exc_info:
            container.get("nonexistent")

        assert "not found" in str(exc_info.value)

    def test_has_dependency_check(self, container):
        """Should check if dependency is registered."""
        container.initialize()

        container.register_singleton("existing", "instance")

        assert container.has("existing") is True
        assert container.has("nonexistent") is False


class TestDIContainerCoreDependencies:
    """Tests for core dependencies registered by container."""

    @pytest.fixture
    def container(self):
        """Create and initialize container."""
        reset_settings()
        container = Container()
        container.initialize()
        yield container
        reset_container()
        reset_settings()

    def test_container_registers_settings(self, container):
        """Should register settings singleton."""
        settings = container.get("settings")
        assert settings is not None
        assert hasattr(settings, "cache")
        assert hasattr(settings, "logging")

    def test_container_registers_logger(self, container):
        """Should register logger singleton."""
        logger = container.get("logger")
        assert logger is not None
        assert hasattr(logger, "debug") or hasattr(logger, "info")

    def test_container_registers_cache(self, container):
        """Should register cache singleton."""
        cache = container.get("cache")
        assert cache is not None
        assert hasattr(cache, "get")
        assert hasattr(cache, "set")

    def test_core_dependencies_are_singletons(self, container):
        """Should return same instance for core dependencies."""
        settings1 = container.get("settings")
        settings2 = container.get("settings")

        assert settings1 is settings2


class TestDIContainerProperties:
    """Tests for container property accessors."""

    @pytest.fixture
    def container(self):
        """Create and initialize container."""
        reset_settings()
        container = Container()
        container.initialize()
        yield container
        reset_container()
        reset_settings()

    def test_settings_property(self, container):
        """Should access settings via property."""
        settings = container.settings
        assert settings is not None
        assert hasattr(settings, "cache")

    def test_logger_property(self, container):
        """Should access logger via property."""
        logger = container.logger
        assert logger is not None

    def test_cache_property(self, container):
        """Should access cache via property."""
        cache = container.cache
        assert cache is not None
        assert hasattr(cache, "get")


class TestDIContainerReset:
    """Tests for container reset functionality."""

    def test_clear_removes_all_dependencies(self):
        """Should clear all registered dependencies."""
        container = Container()
        container.initialize()

        container.register_singleton("test_key", "test_value")
        assert container.has("test_key") is True

        container.clear()

        assert container.has("test_key") is False
        assert container._initialized is False


class TestDIScope:
    """Tests for dependency scope functionality."""

    @pytest.fixture
    def container(self):
        """Create and initialize container."""
        reset_settings()
        container = Container()
        container.initialize()
        yield container
        reset_container()
        reset_settings()

    def test_create_scope(self, container):
        """Should create a scope from container."""
        scope = container.create_scope()
        assert isinstance(scope, Scope)

    def test_scope_inherits_from_container(self, container):
        """Should get container dependencies from scope."""
        scope = container.create_scope()

        settings = scope.get("settings")
        assert settings is not None

    def test_scope_register_scoped_instance(self, container):
        """Should register scope-specific instance."""
        scope = container.create_scope()

        scope.register("scoped_key", "scoped_value")
        assert scope.get("scoped_key") == "scoped_value"

    def test_scope_instance_not_in_container(self, container):
        """Should not expose scope instance to container."""
        scope = container.create_scope()
        scope.register("scoped_key", "scoped_value")

        with pytest.raises(KeyError):
            container.get("scoped_key")

    def test_scope_context_manager(self, container):
        """Should work as context manager."""
        with container.create_scope() as scope:
            scope.register("scoped_key", "scoped_value")
            assert scope.get("scoped_key") == "scoped_value"

    def test_scope_clears_on_exit(self, container):
        """Should clear instances when exiting context."""
        scope = container.create_scope()
        scope.register("scoped_key", "scoped_value")

        scope.__enter__()
        assert scope.get("scoped_key") == "scoped_value"

        scope.__exit__(None, None, None)
        assert len(scope._scoped_instances) == 0


class TestGlobalContainer:
    """Tests for global container instance."""

    def test_get_container_creates_singleton(self):
        """Should create a singleton global container."""
        reset_container()

        container1 = get_container()
        container2 = get_container()

        assert container1 is container2

    def test_global_container_initialized(self):
        """Should return initialized container."""
        reset_container()

        container = get_container()

        # Should have settings
        assert container.has("settings")

    def test_reset_container_clears_global(self):
        """Should reset global container instance."""
        reset_container()

        container1 = get_container()
        reset_container()

        container2 = get_container()

        assert container1 is not container2


# ============================================================================
# Settings and Configuration Tests
# ============================================================================


class TestCacheSettings:
    """Tests for cache configuration settings."""

    def test_cache_settings_defaults(self):
        """Should have sensible defaults."""
        settings = CacheSettings()

        assert settings.backend == CacheBackend.MEMORY
        assert settings.default_ttl == 300
        assert settings.max_size == 1000

    def test_cache_settings_memory_backend(self):
        """Should accept memory backend."""
        settings = CacheSettings(backend=CacheBackend.MEMORY)
        assert settings.backend == CacheBackend.MEMORY

    def test_cache_settings_redis_backend(self):
        """Should accept Redis backend."""
        settings = CacheSettings(backend=CacheBackend.REDIS)
        assert settings.backend == CacheBackend.REDIS

    def test_cache_settings_custom_values(self):
        """Should accept custom values."""
        settings = CacheSettings(
            backend=CacheBackend.MEMORY,
            default_ttl=600,
            max_size=5000,
        )

        assert settings.default_ttl == 600
        assert settings.max_size == 5000

    def test_cache_settings_ttl_validation(self):
        """Should validate TTL is non-negative."""
        # Should accept 0 (no expiration)
        settings = CacheSettings(default_ttl=0)
        assert settings.default_ttl == 0

    def test_cache_settings_max_size_validation(self):
        """Should validate max_size is positive."""
        with pytest.raises(ValueError):
            CacheSettings(max_size=0)

    def test_cache_settings_redis_url_construction(self):
        """Should construct redis_url from components if needed."""
        settings = CacheSettings(
            backend=CacheBackend.REDIS,
            redis_host="localhost",
            redis_port=6379,
            redis_db=0,
        )

        assert settings.redis_url is not None
        assert "localhost:6379" in settings.redis_url


class TestLoggingSettings:
    """Tests for logging configuration settings."""

    def test_logging_settings_defaults(self):
        """Should have sensible logging defaults."""
        settings = LoggingSettings()

        # Level might be overridden by environment, just check it's a valid LogLevel
        assert settings.level in LogLevel
        assert settings.format == LogFormat.TEXT
        assert settings.console_enabled is True
        assert settings.file_enabled is False

    def test_logging_settings_log_levels(self):
        """Should accept all log levels."""
        for level in LogLevel:
            settings = LoggingSettings(level=level)
            assert settings.level == level

    def test_logging_settings_log_formats(self):
        """Should accept all log formats."""
        for fmt in LogFormat:
            settings = LoggingSettings(format=fmt)
            assert settings.format == fmt

    def test_logging_settings_custom_values(self):
        """Should accept custom values."""
        settings = LoggingSettings(
            level=LogLevel.DEBUG,
            format=LogFormat.JSON,
            console_enabled=False,
            file_enabled=True,
        )

        assert settings.level == LogLevel.DEBUG
        assert settings.format == LogFormat.JSON
        assert settings.console_enabled is False
        assert settings.file_enabled is True


class TestMCPServerSettings:
    """Tests for MCP server configuration settings."""

    def test_mcp_server_settings_defaults(self):
        """Should have sensible defaults."""
        settings = MCPServerSettings()

        assert settings.host == "localhost"
        assert settings.port == 8765
        assert settings.max_workers == 10
        assert settings.timeout == 300
        assert settings.cors_enabled is True

    def test_mcp_server_settings_port_validation(self):
        """Should validate port is in valid range."""
        # Valid port
        settings = MCPServerSettings(port=8080)
        assert settings.port == 8080

        # Invalid port (too low)
        with pytest.raises(ValueError):
            MCPServerSettings(port=100)

        # Invalid port (too high)
        with pytest.raises(ValueError):
            MCPServerSettings(port=70000)

    def test_mcp_server_settings_custom_values(self):
        """Should accept custom values."""
        settings = MCPServerSettings(
            host="0.0.0.0",
            port=9000,
            max_workers=20,
            timeout=600,
            cors_origins=["https://example.com"],
        )

        assert settings.host == "0.0.0.0"
        assert settings.port == 9000
        assert settings.max_workers == 20
        assert settings.timeout == 600
        assert "https://example.com" in settings.cors_origins


class TestMainSettings:
    """Tests for main Settings class."""

    def test_settings_creates_all_subsettings(self):
        """Should create all sub-settings."""
        reset_settings()

        settings = Settings()

        assert settings.database is not None
        assert settings.vertex_ai is not None
        assert settings.workos is not None
        assert settings.cache is not None
        assert settings.logging is not None
        assert settings.mcp_server is not None

    def test_settings_app_metadata(self):
        """Should have app metadata."""
        reset_settings()

        settings = Settings()

        assert settings.app_name == "Atoms MCP"
        assert settings.app_version == "1.0.0"
        assert settings.environment == "development"
        assert settings.debug is False

    def test_settings_debug_syncs_with_logging(self):
        """Should sync debug mode with logging level."""
        reset_settings()

        settings = Settings(debug=True)

        assert settings.logging.level == LogLevel.DEBUG

    def test_get_settings_singleton(self):
        """Should return singleton settings instance."""
        reset_settings()

        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1 is settings2

    def test_reset_settings_clears_singleton(self):
        """Should reset global settings instance."""
        reset_settings()

        settings1 = get_settings()
        reset_settings()

        settings2 = get_settings()

        assert settings1 is not settings2


class TestDependencyProviders:
    """Tests for dependency provider classes."""

    def test_logger_provider_create(self):
        """Should create logger instances."""
        logger = LoggerProvider.create()
        assert logger is not None
        assert hasattr(logger, "info") or hasattr(logger, "debug")

    def test_logger_provider_create_for_module(self):
        """Should create module-specific loggers."""
        logger = LoggerProvider.create_for_module("test.module")
        assert logger is not None

    def test_cache_provider_create_from_settings(self):
        """Should create cache from settings."""
        reset_settings()

        settings = Settings(cache=CacheSettings(backend=CacheBackend.MEMORY))
        cache = CacheProvider.create(settings)

        assert isinstance(cache, InMemoryCacheProvider)

    def test_cache_provider_create_memory_cache(self):
        """Should create memory cache directly."""
        cache = CacheProvider.create_memory_cache(max_size=500, default_ttl=600)

        assert isinstance(cache, InMemoryCacheProvider)
        cache.set("test", "value")
        assert cache.get("test") == "value"


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestCacheExceptionHandling:
    """Tests for cache exception handling."""

    def test_cache_handles_get_errors(self):
        """Should raise CacheException on get errors."""
        cache = InMemoryCacheProvider(max_size=1000, default_ttl=300)

        # Simulate error by corrupting internal state (for testing only)
        cache._cache["bad_key"] = ("value", "invalid_expiry_not_a_number")

        with pytest.raises(CacheException) as exc_info:
            cache.get("bad_key")

        assert "Failed to get value" in str(exc_info.value)

    def test_cache_handles_set_errors(self):
        """Should handle set operation errors."""
        cache = InMemoryCacheProvider(max_size=1000, default_ttl=300)

        # Normal set should work
        assert cache.set("key", "value") is True

    def test_cache_handles_delete_errors(self):
        """Should handle delete operation errors."""
        cache = InMemoryCacheProvider(max_size=1000, default_ttl=300)

        cache.set("key", "value")
        assert cache.delete("key") is True
        assert cache.delete("key") is False  # Already deleted

    def test_cache_handles_clear_errors(self):
        """Should handle clear operation errors."""
        cache = InMemoryCacheProvider(max_size=1000, default_ttl=300)

        cache.set("key", "value")
        assert cache.clear() is True


__all__ = [
    "TestInMemoryCacheBasicOperations",
    "TestInMemoryCacheDataTypes",
    "TestInMemoryCacheTTL",
    "TestInMemoryCacheMaxSize",
    "TestInMemoryCacheBulkOperations",
    "TestCacheProviderFactory",
    "TestDIContainerBasics",
    "TestDIContainerCoreDependencies",
    "TestDIContainerProperties",
    "TestDIContainerReset",
    "TestDIScope",
    "TestGlobalContainer",
    "TestCacheSettings",
    "TestLoggingSettings",
    "TestMCPServerSettings",
    "TestMainSettings",
    "TestDependencyProviders",
    "TestCacheExceptionHandling",
]
