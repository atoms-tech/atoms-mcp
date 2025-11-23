"""Context management tool for MCP sessions.

Provides operations to manage session state including:
- Setting/getting current workspace context
- Listing available workspaces for user
- Clearing context

This tool enables agents to set workspace context once and have it
automatically applied to all subsequent operations.
"""

from __future__ import annotations

import logging
from typing import Optional, Dict, Any

from services.context_manager import get_context

logger = logging.getLogger(__name__)


class ContextTool:
    """Tool for managing MCP session context."""

    def __init__(self):
        """Initialize context tool."""
        self.context = get_context()

    async def set_workspace(self, workspace_id: str) -> Dict[str, Any]:
        """Set the current workspace for this session.

        Once set, all subsequent operations will use this workspace
        unless explicitly overridden with a workspace_id parameter.

        Args:
            workspace_id: ID of the workspace to set as current

        Returns:
            Dict with success status and current workspace info
        """
        try:
            # Validate workspace_id format (basic check)
            if not workspace_id or not isinstance(workspace_id, str):
                return {
                    "success": False,
                    "error": "workspace_id must be a non-empty string",
                }

            # Set in both context and session
            self.context.set_workspace_id(workspace_id)

            session_id = self.context.get_session_id()
            if session_id and self.context.session_manager:
                success = await self.context.session_manager.set_workspace_context(
                    session_id, workspace_id
                )
                if not success:
                    return {
                        "success": False,
                        "error": f"Failed to persist workspace context to session {session_id}",
                    }

            logger.info(f"✅ Set workspace context: {workspace_id}")
            return {
                "success": True,
                "message": f"Workspace context set to {workspace_id}",
                "workspace_id": workspace_id,
            }

        except Exception as e:
            logger.error(f"❌ Failed to set workspace: {e}")
            return {
                "success": False,
                "error": f"Failed to set workspace: {str(e)}",
            }

    async def get_workspace(self) -> Dict[str, Any]:
        """Get the current workspace context for this session.

        Returns:
            Dict with current workspace_id or None if not set
        """
        try:
            workspace_id = await self.context.resolve_workspace_id()

            if workspace_id:
                logger.info(f"✅ Current workspace: {workspace_id}")
                return {
                    "success": True,
                    "workspace_id": workspace_id,
                    "message": f"Current workspace: {workspace_id}",
                }
            else:
                logger.debug("No workspace context currently set")
                return {
                    "success": True,
                    "workspace_id": None,
                    "message": "No workspace context set. Use set_workspace to set one.",
                }

        except Exception as e:
            logger.error(f"❌ Failed to get workspace: {e}")
            return {
                "success": False,
                "error": f"Failed to get workspace: {str(e)}",
            }

    async def clear_workspace(self) -> Dict[str, Any]:
        """Clear the current workspace context for this session.

        After calling this, operations will require explicit workspace_id
        parameters or will fail if workspace context is required.

        Returns:
            Dict with success status
        """
        try:
            session_id = self.context.get_session_id()
            if session_id and self.context.session_manager:
                success = await self.context.session_manager.clear_workspace_context(
                    session_id
                )
                if not success:
                    logger.warning(
                        f"Failed to clear workspace in session {session_id}"
                    )

            self.context.set_workspace_id(None)

            logger.info("✅ Cleared workspace context")
            return {
                "success": True,
                "message": "Workspace context cleared",
            }

        except Exception as e:
            logger.error(f"❌ Failed to clear workspace: {e}")
            return {
                "success": False,
                "error": f"Failed to clear workspace: {str(e)}",
            }

    async def get_session_state(self) -> Dict[str, Any]:
        """Get current session state (debugging/info only).

        Returns:
            Dict with session state information
        """
        try:
            session_id = self.context.get_session_id()
            user_id = self.context.get_user_id()
            workspace_id = self.context.get_workspace_id()

            # Try to load from session if available
            if not workspace_id and session_id and self.context.session_manager:
                try:
                    workspace_id = (
                        await self.context.session_manager.get_workspace_context(
                            session_id
                        )
                    )
                except Exception as e:
                    logger.debug(f"Could not load workspace from session: {e}")

            return {
                "success": True,
                "session_id": session_id,
                "user_id": user_id,
                "workspace_id": workspace_id,
            }

        except Exception as e:
            logger.error(f"❌ Failed to get session state: {e}")
            return {
                "success": False,
                "error": f"Failed to get session state: {str(e)}",
            }


# Global context tool instance
_context_tool: Optional[ContextTool] = None


def get_context_tool() -> ContextTool:
    """Get or create the global context tool instance.

    Returns:
        ContextTool instance
    """
    global _context_tool
    if _context_tool is None:
        _context_tool = ContextTool()
    return _context_tool
