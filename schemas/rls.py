"""
Row-Level Security (RLS) Policy Validators for Atoms MCP.

This module provides Python implementations of Supabase RLS policies
for server-side validation and permission checking.

All validators replicate the logic of database RLS policies to:
1. Pre-validate operations before database calls
2. Provide clear permission error messages
3. Enable testing of authorization logic
4. Support authorization decisions in application code

Database RLS policies are still enforced - these validators provide
a first line of defense and better error messages.

Usage:
    from schemas.rls import PolicyValidator, OrganizationPolicy

    # Check permissions before database operation
    validator = PolicyValidator(user_id="user-123", db_adapter=db)

    # Check if user can read organization
    can_read = await validator.can_select("organizations", {"id": "org-456"})

    # Or use table-specific policies
    org_policy = OrganizationPolicy(user_id="user-123", db_adapter=db)
    await org_policy.validate_select({"id": "org-456"})  # Raises PermissionError if denied
"""

from __future__ import annotations

from typing import Any

from schemas.constants import Tables
from schemas.generated.fastapi.schema_public_latest import (
    PublicProjectRoleEnum as ProjectRole,
)

# Import from generated schemas
from schemas.generated.fastapi.schema_public_latest import (
    PublicUserRoleTypeEnum as UserRoleType,
)
from schemas.generated.fastapi.schema_public_latest import (
    PublicVisibilityEnum as Visibility,
)
from utils.logging_setup import get_logger

logger = get_logger(__name__)


# =============================================================================
# EXCEPTIONS
# =============================================================================

class PermissionDeniedError(PermissionError):
    """Raised when RLS policy denies an operation."""

    def __init__(self, table: str, operation: str, reason: str):
        self.table = table
        self.operation = operation
        self.reason = reason
        super().__init__(f"Permission denied for {operation} on {table}: {reason}")


# =============================================================================
# HELPER FUNCTIONS (Database Function Equivalents)
# =============================================================================

async def user_can_access_project(project_id: str, user_id: str, db_adapter) -> bool:
    """
    Check if user can access a project.

    Replicates: user_can_access_project(uuid, uuid) database function

    A user can access a project if:
    1. They are a member of the project (in project_members)
    2. They are a member of the project's organization (in organization_members)
    3. The project visibility is 'public'

    Args:
        project_id: Project UUID
        user_id: User UUID
        db_adapter: Database adapter for queries

    Returns:
        True if user can access project, False otherwise
    """
    try:
        # Check project membership
        project_member = await db_adapter.get_single(
            Tables.PROJECT_MEMBERS,
            filters={"project_id": project_id, "user_id": user_id, "is_deleted": False}
        )
        if project_member:
            return True

        # Get project to check visibility and organization
        project = await db_adapter.get_single(
            Tables.PROJECTS,
            filters={"id": project_id, "is_deleted": False}
        )

        if not project:
            return False

        # Check if project is public
        if project.get("visibility") == Visibility.PUBLIC.value:
            return True

        # Check organization membership
        org_member = await db_adapter.get_single(
            Tables.ORGANIZATION_MEMBERS,
            filters={"organization_id": project["organization_id"], "user_id": user_id, "is_deleted": False}
        )

        return org_member is not None

    except Exception as e:
        logger.error(f"Error checking project access: {e}")
        return False


async def is_project_owner_or_admin(project_id: str, user_id: str, db_adapter) -> bool:
    """
    Check if user is project owner or admin.

    Replicates: is_project_owner_or_admin(uuid, uuid) database function

    Args:
        project_id: Project UUID
        user_id: User UUID
        db_adapter: Database adapter for queries

    Returns:
        True if user is owner or admin of project, False otherwise
    """
    try:
        member = await db_adapter.get_single(
            Tables.PROJECT_MEMBERS,
            filters={"project_id": project_id, "user_id": user_id, "is_deleted": False}
        )

        if not member:
            return False

        role = member.get("role", "")
        return role in [ProjectRole.OWNER.value, ProjectRole.ADMIN.value]

    except Exception as e:
        logger.error(f"Error checking project ownership: {e}")
        return False


