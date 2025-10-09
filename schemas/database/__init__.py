"""
TypedDict definitions for database row types.

These types match the exact structure of PostgreSQL rows
returned by Supabase queries.
"""

from schemas.database.entities import (
    OrganizationRow,
    ProjectRow,
    DocumentRow,
    RequirementRow,
    TestRow,
    ProfileRow,
    BlockRow,
    PropertyRow,
)

from schemas.database.relationships import (
    OrganizationMemberRow,
    ProjectMemberRow,
    RequirementTestRow,
    OrganizationInvitationRow,
)

__all__ = [
    # Core entities
    "OrganizationRow",
    "ProjectRow",
    "DocumentRow",
    "RequirementRow",
    "TestRow",
    "ProfileRow",
    "BlockRow",
    "PropertyRow",
    # Relationships
    "OrganizationMemberRow",
    "ProjectMemberRow",
    "RequirementTestRow",
    "OrganizationInvitationRow",
]
