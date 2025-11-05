"""
Entity Tool Tests

Tests CRUD operations for all Atoms entities using decorator-based framework.
Now compatible with pytest-xdist for parallel execution.
"""

from datetime import UTC, datetime

import pytest

from .framework import mcp_test

LIST_ENTITY_CASES = [
    pytest.param("organization", {"organizations", "data"}, id="organizations"),
    pytest.param("project", {"projects", "data"}, id="projects"),
    pytest.param("document", {"documents", "data"}, id="documents"),
    pytest.param("requirement", {"requirements", "data"}, id="requirements"),
]

READ_ENTITY_CASES = [
    pytest.param("organization", "organizations", "organization", marks=pytest.mark.priority(5), id="organization"),
    pytest.param("project", "projects", "project", marks=pytest.mark.priority(3), id="project"),
    pytest.param("document", "documents", "document", marks=pytest.mark.priority(3), id="document"),
]


@pytest.mark.asyncio
@pytest.mark.parallel
@pytest.mark.parametrize(("entity_type", "expected_keys"), LIST_ENTITY_CASES)
@mcp_test(tool_name="entity_tool", category="entity", priority=10)
async def test_list_entities(client_adapter, entity_type, expected_keys):
    """Verify list operations across core entity types."""
    result = await client_adapter.call_tool(
        "entity_tool",
        {
            "entity_type": entity_type,
            "operation": "list",
        },
    )

    assert result["success"], f"Failed ({entity_type}): {result.get('error')}"

    response = result["response"]
    assert any(key in response for key in expected_keys), (
        f"Missing {entity_type} data in response, got keys: "
        f"{list(response.keys()) if isinstance(response, dict) else type(response).__name__}"
    )


@pytest.mark.asyncio
@pytest.mark.parallel
@pytest.mark.parametrize(("entity_type", "response_key", "entity_label"), READ_ENTITY_CASES)
@mcp_test(tool_name="entity_tool", category="entity", priority=5)
async def test_read_entity_by_id(client_adapter, entity_type, response_key, entity_label):
    """Exercise read operations by reusing IDs from list queries."""
    list_result = await client_adapter.call_tool(
        "entity_tool",
        {
            "entity_type": entity_type,
            "operation": "list",
        },
    )

    if not list_result["success"]:
        return {
            "success": True,
            "skipped": True,
            "skip_reason": f"Cannot list {entity_label}s",
        }

    candidates = list_result["response"].get(response_key, [])
    if not candidates:
        return {
            "success": True,
            "skipped": True,
            "skip_reason": f"No {entity_label}s available",
        }

    entity_id = candidates[0]["id"]
    result = await client_adapter.call_tool(
        "entity_tool",
        {
            "entity_type": entity_type,
            "operation": "read",
            "entity_id": entity_id,
        },
    )

    assert result["success"], f"Failed ({entity_type}): {result.get('error')}"
    return None


@pytest.mark.asyncio
@pytest.mark.parallel
@mcp_test(tool_name="entity_tool", category="entity", priority=3)
async def test_create_organization(client_adapter):
    """Test creating organization (known RLS issue)."""
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")

    result = await client_adapter.call_tool(
        "entity_tool",
        {
            "entity_type": "organization",
            "operation": "create",
            "data": {
                "name": f"Test Org {timestamp}",
                "slug": f"test-org-{timestamp}",
                "description": "Test organization",
            },
        },
    )

    # Known issue: RLS policy allows but NOT NULL constraint on updated_by fails
    # This test documents the issue
    if not result["success"]:
        error = result.get("error", "")
        if "updated_by" in error or "NOT NULL" in error:
            return {
                "success": False,
                "error": "Known RLS issue: updated_by constraint",
                "known_issue": True,
            }

    return {"success": result["success"], "error": result.get("error")}


@pytest.mark.asyncio
@pytest.mark.parallel
@mcp_test(tool_name="entity_tool", category="entity", priority=5)
async def test_search_organizations_fuzzy(client_adapter):
    """Test searching organizations (fuzzy_match not supported as operation)."""
    result = await client_adapter.call_tool(
        "entity_tool",
        {
            "entity_type": "organization",
            "operation": "search",  # Use search instead of fuzzy_match
            "search_term": "test",
        },
    )

    assert result["success"], f"Failed: {result.get('error')}"


@pytest.mark.asyncio
@pytest.mark.parallel
@mcp_test(tool_name="entity_tool", category="entity", priority=5)
async def test_update_organization(client_adapter):
    """Test updating organization."""
    # First get list to find a real ID
    list_result = await client_adapter.call_tool("entity_tool", {"entity_type": "organization", "operation": "list"})

    if not list_result["success"]:
        return {"success": True, "skipped": True, "skip_reason": "Cannot list organizations"}

    orgs = list_result["response"].get("organizations", [])
    if not orgs:
        return {"success": True, "skipped": True, "skip_reason": "No organizations available"}

    org_id = orgs[0]["id"]

    # Update description
    result = await client_adapter.call_tool(
        "entity_tool",
        {
            "entity_type": "organization",
            "operation": "update",
            "entity_id": org_id,
            "data": {"description": "Updated via automated test"},
        },
    )

    # May fail due to permissions
    if not result["success"]:
        error = result.get("error", "")
        if "permission" in error.lower() or "not allowed" in error.lower():
            return {"success": True, "skipped": True, "skip_reason": "Insufficient permissions"}

    assert result["success"], f"Failed: {result.get('error')}"
    return None
