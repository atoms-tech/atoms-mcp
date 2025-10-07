"""
Comprehensive Entity Operations Test Suite
Tests all entity types with systematic coverage of operations and variations
"""

import pytest
from typing import Dict, Any, List
from tests.framework import mcp_test, DataGenerator, validators
from tests.framework.validators import ResponseValidator


# ==================== ORGANIZATION TESTS ====================

# --- List Operations ---
@mcp_test(tool_name="entity_tool", category="entity_list", priority=8)
async def test_list_organizations_basic(client):
    """Test basic organization listing"""
    result = await client.call_tool("entity_tool", {
        "entity_type": "organization",
        "operation": "list"
    })
    assert result["success"]
    assert isinstance(result["response"], list)
    return {"success": True}


@mcp_test(tool_name="entity_tool", category="entity_list", priority=7)
async def test_list_organizations_limit_10(client):
    """Test organization listing with limit=10"""
    result = await client.call_tool("entity_tool", {
        "entity_type": "organization",
        "operation": "list",
        "limit": 10
    })
    assert result["success"]
    assert len(result["response"]) <= 10
    return {"success": True}


@mcp_test(tool_name="entity_tool", category="entity_list", priority=7)
async def test_list_organizations_limit_50(client):
    """Test organization listing with limit=50"""
    result = await client.call_tool("entity_tool", {
        "entity_type": "organization",
        "operation": "list",
        "limit": 50
    })
    assert result["success"]
    assert len(result["response"]) <= 50
    return {"success": True}


@mcp_test(tool_name="entity_tool", category="entity_list", priority=7)
async def test_list_organizations_with_parent_filter(client):
    """Test organization listing with parent filter"""
    parent_id = DataGenerator.uuid()
    result = await client.call_tool("entity_tool", {
        "entity_type": "organization",
        "operation": "list",
        "parent_id": parent_id
    })
    assert result["success"]
    assert isinstance(result["response"], list)
    return {"success": True}


# --- Create Operations ---
@mcp_test(tool_name="entity_tool", category="entity_create", priority=9)
async def test_create_organization_basic(client):
    """Test basic organization creation"""
    data = DataGenerator.organization_data()
    result = await client.call_tool("entity_tool", {
        "entity_type": "organization",
        "operation": "create",
        "data": data
    })
    assert result["success"]
    assert validators.FieldValidator.is_uuid(result["response"].get("id"))
    assert result["response"]["name"] == data["name"]
    return {"success": True, "entity_id": result["response"]["id"]}


@mcp_test(tool_name="entity_tool", category="entity_create", priority=8)
async def test_create_organization_batch(client):
    """Test batch organization creation (3 items)"""
    organizations = []
    for i in range(3):
        data = DataGenerator.organization_data()
        result = await client.call_tool("entity_tool", {
            "entity_type": "organization",
            "operation": "create",
            "data": data
        })
        assert result["success"]
        organizations.append(result["response"]["id"])
    assert len(organizations) == 3
    return {"success": True, "entity_ids": organizations}


# --- Read Operations ---
@mcp_test(tool_name="entity_tool", category="entity_read", priority=8)
async def test_read_organization_by_id(client):
    """Test reading organization by ID - creates test data first"""
    # Step 1: CREATE test organization (with auto-skip if fails)
    entity_id = await ResponseValidator.create_test_entity(
        client,
        "organization",
        DataGenerator.organization_data
    )

    if not entity_id:
        return {"success": False, "error": "Create failed", "skipped": True}

    try:
        # Step 2: READ the created organization
        result = await client.call_tool("entity_tool", {
            "entity_type": "organization",
            "operation": "read",
            "entity_id": entity_id
        })

        # Step 3: Verify read succeeded
        assert result["success"], f"Read failed: {result.get('error')}"

        return {"success": True}

    finally:
        # Step 4: Always DELETE test data (cleanup)
        await client.call_tool("entity_tool", {
            "entity_type": "organization",
            "operation": "delete",
            "entity_id": entity_id
        })


@mcp_test(tool_name="entity_tool", category="entity_read", priority=7)
async def test_read_organization_with_relations(client):
    """Test reading organization with relations - creates test data first"""
    # Step 1: CREATE test organization (with auto-skip if fails)
    entity_id = await ResponseValidator.create_test_entity(
        client,
        "organization",
        DataGenerator.organization_data
    )

    if not entity_id:
        return {"success": False, "error": "Create failed", "skipped": True}

    try:
        # Step 2: READ with relations
        result = await client.call_tool("entity_tool", {
            "entity_type": "organization",
            "operation": "read",
            "entity_id": entity_id,
            "include_relations": True
        })

        # Step 3: Verify read succeeded
        assert result["success"], f"Read with relations failed: {result.get('error')}"
        assert "relations" in result["response"] or "projects" in result["response"]

        return {"success": True}

    finally:
        # Step 4: Always DELETE test data (cleanup)
        await client.call_tool("entity_tool", {
            "entity_type": "organization",
            "operation": "delete",
            "entity_id": entity_id
        })


# --- Update Operations ---
@mcp_test(tool_name="entity_tool", category="entity_update", priority=7)
async def test_update_organization_single_field(client):
    """Test updating single field of organization"""
    # CREATE test entity (with auto-skip if fails)
    entity_id = await ResponseValidator.create_test_entity(
        client, "organization", DataGenerator.organization_data
    )

    if not entity_id:
        return {"success": False, "error": "Create failed", "skipped": True}

    try:
        # UPDATE single field
        new_name = "Updated Test Org"
        result = await client.call_tool("entity_tool", {
            "entity_type": "organization",
            "operation": "update",
            "entity_id": entity_id,
            "data": {"name": new_name}
        })
        assert result["success"], f"Update failed: {result.get('error')}"
        return {"success": True}

    finally:
        # DELETE cleanup
        await client.call_tool("entity_tool", {
            "entity_type": "organization",
            "operation": "delete",
            "entity_id": entity_id
        })


