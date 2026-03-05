"""
Primary adapters for Atoms MCP.

Primary adapters are entry points that receive external requests:
- MCP server: FastMCP protocol server
- CLI: Command-line interface

These adapters call application layer commands/queries and format responses.
"""

from . import cli, mcp

__all__ = ["mcp", "cli"]
