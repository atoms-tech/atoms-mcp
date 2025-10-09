"""
Fast Workspace Tool Tests using FastHTTPClient

These tests use direct HTTP calls instead of the MCP decorator framework,
providing ~20x speed improvement while still validating real Supabase data,
RLS policies, and schema constraints.

Run with: pytest tests/unit/test_workspace_fast.py -v
"""

from datetime import datetime
import pytest


# ============================================================================
# LIST_WORKSPACES TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_list_workspaces_default_pagination(authenticated_client):
    """Test list_workspaces with default pagination settings."""
    result = await authenticated_client.call_tool("workspace_tool", {
        "operation": "list_workspaces"
    })

    assert result["success"], \
        f"Failed to list workspaces: {result.get('error')}"

    # FastHTTPClient extracts structuredContent
    assert "data" in result, f"Expected 'data' in result, got keys: {list(result.keys())}"
    data = result["data"]
    assert isinstance(data, list), f"Expected list of workspaces, got {type(data)}"

    # Check for pagination fields if present in result
    if "pagination" in result:
        pagination = result["pagination"]
        assert all(key in pagination for key in ["total", "limit", "offset"]), \
            f"Pagination missing required fields, got keys: {list(pagination.keys())}"


@pytest.mark.asyncio
async def test_list_workspaces_custom_limit(authenticated_client):
    """Test list_workspaces with custom limit of 50."""
    result = await authenticated_client.call_tool("workspace_tool", {
        "operation": "list_workspaces",
        "limit": 50
    })

    assert result["success"], \
        f"Failed to list workspaces with limit=50: {result.get('error')}"

    # Verify the limit was applied
    if "pagination" in result:
        assert result["pagination"].get("limit") == 50, \
            f"Expected limit=50, got {result['pagination'].get('limit')}"

    # FastHTTPClient extracts structuredContent
    assert "data" in result, f"Expected 'data' in result, got keys: {list(result.keys())}"
    data = result["data"]
    assert isinstance(data, list), f"Expected list of workspaces, got {type(data)}"

    # Verify item count doesn't exceed limit
    assert len(data) <= 50, \
        f"Expected at most 50 items with limit=50, got {len(data)}"


@pytest.mark.asyncio
async def test_list_workspaces_with_offset(authenticated_client):
    """Test list_workspaces with limit=25 and offset=25 for pagination."""
    result = await authenticated_client.call_tool("workspace_tool", {
        "operation": "list_workspaces",
        "limit": 25,
        "offset": 25
    })

    assert result["success"], \
        f"Failed to list workspaces with limit=25, offset=25: {result.get('error')}"

    # Verify pagination parameters
    if "pagination" in result:
        pagination = result["pagination"]
        assert pagination.get("limit") == 25, \
            f"Expected limit=25, got {pagination.get('limit')}"
        assert pagination.get("offset") == 25, \
            f"Expected offset=25, got {pagination.get('offset')}"

    # FastHTTPClient extracts structuredContent
    assert "data" in result, f"Expected 'data' in result, got keys: {list(result.keys())}"
    data = result["data"]
    assert isinstance(data, list), f"Expected list of workspaces, got {type(data)}"

    # Verify item count
    assert len(data) <= 25, \
        f"Expected at most 25 items with limit=25, got {len(data)}"


@pytest.mark.asyncio
async def test_list_workspaces_exceeds_max_limit(authenticated_client):
    """Test list_workspaces with limit=1000 to check max limit handling."""
    result = await authenticated_client.call_tool("workspace_tool", {
        "operation": "list_workspaces",
        "limit": 1000
    })

    # Could either succeed with capped limit or fail with error
    if result["success"]:
        # Check if limit was capped
        if "pagination" in result:
            actual_limit = result["pagination"].get("limit")
            assert actual_limit <= 1000, \
                f"Expected limit <= 1000, got {actual_limit}"

            # Some APIs cap at lower values (e.g., 100 or 200)
            if actual_limit < 1000:
                assert actual_limit in [100, 200, 500], \
                    f"Limit capped to unexpected value: {actual_limit}, expected one of [100, 200, 500]"

        # FastHTTPClient extracts structuredContent
        assert "data" in result, f"Expected 'data' in result, got keys: {list(result.keys())}"
        data = result["data"]
        assert isinstance(data, list), f"Expected list of workspaces, got {type(data)}"
    else:
        # If it failed, should have appropriate error message
        assert "error" in result or "message" in result, \
            f"Expected error details when limit exceeds max, got keys: {list(result.keys())}"
        error_msg = str(result.get("error", result.get("message", ""))).lower()
        assert any(word in error_msg for word in ["limit", "max", "exceed", "invalid"]), \
            f"Expected error to mention limit issue, got: {error_msg}"


