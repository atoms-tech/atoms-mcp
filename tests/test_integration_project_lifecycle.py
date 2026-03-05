"""
Integration Test: Complete Project Lifecycle

This module tests the complete project lifecycle from creation to completion:
- Project setup and initialization
- Requirements management
- Test case creation
- Status tracking
- Completion workflow
"""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime
from typing import Any

import httpx
import pytest

# Test configuration
MCP_BASE_URL = os.getenv("ATOMS_FASTMCP_BASE_URL", "http://127.0.0.1:8000")
MCP_PATH = os.getenv("ATOMS_FASTMCP_HTTP_PATH", "/api/mcp")
TEST_EMAIL = os.getenv("ATOMS_TEST_EMAIL", "kooshapari@kooshapari.com")
TEST_PASSWORD = os.getenv("ATOMS_TEST_PASSWORD", "118118")

pytestmark = [pytest.mark.asyncio, pytest.mark.integration]


@pytest.fixture(scope="session")
def supabase_env():
    """Ensure Supabase environment variables are present."""
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_ANON_KEY", "")

    if not url or not key:
        pytest.skip("Supabase environment variables not set")

    return {"url": url, "key": key}


@pytest.fixture(scope="session")
async def mcp_client(supabase_env):
    """Create authenticated MCP client for integration tests."""
    async with httpx.AsyncClient() as client:
        # Authenticate
        auth_response = await client.post(
            f"{MCP_BASE_URL}{MCP_PATH}",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "auth/login",
                "params": {"email": TEST_EMAIL, "password": TEST_PASSWORD},
            },
        )

        assert auth_response.status_code == 200
        auth_data = auth_response.json()
        assert "result" in auth_data
        assert "access_token" in auth_data["result"]

        # Set authorization header
        client.headers.update({"Authorization": f"Bearer {auth_data['result']['access_token']}"})

        yield client


async def call_mcp(mcp_client: httpx.AsyncClient, tool: str, params: dict[str, Any]) -> dict[str, Any]:
    """Helper function to call MCP tools."""
    response = await mcp_client.post(
        f"{MCP_BASE_URL}{MCP_PATH}",
        json={"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": tool, "arguments": params}},
    )

    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    return data["result"]


