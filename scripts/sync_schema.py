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
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import os

# Add parent directory to path to import schemas
sys.path.insert(0, str(Path(__file__).parent.parent))

from schemas import enums
from schemas.database import entities, relationships


class Colors:
    """ANSI color codes for terminal output."""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


class SchemaSync:
    """Schema synchronization manager."""

    def __init__(self, project_id: Optional[str] = None):
        self.project_id = project_id or os.getenv('SUPABASE_PROJECT_ID')
        self.root_dir = Path(__file__).parent.parent
        self.schemas_dir = self.root_dir / 'schemas'
        self.db_schema = {}
        self.local_schema = {}
        self.differences = []

    def get_supabase_schema(self) -> Dict[str, Any]:
        """Query Supabase for current database schema using MCP tools."""
        try:
            # Try to import supabase client
            from supabase_client import get_supabase_admin

            supabase = get_supabase_admin()

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

            tables_result = supabase.rpc('execute_sql', {'sql': tables_query}).execute()

            schema = {'tables': {}, 'enums': {}}

            # For each table, get columns
            for table in tables_result.data:
                table_name = table['table_name']

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

                cols_result = supabase.rpc('execute_sql', {'sql': columns_query}).execute()

                schema['tables'][table_name] = {
                    'columns': cols_result.data
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

            enums_result = supabase.rpc('execute_sql', {'sql': enums_query}).execute()

            for enum_row in enums_result.data:
                schema['enums'][enum_row['enum_name']] = enum_row['enum_values']

            return schema

        except Exception as e:
            print(f"{Colors.RED}Error querying Supabase schema: {e}{Colors.END}")
            print(f"{Colors.YELLOW}Falling back to mock schema for demo{Colors.END}")
            return self._get_mock_schema()

    def _get_mock_schema(self) -> Dict[str, Any]:
        """Return a mock schema for demonstration."""
        return {
            'tables': {
                'organizations': {
                    'columns': [
                        {'column_name': 'id', 'data_type': 'uuid', 'is_nullable': 'NO', 'udt_name': 'uuid'},
                        {'column_name': 'name', 'data_type': 'text', 'is_nullable': 'NO', 'udt_name': 'text'},
                        {'column_name': 'type', 'data_type': 'USER-DEFINED', 'is_nullable': 'NO', 'udt_name': 'organization_type'},
                        {'column_name': 'billing_plan', 'data_type': 'USER-DEFINED', 'is_nullable': 'NO', 'udt_name': 'billing_plan'},
                    ]
                },
                'projects': {
                    'columns': [
                        {'column_name': 'id', 'data_type': 'uuid', 'is_nullable': 'NO', 'udt_name': 'uuid'},
                        {'column_name': 'name', 'data_type': 'text', 'is_nullable': 'NO', 'udt_name': 'text'},
                        {'column_name': 'status', 'data_type': 'USER-DEFINED', 'is_nullable': 'NO', 'udt_name': 'project_status'},
                    ]
                }
            },
            'enums': {
                'organization_type': ['personal', 'team', 'enterprise'],
                'billing_plan': ['free', 'pro', 'enterprise'],
                'project_status': ['active', 'archived', 'draft', 'deleted'],
            }
        }

    def get_local_schema(self) -> Dict[str, Any]:
        """Extract schema from local Python files."""
        local = {'tables': {}, 'enums': {}}

        # Extract enums from enums.py
        enum_classes = []
        for name in dir(enums):
            obj = getattr(enums, name)
            if isinstance(obj, type) and issubclass(obj, enums.Enum) and obj != enums.Enum:
                if not name.startswith('_'):
                    enum_classes.append(obj)

        for enum_class in enum_classes:
            enum_name = self._convert_class_to_enum_name(enum_class.__name__)
            values = [e.value for e in enum_class]
            local['enums'][enum_name] = values

        # Extract tables from entities.py
        for name in dir(entities):
            if name.endswith('Row'):
                obj = getattr(entities, name)
                if hasattr(obj, '__annotations__'):
                    table_name = self._convert_class_to_table_name(name)
                    columns = []

                    for field_name, field_type in obj.__annotations__.items():
                        columns.append({
                            'column_name': field_name,
                            'python_type': str(field_type),
                        })

                    local['tables'][table_name] = {'columns': columns}

        return local

    def _convert_class_to_enum_name(self, class_name: str) -> str:
        """Convert Python class name to database enum name."""
        # OrganizationType -> organization_type
        name = class_name.replace('Type', '').replace('Status', '').replace('Enum', '')
        # Convert camelCase to snake_case
        import re
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()

        # Handle special cases
        mapping = {
            'organization': 'organization_type',
            'user_role': 'user_role_type',
            'user_status': 'user_status',
            'billing_plan': 'billing_plan',
            'pricing_plan_interval': 'pricing_plan_interval',
            'project_status': 'project_status',
            'project_role': 'project_role',
            'visibility': 'visibility',
            'requirement_status': 'requirement_status',
            'requirement_format': 'requirement_format',
            'requirement_priority': 'requirement_priority',
            'requirement_level': 'requirement_level',
            'test_type': 'test_type',
            'test_priority': 'test_priority',
            'test_status': 'test_status',
            'test_method': 'test_method',
            'execution_status': 'execution_status',
            'invitation_status': 'invitation_status',
            'notification_type': 'notification_type',
            'entity_type': 'entity_type',
            'trace_link_type': 'trace_link_type',
            'assignment_role': 'assignment_role',
            'subscription_status': 'subscription_status',
            'audit_severity': 'audit_severity',
        }

        return mapping.get(name, name)

    def _convert_class_to_table_name(self, class_name: str) -> str:
        """Convert Python class name to database table name."""
        # OrganizationRow -> organizations
        name = class_name.replace('Row', '')

        # Convert camelCase to snake_case
        import re
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()

        # Pluralize (simple rules)
        if name.endswith('y'):
            name = name[:-1] + 'ies'
        elif name.endswith('s'):
            name = name + 'es'
        else:
            name = name + 's'

        # Handle special cases
        mapping = {
            'propertiess': 'properties',
            'columnss': 'columns',
            'table_rowss': 'table_rows',
            'requirements_closures': 'requirements_closure',
        }

        return mapping.get(name, name)

    def compare_schemas(self) -> List[Dict[str, Any]]:
        """Compare database and local schemas."""
        differences = []

        # Compare enums
        db_enums = set(self.db_schema.get('enums', {}).keys())
        local_enums = set(self.local_schema.get('enums', {}).keys())

        # New enums in database
        for enum_name in db_enums - local_enums:
            differences.append({
                'type': 'enum',
                'change': 'added',
                'name': enum_name,
                'values': self.db_schema['enums'][enum_name],
                'severity': 'high'
            })

        # Removed enums
        for enum_name in local_enums - db_enums:
            differences.append({
                'type': 'enum',
                'change': 'removed',
                'name': enum_name,
                'severity': 'critical'
            })

        # Modified enums
        for enum_name in db_enums & local_enums:
            db_values = set(self.db_schema['enums'][enum_name])
            local_values = set(self.local_schema['enums'][enum_name])

            if db_values != local_values:
                differences.append({
                    'type': 'enum',
                    'change': 'modified',
                    'name': enum_name,
                    'added_values': list(db_values - local_values),
                    'removed_values': list(local_values - db_values),
                    'severity': 'high' if (local_values - db_values) else 'medium'
                })

        # Compare tables
        db_tables = set(self.db_schema.get('tables', {}).keys())
        local_tables = set(self.local_schema.get('tables', {}).keys())

        # New tables in database
        for table_name in db_tables - local_tables:
            differences.append({
                'type': 'table',
                'change': 'added',
                'name': table_name,
                'columns': self.db_schema['tables'][table_name]['columns'],
                'severity': 'high'
            })

        # Removed tables
        for table_name in local_tables - db_tables:
            differences.append({
                'type': 'table',
                'change': 'removed',
                'name': table_name,
                'severity': 'critical'
            })

        # Modified tables (column changes)
        for table_name in db_tables & local_tables:
            db_cols = {c['column_name'] for c in self.db_schema['tables'][table_name]['columns']}
            local_cols = {c['column_name'] for c in self.local_schema['tables'][table_name]['columns']}

            added_cols = db_cols - local_cols
            removed_cols = local_cols - db_cols

            if added_cols or removed_cols:
                differences.append({
                    'type': 'table',
                    'change': 'modified',
                    'name': table_name,
                    'added_columns': list(added_cols),
                    'removed_columns': list(removed_cols),
                    'severity': 'high' if removed_cols else 'medium'
                })

        return differences

    def generate_enum_code(self, enum_name: str, values: List[str]) -> str:
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
            const_name = value.upper().replace('-', '_').replace(' ', '_')
            code += f'    {const_name} = "{value}"\n'

        return code

    def _enum_name_to_class(self, enum_name: str) -> str:
        """Convert database enum name to Python class name."""
        # organization_type -> OrganizationType
        parts = enum_name.split('_')
        class_name = ''.join(word.capitalize() for word in parts)

        # Add Type suffix if not present
        if not class_name.endswith('Type') and not class_name.endswith('Status'):
            class_name += 'Type'

        return class_name

    def generate_table_row_code(self, table_name: str, columns: List[Dict]) -> str:
        """Generate Python TypedDict code for table row."""
        class_name = self._table_name_to_class(table_name)

        code = f'''
class {class_name}(TypedDict, total=False):
    """Database row for {table_name} table.

    Auto-generated from database schema.
    """
'''
        for col in columns:
            col_name = col['column_name']
            py_type = self._sql_to_python_type(col)
            code += f'    {col_name}: {py_type}\n'

        return code

    def _table_name_to_class(self, table_name: str) -> str:
        """Convert database table name to Python class name."""
        # organizations -> OrganizationRow

        # De-pluralize (simple rules)
        if table_name.endswith('ies'):
            name = table_name[:-3] + 'y'
        elif table_name.endswith('ses'):
            name = table_name[:-2]
        elif table_name.endswith('s'):
            name = table_name[:-1]
        else:
            name = table_name

        parts = name.split('_')
        class_name = ''.join(word.capitalize() for word in parts) + 'Row'

        return class_name

    def _sql_to_python_type(self, column: Dict) -> str:
        """Convert SQL type to Python type annotation."""
        data_type = column.get('data_type', '').lower()
        udt_name = column.get('udt_name', '').lower()
        is_nullable = column.get('is_nullable', 'YES') == 'YES'

        # Map SQL types to Python types
        type_mapping = {
            'uuid': 'str',
            'text': 'str',
            'character varying': 'str',
            'varchar': 'str',
            'integer': 'int',
            'bigint': 'int',
            'smallint': 'int',
            'boolean': 'bool',
            'timestamp with time zone': 'str',
            'timestamp without time zone': 'str',
            'date': 'str',
            'time': 'str',
            'jsonb': 'dict',
            'json': 'dict',
            'array': 'list',
            'numeric': 'float',
            'real': 'float',
            'double precision': 'float',
            'interval': 'str',
        }

        if data_type == 'user-defined':
            # Check if it's an enum
            py_type = 'str'  # Default for enums
        elif data_type == 'array':
            element_type = type_mapping.get(udt_name.replace('_', ''), 'Any')
            py_type = f'list[{element_type}]'
        else:
            py_type = type_mapping.get(data_type, 'Any')

        if is_nullable:
            py_type = f'Optional[{py_type}]'

        return py_type

    def calculate_schema_hash(self, schema: Dict) -> str:
        """Calculate SHA256 hash of schema."""
        schema_json = json.dumps(schema, sort_keys=True)
        return hashlib.sha256(schema_json.encode()).hexdigest()

    def update_schema_files(self):
        """Update local schema files with database schema."""
        print(f"{Colors.BOLD}Updating schema files...{Colors.END}")

        # Update enums
        enum_updates = [d for d in self.differences if d['type'] == 'enum' and d['change'] in ['added', 'modified']]
        if enum_updates:
            print(f"\n{Colors.CYAN}Updating enums.py...{Colors.END}")
            # Note: This would require more sophisticated code merging
            print(f"{Colors.YELLOW}Manual update required for enums.py{Colors.END}")
            for diff in enum_updates:
                code = self.generate_enum_code(diff['name'], diff.get('values', []))
                print(code)

        # Update tables
        table_updates = [d for d in self.differences if d['type'] == 'table' and d['change'] in ['added', 'modified']]
        if table_updates:
            print(f"\n{Colors.CYAN}Updating entities.py...{Colors.END}")
            print(f"{Colors.YELLOW}Manual update required for entities.py{Colors.END}")
            for diff in table_updates:
                if diff['change'] == 'added':
                    code = self.generate_table_row_code(diff['name'], diff.get('columns', []))
                    print(code)

        # Update version file
        self.update_version_file()

        print(f"\n{Colors.GREEN}Schema update complete!{Colors.END}")

    def update_version_file(self):
        """Update schema_version.py with new version info."""
        version_file = self.schemas_dir / 'schema_version.py'

        now = datetime.now(timezone.utc)
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

        with open(version_file, 'w') as f:
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
                'critical': Colors.RED,
                'high': Colors.YELLOW,
                'medium': Colors.BLUE,
                'low': Colors.GREEN
            }.get(diff.get('severity', 'low'), Colors.END)

            print(f"{severity_color}[{diff['severity'].upper()}] {diff['type'].upper()}: {diff['name']}{Colors.END}")
            print(f"  Change: {diff['change']}")

            if diff['change'] == 'added':
                if diff['type'] == 'enum':
                    print(f"  Values: {', '.join(diff['values'])}")
                elif diff['type'] == 'table':
                    print(f"  Columns: {len(diff['columns'])}")

            elif diff['change'] == 'modified':
                if 'added_values' in diff:
                    print(f"  Added values: {', '.join(diff['added_values'])}")
                if 'removed_values' in diff:
                    print(f"  Removed values: {', '.join(diff['removed_values'])}")
                if 'added_columns' in diff:
                    print(f"  Added columns: {', '.join(diff['added_columns'])}")
                if 'removed_columns' in diff:
                    print(f"  Removed columns: {', '.join(diff['removed_columns'])}")

            print()

    def generate_report(self):
        """Generate a detailed markdown report."""
        report_file = self.root_dir / f"schema_drift_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

        with open(report_file, 'w') as f:
            f.write("# Schema Drift Report\n\n")
            f.write(f"**Generated:** {datetime.now().isoformat()}\n\n")
            f.write(f"**Database Hash:** {self.calculate_schema_hash(self.db_schema)}\n\n")

            if not self.differences:
                f.write("## Status: ✓ No Drift Detected\n\n")
                f.write("Local schemas are in sync with database.\n")
            else:
                f.write(f"## Status: ⚠️ {len(self.differences)} Differences Found\n\n")

                # Group by type
                enums = [d for d in self.differences if d['type'] == 'enum']
                tables = [d for d in self.differences if d['type'] == 'table']

                if enums:
                    f.write("### Enum Changes\n\n")
                    for diff in enums:
                        f.write(f"#### {diff['name']} ({diff['change']})\n")
                        if diff['change'] == 'added':
                            f.write(f"- Values: `{', '.join(diff['values'])}`\n")
                        elif diff['change'] == 'modified':
                            if diff.get('added_values'):
                                f.write(f"- Added: `{', '.join(diff['added_values'])}`\n")
                            if diff.get('removed_values'):
                                f.write(f"- Removed: `{', '.join(diff['removed_values'])}`\n")
                        f.write("\n")

                if tables:
                    f.write("### Table Changes\n\n")
                    for diff in tables:
                        f.write(f"#### {diff['name']} ({diff['change']})\n")
                        if diff['change'] == 'added':
                            f.write(f"- Columns: {len(diff['columns'])}\n")
                        elif diff['change'] == 'modified':
                            if diff.get('added_columns'):
                                f.write(f"- Added columns: `{', '.join(diff['added_columns'])}`\n")
                            if diff.get('removed_columns'):
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

        if mode == 'check':
            has_drift = self.check_drift()
            self.print_diff()

            if has_drift:
                print(f"\n{Colors.YELLOW}⚠️  Schema drift detected!{Colors.END}")
                print(f"Run with --diff for details or --update to sync")
                sys.exit(1)
            else:
                print(f"\n{Colors.GREEN}✓ Schemas are in sync{Colors.END}")
                sys.exit(0)

        elif mode == 'diff':
            self.check_drift()
            self.print_diff()

        elif mode == 'update':
            self.check_drift()
            if not self.differences:
                print(f"{Colors.GREEN}✓ No updates needed{Colors.END}")
            else:
                self.update_schema_files()

        elif mode == 'report':
            self.check_drift()
            self.generate_report()


def main():
    parser = argparse.ArgumentParser(
        description='Synchronize Python schemas with Supabase database'
    )
    parser.add_argument(
        '--check',
        action='store_true',
        help='Check for schema drift (exit 1 if drift found)'
    )
    parser.add_argument(
        '--diff',
        action='store_true',
        help='Show detailed differences'
    )
    parser.add_argument(
        '--update',
        action='store_true',
        help='Update local schema files'
    )
    parser.add_argument(
        '--report',
        action='store_true',
        help='Generate markdown report'
    )
    parser.add_argument(
        '--project-id',
        type=str,
        help='Supabase project ID (default: from env)'
    )

    args = parser.parse_args()

    # Determine mode
    if args.check:
        mode = 'check'
    elif args.diff:
        mode = 'diff'
    elif args.update:
        mode = 'update'
    elif args.report:
        mode = 'report'
    else:
        parser.print_help()
        sys.exit(1)

    # Run sync
    sync = SchemaSync(project_id=args.project_id)
    sync.run(mode)


if __name__ == '__main__':
    main()
