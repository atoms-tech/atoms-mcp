"""
Constants for table names, field names, and configuration.
"""

from typing import Set


class Tables:
    """Database table names - All 39 tables."""

    # Core entities (8)
    ORGANIZATIONS = "organizations"
    PROJECTS = "projects"
    DOCUMENTS = "documents"
    REQUIREMENTS = "requirements"
    TEST_REQ = "test_req"
    PROFILES = "profiles"
    BLOCKS = "blocks"
    PROPERTIES = "properties"

    # Structure tables (3)
    COLUMNS = "columns"
    TABLE_ROWS = "table_rows"
    REQUIREMENTS_CLOSURE = "requirements_closure"

    # Membership tables (4)
    ORGANIZATION_MEMBERS = "organization_members"
    PROJECT_MEMBERS = "project_members"
    ORGANIZATION_INVITATIONS = "organization_invitations"
    PROJECT_INVITATIONS = "project_invitations"

    # Tests and traceability (3)
    REQUIREMENT_TESTS = "requirement_tests"
    TRACE_LINKS = "trace_links"
    ASSIGNMENTS = "assignments"

    # Diagrams (4)
    EXCALIDRAW_DIAGRAMS = "excalidraw_diagrams"
    REACT_FLOW_DIAGRAMS = "react_flow_diagrams"
    DIAGRAM_ELEMENT_LINKS = "diagram_element_links"
    EXCALIDRAW_ELEMENT_LINKS = "excalidraw_element_links"

    # OAuth tables (5)
    MCP_SESSIONS = "mcp_sessions"
    OAUTH_CLIENTS = "oauth_clients"
    OAUTH_AUTHORIZATION_CODES = "oauth_authorization_codes"
    OAUTH_ACCESS_TOKENS = "oauth_access_tokens"
    OAUTH_REFRESH_TOKENS = "oauth_refresh_tokens"

    # Billing tables (3)
    BILLING_CACHE = "billing_cache"
    STRIPE_CUSTOMERS = "stripe_customers"
    USAGE_LOGS = "usage_logs"

    # System tables (5)
    AUDIT_LOGS = "audit_logs"
    NOTIFICATIONS = "notifications"
    EXTERNAL_DOCUMENTS = "external_documents"
    TEST_MATRIX_VIEWS = "test_matrix_views"
    USER_ROLES = "user_roles"

    # Embeddings/RAG tables (3)
    RAG_EMBEDDINGS = "rag_embeddings"
    RAG_SEARCH_ANALYTICS = "rag_search_analytics"
    EMBEDDING_CACHE = "embedding_cache"


