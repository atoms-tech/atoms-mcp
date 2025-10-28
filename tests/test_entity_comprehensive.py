"""
Comprehensive test suite for entity operations covering all entity types and CRUD operations.
Tests organization, project, document, requirement, and test entities with full CRUD validation.
"""

import uuid

import pytest

from tests.framework import DataGenerator, ResponseValidator, mcp_test

# ============================================================================
# ORGANIZATION TESTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.parallel
@pytest.mark.priority(8)
@mcp_test(tool_name="entity_tool", category="organization", priority=8)
async def test_organization_list_operations(client_adapter):
    """Test basic organization listing operations."""
    result = await client_adapter.call_tool("entity_tool", {
        "entity_type": "organization",
        "operation": "list"
    })

    assert result["success"], "Organization list operation should succeed"
    assert ResponseValidator.has_any_fields(
        result["response"],
        ["organizations", "items", "data"]
    ), "Response should contain organization data"

    return {"success": True, "test": "organization_list"}

@pytest.mark.asyncio
@pytest.mark.parallel
@pytest.mark.priority(9)
@mcp_test(tool_name="entity_tool", category="organization", priority=9)
async def test_organization_create_operations(client_adapter):
    """Test organization creation operations."""
    test_data = DataGenerator.organization_data()
    created_org = None

    try:
        result = await client_adapter.call_tool("entity_tool", {
            "entity_type": "organization",
            "operation": "create",
            "data": test_data
        })

        assert result["success"], "Organization creation should succeed"
        created_org = result["response"]

        # Validate UUID format
        assert ResponseValidator.is_uuid(created_org.get("id")), "Organization ID should be valid UUID"

        # Validate required fields
        assert ResponseValidator.has_fields(
            created_org,
            ["id", "name", "created_at", "updated_at"]
        ), "Created organization should have required fields"

        return {"success": True, "test": "organization_create", "id": created_org["id"]}

    finally:
        # Cleanup
        if created_org:
            await client_adapter.call_tool("entity_tool", {
                "entity_type": "organization",
                "operation": "delete",
                "entity_id": created_org["id"]
            })

@pytest.mark.asyncio
@pytest.mark.parallel
@pytest.mark.priority(8)
@mcp_test(tool_name="entity_tool", category="organization", priority=8)
async def test_organization_read_operations(client_adapter):
    """Test organization read operations."""
    test_data = DataGenerator.organization_data()
    created_org = None

    try:
        # Create organization first
        create_result = await client_adapter.call_tool("entity_tool", {
            "entity_type": "organization",
            "operation": "create",
            "data": test_data
        })

        assert create_result["success"], "Organization creation should succeed"
        created_org = create_result["response"]

        # Read organization
        result = await client_adapter.call_tool("entity_tool", {
            "entity_type": "organization",
            "operation": "read",
            "entity_id": created_org["id"]
        })

        assert result["success"], "Organization read operation should succeed"
        assert result["response"]["id"] == created_org["id"], "Should return the correct organization"

        return {"success": True, "test": "organization_read", "id": created_org["id"]}

    finally:
        # Cleanup
        if created_org:
            await client_adapter.call_tool("entity_tool", {
                "entity_type": "organization",
                "operation": "delete",
                "entity_id": created_org["id"]
            })

@pytest.mark.asyncio
@pytest.mark.parallel
@pytest.mark.priority(7)
@mcp_test(tool_name="entity_tool", category="organization", priority=7)
async def test_organization_update_operations(client_adapter):
    """Test organization update operations."""
    test_data = DataGenerator.organization_data()
    created_org = None

    try:
        # Create organization first
        create_result = await client_adapter.call_tool("entity_tool", {
            "entity_type": "organization",
            "operation": "create",
            "data": test_data
        })

        assert create_result["success"], "Organization creation should succeed"
        created_org = create_result["response"]

        # Update organization
        update_data = {"name": f"Updated {test_data['name']}"}
        result = await client_adapter.call_tool("entity_tool", {
            "entity_type": "organization",
            "operation": "update",
            "entity_id": created_org["id"],
            "data": update_data
        })

        assert result["success"], "Organization update operation should succeed"
        assert result["response"]["name"] == update_data["name"], "Name should be updated"

        return {"success": True, "test": "organization_update", "id": created_org["id"]}

    finally:
        # Cleanup
        if created_org:
            await client_adapter.call_tool("entity_tool", {
                "entity_type": "organization",
                "operation": "delete",
                "entity_id": created_org["id"]
            })

