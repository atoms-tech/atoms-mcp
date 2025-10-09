from __future__ import annotations

import datetime
from enum import Enum
from ipaddress import IPv4Address, IPv6Address
from typing import Annotated, Any

from pydantic import UUID4, BaseModel, Field, Json
from pydantic.types import StringConstraints

# ENUM TYPES
# These are generated from Postgres user-defined enum types.


class PublicEntityTypeEnum(str, Enum):
    DOCUMENT = "document"
    REQUIREMENT = "requirement"


class PublicAssignmentRoleEnum(str, Enum):
    ASSIGNEE = "assignee"
    REVIEWER = "reviewer"
    APPROVER = "approver"


class PublicRequirementStatusEnum(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DRAFT = "draft"
    DELETED = "deleted"
    IN_REVIEW = "in_review"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"


class PublicAuditEventTypeEnum(str, Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGE = "password_change"
    MFA_ENABLED = "mfa_enabled"
    MFA_DISABLED = "mfa_disabled"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_DENIED = "permission_denied"
    ROLE_ASSIGNED = "role_assigned"
    ROLE_REMOVED = "role_removed"
    DATA_CREATED = "data_created"
    DATA_READ = "data_read"
    DATA_UPDATED = "data_updated"
    DATA_DELETED = "data_deleted"
    DATA_EXPORTED = "data_exported"
    SYSTEM_CONFIG_CHANGED = "system_config_changed"
    BACKUP_CREATED = "backup_created"
    BACKUP_RESTORED = "backup_restored"
    SECURITY_VIOLATION = "security_violation"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    COMPLIANCE_REPORT_GENERATED = "compliance_report_generated"
    AUDIT_LOG_ACCESSED = "audit_log_accessed"
    DATA_RETENTION_APPLIED = "data_retention_applied"


class PublicAuditSeverityEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PublicResourceTypeEnum(str, Enum):
    ORGANIZATION = "organization"
    PROJECT = "project"
    DOCUMENT = "document"
    REQUIREMENT = "requirement"
    USER = "user"
    MEMBER = "member"
    INVITATION = "invitation"
    ROLE = "role"
    PERMISSION = "permission"
    EXTERNAL_DOCUMENT = "external_document"
    DIAGRAM = "diagram"
    TRACE_LINK = "trace_link"
    ASSIGNMENT = "assignment"
    AUDIT_LOG = "audit_log"
    SECURITY_EVENT = "security_event"
    SYSTEM_CONFIG = "system_config"
    COMPLIANCE_REPORT = "compliance_report"


class PublicUserRoleTypeEnum(str, Enum):
    MEMBER = "member"
    ADMIN = "admin"
    OWNER = "owner"
    SUPER_ADMIN = "super_admin"


class PublicInvitationStatusEnum(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    REVOKED = "revoked"


class PublicUserStatusEnum(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class PublicBillingPlanEnum(str, Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class PublicPricingPlanIntervalEnum(str, Enum):
    NONE = "none"
    MONTH = "month"
    YEAR = "year"


class PublicProjectRoleEnum(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MAINTAINER = "maintainer"
    EDITOR = "editor"
    VIEWER = "viewer"


class PublicVisibilityEnum(str, Enum):
    PRIVATE = "private"
    TEAM = "team"
    ORGANIZATION = "organization"
    PUBLIC = "public"


class PublicProjectStatusEnum(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DRAFT = "draft"
    DELETED = "deleted"


class PublicExecutionStatusEnum(str, Enum):
    NOT_EXECUTED = "not_executed"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


class PublicRequirementPriorityEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PublicRequirementLevelEnum(str, Enum):
    COMPONENT = "component"
    SYSTEM = "system"
    SUBSYSTEM = "subsystem"


class PublicSubscriptionStatusEnum(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    TRIALING = "trialing"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    PAUSED = "paused"


class PublicTestTypeEnum(str, Enum):
    UNIT = "unit"
    INTEGRATION = "integration"
    SYSTEM = "system"
    ACCEPTANCE = "acceptance"
    PERFORMANCE = "performance"
    SECURITY = "security"
    USABILITY = "usability"
    OTHER = "other"


class PublicTestPriorityEnum(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class PublicTestStatusEnum(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    OBSOLETE = "obsolete"


class PublicTestMethodEnum(str, Enum):
    MANUAL = "manual"
    AUTOMATED = "automated"
    HYBRID = "hybrid"


class PublicTraceLinkTypeEnum(str, Enum):
    DERIVES_FROM = "derives_from"
    IMPLEMENTS = "implements"
    RELATES_TO = "relates_to"
    CONFLICTS_WITH = "conflicts_with"
    IS_RELATED_TO = "is_related_to"
    PARENT_OF = "parent_of"
    CHILD_OF = "child_of"


# CUSTOM CLASSES
# Note: These are custom model classes for defining common features among
# Pydantic Base Schema.


class CustomModel(BaseModel):
    """Base model class with common features."""

    pass


class CustomModelInsert(CustomModel):
    """Base model for insert operations with common features."""

    pass


class CustomModelUpdate(CustomModel):
    """Base model for update operations with common features."""

    pass


# BASE CLASSES
# Note: These are the base Row models that include all fields.


class AssignmentBaseSchema(CustomModel):
    """Assignment Base Schema."""

    # Primary Keys
    id: UUID4

    # Columns
    assignee_id: UUID4
    comment: str | None = Field(default=None)
    completed_at: datetime.datetime | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    created_by: UUID4 | None = Field(default=None)
    deleted_at: datetime.datetime | None = Field(default=None)
    deleted_by: UUID4 | None = Field(default=None)
    due_date: datetime.datetime | None = Field(default=None)
    entity_id: UUID4
    entity_type: PublicEntityTypeEnum
    is_deleted: bool | None = Field(default=None)
    role: PublicAssignmentRoleEnum
    status: PublicRequirementStatusEnum
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: UUID4 | None = Field(default=None)
    version: int


class AuditLogBaseSchema(CustomModel):
    """AuditLog Base Schema."""

    # Primary Keys
    id: UUID4

    # Columns
    action: str
    actor_id: UUID4 | None = Field(default=None)
    compliance_category: str | None = Field(default=None)
    correlation_id: UUID4 | None = Field(default=None)
    created_at: datetime.datetime
    description: str | None = Field(default=None)
    details: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    entity_id: UUID4
    entity_type: str
    event_type: PublicAuditEventTypeEnum | None = Field(default=None)
    ip_address: IPv4Address | IPv6Address | None = Field(default=None)
    metadata: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    new_data: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    old_data: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    organization_id: UUID4 | None = Field(default=None)
    project_id: UUID4 | None = Field(default=None)
    resource_id: UUID4 | None = Field(default=None)
    resource_type: PublicResourceTypeEnum | None = Field(default=None)
    risk_level: str | None = Field(default=None)
    session_id: str | None = Field(default=None)
    severity: PublicAuditSeverityEnum | None = Field(default=None)
    soc2_control: str | None = Field(default=None)
    source_system: str | None = Field(default=None)
    threat_indicators: list[str] | None = Field(default=None)
    timestamp: datetime.datetime | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    user_agent: str | None = Field(default=None)
    user_id: UUID4 | None = Field(default=None)


class BillingCacheBaseSchema(CustomModel):
    """BillingCache Base Schema."""

    # Primary Keys
    organization_id: UUID4

    # Columns
    billing_status: dict | list[dict] | list[Any] | Json
    current_period_usage: dict | list[dict] | list[Any] | Json
    period_end: datetime.datetime
    period_start: datetime.datetime
    synced_at: datetime.datetime


class BlockBaseSchema(CustomModel):
    """Block Base Schema."""

    # Primary Keys
    id: UUID4

    # Columns
    content: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    created_by: UUID4 | None = Field(default=None)
    deleted_at: datetime.datetime | None = Field(default=None)
    deleted_by: UUID4 | None = Field(default=None)
    document_id: UUID4
    field_type: str = Field(alias="type")
    is_deleted: bool | None = Field(default=None)
    name: str
    org_id: UUID4 | None = Field(default=None)
    position: int
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: UUID4 | None = Field(default=None)
    version: int


class ColumnBaseSchema(CustomModel):
    """Column Base Schema."""

    # Primary Keys
    id: UUID4

    # Columns
    block_id: UUID4 | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    created_by: UUID4 | None = Field(default=None)
    default_value: str | None = Field(default=None)
    is_hidden: bool | None = Field(default=None)
    is_pinned: bool | None = Field(default=None)
    position: float
    property_id: UUID4
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: UUID4 | None = Field(default=None)
    width: int | None = Field(default=None)


class DiagramElementLinkBaseSchema(CustomModel):
    """DiagramElementLink Base Schema."""

    # Primary Keys
    id: UUID4

    # Columns
    created_at: datetime.datetime | None = Field(default=None)
    created_by: UUID4 | None = Field(default=None)
    diagram_id: UUID4
    element_id: str = Field(description="Excalidraw element ID from the diagram")
    link_type: str | None = Field(
        default=None, description="Whether link was created manually or auto-detected"
    )
    metadata: dict | list[dict] | list[Any] | Json | None = Field(
        default=None,
        description="Additional data like element type, text, confidence scores",
    )
    requirement_id: UUID4
    updated_at: datetime.datetime | None = Field(default=None)


class DiagramElementLinksWithDetailBaseSchema(CustomModel):
    """DiagramElementLinksWithDetail Base Schema."""

    # Columns
    created_at: datetime.datetime | None = Field(default=None)
    created_by: UUID4 | None = Field(default=None)
    created_by_avatar: str | None = Field(default=None)
    created_by_name: str | None = Field(default=None)
    diagram_id: UUID4 | None = Field(default=None)
    diagram_name: str | None = Field(default=None)
    element_id: str | None = Field(default=None)
    id: UUID4 | None = Field(default=None)
    link_type: str | None = Field(default=None)
    metadata: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    requirement_description: str | None = Field(default=None)
    requirement_id: UUID4 | None = Field(default=None)
    requirement_name: str | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)


class DocumentBaseSchema(CustomModel):
    """Document Base Schema."""

    # Primary Keys
    id: UUID4

    # Columns
    created_at: datetime.datetime | None = Field(default=None)
    created_by: UUID4 | None = Field(default=None)
    deleted_at: datetime.datetime | None = Field(default=None)
    deleted_by: UUID4 | None = Field(default=None)
    description: str | None = Field(default=None)
    embedding: Any | None = Field(default=None)
    fts_vector: str | None = Field(
        default=None,
        description="Full-text search vector: name(A) + description(B) + slug(C)",
    )
    is_deleted: bool | None = Field(default=None)
    name: str
    project_id: UUID4
    slug: str
    tags: list[str] | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: UUID4 | None = Field(default=None)
    version: int


class EmbeddingCacheBaseSchema(CustomModel):
    """EmbeddingCache Base Schema."""

    # Primary Keys
    id: UUID4

    # Columns
    access_count: int | None = Field(default=None)
    accessed_at: datetime.datetime | None = Field(default=None)
    cache_key: str
    created_at: datetime.datetime | None = Field(default=None)
    embedding: Any | None = Field(default=None)
    model: str
    tokens_used: int


class ExcalidrawDiagramBaseSchema(CustomModel):
    """ExcalidrawDiagram Base Schema."""

    # Primary Keys
    id: UUID4

    # Columns
    created_at: datetime.datetime | None = Field(default=None)
    created_by: UUID4 | None = Field(default=None)
    diagram_data: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    name: str | None = Field(default=None)
    organization_id: UUID4 | None = Field(default=None)
    project_id: UUID4 | None = Field(default=None)
    thumbnail_url: str | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: UUID4 | None = Field(default=None)


class ExcalidrawElementLinkBaseSchema(CustomModel):
    """ExcalidrawElementLink Base Schema."""

    # Primary Keys
    id: UUID4

    # Columns
    create_by: UUID4 | None = Field(default=None)
    created_at: datetime.datetime
    element_id: str | None = Field(default=None)
    excalidraw_canvas_id: UUID4 | None = Field(default=None)
    requirement_id: UUID4 | None = Field(default=None)


class ExternalDocumentBaseSchema(CustomModel):
    """ExternalDocument Base Schema."""

    # Primary Keys
    id: UUID4

    # Columns
    created_at: datetime.datetime | None = Field(default=None)
    created_by: UUID4 | None = Field(default=None)
    deleted_at: datetime.datetime | None = Field(default=None)
    deleted_by: UUID4 | None = Field(default=None)
    field_type: str | None = Field(default=None, alias="type")
    gumloop_name: str | None = Field(default=None)
    is_deleted: bool | None = Field(default=None)
    name: str
    organization_id: UUID4
    owned_by: UUID4 | None = Field(default=None)
    size: int | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: UUID4 | None = Field(default=None)
    url: str | None = Field(default=None)


class McpSessionBaseSchema(CustomModel):
    """McpSession Base Schema."""

    # Primary Keys
    session_id: str

    # Columns
    created_at: datetime.datetime | None = Field(default=None)
    expires_at: datetime.datetime
    mcp_state: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    oauth_data: dict | list[dict] | list[Any] | Json
    updated_at: datetime.datetime | None = Field(default=None)
    user_id: UUID4


class NotificationBaseSchema(CustomModel):
    """Notification Base Schema."""

    # Primary Keys
    id: UUID4

    # Columns
    created_at: datetime.datetime | None = Field(default=None)
    field_type: Any = Field(alias="type")
    message: str | None = Field(default=None)
    metadata: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    read_at: datetime.datetime | None = Field(default=None)
    title: str
    unread: bool | None = Field(default=None)
    user_id: UUID4


class OauthAccessTokenBaseSchema(CustomModel):
    """OauthAccessToken Base Schema."""

    # Primary Keys
    id: UUID4

    # Columns
    client_id: str
    created_at: datetime.datetime | None = Field(default=None)
    expires_at: datetime.datetime
    last_used_at: datetime.datetime | None = Field(default=None)
    scope: str | None = Field(default=None)
    token_hash: str
    user_id: UUID4 | None = Field(default=None)


class OauthAuthorizationCodeBaseSchema(CustomModel):
    """OauthAuthorizationCode Base Schema."""

    # Primary Keys
    id: UUID4

    # Columns
    client_id: str
    code: str
    code_challenge: str
    code_challenge_method: str
    created_at: datetime.datetime | None = Field(default=None)
    expires_at: datetime.datetime
    redirect_uri: str
    scope: str | None = Field(default=None)
    state: str | None = Field(default=None)
    user_id: UUID4 | None = Field(default=None)


class OauthClientBaseSchema(CustomModel):
    """OauthClient Base Schema."""

    # Primary Keys
    id: UUID4

    # Columns
    client_id: str
    client_name: str
    client_secret: str | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    grant_types: dict | list[dict] | list[Any] | Json
    is_public: bool | None = Field(default=None)
    redirect_uris: dict | list[dict] | list[Any] | Json
    response_types: dict | list[dict] | list[Any] | Json
    scope: str | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)


class OauthRefreshTokenBaseSchema(CustomModel):
    """OauthRefreshToken Base Schema."""

    # Primary Keys
    id: UUID4

    # Columns
    client_id: str
    created_at: datetime.datetime | None = Field(default=None)
    expires_at: datetime.datetime
    last_used_at: datetime.datetime | None = Field(default=None)
    scope: str | None = Field(default=None)
    token: str
    user_id: UUID4


class OrganizationInvitationBaseSchema(CustomModel):
    """OrganizationInvitation Base Schema."""

    # Primary Keys
    id: UUID4

    # Columns
    created_at: datetime.datetime | None = Field(default=None)
    created_by: UUID4
    deleted_at: datetime.datetime | None = Field(default=None)
    deleted_by: UUID4 | None = Field(default=None)
    email: str
    expires_at: datetime.datetime
    is_deleted: bool | None = Field(default=None)
    metadata: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    organization_id: UUID4
    role: PublicUserRoleTypeEnum
    status: PublicInvitationStatusEnum
    token: UUID4
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: UUID4


class OrganizationMemberBaseSchema(CustomModel):
    """OrganizationMember Base Schema."""

    # Primary Keys
    id: UUID4

    # Columns
    created_at: datetime.datetime | None = Field(default=None)
    deleted_at: datetime.datetime | None = Field(default=None)
    deleted_by: UUID4 | None = Field(default=None)
    is_deleted: bool | None = Field(default=None)
    last_active_at: datetime.datetime | None = Field(default=None)
    organization_id: UUID4
    permissions: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    role: PublicUserRoleTypeEnum
    status: PublicUserStatusEnum | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: UUID4 | None = Field(default=None)
    user_id: UUID4


class OrganizationBaseSchema(CustomModel):
    """Organization Base Schema."""

    # Primary Keys
    id: UUID4

    # Columns
    billing_cycle: PublicPricingPlanIntervalEnum
    billing_plan: PublicBillingPlanEnum
    created_at: datetime.datetime | None = Field(default=None)
    created_by: UUID4
    deleted_at: datetime.datetime | None = Field(default=None)
    deleted_by: UUID4 | None = Field(default=None)
    description: str | None = Field(default=None)
    embedding: Any | None = Field(default=None)
    field_type: Any = Field(alias="type")
    fts_vector: str | None = Field(
        default=None,
        description="Full-text search vector: name(A) + description(B) + slug(C)",
    )
    is_deleted: bool | None = Field(default=None)
    logo_url: str | None = Field(default=None)
    max_members: int
    max_monthly_requests: int
    member_count: int | None = Field(default=None)
    metadata: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    name: Annotated[str, StringConstraints(**{"min_length": 2, "max_length": 255})]
    owner_id: UUID4 | None = Field(default=None)
    settings: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    slug: str
    status: PublicUserStatusEnum | None = Field(default=None)
    storage_used: int | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: UUID4


class ProfileBaseSchema(CustomModel):
    """Profile Base Schema."""

    # Primary Keys
    id: UUID4

    # Columns
    avatar_url: str | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    current_organization_id: UUID4 | None = Field(default=None)
    deleted_at: datetime.datetime | None = Field(default=None)
    deleted_by: UUID4 | None = Field(default=None)
    email: str
    full_name: str | None = Field(default=None)
    is_approved: bool
    is_deleted: bool | None = Field(default=None)
    job_title: str | None = Field(default=None)
    last_login_at: datetime.datetime | None = Field(default=None)
    login_count: int | None = Field(default=None)
    personal_organization_id: UUID4 | None = Field(default=None)
    pinned_organization_id: UUID4 | None = Field(default=None)
    preferences: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    status: PublicUserStatusEnum | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)


class ProjectInvitationBaseSchema(CustomModel):
    """ProjectInvitation Base Schema."""

    # Primary Keys
    id: UUID4

    # Columns
    created_at: datetime.datetime | None = Field(default=None)
    created_by: UUID4
    deleted_at: datetime.datetime | None = Field(default=None)
    deleted_by: UUID4 | None = Field(default=None)
    email: str
    expires_at: datetime.datetime
    is_deleted: bool | None = Field(default=None)
    metadata: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    project_id: UUID4
    role: PublicProjectRoleEnum
    status: PublicInvitationStatusEnum
    token: UUID4
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: UUID4


class ProjectMemberBaseSchema(CustomModel):
    """ProjectMember Base Schema."""

    # Primary Keys
    id: UUID4

    # Columns
    created_at: datetime.datetime | None = Field(default=None)
    deleted_at: datetime.datetime | None = Field(default=None)
    deleted_by: UUID4 | None = Field(default=None)
    is_deleted: bool | None = Field(default=None)
    last_accessed_at: datetime.datetime | None = Field(default=None)
    org_id: UUID4 | None = Field(default=None)
    permissions: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    project_id: UUID4
    role: PublicProjectRoleEnum
    status: PublicUserStatusEnum | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    user_id: UUID4


class ProjectBaseSchema(CustomModel):
    """Project Base Schema."""

    # Primary Keys
    id: UUID4

    # Columns
    created_at: datetime.datetime | None = Field(default=None)
    created_by: UUID4
    deleted_at: datetime.datetime | None = Field(default=None)
    deleted_by: UUID4 | None = Field(default=None)
    description: str | None = Field(default=None)
    embedding: Any | None = Field(default=None)
    fts_vector: str | None = Field(
        default=None,
        description="Full-text search vector: name(A) + description(B) + slug(C)",
    )
    is_deleted: bool | None = Field(default=None)
    metadata: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    name: Annotated[str, StringConstraints(**{"min_length": 2, "max_length": 255})]
    organization_id: UUID4
    owned_by: UUID4
    settings: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    slug: str
    star_count: int | None = Field(default=None)
    status: PublicProjectStatusEnum
    tags: list[str] | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: UUID4
    version: int | None = Field(default=None)
    visibility: PublicVisibilityEnum


class PropertyBaseSchema(CustomModel):
    """Property Base Schema."""

    # Primary Keys
    id: UUID4

    # Columns
    created_at: datetime.datetime | None = Field(default=None)
    created_by: UUID4 | None = Field(default=None)
    deleted_at: datetime.datetime | None = Field(default=None)
    deleted_by: UUID4 | None = Field(default=None)
    document_id: UUID4 | None = Field(default=None)
    is_base: bool | None = Field(default=None)
    is_deleted: bool
    name: str
    options: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    org_id: UUID4
    project_id: UUID4 | None = Field(default=None)
    property_type: str
    scope: str | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: UUID4 | None = Field(default=None)


class RagEmbeddingBaseSchema(CustomModel):
    """RagEmbedding Base Schema."""

    # Primary Keys
    id: UUID4

    # Columns
    content_hash: str | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    embedding: Any
    entity_id: str
    entity_type: str
    metadata: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    quality_score: float | None = Field(default=None)


class RagSearchAnalyticBaseSchema(CustomModel):
    """RagSearchAnalytic Base Schema."""

    # Primary Keys
    id: UUID4

    # Columns
    cache_hit: bool
    created_at: datetime.datetime | None = Field(default=None)
    execution_time_ms: int
    organization_id: UUID4 | None = Field(default=None)
    query_hash: str
    query_text: str
    result_count: int
    search_type: str
    user_id: UUID4 | None = Field(default=None)


class ReactFlowDiagramBaseSchema(CustomModel):
    """ReactFlowDiagram Base Schema."""

    # Primary Keys
    id: UUID4

    # Columns
    created_at: datetime.datetime | None = Field(default=None)
    created_by: UUID4 | None = Field(default=None)
    description: str | None = Field(default=None)
    diagram_type: str | None = Field(default=None)
    edges: dict | list[dict] | list[Any] | Json
    layout_algorithm: str | None = Field(default=None)
    metadata: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    name: str
    nodes: dict | list[dict] | list[Any] | Json
    project_id: UUID4
    settings: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    theme: str | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: UUID4 | None = Field(default=None)
    viewport: dict | list[dict] | list[Any] | Json | None = Field(default=None)


class RequirementTestBaseSchema(CustomModel):
    """RequirementTest Base Schema."""

    # Primary Keys
    id: UUID4

    # Columns
    created_at: datetime.datetime | None = Field(default=None)
    defects: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    evidence_artifacts: dict | list[dict] | list[Any] | Json | None = Field(
        default=None
    )
    executed_at: datetime.datetime | None = Field(default=None)
    executed_by: UUID4 | None = Field(default=None)
    execution_environment: str | None = Field(default=None)
    execution_status: PublicExecutionStatusEnum
    execution_version: str | None = Field(default=None)
    external_req_id: str | None = Field(default=None)
    external_test_id: str | None = Field(default=None)
    requirement_id: UUID4
    result_notes: str | None = Field(default=None)
    test_id: UUID4
    updated_at: datetime.datetime | None = Field(default=None)


class RequirementBaseSchema(CustomModel):
    """Requirement Base Schema."""

    # Primary Keys
    id: UUID4

    # Columns
    ai_analysis: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    block_id: UUID4
    created_at: datetime.datetime | None = Field(default=None)
    created_by: UUID4 | None = Field(default=None)
    deleted_at: datetime.datetime | None = Field(default=None)
    deleted_by: UUID4 | None = Field(default=None)
    description: str | None = Field(default=None)
    document_id: UUID4
    embedding: Any | None = Field(default=None)
    enchanced_requirement: str | None = Field(default=None)
    external_id: str | None = Field(default=None)
    field_format: Any = Field(alias="format")
    field_type: str | None = Field(default=None, alias="type")
    fts_vector: str | None = Field(
        default=None,
        description="Full-text search vector: name(A) + description(B) + requirements(C)",
    )
    is_deleted: bool | None = Field(default=None)
    level: PublicRequirementLevelEnum
    name: str
    original_requirement: str | None = Field(default=None)
    position: float
    priority: PublicRequirementPriorityEnum
    properties: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    status: PublicRequirementStatusEnum
    tags: list[str] | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: UUID4 | None = Field(default=None)
    version: int


class RequirementsClosureBaseSchema(CustomModel):
    """RequirementsClosure Base Schema."""

    # Primary Keys
    ancestor_id: UUID4
    descendant_id: UUID4

    # Columns
    created_at: datetime.datetime
    created_by: UUID4
    depth: int
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: UUID4 | None = Field(default=None)


class StripeCustomerBaseSchema(CustomModel):
    """StripeCustomer Base Schema."""

    # Primary Keys
    id: UUID4

    # Columns
    cancel_at_period_end: bool | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    current_period_end: datetime.datetime | None = Field(default=None)
    current_period_start: datetime.datetime | None = Field(default=None)
    organization_id: UUID4 | None = Field(default=None)
    payment_method_brand: str | None = Field(default=None)
    payment_method_last4: str | None = Field(default=None)
    price_id: str | None = Field(default=None)
    stripe_customer_id: str | None = Field(default=None)
    stripe_subscription_id: str | None = Field(default=None)
    subscription_status: PublicSubscriptionStatusEnum
    updated_at: datetime.datetime | None = Field(default=None)


class TableRowBaseSchema(CustomModel):
    """TableRow Base Schema."""

    # Primary Keys
    id: UUID4

    # Columns
    block_id: UUID4
    created_at: datetime.datetime | None = Field(default=None)
    created_by: UUID4 | None = Field(default=None)
    deleted_at: datetime.datetime | None = Field(default=None)
    deleted_by: UUID4 | None = Field(default=None)
    document_id: UUID4
    is_deleted: bool | None = Field(default=None)
    position: float
    row_data: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: UUID4 | None = Field(default=None)
    version: int


class TestMatrixViewBaseSchema(CustomModel):
    """TestMatrixView Base Schema."""

    # Primary Keys
    id: UUID4

    # Columns
    configuration: dict | list[dict] | list[Any] | Json
    created_at: datetime.datetime | None = Field(default=None)
    created_by: UUID4
    is_active: bool | None = Field(default=None)
    is_default: bool | None = Field(default=None)
    name: str
    project_id: UUID4
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: UUID4


class TestReqBaseSchema(CustomModel):
    """TestReq Base Schema."""

    # Primary Keys
    id: UUID4

    # Columns
    attachments: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    category: list[str] | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    created_by: UUID4 | None = Field(default=None)
    deleted_at: datetime.datetime | None = Field(default=None)
    deleted_by: UUID4 | None = Field(default=None)
    description: str | None = Field(default=None)
    estimated_duration: datetime.timedelta | None = Field(default=None)
    expected_results: str | None = Field(default=None)
    is_active: bool | None = Field(default=None)
    is_deleted: bool
    method: PublicTestMethodEnum
    preconditions: str | None = Field(default=None)
    priority: PublicTestPriorityEnum
    project_id: UUID4 | None = Field(default=None)
    result: str | None = Field(default=None)
    status: PublicTestStatusEnum
    test_environment: str | None = Field(default=None)
    test_id: str | None = Field(default=None)
    test_steps: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    test_type: PublicTestTypeEnum
    title: str
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: UUID4 | None = Field(default=None)
    version: str | None = Field(default=None)


class TraceLinkBaseSchema(CustomModel):
    """TraceLink Base Schema."""

    # Primary Keys
    id: UUID4

    # Columns
    created_at: datetime.datetime | None = Field(default=None)
    created_by: UUID4 | None = Field(default=None)
    deleted_at: datetime.datetime | None = Field(default=None)
    deleted_by: UUID4 | None = Field(default=None)
    description: str | None = Field(default=None)
    is_deleted: bool | None = Field(default=None)
    link_type: PublicTraceLinkTypeEnum
    source_id: UUID4
    source_type: PublicEntityTypeEnum
    target_id: UUID4
    target_type: PublicEntityTypeEnum
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: UUID4 | None = Field(default=None)
    version: int


class UsageLogBaseSchema(CustomModel):
    """UsageLog Base Schema."""

    # Primary Keys
    id: UUID4

    # Columns
    created_at: datetime.datetime | None = Field(default=None)
    feature: str
    metadata: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    organization_id: UUID4
    quantity: int
    unit_type: str
    user_id: UUID4


class UserRoleBaseSchema(CustomModel):
    """UserRole Base Schema."""

    # Primary Keys
    id: UUID4

    # Columns
    admin_role: PublicUserRoleTypeEnum | None = Field(default=None)
    created_at: datetime.datetime
    document_id: UUID4 | None = Field(default=None)
    document_role: PublicProjectRoleEnum | None = Field(default=None)
    org_id: UUID4 | None = Field(default=None)
    project_id: UUID4 | None = Field(default=None)
    project_role: PublicProjectRoleEnum | None = Field(default=None)
    updated_at: datetime.datetime
    user_id: UUID4


# INSERT CLASSES
# Note: These models are used for insert operations. Auto-generated fields
# (like IDs and timestamps) are optional.


class AssignmentInsert(CustomModelInsert):
    """Assignment Insert Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)  # has default value

    # Field properties:
    # comment: nullable
    # completed_at: nullable
    # created_at: nullable, has default value
    # created_by: nullable
    # deleted_at: nullable
    # deleted_by: nullable
    # due_date: nullable
    # is_deleted: nullable, has default value
    # updated_at: nullable, has default value
    # updated_by: nullable
    # version: has default value

    # Required fields
    assignee_id: UUID4
    entity_id: UUID4
    entity_type: PublicEntityTypeEnum
    role: PublicAssignmentRoleEnum
    status: PublicRequirementStatusEnum

    # Optional fields
    comment: str | None = Field(default=None)
    completed_at: datetime.datetime | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    created_by: UUID4 | None = Field(default=None)
    deleted_at: datetime.datetime | None = Field(default=None)
    deleted_by: UUID4 | None = Field(default=None)
    due_date: datetime.datetime | None = Field(default=None)
    is_deleted: bool | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: UUID4 | None = Field(default=None)
    version: int | None = Field(default=None)


class AuditLogInsert(CustomModelInsert):
    """AuditLog Insert Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)  # has default value

    # Field properties:
    # actor_id: nullable
    # compliance_category: nullable
    # correlation_id: nullable
    # created_at: has default value
    # description: nullable
    # details: nullable
    # event_type: nullable
    # ip_address: nullable
    # metadata: nullable, has default value
    # new_data: nullable
    # old_data: nullable
    # organization_id: nullable
    # project_id: nullable
    # resource_id: nullable
    # resource_type: nullable
    # risk_level: nullable
    # session_id: nullable
    # severity: nullable, has default value
    # soc2_control: nullable
    # source_system: nullable
    # threat_indicators: nullable
    # timestamp: nullable
    # updated_at: nullable
    # user_agent: nullable
    # user_id: nullable

    # Required fields
    action: str
    entity_id: UUID4
    entity_type: str

    # Optional fields
    actor_id: UUID4 | None = Field(default=None)
    compliance_category: str | None = Field(default=None)
    correlation_id: UUID4 | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    description: str | None = Field(default=None)
    details: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    event_type: PublicAuditEventTypeEnum | None = Field(default=None)
    ip_address: IPv4Address | IPv6Address | None = Field(default=None)
    metadata: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    new_data: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    old_data: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    organization_id: UUID4 | None = Field(default=None)
    project_id: UUID4 | None = Field(default=None)
    resource_id: UUID4 | None = Field(default=None)
    resource_type: PublicResourceTypeEnum | None = Field(default=None)
    risk_level: str | None = Field(default=None)
    session_id: str | None = Field(default=None)
    severity: PublicAuditSeverityEnum | None = Field(default=None)
    soc2_control: str | None = Field(default=None)
    source_system: str | None = Field(default=None)
    threat_indicators: list[str] | None = Field(default=None)
    timestamp: datetime.datetime | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    user_agent: str | None = Field(default=None)
    user_id: UUID4 | None = Field(default=None)


class BillingCacheInsert(CustomModelInsert):
    """BillingCache Insert Schema."""

    # Primary Keys
    organization_id: UUID4

    # Field properties:
    # billing_status: has default value
    # current_period_usage: has default value
    # period_end: has default value
    # period_start: has default value
    # synced_at: has default value

    # Optional fields
    billing_status: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    current_period_usage: dict | list[dict] | list[Any] | Json | None = Field(
        default=None
    )
    period_end: datetime.datetime | None = Field(default=None)
    period_start: datetime.datetime | None = Field(default=None)
    synced_at: datetime.datetime | None = Field(default=None)


class BlockInsert(CustomModelInsert):
    """Block Insert Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)  # has default value

    # Field properties:
    # content: nullable, has default value
    # created_at: nullable, has default value
    # created_by: nullable
    # deleted_at: nullable
    # deleted_by: nullable
    # is_deleted: nullable, has default value
    # name: has default value
    # org_id: nullable
    # updated_at: nullable, has default value
    # updated_by: nullable
    # version: has default value

    # Required fields
    document_id: UUID4
    field_type: str = Field(alias="type")
    position: int

    # Optional fields
    content: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    created_by: UUID4 | None = Field(default=None)
    deleted_at: datetime.datetime | None = Field(default=None)
    deleted_by: UUID4 | None = Field(default=None)
    is_deleted: bool | None = Field(default=None)
    name: str | None = Field(default=None)
    org_id: UUID4 | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: UUID4 | None = Field(default=None)
    version: int | None = Field(default=None)


class ColumnInsert(CustomModelInsert):
    """Column Insert Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)  # has default value

    # Field properties:
    # block_id: nullable
    # created_at: nullable, has default value
    # created_by: nullable
    # default_value: nullable
    # is_hidden: nullable, has default value
    # is_pinned: nullable, has default value
    # updated_at: nullable, has default value
    # updated_by: nullable
    # width: nullable, has default value

    # Required fields
    position: float
    property_id: UUID4

    # Optional fields
    block_id: UUID4 | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    created_by: UUID4 | None = Field(default=None)
    default_value: str | None = Field(default=None)
    is_hidden: bool | None = Field(default=None)
    is_pinned: bool | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: UUID4 | None = Field(default=None)
    width: int | None = Field(default=None)


class DiagramElementLinkInsert(CustomModelInsert):
    """DiagramElementLink Insert Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)  # has default value

    # Field properties:
    # created_at: nullable, has default value
    # created_by: nullable
    # link_type: nullable, has default value
    # metadata: nullable, has default value
    # updated_at: nullable, has default value

    # Required fields
    diagram_id: UUID4
    element_id: str = Field(description="Excalidraw element ID from the diagram")
    requirement_id: UUID4

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    created_by: UUID4 | None = Field(default=None)
    link_type: str | None = Field(
        default=None, description="Whether link was created manually or auto-detected"
    )
    metadata: dict | list[dict] | list[Any] | Json | None = Field(
        default=None,
        description="Additional data like element type, text, confidence scores",
    )
    updated_at: datetime.datetime | None = Field(default=None)


class DiagramElementLinksWithDetailInsert(CustomModelInsert):
    """DiagramElementLinksWithDetail Insert Schema."""

    # Field properties:
    # created_at: nullable
    # created_by: nullable
    # created_by_avatar: nullable
    # created_by_name: nullable
    # diagram_id: nullable
    # diagram_name: nullable
    # element_id: nullable
    # id: nullable
    # link_type: nullable
    # metadata: nullable
    # requirement_description: nullable
    # requirement_id: nullable
    # requirement_name: nullable
    # updated_at: nullable

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    created_by: UUID4 | None = Field(default=None)
    created_by_avatar: str | None = Field(default=None)
    created_by_name: str | None = Field(default=None)
    diagram_id: UUID4 | None = Field(default=None)
    diagram_name: str | None = Field(default=None)
    element_id: str | None = Field(default=None)
    id: UUID4 | None = Field(default=None)
    link_type: str | None = Field(default=None)
    metadata: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    requirement_description: str | None = Field(default=None)
    requirement_id: UUID4 | None = Field(default=None)
    requirement_name: str | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)


class DocumentInsert(CustomModelInsert):
    """Document Insert Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)  # has default value

    # Field properties:
    # created_at: nullable, has default value
    # created_by: nullable
    # deleted_at: nullable
    # deleted_by: nullable
    # description: nullable
    # embedding: nullable
    # fts_vector: nullable
    # is_deleted: nullable, has default value
    # tags: nullable, has default value
    # updated_at: nullable, has default value
    # updated_by: nullable
    # version: has default value

    # Required fields
    name: str
    project_id: UUID4
    slug: str

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    created_by: UUID4 | None = Field(default=None)
    deleted_at: datetime.datetime | None = Field(default=None)
    deleted_by: UUID4 | None = Field(default=None)
    description: str | None = Field(default=None)
    embedding: Any | None = Field(default=None)
    fts_vector: str | None = Field(
        default=None,
        description="Full-text search vector: name(A) + description(B) + slug(C)",
    )
    is_deleted: bool | None = Field(default=None)
    tags: list[str] | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: UUID4 | None = Field(default=None)
    version: int | None = Field(default=None)


class EmbeddingCacheInsert(CustomModelInsert):
    """EmbeddingCache Insert Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)  # has default value

    # Field properties:
    # access_count: nullable, has default value
    # accessed_at: nullable, has default value
    # created_at: nullable, has default value
    # embedding: nullable
    # model: has default value
    # tokens_used: has default value

    # Required fields
    cache_key: str

    # Optional fields
    access_count: int | None = Field(default=None)
    accessed_at: datetime.datetime | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    embedding: Any | None = Field(default=None)
    model: str | None = Field(default=None)
    tokens_used: int | None = Field(default=None)


class ExcalidrawDiagramInsert(CustomModelInsert):
    """ExcalidrawDiagram Insert Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)  # has default value

    # Field properties:
    # created_at: nullable, has default value
    # created_by: nullable
    # diagram_data: nullable
    # name: nullable
    # organization_id: nullable
    # project_id: nullable
    # thumbnail_url: nullable
    # updated_at: nullable
    # updated_by: nullable

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    created_by: UUID4 | None = Field(default=None)
    diagram_data: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    name: str | None = Field(default=None)
    organization_id: UUID4 | None = Field(default=None)
    project_id: UUID4 | None = Field(default=None)
    thumbnail_url: str | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: UUID4 | None = Field(default=None)


class ExcalidrawElementLinkInsert(CustomModelInsert):
    """ExcalidrawElementLink Insert Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)  # has default value

    # Field properties:
    # create_by: nullable, has default value
    # created_at: has default value
    # element_id: nullable
    # excalidraw_canvas_id: nullable, has default value
    # requirement_id: nullable, has default value

    # Optional fields
    create_by: UUID4 | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    element_id: str | None = Field(default=None)
    excalidraw_canvas_id: UUID4 | None = Field(default=None)
    requirement_id: UUID4 | None = Field(default=None)


class ExternalDocumentInsert(CustomModelInsert):
    """ExternalDocument Insert Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)  # has default value

    # Field properties:
    # created_at: nullable, has default value
    # created_by: nullable
    # deleted_at: nullable
    # deleted_by: nullable
    # field_type: nullable
    # gumloop_name: nullable
    # is_deleted: nullable, has default value
    # owned_by: nullable
    # size: nullable
    # updated_at: nullable, has default value
    # updated_by: nullable
    # url: nullable

    # Required fields
    name: str
    organization_id: UUID4

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    created_by: UUID4 | None = Field(default=None)
    deleted_at: datetime.datetime | None = Field(default=None)
    deleted_by: UUID4 | None = Field(default=None)
    field_type: str | None = Field(default=None, alias="type")
    gumloop_name: str | None = Field(default=None)
    is_deleted: bool | None = Field(default=None)
    owned_by: UUID4 | None = Field(default=None)
    size: int | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: UUID4 | None = Field(default=None)
    url: str | None = Field(default=None)


class McpSessionInsert(CustomModelInsert):
    """McpSession Insert Schema."""

    # Primary Keys
    session_id: str

    # Field properties:
    # created_at: nullable, has default value
    # mcp_state: nullable
    # updated_at: nullable, has default value

    # Required fields
    expires_at: datetime.datetime
    oauth_data: dict | list[dict] | list[Any] | Json
    user_id: UUID4

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    mcp_state: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)


class NotificationInsert(CustomModelInsert):
    """Notification Insert Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)  # has default value

    # Field properties:
    # created_at: nullable, has default value
    # message: nullable
    # metadata: nullable, has default value
    # read_at: nullable
    # unread: nullable, has default value

    # Required fields
    field_type: Any = Field(alias="type")
    title: str
    user_id: UUID4

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    message: str | None = Field(default=None)
    metadata: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    read_at: datetime.datetime | None = Field(default=None)
    unread: bool | None = Field(default=None)


class OauthAccessTokenInsert(CustomModelInsert):
    """OauthAccessToken Insert Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)  # has default value

    # Field properties:
    # created_at: nullable, has default value
    # last_used_at: nullable, has default value
    # scope: nullable
    # user_id: nullable

    # Required fields
    client_id: str
    expires_at: datetime.datetime
    token_hash: str

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    last_used_at: datetime.datetime | None = Field(default=None)
    scope: str | None = Field(default=None)
    user_id: UUID4 | None = Field(default=None)


