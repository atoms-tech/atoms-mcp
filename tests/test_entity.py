"""
Entity Tool Tests

Tests CRUD operations for all Atoms entities using decorator-based framework.
"""

from datetime import datetime

from .framework import mcp_test


@mcp_test(tool_name="entity_tool", category="entity", priority=10)
async def test_list_organizations(client):
    """Test listing organizations."""
    result = await client.call_tool("entity_tool", {"entity_type": "organization", "operation": "list"})

    assert result["success"], f"Failed: {result.get('error')}"

    response = result["response"]
    assert "organizations" in response or "data" in response, "Missing organizations in response"

    return {"success": True, "error": None}


@mcp_test(tool_name="entity_tool", category="entity", priority=10)
async def test_list_projects(client):
    """Test listing projects."""
    result = await client.call_tool("entity_tool", {"entity_type": "project", "operation": "list"})

    assert result["success"], f"Failed: {result.get('error')}"

    response = result["response"]
    assert "projects" in response or "data" in response, "Missing projects in response"

    return {"success": True, "error": None}


@mcp_test(tool_name="entity_tool", category="entity", priority=10)
async def test_list_documents(client):
    """Test listing documents."""
    result = await client.call_tool("entity_tool", {"entity_type": "document", "operation": "list"})

    assert result["success"], f"Failed: {result.get('error')}"

    response = result["response"]
    assert "documents" in response or "data" in response, "Missing documents in response"

    return {"success": True, "error": None}


@mcp_test(tool_name="entity_tool", category="entity", priority=10)
async def test_list_requirements(client):
    """Test listing requirements."""
    result = await client.call_tool("entity_tool", {"entity_type": "requirement", "operation": "list"})

    assert result["success"], f"Failed: {result.get('error')}"

    response = result["response"]
    assert "requirements" in response or "data" in response, "Missing requirements in response"

    return {"success": True, "error": None}


@mcp_test(tool_name="entity_tool", category="entity", priority=3)
async def test_create_organization(client):
    """Test creating organization (known RLS issue)."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    result = await client.call_tool(
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


@mcp_test(tool_name="entity_tool", category="entity", priority=5)
async def test_read_organization_by_id(client):
    """Test reading organization by ID."""
    # First get list to find a real ID
    list_result = await client.call_tool("entity_tool", {"entity_type": "organization", "operation": "list"})

    if not list_result["success"]:
        return {"success": False, "skipped": True, "skip_reason": "Cannot list organizations"}

    orgs = list_result["response"].get("organizations", [])
    if not orgs:
        return {"success": False, "skipped": True, "skip_reason": "No organizations available"}

    org_id = orgs[0]["id"]

    # Now read by ID
    result = await client.call_tool(
        "entity_tool",
        {
            "entity_type": "organization",
            "operation": "read",
            "entity_id": org_id,
        },
    )

    assert result["success"], f"Failed: {result.get('error')}"

    return {"success": True, "error": None}


@mcp_test(tool_name="entity_tool", category="entity", priority=5)
async def test_search_organizations_fuzzy(client):
    """Test searching organizations (fuzzy_match not supported as operation)."""
    result = await client.call_tool(
        "entity_tool",
        {
            "entity_type": "organization",
            "operation": "search",  # Use search instead of fuzzy_match
            "search_term": "test",
        },
    )

    assert result["success"], f"Failed: {result.get('error')}"

    return {"success": True, "error": None}


@mcp_test(tool_name="entity_tool", category="entity", priority=5)
async def test_update_organization(client):
    """Test updating organization."""
    # First get list to find a real ID
    list_result = await client.call_tool("entity_tool", {"entity_type": "organization", "operation": "list"})

    if not list_result["success"]:
        return {"success": False, "skipped": True, "skip_reason": "Cannot list organizations"}

    orgs = list_result["response"].get("organizations", [])
    if not orgs:
        return {"success": False, "skipped": True, "skip_reason": "No organizations available"}

    org_id = orgs[0]["id"]

    # Update description
    result = await client.call_tool(
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
            return {"success": False, "skipped": True, "skip_reason": "Insufficient permissions"}

    assert result["success"], f"Failed: {result.get('error')}"

    return {"success": True, "error": None}


@mcp_test(tool_name="entity_tool", category="entity", priority=3)
async def test_read_project_by_id(client):
    """Test reading project by ID."""
    # Get list of projects
    list_result = await client.call_tool("entity_tool", {"entity_type": "project", "operation": "list"})

    if not list_result["success"]:
        return {"success": False, "skipped": True, "skip_reason": "Cannot list projects"}

    projects = list_result["response"].get("projects", [])
    if not projects:
        return {"success": False, "skipped": True, "skip_reason": "No projects available"}

    project_id = projects[0]["id"]

    # Read by ID
    result = await client.call_tool(
        "entity_tool",
        {
            "entity_type": "project",
            "operation": "read",
            "entity_id": project_id,
        },
    )

    assert result["success"], f"Failed: {result.get('error')}"

    return {"success": True, "error": None}


@mcp_test(tool_name="entity_tool", category="entity", priority=3)
async def test_read_document_by_id(client):
    """Test reading document by ID."""
    # Get list of documents
    list_result = await client.call_tool("entity_tool", {"entity_type": "document", "operation": "list"})

    if not list_result["success"]:
        return {"success": False, "skipped": True, "skip_reason": "Cannot list documents"}

    documents = list_result["response"].get("documents", [])
    if not documents:
        return {"success": False, "skipped": True, "skip_reason": "No documents available"}

    doc_id = documents[0]["id"]

    # Read by ID
    result = await client.call_tool(
        "entity_tool",
        {
            "entity_type": "document",
            "operation": "read",
            "entity_id": doc_id,
        },
    )

    assert result["success"], f"Failed: {result.get('error')}"

    return {"success": True, "error": None}
