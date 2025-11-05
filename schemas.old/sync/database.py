"""
Database operations for schema synchronization.

This module contains database-specific operations for querying and managing
database schemas, including Supabase integration and mock data generation.
"""

from typing import Any

import psycopg2

from .base import Colors, resolve_db_url


class DatabaseOperations:
    """Handles database operations for schema synchronization."""

    def __init__(self, db_url: str | None = None):
        self._db_url = db_url

    def _get_db_url(self) -> str:
        """Lazily resolve and cache the database URL."""
        if not self._db_url:
            self._db_url = resolve_db_url()
        return self._db_url

    def get_supabase_schema(self) -> dict[str, Any]:
        """Query Supabase for current database schema via direct psycopg2."""
        try:
            conn = psycopg2.connect(self._get_db_url())
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

            schema: dict[str, Any] = {"tables": {}, "enums": {}}

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
                            "udt_name": col[4],
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
        except Exception as e:
            print(f"{Colors.RED}Error querying Supabase schema: {e}{Colors.END}")
            print(f"{Colors.YELLOW}Falling back to mock schema for demo{Colors.END}")
            return self._get_mock_schema()
        else:
            return schema

    def _get_mock_schema(self) -> dict[str, Any]:
        """Return a mock schema for demonstration."""
        return {
            "tables": {
                "organizations": {
                    "columns": [
                        {"column_name": "id", "data_type": "uuid", "is_nullable": "NO", "udt_name": "uuid"},
                        {"column_name": "name", "data_type": "text", "is_nullable": "NO", "udt_name": "text"},
                        {
                            "column_name": "type",
                            "data_type": "USER-DEFINED",
                            "is_nullable": "NO",
                            "udt_name": "organization_type",
                        },
                        {
                            "column_name": "billing_plan",
                            "data_type": "USER-DEFINED",
                            "is_nullable": "NO",
                            "udt_name": "billing_plan",
                        },
                    ]
                },
                "projects": {
                    "columns": [
                        {"column_name": "id", "data_type": "uuid", "is_nullable": "NO", "udt_name": "uuid"},
                        {"column_name": "name", "data_type": "text", "is_nullable": "NO", "udt_name": "text"},
                        {
                            "column_name": "organization_id",
                            "data_type": "uuid",
                            "is_nullable": "NO",
                            "udt_name": "uuid",
                        },
                        {
                            "column_name": "status",
                            "data_type": "USER-DEFINED",
                            "is_nullable": "NO",
                            "udt_name": "project_status",
                        },
                    ]
                },
                "users": {
                    "columns": [
                        {"column_name": "id", "data_type": "uuid", "is_nullable": "NO", "udt_name": "uuid"},
                        {"column_name": "email", "data_type": "text", "is_nullable": "NO", "udt_name": "text"},
                        {"column_name": "name", "data_type": "text", "is_nullable": "YES", "udt_name": "text"},
                        {
                            "column_name": "created_at",
                            "data_type": "timestamp with time zone",
                            "is_nullable": "NO",
                            "udt_name": "timestamptz",
                        },
                    ]
                },
            },
            "enums": {
                "organization_type": ["enterprise", "startup", "individual"],
                "billing_plan": ["free", "pro", "enterprise"],
                "project_status": ["active", "inactive", "archived"],
            },
        }