@pytest.mark.asyncio
@pytest.mark.parallel
@pytest.mark.priority(6)
@mcp_test(tool_name="entity_tool", category="organization", priority=6)
async def test_organization_delete_operations(client_adapter):
    """Test organization delete operations."""
    test_data = DataGenerator.organization_data()
    created_org = None

    try:
        # Create organization first
        create_result = await client_adapter.call_tool("entity_tool", {
            "entity_type": "organization",
            "operation": "create",
            "data": test_data
        })

        assert create_result["success"], "Organization creation should succeed"
        created_org = create_result["response"]

        # Delete organization
        result = await client_adapter.call_tool("entity_tool", {
            "entity_type": "organization",
            "operation": "delete",
            "entity_id": created_org["id"]
        })

        assert result["success"], "Organization delete operation should succeed"

        # Verify deletion
        read_result = await client_adapter.call_tool("entity_tool", {
            "entity_type": "organization",
            "operation": "read",
            "entity_id": created_org["id"]
        })

        assert not read_result["success"], "Deleted organization should not be readable"

        return {"success": True, "test": "organization_delete", "id": created_org["id"]}

    finally:
        # Cleanup - try to delete if still exists
        if created_org:
            try:
                await client_adapter.call_tool("entity_tool", {
                    "entity_type": "organization",
                    "operation": "delete",
                    "entity_id": created_org["id"]
                })
            except Exception:
                pass  # Already deleted

# ============================================================================
# PROJECT TESTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.parallel
@pytest.mark.priority(8)
@mcp_test(tool_name="entity_tool", category="project", priority=8)
async def test_project_list_operations(client_adapter):
    """Test basic project listing operations."""
    result = await client_adapter.call_tool("entity_tool", {
        "entity_type": "project",
        "operation": "list"
    })

    assert result["success"], "Project list operation should succeed"
    assert ResponseValidator.has_any_fields(
        result["response"],
        ["projects", "items", "data"]
    ), "Response should contain project data"

    return {"success": True, "test": "project_list"}

@pytest.mark.asyncio
@pytest.mark.parallel
@pytest.mark.priority(9)
@mcp_test(tool_name="entity_tool", category="project", priority=9)
async def test_project_create_operations(client_adapter):
    """Test project creation operations."""
    # First create an organization
    org_data = DataGenerator.organization_data()
    created_org = None
    created_project = None

    try:
        # Create organization
        org_result = await client_adapter.call_tool("entity_tool", {
            "entity_type": "organization",
            "operation": "create",
            "data": org_data
        })

        assert org_result["success"], "Organization creation should succeed"
        created_org = org_result["response"]

        # Create project
        test_data = DataGenerator.project_data(organization_id=created_org["id"])
        result = await client_adapter.call_tool("entity_tool", {
            "entity_type": "project",
            "operation": "create",
            "data": test_data
        })

        assert result["success"], "Project creation should succeed"
        created_project = result["response"]

        # Validate UUID format
        assert ResponseValidator.is_uuid(created_project.get("id")), "Project ID should be valid UUID"

        # Validate required fields
        assert ResponseValidator.has_fields(
            created_project,
            ["id", "name", "organization_id", "created_at", "updated_at"]
        ), "Created project should have required fields"

        return {"success": True, "test": "project_create", "id": created_project["id"]}

    finally:
        # Cleanup
        if created_project:
            await client_adapter.call_tool("entity_tool", {
                "entity_type": "project",
                "operation": "delete",
                "entity_id": created_project["id"]
            })
        if created_org:
            await client_adapter.call_tool("entity_tool", {
                "entity_type": "organization",
                "operation": "delete",
                "entity_id": created_org["id"]
            })