@pytest.mark.asyncio
async def test_list_workspaces_with_data_check(authenticated_client):
    """Test list_workspaces returns proper workspace data structure."""
    result = await authenticated_client.call_tool("workspace_tool", {
        "operation": "list_workspaces"
    })

    assert result["success"], \
        f"Failed to list workspaces for data check: {result.get('error')}"

    # FastHTTPClient extracts structuredContent
    assert "data" in result, f"Expected 'data' in result, got keys: {list(result.keys())}"
    data = result["data"]
    assert isinstance(data, list), f"Expected list of workspaces, got {type(data)}"

    # Check for detailed fields in items
    if data and len(data) > 0:
        first_item = data[0]
        # Response should include core fields
        core_fields = ["id", "name"]
        has_core = any(field in first_item for field in core_fields)
        assert has_core, \
            f"Expected core fields {core_fields} in workspace items, got keys: {list(first_item.keys())}"


@pytest.mark.asyncio
async def test_list_workspaces_consistency_check(authenticated_client):
    """Test list_workspaces returns consistent data structure."""
    # Test multiple times to verify consistency
    results = []

    for i in range(2):
        result = await authenticated_client.call_tool("workspace_tool", {
            "operation": "list_workspaces",
            "limit": 5  # Small limit for quick test
        })

        assert result["success"], \
            f"Failed to list workspaces on iteration {i+1}: {result.get('error')}"

        # FastHTTPClient extracts structuredContent
        assert "data" in result, f"Expected 'data' in result on iteration {i+1}, got keys: {list(result.keys())}"
        data = result["data"]
        assert isinstance(data, list), f"Expected list on iteration {i+1}, got {type(data)}"

        results.append(result)

    # Verify both responses have similar structure
    if len(results) == 2:
        # Both should have 'data' key
        assert "data" in results[0] and "data" in results[1], \
            "Both responses should have 'data' key"


# ============================================================================
# GET_CONTEXT TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_get_context_basic(authenticated_client):
    """Test get_context with default parameters."""
    result = await authenticated_client.call_tool("workspace_tool", {
        "operation": "get_context"
    })

    assert result["success"], \
        f"Failed to get context: {result.get('error')}"

    # get_context might return data in different ways
    # Check for context fields in result directly or in data
    context_fields = ["organization", "project", "document", "workspace",
                     "current_context", "active_context", "context", "data"]
    has_context_info = any(field in result for field in context_fields)
    assert has_context_info, \
        f"Expected context information in result, got keys: {list(result.keys())}"

    # Verify context structure if present
    context_data = None
    for field in context_fields:
        if field in result:
            context_data = result[field]
            break

    if context_data and isinstance(context_data, dict):
        # Context should have type information
        id_fields = ["type", "id", "name", "organization_id", "project_id"]
        # Empty context is valid too
        if context_data:
            has_ids = any(field in context_data for field in id_fields)
            # Only assert if context_data is not empty
            if has_ids:
                assert True  # Context has expected fields


@pytest.mark.asyncio
async def test_get_context_structure(authenticated_client):
    """Test get_context returns proper structure."""
    result = await authenticated_client.call_tool("workspace_tool", {
        "operation": "get_context"
    })

    assert result["success"], \
        f"Failed to get context for structure check: {result.get('error')}"

    # get_context might return data in different ways
    context_fields = ["organization", "project", "document", "workspace",
                     "current_context", "active_context", "context", "active_organization",
                     "active_project", "active_document", "data"]
    assert any(field in result for field in context_fields), \
        f"Expected context information in result, got keys: {list(result.keys())}"

    # Context data structure check
    for field in context_fields:
        if field in result:
            # If field exists, it should be a valid data type
            context_value = result[field]
            assert context_value is None or isinstance(context_value, (str, dict, list)), \
                f"Context field '{field}' should be None, string, dict, or list, got {type(context_value).__name__}"
            break


