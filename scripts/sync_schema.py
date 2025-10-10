#!/usr/bin/env python3
"""
Schema Synchronization Tool for Atoms MCP

This tool keeps Python schemas in sync with the Supabase database.
It queries the database schema, compares it with local Python schema files,
and can update the local schemas automatically.

Usage:
    python scripts/sync_schema.py --check           # Check for drift
    python scripts/sync_schema.py --update          # Update local schemas
    python scripts/sync_schema.py --diff            # Show detailed diff
    python scripts/sync_schema.py --report          # Generate report
    python scripts/sync_schema.py --project-id <id> # Specify project ID
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Add parent directory to path to import schemas
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables from .env file
from dotenv import load_dotenv

load_dotenv()

# Import from generated schemas (now the source of truth)
from schemas.generated.fastapi import schema_public_latest as generated_schema  # noqa: E402


class Colors:
    """ANSI color codes for terminal output."""
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    END = "\033[0m"


class SchemaSync:
    """Schema synchronization manager."""

    def __init__(self, project_id: str | None = None):
        self.project_id = project_id or os.getenv("SUPABASE_PROJECT_ID")
        self.root_dir = Path(__file__).parent.parent
        self.schemas_dir = self.root_dir / "schemas"
        self.db_schema = {}
        self.local_schema = {}
        self.differences = []

    def get_supabase_schema(self) -> dict[str, Any]:
        """Query Supabase for current database schema via direct psycopg2."""
        try:
            import psycopg2

            # Get database credentials from environment
            db_url = os.getenv("DB_URL")
            if not db_url:
                db_password = os.getenv("SUPABASE_DB_PASSWORD")
                if not db_password:
                    raise ValueError("Neither DB_URL nor SUPABASE_DB_PASSWORD found in environment")
                db_url = f"postgresql://postgres.ydogoylwenufckscqijp:{db_password}@aws-0-us-west-1.pooler.supabase.com:6543/postgres"

            # Connect to database
            conn = psycopg2.connect(db_url)
            cur = conn.cursor()

            # Get all tables from information_schema
            tables_query = """
                SELECT
                    table_name,
                    table_schema
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """

            cur.execute(tables_query)
            tables = cur.fetchall()

            schema = {"tables": {}, "enums": {}}

            # For each table, get columns
            for table_row in tables:
                table_name = table_row[0]

                columns_query = f"""
                    SELECT
                        column_name,
                        data_type,
                        is_nullable,
                        column_default,
                        udt_name
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                    AND table_name = '{table_name}'
                    ORDER BY ordinal_position;
                """

                cur.execute(columns_query)
                columns = cur.fetchall()

                schema["tables"][table_name] = {
                    "columns": [
                        {
                            "column_name": col[0],
                            "data_type": col[1],
                            "is_nullable": col[2],
                            "column_default": col[3],
                            "udt_name": col[4]
                        }
                        for col in columns
                    ]
                }

            # Get all enums
            enums_query = """
                SELECT
                    t.typname as enum_name,
                    array_agg(e.enumlabel ORDER BY e.enumsortorder) as enum_values
                FROM pg_type t
                JOIN pg_enum e ON t.oid = e.enumtypid
                WHERE t.typtype = 'e'
                GROUP BY t.typname
                ORDER BY t.typname;
            """

            cur.execute(enums_query)
            enum_rows = cur.fetchall()

            for enum_row in enum_rows:
                schema["enums"][enum_row[0]] = enum_row[1]

            cur.close()
            conn.close()

            return schema

        except Exception as e:
            print(f"{Colors.RED}Error querying Supabase schema: {e}{Colors.END}")
            print(f"{Colors.YELLOW}Falling back to mock schema for demo{Colors.END}")
            return self._get_mock_schema()

    def _get_mock_schema(self) -> dict[str, Any]:
        """Return a mock schema for demonstration."""
        return {
            "tables": {
                "organizations": {
                    "columns": [
                        {"column_name": "id", "data_type": "uuid", "is_nullable": "NO", "udt_name": "uuid"},
                        {"column_name": "name", "data_type": "text", "is_nullable": "NO", "udt_name": "text"},
                        {"column_name": "type", "data_type": "USER-DEFINED", "is_nullable": "NO", "udt_name": "organization_type"},
                        {"column_name": "billing_plan", "data_type": "USER-DEFINED", "is_nullable": "NO", "udt_name": "billing_plan"},
                    ]
                },
                "projects": {
                    "columns": [
                        {"column_name": "id", "data_type": "uuid", "is_nullable": "NO", "udt_name": "uuid"},
                        {"column_name": "name", "data_type": "text", "is_nullable": "NO", "udt_name": "text"},
                        {"column_name": "status", "data_type": "USER-DEFINED", "is_nullable": "NO", "udt_name": "project_status"},
                    ]
                }
            },
            "enums": {
                "organization_type": ["personal", "team", "enterprise"],
                "billing_plan": ["free", "pro", "enterprise"],
                "project_status": ["active", "archived", "draft", "deleted"],
            }
        }

    def regenerate_schemas(self) -> bool:
        """Regenerate schemas from database using supabase-pydantic."""
        import subprocess

        db_url = os.getenv("DB_URL")
        if not db_url:
            db_password = os.getenv("SUPABASE_DB_PASSWORD")
            if not db_password:
                raise ValueError("Neither DB_URL nor SUPABASE_DB_PASSWORD found in environment")
            db_url = f"postgresql://postgres.ydogoylwenufckscqijp:{db_password}@aws-0-us-west-1.pooler.supabase.com:6543/postgres"

        print(f"{Colors.CYAN}Regenerating schemas from Supabase...{Colors.END}")

        cmd = [
            "sb-pydantic", "gen",
            "--type", "pydantic",
            "--framework", "fastapi",
            "--db-url", db_url,
            "--db-type", "postgres",
            "--dir", str(self.schemas_dir / "generated"),
            "--singular-names",
            "--schema", "public"
        ]

        result = subprocess.run(cmd, check=False, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"{Colors.GREEN}✅ Schemas regenerated successfully!{Colors.END}")
            print(f"{Colors.BLUE}📁 Updated: schemas/generated/fastapi/schema_public_latest.py{Colors.END}")

            # Post-process to add missing enum definitions
            self._add_missing_enums()

            # Post-process to fix enum types for aliased fields
            self._fix_aliased_enum_types()

            # Update version file
            self._update_version_file()
            return True
        print(f"{Colors.RED}❌ Schema generation failed{Colors.END}")
        print(result.stderr)
        return False

    def _add_missing_enums(self):
        """Add enum definitions that sb-pydantic missed."""
        import re

        import psycopg2

        print(f"{Colors.CYAN}Adding missing enum definitions...{Colors.END}")

        # Get all enums from database
        db_url = os.getenv("DB_URL")
        if not db_url:
            db_password = os.getenv("SUPABASE_DB_PASSWORD")
            if not db_password:
                return
            db_url = f"postgresql://postgres.ydogoylwenufckscqijp:{db_password}@aws-0-us-west-1.pooler.supabase.com:6543/postgres"

        conn = psycopg2.connect(db_url)
        cur = conn.cursor()

        # Get all enums
        enums_query = """
            SELECT
                t.typname as enum_name,
                array_agg(e.enumlabel ORDER BY e.enumsortorder) as enum_values
            FROM pg_type t
            JOIN pg_enum e ON t.oid = e.enumtypid
            JOIN pg_namespace n ON t.typnamespace = n.oid
            WHERE t.typtype = 'e' AND n.nspname = 'public'
            GROUP BY t.typname
            ORDER BY t.typname;
        """

        cur.execute(enums_query)
        db_enums = {row[0]: row[1] for row in cur.fetchall()}

        cur.close()
        conn.close()

        # Read generated schema file
        schema_file = self.schemas_dir / "generated" / "fastapi" / "schema_public_latest.py"
        with open(schema_file) as f:
            content = f.read()

        # Find existing enum definitions
        existing_enums = set(re.findall(r"class Public(\w+)Enum\(str, Enum\):", content))

        # Convert to database enum names
        existing_db_enums = set()
        for enum_class in existing_enums:
            # PublicOrganizationTypeEnum -> organization_type
            db_name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", enum_class)
            db_name = re.sub("([a-z0-9])([A-Z])", r"\1_\2", db_name).lower()
            existing_db_enums.add(db_name)

        # Find missing enums
        missing_enums = set(db_enums.keys()) - existing_db_enums

        if not missing_enums:
            print(f"{Colors.GREEN}✓ No missing enums{Colors.END}")
            return

        # Generate enum definitions
        enum_definitions = []
        for enum_name in sorted(missing_enums):
            enum_class_name = self._enum_name_to_class_name(enum_name)
            values = db_enums[enum_name]

            print(f"  Adding {enum_name} -> {enum_class_name}")

            enum_def = f"\n\nclass {enum_class_name}(str, Enum):\n"
            for value in values:
                const_name = value.upper().replace("-", "_").replace(" ", "_").replace(".", "_")
                enum_def += f'    {const_name} = "{value}"\n'

            enum_definitions.append(enum_def)

        # Find the insertion point (after the last enum definition)
        # Look for the last "class Public*Enum" definition
        last_enum_match = None
        for match in re.finditer(r"class Public\w+Enum\(str, Enum\):.*?(?=\n\nclass|\n\n# |$)", content, re.DOTALL):
            last_enum_match = match

        if last_enum_match:
            insertion_point = last_enum_match.end()
            content = content[:insertion_point] + "".join(enum_definitions) + content[insertion_point:]
        else:
            # If no enums found, insert after the imports
            import_end = content.find("# ENUM TYPES")
            if import_end != -1:
                insertion_point = content.find("\n", import_end) + 1
                content = content[:insertion_point] + "".join(enum_definitions) + content[insertion_point:]

        # Write back
        with open(schema_file, "w") as f:
            f.write(content)

        print(f"{Colors.GREEN}✅ Added {len(missing_enums)} missing enum(s){Colors.END}")

    def _fix_aliased_enum_types(self):
        """Fix enum types for aliased fields (type -> field_type, format -> field_format)."""
        import re

        import psycopg2

        print(f"{Colors.CYAN}Fixing aliased enum types...{Colors.END}")

        # Get enum types for aliased columns from database
        db_url = os.getenv("DB_URL")
        if not db_url:
            db_password = os.getenv("SUPABASE_DB_PASSWORD")
            if not db_password:
                return
            db_url = f"postgresql://postgres.ydogoylwenufckscqijp:{db_password}@aws-0-us-west-1.pooler.supabase.com:6543/postgres"

        conn = psycopg2.connect(db_url)
        cur = conn.cursor()

        # Get columns named 'type' or 'format' with their enum types
        query = """
            SELECT
                c.table_name,
                c.column_name,
                c.udt_name
            FROM information_schema.columns c
            WHERE c.table_schema = 'public'
            AND c.column_name IN ('type', 'format')
            AND c.data_type = 'USER-DEFINED'
            ORDER BY c.table_name, c.column_name;
        """

        cur.execute(query)
        aliased_enums = {}
        for row in cur.fetchall():
            table_name, column_name, enum_name = row
            if table_name not in aliased_enums:
                aliased_enums[table_name] = {}
            aliased_enums[table_name][column_name] = enum_name

        cur.close()
        conn.close()

        if not aliased_enums:
            print(f"{Colors.YELLOW}No aliased enum fields found{Colors.END}")
            return

        # Read generated schema file
        schema_file = self.schemas_dir / "generated" / "fastapi" / "schema_public_latest.py"
        with open(schema_file) as f:
            content = f.read()

        # Fix each aliased field
        for table_name, columns in aliased_enums.items():
            for column_name, enum_name in columns.items():
                # Convert table_name to class name (e.g., organizations -> Organization)
                class_name_base = self._table_name_to_class_base(table_name)

                # Convert enum_name to enum class name (e.g., organization_type -> PublicOrganizationTypeEnum)
                enum_class_name = self._enum_name_to_class_name(enum_name)

                print(f"  Fixing {table_name}.{column_name} -> {enum_class_name}")

                # Replace in BaseSchema, Insert, and Update classes
                for suffix in ["BaseSchema", "Insert", "Update"]:
                    class_name = f"{class_name_base}{suffix}"

                    # Pattern to match the class and field definition
                    # We need to find the class definition and then replace the field within it
                    class_pattern = rf'(class {class_name}\([^)]+\):.*?)(field_{column_name}:\s+)(?:Any|str|PublicNotificationTypeEnum|PublicOrganizationTypeEnum|PublicPropertyTypeEnum|PublicRequirementFormatEnum)(\s*(?:\|[^=]+)?)((?:\s*=\s*Field\([^)]*alias="{column_name}"[^)]*\)))'

                    def replace_in_class(match):
                        return match.group(1) + match.group(2) + enum_class_name + match.group(3) + match.group(4)

                    content = re.sub(class_pattern, replace_in_class, content, flags=re.DOTALL)

        # Write back
        with open(schema_file, "w") as f:
            f.write(content)

        print(f"{Colors.GREEN}✅ Fixed aliased enum types{Colors.END}")

    def _table_name_to_class_base(self, table_name: str) -> str:
        """Convert table name to base class name (without suffix)."""
        # organizations -> Organization
        # De-pluralize
        if table_name.endswith("ies"):
            name = table_name[:-3] + "y"
        elif table_name.endswith("ses"):
            name = table_name[:-2]
        elif table_name.endswith("s"):
            name = table_name[:-1]
        else:
            name = table_name

        # Convert to PascalCase
        parts = name.split("_")
        return "".join(word.capitalize() for word in parts)

    def _enum_name_to_class_name(self, enum_name: str) -> str:
        """Convert database enum name to Python enum class name."""
        # organization_type -> PublicOrganizationTypeEnum
        parts = enum_name.split("_")
        class_name = "Public" + "".join(word.capitalize() for word in parts) + "Enum"
        return class_name

    def _update_version_file(self):
        """Update schema version tracking file."""
        version_content = f'''"""