# --- Delete Operations ---
@mcp_test(tool_name="entity_tool", category="entity_delete", priority=6)
async def test_delete_organization_soft(client):
    """Test soft delete of organization"""
    # CREATE test entity (with auto-skip if fails)
    entity_id = await ResponseValidator.create_test_entity(
        client, "organization", DataGenerator.organization_data
    )

    if not entity_id:
        return {"success": False, "error": "Create failed", "skipped": True}

    # DELETE (soft delete is the actual test, no cleanup needed)
    result = await client.call_tool("entity_tool", {
        "entity_type": "organization",
        "operation": "delete",
        "entity_id": entity_id
    })
    assert result["success"], f"Delete failed: {result.get('error')}"
    return {"success": True}


# --- Search Operations ---
@mcp_test(tool_name="entity_tool", category="entity_search", priority=7)
async def test_fuzzy_match_organization(client):
    """Test fuzzy matching for organizations"""
    result = await client.call_tool("entity_tool", {
        "entity_type": "organization",
        "operation": "search",
        "search_term": "test"
    })
    assert result["success"]
    assert isinstance(result["response"], list)
    return {"success": True}


@mcp_test(tool_name="entity_tool", category="entity_search", priority=7)
async def test_search_organization_with_filters(client):
    """Test searching organizations with filters"""
    result = await client.call_tool("entity_tool", {
        "entity_type": "organization",
        "operation": "search",
        "filters": {
            "status": "active",
            "type": "enterprise"
        }
    })
    assert result["success"]
    assert isinstance(result["response"], list)
    return {"success": True}


# --- Format Variations ---









# --- Error Cases ---
@mcp_test(tool_name="entity_tool", category="entity_errors", priority=5)
async def test_create_organization_missing_required_fields(client):
    """Test organization creation with missing required fields"""
    result = await client.call_tool("entity_tool", {
        "entity_type": "organization",
        "operation": "create",
        "data": {}  # Missing required fields
    })
    assert not result["success"]
    assert "error" in result
    return {"success": True}


@mcp_test(tool_name="entity_tool", category="entity_errors", priority=5)
async def test_read_organization_invalid_id(client):
    """Test reading organization with invalid ID"""
    result = await client.call_tool("entity_tool", {
        "entity_type": "organization",
        "operation": "read",
        "entity_id": "invalid-id-123"
    })
    assert not result["success"]
    assert "error" in result
    return {"success": True}


@mcp_test(tool_name="entity_tool", category="entity_errors", priority=5)
async def test_access_deleted_organization(client):
    """Test accessing deleted organization"""
    # Create and delete
    data = DataGenerator.organization_data()
    create_result = await client.call_tool("entity_tool", {
        "entity_type": "organization",
        "operation": "create",
        "data": data
    })
    entity_id = ResponseValidator.extract_id(create_result["response"])

    await client.call_tool("entity_tool", {
        "entity_type": "organization",
        "operation": "delete",
        "entity_id": entity_id,
        "soft_delete": True
    })

    # Try to access deleted entity
    result = await client.call_tool("entity_tool", {
        "entity_type": "organization",
        "operation": "read",
        "entity_id": entity_id
    })
    assert not result["success"] or result["response"].get("deleted") == True
    return {"success": True}


# ==================== PROJECT TESTS ====================

# --- List Operations ---
@mcp_test(tool_name="entity_tool", category="entity_list", priority=8)
async def test_list_projects_basic(client):
    """Test basic project listing"""
    result = await client.call_tool("entity_tool", {
        "entity_type": "project",
        "operation": "list"
    })
    assert result["success"]
    assert isinstance(result["response"], list)
    return {"success": True}


@mcp_test(tool_name="entity_tool", category="entity_list", priority=7)
async def test_list_projects_limit_10(client):
    """Test project listing with limit=10"""
    result = await client.call_tool("entity_tool", {
        "entity_type": "project",
        "operation": "list",
        "limit": 10
    })
    assert result["success"]
    assert len(result["response"]) <= 10
    return {"success": True}


@mcp_test(tool_name="entity_tool", category="entity_list", priority=7)
async def test_list_projects_limit_50(client):
    """Test project listing with limit=50"""
    result = await client.call_tool("entity_tool", {
        "entity_type": "project",
        "operation": "list",
        "limit": 50
    })
    assert result["success"]
    assert len(result["response"]) <= 50
    return {"success": True}


@mcp_test(tool_name="entity_tool", category="entity_list", priority=7)
async def test_list_projects_with_parent_filter(client):
    """Test project listing with parent filter"""
    parent_id = DataGenerator.uuid()
    result = await client.call_tool("entity_tool", {
        "entity_type": "project",
        "operation": "list",
        "parent_id": parent_id
    })
    assert result["success"]
    assert isinstance(result["response"], list)
    return {"success": True}


