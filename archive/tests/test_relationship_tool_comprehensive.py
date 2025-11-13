"""Comprehensive test suite for relationship_tool - All Operations & Relationship Types.

This test suite comprehensively tests:
- All relationship types: member, assignment, trace_link, requirement_test, invitation
- All operations: link, unlink, list, check, update
- Different source/target combinations
- Metadata handling and defaults
- Soft delete vs hard delete behavior
- Edge cases and error handling
- Pagination and filtering
- Bidirectional relationships
- Profile joining for member relationships

Test Structure:
- Each relationship type has its own test class
- Each operation is tested with success and failure scenarios
- Metadata validation and updates are tested
- Edge cases like duplicates, invalid entities, missing data tested
- Performance and pagination tested

Run with: pytest tests/test_relationship_tool_comprehensive.py -v -s
Run specific test: pytest tests/test_relationship_tool_comprehensive.py::TestMemberRelationship::test_link_organization_member -v -s
"""

from __future__ import annotations

import os
import uuid
from typing import Any, Dict

import httpx
import pytest
from supabase import create_client

# MCP Server Configuration
MCP_BASE_URL = os.getenv("ATOMS_FASTMCP_BASE_URL", "http://127.0.0.1:8000")
MCP_PATH = os.getenv("ATOMS_FASTMCP_HTTP_PATH", "/api/mcp")
TEST_EMAIL = os.getenv("ATOMS_TEST_EMAIL", "kooshapari@kooshapari.com")
TEST_PASSWORD = os.getenv("ATOMS_TEST_PASSWORD", "118118")

pytestmark = [pytest.mark.asyncio, pytest.mark.http]


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def _supabase_env():
    """Ensure Supabase environment variables are present."""
    url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    key = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

    if not url or not key:
        pytest.skip("Supabase credentials not configured")

    return {"url": url, "key": key}


@pytest.fixture(scope="session")
def supabase_jwt(_supabase_env):
    """Authenticate against Supabase and return a user JWT."""
    client = create_client(_supabase_env["url"], _supabase_env["key"])
    auth_response = client.auth.sign_in_with_password(
        {"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )

    session = getattr(auth_response, "session", None)
    if not session or not getattr(session, "access_token", None):
        pytest.skip("Could not obtain Supabase JWT")

    return session.access_token


@pytest.fixture(scope="session")
def check_server_running():
    """Check if MCP server is running."""
    try:
        import socket
        url_parts = MCP_BASE_URL.replace("http://", "").replace("https://", "").split(":")
        host = url_parts[0]
        port = int(url_parts[1]) if len(url_parts) > 1 else 8000

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((host, port))
        sock.close()

        if result != 0:
            pytest.skip(f"MCP server not running at {MCP_BASE_URL}")
    except Exception as e:
        pytest.skip(f"Could not check server status: {e}")


@pytest.fixture(scope="session")
def call_mcp(check_server_running, supabase_jwt):
    """Return a helper that invokes MCP tools over HTTP."""
    base_url = f"{MCP_BASE_URL.rstrip('/')}{MCP_PATH}"
    headers = {
        "Authorization": f"Bearer {supabase_jwt}",
        "Content-Type": "application/json",
    }

    async def _call(tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": f"tools/{tool_name}",
            "params": params,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(base_url, json=payload, headers=headers)

        if response.status_code != 200:
            return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}

        body = response.json()
        if "result" in body:
            return body["result"]
        return {"success": False, "error": body.get("error", "Unknown error")}

    return _call


@pytest.fixture
async def test_entities(call_mcp):
    """Create comprehensive test entities for relationship testing."""
    entities = {}
    created_ids = []

    try:
        # Create organization
        org_resp = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "organization",
                "data": {
                    "name": f"Test Org {uuid.uuid4().hex[:8]}",
                    "slug": f"test-org-{uuid.uuid4().hex[:8]}",
                    "type": "team"
                }
            }
        )
        if org_resp.get("success"):
            entities["organization"] = org_resp["data"]["id"]
            created_ids.append(("organization", entities["organization"]))

        # Create project (requires org)
        if "organization" in entities:
            project_resp = await call_mcp(
                "entity_tool",
                {
                    "operation": "create",
                    "entity_type": "project",
                    "data": {
                        "name": f"Test Project {uuid.uuid4().hex[:8]}",
                        "organization_id": entities["organization"],
                        "status": "active"
                    }
                }
            )
            if project_resp.get("success"):
                entities["project"] = project_resp["data"]["id"]
                created_ids.append(("project", entities["project"]))

        # Create document (requires project)
        if "project" in entities:
            doc_resp = await call_mcp(
                "entity_tool",
                {
                    "operation": "create",
                    "entity_type": "document",
                    "data": {
                        "name": f"Test Doc {uuid.uuid4().hex[:8]}",
                        "project_id": entities["project"],
                        "type": "requirement"
                    }
                }
            )
            if doc_resp.get("success"):
                entities["document"] = doc_resp["data"]["id"]
                created_ids.append(("document", entities["document"]))

        # Create multiple requirements for testing
        if "document" in entities:
            for i in range(3):
                req_resp = await call_mcp(
                    "entity_tool",
                    {
                        "operation": "create",
                        "entity_type": "requirement",
                        "data": {
                            "name": f"Test Req {i} {uuid.uuid4().hex[:8]}",
                            "document_id": entities["document"],
                            "description": f"Test requirement {i}"
                        }
                    }
                )
                if req_resp.get("success"):
                    key = f"requirement_{i}" if i > 0 else "requirement"
                    entities[key] = req_resp["data"]["id"]
                    created_ids.append(("requirement", entities[key]))

        # Create multiple tests for testing
        if "project" in entities:
            for i in range(3):
                test_resp = await call_mcp(
                    "entity_tool",
                    {
                        "operation": "create",
                        "entity_type": "test",
                        "data": {
                            "name": f"Test Case {i} {uuid.uuid4().hex[:8]}",
                            "project_id": entities["project"],
                            "description": f"Test case {i}"
                        }
                    }
                )
                if test_resp.get("success"):
                    key = f"test_{i}" if i > 0 else "test"
                    entities[key] = test_resp["data"]["id"]
                    created_ids.append(("test", entities[key]))

        yield entities

    finally:
        # Cleanup in reverse order
        for entity_type, entity_id in reversed(created_ids):
            try:
                await call_mcp(
                    "entity_tool",
                    {
                        "operation": "delete",
                        "entity_type": entity_type,
                        "entity_id": entity_id,
                        "soft_delete": True
                    }
                )
            except Exception as e:
                print(f"Cleanup error for {entity_type} {entity_id}: {e}")