async def is_super_admin(user_id: str, db_adapter) -> bool:
    """
    Check if user is a super admin.

    Replicates: is_super_admin(uuid) database function

    Args:
        user_id: User UUID
        db_adapter: Database adapter for queries

    Returns:
        True if user is super admin, False otherwise
    """
    try:
        # Check for super_admin role in organization_members
        admin_record = await db_adapter.get_single(
            Tables.ORGANIZATION_MEMBERS,
            filters={"user_id": user_id, "role": UserRoleType.SUPER_ADMIN.value, "is_deleted": False}
        )

        return admin_record is not None

    except Exception as e:
        logger.error(f"Error checking super admin status: {e}")
        return False


async def get_user_organization_ids(user_id: str, db_adapter) -> list[str]:
    """
    Get all organization IDs that a user is a member of.

    Replicates: get_user_organization_ids(uuid) database function

    Args:
        user_id: User UUID
        db_adapter: Database adapter for queries

    Returns:
        List of organization IDs
    """
    try:
        memberships = await db_adapter.query(
            Tables.ORGANIZATION_MEMBERS,
            filters={"user_id": user_id, "is_deleted": False}
        )

        return [m["organization_id"] for m in memberships if "organization_id" in m]

    except Exception as e:
        logger.error(f"Error getting user organizations: {e}")
        return []


async def is_organization_owner_or_admin(org_id: str, user_id: str, db_adapter) -> bool:
    """
    Check if user is organization owner or admin.

    Args:
        org_id: Organization UUID
        user_id: User UUID
        db_adapter: Database adapter for queries

    Returns:
        True if user is owner or admin of organization, False otherwise
    """
    try:
        member = await db_adapter.get_single(
            Tables.ORGANIZATION_MEMBERS,
            filters={"organization_id": org_id, "user_id": user_id, "is_deleted": False}
        )

        if not member:
            return False

        role = member.get("role", "")
        return role in [UserRoleType.OWNER.value, UserRoleType.ADMIN.value, UserRoleType.SUPER_ADMIN.value]

    except Exception as e:
        logger.error(f"Error checking organization ownership: {e}")
        return False


# =============================================================================
# BASE POLICY VALIDATOR
# =============================================================================

class PolicyValidator:
    """
    Base class for RLS policy validation.

    Provides methods to check SELECT, INSERT, UPDATE, DELETE permissions
    for any table based on user context and record data.
    """

    def __init__(self, user_id: str, db_adapter):
        """
        Initialize policy validator.

        Args:
            user_id: User UUID making the request
            db_adapter: Database adapter for membership/permission queries
        """
        self.user_id = user_id
        self.db_adapter = db_adapter
        self._is_super_admin_cache: bool | None = None
        self._user_orgs_cache: list[str] | None = None

    async def _check_super_admin(self) -> bool:
        """Check if user is super admin (cached)."""
        if self._is_super_admin_cache is None:
            self._is_super_admin_cache = await is_super_admin(self.user_id, self.db_adapter)
        return self._is_super_admin_cache

    async def _get_user_orgs(self) -> list[str]:
        """Get user's organization IDs (cached)."""
        if self._user_orgs_cache is None:
            self._user_orgs_cache = await get_user_organization_ids(self.user_id, self.db_adapter)
        return self._user_orgs_cache

    async def can_select(self, table: str, record: dict[str, Any]) -> bool:
        """
        Check if user can SELECT (read) a record.

        Args:
            table: Table name
            record: Record data

        Returns:
            True if allowed, False otherwise
        """
        # Get table-specific policy
        policy = self._get_table_policy(table)
        if policy:
            return await policy.can_select(record)

        # Default: deny
        return False

    async def can_insert(self, table: str, data: dict[str, Any]) -> bool:
        """
        Check if user can INSERT a record.

        Args:
            table: Table name
            data: Data to be inserted

        Returns:
            True if allowed, False otherwise
        """
        policy = self._get_table_policy(table)
        if policy:
            return await policy.can_insert(data)
        return False

    async def can_update(self, table: str, record: dict[str, Any], data: dict[str, Any]) -> bool:
        """
        Check if user can UPDATE a record.

        Args:
            table: Table name
            record: Existing record
            data: Update data

        Returns:
            True if allowed, False otherwise
        """
        policy = self._get_table_policy(table)
        if policy:
            return await policy.can_update(record, data)
        return False

    async def can_delete(self, table: str, record: dict[str, Any]) -> bool:
        """
        Check if user can DELETE a record.

        Args:
            table: Table name
            record: Record to delete

        Returns:
            True if allowed, False otherwise
        """
        policy = self._get_table_policy(table)
        if policy:
            return await policy.can_delete(record)
        return False

    def _get_table_policy(self, table: str):
        """Get table-specific policy validator."""
        policy_map = {
            Tables.ORGANIZATIONS: OrganizationPolicy(self.user_id, self.db_adapter),
            Tables.PROJECTS: ProjectPolicy(self.user_id, self.db_adapter),
            Tables.DOCUMENTS: DocumentPolicy(self.user_id, self.db_adapter),
            Tables.REQUIREMENTS: RequirementPolicy(self.user_id, self.db_adapter),
            Tables.TEST_REQ: TestPolicy(self.user_id, self.db_adapter),
            Tables.PROFILES: ProfilePolicy(self.user_id, self.db_adapter),
            Tables.ORGANIZATION_MEMBERS: OrganizationMemberPolicy(self.user_id, self.db_adapter),
            Tables.PROJECT_MEMBERS: ProjectMemberPolicy(self.user_id, self.db_adapter),
        }
        return policy_map.get(table)


