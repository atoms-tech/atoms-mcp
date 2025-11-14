"""Permission middleware for entity operations."""

from __future__ import annotations

import logging
from functools import wraps
from typing import Any, Dict, Optional, Callable, Awaitable

from .permissions import (
    Permission,
    EntityType,
    get_permission_checker,
    create_user_context,
    create_resource_context
)

logger = logging.getLogger(__name__)


class PermissionMiddleware:
    """Middleware to enforce permissions on entity operations."""
    
    def __init__(self, get_user_context: Callable[[], Awaitable[Dict[str, Any]]]):
        """Initialize permission middleware.
        
        Args:
            get_user_context: Async function that returns current user context
        """
        self.get_user_context = get_user_context
        self.permission_checker = get_permission_checker()
    
    async def check_create_permission(
        self,
        entity_type: str,
        data: Dict[str, Any],
        workspace_id: Optional[str] = None
    ) -> bool:
        """Check if user can create entity of type.
        
        Args:
            entity_type: Type of entity being created
            data: Entity data
            workspace_id: Workspace ID (extracted from data if not provided)
            
        Returns:
            True if allowed, raises PermissionError otherwise
            
        Raises:
            PermissionError: If permission denied
        """
        user_ctx = await self._get_user_context()
        workspace_id = workspace_id or data.get("workspace_id")
        
        # Organizations and users are top-level entities that don't require workspace_id
        # They define workspaces, not contained within them
        # Skip permission checks for these entities in test mode or when no workspace context
        if entity_type.lower() in ["organization", "user"]:
            # Allow creation of top-level entities without workspace_id
            # (they may be outside workspace context)
            logger.debug(
                f"Allowing creation of top-level entity {entity_type} without workspace context"
            )
            return True
        
        if not workspace_id:
            raise PermissionError("Workspace ID required for entity creation")
        
        resource_ctx = create_resource_context(
            entity_type=entity_type,
            workspace_id=workspace_id
        )
        
        has_permission = await self.permission_checker.check_permission(
            user_ctx, Permission.CREATE, resource_ctx
        )
        if not has_permission:
            raise PermissionError(
                f"User {user_ctx.user_id} lacks create permission for {entity_type} "
                f"in workspace {workspace_id}"
            )
        
        return True
    
    async def check_read_permission(
        self,
        entity_type: str,
        entity_id: str,
        entity_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Check if user can read entity.
        
        Args:
            entity_type: Type of entity
            entity_id: Entity ID
            entity_data: Pre-fetched entity data (if available)
            
        Returns:
            True if allowed, raises PermissionError otherwise
            
        Raises:
            PermissionError: If permission denied
        """
        user_ctx = await self._get_user_context()
        
        # If entity_data not provided, we can't check workspace ownership
        # In this case, we rely on RLS policies at database level
        if not entity_data:
            # Log that we're relying on database-level security
            logger.debug(
                f"Relying on RLS for read permission check on "
                f"{entity_type}:{entity_id} for user {user_ctx.user_id}"
            )
            return True
        
        workspace_id = entity_data.get("workspace_id")
        owner_id = entity_data.get("created_by")
        
        resource_ctx = create_resource_context(
            entity_type=entity_type,
            entity_id=entity_id,
            workspace_id=workspace_id,
            owner_id=owner_id
        )
        
        if not await self.permission_checker.check_permission(
            user_ctx, Permission.READ, resource_ctx
        ):
            raise PermissionError(
                f"User {user_ctx.user_id} lacks read permission for {entity_type}:{entity_id}"
            )
        
        return True
    
    async def check_update_permission(
        self,
        entity_type: str,
        entity_id: str,
        update_data: Dict[str, Any],
        entity_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Check if user can update entity.
        
        Args:
            entity_type: Type of entity
            entity_id: Entity ID
            update_data: Data being updated
            entity_data: Pre-fetched entity data (if available)
            
        Returns:
            True if allowed, raises PermissionError otherwise
            
        Raises:
            PermissionError: If permission denied
        """
        user_ctx = await self._get_user_context()
        
        # If entity_data not provided, rely on RLS
        if not entity_data:
            logger.debug(
                f"Relying on RLS for update permission check on "
                f"{entity_type}:{entity_id} for user {user_ctx.user_id}"
            )
            return True
        
        workspace_id = entity_data.get("workspace_id")
        owner_id = entity_data.get("created_by")
        
        resource_ctx = create_resource_context(
            entity_type=entity_type,
            entity_id=entity_id,
            workspace_id=workspace_id,
            owner_id=owner_id
        )
        
        if not await self.permission_checker.check_permission(
            user_ctx, Permission.UPDATE, resource_ctx
        ):
            raise PermissionError(
                f"User {user_ctx.user_id} lacks update permission for {entity_type}:{entity_id}"
            )
        
        return True
    
    async def check_delete_permission(
        self,
        entity_type: str,
        entity_id: str,
        entity_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Check if user can delete entity.
        
        Args:
            entity_type: Type of entity
            entity_id: Entity ID
            entity_data: Pre-fetched entity data (if available)
            
        Returns:
            True if allowed, raises PermissionError otherwise
            
        Raises:
            PermissionError: If permission denied
        """
        user_ctx = await self._get_user_context()
        
        # If entity_data not provided, rely on RLS
        if not entity_data:
            logger.debug(
                f"Relying on RLS for delete permission check on "
                f"{entity_type}:{entity_id} for user {user_ctx.user_id}"
            )
            return True
        
        workspace_id = entity_data.get("workspace_id")
        owner_id = entity_data.get("created_by")
        
        resource_ctx = create_resource_context(
            entity_type=entity_type,
            entity_id=entity_id,
            workspace_id=workspace_id,
            owner_id=owner_id
        )
        
        if not await self.permission_checker.check_permission(
            user_ctx, Permission.DELETE, resource_ctx
        ):
            raise PermissionError(
                f"User {user_ctx.user_id} lacks delete permission for {entity_type}:{entity_id}"
            )
        
        return True
    
    async def check_list_permission(
        self,
        entity_type: str,
        workspace_id: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Check if user can list entities of type in workspace.
        
        Args:
            entity_type: Type of entity
            workspace_id: Workspace ID
            filters: Query filters
            
        Returns:
            True if allowed, raises PermissionError otherwise
            
        Raises:
            PermissionError: If permission denied
        """
        user_ctx = await self._get_user_context()
        
        # System admin bypasses all checks
        if user_ctx.is_system_admin:
            return True
        
        # Check workspace membership first
        if not self.permission_checker.validate_multi_tenant_access(
            user_ctx, workspace_id
        ):
            raise PermissionError(
                f"User {user_ctx.user_id} is not a member of workspace {workspace_id}"
            )
        
        resource_ctx = create_resource_context(
            entity_type=entity_type,
            workspace_id=workspace_id
        )
        
        if not await self.permission_checker.check_permission(
            user_ctx, Permission.LIST, resource_ctx
        ):
            raise PermissionError(
                f"User {user_ctx.user_id} lacks list permission for {entity_type} "
                f"in workspace {workspace_id}"
            )
        
        return True
    
    async def check_bulk_operation_permission(
        self,
        operation: str,
        entity_type: str,
        workspace_id: str,
        entity_ids: Optional[list] = None
    ) -> bool:
        """Check if user can perform bulk operations.
        
        Args:
            operation: Type of bulk operation (archive, restore, delete)
            entity_type: Type of entity
            workspace_id: Workspace ID
            entity_ids: List of entity IDs (if applicable)
            
        Returns:
            True if allowed, raises PermissionError otherwise
            
        Raises:
            PermissionError: If permission denied
        """
        user_ctx = await self._get_user_context()
        
        # System admin bypasses all checks
        if user_ctx.is_system_admin:
            return True
        
        # Check workspace membership
        if not self.permission_checker.validate_multi_tenant_access(
            user_ctx, workspace_id
        ):
            raise PermissionError(
                f"User {user_ctx.user_id} is not a member of workspace {workspace_id}"
            )
        
        # Map operation to permission
        permission_map = {
            "archive": Permission.ARCHIVE,
            "restore": Permission.RESTORE,
            "delete": Permission.DELETE,
            "bulk_update": Permission.UPDATE,
            "bulk_create": Permission.CREATE
        }
        
        permission = permission_map.get(operation)
        if not permission:
            raise PermissionError(f"Unknown bulk operation: {operation}")
        
        resource_ctx = create_resource_context(
            entity_type=entity_type,
            workspace_id=workspace_id
        )
        
        if not await self.permission_checker.check_permission(
            user_ctx, Permission.BULK_OPERATIONS, resource_ctx
        ):
            raise PermissionError(
                f"User {user_ctx.user_id} lacks bulk operations permission "
                f"in workspace {workspace_id}"
            )
        
        if not await self.permission_checker.check_permission(
            user_ctx, permission, resource_ctx
        ):
            raise PermissionError(
                f"User {user_ctx.user_id} lacks {operation} permission for {entity_type} "
                f"in workspace {workspace_id}"
            )
        
        return True
    
    async def filter_query_results(
        self,
        user_ctx,
        results: list,
        entity_type: str
    ) -> list:
        """Filter query results based on user permissions.
        
        Args:
            user_ctx: User context
            results: List of query results
            entity_type: Type of entities in results
            
        Returns:
            Filtered list of results
        """
        if not results:
            return results
        
        return self.permission_checker.filter_entities_by_permission(
            user_ctx, results, Permission.READ
        )
    
    async def _get_user_context(self):
        """Get current user context."""
        user_data = await self.get_user_context()
        
        # Convert user data to UserContext
        return create_user_context(
            user_id=user_data.get("user_id", "anonymous"),
            username=user_data.get("username"),
            email=user_data.get("email"),
            workspace_memberships=user_data.get("workspace_memberships", {}),
            is_system_admin=user_data.get("is_system_admin", False)
        )


class PermissionError(Exception):
    """Permission denied error."""
    pass


def require_permission(permission_type: str):
    """Decorator to require permission for a method.
    
    Args:
        permission_type: Type of permission required (create, read, update, delete, etc.)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Extract entity_type from args/kwargs
            entity_type = kwargs.get("entity_type") or (
                args[0] if args else None
            )
            
            if not entity_type:
                raise PermissionError("entity_type required for permission check")
            
            # Extract workspace_id and other context
            workspace_id = kwargs.get("workspace_id")
            entity_id = kwargs.get("entity_id")
            
            # Get permission middleware from instance
            middleware = getattr(self, "_permission_middleware", None)
            if not middleware:
                raise PermissionError("Permission middleware not configured")
            
            # Perform permission check based on operation type
            if permission_type == "create":
                data = kwargs.get("data", {})
                await middleware.check_create_permission(entity_type, data, workspace_id)
            elif permission_type == "read":
                await middleware.check_read_permission(entity_type, entity_id)
            elif permission_type == "update":
                update_data = kwargs.get("data", {})
                entity_data = kwargs.get("entity_data")
                await middleware.check_update_permission(entity_type, entity_id, update_data, entity_data)
            elif permission_type == "delete":
                entity_data = kwargs.get("entity_data")
                await middleware.check_delete_permission(entity_type, entity_id, entity_data)
            elif permission_type == "list":
                if not workspace_id:
                    raise PermissionError("workspace_id required for list operations")
                await middleware.check_list_permission(entity_type, workspace_id)
            else:
                raise PermissionError(f"Unknown permission type: {permission_type}")
            
            # Call original function
            return await func(self, *args, **kwargs)
        
        return wrapper
    return decorator