# --- Create Operations ---
@mcp_test(tool_name="entity_tool", category="entity_create", priority=9)
async def test_create_project_basic(client):
    """Test basic project creation"""
    data = DataGenerator.project_data()
    result = await client.call_tool("entity_tool", {
        "entity_type": "project",
        "operation": "create",
        "data": data
    })
    assert result["success"]
    assert validators.FieldValidator.is_uuid(result["response"].get("id"))
    assert result["response"]["name"] == data["name"]
    return {"success": True, "entity_id": result["response"]["id"]}


@mcp_test(tool_name="entity_tool", category="entity_create", priority=8)
async def test_create_project_batch(client):
    """Test batch project creation (3 items)"""
    projects = []
    for i in range(3):
        data = DataGenerator.project_data()
        result = await client.call_tool("entity_tool", {
            "entity_type": "project",
            "operation": "create",
            "data": data
        })
        assert result["success"]
        projects.append(result["response"]["id"])
    assert len(projects) == 3
    return {"success": True, "entity_ids": projects}


# --- Read Operations ---
@mcp_test(tool_name="entity_tool", category="entity_read", priority=8)
async def test_read_project_by_id(client):
    """Test reading project by ID - creates test data first"""
    # Step 1: CREATE test project (with auto-skip if fails)
    entity_id = await ResponseValidator.create_test_entity(
        client,
        "project",
        DataGenerator.project_data
    )

    if not entity_id:
        return {"success": False, "error": "Create failed", "skipped": True}

    try:
        # Step 2: READ the created project
        result = await client.call_tool("entity_tool", {
            "entity_type": "project",
            "operation": "read",
            "entity_id": entity_id
        })

        # Step 3: Verify read succeeded
        assert result["success"], f"Read failed: {result.get('error')}"

        return {"success": True}

    finally:
        # Step 4: Always DELETE test data (cleanup)
        await client.call_tool("entity_tool", {
            "entity_type": "project",
            "operation": "delete",
            "entity_id": entity_id
        })


@mcp_test(tool_name="entity_tool", category="entity_read", priority=7)
async def test_read_project_with_relations(client):
    """Test reading project with relations - creates test data first"""
    # Step 1: CREATE test project (with auto-skip if fails)
    entity_id = await ResponseValidator.create_test_entity(
        client,
        "project",
        DataGenerator.project_data
    )

    if not entity_id:
        return {"success": False, "error": "Create failed", "skipped": True}

    try:
        # Step 2: READ with relations
        result = await client.call_tool("entity_tool", {
            "entity_type": "project",
            "operation": "read",
            "entity_id": entity_id,
            "include_relations": True
        })

        # Step 3: Verify read succeeded
        assert result["success"], f"Read with relations failed: {result.get('error')}"
        assert "relations" in result["response"] or "documents" in result["response"]

        return {"success": True}

    finally:
        # Step 4: Always DELETE test data (cleanup)
        await client.call_tool("entity_tool", {
            "entity_type": "project",
            "operation": "delete",
            "entity_id": entity_id
        })


# --- Update Operations ---
@mcp_test(tool_name="entity_tool", category="entity_update", priority=7)
async def test_update_project_single_field(client):
    """Test updating single field of project"""
    entity_id = await ResponseValidator.create_test_entity(
        client, "project", DataGenerator.project_data
    )
    if not entity_id:
        return {"success": False, "error": "Create failed", "skipped": True}
    try:
        result = await client.call_tool("entity_tool", {
            "entity_type": "project",
            "operation": "update",
            "entity_id": entity_id,
            "data": {"name": "Updated Test Project"}
        })
        assert result["success"]
        return {"success": True}
    finally:
        await client.call_tool("entity_tool", {
            "entity_type": "project",
            "operation": "delete",
            "entity_id": entity_id
        })


# --- Delete Operations ---
@mcp_test(tool_name="entity_tool", category="entity_delete", priority=6)
async def test_delete_project_soft(client):
    """Test soft delete of project"""
    entity_id = await ResponseValidator.create_test_entity(
        client, "project", DataGenerator.project_data
    )
    if not entity_id:
        return {"success": False, "error": "Create failed", "skipped": True}
    result = await client.call_tool("entity_tool", {
        "entity_type": "project",
        "operation": "delete",
        "entity_id": entity_id
    })
    assert result["success"]
    return {"success": True}


# --- Search Operations ---
@mcp_test(tool_name="entity_tool", category="entity_search", priority=7)
async def test_fuzzy_match_project(client):
    """Test fuzzy matching for projects"""
    result = await client.call_tool("entity_tool", {
        "entity_type": "project",
        "operation": "search",
        "search_term": "test"
    })
    assert result["success"]
    assert isinstance(result["response"], list)
    return {"success": True}


@mcp_test(tool_name="entity_tool", category="entity_search", priority=7)
async def test_search_project_with_filters(client):
    """Test searching projects with filters"""
    result = await client.call_tool("entity_tool", {
        "entity_type": "project",
        "operation": "search",
        "filters": {
            "status": "active",
            "priority": "high"
        }
    })
    assert result["success"]
    assert isinstance(result["response"], list)
    return {"success": True}


# --- Format Variations ---









# --- Error Cases ---
@mcp_test(tool_name="entity_tool", category="entity_errors", priority=5)
async def test_create_project_missing_required_fields(client):
    """Test project creation with missing required fields"""
    result = await client.call_tool("entity_tool", {
        "entity_type": "project",
        "operation": "create",
        "data": {}  # Missing required fields
    })
    assert not result["success"]
    assert "error" in result
    return {"success": True}