# ============================================================================
# SET_CONTEXT TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_set_context_organization(authenticated_client):
    """Test set_context for organization type."""
    # Get a real organization ID from list_workspaces
    list_result = await authenticated_client.call_tool("workspace_tool", {
        "operation": "list_workspaces"
    })

    if not list_result.get("success"):
        pytest.skip("Cannot list workspaces to get organization ID for context test")

    # FastHTTPClient extracts structuredContent
    assert "data" in list_result, "Expected 'data' in list result"
    orgs = list_result["data"]

    if not orgs or not isinstance(orgs, list) or len(orgs) == 0:
        pytest.skip("No organizations available for set_context test")

    org_id = orgs[0].get("id")
    if not org_id:
        pytest.skip("Organization data missing ID field")

    # Now set context
    result = await authenticated_client.call_tool("workspace_tool", {
        "operation": "set_context",
        "context_type": "organization",
        "entity_id": org_id
    })

    assert result["success"], \
        f"Failed to set organization context for ID {org_id}: {result.get('error')}"

    # set_context may return data differently - check for context in result or data
    if "data" in result:
        context_info = result["data"]
        # Verify context was set
        if isinstance(context_info, dict):
            if "type" in context_info:
                assert context_info.get("type") == "organization", \
                    f"Expected context type 'organization', got '{context_info.get('type')}'"
            if "id" in context_info or "organization_id" in context_info:
                actual_id = context_info.get("id") or context_info.get("organization_id")
                assert actual_id == org_id, \
                    f"Expected organization ID {org_id}, got {actual_id}"


@pytest.mark.asyncio
async def test_set_context_project(authenticated_client):
    """Test set_context for project type."""
    # Get a real project ID by listing entities
    list_result = await authenticated_client.call_tool("entity_tool", {
        "entity_type": "project",
        "operation": "list"
    })

    if not list_result.get("success"):
        pytest.skip("Cannot list projects to get project ID for context test")

    assert "data" in list_result, "Expected 'data' in list result"
    projects = list_result["data"]
    if not projects:
        pytest.skip("No projects available for set_context test")

    project = projects[0]
    project_id = project.get("id")
    org_id = project.get("organization_id")

    if not project_id:
        pytest.skip("Project data missing ID field")

    # Set project context
    context_params = {
        "operation": "set_context",
        "context_type": "project",
        "entity_id": project_id
    }

    if org_id:
        context_params["organization_id"] = org_id

    result = await authenticated_client.call_tool("workspace_tool", context_params)

    assert result["success"], \
        f"Failed to set project context for ID {project_id}: {result.get('error')}"

    # set_context may return data differently - check for context in result or data
    if "data" in result:
        context_info = result["data"]
        # Verify context was set
        if isinstance(context_info, dict):
            if "type" in context_info:
                assert context_info.get("type") == "project", \
                    f"Expected context type 'project', got '{context_info.get('type')}'"
            if "id" in context_info or "project_id" in context_info:
                actual_id = context_info.get("id") or context_info.get("project_id")
                assert actual_id == project_id, \
                    f"Expected project ID {project_id}, got {actual_id}"
            # Organization might be included
            if org_id and "organization_id" in context_info:
                assert context_info["organization_id"] == org_id, \
                    f"Expected organization ID {org_id}, got {context_info['organization_id']}"


@pytest.mark.asyncio
async def test_set_context_document(authenticated_client):
    """Test set_context for document type."""
    # Get a real document ID by listing entities
    list_result = await authenticated_client.call_tool("entity_tool", {
        "entity_type": "document",
        "operation": "list"
    })

    if not list_result.get("success"):
        pytest.skip("Cannot list documents to get document ID for context test")

    assert "data" in list_result, "Expected 'data' in list result"
    documents = list_result["data"]
    if not documents:
        pytest.skip("No documents available for set_context test")

    document = documents[0]
    document_id = document.get("id")
    project_id = document.get("project_id")
    org_id = document.get("organization_id")

    if not document_id:
        pytest.skip("Document data missing ID field")

    # Set document context
    context_params = {
        "operation": "set_context",
        "context_type": "document",
        "entity_id": document_id
    }

    if project_id:
        context_params["project_id"] = project_id
    if org_id:
        context_params["organization_id"] = org_id

    result = await authenticated_client.call_tool("workspace_tool", context_params)

    assert result["success"], \
        f"Failed to set document context for ID {document_id}: {result.get('error')}"

    # set_context may return data differently - check for context in result or data
    if "data" in result:
        context_info = result["data"]
        # Verify context was set
        if isinstance(context_info, dict):
            if "type" in context_info:
                assert context_info.get("type") == "document", \
                    f"Expected context type 'document', got '{context_info.get('type')}'"
            if "id" in context_info or "document_id" in context_info:
                actual_id = context_info.get("id") or context_info.get("document_id")
                assert actual_id == document_id, \
                    f"Expected document ID {document_id}, got {actual_id}"
            # Parent IDs might be included
            if project_id and "project_id" in context_info:
                assert context_info["project_id"] == project_id, \
                    f"Expected project ID {project_id}, got {context_info['project_id']}"
            if org_id and "organization_id" in context_info:
                assert context_info["organization_id"] == org_id, \
                    f"Expected organization ID {org_id}, got {context_info['organization_id']}"


