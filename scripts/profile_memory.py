#!/usr/bin/env python3
"""
Memory profiling script.

Run with: python -m memory_profiler scripts/profile_memory.py
"""

from memory_profiler import profile


@profile
def load_server():
    """Load server module."""
    from server import app
    return app


@profile
def load_schema_sync():
    """Load schema sync."""
    from lib.schema_sync import SchemaSync
    return SchemaSync()


@profile
def load_deployment_checker():
    """Load deployment checker."""
    from lib.deployment_checker import DeploymentChecker
    return DeploymentChecker()


def main():
    """Run all profiling."""
    print("=" * 70)
    print("Memory Profiling - Atoms MCP")
    print("=" * 70)
    print()

    print("1. Loading server...")
    load_server()
    print()

    print("2. Loading schema sync...")
    load_schema_sync()
    print()

    print("3. Loading deployment checker...")
    load_deployment_checker()
    print()

    print("=" * 70)
    print("Profiling complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
