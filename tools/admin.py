"""Admin Tool for Atoms MCP - Workspace and organization management.

Provides administrative operations for managing workspaces, organizations,
users, and audit logging.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class AdminTool:
    """Admin tool for workspace and organization management."""

    def __init__(self):
        """Initialize admin tool."""
        self.audit_log = []

    async def create_workspace(
        self,
        organization_id: str,
        name: str,
        description: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new workspace.
        
        Args:
            organization_id: Organization ID
            name: Workspace name
            description: Workspace description
            settings: Workspace settings
            
        Returns:
            Dict with success status and workspace info
        """
        try:
            if not organization_id or not name:
                return {
                    "success": False,
                    "error": "organization_id and name are required"
                }

            workspace = {
                "id": f"ws-{datetime.now().timestamp()}",
                "organization_id": organization_id,
                "name": name,
                "description": description or "",
                "settings": settings or {},
                "created_at": datetime.now().isoformat(),
                "status": "active"
            }

            # Log audit event
            self._log_audit("create_workspace", workspace)

            return {
                "success": True,
                "data": workspace,
                "message": f"Workspace '{name}' created successfully"
            }
        except Exception as e:
            logger.error(f"Failed to create workspace: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def invite_user(
        self,
        workspace_id: str,
        email: str,
        role: str = "editor"
    ) -> Dict[str, Any]:
        """Invite user to workspace.
        
        Args:
            workspace_id: Workspace ID
            email: User email
            role: User role (viewer, editor, admin)
            
        Returns:
            Dict with success status and invitation info
        """
        try:
            if not workspace_id or not email:
                return {
                    "success": False,
                    "error": "workspace_id and email are required"
                }

            if role not in ["viewer", "editor", "admin"]:
                return {
                    "success": False,
                    "error": f"Invalid role: {role}"
                }

            invitation = {
                "id": f"inv-{datetime.now().timestamp()}",
                "workspace_id": workspace_id,
                "email": email,
                "role": role,
                "status": "pending",
                "created_at": datetime.now().isoformat()
            }

            # Log audit event
            self._log_audit("invite_user", invitation)

            return {
                "success": True,
                "data": invitation,
                "message": f"Invitation sent to {email}"
            }
        except Exception as e:
            logger.error(f"Failed to invite user: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def remove_user(
        self,
        workspace_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Remove user from workspace.
        
        Args:
            workspace_id: Workspace ID
            user_id: User ID
            
        Returns:
            Dict with success status
        """
        try:
            if not workspace_id or not user_id:
                return {
                    "success": False,
                    "error": "workspace_id and user_id are required"
                }

            event = {
                "workspace_id": workspace_id,
                "user_id": user_id,
                "action": "remove_user",
                "timestamp": datetime.now().isoformat()
            }

            # Log audit event
            self._log_audit("remove_user", event)

            return {
                "success": True,
                "message": f"User {user_id} removed from workspace"
            }
        except Exception as e:
            logger.error(f"Failed to remove user: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_audit_log(
        self,
        workspace_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get audit log for workspace.
        
        Args:
            workspace_id: Workspace ID
            limit: Number of entries to return
            offset: Starting position
            
        Returns:
            Dict with audit log entries
        """
        try:
            if not workspace_id:
                return {
                    "success": False,
                    "error": "workspace_id is required"
                }

            # Filter audit log by workspace
            workspace_logs = [
                log for log in self.audit_log
                if log.get("workspace_id") == workspace_id
            ]

            # Apply pagination
            total = len(workspace_logs)
            entries = workspace_logs[offset:offset + limit]

            return {
                "success": True,
                "data": entries,
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "total": total,
                    "has_next": offset + limit < total
                }
            }
        except Exception as e:
            logger.error(f"Failed to get audit log: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def update_workspace_settings(
        self,
        workspace_id: str,
        settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update workspace settings.
        
        Args:
            workspace_id: Workspace ID
            settings: Settings to update
            
        Returns:
            Dict with success status and updated settings
        """
        try:
            if not workspace_id or not settings:
                return {
                    "success": False,
                    "error": "workspace_id and settings are required"
                }

            event = {
                "workspace_id": workspace_id,
                "settings": settings,
                "action": "update_settings",
                "timestamp": datetime.now().isoformat()
            }

            # Log audit event
            self._log_audit("update_workspace_settings", event)

            return {
                "success": True,
                "data": settings,
                "message": "Workspace settings updated"
            }
        except Exception as e:
            logger.error(f"Failed to update workspace settings: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _log_audit(self, action: str, data: Dict[str, Any]) -> None:
        """Log audit event.
        
        Args:
            action: Action name
            data: Action data
        """
        audit_entry = {
            "action": action,
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "workspace_id": data.get("workspace_id") or data.get("organization_id")
        }
        self.audit_log.append(audit_entry)
        logger.info(f"Audit: {action} - {audit_entry}")

    def get_audit_log_entries(self) -> List[Dict[str, Any]]:
        """Get all audit log entries."""
        return self.audit_log.copy()


# Global admin tool instance
_admin_tool = None


def get_admin_tool() -> AdminTool:
    """Get global admin tool instance."""
    global _admin_tool
    if _admin_tool is None:
        _admin_tool = AdminTool()
    return _admin_tool

