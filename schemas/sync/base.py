#!/usr/bin/env python3
"""
Schema Synchronization Base Classes and Utilities

This module contains:
- Base classes for schema synchronization
- Database connection utilities
- Color utilities for terminal output
"""

import os
import sys
from pathlib import Path
from typing import Any

# Ensure repo root is on sys.path for script/CLI invocations
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Load environment variables from .env file
from dotenv import load_dotenv

load_dotenv()

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


class SchemaSyncBase:
    """Base class for schema synchronization functionality."""

    def __init__(self, project_id: str | None = None, db_url: str | None = None):
        self.project_id = project_id or os.getenv("SUPABASE_PROJECT_ID")
        self.root_dir = ROOT_DIR
        self.schemas_dir = self.root_dir / "schemas"
        self.db_schema: dict[str, Any] = {}
        self.local_schema: dict[str, Any] = {}
        self.differences: list[Any] = []
        self._db_url = db_url

    def _get_db_url(self) -> str:
        """Lazily resolve and cache the database URL."""
        if not self._db_url:
            self._db_url = resolve_db_url()
        return self._db_url

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
                        {"column_name": "description", "data_type": "text", "is_nullable": "YES", "udt_name": "text"},
                        {"column_name": "organization_id", "data_type": "uuid", "is_nullable": "NO", "udt_name": "uuid"},
                        {"column_name": "status", "data_type": "USER-DEFINED", "is_nullable": "NO", "udt_name": "project_status"},
                    ]
                },
                "users": {
                    "columns": [
                        {"column_name": "id", "data_type": "uuid", "is_nullable": "NO", "udt_name": "uuid"},
                        {"column_name": "email", "data_type": "text", "is_nullable": "NO", "udt_name": "text"},
                        {"column_name": "name", "data_type": "text", "is_nullable": "YES", "udt_name": "text"},
                        {"column_name": "role", "data_type": "USER-DEFINED", "is_nullable": "NO", "udt_name": "user_role"},
                    ]
                }
            },
            "enums": {
                "organization_type": ["individual", "company", "nonprofit"],
                "billing_plan": ["free", "basic", "premium", "enterprise"],
                "project_status": ["draft", "active", "completed", "archived"],
                "user_role": ["admin", "member", "viewer"]
            }
        }
