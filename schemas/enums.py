"""
Enum definitions for Atoms MCP - Database Schema Aligned.

All enums match the actual Supabase database enum types exactly.
These enums inherit from str to allow seamless string comparison
while providing type safety and IDE autocomplete.

IMPORTANT: These enums are derived from the actual database schema.
Do NOT modify enum values without corresponding database migrations.

Total Enums: 24 (Priority enums covering core business, requirements, tests, relationships, system)
Database Total: 44 enums (remaining enums are system/internal use)
"""

from enum import Enum


# =============================================================================
# PRIORITY 1 - CORE BUSINESS (MUST HAVE)
# =============================================================================

class OrganizationType(str, Enum):
    """
    Organization type enumeration - MUST match Supabase database enum exactly.

    Database: organization_type
    Default: personal

    Valid values in database:
    - personal (default)
    - team
    - enterprise

    NOTE: "business" is NOT a valid database value. Tests using "business" will fail.
    Always use OrganizationType.PERSONAL, OrganizationType.TEAM, or OrganizationType.ENTERPRISE.
    """
    PERSONAL = "personal"  # Default value in database
    TEAM = "team"
    ENTERPRISE = "enterprise"


class UserRoleType(str, Enum):
    """
    User role enumeration for system-wide user roles.

    Database: user_role_type
    """
    MEMBER = "member"
    ADMIN = "admin"
    OWNER = "owner"
    SUPER_ADMIN = "super_admin"


class UserStatus(str, Enum):
    """
    User account status.

    Database: user_status
    """
    ACTIVE = "active"
    INACTIVE = "inactive"


class BillingPlan(str, Enum):
    """
    Billing plan types for organizations.

    Database: billing_plan
    """
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class PricingPlanInterval(str, Enum):
    """
    Billing cycle intervals.

    Database: pricing_plan_interval
    Default: none
    """
    NONE = "none"  # Default value
    MONTH = "month"
    YEAR = "year"


class ProjectStatus(str, Enum):
    """
    Project lifecycle status.

    Database: project_status
    """
    ACTIVE = "active"
    ARCHIVED = "archived"
    DRAFT = "draft"
    DELETED = "deleted"


class ProjectRole(str, Enum):
    """
    Project member roles defining access levels.

    Database: project_role
    """
    OWNER = "owner"
    ADMIN = "admin"
    MAINTAINER = "maintainer"
    EDITOR = "editor"
    VIEWER = "viewer"


class Visibility(str, Enum):
    """
    Visibility levels for resources.

    Database: visibility
    """
    PRIVATE = "private"
    TEAM = "team"
    ORGANIZATION = "organization"
    PUBLIC = "public"


# =============================================================================
# PRIORITY 2 - REQUIREMENTS
# =============================================================================

class RequirementStatus(str, Enum):
    """
    Requirement lifecycle status.

    Database: requirement_status
    """
    ACTIVE = "active"
    ARCHIVED = "archived"
    DRAFT = "draft"
    DELETED = "deleted"
    IN_REVIEW = "in_review"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"


class RequirementFormat(str, Enum):
    """
    Requirement writing format standards.

    Database: requirement_format

    - incose: INCOSE standard format
    - ears: Easy Approach to Requirements Syntax
    - other: Custom or other formats
    """
    INCOSE = "incose"
    EARS = "ears"
    OTHER = "other"


