"""
Enums for Atoms MCP

Enumeration types for the Atoms workspace management system.
"""

from enum import Enum


class EntityStatus(str, Enum):
    """Entity status enumeration."""
    
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    DELETED = "deleted"
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class RAGMode(str, Enum):
    """RAG (Retrieval-Augmented Generation) mode enumeration."""
    
    DISABLED = "disabled"
    ENABLED = "enabled"
    AUTO = "auto"
    MANUAL = "manual"


class RequirementPriority(str, Enum):
    """Requirement priority enumeration."""
    
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    URGENT = "urgent"


class TestStatus(str, Enum):
    """Test status enumeration."""
    
    DRAFT = "draft"
    READY = "ready"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    PENDING = "pending"
    CANCELLED = "cancelled"