# ============================================================================
# DOCUMENT TESTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.parallel
@pytest.mark.priority(8)
@mcp_test(tool_name="entity_tool", category="document", priority=8)
async def test_document_list_operations(client_adapter):
    """Test basic document listing operations."""
    result = await client_adapter.call_tool("entity_tool", {
        "entity_type": "document",
        "operation": "list"
    })

    assert result["success"], "Document list operation should succeed"
    assert ResponseValidator.has_any_fields(
        result["response"],
        ["documents", "items", "data"]
    ), "Response should contain document data"

    return {"success": True, "test": "document_list"}

@pytest.mark.asyncio
@pytest.mark.parallel
@pytest.mark.priority(9)
@mcp_test(tool_name="entity_tool", category="document", priority=9)
async def test_document_create_operations(client_adapter):
    """Test document creation operations."""
    # First create organization and project
    org_data = DataGenerator.organization_data()
    created_org = None
    created_project = None
    created_document = None

    try:
        # Create organization
        org_result = await client_adapter.call_tool("entity_tool", {
            "entity_type": "organization",
            "operation": "create",
            "data": org_data
        })

        assert org_result["success"], "Organization creation should succeed"
        created_org = org_result["response"]

        # Create project
        project_data = DataGenerator.project_data(organization_id=created_org["id"])
        project_result = await client_adapter.call_tool("entity_tool", {
            "entity_type": "project",
            "operation": "create",
            "data": project_data
        })

        assert project_result["success"], "Project creation should succeed"
        created_project = project_result["response"]

        # Create document
        test_data = DataGenerator.document_data(project_id=created_project["id"])
        result = await client_adapter.call_tool("entity_tool", {
            "entity_type": "document",
            "operation": "create",
            "data": test_data
        })

        assert result["success"], "Document creation should succeed"
        created_document = result["response"]

        # Validate UUID format
        assert ResponseValidator.is_uuid(created_document.get("id")), "Document ID should be valid UUID"

        # Validate required fields
        assert ResponseValidator.has_fields(
            created_document,
            ["id", "title", "project_id", "created_at", "updated_at"]
        ), "Created document should have required fields"

        return {"success": True, "test": "document_create", "id": created_document["id"]}

    finally:
        # Cleanup
        if created_document:
            await client_adapter.call_tool("entity_tool", {
                "entity_type": "document",
                "operation": "delete",
                "entity_id": created_document["id"]
            })
        if created_project:
            await client_adapter.call_tool("entity_tool", {
                "entity_type": "project",
                "operation": "delete",
                "entity_id": created_project["id"]
            })
        if created_org:
            await client_adapter.call_tool("entity_tool", {
                "entity_type": "organization",
                "operation": "delete",
                "entity_id": created_org["id"]
            })

# ============================================================================
# REQUIREMENT TESTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.parallel
@pytest.mark.priority(8)
@mcp_test(tool_name="entity_tool", category="requirement", priority=8)
async def test_requirement_list_operations(client_adapter):
    """Test basic requirement listing operations."""
    result = await client_adapter.call_tool("entity_tool", {
        "entity_type": "requirement",
        "operation": "list"
    })

    assert result["success"], "Requirement list operation should succeed"
    assert ResponseValidator.has_any_fields(
        result["response"],
        ["requirements", "items", "data"]
    ), "Response should contain requirement data"

    return {"success": True, "test": "requirement_list"}

