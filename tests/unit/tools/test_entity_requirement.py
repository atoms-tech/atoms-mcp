"""Entity tool tests - Requirement management.

Tests requirement-specific operations:
- Create requirement
- Read requirement
- Search requirements

User stories covered:
- User can create requirements
- User can pull requirements from system
- User can search requirements

Run with: pytest tests/unit/tools/test_entity_requirement.py -v
"""

import uuid
import pytest

pytestmark = [pytest.mark.asyncio, pytest.mark.unit]


class TestRequirementCRUD:
    """Test requirement CRUD operations."""

    @pytest.mark.story("Requirements Traceability - User can create requirement")
    @pytest.mark.unit
    async def test_create_requirement(self, call_mcp, test_organization):
        """User can create requirements."""
        # Create project first
        project_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "project",
                "data": {
                    "name": f"Req Project {uuid.uuid4().hex[:8]}",
                    "organization_id": test_organization,
                },
            },
        )

        if hasattr(project_result, "data"):
            project_id = project_result.data.get("data", {}).get("id")
        else:
            project_id = project_result.get("data", {}).get("id")

        # Create requirement
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "requirement",
                "data": {
                    "name": f"Test Requirement {uuid.uuid4().hex[:8]}",
                    "project_id": project_id,
                    "description": "Requirement description",
                    "requirement_type": "functional",
                    "priority": "high",
                },
            },
        )

        # Parse response
        if hasattr(result, "data"):
            success = result.data.get("success", False)
            data = result.data.get("data", {})
        else:
            success = result.get("success", False)
            data = result.get("data", {})

        assert success, "Requirement creation failed"
        assert "id" in data
        assert data.get("project_id") == project_id

    @pytest.mark.story("Requirements Traceability - User can view requirement")
    @pytest.mark.unit
    async def test_read_requirement(self, call_mcp, test_organization):
        """User can pull requirements from system."""
        # Create requirement first
        project_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "project",
                "data": {
                    "name": f"Req Project {uuid.uuid4().hex[:8]}",
                    "organization_id": test_organization,
                },
            },
        )

        if hasattr(project_result, "data"):
            project_id = project_result.data.get("data", {}).get("id")
        else:
            project_id = project_result.get("data", {}).get("id")

        req_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "requirement",
                "data": {
                    "name": f"Req to Read {uuid.uuid4().hex[:8]}",
                    "project_id": project_id,
                },
            },
        )

        if hasattr(req_result, "data"):
            req_id = req_result.data.get("data", {}).get("id")
        else:
            req_id = req_result.get("data", {}).get("id")

        # Read requirement
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "read",
                "entity_type": "requirement",
                "entity_id": req_id,
            }
        )

        # Parse response
        if hasattr(result, "data"):
            success = result.data.get("success", False)
            data = result.data.get("data", {})
        else:
            success = result.get("success", False)
            data = result.get("data", {})

        assert success, "Requirement read failed"
        assert data.get("id") == req_id


class TestRequirementSearch:
    """Test requirement search."""

    @pytest.mark.story("Requirements Traceability - User can search requirements")
    @pytest.mark.unit
    async def test_search_requirements(self, call_mcp):
        """User can search requirements."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "search",
                "entity_type": "requirement",
                "filters": {"term": "test"}
            }
        )

        # Parse response
        if hasattr(result, "data"):
            success = result.data.get("success", False)
        else:
            success = result.get("success", False)

        assert success, "Requirement search failed"
