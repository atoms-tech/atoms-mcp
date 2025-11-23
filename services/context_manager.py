"""Context manager for MCP session state.

Provides utilities to access and manage session context (workspace, user, etc.)
that persists across MCP calls within a session.
"""

from __future__ import annotations

import logging
from typing import Optional, Any, Dict
from contextvars import ContextVar

logger = logging.getLogger(__name__)

# Context variables for current session/user/workspace
_session_id_var: ContextVar[Optional[str]] = ContextVar("session_id", default=None)
_user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)
_workspace_id_var: ContextVar[Optional[str]] = ContextVar("workspace_id", default=None)


class SessionContext:
    """Thread-safe context manager for session state."""

    def __init__(self):
        """Initialize context manager."""
        self.session_manager = None

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

    def clear(self) -> None:
        """Clear all context variables."""
        _session_id_var.set(None)
        _user_id_var.set(None)
        _workspace_id_var.set(None)
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
