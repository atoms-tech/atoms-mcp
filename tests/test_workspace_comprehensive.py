"""
Comprehensive test suite for workspace operations covering all parameter variations.
Tests list_workspaces, get_context, set_context, and get_defaults operations.
"""

from tests.framework import mcp_test, validators, DataGenerator


# ============================================================================
# LIST_WORKSPACES TESTS (6 tests)
# ============================================================================

@mcp_test(tool_name="workspace_tool", category="workspace", priority=10)
async def test_list_workspaces_default_pagination(client):
    """Test list_workspaces with default pagination settings."""
    result = await client.call_tool("workspace_tool", {
        "operation": "list_workspaces"
    })

    assert result["success"], "Operation should succeed"
    assert validators.ResponseValidator.has_any_fields(
        result["response"],
        ["organizations", "workspaces", "items", "data"]
    ), "Response should contain workspace data"

    # Check for pagination fields if present
    if "pagination" in result["response"]:
        assert validators.ResponseValidator.has_fields(
            result["response"]["pagination"],
            ["total", "limit", "offset"]
        ), "Pagination should have required fields"

    return {"success": True, "test": "default_pagination"}


@mcp_test(tool_name="workspace_tool", category="workspace", priority=10)
async def test_list_workspaces_custom_limit(client):
    """Test list_workspaces with custom limit of 50."""
    result = await client.call_tool("workspace_tool", {
        "operation": "list_workspaces",
        "limit": 50
    })

    assert result["success"], "Operation should succeed"
    response = result["response"]

    # Verify the limit was applied
    if "pagination" in response:
        assert response["pagination"].get("limit") == 50, "Limit should be 50"

    # Check data structure
    assert validators.ResponseValidator.has_any_fields(
        response,
        ["organizations", "workspaces", "items", "data"]
    ), "Response should contain workspace data"

    # Verify item count doesn't exceed limit
    data_field = None
    for field in ["organizations", "workspaces", "items", "data"]:
        if field in response and isinstance(response[field], list):
            data_field = response[field]
            break

    if data_field:
        assert len(data_field) <= 50, f"Should return at most 50 items, got {len(data_field)}"

    return {"success": True, "test": "custom_limit", "limit": 50}


@mcp_test(tool_name="workspace_tool", category="workspace", priority=10)
async def test_list_workspaces_with_offset(client):
    """Test list_workspaces with limit=25 and offset=25 for pagination."""
    result = await client.call_tool("workspace_tool", {
        "operation": "list_workspaces",
        "limit": 25,
        "offset": 25
    })

    assert result["success"], "Operation should succeed"
    response = result["response"]

    # Verify pagination parameters
    if "pagination" in response:
        pagination = response["pagination"]
        assert pagination.get("limit") == 25, "Limit should be 25"
        assert pagination.get("offset") == 25, "Offset should be 25"

    # Check data structure
    assert validators.ResponseValidator.has_any_fields(
        response,
        ["organizations", "workspaces", "items", "data"]
    ), "Response should contain workspace data"

    # Verify item count
    data_field = None
    for field in ["organizations", "workspaces", "items", "data"]:
        if field in response and isinstance(response[field], list):
            data_field = response[field]
            break

    if data_field:
        assert len(data_field) <= 25, f"Should return at most 25 items, got {len(data_field)}"

    return {"success": True, "test": "with_offset", "limit": 25, "offset": 25}


@mcp_test(tool_name="workspace_tool", category="workspace", priority=10)
async def test_list_workspaces_exceeds_max_limit(client):
    """Test list_workspaces with limit=1000 to check max limit handling."""
    result = await client.call_tool("workspace_tool", {
        "operation": "list_workspaces",
        "limit": 1000
    })

    # Could either succeed with capped limit or fail with error
    if result["success"]:
        response = result["response"]

        # Check if limit was capped
        if "pagination" in response:
            actual_limit = response["pagination"].get("limit")
            assert actual_limit <= 1000, "Limit should not exceed 1000"

            # Some APIs cap at lower values (e.g., 100 or 200)
            if actual_limit < 1000:
                assert actual_limit in [100, 200, 500], f"Limit capped to unexpected value: {actual_limit}"

        # Verify data structure
        assert validators.ResponseValidator.has_any_fields(
            response,
            ["organizations", "workspaces", "items", "data"]
        ), "Response should contain workspace data"
    else:
        # If it failed, should have appropriate error message
        assert "error" in result or "message" in result, "Should have error details"
        error_msg = str(result.get("error", result.get("message", ""))).lower()
        assert any(word in error_msg for word in ["limit", "max", "exceed", "invalid"]), \
            "Error should mention limit issue"

    return {"success": True, "test": "exceeds_max_limit", "requested_limit": 1000}


