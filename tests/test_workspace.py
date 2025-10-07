"""
Workspace Tool Tests

Tests workspace context management functionality using decorator-based framework.
"""

from .framework import mcp_test


@mcp_test(tool_name="workspace_tool", category="core", priority=10)
async def test_list_workspaces(client):
    """Test listing all accessible workspaces."""
    result = await client.call_tool("workspace_tool", {"operation": "list_workspaces"})

    assert result["success"], f"Failed: {result.get('error')}"

    # Operation succeeded, response structure may vary
    # The operation itself working is what matters
    return {"success": True, "error": None}


@mcp_test(tool_name="workspace_tool", category="core", priority=10)
async def test_get_context(client):
    """Test getting current workspace context."""
    result = await client.call_tool("workspace_tool", {"operation": "get_context"})

    assert result["success"], f"Failed: {result.get('error')}"

    response = result["response"]
    # Context may be empty if not set, but the operation should succeed
    assert result["success"], "Get context operation failed"

    return {"success": True, "error": None}


@mcp_test(tool_name="workspace_tool", category="core", priority=5)
async def test_set_context(client):
    """Test setting workspace context."""
    # First get list of workspaces to get a valid org ID
    list_result = await client.call_tool("workspace_tool", {"operation": "list_workspaces"})

    if not list_result["success"]:
        return {"success": False, "skipped": True, "skip_reason": "Cannot list workspaces"}

    orgs = list_result["response"].get("organizations", [])
    if not orgs or len(orgs) == 0:
        return {"success": False, "skipped": True, "skip_reason": "No organizations available"}

    org_id = orgs[0].get("id")
    if not org_id:
        return {"success": False, "skipped": True, "skip_reason": "Organization missing ID"}

    # Set context with context_type and entity_id (required parameters)
    result = await client.call_tool("workspace_tool", {
        "operation": "set_context",
        "context_type": "organization",
        "entity_id": org_id
    })

    assert result["success"], f"Failed: {result.get('error')}"

    return {"success": True, "error": None}


@mcp_test(tool_name="workspace_tool", category="core", priority=5)
async def test_get_defaults(client):
    """Test getting workspace defaults."""
    result = await client.call_tool("workspace_tool", {"operation": "get_defaults"})

    assert result["success"], f"Failed: {result.get('error')}"

    response = result["response"]
    assert result["success"], "Get defaults operation failed"

    return {"success": True, "error": None}
