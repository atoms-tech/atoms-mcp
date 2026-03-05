"""
Code generation utilities for schema synchronization.

This module contains methods for generating Python code from database schemas,
including enum classes, table classes, and type conversions.
"""

import re


class CodeGenerator:
    """Handles code generation for schema synchronization."""

    def __init__(self):
        self.enum_overrides = {
            "organization_type": "OrganizationType",
            "billing_plan": "BillingPlan",
            "project_status": "ProjectStatus",
            "user_role": "UserRole",
            "requirement_priority": "RequirementPriority",
            "requirement_status": "RequirementStatus",
            "test_status": "TestStatus",
            "rag_mode": "RAGMode"
        }

        self.table_overrides = {
            "organizations": "Organization",
            "projects": "Project",
            "users": "User",
            "requirements": "Requirement",
            "tests": "Test",
            "workflows": "Workflow",
            "workspaces": "Workspace"
        }

    def _table_name_to_class_base(self, table_name: str) -> str:
        """Convert database table name to Python class base name."""
        if table_name in self.table_overrides:
            return self.table_overrides[table_name]

        # Convert snake_case to PascalCase
        parts = table_name.split("_")
        return "".join(word.capitalize() for word in parts)

    def _enum_name_to_class_name(self, enum_name: str) -> str:
        """Convert database enum name to Python class name."""
        if enum_name in self.enum_overrides:
            return self.enum_overrides[enum_name]

        # Convert snake_case to PascalCase
        parts = enum_name.split("_")
        return "".join(word.capitalize() for word in parts)

    def _convert_class_to_enum_name(self, class_name: str) -> str:
        """Convert Python class name back to database enum name."""
        # Reverse lookup in overrides
        for enum_name, py_class in self.enum_overrides.items():
            if py_class == class_name:
                return enum_name

        # Convert PascalCase to snake_case
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", class_name)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

    def _convert_class_to_table_name(self, class_name: str) -> str:
        """Convert Python class name back to database table name."""
        # Reverse lookup in overrides
        for table_name, py_class in self.table_overrides.items():
            if py_class == class_name:
                return table_name

        # Convert PascalCase to snake_case
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", class_name)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

    def generate_enum_code(self, enum_name: str, values: list[str]) -> str:
        """Generate Python enum class code."""
        class_name = self._enum_name_to_class(enum_name)

        code = f'''
class {class_name}(str, Enum):
    """
    {enum_name} enumeration - Auto-generated from database.

    Database: {enum_name}
    """
'''
        for value in values:
            const_name = value.upper().replace("-", "_").replace(" ", "_")
            code += f'    {const_name} = "{value}"\n'

        return code

    def _enum_name_to_class(self, enum_name: str) -> str:
        """Convert database enum name to Python class name."""
        return self._enum_name_to_class_name(enum_name)

    def generate_table_row_code(self, table_name: str, columns: list[dict]) -> str:
        """Generate Python TypedDict class for table row."""
        class_name = self._table_name_to_class(table_name)

        code = f'''
class {class_name}(TypedDict, total=False):
    """
    {table_name} table row - Auto-generated from database.

    Database: {table_name}
    """
'''
        for col in columns:
            col_name = col["column_name"]
            py_type = self._sql_to_python_type(col)
            nullable = col.get("is_nullable", "YES") == "YES"

            if nullable:
                py_type = f"Optional[{py_type}]"

            code += f"    {col_name}: {py_type}\n"

        return code

    def _table_name_to_class(self, table_name: str) -> str:
        """Convert database table name to Python class name."""
        return self._table_name_to_class_base(table_name)

    def _sql_to_python_type(self, column: dict) -> str:
        """Convert SQL column type to Python type."""
        data_type = column.get("data_type", "").lower()
        udt_name = column.get("udt_name", "").lower()

        # Handle UUID
        if data_type == "uuid" or udt_name == "uuid":
            return "str"

        # Handle text types
        if data_type in ["text", "character varying", "varchar"]:
            return "str"

        # Handle numeric types
        if data_type in ["integer", "bigint", "smallint"]:
            return "int"
        if data_type in ["real", "double precision", "numeric", "decimal"]:
            return "float"

        # Handle boolean
        if data_type == "boolean":
            return "bool"

        # Handle timestamps
        if data_type in ["timestamp with time zone", "timestamp without time zone"]:
            return "datetime"

        # Handle dates
        if data_type == "date":
            return "date"

        # Handle JSON
        if data_type in ["json", "jsonb"]:
            return "dict[str, Any]"

        # Handle arrays
        if data_type.startswith("array") or data_type.endswith("[]"):
            return "list[Any]"

        # Handle user-defined types (enums)
        if data_type == "user-defined" and udt_name:
            return f'"{udt_name}"'

        # Default fallback
        return "str"

    def _singularize_table_name(self, table_name: str) -> str:
        """Return a best-effort singular form for a table."""
        irregulars = {
            "analyses": "analysis",
            "diagnoses": "diagnosis",
            "theses": "thesis",
            "crises": "crisis",
            "indices": "index",
            "matrices": "matrix",
        }

        if table_name in irregulars:
            return irregulars[table_name]
        if table_name.endswith("ies"):
            return table_name[:-3] + "y"
        if table_name.endswith("ses"):
            return table_name[:-2]
        if table_name.endswith("s"):
            return table_name[:-1]
        return table_name
