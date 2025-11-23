# Deep Dive: Resources Implementation

## Overview

MCP Resources expose data that agents can read. They're like built-in documentation, schemas, and reference materials.

## Resource 1: Entity Types Reference

### Purpose
Provide complete reference for all 20 entity types with fields and operations.

### Implementation
```python
@mcp.resource("file:///reference/entity_types.json")
def get_entity_types_reference():
    """Reference for all entity types with fields and operations."""
    
    return {
        "entity_types": [
            {
                "name": "organization",
                "description": "Top-level organization container",
                "table": "organizations",
                "fields": {
                    "id": {"type": "string", "required": True},
                    "name": {"type": "string", "required": True},
                    "slug": {"type": "string", "required": True},
                    "type": {"type": "string", "enum": ["team", "enterprise"]},
                    "description": {"type": "string"},
                    "created_at": {"type": "timestamp"},
                    "updated_at": {"type": "timestamp"}
                },
                "operations": ["create", "read", "update", "delete", "list", "search"],
                "relationships": ["member", "project", "invitation"]
            },
            {
                "name": "project",
                "description": "Project container within organization",
                "table": "projects",
                "fields": {
                    "id": {"type": "string", "required": True},
                    "name": {"type": "string", "required": True},
                    "organization_id": {"type": "string", "required": True},
                    "description": {"type": "string"},
                    "status": {"type": "string", "enum": ["active", "archived"]},
                    "created_at": {"type": "timestamp"},
                    "updated_at": {"type": "timestamp"}
                },
                "operations": ["create", "read", "update", "delete", "list", "search"],
                "relationships": ["member", "document", "requirement"]
            },
            {
                "name": "document",
                "description": "Document within project",
                "table": "documents",
                "fields": {
                    "id": {"type": "string", "required": True},
                    "name": {"type": "string", "required": True},
                    "project_id": {"type": "string", "required": True},
                    "description": {"type": "string"},
                    "status": {"type": "string", "enum": ["draft", "published", "archived"]},
                    "created_at": {"type": "timestamp"},
                    "updated_at": {"type": "timestamp"}
                },
                "operations": ["create", "read", "update", "delete", "list", "search"],
                "relationships": ["requirement", "block"]
            },
            {
                "name": "requirement",
                "description": "Requirement within document",
                "table": "requirements",
                "fields": {
                    "id": {"type": "string", "required": True},
                    "name": {"type": "string", "required": True},
                    "document_id": {"type": "string", "required": True},
                    "description": {"type": "string"},
                    "status": {"type": "string", "enum": ["draft", "active", "completed"]},
                    "priority": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                    "created_at": {"type": "timestamp"},
                    "updated_at": {"type": "timestamp"}
                },
                "operations": ["create", "read", "update", "delete", "list", "search"],
                "relationships": ["test", "trace_link", "property"]
            },
            {
                "name": "test",
                "description": "Test case for requirement",
                "table": "test_req",
                "fields": {
                    "id": {"type": "string", "required": True},
                    "name": {"type": "string", "required": True},
                    "project_id": {"type": "string", "required": True},
                    "description": {"type": "string"},
                    "status": {"type": "string", "enum": ["draft", "active", "completed"]},
                    "created_at": {"type": "timestamp"},
                    "updated_at": {"type": "timestamp"}
                },
                "operations": ["create", "read", "update", "delete", "list", "search"],
                "relationships": ["requirement"]
            },
            # ... 15 more entity types (property, block, column, trace_link, assignment, 
            # audit_log, notification, external_document, test_matrix_view, 
            # organization_member, project_member, organization_invitation, 
            # requirement_test, profile, user)
        ],
        "summary": {
            "total_entity_types": 20,
            "total_operations": 8,
            "total_relationships": 12
        }
    }
```

## Resource 2: Operation Reference

### Purpose
Provide complete reference for all operations across all tools.

