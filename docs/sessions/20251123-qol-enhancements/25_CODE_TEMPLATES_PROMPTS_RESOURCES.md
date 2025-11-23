# Code Templates: Prompts & Resources

## File Structure

```
tools/
├── prompts.py          # All 6 prompts
├── resources.py        # All 6 resources
└── __init__.py

server.py
├── Import prompts & resources
└── Register with @mcp.prompt() and @mcp.resource()
```

## Template 1: Prompts File Structure

```python
# tools/prompts.py

from fastmcp import FastMCP

mcp = FastMCP()

# ============================================================================
# PROMPT 1: Entity Creation Guide
# ============================================================================

@mcp.prompt()
def entity_creation_guide(entity_type: str = "project"):
    """Guide for creating entities of a specific type."""
    
    entity_info = {
        "project": {
            "required": ["name"],
            "optional": ["description", "status"],
            "example": {"name": "My Project"}
        },
        "requirement": {
            "required": ["name", "project_id"],
            "optional": ["description", "status", "priority"],
            "example": {"name": "Security requirement"}
        },
        # ... more entity types
    }
    
    info = entity_info.get(entity_type, entity_info["project"])
    
    return f"""# Creating {entity_type.title()} Entities

## Quick Start
```python
entity_tool(
    operation="create",
    entity_type="{entity_type}",
    data={{"name": "My {entity_type}"}}
)
```

## Required Fields
{chr(10).join(f"- `{f}`" for f in info["required"])}

## Optional Fields
{chr(10).join(f"- `{f}`" for f in info["optional"])}

## Example
```python
entity_tool(
    operation="create",
    entity_type="{entity_type}",
    data={info["example"]}
)
```

## Best Practices
1. Always set workspace context first
2. Use batch_create for 3+ entities
3. Include all required fields
4. Use meaningful names
5. Set status/priority if applicable
"""

# ============================================================================
# PROMPT 2: Entity Search Guide
# ============================================================================

@mcp.prompt()
def entity_search_guide(entity_type: str = "requirement"):
    """Guide for searching entities."""
    
    return f"""# Searching {entity_type.title()} Entities

## Text Search
```python
entity_tool(
    operation="search",
    entity_type="{entity_type}",
    search_term="security"
)
```

## Semantic Search
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

## Best Practices
1. Use semantic search for complex queries
2. Use keyword search for exact matches
3. Use hybrid for best coverage
4. Filter by status/priority when possible
5. Limit results to 10-50 for performance
"""

# ============================================================================
# PROMPT 3: Relationship Guide
# ============================================================================

@mcp.prompt()
def relationship_guide():
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

## Best Practices
1. Always specify source and target types
2. Check before linking to avoid duplicates
3. Use batch operations for multiple links
4. Document relationship semantics
"""

# ============================================================================
# PROMPT 4: Workflow Guide
# ============================================================================

@mcp.prompt()
def workflow_guide():
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

## Best Practices
1. Use workflows for multi-step operations
2. Enable transaction_mode for safety
3. Check parameters before executing
4. Handle errors gracefully
"""

# ============================================================================
# PROMPT 5: Context Guide
# ============================================================================

@mcp.prompt()
def context_guide():
    """Guide for managing session context."""
    
    return """# Managing Session Context

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
```

## Best Practices
1. Set workspace context at session start
2. Set project context for project-specific work
3. Use context to reduce parameter spam
4. Clear context when switching workspaces
"""

# ============================================================================
# PROMPT 6: Error Recovery Guide
# ============================================================================

@mcp.prompt()
def error_recovery_guide():
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
        entity_id=expected_workspace
    )
```

## Best Practices
1. Always set workspace context first
2. Validate IDs before using them
3. Include all required fields
4. Use error suggestions for debugging
"""
```

## Template 2: Resources File Structure

```python
# tools/resources.py

from fastmcp import FastMCP
import json

mcp = FastMCP()

# ============================================================================
# RESOURCE 1: Entity Types Reference
# ============================================================================

@mcp.resource("file:///reference/entity_types.json")
def get_entity_types_reference():
    """Reference for all entity types."""
    
    return {
        "entity_types": [
            {
                "name": "project",
                "description": "Project container",
                "fields": ["id", "name", "organization_id", "description", "status"],
                "operations": ["create", "read", "update", "delete", "list", "search"]
            },
            {
                "name": "requirement",
                "description": "Requirement within document",
                "fields": ["id", "name", "document_id", "description", "status", "priority"],
                "operations": ["create", "read", "update", "delete", "list", "search"]
            },
            # ... 18 more entity types
        ]
    }

# ============================================================================
# RESOURCE 2: Operation Reference
# ============================================================================

@mcp.resource("file:///reference/operations.json")
def get_operation_reference():
    """Reference for all operations."""
    
    return {
        "operations": {
            "create": {
                "description": "Create a new entity",
                "required_params": ["entity_type", "data"],
                "optional_params": ["workspace_id", "parent_id"]
            },
            "read": {
                "description": "Read entity by ID",
                "required_params": ["entity_type", "entity_id"],
                "optional_params": ["include_relations"]
            },
            "search": {
                "description": "Search entities by text",
                "required_params": ["entity_type", "search_term"],
                "optional_params": ["filters", "limit"]
            },
            # ... more operations
        }
    }

