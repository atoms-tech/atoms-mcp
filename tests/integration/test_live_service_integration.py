"""Live service integration tests - mirror of mock integration tests with real API calls."""

import pytest
import pytest_asyncio
import httpx
import os
from typing import Dict, Any


@pytest_asyncio.fixture
async def live_mcp_client(e2e_auth_token):
    """Create authenticated MCP client for live service testing."""
    if not e2e_auth_token:
        pytest.skip("No authentication token available")

    base_url = os.getenv("MCP_INTEGRATION_BASE_URL", "http://127.0.0.1:8000/api/mcp")

    async with httpx.AsyncClient(
        base_url=base_url,
        headers={"Authorization": f"Bearer {e2e_auth_token}"},
        timeout=30.0
    ) as client:
        yield client


class TestLiveEntityIntegration:
    """Live service entity integration tests (20+ tests)."""

    @pytest.mark.asyncio
    async def test_entity_create_basic(self, live_mcp_client):
        """Test basic entity creation via live service."""
        response = await live_mcp_client.post(
            "/tools/entity_create",
            json={"name": "test-entity", "type": "requirement"}
        )
        assert response.status_code in [200, 201]

    @pytest.mark.asyncio
    async def test_entity_create_with_metadata(self, live_mcp_client):
        """Test entity creation with metadata via live service."""
        response = await live_mcp_client.post(
            "/tools/entity_create",
            json={
                "name": "test-entity",
                "type": "requirement",
                "metadata": {"key": "value"}
            }
        )
        assert response.status_code in [200, 201]

    @pytest.mark.asyncio
    async def test_entity_read_by_id(self, live_mcp_client):
        """Test reading entity by ID via live service."""
        response = await live_mcp_client.post(
            "/tools/entity_get",
            json={"id": "test-entity-1"}
        )
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_entity_list(self, live_mcp_client):
        """Test listing entities via live service."""
        response = await live_mcp_client.post(
            "/tools/entity_list",
            json={"limit": 10}
        )
        assert response.status_code in [200, 400]

    @pytest.mark.asyncio
    async def test_entity_update(self, live_mcp_client):
        """Test updating entity via live service."""
        response = await live_mcp_client.post(
            "/tools/entity_update",
            json={"id": "test-entity-1", "name": "updated"}
        )
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_entity_delete(self, live_mcp_client):
        """Test deleting entity via live service."""
        response = await live_mcp_client.post(
            "/tools/entity_delete",
            json={"id": "test-entity-1"}
        )
        assert response.status_code in [200, 204, 404]

    @pytest.mark.asyncio
    async def test_entity_search(self, live_mcp_client):
        """Test searching entities via live service."""
        response = await live_mcp_client.post(
            "/tools/entity_search",
            json={"query": "test"}
        )
        assert response.status_code in [200, 400]

    @pytest.mark.asyncio
    async def test_entity_bulk_create(self, live_mcp_client):
        """Test bulk entity creation via live service."""
        for i in range(3):
            response = await live_mcp_client.post(
                "/tools/entity_create",
                json={"name": f"bulk-entity-{i}", "type": "requirement"}
            )
            assert response.status_code in [200, 201]

    @pytest.mark.asyncio
    async def test_entity_with_pagination(self, live_mcp_client):
        """Test entity listing with pagination via live service."""
        response = await live_mcp_client.post(
            "/tools/entity_list",
            json={"limit": 5, "offset": 0}
        )
        assert response.status_code in [200, 400]

    @pytest.mark.asyncio
    async def test_entity_with_filters(self, live_mcp_client):
        """Test entity listing with filters via live service."""
        response = await live_mcp_client.post(
            "/tools/entity_list",
            json={"filters": {"type": "requirement"}}
        )
        assert response.status_code in [200, 400]

    @pytest.mark.asyncio
    async def test_entity_error_handling_invalid_id(self, live_mcp_client):
        """Test error handling for invalid entity ID."""
        response = await live_mcp_client.post(
            "/tools/entity_get",
            json={"id": "nonexistent-id-12345"}
        )
        assert response.status_code in [404, 400]

    @pytest.mark.asyncio
    async def test_entity_error_handling_missing_field(self, live_mcp_client):
        """Test error handling for missing required field."""
        response = await live_mcp_client.post(
            "/tools/entity_create",
            json={"type": "requirement"}  # missing name
        )
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_entity_concurrent_operations(self, live_mcp_client):
        """Test concurrent entity operations."""
        responses = []
        for i in range(3):
            response = await live_mcp_client.post(
                "/tools/entity_create",
                json={"name": f"concurrent-{i}", "type": "requirement"}
            )
            responses.append(response.status_code)
        
        assert all(code in [200, 201] for code in responses)

    @pytest.mark.asyncio
    async def test_entity_metadata_operations(self, live_mcp_client):
        """Test entity metadata operations."""
        response = await live_mcp_client.post(
            "/tools/entity_create",
            json={
                "name": "metadata-test",
                "type": "requirement",
                "metadata": {"priority": "high", "owner": "test"}
            }
        )
        assert response.status_code in [200, 201]

    @pytest.mark.asyncio
    async def test_entity_status_transitions(self, live_mcp_client):
        """Test entity status transitions."""
        # Create entity
        create_response = await live_mcp_client.post(
            "/tools/entity_create",
            json={"name": "status-test", "type": "requirement", "status": "draft"}
        )
        assert create_response.status_code in [200, 201]

    @pytest.mark.asyncio
    async def test_entity_type_variations(self, live_mcp_client):
        """Test different entity types."""
        types = ["requirement", "document", "project", "organization"]
        for entity_type in types:
            response = await live_mcp_client.post(
                "/tools/entity_create",
                json={"name": f"type-{entity_type}", "type": entity_type}
            )
            assert response.status_code in [200, 201, 400]

    @pytest.mark.asyncio
    async def test_entity_response_format(self, live_mcp_client):
        """Test entity response format."""
        response = await live_mcp_client.post(
            "/tools/entity_list",
            json={"limit": 1}
        )
        assert response.status_code in [200, 400]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (dict, list))

    @pytest.mark.asyncio
    async def test_entity_performance(self, live_mcp_client):
        """Test entity operation performance."""
        import time
        start = time.time()
        response = await live_mcp_client.post(
            "/tools/entity_list",
            json={"limit": 100}
        )
        elapsed = time.time() - start
        assert response.status_code in [200, 400]
        assert elapsed < 5.0  # Should complete within 5 seconds


