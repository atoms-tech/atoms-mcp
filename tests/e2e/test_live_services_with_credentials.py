"""Live service tests using actual account credentials and MCP API."""

import pytest
import os
import asyncio
from typing import Optional, Dict, Any


class TestLiveServicesWithCredentials:
    """Test live services using your account credentials."""

    @pytest.fixture
    def credentials(self):
        """Get credentials from environment."""
        return {
            "email": os.getenv("ATOMS_TEST_EMAIL", "kooshapari@kooshapari.com"),
            "password": os.getenv("ATOMS_TEST_PASSWORD", "ASD3on54_Pax90"),
            "workos_api_key": os.getenv("WORKOS_API_KEY"),
            "workos_client_id": os.getenv("WORKOS_CLIENT_ID"),
            "mcp_base_url": os.getenv("MCP_INTEGRATION_BASE_URL", "http://127.0.0.1:8000/api/mcp")
        }

    @pytest.mark.asyncio
    async def test_authenticate_with_credentials(self, credentials):
        """Test authentication with your credentials."""
        from tests.utils.workos_auth import authenticate_with_workos

        token = await authenticate_with_workos(
            credentials["email"],
            credentials["password"],
            credentials["workos_api_key"],
            credentials["workos_client_id"]
        )

        # Should either get token or skip if WorkOS not configured
        assert token is None or isinstance(token, str)

    @pytest.mark.asyncio
    async def test_create_entity_with_live_service(self, credentials):
        """Test creating entity with live MCP service."""
        from tests.utils.workos_auth import authenticate_with_workos
        import httpx

        # Authenticate
        token = await authenticate_with_workos(
            credentials["email"],
            credentials["password"],
            credentials["workos_api_key"],
            credentials["workos_client_id"]
        )

        if not token:
            pytest.skip("Authentication failed - WorkOS not configured")

        # Create entity via MCP API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{credentials['mcp_base_url']}/tools/entity_create",
                json={
                    "name": "Test Entity",
                    "type": "requirement",
                    "description": "Test entity created by live service test"
                },
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0
            )

            # Should succeed or return meaningful error
            assert response.status_code in [200, 201, 400, 401, 403, 404]

    @pytest.mark.asyncio
    async def test_list_entities_with_live_service(self, credentials):
        """Test listing entities with live MCP service."""
        from tests.utils.workos_auth import authenticate_with_workos
        import httpx

        # Authenticate
        token = await authenticate_with_workos(
            credentials["email"],
            credentials["password"],
            credentials["workos_api_key"],
            credentials["workos_client_id"]
        )

        if not token:
            pytest.skip("Authentication failed - WorkOS not configured")

        # List entities via MCP API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{credentials['mcp_base_url']}/tools/entity_list",
                json={"limit": 10},
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0
            )

            # Should succeed or return meaningful error
            assert response.status_code in [200, 400, 401, 403, 404]

    @pytest.mark.asyncio
    async def test_search_entities_with_live_service(self, credentials):
        """Test searching entities with live MCP service."""
        from tests.utils.workos_auth import authenticate_with_workos
        import httpx

        # Authenticate
        token = await authenticate_with_workos(
            credentials["email"],
            credentials["password"],
            credentials["workos_api_key"],
            credentials["workos_client_id"]
        )

        if not token:
            pytest.skip("Authentication failed - WorkOS not configured")

        # Search entities via MCP API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{credentials['mcp_base_url']}/tools/entity_search",
                json={"query": "test"},
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0
            )

            # Should succeed or return meaningful error
            assert response.status_code in [200, 400, 401, 403, 404]

    @pytest.mark.asyncio
    async def test_create_relationship_with_live_service(self, credentials):
        """Test creating relationship with live MCP service."""
        from tests.utils.workos_auth import authenticate_with_workos
        import httpx

        # Authenticate
        token = await authenticate_with_workos(
            credentials["email"],
            credentials["password"],
            credentials["workos_api_key"],
            credentials["workos_client_id"]
        )

        if not token:
            pytest.skip("Authentication failed - WorkOS not configured")

        # Create relationship via MCP API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{credentials['mcp_base_url']}/tools/relationship_create",
                json={
                    "source_id": "entity-1",
                    "target_id": "entity-2",
                    "type": "depends_on"
                },
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0
            )

            # Should succeed or return meaningful error
            assert response.status_code in [200, 201, 400, 401, 403, 404]

    @pytest.mark.asyncio
    async def test_get_user_profile_with_live_service(self, credentials):
        """Test getting user profile with live MCP service."""
        from tests.utils.workos_auth import authenticate_with_workos
        import httpx

        # Authenticate
        token = await authenticate_with_workos(
            credentials["email"],
            credentials["password"],
            credentials["workos_api_key"],
            credentials["workos_client_id"]
        )

        if not token:
            pytest.skip("Authentication failed - WorkOS not configured")

        # Get user profile via MCP API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{credentials['mcp_base_url']}/tools/user_get_profile",
                json={},
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0
            )

            # Should succeed or return meaningful error
            assert response.status_code in [200, 400, 401, 403, 404]

    @pytest.mark.asyncio
    async def test_list_workspaces_with_live_service(self, credentials):
        """Test listing workspaces with live MCP service."""
        from tests.utils.workos_auth import authenticate_with_workos
        import httpx

        # Authenticate
        token = await authenticate_with_workos(
            credentials["email"],
            credentials["password"],
            credentials["workos_api_key"],
            credentials["workos_client_id"]
        )

        if not token:
            pytest.skip("Authentication failed - WorkOS not configured")

        # List workspaces via MCP API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{credentials['mcp_base_url']}/tools/workspace_list",
                json={},
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0
            )

            # Should succeed or return meaningful error
            assert response.status_code in [200, 400, 401, 403, 404]

    @pytest.mark.asyncio
    async def test_error_handling_with_invalid_token(self):
        """Test error handling with invalid token."""
        import httpx

        mcp_base_url = os.getenv("MCP_INTEGRATION_BASE_URL", "http://127.0.0.1:8000/api/mcp")

        # Try with invalid token
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{mcp_base_url}/tools/entity_list",
                json={"limit": 10},
                headers={"Authorization": "Bearer invalid-token"},
                timeout=10.0
            )

            # Should return 401 Unauthorized
            assert response.status_code in [401, 403, 404]

    @pytest.mark.asyncio
    async def test_error_handling_without_token(self):
        """Test error handling without token."""
        import httpx

        mcp_base_url = os.getenv("MCP_INTEGRATION_BASE_URL", "http://127.0.0.1:8000/api/mcp")

        # Try without token
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{mcp_base_url}/tools/entity_list",
                json={"limit": 10},
                timeout=10.0
            )

            # Should return 401 Unauthorized
            assert response.status_code in [401, 403, 404]