@mcp_test(tool_name="entity_tool", category="entity_errors", priority=5)
async def test_read_project_invalid_id(client):
    """Test reading project with invalid ID"""
    result = await client.call_tool("entity_tool", {
        "entity_type": "project",
        "operation": "read",
        "entity_id": "invalid-id-456"
    })
    assert not result["success"]
    assert "error" in result
    return {"success": True}


@mcp_test(tool_name="entity_tool", category="entity_errors", priority=5)
async def test_access_deleted_project(client):
    """Test accessing deleted project"""
    # Create and delete
    data = DataGenerator.project_data()
    create_result = await client.call_tool("entity_tool", {
        "entity_type": "project",
        "operation": "create",
        "data": data
    })
    entity_id = ResponseValidator.extract_id(create_result["response"])

    await client.call_tool("entity_tool", {
        "entity_type": "project",
        "operation": "delete",
        "entity_id": entity_id,
        "soft_delete": True
    })

    # Try to access deleted entity
    result = await client.call_tool("entity_tool", {
        "entity_type": "project",
        "operation": "read",
        "entity_id": entity_id
    })
    assert not result["success"] or result["response"].get("deleted") == True
    return {"success": True}


# ==================== DOCUMENT TESTS ====================

# --- List Operations ---
@mcp_test(tool_name="entity_tool", category="entity_list", priority=8)
async def test_list_documents_basic(client):
    """Test basic document listing"""
    result = await client.call_tool("entity_tool", {
        "entity_type": "document",
        "operation": "list"
    })
    assert result["success"]
    assert isinstance(result["response"], list)
    return {"success": True}


@mcp_test(tool_name="entity_tool", category="entity_list", priority=7)
async def test_list_documents_limit_10(client):
    """Test document listing with limit=10"""
    result = await client.call_tool("entity_tool", {
        "entity_type": "document",
        "operation": "list",
        "limit": 10
    })
    assert result["success"]
    assert len(result["response"]) <= 10
    return {"success": True}


@mcp_test(tool_name="entity_tool", category="entity_list", priority=7)
async def test_list_documents_limit_50(client):
    """Test document listing with limit=50"""
    result = await client.call_tool("entity_tool", {
        "entity_type": "document",
        "operation": "list",
        "limit": 50
    })
    assert result["success"]
    assert len(result["response"]) <= 50
    return {"success": True}


@mcp_test(tool_name="entity_tool", category="entity_list", priority=7)
async def test_list_documents_with_parent_filter(client):
    """Test document listing with parent filter"""
    parent_id = DataGenerator.uuid()
    result = await client.call_tool("entity_tool", {
        "entity_type": "document",
        "operation": "list",
        "parent_id": parent_id
    })
    assert result["success"]
    assert isinstance(result["response"], list)
    return {"success": True}


# --- Create Operations ---
@mcp_test(tool_name="entity_tool", category="entity_create", priority=9)
async def test_create_document_basic(client):
    """Test basic document creation"""
    data = DataGenerator.document_data()
    result = await client.call_tool("entity_tool", {
        "entity_type": "document",
        "operation": "create",
        "data": data
    })
    assert result["success"]
    assert validators.FieldValidator.is_uuid(result["response"].get("id"))
    assert result["response"]["title"] == data["title"]
    return {"success": True, "entity_id": result["response"]["id"]}


@mcp_test(tool_name="entity_tool", category="entity_create", priority=8)
async def test_create_document_batch(client):
    """Test batch document creation (3 items)"""
    documents = []
    for i in range(3):
        data = DataGenerator.document_data()
        result = await client.call_tool("entity_tool", {
            "entity_type": "document",
            "operation": "create",
            "data": data
        })
        assert result["success"]
        documents.append(result["response"]["id"])
    assert len(documents) == 3
    return {"success": True, "entity_ids": documents}


# --- Read Operations ---
@mcp_test(tool_name="entity_tool", category="entity_read", priority=8)
async def test_read_document_by_id(client):
    """Test reading document by ID - creates test data first"""
    # Step 1: CREATE test document (with auto-skip if fails)
    # Helper automatically: 1) gets/creates org, 2) gets/creates project, 3) creates document
    entity_id = await ResponseValidator.create_test_entity(
        client,
        "document",
        DataGenerator.document_data
    )

    if not entity_id:
        return {"success": False, "error": "Create failed", "skipped": True}

    try:
        # Step 2: READ the created document
        result = await client.call_tool("entity_tool", {
            "entity_type": "document",
            "operation": "read",
            "entity_id": entity_id
        })

        # Step 3: Verify read succeeded
        assert result["success"], f"Read failed: {result.get('error')}"
        assert result["response"]["id"] == entity_id

        return {"success": True}

    finally:
        # Step 4: Always DELETE test data (cleanup)
        await client.call_tool("entity_tool", {
            "entity_type": "document",
            "operation": "delete",
            "entity_id": entity_id
        })


@mcp_test(tool_name="entity_tool", category="entity_read", priority=7)
async def test_read_document_with_relations(client):
    """Test reading document with relations - creates test data first"""
    # Step 1: CREATE test document (with auto-skip if fails)
    entity_id = await ResponseValidator.create_test_entity(
        client,
        "document",
        DataGenerator.document_data
    )

    if not entity_id:
        return {"success": False, "error": "Create failed", "skipped": True}

    try:
        # Step 2: READ the created document with relations
        result = await client.call_tool("entity_tool", {
            "entity_type": "document",
            "operation": "read",
            "entity_id": entity_id,
            "include_relations": True
        })

        # Step 3: Verify read succeeded
        assert result["success"], f"Read failed: {result.get('error')}"
        assert "relations" in result["response"] or "attachments" in result["response"]

        return {"success": True}

    finally:
        # Step 4: Always DELETE test data (cleanup)
        await client.call_tool("entity_tool", {
            "entity_type": "document",
            "operation": "delete",
            "entity_id": entity_id
        })


