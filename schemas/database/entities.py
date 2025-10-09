"""
TypedDict definitions for entity database rows.

These types represent the exact structure of rows returned from Supabase.
Use these in database adapter layers and Supabase query results.

All fields are marked as Optional (total=False) to allow partial row selection.
"""

from typing import TypedDict, Optional, Any


class OrganizationRow(TypedDict, total=False):
    """Database row for organizations table.

    Actual columns from DB:
    - Core: id, name, slug, description, type
    - Billing: billing_plan, billing_cycle, max_members, max_monthly_requests
    - Settings: settings, metadata, logo_url
    - Stats: member_count, storage_used, status
    - Ownership: owner_id, created_by, updated_by, deleted_by
    - Timestamps: created_at, updated_at, deleted_at
    - Soft delete: is_deleted
    - Search: embedding, fts_vector
    """
    id: str
    name: str
    slug: str
    description: Optional[str]
    type: str  # "personal", "team", or "enterprise"
    logo_url: Optional[str]
    billing_plan: str  # "free", "pro", or "enterprise"
    billing_cycle: str  # "none", "month", or "year"
    max_members: int
    max_monthly_requests: int
    settings: Optional[dict]
    metadata: Optional[dict]
    member_count: Optional[int]
    storage_used: Optional[int]
    status: Optional[str]  # "active" or "inactive"
    owner_id: Optional[str]
    created_by: str
    updated_by: str
    deleted_by: Optional[str]
    created_at: str
    updated_at: str
    deleted_at: Optional[str]
    is_deleted: bool
    embedding: Optional[list]  # Vector embedding
    fts_vector: Optional[str]  # Full-text search vector


class ProjectRow(TypedDict, total=False):
    """Database row for projects table.

    Actual columns from DB:
    - Core: id, name, slug, description, organization_id
    - Access: visibility, status, owned_by
    - Settings: settings, metadata
    - Stats: star_count, tags
    - Ownership: created_by, updated_by, deleted_by
    - Timestamps: created_at, updated_at, deleted_at
    - Versioning: version
    - Soft delete: is_deleted
    - Search: embedding, fts_vector
    """
    id: str
    organization_id: str
    name: str
    slug: str
    description: Optional[str]
    visibility: str  # "private", "team", "organization", or "public"
    status: str  # "active", "archived", "draft", or "deleted"
    settings: Optional[dict]
    star_count: Optional[int]
    tags: Optional[list[str]]
    metadata: Optional[dict]
    created_by: str
    updated_by: str
    owned_by: str
    version: Optional[int]
    created_at: str
    updated_at: str
    deleted_at: Optional[str]
    is_deleted: bool
    deleted_by: Optional[str]
    embedding: Optional[list]
    fts_vector: Optional[str]


class DocumentRow(TypedDict, total=False):
    """Database row for documents table.

    Actual columns from DB:
    - Core: id, project_id, name, description, slug
    - Tags: tags (array)
    - Ownership: created_by, updated_by, deleted_by
    - Timestamps: created_at, updated_at, deleted_at
    - Versioning: version
    - Soft delete: is_deleted
    - Search: embedding, fts_vector
    """
    id: str
    project_id: str
    name: str
    description: Optional[str]
    slug: str
    tags: Optional[list[str]]
    created_at: str
    updated_at: str
    created_by: Optional[str]
    updated_by: Optional[str]
    version: int
    is_deleted: bool
    deleted_at: Optional[str]
    deleted_by: Optional[str]
    embedding: Optional[list]
    fts_vector: Optional[str]


