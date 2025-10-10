"""Consolidated, agent-optimized tools for atoms_fastmcp."""

# Support both package and standalone imports
try:
    from .entity import entity_operation
    from .query import data_query
    from .relationship import relationship_operation
    from .workflow import workflow_execute
    from .workspace import workspace_operation
except ImportError:
    from tools.entity import entity_operation
    from tools.query import data_query
    from tools.relationship import relationship_operation
    from tools.workflow import workflow_execute
    from tools.workspace import workspace_operation

__all__ = [
    "data_query",
    "entity_operation",
    "relationship_operation",
    "workflow_execute",
    "workspace_operation"
]
