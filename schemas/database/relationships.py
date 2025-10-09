"""
TypedDict definitions for relationship junction tables.

These types represent the exact structure of rows returned from Supabase.
All fields are marked as Optional (total=False) to allow partial row selection.
"""

from typing import TypedDict, Optional


class OrganizationMemberRow(TypedDict, total=False):
    """Database row for organization_members table.

    Actual columns from DB:
    - Core: id, organization_id, user_id, role, status
    - Activity: last_active_at
    - Permissions: permissions (jsonb)
    - Ownership: deleted_by, updated_by
    - Timestamps: created_at, updated_at, deleted_at
    - Soft delete: is_deleted
    """
    id: str
    organization_id: str
    user_id: str
    role: str  # "member", "admin", "owner", or "super_admin"
    status: Optional[str]  # "active" or "inactive"
    last_active_at: Optional[str]
    permissions: Optional[dict]
    deleted_by: Optional[str]
    updated_by: Optional[str]
    created_at: str
    updated_at: str
    deleted_at: Optional[str]
    is_deleted: bool


class ProjectMemberRow(TypedDict, total=False):
    """Database row for project_members table.

    Actual columns from DB:
    - Core: id, project_id, user_id, org_id, role, status
    - Activity: last_accessed_at
    - Permissions: permissions (jsonb)
    - Ownership: deleted_by
    - Timestamps: created_at, updated_at, deleted_at
    - Soft delete: is_deleted
    """
    id: str
    project_id: str
    user_id: str
    org_id: Optional[str]
    role: str  # "owner", "admin", "maintainer", "editor", or "viewer"
    status: Optional[str]  # "active" or "inactive"
    last_accessed_at: Optional[str]
    permissions: Optional[dict]
    deleted_by: Optional[str]
    created_at: str
    updated_at: str
    deleted_at: Optional[str]
    is_deleted: bool


class RequirementTestRow(TypedDict, total=False):
    """Database row for requirement_tests table.

    Actual columns from DB:
    - Core: id, requirement_id, test_id
    - Execution: execution_status, result_notes, executed_at, executed_by
    - Environment: execution_environment, execution_version
    - Evidence: defects (jsonb), evidence_artifacts (jsonb)
    - External IDs: external_test_id, external_req_id
    - Timestamps: created_at, updated_at
    """
    id: str
    requirement_id: str
    test_id: str
    execution_status: str  # "not_executed", "in_progress", "passed", "failed", "blocked", or "skipped"
    result_notes: Optional[str]
    executed_at: Optional[str]
    executed_by: Optional[str]
    execution_environment: Optional[str]
    execution_version: Optional[str]
    defects: Optional[dict]
    evidence_artifacts: Optional[dict]
    external_test_id: Optional[str]
    external_req_id: Optional[str]
    created_at: str
    updated_at: str


class OrganizationInvitationRow(TypedDict, total=False):
    """Database row for organization_invitations table.

    Actual columns from DB:
    - Core: id, organization_id, email, role, token, status
    - Expiry: expires_at
    - Metadata: metadata (jsonb)
    - Ownership: created_by, updated_by, deleted_by
    - Timestamps: created_at, updated_at, deleted_at
    - Soft delete: is_deleted
    """
    id: str
    organization_id: str
    email: str
    role: str  # "member", "admin", "owner", or "super_admin"
    token: str
    status: str  # "pending", "accepted", "rejected", or "revoked"
    expires_at: str
    metadata: Optional[dict]
    created_by: str
    updated_by: str
    deleted_by: Optional[str]
    created_at: str
    updated_at: str
    deleted_at: Optional[str]
    is_deleted: bool


class ProjectInvitationRow(TypedDict, total=False):
    """Database row for project_invitations table.

    Actual columns from DB:
    - Core: id, project_id, email, role, token, status
    - Expiry: expires_at
    - Metadata: metadata (jsonb)
    - Ownership: created_by, updated_by, deleted_by
    - Timestamps: created_at, updated_at, deleted_at
    - Soft delete: is_deleted
    """
    id: str
    project_id: str
    email: str
    role: str  # "owner", "admin", "maintainer", "editor", or "viewer"
    token: str
    status: str  # "pending", "accepted", "rejected", or "revoked"
    expires_at: str
    metadata: Optional[dict]
    created_by: str
    updated_by: str
    deleted_by: Optional[str]
    created_at: str
    updated_at: str
    deleted_at: Optional[str]
    is_deleted: bool


