"""
Test Framework Validators

Provides validation utilities for test responses and data.
"""

import uuid
from typing import Any


class FieldValidator:
    """Validates individual fields in test responses."""

    @staticmethod
    def validate_required_fields(data: dict[str, Any], required_fields: list[str]) -> list[str]:
        """Validate that all required fields are present in the data.

        Args:
            data: The data to validate
            required_fields: List of required field names

        Returns:
            List of missing field names
        """
        missing_fields = []
        for field in required_fields:
            if field not in data:
                missing_fields.append(field)
        return missing_fields

    @staticmethod
    def validate_field_types(data: dict[str, Any], field_types: dict[str, type]) -> list[str]:
        """Validate that fields have the correct types.

        Args:
            data: The data to validate
            field_types: Dict mapping field names to expected types

        Returns:
            List of fields with incorrect types
        """
        incorrect_types = []
        for field, expected_type in field_types.items():
            if field in data and not isinstance(data[field], expected_type):
                incorrect_types.append(f"{field} (expected {expected_type.__name__}, got {type(data[field]).__name__})")
        return incorrect_types

    @staticmethod
    def is_uuid(value: Any) -> bool:
        """Check if a value is a valid UUID string.

        Args:
            value: The value to check

        Returns:
            True if the value is a valid UUID string
        """
        if not isinstance(value, str):
            return False
        try:
            uuid.UUID(value)
            return True
        except (ValueError, TypeError):
            return False


class ResponseValidator:
    """Validates MCP tool responses."""

    @staticmethod
    def extract_id(response: dict[str, Any]) -> str | None:
        """Extract entity ID from a response.

        Args:
            response: The response data

        Returns:
            Entity ID if found, None otherwise
        """
        if isinstance(response, dict):
            # Try common ID field names
            for id_field in ["id", "entity_id", "document_id", "project_id", "organization_id"]:
                if id_field in response:
                    return str(response[id_field])

            # Try nested data structure
            if "data" in response and isinstance(response["data"], dict):
                for id_field in ["id", "entity_id", "document_id", "project_id", "organization_id"]:
                    if id_field in response["data"]:
                        return str(response["data"][id_field])

        return None

    @staticmethod
    def validate_success_response(response: dict[str, Any]) -> bool:
        """Validate that a response indicates success.

        Args:
            response: The response to validate

        Returns:
            True if response indicates success
        """
        if not isinstance(response, dict):
            return False

        # Check for success field
        if "success" in response:
            return bool(response["success"])

        # Check for error field (absence indicates success)
        if "error" in response:
            return not bool(response["error"])

        # Check for status field
        if "status" in response:
            status = response["status"]
            if isinstance(status, str):
                return status.lower() in ["success", "ok", "completed"]
            if isinstance(status, int):
                return 200 <= status < 300

        # If no explicit success indicators, assume success if no error
        return "error" not in response

    @staticmethod
    def validate_error_response(response: dict[str, Any]) -> bool:
        """Validate that a response indicates an error.

        Args:
            response: The response to validate

        Returns:
            True if response indicates an error
        """
        if not isinstance(response, dict):
            return True  # Non-dict responses are considered errors

        # Check for explicit error indicators
        if response.get("error"):
            return True

        if "success" in response and not response["success"]:
            return True

        if "status" in response:
            status = response["status"]
            if isinstance(status, int):
                return status >= 400
            if isinstance(status, str):
                return status.lower() in ["error", "failed", "failure"]

        return False

    @staticmethod
    def validate_response_structure(response: dict[str, Any], expected_structure: dict[str, Any]) -> list[str]:
        """Validate that response has the expected structure.

        Args:
            response: The response to validate
            expected_structure: Dict describing expected structure

        Returns:
            List of validation errors
        """
        errors = []

        def validate_nested(data: Any, structure: Any, path: str = "") -> None:
            if isinstance(structure, dict):
                if not isinstance(data, dict):
                    errors.append(f"{path}: Expected dict, got {type(data).__name__}")
                    return

                for key, expected_type in structure.items():
                    current_path = f"{path}.{key}" if path else key
                    if key not in data:
                        errors.append(f"{current_path}: Missing required field")
                    else:
                        validate_nested(data[key], expected_type, current_path)
            elif isinstance(structure, type):
                if not isinstance(data, structure):
                    errors.append(f"{path}: Expected {structure.__name__}, got {type(data).__name__}")
            elif isinstance(structure, list) and structure:
                if not isinstance(data, list):
                    errors.append(f"{path}: Expected list, got {type(data).__name__}")
                else:
                    for i, item in enumerate(data):
                        validate_nested(item, structure[0], f"{path}[{i}]")

        validate_nested(response, expected_structure)
        return errors

    @staticmethod
    def has_any_fields(data: dict[str, Any], field_names: list[str]) -> bool:
        """Check if data has any of the specified fields.

        Args:
            data: The data to check
            field_names: List of field names to check for

        Returns:
            True if at least one field exists
        """
        if not isinstance(data, dict):
            return False
        return any(field in data for field in field_names)

    @staticmethod
    def has_fields(data: dict[str, Any], field_names: list[str]) -> bool:
        """Check if data has all of the specified fields.

        Args:
            data: The data to check
            field_names: List of field names to check for

        Returns:
            True if all fields exist
        """
        if not isinstance(data, dict):
            return False
        return all(field in data for field in field_names)

    @staticmethod
    async def create_test_entity(client_adapter, entity_type: str, data_generator_func, **kwargs):
        """Create a test entity using the provided data generator.

        Args:
            client_adapter: The MCP client adapter
            entity_type: Type of entity to create
            data_generator_func: Function to generate test data
            **kwargs: Additional parameters for data generation

        Returns:
            Entity ID if successful, None if failed
        """
        try:
            # Generate test data
            data = data_generator_func(**kwargs)

            # Create the entity
            result = await client_adapter.call_tool(
                "entity_tool", {"entity_type": entity_type, "operation": "create", "data": data}
            )

            if result.get("success"):
                return ResponseValidator.extract_id(result.get("response", {}))
            return None

        except Exception:
            return None


# Backward compatibility aliases
Validator = ResponseValidator
FieldValidator = FieldValidator