### Implementation
```python
@mcp.resource("file:///reference/operations.json")
def get_operation_reference():
    """Reference for all operations."""
    
    return {
        "operations": {
            "create": {
                "description": "Create a new entity",
                "tools": ["entity_tool"],
                "required_params": ["entity_type", "data"],
                "optional_params": ["workspace_id", "parent_id"],
                "returns": "Created entity with ID",
                "example": {
                    "operation": "create",
                    "entity_type": "project",
                    "data": {"name": "My Project"}
                }
            },
            "read": {
                "description": "Read entity by ID",
                "tools": ["entity_tool"],
                "required_params": ["entity_type", "entity_id"],
                "optional_params": ["include_relations", "format_type"],
                "returns": "Entity data",
                "example": {
                    "operation": "read",
                    "entity_type": "project",
                    "entity_id": "proj-1"
                }
            },
            "update": {
                "description": "Update entity",
                "tools": ["entity_tool"],
                "required_params": ["entity_type", "entity_id", "data"],
                "optional_params": ["workspace_id"],
                "returns": "Updated entity",
                "example": {
                    "operation": "update",
                    "entity_type": "project",
                    "entity_id": "proj-1",
                    "data": {"name": "Updated Name"}
                }
            },
            "delete": {
                "description": "Delete entity (soft delete by default)",
                "tools": ["entity_tool"],
                "required_params": ["entity_type", "entity_id"],
                "optional_params": ["soft_delete"],
                "returns": "Success status",
                "example": {
                    "operation": "delete",
                    "entity_type": "project",
                    "entity_id": "proj-1"
                }
            },
            "list": {
                "description": "List entities with optional filters",
                "tools": ["entity_tool"],
                "required_params": ["entity_type"],
                "optional_params": ["filters", "limit", "offset", "order_by"],
                "returns": "List of entities",
                "example": {
                    "operation": "list",
                    "entity_type": "project",
                    "limit": 10
                }
            },
            "search": {
                "description": "Search entities by text",
                "tools": ["entity_tool"],
                "required_params": ["entity_type", "search_term"],
                "optional_params": ["filters", "limit"],
                "returns": "List of matching entities",
                "example": {
                    "operation": "search",
                    "entity_type": "requirement",
                    "search_term": "security"
                }
            },
            "batch_create": {
                "description": "Create multiple entities",
                "tools": ["entity_tool"],
                "required_params": ["entity_type", "batch"],
                "optional_params": ["workspace_id"],
                "returns": "List of created entities",
                "example": {
                    "operation": "batch_create",
                    "entity_type": "requirement",
                    "batch": [{"name": "Req 1"}, {"name": "Req 2"}]
                }
            },
            "rag_search": {
                "description": "AI-powered semantic search",
                "tools": ["entity_tool"],
                "required_params": ["entity_type", "search_query"],
                "optional_params": ["rag_mode", "similarity_threshold", "filters"],
                "returns": "List of semantically similar entities",
                "example": {
                    "operation": "rag_search",
                    "entity_type": "requirement",
                    "search_query": "authentication requirements",
                    "rag_mode": "semantic"
                }
            },
            # ... more operations (archive, restore, bulk_update, etc.)
        },
        "summary": {
            "total_operations": 20,
            "crud_operations": 4,
            "search_operations": 3,
            "bulk_operations": 3,
            "workflow_operations": 10
        }
    }
```

## Resource 3: Workflow Templates

### Purpose
Provide pre-built workflow examples.