# =============================================================================
# TABLE-SPECIFIC POLICY VALIDATORS
# =============================================================================

class TablePolicy:
    """Base class for table-specific policies."""

    def __init__(self, user_id: str, db_adapter):
        self.user_id = user_id
        self.db_adapter = db_adapter

    async def can_select(self, record: dict[str, Any]) -> bool:
        """Check SELECT permission."""
        raise NotImplementedError

    async def can_insert(self, data: dict[str, Any]) -> bool:
        """Check INSERT permission."""
        raise NotImplementedError

    async def can_update(self, record: dict[str, Any], data: dict[str, Any]) -> bool:
        """Check UPDATE permission."""
        raise NotImplementedError

    async def can_delete(self, record: dict[str, Any]) -> bool:
        """Check DELETE permission."""
        raise NotImplementedError

    async def validate_select(self, record: dict[str, Any]):
        """Validate SELECT or raise PermissionDeniedError."""
        if not await self.can_select(record):
            raise PermissionDeniedError(
                self.__class__.__name__.replace("Policy", ""),
                "SELECT",
                "User does not have read access to this record"
            )

    async def validate_insert(self, data: dict[str, Any]):
        """Validate INSERT or raise PermissionDeniedError."""
        if not await self.can_insert(data):
            raise PermissionDeniedError(
                self.__class__.__name__.replace("Policy", ""),
                "INSERT",
                "User does not have permission to create this record"
            )

    async def validate_update(self, record: dict[str, Any], data: dict[str, Any]):
        """Validate UPDATE or raise PermissionDeniedError."""
        if not await self.can_update(record, data):
            raise PermissionDeniedError(
                self.__class__.__name__.replace("Policy", ""),
                "UPDATE",
                "User does not have permission to update this record"
            )

    async def validate_delete(self, record: dict[str, Any]):
        """Validate DELETE or raise PermissionDeniedError."""
        if not await self.can_delete(record):
            raise PermissionDeniedError(
                self.__class__.__name__.replace("Policy", ""),
                "DELETE",
                "User does not have permission to delete this record"
            )


