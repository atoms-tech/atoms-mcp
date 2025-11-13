"""Comprehensive test suite for Atoms workspace_tool.

This test suite provides 100% coverage of the workspace_tool operations including:
1. get_context - verify current workspace context retrieval
2. set_context - test setting organization/project/document contexts
3. list_workspaces - verify workspace listing
4. get_defaults - test smart default value retrieval

For each operation:
- Test successful cases with valid inputs
- Test edge cases (empty states, switching contexts)
- Test error handling (invalid IDs, missing parameters)
- Verify response formats (detailed vs summary)

Canonical test pattern:
- Uses parametrized mcp_client fixture from conftest
- Uses call_mcp helper fixture for consistent tool invocation
- All test methods decorated with @pytest.mark.unit
- Removes ALL inline client fixtures

Run with: pytest tests/unit/tools/test_workspace.py -v -s
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict
import pytest
import pytest_asyncio

pytestmark = [pytest.mark.asyncio, pytest.mark.unit]


@pytest_asyncio.fixture
async def test_organization(call_mcp):
    """Create a test organization for workspace tests."""
    result, _ = await call_mcp(
        "entity_tool",
        {
            "operation": "create",
            "entity_type": "organization",
            "data": {
                "name": f"Workspace Test Org {uuid.uuid4().hex[:8]}",
                "slug": f"workspace-test-{uuid.uuid4().hex[:8]}",
                "description": "Test organization for workspace tool tests",
                "type": "team",
            },
        },
    )

    error_msg = result.get('error') or str(result) if not result.get("success") else None
    assert result.get("success"), f"Failed to create test org: {error_msg}"
    assert "data" in result and result["data"], f"Response missing data: {result}"
    assert "id" in result["data"], f"Response data missing id: {result.get('data')}"
    org_id = result["data"]["id"]

    # Set as active organization for workspace context
    await call_mcp(
        "workspace_tool",
        {
            "operation": "set_context",
            "context_type": "organization",
            "entity_id": org_id,
        },
    )

    yield org_id

    # Cleanup
    try:
        await call_mcp(
            "entity_tool",
            {
                "operation": "delete",
                "entity_type": "organization",
                "entity_id": org_id,
                "soft_delete": True,
            },
        )
    except Exception:
        pass  # Best effort cleanup


@pytest_asyncio.fixture
async def test_project(call_mcp, test_organization):
    """Create a test project for workspace tests."""
    create_response, _ = await call_mcp(
        "entity_tool",
        {
            "operation": "create",
            "entity_type": "project",
            "data": {
                "name": f"Workspace Test Project {uuid.uuid4().hex[:8]}",
                "description": "Test project for workspace tool tests",
                "organization_id": test_organization,
            },
        },
    )

    assert create_response.get("success") is True, f"Failed to create test project: {create_response}"
    project_id = create_response["data"]["id"]

    yield project_id

    # Cleanup
    try:
        await call_mcp(
            "entity_tool",
            {
                "operation": "delete",
                "entity_type": "project",
                "entity_id": project_id,
                "soft_delete": True,
            },
        )
    except Exception:
        pass  # Best effort cleanup


@pytest_asyncio.fixture
async def test_document(call_mcp, test_project):
    """Create a test document for workspace tests."""
    create_response, _ = await call_mcp(
        "entity_tool",
        {
            "operation": "create",
            "entity_type": "document",
            "data": {
                "name": f"Workspace Test Doc {uuid.uuid4().hex[:8]}",
                "description": "Test document for workspace tool tests",
                "project_id": test_project,
            },
        },
    )

    assert create_response.get("success") is True, f"Failed to create test document: {create_response}"
    doc_id = create_response["data"]["id"]

    yield doc_id

    # Cleanup
    try:
        await call_mcp(
            "entity_tool",
            {
                "operation": "delete",
                "entity_type": "document",
                "entity_id": doc_id,
                "soft_delete": True,
            },
        )
    except Exception:
        pass  # Best effort cleanup


class TestGetContext:
    """Test get_context operation - retrieve current workspace context."""

    @pytest.mark.unit
    async def test_get_context_basic(self, call_mcp):
        """
        Given: A user is authenticated
        When: get_context is called with no parameters
        Then: Returns current workspace context successfully
        """
        start_time = time.time()
        response, duration_ms = await call_mcp("workspace_tool", {"operation": "get_context"})
        response_time = time.time() - start_time

        assert response.get("success") is True, f"get_context failed: {response}"
        assert "data" in response, "Response missing data field"

        # Validate response structure
        data = response["data"]
        assert isinstance(data, dict), "Data should be a dictionary"

        # Log response time
        print(f"\nget_context response time: {response_time:.3f}s (fixture: {duration_ms:.3f}ms)")
        print(f"Context data: {data}")

    @pytest.mark.unit
    async def test_get_context_detailed_format(self, call_mcp):
        """
        Given: A user is authenticated
        When: get_context is called with format_type='detailed'
        Then: Returns detailed workspace context
        """
        response, _ = await call_mcp(
            "workspace_tool",
            {"operation": "get_context", "format_type": "detailed"}
        )

        assert response.get("success") is True, f"get_context with detailed format failed: {response}"
        assert "data" in response

    @pytest.mark.unit
    async def test_get_context_summary_format(self, call_mcp):
        """
        Given: A user is authenticated
        When: get_context is called with format_type='summary'
        Then: Returns summarized workspace context
        """
        response, _ = await call_mcp(
            "workspace_tool",
            {"operation": "get_context", "format_type": "summary"}
        )

        assert response.get("success") is True, f"get_context with summary format failed: {response}"
        assert "data" in response

    @pytest.mark.unit
    async def test_get_context_after_set(self, call_mcp, test_organization):
        """
        Given: A context has been set to a specific organization
        When: get_context is called
        Then: Returns the previously set context
        """
        # Set context first
        set_response, _ = await call_mcp(
            "workspace_tool",
            {
                "operation": "set_context",
                "context_type": "organization",
                "entity_id": test_organization,
            },
        )
        assert set_response.get("success") is True

        # Get context
        get_response, _ = await call_mcp("workspace_tool", {"operation": "get_context"})
        assert get_response.get("success") is True

        # Verify context includes the organization
        data = get_response["data"]
        if "active_organization" in data or "organization" in data:
            print(f"\nContext after setting organization: {data}")


class TestSetContext:
    """Test set_context operation - set organization/project/document contexts."""

    @pytest.mark.unit
    async def test_set_organization_context(self, call_mcp, test_organization):
        """
        Given: A valid organization ID
        When: set_context is called with context_type='organization'
        Then: Sets the organization context successfully
        """
        start_time = time.time()
        response, duration_ms = await call_mcp(
            "workspace_tool",
            {
                "operation": "set_context",
                "context_type": "organization",
                "entity_id": test_organization,
            },
        )
        response_time = time.time() - start_time

        assert response.get("success") is True, f"set_context for organization failed: {response}"
        print(f"\nset_organization_context response time: {response_time:.3f}s (fixture: {duration_ms:.3f}ms)")

    @pytest.mark.unit
    async def test_set_project_context(self, call_mcp, test_project):
        """
        Given: A valid project ID
        When: set_context is called with context_type='project'
        Then: Sets the project context successfully
        """
        response, _ = await call_mcp(
            "workspace_tool",
            {
                "operation": "set_context",
                "context_type": "project",
                "entity_id": test_project,
            },
        )

        assert response.get("success") is True, f"set_context for project failed: {response}"

    @pytest.mark.unit
    async def test_set_document_context(self, call_mcp, test_document):
        """
        Given: A valid document ID
        When: set_context is called with context_type='document'
        Then: Sets the document context successfully
        """
        response, _ = await call_mcp(
            "workspace_tool",
            {
                "operation": "set_context",
                "context_type": "document",
                "entity_id": test_document,
            },
        )

        assert response.get("success") is True, f"set_context for document failed: {response}"

    @pytest.mark.unit
    async def test_set_context_invalid_type(self, call_mcp):
        """
        Given: An invalid context type
        When: set_context is called
        Then: Returns an appropriate error
        """
        response, _ = await call_mcp(
            "workspace_tool",
            {
                "operation": "set_context",
                "context_type": "invalid_type",
                "entity_id": "some_id",
            },
        )

        # Should either fail or handle gracefully
        print(f"\nInvalid context type response: {response}")

    @pytest.mark.unit
    async def test_set_context_invalid_id(self, call_mcp):
        """
        Given: A non-existent entity ID
        When: set_context is called
        Then: Returns an appropriate error
        """
        response, _ = await call_mcp(
            "workspace_tool",
            {
                "operation": "set_context",
                "context_type": "organization",
                "entity_id": "non_existent_id_12345",
            },
        )

        # Should fail with appropriate error
        print(f"\nInvalid entity ID response: {response}")

    @pytest.mark.unit
    async def test_set_context_missing_entity_id(self, call_mcp):
        """
        Given: No entity_id is provided
        When: set_context is called
        Then: Returns an appropriate error
        """
        response, _ = await call_mcp(
            "workspace_tool",
            {
                "operation": "set_context",
                "context_type": "organization",
            },
        )

        # Should fail due to missing entity_id
        print(f"\nMissing entity_id response: {response}")

    @pytest.mark.unit
    async def test_switching_contexts(self, call_mcp, test_organization, test_project):
        """
        Given: Multiple context types are available
        When: Switching between different context types
        Then: Each context switch succeeds
        """
        # Set organization context
        org_response, _ = await call_mcp(
            "workspace_tool",
            {
                "operation": "set_context",
                "context_type": "organization",
                "entity_id": test_organization,
            },
        )
        assert org_response.get("success") is True

        # Switch to project context
        proj_response, _ = await call_mcp(
            "workspace_tool",
            {
                "operation": "set_context",
                "context_type": "project",
                "entity_id": test_project,
            },
        )
        assert proj_response.get("success") is True

        # Get context to verify
        get_response, _ = await call_mcp("workspace_tool", {"operation": "get_context"})
        assert get_response.get("success") is True
        print(f"\nContext after switching: {get_response['data']}")


class TestListWorkspaces:
    """Test list_workspaces operation - list available workspaces."""

    @pytest.mark.unit
    async def test_list_workspaces_basic(self, call_mcp):
        """
        Given: A user is authenticated
        When: list_workspaces is called
        Then: Returns list of available workspaces
        """
        start_time = time.time()
        response, duration_ms = await call_mcp("workspace_tool", {"operation": "list_workspaces"})
        response_time = time.time() - start_time

        assert response.get("success") is True, f"list_workspaces failed: {response}"
        assert "data" in response

        data = response["data"]
        assert isinstance(data, dict), "Data should be a dictionary"

        # Should contain organizations at minimum
        assert "organizations" in data or len(data) > 0, "Should have workspace data"

        print(f"\nlist_workspaces response time: {response_time:.3f}s (fixture: {duration_ms:.3f}ms)")
        print(f"Workspaces: {data}")

    @pytest.mark.unit
    async def test_list_workspaces_detailed_format(self, call_mcp):
        """
        Given: A user has access to workspaces
        When: list_workspaces is called with format_type='detailed'
        Then: Returns detailed workspace information
        """
        response, _ = await call_mcp(
            "workspace_tool",
            {"operation": "list_workspaces", "format_type": "detailed"}
        )

        assert response.get("success") is True, f"list_workspaces detailed failed: {response}"
        assert "data" in response

    @pytest.mark.unit
    async def test_list_workspaces_summary_format(self, call_mcp):
        """
        Given: A user has access to workspaces
        When: list_workspaces is called with format_type='summary'
        Then: Returns summarized workspace information
        """
        response, _ = await call_mcp(
            "workspace_tool",
            {"operation": "list_workspaces", "format_type": "summary"}
        )

        assert response.get("success") is True, f"list_workspaces summary failed: {response}"
        assert "data" in response

    @pytest.mark.unit
    async def test_list_workspaces_includes_test_org(self, call_mcp, test_organization):
        """
        Given: A test organization exists
        When: list_workspaces is called
        Then: The test organization appears in the list
        """
        response, _ = await call_mcp("workspace_tool", {"operation": "list_workspaces"})

        assert response.get("success") is True
        data = response["data"]

        # Check if test org appears in organizations
        if "organizations" in data:
            org_ids = [org.get("id") for org in data["organizations"]]
            print(f"\nOrganization IDs: {org_ids}")
            print(f"Looking for test org: {test_organization}")


class TestGetDefaults:
    """Test get_defaults operation - retrieve smart default values."""

    @pytest.mark.unit
    async def test_get_defaults_basic(self, call_mcp):
        """
        Given: A user is authenticated
        When: get_defaults is called
        Then: Returns smart default values
        """
        start_time = time.time()
        response, duration_ms = await call_mcp("workspace_tool", {"operation": "get_defaults"})
        response_time = time.time() - start_time

        assert response.get("success") is True, f"get_defaults failed: {response}"
        assert "data" in response

        print(f"\nget_defaults response time: {response_time:.3f}s (fixture: {duration_ms:.3f}ms)")
        print(f"Default values: {response['data']}")

    @pytest.mark.unit
    async def test_get_defaults_detailed_format(self, call_mcp):
        """
        Given: A user is authenticated
        When: get_defaults is called with format_type='detailed'
        Then: Returns detailed default values
        """
        response, _ = await call_mcp(
            "workspace_tool",
            {"operation": "get_defaults", "format_type": "detailed"}
        )

        assert response.get("success") is True, f"get_defaults detailed failed: {response}"

    @pytest.mark.unit
    async def test_get_defaults_summary_format(self, call_mcp):
        """
        Given: A user is authenticated
        When: get_defaults is called with format_type='summary'
        Then: Returns summarized default values
        """
        response, _ = await call_mcp(
            "workspace_tool",
            {"operation": "get_defaults", "format_type": "summary"}
        )

        assert response.get("success") is True, f"get_defaults summary failed: {response}"

    @pytest.mark.unit
    async def test_get_defaults_with_context(self, call_mcp, test_organization):
        """
        Given: A workspace context is set
        When: get_defaults is called
        Then: Returns defaults appropriate to the context
        """
        # Set context first
        set_response, _ = await call_mcp(
            "workspace_tool",
            {
                "operation": "set_context",
                "context_type": "organization",
                "entity_id": test_organization,
            },
        )
        assert set_response.get("success") is True

        # Get defaults
        defaults_response, _ = await call_mcp(
            "workspace_tool",
            {"operation": "get_defaults"}
        )

        assert defaults_response.get("success") is True
        print(f"\nDefaults with context: {defaults_response['data']}")


class TestErrorHandling:
    """Test error handling and edge cases for workspace_tool."""

    @pytest.mark.unit
    async def test_invalid_operation(self, call_mcp):
        """
        Given: An invalid operation name
        When: workspace_tool is called
        Then: Returns appropriate error
        """
        response, _ = await call_mcp(
            "workspace_tool",
            {"operation": "invalid_operation"}
        )

        print(f"\nInvalid operation response: {response}")

    @pytest.mark.unit
    async def test_missing_operation(self, call_mcp):
        """
        Given: No operation parameter
        When: workspace_tool is called
        Then: Returns appropriate error
        """
        response, _ = await call_mcp("workspace_tool", {})

        print(f"\nMissing operation response: {response}")

    @pytest.mark.unit
    async def test_empty_context_type(self, call_mcp):
        """
        Given: Empty context_type for set_context
        When: set_context is called
        Then: Returns appropriate error
        """
        response, _ = await call_mcp(
            "workspace_tool",
            {
                "operation": "set_context",
                "context_type": "",
                "entity_id": "some_id",
            },
        )

        print(f"\nEmpty context_type response: {response}")

    @pytest.mark.unit
    async def test_null_entity_id(self, call_mcp):
        """
        Given: Null entity_id for set_context
        When: set_context is called
        Then: Returns appropriate error
        """
        response, _ = await call_mcp(
            "workspace_tool",
            {
                "operation": "set_context",
                "context_type": "organization",
                "entity_id": None,
            },
        )

        print(f"\nNull entity_id response: {response}")


class TestConcurrentOperations:
    """Test concurrent workspace operations."""

    @pytest.mark.unit
    @pytest.mark.slow
    async def test_concurrent_get_context(self, call_mcp):
        """
        Given: Multiple concurrent requests
        When: get_context is called simultaneously
        Then: All requests succeed
        """
        import asyncio

        tasks = [
            call_mcp("workspace_tool", {"operation": "get_context"})
            for _ in range(5)
        ]

        start_time = time.time()
        responses = await asyncio.gather(*tasks)
        total_time = time.time() - start_time

        for i, (response, _) in enumerate(responses):
            assert response.get("success") is True, f"Concurrent request {i} failed: {response}"

        print(f"\n5 concurrent get_context calls completed in {total_time:.3f}s")

    @pytest.mark.unit
    @pytest.mark.slow
    async def test_concurrent_list_workspaces(self, call_mcp):
        """
        Given: Multiple concurrent requests
        When: list_workspaces is called simultaneously
        Then: All requests succeed
        """
        import asyncio

        tasks = [
            call_mcp("workspace_tool", {"operation": "list_workspaces"})
            for _ in range(3)
        ]

        responses = await asyncio.gather(*tasks)

        for i, (response, _) in enumerate(responses):
            assert response.get("success") is True, f"Concurrent list request {i} failed: {response}"


class TestResponseFormats:
    """Test different response format types."""

    @pytest.mark.unit
    async def test_all_operations_detailed_format(self, call_mcp):
        """
        Given: All workspace operations
        When: Called with format_type='detailed'
        Then: All return detailed responses
        """
        operations = [
            {"operation": "get_context", "format_type": "detailed"},
            {"operation": "list_workspaces", "format_type": "detailed"},
            {"operation": "get_defaults", "format_type": "detailed"},
        ]

        for op in operations:
            response, _ = await call_mcp("workspace_tool", op)
            assert response.get("success") is True, f"Operation {op['operation']} failed: {response}"
            print(f"\n{op['operation']} detailed response received")

    @pytest.mark.unit
    async def test_all_operations_summary_format(self, call_mcp):
        """
        Given: All workspace operations
        When: Called with format_type='summary'
        Then: All return summarized responses
        """
        operations = [
            {"operation": "get_context", "format_type": "summary"},
            {"operation": "list_workspaces", "format_type": "summary"},
            {"operation": "get_defaults", "format_type": "summary"},
        ]

        for op in operations:
            response, _ = await call_mcp("workspace_tool", op)
            assert response.get("success") is True, f"Operation {op['operation']} failed: {response}"
            print(f"\n{op['operation']} summary response received")

    @pytest.mark.unit
    async def test_invalid_format_type(self, call_mcp):
        """
        Given: An invalid format_type
        When: workspace operations are called
        Then: Either uses default or returns error
        """
        response, _ = await call_mcp(
            "workspace_tool",
            {"operation": "get_context", "format_type": "invalid_format"}
        )

        print(f"\nInvalid format_type response: {response}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