# ============================================================================
# RESOURCE 3: Workflow Templates
# ============================================================================

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
            {
                "name": "import_requirements",
                "description": "Import requirements from external source",
                "parameters": ["project_id", "source", "data"]
            },
            # ... more templates
        ]
    }

# ============================================================================
# RESOURCE 4: Schema Definitions
# ============================================================================

@mcp.resource("file:///schemas/project.json")
def get_project_schema():
    """Project entity schema."""
    
    return {
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
    }

# ============================================================================
# RESOURCE 5: Best Practices Guide
# ============================================================================

@mcp.resource("file:///guides/best_practices.md")
def get_best_practices():
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
"""

# ============================================================================
# RESOURCE 6: API Reference
# ============================================================================

@mcp.resource("file:///reference/api.md")
def get_api_reference():
    """Complete API reference."""
    
    return """# Atoms MCP API Reference

## Tools
- context_tool: Manage session context
- entity_tool: CRUD operations
- relationship_tool: Entity relationships
- workflow_tool: Complex workflows
- query_tool: Data exploration

## Operations
- create, read, update, delete
- list, search, batch_create
- rag_search, aggregate, analyze

## Context Types
- workspace, project, document, entity_type, parent_id

## Relationship Types
- member, assignment, trace_link, requirement_test, invitation

## Response Format
```json
{
  "success": true/false,
  "data": {...},
  "error": "error message if failed",
  "metrics": {"total_ms": 145}
}
```
"""
```

## Template 3: Server Integration

```python
# server.py

from fastmcp import FastMCP
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

# Create FastMCP instance
mcp = FastMCP(
    name="Atoms MCP",
    instructions="Atoms MCP server with consolidated, agent-optimized tools"
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

# Register existing tools
mcp.tool()(context_tool)
mcp.tool()(entity_tool)
mcp.tool()(relationship_tool)
mcp.tool()(workflow_tool)
mcp.tool()(query_tool)

# Export for Vercel
app = mcp.http_app(path="/api/mcp", stateless_http=True)
```

## Template 4: Testing Prompts

```python
# tests/test_prompts.py

import pytest
from tools.prompts import (
    entity_creation_guide,
    entity_search_guide,
    relationship_guide,
    workflow_guide,
    context_guide,
    error_recovery_guide
)

class TestPrompts:
    def test_entity_creation_guide_project(self):
        result = entity_creation_guide("project")
        assert "Creating Project Entities" in result
        assert "Quick Start" in result
        assert "Best Practices" in result
    
    def test_entity_creation_guide_requirement(self):
        result = entity_creation_guide("requirement")
        assert "Creating Requirement Entities" in result
        assert "project_id" in result
    
    def test_entity_search_guide(self):
        result = entity_search_guide("requirement")
        assert "Searching Requirement Entities" in result
        assert "Text Search" in result
        assert "Semantic Search" in result
    
    def test_relationship_guide(self):
        result = relationship_guide()
        assert "Managing Entity Relationships" in result
        assert "Link Entities" in result
    
    def test_workflow_guide(self):
        result = workflow_guide()
        assert "Executing Workflows" in result
        assert "Setup Project" in result
    
    def test_context_guide(self):
        result = context_guide()
        assert "Managing Session Context" in result
        assert "Set Workspace Context" in result
    
    def test_error_recovery_guide(self):
        result = error_recovery_guide()
        assert "Error Recovery Guide" in result
        assert "Entity Not Found" in result
```

## Template 5: Testing Resources

```python
# tests/test_resources.py

import pytest
import json
from tools.resources import (
    get_entity_types_reference,
    get_operation_reference,
    get_workflow_templates,
    get_project_schema,
    get_best_practices,
    get_api_reference
)

class TestResources:
    def test_entity_types_reference(self):
        result = get_entity_types_reference()
        assert "entity_types" in result
        assert len(result["entity_types"]) == 20
        assert result["entity_types"][0]["name"] == "project"
    
    def test_operation_reference(self):
        result = get_operation_reference()
        assert "operations" in result
        assert "create" in result["operations"]
        assert "read" in result["operations"]
    
    def test_workflow_templates(self):
        result = get_workflow_templates()
        assert "templates" in result
        assert len(result["templates"]) == 5
    
    def test_project_schema(self):
        result = get_project_schema()
        assert result["type"] == "object"
        assert "name" in result["properties"]
        assert "id" in result["required"]
    
    def test_best_practices(self):
        result = get_best_practices()
        assert "Context Management" in result
        assert "Entity Operations" in result
    
    def test_api_reference(self):
        result = get_api_reference()
        assert "Tools" in result
        assert "Operations" in result
```

## Usage Instructions

1. **Copy prompts.py template** to `tools/prompts.py`
2. **Copy resources.py template** to `tools/resources.py`
3. **Update server.py** with imports and registrations
4. **Copy test templates** to `tests/test_prompts.py` and `tests/test_resources.py`
5. **Run tests**: `python cli.py test run --scope unit`
6. **Deploy**: `python cli.py server start`

## Customization

- Modify entity_info in entity_creation_guide for your entity types
- Add more entity types to entity_types_reference
- Add more operations to operation_reference
- Add more templates to workflow_templates
- Add more schemas to schema_definitions
- Update best_practices with your guidelines
- Update api_reference with your API details

