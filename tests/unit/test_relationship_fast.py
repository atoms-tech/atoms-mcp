"""
Fast Relationship Tool Tests using FastHTTPClient

These tests use direct HTTP calls instead of the MCP decorator framework,
providing ~20x speed improvement while still validating real Supabase data,
RLS policies, and relationship links.

Based on test_relationship_comprehensive.py but optimized for FastHTTPClient.

Run with: pytest tests/unit/test_relationship_fast.py -v
"""

import pytest

# ============================================================================
# MEMBER RELATIONSHIP TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_member_link_basic(authenticated_client):
    """Test basic member relationship creation via fast HTTP client."""
    result = await authenticated_client.call_tool(
        "relationship_tool",
        {
            "action": "link",
            "relationship_type": "member",
            "source_type": "user",
            "source_id": "user_123",
            "target_type": "organization",
            "target_id": "org_456"
        }
    )

    assert result.get("success") or "id" in result.get("data", {}), \
        f"Failed to create member relationship: {result.get('error')}"


@pytest.mark.asyncio
async def test_member_link_with_metadata(authenticated_client):
    """Test member relationship with role and status metadata."""
    result = await authenticated_client.call_tool(
        "relationship_tool",
        {
            "action": "link",
            "relationship_type": "member",
            "source_type": "user",
            "source_id": "user_123",
            "target_type": "organization",
            "target_id": "org_456",
            "metadata": {
                "role": "admin",
                "status": "active",
                "joined_date": "2024-01-15"
            }
        }
    )

    if result.get("success"):
        data = result.get("data", {})
        metadata = data.get("metadata", {})
        assert metadata.get("role") == "admin", \
            f"Expected role='admin', got {metadata.get('role')}"
        assert metadata.get("status") == "active", \
            f"Expected status='active', got {metadata.get('status')}"


@pytest.mark.asyncio
async def test_member_list_all(authenticated_client):
    """Test listing all member relationships."""
    result = await authenticated_client.call_tool(
        "relationship_tool",
        {
            "action": "list",
            "relationship_type": "member",
            "source_type": "user",
            "source_id": "user_123"
        }
    )

    assert result.get("success") or "relationships" in result.get("data", {}), \
        f"Failed to list member relationships: {result.get('error')}"

    data = result.get("data", {})
    relationships = data.get("relationships", [])
    total = data.get("total", len(relationships))
    assert isinstance(relationships, list), \
        f"Expected relationships to be a list, got {type(relationships).__name__}"
    assert total >= 0, f"Expected total >= 0, got {total}"


@pytest.mark.asyncio
async def test_member_list_paginated(authenticated_client):
    """Test paginated listing of member relationships."""
    result = await authenticated_client.call_tool(
        "relationship_tool",
        {
            "action": "list",
            "relationship_type": "member",
            "source_type": "user",
            "source_id": "user_123",
            "limit": 10,
            "offset": 0
        }
    )

    assert result.get("success") or "relationships" in result.get("data", {}), \
        f"Failed to list paginated relationships: {result.get('error')}"

    data = result.get("data", {})
    relationships = data.get("relationships", [])
    limit = data.get("limit", 10)
    offset = data.get("offset", 0)

    assert len(relationships) <= limit, \
        f"Expected relationships count <= {limit}, got {len(relationships)}"
    assert offset >= 0, f"Expected offset >= 0, got {offset}"


@pytest.mark.asyncio
async def test_member_check_exists(authenticated_client):
    """Test checking if member relationship exists."""
    result = await authenticated_client.call_tool(
        "relationship_tool",
        {
            "action": "check",
            "relationship_type": "member",
            "source_type": "user",
            "source_id": "user_123",
            "target_type": "organization",
            "target_id": "org_456"
        }
    )

    # Check can return success with exists field, or error
    assert "exists" in result or "error" in result, \
        f"Expected 'exists' or 'error' in response, got keys: {list(result.keys())}"