# --- Update Operations ---
@mcp_test(tool_name="entity_tool", category="entity_update", priority=7)
async def test_update_document_single_field(client):
    """Test updating single field of document"""
    # CREATE test entity (with auto-skip if fails)
    entity_id = await ResponseValidator.create_test_entity(
        client, "document", DataGenerator.document_data
    )

    if not entity_id:
        return {"success": False, "error": "Create failed", "skipped": True}

    try:
        # UPDATE single field
        new_title = "Updated Test Document"
        result = await client.call_tool("entity_tool", {
            "entity_type": "document",
            "operation": "update",
            "entity_id": entity_id,
            "data": {"title": new_title}
        })
        assert result["success"], f"Update failed: {result.get('error')}"
        return {"success": True}

    finally:
        # DELETE cleanup
        await client.call_tool("entity_tool", {
            "entity_type": "document",
            "operation": "delete",
            "entity_id": entity_id
        })


# --- Delete Operations ---
@mcp_test(tool_name="entity_tool", category="entity_delete", priority=6)
async def test_delete_document_soft(client):
    """Test soft delete of document"""
    # CREATE test entity (with auto-skip if fails)
    entity_id = await ResponseValidator.create_test_entity(
        client, "document", DataGenerator.document_data
    )

    if not entity_id:
        return {"success": False, "error": "Create failed", "skipped": True}

    # DELETE (soft delete is the actual test, no cleanup needed)
    result = await client.call_tool("entity_tool", {
        "entity_type": "document",
        "operation": "delete",
        "entity_id": entity_id,
        "soft_delete": True
    })
    assert result["success"], f"Delete failed: {result.get('error')}"
    return {"success": True}


# --- Search Operations ---
@mcp_test(tool_name="entity_tool", category="entity_search", priority=7)
async def test_fuzzy_match_document(client):
    """Test fuzzy matching for documents"""
    result = await client.call_tool("entity_tool", {
        "entity_type": "document",
        "operation": "search",
        "search_term": "test"
    })
    assert result["success"]
    assert isinstance(result["response"], list)
    return {"success": True}


@mcp_test(tool_name="entity_tool", category="entity_search", priority=7)
async def test_search_document_with_filters(client):
    """Test searching documents with filters"""
    result = await client.call_tool("entity_tool", {
        "entity_type": "document",
        "operation": "search",
        "filters": {
            "type": "specification",
            "status": "draft"
        }
    })
    assert result["success"]
    assert isinstance(result["response"], list)
    return {"success": True}


# --- Format Variations ---









# --- Error Cases ---
@mcp_test(tool_name="entity_tool", category="entity_errors", priority=5)
async def test_create_document_missing_required_fields(client):
    """Test document creation with missing required fields"""
    result = await client.call_tool("entity_tool", {
        "entity_type": "document",
        "operation": "create",
        "data": {}  # Missing required fields
    })
    assert not result["success"]
    assert "error" in result
    return {"success": True}


@mcp_test(tool_name="entity_tool", category="entity_errors", priority=5)
async def test_read_document_invalid_id(client):
    """Test reading document with invalid ID"""
    result = await client.call_tool("entity_tool", {
        "entity_type": "document",
        "operation": "read",
        "entity_id": "invalid-id-789"
    })
    assert not result["success"]
    assert "error" in result
    return {"success": True}


@mcp_test(tool_name="entity_tool", category="entity_errors", priority=5)
async def test_access_deleted_document(client):
    """Test accessing deleted document"""
    # Create and delete
    data = DataGenerator.document_data()
    create_result = await client.call_tool("entity_tool", {
        "entity_type": "document",
        "operation": "create",
        "data": data
    })
    entity_id = ResponseValidator.extract_id(create_result["response"])

    await client.call_tool("entity_tool", {
        "entity_type": "document",
        "operation": "delete",
        "entity_id": entity_id,
        "soft_delete": True
    })

    # Try to access deleted entity
    result = await client.call_tool("entity_tool", {
        "entity_type": "document",
        "operation": "read",
        "entity_id": entity_id
    })
    assert not result["success"] or result["response"].get("deleted") == True
    return {"success": True}


# ==================== REQUIREMENT TESTS ====================

# --- List Operations ---
@mcp_test(tool_name="entity_tool", category="entity_list", priority=8)
async def test_list_requirements_basic(client):
    """Test basic requirement listing"""
    result = await client.call_tool("entity_tool", {
        "entity_type": "requirement",
        "operation": "list"
    })
    assert result["success"]
    assert isinstance(result["response"], list)
    return {"success": True}


@mcp_test(tool_name="entity_tool", category="entity_list", priority=7)
async def test_list_requirements_limit_10(client):
    """Test requirement listing with limit=10"""
    result = await client.call_tool("entity_tool", {
        "entity_type": "requirement",
        "operation": "list",
        "limit": 10
    })
    assert result["success"]
    assert len(result["response"]) <= 10
    return {"success": True}


@mcp_test(tool_name="entity_tool", category="entity_list", priority=7)
async def test_list_requirements_limit_50(client):
    """Test requirement listing with limit=50"""
    result = await client.call_tool("entity_tool", {
        "entity_type": "requirement",
        "operation": "list",
        "limit": 50
    })
    assert result["success"]
    assert len(result["response"]) <= 50
    return {"success": True}


