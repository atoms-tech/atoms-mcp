"""Permission management and enforcement system."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from datetime import datetime, timezone

if TYPE_CHECKING:
    from supabase import Client

try:
    from .advanced_features_adapter import AdvancedFeaturesAdapter
    from ..errors import normalize_error
except ImportError:
    from infrastructure.advanced_features_adapter import AdvancedFeaturesAdapter
    from errors import normalize_error

logger = logging.getLogger(__name__)


class PermissionManager:
    """Manages entity permissions and access control."""

    # Permission hierarchy
    PERMISSION_LEVELS = {
        "view": 1,
        "edit": 2,
        "admin": 3,
    }

    # Operations and required permission levels
    OPERATION_PERMISSIONS = {
        "read": "view",
        "search": "view",
        "list": "view",
        "export": "view",
        "create": "edit",
        "update": "edit",
        "delete": "admin",
        "archive": "admin",
        "restore": "admin",
        "bulk_update": "edit",
        "bulk_delete": "admin",
        "bulk_archive": "admin",
        "history": "view",
        "restore_version": "admin",
        "trace": "view",
        "coverage": "view",
        "get_permissions": "view",
        "update_permissions": "admin",
        "list_workflows": "view",
        "create_workflow": "edit",
        "update_workflow": "edit",
        "delete_workflow": "admin",
        "execute_workflow": "edit",
        "advanced_search": "view",
        "import": "edit",
    }

    def __init__(self, db: Any, features_adapter: Optional[AdvancedFeaturesAdapter] = None):
        """Initialize permission manager.

        Args:
            db: Database adapter
            features_adapter: Advanced features adapter for permission queries
        """
        self.db = db
        self.features_adapter = features_adapter
        self.cache: Dict[str, tuple[bool, float]] = {}
        self.cache_ttl = 30.0  # seconds

    async def check_permission(
        self,
        user_id: str,
        entity_type: str,
        entity_id: str,
        operation: str,
        workspace_id: Optional[str] = None,
    ) -> bool:
        """Check if user has permission for operation on entity.

        Args:
            user_id: User ID
            entity_type: Type of entity
            entity_id: Entity ID
            operation: Operation being performed
            workspace_id: Workspace context (optional)

        Returns:
            True if allowed, False otherwise

        Raises:
            ValueError: If permission check fails
        """
        try:
            # Admin users bypass permission checks
            if await self._is_admin_user(user_id):
                return True

            # Get required permission level for operation
            required_level = self.OPERATION_PERMISSIONS.get(operation, "view")

            # Get user's permission on entity
            permissions = await self.get_entity_permissions(
                user_id, entity_type, entity_id
            )

            if not permissions:
                return False

            user_perm = permissions[0]
            user_level = user_perm.get("permission_level", "view")

            # Check if user's permission level meets requirement
            user_level_val = self.PERMISSION_LEVELS.get(user_level, 0)
            required_level_val = self.PERMISSION_LEVELS.get(required_level, 0)

            if user_level_val < required_level_val:
                return False

            # Check expiration
            if "expires_at" in user_perm and user_perm["expires_at"]:
                expires = datetime.fromisoformat(user_perm["expires_at"])
                # Handle both naive and aware datetimes
                if expires.tzinfo is None:
                    # Naive datetime - assume UTC
                    expires = expires.replace(tzinfo=timezone.utc)
                if datetime.now(timezone.utc) > expires:
                    return False

            return True

        except Exception as e:
            logger.error(f"Error checking permission: {e}")
            raise normalize_error(e, "Operation failed")

    async def get_entity_permissions(
        self,
        user_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get permissions for entity.

        Args:
            user_id: Filter by user (optional)
            entity_type: Entity type
            entity_id: Entity ID

        Returns:
            List of permission records
        """
        try:
            if not self.features_adapter:
                return []

            perms = await self.features_adapter.get_entity_permissions(
                entity_type, entity_id
            )

            # Filter by user if specified
            if user_id:
                perms = [p for p in perms if p.get("user_id") == user_id]

            return perms
        except Exception as e:
            logger.error(f"Error getting entity permissions: {e}")
            return []

    async def grant_permission(
        self,
        user_id: str,
        entity_type: str,
        entity_id: str,
        workspace_id: str,
        permission_level: str = "view",
        granted_by: Optional[str] = None,
        expires_at: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Grant permission to user on entity.

        Args:
            user_id: User to grant permission to
            entity_type: Entity type
            entity_id: Entity ID
            workspace_id: Workspace ID
            permission_level: Permission level (view, edit, admin)
            granted_by: User granting permission
            expires_at: Optional expiration date

        Returns:
            Created permission record
        """
        try:
            if not self.features_adapter:
                raise ValueError("Features adapter required")

            # Validate permission level
            if permission_level not in self.PERMISSION_LEVELS:
                raise ValueError(
                    f"Invalid permission level: {permission_level}"
                )

            permission = await self.features_adapter.grant_permission(
                entity_type=entity_type,
                entity_id=entity_id,
                workspace_id=workspace_id,
                user_id=user_id,
                permission_level=permission_level,
                granted_by=granted_by,
                expires_at=expires_at,
            )

            # Invalidate cache
            self._invalidate_cache(user_id, entity_type, entity_id)

            return permission

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error granting permission: {e}")
            raise normalize_error(e, "Operation failed")

    async def revoke_permission(
        self,
        user_id: str,
        entity_type: str,
        entity_id: str,
    ) -> bool:
        """Revoke user's permission on entity.

        Args:
            user_id: User to revoke permission from
            entity_type: Entity type
            entity_id: Entity ID

        Returns:
            True if revoked, False otherwise
        """
        try:
            if not self.features_adapter:
                return False

            # Get current permission
            perms = await self.get_entity_permissions(
                user_id, entity_type, entity_id
            )

            if not perms:
                return False

            perm_id = perms[0].get("id")
            if not perm_id:
                return False

            result = await self.features_adapter.revoke_permission(perm_id)

            # Invalidate cache
            self._invalidate_cache(user_id, entity_type, entity_id)

            return result

        except Exception as e:
            logger.error(f"Error revoking permission: {e}")
            return False

    async def _is_admin_user(self, user_id: str) -> bool:
        """Check if user is system admin.

        Args:
            user_id: User ID

        Returns:
            True if user is admin
        """
        try:
            # Check user role in database
            # This would query a users/profiles table for admin flag
            # For now, return False (admin checks in real system)
            return False
        except Exception:
            return False

    def _invalidate_cache(
        self, user_id: str, entity_type: str, entity_id: str
    ) -> None:
        """Invalidate permission cache for user/entity combo.

        Args:
            user_id: User ID
            entity_type: Entity type
            entity_id: Entity ID
        """
        cache_key = f"{user_id}:{entity_type}:{entity_id}"
        if cache_key in self.cache:
            del self.cache[cache_key]

    async def enforce_permission(
        self,
        user_id: str,
        entity_type: str,
        entity_id: str,
        operation: str,
        workspace_id: Optional[str] = None,
    ) -> None:
        """Enforce permission or raise error.

        Args:
            user_id: User ID
            entity_type: Entity type
            entity_id: Entity ID
            operation: Operation
            workspace_id: Workspace context

        Raises:
            PermissionError: If user lacks permission
        """
        allowed = await self.check_permission(
            user_id, entity_type, entity_id, operation, workspace_id
        )

        if not allowed:
            required_level = self.OPERATION_PERMISSIONS.get(operation, "view")
            raise PermissionError(
                f"User {user_id} lacks '{required_level}' permission "
                f"for {operation} on {entity_type} {entity_id}"
            )
