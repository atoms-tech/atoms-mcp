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
from schemas.generated.fastapi.schema_public_latest import (
    # Database Enums (23 total - generated from Supabase)
    PublicEntityTypeEnum,
    PublicAssignmentRoleEnum,
    PublicRequirementStatusEnum,
    PublicAuditEventTypeEnum,
    PublicAuditSeverityEnum,
    PublicResourceTypeEnum,
    PublicUserRoleTypeEnum as UserRoleType,
    PublicInvitationStatusEnum as InvitationStatus,
    PublicUserStatusEnum as UserStatus,
    PublicBillingPlanEnum as BillingPlan,
    PublicPricingPlanIntervalEnum as PricingPlanInterval,
    PublicProjectRoleEnum as ProjectRole,
    PublicVisibilityEnum as Visibility,
    PublicProjectStatusEnum as ProjectStatus,
    PublicExecutionStatusEnum as ExecutionStatus,
    PublicRequirementPriorityEnum as RequirementPriority,
    PublicRequirementLevelEnum as RequirementLevel,
    PublicSubscriptionStatusEnum as SubscriptionStatus,
    PublicTestTypeEnum as TestType,
    PublicTestPriorityEnum as TestPriority,
    PublicTestStatusEnum as TestStatus,
    PublicTestMethodEnum as TestMethod,
    PublicTraceLinkTypeEnum as TraceLinkType,

    # Base Schemas (use as TypedDict-like for DB queries)
    OrganizationBaseSchema as OrganizationRow,
    ProjectBaseSchema as ProjectRow,
    DocumentBaseSchema as DocumentRow,
    RequirementBaseSchema as RequirementRow,
    TestReqBaseSchema as TestRow,
    ProfileBaseSchema as ProfileRow,
    BlockBaseSchema as BlockRow,
    PropertyBaseSchema as PropertyRow,
    OrganizationMemberBaseSchema as OrganizationMemberRow,
    ProjectMemberBaseSchema as ProjectMemberRow,
    RequirementTestBaseSchema as RequirementTestRow,
    OrganizationInvitationBaseSchema as OrganizationInvitationRow,

    # Insert/Update Models (for API validation)
    OrganizationInsert,
    OrganizationUpdate,
    Organization,
    ProjectInsert,
    ProjectUpdate,
    Project,
    DocumentInsert,
    DocumentUpdate,
    Document,
    RequirementInsert,
    RequirementUpdate,
    Requirement,
)

# SECONDARY: Manual additions for application logic
from schemas.constants import (
    Tables,
    Fields,
    TABLES_WITHOUT_SOFT_DELETE,
    TABLES_WITHOUT_AUDIT_FIELDS,
    ENTITY_TABLE_MAP,
)

# Application-level enums (not in database, used by MCP tools)
from schemas.enums import (
    QueryType,
    RAGMode,
    RelationshipType,
)

# RLS validators
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

