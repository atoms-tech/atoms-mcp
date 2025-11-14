"""E2E tests for Requirements Traceability operations.

Tests for all requirements traceability CRUD operations and workflows.

Covers:
- Story 4.1: Create requirements
- Story 4.2: Pull requirements from system via workflow
- Story 4.3: Search requirements
- Story 4.4: Trace links between requirements and test cases

This file validates end-to-end requirements traceability functionality:
- Creating requirements from templates with validation
- Pulling requirements via workflows with filtering
- Searching requirements with various criteria
- Tracing requirement links and dependencies

Test Coverage: 14 test scenarios covering 4 user stories.
File follows canonical naming - describes WHAT is tested (requirements traceability).
Uses canonical fixture patterns for unit/integration/e2e variants.
"""

import pytest
import pytest_asyncio
import uuid
from typing import Dict, Any, List
from datetime import datetime, timezone


class TestRequirementCreation:
    """Test requirement creation scenarios (Story 4.1)."""
    
    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_create_requirement_minimal(self, call_mcp):
        """Create requirement with minimal required data (title only)."""
        req_data = {
            "title": f"Req {uuid.uuid4().hex[:8]}",
            "entity_type": "requirement"
        }
        
        result, duration_ms = await call_mcp(
            "entity_tool",
            {
                "entity_type": "requirement",
                "operation": "create",
                "data": req_data
            }
        )
        
        assert result["success"] is True
        assert "data" in result
        assert "id" in result["data"]
        assert uuid.UUID(result["data"]["id"])
        assert result["data"]["title"] == req_data["title"]
    
    @pytest.mark.asyncio
    async def test_create_requirement_from_template(self, call_mcp):
        """Create requirement using predefined template."""
        req_data = {
            "title": "Login Feature",
            "template": "functional_requirement",
            "priority": "high",
            "status": "draft",
            "acceptance_criteria": [
                "User can enter email",
                "User can enter password",
                "System validates credentials"
            ]
        }
        
        result, duration_ms = await call_mcp(
            "entity_tool",
            {
                "entity_type": "requirement",
                "operation": "create",
                "data": req_data
            }
        )
        
        assert result["success"] is True
        assert result["data"]["priority"] == "high"
        assert result["data"]["status"] == "draft"
        assert len(result["data"]["acceptance_criteria"]) == 3
    
    @pytest.mark.asyncio
    async def test_create_requirement_link_to_document(self, call_mcp):
        """Create requirement and link it to a document."""
        doc_id = str(uuid.uuid4())
        req_data = {
            "title": "Auth System",
            "document_id": doc_id
        }
        
        result, duration_ms = await call_mcp(
            "entity_tool",
            {
                "entity_type": "requirement",
                "operation": "create",
                "data": req_data
            }
        )
        
        assert result["success"] is True
        req_id = result["data"]["id"]
        
        # Link requirement to document
        link_result, _ = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "entity_a_id": req_id,
                "entity_b_id": doc_id,
                "relationship_type": "defined_in"
            }
        )
        
        assert link_result["success"] is True
    
    @pytest.mark.asyncio
    async def test_create_requirement_link_to_project(self, call_mcp):
        """Create requirement and link it to a project."""
        project_id = str(uuid.uuid4())
        req_data = {
            "title": "Data API",
            "project_id": project_id
        }
        
        result, duration_ms = await call_mcp(
            "entity_tool",
            {
                "entity_type": "requirement",
                "operation": "create",
                "data": req_data
            }
        )
        
        assert result["success"] is True
        req_id = result["data"]["id"]
        
        # Link to project
        link_result, _ = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "entity_a_id": req_id,
                "entity_b_id": project_id,
                "relationship_type": "fulfills"
            }
        )
        
        assert link_result["success"] is True


class TestRequirementWorkflow:
    """Test requirement pulling via workflows."""
    
    @pytest.mark.asyncio
    async def test_pull_requirements_from_document(self, call_mcp):
        """Pull requirements from linked document via workflow."""
        doc_id = str(uuid.uuid4())
        
        result, duration_ms = await call_mcp(
            "workflow_execute",
            {
                "workflow_name": "pull_requirements",
                "parameters": {
                    "document_id": doc_id,
                    "template": "functional_requirement"
                }
            }
        )
        
        assert result["success"] is True
        assert "data" in result
        assert "requirements_created" in result["data"]
    
    @pytest.mark.asyncio
    async def test_pull_requirements_with_filtering(self, call_mcp):
        """Pull requirements with priority/status filtering."""
        doc_id = str(uuid.uuid4())
        
        result, duration_ms = await call_mcp(
            "workflow_execute",
            {
                "workflow_name": "pull_requirements",
                "parameters": {
                    "document_id": doc_id,
                    "filter": {
                        "priority": "high",
                        "status": "draft"
                    }
                }
            }
        )
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_pull_requirements_with_validation(self, call_mcp):
        """Pull requirements and validate against acceptance criteria."""
        doc_id = str(uuid.uuid4())
        
        result, duration_ms = await call_mcp(
            "workflow_execute",
            {
                "workflow_name": "pull_requirements_with_validation",
                "parameters": {
                    "document_id": doc_id,
                    "validate_criteria": True
                }
            }
        )
        
        assert result["success"] is True
        assert "validation_results" in result["data"]


