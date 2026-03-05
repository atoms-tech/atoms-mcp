"""
Integration Test: Requirements Management Workflow

This module tests comprehensive requirements management workflows:
- Requirements creation and organization
- Status tracking and updates
- Bulk operations
- Requirements relationships
- Search and filtering
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


class TestRequirementsManagement:
    """Test comprehensive requirements management workflows."""

    @pytest.mark.asyncio
    async def test_requirements_creation_and_organization(self, mcp_client):
        """Test creating and organizing requirements."""
        # Create organization and project
        org_result = await call_mcp(
            mcp_client,
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "organization",
                "data": {
                    "name": f"Requirements Test Org {uuid.uuid4().hex[:8]}",
                    "description": "Organization for requirements testing",
                },
            },
        )

        assert org_result["success"] is True
        org_id = org_result["entity"]["id"]

        project_result = await call_mcp(
            mcp_client,
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "project",
                "data": {
                    "name": f"Requirements Test Project {uuid.uuid4().hex[:8]}",
                    "description": "Project for requirements testing",
                    "organization_id": org_id,
                },
            },
        )

        assert project_result["success"] is True
        project_id = project_result["entity"]["id"]

        # Create requirements with different priorities and categories
        requirements_data = [
            {
                "title": "User Authentication",
                "description": "Implement secure user authentication system",
                "priority": "high",
                "project_id": project_id,
                "metadata": {"category": "security", "complexity": "high", "estimated_hours": 40},
            },
            {
                "title": "Data Validation",
                "description": "Implement data validation rules",
                "priority": "medium",
                "project_id": project_id,
                "metadata": {"category": "data", "complexity": "medium", "estimated_hours": 20},
            },
            {
                "title": "API Documentation",
                "description": "Create comprehensive API documentation",
                "priority": "low",
                "project_id": project_id,
                "metadata": {"category": "documentation", "complexity": "low", "estimated_hours": 15},
            },
            {
                "title": "Performance Optimization",
                "description": "Optimize application performance",
                "priority": "medium",
                "project_id": project_id,
                "metadata": {"category": "performance", "complexity": "high", "estimated_hours": 30},
            },
        ]

        created_requirements = []
        for req_data in requirements_data:
            req_result = await call_mcp(
                mcp_client, "entity_tool", {"operation": "create", "entity_type": "requirement", "data": req_data}
            )

            assert req_result["success"] is True
            created_requirements.append(req_result["entity"]["id"])

        # Verify all requirements were created
        assert len(created_requirements) == 4

        # Test requirements listing with filters
        list_result = await call_mcp(
            mcp_client,
            "entity_tool",
            {"operation": "list", "entity_type": "requirement", "filters": {"project_id": project_id}},
        )

        assert list_result["success"] is True
        assert len(list_result["entities"]) == 4

        # Test filtering by priority
        high_priority_result = await call_mcp(
            mcp_client,
            "entity_tool",
            {
                "operation": "list",
                "entity_type": "requirement",
                "filters": {"project_id": project_id, "priority": "high"},
            },
        )

        assert high_priority_result["success"] is True
        assert len(high_priority_result["entities"]) == 1
        assert high_priority_result["entities"][0]["title"] == "User Authentication"

        # Test filtering by metadata
        security_result = await call_mcp(
            mcp_client,
            "entity_tool",
            {
                "operation": "list",
                "entity_type": "requirement",
                "filters": {"project_id": project_id, "metadata.category": "security"},
            },
        )

        assert security_result["success"] is True
        assert len(security_result["entities"]) == 1
        assert security_result["entities"][0]["title"] == "User Authentication"

    @pytest.mark.asyncio
    async def test_requirements_status_tracking(self, mcp_client):
        """Test requirements status tracking and updates."""
        # Create project
        project_result = await call_mcp(
            mcp_client,
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "project",
                "data": {
                    "name": f"Status Test Project {uuid.uuid4().hex[:8]}",
                    "description": "Project for status testing",
                },
            },
        )

        assert project_result["success"] is True
        project_id = project_result["entity"]["id"]

        # Create requirements with different initial statuses
        requirements_data = [
            {
                "title": "Requirement 1",
                "description": "First requirement",
                "priority": "high",
                "project_id": project_id,
                "status": "draft",
            },
            {
                "title": "Requirement 2",
                "description": "Second requirement",
                "priority": "medium",
                "project_id": project_id,
                "status": "review",
            },
            {
                "title": "Requirement 3",
                "description": "Third requirement",
                "priority": "low",
                "project_id": project_id,
                "status": "approved",
            },
        ]

        created_requirements = []
        for req_data in requirements_data:
            req_result = await call_mcp(
                mcp_client, "entity_tool", {"operation": "create", "entity_type": "requirement", "data": req_data}
            )

            assert req_result["success"] is True
            created_requirements.append(req_result["entity"]["id"])

        # Update statuses through workflow
        status_updates = [("draft", "review"), ("review", "approved"), ("approved", "in_progress")]

        for i, (from_status, to_status) in enumerate(status_updates):
            update_result = await call_mcp(
                mcp_client,
                "entity_tool",
                {
                    "operation": "update",
                    "entity_type": "requirement",
                    "entity_id": created_requirements[i],
                    "data": {
                        "status": to_status,
                        "metadata": {
                            "status_changed_at": datetime.now(UTC).isoformat(),
                            "status_changed_from": from_status,
                        },
                    },
                },
            )

            assert update_result["success"] is True

        # Verify final statuses
        for i, expected_status in enumerate(["review", "approved", "in_progress"]):
            req_result = await call_mcp(
                mcp_client,
                "entity_tool",
                {"operation": "get", "entity_type": "requirement", "entity_id": created_requirements[i]},
            )

            assert req_result["success"] is True
            assert req_result["entity"]["status"] == expected_status

    @pytest.mark.asyncio
    async def test_requirements_bulk_operations(self, mcp_client):
        """Test bulk operations on requirements."""
        # Create project
        project_result = await call_mcp(
            mcp_client,
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "project",
                "data": {
                    "name": f"Bulk Test Project {uuid.uuid4().hex[:8]}",
                    "description": "Project for bulk operations testing",
                },
            },
        )

        assert project_result["success"] is True
        project_id = project_result["entity"]["id"]

        # Create multiple requirements
        requirements_data = [
            {
                "title": f"Bulk Requirement {i}",
                "description": f"Description for requirement {i}",
                "priority": "medium",
                "project_id": project_id,
                "status": "draft",
            }
            for i in range(10)
        ]

        created_requirements = []
        for req_data in requirements_data:
            req_result = await call_mcp(
                mcp_client, "entity_tool", {"operation": "create", "entity_type": "requirement", "data": req_data}
            )

            assert req_result["success"] is True
            created_requirements.append(req_result["entity"]["id"])

        # Test bulk status update
        bulk_update_result = await call_mcp(
            mcp_client,
            "workflow_tool",
            {
                "operation": "bulk_status_update",
                "entity_type": "requirement",
                "entity_ids": created_requirements,
                "new_status": "in_progress",
            },
        )

        assert bulk_update_result["success"] is True
        assert bulk_update_result["entities_updated"] == 10

        # Verify all requirements have updated status
        for req_id in created_requirements:
            req_result = await call_mcp(
                mcp_client, "entity_tool", {"operation": "get", "entity_type": "requirement", "entity_id": req_id}
            )

            assert req_result["success"] is True
            assert req_result["entity"]["status"] == "in_progress"

        # Test bulk metadata update
        bulk_metadata_result = await call_mcp(
            mcp_client,
            "workflow_tool",
            {
                "operation": "bulk_status_update",
                "entity_type": "requirement",
                "entity_ids": created_requirements,
                "new_status": "completed",
                "metadata_update": {"completed_by": "test_user", "completed_at": datetime.now(UTC).isoformat()},
            },
        )

        assert bulk_metadata_result["success"] is True
        assert bulk_metadata_result["entities_updated"] == 10

    @pytest.mark.asyncio
    async def test_requirements_search_and_filtering(self, mcp_client):
        """Test requirements search and filtering capabilities."""
        # Create project
        project_result = await call_mcp(
            mcp_client,
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "project",
                "data": {
                    "name": f"Search Test Project {uuid.uuid4().hex[:8]}",
                    "description": "Project for search testing",
                },
            },
        )

        assert project_result["success"] is True
        project_id = project_result["entity"]["id"]

        # Create requirements with varied content for search testing
        requirements_data = [
            {
                "title": "User Authentication System",
                "description": "Implement secure user authentication with OAuth2",
                "priority": "high",
                "project_id": project_id,
                "metadata": {"category": "security", "technology": "oauth2"},
            },
            {
                "title": "Data Validation Rules",
                "description": "Implement comprehensive data validation for user input",
                "priority": "medium",
                "project_id": project_id,
                "metadata": {"category": "data", "technology": "validation"},
            },
            {
                "title": "API Documentation",
                "description": "Create comprehensive API documentation for developers",
                "priority": "low",
                "project_id": project_id,
                "metadata": {"category": "documentation", "technology": "swagger"},
            },
            {
                "title": "Performance Monitoring",
                "description": "Implement performance monitoring and alerting system",
                "priority": "medium",
                "project_id": project_id,
                "metadata": {"category": "monitoring", "technology": "metrics"},
            },
        ]

        created_requirements = []
        for req_data in requirements_data:
            req_result = await call_mcp(
                mcp_client, "entity_tool", {"operation": "create", "entity_type": "requirement", "data": req_data}
            )

            assert req_result["success"] is True
            created_requirements.append(req_result["entity"]["id"])

        # Test text search
        search_result = await call_mcp(
            mcp_client,
            "query_tool",
            {
                "operation": "search",
                "entity_types": ["requirement"],
                "search_query": "authentication",
                "filters": {"project_id": project_id},
            },
        )

        assert search_result["success"] is True
        assert len(search_result["entities"]) == 1
        assert "authentication" in search_result["entities"][0]["title"].lower()

        # Test metadata filtering
        security_result = await call_mcp(
            mcp_client,
            "query_tool",
            {
                "operation": "search",
                "entity_types": ["requirement"],
                "filters": {"project_id": project_id, "metadata.category": "security"},
            },
        )

        assert security_result["success"] is True
        assert len(security_result["entities"]) == 1
        assert security_result["entities"][0]["metadata"]["category"] == "security"

        # Test priority filtering
        high_priority_result = await call_mcp(
            mcp_client,
            "query_tool",
            {
                "operation": "search",
                "entity_types": ["requirement"],
                "filters": {"project_id": project_id, "priority": "high"},
            },
        )

        assert high_priority_result["success"] is True
        assert len(high_priority_result["entities"]) == 1
        assert high_priority_result["entities"][0]["priority"] == "high"
