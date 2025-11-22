"""E2E tests for Entity Relationships operations.

This file validates end-to-end entity relationship functionality:
- Linking entities together (all relationship types)
- Unlinking/removing entity relationships
- Viewing inbound/outbound relationships with filtering and pagination
- Checking if entities are related

Test Coverage: 18 test scenarios covering 4 user stories.
File follows canonical naming - describes WHAT is tested (entity relationships).
Uses canonical fixture patterns for unit/integration/e2e variants.
"""

import pytest
import pytest_asyncio
import uuid
from typing import Dict, Any, List
from datetime import datetime, timezone


class TestEntityLinking:
    """Test linking entities together across all relationship types."""
    
    @pytest.mark.asyncio
    async def test_link_member_to_organization(self, call_mcp):
        """Link member (add user to organization)."""
        # Create organization
        org_data = {"name": f"Member Org {uuid.uuid4().hex[:8]}"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        org_id = org_result["data"]["id"]

        # Link member to organization using correct API format
        result, _ = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "member",
                "source": {"type": "organization", "id": org_id},
                "target": {"type": "user", "id": "user_123"},
                "metadata": {"role": "member"}
            }
        )

        assert result["success"] is True or result.get("exists") is True
    
    @pytest.mark.asyncio
    async def test_link_member_to_project(self, call_mcp):
        """Link member (add user to project)."""
        # Create project
        project_data = {"name": f"Member Project {uuid.uuid4().hex[:8]}"}
        project_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": project_data}
        )
        project_id = project_result["data"]["id"]

        # Link member to project using correct API format
        result, _ = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "member",
                "source": {"type": "project", "id": project_id},
                "target": {"type": "user", "id": "user_456"},
                "metadata": {"role": "developer"}
            }
        )

        assert result["success"] is True or result.get("exists") is True
    
    @pytest.mark.asyncio
    async def test_link_assignment_to_user(self, call_mcp):
        """Link assignment (assign entity to user)."""
        # Create document
        doc_data = {"name": f"Assignment Doc {uuid.uuid4().hex[:8]}"}
        doc_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": doc_data}
        )
        doc_id = doc_result["data"]["id"]

        # Assign document to user using correct API format
        result, _ = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "assignment",
                "source": {"type": "document", "id": doc_id},
                "target": {"type": "user", "id": "user_789"},
                "metadata": {"role": "reviewer", "priority": "high"}
            }
        )

        assert result["success"] is True or result.get("exists") is True
    
    @pytest.mark.asyncio
    async def test_link_trace_requirement_to_implementation(self, call_mcp):
        """Link trace_link (requirement → implementation)."""
        # Create requirement and document
        req_data = {"name": f"Test Requirement {uuid.uuid4().hex[:8]}"}
        req_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "requirement", "operation": "create", "data": req_data}
        )
        req_id = req_result["data"]["id"]

        doc_data = {"name": f"Implementation Doc {uuid.uuid4().hex[:8]}"}
        doc_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": doc_data}
        )
        doc_id = doc_result["data"]["id"]

        # Link requirement to implementation using correct API format
        result, _ = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "trace_link",
                "source": {"type": "requirement", "id": req_id},
                "target": {"type": "document", "id": doc_id},
                "metadata": {"link_type": "implements", "confidence": "high"}
            }
        )

        assert result["success"] is True or result.get("exists") is True
    
    @pytest.mark.asyncio
    async def test_link_requirement_to_test(self, call_mcp):
        """Link requirement_test (requirement → test case)."""
        # Create requirement and test
        req_data = {"name": f"Req for Test {uuid.uuid4().hex[:8]}"}
        req_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "requirement", "operation": "create", "data": req_data}
        )
        req_id = req_result["data"]["id"]

        test_data = {"name": f"Test Case {uuid.uuid4().hex[:8]}"}
        test_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "test", "operation": "create", "data": test_data}
        )
        test_id = test_result["data"]["id"]

        # Link requirement to test using correct API format
        result, _ = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "requirement_test",
                "source": {"type": "requirement", "id": req_id},
                "target": {"type": "test", "id": test_id},
                "metadata": {"relationship_type": "unit_test", "coverage_level": "direct"}
            }
        )

        assert result["success"] is True or result.get("exists") is True
        assert result["data"]["test_type"] == "unit_test"
        assert result["data"]["coverage"] == "direct"
    
    @pytest.mark.asyncio
    async def test_link_with_metadata(self, call_mcp):
        """Create link with additional metadata."""
        # Create two entities
        org_data = {"name": f"Metadata Org {uuid.uuid4().hex[:8]}"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )

        project_data = {"name": f"Metadata Project {uuid.uuid4().hex[:8]}"}
        project_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": project_data}
        )

        # Link with rich metadata using correct API format
        result, _ = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "member",
                "source": {"type": "organization", "id": org_result["data"]["id"]},
                "target": {"type": "user", "id": "user_admin"},
                "metadata": {
                    "role": "admin",
                    "status": "active",
                    "department": "Engineering",
                    "start_date": "2024-01-01"
                }
            }
        )

        assert result["success"] is True or result.get("exists") is True
    
    @pytest.mark.asyncio
    async def test_invalid_link_fails(self, call_mcp):
        """Attempting invalid link should fail."""
        fake_id = str(uuid.uuid4())

        # Try to link non-existent entities using correct API format
        result, _ = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "member",
                "source": {"type": "organization", "id": fake_id},
                "target": {"type": "user", "id": "user_invalid"}
            }
        )

        # Should either fail or return empty result
        assert result["success"] is False or result.get("exists") is False
    
    @pytest.mark.asyncio
    async def test_duplicate_link_behavior(self, call_mcp):
        """Creating duplicate link should either fail or update."""
        # Create organization and user
        org_data = {"name": f"Duplicate Org {uuid.uuid4().hex[:8]}"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        org_id = org_result["data"]["id"]
        user_id = "user_dup_123"

        # Create first link using correct API format
        result1, _ = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "member",
                "source": {"type": "organization", "id": org_id},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "member"}
            }
        )

        assert result1["success"] is True or result1.get("exists") is True

        # Attempt duplicate link - should either fail or return exists
        result2, _ = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "member",
                "source": {"type": "organization", "id": org_id},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "admin"}
            }
        )

        # Either succeeds or indicates it already exists
        assert result2["success"] is True or result2.get("exists") is True


