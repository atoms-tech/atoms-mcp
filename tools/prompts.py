"""MCP Prompts for Atoms - Agent guidance and best practices.

Provides 6 essential prompts to guide agents in using the Atoms MCP effectively.
"""

import logging

logger = logging.getLogger(__name__)


def get_entity_creation_guide(entity_type: str = "project") -> str:
    """Guide for creating entities of a specific type."""
    
    entity_info = {
        "project": {
            "required": ["name"],
            "optional": ["description", "status"],
            "example": '{"name": "My Project", "description": "Project description"}'
        },
        "requirement": {
            "required": ["name", "project_id"],
            "optional": ["description", "status", "priority"],
            "example": '{"name": "Security requirement", "project_id": "proj-1"}'
        },
        "test": {
            "required": ["name", "project_id"],
            "optional": ["description", "status", "test_type"],
            "example": '{"name": "Test case", "project_id": "proj-1"}'
        },
        "document": {
            "required": ["name", "project_id"],
            "optional": ["description", "content"],
            "example": '{"name": "Requirements document", "project_id": "proj-1"}'
        }
    }
    
    info = entity_info.get(entity_type, entity_info["project"])
    required_fields = ", ".join(f"`{f}`" for f in info["required"])
    optional_fields = ", ".join(f"`{f}`" for f in info["optional"])
    
    return f"""# Creating {entity_type.title()} Entities

## Quick Start
```python
entity_tool(
    operation="create",
    entity_type="{entity_type}",
    data={info["example"]}
)
```

## Required Fields
{required_fields}

## Optional Fields
{optional_fields}

## Best Practices
1. Always set workspace context first with `context_tool`
2. Use batch_create for 3+ entities
3. Include all required fields
4. Use meaningful names
5. Set status/priority if applicable

## Common Mistakes
- ❌ Forgetting required fields
- ❌ Not setting workspace context
- ❌ Creating entities one-by-one instead of batch
- ✅ Always validate required fields first
"""


def get_entity_search_guide(entity_type: str = "requirement") -> str:
    """Guide for searching entities."""
    
    return f"""# Searching {entity_type.title()} Entities

## Text Search
```python
entity_tool(
    operation="search",
    entity_type="{entity_type}",
    search_term="security",
    limit=10
)
```

## Semantic Search
```python
entity_tool(
    operation="rag_search",
    entity_type="{entity_type}",
    content="authentication requirements",
    rag_mode="semantic",
    limit=10
)
```

## Hybrid Search
```python
entity_tool(
    operation="rag_search",
    entity_type="{entity_type}",
    content="security",
    rag_mode="hybrid",
    limit=10
)
```

## With Filters
```python
entity_tool(
    operation="search",
    entity_type="{entity_type}",
    search_term="security",
    filters={{"status": "active", "priority": "high"}},
    limit=10
)
```

## Best Practices
1. Use semantic search for complex queries
2. Use keyword search for exact matches
3. Use hybrid for best coverage
4. Filter by status/priority when possible
5. Limit results to 10-50 for performance
"""


def get_relationship_guide() -> str:
    """Guide for managing entity relationships."""
    
    return """# Managing Entity Relationships

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
2. Check before linking to avoid duplicates
3. Use batch operations for multiple links
4. Document relationship semantics
"""


def get_workflow_guide() -> str:
    """Guide for executing workflows."""
    
    return """# Executing Workflows

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
"""


def get_context_guide() -> str:
    """Guide for managing session context."""
    
    return """# Managing Session Context

## Set Workspace Context
```python
context_tool(
    operation="set_context",
    context_type="workspace",
    context_id="ws-1"
)
```

## Set Project Context
```python
context_tool(
    operation="set_context",
    context_type="project",
    context_id="proj-1"
)
```

## Set Document Context
```python
context_tool(
    operation="set_context",
    context_type="document",
    context_id="doc-1"
)
```

## Get Current Context
```python
context_tool(operation="get_context")
```

## Best Practices
1. Set workspace context at session start
2. Set project context for project-specific work
3. Set document context for document-specific work
4. Use context to reduce parameter spam
5. Clear context when switching workspaces
"""


def get_error_recovery_guide() -> str:
    """Guide for handling errors and recovery."""
    
    return """# Error Recovery Guide

## Entity Not Found
```python
# List entities to find correct ID
entities = entity_tool(operation="list", entity_type="project")

# Find by name
target = next((e for e in entities if e["name"] == "My Project"), None)

# Use correct ID
if target:
    entity_tool(operation="read", entity_type="project", entity_id=target["id"])
```

## Missing Required Field
```python
# Include all required fields
entity_tool(
    operation="create",
    entity_type="project",
    data={"name": "My Project", "description": "..."}
)
```

## Permission Denied
```python
# Check context
context = context_tool(operation="get_context")

# Verify workspace is correct
if context["workspace_id"] != expected_workspace:
    context_tool(
        operation="set_context",
        context_type="workspace",
        context_id=expected_workspace
    )
```

## Best Practices
1. Always set workspace context first
2. Validate IDs before using them
3. Include all required fields
4. Use error suggestions for debugging
5. Check context when operations fail
"""

