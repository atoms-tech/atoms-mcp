"""Canonical integration tests for Atoms MCP.

These tests exercise the production HTTP surface area using real Supabase
credentials and an AuthKit-configured MCP server.
Run with: pytest tests/test_end_to_end.py -v -s
"""

from __future__ import annotations

import os
import time
import uuid
from typing import Any, Dict

import httpx
import pytest
from supabase import create_client

MCP_BASE_URL = os.getenv("ATOMS_FASTMCP_BASE_URL", "http://127.0.0.1:8000")
MCP_PATH = os.getenv("ATOMS_FASTMCP_HTTP_PATH", "/api/mcp")
TEST_EMAIL = os.getenv("ATOMS_TEST_EMAIL", "kooshapari@kooshapari.com")
TEST_PASSWORD = os.getenv("ATOMS_TEST_PASSWORD", "118118")

pytestmark = [pytest.mark.asyncio, pytest.mark.http]


@pytest.fixture(scope="session")
def _supabase_env():
    """Ensure Supabase environment variables are present."""
    url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    key = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

    if not url or not key:
        pytest.skip("Supabase credentials not configured for canonical tests")

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
        pytest.skip("Could not obtain Supabase JWT for canonical tests")

    return session.access_token


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


class TestEntityLifecycle:
    """Validate CRUD operations via the consolidated entity tool."""

    @pytest.mark.asyncio
    async def test_entity_crud_flow(self, call_mcp):
        create = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "organization",
                "data": {
                    "name": "Canonical Test Org",
                    "slug": f"canonical-org-{uuid.uuid4().hex[:8]}",
                    "description": "Created by canonical end-to-end tests",
                    "type": "team",
                },
            },
        )
        assert create.get("success") is True, create
        org_id = create["data"]["id"]

        read = await call_mcp(
            "entity_tool",
            {
                "operation": "read",
                "entity_type": "organization",
                "entity_id": org_id,
            },
        )
        assert read.get("success") is True, read
        assert read["data"]["id"] == org_id

        update = await call_mcp(
            "entity_tool",
            {
                "operation": "update",
                "entity_type": "organization",
                "entity_id": org_id,
                "data": {"description": "Updated by canonical tests"},
            },
        )
        assert update.get("success") is True, update
        assert "Updated by canonical tests" in update["data"]["description"]

        listing = await call_mcp(
            "entity_tool",
            {
                "operation": "list",
                "entity_type": "organization",
                "limit": 5,
            },
        )
        assert listing.get("success") is True, listing
        assert isinstance(listing.get("data"), list)

        delete = await call_mcp(
            "entity_tool",
            {
                "operation": "delete",
                "entity_type": "organization",
                "entity_id": org_id,
                "soft_delete": True,
            },
        )
        assert delete.get("success") is True, delete


class TestWorkspaceAndQuery:
    """Exercise workspace management and data queries."""

    @pytest.mark.asyncio
    async def test_workspace_operations(self, call_mcp):
        context = await call_mcp("workspace_tool", {"operation": "get_context"})
        assert context.get("success") is True, context

        workspaces = await call_mcp("workspace_tool", {"operation": "list_workspaces"})
        assert workspaces.get("success") is True, workspaces
        assert "organizations" in workspaces.get("data", {})

    @pytest.mark.asyncio
    async def test_query_search(self, call_mcp):
        query = await call_mcp(
            "query_tool",
            {
                "query_type": "search",
                "entities": ["organization"],
                "search_term": "test",
                "limit": 5,
            },
        )
        assert query.get("success") is True, query
        assert "data" in query


class TestAuthComplete:
    """Verify the AuthKit completion bridge remains reachable."""

    @pytest.mark.asyncio
    async def test_auth_complete_endpoint(self, supabase_jwt):
        endpoint = f"{MCP_BASE_URL.rstrip('/')}/auth/complete"
        payload = {"external_auth_id": f"pytest_{int(time.time())}"}
        headers = {
            "Authorization": f"Bearer {supabase_jwt}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(endpoint, json=payload, headers=headers)

        assert response.status_code in {200, 400}, response.text
        if response.status_code == 200:
            body = response.json()
            assert "success" in body
            if body.get("success"):
                assert "redirect_uri" in body
                assert "session_id" in body


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
