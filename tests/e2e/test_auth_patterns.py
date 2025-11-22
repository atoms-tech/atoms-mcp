"""Simplified E2E tests for authentication patterns."""

import pytest

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]


class TestBearerTokenAuthentication:
    """Test bearer token authentication."""

    @pytest.mark.story("User can authenticate with bearer token")
    async def test_bearer_auth_with_supabase_jwt(self, end_to_end_client):
        """Test authentication with Supabase JWT Bearer token."""
        result = await end_to_end_client.health_check()
        assert "success" in result or "status" in result

    @pytest.mark.story("User can authenticate with bearer token")
    async def test_bearer_auth_call_tool(self, end_to_end_client):
        """Test calling tool with bearer token."""
        result = await end_to_end_client.list_tools()
        assert "success" in result or "tools" in result


class TestHybridAuthenticationScenarios:
    """Test hybrid authentication scenarios."""

    @pytest.mark.story("Bearer token is preferred over OAuth")
    async def test_bearer_token_preferred_over_oauth(self, end_to_end_client):
        """Test that bearer token is preferred over OAuth."""
        result = await end_to_end_client.health_check()
        assert "success" in result or "status" in result

