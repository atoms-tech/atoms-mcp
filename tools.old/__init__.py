"""Consolidated, agent-optimized tools for atoms_fastmcp."""

# Try to import tool functions with fallback for missing modules
import contextlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine
    from typing import Any, Literal

    data_query: Callable[..., Coroutine[Any, Any, dict[str, Any]]] | None = None
    entity_operation: Callable[..., Coroutine[Any, Any, dict[str, Any]]] | None = None
    relationship_operation: Callable[..., Coroutine[Any, Any, dict[str, Any]]] | None = None
    workflow_execute: Callable[..., Coroutine[Any, Any, dict[str, Any]]] | None = None
    workspace_operation: Callable[..., Coroutine[Any, Any, dict[str, Any]]] | None = None
else:
    __all__ = ["data_query", "entity_operation", "relationship_operation", "workflow_execute", "workspace_operation"]

    # Initialize functions to None for graceful fallback
    data_query = None
    entity_operation = None
    relationship_operation = None
    workflow_execute = None
    workspace_operation = None

# Try to import each tool module independently
with contextlib.suppress(ImportError):
    if entity_operation is None:
        from .entity.entity import entity_operation

with contextlib.suppress(ImportError):
    if data_query is None:
        from .query import data_query

with contextlib.suppress(ImportError):
    if relationship_operation is None:
        from .entity.relationship import relationship_operation

with contextlib.suppress(ImportError):
    if workflow_execute is None:
        from .workflow.workflow import workflow_execute

with contextlib.suppress(ImportError):
    if workspace_operation is None:
        from .workflow.workspace import workspace_operation