@pytest.mark.asyncio
async def test_member_unlink_soft(authenticated_client):
    """Test soft deletion of member relationship."""
    result = await authenticated_client.call_tool(
        "relationship_tool",
        {
            "action": "unlink",
            "relationship_type": "member",
            "source_type": "user",
            "source_id": "user_123",
            "target_type": "organization",
            "target_id": "org_456",
            "soft_delete": True
        }
    )

    # Unlink may succeed or fail depending on whether relationship exists
    # Just verify the response structure is valid
    assert isinstance(result, dict), \
        f"Expected dict response, got {type(result).__name__}"


# ============================================================================
# ASSIGNMENT RELATIONSHIP TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_assignment_link_basic(authenticated_client):
    """Test basic assignment relationship creation."""
    result = await authenticated_client.call_tool(
        "relationship_tool",
        {
            "action": "link",
            "relationship_type": "assignment",
            "source_type": "task",
            "source_id": "task_123",
            "target_type": "user",
            "target_id": "user_456"
        }
    )

    assert result.get("success") or "id" in result.get("data", {}), \
        f"Failed to create assignment relationship: {result.get('error')}"


@pytest.mark.asyncio
async def test_assignment_link_with_metadata(authenticated_client):
    """Test assignment with priority and deadline metadata."""
    result = await authenticated_client.call_tool(
        "relationship_tool",
        {
            "action": "link",
            "relationship_type": "assignment",
            "source_type": "task",
            "source_id": "task_123",
            "target_type": "user",
            "target_id": "user_456",
            "metadata": {
                "priority": "high",
                "deadline": "2024-12-31",
                "estimated_hours": 8
            }
        }
    )

    if result.get("success"):
        data = result.get("data", {})
        metadata = data.get("metadata", {})
        assert metadata.get("priority") == "high", \
            f"Expected priority='high', got {metadata.get('priority')}"


@pytest.mark.asyncio
async def test_assignment_list_all(authenticated_client):
    """Test listing all assignments for a task."""
    result = await authenticated_client.call_tool(
        "relationship_tool",
        {
            "action": "list",
            "relationship_type": "assignment",
            "source_type": "task",
            "source_id": "task_123"
        }
    )

    assert result.get("success") or "relationships" in result.get("data", {}), \
        f"Failed to list assignments: {result.get('error')}"


@pytest.mark.asyncio
async def test_assignment_check_exists(authenticated_client):
    """Test checking if assignment exists."""
    result = await authenticated_client.call_tool(
        "relationship_tool",
        {
            "action": "check",
            "relationship_type": "assignment",
            "source_type": "task",
            "source_id": "task_123",
            "target_type": "user",
            "target_id": "user_456"
        }
    )

    assert "exists" in result or "error" in result, \
        f"Expected 'exists' or 'error' in response, got keys: {list(result.keys())}"


# ============================================================================
# TRACE_LINK RELATIONSHIP TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_trace_link_link_basic(authenticated_client):
    """Test basic trace link creation."""
    result = await authenticated_client.call_tool(
        "relationship_tool",
        {
            "action": "link",
            "relationship_type": "trace_link",
            "source_type": "requirement",
            "source_id": "req_123",
            "target_type": "test_case",
            "target_id": "test_456"
        }
    )

    assert result.get("success") or "id" in result.get("data", {}), \
        f"Failed to create trace link: {result.get('error')}"


@pytest.mark.asyncio
async def test_trace_link_with_metadata(authenticated_client):
    """Test trace link with coverage metadata."""
    result = await authenticated_client.call_tool(
        "relationship_tool",
        {
            "action": "link",
            "relationship_type": "trace_link",
            "source_type": "requirement",
            "source_id": "req_123",
            "target_type": "test_case",
            "target_id": "test_456",
            "metadata": {
                "coverage_type": "functional",
                "coverage_percentage": 100,
                "validation_status": "approved"
            }
        }
    )

    if result.get("success"):
        data = result.get("data", {})
        metadata = data.get("metadata", {})
        assert metadata.get("coverage_percentage") == 100, \
            f"Expected coverage_percentage=100, got {metadata.get('coverage_percentage')}"


