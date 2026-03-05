"""
Supabase adapter module.

This module provides Supabase-based implementations of the repository
pattern for data persistence.
"""

from atoms_mcp.adapters.secondary.supabase.connection import (
    SupabaseConnection,
    SupabaseConnectionError,
    get_client,
    get_client_with_retry,
    get_connection,
    reset_connection,
)
from atoms_mcp.adapters.secondary.supabase.repository import SupabaseRepository

__all__ = [
    "SupabaseConnection",
    "SupabaseConnectionError",
    "SupabaseRepository",
    "get_client",
    "get_client_with_retry",
    "get_connection",
    "reset_connection",
]