class OrganizationPolicy(TablePolicy):
    """
    RLS policy for organizations table.

    Database Policies:
    - SELECT: User is member of organization OR organization is public
    - INSERT: Authenticated users can create (will be owner)
    - UPDATE: Organization owner or admin
    - DELETE: Organization owner only
    """

    async def can_select(self, record: dict[str, Any]) -> bool:
        """User can read if they are a member."""
        org_id = record.get("id")
        if not org_id:
            return False

        # Check membership
        member = await self.db_adapter.get_single(
            Tables.ORGANIZATION_MEMBERS,
            filters={"organization_id": org_id, "user_id": self.user_id, "is_deleted": False}
        )
        return member is not None

    async def can_insert(self, data: dict[str, Any]) -> bool:
        """Authenticated users can create organizations."""
        return bool(self.user_id)

    async def can_update(self, record: dict[str, Any], data: dict[str, Any]) -> bool:
        """Owner or admin can update."""
        org_id = record.get("id")
        if not org_id:
            return False

        return await is_organization_owner_or_admin(org_id, self.user_id, self.db_adapter)

    async def can_delete(self, record: dict[str, Any]) -> bool:
        """Only owner can delete."""
        org_id = record.get("id")
        if not org_id:
            return False

        member = await self.db_adapter.get_single(
            Tables.ORGANIZATION_MEMBERS,
            filters={"organization_id": org_id, "user_id": self.user_id, "is_deleted": False}
        )

        return member and member.get("role") == UserRoleType.OWNER.value


class ProjectPolicy(TablePolicy):
    """
    RLS policy for projects table.

    Database Policies:
    - SELECT: User can access project (member or org member or public)
    - INSERT: User is member of parent organization
    - UPDATE: Project owner or admin
    - DELETE: Project owner only
    """

    async def can_select(self, record: dict[str, Any]) -> bool:
        """User can read if they can access the project."""
        project_id = record.get("id")
        if not project_id:
            return False

        return await user_can_access_project(project_id, self.user_id, self.db_adapter)

    async def can_insert(self, data: dict[str, Any]) -> bool:
        """User must be member of parent organization."""
        org_id = data.get("organization_id")
        if not org_id:
            return False

        member = await self.db_adapter.get_single(
            Tables.ORGANIZATION_MEMBERS,
            filters={"organization_id": org_id, "user_id": self.user_id, "is_deleted": False}
        )
        return member is not None

    async def can_update(self, record: dict[str, Any], data: dict[str, Any]) -> bool:
        """Project owner or admin can update."""
        project_id = record.get("id")
        if not project_id:
            return False

        return await is_project_owner_or_admin(project_id, self.user_id, self.db_adapter)

    async def can_delete(self, record: dict[str, Any]) -> bool:
        """Only project owner can delete."""
        project_id = record.get("id")
        if not project_id:
            return False

        member = await self.db_adapter.get_single(
            Tables.PROJECT_MEMBERS,
            filters={"project_id": project_id, "user_id": self.user_id, "is_deleted": False}
        )

        return member and member.get("role") == ProjectRole.OWNER.value


class DocumentPolicy(TablePolicy):
    """
    RLS policy for documents table.

    Database Policies:
    - SELECT: User can access parent project
    - INSERT: User can access parent project (editor+)
    - UPDATE: User can access parent project (editor+)
    - DELETE: Project owner or admin
    """

    async def can_select(self, record: dict[str, Any]) -> bool:
        """User can read if they can access the parent project."""
        project_id = record.get("project_id")
        if not project_id:
            return False

        return await user_can_access_project(project_id, self.user_id, self.db_adapter)

    async def can_insert(self, data: dict[str, Any]) -> bool:
        """User must have editor+ role in parent project."""
        project_id = data.get("project_id")
        if not project_id:
            return False

        member = await self.db_adapter.get_single(
            Tables.PROJECT_MEMBERS,
            filters={"project_id": project_id, "user_id": self.user_id, "is_deleted": False}
        )

        if not member:
            return False

        role = member.get("role", "")
        return role in [ProjectRole.OWNER.value, ProjectRole.ADMIN.value,
                       ProjectRole.MAINTAINER.value, ProjectRole.EDITOR.value]

    async def can_update(self, record: dict[str, Any], data: dict[str, Any]) -> bool:
        """User must have editor+ role in parent project."""
        project_id = record.get("project_id")
        if not project_id:
            return False

        member = await self.db_adapter.get_single(
            Tables.PROJECT_MEMBERS,
            filters={"project_id": project_id, "user_id": self.user_id, "is_deleted": False}
        )

        if not member:
            return False

        role = member.get("role", "")
        return role in [ProjectRole.OWNER.value, ProjectRole.ADMIN.value,
                       ProjectRole.MAINTAINER.value, ProjectRole.EDITOR.value]

    async def can_delete(self, record: dict[str, Any]) -> bool:
        """Project owner or admin can delete."""
        project_id = record.get("project_id")
        if not project_id:
            return False

        return await is_project_owner_or_admin(project_id, self.user_id, self.db_adapter)