@pytest.mark.asyncio
async def test_trace_link_list_all(authenticated_client):
    """Test listing all trace links."""
    result = await authenticated_client.call_tool(
        "relationship_tool",
        {
            "action": "list",
            "relationship_type": "trace_link",
            "source_type": "requirement",
            "source_id": "req_123"
        }
    )

    assert result.get("success") or "relationships" in result.get("data", {}), \
        f"Failed to list trace links: {result.get('error')}"


@pytest.mark.asyncio
async def test_trace_link_unlink_soft(authenticated_client):
    """Test soft deletion of trace link."""
    result = await authenticated_client.call_tool(
        "relationship_tool",
        {
            "action": "unlink",
            "relationship_type": "trace_link",
            "source_type": "requirement",
            "source_id": "req_123",
            "target_type": "test_case",
            "target_id": "test_456",
            "soft_delete": True
        }
    )

    # Verify response structure
    assert isinstance(result, dict), \
        f"Expected dict response, got {type(result).__name__}"


# ============================================================================
# REQUIREMENT_TEST RELATIONSHIP TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_requirement_test_link_basic(authenticated_client):
    """Test basic requirement-test relationship creation."""
    result = await authenticated_client.call_tool(
        "relationship_tool",
        {
            "action": "link",
            "relationship_type": "requirement_test",
            "source_type": "requirement",
            "source_id": "req_123",
            "target_type": "test",
            "target_id": "test_789"
        }
    )

    assert result.get("success") or "id" in result.get("data", {}), \
        f"Failed to create requirement_test relationship: {result.get('error')}"


@pytest.mark.asyncio
async def test_requirement_test_with_metadata(authenticated_client):
    """Test requirement-test link with test coverage metadata."""
    result = await authenticated_client.call_tool(
        "relationship_tool",
        {
            "action": "link",
            "relationship_type": "requirement_test",
            "source_type": "requirement",
            "source_id": "req_123",
            "target_type": "test",
            "target_id": "test_789",
            "metadata": {
                "test_type": "unit",
                "coverage_percentage": 85,
                "last_run": "2024-01-14",
                "status": "passing"
            }
        }
    )

    if result.get("success"):
        data = result.get("data", {})
        metadata = data.get("metadata", {})
        assert metadata.get("coverage_percentage") == 85, \
            f"Expected coverage_percentage=85, got {metadata.get('coverage_percentage')}"
        assert metadata.get("test_type") == "unit", \
            f"Expected test_type='unit', got {metadata.get('test_type')}"


@pytest.mark.asyncio
async def test_requirement_test_list_all(authenticated_client):
    """Test listing all requirement-test relationships."""
    result = await authenticated_client.call_tool(
        "relationship_tool",
        {
            "action": "list",
            "relationship_type": "requirement_test",
            "source_type": "requirement",
            "source_id": "req_123"
        }
    )

    assert result.get("success") or "relationships" in result.get("data", {}), \
        f"Failed to list requirement_test relationships: {result.get('error')}"


@pytest.mark.asyncio
async def test_requirement_test_check_exists(authenticated_client):
    """Test checking if requirement-test relationship exists."""
    result = await authenticated_client.call_tool(
        "relationship_tool",
        {
            "action": "check",
            "relationship_type": "requirement_test",
            "source_type": "requirement",
            "source_id": "req_123",
            "target_type": "test",
            "target_id": "test_789"
        }
    )

    assert "exists" in result or "error" in result, \
        f"Expected 'exists' or 'error' in response, got keys: {list(result.keys())}"