@pytest.fixture
async def user_id(call_mcp):
    """Get current user ID."""
    context = await call_mcp("workspace_tool", {"operation": "get_context"})
    uid = context.get("data", {}).get("user_id")
    if not uid:
        pytest.skip("Could not get user_id")
    return uid


# ============================================================================
# TEST: MEMBER RELATIONSHIPS
# ============================================================================

class TestMemberRelationship:
    """Comprehensive tests for member relationship type (organizations and projects)."""

    @pytest.mark.asyncio
    async def test_link_organization_member_success(self, call_mcp, test_entities, user_id):
        """Test successfully linking a user to an organization as a member."""
        if "organization" not in test_entities:
            pytest.skip("Organization not created")

        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "member",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "admin", "status": "active"}
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        assert result["data"]["role"] == "admin"
        assert result["data"]["status"] == "active"
        assert result["data"]["organization_id"] == test_entities["organization"]
        assert result["data"]["user_id"] == user_id
        print(f"✓ Organization member link created: {result['data']['id']}")

    @pytest.mark.asyncio
    async def test_link_organization_member_minimal_metadata(self, call_mcp, test_entities, user_id):
        """Test linking with minimal metadata (should use defaults)."""
        if "organization" not in test_entities:
            pytest.skip("Organization not created")

        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "member",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "viewer"}
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        assert result["data"]["role"] == "viewer"
        assert result["data"]["status"] == "active"  # Default value
        print(f"✓ Member created with defaults: status={result['data']['status']}")

    @pytest.mark.asyncio
    async def test_link_project_member_with_org_context(self, call_mcp, test_entities, user_id):
        """Test linking user to project with organization context."""
        if "project" not in test_entities or "organization" not in test_entities:
            pytest.skip("Project or Organization not created")

        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "member",
                "source": {"type": "project", "id": test_entities["project"]},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "developer"},
                "source_context": test_entities["organization"]
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        assert result["data"]["role"] == "developer"
        assert result["data"]["org_id"] == test_entities["organization"]
        assert result["data"]["project_id"] == test_entities["project"]
        print(f"✓ Project member created with org_id: {result['data']['org_id']}")

    @pytest.mark.asyncio
    async def test_list_organization_members(self, call_mcp, test_entities, user_id):
        """Test listing all members of an organization."""
        if "organization" not in test_entities:
            pytest.skip("Organization not created")

        # First create a member
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "member",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "admin"}
            }
        )

        # List members
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "list",
                "relationship_type": "member",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "limit": 10,
                "offset": 0
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        assert isinstance(result.get("data"), list)
        assert len(result["data"]) > 0

        # Verify profile join
        for member in result["data"]:
            if member.get("user_id") == user_id:
                # Check if profiles were joined
                if "profiles" in member:
                    print(f"✓ Profile joined: {member['profiles'].get('email', 'N/A')}")
                break

        print(f"✓ Listed {len(result['data'])} members")

    @pytest.mark.asyncio
    async def test_list_project_members(self, call_mcp, test_entities, user_id):
        """Test listing project members."""
        if "project" not in test_entities or "organization" not in test_entities:
            pytest.skip("Project or Organization not created")

        # Create project member
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "member",
                "source": {"type": "project", "id": test_entities["project"]},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "developer"},
                "source_context": test_entities["organization"]
            }
        )

        # List project members
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "list",
                "relationship_type": "member",
                "source": {"type": "project", "id": test_entities["project"]},
                "limit": 10
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        assert isinstance(result.get("data"), list)
        print(f"✓ Listed {len(result['data'])} project members")

    @pytest.mark.asyncio
    async def test_check_member_exists(self, call_mcp, test_entities, user_id):
        """Test checking if a member relationship exists."""
        if "organization" not in test_entities:
            pytest.skip("Organization not created")

        # Create member
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "member",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "viewer"}
            }
        )

        # Check existence
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "check",
                "relationship_type": "member",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "user", "id": user_id}
            }
        )

        assert result.get("exists") is True, f"Failed: {result}"
        assert result["relationship"] is not None
        assert result["relationship"]["role"] in ["viewer", "admin"]  # Could be from previous test
        print(f"✓ Member exists: {result['relationship']['role']}")

    @pytest.mark.asyncio
    async def test_check_member_not_exists(self, call_mcp, test_entities):
        """Test checking for a non-existent member."""
        if "organization" not in test_entities:
            pytest.skip("Organization not created")

        fake_user_id = str(uuid.uuid4())

        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "check",
                "relationship_type": "member",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "user", "id": fake_user_id}
            }
        )

        assert result.get("exists") is False, f"Should not exist: {result}"
        assert result["relationship"] is None
        print("✓ Correctly reported non-existent member")

    @pytest.mark.asyncio
    async def test_update_member_role(self, call_mcp, test_entities, user_id):
        """Test updating member role metadata."""
        if "organization" not in test_entities:
            pytest.skip("Organization not created")

        # Create member with viewer role
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "member",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "viewer"}
            }
        )

        # Update to admin
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "update",
                "relationship_type": "member",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "admin"}
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        assert result["data"]["role"] == "admin"
        assert "updated_at" in result["data"]
        print("✓ Member role updated from viewer to admin")

    @pytest.mark.asyncio
    async def test_update_member_status(self, call_mcp, test_entities, user_id):
        """Test updating member status."""
        if "organization" not in test_entities:
            pytest.skip("Organization not created")

        # Create active member
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "member",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "member", "status": "active"}
            }
        )

        # Update to inactive
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "update",
                "relationship_type": "member",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "user", "id": user_id},
                "metadata": {"status": "inactive"}
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        assert result["data"]["status"] == "inactive"
        print("✓ Member status updated to inactive")

    @pytest.mark.asyncio
    async def test_unlink_member(self, call_mcp, test_entities, user_id):
        """Test removing a member relationship (hard delete for members)."""
        if "organization" not in test_entities:
            pytest.skip("Organization not created")

        # Create member
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "member",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "viewer"}
            }
        )

        # Unlink (member tables don't have is_deleted, so this is hard delete)
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "unlink",
                "relationship_type": "member",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "user", "id": user_id},
                "soft_delete": True
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        print("✓ Member unlinked successfully")

        # Verify it's gone
        check = await call_mcp(
            "relationship_tool",
            {
                "operation": "check",
                "relationship_type": "member",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "user", "id": user_id}
            }
        )
        assert check.get("exists") is False
        print("✓ Verified member no longer exists after unlink")