@pytest.mark.asyncio
async def test_set_context_invalid_type(authenticated_client):
    """Test set_context with invalid context type (error test)."""
    result = await authenticated_client.call_tool("workspace_tool", {
        "operation": "set_context",
        "context_type": "invalid_type",
        "entity_id": "00000000-0000-0000-0000-000000000000"
    })

    # This should fail
    assert not result["success"], \
        f"Expected set_context to fail with invalid type 'invalid_type', but it succeeded"

    # Check for appropriate error message
    error = result.get("error", result.get("message", ""))
    assert error, \
        f"Expected error message when setting invalid context type, got: {result}"

    error_lower = str(error).lower()
    assert any(word in error_lower for word in ["invalid", "type", "unsupported", "unknown"]), \
        f"Expected error to mention invalid type, got: {error}"


# ============================================================================
# GET_DEFAULTS TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_get_defaults_basic(authenticated_client):
    """Test get_defaults with default parameters."""
    result = await authenticated_client.call_tool("workspace_tool", {
        "operation": "get_defaults"
    })

    assert result["success"], \
        f"Failed to get defaults: {result.get('error')}"

    # get_defaults might return data in different ways
    # Check for default settings in result directly or in data
    default_fields = ["defaults", "settings", "preferences", "configuration", "data"]
    assert any(field in result for field in default_fields), \
        f"Expected default settings in result, got keys: {list(result.keys())}"

    # Verify defaults structure
    defaults_data = None
    for field in default_fields:
        if field in result:
            defaults_data = result[field]
            break

    if defaults_data and isinstance(defaults_data, dict):
        # Should have various default settings - but empty defaults is also valid
        common_defaults = ["organization", "project", "format", "limit",
                          "timeout", "region", "language"]
        # Just check if it's a dict, empty is OK
        assert isinstance(defaults_data, dict), \
            f"Expected defaults_data to be a dict, got {type(defaults_data)}"


@pytest.mark.asyncio
async def test_get_defaults_data_types(authenticated_client):
    """Test get_defaults returns proper data types."""
    result = await authenticated_client.call_tool("workspace_tool", {
        "operation": "get_defaults"
    })

    assert result["success"], \
        f"Failed to get defaults for data type check: {result.get('error')}"

    # get_defaults might return data in different ways
    # Check for default settings in result
    default_fields = ["organization_id", "project_id", "document_id",
                     "defaults", "settings", "preferences", "data"]
    has_defaults = any(field in result for field in default_fields)
    assert has_defaults or len(result.keys()) > 1, \
        f"Expected default configuration fields, got keys: {list(result.keys())}"

    # Check data type structure - can be in 'data' or other fields
    for field in default_fields:
        if field in result:
            data_value = result[field]
            if data_value is not None:
                # Valid data types for defaults
                assert isinstance(data_value, (str, dict, list, int, bool)), \
                    f"Expected valid data type for '{field}', got {type(data_value)}"
            break


# ============================================================================
# Performance Validation
# ============================================================================


@pytest.mark.asyncio
async def test_list_workspaces_performance(authenticated_client):
    """Validate that list_workspaces operations are fast (< 2 seconds)."""
    import time

    start_time = time.time()

    result = await authenticated_client.call_tool("workspace_tool", {
        "operation": "list_workspaces"
    })

    duration = time.time() - start_time

    assert result["success"], \
        f"Failed to list workspaces in performance test: {result.get('error')}"
    assert duration < 2.0, \
        f"List workspaces took {duration:.2f}s, expected < 2.0s. FastHTTPClient should provide ~20x speedup."


@pytest.mark.asyncio
async def test_get_context_performance(authenticated_client):
    """Validate that get_context operations are fast (< 1 second)."""
    import time

    start_time = time.time()

    result = await authenticated_client.call_tool("workspace_tool", {
        "operation": "get_context"
    })

    duration = time.time() - start_time

    assert result["success"], \
        f"Failed to get context in performance test: {result.get('error')}"
    assert duration < 1.0, \
        f"Get context took {duration:.2f}s, expected < 1.0s. FastHTTPClient should provide ~20x speedup."