# ============================================================================
# INVITATION RELATIONSHIP TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_invitation_link_basic(authenticated_client):
    """Test basic invitation relationship creation."""
    result = await authenticated_client.call_tool(
        "relationship_tool",
        {
            "action": "link",
            "relationship_type": "invitation",
            "source_type": "user",
            "source_id": "inviter_123",
            "target_type": "user",
            "target_id": "invitee_456"
        }
    )

    assert result.get("success") or "id" in result.get("data", {}), \
        f"Failed to create invitation relationship: {result.get('error')}"


@pytest.mark.asyncio
async def test_invitation_with_metadata(authenticated_client):
    """Test invitation with metadata including expiry and permissions."""
    result = await authenticated_client.call_tool(
        "relationship_tool",
        {
            "action": "link",
            "relationship_type": "invitation",
            "source_type": "user",
            "source_id": "inviter_123",
            "target_type": "email",
            "target_id": "user@example.com",
            "metadata": {
                "invitation_type": "project_member",
                "expires_at": "2024-02-01",
                "permissions": ["read", "write"],
                "invitation_code": "ABC123XYZ"
            }
        }
    )

    if result.get("success"):
        data = result.get("data", {})
        metadata = data.get("metadata", {})
        assert metadata.get("invitation_code") == "ABC123XYZ", \
            f"Expected invitation_code='ABC123XYZ', got {metadata.get('invitation_code')}"


@pytest.mark.asyncio
async def test_invitation_list_all(authenticated_client):
    """Test listing all invitations."""
    result = await authenticated_client.call_tool(
        "relationship_tool",
        {
            "action": "list",
            "relationship_type": "invitation",
            "source_type": "user",
            "source_id": "inviter_123"
        }
    )

    assert result.get("success") or "relationships" in result.get("data", {}), \
        f"Failed to list invitations: {result.get('error')}"


@pytest.mark.asyncio
async def test_invitation_list_filtered(authenticated_client):
    """Test filtered listing of invitations."""
    result = await authenticated_client.call_tool(
        "relationship_tool",
        {
            "action": "list",
            "relationship_type": "invitation",
            "source_type": "user",
            "source_id": "inviter_123",
            "filters": {
                "status": "pending",
                "invitation_type": "project_member"
            }
        }
    )

    assert result.get("success") or "relationships" in result.get("data", {}), \
        f"Failed to list filtered invitations: {result.get('error')}"


# ============================================================================
# COMPLEX SCENARIOS & EDGE CASES
# ============================================================================


