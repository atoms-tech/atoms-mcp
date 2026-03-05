"""
Comprehensive test suite for Pheno integration with full mocking.

This module provides complete test coverage for Pheno tunnel provider,
logger adapter, SDK initialization, configuration management, and error
handling using fully mocked Pheno components.
"""

from __future__ import annotations

import pytest
import logging
from typing import Any, Optional
from unittest.mock import MagicMock, Mock, patch, PropertyMock

from atoms_mcp.adapters.secondary.pheno.tunnel import (
    PhenoTunnelAdapter,
    get_pheno_tunnel,
    reset_tunnel,
)
from atoms_mcp.adapters.secondary.pheno.logger import (
    PhenoLoggerAdapter,
)


# ============================================================================
# Mock Pheno Implementation
# ============================================================================


class MockPhenoTunnel:
    """Mock Pheno tunnel instance."""

    def __init__(
        self,
        port: int,
        subdomain: Optional[str] = None,
        should_fail: bool = False,
    ):
        self.port = port
        self.subdomain = subdomain
        self.should_fail = should_fail
        self._is_active = False
        self.public_url = f"https://{subdomain or 'random123'}.pheno.dev"

    def close(self):
        """Close the tunnel."""
        self._is_active = False

    @property
    def is_active(self) -> bool:
        """Check if tunnel is active."""
        return self._is_active


class MockTunnelProvider:
    """Mock Pheno tunnel provider."""

    def __init__(self):
        self.tunnels: list[MockPhenoTunnel] = []
        self.call_log: list[tuple[str, Any]] = []

    def create_tunnel(
        self,
        port: int,
        subdomain: Optional[str] = None,
    ) -> MockPhenoTunnel:
        """Create a mock tunnel."""
        self.call_log.append(("create_tunnel", {"port": port, "subdomain": subdomain}))
        tunnel = MockPhenoTunnel(port=port, subdomain=subdomain)
        tunnel._is_active = True
        self.tunnels.append(tunnel)
        return tunnel


class MockPhenoLogger:
    """Mock Pheno logger."""

    def __init__(self, name: str):
        self.name = name
        self.logs: list[tuple[str, str, dict]] = []

    def debug(self, message: str, **context):
        """Log debug message."""
        self.logs.append(("debug", message, context))

    def info(self, message: str, **context):
        """Log info message."""
        self.logs.append(("info", message, context))

    def warning(self, message: str, **context):
        """Log warning message."""
        self.logs.append(("warning", message, context))

    def error(self, message: str, **context):
        """Log error message."""
        self.logs.append(("error", message, context))

    def critical(self, message: str, **context):
        """Log critical message."""
        self.logs.append(("critical", message, context))


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_tunnel_provider():
    """Mock Pheno tunnel provider."""
    with patch("atoms_mcp.adapters.secondary.pheno.tunnel.TunnelProvider") as mock:
        provider = MockTunnelProvider()
        mock.return_value = provider
        yield provider


@pytest.fixture
def mock_pheno_logger_class():
    """Mock Pheno logger class."""
    with patch("atoms_mcp.adapters.secondary.pheno.logger.PhenoLogger") as mock:
        mock.side_effect = MockPhenoLogger
        yield mock


@pytest.fixture
def mock_settings():
    """Mock settings for Pheno."""
    with patch("atoms_mcp.adapters.secondary.pheno.tunnel.get_settings") as mock:
        settings = MagicMock()
        settings.pheno.tunnel_subdomain = None
        mock.return_value = settings
        yield settings


# ============================================================================
# Tunnel Setup and Configuration Tests (8 tests)
# ============================================================================


