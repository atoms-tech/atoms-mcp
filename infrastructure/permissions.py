"""Permission system for entity operations and multi-tenant isolation."""

from __future__ import annotations

import logging
from typing import Dict, List, Set, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class Permission(Enum):
    """Permission types for entities."""
    
    # Basic CRUD permissions
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    ARCHIVE = "archive"
    RESTORE = "restore"
    
    # Special permissions
    LIST = "list"
    SEARCH = "search"
    EXPORT = "export"
    IMPORT = "import"
    BULK_OPERATIONS = "bulk_operations"
    
    # Administrative permissions
    MANAGE_PERMISSIONS = "manage_permissions"
    MANAGE_WORKSPACE = "manage_workspace"
    VIEW_AUDIT_LOG = "view_audit_log"
    SYSTEM_ADMIN = "system_admin"


class EntityType(Enum):
    """Entity types in the system."""
    
    ORGANIZATION = "organization"
    PROJECT = "project"
    DOCUMENT = "document"
    REQUIREMENT = "requirement"
    TEST = "test"
    PROPERTY = "property"
    BLOCK = "block"
    COLUMN = "column"
    WORKFLOW = "workflow"
    WORKFLOW_EXECUTION = "workflow_execution"
    INVITATION = "invitation"
    MEMBER = "member"
    COMMENT = "comment"
    TAG = "tag"
    ATTACHMENT = "attachment"
    VERSION = "version"
    AUDIT_LOG = "audit_log"


@dataclass
class UserContext:
    """User context for permission checks."""
    
    user_id: str
    username: Optional[str] = None
    email: Optional[str] = None
    roles: Set[str] = None
    workspace_memberships: Dict[str, str] = None  # workspace_id -> role
    is_system_admin: bool = False
    
    def __post_init__(self):
        if self.roles is None:
            self.roles = set()
        if self.workspace_memberships is None:
            self.workspace_memberships = {}


@dataclass
class ResourceContext:
    """Resource context for permission checks."""
    
    entity_type: EntityType
    entity_id: Optional[str] = None
    workspace_id: Optional[str] = None
    parent_id: Optional[str] = None  # For hierarchical permissions
    owner_id: Optional[str] = None  # Direct owner
    additional_data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.additional_data is None:
            self.additional_data = {}


