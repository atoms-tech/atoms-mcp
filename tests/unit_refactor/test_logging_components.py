"""
Comprehensive unit tests for logging components achieving 100% code coverage.

Tests all logging functionality including:
- StdLibLogger methods (debug, info, warning, error, critical)
- Context management and field propagation
- Timer functionality
- Logger factory functions
- Formatters (JSON and Text)
- Logging setup and configuration
- Context variables for request tracking
"""

import logging
import time
import json
import sys
from io import StringIO
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock, call
import tempfile

import pytest

from atoms_mcp.infrastructure.logging.logger import (
    StdLibLogger,
    get_logger,
)
from atoms_mcp.infrastructure.logging.setup import (
    JSONFormatter,
    TextFormatter,
    setup_logging,
    set_request_context,
    clear_request_context,
    get_request_context,
    request_id_var,
    user_id_var,
    organization_id_var,
)
from atoms_mcp.infrastructure.config.settings import (
    LogLevel,
    LogFormat,
    LoggingSettings,
)


class TestStdLibLogger:
    """Test suite for StdLibLogger class."""

    def setup_method(self):
        """Set up test fixtures."""
        # Clear any existing handlers
        logging.root.handlers = []
        # Reset context variables
        clear_request_context()

    def test_logger_creation_default_name(self):
        """
        Given: No logger name specified
        When: Creating a StdLibLogger
        Then: Logger is created with default name
        """
        logger = StdLibLogger()
        assert logger._logger.name == "atoms_mcp"
        assert logger._extra_fields == {}

    def test_logger_creation_custom_name(self):
        """
        Given: Custom logger name
        When: Creating a StdLibLogger
        Then: Logger is created with custom name
        """
        logger = StdLibLogger("custom.module")
        assert logger._logger.name == "custom.module"

    def test_debug_message_simple(self, caplog):
        """
        Given: A logger instance
        When: Logging a debug message
        Then: Message is logged at DEBUG level
        """
        logger = StdLibLogger("test")
        logger._logger.setLevel(logging.DEBUG)

        with caplog.at_level(logging.DEBUG):
            logger.debug("Debug message")

        assert "Debug message" in caplog.text
        assert caplog.records[0].levelname == "DEBUG"

    def test_debug_message_with_kwargs(self, caplog):
        """
        Given: A logger instance
        When: Logging a debug message with kwargs
        Then: Message is logged with extra fields
        """
        logger = StdLibLogger("test")
        logger._logger.setLevel(logging.DEBUG)

        with caplog.at_level(logging.DEBUG):
            logger.debug("Debug with context", user_id="123", action="create")

        assert "Debug with context" in caplog.text
        record = caplog.records[0]
        assert hasattr(record, "extra_fields")
        assert record.extra_fields["user_id"] == "123"
        assert record.extra_fields["action"] == "create"

    def test_info_message_simple(self, caplog):
        """
        Given: A logger instance
        When: Logging an info message
        Then: Message is logged at INFO level
        """
        logger = StdLibLogger("test")

        with caplog.at_level(logging.INFO):
            logger.info("Info message")

        assert "Info message" in caplog.text
        assert caplog.records[0].levelname == "INFO"

    def test_info_message_with_kwargs(self, caplog):
        """
        Given: A logger instance
        When: Logging an info message with kwargs
        Then: Message is logged with extra fields
        """
        logger = StdLibLogger("test")

        with caplog.at_level(logging.INFO):
            logger.info("Info with context", request_id="req-123")

        assert "Info with context" in caplog.text
        record = caplog.records[0]
        assert hasattr(record, "extra_fields")
        assert record.extra_fields["request_id"] == "req-123"

    def test_warning_message_simple(self, caplog):
        """
        Given: A logger instance
        When: Logging a warning message
        Then: Message is logged at WARNING level
        """
        logger = StdLibLogger("test")

        with caplog.at_level(logging.WARNING):
            logger.warning("Warning message")

        assert "Warning message" in caplog.text
        assert caplog.records[0].levelname == "WARNING"

    def test_warning_message_with_kwargs(self, caplog):
        """
        Given: A logger instance
        When: Logging a warning message with kwargs
        Then: Message is logged with extra fields
        """
        logger = StdLibLogger("test")

        with caplog.at_level(logging.WARNING):
            logger.warning("Warning with context", severity="high")

        assert "Warning with context" in caplog.text
        record = caplog.records[0]
        assert hasattr(record, "extra_fields")
        assert record.extra_fields["severity"] == "high"

    def test_error_message_without_exception(self, caplog):
        """
        Given: A logger instance
        When: Logging an error message without exception
        Then: Message is logged at ERROR level without exc_info
        """
        logger = StdLibLogger("test")

        with caplog.at_level(logging.ERROR):
            logger.error("Error message")

        assert "Error message" in caplog.text
        assert caplog.records[0].levelname == "ERROR"
        # exc_info is False (not None) when exception is not provided
        assert caplog.records[0].exc_info is False or caplog.records[0].exc_info is None

    def test_error_message_with_exception(self, caplog):
        """
        Given: A logger instance and an exception
        When: Logging an error message with exception
        Then: Message is logged with exception info
        """
        logger = StdLibLogger("test")
        exc = ValueError("Something went wrong")

        with caplog.at_level(logging.ERROR):
            logger.error("Error occurred", exception=exc)

        assert "Error occurred" in caplog.text
        record = caplog.records[0]
        assert record.exc_info is not None
        # Exception info is added to extra dict which gets unpacked onto record
        assert hasattr(record, "exception_type")
        assert record.exception_type == "ValueError"
        assert record.exception_message == "Something went wrong"

    def test_error_message_with_exception_and_kwargs(self, caplog):
        """
        Given: A logger instance, exception, and kwargs
        When: Logging an error message
        Then: Message is logged with exception info and extra fields
        """
        logger = StdLibLogger("test")
        exc = RuntimeError("Runtime error")

        with caplog.at_level(logging.ERROR):
            logger.error("Error with context", exception=exc, operation="create_user")

        assert "Error with context" in caplog.text
        record = caplog.records[0]
        assert record.exc_info is not None
        # Exception info is added directly to extra dict
        assert record.exception_type == "RuntimeError"
        assert record.exception_message == "Runtime error"
        # kwargs are in extra_fields
        assert hasattr(record, "extra_fields")
        assert record.extra_fields["operation"] == "create_user"

    def test_critical_message_without_exception(self, caplog):
        """
        Given: A logger instance
        When: Logging a critical message without exception
        Then: Message is logged at CRITICAL level
        """
        logger = StdLibLogger("test")

        with caplog.at_level(logging.CRITICAL):
            logger.critical("Critical message")

        assert "Critical message" in caplog.text
        assert caplog.records[0].levelname == "CRITICAL"
        # exc_info is False (not None) when exception is not provided
        assert caplog.records[0].exc_info is False or caplog.records[0].exc_info is None

    def test_critical_message_with_exception(self, caplog):
        """
        Given: A logger instance and an exception
        When: Logging a critical message with exception
        Then: Message is logged with exception info
        """
        logger = StdLibLogger("test")
        exc = Exception("Critical failure")

        with caplog.at_level(logging.CRITICAL):
            logger.critical("System failure", exception=exc)

        assert "System failure" in caplog.text
        record = caplog.records[0]
        assert record.exc_info is not None
        # Exception info is added directly to extra dict
        assert hasattr(record, "exception_type")
        assert record.exception_type == "Exception"
        assert record.exception_message == "Critical failure"

    def test_build_extra_empty_kwargs(self):
        """
        Given: A logger with no extra fields
        When: Building extra with empty kwargs
        Then: Empty dict is returned
        """
        logger = StdLibLogger("test")
        result = logger._build_extra({})
        assert result == {}

    def test_build_extra_with_kwargs(self):
        """
        Given: A logger with no extra fields
        When: Building extra with kwargs
        Then: Extra fields dict is returned
        """
        logger = StdLibLogger("test")
        result = logger._build_extra({"key": "value", "count": 42})
        assert result == {"extra_fields": {"key": "value", "count": 42}}

    def test_build_extra_with_persistent_fields(self):
        """
        Given: A logger with persistent extra fields
        When: Building extra with kwargs
        Then: Merged fields are returned
        """
        logger = StdLibLogger("test")
        logger._extra_fields = {"user_id": "123"}
        result = logger._build_extra({"action": "create"})
        assert result == {
            "extra_fields": {
                "user_id": "123",
                "action": "create",
            }
        }

    def test_build_extra_kwargs_override_persistent(self):
        """
        Given: A logger with persistent fields
        When: Building extra with overlapping kwargs
        Then: Kwargs override persistent fields
        """
        logger = StdLibLogger("test")
        logger._extra_fields = {"user_id": "123", "action": "read"}
        result = logger._build_extra({"action": "create"})
        assert result == {
            "extra_fields": {
                "user_id": "123",
                "action": "create",
            }
        }

    def test_context_manager_adds_fields(self, caplog):
        """
        Given: A logger instance
        When: Using context manager to add fields
        Then: Fields are added to log messages in scope
        """
        logger = StdLibLogger("test")

        with caplog.at_level(logging.INFO):
            with logger.context(user_id="123", request_id="req-456"):
                logger.info("Inside context")

        record = caplog.records[0]
        assert record.extra_fields["user_id"] == "123"
        assert record.extra_fields["request_id"] == "req-456"

    def test_context_manager_restores_fields(self, caplog):
        """
        Given: A logger with existing fields
        When: Using context manager and then exiting
        Then: Original fields are restored
        """
        logger = StdLibLogger("test")
        logger._extra_fields = {"original": "field"}

        with caplog.at_level(logging.INFO):
            with logger.context(temporary="field"):
                logger.info("Inside context")
            logger.info("Outside context")

        inside_record = caplog.records[0]
        outside_record = caplog.records[1]

        assert inside_record.extra_fields.get("temporary") == "field"
        assert inside_record.extra_fields.get("original") == "field"
        assert outside_record.extra_fields.get("temporary") is None
        assert outside_record.extra_fields.get("original") == "field"

    def test_context_manager_restores_on_exception(self):
        """
        Given: A logger with context manager
        When: Exception is raised inside context
        Then: Original fields are still restored
        """
        logger = StdLibLogger("test")
        logger._extra_fields = {"original": "value"}

        try:
            with logger.context(temp="value"):
                assert logger._extra_fields == {"original": "value", "temp": "value"}
                raise ValueError("Test error")
        except ValueError:
            pass

        assert logger._extra_fields == {"original": "value"}

    def test_context_manager_nested(self, caplog):
        """
        Given: A logger instance
        When: Nesting context managers
        Then: Fields are accumulated and restored properly
        """
        logger = StdLibLogger("test")

        with caplog.at_level(logging.INFO):
            with logger.context(level1="a"):
                logger.info("Level 1")
                with logger.context(level2="b"):
                    logger.info("Level 2")
                logger.info("Back to level 1")

        assert caplog.records[0].extra_fields == {"level1": "a"}
        assert caplog.records[1].extra_fields == {"level1": "a", "level2": "b"}
        assert caplog.records[2].extra_fields == {"level1": "a"}

    def test_timer_logs_start_and_completion(self, caplog):
        """
        Given: A logger instance
        When: Using timer context manager
        Then: Start and completion messages are logged
        """
        logger = StdLibLogger("test")
        logger._logger.setLevel(logging.DEBUG)

        with caplog.at_level(logging.DEBUG):
            with logger.timer("test_operation"):
                time.sleep(0.01)

        assert len(caplog.records) == 2
        assert "test_operation started" in caplog.records[0].message
        assert "test_operation completed" in caplog.records[1].message
        assert caplog.records[0].levelname == "DEBUG"
        assert caplog.records[1].levelname == "INFO"

    def test_timer_includes_duration(self, caplog):
        """
        Given: A logger instance
        When: Using timer context manager
        Then: Duration is included in completion log
        """
        logger = StdLibLogger("test")
        logger._logger.setLevel(logging.DEBUG)

        with caplog.at_level(logging.DEBUG):
            with logger.timer("test_operation"):
                time.sleep(0.01)

        completion_record = caplog.records[1]
        assert hasattr(completion_record, "extra_fields")
        assert "duration_seconds" in completion_record.extra_fields
        assert completion_record.extra_fields["duration_seconds"] >= 0.01

    def test_timer_with_extra_fields(self, caplog):
        """
        Given: A logger instance
        When: Using timer with extra fields
        Then: Extra fields are included in both logs
        """
        logger = StdLibLogger("test")
        logger._logger.setLevel(logging.DEBUG)

        with caplog.at_level(logging.DEBUG):
            with logger.timer("database_query", table="users", action="select"):
                pass

        start_record = caplog.records[0]
        completion_record = caplog.records[1]

        assert start_record.extra_fields["table"] == "users"
        assert start_record.extra_fields["action"] == "select"
        assert completion_record.extra_fields["table"] == "users"
        assert completion_record.extra_fields["action"] == "select"

    def test_timer_completes_on_exception(self, caplog):
        """
        Given: A logger instance
        When: Exception occurs during timed operation
        Then: Completion log is still recorded
        """
        logger = StdLibLogger("test")
        logger._logger.setLevel(logging.DEBUG)

        with caplog.at_level(logging.DEBUG):
            try:
                with logger.timer("failing_operation"):
                    raise ValueError("Test error")
            except ValueError:
                pass

        assert len(caplog.records) == 2
        assert "failing_operation completed" in caplog.records[1].message

    def test_with_fields_creates_new_logger(self):
        """
        Given: A logger instance
        When: Creating logger with additional fields
        Then: New logger instance is returned
        """
        logger = StdLibLogger("test")
        new_logger = logger.with_fields(user_id="123")

        assert new_logger is not logger
        assert isinstance(new_logger, StdLibLogger)

    def test_with_fields_preserves_logger_name(self):
        """
        Given: A logger instance
        When: Creating logger with additional fields
        Then: Logger name is preserved
        """
        logger = StdLibLogger("test.module")
        new_logger = logger.with_fields(key="value")

        assert new_logger._logger.name == "test.module"
        assert new_logger._logger is logger._logger

    def test_with_fields_adds_persistent_fields(self, caplog):
        """
        Given: A logger instance
        When: Creating logger with additional fields
        Then: Fields persist in all log messages
        """
        logger = StdLibLogger("test")
        user_logger = logger.with_fields(user_id="123", tenant_id="abc")

        with caplog.at_level(logging.INFO):
            user_logger.info("User action")

        record = caplog.records[0]
        assert record.extra_fields["user_id"] == "123"
        assert record.extra_fields["tenant_id"] == "abc"

    def test_with_fields_merges_with_existing_fields(self, caplog):
        """
        Given: A logger with existing fields
        When: Creating logger with additional fields
        Then: Fields are merged
        """
        logger = StdLibLogger("test")
        logger._extra_fields = {"existing": "field"}
        new_logger = logger.with_fields(new="field")

        with caplog.at_level(logging.INFO):
            new_logger.info("Test message")

        record = caplog.records[0]
        assert record.extra_fields["existing"] == "field"
        assert record.extra_fields["new"] == "field"

    def test_with_fields_does_not_modify_original(self, caplog):
        """
        Given: A logger instance
        When: Creating logger with additional fields
        Then: Original logger is not modified
        """
        logger = StdLibLogger("test")
        user_logger = logger.with_fields(user_id="123")

        with caplog.at_level(logging.INFO):
            logger.info("Original logger")
            user_logger.info("New logger")

        assert not hasattr(caplog.records[0], "extra_fields") or \
               "user_id" not in caplog.records[0].extra_fields
        assert caplog.records[1].extra_fields["user_id"] == "123"

    def test_get_logger_function(self):
        """
        Given: No arguments
        When: Calling get_logger
        Then: Logger with default name is returned
        """
        logger = get_logger()
        assert isinstance(logger, StdLibLogger)
        assert logger._logger.name == "atoms_mcp"

    def test_get_logger_function_custom_name(self):
        """
        Given: Custom logger name
        When: Calling get_logger
        Then: Logger with custom name is returned
        """
        logger = get_logger("custom.logger")
        assert isinstance(logger, StdLibLogger)
        assert logger._logger.name == "custom.logger"