### Implementation
```python
@mcp.resource("file:///templates/workflows.json")
def get_workflow_templates():
    """Pre-built workflow templates."""
    
    return {
        "templates": [
            {
                "name": "setup_project",
                "description": "Create project with initial structure",
                "parameters": {
                    "name": {"type": "string", "required": True},
                    "description": {"type": "string", "required": False},
                    "organization_id": {"type": "string", "required": True}
                },
                "steps": [
                    "Create project entity",
                    "Create initial document",
                    "Setup project members",
                    "Create initial requirements"
                ],
                "example": {
                    "workflow": "setup_project",
                    "parameters": {
                        "name": "My Project",
                        "description": "Project description",
                        "organization_id": "org-1"
                    }
                }
            },
            {
                "name": "import_requirements",
                "description": "Import requirements from external source",
                "parameters": {
                    "project_id": {"type": "string", "required": True},
                    "source": {"type": "string", "enum": ["csv", "json", "excel"]},
                    "data": {"type": "array", "required": True}
                },
                "steps": [
                    "Validate import data",
                    "Create requirement entities",
                    "Link to project",
                    "Generate audit log"
                ],
                "example": {
                    "workflow": "import_requirements",
                    "parameters": {
                        "project_id": "proj-1",
                        "source": "csv",
                        "data": [
                            {"name": "Req 1", "description": "..."},
                            {"name": "Req 2", "description": "..."}
                        ]
                    }
                }
            },
            {
                "name": "bulk_status_update",
                "description": "Update status for multiple entities",
                "parameters": {
                    "entity_type": {"type": "string", "required": True},
                    "entity_ids": {"type": "array", "required": True},
                    "new_status": {"type": "string", "required": True}
                },
                "steps": [
                    "Validate entity IDs",
                    "Update status for each entity",
                    "Generate audit log",
                    "Send notifications"
                ],
                "example": {
                    "workflow": "bulk_status_update",
                    "parameters": {
                        "entity_type": "requirement",
                        "entity_ids": ["req-1", "req-2", "req-3"],
                        "new_status": "completed"
                    }
                }
            },
            {
                "name": "setup_test_matrix",
                "description": "Set up test matrix for project",
                "parameters": {
                    "project_id": {"type": "string", "required": True},
                    "test_types": {"type": "array", "required": True},
                    "environments": {"type": "array", "required": True}
                },
                "steps": [
                    "Create test matrix entity",
                    "Create test combinations",
                    "Link to project",
                    "Setup initial test cases"
                ],
                "example": {
                    "workflow": "setup_test_matrix",
                    "parameters": {
                        "project_id": "proj-1",
                        "test_types": ["unit", "integration", "e2e"],
                        "environments": ["dev", "staging", "prod"]
                    }
                }
            },
            {
                "name": "organization_onboarding",
                "description": "Complete organization setup",
                "parameters": {
                    "organization_name": {"type": "string", "required": True},
                    "admin_email": {"type": "string", "required": True},
                    "initial_projects": {"type": "array", "required": False}
                },
                "steps": [
                    "Create organization",
                    "Create admin user",
                    "Setup initial projects",
                    "Send welcome email",
                    "Generate audit log"
                ],
                "example": {
                    "workflow": "organization_onboarding",
                    "parameters": {
                        "organization_name": "Acme Corp",
                        "admin_email": "admin@acme.com",
                        "initial_projects": ["Project 1", "Project 2"]
                    }
                }
            }
        ],
        "summary": {
            "total_templates": 5,
            "setup_templates": 2,
            "import_templates": 1,
            "bulk_templates": 1,
            "onboarding_templates": 1
        }
    }
```

## Resource 4: Schema Definitions

### Purpose
Provide JSON schemas for all entity types.