class RequirementRow(TypedDict, total=False):
    """Database row for requirements table.

    Actual columns from DB:
    - Core: id, document_id, block_id, external_id, name, description
    - Classification: status, format, priority, level, type, tags
    - Content: original_requirement, enchanced_requirement, ai_analysis
    - Ordering: position
    - Properties: properties (jsonb)
    - Ownership: created_by, updated_by, deleted_by
    - Timestamps: created_at, updated_at, deleted_at
    - Versioning: version
    - Soft delete: is_deleted
    - Search: embedding, fts_vector
    """
    id: str
    document_id: str
    block_id: str
    external_id: Optional[str]
    name: str
    description: Optional[str]
    status: str  # "active", "archived", "draft", "deleted", "in_review", "in_progress", "approved", "rejected"
    format: str  # "incose", "ears", or "other"
    priority: str  # "low", "medium", "high", or "critical"
    level: str  # "component", "system", or "subsystem"
    type: Optional[str]
    tags: Optional[list[str]]
    original_requirement: Optional[str]
    enchanced_requirement: Optional[str]
    ai_analysis: Optional[dict]
    position: float
    properties: Optional[dict]
    created_at: str
    updated_at: str
    created_by: Optional[str]
    updated_by: Optional[str]
    version: int
    is_deleted: bool
    deleted_at: Optional[str]
    deleted_by: Optional[str]
    embedding: Optional[list]
    fts_vector: Optional[str]


class TestRow(TypedDict, total=False):
    """Database row for test_req table.

    Actual columns from DB:
    - Core: id, title, description, project_id, test_id
    - Classification: test_type, priority, status, method, category
    - Results: result, expected_results
    - Execution: preconditions, test_steps, test_environment, estimated_duration
    - Metadata: attachments, version
    - Status: is_active
    - Ownership: created_by, updated_by, deleted_by
    - Timestamps: created_at, updated_at, deleted_at
    - Soft delete: is_deleted
    """
    id: str
    title: str
    description: Optional[str]
    project_id: Optional[str]
    test_id: Optional[str]
    test_type: str  # "unit", "integration", "system", "acceptance", "performance", "security", "usability", "other"
    priority: str  # "critical", "high", "medium", or "low"
    status: str  # "draft", "ready", "in_progress", "blocked", "completed", "obsolete"
    method: str  # "manual", "automated", or "hybrid"
    result: Optional[str]
    expected_results: Optional[str]
    preconditions: Optional[str]
    test_steps: Optional[dict]  # JSONB
    estimated_duration: Optional[str]  # interval
    category: Optional[list[str]]
    test_environment: Optional[str]
    attachments: Optional[dict]  # JSONB
    version: Optional[str]
    is_active: Optional[bool]
    created_by: Optional[str]
    updated_by: Optional[str]
    deleted_by: Optional[str]
    created_at: str
    updated_at: str
    deleted_at: Optional[str]
    is_deleted: bool


class ProfileRow(TypedDict, total=False):
    """Database row for profiles table.

    Actual columns from DB:
    - Core: id, email, full_name, avatar_url
    - Organization: personal_organization_id, current_organization_id, pinned_organization_id
    - Profile: job_title, preferences, status
    - Activity: last_login_at, login_count
    - Approval: is_approved
    - Timestamps: created_at, updated_at, deleted_at
    - Soft delete: is_deleted, deleted_by
    """
    id: str
    email: str
    full_name: Optional[str]
    avatar_url: Optional[str]
    personal_organization_id: Optional[str]
    current_organization_id: Optional[str]
    pinned_organization_id: Optional[str]
    job_title: Optional[str]
    preferences: Optional[dict]
    status: Optional[str]  # "active" or "inactive"
    last_login_at: Optional[str]
    login_count: Optional[int]
    is_approved: bool
    created_at: str
    updated_at: str
    is_deleted: bool
    deleted_at: Optional[str]
    deleted_by: Optional[str]


class BlockRow(TypedDict, total=False):
    """Database row for blocks table.

    Actual columns from DB:
    - Core: id, document_id, name, type, position
    - Content: content (jsonb)
    - Organization: org_id
    - Ownership: created_by, updated_by, deleted_by
    - Timestamps: created_at, updated_at, deleted_at
    - Versioning: version
    - Soft delete: is_deleted
    """
    id: str
    document_id: str
    name: str
    type: str  # "text", "image", or "table"
    position: int
    content: Optional[dict]
    org_id: Optional[str]
    created_by: Optional[str]
    updated_by: Optional[str]
    deleted_by: Optional[str]
    created_at: str
    updated_at: str
    deleted_at: Optional[str]
    version: int
    is_deleted: bool


