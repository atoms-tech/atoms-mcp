"""Backward-compatible import shim for Supabase client helpers.

Projects should import from ``db_kit.supabase_client`` directly; this module
exists to preserve older local imports.
"""

from db_kit.supabase_client import MissingSupabaseConfig, get_supabase

__all__ = ["MissingSupabaseConfig", "get_supabase"]