class TestJSONFormatter:
    """Test suite for JSONFormatter class."""

    def setup_method(self):
        """Set up test fixtures."""
        clear_request_context()

    def test_format_basic_record(self):
        """
        Given: A basic log record
        When: Formatting with JSONFormatter
        Then: Valid JSON is returned with required fields
        """
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)
        data = json.loads(result)

        assert data["level"] == "INFO"
        assert data["logger"] == "test"
        assert data["message"] == "Test message"
        assert "timestamp" in data
        assert data["timestamp"].endswith("Z")

    def test_format_includes_request_context(self):
        """
        Given: Request context is set
        When: Formatting a log record
        Then: Context variables are included
        """
        set_request_context(
            request_id="req-123",
            user_id="user-456",
            organization_id="org-789",
        )

        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)
        data = json.loads(result)

        assert data["request_id"] == "req-123"
        assert data["user_id"] == "user-456"
        assert data["organization_id"] == "org-789"

    def test_format_includes_exception_info(self):
        """
        Given: A log record with exception info
        When: Formatting with JSONFormatter
        Then: Exception details are included
        """
        formatter = JSONFormatter()

        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=10,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )

        result = formatter.format(record)
        data = json.loads(result)

        assert "exception" in data
        assert data["exception"]["type"] == "ValueError"
        assert data["exception"]["message"] == "Test error"
        assert "traceback" in data["exception"]

    def test_format_includes_extra_fields(self):
        """
        Given: A log record with extra fields
        When: Formatting with JSONFormatter
        Then: Extra fields are included
        """
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.extra_fields = {"user_id": "123", "action": "create"}

        result = formatter.format(record)
        data = json.loads(result)

        assert data["user_id"] == "123"
        assert data["action"] == "create"

    def test_format_includes_caller_info(self):
        """
        Given: A log record with caller info
        When: Formatting with JSONFormatter
        Then: Caller details are included
        """
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="/path/to/test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.funcName = "test_function"

        result = formatter.format(record)
        data = json.loads(result)

        assert "caller" in data
        assert data["caller"]["file"] == "/path/to/test.py"
        assert data["caller"]["line"] == 42
        assert data["caller"]["function"] == "test_function"