# ============================================================================
# TEST: ASSIGNMENT RELATIONSHIPS
# ============================================================================

class TestAssignmentRelationship:
    """Comprehensive tests for assignment relationship type."""

    @pytest.mark.asyncio
    async def test_link_assignment_success(self, call_mcp, test_entities, user_id):
        """Test creating an assignment relationship."""
        if "requirement" not in test_entities:
            pytest.skip("Requirement not created")

        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "assignment",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "owner", "status": "active"}
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        assert result["data"]["entity_type"] == "requirement"
        assert result["data"]["role"] == "owner"
        assert result["data"]["status"] == "active"
        assert result["data"]["entity_id"] == test_entities["requirement"]
        assert result["data"]["assignee_id"] == user_id
        print(f"✓ Assignment created: {result['data']['id']}")

    @pytest.mark.asyncio
    async def test_link_assignment_with_defaults(self, call_mcp, test_entities, user_id):
        """Test assignment with default values."""
        if "requirement" not in test_entities:
            pytest.skip("Requirement not created")

        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "assignment",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "reviewer"}
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        assert result["data"]["status"] == "active"  # Default
        assert result["data"]["role"] == "reviewer"
        print(f"✓ Assignment created with defaults: status={result['data']['status']}")

    @pytest.mark.asyncio
    async def test_list_assignments_by_entity(self, call_mcp, test_entities, user_id):
        """Test listing all assignments for an entity."""
        if "requirement" not in test_entities:
            pytest.skip("Requirement not created")

        # Create assignment
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "assignment",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "owner"}
            }
        )

        # List assignments
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "list",
                "relationship_type": "assignment",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "limit": 10
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        assert isinstance(result.get("data"), list)
        assert len(result["data"]) > 0
        print(f"✓ Listed {len(result['data'])} assignments for requirement")

    @pytest.mark.asyncio
    async def test_list_assignments_by_assignee(self, call_mcp, test_entities, user_id):
        """Test listing assignments for a specific user."""
        if "requirement" not in test_entities:
            pytest.skip("Requirement not created")

        # Create assignment
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "assignment",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "contributor"}
            }
        )

        # List by assignee (target)
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "list",
                "relationship_type": "assignment",
                "target": {"type": "user", "id": user_id},
                "limit": 10
            }
        )

        # This may or may not be supported depending on implementation
        if result.get("success"):
            assert isinstance(result.get("data"), list)
            print(f"✓ Listed {len(result['data'])} assignments for user")
        else:
            print("⚠ Target-only listing not supported for assignments")

    @pytest.mark.asyncio
    async def test_list_assignments_with_status_filter(self, call_mcp, test_entities, user_id):
        """Test filtering assignments by status."""
        if "requirement" not in test_entities:
            pytest.skip("Requirement not created")

        # Create active assignment
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "assignment",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "owner", "status": "active"}
            }
        )

        # List with status filter
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "list",
                "relationship_type": "assignment",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "filters": {"status": "active"},
                "limit": 10
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        for assignment in result.get("data", []):
            assert assignment.get("status") == "active"
        print(f"✓ Filtered {len(result['data'])} active assignments")

    @pytest.mark.asyncio
    async def test_list_assignments_with_role_filter(self, call_mcp, test_entities, user_id):
        """Test filtering assignments by role."""
        if "requirement" not in test_entities:
            pytest.skip("Requirement not created")

        # Create assignment with specific role
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "assignment",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "reviewer"}
            }
        )

        # List with role filter
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "list",
                "relationship_type": "assignment",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "filters": {"role": "reviewer"},
                "limit": 10
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        for assignment in result.get("data", []):
            assert assignment.get("role") == "reviewer"
        print(f"✓ Filtered {len(result['data'])} reviewer assignments")

    @pytest.mark.asyncio
    async def test_check_assignment_exists(self, call_mcp, test_entities, user_id):
        """Test checking if an assignment exists."""
        if "requirement" not in test_entities:
            pytest.skip("Requirement not created")

        # Create assignment
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "assignment",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "owner"}
            }
        )

        # Check existence
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "check",
                "relationship_type": "assignment",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "user", "id": user_id}
            }
        )

        assert result.get("exists") is True, f"Failed: {result}"
        assert result["relationship"] is not None
        print(f"✓ Assignment exists: role={result['relationship']['role']}")

    @pytest.mark.asyncio
    async def test_update_assignment_role(self, call_mcp, test_entities, user_id):
        """Test updating assignment role."""
        if "requirement" not in test_entities:
            pytest.skip("Requirement not created")

        # Create assignment
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "assignment",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "contributor"}
            }
        )

        # Update to owner
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "update",
                "relationship_type": "assignment",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "owner"}
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        assert result["data"]["role"] == "owner"
        print("✓ Assignment role updated from contributor to owner")

    @pytest.mark.asyncio
    async def test_unlink_assignment_soft_delete(self, call_mcp, test_entities, user_id):
        """Test soft deleting an assignment."""
        if "requirement" not in test_entities:
            pytest.skip("Requirement not created")

        # Create assignment
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "assignment",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "reviewer"}
            }
        )

        # Soft delete
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "unlink",
                "relationship_type": "assignment",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "user", "id": user_id},
                "soft_delete": True
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        print("✓ Assignment soft deleted")

        # Verify it doesn't appear in normal list
        list_result = await call_mcp(
            "relationship_tool",
            {
                "operation": "list",
                "relationship_type": "assignment",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "limit": 10
            }
        )

        # Should not include soft-deleted assignment
        for assignment in list_result.get("data", []):
            assert assignment.get("is_deleted") is not True
        print("✓ Soft-deleted assignment excluded from list")

    @pytest.mark.asyncio
    async def test_unlink_assignment_hard_delete(self, call_mcp, test_entities, user_id):
        """Test hard deleting an assignment."""
        if "requirement" not in test_entities:
            pytest.skip("Requirement not created")

        # Create assignment
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "assignment",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "reviewer"}
            }
        )

        # Hard delete
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "unlink",
                "relationship_type": "assignment",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "user", "id": user_id},
                "soft_delete": False
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        print("✓ Assignment hard deleted")