@pytest.mark.asyncio
@pytest.mark.parallel
@pytest.mark.priority(9)
@mcp_test(tool_name="entity_tool", category="requirement", priority=9)
async def test_requirement_create_operations(client_adapter):
    """Test requirement creation operations."""
    # First create organization, project, and document
    org_data = DataGenerator.organization_data()
    created_org = None
    created_project = None
    created_document = None
    created_requirement = None

    try:
        # Create organization
        org_result = await client_adapter.call_tool("entity_tool", {
            "entity_type": "organization",
            "operation": "create",
            "data": org_data
        })

        assert org_result["success"], "Organization creation should succeed"
        created_org = org_result["response"]

        # Create project
        project_data = DataGenerator.project_data(organization_id=created_org["id"])
        project_result = await client_adapter.call_tool("entity_tool", {
            "entity_type": "project",
            "operation": "create",
            "data": project_data
        })

        assert project_result["success"], "Project creation should succeed"
        created_project = project_result["response"]

        # Create document
        document_data = DataGenerator.document_data(project_id=created_project["id"])
        document_result = await client_adapter.call_tool("entity_tool", {
            "entity_type": "document",
            "operation": "create",
            "data": document_data
        })

        assert document_result["success"], "Document creation should succeed"
        created_document = document_result["response"]

        # Create requirement
        test_data = DataGenerator.requirement_data(document_id=created_document["id"])
        result = await client_adapter.call_tool("entity_tool", {
            "entity_type": "requirement",
            "operation": "create",
            "data": test_data
        })

        assert result["success"], "Requirement creation should succeed"
        created_requirement = result["response"]

        # Validate UUID format
        assert ResponseValidator.is_uuid(created_requirement.get("id")), "Requirement ID should be valid UUID"

        # Validate required fields
        assert ResponseValidator.has_fields(
            created_requirement,
            ["id", "title", "document_id", "created_at", "updated_at"]
        ), "Created requirement should have required fields"

        return {"success": True, "test": "requirement_create", "id": created_requirement["id"]}

    finally:
        # Cleanup
        if created_requirement:
            await client_adapter.call_tool("entity_tool", {
                "entity_type": "requirement",
                "operation": "delete",
                "entity_id": created_requirement["id"]
            })
        if created_document:
            await client_adapter.call_tool("entity_tool", {
                "entity_type": "document",
                "operation": "delete",
                "entity_id": created_document["id"]
            })
        if created_project:
            await client_adapter.call_tool("entity_tool", {
                "entity_type": "project",
                "operation": "delete",
                "entity_id": created_project["id"]
            })
        if created_org:
            await client_adapter.call_tool("entity_tool", {
                "entity_type": "organization",
                "operation": "delete",
                "entity_id": created_org["id"]
            })

# ============================================================================
# TEST ENTITY TESTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.parallel
@pytest.mark.priority(8)
@mcp_test(tool_name="entity_tool", category="test", priority=8)
async def test_test_entity_list_operations(client_adapter):
    """Test basic test entity listing operations."""
    result = await client_adapter.call_tool("entity_tool", {
        "entity_type": "test",
        "operation": "list"
    })

    assert result["success"], "Test entity list operation should succeed"
    assert ResponseValidator.has_any_fields(
        result["response"],
        ["tests", "items", "data"]
    ), "Response should contain test entity data"

    return {"success": True, "test": "test_entity_list"}