class Fields:
    """Common database field names."""
    # Primary keys
    ID = "id"

    # Timestamps
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    DELETED_AT = "deleted_at"
    EXPIRES_AT = "expires_at"

    # User tracking
    CREATED_BY = "created_by"
    UPDATED_BY = "updated_by"
    DELETED_BY = "deleted_by"
    OWNED_BY = "owned_by"
    INVITED_BY = "invited_by"

    # Soft delete
    IS_DELETED = "is_deleted"
    IS_ACTIVE = "is_active"

    # Common fields
    NAME = "name"
    TITLE = "title"
    SLUG = "slug"
    DESCRIPTION = "description"
    STATUS = "status"
    PRIORITY = "priority"
    TYPE = "type"
    EMAIL = "email"
    CONTENT = "content"

    # Foreign keys - Core entities
    ORGANIZATION_ID = "organization_id"
    PROJECT_ID = "project_id"
    DOCUMENT_ID = "document_id"
    REQUIREMENT_ID = "requirement_id"
    TEST_ID = "test_id"
    USER_ID = "user_id"
    BLOCK_ID = "block_id"
    OWNER_ID = "owner_id"

    # Foreign keys - Relationships
    ANCESTOR_ID = "ancestor_id"
    DESCENDANT_ID = "descendant_id"
    PARENT_ID = "parent_id"
    DEPTH = "depth"

    # Metadata and configuration
    METADATA = "metadata"
    PROPERTIES = "properties"
    SETTINGS = "settings"
    PREFERENCES = "preferences"

    # Billing fields
    BILLING_PLAN = "billing_plan"
    BILLING_CYCLE = "billing_cycle"
    MAX_MEMBERS = "max_members"
    MAX_MONTHLY_REQUESTS = "max_monthly_requests"
    MEMBER_COUNT = "member_count"
    STORAGE_USED = "storage_used"

    # Visual/display fields
    LOGO_URL = "logo_url"
    AVATAR_URL = "avatar_url"
    FULL_NAME = "full_name"

    # Vector search
    EMBEDDING = "embedding"
    QUERY = "query"
    RESULT = "result"

    # External references
    EXTERNAL_ID = "external_id"

    # Version control
    VERSION = "version"

    # Role and permissions
    ROLE = "role"

    # Test-specific fields
    TEST_TYPE = "test_type"
    METHOD = "method"
    EXPECTED_RESULTS = "expected_results"
    PRECONDITIONS = "preconditions"
    TEST_STEPS = "test_steps"
    ESTIMATED_DURATION = "estimated_duration"
    CATEGORY = "category"
    TEST_ENVIRONMENT = "test_environment"

    # Document-specific
    DOC_TYPE = "doc_type"

    # Requirement-specific
    REQUIREMENT_TYPE = "requirement_type"
    FORMAT = "format"
    LEVEL = "level"
    POSITION = "position"

    # Relationship-specific
    RELATIONSHIP_TYPE = "relationship_type"
    COVERAGE_LEVEL = "coverage_level"

    # OAuth-specific
    CLIENT_ID = "client_id"
    CLIENT_SECRET = "client_secret"
    REDIRECT_URI = "redirect_uri"
    GRANT_TYPE = "grant_type"
    CODE = "code"
    TOKEN = "token"
    ACCESS_TOKEN = "access_token"
    REFRESH_TOKEN = "refresh_token"
    SCOPE = "scope"

    # Diagram-specific
    DIAGRAM_ID = "diagram_id"
    ELEMENT_ID = "element_id"
    DIAGRAM_TYPE = "diagram_type"

    # Order/sequence
    ORDER = "order"

    # Key-value
    KEY = "key"
    VALUE = "value"

    # Entity type for generic tables
    ENTITY_TYPE = "entity_type"
    ENTITY_ID = "entity_id"


# Tables that don't have soft delete functionality (is_deleted column)
TABLES_WITHOUT_SOFT_DELETE: Set[str] = {
    # Core tables without soft delete
    Tables.TEST_REQ,  # Has is_active instead
    Tables.PROFILES,

    # Structure tables
    Tables.PROPERTIES,
    Tables.COLUMNS,
    Tables.TABLE_ROWS,
    Tables.REQUIREMENTS_CLOSURE,

    # Membership tables
    Tables.ORGANIZATION_MEMBERS,
    Tables.PROJECT_MEMBERS,
    Tables.ORGANIZATION_INVITATIONS,
    Tables.PROJECT_INVITATIONS,

    # OAuth tables (session-based, expire instead)
    Tables.MCP_SESSIONS,
    Tables.OAUTH_CLIENTS,
    Tables.OAUTH_AUTHORIZATION_CODES,
    Tables.OAUTH_ACCESS_TOKENS,
    Tables.OAUTH_REFRESH_TOKENS,

    # Billing tables (cache/log based)
    Tables.BILLING_CACHE,
    Tables.STRIPE_CUSTOMERS,
    Tables.USAGE_LOGS,

    # System tables
    Tables.USER_ROLES,
    Tables.TEST_MATRIX_VIEWS,

    # RAG/Embeddings tables (cache-based)
    Tables.RAG_EMBEDDINGS,
    Tables.RAG_SEARCH_ANALYTICS,
    Tables.EMBEDDING_CACHE,

    # Diagrams element links
    Tables.DIAGRAM_ELEMENT_LINKS,
    Tables.EXCALIDRAW_ELEMENT_LINKS,
}


