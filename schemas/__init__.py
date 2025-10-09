"""
Comprehensive schema definitions for Atoms MCP.

This package provides type-safe schemas using:
- Enums for constrained values
- TypedDict for database row types
- Pydantic models for validation
- Constants for table and field names
- RLS policy validators for permissions
"""

from schemas.enums import (
    EntityType,
    OrganizationType,
    EntityStatus,
    Priority,
    RelationshipType,
    QueryType,
    RAGMode,
    MemberRole,
    InvitationStatus,
)

from schemas.constants import (
    Tables,
    Fields,
    TABLES_WITHOUT_SOFT_DELETE,
    TABLES_WITHOUT_AUDIT_FIELDS,
)

from schemas.rls import (
    PolicyValidator,
    PermissionDeniedError,
    OrganizationPolicy,
    ProjectPolicy,
    DocumentPolicy,
    RequirementPolicy,
    TestPolicy,
    ProfilePolicy,
    OrganizationMemberPolicy,
    ProjectMemberPolicy,
)

__all__ = [
    # Enums
    "EntityType",
    "OrganizationType",
    "EntityStatus",
    "Priority",
    "RelationshipType",
    "QueryType",
    "RAGMode",
    "MemberRole",
    "InvitationStatus",
    # Constants
    "Tables",
    "Fields",
    "TABLES_WITHOUT_SOFT_DELETE",
    "TABLES_WITHOUT_AUDIT_FIELDS",
    # RLS Policies
    "PolicyValidator",
    "PermissionDeniedError",
    "OrganizationPolicy",
    "ProjectPolicy",
    "DocumentPolicy",
    "RequirementPolicy",
    "TestPolicy",
    "ProfilePolicy",
    "OrganizationMemberPolicy",
    "ProjectMemberPolicy",
]