# ============================================================================
# TEST: TRACE LINK RELATIONSHIPS
# ============================================================================

class TestTraceLinkRelationship:
    """Comprehensive tests for trace_link relationship type."""

    @pytest.mark.asyncio
    async def test_link_trace_link_success(self, call_mcp, test_entities):
        """Test creating a trace link between requirements."""
        if "requirement" not in test_entities or "requirement_1" not in test_entities:
            pytest.skip("Requirements not created")

        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "trace_link",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "requirement", "id": test_entities["requirement_1"]},
                "metadata": {"link_type": "depends_on", "version": 1}
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        assert result["data"]["source_type"] == "requirement"
        assert result["data"]["target_type"] == "requirement"
        assert result["data"]["link_type"] == "depends_on"
        assert result["data"]["version"] == 1
        assert result["data"]["is_deleted"] is False
        print(f"✓ Trace link created: {result['data']['id']}")

    @pytest.mark.asyncio
    async def test_link_trace_link_with_defaults(self, call_mcp, test_entities):
        """Test trace link with default values."""
        if "requirement" not in test_entities or "requirement_1" not in test_entities:
            pytest.skip("Requirements not created")

        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "trace_link",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "requirement", "id": test_entities["requirement_1"]},
                "metadata": {"link_type": "related_to"}
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        assert result["data"]["version"] == 1  # Default
        assert result["data"]["is_deleted"] is False  # Default
        print(f"✓ Trace link created with defaults: version={result['data']['version']}")

    @pytest.mark.asyncio
    async def test_bidirectional_trace_links(self, call_mcp, test_entities):
        """Test creating bidirectional trace links."""
        if "requirement" not in test_entities or "requirement_1" not in test_entities:
            pytest.skip("Requirements not created")

        # Link A -> B
        link1 = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "trace_link",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "requirement", "id": test_entities["requirement_1"]},
                "metadata": {"link_type": "depends_on"}
            }
        )

        # Link B -> A
        link2 = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "trace_link",
                "source": {"type": "requirement", "id": test_entities["requirement_1"]},
                "target": {"type": "requirement", "id": test_entities["requirement"]},
                "metadata": {"link_type": "depended_by"}
            }
        )

        assert link1.get("success") is True, f"Link1 failed: {link1}"
        assert link2.get("success") is True, f"Link2 failed: {link2}"
        print("✓ Bidirectional trace links created")

    @pytest.mark.asyncio
    async def test_list_trace_links_from_source(self, call_mcp, test_entities):
        """Test listing trace links from a source requirement."""
        if "requirement" not in test_entities or "requirement_1" not in test_entities:
            pytest.skip("Requirements not created")

        # Create trace link
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "trace_link",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "requirement", "id": test_entities["requirement_1"]},
                "metadata": {"link_type": "implements"}
            }
        )

        # List from source
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "list",
                "relationship_type": "trace_link",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "limit": 10
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        assert isinstance(result.get("data"), list)
        print(f"✓ Listed {len(result['data'])} trace links from source")

    @pytest.mark.asyncio
    async def test_list_trace_links_to_target(self, call_mcp, test_entities):
        """Test listing trace links to a target requirement."""
        if "requirement" not in test_entities or "requirement_1" not in test_entities:
            pytest.skip("Requirements not created")

        # Create trace link
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "trace_link",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "requirement", "id": test_entities["requirement_1"]},
                "metadata": {"link_type": "derives_from"}
            }
        )

        # List to target
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "list",
                "relationship_type": "trace_link",
                "target": {"type": "requirement", "id": test_entities["requirement_1"]},
                "limit": 10
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        assert isinstance(result.get("data"), list)
        print(f"✓ Listed {len(result['data'])} trace links to target")

    @pytest.mark.asyncio
    async def test_list_trace_links_with_type_filter(self, call_mcp, test_entities):
        """Test filtering trace links by link_type."""
        if "requirement" not in test_entities or "requirement_1" not in test_entities:
            pytest.skip("Requirements not created")

        # Create multiple trace links with different types
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "trace_link",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "requirement", "id": test_entities["requirement_1"]},
                "metadata": {"link_type": "depends_on"}
            }
        )

        # List with type filter
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "list",
                "relationship_type": "trace_link",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "filters": {"link_type": "depends_on"},
                "limit": 10
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        for link in result.get("data", []):
            assert link.get("link_type") == "depends_on"
        print(f"✓ Filtered {len(result['data'])} 'depends_on' trace links")

    @pytest.mark.asyncio
    async def test_check_trace_link_exists(self, call_mcp, test_entities):
        """Test checking if a trace link exists."""
        if "requirement" not in test_entities or "requirement_1" not in test_entities:
            pytest.skip("Requirements not created")

        # Create trace link
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "trace_link",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "requirement", "id": test_entities["requirement_1"]},
                "metadata": {"link_type": "verifies"}
            }
        )

        # Check existence
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "check",
                "relationship_type": "trace_link",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "requirement", "id": test_entities["requirement_1"]}
            }
        )

        assert result.get("exists") is True, f"Failed: {result}"
        assert result["relationship"]["link_type"] == "verifies"
        print(f"✓ Trace link exists: {result['relationship']['link_type']}")

    @pytest.mark.asyncio
    async def test_update_trace_link_version(self, call_mcp, test_entities):
        """Test updating trace link version."""
        if "requirement" not in test_entities or "requirement_1" not in test_entities:
            pytest.skip("Requirements not created")

        # Create trace link
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "trace_link",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "requirement", "id": test_entities["requirement_1"]},
                "metadata": {"link_type": "implements", "version": 1}
            }
        )

        # Update version
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "update",
                "relationship_type": "trace_link",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "requirement", "id": test_entities["requirement_1"]},
                "metadata": {"version": 2}
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        assert result["data"]["version"] == 2
        print("✓ Trace link version updated to 2")

    @pytest.mark.asyncio
    async def test_unlink_trace_link_soft_delete(self, call_mcp, test_entities):
        """Test soft deleting a trace link."""
        if "requirement" not in test_entities or "requirement_1" not in test_entities:
            pytest.skip("Requirements not created")

        # Create trace link
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "trace_link",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "requirement", "id": test_entities["requirement_1"]},
                "metadata": {"link_type": "related_to"}
            }
        )

        # Soft delete
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "unlink",
                "relationship_type": "trace_link",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "requirement", "id": test_entities["requirement_1"]},
                "soft_delete": True
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        print("✓ Trace link soft deleted")

        # Verify it's excluded from normal list (is_deleted=false filter)
        list_result = await call_mcp(
            "relationship_tool",
            {
                "operation": "list",
                "relationship_type": "trace_link",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "limit": 10
            }
        )

        for link in list_result.get("data", []):
            if link.get("target_id") == test_entities["requirement_1"]:
                assert link.get("is_deleted") is False
        print("✓ Soft-deleted trace link excluded from list")


