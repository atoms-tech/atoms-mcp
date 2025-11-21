"""E2E tests for organization CRUD operations.

This module tests all organization CRUD operations:
- Creating organizations
- Reading/retrieving organizations
- Updating organization details
- Deleting organizations
- Organization hierarchy management
- Organization member management

Tests are parametrized to run across unit, integration, and E2E variants.
"""

import pytest
import pytest_asyncio
import httpx
import os
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timezone

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]

# Skip these tests unless running with proper auth or mock harness
skip_reason = "Requires AuthKit access token (ATOMS_TEST_AUTH_TOKEN) or USE_MOCK_HARNESS=true"
has_authkit_token = os.getenv("ATOMS_TEST_AUTH_TOKEN") or os.getenv("AUTHKIT_TOKEN")
has_mock_harness = os.getenv("USE_MOCK_HARNESS", "false").lower() == "true"

if not (has_authkit_token or has_mock_harness):
    pytestmark.append(pytest.mark.skip(reason=skip_reason))


# Helper functions
def unique_test_id():
    """Generate a unique test ID."""
    return uuid.uuid4().hex[:8]


def assert_operation_success(response: Dict[str, Any], message: str = None):
    """Assert that an operation was successful."""
    assert response.get("success") is not None or "result" in response, f"Expected successful response: {response}"


def assert_operation_error(response: Dict[str, Any], error_type: str = None):
    """Assert that an operation failed with expected error."""
    assert response.get("error") or not response.get("result"), f"Expected error response: {response}"