class OauthAuthorizationCodeInsert(CustomModelInsert):
    """OauthAuthorizationCode Insert Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)  # has default value

    # Field properties:
    # code_challenge_method: has default value
    # created_at: nullable, has default value
    # scope: nullable, has default value
    # state: nullable
    # user_id: nullable

    # Required fields
    client_id: str
    code: str
    code_challenge: str
    expires_at: datetime.datetime
    redirect_uri: str

    # Optional fields
    code_challenge_method: str | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    scope: str | None = Field(default=None)
    state: str | None = Field(default=None)
    user_id: UUID4 | None = Field(default=None)


class OauthClientInsert(CustomModelInsert):
    """OauthClient Insert Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)  # has default value

    # Field properties:
    # client_secret: nullable
    # created_at: nullable, has default value
    # grant_types: has default value
    # is_public: nullable, has default value
    # response_types: has default value
    # scope: nullable, has default value
    # updated_at: nullable, has default value

    # Required fields
    client_id: str
    client_name: str
    redirect_uris: dict | list[dict] | list[Any] | Json

    # Optional fields
    client_secret: str | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    grant_types: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    is_public: bool | None = Field(default=None)
    response_types: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    scope: str | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)


class OauthRefreshTokenInsert(CustomModelInsert):
    """OauthRefreshToken Insert Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)  # has default value

    # Field properties:
    # created_at: nullable, has default value
    # last_used_at: nullable
    # scope: nullable, has default value

    # Required fields
    client_id: str
    expires_at: datetime.datetime
    token: str
    user_id: UUID4

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    last_used_at: datetime.datetime | None = Field(default=None)
    scope: str | None = Field(default=None)


class OrganizationInvitationInsert(CustomModelInsert):
    """OrganizationInvitation Insert Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)  # has default value

    # Field properties:
    # created_at: nullable, has default value
    # deleted_at: nullable
    # deleted_by: nullable
    # expires_at: has default value
    # is_deleted: nullable, has default value
    # metadata: nullable, has default value
    # role: has default value
    # status: has default value
    # token: has default value
    # updated_at: nullable, has default value

    # Required fields
    created_by: UUID4
    email: str
    organization_id: UUID4
    updated_by: UUID4

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    deleted_at: datetime.datetime | None = Field(default=None)
    deleted_by: UUID4 | None = Field(default=None)
    expires_at: datetime.datetime | None = Field(default=None)
    is_deleted: bool | None = Field(default=None)
    metadata: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    role: PublicUserRoleTypeEnum | None = Field(default=None)
    status: PublicInvitationStatusEnum | None = Field(default=None)
    token: UUID4 | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)