class TestPhenoTunnelSetup:
    """Test Pheno tunnel setup and configuration."""

    def test_tunnel_initialization_success(self, mock_tunnel_provider):
        """
        Given: Valid port configuration
        When: Creating tunnel adapter
        Then: Adapter is initialized successfully
        """
        adapter = PhenoTunnelAdapter(port=8000)

        assert adapter.port == 8000
        assert adapter.subdomain is None

    def test_tunnel_initialization_with_subdomain(self, mock_tunnel_provider):
        """
        Given: Custom subdomain
        When: Creating tunnel adapter
        Then: Subdomain is stored
        """
        adapter = PhenoTunnelAdapter(subdomain="myapp", port=8000)

        assert adapter.subdomain == "myapp"

    def test_tunnel_initialization_without_pheno(self):
        """
        Given: Pheno tunnel not available
        When: Attempting to create adapter
        Then: RuntimeError is raised
        """
        with patch("atoms_mcp.adapters.secondary.pheno.tunnel.PHENO_TUNNEL_AVAILABLE", False):
            with pytest.raises(RuntimeError, match="not available"):
                PhenoTunnelAdapter(port=8000)

    def test_tunnel_start_success(self, mock_tunnel_provider):
        """
        Given: Initialized tunnel adapter
        When: Starting the tunnel
        Then: Public URL is returned
        """
        adapter = PhenoTunnelAdapter(port=8000)

        url = adapter.start()

        assert url.startswith("https://")
        assert ".pheno.dev" in url
        assert adapter.is_running

    def test_tunnel_start_idempotent(self, mock_tunnel_provider):
        """
        Given: Already running tunnel
        When: Starting again
        Then: Same URL is returned without creating new tunnel
        """
        adapter = PhenoTunnelAdapter(port=8000)

        url1 = adapter.start()
        url2 = adapter.start()

        assert url1 == url2
        assert len(mock_tunnel_provider.tunnels) == 1

    def test_tunnel_stop_success(self, mock_tunnel_provider):
        """
        Given: Running tunnel
        When: Stopping the tunnel
        Then: Tunnel is closed
        """
        adapter = PhenoTunnelAdapter(port=8000)
        adapter.start()

        assert adapter.is_running

        adapter.stop()

        assert not adapter.is_running
        assert adapter.public_url is None

    def test_tunnel_public_url_property(self, mock_tunnel_provider):
        """
        Given: Running tunnel
        When: Accessing public_url property
        Then: URL is returned
        """
        adapter = PhenoTunnelAdapter(port=8000)
        adapter.start()

        url = adapter.public_url

        assert url is not None
        assert url.startswith("https://")

    def test_tunnel_public_url_not_started(self, mock_tunnel_provider):
        """
        Given: Tunnel not started
        When: Accessing public_url property
        Then: None is returned
        """
        adapter = PhenoTunnelAdapter(port=8000)

        url = adapter.public_url

        assert url is None


# ============================================================================
# Tunnel Context Manager Tests (3 tests)
# ============================================================================


class TestPhenoTunnelContextManager:
    """Test tunnel context manager functionality."""

    def test_tunnel_context_manager_success(self, mock_tunnel_provider):
        """
        Given: Tunnel adapter
        When: Using as context manager
        Then: Tunnel is started and stopped automatically
        """
        adapter = PhenoTunnelAdapter(port=8000)

        with adapter as tunnel:
            assert tunnel.is_running
            assert tunnel.public_url is not None

        assert not adapter.is_running

    def test_tunnel_context_manager_with_exception(self, mock_tunnel_provider):
        """
        Given: Tunnel in context manager
        When: Exception occurs
        Then: Tunnel is still stopped
        """
        adapter = PhenoTunnelAdapter(port=8000)

        try:
            with adapter:
                assert adapter.is_running
                raise ValueError("Test error")
        except ValueError:
            pass

        assert not adapter.is_running

    def test_tunnel_context_manager_reentry(self, mock_tunnel_provider):
        """
        Given: Tunnel used in context manager
        When: Using again in another context
        Then: Tunnel works correctly
        """
        adapter = PhenoTunnelAdapter(port=8000)

        with adapter:
            url1 = adapter.public_url

        with adapter:
            url2 = adapter.public_url

        assert url1 is not None
        assert url2 is not None


# ============================================================================
# Global Tunnel Management Tests (3 tests)
# ============================================================================


class TestPhenoGlobalTunnelManagement:
    """Test global tunnel instance management."""

    def test_get_pheno_tunnel_creates_instance(self, mock_tunnel_provider, mock_settings):
        """
        Given: No existing tunnel instance
        When: Getting pheno tunnel
        Then: New instance is created
        """
        reset_tunnel()

        tunnel = get_pheno_tunnel(port=8000)

        assert tunnel is not None
        assert isinstance(tunnel, PhenoTunnelAdapter)

    def test_get_pheno_tunnel_returns_singleton(self, mock_tunnel_provider, mock_settings):
        """
        Given: Existing tunnel instance
        When: Getting pheno tunnel again
        Then: Same instance is returned
        """
        reset_tunnel()

        tunnel1 = get_pheno_tunnel(port=8000)
        tunnel2 = get_pheno_tunnel(port=8000)

        assert tunnel1 is tunnel2

    def test_get_pheno_tunnel_not_available(self):
        """
        Given: Pheno tunnel not available
        When: Getting pheno tunnel
        Then: None is returned
        """
        with patch("atoms_mcp.adapters.secondary.pheno.tunnel.PHENO_TUNNEL_AVAILABLE", False):
            reset_tunnel()

            tunnel = get_pheno_tunnel(port=8000)

            assert tunnel is None


