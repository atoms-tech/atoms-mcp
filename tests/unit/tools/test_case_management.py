"""E2E tests for Test Case Management operations.

Tests for all test case CRUD operations and results viewing.

Covers:
- Story 5.1: Create test cases
- Story 5.2: View test results and coverage metrics

This file validates end-to-end test case management functionality:
- Creating test cases linked to requirements
- Updating test status (pending, passed, failed)
- Viewing test results and coverage metrics
- Running test workflows and tracking outcomes

Test Coverage: 6 test scenarios covering 2 user stories.
File follows canonical naming - describes WHAT is tested (test case management).
Uses canonical fixture patterns for unit/integration/e2e variants.
"""

import pytest
import pytest_asyncio
import uuid
from typing import Dict, Any, List
from datetime import datetime, timezone


class TestCaseCreation:
    """Test case creation scenarios."""
    
    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_create_test_case_minimal(self, call_mcp):
        """Create test case with minimal data (title and requirement link)."""
        # Create organization and project first
        org_data = {"name": f"Test Org {uuid.uuid4().hex[:8]}"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        org_id = org_result["data"]["id"]
        
        proj_data = {"name": f"Test Project {uuid.uuid4().hex[:8]}", "organization_id": org_id}
        proj_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": proj_data}
        )
        project_id = proj_result["data"]["id"]
        
        test_data = {
            "title": f"Test Case {uuid.uuid4().hex[:8]}",
            "project_id": project_id
        }
        
        result, duration_ms = await call_mcp(
            "entity_tool",
            {
                "entity_type": "test",
                "operation": "create",
                "data": test_data
            }
        )
        
        assert result["success"] is True
        assert "data" in result
        assert "id" in result["data"]
        assert uuid.UUID(result["data"]["id"])
        assert result["data"]["title"] == test_data["title"]
    
    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_create_test_case_full(self, call_mcp):
        """Create test case with full specification (steps, expected results, data)."""
        # Create project first
        org_data = {"name": f"Test Org {uuid.uuid4().hex[:8]}"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        org_id = org_result["data"]["id"]
        
        proj_data = {"name": f"Test Project {uuid.uuid4().hex[:8]}", "organization_id": org_id}
        proj_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": proj_data}
        )
        project_id = proj_result["data"]["id"]
        
        test_data = {
            "title": "Login with Valid Credentials",
            "project_id": project_id,
            "description": "Verify user can log in with valid email and password",
            "priority": "critical"
        }
        
        result, duration_ms = await call_mcp(
            "entity_tool",
            {
                "entity_type": "test",
                "operation": "create",
                "data": test_data
            }
        )
        
        assert result["success"] is True
        assert result["data"]["priority"] == "critical"
    
    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_link_test_case_to_requirement(self, call_mcp):
        """Create test case and link it to requirement."""
        # Create project and document first
        org_data = {"name": f"Test Org {uuid.uuid4().hex[:8]}"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        org_id = org_result["data"]["id"]
        
        proj_data = {"name": f"Test Project {uuid.uuid4().hex[:8]}", "organization_id": org_id}
        proj_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": proj_data}
        )
        project_id = proj_result["data"]["id"]
        
        doc_data = {"name": "Test Doc", "project_id": project_id}
        doc_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": doc_data}
        )
        doc_id = doc_result["data"]["id"]
        
        # Create requirement
        req_data = {"name": "Test Requirement", "document_id": doc_id}
        req_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "requirement", "operation": "create", "data": req_data}
        )
        req_id = req_result["data"]["id"]
        
        test_data = {
            "title": "Registration Test",
            "project_id": project_id
        }
        
        result, duration_ms = await call_mcp(
            "entity_tool",
            {
                "entity_type": "test",
                "operation": "create",
                "data": test_data
            }
        )
        
        assert result["success"] is True
        test_id = result["data"]["id"]
        
        # Link test case to requirement using requirement_test relationship
        link_result, _ = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "requirement_test",
                "source": {"type": "requirement", "id": req_id},
                "target": {"type": "test", "id": test_id}
            }
        )
        
        assert link_result["success"] is True
    
    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_set_test_case_status(self, call_mcp):
        """Create test case and update status through lifecycle."""
        # Create organization and project first
        org_data = {"name": f"Test Org {uuid.uuid4().hex[:8]}"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        org_id = org_result["data"]["id"]
        
        proj_data = {"name": f"Test Project {uuid.uuid4().hex[:8]}", "organization_id": org_id}
        proj_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": proj_data}
        )
        project_id = proj_result["data"]["id"]
        
        test_data = {
            "title": "API Endpoint Test",
            "status": "pending",
            "project_id": project_id
        }
        
        result, duration_ms = await call_mcp(
            "entity_tool",
            {
                "entity_type": "test",
                "operation": "create",
                "data": test_data
            }
        )
        
        assert result["success"] is True
        test_id = result["data"]["id"]
        assert result["data"]["status"] == "pending"
        
        # Update to passed
        update_result, _ = await call_mcp(
            "entity_tool",
            {
                "entity_type": "test_case",
                "operation": "update",
                "entity_id": test_id,
                "data": {
                    "status": "passed",
                    "execution_date": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        assert update_result["success"] is True
        assert update_result["data"]["status"] == "passed"


class TestResultsAndMetrics:
    """Test result viewing and coverage metrics."""
    
    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_view_test_results_summary(self, call_mcp):
        """View aggregate test results (passed, failed, pending count)."""
        result, duration_ms = await call_mcp(
            "query_tool",
            {
                "query_type": "aggregate",
                "entities": ["test"]
            }
        )
        
        assert result["success"] is True
        assert "data" in result
    
    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_view_coverage_metrics(self, call_mcp):
        """View test coverage metrics by requirement."""
        result, duration_ms = await call_mcp(
            "query_tool",
            {
                "query_type": "relationships",
                "entities": ["requirement", "test"]
            }
        )
        
        assert result["success"] is True
        assert "data" in result