class OrganizationMemberInsert(CustomModelInsert):
    """OrganizationMember Insert Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)  # has default value

    # Field properties:
    # created_at: nullable, has default value
    # deleted_at: nullable
    # deleted_by: nullable
    # is_deleted: nullable, has default value
    # last_active_at: nullable
    # permissions: nullable, has default value
    # role: has default value
    # status: nullable, has default value
    # updated_at: nullable, has default value
    # updated_by: nullable

    # Required fields
    organization_id: UUID4
    user_id: UUID4

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    deleted_at: datetime.datetime | None = Field(default=None)
    deleted_by: UUID4 | None = Field(default=None)
    is_deleted: bool | None = Field(default=None)
    last_active_at: datetime.datetime | None = Field(default=None)
    permissions: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    role: PublicUserRoleTypeEnum | None = Field(default=None)
    status: PublicUserStatusEnum | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: UUID4 | None = Field(default=None)


class OrganizationInsert(CustomModelInsert):
    """Organization Insert Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)  # has default value

    # Field properties:
    # billing_cycle: has default value
    # billing_plan: has default value
    # created_at: nullable, has default value
    # deleted_at: nullable
    # deleted_by: nullable
    # description: nullable
    # embedding: nullable
    # field_type: has default value
    # fts_vector: nullable
    # is_deleted: nullable, has default value
    # logo_url: nullable
    # max_members: has default value
    # max_monthly_requests: has default value
    # member_count: nullable, has default value
    # metadata: nullable, has default value
    # owner_id: nullable
    # settings: nullable, has default value
    # status: nullable, has default value
    # storage_used: nullable, has default value
    # updated_at: nullable, has default value

    # Required fields
    created_by: UUID4
    name: Annotated[str, StringConstraints(**{"min_length": 2, "max_length": 255})]
    slug: str
    updated_by: UUID4

    # Optional fields
    billing_cycle: PublicPricingPlanIntervalEnum | None = Field(default=None)
    billing_plan: PublicBillingPlanEnum | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    deleted_at: datetime.datetime | None = Field(default=None)
    deleted_by: UUID4 | None = Field(default=None)
    description: str | None = Field(default=None)
    embedding: Any | None = Field(default=None)
    field_type: Any | None = Field(default=None, alias="type")
    fts_vector: str | None = Field(
        default=None,
        description="Full-text search vector: name(A) + description(B) + slug(C)",
    )
    is_deleted: bool | None = Field(default=None)
    logo_url: str | None = Field(default=None)
    max_members: int | None = Field(default=None)
    max_monthly_requests: int | None = Field(default=None)
    member_count: int | None = Field(default=None)
    metadata: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    owner_id: UUID4 | None = Field(default=None)
    settings: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    status: PublicUserStatusEnum | None = Field(default=None)
    storage_used: int | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)


