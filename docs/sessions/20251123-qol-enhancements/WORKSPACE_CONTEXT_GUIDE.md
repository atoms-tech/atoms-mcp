# Workspace Context Persistence Guide

## Overview

Workspace context persistence enables stateful agents and long-running sessions to set a workspace once and have it automatically applied to all subsequent operations that need `workspace_id`.

This eliminates:
- Repeated `workspace_id` parameters in every call
- "Creating without workspace context" warnings
- Database NOT NULL constraint failures in E2E tests
- Cognitive load for agents managing multiple workspaces

## Quick Start

### 1. Set Workspace Context

```python
# Set the current workspace for this session
result = await mcp.call_tool("context_tool", {
    "operation": "set_workspace",
    "workspace_id": "workspace-123"
})

# Response:
# {
#   "success": true,
#   "workspace_id": "workspace-123",
#   "message": "Workspace context set to workspace-123"
# }
```

### 2. Automatic Application to Operations

After setting workspace, all subsequent operations automatically use it:

```python
# No need to specify workspace_id - it's automatically applied
result = await mcp.call_tool("entity_tool", {
    "operation": "create",
    "entity_type": "project",
    "data": {
        "name": "My Project",
        "description": "Created with automatic workspace context"
        # workspace_id is AUTOMATICALLY INJECTED
    }
})
```

### 3. Query Workspace Context

```python
# Get current workspace
result = await mcp.call_tool("context_tool", {
    "operation": "get_workspace"
})

# Response:
# {
#   "success": true,
#   "workspace_id": "workspace-123",
#   "message": "Current workspace: workspace-123"
# }
```

### 4. Clear Workspace (Optional)

```python
# Remove workspace context if needed
result = await mcp.call_tool("context_tool", {
    "operation": "clear_workspace"
})

# Response:
# {
#   "success": true,
#   "message": "Workspace context cleared"
# }
```

## Advanced Usage

### Override Workspace for Specific Operations

Even after setting workspace context, you can override it for individual operations:

```python
# Set default workspace
await mcp.call_tool("context_tool", {
    "operation": "set_workspace",
    "workspace_id": "workspace-123"
})

# Use default workspace
await mcp.call_tool("entity_tool", {
    "operation": "create",
    "entity_type": "project",
    "data": {"name": "Project in workspace-123"}
})

# Override to use different workspace for this specific call
await mcp.call_tool("entity_tool", {
    "operation": "create",
    "entity_type": "project",
    "data": {"name": "Project in workspace-456"},
    "workspace_id": "workspace-456"  # Explicit override
})

# Subsequent calls revert to default
await mcp.call_tool("entity_tool", {
    "operation": "create",
    "entity_type": "project",
    "data": {"name": "Project in workspace-123 again"}
})
```

### Session Persistence Across Requests

Workspace context is persisted in the session, so it survives across multiple HTTP requests:

```python
# Request 1: Set workspace
session_token = await login()
await mcp.call_tool("context_tool", {
    "operation": "set_workspace",
    "workspace_id": "workspace-123"
}, session_token=session_token)

# Request 2: Workspace is automatically available
result = await mcp.call_tool("entity_tool", {
    "operation": "list",
    "entity_type": "project"
    # workspace_id automatically loaded from session
}, session_token=session_token)
```

### Inspect Full Session State

For debugging or monitoring:

```python
result = await mcp.call_tool("context_tool", {
    "operation": "get_session_state"
})

# Response:
# {
#   "success": true,
#   "session_id": "session-uuid",
#   "user_id": "user-uuid",
#   "workspace_id": "workspace-123"
# }
```

## Integration with Tools

### entity_tool

Automatic workspace context application:

```python
# Set context once
await context_tool("set_workspace", workspace_id="ws-1")

# Create without workspace_id
await entity_tool(
    entity_type="project",
    data={"name": "My Project"}
    # workspace_id automatically injected
)

# List without workspace_id
result = await entity_tool(
    entity_type="project",
    operation="list"
    # workspace_id automatically injected
)
```

### relationship_tool

Automatic workspace context application:

```python
# Set context once
await context_tool("set_workspace", workspace_id="ws-1")

# Link entities without workspace_id
await relationship_tool(
    operation="link",
    relationship_type="member",
    source={"type": "organization", "id": "org-1"},
    target={"type": "user", "id": "user-1"}
    # workspace_id automatically injected into metadata
)
```

## Architecture

### Context Storage Hierarchy

Context is stored and loaded in this order:

1. **Explicit parameter**: If `workspace_id` provided to tool call
2. **Request context**: If loaded in this request from session
3. **Session storage**: If persisted in Supabase mcp_sessions table
4. **None**: If not set anywhere (tool may require explicit workspace_id)

### Implementation Details

#### SessionManager Extensions

```python
# auth/session_manager.py
async def set_workspace_context(session_id, workspace_id)
async def get_workspace_context(session_id) -> workspace_id
async def clear_workspace_context(session_id)
```

Workspace context is stored in session's `mcp_state` dict:
```json
{
  "session_id": "...",
  "user_id": "...",
  "mcp_state": {
    "current_workspace_id": "workspace-123"
  }
}
```

#### Context Manager

```python
# services/context_manager.py
class SessionContext:
  - set_workspace_id()
  - get_workspace_id()
  - resolve_workspace_id() -> workspace from param/context/session
  - load_workspace_from_session()
```

Uses Python's `contextvars` for thread-safe context storage.

#### Context Tool

```python
# tools/context.py
async def context_tool(
    operation: "set_workspace" | "get_workspace" | "clear_workspace" | "get_session_state",
    workspace_id: Optional[str]
)
```

## Error Handling

