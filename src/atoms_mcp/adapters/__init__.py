"""
Adapters layer for Atoms MCP.

This layer implements the hexagonal architecture adapters:
- Primary adapters: Entry points (MCP server, CLI)
- Secondary adapters: External dependencies (repositories, cache, logger)
"""

from . import primary

__all__ = ["primary"]
