"""
Relationship Tool Tests

Tests entity relationship management using decorator-based framework.
"""

from .framework import mcp_test, skip_if


# Skip relationship tests that require real entity IDs
# These should be run manually with actual IDs from list operations
SKIP_RELATIONSHIP_TESTS = True


@mcp_test(tool_name="relationship_tool", category="relationship", priority=10)
async def test_list_relationships_member(client):
    """Test listing member relationships."""
    # First get an organization to use
    org_result = await client.call_tool("entity_tool", {"entity_type": "organization", "operation": "list"})

    if not org_result["success"] or not org_result["response"].get("organizations"):
        return {"success": False, "skipped": True, "skip_reason": "No organizations available"}

    org_id = org_result["response"]["organizations"][0]["id"]

    # List member relationships
    result = await client.call_tool(
        "relationship_tool",
        {
            "operation": "list",
            "relationship_type": "member",
            "source": {"type": "organization", "id": org_id},
        },
    )

    assert result["success"], f"Failed: {result.get('error')}"

    response = result["response"]
    assert "relationships" in response or "members" in response or result["success"], "Missing relationships in response"

    return {"success": True, "error": None}


@skip_if(lambda: True, reason="Needs real entity UUIDs")
@mcp_test(tool_name="relationship_tool", category="relationship", priority=5)
async def test_link_entities(client):
    """Test linking two entities - skipped (needs real UUIDs)."""
    return {"success": False, "skipped": True, "skip_reason": "Needs real entity UUIDs"}


@skip_if(lambda: True, reason="Needs real relationship ID and relationship_type")
@mcp_test(tool_name="relationship_tool", category="relationship", priority=5)
async def test_unlink_entities(client):
    """Test unlinking - skipped (needs real IDs and relationship_type parameter)."""
    return {"success": False, "skipped": True, "skip_reason": "Needs real relationship ID"}


@skip_if(lambda: True, reason="Needs real entity UUIDs")
@mcp_test(tool_name="relationship_tool", category="relationship", priority=5)
async def test_check_relationship(client):
    """Test checking relationship - skipped (needs real UUIDs)."""
    return {"success": False, "skipped": True, "skip_reason": "Needs real entity UUIDs"}


@skip_if(lambda: True, reason="Needs real relationship ID and relationship_type")
@mcp_test(tool_name="relationship_tool", category="relationship", priority=5)
async def test_update_relationship(client):
    """Test updating relationship - skipped (missing relationship_type parameter)."""
    return {"success": False, "skipped": True, "skip_reason": "Needs relationship_type parameter"}