@mcp_test(tool_name="workspace_tool", category="workspace", priority=10)
async def test_list_workspaces_with_data_check(client):
    """Test list_workspaces returns proper workspace data structure."""
    result = await client.call_tool("workspace_tool", {
        "operation": "list_workspaces"
    })

    assert result["success"], "Operation should succeed"
    response = result["response"]

    # Check that response includes comprehensive information
    assert validators.ResponseValidator.has_any_fields(
        response,
        ["organizations", "workspaces", "items", "data"]
    ), "Response should contain workspace data"

    # Check for detailed fields in items
    data_field = None
    for field in ["organizations", "workspaces", "items", "data"]:
        if field in response and isinstance(response[field], list) and len(response[field]) > 0:
            data_field = response[field]
            break

    if data_field and len(data_field) > 0:
        first_item = data_field[0]
        # Response should include core fields
        core_fields = ["id", "name"]
        has_core = any(field in first_item for field in core_fields)
        assert has_core, "Response should include core identification fields"

    return {"success": True, "test": "data_structure_check"}


@mcp_test(tool_name="workspace_tool", category="workspace", priority=10)
async def test_list_workspaces_consistency_check(client):
    """Test list_workspaces returns consistent data structure."""
    # Test multiple times to verify consistency
    results = []

    for i in range(2):
        result = await client.call_tool("workspace_tool", {
            "operation": "list_workspaces",
            "limit": 5  # Small limit for quick test
        })

        assert result["success"], f"Operation should succeed on iteration {i+1}"
        response = result["response"]

        # All calls should have consistent data structure
        assert validators.ResponseValidator.has_any_fields(
            response,
            ["organizations", "workspaces", "items", "data"]
        ), f"Response should contain workspace data on iteration {i+1}"

        results.append(response)

    # Verify both responses have similar structure
    if len(results) == 2:
        # Check that both have the same keys
        keys1 = set(results[0].keys())
        keys2 = set(results[1].keys())
        assert keys1 == keys2, "Response structure should be consistent across calls"

    return {"success": True, "test": "consistency_check", "iterations": len(results)}


# ============================================================================
# GET_CONTEXT TESTS (2 tests)
# ============================================================================

@mcp_test(tool_name="workspace_tool", category="workspace", priority=10)
async def test_get_context_basic(client):
    """Test get_context with default parameters."""
    result = await client.call_tool("workspace_tool", {
        "operation": "get_context"
    })

    assert result["success"], "Operation should succeed"
    response = result["response"]

    # Check for context fields
    context_fields = ["organization", "project", "document", "workspace",
                     "current_context", "active_context", "context"]
    assert validators.ResponseValidator.has_any_fields(
        response,
        context_fields
    ), "Response should contain context information"

    # Verify context structure if present
    context_data = None
    for field in context_fields:
        if field in response:
            context_data = response[field]
            break

    if context_data and isinstance(context_data, dict):
        # Context should have type information
        assert validators.ResponseValidator.has_any_fields(
            context_data,
            ["type", "id", "name", "organization_id", "project_id"]
        ), "Context should have identification fields"

    return {"success": True, "test": "get_context_basic"}


@mcp_test(tool_name="workspace_tool", category="workspace", priority=10)
async def test_get_context_structure(client):
    """Test get_context returns proper structure."""
    result = await client.call_tool("workspace_tool", {
        "operation": "get_context"
    })

    assert result["success"], "Operation should succeed"
    response = result["response"]

    # Response should provide context info
    context_fields = ["organization", "project", "document", "workspace",
                     "current_context", "active_context", "context", "active_organization",
                     "active_project", "active_document"]
    assert validators.ResponseValidator.has_any_fields(
        response,
        context_fields
    ), "Response should contain context information"

    # Context data structure check
    for field in context_fields:
        if field in response:
            # If field exists, it should be a valid data type
            context_value = response[field]
            assert context_value is None or isinstance(context_value, (str, dict)), \
                f"Context field '{field}' should be None, string, or dict"
            break

    return {"success": True, "test": "get_context_structure"}


# ============================================================================
# SET_CONTEXT TESTS (4 tests)
# ============================================================================

@mcp_test(tool_name="workspace_tool", category="workspace", priority=10)
async def test_set_context_organization(client):
    """Test set_context for organization type."""
    # Generate test organization ID
    org_id = DataGenerator.uuid()

    result = await client.call_tool("workspace_tool", {
        "operation": "set_context",
        "type": "organization",
        "id": org_id
    })

    assert result["success"], "Operation should succeed"
    response = result["response"]

    # Verify context was set
    assert validators.ResponseValidator.has_any_fields(
        response,
        ["success", "context", "updated", "organization"]
    ), "Response should confirm context update"

    # Check if organization context is reflected
    if "context" in response:
        context = response["context"]
        if isinstance(context, dict):
            assert context.get("type") == "organization", "Context type should be organization"
            assert context.get("id") == org_id or context.get("organization_id") == org_id, \
                "Organization ID should match"

    return {"success": True, "test": "set_organization", "org_id": org_id}