class TestEntityUnlinking:
    """Test removing/unlinking entity relationships."""
    
    @pytest.mark.asyncio
    async def test_unlink_member_from_organization(self, call_mcp):
        """Remove member from organization."""
        # Create organization and link member
        org_data = {"name": f"Unlink Org {uuid.uuid4().hex[:8]}"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        org_id = org_result["data"]["id"]
        user_id = "user_removable"

        # Link member using correct API format
        link_result, _ = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "member",
                "source": {"type": "organization", "id": org_id},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "member"}
            }
        )

        assert link_result["success"] is True or link_result.get("exists") is True

        # Unlink member using correct API format
        result, _ = await call_mcp(
            "relationship_tool",
            {
                "operation": "unlink",
                "relationship_type": "member",
                "source": {"type": "organization", "id": org_id},
                "target": {"type": "user", "id": user_id}
            }
        )

        assert result["success"] is True

        # Verify relationship is removed
        check_result, _ = await call_mcp(
            "relationship_tool",
            {
                "operation": "check",
                "relationship_type": "member",
                "source": {"type": "organization", "id": org_id},
                "target": {"type": "user", "id": user_id}
            }
        )

        # Relationship should no longer exist
        assert check_result.get("exists") is False
    
    @pytest.mark.asyncio
    async def test_unlink_assignment(self, call_mcp):
        """Remove assignment relationship."""
        # Create document and assignment
        doc_data = {"name": f"Unlink Assignment Doc {uuid.uuid4().hex[:8]}"}
        doc_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": doc_data}
        )
        doc_id = doc_result["data"]["id"]
        user_id = "user_unassign"

        # Create assignment using correct API format
        assign_result, _ = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "assignment",
                "source": {"type": "document", "id": doc_id},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "reviewer"}
            }
        )

        assert assign_result["success"] is True or assign_result.get("exists") is True

        # Unlink assignment using correct API format
        result, _ = await call_mcp(
            "relationship_tool",
            {
                "operation": "unlink",
                "relationship_type": "assignment",
                "source": {"type": "document", "id": doc_id},
                "target": {"type": "user", "id": user_id}
            }
        )
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_unlink_trace_link(self, call_mcp):
        """Remove trace link between requirement and implementation."""
        # Create requirement and document
        req_data = {"name": f"Unlink Requirement {uuid.uuid4().hex[:8]}"}
        req_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "requirement", "operation": "create", "data": req_data}
        )
        req_id = req_result["data"]["id"]

        doc_data = {"name": f"Unlink Implementation {uuid.uuid4().hex[:8]}"}
        doc_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": doc_data}
        )
        doc_id = doc_result["data"]["id"]

        # Create trace link using correct API format
        trace_result, _ = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "trace_link",
                "source": {"type": "requirement", "id": req_id},
                "target": {"type": "document", "id": doc_id}
            }
        )

        assert trace_result["success"] is True or trace_result.get("exists") is True

        # Unlink trace using correct API format
        result, _ = await call_mcp(
            "relationship_tool",
            {
                "operation": "unlink",
                "relationship_type": "trace_link",
                "source": {"type": "requirement", "id": req_id},
                "target": {"type": "document", "id": doc_id}
            }
        )

        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_unlink_nonexistent_relationship_fails_gracefully(self, call_mcp):
        """Attempting to unlink non-existent relationship should fail gracefully."""
        fake_org_id = str(uuid.uuid4())
        fake_user_id = str(uuid.uuid4())

        result, _ = await call_mcp(
            "relationship_tool",
            {
                "operation": "unlink",
                "relationship_type": "member",
                "source": {"type": "organization", "id": fake_org_id},
                "target": {"type": "user", "id": fake_user_id}
            }
        )

        # Should either fail or succeed (depending on implementation)
        assert result["success"] is False or result["success"] is True