# Tables that don't have created_by/updated_by columns
TABLES_WITHOUT_AUDIT_FIELDS: Set[str] = {
    Tables.PROFILES,
    Tables.PROPERTIES,
}


# Entity type to table name mapping (for tools and operations)
ENTITY_TABLE_MAP = {
    # Core entities
    "organization": Tables.ORGANIZATIONS,
    "project": Tables.PROJECTS,
    "document": Tables.DOCUMENTS,
    "requirement": Tables.REQUIREMENTS,
    "test": Tables.TEST_REQ,
    "profile": Tables.PROFILES,
    "user": Tables.PROFILES,  # Alias for profile
    "block": Tables.BLOCKS,
    "property": Tables.PROPERTIES,

    # Structure
    "column": Tables.COLUMNS,
    "table_row": Tables.TABLE_ROWS,
    "requirements_closure": Tables.REQUIREMENTS_CLOSURE,

    # Membership
    "organization_member": Tables.ORGANIZATION_MEMBERS,
    "project_member": Tables.PROJECT_MEMBERS,
    "organization_invitation": Tables.ORGANIZATION_INVITATIONS,
    "project_invitation": Tables.PROJECT_INVITATIONS,

    # Tests and traceability
    "requirement_test": Tables.REQUIREMENT_TESTS,
    "trace_link": Tables.TRACE_LINKS,
    "assignment": Tables.ASSIGNMENTS,

    # Diagrams
    "excalidraw_diagram": Tables.EXCALIDRAW_DIAGRAMS,
    "react_flow_diagram": Tables.REACT_FLOW_DIAGRAMS,
    "diagram_element_link": Tables.DIAGRAM_ELEMENT_LINKS,
    "excalidraw_element_link": Tables.EXCALIDRAW_ELEMENT_LINKS,

    # OAuth
    "mcp_session": Tables.MCP_SESSIONS,
    "oauth_client": Tables.OAUTH_CLIENTS,
    "oauth_authorization_code": Tables.OAUTH_AUTHORIZATION_CODES,
    "oauth_access_token": Tables.OAUTH_ACCESS_TOKENS,
    "oauth_refresh_token": Tables.OAUTH_REFRESH_TOKENS,

    # Billing
    "billing_cache": Tables.BILLING_CACHE,
    "stripe_customer": Tables.STRIPE_CUSTOMERS,
    "usage_log": Tables.USAGE_LOGS,

    # System
    "audit_log": Tables.AUDIT_LOGS,
    "notification": Tables.NOTIFICATIONS,
    "external_document": Tables.EXTERNAL_DOCUMENTS,
    "test_matrix_view": Tables.TEST_MATRIX_VIEWS,
    "user_role": Tables.USER_ROLES,

    # RAG/Embeddings
    "rag_embedding": Tables.RAG_EMBEDDINGS,
    "rag_search_analytics": Tables.RAG_SEARCH_ANALYTICS,
    "embedding_cache": Tables.EMBEDDING_CACHE,
}


# Required fields by entity type
REQUIRED_FIELDS = {
    "organization": {Fields.NAME, Fields.SLUG, Fields.TYPE},
    "project": {Fields.NAME, Fields.ORGANIZATION_ID},
    "document": {Fields.NAME, Fields.PROJECT_ID},
    "requirement": {Fields.NAME, Fields.DESCRIPTION, Fields.DOCUMENT_ID},
    "test": {Fields.TITLE, Fields.PROJECT_ID},
    "profile": {Fields.EMAIL},
}


# Auto-generated fields (set by database)
AUTO_FIELDS = {
    Fields.ID,
    Fields.CREATED_AT,
    Fields.UPDATED_AT,
    Fields.DELETED_AT,
    Fields.CREATED_BY,
    Fields.UPDATED_BY,
    Fields.DELETED_BY,
}