@mcp_test(tool_name="entity_tool", category="entity_list", priority=7)
async def test_list_requirements_with_parent_filter(client):
    """Test requirement listing with parent filter"""
    parent_id = DataGenerator.uuid()
    result = await client.call_tool("entity_tool", {
        "entity_type": "requirement",
        "operation": "list",
        "parent_id": parent_id
    })
    assert result["success"]
    assert isinstance(result["response"], list)
    return {"success": True}


# --- Create Operations ---
@mcp_test(tool_name="entity_tool", category="entity_create", priority=9)
async def test_create_requirement_basic(client):
    """Test basic requirement creation"""
    data = DataGenerator.requirement_data()
    result = await client.call_tool("entity_tool", {
        "entity_type": "requirement",
        "operation": "create",
        "data": data
    })
    assert result["success"]
    assert validators.FieldValidator.is_uuid(result["response"].get("id"))
    assert result["response"]["title"] == data["title"]
    return {"success": True, "entity_id": result["response"]["id"]}


@mcp_test(tool_name="entity_tool", category="entity_create", priority=8)
async def test_create_requirement_batch(client):
    """Test batch requirement creation (3 items)"""
    requirements = []
    for i in range(3):
        data = DataGenerator.requirement_data()
        result = await client.call_tool("entity_tool", {
            "entity_type": "requirement",
            "operation": "create",
            "data": data
        })
        assert result["success"]
        requirements.append(result["response"]["id"])
    assert len(requirements) == 3
    return {"success": True, "entity_ids": requirements}


# --- Read Operations ---
@mcp_test(tool_name="entity_tool", category="entity_read", priority=8)
async def test_read_requirement_by_id(client):
    """Test reading requirement by ID - creates test data first"""
    # Step 1: CREATE test requirement (with auto-skip if fails)
    entity_id = await ResponseValidator.create_test_entity(
        client,
        "requirement",
        DataGenerator.requirement_data
    )

    if not entity_id:
        return {"success": False, "error": "Create failed", "skipped": True}

    try:
        # Step 2: READ the created requirement
        result = await client.call_tool("entity_tool", {
            "entity_type": "requirement",
            "operation": "read",
            "entity_id": entity_id
        })

        # Step 3: Verify read succeeded
        assert result["success"], f"Read failed: {result.get('error')}"

        return {"success": True}

    finally:
        # Step 4: Always DELETE test data (cleanup)
        await client.call_tool("entity_tool", {
            "entity_type": "requirement",
            "operation": "delete",
            "entity_id": entity_id
        })


@mcp_test(tool_name="entity_tool", category="entity_read", priority=7)
async def test_read_requirement_with_relations(client):
    """Test reading requirement with relations - creates test data first"""
    # Step 1: CREATE test requirement (with auto-skip if fails)
    entity_id = await ResponseValidator.create_test_entity(
        client,
        "requirement",
        DataGenerator.requirement_data
    )

    if not entity_id:
        return {"success": False, "error": "Create failed", "skipped": True}

    try:
        # Step 2: READ the created requirement with relations
        result = await client.call_tool("entity_tool", {
            "entity_type": "requirement",
            "operation": "read",
            "entity_id": entity_id,
            "include_relations": True
        })

        # Step 3: Verify read succeeded
        assert result["success"], f"Read failed: {result.get('error')}"
        assert "relations" in result["response"] or "tests" in result["response"]

        return {"success": True}

    finally:
        # Step 4: Always DELETE test data (cleanup)
        await client.call_tool("entity_tool", {
            "entity_type": "requirement",
            "operation": "delete",
            "entity_id": entity_id
        })


# --- Update Operations ---
@mcp_test(tool_name="entity_tool", category="entity_update", priority=7)
async def test_update_requirement_single_field(client):
    """Test updating single field of requirement"""
    # CREATE test entity (with auto-skip if fails)
    entity_id = await ResponseValidator.create_test_entity(
        client, "requirement", DataGenerator.requirement_data
    )
    if not entity_id:
        return {"success": False, "error": "Create failed", "skipped": True}
    try:
        result = await client.call_tool("entity_tool", {
            "entity_type": "requirement",
            "operation": "update",
            "entity_id": entity_id,
            "data": {"title": "Updated Test Requirement"}
        })
        assert result["success"]
        return {"success": True}
    finally:
        await client.call_tool("entity_tool", {
            "entity_type": "requirement",
            "operation": "delete",
            "entity_id": entity_id
        })


# --- Delete Operations ---
@mcp_test(tool_name="entity_tool", category="entity_delete", priority=6)
async def test_delete_requirement_soft(client):
    """Test soft delete of requirement"""
    # CREATE test entity (with auto-skip if fails)
    entity_id = await ResponseValidator.create_test_entity(
        client, "requirement", DataGenerator.requirement_data
    )
    if not entity_id:
        return {"success": False, "error": "Create failed", "skipped": True}
    result = await client.call_tool("entity_tool", {
        "entity_type": "requirement",
        "operation": "delete",
        "entity_id": entity_id,
        "soft_delete": True
    })
    assert result["success"]
    return {"success": True}


# --- Search Operations ---
@mcp_test(tool_name="entity_tool", category="entity_search", priority=7)
async def test_fuzzy_match_requirement(client):
    """Test fuzzy matching for requirements"""
    result = await client.call_tool("entity_tool", {
        "entity_type": "requirement",
        "operation": "search",
        "search_term": "test"
    })
    assert result["success"]
    assert isinstance(result["response"], list)
    return {"success": True}