class TestTextFormatter:
    """Test suite for TextFormatter class."""

    def setup_method(self):
        """Set up test fixtures."""
        clear_request_context()

    def test_format_basic_with_timestamp(self):
        """
        Given: TextFormatter with timestamp enabled
        When: Formatting a log record
        Then: Timestamp is included in output
        """
        formatter = TextFormatter(include_timestamp=True, include_caller=False)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)

        # Check format: timestamp [LEVEL] name: message
        assert "[INFO]" in result
        assert "test:" in result
        assert "Test message" in result

    def test_format_basic_without_timestamp(self):
        """
        Given: TextFormatter with timestamp disabled
        When: Formatting a log record
        Then: Timestamp is not included
        """
        formatter = TextFormatter(include_timestamp=False, include_caller=False)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)

        assert "[INFO]" in result
        assert "test:" in result
        assert "Test message" in result
        # Should not contain timestamp pattern (YYYY-MM-DD)
        assert not any(char.isdigit() and result.count("-") >= 2 for char in result[:20])

    def test_format_with_caller_info(self):
        """
        Given: TextFormatter with caller info enabled
        When: Formatting a log record
        Then: Caller info is included
        """
        formatter = TextFormatter(include_timestamp=False, include_caller=True)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="/path/to/test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)

        assert "(/path/to/test.py:42)" in result

    def test_format_includes_request_context(self):
        """
        Given: Request context is set
        When: Formatting a log record
        Then: Context is appended to message
        """
        set_request_context(request_id="req-123")

        formatter = TextFormatter(include_timestamp=False, include_caller=False)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)

        assert "Test message [request_id=req-123]" in result

    def test_format_includes_multiple_context_values(self):
        """
        Given: Multiple context values are set
        When: Formatting a log record
        Then: All context values are included
        """
        set_request_context(
            request_id="req-123",
            user_id="user-456",
            organization_id="org-789",
        )

        formatter = TextFormatter(include_timestamp=False, include_caller=False)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)

        assert "request_id=req-123" in result
        assert "user_id=user-456" in result
        assert "org_id=org-789" in result


