#!/usr/bin/env python3
"""
Query Database Schema using Supabase MCP Tools

This script demonstrates how to query the database schema
using the Supabase MCP integration.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


async def get_all_tables(project_id: str) -> list[dict[str, Any]]:
    """Get all tables in the public schema using MCP."""
    try:
        # This would use the Supabase MCP list_tables tool
        # For now, we'll simulate the call
        print(f"Querying tables for project: {project_id}")

        # In actual implementation, this would call:
        # result = await mcp_client.call_tool("list_tables", {
        #     "project_id": project_id,
        #     "schemas": ["public"]
        # })

        return []
    except Exception as e:
        print(f"Error getting tables: {e}")
        return []


async def get_table_columns(project_id: str, table_name: str) -> list[dict[str, Any]]:
    """Get columns for a specific table."""
    try:
        # This would execute SQL via MCP
        _sql = f"""
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

        # In actual implementation:
        # result = await mcp_client.call_tool("execute_sql", {
        #     "project_id": project_id,
        #     "query": sql
        # })

        print(f"  Querying columns for table: {table_name}")
        return []
    except Exception as e:
        print(f"Error getting columns for {table_name}: {e}")
        return []


async def get_all_enums(project_id: str) -> dict[str, list[str]]:
    """Get all enum types and their values."""
    try:
        _sql = """
            SELECT
                t.typname as enum_name,
                array_agg(e.enumlabel ORDER BY e.enumsortorder) as enum_values
            FROM pg_type t
            JOIN pg_enum e ON t.oid = e.enumtypid
            WHERE t.typtype = 'e'
            GROUP BY t.typname
            ORDER BY t.typname;
        """

        # In actual implementation:
        # result = await mcp_client.call_tool("execute_sql", {
        #     "project_id": project_id,
        #     "query": sql
        # })

        print("Querying enum types...")
        return {}
    except Exception as e:
        print(f"Error getting enums: {e}")
        return {}


async def get_table_constraints(project_id: str, table_name: str) -> list[dict[str, Any]]:
    """Get constraints for a table (foreign keys, unique, etc)."""
    try:
        _sql = f"""
            SELECT
                tc.constraint_name,
                tc.constraint_type,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            LEFT JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.table_schema = 'public'
            AND tc.table_name = '{table_name}';
        """

        print(f"  Querying constraints for table: {table_name}")
        return []
    except Exception as e:
        print(f"Error getting constraints for {table_name}: {e}")
        return []


async def get_table_indexes(project_id: str, table_name: str) -> list[dict[str, Any]]:
    """Get indexes for a table."""
    try:
        _sql = f"""
            SELECT
                indexname,
                indexdef
            FROM pg_indexes
            WHERE schemaname = 'public'
            AND tablename = '{table_name}';
        """

        print(f"  Querying indexes for table: {table_name}")
        return []
    except Exception as e:
        print(f"Error getting indexes for {table_name}: {e}")
        return []


async def export_schema_to_json(project_id: str, output_file: str):
    """Export full schema to JSON file."""
    schema = {
        "tables": {},
        "enums": {},
        "metadata": {
            "project_id": project_id,
            "exported_at": None,  # Would be datetime.now().isoformat()
        }
    }

    # Get enums
    enums = await get_all_enums(project_id)
    schema["enums"] = enums

    # Get tables
    tables = await get_all_tables(project_id)

    for table in tables:
        table_name = table.get("table_name")
        if not table_name:
            continue

        columns = await get_table_columns(project_id, table_name)
        constraints = await get_table_constraints(project_id, table_name)
        indexes = await get_table_indexes(project_id, table_name)

        schema["tables"][table_name] = {
            "columns": columns,
            "constraints": constraints,
            "indexes": indexes,
        }

    # Write to file
    output_path = Path(output_file)
    with open(output_path, "w") as f:
        json.dump(schema, f, indent=2)

    print(f"\nSchema exported to: {output_path}")
    print(f"  Tables: {len(schema['tables'])}")
    print(f"  Enums: {len(schema['enums'])}")


async def compare_with_local_schema():
    """Compare database schema with local Python schemas."""
    # Import local schemas
    from schemas.database import entities

    from schemas import enums

    print("\nComparing with local schemas...")

    # Get local enum classes
    local_enums = []
    for name in dir(enums):
        obj = getattr(enums, name)
        if isinstance(obj, type) and issubclass(obj, enums.Enum) and obj != enums.Enum:
            if not name.startswith("_"):
                local_enums.append(name)

    print(f"  Local enums: {len(local_enums)}")

    # Get local table definitions
    local_tables = []
    for name in dir(entities):
        if name.endswith("Row"):
            local_tables.append(name)

    print(f"  Local tables: {len(local_tables)}")


async def main():
    """Main entry point."""
    project_id = os.getenv("SUPABASE_PROJECT_ID")

    if not project_id:
        print("Error: SUPABASE_PROJECT_ID environment variable not set")
        sys.exit(1)

    print(f"Querying schema for project: {project_id}\n")

    # Example: Export schema to JSON
    output_file = Path(__file__).parent.parent / "schema_export.json"
    await export_schema_to_json(project_id, str(output_file))

    # Example: Compare with local schema
    await compare_with_local_schema()


if __name__ == "__main__":
    asyncio.run(main())
