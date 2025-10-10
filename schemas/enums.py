"""
Application-level enums for Atoms MCP.

These are NOT database enums - they are used by the MCP tools for operations.
For database enums, use the generated schemas from schemas.generated.fastapi.schema_public_latest
"""

from enum import Enum


class QueryType(str, Enum):
    """Data query operation types (application-level)."""
    SEARCH = "search"
    AGGREGATE = "aggregate"
    ANALYZE = "analyze"
    RELATIONSHIPS = "relationships"
    RAG_SEARCH = "rag_search"
    SIMILARITY = "similarity"


class RAGMode(str, Enum):
    """RAG search modes (application-level)."""
    AUTO = "auto"
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    HYBRID = "hybrid"


class RelationshipType(str, Enum):
    """Types of relationships between entities (application-level)."""
    MEMBER = "member"
    ASSIGNMENT = "assignment"
    TRACE_LINK = "trace_link"
    REQUIREMENT_TEST = "requirement_test"
    INVITATION = "invitation"


class EntityStatus(str, Enum):
    """Entity status values (application-level)."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    DELETED = "deleted"
    DRAFT = "draft"
    PENDING = "pending"
    COMPLETED = "completed"


class EntityType(str, Enum):
    """Entity types (application-level)."""
    WORKSPACE = "workspace"
    ORGANIZATION = "organization"
    PROJECT = "project"
    REQUIREMENT = "requirement"
    TEST = "test"
    DOCUMENT = "document"
    USER = "user"


class OrganizationType(str, Enum):
    """Organization types (application-level)."""
    PERSONAL = "personal"
    TEAM = "team"
    ENTERPRISE = "enterprise"
    BUSINESS = "business"


class Priority(str, Enum):
    """Priority levels (application-level)."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