class ProfileInsert(CustomModelInsert):
    """Profile Insert Schema."""

    # Primary Keys
    id: UUID4

    # Field properties:
    # avatar_url: nullable
    # created_at: nullable, has default value
    # current_organization_id: nullable
    # deleted_at: nullable
    # deleted_by: nullable
    # full_name: nullable
    # is_approved: has default value
    # is_deleted: nullable, has default value
    # job_title: nullable
    # last_login_at: nullable
    # login_count: nullable, has default value
    # personal_organization_id: nullable
    # pinned_organization_id: nullable
    # preferences: nullable, has default value
    # status: nullable, has default value
    # updated_at: nullable, has default value

    # Required fields
    email: str

    # Optional fields
    avatar_url: str | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    current_organization_id: UUID4 | None = Field(default=None)
    deleted_at: datetime.datetime | None = Field(default=None)
    deleted_by: UUID4 | None = Field(default=None)
    full_name: str | None = Field(default=None)
    is_approved: bool | None = Field(default=None)
    is_deleted: bool | None = Field(default=None)
    job_title: str | None = Field(default=None)
    last_login_at: datetime.datetime | None = Field(default=None)
    login_count: int | None = Field(default=None)
    personal_organization_id: UUID4 | None = Field(default=None)
    pinned_organization_id: UUID4 | None = Field(default=None)
    preferences: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    status: PublicUserStatusEnum | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)


class ProjectInvitationInsert(CustomModelInsert):
    """ProjectInvitation Insert Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)  # has default value

    # Field properties:
    # created_at: nullable, has default value
    # deleted_at: nullable
    # deleted_by: nullable
    # expires_at: has default value
    # is_deleted: nullable, has default value
    # metadata: nullable, has default value
    # role: has default value
    # status: has default value
    # token: has default value
    # updated_at: nullable, has default value

    # Required fields
    created_by: UUID4
    email: str
    project_id: UUID4
    updated_by: UUID4

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    deleted_at: datetime.datetime | None = Field(default=None)
    deleted_by: UUID4 | None = Field(default=None)
    expires_at: datetime.datetime | None = Field(default=None)
    is_deleted: bool | None = Field(default=None)
    metadata: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    role: PublicProjectRoleEnum | None = Field(default=None)
    status: PublicInvitationStatusEnum | None = Field(default=None)
    token: UUID4 | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)


class ProjectMemberInsert(CustomModelInsert):
    """ProjectMember Insert Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)  # has default value

    # Field properties:
    # created_at: nullable, has default value
    # deleted_at: nullable
    # deleted_by: nullable
    # is_deleted: nullable, has default value
    # last_accessed_at: nullable
    # org_id: nullable
    # permissions: nullable, has default value
    # role: has default value
    # status: nullable, has default value
    # updated_at: nullable, has default value

    # Required fields
    project_id: UUID4
    user_id: UUID4

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    deleted_at: datetime.datetime | None = Field(default=None)
    deleted_by: UUID4 | None = Field(default=None)
    is_deleted: bool | None = Field(default=None)
    last_accessed_at: datetime.datetime | None = Field(default=None)
    org_id: UUID4 | None = Field(default=None)
    permissions: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    role: PublicProjectRoleEnum | None = Field(default=None)
    status: PublicUserStatusEnum | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)


class ProjectInsert(CustomModelInsert):
    """Project Insert Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)  # has default value

    # Field properties:
    # created_at: nullable, has default value
    # deleted_at: nullable
    # deleted_by: nullable
    # description: nullable
    # embedding: nullable
    # fts_vector: nullable
    # is_deleted: nullable, has default value
    # metadata: nullable, has default value
    # settings: nullable, has default value
    # star_count: nullable, has default value
    # status: has default value
    # tags: nullable, has default value
    # updated_at: nullable, has default value
    # version: nullable, has default value
    # visibility: has default value

    # Required fields
    created_by: UUID4
    name: Annotated[str, StringConstraints(**{"min_length": 2, "max_length": 255})]
    organization_id: UUID4
    owned_by: UUID4
    slug: str
    updated_by: UUID4

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    deleted_at: datetime.datetime | None = Field(default=None)
    deleted_by: UUID4 | None = Field(default=None)
    description: str | None = Field(default=None)
    embedding: Any | None = Field(default=None)
    fts_vector: str | None = Field(
        default=None,
        description="Full-text search vector: name(A) + description(B) + slug(C)",
    )
    is_deleted: bool | None = Field(default=None)
    metadata: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    settings: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    star_count: int | None = Field(default=None)
    status: PublicProjectStatusEnum | None = Field(default=None)
    tags: list[str] | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    version: int | None = Field(default=None)
    visibility: PublicVisibilityEnum | None = Field(default=None)


class PropertyInsert(CustomModelInsert):
    """Property Insert Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)  # has default value

    # Field properties:
    # created_at: nullable, has default value
    # created_by: nullable
    # deleted_at: nullable
    # deleted_by: nullable
    # document_id: nullable
    # is_base: nullable, has default value
    # is_deleted: has default value
    # options: nullable, has default value
    # project_id: nullable
    # scope: nullable
    # updated_at: nullable, has default value
    # updated_by: nullable

    # Required fields
    name: str
    org_id: UUID4
    property_type: str

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    created_by: UUID4 | None = Field(default=None)
    deleted_at: datetime.datetime | None = Field(default=None)
    deleted_by: UUID4 | None = Field(default=None)
    document_id: UUID4 | None = Field(default=None)
    is_base: bool | None = Field(default=None)
    is_deleted: bool | None = Field(default=None)
    options: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    project_id: UUID4 | None = Field(default=None)
    scope: str | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: UUID4 | None = Field(default=None)


class RagEmbeddingInsert(CustomModelInsert):
    """RagEmbedding Insert Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)  # has default value

    # Field properties:
    # content_hash: nullable
    # created_at: nullable, has default value
    # metadata: nullable
    # quality_score: nullable, has default value

    # Required fields
    embedding: Any
    entity_id: str
    entity_type: str

    # Optional fields
    content_hash: str | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    metadata: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    quality_score: float | None = Field(default=None)


class RagSearchAnalyticInsert(CustomModelInsert):
    """RagSearchAnalytic Insert Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)  # has default value

    # Field properties:
    # cache_hit: has default value
    # created_at: nullable, has default value
    # organization_id: nullable
    # user_id: nullable

    # Required fields
    execution_time_ms: int
    query_hash: str
    query_text: str
    result_count: int
    search_type: str

    # Optional fields
    cache_hit: bool | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    organization_id: UUID4 | None = Field(default=None)
    user_id: UUID4 | None = Field(default=None)


class ReactFlowDiagramInsert(CustomModelInsert):
    """ReactFlowDiagram Insert Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)  # has default value

    # Field properties:
    # created_at: nullable, has default value
    # created_by: nullable
    # description: nullable
    # diagram_type: nullable, has default value
    # edges: has default value
    # layout_algorithm: nullable, has default value
    # metadata: nullable, has default value
    # name: has default value
    # nodes: has default value
    # settings: nullable, has default value
    # theme: nullable, has default value
    # updated_at: nullable, has default value
    # updated_by: nullable
    # viewport: nullable, has default value

    # Required fields
    project_id: UUID4

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    created_by: UUID4 | None = Field(default=None)
    description: str | None = Field(default=None)
    diagram_type: str | None = Field(default=None)
    edges: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    layout_algorithm: str | None = Field(default=None)
    metadata: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    name: str | None = Field(default=None)
    nodes: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    settings: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    theme: str | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: UUID4 | None = Field(default=None)
    viewport: dict | list[dict] | list[Any] | Json | None = Field(default=None)


class RequirementTestInsert(CustomModelInsert):
    """RequirementTest Insert Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)  # has default value

    # Field properties:
    # created_at: nullable, has default value
    # defects: nullable
    # evidence_artifacts: nullable
    # executed_at: nullable
    # executed_by: nullable
    # execution_environment: nullable
    # execution_status: has default value
    # execution_version: nullable
    # external_req_id: nullable
    # external_test_id: nullable
    # result_notes: nullable
    # updated_at: nullable, has default value

    # Required fields
    requirement_id: UUID4
    test_id: UUID4

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    defects: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    evidence_artifacts: dict | list[dict] | list[Any] | Json | None = Field(
        default=None
    )
    executed_at: datetime.datetime | None = Field(default=None)
    executed_by: UUID4 | None = Field(default=None)
    execution_environment: str | None = Field(default=None)
    execution_status: PublicExecutionStatusEnum | None = Field(default=None)
    execution_version: str | None = Field(default=None)
    external_req_id: str | None = Field(default=None)
    external_test_id: str | None = Field(default=None)
    result_notes: str | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)


