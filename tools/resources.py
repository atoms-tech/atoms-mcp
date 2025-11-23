"""MCP Resources for Atoms - Reference documentation and schemas.

Provides 6 essential resources to help agents understand the Atoms MCP.
"""

import json
import logging

logger = logging.getLogger(__name__)


def get_entity_types_reference() -> dict:
    """Reference for all entity types."""
    
    return {
        "entity_types": [
            {
                "name": "project",
                "description": "Project container for organizing work",
                "fields": ["id", "name", "organization_id", "description", "status"],
                "operations": ["create", "read", "update", "delete", "list", "search"]
            },
            {
                "name": "requirement",
                "description": "Requirement within a document",
                "fields": ["id", "name", "project_id", "document_id", "description", "status", "priority"],
                "operations": ["create", "read", "update", "delete", "list", "search"]
            },
            {
                "name": "test",
                "description": "Test case for requirements",
                "fields": ["id", "name", "project_id", "description", "status", "test_type"],
                "operations": ["create", "read", "update", "delete", "list", "search"]
            },
            {
                "name": "document",
                "description": "Document containing requirements",
                "fields": ["id", "name", "project_id", "description", "content", "status"],
                "operations": ["create", "read", "update", "delete", "list", "search"]
            }
        ]
    }


def get_operation_reference() -> dict:
    """Reference for all operations."""
    
    return {
        "operations": {
            "create": {
                "description": "Create a new entity",
                "required_params": ["entity_type", "data"],
                "optional_params": ["workspace_id", "project_id", "document_id"],
                "example": '{"operation": "create", "entity_type": "project", "data": {"name": "My Project"}}'
            },
            "read": {
                "description": "Read entity by ID",
                "required_params": ["entity_type", "entity_id"],
                "optional_params": ["include_relations"],
                "example": '{"operation": "read", "entity_type": "project", "entity_id": "proj-1"}'
            },
            "update": {
                "description": "Update entity",
                "required_params": ["entity_type", "entity_id", "data"],
                "optional_params": [],
                "example": '{"operation": "update", "entity_type": "project", "entity_id": "proj-1", "data": {"name": "Updated"}}'
            },
            "delete": {
                "description": "Delete entity",
                "required_params": ["entity_type", "entity_id"],
                "optional_params": ["soft_delete"],
                "example": '{"operation": "delete", "entity_type": "project", "entity_id": "proj-1"}'
            },
            "list": {
                "description": "List entities",
                "required_params": ["entity_type"],
                "optional_params": ["limit", "offset", "filters"],
                "example": '{"operation": "list", "entity_type": "project", "limit": 20}'
            },
            "search": {
                "description": "Search entities by text",
                "required_params": ["entity_type", "search_term"],
                "optional_params": ["filters", "limit"],
                "example": '{"operation": "search", "entity_type": "requirement", "search_term": "security"}'
            }
        }
    }


def get_workflow_templates() -> dict:
    """Pre-built workflow templates."""
    
    return {
        "templates": [
            {
                "name": "setup_project",
                "description": "Create project with initial structure",
                "parameters": ["name", "description", "organization_id"],
                "steps": ["Create project", "Create default document", "Set permissions"]
            },
            {
                "name": "import_requirements",
                "description": "Import requirements from external source",
                "parameters": ["project_id", "source", "data"],
                "steps": ["Validate data", "Create requirements", "Link to document"]
            },
            {
                "name": "bulk_status_update",
                "description": "Update status for multiple entities",
                "parameters": ["entity_type", "entity_ids", "new_status"],
                "steps": ["Validate entities", "Update status", "Record history"]
            },
            {
                "name": "setup_test_matrix",
                "description": "Create test matrix for requirements",
                "parameters": ["project_id", "requirement_ids"],
                "steps": ["Create tests", "Link to requirements", "Set test types"]
            },
            {
                "name": "organization_onboarding",
                "description": "Onboard new organization",
                "parameters": ["organization_name", "admin_email"],
                "steps": ["Create organization", "Create workspace", "Invite admin"]
            }
        ]
    }


def get_schema_definitions() -> dict:
    """JSON schemas for entities."""
    
    return {
        "project": {
            "type": "object",
            "title": "Project",
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string", "minLength": 1},
                "organization_id": {"type": "string"},
                "description": {"type": "string"},
                "status": {"type": "string", "enum": ["active", "archived"]}
            },
            "required": ["id", "name", "organization_id"]
        },
        "requirement": {
            "type": "object",
            "title": "Requirement",
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string", "minLength": 1},
                "project_id": {"type": "string"},
                "document_id": {"type": "string"},
                "description": {"type": "string"},
                "status": {"type": "string", "enum": ["draft", "active", "completed"]},
                "priority": {"type": "string", "enum": ["low", "medium", "high", "critical"]}
            },
            "required": ["id", "name", "project_id"]
        }
    }


def get_best_practices() -> str:
    """Agent best practices guide."""
    
    return """# Best Practices for Atoms MCP

## Context Management
1. Set workspace context at session start
2. Set project context for project-specific work
3. Use context to reduce parameter spam
4. Clear context when switching workspaces

## Entity Operations
1. Always validate IDs before using
2. Use batch operations for 3+ entities
3. Include all required fields
4. Use meaningful names

## Search Operations
1. Use semantic search for complex queries
2. Use keyword search for exact matches
3. Use hybrid for best coverage
4. Filter by status/priority when possible

## Error Handling
1. Check context before operations
2. Validate IDs before using them
3. Include all required fields
4. Use error suggestions for debugging

## Performance
1. Use pagination for large result sets
2. Filter early to reduce result size
3. Use batch operations for bulk changes
4. Cache frequently accessed entities
"""


def get_api_reference() -> str:
    """Complete API reference."""
    
    return """# Atoms MCP API Reference

## Tools
- **context_tool**: Manage session context
- **entity_tool**: CRUD operations and search
- **relationship_tool**: Entity relationships
- **workflow_tool**: Complex workflows
- **query_tool**: Data exploration (deprecated, use entity_tool)

## Operations
- create, read, update, delete
- list, search, batch_create
- rag_search, aggregate, analyze
- similarity

## Context Types
- workspace, project, organization
- entity_type, document, parent_id

## Relationship Types
- member, assignment, trace_link
- requirement_test, invitation

## Response Format
```json
{
  "success": true/false,
  "data": {...},
  "error": "error message if failed",
  "metrics": {"total_ms": 145}
}
```

## Error Handling
- 400: Validation error
- 401: Authentication error
- 403: Authorization error
- 404: Not found error
- 500: Server error

## Rate Limiting
- 100 requests per minute per user
- 1000 requests per hour per workspace

## Authentication
- Bearer token in Authorization header
- Token must be valid and not expired

## Pagination
- limit: Page size (default: 20, max: 100)
- offset: Starting position (default: 0)

## Filtering
- filters: Dictionary of field:value pairs
- Supports nested filtering

## Sorting
- order_by: Field name with optional direction
- Example: "name" or "created_at:desc"

## Batch Operations
- batch_create: Create multiple entities
- bulk_update: Update multiple entities
- bulk_delete: Delete multiple entities

## Performance Tips
1. Use pagination for large result sets
2. Filter early to reduce result size
3. Use batch operations for bulk changes
4. Cache frequently accessed entities
5. Use semantic search for complex queries
"""