# ============================================================================
# Logger Adapter Tests (10 tests)
# ============================================================================


class TestPhenoLoggerAdapter:
    """Test Pheno logger adapter integration."""

    def test_logger_initialization_success(self, mock_pheno_logger_class):
        """
        Given: Valid logger name
        When: Creating logger adapter
        Then: Adapter is initialized
        """
        logger = PhenoLoggerAdapter("test_logger")

        assert logger.name == "test_logger"

    def test_logger_initialization_without_pheno(self):
        """
        Given: Pheno logging not available
        When: Attempting to create logger
        Then: RuntimeError is raised
        """
        with patch("atoms_mcp.adapters.secondary.pheno.logger.PHENO_LOGGING_AVAILABLE", False):
            with pytest.raises(RuntimeError, match="not available"):
                PhenoLoggerAdapter("test")

    def test_logger_debug_message(self, mock_pheno_logger_class):
        """
        Given: Logger adapter
        When: Logging debug message
        Then: Message is logged at debug level
        """
        logger = PhenoLoggerAdapter("test", level="DEBUG")
        logger._pheno_logger = MockPhenoLogger("test")

        logger.debug("Debug message")

        assert len(logger._pheno_logger.logs) == 1
        level, message, context = logger._pheno_logger.logs[0]
        assert level == "debug"
        assert message == "Debug message"

    def test_logger_info_message(self, mock_pheno_logger_class):
        """
        Given: Logger adapter
        When: Logging info message
        Then: Message is logged at info level
        """
        logger = PhenoLoggerAdapter("test")
        logger._pheno_logger = MockPhenoLogger("test")

        logger.info("Info message")

        assert len(logger._pheno_logger.logs) == 1
        level, message, context = logger._pheno_logger.logs[0]
        assert level == "info"
        assert message == "Info message"

    def test_logger_warning_message(self, mock_pheno_logger_class):
        """
        Given: Logger adapter
        When: Logging warning message
        Then: Message is logged at warning level
        """
        logger = PhenoLoggerAdapter("test")
        logger._pheno_logger = MockPhenoLogger("test")

        logger.warning("Warning message")

        assert len(logger._pheno_logger.logs) == 1
        level, message, context = logger._pheno_logger.logs[0]
        assert level == "warning"
        assert message == "Warning message"

    def test_logger_error_message(self, mock_pheno_logger_class):
        """
        Given: Logger adapter
        When: Logging error message
        Then: Message is logged at error level
        """
        logger = PhenoLoggerAdapter("test")
        logger._pheno_logger = MockPhenoLogger("test")

        logger.error("Error message")

        assert len(logger._pheno_logger.logs) == 1
        level, message, context = logger._pheno_logger.logs[0]
        assert level == "error"
        assert message == "Error message"

    def test_logger_critical_message(self, mock_pheno_logger_class):
        """
        Given: Logger adapter
        When: Logging critical message
        Then: Message is logged at critical level
        """
        logger = PhenoLoggerAdapter("test")
        logger._pheno_logger = MockPhenoLogger("test")

        logger.critical("Critical message")

        assert len(logger._pheno_logger.logs) == 1
        level, message, context = logger._pheno_logger.logs[0]
        assert level == "critical"
        assert message == "Critical message"

    def test_logger_with_context(self, mock_pheno_logger_class):
        """
        Given: Logger adapter
        When: Logging with context data
        Then: Context is included in log
        """
        logger = PhenoLoggerAdapter("test")
        logger._pheno_logger = MockPhenoLogger("test")

        logger.info("Message", user_id=123, action="login")

        level, message, context = logger._pheno_logger.logs[0]
        assert context["user_id"] == 123
        assert context["action"] == "login"

    def test_logger_with_formatting(self, mock_pheno_logger_class):
        """
        Given: Logger adapter
        When: Logging with format string
        Then: Message is formatted correctly
        """
        logger = PhenoLoggerAdapter("test")
        logger._pheno_logger = MockPhenoLogger("test")

        logger.info("User %s logged in", "john")

        level, message, context = logger._pheno_logger.logs[0]
        assert message == "User john logged in"

    def test_logger_exception_with_traceback(self, mock_pheno_logger_class):
        """
        Given: Logger adapter
        When: Logging exception
        Then: Exception info and traceback are included
        """
        logger = PhenoLoggerAdapter("test")
        logger._pheno_logger = MockPhenoLogger("test")

        try:
            raise ValueError("Test error")
        except ValueError:
            logger.exception("An error occurred")

        level, message, context = logger._pheno_logger.logs[0]
        assert level == "error"
        assert "exception" in context
        assert "traceback" in context