Schema Version Tracking

This file is auto-updated when schemas are regenerated.
"""

SCHEMA_VERSION = "{datetime.now(UTC).strftime('%Y-%m-%d')}"
LAST_REGENERATED = "{datetime.now(UTC).isoformat()}"
SOURCE = "supabase-pydantic generated from database"
'''

        version_file = self.schemas_dir / "schema_version.py"
        version_file.write_text(version_content)
        print(f"{Colors.GREEN}✅ Version file updated{Colors.END}")

    def get_local_schema(self) -> dict[str, Any]:
        """Extract schema from generated Python file."""
        local = {"tables": {}, "enums": {}}

        # Extract enums from generated schema
        for name in dir(generated_schema):
            if name.startswith("Public") and name.endswith("Enum"):
                obj = getattr(generated_schema, name)
                if hasattr(obj, "__members__"):
                    # Convert PublicUserRoleTypeEnum -> user_role_type
                    enum_name = name.replace("Public", "").replace("Enum", "")
                    # Convert CamelCase to snake_case
                    import re
                    enum_name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", enum_name)
                    enum_name = re.sub("([a-z0-9])([A-Z])", r"\1_\2", enum_name).lower()

                    values = [e.value for e in obj]
                    local["enums"][enum_name] = values

        # Extract tables from generated schema (BaseSchema classes)
        for name in dir(generated_schema):
            if name.endswith("BaseSchema"):
                obj = getattr(generated_schema, name)
                if hasattr(obj, "model_fields"):
                    # Convert OrganizationBaseSchema -> organizations
                    table_name = name.replace("BaseSchema", "")
                    # Convert CamelCase to snake_case
                    import re
                    table_name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", table_name)
                    table_name = re.sub("([a-z0-9])([A-Z])", r"\1_\2", table_name).lower()

                    # Pluralize
                    if not table_name.endswith("s"):
                        if table_name.endswith("y"):
                            table_name = table_name[:-1] + "ies"
                        else:
                            table_name = table_name + "s"

                    # Special cases
                    table_name = table_name.replace("test_reqs", "test_req")

                    columns = []
                    for field_name, field_info in obj.model_fields.items():
                        # Handle aliased fields (field_type -> type, field_format -> format)
                        actual_field_name = field_name
                        if hasattr(field_info, "alias") and field_info.alias:
                            actual_field_name = field_info.alias

                        columns.append({
                            "column_name": actual_field_name,
                            "python_type": str(field_info.annotation),
                        })

                    local["tables"][table_name] = {"columns": columns}

        return local

    def _convert_class_to_enum_name(self, class_name: str) -> str:
        """Convert Python class name to database enum name."""
        # OrganizationType -> organization_type
        name = class_name.replace("Type", "").replace("Status", "").replace("Enum", "")
        # Convert camelCase to snake_case
        import re
        name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        name = re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()

        # Handle special cases
        mapping = {
            "organization": "organization_type",
            "user_role": "user_role_type",
            "user_status": "user_status",
            "billing_plan": "billing_plan",
            "pricing_plan_interval": "pricing_plan_interval",
            "project_status": "project_status",
            "project_role": "project_role",
            "visibility": "visibility",
            "requirement_status": "requirement_status",
            "requirement_format": "requirement_format",
            "requirement_priority": "requirement_priority",
            "requirement_level": "requirement_level",
            "test_type": "test_type",
            "test_priority": "test_priority",
            "test_status": "test_status",
            "test_method": "test_method",
            "execution_status": "execution_status",
            "invitation_status": "invitation_status",
            "notification_type": "notification_type",
            "entity_type": "entity_type",
            "trace_link_type": "trace_link_type",
            "assignment_role": "assignment_role",
            "subscription_status": "subscription_status",
            "audit_severity": "audit_severity",
        }

        return mapping.get(name, name)

    def _convert_class_to_table_name(self, class_name: str) -> str:
        """Convert Python class name to database table name."""
        # OrganizationRow -> organizations
        name = class_name.replace("Row", "")

        # Convert camelCase to snake_case
        import re
        name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        name = re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()

        # Pluralize (simple rules)
        if name.endswith("y"):
            name = name[:-1] + "ies"
        elif name.endswith("s"):
            name = name + "es"
        else:
            name = name + "s"

        # Handle special cases
        mapping = {
            "propertiess": "properties",
            "columnss": "columns",
            "table_rowss": "table_rows",
            "requirements_closures": "requirements_closure",
        }

        return mapping.get(name, name)

    def compare_schemas(self) -> list[dict[str, Any]]:
        """Compare database and local schemas."""
        differences = []

        # Filter out system enums (Supabase auth schema enums)
        system_enums = {
            "key_status", "key_type", "aal_level", "code_challenge_method",
            "factor_status", "factor_type", "one_time_token_type",
            "request_status", "equality_op", "action", "buckettype",
            "oauth_registration_type"
        }

        # Compare enums
        db_enums = set(self.db_schema.get("enums", {}).keys()) - system_enums
        local_enums = set(self.local_schema.get("enums", {}).keys())

        # New enums in database
        for enum_name in db_enums - local_enums:
            differences.append({
                "type": "enum",
                "change": "added",
                "name": enum_name,
                "values": self.db_schema["enums"][enum_name],
                "severity": "high"
            })

        # Removed enums
        for enum_name in local_enums - db_enums:
            differences.append({
                "type": "enum",
                "change": "removed",
                "name": enum_name,
                "severity": "critical"
            })

        # Modified enums
        for enum_name in db_enums & local_enums:
            db_values = set(self.db_schema["enums"][enum_name])
            local_values = set(self.local_schema["enums"][enum_name])

            if db_values != local_values:
                differences.append({
                    "type": "enum",
                    "change": "modified",
                    "name": enum_name,
                    "added_values": list(db_values - local_values),
                    "removed_values": list(local_values - db_values),
                    "severity": "high" if (local_values - db_values) else "medium"
                })

        # Filter out system tables and views
        system_tables = {
            "diagram_element_links_with_details",  # This is a view, not a table
        }

        # Also filter out tables with singular/plural naming issues
        # (e.g., billing_cache vs billing_caches)
        # Map database table name -> local table name
        table_aliases = {
            "billing_cache": "billing_caches",
            "embedding_cache": "embedding_caches",
            "requirements_closure": "requirements_closures",
        }

        # Compare tables
        db_tables_raw = set(self.db_schema.get("tables", {}).keys()) - system_tables
        local_tables_raw = set(self.local_schema.get("tables", {}).keys())

        # Filter out system tables from local schema too
        local_tables = local_tables_raw - system_tables

        # Apply table aliases to create normalized db_tables set
        db_tables = set()
        for table in db_tables_raw:
            if table in table_aliases:
                db_tables.add(table_aliases[table])
            else:
                db_tables.add(table)

        # New tables in database
        for table_name in db_tables - local_tables:
            differences.append({
                "type": "table",
                "change": "added",
                "name": table_name,
                "columns": self.db_schema["tables"][table_name]["columns"],
                "severity": "high"
            })

        # Removed tables
        for table_name in local_tables - db_tables:
            differences.append({
                "type": "table",
                "change": "removed",
                "name": table_name,
                "severity": "critical"
            })

        # Modified tables (column changes)
        for table_name in db_tables & local_tables:
            # Get the original database table name (reverse the alias)
            db_table_name = table_name
            for db_name, local_name in table_aliases.items():
                if local_name == table_name:
                    db_table_name = db_name
                    break

            db_cols = {c["column_name"] for c in self.db_schema["tables"][db_table_name]["columns"]}
            local_cols = {c["column_name"] for c in self.local_schema["tables"][table_name]["columns"]}

            added_cols = db_cols - local_cols
            removed_cols = local_cols - db_cols

            if added_cols or removed_cols:
                differences.append({
                    "type": "table",
                    "change": "modified",
                    "name": table_name,
                    "added_columns": list(added_cols),
                    "removed_columns": list(removed_cols),
                    "severity": "high" if removed_cols else "medium"
                })

        return differences

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
        # organization_type -> OrganizationType
        parts = enum_name.split("_")
        class_name = "".join(word.capitalize() for word in parts)

        # Add Type suffix if not present
        if not class_name.endswith("Type") and not class_name.endswith("Status"):
            class_name += "Type"

        return class_name

    def generate_table_row_code(self, table_name: str, columns: list[dict]) -> str:
        """Generate Python TypedDict code for table row."""
        class_name = self._table_name_to_class(table_name)

        code = f'''
class {class_name}(TypedDict, total=False):
    """Database row for {table_name} table.

    Auto-generated from database schema.
    """
'''
        for col in columns:
            col_name = col["column_name"]
            py_type = self._sql_to_python_type(col)
            code += f"    {col_name}: {py_type}\n"

        return code

    def _table_name_to_class(self, table_name: str) -> str:
        """Convert database table name to Python class name."""
        # organizations -> OrganizationRow

        # De-pluralize (simple rules)
        if table_name.endswith("ies"):
            name = table_name[:-3] + "y"
        elif table_name.endswith("ses"):
            name = table_name[:-2]
        elif table_name.endswith("s"):
            name = table_name[:-1]
        else:
            name = table_name

        parts = name.split("_")
        class_name = "".join(word.capitalize() for word in parts) + "Row"

        return class_name

    def _sql_to_python_type(self, column: dict) -> str:
        """Convert SQL type to Python type annotation."""
        data_type = column.get("data_type", "").lower()
        udt_name = column.get("udt_name", "").lower()
        is_nullable = column.get("is_nullable", "YES") == "YES"

        # Map SQL types to Python types
        type_mapping = {
            "uuid": "str",
            "text": "str",
            "character varying": "str",
            "varchar": "str",
            "integer": "int",
            "bigint": "int",
            "smallint": "int",
            "boolean": "bool",
            "timestamp with time zone": "str",
            "timestamp without time zone": "str",
            "date": "str",
            "time": "str",
            "jsonb": "dict",
            "json": "dict",
            "array": "list",
            "numeric": "float",
            "real": "float",
            "double precision": "float",
            "interval": "str",
        }

        if data_type == "user-defined":
            # Check if it's an enum
            py_type = "str"  # Default for enums
        elif data_type == "array":
            element_type = type_mapping.get(udt_name.replace("_", ""), "Any")
            py_type = f"list[{element_type}]"
        else:
            py_type = type_mapping.get(data_type, "Any")

        if is_nullable:
            py_type = f"Optional[{py_type}]"

        return py_type

    def calculate_schema_hash(self, schema: dict) -> str:
        """Calculate SHA256 hash of schema."""
        schema_json = json.dumps(schema, sort_keys=True)
        return hashlib.sha256(schema_json.encode()).hexdigest()

    def update_schema_files(self):
        """Update local schema files with database schema."""
        print(f"{Colors.BOLD}Updating schema files...{Colors.END}")

        # Update enums
        enum_updates = [d for d in self.differences if d["type"] == "enum" and d["change"] in ["added", "modified"]]
        if enum_updates:
            print(f"\n{Colors.CYAN}Updating enums.py...{Colors.END}")
            # Note: This would require more sophisticated code merging
            print(f"{Colors.YELLOW}Manual update required for enums.py{Colors.END}")
            for diff in enum_updates:
                code = self.generate_enum_code(diff["name"], diff.get("values", []))
                print(code)

        # Update tables
        table_updates = [d for d in self.differences if d["type"] == "table" and d["change"] in ["added", "modified"]]
        if table_updates:
            print(f"\n{Colors.CYAN}Updating entities.py...{Colors.END}")
            print(f"{Colors.YELLOW}Manual update required for entities.py{Colors.END}")
            for diff in table_updates:
                if diff["change"] == "added":
                    code = self.generate_table_row_code(diff["name"], diff.get("columns", []))
                    print(code)

        # Update version file
        self.update_version_file()

        print(f"\n{Colors.GREEN}Schema update complete!{Colors.END}")

    def update_version_file(self):
        """Update schema_version.py with new version info."""
        version_file = self.schemas_dir / "schema_version.py"

        now = datetime.now(UTC)
        db_hash = self.calculate_schema_hash(self.db_schema)

        content = f'''"""