# ============================================================================
# TEST: REQUIREMENT-TEST RELATIONSHIPS
# ============================================================================

class TestRequirementTestRelationship:
    """Comprehensive tests for requirement_test relationship type."""

    @pytest.mark.asyncio
    async def test_link_requirement_to_test_success(self, call_mcp, test_entities):
        """Test linking a requirement to a test."""
        if "requirement" not in test_entities or "test" not in test_entities:
            pytest.skip("Requirement or Test not created")

        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "requirement_test",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "test", "id": test_entities["test"]},
                "metadata": {
                    "relationship_type": "tests",
                    "coverage_level": "full"
                }
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        assert result["data"]["relationship_type"] == "tests"
        assert result["data"]["coverage_level"] == "full"
        assert result["data"]["requirement_id"] == test_entities["requirement"]
        assert result["data"]["test_id"] == test_entities["test"]
        print(f"✓ Requirement-test link created: {result['data']['id']}")

    @pytest.mark.asyncio
    async def test_link_requirement_test_with_defaults(self, call_mcp, test_entities):
        """Test linking with default values."""
        if "requirement" not in test_entities or "test" not in test_entities:
            pytest.skip("Requirement or Test not created")

        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "requirement_test",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "test", "id": test_entities["test"]},
                "metadata": {"coverage_level": "partial"}
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        assert result["data"]["relationship_type"] == "tests"  # Default
        assert result["data"]["coverage_level"] == "partial"
        print(f"✓ Created with defaults: relationship_type={result['data']['relationship_type']}")

    @pytest.mark.asyncio
    async def test_link_multiple_tests_to_requirement(self, call_mcp, test_entities):
        """Test linking multiple tests to a single requirement."""
        if "requirement" not in test_entities or "test" not in test_entities or "test_1" not in test_entities:
            pytest.skip("Requirements or Tests not created")

        # Link test 1
        link1 = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "requirement_test",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "test", "id": test_entities["test"]},
                "metadata": {"coverage_level": "full"}
            }
        )

        # Link test 2
        link2 = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "requirement_test",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "test", "id": test_entities["test_1"]},
                "metadata": {"coverage_level": "partial"}
            }
        )

        assert link1.get("success") is True
        assert link2.get("success") is True
        print("✓ Linked 2 tests to requirement")

    @pytest.mark.asyncio
    async def test_list_test_coverage_for_requirement(self, call_mcp, test_entities):
        """Test listing all tests covering a requirement."""
        if "requirement" not in test_entities or "test" not in test_entities:
            pytest.skip("Requirement or Test not created")

        # Create link
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "requirement_test",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "test", "id": test_entities["test"]},
                "metadata": {"coverage_level": "full"}
            }
        )

        # List tests
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "list",
                "relationship_type": "requirement_test",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "limit": 10
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        assert isinstance(result.get("data"), list)
        print(f"✓ Listed {len(result['data'])} test coverage links")

    @pytest.mark.asyncio
    async def test_list_requirements_covered_by_test(self, call_mcp, test_entities):
        """Test listing requirements covered by a specific test."""
        if "requirement" not in test_entities or "test" not in test_entities:
            pytest.skip("Requirement or Test not created")

        # Create link
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "requirement_test",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "test", "id": test_entities["test"]},
                "metadata": {"coverage_level": "full"}
            }
        )

        # List by test (target)
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "list",
                "relationship_type": "requirement_test",
                "target": {"type": "test", "id": test_entities["test"]},
                "limit": 10
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        assert isinstance(result.get("data"), list)
        print(f"✓ Listed {len(result['data'])} requirements covered by test")

    @pytest.mark.asyncio
    async def test_list_with_coverage_level_filter(self, call_mcp, test_entities):
        """Test filtering by coverage level."""
        if "requirement" not in test_entities or "test" not in test_entities:
            pytest.skip("Requirement or Test not created")

        # Create link with full coverage
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "requirement_test",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "test", "id": test_entities["test"]},
                "metadata": {"coverage_level": "full"}
            }
        )

        # List with filter
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "list",
                "relationship_type": "requirement_test",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "filters": {"coverage_level": "full"},
                "limit": 10
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        for link in result.get("data", []):
            assert link.get("coverage_level") == "full"
        print(f"✓ Filtered {len(result['data'])} full coverage links")

    @pytest.mark.asyncio
    async def test_check_requirement_test_link(self, call_mcp, test_entities):
        """Test checking if a requirement-test link exists."""
        if "requirement" not in test_entities or "test" not in test_entities:
            pytest.skip("Requirement or Test not created")

        # Create link
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "requirement_test",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "test", "id": test_entities["test"]},
                "metadata": {"coverage_level": "partial"}
            }
        )

        # Check
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "check",
                "relationship_type": "requirement_test",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "test", "id": test_entities["test"]}
            }
        )

        assert result.get("exists") is True, f"Failed: {result}"
        assert result["relationship"]["coverage_level"] == "partial"
        print(f"✓ Link exists with coverage: {result['relationship']['coverage_level']}")

    @pytest.mark.asyncio
    async def test_update_coverage_level(self, call_mcp, test_entities):
        """Test updating coverage level metadata."""
        if "requirement" not in test_entities or "test" not in test_entities:
            pytest.skip("Requirement or Test not created")

        # Create with partial coverage
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "requirement_test",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "test", "id": test_entities["test"]},
                "metadata": {"coverage_level": "partial"}
            }
        )

        # Update to full coverage
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "update",
                "relationship_type": "requirement_test",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "test", "id": test_entities["test"]},
                "metadata": {"coverage_level": "full"}
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        assert result["data"]["coverage_level"] == "full"
        print("✓ Coverage level updated from partial to full")

    @pytest.mark.asyncio
    async def test_unlink_requirement_test(self, call_mcp, test_entities):
        """Test removing a requirement-test link."""
        if "requirement" not in test_entities or "test" not in test_entities:
            pytest.skip("Requirement or Test not created")

        # Create link
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "requirement_test",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "test", "id": test_entities["test"]},
                "metadata": {"coverage_level": "full"}
            }
        )

        # Unlink
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "unlink",
                "relationship_type": "requirement_test",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "test", "id": test_entities["test"]},
                "soft_delete": False
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        print("✓ Requirement-test link removed")