class TestProjectLifecycle:
    """Test complete project lifecycle workflow."""

    @pytest.mark.asyncio
    async def test_complete_project_lifecycle(self, mcp_client):
        """Test complete project lifecycle from creation to completion."""
        # Step 1: Create organization
        org_result = await call_mcp(
            mcp_client,
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "organization",
                "data": {
                    "name": f"Test Org {uuid.uuid4().hex[:8]}",
                    "description": "Test organization for lifecycle testing",
                    "metadata": {"industry": "technology", "size": "small"},
                },
            },
        )

        assert org_result["success"] is True
        org_id = org_result["entity"]["id"]

        # Step 2: Create project
        project_result = await call_mcp(
            mcp_client,
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "project",
                "data": {
                    "name": f"Lifecycle Test Project {uuid.uuid4().hex[:8]}",
                    "description": "Project for testing complete lifecycle",
                    "organization_id": org_id,
                    "metadata": {"type": "development", "priority": "high"},
                },
            },
        )

        assert project_result["success"] is True
        project_id = project_result["entity"]["id"]

        # Step 3: Create requirements
        requirements = [
            {
                "title": "User Authentication",
                "description": "Implement secure user authentication system",
                "priority": "high",
                "project_id": project_id,
                "metadata": {"complexity": "medium", "estimated_hours": 40},
            },
            {
                "title": "Data Validation",
                "description": "Implement data validation rules",
                "priority": "medium",
                "project_id": project_id,
                "metadata": {"complexity": "low", "estimated_hours": 20},
            },
            {
                "title": "API Documentation",
                "description": "Create comprehensive API documentation",
                "priority": "low",
                "project_id": project_id,
                "metadata": {"complexity": "low", "estimated_hours": 15},
            },
        ]

        created_requirements = []
        for req_data in requirements:
            req_result = await call_mcp(
                mcp_client, "entity_tool", {"operation": "create", "entity_type": "requirement", "data": req_data}
            )

            assert req_result["success"] is True
            created_requirements.append(req_result["entity"]["id"])

        # Step 4: Create test cases
        test_cases = [
            {
                "name": "Authentication Test",
                "description": "Test user authentication functionality",
                "project_id": project_id,
                "metadata": {"type": "unit", "coverage": "high"},
            },
            {
                "name": "Data Validation Test",
                "description": "Test data validation rules",
                "project_id": project_id,
                "metadata": {"type": "integration", "coverage": "medium"},
            },
            {
                "name": "API Documentation Test",
                "description": "Test API documentation completeness",
                "project_id": project_id,
                "metadata": {"type": "manual", "coverage": "low"},
            },
        ]

        created_tests = []
        for test_data in test_cases:
            test_result = await call_mcp(
                mcp_client, "entity_tool", {"operation": "create", "entity_type": "test", "data": test_data}
            )

            assert test_result["success"] is True
            created_tests.append(test_result["entity"]["id"])

        # Step 5: Create documents
        documents = [
            {
                "title": "API Documentation",
                "content": "Comprehensive API documentation for the project",
                "project_id": project_id,
                "metadata": {"type": "documentation", "format": "markdown"},
            },
            {
                "title": "User Guide",
                "content": "User guide for the application",
                "project_id": project_id,
                "metadata": {"type": "user_guide", "format": "markdown"},
            },
        ]

        created_documents = []
        for doc_data in documents:
            doc_result = await call_mcp(
                mcp_client, "entity_tool", {"operation": "create", "entity_type": "document", "data": doc_data}
            )

            assert doc_result["success"] is True
            created_documents.append(doc_result["entity"]["id"])

        # Step 6: Update requirement statuses
        for req_id in created_requirements:
            update_result = await call_mcp(
                mcp_client,
                "entity_tool",
                {
                    "operation": "update",
                    "entity_type": "requirement",
                    "entity_id": req_id,
                    "data": {"status": "in_progress"},
                },
            )

            assert update_result["success"] is True

        # Step 7: Update test statuses
        for test_id in created_tests:
            update_result = await call_mcp(
                mcp_client,
                "entity_tool",
                {"operation": "update", "entity_type": "test", "entity_id": test_id, "data": {"status": "passed"}},
            )

            assert update_result["success"] is True

        # Step 8: Update project status
        project_update_result = await call_mcp(
            mcp_client,
            "entity_tool",
            {
                "operation": "update",
                "entity_type": "project",
                "entity_id": project_id,
                "data": {
                    "status": "completed",
                    "metadata": {"completion_date": datetime.now(UTC).isoformat(), "final_status": "success"},
                },
            },
        )

        assert project_update_result["success"] is True

        # Step 9: Verify final state
        final_project = await call_mcp(
            mcp_client, "entity_tool", {"operation": "get", "entity_type": "project", "entity_id": project_id}
        )

        assert final_project["success"] is True
        assert final_project["entity"]["status"] == "completed"

        # Verify all requirements are in progress or completed
        for req_id in created_requirements:
            req_result = await call_mcp(
                mcp_client, "entity_tool", {"operation": "get", "entity_type": "requirement", "entity_id": req_id}
            )

            assert req_result["success"] is True
            assert req_result["entity"]["status"] in ["in_progress", "completed"]

        # Verify all tests are passed
        for test_id in created_tests:
            test_result = await call_mcp(
                mcp_client, "entity_tool", {"operation": "get", "entity_type": "test", "entity_id": test_id}
            )

            assert test_result["success"] is True
            assert test_result["entity"]["status"] == "passed"

    @pytest.mark.asyncio
    async def test_project_lifecycle_with_relationships(self, mcp_client):
        """Test project lifecycle with entity relationships."""
        # Create organization
        org_result = await call_mcp(
            mcp_client,
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "organization",
                "data": {
                    "name": f"Relationship Test Org {uuid.uuid4().hex[:8]}",
                    "description": "Organization for relationship testing",
                },
            },
        )

        assert org_result["success"] is True
        org_id = org_result["entity"]["id"]

        # Create project
        project_result = await call_mcp(
            mcp_client,
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "project",
                "data": {
                    "name": f"Relationship Test Project {uuid.uuid4().hex[:8]}",
                    "description": "Project for relationship testing",
                    "organization_id": org_id,
                },
            },
        )

        assert project_result["success"] is True
        project_id = project_result["entity"]["id"]

        # Create requirement
        req_result = await call_mcp(
            mcp_client,
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "requirement",
                "data": {
                    "title": "Test Requirement",
                    "description": "Test requirement for relationship testing",
                    "project_id": project_id,
                },
            },
        )

        assert req_result["success"] is True
        req_id = req_result["entity"]["id"]

        # Create test
        test_result = await call_mcp(
            mcp_client,
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "test",
                "data": {"name": "Test Case", "description": "Test case for requirement", "project_id": project_id},
            },
        )

        assert test_result["success"] is True
        test_id = test_result["entity"]["id"]

        # Create relationships
        # Link test to requirement
        link_result = await call_mcp(
            mcp_client,
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "tests_requirement",
                "source_type": "test",
                "source_id": test_id,
                "target_type": "requirement",
                "target_id": req_id,
            },
        )

        assert link_result["success"] is True

        # Verify relationship exists
        check_result = await call_mcp(
            mcp_client,
            "relationship_tool",
            {
                "operation": "check",
                "relationship_type": "tests_requirement",
                "source_type": "test",
                "source_id": test_id,
                "target_type": "requirement",
                "target_id": req_id,
            },
        )

        assert check_result["success"] is True
        assert check_result["exists"] is True

        # List relationships
        list_result = await call_mcp(
            mcp_client,
            "relationship_tool",
            {
                "operation": "list",
                "relationship_type": "tests_requirement",
                "source_type": "test",
                "source_id": test_id,
            },
        )

        assert list_result["success"] is True
        assert len(list_result["relationships"]) == 1
        assert list_result["relationships"][0]["target_id"] == req_id

    @pytest.mark.asyncio
    async def test_project_lifecycle_error_handling(self, mcp_client):
        """Test project lifecycle error handling and recovery."""
        # Try to create project with invalid organization
        project_result = await call_mcp(
            mcp_client,
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "project",
                "data": {
                    "name": "Error Test Project",
                    "description": "Project for error testing",
                    "organization_id": "invalid-org-id",
                },
            },
        )

        # Should fail gracefully
        assert project_result["success"] is False
        assert "error" in project_result

        # Create valid organization first
        org_result = await call_mcp(
            mcp_client,
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "organization",
                "data": {
                    "name": f"Error Test Org {uuid.uuid4().hex[:8]}",
                    "description": "Organization for error testing",
                },
            },
        )

        assert org_result["success"] is True
        org_id = org_result["entity"]["id"]

        # Now create project with valid organization
        project_result = await call_mcp(
            mcp_client,
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "project",
                "data": {
                    "name": "Error Test Project",
                    "description": "Project for error testing",
                    "organization_id": org_id,
                },
            },
        )

        assert project_result["success"] is True
        project_id = project_result["entity"]["id"]

        # Try to create requirement with invalid project
        req_result = await call_mcp(
            mcp_client,
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "requirement",
                "data": {
                    "title": "Test Requirement",
                    "description": "Test requirement",
                    "project_id": "invalid-project-id",
                },
            },
        )

        # Should fail gracefully
        assert req_result["success"] is False
        assert "error" in req_result

        # Create requirement with valid project
        req_result = await call_mcp(
            mcp_client,
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "requirement",
                "data": {"title": "Test Requirement", "description": "Test requirement", "project_id": project_id},
            },
        )

        assert req_result["success"] is True
