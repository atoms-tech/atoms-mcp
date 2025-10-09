"""Workspace context management tool."""

from __future__ import annotations

from typing import Dict, Any, Optional, Literal

try:
    from .base import ToolBase
except ImportError:
    from tools.base import ToolBase


class WorkspaceManager(ToolBase):
    """Manages workspace context for users."""
    
    def __init__(self):
        super().__init__()
        # In-memory context store (in production, could be Redis/database)
        self._user_contexts: Dict[str, Dict[str, Any]] = {}
    
    async def get_context(self, user_id: str) -> Dict[str, Any]:
        """Get current workspace context for user."""
        return self._user_contexts.get(user_id, {
            "active_organization": None,
            "active_project": None,
            "active_document": None,
            "recent_organizations": [],
            "recent_projects": [],
            "recent_documents": []
        })
    
    async def set_context(
        self,
        user_id: str,
        context_type: str,
        entity_id: str
    ) -> Dict[str, Any]:
        """Set active context for user."""
        if user_id not in self._user_contexts:
            self._user_contexts[user_id] = await self.get_context(user_id)

        context = self._user_contexts[user_id]

        # Validate entity exists before setting context
        table_map = {
            "organization": "organizations",
            "project": "projects",
            "document": "documents"
        }

        if context_type not in table_map:
            raise ValueError(f"Invalid context_type: {context_type}. Must be one of: {list(table_map.keys())}")

        table = table_map[context_type]
        entity = await self._db_get_single(table, filters={"id": entity_id, "is_deleted": False})

        if not entity:
            raise ValueError(f"{context_type.capitalize()} '{entity_id}' not found or has been deleted")

        # Set active context
        if context_type == "organization":
            context["active_organization"] = entity_id
            # Add to recent if not already there
            recent = context["recent_organizations"]
            if entity_id in recent:
                recent.remove(entity_id)
            recent.insert(0, entity_id)
            context["recent_organizations"] = recent[:10]  # Keep last 10
            
        elif context_type == "project":
            context["active_project"] = entity_id
            recent = context["recent_projects"]
            if entity_id in recent:
                recent.remove(entity_id)
            recent.insert(0, entity_id)
            context["recent_projects"] = recent[:10]
            
        elif context_type == "document":
            context["active_document"] = entity_id
            recent = context["recent_documents"]
            if entity_id in recent:
                recent.remove(entity_id)
            recent.insert(0, entity_id)
            context["recent_documents"] = recent[:10]
        
        return context
    
    async def list_workspaces(
        self,
        user_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """List available workspaces for user with pagination.

        Args:
            user_id: User ID to list workspaces for
            limit: Maximum number of results (default: 100, max: 500)
            offset: Number of results to skip (default: 0)

        Returns:
            Dict with organizations, pagination metadata, and user context
        """
        # Enforce max limit
        limit = min(limit, 500)

        # Get total count first
        total_count = await self._db_count(
            "organization_members",
            filters={
                "user_id": user_id,
                "status": "active",
                "is_deleted": False
            }
        )

        # Get user's organizations with minimal data to prevent oversized responses
        orgs = await self._db_query(
            "organization_members",
            select="organizations!inner(id,name,slug,type,status)",
            filters={
                "user_id": user_id,
                "status": "active",
                "is_deleted": False
            },
            limit=limit,
            offset=offset
        )

        organizations = []
        for org_member in orgs:
            org_data = org_member.get("organizations")
            if org_data:
                # Get projects count for this org
                project_count = await self._db_count(
                    "projects",
                    filters={
                        "organization_id": org_data["id"],
                        "is_deleted": False
                    }
                )

                org_data["project_count"] = project_count
                organizations.append(org_data)

        return {
            "organizations": organizations,
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + len(organizations)) < total_count,
            "context": await self.get_context(user_id)
        }
    
    async def get_smart_defaults(self, user_id: str) -> Dict[str, Optional[str]]:
        """Get smart default values based on user context."""
        context = await self.get_context(user_id)
        
        # Try to get active context first
        org_id = context.get("active_organization")
        project_id = context.get("active_project")
        document_id = context.get("active_document")
        
        # If no active org, try personal org
        if not org_id:
            personal_org = await self._db_get_single(
                "organizations",
                filters={
                    "created_by": user_id,
                    "type": "personal",
                    "is_deleted": False
                }
            )
            if personal_org:
                org_id = personal_org["id"]
        
        # If no active org still, try most recent
        if not org_id and context.get("recent_organizations"):
            org_id = context["recent_organizations"][0]
        
        return {
            "organization_id": org_id,
            "project_id": project_id,
            "document_id": document_id
        }


# Global manager instance
_workspace_manager = WorkspaceManager()


async def workspace_operation(
    auth_token: Optional[str],
    operation: Literal["get_context", "set_context", "list_workspaces", "get_defaults"],
    context_type: Optional[Literal["organization", "project", "document"]] = None,
    entity_id: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    format_type: str = "detailed",
    organization_id: Optional[str] = None,
    project_id: Optional[str] = None
) -> Dict[str, Any]:
    """Manage workspace context for the current user.

    Args:
        auth_token: Authentication token (Supabase JWT or session token)
        operation: Operation to perform
        context_type: Type of context to set (required for set_context)
        entity_id: ID of entity to set as active (required for set_context)
        limit: Max results for list_workspaces (default: 100, max: 500)
        offset: Skip N results for list_workspaces pagination (default: 0)
        format_type: Result format (detailed, summary, raw)
        organization_id: Optional organization context (for hierarchical operations)
        project_id: Optional project context (for hierarchical operations)

    Returns:
        Dict containing operation result
    """
    try:
        # Validate authentication (OAuth-only)
        if not auth_token:
            raise ValueError("Authorization required: missing bearer token. Please authenticate via OAuth and retry.")
        user_info = await _workspace_manager._validate_auth(auth_token)
        user_id = user_info.get("user_id") or user_info.get("sub") or ""

        if operation == "get_context":
            result = await _workspace_manager.get_context(user_id)

        elif operation == "set_context":
            if not context_type or not entity_id:
                raise ValueError("context_type and entity_id are required for set_context")
            result = await _workspace_manager.set_context(user_id, context_type, entity_id)

        elif operation == "list_workspaces":
            result = await _workspace_manager.list_workspaces(
                user_id,
                limit=limit or 100,
                offset=offset or 0
            )

        elif operation == "get_defaults":
            result = await _workspace_manager.get_smart_defaults(user_id)

        else:
            raise ValueError(f"Unknown operation: {operation}")

        return _workspace_manager._format_result(result, format_type)

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "operation": operation
        }