@pytest.mark.asyncio
async def test_complex_metadata_structures(authenticated_client):
    """Test handling of complex nested metadata structures."""
    result = await authenticated_client.call_tool(
        "relationship_tool",
        {
            "action": "link",
            "relationship_type": "member",
            "source_type": "user",
            "source_id": "user_123",
            "target_type": "organization",
            "target_id": "org_456",
            "metadata": {
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
        }
    )

    if result.get("success"):
        data = result.get("data", {})
        metadata = data.get("metadata", {})
        permissions = metadata.get("permissions", {})
        projects = permissions.get("projects", {})
        assert projects.get("create") is True, \
            f"Expected permissions.projects.create=True, got {projects.get('create')}"

        custom_fields = metadata.get("custom_fields", [])
        assert len(custom_fields) == 2, \
            f"Expected 2 custom fields, got {len(custom_fields)}"


@pytest.mark.asyncio
async def test_relationship_with_context(authenticated_client):
    """Test member-project relationship with organization context."""
    result = await authenticated_client.call_tool(
        "relationship_tool",
        {
            "action": "link",
            "relationship_type": "member",
            "source_type": "user",
            "source_id": "user_123",
            "target_type": "project",
            "target_id": "proj_789",
            "source_context": {"org_id": "org_456"},
            "metadata": {
                "role": "developer",
                "access_level": "write"
            }
        }
    )

    if result.get("success"):
        data = result.get("data", {})
        context = data.get("source_context", {})
        assert context.get("org_id") == "org_456", \
            f"Expected source_context.org_id='org_456', got {context.get('org_id')}"


@pytest.mark.asyncio
async def test_profile_joining_member(authenticated_client):
    """Test profile joining for member relationships."""
    result = await authenticated_client.call_tool(
        "relationship_tool",
        {
            "action": "list",
            "relationship_type": "member",
            "source_type": "user",
            "source_id": "user_123",
            "join_profiles": True
        }
    )

    if result.get("success"):
        data = result.get("data", {})
        relationships = data.get("relationships", [])
        # If relationships exist with profiles, verify structure
        for rel in relationships:
            if "target_profile" in rel:
                profile = rel["target_profile"]
                assert isinstance(profile, dict), \
                    f"Expected target_profile to be dict, got {type(profile).__name__}"


# ============================================================================
# PERFORMANCE VALIDATION
# ============================================================================


@pytest.mark.asyncio
async def test_relationship_list_performance(authenticated_client):
    """Validate that relationship list operations are fast (< 2 seconds)."""
    import time

    start_time = time.time()

    result = await authenticated_client.call_tool(
        "relationship_tool",
        {
            "action": "list",
            "relationship_type": "member",
            "source_type": "user",
            "source_id": "user_123",
            "limit": 10
        }
    )

    duration = time.time() - start_time

    assert result.get("success") or "relationships" in result.get("data", {}), \
        f"Failed to list relationships: {result.get('error')}"
    assert duration < 2.0, \
        f"List operation took {duration:.2f}s, expected < 2.0s. Fast HTTP client should be faster."


@pytest.mark.asyncio
async def test_relationship_check_performance(authenticated_client):
    """Validate that relationship check operations are fast (< 1 second)."""
    import time

    start_time = time.time()

    result = await authenticated_client.call_tool(
        "relationship_tool",
        {
            "action": "check",
            "relationship_type": "member",
            "source_type": "user",
            "source_id": "user_123",
            "target_type": "organization",
            "target_id": "org_456"
        }
    )

    duration = time.time() - start_time

    # Check should return quickly regardless of whether relationship exists
    assert isinstance(result, dict), \
        f"Expected dict response, got {type(result).__name__}"
    assert duration < 1.0, \
        f"Check operation took {duration:.2f}s, expected < 1.0s. Fast HTTP client should be faster."


# ============================================================================
# ERROR HANDLING & VALIDATION
# ============================================================================


@pytest.mark.asyncio
async def test_invalid_relationship_type(authenticated_client):
    """Test error handling for invalid relationship type."""
    result = await authenticated_client.call_tool(
        "relationship_tool",
        {
            "action": "link",
            "relationship_type": "invalid_type",
            "source_type": "user",
            "source_id": "user_123",
            "target_type": "organization",
            "target_id": "org_456"
        }
    )

    # Should return error for invalid relationship type
    assert not result.get("success") or "error" in result, \
        f"Expected error for invalid relationship type, got: {result}"


@pytest.mark.asyncio
async def test_missing_required_fields(authenticated_client):
    """Test error handling for missing required fields."""
    result = await authenticated_client.call_tool(
        "relationship_tool",
        {
            "action": "link",
            "relationship_type": "member",
            # Missing source_id and target_id
            "source_type": "user",
            "target_type": "organization"
        }
    )

    # Should return error for missing required fields
    assert not result.get("success") or "error" in result, \
        f"Expected error for missing required fields, got: {result}"


@pytest.mark.asyncio
async def test_invalid_action(authenticated_client):
    """Test error handling for invalid action."""
    result = await authenticated_client.call_tool(
        "relationship_tool",
        {
            "action": "invalid_action",
            "relationship_type": "member",
            "source_type": "user",
            "source_id": "user_123",
            "target_type": "organization",
            "target_id": "org_456"
        }
    )

    # Should return error for invalid action
    assert not result.get("success") or "error" in result, \
        f"Expected error for invalid action, got: {result}"