class PropertyRow(TypedDict, total=False):
    """Database row for properties table.

    Actual columns from DB:
    - Core: id, name, property_type, scope
    - Organization: org_id, project_id, document_id
    - Configuration: options (jsonb), is_base
    - Ownership: created_by, updated_by, deleted_by
    - Timestamps: created_at, updated_at, deleted_at
    - Soft delete: is_deleted
    """
    id: str
    org_id: str
    project_id: Optional[str]
    document_id: Optional[str]
    name: str
    property_type: str  # "text", "number", "boolean", "date", "url", "array", "enum", "entity_reference", "select", "multi_select", "file"
    scope: Optional[str]  # "org", "project", or "document"
    options: Optional[dict]
    is_base: Optional[bool]
    created_by: Optional[str]
    updated_by: Optional[str]
    deleted_by: Optional[str]
    created_at: str
    updated_at: str
    deleted_at: Optional[str]
    is_deleted: bool


class ColumnsRow(TypedDict, total=False):
    """Database row for columns table (table block column metadata).

    Actual columns from DB:
    - Core: id, block_id, property_id, position
    - Display: width, is_hidden, is_pinned, default_value
    - Ownership: created_by, updated_by
    - Timestamps: created_at, updated_at
    """
    id: str
    block_id: Optional[str]
    property_id: str
    position: float
    width: Optional[int]
    is_hidden: Optional[bool]
    is_pinned: Optional[bool]
    default_value: Optional[str]
    created_by: Optional[str]
    updated_by: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]


class TableRowsRow(TypedDict, total=False):
    """Database row for table_rows table (table block row data).

    Actual columns from DB:
    - Core: id, document_id, block_id, row_data (jsonb), position
    - Ownership: created_by, updated_by, deleted_by
    - Timestamps: created_at, updated_at, deleted_at
    - Versioning: version
    - Soft delete: is_deleted
    """
    id: str
    document_id: str
    block_id: str
    row_data: Optional[dict]
    position: float
    created_by: Optional[str]
    updated_by: Optional[str]
    deleted_by: Optional[str]
    created_at: str
    updated_at: str
    deleted_at: Optional[str]
    version: int
    is_deleted: bool


class RequirementsClosureRow(TypedDict, total=False):
    """Database row for requirements_closure table (hierarchy closure table).

    Actual columns from DB:
    - Core: ancestor_id, descendant_id, depth
    - Ownership: created_by, updated_by
    - Timestamps: created_at, updated_at
    """
    ancestor_id: str
    descendant_id: str
    depth: int
    created_by: str
    updated_by: Optional[str]
    created_at: str
    updated_at: Optional[str]


class DiagramElementLinksRow(TypedDict, total=False):
    """Database row for diagram_element_links table.

    Actual columns from DB:
    - Core: id, diagram_id, element_id, requirement_id
    - Classification: link_type ("manual" or "auto_detected")
    - Metadata: metadata (jsonb)
    - Ownership: created_by
    - Timestamps: created_at, updated_at
    """
    id: str
    diagram_id: str
    element_id: str
    requirement_id: str
    link_type: Optional[str]
    metadata: Optional[dict]
    created_by: Optional[str]
    created_at: str
    updated_at: str


class ExcalidrawDiagramsRow(TypedDict, total=False):
    """Database row for excalidraw_diagrams table.

    Actual columns from DB:
    - Core: id, name, diagram_data (jsonb), thumbnail_url
    - Organization: organization_id, project_id
    - Ownership: created_by, updated_by
    - Timestamps: created_at, updated_at
    """
    id: str
    name: Optional[str]
    diagram_data: Optional[dict]
    thumbnail_url: Optional[str]
    organization_id: Optional[str]
    project_id: Optional[str]
    created_by: Optional[str]
    updated_by: Optional[str]
    created_at: str
    updated_at: Optional[str]