class RequirementPolicy(TablePolicy):
    """
    RLS policy for requirements table.

    Database Policies:
    - SELECT: User can access parent document's project
    - INSERT: User can access parent document's project (editor+)
    - UPDATE: User can access parent document's project (editor+)
    - DELETE: User can access parent document's project (editor+)
    """

    async def _get_project_id(self, record: dict[str, Any]) -> str | None:
        """Get project ID from document ID."""
        doc_id = record.get("document_id")
        if not doc_id:
            return None

        doc = await self.db_adapter.get_single(
            Tables.DOCUMENTS,
            filters={"id": doc_id, "is_deleted": False}
        )

        return doc.get("project_id") if doc else None

    async def can_select(self, record: dict[str, Any]) -> bool:
        """User can read if they can access the parent project."""
        project_id = await self._get_project_id(record)
        if not project_id:
            return False

        return await user_can_access_project(project_id, self.user_id, self.db_adapter)

    async def can_insert(self, data: dict[str, Any]) -> bool:
        """User must have editor+ role."""
        project_id = await self._get_project_id(data)
        if not project_id:
            return False

        member = await self.db_adapter.get_single(
            Tables.PROJECT_MEMBERS,
            filters={"project_id": project_id, "user_id": self.user_id, "is_deleted": False}
        )

        if not member:
            return False

        role = member.get("role", "")
        return role in [ProjectRole.OWNER.value, ProjectRole.ADMIN.value,
                       ProjectRole.MAINTAINER.value, ProjectRole.EDITOR.value]

    async def can_update(self, record: dict[str, Any], data: dict[str, Any]) -> bool:
        """User must have editor+ role."""
        return await self.can_insert(record)

    async def can_delete(self, record: dict[str, Any]) -> bool:
        """User must have editor+ role."""
        return await self.can_insert(record)


class TestPolicy(TablePolicy):
    """
    RLS policy for test_req table.

    Database Policies:
    - SELECT: User can access parent project
    - INSERT: User can access parent project (editor+)
    - UPDATE: User can access parent project (editor+)
    - DELETE: Project owner or admin
    """

    async def can_select(self, record: dict[str, Any]) -> bool:
        """User can read if they can access the parent project."""
        project_id = record.get("project_id")
        if not project_id:
            return False

        return await user_can_access_project(project_id, self.user_id, self.db_adapter)

    async def can_insert(self, data: dict[str, Any]) -> bool:
        """User must have editor+ role."""
        project_id = data.get("project_id")
        if not project_id:
            return False

        member = await self.db_adapter.get_single(
            Tables.PROJECT_MEMBERS,
            filters={"project_id": project_id, "user_id": self.user_id, "is_deleted": False}
        )

        if not member:
            return False

        role = member.get("role", "")
        return role in [ProjectRole.OWNER.value, ProjectRole.ADMIN.value,
                       ProjectRole.MAINTAINER.value, ProjectRole.EDITOR.value]

    async def can_update(self, record: dict[str, Any], data: dict[str, Any]) -> bool:
        """User must have editor+ role."""
        return await self.can_insert(record)

    async def can_delete(self, record: dict[str, Any]) -> bool:
        """Project owner or admin can delete."""
        project_id = record.get("project_id")
        if not project_id:
            return False

        return await is_project_owner_or_admin(project_id, self.user_id, self.db_adapter)