# ============================================================================
# Error Handling Tests (5 tests)
# ============================================================================


class TestPhenoErrorHandling:
    """Test error handling in Pheno integration."""

    def test_tunnel_start_failure(self, mock_tunnel_provider):
        """
        Given: Tunnel creation that fails
        When: Starting tunnel
        Then: RuntimeError is raised
        """
        with patch.object(mock_tunnel_provider, "create_tunnel") as mock_create:
            mock_create.side_effect = Exception("Connection failed")

            adapter = PhenoTunnelAdapter(port=8000)

            with pytest.raises(RuntimeError, match="Failed to start tunnel"):
                adapter.start()

    def test_tunnel_stop_with_error(self, mock_tunnel_provider):
        """
        Given: Running tunnel with close error
        When: Stopping tunnel
        Then: Error is silently handled
        """
        adapter = PhenoTunnelAdapter(port=8000)
        adapter.start()

        # Mock close to raise error
        adapter._tunnel.close = Mock(side_effect=Exception("Close error"))

        # Should not raise
        adapter.stop()

        assert not adapter.is_running

    def test_logger_level_filtering(self, mock_pheno_logger_class):
        """
        Given: Logger with specific level
        When: Logging below that level
        Then: Message is not logged
        """
        logger = PhenoLoggerAdapter("test", level="ERROR")
        logger._pheno_logger = MockPhenoLogger("test")

        logger.debug("Debug message")
        logger.info("Info message")

        # Should not log messages below ERROR level
        assert len(logger._pheno_logger.logs) == 0

    def test_reset_tunnel_with_running_tunnel(self, mock_tunnel_provider):
        """
        Given: Running global tunnel
        When: Resetting tunnel
        Then: Tunnel is stopped and cleared
        """
        reset_tunnel()

        tunnel = get_pheno_tunnel(port=8000)
        tunnel.start()

        assert tunnel.is_running

        reset_tunnel()

        # New tunnel should be independent
        new_tunnel = get_pheno_tunnel(port=8000)
        assert not new_tunnel.is_running

    def test_get_pheno_tunnel_with_settings_subdomain(self, mock_tunnel_provider, mock_settings):
        """
        Given: Settings with tunnel subdomain
        When: Getting pheno tunnel
        Then: Subdomain from settings is used
        """
        reset_tunnel()
        mock_settings.pheno.tunnel_subdomain = "myapp"

        tunnel = get_pheno_tunnel(port=8000)

        assert tunnel.subdomain == "myapp"


# ============================================================================
# Integration and Configuration Tests (5 tests)
# ============================================================================


class TestPhenoIntegrationConfiguration:
    """Test Pheno integration and configuration."""

    def test_tunnel_with_different_ports(self, mock_tunnel_provider):
        """
        Given: Tunnel adapters with different ports
        When: Creating multiple adapters
        Then: Each uses correct port
        """
        adapter1 = PhenoTunnelAdapter(port=8000)
        adapter2 = PhenoTunnelAdapter(port=9000)

        assert adapter1.port == 8000
        assert adapter2.port == 9000

    def test_tunnel_subdomain_in_url(self, mock_tunnel_provider):
        """
        Given: Tunnel with custom subdomain
        When: Starting tunnel
        Then: Subdomain appears in public URL
        """
        adapter = PhenoTunnelAdapter(subdomain="myapp", port=8000)

        url = adapter.start()

        assert "myapp" in url

    def test_logger_inherits_from_logging_logger(self, mock_pheno_logger_class):
        """
        Given: PhenoLoggerAdapter
        When: Checking inheritance
        Then: Inherits from logging.Logger
        """
        logger = PhenoLoggerAdapter("test")

        assert isinstance(logger, logging.Logger)

    def test_logger_context_private_fields_filtered(self, mock_pheno_logger_class):
        """
        Given: Logger with context including private fields
        When: Logging message
        Then: Private fields are filtered out
        """
        logger = PhenoLoggerAdapter("test")
        logger._pheno_logger = MockPhenoLogger("test")

        logger.info("Message", _private="hidden", public="visible")

        level, message, context = logger._pheno_logger.logs[0]
        assert "public" in context
        assert "_private" not in context

    def test_multiple_tunnel_instances_independent(self, mock_tunnel_provider):
        """
        Given: Multiple tunnel adapter instances
        When: Operating on them independently
        Then: Each maintains separate state
        """
        adapter1 = PhenoTunnelAdapter(port=8000)
        adapter2 = PhenoTunnelAdapter(port=9000)

        adapter1.start()

        assert adapter1.is_running
        assert not adapter2.is_running

        adapter2.start()

        assert adapter1.is_running
        assert adapter2.is_running
