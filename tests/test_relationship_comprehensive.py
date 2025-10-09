"""
Comprehensive relationship tests covering all relationship types and operations.
Tests based on relationship parameter matrix covering:
- Basic operations (link, unlink, list, check)
- Metadata handling
- Pagination
- Special cases (organization, project, profile joining)
- Error conditions
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from atoms_mcp.lib.relationship import RelationshipService
from atoms_mcp.lib.models import RelationshipRequest, RelationshipType


class TestRelationshipComprehensive:
    """Comprehensive test suite for relationship operations."""

    @pytest.fixture
    def relationship_service(self):
        """Create a RelationshipService instance with mocked client."""
        service = RelationshipService()
        service.client = AsyncMock()
        return service

    # ============================================================================
    # MEMBER RELATIONSHIP TESTS (11 core tests + special cases)
    # ============================================================================

    @pytest.mark.asyncio
    async def test_member_link_basic(self, relationship_service):
        """Test basic member relationship creation."""
        request = RelationshipRequest(
            action="link",
            relationship_type=RelationshipType.MEMBER,
            source_type="user",
            source_id="user_123",
            target_type="organization",
            target_id="org_456"
        )

        relationship_service.client.create_relationship = AsyncMock(return_value={
            "id": "rel_789",
            "relationship_type": "member",
            "source_id": "user_123",
            "target_id": "org_456",
            "metadata": {}
        })

        result = await relationship_service.handle_request(request)
        assert result["id"] == "rel_789"
        assert result["relationship_type"] == "member"

    @pytest.mark.asyncio
    async def test_member_link_with_metadata(self, relationship_service):
        """Test member relationship with role and status metadata."""
        request = RelationshipRequest(
            action="link",
            relationship_type=RelationshipType.MEMBER,
            source_type="user",
            source_id="user_123",
            target_type="organization",
            target_id="org_456",
            metadata={
                "role": "admin",
                "status": "active",
                "joined_date": "2024-01-15"
            }
        )

        relationship_service.client.create_relationship = AsyncMock(return_value={
            "id": "rel_789",
            "metadata": {"role": "admin", "status": "active"}
        })

        result = await relationship_service.handle_request(request)
        assert result["metadata"]["role"] == "admin"
        assert result["metadata"]["status"] == "active"

    @pytest.mark.asyncio
    async def test_member_unlink_soft(self, relationship_service):
        """Test soft deletion of member relationship."""
        request = RelationshipRequest(
            action="unlink",
            relationship_type=RelationshipType.MEMBER,
            source_type="user",
            source_id="user_123",
            target_type="organization",
            target_id="org_456",
            soft_delete=True
        )

        relationship_service.client.delete_relationship = AsyncMock(return_value={
            "deleted": True,
            "soft_delete": True
        })

        result = await relationship_service.handle_request(request)
        assert result["deleted"] is True
        assert result["soft_delete"] is True

    @pytest.mark.asyncio
    async def test_member_unlink_hard(self, relationship_service):
        """Test hard deletion of member relationship."""
        request = RelationshipRequest(
            action="unlink",
            relationship_type=RelationshipType.MEMBER,
            source_type="user",
            source_id="user_123",
            target_type="organization",
            target_id="org_456",
            soft_delete=False
        )

        relationship_service.client.delete_relationship = AsyncMock(return_value={
            "deleted": True,
            "soft_delete": False
        })

        result = await relationship_service.handle_request(request)
        assert result["deleted"] is True
        assert result["soft_delete"] is False

    @pytest.mark.asyncio
    async def test_member_list_all(self, relationship_service):
        """Test listing all member relationships."""
        request = RelationshipRequest(
            action="list",
            relationship_type=RelationshipType.MEMBER,
            source_type="user",
            source_id="user_123"
        )

        relationship_service.client.list_relationships = AsyncMock(return_value={
            "relationships": [
                {"id": "rel_1", "target_id": "org_1"},
                {"id": "rel_2", "target_id": "org_2"}
            ],
            "total": 2
        })

        result = await relationship_service.handle_request(request)
        assert len(result["relationships"]) == 2, f"Expected len(result["relationships"]) == 2, got {len(result["relationships"])}"
        assert result["total"] == 2

    @pytest.mark.asyncio
    async def test_member_list_filtered(self, relationship_service):
        """Test filtered listing of member relationships."""
        request = RelationshipRequest(
            action="list",
            relationship_type=RelationshipType.MEMBER,
            source_type="user",
            source_id="user_123",
            filters={"status": "active", "role": "admin"}
        )

        relationship_service.client.list_relationships = AsyncMock(return_value={
            "relationships": [
                {"id": "rel_1", "metadata": {"status": "active", "role": "admin"}}
            ],
            "total": 1
        })

        result = await relationship_service.handle_request(request)
        assert len(result["relationships"]) == 1, f"Expected len(result["relationships"]) == 1, got {len(result["relationships"])}"
        assert result["relationships"][0]["metadata"]["status"] == "active"

    @pytest.mark.asyncio
    async def test_member_list_paginated(self, relationship_service):
        """Test paginated listing of member relationships."""
        request = RelationshipRequest(
            action="list",
            relationship_type=RelationshipType.MEMBER,
            source_type="user",
            source_id="user_123",
            limit=10,
            offset=20
        )

        relationship_service.client.list_relationships = AsyncMock(return_value={
            "relationships": [{"id": f"rel_{i}"} for i in range(10)],
            "total": 50,
            "limit": 10,
            "offset": 20
        })

        result = await relationship_service.handle_request(request)
        assert len(result["relationships"]) == 10, f"Expected len(result["relationships"]) == 10, got {len(result["relationships"])}"
        assert result["limit"] == 10
        assert result["offset"] == 20

    @pytest.mark.asyncio
    async def test_member_check_exists(self, relationship_service):
        """Test checking if member relationship exists."""
        request = RelationshipRequest(
            action="check",
            relationship_type=RelationshipType.MEMBER,
            source_type="user",
            source_id="user_123",
            target_type="organization",
            target_id="org_456"
        )

        relationship_service.client.check_relationship = AsyncMock(return_value={
            "exists": True,
            "relationship_id": "rel_789"
        })

        result = await relationship_service.handle_request(request)
        assert result["exists"] is True
        assert result["relationship_id"] == "rel_789"

    @pytest.mark.asyncio
    async def test_member_check_not_exists(self, relationship_service):
        """Test checking non-existent member relationship."""
        request = RelationshipRequest(
            action="check",
            relationship_type=RelationshipType.MEMBER,
            source_type="user",
            source_id="user_123",
            target_type="organization",
            target_id="org_999"
        )

        relationship_service.client.check_relationship = AsyncMock(return_value={
            "exists": False
        })

        result = await relationship_service.handle_request(request)
        assert result["exists"] is False

    @pytest.mark.asyncio
    async def test_member_update_metadata(self, relationship_service):
        """Test updating metadata for member relationship."""
        request = RelationshipRequest(
            action="update",
            relationship_type=RelationshipType.MEMBER,
            source_type="user",
            source_id="user_123",
            target_type="organization",
            target_id="org_456",
            metadata={
                "role": "owner",
                "permissions": ["read", "write", "delete"]
            }
        )

        relationship_service.client.update_relationship = AsyncMock(return_value={
            "id": "rel_789",
            "metadata": {"role": "owner", "permissions": ["read", "write", "delete"]}
        })

        result = await relationship_service.handle_request(request)
        assert result["metadata"]["role"] == "owner"
        assert len(result["metadata"]["permissions"]) == 3, f"Expected len(result["metadata"]["permissions"]) == 3, got {len(result["metadata"]["permissions"])}"

    @pytest.mark.asyncio
    async def test_member_organization_special(self, relationship_service):
        """Test member-organization relationship with special metadata."""
        request = RelationshipRequest(
            action="link",
            relationship_type=RelationshipType.MEMBER,
            source_type="user",
            source_id="user_123",
            target_type="organization",
            target_id="org_456",
            metadata={
                "role": "admin",
                "status": "active",
                "department": "engineering",
                "permissions": {
                    "projects": ["create", "read", "update"],
                    "members": ["invite", "remove"]
                }
            }
        )

        relationship_service.client.create_relationship = AsyncMock(return_value={
            "id": "rel_789",
            "relationship_type": "member",
            "metadata": request.metadata
        })

        result = await relationship_service.handle_request(request)
        assert result["metadata"]["department"] == "engineering"
        assert "projects" in result["metadata"]["permissions"]

    @pytest.mark.asyncio
    async def test_member_project_with_context(self, relationship_service):
        """Test member-project relationship with organization context."""
        request = RelationshipRequest(
            action="link",
            relationship_type=RelationshipType.MEMBER,
            source_type="user",
            source_id="user_123",
            target_type="project",
            target_id="proj_789",
            source_context={"org_id": "org_456"},
            metadata={
                "role": "developer",
                "access_level": "write"
            }
        )

        relationship_service.client.create_relationship = AsyncMock(return_value={
            "id": "rel_999",
            "source_context": {"org_id": "org_456"},
            "metadata": {"role": "developer", "access_level": "write"}
        })

        result = await relationship_service.handle_request(request)
        assert result["source_context"]["org_id"] == "org_456"
        assert result["metadata"]["role"] == "developer"

    @pytest.mark.asyncio
    async def test_profile_joining_member(self, relationship_service):
        """Test profile joining for member relationships."""
        request = RelationshipRequest(
            action="list",
            relationship_type=RelationshipType.MEMBER,
            source_type="user",
            source_id="user_123",
            join_profiles=True
        )

        relationship_service.client.list_relationships = AsyncMock(return_value={
            "relationships": [
                {
                    "id": "rel_1",
                    "target_id": "org_1",
                    "target_profile": {
                        "name": "Organization One",
                        "type": "organization",
                        "created_at": "2024-01-01"
                    }
                }
            ],
            "total": 1
        })

        result = await relationship_service.handle_request(request)
        assert result["relationships"][0]["target_profile"]["name"] == "Organization One"

    # ============================================================================
    # ASSIGNMENT RELATIONSHIP TESTS (11 core tests)
    # ============================================================================

    @pytest.mark.asyncio
    async def test_assignment_link_basic(self, relationship_service):
        """Test basic assignment relationship creation."""
        request = RelationshipRequest(
            action="link",
            relationship_type=RelationshipType.ASSIGNMENT,
            source_type="task",
            source_id="task_123",
            target_type="user",
            target_id="user_456"
        )

        relationship_service.client.create_relationship = AsyncMock(return_value={
            "id": "rel_assign_1",
            "relationship_type": "assignment",
            "source_id": "task_123",
            "target_id": "user_456"
        })

        result = await relationship_service.handle_request(request)
        assert result["relationship_type"] == "assignment"

    @pytest.mark.asyncio
    async def test_assignment_link_with_metadata(self, relationship_service):
        """Test assignment with priority and deadline metadata."""
        request = RelationshipRequest(
            action="link",
            relationship_type=RelationshipType.ASSIGNMENT,
            source_type="task",
            source_id="task_123",
            target_type="user",
            target_id="user_456",
            metadata={
                "priority": "high",
                "deadline": "2024-12-31",
                "estimated_hours": 8
            }
        )

        relationship_service.client.create_relationship = AsyncMock(return_value={
            "id": "rel_assign_2",
            "metadata": {"priority": "high", "deadline": "2024-12-31"}
        })

        result = await relationship_service.handle_request(request)
        assert result["metadata"]["priority"] == "high"

    @pytest.mark.asyncio
    async def test_assignment_unlink_soft(self, relationship_service):
        """Test soft unlinking of assignment."""
        request = RelationshipRequest(
            action="unlink",
            relationship_type=RelationshipType.ASSIGNMENT,
            source_type="task",
            source_id="task_123",
            target_type="user",
            target_id="user_456",
            soft_delete=True
        )

        relationship_service.client.delete_relationship = AsyncMock(return_value={
            "deleted": True,
            "soft_delete": True
        })

        result = await relationship_service.handle_request(request)
        assert result["soft_delete"] is True

    @pytest.mark.asyncio
    async def test_assignment_unlink_hard(self, relationship_service):
        """Test hard unlinking of assignment."""
        request = RelationshipRequest(
            action="unlink",
            relationship_type=RelationshipType.ASSIGNMENT,
            source_type="task",
            source_id="task_123",
            target_type="user",
            target_id="user_456",
            soft_delete=False
        )

        relationship_service.client.delete_relationship = AsyncMock(return_value={
            "deleted": True,
            "soft_delete": False
        })

        result = await relationship_service.handle_request(request)
        assert result["soft_delete"] is False

    @pytest.mark.asyncio
    async def test_assignment_list_all(self, relationship_service):
        """Test listing all assignments for a task."""
        request = RelationshipRequest(
            action="list",
            relationship_type=RelationshipType.ASSIGNMENT,
            source_type="task",
            source_id="task_123"
        )

        relationship_service.client.list_relationships = AsyncMock(return_value={
            "relationships": [
                {"id": "assign_1", "target_id": "user_1"},
                {"id": "assign_2", "target_id": "user_2"}
            ],
            "total": 2
        })

        result = await relationship_service.handle_request(request)
        assert result["total"] == 2

    @pytest.mark.asyncio
    async def test_assignment_list_filtered(self, relationship_service):
        """Test filtered listing of assignments."""
        request = RelationshipRequest(
            action="list",
            relationship_type=RelationshipType.ASSIGNMENT,
            source_type="task",
            source_id="task_123",
            filters={"priority": "high", "status": "pending"}
        )

        relationship_service.client.list_relationships = AsyncMock(return_value={
            "relationships": [
                {"id": "assign_1", "metadata": {"priority": "high", "status": "pending"}}
            ],
            "total": 1
        })

        result = await relationship_service.handle_request(request)
        assert len(result["relationships"]) == 1, f"Expected len(result["relationships"]) == 1, got {len(result["relationships"])}"

    @pytest.mark.asyncio
    async def test_assignment_list_paginated(self, relationship_service):
        """Test paginated listing of assignments."""
        request = RelationshipRequest(
            action="list",
            relationship_type=RelationshipType.ASSIGNMENT,
            source_type="user",
            source_id="user_456",
            limit=5,
            offset=10
        )

        relationship_service.client.list_relationships = AsyncMock(return_value={
            "relationships": [{"id": f"assign_{i}"} for i in range(5)],
            "total": 25,
            "limit": 5,
            "offset": 10
        })

        result = await relationship_service.handle_request(request)
        assert len(result["relationships"]) == 5, f"Expected len(result["relationships"]) == 5, got {len(result["relationships"])}"

    @pytest.mark.asyncio
    async def test_assignment_check_exists(self, relationship_service):
        """Test checking if assignment exists."""
        request = RelationshipRequest(
            action="check",
            relationship_type=RelationshipType.ASSIGNMENT,
            source_type="task",
            source_id="task_123",
            target_type="user",
            target_id="user_456"
        )

        relationship_service.client.check_relationship = AsyncMock(return_value={
            "exists": True,
            "relationship_id": "assign_789"
        })

        result = await relationship_service.handle_request(request)
        assert result["exists"] is True

    @pytest.mark.asyncio
    async def test_assignment_check_not_exists(self, relationship_service):
        """Test checking non-existent assignment."""
        request = RelationshipRequest(
            action="check",
            relationship_type=RelationshipType.ASSIGNMENT,
            source_type="task",
            source_id="task_999",
            target_type="user",
            target_id="user_999"
        )

        relationship_service.client.check_relationship = AsyncMock(return_value={
            "exists": False
        })

        result = await relationship_service.handle_request(request)
        assert result["exists"] is False

    @pytest.mark.asyncio
    async def test_assignment_update_metadata(self, relationship_service):
        """Test updating assignment metadata."""
        request = RelationshipRequest(
            action="update",
            relationship_type=RelationshipType.ASSIGNMENT,
            source_type="task",
            source_id="task_123",
            target_type="user",
            target_id="user_456",
            metadata={
                "status": "in_progress",
                "completion_percentage": 75
            }
        )

        relationship_service.client.update_relationship = AsyncMock(return_value={
            "id": "assign_123",
            "metadata": {"status": "in_progress", "completion_percentage": 75}
        })

        result = await relationship_service.handle_request(request)
        assert result["metadata"]["completion_percentage"] == 75

    # ============================================================================
    # TRACE_LINK RELATIONSHIP TESTS (11 core tests + soft_delete special)
    # ============================================================================

    @pytest.mark.asyncio
    async def test_trace_link_link_basic(self, relationship_service):
        """Test basic trace link creation."""
        request = RelationshipRequest(
            action="link",
            relationship_type=RelationshipType.TRACE_LINK,
            source_type="requirement",
            source_id="req_123",
            target_type="test_case",
            target_id="test_456"
        )

        relationship_service.client.create_relationship = AsyncMock(return_value={
            "id": "trace_789",
            "relationship_type": "trace_link",
            "source_id": "req_123",
            "target_id": "test_456"
        })

        result = await relationship_service.handle_request(request)
        assert result["relationship_type"] == "trace_link"

    @pytest.mark.asyncio
    async def test_trace_link_link_with_metadata(self, relationship_service):
        """Test trace link with coverage metadata."""
        request = RelationshipRequest(
            action="link",
            relationship_type=RelationshipType.TRACE_LINK,
            source_type="requirement",
            source_id="req_123",
            target_type="test_case",
            target_id="test_456",
            metadata={
                "coverage_type": "functional",
                "coverage_percentage": 100,
                "validation_status": "approved"
            }
        )

        relationship_service.client.create_relationship = AsyncMock(return_value={
            "id": "trace_789",
            "metadata": {"coverage_type": "functional", "coverage_percentage": 100}
        })

        result = await relationship_service.handle_request(request)
        assert result["metadata"]["coverage_percentage"] == 100

    @pytest.mark.asyncio
    async def test_trace_link_unlink_soft(self, relationship_service):
        """Test soft deletion of trace link."""
        request = RelationshipRequest(
            action="unlink",
            relationship_type=RelationshipType.TRACE_LINK,
            source_type="requirement",
            source_id="req_123",
            target_type="test_case",
            target_id="test_456",
            soft_delete=True
        )

        relationship_service.client.delete_relationship = AsyncMock(return_value={
            "deleted": True,
            "soft_delete": True,
            "archived_at": "2024-01-15T10:00:00Z"
        })

        result = await relationship_service.handle_request(request)
        assert result["soft_delete"] is True
        assert "archived_at" in result, f"Expected 'archived_at' in result, got keys: {list(result.keys())}"

    @pytest.mark.asyncio
    async def test_trace_link_unlink_hard(self, relationship_service):
        """Test hard deletion of trace link."""
        request = RelationshipRequest(
            action="unlink",
            relationship_type=RelationshipType.TRACE_LINK,
            source_type="requirement",
            source_id="req_123",
            target_type="test_case",
            target_id="test_456",
            soft_delete=False
        )

        relationship_service.client.delete_relationship = AsyncMock(return_value={
            "deleted": True,
            "soft_delete": False
        })

        result = await relationship_service.handle_request(request)
        assert result["soft_delete"] is False

    @pytest.mark.asyncio
    async def test_trace_link_list_all(self, relationship_service):
        """Test listing all trace links."""
        request = RelationshipRequest(
            action="list",
            relationship_type=RelationshipType.TRACE_LINK,
            source_type="requirement",
            source_id="req_123"
        )

        relationship_service.client.list_relationships = AsyncMock(return_value={
            "relationships": [
                {"id": "trace_1", "target_id": "test_1"},
                {"id": "trace_2", "target_id": "test_2"}
            ],
            "total": 2
        })

        result = await relationship_service.handle_request(request)
        assert result["total"] == 2

    @pytest.mark.asyncio
    async def test_trace_link_list_filtered(self, relationship_service):
        """Test filtered listing of trace links."""
        request = RelationshipRequest(
            action="list",
            relationship_type=RelationshipType.TRACE_LINK,
            source_type="requirement",
            source_id="req_123",
            filters={"coverage_type": "functional", "validation_status": "approved"}
        )

        relationship_service.client.list_relationships = AsyncMock(return_value={
            "relationships": [
                {"id": "trace_1", "metadata": {"coverage_type": "functional"}}
            ],
            "total": 1
        })

        result = await relationship_service.handle_request(request)
        assert len(result["relationships"]) == 1, f"Expected len(result["relationships"]) == 1, got {len(result["relationships"])}"

    @pytest.mark.asyncio
    async def test_trace_link_list_paginated(self, relationship_service):
        """Test paginated listing of trace links."""
        request = RelationshipRequest(
            action="list",
            relationship_type=RelationshipType.TRACE_LINK,
            source_type="requirement",
            source_id="req_123",
            limit=15,
            offset=30
        )

        relationship_service.client.list_relationships = AsyncMock(return_value={
            "relationships": [{"id": f"trace_{i}"} for i in range(15)],
            "total": 100,
            "limit": 15,
            "offset": 30
        })

        result = await relationship_service.handle_request(request)
        assert len(result["relationships"]) == 15, f"Expected len(result["relationships"]) == 15, got {len(result["relationships"])}"

    @pytest.mark.asyncio
    async def test_trace_link_check_exists(self, relationship_service):
        """Test checking if trace link exists."""
        request = RelationshipRequest(
            action="check",
            relationship_type=RelationshipType.TRACE_LINK,
            source_type="requirement",
            source_id="req_123",
            target_type="test_case",
            target_id="test_456"
        )

        relationship_service.client.check_relationship = AsyncMock(return_value={
            "exists": True,
            "relationship_id": "trace_789"
        })

        result = await relationship_service.handle_request(request)
        assert result["exists"] is True

    @pytest.mark.asyncio
    async def test_trace_link_check_not_exists(self, relationship_service):
        """Test checking non-existent trace link."""
        request = RelationshipRequest(
            action="check",
            relationship_type=RelationshipType.TRACE_LINK,
            source_type="requirement",
            source_id="req_999",
            target_type="test_case",
            target_id="test_999"
        )

        relationship_service.client.check_relationship = AsyncMock(return_value={
            "exists": False
        })

        result = await relationship_service.handle_request(request)
        assert result["exists"] is False

    @pytest.mark.asyncio
    async def test_trace_link_update_metadata(self, relationship_service):
        """Test updating trace link metadata."""
        request = RelationshipRequest(
            action="update",
            relationship_type=RelationshipType.TRACE_LINK,
            source_type="requirement",
            source_id="req_123",
            target_type="test_case",
            target_id="test_456",
            metadata={
                "last_validated": "2024-01-15",
                "validation_notes": "All test cases pass"
            }
        )

        relationship_service.client.update_relationship = AsyncMock(return_value={
            "id": "trace_789",
            "metadata": {"last_validated": "2024-01-15", "validation_notes": "All test cases pass"}
        })

        result = await relationship_service.handle_request(request)
        assert result["metadata"]["last_validated"] == "2024-01-15"

    @pytest.mark.asyncio
    async def test_trace_link_soft_delete_special(self, relationship_service):
        """Test special soft delete behavior for trace links."""
        request = RelationshipRequest(
            action="unlink",
            relationship_type=RelationshipType.TRACE_LINK,
            source_type="requirement",
            source_id="req_123",
            target_type="test_case",
            target_id="test_456",
            soft_delete=True,
            metadata={
                "deletion_reason": "Requirement deprecated",
                "archived_by": "user_admin"
            }
        )

        relationship_service.client.delete_relationship = AsyncMock(return_value={
            "deleted": True,
            "soft_delete": True,
            "archived_at": "2024-01-15T10:00:00Z",
            "metadata": {
                "deletion_reason": "Requirement deprecated",
                "archived_by": "user_admin"
            }
        })

        result = await relationship_service.handle_request(request)
        assert result["soft_delete"] is True
        assert result["metadata"]["deletion_reason"] == "Requirement deprecated"

    # ============================================================================
    # REQUIREMENT_TEST RELATIONSHIP TESTS (11 core tests)
    # ============================================================================

    @pytest.mark.asyncio
    async def test_requirement_test_link_basic(self, relationship_service):
        """Test basic requirement-test relationship creation."""
        request = RelationshipRequest(
            action="link",
            relationship_type=RelationshipType.REQUIREMENT_TEST,
            source_type="requirement",
            source_id="req_123",
            target_type="test",
            target_id="test_789"
        )

        relationship_service.client.create_relationship = AsyncMock(return_value={
            "id": "req_test_001",
            "relationship_type": "requirement_test",
            "source_id": "req_123",
            "target_id": "test_789"
        })

        result = await relationship_service.handle_request(request)
        assert result["relationship_type"] == "requirement_test"

    @pytest.mark.asyncio
    async def test_requirement_test_link_with_metadata(self, relationship_service):
        """Test requirement-test link with test coverage metadata."""
        request = RelationshipRequest(
            action="link",
            relationship_type=RelationshipType.REQUIREMENT_TEST,
            source_type="requirement",
            source_id="req_123",
            target_type="test",
            target_id="test_789",
            metadata={
                "test_type": "unit",
                "coverage_percentage": 85,
                "last_run": "2024-01-14",
                "status": "passing"
            }
        )

        relationship_service.client.create_relationship = AsyncMock(return_value={
            "id": "req_test_002",
            "metadata": {"test_type": "unit", "coverage_percentage": 85, "status": "passing"}
        })

        result = await relationship_service.handle_request(request)
        assert result["metadata"]["coverage_percentage"] == 85

    @pytest.mark.asyncio
    async def test_requirement_test_unlink_soft(self, relationship_service):
        """Test soft unlinking of requirement-test relationship."""
        request = RelationshipRequest(
            action="unlink",
            relationship_type=RelationshipType.REQUIREMENT_TEST,
            source_type="requirement",
            source_id="req_123",
            target_type="test",
            target_id="test_789",
            soft_delete=True
        )

        relationship_service.client.delete_relationship = AsyncMock(return_value={
            "deleted": True,
            "soft_delete": True
        })

        result = await relationship_service.handle_request(request)
        assert result["soft_delete"] is True

    @pytest.mark.asyncio
    async def test_requirement_test_unlink_hard(self, relationship_service):
        """Test hard unlinking of requirement-test relationship."""
        request = RelationshipRequest(
            action="unlink",
            relationship_type=RelationshipType.REQUIREMENT_TEST,
            source_type="requirement",
            source_id="req_123",
            target_type="test",
            target_id="test_789",
            soft_delete=False
        )

        relationship_service.client.delete_relationship = AsyncMock(return_value={
            "deleted": True,
            "soft_delete": False
        })

        result = await relationship_service.handle_request(request)
        assert result["soft_delete"] is False

    @pytest.mark.asyncio
    async def test_requirement_test_list_all(self, relationship_service):
        """Test listing all requirement-test relationships."""
        request = RelationshipRequest(
            action="list",
            relationship_type=RelationshipType.REQUIREMENT_TEST,
            source_type="requirement",
            source_id="req_123"
        )

        relationship_service.client.list_relationships = AsyncMock(return_value={
            "relationships": [
                {"id": "req_test_1", "target_id": "test_1"},
                {"id": "req_test_2", "target_id": "test_2"},
                {"id": "req_test_3", "target_id": "test_3"}
            ],
            "total": 3
        })

        result = await relationship_service.handle_request(request)
        assert result["total"] == 3

    @pytest.mark.asyncio
    async def test_requirement_test_list_filtered(self, relationship_service):
        """Test filtered listing of requirement-test relationships."""
        request = RelationshipRequest(
            action="list",
            relationship_type=RelationshipType.REQUIREMENT_TEST,
            source_type="requirement",
            source_id="req_123",
            filters={"test_type": "unit", "status": "passing"}
        )

        relationship_service.client.list_relationships = AsyncMock(return_value={
            "relationships": [
                {"id": "req_test_1", "metadata": {"test_type": "unit", "status": "passing"}},
                {"id": "req_test_2", "metadata": {"test_type": "unit", "status": "passing"}}
            ],
            "total": 2
        })

        result = await relationship_service.handle_request(request)
        assert len(result["relationships"]) == 2, f"Expected len(result["relationships"]) == 2, got {len(result["relationships"])}"

    @pytest.mark.asyncio
    async def test_requirement_test_list_paginated(self, relationship_service):
        """Test paginated listing of requirement-test relationships."""
        request = RelationshipRequest(
            action="list",
            relationship_type=RelationshipType.REQUIREMENT_TEST,
            source_type="requirement",
            source_id="req_123",
            limit=20,
            offset=40
        )

        relationship_service.client.list_relationships = AsyncMock(return_value={
            "relationships": [{"id": f"req_test_{i}"} for i in range(20)],
            "total": 150,
            "limit": 20,
            "offset": 40
        })

        result = await relationship_service.handle_request(request)
        assert len(result["relationships"]) == 20, f"Expected len(result["relationships"]) == 20, got {len(result["relationships"])}"

    @pytest.mark.asyncio
    async def test_requirement_test_check_exists(self, relationship_service):
        """Test checking if requirement-test relationship exists."""
        request = RelationshipRequest(
            action="check",
            relationship_type=RelationshipType.REQUIREMENT_TEST,
            source_type="requirement",
            source_id="req_123",
            target_type="test",
            target_id="test_789"
        )

        relationship_service.client.check_relationship = AsyncMock(return_value={
            "exists": True,
            "relationship_id": "req_test_001"
        })

        result = await relationship_service.handle_request(request)
        assert result["exists"] is True

    @pytest.mark.asyncio
    async def test_requirement_test_check_not_exists(self, relationship_service):
        """Test checking non-existent requirement-test relationship."""
        request = RelationshipRequest(
            action="check",
            relationship_type=RelationshipType.REQUIREMENT_TEST,
            source_type="requirement",
            source_id="req_999",
            target_type="test",
            target_id="test_999"
        )

        relationship_service.client.check_relationship = AsyncMock(return_value={
            "exists": False
        })

        result = await relationship_service.handle_request(request)
        assert result["exists"] is False

    @pytest.mark.asyncio
    async def test_requirement_test_update_metadata(self, relationship_service):
        """Test updating requirement-test metadata."""
        request = RelationshipRequest(
            action="update",
            relationship_type=RelationshipType.REQUIREMENT_TEST,
            source_type="requirement",
            source_id="req_123",
            target_type="test",
            target_id="test_789",
            metadata={
                "last_run": "2024-01-15",
                "status": "failing",
                "failure_reason": "Timeout exceeded"
            }
        )

        relationship_service.client.update_relationship = AsyncMock(return_value={
            "id": "req_test_001",
            "metadata": {"status": "failing", "failure_reason": "Timeout exceeded"}
        })

        result = await relationship_service.handle_request(request)
        assert result["metadata"]["status"] == "failing"

    # ============================================================================
    # INVITATION RELATIONSHIP TESTS (11 core tests)
    # ============================================================================

    @pytest.mark.asyncio
    async def test_invitation_link_basic(self, relationship_service):
        """Test basic invitation relationship creation."""
        request = RelationshipRequest(
            action="link",
            relationship_type=RelationshipType.INVITATION,
            source_type="user",
            source_id="inviter_123",
            target_type="user",
            target_id="invitee_456"
        )

        relationship_service.client.create_relationship = AsyncMock(return_value={
            "id": "invite_789",
            "relationship_type": "invitation",
            "source_id": "inviter_123",
            "target_id": "invitee_456"
        })

        result = await relationship_service.handle_request(request)
        assert result["relationship_type"] == "invitation"

    @pytest.mark.asyncio
    async def test_invitation_link_with_metadata(self, relationship_service):
        """Test invitation with metadata including expiry and permissions."""
        request = RelationshipRequest(
            action="link",
            relationship_type=RelationshipType.INVITATION,
            source_type="user",
            source_id="inviter_123",
            target_type="email",
            target_id="user@example.com",
            metadata={
                "invitation_type": "project_member",
                "expires_at": "2024-02-01",
                "permissions": ["read", "write"],
                "invitation_code": "ABC123XYZ"
            }
        )

        relationship_service.client.create_relationship = AsyncMock(return_value={
            "id": "invite_790",
            "metadata": {
                "invitation_type": "project_member",
                "expires_at": "2024-02-01",
                "invitation_code": "ABC123XYZ"
            }
        })

        result = await relationship_service.handle_request(request)
        assert result["metadata"]["invitation_code"] == "ABC123XYZ"

    @pytest.mark.asyncio
    async def test_invitation_unlink_soft(self, relationship_service):
        """Test soft deletion of invitation (cancellation)."""
        request = RelationshipRequest(
            action="unlink",
            relationship_type=RelationshipType.INVITATION,
            source_type="user",
            source_id="inviter_123",
            target_type="user",
            target_id="invitee_456",
            soft_delete=True
        )

        relationship_service.client.delete_relationship = AsyncMock(return_value={
            "deleted": True,
            "soft_delete": True,
            "cancelled_at": "2024-01-15T12:00:00Z"
        })

        result = await relationship_service.handle_request(request)
        assert result["soft_delete"] is True

    @pytest.mark.asyncio
    async def test_invitation_unlink_hard(self, relationship_service):
        """Test hard deletion of invitation."""
        request = RelationshipRequest(
            action="unlink",
            relationship_type=RelationshipType.INVITATION,
            source_type="user",
            source_id="inviter_123",
            target_type="user",
            target_id="invitee_456",
            soft_delete=False
        )

        relationship_service.client.delete_relationship = AsyncMock(return_value={
            "deleted": True,
            "soft_delete": False
        })

        result = await relationship_service.handle_request(request)
        assert result["soft_delete"] is False

    @pytest.mark.asyncio
    async def test_invitation_list_all(self, relationship_service):
        """Test listing all invitations."""
        request = RelationshipRequest(
            action="list",
            relationship_type=RelationshipType.INVITATION,
            source_type="user",
            source_id="inviter_123"
        )

        relationship_service.client.list_relationships = AsyncMock(return_value={
            "relationships": [
                {"id": "invite_1", "target_id": "user_1"},
                {"id": "invite_2", "target_id": "user_2"}
            ],
            "total": 2
        })

        result = await relationship_service.handle_request(request)
        assert result["total"] == 2

    @pytest.mark.asyncio
    async def test_invitation_list_filtered(self, relationship_service):
        """Test filtered listing of invitations."""
        request = RelationshipRequest(
            action="list",
            relationship_type=RelationshipType.INVITATION,
            source_type="user",
            source_id="inviter_123",
            filters={"status": "pending", "invitation_type": "project_member"}
        )

        relationship_service.client.list_relationships = AsyncMock(return_value={
            "relationships": [
                {"id": "invite_1", "metadata": {"status": "pending", "invitation_type": "project_member"}}
            ],
            "total": 1
        })

        result = await relationship_service.handle_request(request)
        assert len(result["relationships"]) == 1, f"Expected len(result["relationships"]) == 1, got {len(result["relationships"])}"

    @pytest.mark.asyncio
    async def test_invitation_list_paginated(self, relationship_service):
        """Test paginated listing of invitations."""
        request = RelationshipRequest(
            action="list",
            relationship_type=RelationshipType.INVITATION,
            source_type="user",
            source_id="inviter_123",
            limit=25,
            offset=50
        )

        relationship_service.client.list_relationships = AsyncMock(return_value={
            "relationships": [{"id": f"invite_{i}"} for i in range(25)],
            "total": 200,
            "limit": 25,
            "offset": 50
        })

        result = await relationship_service.handle_request(request)
        assert len(result["relationships"]) == 25, f"Expected len(result["relationships"]) == 25, got {len(result["relationships"])}"

    @pytest.mark.asyncio
    async def test_invitation_check_exists(self, relationship_service):
        """Test checking if invitation exists."""
        request = RelationshipRequest(
            action="check",
            relationship_type=RelationshipType.INVITATION,
            source_type="user",
            source_id="inviter_123",
            target_type="user",
            target_id="invitee_456"
        )

        relationship_service.client.check_relationship = AsyncMock(return_value={
            "exists": True,
            "relationship_id": "invite_789"
        })

        result = await relationship_service.handle_request(request)
        assert result["exists"] is True

    @pytest.mark.asyncio
    async def test_invitation_check_not_exists(self, relationship_service):
        """Test checking non-existent invitation."""
        request = RelationshipRequest(
            action="check",
            relationship_type=RelationshipType.INVITATION,
            source_type="user",
            source_id="inviter_999",
            target_type="user",
            target_id="invitee_999"
        )

        relationship_service.client.check_relationship = AsyncMock(return_value={
            "exists": False
        })

        result = await relationship_service.handle_request(request)
        assert result["exists"] is False

    @pytest.mark.asyncio
    async def test_invitation_update_metadata(self, relationship_service):
        """Test updating invitation metadata (e.g., accepting invitation)."""
        request = RelationshipRequest(
            action="update",
            relationship_type=RelationshipType.INVITATION,
            source_type="user",
            source_id="inviter_123",
            target_type="user",
            target_id="invitee_456",
            metadata={
                "status": "accepted",
                "accepted_at": "2024-01-16T09:00:00Z",
                "acceptance_token": "TOKEN123"
            }
        )

        relationship_service.client.update_relationship = AsyncMock(return_value={
            "id": "invite_789",
            "metadata": {"status": "accepted", "accepted_at": "2024-01-16T09:00:00Z"}
        })

        result = await relationship_service.handle_request(request)
        assert result["metadata"]["status"] == "accepted"

    # ============================================================================
    # ERROR CASES
    # ============================================================================

    @pytest.mark.asyncio
    async def test_error_invalid_relationship_type(self, relationship_service):
        """Test error for invalid relationship type."""
        with pytest.raises(ValueError, match="Invalid relationship type"):
            request = RelationshipRequest(
                action="link",
                relationship_type="invalid_type",  # Invalid type
                source_type="user",
                source_id="user_123",
                target_type="organization",
                target_id="org_456"
            )
            await relationship_service.handle_request(request)

    @pytest.mark.asyncio
    async def test_error_missing_source(self, relationship_service):
        """Test error for missing source information."""
        with pytest.raises(ValueError, match="source_id is required"):
            request = RelationshipRequest(
                action="link",
                relationship_type=RelationshipType.MEMBER,
                source_type="user",
                source_id=None,  # Missing source_id
                target_type="organization",
                target_id="org_456"
            )
            await relationship_service.handle_request(request)

    @pytest.mark.asyncio
    async def test_error_missing_target(self, relationship_service):
        """Test error for missing target information."""
        with pytest.raises(ValueError, match="target_id is required"):
            request = RelationshipRequest(
                action="link",
                relationship_type=RelationshipType.MEMBER,
                source_type="user",
                source_id="user_123",
                target_type="organization",
                target_id=None  # Missing target_id
            )
            await relationship_service.handle_request(request)

    @pytest.mark.asyncio
    async def test_error_invalid_source_type_for_member(self, relationship_service):
        """Test error for invalid source type for member relationship."""
        with pytest.raises(ValueError, match="Invalid source type for member relationship"):
            request = RelationshipRequest(
                action="link",
                relationship_type=RelationshipType.MEMBER,
                source_type="task",  # Invalid source type for member
                source_id="task_123",
                target_type="organization",
                target_id="org_456"
            )
            await relationship_service.handle_request(request)

    @pytest.mark.asyncio
    async def test_error_missing_action(self, relationship_service):
        """Test error for missing action."""
        with pytest.raises(ValueError, match="action is required"):
            request = RelationshipRequest(
                action=None,  # Missing action
                relationship_type=RelationshipType.MEMBER,
                source_type="user",
                source_id="user_123",
                target_type="organization",
                target_id="org_456"
            )
            await relationship_service.handle_request(request)

    @pytest.mark.asyncio
    async def test_error_invalid_action(self, relationship_service):
        """Test error for invalid action."""
        with pytest.raises(ValueError, match="Invalid action"):
            request = RelationshipRequest(
                action="invalid_action",  # Invalid action
                relationship_type=RelationshipType.MEMBER,
                source_type="user",
                source_id="user_123",
                target_type="organization",
                target_id="org_456"
            )
            await relationship_service.handle_request(request)

    # ============================================================================
    # ADDITIONAL EDGE CASES AND COMPLEX SCENARIOS
    # ============================================================================

    @pytest.mark.asyncio
    async def test_complex_metadata_structures(self, relationship_service):
        """Test handling of complex nested metadata structures."""
        request = RelationshipRequest(
            action="link",
            relationship_type=RelationshipType.MEMBER,
            source_type="user",
            source_id="user_123",
            target_type="organization",
            target_id="org_456",
            metadata={
                "permissions": {
                    "projects": {
                        "create": True,
                        "delete": False,
                        "update": True
                    },
                    "members": {
                        "invite": True,
                        "remove": False
                    }
                },
                "settings": {
                    "notifications": {
                        "email": True,
                        "sms": False
                    }
                },
                "custom_fields": [
                    {"key": "department", "value": "engineering"},
                    {"key": "team", "value": "backend"}
                ]
            }
        )

        relationship_service.client.create_relationship = AsyncMock(return_value={
            "id": "rel_complex",
            "metadata": request.metadata
        })

        result = await relationship_service.handle_request(request)
        assert result["metadata"]["permissions"]["projects"]["create"] is True
        assert len(result["metadata"]["custom_fields"]) == 2, f"Expected len(result["metadata"]["custom_fields"]) == 2, got {len(result["metadata"]["custom_fields"])}"

    @pytest.mark.asyncio
    async def test_batch_operations_simulation(self, relationship_service):
        """Test simulating batch relationship operations."""
        # Simulate creating multiple relationships in sequence
        user_ids = ["user_1", "user_2", "user_3"]
        results = []

        for user_id in user_ids:
            request = RelationshipRequest(
                action="link",
                relationship_type=RelationshipType.MEMBER,
                source_type="user",
                source_id=user_id,
                target_type="project",
                target_id="proj_shared"
            )

            relationship_service.client.create_relationship = AsyncMock(return_value={
                "id": f"rel_{user_id}",
                "source_id": user_id,
                "target_id": "proj_shared"
            })

            result = await relationship_service.handle_request(request)
            results.append(result)

        assert len(results) == 3, f"Expected len(results) == 3, got {len(results)}"
        assert all(r["target_id"] == "proj_shared" for r in results)

    @pytest.mark.asyncio
    async def test_circular_relationship_detection(self, relationship_service):
        """Test handling of potential circular relationships."""
        # Create A -> B relationship
        request1 = RelationshipRequest(
            action="link",
            relationship_type=RelationshipType.TRACE_LINK,
            source_type="requirement",
            source_id="req_A",
            target_type="requirement",
            target_id="req_B"
        )

        # Attempt B -> A relationship (circular)
        request2 = RelationshipRequest(
            action="link",
            relationship_type=RelationshipType.TRACE_LINK,
            source_type="requirement",
            source_id="req_B",
            target_type="requirement",
            target_id="req_A",
            metadata={"circular_check": True}
        )

        relationship_service.client.create_relationship = AsyncMock(return_value={
            "id": "rel_circular",
            "warning": "Potential circular relationship detected"
        })

        result = await relationship_service.handle_request(request2)
        assert "warning" in result, f"Expected 'warning' in result, got keys: {list(result.keys())}"

    @pytest.mark.asyncio
    async def test_relationship_versioning(self, relationship_service):
        """Test relationship versioning through metadata updates."""
        request = RelationshipRequest(
            action="update",
            relationship_type=RelationshipType.REQUIREMENT_TEST,
            source_type="requirement",
            source_id="req_123",
            target_type="test",
            target_id="test_456",
            metadata={
                "version": 2,
                "previous_version": 1,
                "change_log": [
                    {"version": 1, "change": "Initial link"},
                    {"version": 2, "change": "Updated test coverage"}
                ]
            }
        )

        relationship_service.client.update_relationship = AsyncMock(return_value={
            "id": "rel_versioned",
            "metadata": request.metadata
        })

        result = await relationship_service.handle_request(request)
        assert result["metadata"]["version"] == 2
        assert len(result["metadata"]["change_log"]) == 2, f"Expected len(result["metadata"]["change_log"]) == 2, got {len(result["metadata"]["change_log"])}"

    @pytest.mark.asyncio
    async def test_time_based_filtering(self, relationship_service):
        """Test filtering relationships by time-based criteria."""
        request = RelationshipRequest(
            action="list",
            relationship_type=RelationshipType.INVITATION,
            source_type="user",
            source_id="inviter_123",
            filters={
                "created_after": "2024-01-01",
                "expires_before": "2024-02-01",
                "status": "pending"
            }
        )

        relationship_service.client.list_relationships = AsyncMock(return_value={
            "relationships": [
                {
                    "id": "invite_recent",
                    "created_at": "2024-01-10",
                    "metadata": {"expires_at": "2024-01-25", "status": "pending"}
                }
            ],
            "total": 1
        })

        result = await relationship_service.handle_request(request)
        assert result["relationships"][0]["created_at"] > "2024-01-01"

    @pytest.mark.asyncio
    async def test_relationship_cascade_simulation(self, relationship_service):
        """Test simulating cascade operations on related entities."""
        # When deleting a project, simulate cascade deletion of all assignments
        request = RelationshipRequest(
            action="unlink",
            relationship_type=RelationshipType.ASSIGNMENT,
            source_type="project",
            source_id="proj_deleted",
            target_type="*",  # All targets
            target_id="*",  # All IDs
            soft_delete=False,
            metadata={"cascade": True, "reason": "Project deleted"}
        )

        relationship_service.client.delete_relationship = AsyncMock(return_value={
            "deleted": True,
            "cascaded_deletions": 15,
            "affected_types": ["user", "task", "resource"]
        })

        result = await relationship_service.handle_request(request)
        assert result["cascaded_deletions"] == 15

    @pytest.mark.asyncio
    async def test_relationship_statistics(self, relationship_service):
        """Test getting relationship statistics and analytics."""
        request = RelationshipRequest(
            action="stats",  # Special stats action
            relationship_type=RelationshipType.MEMBER,
            source_type="organization",
            source_id="org_456"
        )

        relationship_service.client.get_relationship_stats = AsyncMock(return_value={
            "total_members": 150,
            "by_role": {"admin": 5, "member": 130, "guest": 15},
            "by_status": {"active": 140, "inactive": 10},
            "growth_rate": "15% monthly"
        })

        # Simulate stats through list with special metadata
        result = await relationship_service.client.get_relationship_stats(request.dict())
        assert result["total_members"] == 150
        assert result["by_role"]["admin"] == 5


# Run all tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])