class UserRolesRow(TypedDict, total=False):
    """Database row for user_roles table.

    Actual columns from DB:
    - Core: id, user_id
    - Roles: admin_role, project_role, document_role
    - Scope: project_id, document_id, org_id
    - Timestamps: created_at, updated_at
    """
    id: str
    user_id: str
    admin_role: Optional[str]  # "member", "admin", "owner", or "super_admin"
    project_role: Optional[str]  # "owner", "admin", "maintainer", "editor", or "viewer"
    document_role: Optional[str]  # "owner", "admin", "maintainer", "editor", or "viewer"
    project_id: Optional[str]
    document_id: Optional[str]
    org_id: Optional[str]
    created_at: str
    updated_at: str


class ExternalDocumentsRow(TypedDict, total=False):
    """Database row for external_documents table.

    Actual columns from DB:
    - Core: id, organization_id, name, url, type, size
    - Integration: gumloop_name
    - Ownership: created_by, updated_by, owned_by, deleted_by
    - Timestamps: created_at, updated_at, deleted_at
    - Soft delete: is_deleted
    """
    id: str
    organization_id: str
    name: str
    url: Optional[str]
    type: Optional[str]
    size: Optional[int]
    gumloop_name: Optional[str]
    created_by: Optional[str]
    updated_by: Optional[str]
    owned_by: Optional[str]
    deleted_by: Optional[str]
    created_at: str
    updated_at: str
    deleted_at: Optional[str]
    is_deleted: bool


class UsageLogsRow(TypedDict, total=False):
    """Database row for usage_logs table.

    Actual columns from DB:
    - Core: id, organization_id, user_id, feature, quantity, unit_type
    - Metadata: metadata (jsonb)
    - Timestamps: created_at
    """
    id: str
    organization_id: str
    user_id: str
    feature: str
    quantity: int
    unit_type: str
    metadata: Optional[dict]
    created_at: str


class BillingCacheRow(TypedDict, total=False):
    """Database row for billing_cache table.

    Actual columns from DB:
    - Core: organization_id
    - Status: billing_status (jsonb), current_period_usage (jsonb)
    - Period: period_start, period_end
    - Sync: synced_at
    """
    organization_id: str
    billing_status: dict
    current_period_usage: dict
    period_start: str
    period_end: str
    synced_at: str


class StripeCustomersRow(TypedDict, total=False):
    """Database row for stripe_customers table.

    Actual columns from DB:
    - Core: id, organization_id
    - Stripe: stripe_customer_id, stripe_subscription_id, subscription_status, price_id
    - Period: current_period_start, current_period_end, cancel_at_period_end
    - Payment: payment_method_last4, payment_method_brand
    - Timestamps: created_at, updated_at
    """
    id: str
    organization_id: Optional[str]
    stripe_customer_id: Optional[str]
    stripe_subscription_id: Optional[str]
    subscription_status: str  # "active", "inactive", "trialing", "past_due", "canceled", or "paused"
    price_id: Optional[str]
    current_period_start: Optional[str]
    current_period_end: Optional[str]
    cancel_at_period_end: Optional[bool]
    payment_method_last4: Optional[str]
    payment_method_brand: Optional[str]
    created_at: str
    updated_at: str


class TestMatrixViewsRow(TypedDict, total=False):
    """Database row for test_matrix_views table.

    Actual columns from DB:
    - Core: id, name, project_id, configuration (jsonb)
    - Status: is_active, is_default
    - Ownership: created_by, updated_by
    - Timestamps: created_at, updated_at
    """
    id: str
    name: str
    project_id: str
    configuration: dict
    is_active: Optional[bool]
    is_default: Optional[bool]
    created_by: str
    updated_by: str
    created_at: str
    updated_at: str


