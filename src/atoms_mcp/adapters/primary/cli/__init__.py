"""
CLI adapter for Atoms.

This package provides a modern command-line interface using Typer.
It replaces the old CLI files with a unified, well-structured system.
"""

from .commands import app, main
from .formatters import (
    EntityFormatter,
    RelationshipFormatter,
    StatsFormatter,
    WorkflowFormatter,
)
from .handlers import CLIHandlers

__all__ = [
    "app",
    "main",
    "CLIHandlers",
    "EntityFormatter",
    "RelationshipFormatter",
    "WorkflowFormatter",
    "StatsFormatter",
]