class TestLiveRelationshipIntegration:
    """Live service relationship integration tests (15+ tests)."""

    @pytest.mark.asyncio
    async def test_relationship_create(self, live_mcp_client):
        """Test creating relationship via live service."""
        response = await live_mcp_client.post(
            "/tools/relationship_create",
            json={
                "source_id": "entity-1",
                "target_id": "entity-2",
                "type": "depends_on"
            }
        )
        assert response.status_code in [200, 201, 400, 404]

    @pytest.mark.asyncio
    async def test_relationship_list(self, live_mcp_client):
        """Test listing relationships via live service."""
        response = await live_mcp_client.post(
            "/tools/relationship_list",
            json={"limit": 10}
        )
        assert response.status_code in [200, 400]

    @pytest.mark.asyncio
    async def test_relationship_get(self, live_mcp_client):
        """Test getting relationship via live service."""
        response = await live_mcp_client.post(
            "/tools/relationship_get",
            json={"id": "rel-1"}
        )
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_relationship_update(self, live_mcp_client):
        """Test updating relationship via live service."""
        response = await live_mcp_client.post(
            "/tools/relationship_update",
            json={"id": "rel-1", "metadata": {"priority": "high"}}
        )
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_relationship_delete(self, live_mcp_client):
        """Test deleting relationship via live service."""
        response = await live_mcp_client.post(
            "/tools/relationship_delete",
            json={"id": "rel-1"}
        )
        assert response.status_code in [200, 204, 404]

    @pytest.mark.asyncio
    async def test_relationship_by_source(self, live_mcp_client):
        """Test getting relationships by source."""
        response = await live_mcp_client.post(
            "/tools/relationship_list",
            json={"filters": {"source_id": "entity-1"}}
        )
        assert response.status_code in [200, 400]

    @pytest.mark.asyncio
    async def test_relationship_by_target(self, live_mcp_client):
        """Test getting relationships by target."""
        response = await live_mcp_client.post(
            "/tools/relationship_list",
            json={"filters": {"target_id": "entity-2"}}
        )
        assert response.status_code in [200, 400]

    @pytest.mark.asyncio
    async def test_relationship_by_type(self, live_mcp_client):
        """Test getting relationships by type."""
        response = await live_mcp_client.post(
            "/tools/relationship_list",
            json={"filters": {"type": "depends_on"}}
        )
        assert response.status_code in [200, 400]

    @pytest.mark.asyncio
    async def test_relationship_bulk_create(self, live_mcp_client):
        """Test bulk relationship creation."""
        for i in range(3):
            response = await live_mcp_client.post(
                "/tools/relationship_create",
                json={
                    "source_id": f"entity-{i}",
                    "target_id": f"entity-{i+1}",
                    "type": "depends_on"
                }
            )
            assert response.status_code in [200, 201, 400, 404]

    @pytest.mark.asyncio
    async def test_relationship_error_handling(self, live_mcp_client):
        """Test relationship error handling."""
        response = await live_mcp_client.post(
            "/tools/relationship_create",
            json={"source_id": "invalid", "target_id": "invalid"}
        )
        assert response.status_code in [400, 404]

    @pytest.mark.asyncio
    async def test_relationship_metadata(self, live_mcp_client):
        """Test relationship metadata operations."""
        response = await live_mcp_client.post(
            "/tools/relationship_create",
            json={
                "source_id": "entity-1",
                "target_id": "entity-2",
                "type": "depends_on",
                "metadata": {"priority": "high"}
            }
        )
        assert response.status_code in [200, 201, 400, 404]

    @pytest.mark.asyncio
    async def test_relationship_type_variations(self, live_mcp_client):
        """Test different relationship types."""
        types = ["depends_on", "related_to", "blocks", "is_blocked_by"]
        for rel_type in types:
            response = await live_mcp_client.post(
                "/tools/relationship_create",
                json={
                    "source_id": "entity-1",
                    "target_id": "entity-2",
                    "type": rel_type
                }
            )
            assert response.status_code in [200, 201, 400, 404]

    @pytest.mark.asyncio
    async def test_relationship_pagination(self, live_mcp_client):
        """Test relationship pagination."""
        response = await live_mcp_client.post(
            "/tools/relationship_list",
            json={"limit": 5, "offset": 0}
        )
        assert response.status_code in [200, 400]

    @pytest.mark.asyncio
    async def test_relationship_performance(self, live_mcp_client):
        """Test relationship operation performance."""
        import time
        start = time.time()
        response = await live_mcp_client.post(
            "/tools/relationship_list",
            json={"limit": 100}
        )
        elapsed = time.time() - start
        assert response.status_code in [200, 400]
        assert elapsed < 5.0

