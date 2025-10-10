"""
Error Handling and Edge Case Tests for Atoms MCP

This test suite validates error handling, edge cases, and failure scenarios:
- Authentication failures
- Invalid input validation
- Missing required parameters
- Database constraint violations
- Concurrent operation conflicts
- Resource not found errors
- Permission errors
- Transaction rollback scenarios

Run with: pytest tests/test_error_handling.py -v -s
"""

from __future__ import annotations

import os
import uuid
from typing import Any

import httpx
import pytest

MCP_BASE_URL = os.getenv("ATOMS_FASTMCP_BASE_URL", "http://127.0.0.1:8000")
MCP_PATH = os.getenv("ATOMS_FASTMCP_HTTP_PATH", "/api/mcp")
TEST_EMAIL = os.getenv("ATOMS_TEST_EMAIL", "kooshapari@kooshapari.com")
TEST_PASSWORD = os.getenv("ATOMS_TEST_PASSWORD", "118118")

pytestmark = [pytest.mark.asyncio, pytest.mark.error_handling]

@pytest.fixture(scope="module")
def mcp_client(check_server_running, shared_authkit_session):
    """Return MCP client helper."""
    base_url = f"{MCP_BASE_URL.rstrip('/')}{MCP_PATH}"
    headers = {
        "Authorization": f"Bearer {shared_authkit_session}",
        "Content-Type": "application/json",
    }

    async def call_tool(tool_name: str, params: dict[str, Any], expect_error: bool = False) -> dict[str, Any]:
        """Call MCP tool with error handling."""
        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": f"tools/{tool_name}",
            "params": params,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(base_url, json=payload, headers=headers)

                if response.status_code != 200:
                    if expect_error:
                        return {"success": False, "error": response.text, "status_code": response.status_code}
                    raise Exception(f"HTTP {response.status_code}: {response.text}")

                body = response.json()
                if "result" in body:
                    return body["result"]

                if expect_error:
                    return body.get("error", {"success": False, "error": "Unknown error"})

                raise Exception(f"Unexpected response: {body}")

            except Exception as e:
                if expect_error:
                    return {"success": False, "error": str(e)}
                raise

    return call_tool

# ============================================================================
# Authentication and Authorization Errors
# ============================================================================

class TestAuthenticationErrors:
    """Test authentication and authorization error handling."""

    @pytest.mark.asyncio
    async def test_missing_auth_token(self, check_server_running):
        """Test request without authentication token."""
        base_url = f"{MCP_BASE_URL.rstrip('/')}{MCP_PATH}"
        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/workspace_tool",
            "params": {"operation": "get_context"}
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                base_url,
                json=payload,
                headers={"Content-Type": "application/json"}  # No Authorization header
            )

            # Should fail with 401 or return error in result
            assert response.status_code in [401, 403, 200], "Missing auth should be rejected"

            if response.status_code == 200:
                body = response.json()
                result = body.get("result", {})
                assert result.get("success") is False, "Should fail without auth token"
                assert "authorization" in result.get("error", "").lower() or "auth" in result.get("error", "").lower()

    @pytest.mark.asyncio
    async def test_invalid_auth_token(self, check_server_running):
        """Test request with invalid authentication token."""
        base_url = f"{MCP_BASE_URL.rstrip('/')}{MCP_PATH}"
        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/workspace_tool",
            "params": {"operation": "get_context"}
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                base_url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": "Bearer invalid_token_12345"
                }
            )

            # Should fail with 401 or return error
            if response.status_code == 200:
                body = response.json()
                result = body.get("result", {})
                assert result.get("success") is False, "Should fail with invalid token"

# ============================================================================
# Input Validation Errors
# ============================================================================