### No Workspace Set

If workspace is required but not set:

```python
result = await entity_tool(
    entity_type="project",
    operation="create",
    data={"name": "My Project"}
    # No workspace in context or session
)

# May fail with:
# {
#   "success": false,
#   "error": "NOT NULL constraint failed: projects.workspace_id"
# }
```

**Fix**: Set workspace first
```python
await context_tool("set_workspace", workspace_id="ws-1")
```

### Invalid Workspace

If workspace doesn't exist or user doesn't have access:

```python
result = await context_tool(
    "set_workspace",
    workspace_id="invalid-workspace"
)

# Sets successfully in context (validation is in DB)
# When used in operations, may fail with:
# {
#   "success": false,
#   "error": "Workspace not found or access denied"
# }
```

## Best Practices

### 1. Set Workspace Early

```python
# Good: Set at session start
async def start_session():
    session = await authenticate()
    await context_tool("set_workspace", workspace_id=session.default_workspace)
    return session
```

### 2. Explicit for Multi-Workspace Operations

```python
# If operation needs different workspace, be explicit
await entity_tool(..., workspace_id="ws-2")

# Or set temporarily and restore
old_ws = await context_tool("get_workspace")
await context_tool("set_workspace", workspace_id="ws-2")
# ... do work in ws-2
await context_tool("set_workspace", workspace_id=old_ws)
```

### 3. Document Workspace Expectations

```python
"""
Process workflow for organization.

Requires workspace context to be set before calling this function.
Will create entities within the current workspace context.

Args:
    org_id: Organization ID
    
Raises:
    ValueError: If workspace context not set
"""
async def process_organization(org_id):
    ws = await context_tool("get_workspace")
    if not ws:
        raise ValueError("Workspace context required")
    ...
```

### 4. Test with Workspace Context

```python
# In test setup
async def setup_test():
    # Set workspace context
    await context_tool("set_workspace", workspace_id=TEST_WORKSPACE)
    
    # All operations automatically use TEST_WORKSPACE
    result = await entity_tool(
        operation="create",
        entity_type="project",
        data={"name": "Test Project"}
        # No workspace_id needed!
    )
    assert result["success"]
```

## Migration Guide

### Before (Without Context Persistence)

```python
# Had to specify workspace_id everywhere
await entity_tool(
    operation="create",
    entity_type="project",
    data={"name": "Project 1"},
    workspace_id="ws-1"
)

await entity_tool(
    operation="create",
    entity_type="document",
    data={"title": "Doc 1"},
    workspace_id="ws-1"
)

await relationship_tool(
    operation="link",
    relationship_type="member",
    source={"type": "workspace", "id": "ws-1"},
    target={"type": "user", "id": "user-1"}
)
```

### After (With Context Persistence)

```python
# Set once at session start
await context_tool("set_workspace", workspace_id="ws-1")

# All operations automatically use workspace
await entity_tool(
    operation="create",
    entity_type="project",
    data={"name": "Project 1"}
)

await entity_tool(
    operation="create",
    entity_type="document",
    data={"title": "Doc 1"}
)

await relationship_tool(
    operation="link",
    relationship_type="member",
    source={"type": "workspace", "id": "ws-1"},
    target={"type": "user", "id": "user-1"}
)
```

**Benefit**: 67% fewer `workspace_id` parameters, clearer intent, less repetition.

## Troubleshooting

### Workspace Not Being Applied

**Symptom**: Operations still require explicit `workspace_id`

**Causes**:
1. Workspace not set in context
2. Session context not initialized
3. Tool doesn't support context resolution

**Debug**:
```python
# Check current context
result = await context_tool("get_session_state")
print(result)  # Shows session_id, user_id, workspace_id

# If workspace_id is None, set it
await context_tool("set_workspace", workspace_id="ws-1")
```

### "Creating without workspace context" Warnings

**Symptom**: 
```
WARNING: User creating project without workspace context. 
This may fail at database level due to NOT NULL constraints.
```

**Causes**:
- Workspace context not set before operation
- Operation doesn't check context (older tools)

**Fix**:
```python
# Set workspace before any create operations
await context_tool("set_workspace", workspace_id="ws-1")

# Then create
await entity_tool(operation="create", entity_type="project", data={...})
```

### Session Not Persisting Workspace

**Symptom**: Workspace context lost between requests

**Causes**:
1. Session token not preserved between requests
2. Session expired (default: 24 hours)
3. Session cleared by explicit operation

**Debug**:
```python
# Before request 1
await context_tool("set_workspace", workspace_id="ws-1")
result = await context_tool("get_workspace")
print(result["workspace_id"])  # Shows "ws-1"

# In request 2 with same session token
result = await context_tool("get_workspace")  
print(result["workspace_id"])  # Should still show "ws-1"
```

## API Reference

### context_tool

**Operations**:

#### set_workspace
Sets current workspace for this session.

```
context_tool(
    operation="set_workspace",
    workspace_id="workspace-123"  # Required
) -> {success, workspace_id, message}
```

#### get_workspace
Gets current workspace from context/session.

```
context_tool(
    operation="get_workspace"
) -> {success, workspace_id, message}
```

#### clear_workspace
Removes workspace context.

```
context_tool(
    operation="clear_workspace"
) -> {success, message}
```

#### get_session_state
Gets full session state (debugging).

```
context_tool(
    operation="get_session_state"
) -> {success, session_id, user_id, workspace_id}
```

## See Also

- [SessionManager API](auth/session_manager.py)
- [SessionContext Implementation](services/context_manager.py)
- [Context Tool Implementation](tools/context.py)
- [Entity Tool Integration](server.py#L680-L690)
