"""Context manager for MCP session state.

Provides utilities to access and manage session context (workspace, user, etc.)
that persists across MCP calls within a session.
"""

from __future__ import annotations

import logging
from typing import Optional, Any, Dict
from contextvars import ContextVar

logger = logging.getLogger(__name__)

# Context variables for current session/user/workspace/project/entity
_session_id_var: ContextVar[Optional[str]] = ContextVar("session_id", default=None)
_user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)
_workspace_id_var: ContextVar[Optional[str]] = ContextVar("workspace_id", default=None)
_project_id_var: ContextVar[Optional[str]] = ContextVar("project_id", default=None)
_organization_id_var: ContextVar[Optional[str]] = ContextVar("organization_id", default=None)
_entity_type_var: ContextVar[Optional[str]] = ContextVar("entity_type", default=None)
_parent_id_var: ContextVar[Optional[str]] = ContextVar("parent_id", default=None)
_document_id_var: ContextVar[Optional[str]] = ContextVar("document_id", default=None)  # Phase 1: Extended context


class SessionContext:
    """Thread-safe context manager for session state."""

    def __init__(self):
        """Initialize context manager with operation memory (Phase 4)."""
        self.session_manager = None
        # In-memory operation history (cleared on session end)
        self._operation_history: list[Dict[str, Any]] = []
        self._last_created_entities: Dict[str, Any] = {}  # entity_type -> {id, data}
        self._pagination_state: Dict[str, Any] = {}  # entity_type -> {limit, offset, total}

    def set_session_manager(self, session_manager: Any) -> None:
        """Set the session manager instance (for loading/saving context).

        Args:
            session_manager: SessionManager instance from auth.session_manager
        """
        self.session_manager = session_manager

    def set_session_id(self, session_id: str) -> None:
        """Set current session ID in context.

        Args:
            session_id: Session identifier
        """
        _session_id_var.set(session_id)

    def get_session_id(self) -> Optional[str]:
        """Get current session ID from context.

        Returns:
            Current session ID or None
        """
        return _session_id_var.get()

    def set_user_id(self, user_id: str) -> None:
        """Set current user ID in context.

        Args:
            user_id: User identifier
        """
        _user_id_var.set(user_id)

    def get_user_id(self) -> Optional[str]:
        """Get current user ID from context.

        Returns:
            Current user ID or None
        """
        return _user_id_var.get()

    def set_workspace_id(self, workspace_id: str) -> None:
        """Set current workspace ID in context.

        Args:
            workspace_id: Workspace identifier
        """
        _workspace_id_var.set(workspace_id)

    def get_workspace_id(self) -> Optional[str]:
        """Get current workspace ID from context.

        Returns:
            Current workspace ID or None
        """
        return _workspace_id_var.get()

    def set_project_id(self, project_id: str) -> None:
        """Set current project ID in context."""
        _project_id_var.set(project_id)

    def get_project_id(self) -> Optional[str]:
        """Get current project ID from context."""
        return _project_id_var.get()

    def set_organization_id(self, organization_id: str) -> None:
        """Set current organization ID in context."""
        _organization_id_var.set(organization_id)

    def get_organization_id(self) -> Optional[str]:
        """Get current organization ID from context."""
        return _organization_id_var.get()

    def set_entity_type(self, entity_type: str) -> None:
        """Set current entity type in context."""
        _entity_type_var.set(entity_type)

    def get_entity_type(self) -> Optional[str]:
        """Get current entity type from context."""
        return _entity_type_var.get()

    def set_parent_id(self, parent_id: str) -> None:
        """Set current parent ID (for nested entities) in context."""
        _parent_id_var.set(parent_id)

    def get_parent_id(self) -> Optional[str]:
        """Get current parent ID from context."""
        return _parent_id_var.get()

    def set_document_id(self, document_id: str) -> None:
        """Set current document ID in context. (Phase 1: Extended context)"""
        _document_id_var.set(document_id)

    def get_document_id(self) -> Optional[str]:
        """Get current document ID from context. (Phase 1: Extended context)"""
        return _document_id_var.get()

    async def resolve_workspace_id(
        self,
        explicit_workspace_id: Optional[str] = None,
    ) -> Optional[str]:
        """Resolve workspace ID from explicit param or session context.

        This is the primary pattern for tools:
        1. If explicit workspace_id provided, use it
        2. If not, check session context
        3. If still not available, return None (caller must handle)

        Args:
            explicit_workspace_id: Explicit workspace_id if provided by user

        Returns:
            Resolved workspace_id or None if not available
        """
        # Explicit param takes priority
        if explicit_workspace_id:
            return explicit_workspace_id

        # Check context
        context_workspace = self.get_workspace_id()
        if context_workspace:
            logger.debug(f"Using workspace from context: {context_workspace}")
            return context_workspace

        # Try to load from session if manager available
        if self.session_manager:
            session_id = self.get_session_id()
            if session_id:
                try:
                    workspace_id = await self.session_manager.get_workspace_context(
                        session_id
                    )
                    if workspace_id:
                        logger.debug(
                            f"Loaded workspace from session: {workspace_id}"
                        )
                        self.set_workspace_id(workspace_id)
                        return workspace_id
                except Exception as e:
                    logger.warning(f"Failed to load workspace from session: {e}")

        return None

    def resolve_project_id(self, explicit_project_id: Optional[str] = None) -> Optional[str]:
        """Resolve project ID from explicit param or context.
        
        Args:
            explicit_project_id: Explicit project_id if provided
            
        Returns:
            Resolved project_id or None if not available
        """
        if explicit_project_id:
            return explicit_project_id
        return self.get_project_id()

    def resolve_organization_id(self, explicit_org_id: Optional[str] = None) -> Optional[str]:
        """Resolve organization ID from explicit param or context."""
        if explicit_org_id:
            return explicit_org_id
        return self.get_organization_id()

    def resolve_entity_type(self, explicit_type: Optional[str] = None) -> Optional[str]:
        """Resolve entity type from explicit param or context."""
        if explicit_type:
            return explicit_type
        return self.get_entity_type()

    def resolve_parent_id(self, explicit_parent_id: Optional[str] = None) -> Optional[str]:
        """Resolve parent ID from explicit param or context."""
        if explicit_parent_id:
            return explicit_parent_id
        return self.get_parent_id()

    def resolve_document_id(self, explicit_document_id: Optional[str] = None) -> Optional[str]:
        """Resolve document ID from explicit param or context. (Phase 1: Extended context)"""
        if explicit_document_id:
            return explicit_document_id
        return self.get_document_id()

    async def load_workspace_from_session(self) -> Optional[str]:
        """Load workspace context from session storage.

        This is called when starting an operation with a session ID.
        It pre-loads the workspace context so subsequent operations
        don't need to fetch it repeatedly.

        Returns:
            Workspace ID if found in session, None otherwise
        """
        if not self.session_manager:
            return None

        session_id = self.get_session_id()
        if not session_id:
            return None

        try:
            workspace_id = await self.session_manager.get_workspace_context(
                session_id
            )
            if workspace_id:
                self.set_workspace_id(workspace_id)
                logger.debug(f"Loaded workspace context: {workspace_id}")
            return workspace_id
        except Exception as e:
            logger.warning(f"Failed to load workspace from session: {e}")
            return None

    # Phase 4: Operation Memory & Smart Defaults
    def record_operation(self, operation: str, entity_type: str, result: Dict[str, Any]) -> None:
        """Record an operation in history for potential undo/redo.

        Args:
            operation: Operation type (create, update, delete, etc.)
            entity_type: Type of entity
            result: Operation result with entity_id and data
        """
        try:
            import datetime
            record = {
                "operation": operation,
                "entity_type": entity_type,
                "entity_id": result.get("entity_id"),
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "success": result.get("success", True)
            }
            self._operation_history.append(record)
            
            # Keep only last 50 operations in memory
            if len(self._operation_history) > 50:
                self._operation_history = self._operation_history[-50:]
            
            # If successful create, record as last created (for auto-parent)
            if operation == "create" and result.get("success"):
                self._last_created_entities[entity_type] = {
                    "id": result.get("entity_id"),
                    "data": result.get("data", {}),
                    "timestamp": record["timestamp"]
                }
        except Exception as e:
            logger.debug(f"Failed to record operation: {e}")

    def get_last_created_entity(self, entity_type: str) -> Optional[Dict[str, Any]]:
        """Get the last created entity of a given type (Phase 4: Smart Defaults).

        Useful for auto-parent in nested operations.

        Args:
            entity_type: Type of entity to get

        Returns:
            Last created entity info {id, data, timestamp} or None
        """
        return self._last_created_entities.get(entity_type)

    def set_pagination_state(self, entity_type: str, limit: int, offset: int, total: int) -> None:
        """Track pagination state for convenience in subsequent calls (Phase 4).

        Args:
            entity_type: Type of entity being paginated
            limit: Page size
            offset: Current offset
            total: Total results
        """
        try:
            self._pagination_state[entity_type] = {
                "limit": limit,
                "offset": offset,
                "total": total,
                "has_next": (offset + limit) < total,
                "has_previous": offset > 0,
                "current_page": (offset // limit) + 1 if limit > 0 else 1,
                "total_pages": (total + limit - 1) // limit if limit > 0 else 1
            }
        except Exception as e:
            logger.debug(f"Failed to record pagination state: {e}")

    def get_pagination_state(self, entity_type: str) -> Optional[Dict[str, Any]]:
        """Get tracked pagination state for an entity type (Phase 4).

        Args:
            entity_type: Type of entity

        Returns:
            Pagination state {limit, offset, total, has_next, has_previous, ...} or None
        """
        return self._pagination_state.get(entity_type)

    def get_next_page_offset(self, entity_type: str) -> Optional[int]:
        """Get offset for next page based on tracked pagination state (Phase 4).

        Args:
            entity_type: Type of entity

        Returns:
            Offset for next page, or None if no next page or no tracked state
        """
        state = self.get_pagination_state(entity_type)
        if state and state.get("has_next"):
            return state.get("offset", 0) + state.get("limit", 20)
        return None

    def get_operation_history(self, limit: int = 20) -> list[Dict[str, Any]]:
        """Get recent operation history (Phase 4: Smart Defaults).

        Args:
            limit: Maximum number of operations to return

        Returns:
            List of recent operations
        """
        return self._operation_history[-limit:] if limit > 0 else self._operation_history

    def clear(self) -> None:
        """Clear all context variables and operation memory (Phase 4)."""
        _session_id_var.set(None)
        _user_id_var.set(None)
        _workspace_id_var.set(None)
        _project_id_var.set(None)
        _organization_id_var.set(None)
        _entity_type_var.set(None)
        _parent_id_var.set(None)
        _document_id_var.set(None)  # Phase 1: Extended context
        # Clear operation memory on session end
        self._operation_history.clear()
        self._last_created_entities.clear()
        self._pagination_state.clear()
        logger.debug("Cleared session context")


# Global context instance
_context = SessionContext()


def get_context() -> SessionContext:
    """Get the global session context manager.

    Returns:
        SessionContext instance
    """
    return _context


def resolve_workspace_id(explicit_workspace_id: Optional[str] = None) -> Optional[str]:
    """Synchronous helper to resolve workspace ID from context.

    For async contexts, use context.resolve_workspace_id() instead.

    Args:
        explicit_workspace_id: Explicit workspace_id if provided

    Returns:
        Resolved workspace_id or None
    """
    if explicit_workspace_id:
        return explicit_workspace_id
    return _context.get_workspace_id()