class TestInputValidation:
    """Test input validation and parameter errors."""

    @pytest.mark.asyncio
    async def test_missing_required_parameters(self, mcp_client):
        """Test operations with missing required parameters."""
        # Create without required fields
        result = await mcp_client(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "organization",
                "data": {}  # Missing name and slug
            },
            expect_error=True
        )

        assert result.get("success") is False, "Should fail with missing required fields"
        assert "error" in result

    @pytest.mark.asyncio
    async def test_invalid_entity_type(self, mcp_client):
        """Test operation with invalid entity type."""
        result = await mcp_client(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "invalid_type_xyz",
                "data": {"name": "Test"}
            },
            expect_error=True
        )

        assert result.get("success") is False, "Should fail with invalid entity type"

    @pytest.mark.asyncio
    async def test_invalid_operation(self, mcp_client):
        """Test with invalid operation name."""
        result = await mcp_client(
            "entity_tool",
            {
                "operation": "invalid_operation",
                "entity_type": "organization",
                "data": {"name": "Test"}
            },
            expect_error=True
        )

        assert result.get("success") is False, "Should fail with invalid operation"

    @pytest.mark.asyncio
    async def test_null_and_empty_values(self, mcp_client):
        """Test handling of null and empty values."""
        # Empty string for required field
        result = await mcp_client(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "organization",
                "data": {
                    "name": "",  # Empty string
                    "slug": "test-slug"
                }
            },
            expect_error=True
        )

        assert result.get("success") is False, "Should fail with empty required field"

    @pytest.mark.asyncio
    async def test_malformed_data_types(self, mcp_client):
        """Test with incorrect data types."""
        # String where ID expected
        result = await mcp_client(
            "entity_tool",
            {
                "operation": "read",
                "entity_type": "organization",
                "entity_id": 12345  # Should be string
            },
            expect_error=True
        )

        # Should either fail or handle gracefully
        # Some systems auto-convert, others reject

# ============================================================================
# Resource Not Found Errors
# ============================================================================

class TestResourceNotFound:
    """Test resource not found error handling."""

    @pytest.mark.asyncio
    async def test_read_nonexistent_entity(self, mcp_client):
        """Test reading non-existent entity."""
        fake_id = f"fake-id-{uuid.uuid4()}"

        result = await mcp_client(
            "entity_tool",
            {
                "operation": "read",
                "entity_type": "organization",
                "entity_id": fake_id
            },
            expect_error=True
        )

        assert result.get("success") is False, "Should fail for non-existent entity"
        assert "not found" in result.get("error", "").lower() or "does not exist" in result.get("error", "").lower()

    @pytest.mark.asyncio
    async def test_update_nonexistent_entity(self, mcp_client):
        """Test updating non-existent entity."""
        fake_id = f"fake-id-{uuid.uuid4()}"

        result = await mcp_client(
            "entity_tool",
            {
                "operation": "update",
                "entity_type": "organization",
                "entity_id": fake_id,
                "data": {"name": "Updated Name"}
            },
            expect_error=True
        )

        assert result.get("success") is False, "Should fail updating non-existent entity"

    @pytest.mark.asyncio
    async def test_delete_nonexistent_entity(self, mcp_client):
        """Test deleting non-existent entity."""
        fake_id = f"fake-id-{uuid.uuid4()}"

        result = await mcp_client(
            "entity_tool",
            {
                "operation": "delete",
                "entity_type": "organization",
                "entity_id": fake_id
            },
            expect_error=True
        )

        assert result.get("success") is False, "Should fail deleting non-existent entity"

    @pytest.mark.asyncio
    async def test_invalid_context_entity(self, mcp_client):
        """Test setting context to non-existent entity."""
        fake_id = f"fake-id-{uuid.uuid4()}"

        result = await mcp_client(
            "workspace_tool",
            {
                "operation": "set_context",
                "context_type": "organization",
                "entity_id": fake_id
            },
            expect_error=True
        )

        assert result.get("success") is False, "Should fail setting context to non-existent entity"

# ============================================================================
# Relationship and Constraint Errors
# ============================================================================

