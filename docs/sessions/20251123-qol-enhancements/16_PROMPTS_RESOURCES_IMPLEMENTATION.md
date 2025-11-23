# Prompts & Resources Implementation Guide

## File Structure

```
tools/
├── prompts.py          # NEW: All MCP prompts
└── resources.py        # NEW: All MCP resources

server.py
├── Import prompts & resources
└── Register with @mcp.prompt() and @mcp.resource()
```

## Implementation: Prompts

### 1. Entity Creation Guide
```python
@mcp.prompt()
def entity_creation_guide(entity_type: str = "project"):
    """Guide for creating entities of a specific type."""
    return f"""
# Creating {entity_type} Entities

## Quick Start
```python
entity_tool(
    operation="create",
    entity_type="{entity_type}",
    data={{"name": "My {entity_type}"}}
)
```

## With Context (Recommended)
```python
# Set workspace context first
context_tool("set_context", context_type="workspace", entity_id="ws-1")

# Now create - workspace auto-injected
entity_tool(
    operation="create",
    entity_type="{entity_type}",
    data={{"name": "My {entity_type}"}}
)
```

## Batch Creation
```python
entity_tool(
    operation="batch_create",
    entity_type="{entity_type}",
    batch=[
        {{"name": "Item 1"}},
        {{"name": "Item 2"}},
        {{"name": "Item 3"}}
    ]
)
```

## Best Practices
1. Always set workspace context first
2. Use batch_create for 3+ entities
3. Include all required fields
4. Use meaningful names
5. Set status/priority if applicable
"""
```

### 2. Entity Search Guide
```python
@mcp.prompt()
def entity_search_guide(entity_type: str = "requirement"):
    """Guide for searching entities."""
    return f"""
# Searching {entity_type} Entities

## Text Search
```python
entity_tool(
    operation="search",
    entity_type="{entity_type}",
    search_term="security"
)
```

## Semantic Search (RAG)
```python
entity_tool(
    operation="rag_search",
    entity_type="{entity_type}",
    search_query="authentication requirements",
    rag_mode="semantic"
)
```

## Hybrid Search
```python
entity_tool(
    operation="rag_search",
    entity_type="{entity_type}",
    search_query="security",
    rag_mode="hybrid",
    keyword_weight=0.3,
    semantic_weight=0.7
)
```

## With Filters
```python
entity_tool(
    operation="search",
    entity_type="{entity_type}",
    search_term="security",
    filters={{"status": "active", "priority": "high"}}
)
```

## Best Practices
1. Use semantic search for complex queries
2. Use keyword search for exact matches
3. Use hybrid for best coverage
4. Filter by status/priority when possible
5. Limit results to 10-50 for performance
"""
```

### 3. Relationship Guide
```python
@mcp.prompt()
def relationship_guide():
    """Guide for managing entity relationships."""
    return """
# Managing Entity Relationships

## Link Entities
```python
relationship_tool(
    operation="link",
    relationship_type="requirement_test",
    source={"type": "requirement", "id": "req-1"},
    target={"type": "test", "id": "test-1"}
)
```

## List Relationships
```python
relationship_tool(
    operation="list",
    relationship_type="requirement_test",
    source={"type": "requirement", "id": "req-1"}
)
```

## Check Relationship
```python
relationship_tool(
    operation="check",
    relationship_type="requirement_test",
    source={"type": "requirement", "id": "req-1"},
    target={"type": "test", "id": "test-1"}
)
```

## Unlink Entities
```python
relationship_tool(
    operation="unlink",
    relationship_type="requirement_test",
    source={"type": "requirement", "id": "req-1"},
    target={"type": "test", "id": "test-1"}
)
```

## Best Practices
1. Always specify source and target types
2. Use meaningful relationship types
3. Check before linking to avoid duplicates
4. Use batch operations for multiple links
5. Document relationship semantics
"""
```

### 4. Workflow Guide
```python
@mcp.prompt()
def workflow_guide():
    """Guide for executing workflows."""
    return """
# Executing Workflows

## Setup Project
```python
workflow_tool(
    workflow="setup_project",
    parameters={
        "name": "My Project",
        "description": "Project description",
        "organization_id": "org-1"
    }
)
```

## Bulk Status Update
```python
workflow_tool(
    workflow="bulk_status_update",
    parameters={
        "entity_type": "requirement",
        "entity_ids": ["req-1", "req-2", "req-3"],
        "new_status": "completed"
    }
)
```

## Import Requirements
```python
workflow_tool(
    workflow="import_requirements",
    parameters={
        "project_id": "proj-1",
        "source": "csv",
        "data": [...]
    }
)
```

## Best Practices
1. Use workflows for multi-step operations
2. Enable transaction_mode for safety
3. Check parameters before executing
4. Handle errors gracefully
5. Monitor workflow progress
"""
```

### 5. Context Guide
```python
@mcp.prompt()
def context_guide():
    """Guide for managing session context."""
    return """
# Managing Session Context

## Set Workspace Context
```python
context_tool(
    operation="set_context",
    context_type="workspace",
    entity_id="ws-1"
)
```

## Set Project Context
```python
context_tool(
    operation="set_context",
    context_type="project",
    entity_id="proj-1"
)
```

## Get Current Context
```python
context_tool(operation="get_context")
# Returns: {"workspace_id": "ws-1", "project_id": "proj-1", ...}
```

## Clear Context
```python
context_tool(operation="clear_context")
```

## Best Practices
1. Set workspace context at session start
2. Set project context for project-specific work
3. Use context to reduce parameter spam
4. Clear context when switching workspaces
5. Check context before operations
"""
```