### Implementation
```python
@mcp.resource("file:///schemas/project.json")
def get_project_schema():
    """Project entity schema."""
    
    return {
        "type": "object",
        "title": "Project",
        "description": "A project container within an organization",
        "properties": {
            "id": {
                "type": "string",
                "description": "Unique project ID"
            },
            "name": {
                "type": "string",
                "description": "Project name",
                "minLength": 1,
                "maxLength": 255
            },
            "organization_id": {
                "type": "string",
                "description": "Parent organization ID"
            },
            "description": {
                "type": "string",
                "description": "Project description",
                "maxLength": 1000
            },
            "status": {
                "type": "string",
                "enum": ["active", "archived"],
                "description": "Project status"
            },
            "created_at": {
                "type": "string",
                "format": "date-time",
                "description": "Creation timestamp"
            },
            "updated_at": {
                "type": "string",
                "format": "date-time",
                "description": "Last update timestamp"
            }
        },
        "required": ["id", "name", "organization_id"],
        "additionalProperties": False,
        "examples": [
            {
                "id": "proj-1",
                "name": "My Project",
                "organization_id": "org-1",
                "description": "Project description",
                "status": "active",
                "created_at": "2025-11-23T10:00:00Z",
                "updated_at": "2025-11-23T10:00:00Z"
            }
        ]
    }

@mcp.resource("file:///schemas/requirement.json")
def get_requirement_schema():
    """Requirement entity schema."""
    
    return {
        "type": "object",
        "title": "Requirement",
        "description": "A requirement within a document",
        "properties": {
            "id": {"type": "string"},
            "name": {"type": "string", "minLength": 1},
            "document_id": {"type": "string"},
            "description": {"type": "string"},
            "status": {
                "type": "string",
                "enum": ["draft", "active", "completed"]
            },
            "priority": {
                "type": "string",
                "enum": ["low", "medium", "high", "critical"]
            },
            "created_at": {"type": "string", "format": "date-time"},
            "updated_at": {"type": "string", "format": "date-time"}
        },
        "required": ["id", "name", "document_id"],
        "additionalProperties": False
    }

# ... More schemas for other entity types
```

## Resource 5: Best Practices Guide

### Purpose
Provide agent best practices guide.

### Implementation
```python
@mcp.resource("file:///guides/best_practices.md")
def get_best_practices():
    """Agent best practices guide."""
    
    return """# Best Practices for Atoms MCP

## Context Management

### 1. Set Workspace Context at Session Start
```python
context_tool(
    operation="set_context",
    context_type="workspace",
    entity_id="ws-1"
)
```
- Required for most operations
- Auto-injected into all operations
- Prevents permission errors

### 2. Set Project Context for Project-Specific Work
```python
context_tool(
    operation="set_context",
    context_type="project",
    entity_id="proj-1"
)
```
- Reduces parameter spam
- Auto-injected into operations
- Improves clarity

### 3. Use Context to Reduce Parameter Spam
- Fewer parameters needed
- Cleaner code
- Better readability

## Entity Operations

### 1. Always Validate IDs Before Using
```python
# Check entity exists
entity = entity_tool(operation="read", entity_type="project", entity_id="proj-1")
if entity["success"]:
    # Use entity
else:
    # Handle error
```

### 2. Use Batch Operations for 3+ Entities
```python
# GOOD: Batch create
entity_tool(operation="batch_create", entity_type="requirement", batch=[...])

# BAD: Individual creates
for item in items:
    entity_tool(operation="create", entity_type="requirement", data=item)
```

### 3. Include All Required Fields
- Check entity_types_reference for required fields
- Prevent "missing field" errors
- Improve data quality

### 4. Use Meaningful Names
- Clear, descriptive names
- Helps with searching later
- Improves readability

## Search Operations

### 1. Use Semantic Search for Complex Queries
- Better for natural language
- Finds related concepts
- More forgiving of phrasing

### 2. Use Keyword Search for Exact Matches
- Faster
- More precise
- Better for technical terms

### 3. Use Hybrid for Best Coverage
- Combines both approaches
- Adjust weights for your use case
- Default weights usually work well

### 4. Filter by Status/Priority When Possible
- Reduces noise
- Improves relevance
- Faster results

## Error Handling

### 1. Check Context Before Operations
```python
context = context_tool(operation="get_context")
assert context["workspace_id"] == expected_workspace
```

### 2. Validate IDs Before Using Them
```python
entities = entity_tool(operation="list", entity_type="project")
target = next((e for e in entities if e["id"] == "proj-1"), None)
if not target:
    raise ValueError("Project not found")