@mcp_test(tool_name="entity_tool", category="entity_search", priority=7)
async def test_search_requirement_with_filters(client):
    """Test searching requirements with filters"""
    result = await client.call_tool("entity_tool", {
        "entity_type": "requirement",
        "operation": "search",
        "filters": {
            "priority": "high",
            "status": "pending"
        }
    })
    assert result["success"]
    assert isinstance(result["response"], list)
    return {"success": True}


# --- Format Variations ---









# --- Error Cases ---
@mcp_test(tool_name="entity_tool", category="entity_errors", priority=5)
async def test_create_requirement_missing_required_fields(client):
    """Test requirement creation with missing required fields"""
    result = await client.call_tool("entity_tool", {
        "entity_type": "requirement",
        "operation": "create",
        "data": {}  # Missing required fields
    })
    assert not result["success"]
    assert "error" in result
    return {"success": True}


@mcp_test(tool_name="entity_tool", category="entity_errors", priority=5)
async def test_read_requirement_invalid_id(client):
    """Test reading requirement with invalid ID"""
    result = await client.call_tool("entity_tool", {
        "entity_type": "requirement",
        "operation": "read",
        "entity_id": "invalid-id-abc"
    })
    assert not result["success"]
    assert "error" in result
    return {"success": True}


@mcp_test(tool_name="entity_tool", category="entity_errors", priority=5)
async def test_access_deleted_requirement(client):
    """Test accessing deleted requirement"""
    # Create and delete
    data = DataGenerator.requirement_data()
    create_result = await client.call_tool("entity_tool", {
        "entity_type": "requirement",
        "operation": "create",
        "data": data
    })
    entity_id = ResponseValidator.extract_id(create_result["response"])

    await client.call_tool("entity_tool", {
        "entity_type": "requirement",
        "operation": "delete",
        "entity_id": entity_id,
        "soft_delete": True
    })

    # Try to access deleted entity
    result = await client.call_tool("entity_tool", {
        "entity_type": "requirement",
        "operation": "read",
        "entity_id": entity_id
    })
    assert not result["success"] or result["response"].get("deleted") == True
    return {"success": True}


# ==================== TEST ENTITY TESTS ====================

# --- List Operations ---
@mcp_test(tool_name="entity_tool", category="entity_list", priority=8)
async def test_list_tests_basic(client):
    """Test basic test entity listing"""
    result = await client.call_tool("entity_tool", {
        "entity_type": "test",
        "operation": "list"
    })
    assert result["success"]
    assert isinstance(result["response"], list)
    return {"success": True}


@mcp_test(tool_name="entity_tool", category="entity_list", priority=7)
async def test_list_tests_limit_10(client):
    """Test test entity listing with limit=10"""
    result = await client.call_tool("entity_tool", {
        "entity_type": "test",
        "operation": "list",
        "limit": 10
    })
    assert result["success"]
    assert len(result["response"]) <= 10
    return {"success": True}


@mcp_test(tool_name="entity_tool", category="entity_list", priority=7)
async def test_list_tests_limit_50(client):
    """Test test entity listing with limit=50"""
    result = await client.call_tool("entity_tool", {
        "entity_type": "test",
        "operation": "list",
        "limit": 50
    })
    assert result["success"]
    assert len(result["response"]) <= 50
    return {"success": True}


@mcp_test(tool_name="entity_tool", category="entity_list", priority=7)
async def test_list_tests_with_parent_filter(client):
    """Test test entity listing with parent filter"""
    parent_id = DataGenerator.uuid()
    result = await client.call_tool("entity_tool", {
        "entity_type": "test",
        "operation": "list",
        "parent_id": parent_id
    })
    assert result["success"]
    assert isinstance(result["response"], list)
    return {"success": True}


# --- Create Operations ---
@mcp_test(tool_name="entity_tool", category="entity_create", priority=9)
async def test_create_test_basic(client):
    """Test basic test entity creation"""
    data = DataGenerator.test_data()
    result = await client.call_tool("entity_tool", {
        "entity_type": "test",
        "operation": "create",
        "data": data
    })
    assert result["success"]
    assert validators.FieldValidator.is_uuid(result["response"].get("id"))
    assert result["response"]["name"] == data["name"]
    return {"success": True, "entity_id": result["response"]["id"]}


@mcp_test(tool_name="entity_tool", category="entity_create", priority=8)
async def test_create_test_batch(client):
    """Test batch test entity creation (3 items)"""
    tests = []
    for i in range(3):
        data = DataGenerator.test_data()
        result = await client.call_tool("entity_tool", {
            "entity_type": "test",
            "operation": "create",
            "data": data
        })
        assert result["success"]
        tests.append(result["response"]["id"])
    assert len(tests) == 3
    return {"success": True, "entity_ids": tests}


# --- Read Operations ---
@mcp_test(tool_name="entity_tool", category="entity_read", priority=8)
async def test_read_test_by_id(client):
    """Test reading test entity by ID - creates test data first"""
    # Step 1: CREATE test entity (with auto-skip if fails)
    entity_id = await ResponseValidator.create_test_entity(
        client,
        "test",
        DataGenerator.test_data
    )

    if not entity_id:
        return {"success": False, "error": "Create failed", "skipped": True}

    try:
        # Step 2: READ the created test entity
        result = await client.call_tool("entity_tool", {
            "entity_type": "test",
            "operation": "read",
            "entity_id": entity_id
        })

        # Step 3: Verify read succeeded
        assert result["success"], f"Read failed: {result.get('error')}"

        return {"success": True}

    finally:
        # Step 4: Always DELETE test data (cleanup)
        await client.call_tool("entity_tool", {
            "entity_type": "test",
            "operation": "delete",
            "entity_id": entity_id
        })