class PermissionChecker:
    """Main permission checking system."""
    
    def __init__(self):
        """Initialize permission checker with default rules."""
        self._rules = self._load_default_rules()
    
    def _load_default_rules(self) -> Dict[tuple, Dict[Permission, bool]]:
        """Load default permission rules based on roles and ownership."""
        rules = {}
        
        # System admin has all permissions
        rules[("system_admin", None)] = {perm: True for perm in Permission}
        
        # Workspace owner permissions
        rules[("workspace_owner", None)] = {
            Permission.CREATE: True,
            Permission.READ: True,
            Permission.UPDATE: True,
            Permission.DELETE: True,
            Permission.ARCHIVE: True,
            Permission.RESTORE: True,
            Permission.LIST: True,
            Permission.SEARCH: True,
            Permission.EXPORT: True,
            Permission.IMPORT: True,
            Permission.BULK_OPERATIONS: True,
            Permission.MANAGE_PERMISSIONS: True,
            Permission.VIEW_AUDIT_LOG: True,
        }
        
        # Workspace admin permissions
        rules[("workspace_admin", None)] = {
            Permission.CREATE: True,
            Permission.READ: True,
            Permission.UPDATE: True,
            Permission.DELETE: True,
            Permission.ARCHIVE: True,
            Permission.RESTORE: True,
            Permission.LIST: True,
            Permission.SEARCH: True,
            Permission.EXPORT: True,
            Permission.IMPORT: True,
            Permission.BULK_OPERATIONS: True,
            Permission.VIEW_AUDIT_LOG: True,
            Permission.MANAGE_PERMISSIONS: False,
        }
        
        # Workspace member permissions
        rules[("workspace_member", None)] = {
            Permission.CREATE: True,
            Permission.READ: True,
            Permission.UPDATE: True,
            Permission.DELETE: False,  # Need special permissions
            Permission.ARCHIVE: True,
            Permission.RESTORE: True,
            Permission.LIST: True,
            Permission.SEARCH: True,
            Permission.EXPORT: True,
            Permission.IMPORT: True,
            Permission.BULK_OPERATIONS: True,
            Permission.VIEW_AUDIT_LOG: False,
        }
        
        # Workspace viewer (read-only)
        rules[("workspace_viewer", None)] = {
            Permission.CREATE: False,
            Permission.READ: True,
            Permission.UPDATE: False,
            Permission.DELETE: False,
            Permission.ARCHIVE: False,
            Permission.RESTORE: False,
            Permission.LIST: True,
            Permission.SEARCH: True,
            Permission.EXPORT: True,
            Permission.IMPORT: False,
            Permission.BULK_OPERATIONS: False,
            Permission.VIEW_AUDIT_LOG: False,
        }
        
        return rules
    
    async def check_permission(
        self,
        user: UserContext,
        permission: Permission,
        resource: ResourceContext,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Check if user has permission on resource.
        
        Args:
            user: User context
            permission: Permission to check
            resource: Resource context
            additional_context: Additional context for decision making
            
        Returns:
            True if permission granted, False otherwise
        """
        # System admin bypasses all checks
        if user.is_system_admin:
            return True
        
        # Get user's role in the workspace
        workspace_role = None
        if resource.workspace_id:
            workspace_role = user.workspace_memberships.get(resource.workspace_id)
        
        if not workspace_role:
            # User is not a member of the workspace
            return False
        
        # Check base role permissions
        role_key = (workspace_role, None)
        base_permissions = self._rules.get(role_key, {})
        
        # Check if permission is granted by base role
        if not base_permissions.get(permission, False):
            # Check ownership rules for delete operations
            if permission == Permission.DELETE and resource.owner_id == user.user_id:
                return True
            
            # Check parent permissions for nested entities
            if await self._check_parent_permissions(user, permission, resource):
                return True
            
            return False
        
        # Check entity-specific restrictions
        return await self._check_entity_specific_permissions(
            user, permission, resource, workspace_role
        )
    
    async def _check_parent_permissions(
        self,
        user: UserContext,
        permission: Permission,
        resource: ResourceContext
    ) -> bool:
        """Check permissions inherited from parent entity."""
        if not resource.parent_id:
            return False
        
        # For now, allow most operations on child entities if parent is accessible
        # In production, this would query the parent entity and check its permissions
        if permission in [Permission.READ, Permission.UPDATE, Permission.ARCHIVE]:
            return True
        
        return False
    
    async def _check_entity_specific_permissions(
        self,
        user: UserContext,
        permission: Permission,
        resource: ResourceContext,
        workspace_role: str
    ) -> bool:
        """Check entity-type specific permission rules."""
        
        # Special handling for sensitive entity types
        if resource.entity_type == EntityType.WORKFLOW:
            # Workflow management requires admin permissions
            if permission in [Permission.UPDATE, Permission.DELETE]:
                return workspace_role in ["workspace_owner", "workspace_admin"]
        
        elif resource.entity_type == EntityType.AUDIT_LOG:
            # Audit logs are restricted
            return workspace_role in ["workspace_owner", "workspace_admin"]
        
        elif resource.entity_type == EntityType.INVITATION:
            # Invitation management requires elevated permissions
            if permission in [Permission.CREATE, Permission.DELETE]:
                return workspace_role in ["workspace_owner", "workspace_admin"]
        
        # Default to allowed if no specific restrictions
        return True
    
    def get_accessible_entities(
        self,
        user: UserContext,
        workspace_id: str,
        permission: Permission = Permission.READ
    ) -> List[EntityType]:
        """Get list of entity types user can access in workspace.
        
        Args:
            user: User context
            workspace_id: Workspace to check
            permission: Permission level required
            
        Returns:
            List of accessible entity types
        """
        workspace_role = user.workspace_memberships.get(workspace_id)
        if not workspace_role:
            return []
        
        accessible = []
        for entity_type in EntityType:
            resource = ResourceContext(
                entity_type=entity_type,
                workspace_id=workspace_id
            )
            
            # Use sync version for simple checks
            if self._has_permission_sync(
                workspace_role, permission, resource
            ):
                accessible.append(entity_type)
        
        return accessible
    
    def _has_permission_sync(
        self,
        workspace_role: str,
        permission: Permission,
        resource: ResourceContext
    ) -> bool:
        """Simplified permission check for entity listing."""
        role_key = (workspace_role, None)
        base_permissions = self._rules.get(role_key, {})
        return base_permissions.get(permission, False)
    
    def filter_entities_by_permission(
        self,
        user: UserContext,
        entities: List[Dict[str, Any]],
        permission: Permission = Permission.READ
    ) -> List[Dict[str, Any]]:
        """Filter list of entities based on user permissions.
        
        Args:
            user: User context
            entities: List of entity dictionaries
            permission: Permission required
            
        Returns:
            Filtered list of entities
        """
        accessible = []
        
        for entity in entities:
            entity_type = EntityType(entity.get("entity_type"))
            workspace_id = entity.get("workspace_id")
            owner_id = entity.get("created_by")
            
            resource = ResourceContext(
                entity_type=entity_type,
                entity_id=entity.get("id"),
                workspace_id=workspace_id,
                owner_id=owner_id
            )
            
            if self._has_permission_sync(
                user.workspace_memberships.get(workspace_id, ""),
                permission,
                resource
            ):
                accessible.append(entity)
        
        return accessible
    
    def validate_multi_tenant_access(
        self,
        user: UserContext,
        workspace_id: str
    ) -> bool:
        """Validate user has access to the workspace (multi-tenant isolation).
        
        Args:
            user: User context
            workspace_id: Workspace to validate access
            
        Returns:
            True if user can access workspace, False otherwise
        """
        return workspace_id in user.workspace_memberships
    
    def get_workspace_role(self, user: UserContext, workspace_id: str) -> Optional[str]:
        """Get user's role in a workspace.
        
        Args:
            user: User context
            workspace_id: Workspace ID
            
        Returns:
            Role string or None if not a member
        """
        return user.workspace_memberships.get(workspace_id)


# Global permission checker instance
_permission_checker = None


def get_permission_checker() -> PermissionChecker:
    """Get the global permission checker instance."""
    global _permission_checker
    if _permission_checker is None:
        _permission_checker = PermissionChecker()
    return _permission_checker


def create_user_context(
    user_id: str,
    workspace_memberships: Optional[Dict[str, str]] = None,
    is_system_admin: bool = False,
    **kwargs
) -> UserContext:
    """Create a user context for permission checking.
    
    Args:
        user_id: User identifier
        workspace_memberships: Dict mapping workspace_id -> role
        is_system_admin: Whether user is system admin
        **kwargs: Additional user fields
        
    Returns:
        UserContext instance
    """
    return UserContext(
        user_id=user_id,
        workspace_memberships=workspace_memberships or {},
        is_system_admin=is_system_admin,
        **kwargs
    )


def create_resource_context(
    entity_type: str,
    workspace_id: Optional[str] = None,
    entity_id: Optional[str] = None,
    owner_id: Optional[str] = None,
    **kwargs
) -> ResourceContext:
    """Create a resource context for permission checking.
    
    Args:
        entity_type: Type of entity
        workspace_id: Workspace ID
        entity_id: Entity ID
        owner_id: Owner of the entity
        **kwargs: Additional resource fields
        
    Returns:
        ResourceContext instance
    """
    return ResourceContext(
        entity_type=EntityType(entity_type),
        workspace_id=workspace_id,
        entity_id=entity_id,
        owner_id=owner_id,
        **kwargs
    )
