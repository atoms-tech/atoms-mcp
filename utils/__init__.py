"""
Atoms MCP Utilities

Provides logging and adapter utilities for Atoms MCP server.
"""

import importlib

from .logging_setup import get_logger, setup_logging


# Lazy import for mcp_adapter to avoid requiring mcp_qa in production
def create_atoms_adapter(*args, **kwargs):
    """Create Atoms MCP adapter (lazy import)."""
    module = importlib.import_module("utils.mcp_adapter")
    return module.create_atoms_adapter(*args, **kwargs)

__all__ = [
    "create_atoms_adapter",
    "get_logger",
    "setup_logging",
]