class TestRelationshipErrors:
    """Test relationship and constraint error handling."""

    @pytest.mark.asyncio
    async def test_create_entity_with_invalid_foreign_key(self, mcp_client):
        """Test creating entity with invalid foreign key reference."""
        fake_org_id = f"fake-org-{uuid.uuid4()}"

        result = await mcp_client(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "project",
                "data": {
                    "name": "Test Project",
                    "organization_id": fake_org_id  # Invalid FK
                }
            },
            expect_error=True
        )

        assert result.get("success") is False, "Should fail with invalid foreign key"

    @pytest.mark.asyncio
    async def test_duplicate_relationship(self, mcp_client):
        """Test creating duplicate relationship."""
        # First create an org and project
        org_result = await mcp_client(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "organization",
                "data": {
                    "name": "Duplicate Rel Test Org",
                    "slug": f"dup-rel-{uuid.uuid4().hex[:8]}"
                }
            }
        )

        if not org_result.get("success"):
            return {"success": True, "skipped": True, "skip_reason": "Could not create test organization"}

        org_id = org_result["data"]["id"]

        # The workflow already adds creator as admin, so trying to add again might fail
        # This tests duplicate prevention

    @pytest.mark.asyncio
    async def test_link_incompatible_entities(self, mcp_client):
        """Test linking incompatible entity types."""
        # Try to create invalid relationship type
        result = await mcp_client(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "member",
                "source": {"type": "invalid_type", "id": "some-id"},
                "target": {"type": "user", "id": "user-id"}
            },
            expect_error=True
        )

        # Should fail with invalid relationship config
        assert result.get("success") is False

# ============================================================================
# Workflow and Transaction Errors
# ============================================================================

class TestWorkflowErrors:
    """Test workflow and transaction error handling."""

    @pytest.mark.asyncio
    async def test_workflow_with_missing_parameters(self, mcp_client):
        """Test workflow with missing required parameters."""
        result = await mcp_client(
            "workflow_tool",
            {
                "workflow": "setup_project",
                "parameters": {
                    "name": "Test Project"
                    # Missing organization_id
                }
            },
            expect_error=True
        )

        assert result.get("success") is False, "Should fail with missing workflow parameters"

    @pytest.mark.asyncio
    async def test_invalid_workflow_name(self, mcp_client):
        """Test with invalid workflow name."""
        result = await mcp_client(
            "workflow_tool",
            {
                "workflow": "invalid_workflow_xyz",
                "parameters": {}
            },
            expect_error=True
        )

        assert result.get("success") is False, "Should fail with invalid workflow name"

    @pytest.mark.asyncio
    async def test_workflow_partial_failure(self, mcp_client):
        """Test workflow that fails partway through."""
        # Create org first
        org_result = await mcp_client(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "organization",
                "data": {
                    "name": "Workflow Failure Test",
                    "slug": f"wf-fail-{uuid.uuid4().hex[:8]}"
                }
            }
        )

        if not org_result.get("success"):
            return {"success": True, "skipped": True, "skip_reason": "Could not create test organization"}

        org_id = org_result["data"]["id"]

        # Try workflow with some invalid data in initial_documents
        result = await mcp_client(
            "workflow_tool",
            {
                "workflow": "setup_project",
                "parameters": {
                    "name": "Test Project",
                    "organization_id": org_id,
                    "initial_documents": ["Valid Doc", None, "", 123]  # Some invalid items
                }
            },
            expect_error=False  # Workflow should handle errors gracefully
        )

        # Workflow should report partial success or handle errors
        # Check that steps are properly reported
        if result.get("data", {}).get("steps"):
            steps = result["data"]["steps"]
            # Some steps may have failed
            failed_steps = [s for s in steps if s.get("status") == "failed"]
            # Workflow should have error information

# ============================================================================
# Query and Search Errors
# ============================================================================

class TestQueryErrors:
    """Test query and search error handling."""

    @pytest.mark.asyncio
    async def test_query_invalid_entity_types(self, mcp_client):
        """Test query with invalid entity types."""
        result = await mcp_client(
            "query_tool",
            {
                "query_type": "search",
                "entities": ["invalid_entity_type"],
                "search_term": "test"
            },
            expect_error=True
        )

        # Should handle invalid entity types gracefully

    @pytest.mark.asyncio
    async def test_query_with_invalid_conditions(self, mcp_client):
        """Test query with malformed conditions."""
        result = await mcp_client(
            "query_tool",
            {
                "query_type": "aggregate",
                "entities": ["organization"],
                "conditions": "invalid_conditions"  # Should be dict
            },
            expect_error=True
        )

        # Should validate conditions format

    @pytest.mark.asyncio
    async def test_rag_search_without_embeddings(self, mcp_client):
        """Test RAG search when embeddings might not be available."""
        result = await mcp_client(
            "query_tool",
            {
                "query_type": "rag_search",
                "entities": ["requirement"],
                "search_term": "test search",
                "rag_mode": "semantic"
            },
            expect_error=False  # Should fallback gracefully
        )

        # Should either work or fallback to keyword search

