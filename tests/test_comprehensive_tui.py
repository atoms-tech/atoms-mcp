#!/usr/bin/env python3
"""
Atoms MCP Test Suite - TUI Mode

Interactive terminal dashboard with:
- Live test execution display
- Real-time progress updates
- Auto-reload on file changes
- Interactive filtering and navigation
- Keyboard shortcuts for common actions

Usage:
    python tests/test_comprehensive_tui.py
    python tests/test_comprehensive_tui.py --no-live-reload
    python tests/test_comprehensive_tui.py --watch tools/ tests/
"""

import os
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.framework.tui import run_tui_dashboard

# Configuration
MCP_ENDPOINT = os.getenv("MCP_ENDPOINT", "https://mcp.atoms.tech/api/mcp")

# Test modules to load
TEST_MODULES = [
    # Basic tests
    "tests.test_workspace",
    "tests.test_entity",
    "tests.test_query",
    "tests.test_relationship",
    "tests.test_workflow",
    # Comprehensive tests
    "tests.test_workspace_comprehensive",
    "tests.test_entity_comprehensive",
    "tests.test_query_comprehensive",
    "tests.test_relationship_comprehensive",
    "tests.test_workflow_comprehensive",
    # Integration tests
    "tests.test_user_stories",
]


def main():
    """Launch TUI dashboard."""
    import argparse

    parser = argparse.ArgumentParser(description="Atoms MCP Test Suite - TUI Mode")
    parser.add_argument("--endpoint", default=MCP_ENDPOINT, help="MCP endpoint URL")
    parser.add_argument("--no-live-reload", action="store_true", help="Disable auto-reload on file changes")
    parser.add_argument("--watch", nargs="+", default=["tools/"], help="Paths to watch for changes")

    args = parser.parse_args()

    print("=" * 80)
    print("🎨 ATOMS MCP TEST SUITE - TUI MODE")
    print("=" * 80)
    print()
    print("Starting interactive test dashboard...")
    print(f"Endpoint: {args.endpoint}")
    print(f"Live Reload: {'Enabled' if not args.no_live_reload else 'Disabled'}")
    print()
    print("Keyboard Shortcuts:")
    print("  r - Run tests")
    print("  c - Clear test cache")
    print("  o - Clear OAuth cache")
    print("  l - Toggle live reload")
    print("  f - Filter tests")
    print("  q - Quit")
    print()
    print("Starting dashboard...")
    print("=" * 80)

    try:
        run_tui_dashboard(
            endpoint=args.endpoint,
            test_modules=TEST_MODULES,
            enable_live_reload=not args.no_live_reload,
            watch_paths=args.watch,
        )
    except ImportError as e:
        print()
        print("❌ Required dependencies not installed")
        print()
        print("Install with:")
        print("  pip install textual rich watchdog")
        print()
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