class TestRequirementSearch:
    """Test requirement search capabilities."""
    
    @pytest.mark.asyncio
    async def test_search_requirements_by_title(self, call_mcp):
        """Search requirements by title keywords."""
        result, duration_ms = await call_mcp(
            "data_query",
            {
                "query_type": "search",
                "entity_type": "requirement",
                "search_term": "authentication",
                "search_mode": "keyword"
            }
        )
        
        assert result["success"] is True
        assert "results" in result["data"]
    
    @pytest.mark.asyncio
    async def test_search_requirements_by_priority(self, call_mcp):
        """Search requirements by priority level."""
        result, duration_ms = await call_mcp(
            "data_query",
            {
                "query_type": "search",
                "entity_type": "requirement",
                "filters": {
                    "priority": ["high", "critical"]
                }
            }
        )
        
        assert result["success"] is True
        assert "results" in result["data"]
    
    @pytest.mark.asyncio
    async def test_search_requirements_by_status(self, call_mcp):
        """Search requirements by status."""
        result, duration_ms = await call_mcp(
            "data_query",
            {
                "query_type": "search",
                "entity_type": "requirement",
                "filters": {
                    "status": ["draft", "pending_review"]
                }
            }
        )
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_search_requirements_advanced(self, call_mcp):
        """Search requirements with advanced filters (priority + status + created date)."""
        result, duration_ms = await call_mcp(
            "data_query",
            {
                "query_type": "search",
                "entity_type": "requirement",
                "filters": {
                    "priority": "high",
                    "status": "draft",
                    "created_after": "2025-11-01",
                    "created_before": "2025-11-30"
                },
                "sort": {"field": "created_at", "order": "desc"}
            }
        )
        
        assert result["success"] is True


class TestRequirementTracing:
    """Test requirement tracing and link analysis."""
    
    @pytest.mark.asyncio
    async def test_trace_requirement_to_document(self, call_mcp):
        """Trace which document a requirement is defined in."""
        req_id = str(uuid.uuid4())
        
        result, duration_ms = await call_mcp(
            "relationship_tool",
            {
                "operation": "get_outbound",
                "entity_id": req_id,
                "relationship_type": "defined_in"
            }
        )
        
        assert result["success"] is True
        assert "relationships" in result["data"]
    
    @pytest.mark.asyncio
    async def test_trace_requirement_to_project(self, call_mcp):
        """Trace which project a requirement fulfills."""
        req_id = str(uuid.uuid4())
        
        result, duration_ms = await call_mcp(
            "relationship_tool",
            {
                "operation": "get_outbound",
                "entity_id": req_id,
                "relationship_type": "fulfills"
            }
        )
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_trace_requirement_dependents(self, call_mcp):
        """Trace test cases and documents that depend on a requirement."""
        req_id = str(uuid.uuid4())
        
        result, duration_ms = await call_mcp(
            "relationship_tool",
            {
                "operation": "get_inbound",
                "entity_id": req_id,
                "relationship_type": "validates"
            }
        )
        
        assert result["success"] is True
        assert "relationships" in result["data"]
    
    @pytest.mark.asyncio
    async def test_trace_requirement_chain(self, call_mcp):
        """Trace full dependency chain: document → requirement → test case → execution."""
        req_id = str(uuid.uuid4())
        
        # Get outbound to document
        doc_result, _ = await call_mcp(
            "relationship_tool",
            {
                "operation": "get_outbound",
                "entity_id": req_id,
                "relationship_type": "defined_in"
            }
        )
        
        assert doc_result["success"] is True
        
        # Get inbound from test cases
        test_result, _ = await call_mcp(
            "relationship_tool",
            {
                "operation": "get_inbound",
                "entity_id": req_id,
                "relationship_type": "validates"
            }
        )
        
        assert test_result["success"] is True
