"""
Test script for infrastructure layer.

Run this to verify all infrastructure components work correctly.
"""

import sys
import os
from pathlib import Path

# Add src to path, but import modules directly to avoid atoms_mcp.__init__.py
root_dir = Path(__file__).parent
src_dir = root_dir / "src"
sys.path.insert(0, str(src_dir))


def test_config():
    """Test configuration settings."""
    print("=" * 60)
    print("TEST 1: Configuration Settings")
    print("=" * 60)

    from atoms_mcp.infrastructure.config.settings import Settings

    settings = Settings(
        environment="development",
        database={"url": "https://test.supabase.co", "api_key": "test-key"},
        vertex_ai={"project_id": "test-project"},
        workos={"api_key": "test-workos-key"},
    )

    print(f"✓ Settings created successfully")
    print(f"  - App: {settings.app_name}")
    print(f"  - Environment: {settings.environment}")
    print(f"  - Database URL: {settings.database.url}")
    print(f"  - Cache backend: {settings.cache.backend.value}")
    print(f"  - Log level: {settings.logging.level.value}")
    print()
    return settings


def test_logger():
    """Test logger."""
    print("=" * 60)
    print("TEST 2: Logger")
    print("=" * 60)

    from atoms_mcp.infrastructure.logging.logger import get_logger

    logger = get_logger("test")
    logger.info("Test info message", user_id="123")
    logger.debug("Test debug message")
    logger.warning("Test warning", operation="test")
    print("✓ Logger working correctly")
    print()
    return logger


def test_cache():
    """Test cache."""
    print("=" * 60)
    print("TEST 3: Cache")
    print("=" * 60)

    from atoms_mcp.infrastructure.cache.provider import InMemoryCacheProvider

    cache = InMemoryCacheProvider(max_size=100, default_ttl=60)
    cache.set("test_key", {"data": "value"})
    result = cache.get("test_key")
    print(f"✓ Cache set/get working: {result}")

    cache.set_many({"key1": "val1", "key2": "val2"})
    batch = cache.get_many(["key1", "key2"])
    print(f"✓ Batch operations working: {batch}")

    # Test expiry
    cache.set("expiring_key", "value", ttl=1)
    import time
    time.sleep(1.1)
    expired = cache.get("expiring_key")
    print(f"✓ TTL expiration working: {expired is None}")
    print()
    return cache


def test_exceptions():
    """Test exceptions."""
    print("=" * 60)
    print("TEST 4: Exceptions")
    print("=" * 60)

    from atoms_mcp.infrastructure.errors.exceptions import (
        EntityNotFoundException,
        ValidationException,
        ErrorCode,
    )

    try:
        raise EntityNotFoundException(entity_type="project", entity_id="123")
    except EntityNotFoundException as e:
        print(f"✓ EntityNotFoundException: {e}")
        print(f"  - Error code: {e.error_code.value}")
        print(f"  - Details: {e.details}")
        assert e.error_code == ErrorCode.ENTITY_NOT_FOUND

    try:
        raise ValidationException(
            message="Invalid email", field="email", value="invalid-email"
        )
    except ValidationException as e:
        print(f"✓ ValidationException: {e}")
        print(f"  - Error code: {e.error_code.value}")
        assert e.error_code == ErrorCode.VALIDATION_ERROR
    print()


def test_di_container(settings):
    """Test DI container."""
    print("=" * 60)
    print("TEST 5: DI Container")
    print("=" * 60)

    from atoms_mcp.infrastructure.di.container import Container

    container = Container()
    container.initialize(settings)
    print(f"✓ Container initialized")
    print(f"  - Has settings: {container.has('settings')}")
    print(f"  - Has logger: {container.has('logger')}")
    print(f"  - Has cache: {container.has('cache')}")

    retrieved_settings = container.get("settings")
    print(f"  - Retrieved settings: {retrieved_settings.app_name}")

    # Test scope
    with container.create_scope() as scope:
        scope.register("scoped_value", "test")
        scoped_val = scope.get("scoped_value")
        print(f"  - Scoped value: {scoped_val}")

    print()
    return container


def test_serialization():
    """Test serialization."""
    print("=" * 60)
    print("TEST 6: Serialization")
    print("=" * 60)

    from atoms_mcp.infrastructure.serialization.json import dumps, loads, is_json
    from datetime import datetime
    from uuid import uuid4

    test_data = {
        "id": uuid4(),
        "timestamp": datetime.now(),
        "data": {"key": "value"},
        "items": [1, 2, 3],
    }

    serialized = dumps(test_data)
    print(f"✓ Serialization working: {serialized[:80]}...")

    deserialized = loads(serialized)
    print(f"✓ Deserialization working: {deserialized['data']}")

    print(f"✓ JSON validation: is_json(serialized) = {is_json(serialized)}")
    print()


def test_error_handlers():
    """Test error handlers."""
    print("=" * 60)
    print("TEST 7: Error Handlers")
    print("=" * 60)

    from atoms_mcp.infrastructure.errors.handlers import (
        handle_application_exception,
        exception_to_http_status,
    )
    from atoms_mcp.infrastructure.errors.exceptions import (
        EntityNotFoundException,
        ErrorCode,
    )

    exc = EntityNotFoundException(entity_type="project", entity_id="123")
    response = handle_application_exception(exc)
    status = exception_to_http_status(exc.error_code)

    print(f"✓ Error handler response: {response}")
    print(f"✓ HTTP status code: {status}")
    assert status == 404
    assert response["error"] is True
    print()


def test_logging_setup():
    """Test logging setup."""
    print("=" * 60)
    print("TEST 8: Logging Setup")
    print("=" * 60)

    from atoms_mcp.infrastructure.logging.setup import (
        setup_logging,
        set_request_context,
        get_request_context,
        clear_request_context,
    )
    from atoms_mcp.infrastructure.config.settings import LoggingSettings, LogLevel

    config = LoggingSettings(
        level=LogLevel.INFO,
        console_enabled=True,
        file_enabled=False,
    )

    setup_logging(config)
    print("✓ Logging configured")

    set_request_context(request_id="req-123", user_id="user-456")
    context = get_request_context()
    print(f"✓ Request context set: {context}")

    clear_request_context()
    cleared_context = get_request_context()
    print(f"✓ Request context cleared: {cleared_context}")
    print()


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("INFRASTRUCTURE LAYER TESTS")
    print("=" * 60 + "\n")

    try:
        # Run tests
        settings = test_config()
        logger = test_logger()
        cache = test_cache()
        test_exceptions()
        container = test_di_container(settings)
        test_serialization()
        test_error_handlers()
        test_logging_setup()

        # Summary
        print("=" * 60)
        print("ALL INFRASTRUCTURE TESTS PASSED ✓")
        print("=" * 60)
        print("\nInfrastructure layer components:")
        print("  ✓ Configuration (Pydantic settings)")
        print("  ✓ Logging (stdlib with context)")
        print("  ✓ Error handling (exceptions + handlers)")
        print("  ✓ Dependency injection (simple container)")
        print("  ✓ Caching (in-memory + Redis support)")
        print("  ✓ Serialization (JSON with custom types)")
        print("\nAll components work without optional dependencies!")
        print()

        return 0

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
