#!/usr/bin/env python3
"""
MCP-based Schema Query Tool

This script uses Supabase MCP tools to query and analyze the database schema.
It demonstrates integration with the MCP system for schema introspection.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class MCPSchemaQuery:
    """Query database schema using MCP tools."""

    def __init__(self, project_id: str | None = None):
        self.project_id = project_id or os.getenv("SUPABASE_PROJECT_ID")

    async def execute_sql(self, query: str) -> list[dict[str, Any]]:
        """Execute SQL query using MCP execute_sql tool."""
        try:
            # This would call the Supabase MCP execute_sql tool
            # For implementation, use: mcp__supabase__execute_sql
            print(f"Executing SQL: {query[:100]}...")

            # Simulated response for documentation
            return []
        except Exception as e:
            print(f"Error executing SQL: {e}")
            return []

    async def list_tables(self, schemas: list[str] = None) -> list[dict[str, Any]]:
        """List all tables using MCP list_tables tool."""
        if schemas is None:
            schemas = ["public"]

        try:
            # This would call: mcp__supabase__list_tables
            query = """
                SELECT
                    table_name,
                    table_type,
                    table_schema
                FROM information_schema.tables
                WHERE table_schema = ANY($1)
                AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """

            result = await self.execute_sql(query)
            return result
        except Exception as e:
            print(f"Error listing tables: {e}")
            return []

    async def get_table_schema(self, table_name: str) -> dict[str, Any]:
        """Get complete schema for a table including columns, constraints, indexes."""
        schema = {
            "table_name": table_name,
            "columns": [],
            "constraints": [],
            "indexes": [],
            "triggers": [],
        }

        # Get columns
        columns_query = f"""
            SELECT
                column_name,
                data_type,
                udt_name,
                is_nullable,
                column_default,
                character_maximum_length,
                numeric_precision,
                numeric_scale,
                datetime_precision,
                ordinal_position
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = '{table_name}'
            ORDER BY ordinal_position;
        """
        schema["columns"] = await self.execute_sql(columns_query)

        # Get constraints
        constraints_query = f"""
            SELECT
                tc.constraint_name,
                tc.constraint_type,
                kcu.column_name,
                ccu.table_schema AS foreign_table_schema,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name,
                rc.update_rule,
                rc.delete_rule
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            LEFT JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            LEFT JOIN information_schema.referential_constraints AS rc
                ON tc.constraint_name = rc.constraint_name
                AND tc.table_schema = rc.constraint_schema
            WHERE tc.table_schema = 'public'
            AND tc.table_name = '{table_name}'
            ORDER BY tc.constraint_type, tc.constraint_name;
        """
        schema["constraints"] = await self.execute_sql(constraints_query)

        # Get indexes
        indexes_query = f"""
            SELECT
                indexname,
                indexdef,
                tablespace
            FROM pg_indexes
            WHERE schemaname = 'public'
            AND tablename = '{table_name}'
            ORDER BY indexname;
        """
        schema["indexes"] = await self.execute_sql(indexes_query)

        # Get triggers
        triggers_query = f"""
            SELECT
                trigger_name,
                event_manipulation,
                event_object_table,
                action_statement,
                action_timing,
                action_orientation
            FROM information_schema.triggers
            WHERE event_object_schema = 'public'
            AND event_object_table = '{table_name}'
            ORDER BY trigger_name;
        """
        schema["triggers"] = await self.execute_sql(triggers_query)

        return schema

    async def get_all_enums(self) -> dict[str, list[str]]:
        """Get all enum types and their values."""
        query = """
            SELECT
                t.typname as enum_name,
                e.enumlabel as enum_value,
                e.enumsortorder as sort_order
            FROM pg_type t
            JOIN pg_enum e ON t.oid = e.enumtypid
            WHERE t.typtype = 'e'
            ORDER BY t.typname, e.enumsortorder;
        """

        results = await self.execute_sql(query)

        # Group by enum name
        enums = {}
        for row in results:
            enum_name = row["enum_name"]
            enum_value = row["enum_value"]

            if enum_name not in enums:
                enums[enum_name] = []

            enums[enum_name].append(enum_value)

        return enums

    async def get_rls_policies(self, table_name: str) -> list[dict[str, Any]]:
        """Get Row Level Security policies for a table."""
        query = f"""
            SELECT
                schemaname,
                tablename,
                policyname,
                permissive,
                roles,
                cmd,
                qual,
                with_check
            FROM pg_policies
            WHERE schemaname = 'public'
            AND tablename = '{table_name}'
            ORDER BY policyname;
        """

        return await self.execute_sql(query)

    async def get_extensions(self) -> list[dict[str, Any]]:
        """Get installed PostgreSQL extensions."""
        query = """
            SELECT
                extname,
                extversion,
                extrelocatable,
                extnamespace::regnamespace::text as schema
            FROM pg_extension
            ORDER BY extname;
        """

        return await self.execute_sql(query)

    async def analyze_schema_complexity(self) -> dict[str, Any]:
        """Analyze schema complexity and provide metrics."""
        metrics = {
            "tables": {},
            "total_columns": 0,
            "total_indexes": 0,
            "total_constraints": 0,
            "enums": {},
            "extensions": [],
        }

        # Get all tables
        tables = await self.list_tables()

        for table in tables:
            table_name = table.get("table_name")
            if not table_name:
                continue

            schema = await self.get_table_schema(table_name)

            metrics["tables"][table_name] = {
                "columns": len(schema["columns"]),
                "constraints": len(schema["constraints"]),
                "indexes": len(schema["indexes"]),
                "triggers": len(schema["triggers"]),
            }

            metrics["total_columns"] += len(schema["columns"])
            metrics["total_indexes"] += len(schema["indexes"])
            metrics["total_constraints"] += len(schema["constraints"])

        # Get enums
        metrics["enums"] = await self.get_all_enums()

        # Get extensions
        metrics["extensions"] = await self.get_extensions()

        return metrics

    async def export_schema_documentation(self, output_dir: str):
        """Export comprehensive schema documentation."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True, parents=True)

        print(f"Exporting schema documentation to {output_path}...")

        # Export table schemas
        tables = await self.list_tables()

        for table in tables:
            table_name = table.get("table_name")
            if not table_name:
                continue

            print(f"  Exporting {table_name}...")

            schema = await self.get_table_schema(table_name)
            rls_policies = await self.get_rls_policies(table_name)

            # Create markdown documentation
            md_content = self._generate_table_markdown(table_name, schema, rls_policies)

            md_file = output_path / f"{table_name}.md"
            with open(md_file, "w") as f:
                f.write(md_content)

        # Export enums
        print("  Exporting enums...")
        enums = await self.get_all_enums()

        enums_md = self._generate_enums_markdown(enums)
        enums_file = output_path / "enums.md"
        with open(enums_file, "w") as f:
            f.write(enums_md)

        # Export overview
        print("  Generating overview...")
        metrics = await self.analyze_schema_complexity()

        overview_md = self._generate_overview_markdown(metrics)
        overview_file = output_path / "README.md"
        with open(overview_file, "w") as f:
            f.write(overview_md)

        print(f"\n✓ Schema documentation exported to {output_path}")

    def _generate_table_markdown(
        self,
        table_name: str,
        schema: dict[str, Any],
        rls_policies: list[dict[str, Any]]
    ) -> str:
        """Generate markdown documentation for a table."""
        md = f"# Table: {table_name}\n\n"

        # Columns
        md += "## Columns\n\n"
        md += "| Column | Type | Nullable | Default |\n"
        md += "|--------|------|----------|----------|\n"

        for col in schema.get("columns", []):
            col_name = col.get("column_name", "")
            data_type = col.get("data_type", "")
            udt_name = col.get("udt_name", "")
            is_nullable = col.get("is_nullable", "")
            default = col.get("column_default", "")

            type_display = data_type if data_type != "USER-DEFINED" else udt_name
            nullable_display = "✓" if is_nullable == "YES" else ""
            default_display = default if default else ""

            md += f"| {col_name} | {type_display} | {nullable_display} | {default_display} |\n"

        # Constraints
        md += "\n## Constraints\n\n"

        constraints = schema.get("constraints", [])
        if constraints:
            md += "| Name | Type | Column | References |\n"
            md += "|------|------|--------|------------|\n"

            for const in constraints:
                const_name = const.get("constraint_name", "")
                const_type = const.get("constraint_type", "")
                col_name = const.get("column_name", "")
                foreign_ref = ""

                if const_type == "FOREIGN KEY":
                    foreign_table = const.get("foreign_table_name", "")
                    foreign_col = const.get("foreign_column_name", "")
                    foreign_ref = f"{foreign_table}.{foreign_col}" if foreign_table else ""

                md += f"| {const_name} | {const_type} | {col_name} | {foreign_ref} |\n"
        else:
            md += "*No constraints defined*\n"

        # Indexes
        md += "\n## Indexes\n\n"

        indexes = schema.get("indexes", [])
        if indexes:
            md += "| Name | Definition |\n"
            md += "|------|------------|\n"

            for idx in indexes:
                idx_name = idx.get("indexname", "")
                idx_def = idx.get("indexdef", "")
                md += f"| {idx_name} | `{idx_def}` |\n"
        else:
            md += "*No indexes defined*\n"

        # RLS Policies
        md += "\n## Row Level Security\n\n"

        if rls_policies:
            md += "| Policy | Command | Roles | Condition |\n"
            md += "|--------|---------|-------|----------|\n"

            for policy in rls_policies:
                policy_name = policy.get("policyname", "")
                cmd = policy.get("cmd", "")
                roles = policy.get("roles", [])
                qual = policy.get("qual", "")

                roles_display = ", ".join(roles) if isinstance(roles, list) else str(roles)
                md += f"| {policy_name} | {cmd} | {roles_display} | `{qual}` |\n"
        else:
            md += "*No RLS policies defined*\n"

        # Triggers
        md += "\n## Triggers\n\n"

        triggers = schema.get("triggers", [])
        if triggers:
            for trigger in triggers:
                trigger_name = trigger.get("trigger_name", "")
                timing = trigger.get("action_timing", "")
                event = trigger.get("event_manipulation", "")
                statement = trigger.get("action_statement", "")

                md += f"### {trigger_name}\n\n"
                md += f"- **Timing:** {timing}\n"
                md += f"- **Event:** {event}\n"
                md += f"- **Statement:** `{statement}`\n\n"
        else:
            md += "*No triggers defined*\n"

        return md

    def _generate_enums_markdown(self, enums: dict[str, list[str]]) -> str:
        """Generate markdown documentation for enums."""
        md = "# Enums\n\n"

        if not enums:
            md += "*No enums defined*\n"
            return md

        for enum_name, values in sorted(enums.items()):
            md += f"## {enum_name}\n\n"
            md += "Values:\n"
            for value in values:
                md += f"- `{value}`\n"
            md += "\n"

        return md

    def _generate_overview_markdown(self, metrics: dict[str, Any]) -> str:
        """Generate overview markdown."""
        md = "# Database Schema Overview\n\n"
        md += f"*Generated: {datetime.now().isoformat()}*\n\n"

        # Summary
        md += "## Summary\n\n"
        md += f"- **Tables:** {len(metrics['tables'])}\n"
        md += f"- **Total Columns:** {metrics['total_columns']}\n"
        md += f"- **Total Indexes:** {metrics['total_indexes']}\n"
        md += f"- **Total Constraints:** {metrics['total_constraints']}\n"
        md += f"- **Enums:** {len(metrics['enums'])}\n"
        md += f"- **Extensions:** {len(metrics['extensions'])}\n\n"

        # Extensions
        md += "## Installed Extensions\n\n"
        for ext in metrics["extensions"]:
            ext_name = ext.get("extname", "")
            ext_version = ext.get("extversion", "")
            md += f"- {ext_name} ({ext_version})\n"

        # Table details
        md += "\n## Tables\n\n"
        md += "| Table | Columns | Constraints | Indexes | Triggers |\n"
        md += "|-------|---------|-------------|---------|----------|\n"

        for table_name, table_metrics in sorted(metrics["tables"].items()):
            md += f"| [{table_name}]({table_name}.md) | "
            md += f"{table_metrics['columns']} | "
            md += f"{table_metrics['constraints']} | "
            md += f"{table_metrics['indexes']} | "
            md += f"{table_metrics['triggers']} |\n"

        return md


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Query database schema using MCP")
    parser.add_argument("--project-id", help="Supabase project ID")
    parser.add_argument("--export-docs", metavar="DIR", help="Export schema documentation to directory")
    parser.add_argument("--analyze", action="store_true", help="Analyze schema complexity")
    parser.add_argument("--list-tables", action="store_true", help="List all tables")
    parser.add_argument("--list-enums", action="store_true", help="List all enums")

    args = parser.parse_args()

    query = MCPSchemaQuery(project_id=args.project_id)

    if args.export_docs:
        await query.export_schema_documentation(args.export_docs)

    elif args.analyze:
        metrics = await query.analyze_schema_complexity()
        print(json.dumps(metrics, indent=2))

    elif args.list_tables:
        tables = await query.list_tables()
        for table in tables:
            print(table.get("table_name", ""))

    elif args.list_enums:
        enums = await query.get_all_enums()
        for enum_name, values in sorted(enums.items()):
            print(f"{enum_name}: {', '.join(values)}")

    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
