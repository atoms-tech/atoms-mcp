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
        
        # Link member to organization
        result, duration_ms = await call_mcp(
            "relationship_tool",
            {
                "relationship_type": "member",
                "operation": "create",
                "data": {
                    "organization_id": org_id,
                    "member_email": "user@example.com",
                    "role": "member"
                }
            }
        )
        
        assert result["success"] is True
        assert "relationship_id" in result["data"]
        assert result["data"]["organization_id"] == org_id
        assert result["data"]["member_email"] == "user@example.com"
        assert result["data"]["role"] == "member"
    
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
        
        # Link member to project
        result, duration_ms = await call_mcp(
            "relationship_tool",
            {
                "relationship_type": "member",
                "operation": "create",
                "data": {
                    "project_id": project_id,
                    "member_email": "developer@example.com",
                    "role": "developer"
                }
            }
        )
        
        assert result["success"] is True
        assert result["data"]["project_id"] == project_id
        assert result["data"]["member_email"] == "developer@example.com"
        assert result["data"]["role"] == "developer"
    
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
        
        # Assign document to user
        result, duration_ms = await call_mcp(
            "relationship_tool",
            {
                "relationship_type": "assignment",
                "operation": "create",
                "data": {
                    "document_id": doc_id,
                    "assignee_email": "assignee@example.com",
                    "assignment_type": "reviewer",
                    "priority": "high"
                }
            }
        )
        
        assert result["success"] is True
        assert result["data"]["document_id"] == doc_id
        assert result["data"]["assignee_email"] == "assignee@example.com"
        assert result["data"]["assignment_type"] == "reviewer"
        assert result["data"]["priority"] == "high"
    
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
        
        # Link requirement to implementation
        result, duration_ms = await call_mcp(
            "relationship_tool",
            {
                "relationship_type": "trace_link",
                "operation": "create",
                "data": {
                    "requirement_id": req_id,
                    "implementation_id": doc_id,
                    "trace_type": "implements",
                    "confidence": "high"
                }
            }
        )
        
        assert result["success"] is True
        assert result["data"]["requirement_id"] == req_id
        assert result["data"]["implementation_id"] == doc_id
        assert result["data"]["trace_type"] == "implements"
        assert result["data"]["confidence"] == "high"
    
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
        
        # Link requirement to test
        result, duration_ms = await call_mcp(
            "relationship_tool",
            {
                "relationship_type": "requirement_test",
                "operation": "create",
                "data": {
                    "requirement_id": req_id,
                    "test_id": test_id,
                    "test_type": "unit_test",
                    "coverage": "direct"
                }
            }
        )
        
        assert result["success"] is True
        assert result["data"]["requirement_id"] == req_id
        assert result["data"]["test_id"] == test_id
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
        
        # Link with rich metadata
        result, duration_ms = await call_mcp(
            "relationship_tool",
            {
                "relationship_type": "member",
                "operation": "create",
                "data": {
                    "organization_id": org_result["data"]["id"],
                    "project_id": project_result["data"]["id"],
                    "member_email": "admin@example.com",
                    "role": "admin",
                    "permissions": ["read", "write", "delete"],
                    "department": "Engineering",
                    "start_date": "2024-01-01",
                    "notes": "System administrator"
                }
            }
        )
        
        assert result["success"] is True
        data = result["data"]
        assert data["permissions"] == ["read", "write", "delete"]
        assert data["department"] == "Engineering"
        assert data["start_date"] == "2024-01-01"
        assert data["notes"] == "System administrator"
    
    @pytest.mark.asyncio
    async def test_invalid_link_fails(self, call_mcp):
        """Attempting invalid link should fail."""
        fake_id = str(uuid.uuid4())
        
        # Try to link non-existent entities
        result, duration_ms = await call_mcp(
            "relationship_tool",
            {
                "relationship_type": "member",
                "operation": "create",
                "data": {
                    "organization_id": fake_id,
                    "member_email": "invalid@example.com"
                }
            }
        )
        
        assert result["success"] is False
        assert "not found" in result["error"].lower() or "invalid" in result["error"].lower()
    
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
        
        email = f"duplicate{uuid.uuid4().hex[:8]}@example.com"
        
        # Create first link
        result1, duration_ms = await call_mcp(
            "relationship_tool",
            {
                "relationship_type": "member",
                "operation": "create",
                "data": {
                    "organization_id": org_id,
                    "member_email": email,
                    "role": "member"
                }
            }
        )
        
        assert result1["success"] is True
        
        # Attempt duplicate link - should either fail or update
        result2, _ = await call_mcp(
            "relationship_tool",
            {
                "relationship_type": "member",
                "operation": "create",
                "data": {
                    "organization_id": org_id,
                    "member_email": email,
                    "role": "admin"
                }
            }
        )
        
        # Either the operation fails (expected) or updates the role (acceptable)
        if result2["success"]:
            # If it succeeds, verify it updated the existing relationship
            assert result2["data"]["role"] == "admin"
        else:
            # If it fails, that's also acceptable
            assert "duplicate" in result2["error"].lower() or "exists" in result2["error"].lower()


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
        
        # Link member
        link_result, _ = await call_mcp(
            "relationship_tool",
            {
                "relationship_type": "member",
                "operation": "create",
                "data": {
                    "organization_id": org_id,
                    "member_email": "removable@example.com",
                    "role": "member"
                }
            }
        )
        relationship_id = link_result["data"]["relationship_id"]
        
        # Unlink member
        result, duration_ms = await call_mcp(
            "relationship_tool",
            {
                "relationship_type": "member",
                "operation": "delete",
                "entity_id": relationship_id
            }
        )
        
        assert result["success"] is True
        
        # Verify relationship is removed
        check_result, _ = await call_mcp(
            "relationship_tool",
            {
                "relationship_type": "member",
                "operation": "check",
                "filters": {
                    "organization_id": org_id,
                    "member_email": "removable@example.com"
                }
            }
        )
        
        # Relationship should no longer exist
        assert check_result["success"] is True
        assert check_result["data"]["exists"] is False
    
    @pytest.mark.asyncio
    async def test_unlink_assignment(self, call_mcp):
        """Remove assignment relationship."""
        # Create document and assignment
        doc_data = {"name": f"Unlink Assignment Doc {uuid.uuid4().hex[:8]}"}
        doc_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": doc_data}
        )
        
        # Create assignment
        assign_result, _ = await call_mcp(
            "relationship_tool",
            {
                "relationship_type": "assignment",
                "operation": "create",
                "data": {
                    "document_id": doc_result["data"]["id"],
                    "assignee_email": "unassign@example.com"
                }
            }
        )
        assignment_id = assign_result["data"]["relationship_id"]
        
        # Unlink assignment
        result, duration_ms = await call_mcp(
            "relationship_tool",
            {
                "relationship_type": "assignment",
                "operation": "delete",
                "entity_id": assignment_id
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
        
        doc_data = {"name": f"Unlink Implementation {uuid.uuid4().hex[:8]}"}
        doc_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": doc_data}
        )
        
        # Create trace link
        trace_result, _ = await call_mcp(
            "relationship_tool",
            {
                "relationship_type": "trace_link",
                "operation": "create",
                "data": {
                    "requirement_id": req_result["data"]["id"],
                    "implementation_id": doc_result["data"]["id"]
                }
            }
        )
        trace_id = trace_result["data"]["relationship_id"]
        
        # Unlink trace
        result, duration_ms = await call_mcp(
            "relationship_tool",
            {
                "relationship_type": "trace_link",
                "operation": "delete",
                "entity_id": trace_id
            }
        )
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_unlink_nonexistent_relationship_fails_gracefully(self, call_mcp):
        """Attempting to unlink non-existent relationship should fail gracefully."""
        fake_id = str(uuid.uuid4())
        
        result, duration_ms = await call_mcp(
            "relationship_tool",
            {
                "relationship_type": "member",
                "operation": "delete",
                "entity_id": fake_id
            }
        )
        
        assert result["success"] is False
        assert "not found" in result["error"].lower() or "does not exist" in result["error"].lower()


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
        
        # Create multiple member relationships
        members = ["user1@example.com", "user2@example.com", "user3@example.com"]
        relationship_ids = []
        
        for email in members:
            result, _ = await call_mcp(
                "relationship_tool",
                {
                    "relationship_type": "member",
                    "operation": "create",
                    "data": {
                        "organization_id": org_id,
                        "member_email": email,
                        "role": "member"
                    }
                }
            )
            relationship_ids.append(result["data"]["relationship_id"])
        
        # List inbound relationships (members pointing to this org)
        result, duration_ms = await call_mcp(
            "relationship_tool",
            {
                "relationship_type": "member",
                "operation": "list",
                "direction": "inbound",
                "filters": {"organization_id": org_id}
            }
        )
        
        assert result["success"] is True
        assert len(result["data"]) >= len(members)
        
        # Verify all our members are in the list
        member_emails = {rel["member_email"] for rel in result["data"]}
        for email in members:
            assert email in member_emails
    
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
        
        # Create outbound member relationship (project member)
        member_result, _ = await call_mcp(
            "relationship_tool",
            {
                "relationship_type": "member",
                "operation": "create",
                "data": {
                    "project_id": project_id,
                    "member_email": "developer@example.com",
                    "role": "developer"
                }
            }
        )
        
        # List outbound relationships
        result, duration_ms = await call_mcp(
            "relationship_tool",
            {
                "relationship_type": "member",
                "operation": "list",
                "direction": "outbound",
                "filters": {"project_id": project_id}
            }
        )
        
        assert result["success"] is True
        # Should find at least one outbound relationship
        outbound_rels = result["data"]
        assert len(outbound_rels) >= 1
        
        # Verify it's outbound (from project perspective)
        for rel in outbound_rels:
            assert rel["project_id"] == project_id
    
    @pytest.mark.asyncio
    async def test_list_relationships_filtered_by_type(self, call_mcp):
        """List relationships filtered by specific relationship type."""
        # Create entities for different relationship types
        org_data = {"name": f"Filtered Org {uuid.uuid4().hex[:8]}"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        
        project_data = {"name": f"Filtered Project {uuid.uuid4().hex[:8]}"}
        project_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": project_data}
        )
        
        # Create member relationship
        await call_mcp(
            "relationship_tool",
            {
                "relationship_type": "member",
                "operation": "create",
                "data": {
                    "organization_id": org_result["data"]["id"],
                    "member_email": "member@example.com"
                }
            }
        )
        
        # Create assignment relationship
        await call_mcp(
            "relationship_tool",
            {
                "relationship_type": "assignment",
                "operation": "create",
                "data": {
                    "project_id": project_result["data"]["id"],
                    "assignee_email": "assignee@example.com"
                }
            }
        )
        
        # List only member relationships
        result, duration_ms = await call_mcp(
            "relationship_tool",
            {
                "relationship_type": "member",
                "operation": "list",
                "filters": {"organization_id": org_result["data"]["id"]}
            }
        )
        
        assert result["success"] is True
        # Should only return member relationships
        for rel in result["data"]:
            assert "member_email" in rel
            assert "organization_id" in rel or "project_id" in rel
    
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
        
        # Create 12 member relationships
        for i in range(12):
            await call_mcp(
                "relationship_tool",
                {
                    "relationship_type": "member",
                    "operation": "create",
                    "data": {
                        "organization_id": org_id,
                        "member_email": f"user{i}@example.com",
                        "role": "member"
                    }
                }
            )
        
        # Test pagination (limit 5, offset 0)
        result1, duration_ms = await call_mcp(
            "relationship_tool",
            {
                "relationship_type": "member",
                "operation": "list",
                "filters": {"organization_id": org_id},
                "limit": 5,
                "offset": 0
            }
        )
        
        assert result1["success"] is True
        assert len(result1["data"]) <= 5
        
        # Test pagination (limit 5, offset 5)
        result2, _ = await call_mcp(
            "relationship_tool",
            {
                "relationship_type": "member",
                "operation": "list",
                "filters": {"organization_id": org_id},
                "limit": 5,
                "offset": 5
            }
        )
        
        assert result2["success"] is True
        assert len(result2["data"]) <= 5
        
        # Test pagination (limit 5, offset 10)
        result3, _ = await call_mcp(
            "relationship_tool",
            {
                "relationship_type": "member",
                "operation": "list",
                "filters": {"organization_id": org_id},
                "limit": 5,
                "offset": 10
            }
        )
        
        assert result3["success"] is True
        assert len(result3["data"]) <= 5
        
        # Combined results should have most of our relationships
        total_relationships = len(result1["data"]) + len(result2["data"]) + len(result3["data"])
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
        
        email = f"existing{uuid.uuid4().hex[:8]}@example.com"
        
        # Create relationship first
        link_result, _ = await call_mcp(
            "relationship_tool",
            {
                "relationship_type": "member",
                "operation": "create",
                "data": {
                    "organization_id": org_id,
                    "member_email": email,
                    "role": "member"
                }
            }
        )
        
        # Check if relationship exists
        result, duration_ms = await call_mcp(
            "relationship_tool",
            {
                "relationship_type": "member",
                "operation": "check",
                "filters": {
                    "organization_id": org_id,
                    "member_email": email
                }
            }
        )
        
        assert result["success"] is True
        assert result["data"]["exists"] is True
        assert result["data"]["relationship_id"] == link_result["data"]["relationship_id"]
        assert result["data"]["role"] == "member"
    
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
        
        email = f"nonexistent{uuid.uuid4().hex[:8]}@example.com"
        
        # Don't create any relationship
        
        # Check if relationship exists (should be false)
        result, duration_ms = await call_mcp(
            "relationship_tool",
            {
                "relationship_type": "member",
                "operation": "check",
                "filters": {
                    "organization_id": org_id,
                    "member_email": email
                }
            }
        )
        
        assert result["success"] is True
        assert result["data"]["exists"] is False
        assert "relationship_id" not in result["data"] or result["data"]["relationship_id"] is None
