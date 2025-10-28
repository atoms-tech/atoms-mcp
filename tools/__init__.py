"""Consolidated, agent-optimized tools for atoms_fastmcp."""

# Try to import tool functions with fallback for missing modules
import contextlib

__all__ = [
    "data_query",
    "entity_operation",
    "relationship_operation",
    "workflow_execute",
    "workspace_operation"
]

# Initialize functions to None for graceful fallback
data_query = None
entity_operation = None
relationship_operation = None
workflow_execute = None
workspace_operation = None

# Try to import each tool module independently
with contextlib.suppress(ImportError):
    from .entity import entity_operation

with contextlib.suppress(ImportError):
    from .query import data_query

with contextlib.suppress(ImportError):
    from .relationship import relationship_operation

with contextlib.suppress(ImportError):
    from .workflow import workflow_execute

with contextlib.suppress(ImportError):
    from .workspace import workspace_operation
