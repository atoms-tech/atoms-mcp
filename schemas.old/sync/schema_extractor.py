"""
Schema extraction utilities for schema synchronization.

This module contains methods for extracting schemas from generated Python files
and converting between different schema formats.
"""

import re
from typing import Any

from schemas.generated.fastapi import schema_public_latest as generated_schema


class SchemaExtractor:
    """Handles schema extraction from generated Python files."""

    def __init__(self):
        self.generated_schema = generated_schema

    def get_local_schema(self) -> dict[str, Any]:
        """Extract schema from generated Python file."""
        local: dict[str, Any] = {"tables": {}, "enums": {}}

        # Extract enums from generated schema
        for name in dir(self.generated_schema):
            if name.startswith("Public") and name.endswith("Enum"):
                obj = getattr(self.generated_schema, name)
                if hasattr(obj, "__members__"):
                    # Convert PublicUserRoleTypeEnum -> user_role_type
                    enum_name = name.replace("Public", "").replace("Enum", "")
                    # Convert CamelCase to snake_case
                    enum_name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", enum_name)
                    enum_name = re.sub("([a-z0-9])([A-Z])", r"\1_\2", enum_name).lower()

                    values = [e.value for e in obj]
                    local["enums"][enum_name] = values

        # Extract tables from generated schema (BaseSchema classes)
        for name in dir(self.generated_schema):
            if name.endswith("BaseSchema"):
                obj = getattr(self.generated_schema, name)
                if hasattr(obj, "model_fields"):
                    # Convert OrganizationBaseSchema -> organizations
                    table_name = name.replace("BaseSchema", "")
                    # Convert CamelCase to snake_case
                    table_name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", table_name)
                    table_name = re.sub("([a-z0-9])([A-Z])", r"\1_\2", table_name).lower()

                    # Pluralize
                    if not table_name.endswith("s"):
                        table_name = table_name[:-1] + "ies" if table_name.endswith("y") else table_name + "s"

                    # Special cases
                    table_name = table_name.replace("test_reqs", "test_req")

                    columns = []
                    for field_name, field_info in obj.model_fields.items():
                        # Handle aliased fields (field_type -> type, field_format -> format)
                        actual_field_name = field_name
                        if hasattr(field_info, "alias") and field_info.alias:
                            actual_field_name = field_info.alias

                        columns.append(
                            {
                                "column_name": actual_field_name,
                                "python_type": str(field_info.annotation),
                            }
                        )

                    local["tables"][table_name] = {"columns": columns}

        return local