@pytest.mark.asyncio
@pytest.mark.parallel
@pytest.mark.priority(9)
@mcp_test(tool_name="entity_tool", category="test", priority=9)
async def test_test_entity_create_operations(client_adapter):
    """Test test entity creation operations."""
    # First create organization, project, document, and requirement
    org_data = DataGenerator.organization_data()
    created_org = None
    created_project = None
    created_document = None
    created_requirement = None
    created_test = None

    try:
        # Create organization
        org_result = await client_adapter.call_tool("entity_tool", {
            "entity_type": "organization",
            "operation": "create",
            "data": org_data
        })

        assert org_result["success"], "Organization creation should succeed"
        created_org = org_result["response"]

        # Create project
        project_data = DataGenerator.project_data(organization_id=created_org["id"])
        project_result = await client_adapter.call_tool("entity_tool", {
            "entity_type": "project",
            "operation": "create",
            "data": project_data
        })

        assert project_result["success"], "Project creation should succeed"
        created_project = project_result["response"]

        # Create document
        document_data = DataGenerator.document_data(project_id=created_project["id"])
        document_result = await client_adapter.call_tool("entity_tool", {
            "entity_type": "document",
            "operation": "create",
            "data": document_data
        })

        assert document_result["success"], "Document creation should succeed"
        created_document = document_result["response"]

        # Create requirement
        requirement_data = DataGenerator.requirement_data(document_id=created_document["id"])
        requirement_result = await client_adapter.call_tool("entity_tool", {
            "entity_type": "requirement",
            "operation": "create",
            "data": requirement_data
        })

        assert requirement_result["success"], "Requirement creation should succeed"
        created_requirement = requirement_result["response"]

        # Create test entity
        test_data = DataGenerator.test_data(requirement_id=created_requirement["id"])
        result = await client_adapter.call_tool("entity_tool", {
            "entity_type": "test",
            "operation": "create",
            "data": test_data
        })

        assert result["success"], "Test entity creation should succeed"
        created_test = result["response"]

        # Validate UUID format
        assert ResponseValidator.is_uuid(created_test.get("id")), "Test entity ID should be valid UUID"

        # Validate required fields
        assert ResponseValidator.has_fields(
            created_test,
            ["id", "title", "requirement_id", "created_at", "updated_at"]
        ), "Created test entity should have required fields"

        return {"success": True, "test": "test_entity_create", "id": created_test["id"]}

    finally:
        # Cleanup
        if created_test:
            await client_adapter.call_tool("entity_tool", {
                "entity_type": "test",
                "operation": "delete",
                "entity_id": created_test["id"]
            })
        if created_requirement:
            await client_adapter.call_tool("entity_tool", {
                "entity_type": "requirement",
                "operation": "delete",
                "entity_id": created_requirement["id"]
            })
        if created_document:
            await client_adapter.call_tool("entity_tool", {
                "entity_type": "document",
                "operation": "delete",
                "entity_id": created_document["id"]
            })
        if created_project:
            await client_adapter.call_tool("entity_tool", {
                "entity_type": "project",
                "operation": "delete",
                "entity_id": created_project["id"]
            })
        if created_org:
            await client_adapter.call_tool("entity_tool", {
                "entity_type": "organization",
                "operation": "delete",
                "entity_id": created_org["id"]
            })

# ============================================================================
# ERROR CASE TESTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.parallel
@pytest.mark.priority(5)
@mcp_test(tool_name="entity_tool", category="error", priority=5)
async def test_invalid_entity_type_error(client_adapter):
    """Test error handling for invalid entity type."""
    result = await client_adapter.call_tool("entity_tool", {
        "entity_type": "invalid_entity",
        "operation": "list"
    })

    assert not result["success"], "Invalid entity type should fail"
    assert "error" in result, "Error response should contain error information"

    return {"success": True, "test": "invalid_entity_type_error"}

@pytest.mark.asyncio
@pytest.mark.parallel
@pytest.mark.priority(5)
@mcp_test(tool_name="entity_tool", category="error", priority=5)
async def test_missing_required_fields_error(client_adapter):
    """Test error handling for missing required fields."""
    result = await client_adapter.call_tool("entity_tool", {
        "entity_type": "organization",
        "operation": "create",
        "data": {}  # Missing required fields
    })

    assert not result["success"], "Missing required fields should fail"
    assert "error" in result, "Error response should contain error information"

    return {"success": True, "test": "missing_required_fields_error"}

@pytest.mark.asyncio
@pytest.mark.parallel
@pytest.mark.priority(5)
@mcp_test(tool_name="entity_tool", category="error", priority=5)
async def test_nonexistent_entity_read_error(client_adapter):
    """Test error handling for reading nonexistent entity."""
    fake_id = str(uuid.uuid4())
    result = await client_adapter.call_tool("entity_tool", {
        "entity_type": "organization",
        "operation": "read",
        "entity_id": fake_id
    })

    assert not result["success"], "Reading nonexistent entity should fail"
    assert "error" in result, "Error response should contain error information"

    return {"success": True, "test": "nonexistent_entity_read_error"}