class RequirementInsert(CustomModelInsert):
    """Requirement Insert Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)  # has default value

    # Field properties:
    # ai_analysis: nullable, has default value
    # created_at: nullable, has default value
    # created_by: nullable
    # deleted_at: nullable
    # deleted_by: nullable
    # description: nullable
    # embedding: nullable
    # enchanced_requirement: nullable
    # external_id: nullable
    # field_format: has default value
    # field_type: nullable
    # fts_vector: nullable
    # is_deleted: nullable, has default value
    # level: has default value
    # original_requirement: nullable
    # position: has default value
    # priority: has default value
    # properties: nullable, has default value
    # status: has default value
    # tags: nullable, has default value
    # updated_at: nullable, has default value
    # updated_by: nullable
    # version: has default value

    # Required fields
    block_id: UUID4
    document_id: UUID4
    name: str

    # Optional fields
    ai_analysis: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    created_by: UUID4 | None = Field(default=None)
    deleted_at: datetime.datetime | None = Field(default=None)
    deleted_by: UUID4 | None = Field(default=None)
    description: str | None = Field(default=None)
    embedding: Any | None = Field(default=None)
    enchanced_requirement: str | None = Field(default=None)
    external_id: str | None = Field(default=None)
    field_format: Any | None = Field(default=None, alias="format")
    field_type: str | None = Field(default=None, alias="type")
    fts_vector: str | None = Field(
        default=None,
        description="Full-text search vector: name(A) + description(B) + requirements(C)",
    )
    is_deleted: bool | None = Field(default=None)
    level: PublicRequirementLevelEnum | None = Field(default=None)
    original_requirement: str | None = Field(default=None)
    position: float | None = Field(default=None)
    priority: PublicRequirementPriorityEnum | None = Field(default=None)
    properties: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    status: PublicRequirementStatusEnum | None = Field(default=None)
    tags: list[str] | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: UUID4 | None = Field(default=None)
    version: int | None = Field(default=None)


class RequirementsClosureInsert(CustomModelInsert):
    """RequirementsClosure Insert Schema."""

    # Primary Keys
    ancestor_id: UUID4
    descendant_id: UUID4

    # Field properties:
    # created_at: has default value
    # updated_at: nullable
    # updated_by: nullable

    # Required fields
    created_by: UUID4
    depth: int

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: UUID4 | None = Field(default=None)


class StripeCustomerInsert(CustomModelInsert):
    """StripeCustomer Insert Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)  # has default value

    # Field properties:
    # cancel_at_period_end: nullable, has default value
    # created_at: nullable, has default value
    # current_period_end: nullable
    # current_period_start: nullable
    # organization_id: nullable
    # payment_method_brand: nullable
    # payment_method_last4: nullable
    # price_id: nullable
    # stripe_customer_id: nullable
    # stripe_subscription_id: nullable
    # updated_at: nullable, has default value

    # Required fields
    subscription_status: PublicSubscriptionStatusEnum

    # Optional fields
    cancel_at_period_end: bool | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    current_period_end: datetime.datetime | None = Field(default=None)
    current_period_start: datetime.datetime | None = Field(default=None)
    organization_id: UUID4 | None = Field(default=None)
    payment_method_brand: str | None = Field(default=None)
    payment_method_last4: str | None = Field(default=None)
    price_id: str | None = Field(default=None)
    stripe_customer_id: str | None = Field(default=None)
    stripe_subscription_id: str | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)


class TableRowInsert(CustomModelInsert):
    """TableRow Insert Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)  # has default value

    # Field properties:
    # created_at: nullable, has default value
    # created_by: nullable
    # deleted_at: nullable
    # deleted_by: nullable
    # is_deleted: nullable, has default value
    # position: has default value
    # row_data: nullable, has default value
    # updated_at: nullable, has default value
    # updated_by: nullable
    # version: has default value

    # Required fields
    block_id: UUID4
    document_id: UUID4

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    created_by: UUID4 | None = Field(default=None)
    deleted_at: datetime.datetime | None = Field(default=None)
    deleted_by: UUID4 | None = Field(default=None)
    is_deleted: bool | None = Field(default=None)
    position: float | None = Field(default=None)
    row_data: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: UUID4 | None = Field(default=None)
    version: int | None = Field(default=None)


class TestMatrixViewInsert(CustomModelInsert):
    """TestMatrixView Insert Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)  # has default value

    # Field properties:
    # configuration: has default value
    # created_at: nullable, has default value
    # is_active: nullable, has default value
    # is_default: nullable, has default value
    # updated_at: nullable, has default value

    # Required fields
    created_by: UUID4
    name: str
    project_id: UUID4
    updated_by: UUID4

    # Optional fields
    configuration: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    is_active: bool | None = Field(default=None)
    is_default: bool | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)


class TestReqInsert(CustomModelInsert):
    """TestReq Insert Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)  # has default value

    # Field properties:
    # attachments: nullable
    # category: nullable
    # created_at: nullable, has default value
    # created_by: nullable
    # deleted_at: nullable
    # deleted_by: nullable
    # description: nullable
    # estimated_duration: nullable
    # expected_results: nullable
    # is_active: nullable, has default value
    # is_deleted: has default value
    # method: has default value
    # preconditions: nullable
    # priority: has default value
    # project_id: nullable
    # result: nullable, has default value
    # status: has default value
    # test_environment: nullable
    # test_id: nullable
    # test_steps: nullable
    # test_type: has default value
    # updated_at: nullable, has default value
    # updated_by: nullable
    # version: nullable

    # Required fields
    title: str

    # Optional fields
    attachments: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    category: list[str] | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    created_by: UUID4 | None = Field(default=None)
    deleted_at: datetime.datetime | None = Field(default=None)
    deleted_by: UUID4 | None = Field(default=None)
    description: str | None = Field(default=None)
    estimated_duration: datetime.timedelta | None = Field(default=None)
    expected_results: str | None = Field(default=None)
    is_active: bool | None = Field(default=None)
    is_deleted: bool | None = Field(default=None)
    method: PublicTestMethodEnum | None = Field(default=None)
    preconditions: str | None = Field(default=None)
    priority: PublicTestPriorityEnum | None = Field(default=None)
    project_id: UUID4 | None = Field(default=None)
    result: str | None = Field(default=None)
    status: PublicTestStatusEnum | None = Field(default=None)
    test_environment: str | None = Field(default=None)
    test_id: str | None = Field(default=None)
    test_steps: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    test_type: PublicTestTypeEnum | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: UUID4 | None = Field(default=None)
    version: str | None = Field(default=None)


class TraceLinkInsert(CustomModelInsert):
    """TraceLink Insert Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)  # has default value

    # Field properties:
    # created_at: nullable, has default value
    # created_by: nullable
    # deleted_at: nullable
    # deleted_by: nullable
    # description: nullable
    # is_deleted: nullable, has default value
    # updated_at: nullable, has default value
    # updated_by: nullable
    # version: has default value

    # Required fields
    link_type: PublicTraceLinkTypeEnum
    source_id: UUID4
    source_type: PublicEntityTypeEnum
    target_id: UUID4
    target_type: PublicEntityTypeEnum

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    created_by: UUID4 | None = Field(default=None)
    deleted_at: datetime.datetime | None = Field(default=None)
    deleted_by: UUID4 | None = Field(default=None)
    description: str | None = Field(default=None)
    is_deleted: bool | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: UUID4 | None = Field(default=None)
    version: int | None = Field(default=None)


class UsageLogInsert(CustomModelInsert):
    """UsageLog Insert Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)  # has default value

    # Field properties:
    # created_at: nullable, has default value
    # metadata: nullable, has default value

    # Required fields
    feature: str
    organization_id: UUID4
    quantity: int
    unit_type: str
    user_id: UUID4

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    metadata: dict | list[dict] | list[Any] | Json | None = Field(default=None)


class UserRoleInsert(CustomModelInsert):
    """UserRole Insert Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)  # has default value

    # Field properties:
    # admin_role: nullable
    # created_at: has default value
    # document_id: nullable
    # document_role: nullable
    # org_id: nullable
    # project_id: nullable
    # project_role: nullable
    # updated_at: has default value

    # Required fields
    user_id: UUID4

    # Optional fields
    admin_role: PublicUserRoleTypeEnum | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    document_id: UUID4 | None = Field(default=None)
    document_role: PublicProjectRoleEnum | None = Field(default=None)
    org_id: UUID4 | None = Field(default=None)
    project_id: UUID4 | None = Field(default=None)
    project_role: PublicProjectRoleEnum | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)


# UPDATE CLASSES
# Note: These models are used for update operations. All fields are optional.


class AssignmentUpdate(CustomModelUpdate):
    """Assignment Update Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)

    # Field properties:
    # comment: nullable
    # completed_at: nullable
    # created_at: nullable, has default value
    # created_by: nullable
    # deleted_at: nullable
    # deleted_by: nullable
    # due_date: nullable
    # is_deleted: nullable, has default value
    # updated_at: nullable, has default value
    # updated_by: nullable
    # version: has default value

    # Optional fields
    assignee_id: UUID4 | None = Field(default=None)
    comment: str | None = Field(default=None)
    completed_at: datetime.datetime | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    created_by: UUID4 | None = Field(default=None)
    deleted_at: datetime.datetime | None = Field(default=None)
    deleted_by: UUID4 | None = Field(default=None)
    due_date: datetime.datetime | None = Field(default=None)
    entity_id: UUID4 | None = Field(default=None)
    entity_type: PublicEntityTypeEnum | None = Field(default=None)
    is_deleted: bool | None = Field(default=None)
    role: PublicAssignmentRoleEnum | None = Field(default=None)
    status: PublicRequirementStatusEnum | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: UUID4 | None = Field(default=None)
    version: int | None = Field(default=None)


class AuditLogUpdate(CustomModelUpdate):
    """AuditLog Update Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)

    # Field properties:
    # actor_id: nullable
    # compliance_category: nullable
    # correlation_id: nullable
    # created_at: has default value
    # description: nullable
    # details: nullable
    # event_type: nullable
    # ip_address: nullable
    # metadata: nullable, has default value
    # new_data: nullable
    # old_data: nullable
    # organization_id: nullable
    # project_id: nullable
    # resource_id: nullable
    # resource_type: nullable
    # risk_level: nullable
    # session_id: nullable
    # severity: nullable, has default value
    # soc2_control: nullable
    # source_system: nullable
    # threat_indicators: nullable
    # timestamp: nullable
    # updated_at: nullable
    # user_agent: nullable
    # user_id: nullable

    # Optional fields
    action: str | None = Field(default=None)
    actor_id: UUID4 | None = Field(default=None)
    compliance_category: str | None = Field(default=None)
    correlation_id: UUID4 | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    description: str | None = Field(default=None)
    details: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    entity_id: UUID4 | None = Field(default=None)
    entity_type: str | None = Field(default=None)
    event_type: PublicAuditEventTypeEnum | None = Field(default=None)
    ip_address: IPv4Address | IPv6Address | None = Field(default=None)
    metadata: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    new_data: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    old_data: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    organization_id: UUID4 | None = Field(default=None)
    project_id: UUID4 | None = Field(default=None)
    resource_id: UUID4 | None = Field(default=None)
    resource_type: PublicResourceTypeEnum | None = Field(default=None)
    risk_level: str | None = Field(default=None)
    session_id: str | None = Field(default=None)
    severity: PublicAuditSeverityEnum | None = Field(default=None)
    soc2_control: str | None = Field(default=None)
    source_system: str | None = Field(default=None)
    threat_indicators: list[str] | None = Field(default=None)
    timestamp: datetime.datetime | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    user_agent: str | None = Field(default=None)
    user_id: UUID4 | None = Field(default=None)


class BillingCacheUpdate(CustomModelUpdate):
    """BillingCache Update Schema."""

    # Primary Keys
    organization_id: UUID4 | None = Field(default=None)

    # Field properties:
    # billing_status: has default value
    # current_period_usage: has default value
    # period_end: has default value
    # period_start: has default value
    # synced_at: has default value

    # Optional fields
    billing_status: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    current_period_usage: dict | list[dict] | list[Any] | Json | None = Field(
        default=None
    )
    period_end: datetime.datetime | None = Field(default=None)
    period_start: datetime.datetime | None = Field(default=None)
    synced_at: datetime.datetime | None = Field(default=None)


class BlockUpdate(CustomModelUpdate):
    """Block Update Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)

    # Field properties:
    # content: nullable, has default value
    # created_at: nullable, has default value
    # created_by: nullable
    # deleted_at: nullable
    # deleted_by: nullable
    # is_deleted: nullable, has default value
    # name: has default value
    # org_id: nullable
    # updated_at: nullable, has default value
    # updated_by: nullable
    # version: has default value

    # Optional fields
    content: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    created_by: UUID4 | None = Field(default=None)
    deleted_at: datetime.datetime | None = Field(default=None)
    deleted_by: UUID4 | None = Field(default=None)
    document_id: UUID4 | None = Field(default=None)
    field_type: str | None = Field(default=None, alias="type")
    is_deleted: bool | None = Field(default=None)
    name: str | None = Field(default=None)
    org_id: UUID4 | None = Field(default=None)
    position: int | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: UUID4 | None = Field(default=None)
    version: int | None = Field(default=None)


class ColumnUpdate(CustomModelUpdate):
    """Column Update Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)

    # Field properties:
    # block_id: nullable
    # created_at: nullable, has default value
    # created_by: nullable
    # default_value: nullable
    # is_hidden: nullable, has default value
    # is_pinned: nullable, has default value
    # updated_at: nullable, has default value
    # updated_by: nullable
    # width: nullable, has default value

    # Optional fields
    block_id: UUID4 | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    created_by: UUID4 | None = Field(default=None)
    default_value: str | None = Field(default=None)
    is_hidden: bool | None = Field(default=None)
    is_pinned: bool | None = Field(default=None)
    position: float | None = Field(default=None)
    property_id: UUID4 | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: UUID4 | None = Field(default=None)
    width: int | None = Field(default=None)