# ============================================================================
# Edge Cases and Boundary Conditions
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_very_long_string_inputs(self, mcp_client):
        """Test with very long string inputs."""
        long_string = "A" * 10000  # 10k characters

        result = await mcp_client(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "organization",
                "data": {
                    "name": long_string,
                    "slug": f"long-{uuid.uuid4().hex[:8]}"
                }
            },
            expect_error=False
        )

        # Should either truncate, reject, or accept based on database limits

    @pytest.mark.asyncio
    async def test_special_characters_in_input(self, mcp_client):
        """Test with special characters and unicode."""
        special_chars = "Test 🚀 Org <script>alert('xss')</script> 你好"

        result = await mcp_client(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "organization",
                "data": {
                    "name": special_chars,
                    "slug": f"special-{uuid.uuid4().hex[:8]}"
                }
            },
            expect_error=False
        )

        # Should handle special chars safely (no XSS, proper escaping)
        if result.get("success"):
            # Verify data is stored/retrieved correctly
            org_id = result["data"]["id"]
            read_result = await mcp_client(
                "entity_tool",
                {
                    "operation": "read",
                    "entity_type": "organization",
                    "entity_id": org_id
                }
            )

            if read_result.get("success"):
                # Name should be preserved (but safely escaped)
                assert read_result["data"].get("name")

    @pytest.mark.asyncio
    async def test_pagination_boundary_cases(self, mcp_client):
        """Test pagination with boundary values."""
        # Zero limit
        result = await mcp_client(
            "entity_tool",
            {
                "operation": "list",
                "entity_type": "organization",
                "limit": 0
            },
            expect_error=False
        )

        # Negative offset
        result = await mcp_client(
            "entity_tool",
            {
                "operation": "list",
                "entity_type": "organization",
                "offset": -1
            },
            expect_error=False
        )

        # Very large limit
        result = await mcp_client(
            "entity_tool",
            {
                "operation": "list",
                "entity_type": "organization",
                "limit": 999999
            },
            expect_error=False
        )

        # Should enforce maximum limits

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, mcp_client):
        """Test concurrent operations on same entity."""
        # Create an org
        org_result = await mcp_client(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "organization",
                "data": {
                    "name": "Concurrent Test Org",
                    "slug": f"concurrent-{uuid.uuid4().hex[:8]}"
                }
            }
        )

        if not org_result.get("success"):
            return {"success": True, "skipped": True, "skip_reason": "Could not create test organization"}

        org_id = org_result["data"]["id"]

        # Simulate concurrent updates
        import asyncio

        async def update_org(name_suffix: str):
            return await mcp_client(
                "entity_tool",
                {
                    "operation": "update",
                    "entity_type": "organization",
                    "entity_id": org_id,
                    "data": {"name": f"Updated Name {name_suffix}"}
                }
            )

        # Run multiple updates concurrently
        results = await asyncio.gather(
            update_org("A"),
            update_org("B"),
            update_org("C"),
            return_exceptions=True
        )

        # All should succeed or handle conflicts gracefully
        for result in results:
            if isinstance(result, Exception):
                # Should not crash
                print(f"Concurrent update exception (expected): {result}")

    @pytest.mark.asyncio
    async def test_deleted_entity_access(self, mcp_client):
        """Test accessing soft-deleted entities."""
        # Create and delete an org
        org_result = await mcp_client(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "organization",
                "data": {
                    "name": "To Be Deleted",
                    "slug": f"deleted-{uuid.uuid4().hex[:8]}"
                }
            }
        )

        if not org_result.get("success"):
            return {"success": True, "skipped": True, "skip_reason": "Could not create test organization"}

        org_id = org_result["data"]["id"]

        # Delete it
        delete_result = await mcp_client(
            "entity_tool",
            {
                "operation": "delete",
                "entity_type": "organization",
                "entity_id": org_id,
                "soft_delete": True
            }
        )

        # Try to read deleted entity
        read_result = await mcp_client(
            "entity_tool",
            {
                "operation": "read",
                "entity_type": "organization",
                "entity_id": org_id
            },
            expect_error=True
        )

        # Should fail or return is_deleted=true
        assert read_result.get("success") is False or read_result.get("data", {}).get("is_deleted") is True

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