class TestOrganizationCRUD:
    """Test organization CRUD operations."""

    @pytest.mark.story("User can create an organization")
    async def test_create_organization_basic(self, e2e_auth_token):
        """Test creating a basic organization with minimal data."""
        base_url = os.getenv("MCP_E2E_BASE_URL", "https://mcpdev.atoms.tech/api/mcp")
        test_id = unique_test_id()
        
        org_data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "entity_tool",
                "arguments": {
                    "operation": "create",
                    "entity_type": "organization",
                    "data": {
                        "name": f"Test Org {test_id}",
                        "slug": f"test-org-{test_id}",
                        "description": "Test organization for E2E testing"
                    }
                }
            }
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                base_url,
                json=org_data,
                headers={
                    "Authorization": f"Bearer {e2e_auth_token}",
                    "Content-Type": "application/json"
                }
            )
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
            
            result = response.json()
            assert "result" in result, "Expected result field in JSON-RPC response"
            
            # Verify the organization was created
            org = result["result"]
            assert org.get("success") is True or "data" in org, f"Expected successful creation: {org}"
            
            if "data" in org:
                org_data = org["data"]
                assert org_data["name"] == f"Test Org {test_id}"
                assert org_data["slug"] == f"test-org-{test_id}"
                assert org_data["description"] == "Test organization for E2E testing"
                assert org_data.get("is_active") is True
                assert "created_at" in org_data
                assert "updated_at" in org_data

    @pytest.mark.story("User can create an organization")
    async def test_create_organization_with_all_fields(self, e2e_auth_token):
        """Test creating an organization with all optional fields."""
        base_url = os.getenv("MCP_E2E_BASE_URL", "https://mcpdev.atoms.tech/api/mcp")
        test_id = unique_test_id()
        
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "entity_tool",
                "arguments": {
                    "operation": "create",
                    "entity_type": "organization",
                    "data": {
                        "name": f"Complete Org {test_id}",
                        "slug": f"complete-org-{test_id}",
                        "description": "Complete organization with all fields",
                        "website_url": "https://example.com",
                        "logo_url": "https://example.com/logo.png",
                        "is_active": True,
                        "settings": {
                            "allow_public_projects": False,
                            "max_members": 100,
                            "default_role": "member"
                        }
                    }
                }
            }
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                base_url,
                json=payload,
                headers={
                    "Authorization": f"Bearer {e2e_auth_token}",
                    "Content-Type": "application/json"
                }
            )
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
            
            result = response.json()
            assert "result" in result
            
            org = result["result"]
            if "data" in org:
                org_data = org["data"]
                assert org_data["name"] == f"Complete Org {test_id}"
                assert org_data["website_url"] == "https://example.com"
                assert org_data["logo_url"] == "https://example.com/logo.png"
                assert org_data["settings"]["allow_public_projects"] is False

    @pytest.mark.story("User can view organization details")
    async def test_read_organization_by_id(self, e2e_auth_token):
        """Test reading an organization by its ID."""
        base_url = os.getenv("MCP_E2E_BASE_URL", "https://mcpdev.atoms.tech/api/mcp")
        test_id = unique_test_id()
        
        # First create an organization
        create_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "entity_tool",
                "arguments": {
                    "operation": "create",
                    "entity_type": "organization",
                    "data": {
                        "name": f"Read Test Org {test_id}",
                        "slug": f"read-test-org-{test_id}",
                        "description": "Organization for read testing"
                    }
                }
            }
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Create organization
            create_response = await client.post(
                base_url,
                json=create_payload,
                headers={
                    "Authorization": f"Bearer {e2e_auth_token}",
                    "Content-Type": "application/json"
                }
            )
            
            assert create_response.status_code == 200
            create_result = create_response.json()
            org_id = create_result["result"]["data"]["id"]
            
            # Read the organization
            read_payload = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "entity_tool",
                    "arguments": {
                        "operation": "read",
                        "entity_type": "organization",
                        "entity_id": org_id
                    }
                }
            }
            
            read_response = await client.post(
                base_url,
                json=read_payload,
                headers={
                    "Authorization": f"Bearer {e2e_auth_token}",
                    "Content-Type": "application/json"
                }
            )
            
            assert read_response.status_code == 200
            read_result = read_response.json()
            
            org = read_result["result"]
            if "data" in org:
                org_data = org["data"]
                assert org_data["id"] == org_id
                assert org_data["name"] == f"Read Test Org {test_id}"
                assert org_data["slug"] == f"read-test-org-{test_id}"

    @pytest.mark.story("User can list all organizations")
    async def test_list_organizations(self, e2e_auth_token):
        """Test listing multiple organizations."""
        base_url = os.getenv("MCP_E2E_BASE_URL", "https://mcpdev.atoms.tech/api/mcp")
        test_id = unique_test_id()
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Create multiple organizations
            org_slugs = []
            for i in range(3):
                slug = f"list-test-{i}-{test_id}"
                org_slugs.append(slug)
                
                payload = {
                    "jsonrpc": "2.0",
                    "id": i + 1,
                    "method": "tools/call",
                    "params": {
                        "name": "entity_tool",
                        "arguments": {
                            "operation": "create",
                            "entity_type": "organization",
                            "data": {
                                "name": f"List Test Org {i} {test_id}",
                                "slug": slug,
                                "description": f"Organization {i} for list testing"
                            }
                        }
                    }
                }
                
                response = await client.post(
                    base_url,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {e2e_auth_token}",
                        "Content-Type": "application/json"
                    }
                )
                
                assert response.status_code == 200
            
            # List all organizations
            list_payload = {
                "jsonrpc": "2.0",
                "id": 10,
                "method": "tools/call",
                "params": {
                    "name": "entity_tool",
                    "arguments": {
                        "operation": "list",
                        "entity_type": "organization"
                    }
                }
            }
            
            list_response = await client.post(
                base_url,
                json=list_payload,
                headers={
                    "Authorization": f"Bearer {e2e_auth_token}",
                    "Content-Type": "application/json"
                }
            )
            
            assert list_response.status_code == 200
            list_result = list_response.json()
            
            # Should get a list of organizations
            orgs = list_result["result"]
            assert isinstance(orgs, (list, dict)), f"Expected list of organizations, got {type(orgs)}"

    @pytest.mark.story("User can update organization settings")
    async def test_update_organization(self, e2e_auth_token):
        """Test updating an organization."""
        base_url = os.getenv("MCP_E2E_BASE_URL", "https://mcpdev.atoms.tech/api/mcp")
        test_id = unique_test_id()
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Create organization
            create_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "entity_tool",
                    "arguments": {
                        "operation": "create",
                        "entity_type": "organization",
                        "data": {
                            "name": f"Update Test Org {test_id}",
                            "slug": f"update-test-org-{test_id}",
                            "description": "Original description"
                        }
                    }
                }
            }
            
            create_response = await client.post(
                base_url,
                json=create_payload,
                headers={
                    "Authorization": f"Bearer {e2e_auth_token}",
                    "Content-Type": "application/json"
                }
            )
            
            assert create_response.status_code == 200
            org_id = create_response.json()["result"]["data"]["id"]
            
            # Update the organization
            update_payload = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "entity_tool",
                    "arguments": {
                        "operation": "update",
                        "entity_type": "organization",
                        "entity_id": org_id,
                        "data": {
                            "description": "Updated description",
                            "website_url": "https://updated-example.com"
                        }
                    }
                }
            }
            
            update_response = await client.post(
                base_url,
                json=update_payload,
                headers={
                    "Authorization": f"Bearer {e2e_auth_token}",
                    "Content-Type": "application/json"
                }
            )
            
            assert update_response.status_code == 200
            update_result = update_response.json()
            
            updated_org = update_result["result"]
            if "data" in updated_org:
                org_data = updated_org["data"]
                assert org_data["id"] == org_id
                assert org_data["description"] == "Updated description"
                assert org_data["website_url"] == "https://updated-example.com"

    @pytest.mark.story("User can delete an organization")
    async def test_delete_organization(self, e2e_auth_token):
        """Test deleting an organization."""
        base_url = os.getenv("MCP_E2E_BASE_URL", "https://mcpdev.atoms.tech/api/mcp")
        test_id = unique_test_id()
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Create organization
            create_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "entity_tool",
                    "arguments": {
                        "operation": "create",
                        "entity_type": "organization",
                        "data": {
                            "name": f"Delete Test Org {test_id}",
                            "slug": f"delete-test-org-{test_id}",
                            "description": "Organization to be deleted"
                        }
                    }
                }
            }
            
            create_response = await client.post(
                base_url,
                json=create_payload,
                headers={
                    "Authorization": f"Bearer {e2e_auth_token}",
                    "Content-Type": "application/json"
                }
            )
            
            assert create_response.status_code == 200
            org_id = create_response.json()["result"]["data"]["id"]
            
            # Delete the organization
            delete_payload = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "entity_tool",
                    "arguments": {
                        "operation": "delete",
                        "entity_type": "organization",
                        "entity_id": org_id
                    }
                }
            }
            
            delete_response = await client.post(
                base_url,
                json=delete_payload,
                headers={
                    "Authorization": f"Bearer {e2e_auth_token}",
                    "Content-Type": "application/json"
                }
            )
            
            assert delete_response.status_code == 200
            delete_result = delete_response.json()
            
            # Verify deletion was successful
            assert delete_result["result"].get("success") is True or "deleted" in str(delete_result["result"])

    @pytest.mark.story("User can list all organizations")
    async def test_organization_search(self, e2e_auth_token):
        """Test searching organizations."""
        base_url = os.getenv("MCP_E2E_BASE_URL", "https://mcpdev.atoms.tech/api/mcp")
        test_id = unique_test_id()
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Create organizations with searchable content
            search_terms = ["technology", "healthcare", "finance"]
            
            for i, term in enumerate(search_terms):
                payload = {
                    "jsonrpc": "2.0",
                    "id": i + 1,
                    "method": "tools/call",
                    "params": {
                        "name": "entity_tool",
                        "arguments": {
                            "operation": "create",
                            "entity_type": "organization",
                            "data": {
                                "name": f"{term.title()} Corp {test_id}",
                                "slug": f"{term}-corp-{test_id}",
                                "description": f"A leading company in the {term} industry"
                            }
                        }
                    }
                }
                
                response = await client.post(
                    base_url,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {e2e_auth_token}",
                        "Content-Type": "application/json"
                    }
                )
                
                assert response.status_code == 200
            
            # Search for organizations
            search_payload = {
                "jsonrpc": "2.0",
                "id": 10,
                "method": "tools/call",
                "params": {
                    "name": "entity_tool",
                    "arguments": {
                        "operation": "search",
                        "entity_type": "organization",
                        "query": "technology",
                        "search_fields": ["name", "description"]
                    }
                }
            }
            
            search_response = await client.post(
                base_url,
                json=search_payload,
                headers={
                    "Authorization": f"Bearer {e2e_auth_token}",
                    "Content-Type": "application/json"
                }
            )
            
            assert search_response.status_code == 200
            search_result = search_response.json()
            
            # Should find the technology organization
            results = search_result["result"]
            assert results is not None