class ReactFlowDiagramsRow(TypedDict, total=False):
    """Database row for react_flow_diagrams table.

    Actual columns from DB:
    - Core: id, project_id, name, description
    - Diagram: nodes (jsonb), edges (jsonb), viewport (jsonb)
    - Configuration: diagram_type, layout_algorithm, theme, settings (jsonb)
    - Metadata: metadata (jsonb)
    - Ownership: created_by, updated_by
    - Timestamps: created_at, updated_at
    """
    id: str
    project_id: str
    name: str
    description: Optional[str]
    nodes: dict
    edges: dict
    viewport: Optional[dict]
    diagram_type: Optional[str]  # "workflow", "requirements", "architecture", "mixed"
    layout_algorithm: Optional[str]  # "dagre", "elk", "force", "hierarchical", "manual"
    theme: Optional[str]  # "light" or "dark"
    settings: Optional[dict]
    metadata: Optional[dict]
    created_by: Optional[str]
    updated_by: Optional[str]
    created_at: str
    updated_at: str


class AuditLogsRow(TypedDict, total=False):
    """Database row for audit_logs table.

    Actual columns from DB:
    - Core: id, entity_id, entity_type, action
    - Event: event_type, severity, description
    - Actor: actor_id, user_id, session_id
    - Context: ip_address, user_agent, source_system
    - Resource: resource_type, resource_id, organization_id, project_id
    - Data: old_data, new_data, details, metadata
    - Compliance: soc2_control, compliance_category, risk_level, threat_indicators
    - Correlation: correlation_id
    - Timestamps: created_at, updated_at, timestamp
    """
    id: str
    entity_id: str
    entity_type: str
    action: str
    event_type: Optional[str]
    severity: Optional[str]  # "low", "medium", "high", "critical"
    description: Optional[str]
    actor_id: Optional[str]
    user_id: Optional[str]
    session_id: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    source_system: Optional[str]
    resource_type: Optional[str]
    resource_id: Optional[str]
    organization_id: Optional[str]
    project_id: Optional[str]
    old_data: Optional[dict]
    new_data: Optional[dict]
    details: Optional[dict]
    metadata: Optional[dict]
    soc2_control: Optional[str]
    compliance_category: Optional[str]
    risk_level: Optional[str]
    threat_indicators: Optional[list[str]]
    correlation_id: Optional[str]
    created_at: str
    updated_at: Optional[str]
    timestamp: Optional[str]


class TraceLinksRow(TypedDict, total=False):
    """Database row for trace_links table.

    Actual columns from DB:
    - Core: id, source_id, target_id, source_type, target_type, link_type
    - Description: description
    - Ownership: created_by, updated_by, deleted_by
    - Timestamps: created_at, updated_at, deleted_at
    - Versioning: version
    - Soft delete: is_deleted
    """
    id: str
    source_id: str
    target_id: str
    source_type: str  # "document" or "requirement"
    target_type: str  # "document" or "requirement"
    link_type: str  # "derives_from", "implements", "relates_to", "conflicts_with", "is_related_to", "parent_of", "child_of"
    description: Optional[str]
    created_by: Optional[str]
    updated_by: Optional[str]
    deleted_by: Optional[str]
    created_at: str
    updated_at: str
    deleted_at: Optional[str]
    version: int
    is_deleted: bool


class AssignmentsRow(TypedDict, total=False):
    """Database row for assignments table.

    Actual columns from DB:
    - Core: id, entity_id, entity_type, assignee_id, role
    - Status: status, comment, due_date, completed_at
    - Ownership: created_by, updated_by, deleted_by
    - Timestamps: created_at, updated_at, deleted_at
    - Versioning: version
    - Soft delete: is_deleted
    """
    id: str
    entity_id: str
    entity_type: str  # "document" or "requirement"
    assignee_id: str
    role: str  # "assignee", "reviewer", or "approver"
    status: str
    comment: Optional[str]
    due_date: Optional[str]
    completed_at: Optional[str]
    created_by: Optional[str]
    updated_by: Optional[str]
    deleted_by: Optional[str]
    created_at: str
    updated_at: str
    deleted_at: Optional[str]
    version: int
    is_deleted: bool


class NotificationsRow(TypedDict, total=False):
    """Database row for notifications table.

    Actual columns from DB:
    - Core: id, user_id, type, title, message
    - Status: unread, read_at
    - Metadata: metadata (jsonb)
    - Timestamps: created_at
    """
    id: str
    user_id: str
    type: str  # "invitation", "mention", or "system"
    title: str
    message: Optional[str]
    unread: Optional[bool]
    metadata: Optional[dict]
    read_at: Optional[str]
    created_at: str
