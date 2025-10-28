#!/usr/bin/env python3
"""
Backward-compatible entrypoint for schema synchronization utilities.

Historically the SchemaSync implementation lived here. The actual implementation
now resides in `schemas.sync.core`, and this module simply re-exports the public
API so existing imports (e.g., scripts/profile_memory.py) continue to work.
"""

from schemas.sync.core import Colors, SchemaSync, main, resolve_db_url

__all__ = ["Colors", "SchemaSync", "main", "resolve_db_url"]


if __name__ == "__main__":
    main()
