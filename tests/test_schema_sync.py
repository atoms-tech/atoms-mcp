"""
Tests for Schema Synchronization System

These tests validate the schema sync tool's ability to:
- Query database schema
- Compare with local schemas
- Detect drift
- Generate update code
"""

import sys
from pathlib import Path
from typing import Any

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.sync_schema import SchemaSync


class TestSchemaSync:
    """Test suite for SchemaSync class."""

    @pytest.fixture
    def sync(self):
        """Create a SchemaSync instance for testing."""
        return SchemaSync(project_id="test-project")

    @pytest.fixture
    def mock_db_schema(self) -> dict[str, Any]:
        """Mock database schema."""
        return {
            "tables": {
                "organizations": {
                    "columns": [
                        {"column_name": "id", "data_type": "uuid", "is_nullable": "NO"},
                        {"column_name": "name", "data_type": "text", "is_nullable": "NO"},
                        {"column_name": "type", "data_type": "USER-DEFINED", "is_nullable": "NO", "udt_name": "organization_type"},
                        {"column_name": "new_field", "data_type": "text", "is_nullable": "YES"},
                    ]
                },
                "new_table": {
                    "columns": [
                        {"column_name": "id", "data_type": "uuid", "is_nullable": "NO"},
                        {"column_name": "value", "data_type": "text", "is_nullable": "YES"},
                    ]
                }
            },
            "enums": {
                "organization_type": ["personal", "team", "enterprise", "nonprofit"],
                "new_enum": ["value1", "value2"],
            }
        }

    @pytest.fixture
    def mock_local_schema(self) -> dict[str, Any]:
        """Mock local schema."""
        return {
            "tables": {
                "organizations": {
                    "columns": [
                        {"column_name": "id", "python_type": "str"},
                        {"column_name": "name", "python_type": "str"},
                        {"column_name": "type", "python_type": "str"},
                    ]
                },
            },
            "enums": {
                "organization_type": ["personal", "team", "enterprise"],
            }
        }

    def test_convert_class_to_enum_name(self, sync):
        """Test converting Python class names to database enum names."""
        assert sync._convert_class_to_enum_name("OrganizationType") == "organization_type"
        assert sync._convert_class_to_enum_name("ProjectStatus") == "project_status"
        assert sync._convert_class_to_enum_name("UserRole") == "user_role_type"

    def test_convert_class_to_table_name(self, sync):
        """Test converting Python class names to database table names."""
        assert sync._convert_class_to_table_name("OrganizationRow") == "organizations"
        assert sync._convert_class_to_table_name("ProjectRow") == "projects"
        assert sync._convert_class_to_table_name("PropertyRow") == "properties"

    def test_enum_name_to_class(self, sync):
        """Test converting database enum names to Python class names."""
        assert sync._enum_name_to_class("organization_type") == "OrganizationType"
        assert sync._enum_name_to_class("project_status") == "ProjectStatus"
        assert sync._enum_name_to_class("billing_plan") == "BillingPlanType"

    def test_table_name_to_class(self, sync):
        """Test converting database table names to Python class names."""
        assert sync._table_name_to_class("organizations") == "OrganizationRow"
        assert sync._table_name_to_class("projects") == "ProjectRow"
        assert sync._table_name_to_class("properties") == "PropertyRow"

    def test_sql_to_python_type(self, sync):
        """Test SQL to Python type conversion."""
        # UUID
        assert sync._sql_to_python_type({"data_type": "uuid", "is_nullable": "NO"}) == "str"
        assert sync._sql_to_python_type({"data_type": "uuid", "is_nullable": "YES"}) == "Optional[str]"

        # Text
        assert sync._sql_to_python_type({"data_type": "text", "is_nullable": "NO"}) == "str"

        # Integer
        assert sync._sql_to_python_type({"data_type": "integer", "is_nullable": "NO"}) == "int"

        # Boolean
        assert sync._sql_to_python_type({"data_type": "boolean", "is_nullable": "YES"}) == "Optional[bool]"

        # JSONB
        assert sync._sql_to_python_type({"data_type": "jsonb", "is_nullable": "NO"}) == "dict"

        # Timestamp
        assert sync._sql_to_python_type({"data_type": "timestamp with time zone", "is_nullable": "NO"}) == "str"

    def test_detect_new_enum(self, sync, mock_db_schema, mock_local_schema):
        """Test detection of new enum in database."""
        sync.db_schema = mock_db_schema
        sync.local_schema = mock_local_schema
        differences = sync.compare_schemas()

        new_enums = [d for d in differences if d["type"] == "enum" and d["change"] == "added"]
        assert len(new_enums) == 1
        assert new_enums[0]["name"] == "new_enum"
        assert new_enums[0]["severity"] == "high"

    def test_detect_modified_enum(self, sync, mock_db_schema, mock_local_schema):
        """Test detection of modified enum."""
        sync.db_schema = mock_db_schema
        sync.local_schema = mock_local_schema
        differences = sync.compare_schemas()

        modified_enums = [d for d in differences if d["type"] == "enum" and d["change"] == "modified"]
        assert len(modified_enums) == 1
        assert modified_enums[0]["name"] == "organization_type"
        assert "nonprofit" in modified_enums[0]["added_values"]

    def test_detect_new_table(self, sync, mock_db_schema, mock_local_schema):
        """Test detection of new table in database."""
        sync.db_schema = mock_db_schema
        sync.local_schema = mock_local_schema
        differences = sync.compare_schemas()

        new_tables = [d for d in differences if d["type"] == "table" and d["change"] == "added"]
        assert len(new_tables) == 1
        assert new_tables[0]["name"] == "new_table"
        assert len(new_tables[0]["columns"]) == 2

    def test_detect_modified_table(self, sync, mock_db_schema, mock_local_schema):
        """Test detection of modified table (new columns)."""
        sync.db_schema = mock_db_schema
        sync.local_schema = mock_local_schema
        differences = sync.compare_schemas()

        modified_tables = [d for d in differences if d["type"] == "table" and d["change"] == "modified"]
        assert len(modified_tables) == 1
        assert modified_tables[0]["name"] == "organizations"
        assert "new_field" in modified_tables[0]["added_columns"]

    def test_generate_enum_code(self, sync):
        """Test enum code generation."""
        code = sync.generate_enum_code("test_status", ["active", "inactive", "pending"])

        assert "class TestStatusType(str, Enum):" in code
        assert 'ACTIVE = "active"' in code
        assert 'INACTIVE = "inactive"' in code
        assert 'PENDING = "pending"' in code

        # Validate Python syntax
        compile(code, "<string>", "exec")

    def test_generate_table_row_code(self, sync):
        """Test table row code generation."""
        columns = [
            {"column_name": "id", "data_type": "uuid", "is_nullable": "NO"},
            {"column_name": "name", "data_type": "text", "is_nullable": "NO"},
            {"column_name": "count", "data_type": "integer", "is_nullable": "YES"},
        ]

        code = sync.generate_table_row_code("test_items", columns)

        assert "class TestItemRow(TypedDict, total=False):" in code
        assert "id: str" in code
        assert "name: str" in code
        assert "count: Optional[int]" in code

        # Validate Python syntax (with necessary imports)
        full_code = """
from typing import TypedDict, Optional

""" + code
        compile(full_code, "<string>", "exec")

    def test_calculate_schema_hash(self, sync):
        """Test schema hash calculation."""
        schema1 = {"tables": {"test": {}}, "enums": {}}
        schema2 = {"tables": {"test": {}}, "enums": {}}
        schema3 = {"tables": {"other": {}}, "enums": {}}

        hash1 = sync.calculate_schema_hash(schema1)
        hash2 = sync.calculate_schema_hash(schema2)
        hash3 = sync.calculate_schema_hash(schema3)

        # Same schema should produce same hash
        assert hash1 == hash2

        # Different schema should produce different hash
        assert hash1 != hash3

        # Hash should be SHA256 (64 hex chars)
        assert len(hash1) == 64
        assert all(c in "0123456789abcdef" for c in hash1)

    def test_no_drift_detection(self, sync):
        """Test when schemas are in sync."""
        identical_schema = {
            "tables": {
                "organizations": {
                    "columns": [
                        {"column_name": "id", "data_type": "uuid", "is_nullable": "NO"},
                    ]
                }
            },
            "enums": {
                "status": ["active", "inactive"]
            }
        }

        sync.db_schema = identical_schema
        sync.local_schema = {
            "tables": {
                "organizations": {
                    "columns": [
                        {"column_name": "id", "python_type": "str"},
                    ]
                }
            },
            "enums": {
                "status": ["active", "inactive"]
            }
        }

        differences = sync.compare_schemas()

        # Should only detect table column changes (due to different representations)
        # Enums should be identical
        enum_diffs = [d for d in differences if d["type"] == "enum"]
        assert len(enum_diffs) == 0

    def test_severity_levels(self, sync, mock_db_schema, mock_local_schema):
        """Test severity assignment for different changes."""
        sync.db_schema = mock_db_schema
        sync.local_schema = mock_local_schema
        differences = sync.compare_schemas()

        # New enum should be high severity
        new_enum = next(d for d in differences if d["type"] == "enum" and d["change"] == "added")
        assert new_enum["severity"] == "high"

        # Modified enum (added values) should be medium severity
        modified_enum = next(d for d in differences if d["type"] == "enum" and d["change"] == "modified")
        assert modified_enum["severity"] in ["medium", "high"]

        # New table should be high severity
        new_table = next(d for d in differences if d["type"] == "table" and d["change"] == "added")
        assert new_table["severity"] == "high"