@mcp_test(tool_name="entity_tool", category="entity_read", priority=7)
async def test_read_test_with_relations(client):
    """Test reading test entity with relations - creates test data first"""
    # Step 1: CREATE test entity (with auto-skip if fails)
    entity_id = await ResponseValidator.create_test_entity(
        client,
        "test",
        DataGenerator.test_data
    )

    if not entity_id:
        return {"success": False, "error": "Create failed", "skipped": True}

    try:
        # Step 2: READ with relations
        result = await client.call_tool("entity_tool", {
            "entity_type": "test",
            "operation": "read",
            "entity_id": entity_id,
            "include_relations": True
        })

        # Step 3: Verify read succeeded
        assert result["success"], f"Read with relations failed: {result.get('error')}"
        assert "relations" in result["response"] or "results" in result["response"]

        return {"success": True}

    finally:
        # Step 4: Always DELETE test data (cleanup)
        await client.call_tool("entity_tool", {
            "entity_type": "test",
            "operation": "delete",
            "entity_id": entity_id
        })


# --- Update Operations ---
@mcp_test(tool_name="entity_tool", category="entity_update", priority=7)
async def test_update_test_single_field(client):
    """Test updating single field of test entity"""
    # CREATE test entity (with auto-skip if fails)
    entity_id = await ResponseValidator.create_test_entity(
        client, "test", DataGenerator.test_data
    )

    if not entity_id:
        return {"success": False, "error": "Create failed", "skipped": True}

    try:
        # UPDATE single field
        new_name = "Updated Test Name"
        result = await client.call_tool("entity_tool", {
            "entity_type": "test",
            "operation": "update",
            "entity_id": entity_id,
            "data": {"name": new_name}
        })
        assert result["success"], f"Update failed: {result.get('error')}"
        return {"success": True}

    finally:
        # DELETE cleanup
        await client.call_tool("entity_tool", {
            "entity_type": "test",
            "operation": "delete",
            "entity_id": entity_id
        })


# --- Delete Operations ---
@mcp_test(tool_name="entity_tool", category="entity_delete", priority=6)
async def test_delete_test_soft(client):
    """Test soft delete of test entity"""
    # CREATE test entity (with auto-skip if fails)
    entity_id = await ResponseValidator.create_test_entity(
        client, "test", DataGenerator.test_data
    )

    if not entity_id:
        return {"success": False, "error": "Create failed", "skipped": True}

    # DELETE (soft delete is the actual test, no cleanup needed)
    result = await client.call_tool("entity_tool", {
        "entity_type": "test",
        "operation": "delete",
        "entity_id": entity_id,
        "soft_delete": True
    })
    assert result["success"], f"Delete failed: {result.get('error')}"
    return {"success": True}


# --- Search Operations ---
@mcp_test(tool_name="entity_tool", category="entity_search", priority=7)
async def test_fuzzy_match_test(client):
    """Test fuzzy matching for test entities"""
    result = await client.call_tool("entity_tool", {
        "entity_type": "test",
        "operation": "search",
        "search_term": "test"
    })
    assert result["success"]
    assert isinstance(result["response"], list)
    return {"success": True}


@mcp_test(tool_name="entity_tool", category="entity_search", priority=7)
async def test_search_test_with_filters(client):
    """Test searching test entities with filters"""
    result = await client.call_tool("entity_tool", {
        "entity_type": "test",
        "operation": "search",
        "filters": {
            "status": "passed",
            "type": "integration"
        }
    })
    assert result["success"]
    assert isinstance(result["response"], list)
    return {"success": True}


# --- Format Variations ---









# --- Error Cases ---
@mcp_test(tool_name="entity_tool", category="entity_errors", priority=5)
async def test_create_test_missing_required_fields(client):
    """Test test entity creation with missing required fields"""
    result = await client.call_tool("entity_tool", {
        "entity_type": "test",
        "operation": "create",
        "data": {}  # Missing required fields
    })
    assert not result["success"]
    assert "error" in result
    return {"success": True}


@mcp_test(tool_name="entity_tool", category="entity_errors", priority=5)
async def test_read_test_invalid_id(client):
    """Test reading test entity with invalid ID"""
    result = await client.call_tool("entity_tool", {
        "entity_type": "test",
        "operation": "read",
        "entity_id": "invalid-id-xyz"
    })
    assert not result["success"]
    assert "error" in result
    return {"success": True}


@mcp_test(tool_name="entity_tool", category="entity_errors", priority=5)
async def test_access_deleted_test(client):
    """Test accessing deleted test entity"""
    # Create and delete
    data = DataGenerator.test_data()
    create_result = await client.call_tool("entity_tool", {
        "entity_type": "test",
        "operation": "create",
        "data": data
    })
    entity_id = ResponseValidator.extract_id(create_result["response"])

    await client.call_tool("entity_tool", {
        "entity_type": "test",
        "operation": "delete",
        "entity_id": entity_id,
        "soft_delete": True
    })

    # Try to access deleted entity
    result = await client.call_tool("entity_tool", {
        "entity_type": "test",
        "operation": "read",
        "entity_id": entity_id
    })
    assert not result["success"] or result["response"].get("deleted") == True
    return {"success": True}