```

### 3. Include All Required Fields
- Check entity_types_reference
- Prevent "missing field" errors
- Improve data quality

### 4. Use Error Suggestions for Debugging
- Suggestions provided in error responses
- Helps identify issues
- Speeds up debugging

## Performance Tips

### 1. Use Pagination for Large Result Sets
```python
entity_tool(
    operation="list",
    entity_type="requirement",
    limit=50,
    offset=0
)
```

### 2. Use Filters to Reduce Result Size
```python
entity_tool(
    operation="search",
    entity_type="requirement",
    search_term="security",
    filters={"status": "active"}
)
```

### 3. Use Batch Operations for Multiple Changes
- More efficient
- Better performance
- Atomic operation

### 4. Cache Results When Possible
- Reduce API calls
- Improve performance
- Better UX

## Workflow Best Practices

### 1. Use Workflows for Multi-Step Operations
- Atomic operations
- Better error handling
- Consistent results

### 2. Enable Transaction Mode for Safety
- All-or-nothing execution
- Rollback on error
- Data consistency

### 3. Check Parameters Before Executing
- Validate inputs
- Prevent errors
- Better UX

### 4. Handle Errors Gracefully
- Check response status
- Log errors
- Provide feedback

## Relationship Best Practices

### 1. Always Specify Source and Target Types
- Prevents ambiguity
- Enables validation
- Improves performance

### 2. Check Before Linking to Avoid Duplicates
```python
exists = relationship_tool(
    operation="check",
    relationship_type="requirement_test",
    source={"type": "requirement", "id": "req-1"},
    target={"type": "test", "id": "test-1"}
)
if not exists:
    relationship_tool(operation="link", ...)
```

### 3. Use Batch Operations for Multiple Links
- More efficient
- Better performance
- Atomic operation

## Summary

- ✅ Set context at session start
- ✅ Validate IDs before using
- ✅ Use batch operations for multiple items
- ✅ Include all required fields
- ✅ Use semantic search for complex queries
- ✅ Filter results to reduce noise
- ✅ Check before linking to avoid duplicates
- ✅ Handle errors gracefully
- ✅ Use pagination for large result sets
- ✅ Cache results when possible
"""
```

## Resource 6: API Reference

### Purpose
Provide complete API documentation.

### Implementation
```python
@mcp.resource("file:///reference/api.md")
def get_api_reference():
    """Complete API reference."""
    
    return """# Atoms MCP API Reference

## Tools

### context_tool
Manage session context (workspace, project, document, entity_type, parent_id)

**Operations**:
- set_context: Set any context value
- get_context: Get all current context values
- clear_context: Clear all context

### entity_tool
CRUD operations for all entity types

**Operations**:
- create: Create new entity
- read: Read entity by ID
- update: Update entity
- delete: Delete entity
- list: List entities with filters
- search: Search entities by text
- batch_create: Create multiple entities
- rag_search: AI-powered semantic search
- aggregate: Summary statistics
- analyze: Deep analysis

### relationship_tool
Manage entity relationships

**Operations**:
- link: Create relationship
- unlink: Remove relationship
- list: List relationships
- check: Check if relationship exists
- update: Update relationship

### workflow_tool
Execute complex workflows

**Workflows**:
- setup_project: Create project with structure
- import_requirements: Import from external source
- bulk_status_update: Update multiple entities
- setup_test_matrix: Setup test matrix
- organization_onboarding: Complete org setup

### query_tool
Data exploration and analysis

**Query Types**:
- search: Cross-entity text search
- semantic_search: Semantic search
- keyword_search: Keyword search
- hybrid_search: Hybrid search
- aggregate: Summary statistics
- analyze: Deep analysis
- rag_search: AI-powered search
- similarity: Find similar content

## Entity Types

- organization, project, document
- requirement, test, property
- block, column, trace_link
- assignment, audit_log, notification
- external_document, test_matrix_view
- organization_member, project_member
- organization_invitation, requirement_test
- profile, user

## Context Types

- workspace: Current workspace
- project: Current project
- document: Current document
- entity_type: Current entity type focus
- parent_id: Current parent entity

## Relationship Types

- member: User membership
- assignment: Entity assignment
- trace_link: Related entities
- requirement_test: Requirement to test
- invitation: Organization invitation

## Response Format

All responses follow this format:

```json
{
  "success": true/false,
  "data": {...},
  "error": "error message if failed",
  "metrics": {
    "total_ms": 145,
    "db_query_ms": 120
  }
}
```

## Error Handling

Common error codes:
- 400: Bad request (invalid parameters)
- 401: Unauthorized (auth required)
- 403: Forbidden (permission denied)
- 404: Not found (entity not found)
- 500: Server error

## Rate Limiting

- 120 requests per minute (default)
- Rate limit headers in response
- Backoff recommended on 429 responses

## Authentication

- OAuth 2.0 via AuthKit
- Bearer token in Authorization header
- Scopes: openid, profile, email

## Pagination

- limit: Number of results (default 10, max 100)
- offset: Starting position (default 0)
- Returns: total_count, items

## Filtering

Filters use MongoDB-style syntax:

```python
filters = {
    "status": "active",
    "priority": {"$in": ["high", "critical"]},
    "created_at": {"$gte": "2025-01-01"}
}
```

## Sorting

Sort by field name:

```python
sort_list = [
    {"field": "name", "direction": "asc"},
    {"field": "created_at", "direction": "desc"}
]
```

## Batch Operations

Batch operations are atomic (all-or-nothing):

```python
entity_tool(
    operation="batch_create",
    entity_type="requirement",
    batch=[...],
    transaction_mode=True
)
```

## Webhooks

Subscribe to entity changes:

```python
context_tool(
    operation="subscribe",
    entity_type="requirement",
    events=["created", "updated", "deleted"]
)
```

## Performance Tips

- Use pagination for large result sets
- Use filters to reduce result size
- Use batch operations for multiple changes
- Cache results when possible
- Use semantic search for complex queries

## Support

- Documentation: See prompts and resources
- Examples: See workflow_templates resource
- Schemas: See schema_definitions resource
- Best practices: See best_practices resource
"""
```