Schema Version Tracking

This file is auto-generated by scripts/sync_schema.py
DO NOT EDIT MANUALLY
"""

SCHEMA_VERSION = "{now.strftime('%Y-%m-%d')}"
LAST_SYNC = "{now.isoformat()}"
DB_HASH = "{db_hash}"

# Schema statistics
TABLES_COUNT = {len(self.db_schema.get('tables', {}))}
ENUMS_COUNT = {len(self.db_schema.get('enums', {}))}

# Last sync differences count
LAST_SYNC_DIFFERENCES = {len(self.differences)}
'''

        with open(version_file, "w") as f:
            f.write(content)

        print(f"{Colors.GREEN}Updated {version_file}{Colors.END}")

    def print_diff(self):
        """Print detailed diff of schema changes."""
        if not self.differences:
            print(f"{Colors.GREEN}✓ No schema differences found{Colors.END}")
            return

        print(f"\n{Colors.BOLD}Schema Differences:{Colors.END}\n")

        for diff in self.differences:
            severity_color = {
                "critical": Colors.RED,
                "high": Colors.YELLOW,
                "medium": Colors.BLUE,
                "low": Colors.GREEN
            }.get(diff.get("severity", "low"), Colors.END)

            print(f"{severity_color}[{diff['severity'].upper()}] {diff['type'].upper()}: {diff['name']}{Colors.END}")
            print(f"  Change: {diff['change']}")

            if diff["change"] == "added":
                if diff["type"] == "enum":
                    print(f"  Values: {', '.join(diff['values'])}")
                elif diff["type"] == "table":
                    print(f"  Columns: {len(diff['columns'])}")

            elif diff["change"] == "modified":
                if "added_values" in diff:
                    print(f"  Added values: {', '.join(diff['added_values'])}")
                if "removed_values" in diff:
                    print(f"  Removed values: {', '.join(diff['removed_values'])}")
                if "added_columns" in diff:
                    print(f"  Added columns: {', '.join(diff['added_columns'])}")
                if "removed_columns" in diff:
                    print(f"  Removed columns: {', '.join(diff['removed_columns'])}")

            print()

    def generate_report(self):
        """Generate a detailed markdown report."""
        report_file = self.root_dir / f"schema_drift_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

        with open(report_file, "w") as f:
            f.write("# Schema Drift Report\n\n")
            f.write(f"**Generated:** {datetime.now().isoformat()}\n\n")
            f.write(f"**Database Hash:** {self.calculate_schema_hash(self.db_schema)}\n\n")

            if not self.differences:
                f.write("## Status: ✓ No Drift Detected\n\n")
                f.write("Local schemas are in sync with database.\n")
            else:
                f.write(f"## Status: ⚠️ {len(self.differences)} Differences Found\n\n")

                # Group by type
                enums = [d for d in self.differences if d["type"] == "enum"]
                tables = [d for d in self.differences if d["type"] == "table"]

                if enums:
                    f.write("### Enum Changes\n\n")
                    for diff in enums:
                        f.write(f"#### {diff['name']} ({diff['change']})\n")
                        if diff["change"] == "added":
                            f.write(f"- Values: `{', '.join(diff['values'])}`\n")
                        elif diff["change"] == "modified":
                            if diff.get("added_values"):
                                f.write(f"- Added: `{', '.join(diff['added_values'])}`\n")
                            if diff.get("removed_values"):
                                f.write(f"- Removed: `{', '.join(diff['removed_values'])}`\n")
                        f.write("\n")

                if tables:
                    f.write("### Table Changes\n\n")
                    for diff in tables:
                        f.write(f"#### {diff['name']} ({diff['change']})\n")
                        if diff["change"] == "added":
                            f.write(f"- Columns: {len(diff['columns'])}\n")
                        elif diff["change"] == "modified":
                            if diff.get("added_columns"):
                                f.write(f"- Added columns: `{', '.join(diff['added_columns'])}`\n")
                            if diff.get("removed_columns"):
                                f.write(f"- Removed columns: `{', '.join(diff['removed_columns'])}`\n")
                        f.write("\n")

                f.write("\n## Actions Required\n\n")
                f.write("1. Review the differences above\n")
                f.write("2. Update local schema files: `python scripts/sync_schema.py --update`\n")
                f.write("3. Update any code that depends on changed schemas\n")
                f.write("4. Run tests to verify compatibility\n")

        print(f"{Colors.GREEN}Report generated: {report_file}{Colors.END}")

    def check_drift(self) -> bool:
        """Check for schema drift and return True if drift exists."""
        self.db_schema = self.get_supabase_schema()
        self.local_schema = self.get_local_schema()
        self.differences = self.compare_schemas()

        return len(self.differences) > 0

    def run(self, mode: str):
        """Run the schema sync tool in specified mode."""
        print(f"{Colors.BOLD}Atoms MCP Schema Synchronization{Colors.END}\n")

        if mode == "regenerate":
            success = self.regenerate_schemas()
            sys.exit(0 if success else 1)

        elif mode == "check":
            has_drift = self.check_drift()
            self.print_diff()

            if has_drift:
                print(f"\n{Colors.YELLOW}⚠️  Schema drift detected!{Colors.END}")
                print("Run with --regenerate to regenerate from database")
                sys.exit(1)
            else:
                print(f"\n{Colors.GREEN}✓ Schemas are in sync{Colors.END}")
                sys.exit(0)

        elif mode == "diff":
            self.check_drift()
            self.print_diff()

        elif mode == "update":
            # Update is now an alias for regenerate
            success = self.regenerate_schemas()
            sys.exit(0 if success else 1)

        elif mode == "report":
            self.check_drift()
            self.generate_report()


def main():
    parser = argparse.ArgumentParser(
        description="Synchronize Python schemas with Supabase database using supabase-pydantic"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check for schema drift (exit 1 if drift found)"
    )
    parser.add_argument(
        "--diff",
        action="store_true",
        help="Show detailed differences"
    )
    parser.add_argument(
        "--regenerate",
        action="store_true",
        help="Regenerate schemas from database using supabase-pydantic"
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Update local schema files (alias for --regenerate)"
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate markdown report"
    )
    parser.add_argument(
        "--project-id",
        type=str,
        help="Supabase project ID (default: from env)"
    )

    args = parser.parse_args()

    # Determine mode
    if args.regenerate:
        mode = "regenerate"
    elif args.check:
        mode = "check"
    elif args.diff:
        mode = "diff"
    elif args.update:
        mode = "update"
    elif args.report:
        mode = "report"
    else:
        parser.print_help()
        sys.exit(1)

    # Run sync
    sync = SchemaSync(project_id=args.project_id)
    sync.run(mode)


if __name__ == "__main__":
    main()