class DiagramElementLinkUpdate(CustomModelUpdate):
    """DiagramElementLink Update Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)

    # Field properties:
    # created_at: nullable, has default value
    # created_by: nullable
    # link_type: nullable, has default value
    # metadata: nullable, has default value
    # updated_at: nullable, has default value

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    created_by: UUID4 | None = Field(default=None)
    diagram_id: UUID4 | None = Field(default=None)
    element_id: str | None = Field(
        default=None, description="Excalidraw element ID from the diagram"
    )
    link_type: str | None = Field(
        default=None, description="Whether link was created manually or auto-detected"
    )
    metadata: dict | list[dict] | list[Any] | Json | None = Field(
        default=None,
        description="Additional data like element type, text, confidence scores",
    )
    requirement_id: UUID4 | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)


class DiagramElementLinksWithDetailUpdate(CustomModelUpdate):
    """DiagramElementLinksWithDetail Update Schema."""

    # Field properties:
    # created_at: nullable
    # created_by: nullable
    # created_by_avatar: nullable
    # created_by_name: nullable
    # diagram_id: nullable
    # diagram_name: nullable
    # element_id: nullable
    # id: nullable
    # link_type: nullable
    # metadata: nullable
    # requirement_description: nullable
    # requirement_id: nullable
    # requirement_name: nullable
    # updated_at: nullable

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    created_by: UUID4 | None = Field(default=None)
    created_by_avatar: str | None = Field(default=None)
    created_by_name: str | None = Field(default=None)
    diagram_id: UUID4 | None = Field(default=None)
    diagram_name: str | None = Field(default=None)
    element_id: str | None = Field(default=None)
    id: UUID4 | None = Field(default=None)
    link_type: str | None = Field(default=None)
    metadata: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    requirement_description: str | None = Field(default=None)
    requirement_id: UUID4 | None = Field(default=None)
    requirement_name: str | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)


class DocumentUpdate(CustomModelUpdate):
    """Document Update Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)

    # Field properties:
    # created_at: nullable, has default value
    # created_by: nullable
    # deleted_at: nullable
    # deleted_by: nullable
    # description: nullable
    # embedding: nullable
    # fts_vector: nullable
    # is_deleted: nullable, has default value
    # tags: nullable, has default value
    # updated_at: nullable, has default value
    # updated_by: nullable
    # version: has default value

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    created_by: UUID4 | None = Field(default=None)
    deleted_at: datetime.datetime | None = Field(default=None)
    deleted_by: UUID4 | None = Field(default=None)
    description: str | None = Field(default=None)
    embedding: Any | None = Field(default=None)
    fts_vector: str | None = Field(
        default=None,
        description="Full-text search vector: name(A) + description(B) + slug(C)",
    )
    is_deleted: bool | None = Field(default=None)
    name: str | None = Field(default=None)
    project_id: UUID4 | None = Field(default=None)
    slug: str | None = Field(default=None)
    tags: list[str] | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: UUID4 | None = Field(default=None)
    version: int | None = Field(default=None)


class EmbeddingCacheUpdate(CustomModelUpdate):
    """EmbeddingCache Update Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)

    # Field properties:
    # access_count: nullable, has default value
    # accessed_at: nullable, has default value
    # created_at: nullable, has default value
    # embedding: nullable
    # model: has default value
    # tokens_used: has default value

    # Optional fields
    access_count: int | None = Field(default=None)
    accessed_at: datetime.datetime | None = Field(default=None)
    cache_key: str | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    embedding: Any | None = Field(default=None)
    model: str | None = Field(default=None)
    tokens_used: int | None = Field(default=None)


class ExcalidrawDiagramUpdate(CustomModelUpdate):
    """ExcalidrawDiagram Update Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)

    # Field properties:
    # created_at: nullable, has default value
    # created_by: nullable
    # diagram_data: nullable
    # name: nullable
    # organization_id: nullable
    # project_id: nullable
    # thumbnail_url: nullable
    # updated_at: nullable
    # updated_by: nullable

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    created_by: UUID4 | None = Field(default=None)
    diagram_data: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    name: str | None = Field(default=None)
    organization_id: UUID4 | None = Field(default=None)
    project_id: UUID4 | None = Field(default=None)
    thumbnail_url: str | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: UUID4 | None = Field(default=None)


class ExcalidrawElementLinkUpdate(CustomModelUpdate):
    """ExcalidrawElementLink Update Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)

    # Field properties:
    # create_by: nullable, has default value
    # created_at: has default value
    # element_id: nullable
    # excalidraw_canvas_id: nullable, has default value
    # requirement_id: nullable, has default value

    # Optional fields
    create_by: UUID4 | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    element_id: str | None = Field(default=None)
    excalidraw_canvas_id: UUID4 | None = Field(default=None)
    requirement_id: UUID4 | None = Field(default=None)


class ExternalDocumentUpdate(CustomModelUpdate):
    """ExternalDocument Update Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)

    # Field properties:
    # created_at: nullable, has default value
    # created_by: nullable
    # deleted_at: nullable
    # deleted_by: nullable
    # field_type: nullable
    # gumloop_name: nullable
    # is_deleted: nullable, has default value
    # owned_by: nullable
    # size: nullable
    # updated_at: nullable, has default value
    # updated_by: nullable
    # url: nullable

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    created_by: UUID4 | None = Field(default=None)
    deleted_at: datetime.datetime | None = Field(default=None)
    deleted_by: UUID4 | None = Field(default=None)
    field_type: str | None = Field(default=None, alias="type")
    gumloop_name: str | None = Field(default=None)
    is_deleted: bool | None = Field(default=None)
    name: str | None = Field(default=None)
    organization_id: UUID4 | None = Field(default=None)
    owned_by: UUID4 | None = Field(default=None)
    size: int | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: UUID4 | None = Field(default=None)
    url: str | None = Field(default=None)


class McpSessionUpdate(CustomModelUpdate):
    """McpSession Update Schema."""

    # Primary Keys
    session_id: str | None = Field(default=None)

    # Field properties:
    # created_at: nullable, has default value
    # mcp_state: nullable
    # updated_at: nullable, has default value

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    expires_at: datetime.datetime | None = Field(default=None)
    mcp_state: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    oauth_data: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    user_id: UUID4 | None = Field(default=None)


class NotificationUpdate(CustomModelUpdate):
    """Notification Update Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)

    # Field properties:
    # created_at: nullable, has default value
    # message: nullable
    # metadata: nullable, has default value
    # read_at: nullable
    # unread: nullable, has default value

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    field_type: Any | None = Field(default=None, alias="type")
    message: str | None = Field(default=None)
    metadata: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    read_at: datetime.datetime | None = Field(default=None)
    title: str | None = Field(default=None)
    unread: bool | None = Field(default=None)
    user_id: UUID4 | None = Field(default=None)


class OauthAccessTokenUpdate(CustomModelUpdate):
    """OauthAccessToken Update Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)

    # Field properties:
    # created_at: nullable, has default value
    # last_used_at: nullable, has default value
    # scope: nullable
    # user_id: nullable

    # Optional fields
    client_id: str | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    expires_at: datetime.datetime | None = Field(default=None)
    last_used_at: datetime.datetime | None = Field(default=None)
    scope: str | None = Field(default=None)
    token_hash: str | None = Field(default=None)
    user_id: UUID4 | None = Field(default=None)


class OauthAuthorizationCodeUpdate(CustomModelUpdate):
    """OauthAuthorizationCode Update Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)

    # Field properties:
    # code_challenge_method: has default value
    # created_at: nullable, has default value
    # scope: nullable, has default value
    # state: nullable
    # user_id: nullable

    # Optional fields
    client_id: str | None = Field(default=None)
    code: str | None = Field(default=None)
    code_challenge: str | None = Field(default=None)
    code_challenge_method: str | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    expires_at: datetime.datetime | None = Field(default=None)
    redirect_uri: str | None = Field(default=None)
    scope: str | None = Field(default=None)
    state: str | None = Field(default=None)
    user_id: UUID4 | None = Field(default=None)


class OauthClientUpdate(CustomModelUpdate):
    """OauthClient Update Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)

    # Field properties:
    # client_secret: nullable
    # created_at: nullable, has default value
    # grant_types: has default value
    # is_public: nullable, has default value
    # response_types: has default value
    # scope: nullable, has default value
    # updated_at: nullable, has default value

    # Optional fields
    client_id: str | None = Field(default=None)
    client_name: str | None = Field(default=None)
    client_secret: str | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    grant_types: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    is_public: bool | None = Field(default=None)
    redirect_uris: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    response_types: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    scope: str | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)


class OauthRefreshTokenUpdate(CustomModelUpdate):
    """OauthRefreshToken Update Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)

    # Field properties:
    # created_at: nullable, has default value
    # last_used_at: nullable
    # scope: nullable, has default value

    # Optional fields
    client_id: str | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    expires_at: datetime.datetime | None = Field(default=None)
    last_used_at: datetime.datetime | None = Field(default=None)
    scope: str | None = Field(default=None)
    token: str | None = Field(default=None)
    user_id: UUID4 | None = Field(default=None)


class OrganizationInvitationUpdate(CustomModelUpdate):
    """OrganizationInvitation Update Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)

    # Field properties:
    # created_at: nullable, has default value
    # deleted_at: nullable
    # deleted_by: nullable
    # expires_at: has default value
    # is_deleted: nullable, has default value
    # metadata: nullable, has default value
    # role: has default value
    # status: has default value
    # token: has default value
    # updated_at: nullable, has default value

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    created_by: UUID4 | None = Field(default=None)
    deleted_at: datetime.datetime | None = Field(default=None)
    deleted_by: UUID4 | None = Field(default=None)
    email: str | None = Field(default=None)
    expires_at: datetime.datetime | None = Field(default=None)
    is_deleted: bool | None = Field(default=None)
    metadata: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    organization_id: UUID4 | None = Field(default=None)
    role: PublicUserRoleTypeEnum | None = Field(default=None)
    status: PublicInvitationStatusEnum | None = Field(default=None)
    token: UUID4 | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: UUID4 | None = Field(default=None)


class OrganizationMemberUpdate(CustomModelUpdate):
    """OrganizationMember Update Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)

    # Field properties:
    # created_at: nullable, has default value
    # deleted_at: nullable
    # deleted_by: nullable
    # is_deleted: nullable, has default value
    # last_active_at: nullable
    # permissions: nullable, has default value
    # role: has default value
    # status: nullable, has default value
    # updated_at: nullable, has default value
    # updated_by: nullable

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    deleted_at: datetime.datetime | None = Field(default=None)
    deleted_by: UUID4 | None = Field(default=None)
    is_deleted: bool | None = Field(default=None)
    last_active_at: datetime.datetime | None = Field(default=None)
    organization_id: UUID4 | None = Field(default=None)
    permissions: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    role: PublicUserRoleTypeEnum | None = Field(default=None)
    status: PublicUserStatusEnum | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: UUID4 | None = Field(default=None)
    user_id: UUID4 | None = Field(default=None)


class OrganizationUpdate(CustomModelUpdate):
    """Organization Update Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)

    # Field properties:
    # billing_cycle: has default value
    # billing_plan: has default value
    # created_at: nullable, has default value
    # deleted_at: nullable
    # deleted_by: nullable
    # description: nullable
    # embedding: nullable
    # field_type: has default value
    # fts_vector: nullable
    # is_deleted: nullable, has default value
    # logo_url: nullable
    # max_members: has default value
    # max_monthly_requests: has default value
    # member_count: nullable, has default value
    # metadata: nullable, has default value
    # owner_id: nullable
    # settings: nullable, has default value
    # status: nullable, has default value
    # storage_used: nullable, has default value
    # updated_at: nullable, has default value

    # Optional fields
    billing_cycle: PublicPricingPlanIntervalEnum | None = Field(default=None)
    billing_plan: PublicBillingPlanEnum | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    created_by: UUID4 | None = Field(default=None)
    deleted_at: datetime.datetime | None = Field(default=None)
    deleted_by: UUID4 | None = Field(default=None)
    description: str | None = Field(default=None)
    embedding: Any | None = Field(default=None)
    field_type: Any | None = Field(default=None, alias="type")
    fts_vector: str | None = Field(
        default=None,
        description="Full-text search vector: name(A) + description(B) + slug(C)",
    )
    is_deleted: bool | None = Field(default=None)
    logo_url: str | None = Field(default=None)
    max_members: int | None = Field(default=None)
    max_monthly_requests: int | None = Field(default=None)
    member_count: int | None = Field(default=None)
    metadata: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    name: (
        Annotated[str, StringConstraints(**{"min_length": 2, "max_length": 255})] | None
    ) = Field(default=None)
    owner_id: UUID4 | None = Field(default=None)
    settings: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    slug: str | None = Field(default=None)
    status: PublicUserStatusEnum | None = Field(default=None)
    storage_used: int | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: UUID4 | None = Field(default=None)


class ProfileUpdate(CustomModelUpdate):
    """Profile Update Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)

    # Field properties:
    # avatar_url: nullable
    # created_at: nullable, has default value
    # current_organization_id: nullable
    # deleted_at: nullable
    # deleted_by: nullable
    # full_name: nullable
    # is_approved: has default value
    # is_deleted: nullable, has default value
    # job_title: nullable
    # last_login_at: nullable
    # login_count: nullable, has default value
    # personal_organization_id: nullable
    # pinned_organization_id: nullable
    # preferences: nullable, has default value
    # status: nullable, has default value
    # updated_at: nullable, has default value

    # Optional fields
    avatar_url: str | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    current_organization_id: UUID4 | None = Field(default=None)
    deleted_at: datetime.datetime | None = Field(default=None)
    deleted_by: UUID4 | None = Field(default=None)
    email: str | None = Field(default=None)
    full_name: str | None = Field(default=None)
    is_approved: bool | None = Field(default=None)
    is_deleted: bool | None = Field(default=None)
    job_title: str | None = Field(default=None)
    last_login_at: datetime.datetime | None = Field(default=None)
    login_count: int | None = Field(default=None)
    personal_organization_id: UUID4 | None = Field(default=None)
    pinned_organization_id: UUID4 | None = Field(default=None)
    preferences: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    status: PublicUserStatusEnum | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)


class ProjectInvitationUpdate(CustomModelUpdate):
    """ProjectInvitation Update Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)

    # Field properties:
    # created_at: nullable, has default value
    # deleted_at: nullable
    # deleted_by: nullable
    # expires_at: has default value
    # is_deleted: nullable, has default value
    # metadata: nullable, has default value
    # role: has default value
    # status: has default value
    # token: has default value
    # updated_at: nullable, has default value

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    created_by: UUID4 | None = Field(default=None)
    deleted_at: datetime.datetime | None = Field(default=None)
    deleted_by: UUID4 | None = Field(default=None)
    email: str | None = Field(default=None)
    expires_at: datetime.datetime | None = Field(default=None)
    is_deleted: bool | None = Field(default=None)
    metadata: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    project_id: UUID4 | None = Field(default=None)
    role: PublicProjectRoleEnum | None = Field(default=None)
    status: PublicInvitationStatusEnum | None = Field(default=None)
    token: UUID4 | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: UUID4 | None = Field(default=None)


