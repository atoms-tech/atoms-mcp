"""E2E tests for Test Case Management operations.

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
    async def test_create_test_case_minimal(self, call_mcp):
        """Create test case with minimal data (title and requirement link)."""
        req_id = str(uuid.uuid4())
        
        test_data = {
            "title": f"Test Case {uuid.uuid4().hex[:8]}",
            "requirement_id": req_id
        }
        
        result, duration_ms = await call_mcp(
            "entity_tool",
            {
                "entity_type": "test_case",
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
    async def test_create_test_case_full(self, call_mcp):
        """Create test case with full specification (steps, expected results, data)."""
        req_id = str(uuid.uuid4())
        
        test_data = {
            "title": "Login with Valid Credentials",
            "requirement_id": req_id,
            "description": "Verify user can log in with valid email and password",
            "preconditions": [
                "User is on login page",
                "Database has test user account"
            ],
            "test_steps": [
                {"step": 1, "action": "Enter valid email", "expected": "Email field populated"},
                {"step": 2, "action": "Enter valid password", "expected": "Password field masked"},
                {"step": 3, "action": "Click login button", "expected": "User redirected to dashboard"}
            ],
            "expected_result": "User successfully authenticated and dashboard loads",
            "priority": "critical"
        }
        
        result, duration_ms = await call_mcp(
            "entity_tool",
            {
                "entity_type": "test_case",
                "operation": "create",
                "data": test_data
            }
        )
        
        assert result["success"] is True
        assert result["data"]["priority"] == "critical"
        assert len(result["data"]["test_steps"]) == 3
        assert len(result["data"]["preconditions"]) == 2
    
    @pytest.mark.asyncio
    async def test_link_test_case_to_requirement(self, call_mcp):
        """Create test case and link it to requirement."""
        req_id = str(uuid.uuid4())
        
        test_data = {
            "title": "Registration Test"
        }
        
        result, duration_ms = await call_mcp(
            "entity_tool",
            {
                "entity_type": "test_case",
                "operation": "create",
                "data": test_data
            }
        )
        
        assert result["success"] is True
        test_id = result["data"]["id"]
        
        # Link test case to requirement
        link_result, _ = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "entity_a_id": test_id,
                "entity_b_id": req_id,
                "relationship_type": "validates"
            }
        )
        
        assert link_result["success"] is True
    
    @pytest.mark.asyncio
    async def test_set_test_case_status(self, call_mcp):
        """Create test case and update status through lifecycle."""
        test_data = {
            "title": "API Endpoint Test",
            "status": "pending"
        }
        
        result, duration_ms = await call_mcp(
            "entity_tool",
            {
                "entity_type": "test_case",
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
    async def test_view_test_results_summary(self, call_mcp):
        """View aggregate test results (passed, failed, pending count)."""
        result, duration_ms = await call_mcp(
            "data_query",
            {
                "query_type": "search",
                "entity_type": "test_case",
                "aggregations": {
                    "group_by": "status",
                    "count": True
                }
            }
        )
        
        assert result["success"] is True
        assert "aggregations" in result["data"]
    
    @pytest.mark.asyncio
    async def test_view_coverage_metrics(self, call_mcp):
        """View test coverage metrics by requirement."""
        result, duration_ms = await call_mcp(
            "data_query",
            {
                "query_type": "search",
                "entity_type": "requirement",
                "include_coverage": True,
                "aggregations": {
                    "coverage_percentage": True,
                    "validated_by_count": True
                }
            }
        )
        
        assert result["success"] is True
        assert "data" in result