# ============================================================================
# SEARCH OPERATIONS TESTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.parallel
@pytest.mark.priority(7)
@mcp_test(tool_name="entity_tool", category="search", priority=7)
async def test_organization_search_operations(client_adapter):
    """Test organization search operations."""
    result = await client_adapter.call_tool("entity_tool", {
        "entity_type": "organization",
        "operation": "search",
        "query": "test"
    })

    assert result["success"], "Organization search operation should succeed"
    assert ResponseValidator.has_any_fields(
        result["response"],
        ["organizations", "items", "data"]
    ), "Response should contain search results"

    return {"success": True, "test": "organization_search"}

@pytest.mark.asyncio
@pytest.mark.parallel
@pytest.mark.priority(7)
@mcp_test(tool_name="entity_tool", category="search", priority=7)
async def test_project_search_operations(client_adapter):
    """Test project search operations."""
    result = await client_adapter.call_tool("entity_tool", {
        "entity_type": "project",
        "operation": "search",
        "query": "test"
    })

    assert result["success"], "Project search operation should succeed"
    assert ResponseValidator.has_any_fields(
        result["response"],
        ["projects", "items", "data"]
    ), "Response should contain search results"

    return {"success": True, "test": "project_search"}

# ============================================================================
# BATCH OPERATIONS TESTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.parallel
@pytest.mark.priority(8)
@mcp_test(tool_name="entity_tool", category="batch", priority=8)
async def test_organization_batch_create_operations(client_adapter):
    """Test organization batch creation operations."""
    test_data = [
        DataGenerator.organization_data(),
        DataGenerator.organization_data(),
        DataGenerator.organization_data()
    ]
    created_orgs = []

    try:
        result = await client_adapter.call_tool("entity_tool", {
            "entity_type": "organization",
            "operation": "batch_create",
            "data": test_data
        })

        assert result["success"], "Organization batch creation should succeed"
        created_orgs = result["response"]

        assert len(created_orgs) == 3, "Should create 3 organizations"

        # Validate each created organization
        for org in created_orgs:
            assert ResponseValidator.is_uuid(org.get("id")), "Organization ID should be valid UUID"
            assert ResponseValidator.has_fields(
                org,
                ["id", "name", "created_at", "updated_at"]
            ), "Created organization should have required fields"

        return {"success": True, "test": "organization_batch_create", "count": len(created_orgs)}

    finally:
        # Cleanup
        for org in created_orgs:
            try:
                await client_adapter.call_tool("entity_tool", {
                    "entity_type": "organization",
                    "operation": "delete",
                    "entity_id": org["id"]
                })
            except Exception:
                pass  # Already deleted

# ============================================================================
# RELATION OPERATIONS TESTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.parallel
@pytest.mark.priority(8)
@mcp_test(tool_name="entity_tool", category="relations", priority=8)
async def test_organization_with_relations(client_adapter):
    """Test organization read with relations."""
    test_data = DataGenerator.organization_data()
    created_org = None

    try:
        # Create organization
        create_result = await client_adapter.call_tool("entity_tool", {
            "entity_type": "organization",
            "operation": "create",
            "data": test_data
        })

        assert create_result["success"], "Organization creation should succeed"
        created_org = create_result["response"]

        # Read organization with relations
        result = await client_adapter.call_tool("entity_tool", {
            "entity_type": "organization",
            "operation": "read",
            "entity_id": created_org["id"],
            "include_relations": True
        })

        assert result["success"], "Organization read with relations should succeed"
        assert result["response"]["id"] == created_org["id"], "Should return the correct organization"

        # Check if relations are included (if any exist)
        response = result["response"]
        if "projects" in response:
            assert isinstance(response["projects"], list), "Projects should be a list"

        return {"success": True, "test": "organization_with_relations", "id": created_org["id"]}

    finally:
        # Cleanup
        if created_org:
            await client_adapter.call_tool("entity_tool", {
                "entity_type": "organization",
                "operation": "delete",
                "entity_id": created_org["id"]
            })