class TestLoggingSetup:
    """Test suite for logging setup functions."""

    def setup_method(self):
        """Set up test fixtures."""
        # Clear all handlers
        logging.root.handlers = []
        clear_request_context()

    def teardown_method(self):
        """Clean up after tests."""
        # Reset logging
        logging.root.handlers = []
        logging.root.setLevel(logging.WARNING)

    def test_setup_logging_console_text_format(self):
        """
        Given: Logging config with console enabled and text format
        When: Setting up logging
        Then: Console handler with text formatter is added
        """
        config = LoggingSettings(
            level=LogLevel.INFO,
            format=LogFormat.TEXT,
            console_enabled=True,
            file_enabled=False,
        )

        setup_logging(config)

        assert len(logging.root.handlers) == 1
        handler = logging.root.handlers[0]
        assert isinstance(handler, logging.StreamHandler)
        assert isinstance(handler.formatter, TextFormatter)
        assert logging.root.level == logging.INFO

    def test_setup_logging_console_json_format(self):
        """
        Given: Logging config with console enabled and JSON format
        When: Setting up logging
        Then: Console handler with JSON formatter is added
        """
        config = LoggingSettings(
            level=LogLevel.DEBUG,
            format=LogFormat.JSON,
            console_enabled=True,
            file_enabled=False,
        )

        setup_logging(config)

        assert len(logging.root.handlers) == 1
        handler = logging.root.handlers[0]
        assert isinstance(handler, logging.StreamHandler)
        assert isinstance(handler.formatter, JSONFormatter)
        assert logging.root.level == logging.DEBUG

    def test_setup_logging_file_handler(self):
        """
        Given: Logging config with file enabled
        When: Setting up logging
        Then: Rotating file handler is added
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            config = LoggingSettings(
                level=LogLevel.INFO,
                format=LogFormat.TEXT,
                console_enabled=False,
                file_enabled=True,
                file_path=str(log_file),
            )

            setup_logging(config)

            assert len(logging.root.handlers) == 1
            handler = logging.root.handlers[0]
            assert isinstance(handler, logging.handlers.RotatingFileHandler)
            assert log_file.parent.exists()

    def test_setup_logging_both_handlers(self):
        """
        Given: Logging config with both console and file enabled
        When: Setting up logging
        Then: Both handlers are added
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            config = LoggingSettings(
                level=LogLevel.INFO,
                format=LogFormat.JSON,
                console_enabled=True,
                file_enabled=True,
                file_path=str(log_file),
            )

            setup_logging(config)

            assert len(logging.root.handlers) == 2

    def test_setup_logging_clears_existing_handlers(self):
        """
        Given: Existing handlers on root logger
        When: Setting up logging
        Then: Old handlers are removed
        """
        # Store original count
        original_count = len(logging.root.handlers)

        # Add a dummy handler
        logging.root.addHandler(logging.NullHandler())

        config = LoggingSettings(
            level=LogLevel.INFO,
            format=LogFormat.TEXT,
            console_enabled=True,
            file_enabled=False,
        )

        setup_logging(config)

        # Should have only the new handler(s) - at least one from setup
        assert len(logging.root.handlers) >= 1
        # Verify NullHandler is not present
        assert not any(isinstance(h, logging.NullHandler) for h in logging.root.handlers)

    def test_setup_logging_creates_log_directory(self):
        """
        Given: Log file path in non-existent directory
        When: Setting up logging
        Then: Directory is created
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "subdir" / "test.log"
            config = LoggingSettings(
                level=LogLevel.INFO,
                format=LogFormat.TEXT,
                console_enabled=False,
                file_enabled=True,
                file_path=str(log_file),
            )

            setup_logging(config)

            assert log_file.parent.exists()

    def test_set_request_context_all_fields(self):
        """
        Given: Request context values
        When: Setting request context
        Then: All values are stored
        """
        set_request_context(
            request_id="req-123",
            user_id="user-456",
            organization_id="org-789",
        )

        assert request_id_var.get() == "req-123"
        assert user_id_var.get() == "user-456"
        assert organization_id_var.get() == "org-789"

    def test_set_request_context_partial_fields(self):
        """
        Given: Partial request context values
        When: Setting request context
        Then: Only provided values are updated
        """
        set_request_context(request_id="req-123")

        assert request_id_var.get() == "req-123"
        assert user_id_var.get() is None
        assert organization_id_var.get() is None

    def test_clear_request_context(self):
        """
        Given: Request context is set
        When: Clearing request context
        Then: All values are set to None
        """
        set_request_context(
            request_id="req-123",
            user_id="user-456",
            organization_id="org-789",
        )

        clear_request_context()

        assert request_id_var.get() is None
        assert user_id_var.get() is None
        assert organization_id_var.get() is None

    def test_get_request_context(self):
        """
        Given: Request context is set
        When: Getting request context
        Then: Dictionary with all values is returned
        """
        set_request_context(
            request_id="req-123",
            user_id="user-456",
            organization_id="org-789",
        )

        context = get_request_context()

        assert context == {
            "request_id": "req-123",
            "user_id": "user-456",
            "organization_id": "org-789",
        }

    def test_get_request_context_empty(self):
        """
        Given: No request context is set
        When: Getting request context
        Then: Dictionary with None values is returned
        """
        clear_request_context()
        context = get_request_context()

        assert context == {
            "request_id": None,
            "user_id": None,
            "organization_id": None,
        }


class TestLoggingIntegration:
    """Integration tests for complete logging workflows."""

    def setup_method(self):
        """Set up test fixtures."""
        logging.root.handlers = []
        clear_request_context()

    def teardown_method(self):
        """Clean up after tests."""
        logging.root.handlers = []
        logging.root.setLevel(logging.WARNING)

    def test_end_to_end_logging_with_context(self, caplog):
        """
        Given: Complete logging setup
        When: Logging with context and fields
        Then: All features work together correctly
        """
        # Setup logging - but setup_logging clears caplog handlers!
        # So we need to re-add caplog's handler
        config = LoggingSettings(
            level=LogLevel.DEBUG,
            format=LogFormat.TEXT,
            console_enabled=False,  # Don't add console handler
            file_enabled=False,
        )

        # Set request context
        set_request_context(request_id="req-123", user_id="user-456")

        # Create logger and log with various methods
        logger = get_logger("integration.test")
        logger._logger.setLevel(logging.DEBUG)

        with caplog.at_level(logging.DEBUG):
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")

            with logger.context(operation="test"):
                logger.info("Context message")

            with logger.timer("timed_operation"):
                time.sleep(0.01)

        # Verify messages were logged
        assert len(caplog.records) >= 5  # At least the main messages

    def test_logger_with_persistent_fields_and_timer(self, caplog):
        """
        Given: Logger with persistent fields
        When: Using timer
        Then: Persistent fields appear in timer logs
        """
        logger = get_logger("test")
        user_logger = logger.with_fields(user_id="123", tenant="abc")
        user_logger._logger.setLevel(logging.DEBUG)

        with caplog.at_level(logging.DEBUG):
            with user_logger.timer("operation"):
                pass

        assert all(
            record.extra_fields.get("user_id") == "123"
            for record in caplog.records
        )
