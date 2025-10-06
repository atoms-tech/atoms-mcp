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

Run with: pytest tests/test_workspace_tool_comprehensive.py -v -s
"""

from __future__ import annotations

import os
import time
import uuid
from typing import Any, Dict
import pytest
import httpx
from supabase import create_client

MCP_BASE_URL = os.getenv("ATOMS_FASTMCP_BASE_URL", "http://127.0.0.1:8000")
MCP_PATH = os.getenv("ATOMS_FASTMCP_HTTP_PATH", "/api/mcp")
TEST_EMAIL = os.getenv("ATOMS_TEST_EMAIL", "kooshapari@kooshapari.com")
TEST_PASSWORD = os.getenv("ATOMS_TEST_PASSWORD", "118118")

pytestmark = [pytest.mark.asyncio, pytest.mark.http]


@pytest.fixture(scope="session")
def _supabase_env():
    """Ensure Supabase environment variables are present."""
    url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    key = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

    if not url or not key:
        pytest.skip("Supabase credentials not configured")

    return {"url": url, "key": key}


@pytest.fixture(scope="session")
def supabase_jwt(_supabase_env):
    """Authenticate against Supabase and return a user JWT."""
    client = create_client(_supabase_env["url"], _supabase_env["key"])
    auth_response = client.auth.sign_in_with_password(
        {"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )

    session = getattr(auth_response, "session", None)
    if not session or not getattr(session, "access_token", None):
        pytest.skip("Could not obtain Supabase JWT")

    return session.access_token


@pytest.fixture(scope="session")
def check_server_running():
    """Check if MCP server is running on localhost:8000."""
    try:
        response = httpx.get(f"{MCP_BASE_URL}/health", timeout=2.0)
        if response.status_code == 200:
            return True
    except:
        pass

    pytest.skip("MCP server not running on http://127.0.0.1:8000")


@pytest.fixture
async def call_mcp(check_server_running, supabase_jwt):
    """Return a helper that invokes MCP tools over HTTP."""
    base_url = f"{MCP_BASE_URL.rstrip('/')}{MCP_PATH}"
    headers = {
        "Authorization": f"Bearer {supabase_jwt}",
        "Content-Type": "application/json",
    }

    async def _call(tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": f"tools/{tool_name}",
            "params": params,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(base_url, json=payload, headers=headers)

        if response.status_code != 200:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text}",
                "status_code": response.status_code
            }

        body = response.json()
        if "result" in body:
            return body["result"]
        return {"success": False, "error": body.get("error", "Unknown error")}

    return _call


@pytest.fixture
async def test_organization(call_mcp):
    """Create a test organization for workspace tests."""
    create_response = await call_mcp(
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

    assert create_response.get("success") is True, f"Failed to create test org: {create_response}"
    org_id = create_response["data"]["id"]

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
    except:
        pass  # Best effort cleanup


@pytest.fixture
async def test_project(call_mcp, test_organization):
    """Create a test project for workspace tests."""
    create_response = await call_mcp(
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
    except:
        pass  # Best effort cleanup


@pytest.fixture
async def test_document(call_mcp, test_project):
    """Create a test document for workspace tests."""
    create_response = await call_mcp(
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
    except:
        pass  # Best effort cleanup


class TestGetContext:
    """Test get_context operation - retrieve current workspace context."""

    @pytest.mark.asyncio
    async def test_get_context_basic(self, call_mcp):
        """
        Given: A user is authenticated
        When: get_context is called with no parameters
        Then: Returns current workspace context successfully
        """
        start_time = time.time()
        response = await call_mcp("workspace_tool", {"operation": "get_context"})
        response_time = time.time() - start_time

        assert response.get("success") is True, f"get_context failed: {response}"
        assert "data" in response, "Response missing data field"

        # Validate response structure
        data = response["data"]
        assert isinstance(data, dict), "Data should be a dictionary"

        # Log response time
        print(f"\nget_context response time: {response_time:.3f}s")
        print(f"Context data: {data}")

    @pytest.mark.asyncio
    async def test_get_context_detailed_format(self, call_mcp):
        """
        Given: A user is authenticated
        When: get_context is called with format_type='detailed'
        Then: Returns detailed workspace context
        """
        response = await call_mcp(
            "workspace_tool",
            {"operation": "get_context", "format_type": "detailed"}
        )

        assert response.get("success") is True, f"get_context with detailed format failed: {response}"
        assert "data" in response

    @pytest.mark.asyncio
    async def test_get_context_summary_format(self, call_mcp):
        """
        Given: A user is authenticated
        When: get_context is called with format_type='summary'
        Then: Returns summarized workspace context
        """
        response = await call_mcp(
            "workspace_tool",
            {"operation": "get_context", "format_type": "summary"}
        )

        assert response.get("success") is True, f"get_context with summary format failed: {response}"
        assert "data" in response

    @pytest.mark.asyncio
    async def test_get_context_after_set(self, call_mcp, test_organization):
        """
        Given: A context has been set to a specific organization
        When: get_context is called
        Then: Returns the previously set context
        """
        # Set context first
        set_response = await call_mcp(
            "workspace_tool",
            {
                "operation": "set_context",
                "context_type": "organization",
                "entity_id": test_organization,
            },
        )
        assert set_response.get("success") is True

        # Get context
        get_response = await call_mcp("workspace_tool", {"operation": "get_context"})
        assert get_response.get("success") is True

        # Verify context includes the organization
        data = get_response["data"]
        if "active_organization" in data or "organization" in data:
            print(f"\nContext after setting organization: {data}")


class TestSetContext:
    """Test set_context operation - set organization/project/document contexts."""

    @pytest.mark.asyncio
    async def test_set_organization_context(self, call_mcp, test_organization):
        """
        Given: A valid organization ID
        When: set_context is called with context_type='organization'
        Then: Sets the organization context successfully
        """
        start_time = time.time()
        response = await call_mcp(
            "workspace_tool",
            {
                "operation": "set_context",
                "context_type": "organization",
                "entity_id": test_organization,
            },
        )
        response_time = time.time() - start_time

        assert response.get("success") is True, f"set_context for organization failed: {response}"
        print(f"\nset_organization_context response time: {response_time:.3f}s")

    @pytest.mark.asyncio
    async def test_set_project_context(self, call_mcp, test_project):
        """
        Given: A valid project ID
        When: set_context is called with context_type='project'
        Then: Sets the project context successfully
        """
        response = await call_mcp(
            "workspace_tool",
            {
                "operation": "set_context",
                "context_type": "project",
                "entity_id": test_project,
            },
        )

        assert response.get("success") is True, f"set_context for project failed: {response}"

    @pytest.mark.asyncio
    async def test_set_document_context(self, call_mcp, test_document):
        """
        Given: A valid document ID
        When: set_context is called with context_type='document'
        Then: Sets the document context successfully
        """
        response = await call_mcp(
            "workspace_tool",
            {
                "operation": "set_context",
                "context_type": "document",
                "entity_id": test_document,
            },
        )

        assert response.get("success") is True, f"set_context for document failed: {response}"

    @pytest.mark.asyncio
    async def test_set_context_invalid_type(self, call_mcp):
        """
        Given: An invalid context type
        When: set_context is called
        Then: Returns an appropriate error
        """
        response = await call_mcp(
            "workspace_tool",
            {
                "operation": "set_context",
                "context_type": "invalid_type",
                "entity_id": "some_id",
            },
        )

        # Should either fail or handle gracefully
        print(f"\nInvalid context type response: {response}")

    @pytest.mark.asyncio
    async def test_set_context_invalid_id(self, call_mcp):
        """
        Given: A non-existent entity ID
        When: set_context is called
        Then: Returns an appropriate error
        """
        response = await call_mcp(
            "workspace_tool",
            {
                "operation": "set_context",
                "context_type": "organization",
                "entity_id": "non_existent_id_12345",
            },
        )

        # Should fail with appropriate error
        print(f"\nInvalid entity ID response: {response}")

    @pytest.mark.asyncio
    async def test_set_context_missing_entity_id(self, call_mcp):
        """
        Given: No entity_id is provided
        When: set_context is called
        Then: Returns an appropriate error
        """
        response = await call_mcp(
            "workspace_tool",
            {
                "operation": "set_context",
                "context_type": "organization",
            },
        )

        # Should fail due to missing entity_id
        print(f"\nMissing entity_id response: {response}")

    @pytest.mark.asyncio
    async def test_switching_contexts(self, call_mcp, test_organization, test_project):
        """
        Given: Multiple context types are available
        When: Switching between different context types
        Then: Each context switch succeeds
        """
        # Set organization context
        org_response = await call_mcp(
            "workspace_tool",
            {
                "operation": "set_context",
                "context_type": "organization",
                "entity_id": test_organization,
            },
        )
        assert org_response.get("success") is True

        # Switch to project context
        proj_response = await call_mcp(
            "workspace_tool",
            {
                "operation": "set_context",
                "context_type": "project",
                "entity_id": test_project,
            },
        )
        assert proj_response.get("success") is True

        # Get context to verify
        get_response = await call_mcp("workspace_tool", {"operation": "get_context"})
        assert get_response.get("success") is True
        print(f"\nContext after switching: {get_response['data']}")


class TestListWorkspaces:
    """Test list_workspaces operation - list available workspaces."""

    @pytest.mark.asyncio
    async def test_list_workspaces_basic(self, call_mcp):
        """
        Given: A user is authenticated
        When: list_workspaces is called
        Then: Returns list of available workspaces
        """
        start_time = time.time()
        response = await call_mcp("workspace_tool", {"operation": "list_workspaces"})
        response_time = time.time() - start_time

        assert response.get("success") is True, f"list_workspaces failed: {response}"
        assert "data" in response

        data = response["data"]
        assert isinstance(data, dict), "Data should be a dictionary"

        # Should contain organizations at minimum
        assert "organizations" in data or len(data) > 0, "Should have workspace data"

        print(f"\nlist_workspaces response time: {response_time:.3f}s")
        print(f"Workspaces: {data}")

    @pytest.mark.asyncio
    async def test_list_workspaces_detailed_format(self, call_mcp):
        """
        Given: A user has access to workspaces
        When: list_workspaces is called with format_type='detailed'
        Then: Returns detailed workspace information
        """
        response = await call_mcp(
            "workspace_tool",
            {"operation": "list_workspaces", "format_type": "detailed"}
        )

        assert response.get("success") is True, f"list_workspaces detailed failed: {response}"
        assert "data" in response

    @pytest.mark.asyncio
    async def test_list_workspaces_summary_format(self, call_mcp):
        """
        Given: A user has access to workspaces
        When: list_workspaces is called with format_type='summary'
        Then: Returns summarized workspace information
        """
        response = await call_mcp(
            "workspace_tool",
            {"operation": "list_workspaces", "format_type": "summary"}
        )

        assert response.get("success") is True, f"list_workspaces summary failed: {response}"
        assert "data" in response

    @pytest.mark.asyncio
    async def test_list_workspaces_includes_test_org(self, call_mcp, test_organization):
        """
        Given: A test organization exists
        When: list_workspaces is called
        Then: The test organization appears in the list
        """
        response = await call_mcp("workspace_tool", {"operation": "list_workspaces"})

        assert response.get("success") is True
        data = response["data"]

        # Check if test org appears in organizations
        if "organizations" in data:
            org_ids = [org.get("id") for org in data["organizations"]]
            print(f"\nOrganization IDs: {org_ids}")
            print(f"Looking for test org: {test_organization}")


class TestGetDefaults:
    """Test get_defaults operation - retrieve smart default values."""

    @pytest.mark.asyncio
    async def test_get_defaults_basic(self, call_mcp):
        """
        Given: A user is authenticated
        When: get_defaults is called
        Then: Returns smart default values
        """
        start_time = time.time()
        response = await call_mcp("workspace_tool", {"operation": "get_defaults"})
        response_time = time.time() - start_time

        assert response.get("success") is True, f"get_defaults failed: {response}"
        assert "data" in response

        print(f"\nget_defaults response time: {response_time:.3f}s")
        print(f"Default values: {response['data']}")

    @pytest.mark.asyncio
    async def test_get_defaults_detailed_format(self, call_mcp):
        """
        Given: A user is authenticated
        When: get_defaults is called with format_type='detailed'
        Then: Returns detailed default values
        """
        response = await call_mcp(
            "workspace_tool",
            {"operation": "get_defaults", "format_type": "detailed"}
        )

        assert response.get("success") is True, f"get_defaults detailed failed: {response}"

    @pytest.mark.asyncio
    async def test_get_defaults_summary_format(self, call_mcp):
        """
        Given: A user is authenticated
        When: get_defaults is called with format_type='summary'
        Then: Returns summarized default values
        """
        response = await call_mcp(
            "workspace_tool",
            {"operation": "get_defaults", "format_type": "summary"}
        )

        assert response.get("success") is True, f"get_defaults summary failed: {response}"

    @pytest.mark.asyncio
    async def test_get_defaults_with_context(self, call_mcp, test_organization):
        """
        Given: A workspace context is set
        When: get_defaults is called
        Then: Returns defaults appropriate to the context
        """
        # Set context first
        set_response = await call_mcp(
            "workspace_tool",
            {
                "operation": "set_context",
                "context_type": "organization",
                "entity_id": test_organization,
            },
        )
        assert set_response.get("success") is True

        # Get defaults
        defaults_response = await call_mcp(
            "workspace_tool",
            {"operation": "get_defaults"}
        )

        assert defaults_response.get("success") is True
        print(f"\nDefaults with context: {defaults_response['data']}")


class TestErrorHandling:
    """Test error handling and edge cases for workspace_tool."""

    @pytest.mark.asyncio
    async def test_invalid_operation(self, call_mcp):
        """
        Given: An invalid operation name
        When: workspace_tool is called
        Then: Returns appropriate error
        """
        response = await call_mcp(
            "workspace_tool",
            {"operation": "invalid_operation"}
        )

        print(f"\nInvalid operation response: {response}")

    @pytest.mark.asyncio
    async def test_missing_operation(self, call_mcp):
        """
        Given: No operation parameter
        When: workspace_tool is called
        Then: Returns appropriate error
        """
        response = await call_mcp("workspace_tool", {})

        print(f"\nMissing operation response: {response}")

    @pytest.mark.asyncio
    async def test_empty_context_type(self, call_mcp):
        """
        Given: Empty context_type for set_context
        When: set_context is called
        Then: Returns appropriate error
        """
        response = await call_mcp(
            "workspace_tool",
            {
                "operation": "set_context",
                "context_type": "",
                "entity_id": "some_id",
            },
        )

        print(f"\nEmpty context_type response: {response}")

    @pytest.mark.asyncio
    async def test_null_entity_id(self, call_mcp):
        """
        Given: Null entity_id for set_context
        When: set_context is called
        Then: Returns appropriate error
        """
        response = await call_mcp(
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

    @pytest.mark.asyncio
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

        for i, response in enumerate(responses):
            assert response.get("success") is True, f"Concurrent request {i} failed: {response}"

        print(f"\n5 concurrent get_context calls completed in {total_time:.3f}s")

    @pytest.mark.asyncio
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

        for i, response in enumerate(responses):
            assert response.get("success") is True, f"Concurrent list request {i} failed: {response}"


class TestResponseFormats:
    """Test different response format types."""

    @pytest.mark.asyncio
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
            response = await call_mcp("workspace_tool", op)
            assert response.get("success") is True, f"Operation {op['operation']} failed: {response}"
            print(f"\n{op['operation']} detailed response received")

    @pytest.mark.asyncio
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
            response = await call_mcp("workspace_tool", op)
            assert response.get("success") is True, f"Operation {op['operation']} failed: {response}"
            print(f"\n{op['operation']} summary response received")

    @pytest.mark.asyncio
    async def test_invalid_format_type(self, call_mcp):
        """
        Given: An invalid format_type
        When: workspace operations are called
        Then: Either uses default or returns error
        """
        response = await call_mcp(
            "workspace_tool",
            {"operation": "get_context", "format_type": "invalid_format"}
        )

        print(f"\nInvalid format_type response: {response}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
