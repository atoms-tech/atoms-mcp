"""
Relationship Tool Tests

Tests entity relationship management using decorator-based framework.
Now compatible with pytest-xdist for parallel execution.
"""

import pytest

from .framework import EntityFactory, mcp_test


@pytest.fixture
async def test_entities(client_adapter):
    """Create test entities for relationship operations."""
    # Create organization
    org_data = EntityFactory.organization()
    org_result = await client_adapter.call_tool(
        "entity_tool", {"entity_type": "organization", "operation": "create", "data": org_data}
    )

    if not org_result["success"]:
        pytest.skip("Failed to create test organization")

    org_id = org_result["response"]["organization"]["id"]

    # Create project
    project_data = EntityFactory.project(organization_id=org_id)
    project_result = await client_adapter.call_tool(
        "entity_tool", {"entity_type": "project", "operation": "create", "data": project_data}
    )

    if not project_result["success"]:
        pytest.skip("Failed to create test project")

    project_id = project_result["response"]["project"]["id"]

    # Create document
    doc_data = EntityFactory.document(project_id=project_id)
    doc_result = await client_adapter.call_tool(
        "entity_tool", {"entity_type": "document", "operation": "create", "data": doc_data}
    )

    if not doc_result["success"]:
        pytest.skip("Failed to create test document")

    doc_id = doc_result["response"]["document"]["id"]

    return {"organization_id": org_id, "project_id": project_id, "document_id": doc_id}


@pytest.mark.asyncio
@pytest.mark.parallel
@mcp_test(tool_name="relationship_tool", category="relationship", priority=10)
async def test_list_relationships_member(client_adapter, test_entities):
    """Test listing member relationships."""
    org_id = test_entities["organization_id"]

    result = await client_adapter.call_tool(
        "relationship_tool",
        {
            "operation": "list",
            "relationship_type": "member",
            "source": {"type": "organization", "id": org_id},
        },
    )

    assert result["success"], f"Failed: {result.get('error')}"
    response = result["response"]
    assert "relationships" in response or "members" in response, "Missing relationships in response"


@pytest.mark.asyncio
@pytest.mark.parallel
@mcp_test(tool_name="relationship_tool", category="relationship", priority=8)
async def test_link_entities(client_adapter, test_entities):
    """Test linking two entities."""
    org_id = test_entities["organization_id"]
    project_id = test_entities["project_id"]

    result = await client_adapter.call_tool(
        "relationship_tool",
        {
            "operation": "link",
            "relationship_type": "contains",
            "source": {"type": "organization", "id": org_id},
            "target": {"type": "project", "id": project_id},
        },
    )

    assert result["success"], f"Failed: {result.get('error')}"
    response = result["response"]
    assert "relationship" in response, "Missing relationship in response"


@pytest.mark.asyncio
@pytest.mark.parallel
@mcp_test(tool_name="relationship_tool", category="relationship", priority=7)
async def test_check_relationship(client_adapter, test_entities):
    """Test checking if relationship exists."""
    org_id = test_entities["organization_id"]
    project_id = test_entities["project_id"]

    result = await client_adapter.call_tool(
        "relationship_tool",
        {
            "operation": "check",
            "relationship_type": "contains",
            "source": {"type": "organization", "id": org_id},
            "target": {"type": "project", "id": project_id},
        },
    )

    assert result["success"], f"Failed: {result.get('error')}"
    response = result["response"]
    assert "exists" in response, "Missing exists field in response"


@pytest.mark.asyncio
@pytest.mark.parallel
@mcp_test(tool_name="relationship_tool", category="relationship", priority=6)
async def test_unlink_entities(client_adapter, test_entities):
    """Test unlinking entities."""
    org_id = test_entities["organization_id"]
    project_id = test_entities["project_id"]

    # First create a relationship
    link_result = await client_adapter.call_tool(
        "relationship_tool",
        {
            "operation": "link",
            "relationship_type": "contains",
            "source": {"type": "organization", "id": org_id},
            "target": {"type": "project", "id": project_id},
        },
    )

    if not link_result["success"]:
        pytest.skip("Failed to create relationship for unlink test")

    # Now unlink it
    result = await client_adapter.call_tool(
        "relationship_tool",
        {
            "operation": "unlink",
            "relationship_type": "contains",
            "source": {"type": "organization", "id": org_id},
            "target": {"type": "project", "id": project_id},
        },
    )

    assert result["success"], f"Failed: {result.get('error')}"
    response = result["response"]
    assert "unlinked" in response or "success" in response, "Missing unlink confirmation in response"