class ProfilePolicy(TablePolicy):
    """
    RLS policy for profiles table.

    Database Policies:
    - SELECT: All authenticated users can read (for collaboration)
    - INSERT: Super admin only (profiles auto-created on signup)
    - UPDATE: Own profile only
    - DELETE: Super admin only
    """

    async def can_select(self, record: dict[str, Any]) -> bool:
        """All authenticated users can read profiles."""
        return bool(self.user_id)

    async def can_insert(self, data: dict[str, Any]) -> bool:
        """Only super admin can insert (normally auto-created)."""
        return await is_super_admin(self.user_id, self.db_adapter)

    async def can_update(self, record: dict[str, Any], data: dict[str, Any]) -> bool:
        """User can only update their own profile."""
        profile_id = record.get("id")
        return profile_id == self.user_id

    async def can_delete(self, record: dict[str, Any]) -> bool:
        """Only super admin can delete."""
        return await is_super_admin(self.user_id, self.db_adapter)


class OrganizationMemberPolicy(TablePolicy):
    """
    RLS policy for organization_members table.

    Database Policies:
    - SELECT: User is member of the organization
    - INSERT: Organization owner or admin
    - UPDATE: Organization owner or admin
    - DELETE: Organization owner or admin
    """

    async def can_select(self, record: dict[str, Any]) -> bool:
        """User can read if they are member of the organization."""
        org_id = record.get("organization_id")
        if not org_id:
            return False

        member = await self.db_adapter.get_single(
            Tables.ORGANIZATION_MEMBERS,
            filters={"organization_id": org_id, "user_id": self.user_id, "is_deleted": False}
        )
        return member is not None

    async def can_insert(self, data: dict[str, Any]) -> bool:
        """Organization owner or admin can add members."""
        org_id = data.get("organization_id")
        if not org_id:
            return False

        return await is_organization_owner_or_admin(org_id, self.user_id, self.db_adapter)

    async def can_update(self, record: dict[str, Any], data: dict[str, Any]) -> bool:
        """Organization owner or admin can update memberships."""
        org_id = record.get("organization_id")
        if not org_id:
            return False

        return await is_organization_owner_or_admin(org_id, self.user_id, self.db_adapter)

    async def can_delete(self, record: dict[str, Any]) -> bool:
        """Organization owner or admin can remove members."""
        org_id = record.get("organization_id")
        if not org_id:
            return False

        return await is_organization_owner_or_admin(org_id, self.user_id, self.db_adapter)


class ProjectMemberPolicy(TablePolicy):
    """
    RLS policy for project_members table.

    Database Policies:
    - SELECT: User can access the project
    - INSERT: Project owner or admin
    - UPDATE: Project owner or admin
    - DELETE: Project owner or admin
    """

    async def can_select(self, record: dict[str, Any]) -> bool:
        """User can read if they can access the project."""
        project_id = record.get("project_id")
        if not project_id:
            return False

        return await user_can_access_project(project_id, self.user_id, self.db_adapter)

    async def can_insert(self, data: dict[str, Any]) -> bool:
        """Project owner or admin can add members."""
        project_id = data.get("project_id")
        if not project_id:
            return False

        return await is_project_owner_or_admin(project_id, self.user_id, self.db_adapter)

    async def can_update(self, record: dict[str, Any], data: dict[str, Any]) -> bool:
        """Project owner or admin can update memberships."""
        project_id = record.get("project_id")
        if not project_id:
            return False

        return await is_project_owner_or_admin(project_id, self.user_id, self.db_adapter)

    async def can_delete(self, record: dict[str, Any]) -> bool:
        """Project owner or admin can remove members."""
        project_id = record.get("project_id")
        if not project_id:
            return False

        return await is_project_owner_or_admin(project_id, self.user_id, self.db_adapter)


# =============================================================================
# PUBLIC API
# =============================================================================

__all__ = [
    # Exceptions
    "PermissionDeniedError",

    # Helper functions
    "user_can_access_project",
    "is_project_owner_or_admin",
    "is_super_admin",
    "get_user_organization_ids",
    "is_organization_owner_or_admin",

    # Validators
    "PolicyValidator",
    "TablePolicy",
    "OrganizationPolicy",
    "ProjectPolicy",
    "DocumentPolicy",
    "RequirementPolicy",
    "TestPolicy",
    "ProfilePolicy",
    "OrganizationMemberPolicy",
    "ProjectMemberPolicy",
]