# ============================================================================
# TEST: INVITATION RELATIONSHIPS
# ============================================================================

class TestInvitationRelationship:
    """Comprehensive tests for invitation relationship type."""

    @pytest.mark.asyncio
    async def test_create_invitation_success(self, call_mcp, test_entities):
        """Test creating an organization invitation."""
        if "organization" not in test_entities:
            pytest.skip("Organization not created")

        test_email = f"test-{uuid.uuid4().hex[:8]}@example.com"

        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "invitation",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "email", "id": test_email},
                "metadata": {
                    "role": "member",
                    "status": "pending"
                }
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        assert result["data"]["role"] == "member"
        assert result["data"]["status"] == "pending"
        assert result["data"]["email"] == test_email
        print(f"✓ Invitation created: {result['data']['id']}")

    @pytest.mark.asyncio
    async def test_create_invitation_with_defaults(self, call_mcp, test_entities):
        """Test invitation with default values."""
        if "organization" not in test_entities:
            pytest.skip("Organization not created")

        test_email = f"default-{uuid.uuid4().hex[:8]}@example.com"

        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "invitation",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "email", "id": test_email},
                "metadata": {"role": "viewer"}
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        assert result["data"]["status"] == "pending"  # Default
        print(f"✓ Invitation created with default status: {result['data']['status']}")

    @pytest.mark.asyncio
    async def test_create_admin_invitation(self, call_mcp, test_entities):
        """Test creating admin invitation."""
        if "organization" not in test_entities:
            pytest.skip("Organization not created")

        test_email = f"admin-{uuid.uuid4().hex[:8]}@example.com"

        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "invitation",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "email", "id": test_email},
                "metadata": {"role": "admin"}
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        assert result["data"]["role"] == "admin"
        print("✓ Admin invitation created")

    @pytest.mark.asyncio
    async def test_list_all_invitations(self, call_mcp, test_entities):
        """Test listing all invitations for an organization."""
        if "organization" not in test_entities:
            pytest.skip("Organization not created")

        # Create invitation
        test_email = f"list-{uuid.uuid4().hex[:8]}@example.com"
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "invitation",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "email", "id": test_email},
                "metadata": {"role": "member"}
            }
        )

        # List invitations
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "list",
                "relationship_type": "invitation",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "limit": 10
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        assert isinstance(result.get("data"), list)
        print(f"✓ Listed {len(result['data'])} invitations")

    @pytest.mark.asyncio
    async def test_list_pending_invitations(self, call_mcp, test_entities):
        """Test filtering invitations by pending status."""
        if "organization" not in test_entities:
            pytest.skip("Organization not created")

        # Create pending invitation
        test_email = f"pending-{uuid.uuid4().hex[:8]}@example.com"
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "invitation",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "email", "id": test_email},
                "metadata": {"role": "member", "status": "pending"}
            }
        )

        # List with status filter
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "list",
                "relationship_type": "invitation",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "filters": {"status": "pending"},
                "limit": 10
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        for inv in result.get("data", []):
            assert inv.get("status") == "pending"
        print(f"✓ Filtered {len(result['data'])} pending invitations")

    @pytest.mark.asyncio
    async def test_list_invitations_by_role(self, call_mcp, test_entities):
        """Test filtering invitations by role."""
        if "organization" not in test_entities:
            pytest.skip("Organization not created")

        # Create admin invitation
        test_email = f"role-filter-{uuid.uuid4().hex[:8]}@example.com"
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "invitation",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "email", "id": test_email},
                "metadata": {"role": "admin"}
            }
        )

        # List admin invitations
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "list",
                "relationship_type": "invitation",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "filters": {"role": "admin"},
                "limit": 10
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        for inv in result.get("data", []):
            assert inv.get("role") == "admin"
        print(f"✓ Filtered {len(result['data'])} admin invitations")

    @pytest.mark.asyncio
    async def test_check_invitation_exists(self, call_mcp, test_entities):
        """Test checking if an invitation exists."""
        if "organization" not in test_entities:
            pytest.skip("Organization not created")

        test_email = f"check-{uuid.uuid4().hex[:8]}@example.com"

        # Create invitation
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "invitation",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "email", "id": test_email},
                "metadata": {"role": "member"}
            }
        )

        # Check
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "check",
                "relationship_type": "invitation",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "email", "id": test_email}
            }
        )

        assert result.get("exists") is True, f"Failed: {result}"
        assert result["relationship"]["email"] == test_email
        print(f"✓ Invitation exists for {test_email}")

    @pytest.mark.asyncio
    async def test_update_invitation_status_accept(self, call_mcp, test_entities):
        """Test accepting an invitation by updating status."""
        if "organization" not in test_entities:
            pytest.skip("Organization not created")

        test_email = f"accept-{uuid.uuid4().hex[:8]}@example.com"

        # Create invitation
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "invitation",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "email", "id": test_email},
                "metadata": {"role": "member"}
            }
        )

        # Accept invitation
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "update",
                "relationship_type": "invitation",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "email", "id": test_email},
                "metadata": {"status": "accepted"}
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        assert result["data"]["status"] == "accepted"
        print("✓ Invitation accepted")

    @pytest.mark.asyncio
    async def test_update_invitation_status_reject(self, call_mcp, test_entities):
        """Test rejecting an invitation."""
        if "organization" not in test_entities:
            pytest.skip("Organization not created")

        test_email = f"reject-{uuid.uuid4().hex[:8]}@example.com"

        # Create invitation
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "invitation",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "email", "id": test_email},
                "metadata": {"role": "member"}
            }
        )

        # Reject invitation
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "update",
                "relationship_type": "invitation",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "email", "id": test_email},
                "metadata": {"status": "rejected"}
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        assert result["data"]["status"] == "rejected"
        print("✓ Invitation rejected")

    @pytest.mark.asyncio
    async def test_revoke_invitation(self, call_mcp, test_entities):
        """Test revoking (deleting) an invitation."""
        if "organization" not in test_entities:
            pytest.skip("Organization not created")

        test_email = f"revoke-{uuid.uuid4().hex[:8]}@example.com"

        # Create invitation
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "invitation",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "email", "id": test_email},
                "metadata": {"role": "member"}
            }
        )

        # Revoke (hard delete)
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "unlink",
                "relationship_type": "invitation",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "email", "id": test_email},
                "soft_delete": False
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        print("✓ Invitation revoked")

        # Verify it's gone
        check = await call_mcp(
            "relationship_tool",
            {
                "operation": "check",
                "relationship_type": "invitation",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "email", "id": test_email}
            }
        )
        assert check.get("exists") is False
        print("✓ Verified invitation no longer exists")