class RequirementPriority(str, Enum):
    """
    Priority levels for requirements.

    Database: requirement_priority
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RequirementLevel(str, Enum):
    """
    Requirement hierarchy level in system architecture.

    Database: requirement_level
    """
    COMPONENT = "component"
    SYSTEM = "system"
    SUBSYSTEM = "subsystem"


# =============================================================================
# PRIORITY 3 - TESTS
# =============================================================================

class TestType(str, Enum):
    """
    Test types and categories.

    Database: test_type
    """
    UNIT = "unit"
    INTEGRATION = "integration"
    SYSTEM = "system"
    ACCEPTANCE = "acceptance"
    PERFORMANCE = "performance"
    SECURITY = "security"
    USABILITY = "usability"
    OTHER = "other"


class TestPriority(str, Enum):
    """
    Priority levels for tests.

    Database: test_priority
    """
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TestStatus(str, Enum):
    """
    Test definition status (not execution status).

    Database: test_status
    """
    DRAFT = "draft"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    OBSOLETE = "obsolete"


class TestMethod(str, Enum):
    """
    Test execution method.

    Database: test_method
    """
    MANUAL = "manual"
    AUTOMATED = "automated"
    HYBRID = "hybrid"


class ExecutionStatus(str, Enum):
    """
    Test execution result status.

    Database: execution_status

    This is separate from TestStatus - this tracks execution results,
    while TestStatus tracks test definition lifecycle.
    """
    NOT_EXECUTED = "not_executed"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


# =============================================================================
# PRIORITY 4 - RELATIONSHIPS
# =============================================================================

class InvitationStatus(str, Enum):
    """
    Status of organization/project invitations.

    Database: invitation_status
    """
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    REVOKED = "revoked"


class NotificationType(str, Enum):
    """
    Notification type categories.

    Database: notification_type
    """
    INVITATION = "invitation"
    MENTION = "mention"
    SYSTEM = "system"


class EntityType(str, Enum):
    """
    Valid entity types in the system.

    Database: entity_type

    NOTE: This is a subset. Full list includes organization, project,
    profile, block, property, organization_member, project_member, etc.
    """
    DOCUMENT = "document"
    REQUIREMENT = "requirement"
    # Extended types (not exhaustive - add as needed)
    ORGANIZATION = "organization"
    PROJECT = "project"
    TEST = "test"
    PROFILE = "profile"
    BLOCK = "block"
    PROPERTY = "property"
    ORGANIZATION_MEMBER = "organization_member"
    PROJECT_MEMBER = "project_member"
    REQUIREMENT_TEST = "requirement_test"
    ORGANIZATION_INVITATION = "organization_invitation"


class TraceLinkType(str, Enum):
    """
    Types of traceability links between requirements.

    Database: trace_link_type
    """
    DERIVES_FROM = "derives_from"
    IMPLEMENTS = "implements"
    RELATES_TO = "relates_to"
    CONFLICTS_WITH = "conflicts_with"
    IS_RELATED_TO = "is_related_to"
    PARENT_OF = "parent_of"
    CHILD_OF = "child_of"


class AssignmentRole(str, Enum):
    """
    Role types for entity assignments.

    Database: assignment_role
    """
    ASSIGNEE = "assignee"
    REVIEWER = "reviewer"
    APPROVER = "approver"


# =============================================================================
# PRIORITY 5 - SYSTEM
# =============================================================================

class SubscriptionStatus(str, Enum):
    """
    Subscription status for billing.

    Database: subscription_status
    """
    ACTIVE = "active"
    INACTIVE = "inactive"
    TRIALING = "trialing"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    PAUSED = "paused"


class AuditSeverity(str, Enum):
    """
    Severity level for audit log entries.

    Database: audit_severity
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# =============================================================================
# LEGACY/COMPATIBILITY ENUMS (for backward compatibility)
# =============================================================================

class EntityStatus(str, Enum):
    """
    Generic entity lifecycle status.

    NOTE: Use specific status enums (RequirementStatus, ProjectStatus, etc.)
    instead of this generic enum when possible.

    Database: Multiple status fields use similar values
    """
    ACTIVE = "active"
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"
    DELETED = "deleted"


class Priority(str, Enum):
    """
    Generic priority levels for requirements and tests.

    NOTE: Use specific priority enums (RequirementPriority, TestPriority)
    instead of this generic enum when possible.

    Database: Multiple priority fields use these values
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# =============================================================================
# MCP/QUERY ENUMS (not database enums, application-level)
# =============================================================================

class RelationshipType(str, Enum):
    """
    Types of relationships between entities (application-level categorization).

    NOTE: This is not a database enum - it's used for categorizing
    different relationship patterns in the application.
    """
    MEMBER = "member"
    ASSIGNMENT = "assignment"
    TRACE_LINK = "trace_link"
    REQUIREMENT_TEST = "requirement_test"
    INVITATION = "invitation"


class QueryType(str, Enum):
    """
    Data query operation types (application-level).

    NOTE: This is not a database enum - used by query_tool.
    """
    SEARCH = "search"
    AGGREGATE = "aggregate"
    ANALYZE = "analyze"
    RELATIONSHIPS = "relationships"
    RAG_SEARCH = "rag_search"
    SIMILARITY = "similarity"


class RAGMode(str, Enum):
    """
    RAG search modes (application-level).

    NOTE: This is not a database enum - used by RAG search system.
    """
    AUTO = "auto"
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    HYBRID = "hybrid"


class MemberRole(str, Enum):
    """
    Member roles for organizations and projects.

    NOTE: Deprecated - use ProjectRole or specific role enums instead.
    Kept for backward compatibility.
    """
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"
    OWNER = "owner"


class DocumentType(str, Enum):
    """
    Document types (application-level categorization).

    Database: doc_type field in documents table
    """
    TECHNICAL = "technical"
    API = "api"
    SPECIFICATION = "specification"
    DESIGN = "design"
    REQUIREMENT = "requirement"
    TEST_PLAN = "test_plan"


class CoverageLevel(str, Enum):
    """
    Coverage level for requirement-test relationships.

    Database: coverage_level in requirement_test junction table
    """
    FULL = "full"
    PARTIAL = "partial"
    NONE = "none"


# =============================================================================
# ENUM HELPERS
# =============================================================================

def get_enum_values(enum_class: type[Enum]) -> list[str]:
    """Get list of all valid string values for an enum."""
    return [e.value for e in enum_class]


def validate_enum_value(enum_class: type[Enum], value: str) -> bool:
    """Check if a string value is valid for an enum."""
    return value in get_enum_values(enum_class)