class ProjectMemberUpdate(CustomModelUpdate):
    """ProjectMember Update Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)

    # Field properties:
    # created_at: nullable, has default value
    # deleted_at: nullable
    # deleted_by: nullable
    # is_deleted: nullable, has default value
    # last_accessed_at: nullable
    # org_id: nullable
    # permissions: nullable, has default value
    # role: has default value
    # status: nullable, has default value
    # updated_at: nullable, has default value

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    deleted_at: datetime.datetime | None = Field(default=None)
    deleted_by: UUID4 | None = Field(default=None)
    is_deleted: bool | None = Field(default=None)
    last_accessed_at: datetime.datetime | None = Field(default=None)
    org_id: UUID4 | None = Field(default=None)
    permissions: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    project_id: UUID4 | None = Field(default=None)
    role: PublicProjectRoleEnum | None = Field(default=None)
    status: PublicUserStatusEnum | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    user_id: UUID4 | None = Field(default=None)


class ProjectUpdate(CustomModelUpdate):
    """Project Update Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)

    # Field properties:
    # created_at: nullable, has default value
    # deleted_at: nullable
    # deleted_by: nullable
    # description: nullable
    # embedding: nullable
    # fts_vector: nullable
    # is_deleted: nullable, has default value
    # metadata: nullable, has default value
    # settings: nullable, has default value
    # star_count: nullable, has default value
    # status: has default value
    # tags: nullable, has default value
    # updated_at: nullable, has default value
    # version: nullable, has default value
    # visibility: has default value

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    created_by: UUID4 | None = Field(default=None)
    deleted_at: datetime.datetime | None = Field(default=None)
    deleted_by: UUID4 | None = Field(default=None)
    description: str | None = Field(default=None)
    embedding: Any | None = Field(default=None)
    fts_vector: str | None = Field(
        default=None,
        description="Full-text search vector: name(A) + description(B) + slug(C)",
    )
    is_deleted: bool | None = Field(default=None)
    metadata: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    name: (
        Annotated[str, StringConstraints(**{"min_length": 2, "max_length": 255})] | None
    ) = Field(default=None)
    organization_id: UUID4 | None = Field(default=None)
    owned_by: UUID4 | None = Field(default=None)
    settings: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    slug: str | None = Field(default=None)
    star_count: int | None = Field(default=None)
    status: PublicProjectStatusEnum | None = Field(default=None)
    tags: list[str] | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: UUID4 | None = Field(default=None)
    version: int | None = Field(default=None)
    visibility: PublicVisibilityEnum | None = Field(default=None)


class PropertyUpdate(CustomModelUpdate):
    """Property Update Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)

    # Field properties:
    # created_at: nullable, has default value
    # created_by: nullable
    # deleted_at: nullable
    # deleted_by: nullable
    # document_id: nullable
    # is_base: nullable, has default value
    # is_deleted: has default value
    # options: nullable, has default value
    # project_id: nullable
    # scope: nullable
    # updated_at: nullable, has default value
    # updated_by: nullable

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    created_by: UUID4 | None = Field(default=None)
    deleted_at: datetime.datetime | None = Field(default=None)
    deleted_by: UUID4 | None = Field(default=None)
    document_id: UUID4 | None = Field(default=None)
    is_base: bool | None = Field(default=None)
    is_deleted: bool | None = Field(default=None)
    name: str | None = Field(default=None)
    options: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    org_id: UUID4 | None = Field(default=None)
    project_id: UUID4 | None = Field(default=None)
    property_type: str | None = Field(default=None)
    scope: str | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: UUID4 | None = Field(default=None)


class RagEmbeddingUpdate(CustomModelUpdate):
    """RagEmbedding Update Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)

    # Field properties:
    # content_hash: nullable
    # created_at: nullable, has default value
    # metadata: nullable
    # quality_score: nullable, has default value

    # Optional fields
    content_hash: str | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    embedding: Any | None = Field(default=None)
    entity_id: str | None = Field(default=None)
    entity_type: str | None = Field(default=None)
    metadata: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    quality_score: float | None = Field(default=None)


class RagSearchAnalyticUpdate(CustomModelUpdate):
    """RagSearchAnalytic Update Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)

    # Field properties:
    # cache_hit: has default value
    # created_at: nullable, has default value
    # organization_id: nullable
    # user_id: nullable

    # Optional fields
    cache_hit: bool | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    execution_time_ms: int | None = Field(default=None)
    organization_id: UUID4 | None = Field(default=None)
    query_hash: str | None = Field(default=None)
    query_text: str | None = Field(default=None)
    result_count: int | None = Field(default=None)
    search_type: str | None = Field(default=None)
    user_id: UUID4 | None = Field(default=None)


class ReactFlowDiagramUpdate(CustomModelUpdate):
    """ReactFlowDiagram Update Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)

    # Field properties:
    # created_at: nullable, has default value
    # created_by: nullable
    # description: nullable
    # diagram_type: nullable, has default value
    # edges: has default value
    # layout_algorithm: nullable, has default value
    # metadata: nullable, has default value
    # name: has default value
    # nodes: has default value
    # settings: nullable, has default value
    # theme: nullable, has default value
    # updated_at: nullable, has default value
    # updated_by: nullable
    # viewport: nullable, has default value

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    created_by: UUID4 | None = Field(default=None)
    description: str | None = Field(default=None)
    diagram_type: str | None = Field(default=None)
    edges: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    layout_algorithm: str | None = Field(default=None)
    metadata: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    name: str | None = Field(default=None)
    nodes: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    project_id: UUID4 | None = Field(default=None)
    settings: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    theme: str | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: UUID4 | None = Field(default=None)
    viewport: dict | list[dict] | list[Any] | Json | None = Field(default=None)


class RequirementTestUpdate(CustomModelUpdate):
    """RequirementTest Update Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)

    # Field properties:
    # created_at: nullable, has default value
    # defects: nullable
    # evidence_artifacts: nullable
    # executed_at: nullable
    # executed_by: nullable
    # execution_environment: nullable
    # execution_status: has default value
    # execution_version: nullable
    # external_req_id: nullable
    # external_test_id: nullable
    # result_notes: nullable
    # updated_at: nullable, has default value

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    defects: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    evidence_artifacts: dict | list[dict] | list[Any] | Json | None = Field(
        default=None
    )
    executed_at: datetime.datetime | None = Field(default=None)
    executed_by: UUID4 | None = Field(default=None)
    execution_environment: str | None = Field(default=None)
    execution_status: PublicExecutionStatusEnum | None = Field(default=None)
    execution_version: str | None = Field(default=None)
    external_req_id: str | None = Field(default=None)
    external_test_id: str | None = Field(default=None)
    requirement_id: UUID4 | None = Field(default=None)
    result_notes: str | None = Field(default=None)
    test_id: UUID4 | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)


class RequirementUpdate(CustomModelUpdate):
    """Requirement Update Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)

    # Field properties:
    # ai_analysis: nullable, has default value
    # created_at: nullable, has default value
    # created_by: nullable
    # deleted_at: nullable
    # deleted_by: nullable
    # description: nullable
    # embedding: nullable
    # enchanced_requirement: nullable
    # external_id: nullable
    # field_format: has default value
    # field_type: nullable
    # fts_vector: nullable
    # is_deleted: nullable, has default value
    # level: has default value
    # original_requirement: nullable
    # position: has default value
    # priority: has default value
    # properties: nullable, has default value
    # status: has default value
    # tags: nullable, has default value
    # updated_at: nullable, has default value
    # updated_by: nullable
    # version: has default value

    # Optional fields
    ai_analysis: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    block_id: UUID4 | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    created_by: UUID4 | None = Field(default=None)
    deleted_at: datetime.datetime | None = Field(default=None)
    deleted_by: UUID4 | None = Field(default=None)
    description: str | None = Field(default=None)
    document_id: UUID4 | None = Field(default=None)
    embedding: Any | None = Field(default=None)
    enchanced_requirement: str | None = Field(default=None)
    external_id: str | None = Field(default=None)
    field_format: Any | None = Field(default=None, alias="format")
    field_type: str | None = Field(default=None, alias="type")
    fts_vector: str | None = Field(
        default=None,
        description="Full-text search vector: name(A) + description(B) + requirements(C)",
    )
    is_deleted: bool | None = Field(default=None)
    level: PublicRequirementLevelEnum | None = Field(default=None)
    name: str | None = Field(default=None)
    original_requirement: str | None = Field(default=None)
    position: float | None = Field(default=None)
    priority: PublicRequirementPriorityEnum | None = Field(default=None)
    properties: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    status: PublicRequirementStatusEnum | None = Field(default=None)
    tags: list[str] | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: UUID4 | None = Field(default=None)
    version: int | None = Field(default=None)


class RequirementsClosureUpdate(CustomModelUpdate):
    """RequirementsClosure Update Schema."""

    # Primary Keys
    ancestor_id: UUID4 | None = Field(default=None)
    descendant_id: UUID4 | None = Field(default=None)

    # Field properties:
    # created_at: has default value
    # updated_at: nullable
    # updated_by: nullable

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    created_by: UUID4 | None = Field(default=None)
    depth: int | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: UUID4 | None = Field(default=None)


class StripeCustomerUpdate(CustomModelUpdate):
    """StripeCustomer Update Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)

    # Field properties:
    # cancel_at_period_end: nullable, has default value
    # created_at: nullable, has default value
    # current_period_end: nullable
    # current_period_start: nullable
    # organization_id: nullable
    # payment_method_brand: nullable
    # payment_method_last4: nullable
    # price_id: nullable
    # stripe_customer_id: nullable
    # stripe_subscription_id: nullable
    # updated_at: nullable, has default value

    # Optional fields
    cancel_at_period_end: bool | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    current_period_end: datetime.datetime | None = Field(default=None)
    current_period_start: datetime.datetime | None = Field(default=None)
    organization_id: UUID4 | None = Field(default=None)
    payment_method_brand: str | None = Field(default=None)
    payment_method_last4: str | None = Field(default=None)
    price_id: str | None = Field(default=None)
    stripe_customer_id: str | None = Field(default=None)
    stripe_subscription_id: str | None = Field(default=None)
    subscription_status: PublicSubscriptionStatusEnum | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)


class TableRowUpdate(CustomModelUpdate):
    """TableRow Update Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)

    # Field properties:
    # created_at: nullable, has default value
    # created_by: nullable
    # deleted_at: nullable
    # deleted_by: nullable
    # is_deleted: nullable, has default value
    # position: has default value
    # row_data: nullable, has default value
    # updated_at: nullable, has default value
    # updated_by: nullable
    # version: has default value

    # Optional fields
    block_id: UUID4 | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    created_by: UUID4 | None = Field(default=None)
    deleted_at: datetime.datetime | None = Field(default=None)
    deleted_by: UUID4 | None = Field(default=None)
    document_id: UUID4 | None = Field(default=None)
    is_deleted: bool | None = Field(default=None)
    position: float | None = Field(default=None)
    row_data: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: UUID4 | None = Field(default=None)
    version: int | None = Field(default=None)


class TestMatrixViewUpdate(CustomModelUpdate):
    """TestMatrixView Update Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)

    # Field properties:
    # configuration: has default value
    # created_at: nullable, has default value
    # is_active: nullable, has default value
    # is_default: nullable, has default value
    # updated_at: nullable, has default value

    # Optional fields
    configuration: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    created_by: UUID4 | None = Field(default=None)
    is_active: bool | None = Field(default=None)
    is_default: bool | None = Field(default=None)
    name: str | None = Field(default=None)
    project_id: UUID4 | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: UUID4 | None = Field(default=None)


class TestReqUpdate(CustomModelUpdate):
    """TestReq Update Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)

    # Field properties:
    # attachments: nullable
    # category: nullable
    # created_at: nullable, has default value
    # created_by: nullable
    # deleted_at: nullable
    # deleted_by: nullable
    # description: nullable
    # estimated_duration: nullable
    # expected_results: nullable
    # is_active: nullable, has default value
    # is_deleted: has default value
    # method: has default value
    # preconditions: nullable
    # priority: has default value
    # project_id: nullable
    # result: nullable, has default value
    # status: has default value
    # test_environment: nullable
    # test_id: nullable
    # test_steps: nullable
    # test_type: has default value
    # updated_at: nullable, has default value
    # updated_by: nullable
    # version: nullable

    # Optional fields
    attachments: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    category: list[str] | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    created_by: UUID4 | None = Field(default=None)
    deleted_at: datetime.datetime | None = Field(default=None)
    deleted_by: UUID4 | None = Field(default=None)
    description: str | None = Field(default=None)
    estimated_duration: datetime.timedelta | None = Field(default=None)
    expected_results: str | None = Field(default=None)
    is_active: bool | None = Field(default=None)
    is_deleted: bool | None = Field(default=None)
    method: PublicTestMethodEnum | None = Field(default=None)
    preconditions: str | None = Field(default=None)
    priority: PublicTestPriorityEnum | None = Field(default=None)
    project_id: UUID4 | None = Field(default=None)
    result: str | None = Field(default=None)
    status: PublicTestStatusEnum | None = Field(default=None)
    test_environment: str | None = Field(default=None)
    test_id: str | None = Field(default=None)
    test_steps: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    test_type: PublicTestTypeEnum | None = Field(default=None)
    title: str | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: UUID4 | None = Field(default=None)
    version: str | None = Field(default=None)