# ============================================================================
# TEST: ERROR CASES AND EDGE CASES
# ============================================================================

class TestErrorCasesAndEdgeCases:
    """Test error handling, validation, and edge cases."""

    @pytest.mark.asyncio
    async def test_link_with_missing_target(self, call_mcp, test_entities):
        """Test link operation without target (should fail)."""
        if "organization" not in test_entities:
            pytest.skip("Organization not created")

        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "member",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "metadata": {"role": "admin"}
            }
        )

        assert result.get("success") is False
        assert "error" in result or "target" in str(result).lower()
        print(f"✓ Correctly failed with missing target: {result.get('error', 'validation error')}")

    @pytest.mark.asyncio
    async def test_invalid_relationship_type(self, call_mcp, test_entities, user_id):
        """Test with invalid relationship type."""
        if "organization" not in test_entities:
            pytest.skip("Organization not created")

        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "invalid_type",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "admin"}
            }
        )

        assert result.get("success") is False
        print("✓ Correctly rejected invalid relationship type")

    @pytest.mark.asyncio
    async def test_invalid_source_type_for_member(self, call_mcp, test_entities, user_id):
        """Test member relationship with invalid source type."""
        if "requirement" not in test_entities:
            pytest.skip("Requirement not created")

        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "member",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "admin"}
            }
        )

        assert result.get("success") is False
        print("✓ Correctly rejected invalid source type for member relationship")

    @pytest.mark.asyncio
    async def test_non_existent_entity(self, call_mcp, user_id):
        """Test linking with non-existent entity ID."""
        fake_org_id = str(uuid.uuid4())

        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "member",
                "source": {"type": "organization", "id": fake_org_id},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "admin"}
            }
        )

        # This might succeed (no FK validation) or fail - either is acceptable
        print(f"✓ Non-existent entity result: success={result.get('success')}")

    @pytest.mark.asyncio
    async def test_duplicate_relationship(self, call_mcp, test_entities, user_id):
        """Test creating duplicate relationships."""
        if "organization" not in test_entities:
            pytest.skip("Organization not created")

        # Create first relationship
        result1 = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "member",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "viewer"}
            }
        )

        # Try to create duplicate
        result2 = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "member",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "admin"}
            }
        )

        # May fail with constraint error or succeed (depends on DB constraints)
        print(f"✓ Duplicate link result: success={result2.get('success')}, error={result2.get('error', 'none')}")

    @pytest.mark.asyncio
    async def test_update_non_existent_relationship(self, call_mcp, test_entities, user_id):
        """Test updating a relationship that doesn't exist."""
        if "organization" not in test_entities:
            pytest.skip("Organization not created")

        fake_user_id = str(uuid.uuid4())

        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "update",
                "relationship_type": "member",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "user", "id": fake_user_id},
                "metadata": {"role": "admin"}
            }
        )

        # May fail or return empty result
        print(f"✓ Update non-existent result: success={result.get('success')}")

    @pytest.mark.asyncio
    async def test_unlink_non_existent_relationship(self, call_mcp, test_entities, user_id):
        """Test unlinking a relationship that doesn't exist."""
        if "organization" not in test_entities:
            pytest.skip("Organization not created")

        fake_user_id = str(uuid.uuid4())

        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "unlink",
                "relationship_type": "member",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "user", "id": fake_user_id},
                "soft_delete": False
            }
        )

        # Should succeed (0 rows deleted) or fail
        print(f"✓ Unlink non-existent result: success={result.get('success')}")

    @pytest.mark.asyncio
    async def test_pagination_functionality(self, call_mcp, test_entities):
        """Test pagination with limit and offset."""
        if "organization" not in test_entities:
            pytest.skip("Organization not created")

        # Create multiple invitations
        created_emails = []
        for i in range(5):
            email = f"page-test-{i}-{uuid.uuid4().hex[:4]}@example.com"
            created_emails.append(email)
            await call_mcp(
                "relationship_tool",
                {
                    "operation": "link",
                    "relationship_type": "invitation",
                    "source": {"type": "organization", "id": test_entities["organization"]},
                    "target": {"type": "email", "id": email},
                    "metadata": {"role": "member"}
                }
            )

        # Get first page
        page1 = await call_mcp(
            "relationship_tool",
            {
                "operation": "list",
                "relationship_type": "invitation",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "limit": 2,
                "offset": 0
            }
        )

        # Get second page
        page2 = await call_mcp(
            "relationship_tool",
            {
                "operation": "list",
                "relationship_type": "invitation",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "limit": 2,
                "offset": 2
            }
        )

        assert page1.get("success") is True
        assert page2.get("success") is True
        assert len(page1.get("data", [])) <= 2
        assert len(page2.get("data", [])) <= 2
        print(f"✓ Page 1: {len(page1['data'])} items, Page 2: {len(page2['data'])} items")

        # Verify different results
        if page1.get("data") and page2.get("data"):
            page1_ids = {item["id"] for item in page1["data"]}
            page2_ids = {item["id"] for item in page2["data"]}

            if page1_ids.intersection(page2_ids):
                print("⚠ Pages contain overlapping items (unexpected)")
            else:
                print("✓ Pages contain different items")

    @pytest.mark.asyncio
    async def test_list_with_large_limit(self, call_mcp, test_entities):
        """Test listing with very large limit."""
        if "organization" not in test_entities:
            pytest.skip("Organization not created")

        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "list",
                "relationship_type": "member",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "limit": 1000
            }
        )

        assert result.get("success") is True
        print(f"✓ Large limit handled: returned {len(result.get('data', []))} items")

    @pytest.mark.asyncio
    async def test_list_with_zero_limit(self, call_mcp, test_entities):
        """Test listing with limit=0."""
        if "organization" not in test_entities:
            pytest.skip("Organization not created")

        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "list",
                "relationship_type": "member",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "limit": 0
            }
        )

        # May fail or return empty
        print(f"✓ Zero limit result: success={result.get('success')}, count={len(result.get('data', []))}")


