"""Test server modules for 100% coverage."""

from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Import server components
from server.auth import BearerToken, RateLimiter, RateLimitExceeded, extract_bearer_token
from server.core import ServerConfig
from server.env import EnvConfig, get_env_var, get_fastmcp_vars, load_env_files
from server.errors import ApiError, create_api_error_internal, normalize_error
from server.serializers import Serializable, SerializerConfig, serialize_to_markdown
from server.tools import (
    register_entity_tool,
    register_query_tool,
    register_relationship_tool,
    register_workflow_tool,
    register_workspace_tool,
)


class TestAuthentication:
    """Test authentication and rate limiting."""

    def test_rate_limiter_creation(self):
        """Test rate limiter creation."""
        limiter = RateLimiter(max_requests=100, window_seconds=3600, cleanup_interval=300)

        assert limiter.max_requests == 100
        assert limiter.window_seconds == 3600
        assert limiter.cleanup_interval == 300

    def test_rate_limiter_basic_functionality(self):
        """Test basic rate limiting functionality."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)

        user_id = "test-user"

        # Should allow requests within limit
        for _ in range(5):
            result = limiter.is_allowed(user_id)
            assert result is True

        # Should deny requests over limit
        result = limiter.is_allowed(user_id)
        assert result is False

    def test_rate_limiter_with_retry_after(self):
        """Test rate limiter with retry-after calculation."""
        limiter = RateLimiter(max_requests=2, window_seconds=10)
        user_id = "test-user"

        # Exhaust limit
        limiter.is_allowed(user_id)
        limiter.is_allowed(user_id)

        # Should be limited with retry-after
        allowed, retry_after = limiter.is_allowed_with_retry_after(user_id)
        assert allowed is False
        assert retry_after > 0
        assert retry_after <= 10

    def test_rate_limiter_cleanup(self):
        """Test rate limiter cleanup of old entries."""
        limiter = RateLimiter(max_requests=5, window_seconds=1, cleanup_interval=0.1)

        user_id = "test-user"

        # Exhaust limit
        for _ in range(5):
            limiter.is_allowed(user_id)

        # Wait for window to expire
        import time

        time.sleep(1.5)

        # Cleanup should remove old entries
        limiter.cleanup()

        # Should allow requests again
        result = limiter.is_allowed(user_id)
        assert result is True

    def test_rate_limit_exceeded(self):
        """Test rate limit exceeded exception."""
        error = RateLimitExceeded(message="Rate limit exceeded", retry_after=60)

        assert error.message == "Rate limit exceeded"
        assert error.retry_after == 60
        assert error.status_code == 429

    def test_bearer_token(self):
        """Test bearer token creation and methods."""
        token = BearerToken(
            access_token="test-access-token",
            refresh_token="test-refresh-token",
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )

        assert token.access_token == "test-access-token"
        assert token.refresh_token == "test-refresh-token"
        assert isinstance(token.expires_at, datetime)

        # Test is_expired
        assert token.is_expired() is False

        # Test expired token
        expired_token = BearerToken(
            access_token="expired-token",
            refresh_token="expired-refresh",
            expires_at=datetime.now(UTC) - timedelta(hours=1),
        )
        assert expired_token.is_expired() is True

    def test_extract_bearer_token(self):
        """Test bearer token extraction from headers."""
        # Valid bearer token
        auth_header = "Bearer test-access-token"
        token = extract_bearer_token(auth_header)
        assert token == "test-access-token"

        # Invalid format
        assert extract_bearer_token("Invalid token") is None
        assert extract_bearer_token("Bearer ") is None
        assert extract_bearer_token(None) is None

    def test_get_remaining(self):
        """Test time remaining calculation."""
        token = BearerToken(
            access_token="test-token", refresh_token="refresh-token", expires_at=datetime.now(UTC) + timedelta(minutes=30)
        )

        remaining = token.get_remaining()
        assert remaining > 0
        assert remaining <= 30 * 60  # 30 minutes in seconds

        # Test expired token
        expired_token = BearerToken(
            access_token="expired-token",
            refresh_token="expired-refresh",
            expires_at=datetime.now(UTC) - timedelta(minutes=5),
        )

        remaining = expired_token.get_remaining()
        assert remaining == 0


class TestEnvironment:
    """Test environment configuration."""

    def test_env_config_creation(self):
        """Test environment configuration creation."""
        config = EnvConfig(database_url="postgresql://test", redis_url="redis://test", jwt_secret="test-secret")

        assert config.database_url == "postgresql://test"
        assert config.redis_url == "redis://test"
        assert config.jwt_secret == "test-secret"

    @pytest.mark.asyncio
    async def test_load_env_files(self):
        """Test loading environment files."""
        # Create temporary env file
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("TEST_VAR=test_value\n")
            f.write("ANOTHER_VAR=another_value\n")
            temp_file = f.name

        try:
            # Load environment
            env_vars = await load_env_files([temp_file])

            assert env_vars["TEST_VAR"] == "test_value"
            assert env_vars["ANOTHER_VAR"] == "another_value"
        finally:
            os.unlink(temp_file)

    def test_get_env_var(self):
        """Test environment variable retrieval."""
        # Set environment variable
        import os

        os.environ["TEST_GET_VAR"] = "test_value"

        try:
            # Should retrieve existing variable
            value = get_env_var("TEST_GET_VAR")
            assert value == "test_value"

            # Should return default for non-existing variable
            value = get_env_var("NON_EXISTENT_VAR", "default_value")
            assert value == "default_value"
        finally:
            os.environ.pop("TEST_GET_VAR", None)

    def test_get_fastmcp_vars(self):
        """Test FastMCP environment variables retrieval."""
        # Mock environment variables
        import os

        env_vars = {"FASTMCP_HOST": "localhost", "FASTMCP_PORT": "50002", "FASTMCP_LOG_LEVEL": "INFO"}

        for key, value in env_vars.items():
            os.environ[key] = value

        try:
            fastmcp_vars = get_fastmcp_vars()

            assert fastmcp_vars["host"] == "localhost"
            assert fastmcp_vars["port"] == "50002"
            assert fastmcp_vars["log_level"] == "INFO"
        finally:
            for key in env_vars:
                os.environ.pop(key, None)

    def test_temporary_env(self):
        """Test temporary environment context manager."""
        import os

        original_value = os.environ.get("TEST_TEMP_VAR", "original")

        # Use temporary environment
        with temporary_env(TEST_TEMP_VAR="temporary_value") as env:
            assert os.environ["TEST_TEMP_VAR"] == "temporary_value"
            assert env["TEST_TEMP_VAR"] == "temporary_value"

        # Should restore original value
        assert os.environ.get("TEST_TEMP_VAR", "original") == original_value


class TestSerializers:
    """Test serialization components."""

    def test_serializer_config(self):
        """Test serializer configuration."""
        config = SerializerConfig(max_depth=10, max_array_length=100, pretty_print=True)

        assert config.max_depth == 10
        assert config.max_array_length == 100
        assert config.pretty_print is True

    def test_serializable_mixin(self):
        """Test serializable mixin functionality."""

        class TestClass(Serializable):
            def __init__(self, name: str, value: int):
                self.name = name
                self.value = value

            def to_dict(self) -> dict[str, Any]:
                return {"name": self.name, "value": self.value}

        obj = TestClass("test", 42)
        obj_dict = obj.to_dict()

        assert obj_dict == {"name": "test", "value": 42}

    def test_serialize_to_markdown(self):
        """Test markdown serialization."""
        data = {
            "string_field": "test string",
            "number_field": 42,
            "boolean_field": True,
            "list_field": ["item1", "item2"],
            "nested_dict": {"inner_key": "inner_value"},
        }

        markdown = serialize_to_markdown(data)

        # Should contain field names and values
        assert "string_field" in markdown
        assert "test string" in markdown
        assert "number_field" in markdown
        assert "42" in markdown
        assert "list_field" in markdown
        assert "nested_dict" in markdown
        assert "inner_value" in markdown

    def test_serialize_nested_objects(self):
        """Test serialization of nested objects."""

        class NestedClass(Serializable):
            def __init__(self, value: str):
                self.value = value

            def to_dict(self) -> dict[str, Any]:
                return {"value": self.value}

        class OuterClass(Serializable):
            def __init__(self, nested: NestedClass):
                self.nested = nested

            def to_dict(self) -> dict[str, Any]:
                return {"nested": self.nested.to_dict()}

        nested = NestedClass("nested_value")
        outer = OuterClass(nested)

        markdown = serialize_to_markdown(outer.to_dict())
        assert "nested_value" in markdown


class TestToolRegistration:
    """Test tool registration functions."""

    def test_register_workspace_tool(self):
        """Test workspace tool registration."""
        mcp_server = Mock()
        workspace_operation = AsyncMock()
        rate_limiter = Mock()

        register_workspace_tool(mcp_server, workspace_operation, rate_limiter)

        # Should call mcp_server.tool
        mcp_server.tool.assert_called_once()

        # Get the registered tool function
        tool_func = mcp_server.tool.call_args[0][0]
        assert callable(tool_func)

        # Check tool metadata
        tool_decorator = mcp_server.tool.call_args[1]
        assert tool_decorator["tags"] == {"workspace", "context"}

    def test_register_entity_tool(self):
        """Test entity tool registration."""
        mcp_server = Mock()
        entity_operation = AsyncMock()
        rate_limiter = Mock()

        register_entity_tool(mcp_server, entity_operation, rate_limiter)

        # Should call mcp_server.tool
        mcp_server.tool.assert_called_once()

        # Check tool metadata
        tool_decorator = mcp_server.tool.call_args[1]
        assert tool_decorator["tags"] == {"entity", "crud"}

    def test_register_relationship_tool(self):
        """Test relationship tool registration."""
        mcp_server = Mock()
        relationship_operation = AsyncMock()
        rate_limiter = Mock()

        register_relationship_tool(mcp_server, relationship_operation, rate_limiter)

        # Check tool metadata
        tool_decorator = mcp_server.tool.call_args[1]
        assert tool_decorator["tags"] == {"relationship", "association"}

    def test_register_workflow_tool(self):
        """Test workflow tool registration."""
        mcp_server = Mock()
        workflow_execute = AsyncMock()
        rate_limiter = Mock()

        register_workflow_tool(mcp_server, workflow_execute, rate_limiter)

        # Check tool metadata
        tool_decorator = mcp_server.tool.call_args[1]
        assert tool_decorator["tags"] == {"workflow", "automation"}

    def test_register_query_tool(self):
        """Test query tool registration."""
        mcp_server = Mock()
        data_query = AsyncMock()
        rate_limiter = Mock()

        register_query_tool(mcp_server, data_query, rate_limiter)

        # Check tool metadata
        tool_decorator = mcp_server.tool.call_args[1]
        assert tool_decorator["tags"] == {"query", "analysis", "rag"}


class TestErrorHandling:
    """Test error handling components."""

    def test_api_error_creation(self):
        """Test API error creation."""
        error = ApiError(message="Test error", status_code=400, error_code="TEST_ERROR", details={"field": "value"})

        assert error.message == "Test error"
        assert error.status_code == 400
        assert error.error_code == "TEST_ERROR"
        assert error.details == {"field": "value"}

    def test_api_error_str_representation(self):
        """Test API error string representation."""
        error = ApiError(message="Test error", status_code=400, error_code="TEST_ERROR")

        error_str = str(error)
        assert "Test error" in error_str
        assert "400" in error_str
        assert "TEST_ERROR" in error_str

    def test_create_api_error_internal(self):
        """Test internal API error creation."""
        error = create_api_error_internal(message="Internal error", details={"stack": "trace"})

        assert error.message == "Internal error"
        assert error.status_code == 500
        assert error.error_code == "INTERNAL_ERROR"
        assert error.details == {"stack": "trace"}

    def test_normalize_error(self):
        """Test error normalization."""
        # API error (should be returned as-is)
        api_error = ApiError("API error", 400, "API_ERROR")
        normalized = normalize_error(api_error)
        assert normalized == api_error

        # Generic exception (should be converted to API error)
        generic_error = Exception("Generic error")
        normalized = normalize_error(generic_error)

        assert isinstance(normalized, ApiError)
        assert normalized.status_code == 500
        assert "Generic error" in normalized.message

        # String error (should be converted to API error)
        string_error = "String error"
        normalized = normalize_error(string_error)

        assert isinstance(normalized, ApiError)
        assert normalized.status_code == 400
        assert normalized.message == "String error"


class TestServerCore:
    """Test server core functionality."""

    def test_server_config_creation(self):
        """Test server configuration creation."""
        config = ServerConfig(
            host="localhost",
            port=50002,
            debug=True,
            log_level="INFO",
            enable_auth=True,
            rate_limiting={"enabled": True, "max_requests": 100, "window_seconds": 3600},
        )

        assert config.host == "localhost"
        assert config.port == 50002
        assert config.debug is True
        assert config.log_level == "INFO"
        assert config.enable_auth is True
        assert config.rate_limiting["enabled"] is True

    @pytest.mark.asyncio
    async def test_server_initialization(self):
        """Test server initialization."""
        config = ServerConfig(host="localhost", port=50003, debug=False, log_level="DEBUG")

        # Mock FastMCP server
        mock_mcp = Mock()

        with patch("fastmcp.FastMCP", return_value=mock_mcp):
            from server.core import create_atoms_server

            server = create_atoms_server(config)

            # Should initialize FastMCP with correct config
            assert server is not None

    def test_tool_registration_integration(self):
        """Test integrated tool registration."""
        mock_mcp = Mock()

        # Mock tool operations
        mock_workspace_op = AsyncMock()
        mock_entity_op = AsyncMock()
        mock_relationship_op = AsyncMock()
        mock_workflow_op = AsyncMock()
        mock_query_op = AsyncMock()

        # Register all tools
        register_workspace_tool(mock_mcp, mock_workspace_op)
        register_entity_tool(mock_mcp, mock_entity_op)
        register_relationship_tool(mock_mcp, mock_relationship_op)
        register_workflow_tool(mock_mcp, mock_workflow_op)
        register_query_tool(mock_mcp, mock_query_op)

        # Should have called tool decorator 5 times
        assert mock_mcp.tool.call_count == 5

        # Check each registration had correct tags
        tool_calls = mock_mcp.tool.call_args_list
        tags_list = [call[1]["tags"] for call in tool_calls]

        expected_tags = [
            {"workspace", "context"},
            {"entity", "crud"},
            {"relationship", "association"},
            {"workflow", "automation"},
            {"query", "analysis", "rag"},
        ]

        for expected in expected_tags:
            assert expected in tags_list


class TestServerIntegration:
    """Test server integration scenarios."""

    @pytest.mark.asyncio
    async def test_authenticated_request_flow(self):
        """Test complete authenticated request flow."""
        # Setup rate limiter
        rate_limiter = RateLimiter(max_requests=10, window_seconds=60)

        # Create bearer token
        token = BearerToken(
            access_token="test-access-token",
            refresh_token="test-refresh-token",
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )

        # Simulate authenticated request
        user_id = "test-user"

        # Check rate limiting
        is_allowed = rate_limiter.is_allowed(user_id)
        assert is_allowed is True

        # Check token is valid
        is_expired = token.is_expired()
        assert is_expired is False

        # Simulate token refresh
        new_token = BearerToken(
            access_token="new-access-token",
            refresh_token="new-refresh-token",
            expires_at=datetime.now(UTC) + timedelta(hours=2),
        )

        assert new_token.access_token != token.access_token
        assert new_token.is_expired() is False

    @pytest.mark.asyncio
    async def test_error_handling_flow(self):
        """Test error handling flow."""
        # Test various error scenarios
        errors = [
            ApiError("Validation error", 400, "VALIDATION_ERROR"),
            Exception("Unexpected error"),
            "String error",
            None,
        ]

        for error in errors:
            try:
                # Normalize error
                normalized = normalize_error(error)

                if normalized:
                    assert isinstance(normalized, ApiError)
                    assert normalized.message is not None
                    assert normalized.status_code is not None

            except Exception as e:
                # Normalization should not raise exceptions
                pytest.fail(f"Error normalization failed: {e}")

    @pytest.mark.asyncio
    async def test_tool_execution_flow(self):
        """Test tool execution flow with rate limiting."""
        # Setup components
        mcp_server = Mock()
        workspace_operation = AsyncMock(return_value={"success": True})
        rate_limiter = RateLimiter(max_requests=5, window_seconds=60)

        # Register workspace tool
        register_workspace_tool(mcp_server, workspace_operation, rate_limiter)

        # Get the registered tool function
        tool_func = mcp_server.tool.call_args[0][0]

        # Execute tool multiple times (within rate limit)
        for _i in range(5):
            try:
                result = await tool_func(operation="get_context", context_type="project", entity_id="proj-123")

                assert result["success"] is True
                workspace_operation.assert_called()

            except Exception as e:
                # Should not fail within rate limit
                pytest.fail(f"Tool execution failed within rate limit: {e}")

        # Next execution should be rate limited
        try:
            await tool_func(operation="get_context", context_type="project", entity_id="proj-123")
            pytest.fail("Expected rate limit exceeded error")
        except RateLimitExceeded as e:
            assert e.status_code == 429
            assert e.retry_after > 0
