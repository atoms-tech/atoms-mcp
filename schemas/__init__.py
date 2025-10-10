"""
Schema module for Atoms MCP.

Uses GENERATED schemas from supabase-pydantic as the primary source.
All Pydantic models and enums are auto-generated from the Supabase database.

Manual additions:
- Constants (Tables, Fields) - for convenience
- RLS validators - for server-side permission checks
- Trigger emulators - for client-side data transformation
- Application-level enums (QueryType, RAGMode, etc.) - not in database
"""

# PRIMARY: Generated Pydantic models and database enums
# SECONDARY: Manual additions for application logic
from schemas.constants import (
    ENTITY_TABLE_MAP,
    TABLES_WITHOUT_AUDIT_FIELDS,
    TABLES_WITHOUT_SOFT_DELETE,
    Fields,
    Tables,
)

# Application-level enums (not in database, used by MCP tools)
from schemas.enums import (
    QueryType,
    RAGMode,
    RelationshipType,
)
from schemas.generated.fastapi.schema_public_latest import (
    BlockBaseSchema as BlockRow,
)
from schemas.generated.fastapi.schema_public_latest import (
    Document,
    DocumentInsert,
    DocumentUpdate,
    Organization,
    # Insert/Update Models (for API validation)
    OrganizationInsert,
    OrganizationUpdate,
    Project,
    ProjectInsert,
    ProjectUpdate,
    PublicAssignmentRoleEnum,
    PublicAuditEventTypeEnum,
    PublicAuditSeverityEnum,
    # Database Enums (23 total - generated from Supabase)
    PublicEntityTypeEnum,
    PublicRequirementStatusEnum,
    PublicResourceTypeEnum,
    Requirement,
    RequirementInsert,
    RequirementUpdate,
)
from schemas.generated.fastapi.schema_public_latest import (
    DocumentBaseSchema as DocumentRow,
)
from schemas.generated.fastapi.schema_public_latest import (
    # Base Schemas (use as TypedDict-like for DB queries)
    OrganizationBaseSchema as OrganizationRow,
)
from schemas.generated.fastapi.schema_public_latest import (
    OrganizationInvitationBaseSchema as OrganizationInvitationRow,
)
from schemas.generated.fastapi.schema_public_latest import (
    OrganizationMemberBaseSchema as OrganizationMemberRow,
)
from schemas.generated.fastapi.schema_public_latest import (
    ProfileBaseSchema as ProfileRow,
)
from schemas.generated.fastapi.schema_public_latest import (
    ProjectBaseSchema as ProjectRow,
)
from schemas.generated.fastapi.schema_public_latest import (
    ProjectMemberBaseSchema as ProjectMemberRow,
)
from schemas.generated.fastapi.schema_public_latest import (
    PropertyBaseSchema as PropertyRow,
)
from schemas.generated.fastapi.schema_public_latest import (
    PublicBillingPlanEnum as BillingPlan,
)
from schemas.generated.fastapi.schema_public_latest import (
    PublicExecutionStatusEnum as ExecutionStatus,
)
from schemas.generated.fastapi.schema_public_latest import (
    PublicInvitationStatusEnum as InvitationStatus,
)
from schemas.generated.fastapi.schema_public_latest import (
    PublicPricingPlanIntervalEnum as PricingPlanInterval,
)
from schemas.generated.fastapi.schema_public_latest import (
    PublicProjectRoleEnum as ProjectRole,
)
from schemas.generated.fastapi.schema_public_latest import (
    PublicProjectStatusEnum as ProjectStatus,
)
from schemas.generated.fastapi.schema_public_latest import (
    PublicRequirementLevelEnum as RequirementLevel,
)
from schemas.generated.fastapi.schema_public_latest import (
    PublicRequirementPriorityEnum as RequirementPriority,
)
from schemas.generated.fastapi.schema_public_latest import (
    PublicSubscriptionStatusEnum as SubscriptionStatus,
)
from schemas.generated.fastapi.schema_public_latest import (
    PublicTestMethodEnum as TestMethod,
)
from schemas.generated.fastapi.schema_public_latest import (
    PublicTestPriorityEnum as TestPriority,
)
from schemas.generated.fastapi.schema_public_latest import (
    PublicTestStatusEnum as TestStatus,
)
from schemas.generated.fastapi.schema_public_latest import (
    PublicTestTypeEnum as TestType,
)
from schemas.generated.fastapi.schema_public_latest import (
    PublicTraceLinkTypeEnum as TraceLinkType,
)
from schemas.generated.fastapi.schema_public_latest import (
    PublicUserRoleTypeEnum as UserRoleType,
)
from schemas.generated.fastapi.schema_public_latest import (
    PublicUserStatusEnum as UserStatus,
)
from schemas.generated.fastapi.schema_public_latest import (
    PublicVisibilityEnum as Visibility,
)
from schemas.generated.fastapi.schema_public_latest import (
    RequirementBaseSchema as RequirementRow,
)
from schemas.generated.fastapi.schema_public_latest import (
    RequirementTestBaseSchema as RequirementTestRow,
)
from schemas.generated.fastapi.schema_public_latest import (
    TestReqBaseSchema as TestRow,
)

# RLS validators
from schemas.rls import (
    DocumentPolicy,
    OrganizationMemberPolicy,
    OrganizationPolicy,
    PermissionDeniedError,
    PolicyValidator,
    ProfilePolicy,
    ProjectMemberPolicy,
    ProjectPolicy,
    RequirementPolicy,
    TestPolicy,
)

# Trigger emulators
from schemas.triggers import TriggerEmulator

__all__ = [
    # Database Enums (from generated)
    "PublicEntityTypeEnum",
    "PublicAssignmentRoleEnum",
    "PublicRequirementStatusEnum",
    "PublicAuditEventTypeEnum",
    "PublicAuditSeverityEnum",
    "PublicResourceTypeEnum",
    "UserRoleType",
    "InvitationStatus",
    "UserStatus",
    "BillingPlan",
    "PricingPlanInterval",
    "ProjectRole",
    "Visibility",
    "ProjectStatus",
    "ExecutionStatus",
    "RequirementPriority",
    "RequirementLevel",
    "SubscriptionStatus",
    "TestType",
    "TestPriority",
    "TestStatus",
    "TestMethod",
    "TraceLinkType",

    # Application Enums (manual)
    "QueryType",
    "RAGMode",
    "RelationshipType",

    # Row Schemas (for DB queries)
    "OrganizationRow",
    "ProjectRow",
    "DocumentRow",
    "RequirementRow",
    "TestRow",
    "ProfileRow",
    "BlockRow",
    "PropertyRow",
    "OrganizationMemberRow",
    "ProjectMemberRow",
    "RequirementTestRow",
    "OrganizationInvitationRow",

    # Pydantic Models (for API validation)
    "OrganizationInsert",
    "OrganizationUpdate",
    "Organization",
    "ProjectInsert",
    "ProjectUpdate",
    "Project",
    "DocumentInsert",
    "DocumentUpdate",
    "Document",
    "RequirementInsert",
    "RequirementUpdate",
    "Requirement",

    # Constants
    "Tables",
    "Fields",
    "TABLES_WITHOUT_SOFT_DELETE",
    "TABLES_WITHOUT_AUDIT_FIELDS",
    "ENTITY_TABLE_MAP",

    # RLS Validators
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

    # Trigger Emulators
    "TriggerEmulator",
]