### 6. Error Recovery Guide
```python
@mcp.prompt()
def error_recovery_guide():
    """Guide for handling errors and recovery."""
    return """
# Error Recovery Guide

## Common Errors

### Entity Not Found
```python
# Error: "Entity not found: 'proj-xyz'"
# Solution: List entities to find correct ID
entity_tool(operation="list", entity_type="project")
```

### Missing Required Field
```python
# Error: "Missing required field: 'name'"
# Solution: Include all required fields
entity_tool(
    operation="create",
    entity_type="project",
    data={"name": "My Project", "description": "..."}
)
```

### Permission Denied
```python
# Error: "Permission denied"
# Solution: Check workspace/project context
context_tool(operation="get_context")
```

## Best Practices
1. Always check context before operations
2. Validate IDs before using them
3. Include all required fields
4. Use error suggestions for debugging
5. Check operation history for recovery
"""
```

## Implementation: Resources

### 1. Entity Types Reference
```python
@mcp.resource("file:///reference/entity_types.json")
def get_entity_types_reference():
    """Reference for all entity types."""
    return {
        "entity_types": [
            {
                "name": "project",
                "description": "A project container",
                "table": "projects",
                "fields": ["name", "description", "status"],
                "operations": ["create", "read", "update", "delete", "list", "search"]
            },
            # ... 19 more entity types
        ]
    }
```

### 2. Operation Reference
```python
@mcp.resource("file:///reference/operations.json")
def get_operation_reference():
    """Reference for all operations."""
    return {
        "operations": {
            "create": {"description": "Create new entity", "required": ["entity_type", "data"]},
            "read": {"description": "Read entity by ID", "required": ["entity_type", "entity_id"]},
            "update": {"description": "Update entity", "required": ["entity_type", "entity_id", "data"]},
            # ... more operations
        }
    }
```

### 3. Workflow Templates
```python
@mcp.resource("file:///templates/workflows.json")
def get_workflow_templates():
    """Pre-built workflow templates."""
    return {
        "templates": [
            {
                "name": "setup_project",
                "description": "Create project with initial structure",
                "parameters": ["name", "description", "organization_id"]
            },
            # ... more templates
        ]
    }
```

### 4. Schema Definitions
```python
@mcp.resource("file:///schemas/project.json")
def get_project_schema():
    """Project entity schema."""
    return {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "name": {"type": "string"},
            "description": {"type": "string"},
            "status": {"type": "string", "enum": ["active", "archived"]},
        },
        "required": ["name"]
    }
```

### 5. Best Practices Guide
```python
@mcp.resource("file:///guides/best_practices.md")
def get_best_practices():
    """Agent best practices guide."""
    return """
# Best Practices for Atoms MCP

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
"""
```

### 6. API Reference
```python
@mcp.resource("file:///reference/api.md")
def get_api_reference():
    """Complete API reference."""
    return """
# Atoms MCP API Reference

## Tools
- context_tool: Manage session context
- entity_tool: CRUD operations
- relationship_tool: Entity relationships
- workflow_tool: Complex workflows
- query_tool: Data exploration

## Operations
- create, read, update, delete
- archive, restore, list, search
- batch_create, bulk_update, bulk_delete
- rag_search, aggregate, analyze

## Context Types
- workspace, project, document, entity_type, parent_id

## Relationship Types
- member, assignment, trace_link, requirement_test, invitation
"""
```

## Integration with server.py

```python
# In server.py, after creating FastMCP instance:

# Import prompts and resources
from tools.prompts import (
    entity_creation_guide,
    entity_search_guide,
    relationship_guide,
    workflow_guide,
    context_guide,
    error_recovery_guide
)

from tools.resources import (
    get_entity_types_reference,
    get_operation_reference,
    get_workflow_templates,
    get_project_schema,
    get_best_practices,
    get_api_reference
)

# Register prompts
mcp.prompt()(entity_creation_guide)
mcp.prompt()(entity_search_guide)
mcp.prompt()(relationship_guide)
mcp.prompt()(workflow_guide)
mcp.prompt()(context_guide)
mcp.prompt()(error_recovery_guide)

# Register resources
mcp.resource("file:///reference/entity_types.json")(get_entity_types_reference)
mcp.resource("file:///reference/operations.json")(get_operation_reference)
mcp.resource("file:///templates/workflows.json")(get_workflow_templates)
mcp.resource("file:///schemas/project.json")(get_project_schema)
mcp.resource("file:///guides/best_practices.md")(get_best_practices)
mcp.resource("file:///reference/api.md")(get_api_reference)
```

## Testing

```python
# Test prompts
def test_prompts():
    assert entity_creation_guide("project") is not None
    assert entity_search_guide("requirement") is not None
    assert relationship_guide() is not None
    assert workflow_guide() is not None
    assert context_guide() is not None
    assert error_recovery_guide() is not None

# Test resources
def test_resources():
    assert get_entity_types_reference() is not None
    assert get_operation_reference() is not None
    assert get_workflow_templates() is not None
    assert get_project_schema() is not None
    assert get_best_practices() is not None
    assert get_api_reference() is not None
```

## Effort Breakdown

| Item | Effort |
|------|--------|
| 6 Prompts | 2 days |
| 6 Resources | 2 days |
| Integration | 1 day |
| Testing | 1 day |
| Documentation | 1 day |
| **TOTAL** | **7 days** |

## Recommendation

Add to Phase 1 of QOL Plan as **Phase 1.5: Prompts & Resources** (1 week):
- Implement 6 essential prompts
- Implement 6 essential resources
- Integrate with server.py
- Write tests
- Update documentation

**Impact**: Significantly improves agent experience and reduces errors
**Risk**: Low (non-breaking, additive only)
**Timeline**: Fits within Phase 1 (4 weeks)

