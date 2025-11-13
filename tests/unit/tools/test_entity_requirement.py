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
        """User can create requirements.
        
        User Story: User can create requirements
        Acceptance Criteria:
        - Requirement can be created with name and document_id
        - Requirement gets unique ID
        - Requirement is stored successfully
        """
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

        # Handle project_result parsing
        if hasattr(project_result, "data"):
            project_data = project_result.data.get("data", {})
        else:
            project_data = project_result.get("data", {})
        
        project_id = project_data.get("id")
        if not project_id:
            pytest.skip("Could not create test project")

        # Create document (requirement needs document_id, not project_id)
        doc_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "document",
                "data": {
                    "name": f"Req Doc {uuid.uuid4().hex[:8]}",
                    "project_id": project_id,
                },
            },
        )

        # Parse document result
        if hasattr(doc_result, "data"):
            doc_data = doc_result.data.get("data", {})
        else:
            doc_data = doc_result.get("data", {})
        
        document_id = doc_data.get("id")
        if not document_id:
            pytest.skip("Could not create test document")

        # Create requirement (requires document_id, not project_id)
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "requirement",
                "data": {
                    "name": f"Test Requirement {uuid.uuid4().hex[:8]}",
                    "document_id": document_id,
                    "description": "Requirement description",
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

        # Verify requirement was created
        assert success, f"Requirement creation failed: {result}"
        assert "id" in data, "Requirement should have an ID"
        assert data.get("document_id") == document_id, "Requirement should reference correct document"

    @pytest.mark.story("Requirements Traceability - User can view requirement")
    @pytest.mark.unit
    async def test_read_requirement(self, call_mcp, test_organization):
        """User can pull requirements from system.
        
        User Story: User can view requirement
        Acceptance Criteria:
        - Requirement can be retrieved by ID
        - Retrieved requirement has correct fields
        - Requirement data is accurate
        """
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

        # Parse project result
        if hasattr(project_result, "data"):
            project_data = project_result.data.get("data", {})
        else:
            project_data = project_result.get("data", {})
        
        project_id = project_data.get("id")
        if not project_id:
            pytest.skip("Could not create test project")

        # Create document (requirement needs document_id)
        doc_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "document",
                "data": {
                    "name": f"Req Doc {uuid.uuid4().hex[:8]}",
                    "project_id": project_id,
                },
            },
        )

        # Parse document result
        if hasattr(doc_result, "data"):
            doc_data = doc_result.data.get("data", {})
        else:
            doc_data = doc_result.get("data", {})
        
        document_id = doc_data.get("id")
        if not document_id:
            pytest.skip("Could not create test document")

        # Create requirement
        req_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "requirement",
                "data": {
                    "name": f"Req to Read {uuid.uuid4().hex[:8]}",
                    "document_id": document_id,
                },
            },
        )

        # Parse requirement result
        if hasattr(req_result, "data"):
            req_data = req_result.data.get("data", {})
        else:
            req_data = req_result.get("data", {})
        
        req_id = req_data.get("id")
        if not req_id:
            pytest.skip("Could not create test requirement")

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

        # Verify requirement was read successfully
        assert success, f"Requirement read failed: {result}"
        assert data.get("id") == req_id, "Retrieved requirement should have correct ID"
        assert data.get("document_id") == document_id, "Retrieved requirement should reference correct document"


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