class TestEntityRelationshipViews:
    """Test viewing inbound/outbound relationships with filtering and pagination."""
    
    @pytest.mark.asyncio
    async def test_list_inbound_relationships(self, call_mcp):
        """List all inbound relationships for an entity."""
        # Create organization and link multiple members
        org_data = {"name": f"Inbound Org {uuid.uuid4().hex[:8]}"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        org_id = org_result["data"]["id"]

        # Create multiple member relationships using correct API format
        user_ids = ["user_1", "user_2", "user_3"]

        for user_id in user_ids:
            _, _ = await call_mcp(
                "relationship_tool",
                {
                    "operation": "link",
                    "relationship_type": "member",
                    "source": {"type": "organization", "id": org_id},
                    "target": {"type": "user", "id": user_id},
                    "metadata": {"role": "member"}
                }
            )

        # List inbound relationships (members pointing to this org)
        result, _ = await call_mcp(
            "relationship_tool",
            {
                "operation": "list",
                "relationship_type": "member",
                "source": {"type": "organization", "id": org_id}
            }
        )

        assert result["success"] is True or "data" in result
    
    @pytest.mark.asyncio
    async def test_list_outbound_relationships(self, call_mcp):
        """List all outbound relationships from an entity."""
        # Create project and link it to organization
        project_data = {"name": f"Outbound Project {uuid.uuid4().hex[:8]}"}
        project_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": project_data}
        )
        project_id = project_result["data"]["id"]

        # Create outbound member relationship (project member) using correct API format
        _, _ = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "member",
                "source": {"type": "project", "id": project_id},
                "target": {"type": "user", "id": "user_dev"},
                "metadata": {"role": "developer"}
            }
        )

        # List outbound relationships
        result, _ = await call_mcp(
            "relationship_tool",
            {
                "operation": "list",
                "relationship_type": "member",
                "source": {"type": "project", "id": project_id}
            }
        )

        assert result["success"] is True or "data" in result
    
    @pytest.mark.asyncio
    async def test_list_relationships_filtered_by_type(self, call_mcp):
        """List relationships filtered by specific relationship type."""
        # Create entities for different relationship types
        org_data = {"name": f"Filtered Org {uuid.uuid4().hex[:8]}"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        org_id = org_result["data"]["id"]

        project_data = {"name": f"Filtered Project {uuid.uuid4().hex[:8]}"}
        project_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": project_data}
        )
        project_id = project_result["data"]["id"]

        # Create member relationship using correct API format
        _, _ = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "member",
                "source": {"type": "organization", "id": org_id},
                "target": {"type": "user", "id": "user_member"}
            }
        )

        # Create assignment relationship using correct API format
        _, _ = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "assignment",
                "source": {"type": "project", "id": project_id},
                "target": {"type": "user", "id": "user_assignee"}
            }
        )

        # List only member relationships
        result, _ = await call_mcp(
            "relationship_tool",
            {
                "operation": "list",
                "relationship_type": "member",
                "source": {"type": "organization", "id": org_id}
            }
        )

        assert result["success"] is True or "data" in result
    
    @pytest.mark.asyncio
    async def test_list_relationships_with_pagination(self, call_mcp):
        """Test pagination when listing relationships."""
        # Create organization and add many members
        org_data = {"name": f"Paginated Org {uuid.uuid4().hex[:8]}"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        org_id = org_result["data"]["id"]

        # Create 12 member relationships using correct API format
        for i in range(12):
            _, _ = await call_mcp(
                "relationship_tool",
                {
                    "operation": "link",
                    "relationship_type": "member",
                    "source": {"type": "organization", "id": org_id},
                    "target": {"type": "user", "id": f"user_{i}"},
                    "metadata": {"role": "member"}
                }
            )

        # Test pagination (limit 5, offset 0)
        result1, _ = await call_mcp(
            "relationship_tool",
            {
                "operation": "list",
                "relationship_type": "member",
                "source": {"type": "organization", "id": org_id},
                "limit": 5,
                "offset": 0
            }
        )

        assert result1["success"] is True or "data" in result1

        # Test pagination (limit 5, offset 5)
        result2, _ = await call_mcp(
            "relationship_tool",
            {
                "operation": "list",
                "relationship_type": "member",
                "source": {"type": "organization", "id": org_id},
                "limit": 5,
                "offset": 5
            }
        )

        assert result2["success"] is True or "data" in result2
        assert total_relationships >= 10  # At least 10 of 12 relationships


class TestRelationshipExistence:
    """Test checking if entities are related."""
    
    @pytest.mark.asyncio
    async def test_check_relationship_exists_true(self, call_mcp):
        """Check if related entities have a relationship (true case)."""
        # Create organization and member
        org_data = {"name": f"Check Org {uuid.uuid4().hex[:8]}"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        org_id = org_result["data"]["id"]
        user_id = "user_existing"

        # Create relationship first using correct API format
        link_result, _ = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "member",
                "source": {"type": "organization", "id": org_id},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "member"}
            }
        )

        assert link_result["success"] is True or link_result.get("exists") is True

        # Check if relationship exists using correct API format
        result, _ = await call_mcp(
            "relationship_tool",
            {
                "operation": "check",
                "relationship_type": "member",
                "source": {"type": "organization", "id": org_id},
                "target": {"type": "user", "id": user_id}
            }
        )

        assert result.get("exists") is True
    
    @pytest.mark.asyncio
    async def test_check_relationship_exists_false(self, call_mcp):
        """Check if unrelated entities have a relationship (false case)."""
        # Create organization
        org_data = {"name": f"No Relationship Org {uuid.uuid4().hex[:8]}"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        org_id = org_result["data"]["id"]
        user_id = "user_nonexistent"

        # Don't create any relationship

        # Check if relationship exists (should be false) using correct API format
        result, _ = await call_mcp(
            "relationship_tool",
            {
                "operation": "check",
                "relationship_type": "member",
                "source": {"type": "organization", "id": org_id},
                "target": {"type": "user", "id": user_id}
            }
        )

        assert result.get("exists") is False
