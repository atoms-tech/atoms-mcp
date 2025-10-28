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

# Ensure repo root is on sys.path for script/CLI invocations
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Load environment variables from .env file
from dotenv import load_dotenv

load_dotenv()

# Import from generated schemas (now the source of truth)
import contextlib

from schemas.generated.fastapi import schema_public_latest as generated_schema  # noqa: E402
from .database import DatabaseOperations
from .codegen import CodeGenerator
from .comparison import SchemaComparator
from .file_ops import FileOperations
from .reporting import SchemaReporter
from .schema_extractor import SchemaExtractor

DEFAULT_SUPABASE_USER = "postgres.ydogoylwenufckscqijp"
DEFAULT_SUPABASE_HOST = "aws-0-us-west-1.pooler.supabase.com"
DEFAULT_SUPABASE_PORT = "6543"
DEFAULT_SUPABASE_DB = "postgres"


def resolve_db_url(explicit_url: str | None = None) -> str:
    """
    Return a Postgres connection URL, preferring explicit/env inputs over defaults.
    """
    if explicit_url:
        return explicit_url

    env_url = os.getenv("DB_URL") or os.getenv("SUPABASE_DB_URL")
    if env_url:
        return env_url

    password = os.getenv("SUPABASE_DB_PASSWORD")
    if not password:
        raise ValueError("Set DB_URL or SUPABASE_DB_PASSWORD to query Supabase schema")

    user = os.getenv("SUPABASE_DB_USER", DEFAULT_SUPABASE_USER)
    host = os.getenv("SUPABASE_DB_HOST", DEFAULT_SUPABASE_HOST)
    port = os.getenv("SUPABASE_DB_PORT", DEFAULT_SUPABASE_PORT)
    db_name = os.getenv("SUPABASE_DB_NAME", DEFAULT_SUPABASE_DB)

    return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"


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

    def __init__(self, project_id: str | None = None, db_url: str | None = None):
        self.project_id = project_id or os.getenv("SUPABASE_PROJECT_ID")
        self.root_dir = ROOT_DIR
        self.schemas_dir = self.root_dir / "schemas"
        self.db_schema: dict[str, Any] = {}
        self.local_schema: dict[str, Any] = {}
        self.differences: list[Any] = []
        self._db_url = db_url
        self.db_ops = DatabaseOperations(db_url)
        self.codegen = CodeGenerator()
        self.comparator = SchemaComparator()
        self.file_ops = FileOperations(self.schemas_dir)
        self.reporter = SchemaReporter(self.root_dir)
        self.extractor = SchemaExtractor()

    def _get_db_url(self) -> str:
        """Lazily resolve and cache the database URL."""
        if not self._db_url:
            self._db_url = resolve_db_url()
        return self._db_url


    def regenerate_schemas(self) -> bool:
        """Regenerate schemas from database using supabase-pydantic."""
        import subprocess

        db_url = self._get_db_url()

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

            # Update version metadata and snapshot retention
            self.update_version_file()
            self.prune_schema_snapshots()
            return True
        print(f"{Colors.RED}❌ Schema generation failed{Colors.END}")
        print(result.stderr)
        return False

    def _add_missing_enums(self):
        """Add enum definitions that sb-pydantic missed."""
        import re

        import psycopg2

        print(f"{Colors.CYAN}Adding missing enum definitions...{Colors.END}")

        try:
            db_url = self._get_db_url()
        except ValueError:
            return

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

        try:
            db_url = self._get_db_url()
        except ValueError:
            return

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



    def get_local_schema(self) -> dict[str, Any]:
        """Extract schema from generated Python file."""
        return self.extractor.get_local_schema()


    def compare_schemas(self) -> list[dict[str, Any]]:
        """Compare database and local schemas."""
        return self.comparator.compare_schemas(self.db_schema, self.local_schema)


    def calculate_schema_hash(self, schema: dict) -> str:
        """Calculate SHA256 hash of schema."""
        return self.file_ops.calculate_schema_hash(schema)

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
                code = self.codegen.generate_enum_code(diff["name"], diff.get("values", []))
                print(code)

        # Update tables
        table_updates = [d for d in self.differences if d["type"] == "table" and d["change"] in ["added", "modified"]]
        if table_updates:
            print(f"\n{Colors.CYAN}Updating entities.py...{Colors.END}")
            print(f"{Colors.YELLOW}Manual update required for entities.py{Colors.END}")
            for diff in table_updates:
                if diff["change"] == "added":
                    code = self.codegen.generate_table_row_code(diff["name"], diff.get("columns", []))
                    print(code)

        # Update version file
        self.file_ops.update_version_file()

        print(f"\n{Colors.GREEN}Schema update complete!{Colors.END}")



    def print_diff(self):
        """Print detailed diff of schema changes."""
        self.reporter.print_diff(self.differences)

    def generate_report(self):
        """Generate a detailed markdown report."""
        return self.reporter.generate_report(self.differences, self.db_schema, self.calculate_schema_hash)

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
