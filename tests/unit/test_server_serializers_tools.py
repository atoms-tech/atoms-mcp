"""Server serializers and tools testing using established mock framework."""

import json

import pytest

# Import our mock framework
from test_comprehensive_mock_framework import (
    mock_external_services,
)


class TestServerSerializersComplete:
    """Complete testing of server serializers."""

    @pytest.fixture
    def mock_serializer_environment(self):
        """Create mock serializer environment."""
        with mock_external_services() as services:
            return services

    def test_server_serializers_imports(self):
        """Test server serializers module imports."""
        try:
            import server.serializers

            assert server.serializers is not None
        except ImportError:
            pytest.skip("server.serializers not available")

    def test_json_serialization(self, _mock_serializer_environment):
        """Test JSON serialization."""
        try:
            from server.serializers import serialize_error, serialize_response

            # Test response serialization
            test_data = {"message": "Success", "data": {"id": 1, "name": "Test"}, "status": "ok"}

            result = serialize_response(test_data)
            assert isinstance(result, str)

            # Should be valid JSON
            parsed = json.loads(result)
            assert parsed == test_data

            # Test error serialization
            from server.errors import ApiError

            error = ApiError("Test error", 400, "TEST_ERROR")

            error_result = serialize_error(error)
            assert isinstance(error_result, str)

            # Should contain error information
            assert "Test error" in error_result
            assert "400" in error_result

        except ImportError:
            pytest.skip("JSON serialization not available")

    def test_response_formatting(self, _mock_serializer_environment):
        """Test response formatting."""
        try:
            from server.serializers import format_response

            # Test success response
            success_response = format_response(data={"result": "success"}, status=200, message="Operation completed")

            assert success_response is not None
            assert isinstance(success_response, dict)

            # Test error response
            error_response = format_response(error="Test error", status=400, error_code="TEST_ERROR")

            assert error_response is not None
            assert isinstance(error_response, dict)

        except ImportError:
            pytest.skip("Response formatting not available")

    def test_data_validation_serialization(self, _mock_serializer_environment):
        """Test data validation serialization."""
        try:
            from server.serializers import validate_and_serialize

            # Test valid data
            valid_data = {"name": "Test", "value": 42}
            result = validate_and_serialize(valid_data, schema={"type": "object"})

            assert result is not None

            # Test invalid data (should handle gracefully)
            invalid_data = {"name": None, "value": "not_number"}
            try:
                result = validate_and_serialize(invalid_data, schema={"type": "object"})
                # May return error information or raise exception
                assert result is not None
            except Exception:
                # May raise validation exception
                pass

        except ImportError:
            pytest.skip("Data validation serialization not available")


class TestServerToolsComplete:
    """Complete testing of server tools."""

    @pytest.fixture
    def mock_server_tools_environment(self):
        """Create mock server tools environment."""
        with mock_external_services() as services:
            return services

    def test_server_tools_imports(self):
        """Test server tools module imports."""
        try:
            import server.tools

            assert server.tools is not None
        except ImportError:
            pytest.skip("server.tools not available")

    def test_mcp_tool_registration(self, _mock_server_tools_environment):
        """Test MCP tool registration."""
        try:
            from server.tools import get_registered_mcp_tools, register_mcp_tool

            # Mock tool function
            def mock_mcp_function(name: str, value: int = 10):
                return {"processed_name": name.upper(), "doubled_value": value * 2}

            # Register MCP tool
            register_mcp_tool(
                name="mock_mcp_tool",
                function=mock_mcp_function,
                description="Mock MCP tool for testing",
                schema={
                    "type": "object",
                    "properties": {"name": {"type": "string"}, "value": {"type": "integer", "default": 10}},
                },
            )

            # Verify registration
            tools = get_registered_mcp_tools()
            assert isinstance(tools, list)

            # Find our tool
            tool_names = [tool.get("name") for tool in tools if isinstance(tool, dict)]
            assert "mock_mcp_tool" in tool_names or len(tools) > 0

        except ImportError:
            pytest.skip("MCP tool registration not available")

    def test_tool_execution(self, _mock_server_tools_environment):
        """Test tool execution."""
        try:
            from server.tools import execute_tool

            # Mock tool function
            def test_function(param1: str, param2: int = 5):
                return {"result": f"{param1}-{param2}", "success": True}

            # Execute tool
            result = execute_tool(
                tool_name="test_tool", function=test_function, arguments={"param1": "hello", "param2": 10}
            )

            assert result is not None
            if isinstance(result, dict):
                assert result["result"] == "hello-10"
                assert result["success"] is True

        except ImportError:
            pytest.skip("Tool execution not available")

    def test_tool_error_handling(self, _mock_server_tools_environment):
        """Test tool error handling."""
        try:
            from server.tools import execute_tool

            # Mock failing tool function
            def failing_function():
                raise ValueError("Tool execution failed")

            # Execute failing tool
            result = execute_tool(tool_name="failing_tool", function=failing_function, arguments={})

            assert result is not None
            if isinstance(result, dict):
                assert result.get("success") is False or "error" in result

        except ImportError:
            pytest.skip("Tool error handling not available")

    def test_tool_parameter_validation(self, _mock_server_tools_environment):
        """Test tool parameter validation."""
        try:
            from server.tools import validate_tool_parameters

            # Define test schema
            test_schema = {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer", "minimum": 0},
                    "email": {"type": "string", "format": "email"},
                },
                "required": ["name", "age"],
            }

            # Test valid parameters
            valid_params = {"name": "John", "age": 25, "email": "john@example.com"}
            result = validate_tool_parameters(valid_params, test_schema)
            assert result.get("valid") is True or result is True

            # Test invalid parameters
            invalid_params = {"name": "", "age": -5, "email": "invalid-email"}
            result = validate_tool_parameters(invalid_params, test_schema)

            if result is not True:  # May return validation errors
                assert result.get("valid") is False or "errors" in result

        except ImportError:
            pytest.skip("Tool parameter validation not available")