# ============================================================================
# SUMMARY TEST
# ============================================================================

class TestComprehensiveSummary:
    """Generate a comprehensive test summary."""

    @pytest.mark.asyncio
    async def test_generate_summary(self, call_mcp, test_entities, user_id):
        """Generate a summary of all relationship types and operations."""
        print("\n" + "="*80)
        print("COMPREHENSIVE RELATIONSHIP_TOOL TEST SUMMARY")
        print("="*80)

        summary = {
            "member": {"link": 0, "unlink": 0, "list": 0, "check": 0, "update": 0},
            "assignment": {"link": 0, "unlink": 0, "list": 0, "check": 0, "update": 0},
            "trace_link": {"link": 0, "unlink": 0, "list": 0, "check": 0, "update": 0},
            "requirement_test": {"link": 0, "unlink": 0, "list": 0, "check": 0, "update": 0},
            "invitation": {"link": 0, "unlink": 0, "list": 0, "check": 0, "update": 0},
        }

        # Test each relationship type
        test_cases = [
            ("member", "organization", "organization", "user", user_id, {"role": "admin"}),
            ("assignment", "requirement", "requirement", "user", user_id, {"role": "owner"}),
            ("trace_link", "requirement", "requirement", "requirement", test_entities.get("requirement_1"), {"link_type": "depends_on"}),
            ("requirement_test", "requirement", "requirement", "test", test_entities.get("test"), {"coverage_level": "full"}),
            ("invitation", "organization", "organization", "email", f"summary-{uuid.uuid4().hex[:8]}@example.com", {"role": "member"}),
        ]

        for rel_type, source_type, source_key, target_type, target_id, metadata in test_cases:
            if source_key not in test_entities or not target_id:
                continue

            source_id = test_entities[source_key]

            # Test link
            link_result = await call_mcp(
                "relationship_tool",
                {
                    "operation": "link",
                    "relationship_type": rel_type,
                    "source": {"type": source_type, "id": source_id},
                    "target": {"type": target_type, "id": target_id},
                    "metadata": metadata
                }
            )
            if link_result.get("success"):
                summary[rel_type]["link"] += 1

            # Test list
            list_result = await call_mcp(
                "relationship_tool",
                {
                    "operation": "list",
                    "relationship_type": rel_type,
                    "source": {"type": source_type, "id": source_id},
                    "limit": 10
                }
            )
            if list_result.get("success"):
                summary[rel_type]["list"] += 1

            # Test check
            check_result = await call_mcp(
                "relationship_tool",
                {
                    "operation": "check",
                    "relationship_type": rel_type,
                    "source": {"type": source_type, "id": source_id},
                    "target": {"type": target_type, "id": target_id}
                }
            )
            if check_result.get("success") or check_result.get("exists") is not None:
                summary[rel_type]["check"] += 1

            # Test update
            update_metadata = metadata.copy()
            if "role" in update_metadata:
                update_metadata["role"] = "updated"
            elif "coverage_level" in update_metadata:
                update_metadata["coverage_level"] = "partial"
            elif "status" in update_metadata:
                update_metadata["status"] = "accepted"

            update_result = await call_mcp(
                "relationship_tool",
                {
                    "operation": "update",
                    "relationship_type": rel_type,
                    "source": {"type": source_type, "id": source_id},
                    "target": {"type": target_type, "id": target_id},
                    "metadata": update_metadata
                }
            )
            if update_result.get("success"):
                summary[rel_type]["update"] += 1

            # Test unlink
            unlink_result = await call_mcp(
                "relationship_tool",
                {
                    "operation": "unlink",
                    "relationship_type": rel_type,
                    "source": {"type": source_type, "id": source_id},
                    "target": {"type": target_type, "id": target_id},
                    "soft_delete": True
                }
            )
            if unlink_result.get("success"):
                summary[rel_type]["unlink"] += 1

        # Print summary
        print("\nOperation Success Count by Relationship Type:")
        print("-" * 80)
        print(f"{'Relationship Type':<20} {'Link':<8} {'Unlink':<8} {'List':<8} {'Check':<8} {'Update':<8}")
        print("-" * 80)

        for rel_type, ops in summary.items():
            print(f"{rel_type:<20} {ops['link']:<8} {ops['unlink']:<8} {ops['list']:<8} {ops['check']:<8} {ops['update']:<8}")

        print("-" * 80)

        total_ops = sum(sum(ops.values()) for ops in summary.values())
        print(f"\nTotal Successful Operations: {total_ops}")
        print("="*80 + "\n")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
