# Deep Dive: Prompts Implementation

## Overview

MCP Prompts are pre-written instructions that agents can invoke to get guidance on using tools. They're like built-in documentation that agents can reference.

## Prompt 1: Entity Creation Guide

### Purpose
Guide agents on creating entities with best practices and examples.

### Implementation
```python
@mcp.prompt()
def entity_creation_guide(entity_type: str = "project"):
    """Guide for creating entities of a specific type.
    
    Args:
        entity_type: The type of entity to create (project, requirement, test, etc.)
    
    Returns:
        Markdown guide with examples and best practices
    """
    
    # Get entity metadata
    entity_info = {
        "project": {
            "required": ["name"],
            "optional": ["description", "status"],
            "example": {"name": "My Project", "description": "Project description"}
        },
        "requirement": {
            "required": ["name", "project_id"],
            "optional": ["description", "status", "priority"],
            "example": {"name": "Security requirement", "project_id": "proj-1"}
        },
        "test": {
            "required": ["name", "project_id"],
            "optional": ["description", "status"],
            "example": {"name": "Security test", "project_id": "proj-1"}
        }
    }
    
    info = entity_info.get(entity_type, entity_info["project"])
    
    return f"""# Creating {entity_type.title()} Entities

## Quick Start

```python
entity_tool(
    operation="create",
    entity_type="{entity_type}",
    data={{
        "name": "My {entity_type}",
        "description": "Description here"
    }}
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

## With Context (Recommended)

Set workspace context first to auto-inject workspace_id:

```python
# Set workspace context
context_tool(
    operation="set_context",
    context_type="workspace",
    entity_id="ws-1"
)

# Now create - workspace auto-injected
entity_tool(
    operation="create",
    entity_type="{entity_type}",
    data={{"name": "My {entity_type}"}}
)
```

## Batch Creation

For creating 3+ entities, use batch_create:

```python
entity_tool(
    operation="batch_create",
    entity_type="{entity_type}",
    batch=[
        {{"name": "Item 1", "description": "First item"}},
        {{"name": "Item 2", "description": "Second item"}},
        {{"name": "Item 3", "description": "Third item"}}
    ]
)
```

## Best Practices

1. **Always set workspace context first**
   - Reduces parameter spam
   - Auto-injects workspace_id
   - Ensures correct workspace

2. **Use batch_create for multiple entities**
   - More efficient than individual creates
   - Atomic operation (all-or-nothing)
   - Better performance

3. **Include all required fields**
   - Check error messages for missing fields
   - Use entity_types_reference resource for field info
   - Validate before creating

4. **Use meaningful names**
   - Clear, descriptive names
   - Helps with searching later
   - Improves readability

5. **Set status/priority if applicable**
   - Helps with filtering
   - Improves organization
   - Enables better workflows

## Common Mistakes

❌ **Don't**: Create without setting workspace context
```python
# BAD - workspace_id required
entity_tool(operation="create", entity_type="{entity_type}", data={{"name": "..."}})
```

✅ **Do**: Set context first
```python
# GOOD - workspace auto-injected
context_tool("set_context", context_type="workspace", entity_id="ws-1")
entity_tool(operation="create", entity_type="{entity_type}", data={{"name": "..."}})
```

❌ **Don't**: Create one at a time
```python
# BAD - inefficient
for item in items:
    entity_tool(operation="create", entity_type="{entity_type}", data=item)
```

✅ **Do**: Use batch_create
```python
# GOOD - efficient
entity_tool(operation="batch_create", entity_type="{entity_type}", batch=items)
```

## Error Handling

### Missing Required Field
```
Error: Missing required field: 'name'
Solution: Include all required fields in data
```

### Invalid Entity Type
```
Error: Unknown entity type: 'invalid'
Solution: Use entity_types_reference resource to see valid types
```

### Workspace Not Found
```
Error: Workspace not found: 'ws-xyz'
Solution: Check workspace context with context_tool("get_context")
```

## Next Steps

- Use entity_types_reference to see all available entity types
- Use operation_reference to see all available operations
- Use best_practices guide for more tips
- Use error_recovery_guide if you encounter errors
"""
```

## Prompt 2: Entity Search Guide

### Purpose
Guide agents on searching entities with different modes.

### Implementation
```python
@mcp.prompt()
def entity_search_guide(entity_type: str = "requirement"):
    """Guide for searching entities."""
    
    return f"""# Searching {entity_type.title()} Entities

## Text Search

Simple keyword search:

```python
entity_tool(
    operation="search",
    entity_type="{entity_type}",
    search_term="security"
)
```

## Semantic Search (RAG)

AI-powered semantic search using embeddings:

```python
entity_tool(
    operation="rag_search",
    entity_type="{entity_type}",
    search_query="authentication requirements",
    rag_mode="semantic"
)
```

## Hybrid Search

Combination of keyword and semantic search:

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

Combine search with filters:

```python
entity_tool(
    operation="search",
    entity_type="{entity_type}",
    search_term="security",
    filters={{
        "status": "active",
        "priority": "high"
    }}
)
```

## With Pagination

Control result size:

```python
entity_tool(
    operation="search",
    entity_type="{entity_type}",
    search_term="security",
    limit=10,
    offset=0
)
```

## Search Modes Explained

### Keyword Search
- **Best for**: Exact matches, specific terms
- **Speed**: Fast
- **Accuracy**: High for exact matches
- **Example**: Searching for "SQL injection"

### Semantic Search
- **Best for**: Conceptual matches, complex queries
- **Speed**: Slower (uses embeddings)
- **Accuracy**: High for meaning-based matches
- **Example**: Searching for "database security vulnerabilities"

### Hybrid Search
- **Best for**: Balanced results
- **Speed**: Medium
- **Accuracy**: Best overall
- **Example**: Searching for "authentication" (gets both exact and related)

## Best Practices

1. **Use semantic search for complex queries**
   - Better for natural language
   - Finds related concepts
   - More forgiving of phrasing

2. **Use keyword search for exact matches**
   - Faster
   - More precise
   - Better for technical terms

3. **Use hybrid for best coverage**
   - Combines both approaches
   - Adjust weights for your use case
   - Default weights usually work well

4. **Filter by status/priority when possible**
   - Reduces noise
   - Improves relevance
   - Faster results

5. **Limit results to 10-50 for performance**
   - Reduces latency
   - Easier to process
   - Better UX

## Common Patterns

### Find Active Requirements
```python
entity_tool(
    operation="search",
    entity_type="requirement",
    search_term="security",
    filters={{"status": "active"}},
    limit=20
)
```

### Find High Priority Items
```python
entity_tool(
    operation="search",
    entity_type="requirement",
    search_term="critical",
    filters={{"priority": "high"}},
    limit=10
)
```

### Semantic Search with Filters
```python
entity_tool(
    operation="rag_search",
    entity_type="requirement",
    search_query="What are the authentication requirements?",
    rag_mode="semantic",
    filters={{"status": "active"}},
    limit=5
)
```

## Error Handling

### No Results Found
```
Error: No results found for 'xyz'
Solution: Try broader search term or remove filters
```

### Invalid Search Mode
```
Error: Invalid rag_mode: 'invalid'
Solution: Use 'semantic', 'keyword', 'hybrid', or 'auto'
```

## Next Steps

- Use best_practices guide for more search tips
- Use operation_reference for all search operations
- Use error_recovery_guide if you encounter errors
"""
```

## Prompt 3: Relationship Guide

### Purpose
Guide agents on linking and managing entity relationships.

### Implementation
```python
@mcp.prompt()
def relationship_guide():
    """Guide for managing entity relationships."""
    
    return """# Managing Entity Relationships

## Link Entities

Create a relationship between two entities:

```python
relationship_tool(
    operation="link",
    relationship_type="requirement_test",
    source={"type": "requirement", "id": "req-1"},
    target={"type": "test", "id": "test-1"}
)
```

## List Relationships

Find all relationships for an entity:

```python
relationship_tool(
    operation="list",
    relationship_type="requirement_test",
    source={"type": "requirement", "id": "req-1"}
)
```

## Check Relationship

Check if a relationship exists:

```python
relationship_tool(
    operation="check",
    relationship_type="requirement_test",
    source={"type": "requirement", "id": "req-1"},
    target={"type": "test", "id": "test-1"}
)
```

## Unlink Entities

Remove a relationship:

```python
relationship_tool(
    operation="unlink",
    relationship_type="requirement_test",
    source={"type": "requirement", "id": "req-1"},
    target={"type": "test", "id": "test-1"}
)
```

## Relationship Types

- `requirement_test` - Links requirements to tests
- `member` - Links users to organizations/projects
- `assignment` - Links entities to assignees
- `trace_link` - Links related entities
- `invitation` - Links invitations to organizations

## Best Practices

1. **Always specify source and target types**
   - Prevents ambiguity
   - Enables validation
   - Improves performance

2. **Use meaningful relationship types**
   - Clear semantics
   - Enables filtering
   - Improves maintainability

3. **Check before linking to avoid duplicates**
   - Use check operation first
   - Prevents duplicate relationships
   - Improves data quality

4. **Use batch operations for multiple links**
   - More efficient
   - Better performance
   - Atomic operation

5. **Document relationship semantics**
   - Clear meaning
   - Helps other developers
   - Improves maintainability

## Common Patterns

### Link Requirement to Tests
```python
# Check if already linked
exists = relationship_tool(
    operation="check",
    relationship_type="requirement_test",
    source={"type": "requirement", "id": "req-1"},
    target={"type": "test", "id": "test-1"}
)

# Link if not already linked
if not exists:
    relationship_tool(
        operation="link",
        relationship_type="requirement_test",
        source={"type": "requirement", "id": "req-1"},
        target={"type": "test", "id": "test-1"}
    )
```

### Find All Tests for a Requirement
```python
tests = relationship_tool(
    operation="list",
    relationship_type="requirement_test",
    source={"type": "requirement", "id": "req-1"}
)
```

## Error Handling

### Entity Not Found
```
Error: Entity not found: 'req-xyz'
Solution: Check entity ID with entity_tool("read", ...)
```

### Invalid Relationship Type
```
Error: Invalid relationship type: 'invalid'
Solution: Use valid relationship types (requirement_test, member, etc.)
```

## Next Steps

- Use best_practices guide for more relationship tips
- Use operation_reference for all relationship operations
- Use error_recovery_guide if you encounter errors
"""
```

## Prompt 4: Workflow Guide

### Purpose
Guide agents on executing complex workflows.

### Implementation
```python
@mcp.prompt()
def workflow_guide():
    """Guide for executing workflows."""
    
    return """# Executing Workflows

## Setup Project

Create a project with initial structure:

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

Update status for multiple entities:

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

Import requirements from external source:

```python
workflow_tool(
    workflow="import_requirements",
    parameters={
        "project_id": "proj-1",
        "source": "csv",
        "data": [
            {"name": "Req 1", "description": "..."},
            {"name": "Req 2", "description": "..."}
        ]
    }
)
```

## Setup Test Matrix

Set up test matrix for a project:

```python
workflow_tool(
    workflow="setup_test_matrix",
    parameters={
        "project_id": "proj-1",
        "test_types": ["unit", "integration", "e2e"],
        "environments": ["dev", "staging", "prod"]
    }
)
```

## Organization Onboarding

Complete organization setup:

```python
workflow_tool(
    workflow="organization_onboarding",
    parameters={
        "organization_name": "Acme Corp",
        "admin_email": "admin@acme.com",
        "initial_projects": ["Project 1", "Project 2"]
    }
)
```

## Best Practices

1. **Use workflows for multi-step operations**
   - Atomic operations
   - Better error handling
   - Consistent results

2. **Enable transaction_mode for safety**
   - All-or-nothing execution
   - Rollback on error
   - Data consistency

3. **Check parameters before executing**
   - Validate inputs
   - Prevent errors
   - Better UX

4. **Handle errors gracefully**
   - Check response status
   - Log errors
   - Provide feedback

5. **Monitor workflow progress**
   - Track execution
   - Handle timeouts
   - Provide status updates

## Common Patterns

### Setup New Project
```python
# 1. Create project
project = entity_tool(
    operation="create",
    entity_type="project",
    data={"name": "New Project"}
)

# 2. Setup project structure
workflow_tool(
    workflow="setup_project",
    parameters={
        "project_id": project["id"],
        "organization_id": "org-1"
    }
)

# 3. Import initial requirements
workflow_tool(
    workflow="import_requirements",
    parameters={
        "project_id": project["id"],
        "source": "csv",
        "data": [...]
    }
)
```

## Error Handling

### Invalid Workflow
```
Error: Unknown workflow: 'invalid'
Solution: Use valid workflow names (setup_project, import_requirements, etc.)
```

### Missing Parameters
```
Error: Missing required parameter: 'project_id'
Solution: Include all required parameters
```

## Next Steps

- Use best_practices guide for more workflow tips
- Use operation_reference for all workflow operations
- Use error_recovery_guide if you encounter errors
"""
```

## Prompt 5: Context Guide

### Purpose
Guide agents on managing session context.

### Implementation
```python
@mcp.prompt()
def context_guide():
    """Guide for managing session context."""
    
    return """# Managing Session Context

## Set Workspace Context

Set the current workspace:

```python
context_tool(
    operation="set_context",
    context_type="workspace",
    entity_id="ws-1"
)
```

## Set Project Context

Set the current project:

```python
context_tool(
    operation="set_context",
    context_type="project",
    entity_id="proj-1"
)
```

## Set Document Context

Set the current document:

```python
context_tool(
    operation="set_context",
    context_type="document",
    entity_id="doc-1"
)
```

## Set Entity Type Context

Set the current entity type focus:

```python
context_tool(
    operation="set_context",
    context_type="entity_type",
    entity_id="requirement"
)
```

## Get Current Context

Get all current context values:

```python
context = context_tool(operation="get_context")
# Returns: {"workspace_id": "ws-1", "project_id": "proj-1", ...}
```

## Clear Context

Clear all context:

```python
context_tool(operation="clear_context")
```

## Context Types

- `workspace` - Current workspace
- `project` - Current project
- `document` - Current document
- `entity_type` - Current entity type focus
- `parent_id` - Current parent entity

## Best Practices

1. **Set workspace context at session start**
   - Required for most operations
   - Auto-injected into all operations
   - Prevents errors

2. **Set project context for project-specific work**
   - Reduces parameter spam
   - Auto-injected into operations
   - Improves clarity

3. **Use context to reduce parameter spam**
   - Fewer parameters needed
   - Cleaner code
   - Better readability

4. **Clear context when switching workspaces**
   - Prevents cross-workspace errors
   - Ensures clean state
   - Improves safety

5. **Check context before operations**
   - Verify correct context
   - Prevent mistakes
   - Better debugging

## Common Patterns

### Setup Session
```python
# 1. Set workspace context
context_tool(
    operation="set_context",
    context_type="workspace",
    entity_id="ws-1"
)

# 2. Set project context
context_tool(
    operation="set_context",
    context_type="project",
    entity_id="proj-1"
)

# 3. Now all operations use this context
entity_tool(operation="list", entity_type="requirement")
# workspace_id and project_id auto-injected
```

### Switch Projects
```python
# 1. Get current context
context = context_tool(operation="get_context")

# 2. Update project context
context_tool(
    operation="set_context",
    context_type="project",
    entity_id="proj-2"
)

# 3. Now operations use new project
entity_tool(operation="list", entity_type="requirement")
# Uses proj-2 instead of proj-1
```

## Error Handling

### Invalid Context Type
```
Error: Invalid context type: 'invalid'
Solution: Use valid context types (workspace, project, document, entity_type, parent_id)
```

### Entity Not Found
```
Error: Entity not found: 'ws-xyz'
Solution: Check entity ID with entity_tool("read", ...)
```

## Next Steps

- Use best_practices guide for more context tips
- Use operation_reference for all context operations
- Use error_recovery_guide if you encounter errors
"""
```

## Prompt 6: Error Recovery Guide

### Purpose
Guide agents on handling errors and recovering.

### Implementation
```python
@mcp.prompt()
def error_recovery_guide():
    """Guide for handling errors and recovery."""
    
    return """# Error Recovery Guide

## Common Errors

### Entity Not Found

**Error**: "Entity not found: 'proj-xyz'"

**Causes**:
- Wrong entity ID
- Entity was deleted
- Wrong workspace context

**Recovery**:
```python
# 1. List entities to find correct ID
entities = entity_tool(operation="list", entity_type="project")

# 2. Find the correct ID
correct_id = next(e["id"] for e in entities if e["name"] == "My Project")

# 3. Use correct ID
entity_tool(operation="read", entity_type="project", entity_id=correct_id)
```

### Missing Required Field

**Error**: "Missing required field: 'name'"

**Causes**:
- Forgot to include required field
- Field name is wrong
- Field value is null

**Recovery**:
```python
# 1. Check entity_types_reference for required fields
# 2. Include all required fields
entity_tool(
    operation="create",
    entity_type="project",
    data={
        "name": "My Project",  # Required
        "description": "..."   # Optional
    }
)
```

### Permission Denied

**Error**: "Permission denied"

**Causes**:
- Wrong workspace context
- Insufficient permissions
- Entity belongs to different workspace

**Recovery**:
```python
# 1. Check current context
context = context_tool(operation="get_context")

# 2. Verify workspace is correct
if context["workspace_id"] != expected_workspace:
    context_tool(
        operation="set_context",
        context_type="workspace",
        entity_id=expected_workspace
    )

# 3. Try operation again
entity_tool(operation="read", entity_type="project", entity_id="proj-1")
```

### Invalid Operation

**Error**: "Invalid operation: 'invalid'"

**Causes**:
- Typo in operation name
- Operation not supported for entity type
- Operation requires additional parameters

**Recovery**:
```python
# 1. Check operation_reference for valid operations
# 2. Use correct operation name
entity_tool(operation="create", entity_type="project", data={...})
# Not: entity_tool(operation="creat", ...)
```

## Debugging Tips

### 1. Check Context
```python
context = context_tool(operation="get_context")
print(f"Current workspace: {context['workspace_id']}")
print(f"Current project: {context['project_id']}")
```

### 2. Verify Entity Exists
```python
try:
    entity = entity_tool(
        operation="read",
        entity_type="project",
        entity_id="proj-1"
    )
    print(f"Entity found: {entity}")
except Exception as e:
    print(f"Entity not found: {e}")
```

### 3. Check Operation Parameters
```python
# Use operation_reference to see required parameters
# Verify all required parameters are provided
entity_tool(
    operation="create",
    entity_type="project",
    data={"name": "My Project"}  # Include all required fields
)
```

### 4. Review Error Message
```python
# Error messages usually indicate the problem
# "Missing required field: 'name'" → Add name field
# "Entity not found: 'proj-xyz'" → Check entity ID
# "Invalid operation: 'invalid'" → Check operation name
```

## Best Practices

1. **Always set workspace context first**
   - Prevents permission errors
   - Ensures correct workspace
   - Improves safety

2. **Validate IDs before using them**
   - Check entity exists
   - Prevent "not found" errors
   - Better error handling

3. **Include all required fields**
   - Check entity_types_reference
   - Prevent "missing field" errors
   - Improve data quality

4. **Use error suggestions for debugging**
   - Suggestions provided in error responses
   - Helps identify issues
   - Speeds up debugging

5. **Check operation history for recovery**
   - See what operations were executed
   - Identify what went wrong
   - Plan recovery steps

## Common Patterns

### Safe Entity Creation
```python
# 1. Set context
context_tool("set_context", context_type="workspace", entity_id="ws-1")

# 2. Verify workspace exists
context = context_tool(operation="get_context")
assert context["workspace_id"] == "ws-1"

# 3. Create entity with all required fields
entity = entity_tool(
    operation="create",
    entity_type="project",
    data={"name": "My Project"}
)

# 4. Verify creation succeeded
assert entity["success"]
print(f"Created: {entity['data']['id']}")
```

### Safe Entity Read
```python
# 1. List entities to find correct ID
entities = entity_tool(operation="list", entity_type="project")

# 2. Find entity by name
target = next((e for e in entities if e["name"] == "My Project"), None)

# 3. Read if found
if target:
    entity = entity_tool(
        operation="read",
        entity_type="project",
        entity_id=target["id"]
    )
else:
    print("Entity not found")
```

## Next Steps

- Use best_practices guide for more tips
- Use operation_reference for all operations
- Use entity_types_reference for entity information
"""
```

## Summary

These 6 prompts provide comprehensive guidance for agents on:
1. Creating entities
2. Searching entities
3. Managing relationships
4. Executing workflows
5. Managing context
6. Recovering from errors

Each prompt includes:
- Quick start examples
- Detailed explanations
- Best practices
- Common patterns
- Error handling
- Next steps

**Total effort**: 2 days to implement all 6 prompts
**Impact**: Significantly improves agent experience and reduces errors