@mcp_test(tool_name="workspace_tool", category="workspace", priority=10)
async def test_set_context_project(client):
    """Test set_context for project type."""
    # Generate test IDs
    org_id = DataGenerator.uuid()
    project_id = DataGenerator.uuid()

    result = await client.call_tool("workspace_tool", {
        "operation": "set_context",
        "type": "project",
        "id": project_id,
        "organization_id": org_id
    })

    assert result["success"], "Operation should succeed"
    response = result["response"]

    # Verify context was set
    assert validators.ResponseValidator.has_any_fields(
        response,
        ["success", "context", "updated", "project"]
    ), "Response should confirm context update"

    # Check if project context is reflected
    if "context" in response:
        context = response["context"]
        if isinstance(context, dict):
            assert context.get("type") == "project", "Context type should be project"
            assert context.get("id") == project_id or context.get("project_id") == project_id, \
                "Project ID should match"
            # Organization might be included
            if "organization_id" in context:
                assert context["organization_id"] == org_id, "Organization ID should match"

    return {"success": True, "test": "set_project", "project_id": project_id}


@mcp_test(tool_name="workspace_tool", category="workspace", priority=10)
async def test_set_context_document(client):
    """Test set_context for document type."""
    # Generate test IDs
    org_id = DataGenerator.uuid()
    project_id = DataGenerator.uuid()
    document_id = DataGenerator.uuid()

    result = await client.call_tool("workspace_tool", {
        "operation": "set_context",
        "type": "document",
        "id": document_id,
        "project_id": project_id,
        "organization_id": org_id
    })

    assert result["success"], "Operation should succeed"
    response = result["response"]

    # Verify context was set
    assert validators.ResponseValidator.has_any_fields(
        response,
        ["success", "context", "updated", "document"]
    ), "Response should confirm context update"

    # Check if document context is reflected
    if "context" in response:
        context = response["context"]
        if isinstance(context, dict):
            assert context.get("type") == "document", "Context type should be document"
            assert context.get("id") == document_id or context.get("document_id") == document_id, \
                "Document ID should match"
            # Parent IDs might be included
            if "project_id" in context:
                assert context["project_id"] == project_id, "Project ID should match"
            if "organization_id" in context:
                assert context["organization_id"] == org_id, "Organization ID should match"

    return {"success": True, "test": "set_document", "document_id": document_id}


@mcp_test(tool_name="workspace_tool", category="workspace", priority=10)
async def test_set_context_invalid_type(client):
    """Test set_context with invalid context type (error test)."""
    result = await client.call_tool("workspace_tool", {
        "operation": "set_context",
        "type": "invalid_type",
        "id": DataGenerator.uuid()
    })

    # This should fail
    assert not result["success"], "Operation should fail with invalid type"

    # Check for appropriate error message
    error = result.get("error", result.get("message", ""))
    assert error, "Should have error message"

    error_lower = str(error).lower()
    assert any(word in error_lower for word in ["invalid", "type", "unsupported", "unknown"]), \
        f"Error should mention invalid type: {error}"

    return {"success": True, "test": "invalid_context_type", "expected_failure": True}


# ============================================================================
# GET_DEFAULTS TESTS (2 tests)
# ============================================================================

@mcp_test(tool_name="workspace_tool", category="workspace", priority=10)
async def test_get_defaults_basic(client):
    """Test get_defaults with default parameters."""
    result = await client.call_tool("workspace_tool", {
        "operation": "get_defaults"
    })

    assert result["success"], "Operation should succeed"
    response = result["response"]

    # Check for default settings
    assert validators.ResponseValidator.has_any_fields(
        response,
        ["defaults", "settings", "preferences", "configuration"]
    ), "Response should contain default settings"

    # Verify defaults structure
    defaults_data = None
    for field in ["defaults", "settings", "preferences", "configuration"]:
        if field in response:
            defaults_data = response[field]
            break

    if defaults_data and isinstance(defaults_data, dict):
        # Should have various default settings
        common_defaults = ["organization", "project", "format", "limit",
                          "timeout", "region", "language"]
        has_defaults = any(field in defaults_data for field in common_defaults)
        assert has_defaults, "Should have some default settings"

    return {"success": True, "test": "get_defaults_basic"}


@mcp_test(tool_name="workspace_tool", category="workspace", priority=10)
async def test_get_defaults_data_types(client):
    """Test get_defaults returns proper data types."""
    result = await client.call_tool("workspace_tool", {
        "operation": "get_defaults"
    })

    assert result["success"], "Operation should succeed"
    response = result["response"]

    # Response should not be empty
    assert response, "Response should not be empty"

    # Check data type structure
    if isinstance(response, str):
        # String response should have content
        assert len(response) > 0, "String response should have content"
    elif isinstance(response, dict):
        # Dict should have fields
        assert len(response.keys()) > 0, "Dict response should have fields"

        # Check for common default fields
        default_fields = ["organization_id", "project_id", "document_id",
                         "defaults", "settings", "preferences"]
        has_defaults = any(field in response for field in default_fields)
        assert has_defaults, "Response should contain default configuration fields"
    elif isinstance(response, (list, tuple)):
        # List/tuple should have items
        assert len(response) > 0, "List response should have items"

    return {"success": True, "test": "get_defaults_data_types"}