class TraceLinkUpdate(CustomModelUpdate):
    """TraceLink Update Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)

    # Field properties:
    # created_at: nullable, has default value
    # created_by: nullable
    # deleted_at: nullable
    # deleted_by: nullable
    # description: nullable
    # is_deleted: nullable, has default value
    # updated_at: nullable, has default value
    # updated_by: nullable
    # version: has default value

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    created_by: UUID4 | None = Field(default=None)
    deleted_at: datetime.datetime | None = Field(default=None)
    deleted_by: UUID4 | None = Field(default=None)
    description: str | None = Field(default=None)
    is_deleted: bool | None = Field(default=None)
    link_type: PublicTraceLinkTypeEnum | None = Field(default=None)
    source_id: UUID4 | None = Field(default=None)
    source_type: PublicEntityTypeEnum | None = Field(default=None)
    target_id: UUID4 | None = Field(default=None)
    target_type: PublicEntityTypeEnum | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    updated_by: UUID4 | None = Field(default=None)
    version: int | None = Field(default=None)


class UsageLogUpdate(CustomModelUpdate):
    """UsageLog Update Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)

    # Field properties:
    # created_at: nullable, has default value
    # metadata: nullable, has default value

    # Optional fields
    created_at: datetime.datetime | None = Field(default=None)
    feature: str | None = Field(default=None)
    metadata: dict | list[dict] | list[Any] | Json | None = Field(default=None)
    organization_id: UUID4 | None = Field(default=None)
    quantity: int | None = Field(default=None)
    unit_type: str | None = Field(default=None)
    user_id: UUID4 | None = Field(default=None)


class UserRoleUpdate(CustomModelUpdate):
    """UserRole Update Schema."""

    # Primary Keys
    id: UUID4 | None = Field(default=None)

    # Field properties:
    # admin_role: nullable
    # created_at: has default value
    # document_id: nullable
    # document_role: nullable
    # org_id: nullable
    # project_id: nullable
    # project_role: nullable
    # updated_at: has default value

    # Optional fields
    admin_role: PublicUserRoleTypeEnum | None = Field(default=None)
    created_at: datetime.datetime | None = Field(default=None)
    document_id: UUID4 | None = Field(default=None)
    document_role: PublicProjectRoleEnum | None = Field(default=None)
    org_id: UUID4 | None = Field(default=None)
    project_id: UUID4 | None = Field(default=None)
    project_role: PublicProjectRoleEnum | None = Field(default=None)
    updated_at: datetime.datetime | None = Field(default=None)
    user_id: UUID4 | None = Field(default=None)


# OPERATIONAL CLASSES


class Assignment(AssignmentBaseSchema):
    """Assignment Schema for Pydantic.

    Inherits from AssignmentBaseSchema. Add any customization here.
    """

    pass


class AuditLog(AuditLogBaseSchema):
    """AuditLog Schema for Pydantic.

    Inherits from AuditLogBaseSchema. Add any customization here.
    """

    # Foreign Keys
    organizations: Organization | None = Field(default=None)
    projects: Project | None = Field(default=None)
    profiles: Profile | None = Field(default=None)


class BillingCache(BillingCacheBaseSchema):
    """BillingCache Schema for Pydantic.

    Inherits from BillingCacheBaseSchema. Add any customization here.
    """

    # Foreign Keys
    organizations: Organization | None = Field(default=None)


class Block(BlockBaseSchema):
    """Block Schema for Pydantic.

    Inherits from BlockBaseSchema. Add any customization here.
    """

    # Foreign Keys
    documents: Document | None = Field(default=None)
    organizations: Organization | None = Field(default=None)
    columns: list[Column] | None = Field(default=None)
    requirements: list[Requirement] | None = Field(default=None)
    table_rows: list[TableRow] | None = Field(default=None)


class Column(ColumnBaseSchema):
    """Column Schema for Pydantic.

    Inherits from ColumnBaseSchema. Add any customization here.
    """

    # Foreign Keys
    blocks: Block | None = Field(default=None)
    properties: Property | None = Field(default=None)


class DiagramElementLink(DiagramElementLinkBaseSchema):
    """DiagramElementLink Schema for Pydantic.

    Inherits from DiagramElementLinkBaseSchema. Add any customization here.
    """

    # Foreign Keys
    excalidraw_diagrams: ExcalidrawDiagram | None = Field(default=None)
    requirements: Requirement | None = Field(default=None)


class DiagramElementLinksWithDetail(DiagramElementLinksWithDetailBaseSchema):
    """DiagramElementLinksWithDetail Schema for Pydantic.

    Inherits from DiagramElementLinksWithDetailBaseSchema. Add any customization here.
    """

    pass


class Document(DocumentBaseSchema):
    """Document Schema for Pydantic.

    Inherits from DocumentBaseSchema. Add any customization here.
    """

    # Foreign Keys
    projects: Project | None = Field(default=None)
    blocks: list[Block] | None = Field(default=None)
    properties: list[Property] | None = Field(default=None)
    requirements: list[Requirement] | None = Field(default=None)
    table_rows: list[TableRow] | None = Field(default=None)
    user_roles: list[UserRole] | None = Field(default=None)


class EmbeddingCache(EmbeddingCacheBaseSchema):
    """EmbeddingCache Schema for Pydantic.

    Inherits from EmbeddingCacheBaseSchema. Add any customization here.
    """

    pass


class ExcalidrawDiagram(ExcalidrawDiagramBaseSchema):
    """ExcalidrawDiagram Schema for Pydantic.

    Inherits from ExcalidrawDiagramBaseSchema. Add any customization here.
    """

    # Foreign Keys
    diagram_element_links: DiagramElementLink | None = Field(default=None)


class ExcalidrawElementLink(ExcalidrawElementLinkBaseSchema):
    """ExcalidrawElementLink Schema for Pydantic.

    Inherits from ExcalidrawElementLinkBaseSchema. Add any customization here.
    """

    pass


class ExternalDocument(ExternalDocumentBaseSchema):
    """ExternalDocument Schema for Pydantic.

    Inherits from ExternalDocumentBaseSchema. Add any customization here.
    """

    pass


class McpSession(McpSessionBaseSchema):
    """McpSession Schema for Pydantic.

    Inherits from McpSessionBaseSchema. Add any customization here.
    """

    pass


class Notification(NotificationBaseSchema):
    """Notification Schema for Pydantic.

    Inherits from NotificationBaseSchema. Add any customization here.
    """

    pass


class OauthAccessToken(OauthAccessTokenBaseSchema):
    """OauthAccessToken Schema for Pydantic.

    Inherits from OauthAccessTokenBaseSchema. Add any customization here.
    """

    pass


class OauthAuthorizationCode(OauthAuthorizationCodeBaseSchema):
    """OauthAuthorizationCode Schema for Pydantic.

    Inherits from OauthAuthorizationCodeBaseSchema. Add any customization here.
    """

    # Foreign Keys
    profiles: Profile | None = Field(default=None)


class OauthClient(OauthClientBaseSchema):
    """OauthClient Schema for Pydantic.

    Inherits from OauthClientBaseSchema. Add any customization here.
    """

    pass


class OauthRefreshToken(OauthRefreshTokenBaseSchema):
    """OauthRefreshToken Schema for Pydantic.

    Inherits from OauthRefreshTokenBaseSchema. Add any customization here.
    """

    # Foreign Keys
    profiles: Profile | None = Field(default=None)


class OrganizationInvitation(OrganizationInvitationBaseSchema):
    """OrganizationInvitation Schema for Pydantic.

    Inherits from OrganizationInvitationBaseSchema. Add any customization here.
    """

    # Foreign Keys
    organizations: Organization | None = Field(default=None)


class OrganizationMember(OrganizationMemberBaseSchema):
    """OrganizationMember Schema for Pydantic.

    Inherits from OrganizationMemberBaseSchema. Add any customization here.
    """

    # Foreign Keys
    organizations: Organization | None = Field(default=None)


class Organization(OrganizationBaseSchema):
    """Organization Schema for Pydantic.

    Inherits from OrganizationBaseSchema. Add any customization here.
    """

    # Foreign Keys
    audit_logs: list[AuditLog] | None = Field(default=None)
    billing_cache: BillingCache | None = Field(default=None)
    blocks: list[Block] | None = Field(default=None)
    organization_invitations: list[OrganizationInvitation] | None = Field(default=None)
    organization_members: OrganizationMember | None = Field(default=None)
    project_members: list[ProjectMember] | None = Field(default=None)
    projects: list[Project] | None = Field(default=None)
    properties: list[Property] | None = Field(default=None)
    stripe_customers: StripeCustomer | None = Field(default=None)
    usage_logs: list[UsageLog] | None = Field(default=None)
    user_roles: list[UserRole] | None = Field(default=None)


class Profile(ProfileBaseSchema):
    """Profile Schema for Pydantic.

    Inherits from ProfileBaseSchema. Add any customization here.
    """

    # Foreign Keys
    audit_logs: list[AuditLog] | None = Field(default=None)
    oauth_authorization_codes: list[OauthAuthorizationCode] | None = Field(default=None)
    oauth_refresh_tokens: list[OauthRefreshToken] | None = Field(default=None)
    properties: list[Property] | None = Field(default=None)
    requirements_closures: list[RequirementsClosure] | None = Field(default=None)
    test_reqs: list[TestReq] | None = Field(default=None)


class ProjectInvitation(ProjectInvitationBaseSchema):
    """ProjectInvitation Schema for Pydantic.

    Inherits from ProjectInvitationBaseSchema. Add any customization here.
    """

    # Foreign Keys
    projects: Project | None = Field(default=None)


class ProjectMember(ProjectMemberBaseSchema):
    """ProjectMember Schema for Pydantic.

    Inherits from ProjectMemberBaseSchema. Add any customization here.
    """

    # Foreign Keys
    organizations: Organization | None = Field(default=None)
    projects: Project | None = Field(default=None)


class Project(ProjectBaseSchema):
    """Project Schema for Pydantic.

    Inherits from ProjectBaseSchema. Add any customization here.
    """

    # Foreign Keys
    organizations: Organization | None = Field(default=None)
    audit_logs: list[AuditLog] | None = Field(default=None)
    documents: list[Document] | None = Field(default=None)
    project_invitations: list[ProjectInvitation] | None = Field(default=None)
    project_members: ProjectMember | None = Field(default=None)
    properties: list[Property] | None = Field(default=None)
    react_flow_diagrams: list[ReactFlowDiagram] | None = Field(default=None)
    test_matrix_views: list[TestMatrixView] | None = Field(default=None)
    test_reqs: list[TestReq] | None = Field(default=None)
    user_roles: list[UserRole] | None = Field(default=None)


class Property(PropertyBaseSchema):
    """Property Schema for Pydantic.

    Inherits from PropertyBaseSchema. Add any customization here.
    """

    # Foreign Keys
    profiles: list[Profile] | None = Field(default=None)
    documents: Document | None = Field(default=None)
    organizations: Organization | None = Field(default=None)
    projects: Project | None = Field(default=None)
    columns: list[Column] | None = Field(default=None)


class RagEmbedding(RagEmbeddingBaseSchema):
    """RagEmbedding Schema for Pydantic.

    Inherits from RagEmbeddingBaseSchema. Add any customization here.
    """

    pass


class RagSearchAnalytic(RagSearchAnalyticBaseSchema):
    """RagSearchAnalytic Schema for Pydantic.

    Inherits from RagSearchAnalyticBaseSchema. Add any customization here.
    """

    pass


class ReactFlowDiagram(ReactFlowDiagramBaseSchema):
    """ReactFlowDiagram Schema for Pydantic.

    Inherits from ReactFlowDiagramBaseSchema. Add any customization here.
    """

    # Foreign Keys
    projects: Project | None = Field(default=None)


class RequirementTest(RequirementTestBaseSchema):
    """RequirementTest Schema for Pydantic.

    Inherits from RequirementTestBaseSchema. Add any customization here.
    """

    # Foreign Keys
    requirements: Requirement | None = Field(default=None)
    test_req: TestReq | None = Field(default=None)


class Requirement(RequirementBaseSchema):
    """Requirement Schema for Pydantic.

    Inherits from RequirementBaseSchema. Add any customization here.
    """

    # Foreign Keys
    blocks: Block | None = Field(default=None)
    documents: Document | None = Field(default=None)
    diagram_element_links: DiagramElementLink | None = Field(default=None)
    requirement_tests: RequirementTest | None = Field(default=None)
    requirements_closures: list[RequirementsClosure] | None = Field(default=None)


class RequirementsClosure(RequirementsClosureBaseSchema):
    """RequirementsClosure Schema for Pydantic.

    Inherits from RequirementsClosureBaseSchema. Add any customization here.
    """

    # Foreign Keys
    requirements: Requirement | None = Field(default=None)
    profiles: list[Profile] | None = Field(default=None)


class StripeCustomer(StripeCustomerBaseSchema):
    """StripeCustomer Schema for Pydantic.

    Inherits from StripeCustomerBaseSchema. Add any customization here.
    """

    # Foreign Keys
    organizations: Organization | None = Field(default=None)


class TableRow(TableRowBaseSchema):
    """TableRow Schema for Pydantic.

    Inherits from TableRowBaseSchema. Add any customization here.
    """

    # Foreign Keys
    blocks: Block | None = Field(default=None)
    documents: Document | None = Field(default=None)


class TestMatrixView(TestMatrixViewBaseSchema):
    """TestMatrixView Schema for Pydantic.

    Inherits from TestMatrixViewBaseSchema. Add any customization here.
    """

    # Foreign Keys
    projects: Project | None = Field(default=None)


class TestReq(TestReqBaseSchema):
    """TestReq Schema for Pydantic.

    Inherits from TestReqBaseSchema. Add any customization here.
    """

    # Foreign Keys
    profiles: list[Profile] | None = Field(default=None)
    projects: Project | None = Field(default=None)
    requirement_tests: RequirementTest | None = Field(default=None)


class TraceLink(TraceLinkBaseSchema):
    """TraceLink Schema for Pydantic.

    Inherits from TraceLinkBaseSchema. Add any customization here.
    """

    pass


class UsageLog(UsageLogBaseSchema):
    """UsageLog Schema for Pydantic.

    Inherits from UsageLogBaseSchema. Add any customization here.
    """

    # Foreign Keys
    organizations: Organization | None = Field(default=None)


class UserRole(UserRoleBaseSchema):
    """UserRole Schema for Pydantic.

    Inherits from UserRoleBaseSchema. Add any customization here.
    """

    # Foreign Keys
    documents: Document | None = Field(default=None)
    organizations: Organization | None = Field(default=None)
    projects: Project | None = Field(default=None)
