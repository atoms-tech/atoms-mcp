"""Consolidated, agent-optimized tools for atoms_fastmcp."""

# Support both package and standalone imports
try:
    from .workspace import workspace_operation
    from .entity import entity_operation
    from .relationship import relationship_operation
    from .workflow import workflow_execute
    from .query import data_query
except ImportError:
    from tools.workspace import workspace_operation
    from tools.entity import entity_operation
    from tools.relationship import relationship_operation
    from tools.workflow import workflow_execute
    from tools.query import data_query

__all__ = [
    "workspace_operation",
    "entity_operation", 
    "relationship_operation",
    "workflow_execute",
    "data_query"
]