class MCPSessionsRow(TypedDict, total=False):
    """Database row for mcp_sessions table.

    Actual columns from DB:
    - Core: session_id, user_id
    - Data: oauth_data (jsonb), mcp_state (jsonb)
    - Timestamps: created_at, updated_at, expires_at
    """
    session_id: str
    user_id: str
    oauth_data: dict
    mcp_state: Optional[dict]
    created_at: str
    updated_at: str
    expires_at: str


class OAuthClientsRow(TypedDict, total=False):
    """Database row for oauth_clients table.

    Actual columns from DB:
    - Core: id, client_id, client_name, client_secret
    - Configuration: redirect_uris (jsonb), grant_types (jsonb), response_types (jsonb), scope
    - Status: is_public
    - Timestamps: created_at, updated_at
    """
    id: str
    client_id: str
    client_name: str
    client_secret: Optional[str]
    redirect_uris: dict
    grant_types: dict
    response_types: dict
    scope: Optional[str]
    is_public: Optional[bool]
    created_at: str
    updated_at: str


class OAuthAuthorizationCodesRow(TypedDict, total=False):
    """Database row for oauth_authorization_codes table.

    Actual columns from DB:
    - Core: id, code, client_id, user_id, redirect_uri
    - PKCE: code_challenge, code_challenge_method
    - Authorization: scope, state
    - Timestamps: created_at, expires_at
    """
    id: str
    code: str
    client_id: str
    user_id: Optional[str]
    redirect_uri: str
    code_challenge: str
    code_challenge_method: str
    scope: Optional[str]
    state: Optional[str]
    created_at: str
    expires_at: str


class OAuthAccessTokensRow(TypedDict, total=False):
    """Database row for oauth_access_tokens table.

    Actual columns from DB:
    - Core: id, token_hash, client_id, user_id, scope
    - Timestamps: created_at, expires_at, last_used_at
    """
    id: str
    token_hash: str
    client_id: str
    user_id: Optional[str]
    scope: Optional[str]
    created_at: str
    expires_at: str
    last_used_at: Optional[str]


class OAuthRefreshTokensRow(TypedDict, total=False):
    """Database row for oauth_refresh_tokens table.

    Actual columns from DB:
    - Core: id, token, client_id, user_id, scope
    - Timestamps: created_at, expires_at, last_used_at
    """
    id: str
    token: str
    client_id: str
    user_id: str
    scope: Optional[str]
    created_at: str
    expires_at: str
    last_used_at: Optional[str]


class RAGEmbeddingsRow(TypedDict, total=False):
    """Database row for rag_embeddings table.

    Actual columns from DB:
    - Core: id, entity_id, entity_type
    - Vector: embedding
    - Quality: content_hash, quality_score
    - Metadata: metadata (jsonb)
    - Timestamps: created_at
    """
    id: str
    entity_id: str
    entity_type: str
    embedding: list
    content_hash: Optional[str]
    quality_score: Optional[float]
    metadata: Optional[dict]
    created_at: str


class RAGSearchAnalyticsRow(TypedDict, total=False):
    """Database row for rag_search_analytics table.

    Actual columns from DB:
    - Core: id, user_id, organization_id
    - Query: query_text, query_hash, search_type
    - Performance: execution_time_ms, result_count, cache_hit
    - Timestamps: created_at
    """
    id: str
    user_id: Optional[str]
    organization_id: Optional[str]
    query_text: str
    query_hash: str
    search_type: str
    execution_time_ms: int
    result_count: int
    cache_hit: bool
    created_at: str


class EmbeddingCacheRow(TypedDict, total=False):
    """Database row for embedding_cache table.

    Actual columns from DB:
    - Core: id, cache_key, embedding
    - Stats: tokens_used, model, access_count
    - Timestamps: created_at, accessed_at
    """
    id: str
    cache_key: str
    embedding: Optional[list]
    tokens_used: int
    model: str
    access_count: Optional[int]
    created_at: str
    accessed_at: str