class TestSchemaVersionTracking:
    """Test schema version tracking functionality."""

    def test_version_file_format(self):
        """Test that schema_version.py has correct format."""
        from schemas import schema_version

        # Should have required attributes
        assert hasattr(schema_version, "SCHEMA_VERSION")
        assert hasattr(schema_version, "LAST_SYNC")
        assert hasattr(schema_version, "DB_HASH")
        assert hasattr(schema_version, "TABLES_COUNT")
        assert hasattr(schema_version, "ENUMS_COUNT")
        assert hasattr(schema_version, "LAST_SYNC_DIFFERENCES")

        # Types should be correct
        assert isinstance(schema_version.SCHEMA_VERSION, str)
        assert isinstance(schema_version.LAST_SYNC, str)
        assert isinstance(schema_version.DB_HASH, str)
        assert isinstance(schema_version.TABLES_COUNT, int)
        assert isinstance(schema_version.ENUMS_COUNT, int)
        assert isinstance(schema_version.LAST_SYNC_DIFFERENCES, int)


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_schema(self):
        """Test handling of empty schemas."""
        sync = SchemaSync()
        sync.db_schema = {"tables": {}, "enums": {}}
        sync.local_schema = {"tables": {}, "enums": {}}

        differences = sync.compare_schemas()
        assert len(differences) == 0

    def test_special_table_names(self):
        """Test handling of special table names."""
        sync = SchemaSync()

        # Test pluralization edge cases
        assert sync._table_name_to_class("properties") == "PropertyRow"
        assert sync._table_name_to_class("entries") == "EntryRow"
        assert sync._table_name_to_class("analyses") == "AnalysisRow"

    def test_special_enum_names(self):
        """Test handling of special enum names."""
        sync = SchemaSync()

        # Test various enum name formats
        assert sync._convert_class_to_enum_name("OrganizationType") == "organization_type"
        assert sync._convert_class_to_enum_name("UserRoleType") == "user_role_type"
        assert sync._convert_class_to_enum_name("ProjectStatus") == "project_status"

    def test_complex_types(self):
        """Test handling of complex SQL types."""
        sync = SchemaSync()

        # Array types
        array_col = {"data_type": "array", "udt_name": "text", "is_nullable": "NO"}
        assert sync._sql_to_python_type(array_col) == "list[str]"

        # User-defined types (enums)
        enum_col = {"data_type": "USER-DEFINED", "udt_name": "status_enum", "is_nullable": "NO"}
        assert sync._sql_to_python_type(enum_col) == "str"

        # Interval
        interval_col = {"data_type": "interval", "is_nullable": "YES"}
        assert sync._sql_to_python_type(interval_col) == "Optional[str]"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
