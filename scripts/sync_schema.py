#!/usr/bin/env python3
"""
Thin CLI shim preserved for backwards compatibility.

The full SchemaSync implementation now lives in `schemas.sync.core`. This script
re-exports the primary class so existing imports keep working and forwards CLI
execution to the shared entrypoint.
"""

from schemas.sync.core import Colors, SchemaSync, main

__all__ = ["Colors", "SchemaSync", "main"]


if __name__ == "__main__":
    main()
