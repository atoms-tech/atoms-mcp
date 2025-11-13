"""Atoms MCP - Consolidated MCP server for Atoms platform.

This package re-exports the main modules from the parent package.
"""

# Re-export from parent package
import sys
from pathlib import Path

# Add parent directory to path so we can import the root-level modules
parent = Path(__file__).parent.parent
sys.path.insert(0, str(parent))

__version__ = "0.1.0"


def main():
    """Entry point for the atoms CLI."""
    from cli import main as cli_main
    cli_main()


__all__ = ["main"]