## Integration with server.py

```python
# In server.py, after creating FastMCP instance:

from tools.resources import (
    get_entity_types_reference,
    get_operation_reference,
    get_workflow_templates,
    get_project_schema,
    get_requirement_schema,
    get_best_practices,
    get_api_reference
)

# Register resources
mcp.resource("file:///reference/entity_types.json")(get_entity_types_reference)
mcp.resource("file:///reference/operations.json")(get_operation_reference)
mcp.resource("file:///templates/workflows.json")(get_workflow_templates)
mcp.resource("file:///schemas/project.json")(get_project_schema)
mcp.resource("file:///schemas/requirement.json")(get_requirement_schema)
mcp.resource("file:///guides/best_practices.md")(get_best_practices)
mcp.resource("file:///reference/api.md")(get_api_reference)
```

## Testing Resources

```python
def test_resources():
    # Test entity types reference
    ref = get_entity_types_reference()
    assert "entity_types" in ref
    assert len(ref["entity_types"]) == 20
    
    # Test operation reference
    ops = get_operation_reference()
    assert "operations" in ops
    assert "create" in ops["operations"]
    
    # Test workflow templates
    templates = get_workflow_templates()
    assert "templates" in templates
    assert len(templates["templates"]) == 5
    
    # Test schemas
    project_schema = get_project_schema()
    assert project_schema["type"] == "object"
    assert "name" in project_schema["properties"]
    
    # Test best practices
    practices = get_best_practices()
    assert "Context Management" in practices
    
    # Test API reference
    api_ref = get_api_reference()
    assert "Tools" in api_ref
```

## Summary

These 6 resources provide:
1. **entity_types_reference** - All 20 entity types with fields
2. **operation_reference** - All operations with parameters
3. **workflow_templates** - Pre-built workflow examples
4. **schema_definitions** - JSON schemas for validation
5. **best_practices** - Agent best practices guide
6. **api_reference** - Complete API documentation

**Total effort**: 2 days to implement all 6 resources
**Impact**: Significantly improves agent experience and reduces errors

