"""
FastMCP adapter for Atoms.

This package provides the MCP server implementation using FastMCP SDK.
It registers all tools and handles protocol communication.
"""

from .server import AtomsServer, create_server, main

__all__ = ["AtomsServer", "create_server", "main"]
