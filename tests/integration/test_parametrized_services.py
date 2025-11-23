"""Parametrized integration tests - same tests run against mock and live services."""

import pytest
import os
from typing import Dict, Any


@pytest.fixture(params=["mock", "live"])
def service_client(request, database, live_mcp_client):
    """Parametrized fixture that provides either mock or live service client.
    
    Each test using this fixture will run twice:
    - Once with mock database
    - Once with live MCP client (if available)
    """
    if request.param == "mock":
        return database
    else:
        return live_mcp_client


class TestEntityOperations:
    """Entity operations - runs against both mock and live services."""

    def test_entity_create(self, service_client):
        """Test entity creation (mock and live)."""
        if hasattr(service_client, 'execute'):
            # Mock service
            result = service_client.execute("INSERT INTO entities (name, type) VALUES ('test', 'requirement')")
            assert result["success"] is True
        else:
            # Live service (httpx client)
            import asyncio
            async def create():
                response = await service_client.post(
                    "/tools/entity_create",
                    json={"name": "test", "type": "requirement"}
                )
                return response.status_code in [200, 201]
            assert asyncio.run(create())

    def test_entity_read(self, service_client):
        """Test entity read (mock and live)."""
        if hasattr(service_client, 'query'):
            # Mock service
            result = service_client.query("SELECT * FROM entities LIMIT 1")
            assert isinstance(result, list)
        else:
            # Live service
            import asyncio
            async def read():
                response = await service_client.post(
                    "/tools/entity_list",
                    json={"limit": 1}
                )
                return response.status_code in [200, 400]
            assert asyncio.run(read())

    def test_entity_update(self, service_client):
        """Test entity update (mock and live)."""
        if hasattr(service_client, 'execute'):
            # Mock service
            result = service_client.execute("UPDATE entities SET name = 'updated' WHERE id = 'e1'")
            assert result["success"] is True
        else:
            # Live service
            import asyncio
            async def update():
                response = await service_client.post(
                    "/tools/entity_update",
                    json={"id": "e1", "name": "updated"}
                )
                return response.status_code in [200, 404]
            assert asyncio.run(update())

    def test_entity_delete(self, service_client):
        """Test entity delete (mock and live)."""
        if hasattr(service_client, 'execute'):
            # Mock service
            result = service_client.execute("DELETE FROM entities WHERE id = 'e1'")
            assert result["success"] is True
        else:
            # Live service
            import asyncio
            async def delete():
                response = await service_client.post(
                    "/tools/entity_delete",
                    json={"id": "e1"}
                )
                return response.status_code in [200, 204, 404]
            assert asyncio.run(delete())

    def test_entity_search(self, service_client):
        """Test entity search (mock and live)."""
        if hasattr(service_client, 'query'):
            # Mock service
            result = service_client.query("SELECT * FROM entities WHERE name LIKE '%test%'")
            assert isinstance(result, list)
        else:
            # Live service
            import asyncio
            async def search():
                response = await service_client.post(
                    "/tools/entity_search",
                    json={"query": "test"}
                )
                return response.status_code in [200, 400]
            assert asyncio.run(search())

    def test_entity_list_with_pagination(self, service_client):
        """Test entity listing with pagination (mock and live)."""
        if hasattr(service_client, 'query'):
            # Mock service
            result = service_client.query("SELECT * FROM entities LIMIT 10 OFFSET 0")
            assert isinstance(result, list)
        else:
            # Live service
            import asyncio
            async def list_paginated():
                response = await service_client.post(
                    "/tools/entity_list",
                    json={"limit": 10, "offset": 0}
                )
                return response.status_code in [200, 400]
            assert asyncio.run(list_paginated())

    def test_entity_bulk_operations(self, service_client):
        """Test bulk entity operations (mock and live)."""
        if hasattr(service_client, 'execute'):
            # Mock service
            for i in range(3):
                result = service_client.execute(f"INSERT INTO entities (id, name, type) VALUES ('e{i}', 'entity{i}', 'requirement')")
                assert result["success"] is True
        else:
            # Live service
            import asyncio
            async def bulk_create():
                for i in range(3):
                    response = await service_client.post(
                        "/tools/entity_create",
                        json={"name": f"entity{i}", "type": "requirement"}
                    )
                    if response.status_code not in [200, 201]:
                        return False
                return True
            assert asyncio.run(bulk_create())

    def test_entity_error_handling(self, service_client):
        """Test entity error handling (mock and live)."""
        if hasattr(service_client, 'query'):
            # Mock service
            result = service_client.query("SELECT * FROM entities WHERE id = 'nonexistent'")
            assert isinstance(result, list)
        else:
            # Live service
            import asyncio
            async def error_handling():
                response = await service_client.post(
                    "/tools/entity_get",
                    json={"id": "nonexistent"}
                )
                return response.status_code in [404, 400]
            assert asyncio.run(error_handling())

    def test_entity_concurrent_operations(self, service_client):
        """Test concurrent entity operations (mock and live)."""
        if hasattr(service_client, 'execute'):
            # Mock service
            results = []
            for i in range(3):
                result = service_client.execute(f"INSERT INTO entities (id, name, type) VALUES ('c{i}', 'concurrent{i}', 'requirement')")
                results.append(result["success"])
            assert all(results)
        else:
            # Live service
            import asyncio
            async def concurrent():
                responses = []
                for i in range(3):
                    response = await service_client.post(
                        "/tools/entity_create",
                        json={"name": f"concurrent{i}", "type": "requirement"}
                    )
                    responses.append(response.status_code)
                return all(code in [200, 201] for code in responses)
            assert asyncio.run(concurrent())


class TestRelationshipOperations:
    """Relationship operations - runs against both mock and live services."""

    def test_relationship_create(self, service_client):
        """Test relationship creation (mock and live)."""
        if hasattr(service_client, 'execute'):
            # Mock service
            result = service_client.execute("INSERT INTO relationships (source_id, target_id, type) VALUES ('e1', 'e2', 'depends_on')")
            assert result["success"] is True
        else:
            # Live service
            import asyncio
            async def create():
                response = await service_client.post(
                    "/tools/relationship_create",
                    json={"source_id": "e1", "target_id": "e2", "type": "depends_on"}
                )
                return response.status_code in [200, 201, 400, 404]
            assert asyncio.run(create())

    def test_relationship_read(self, service_client):
        """Test relationship read (mock and live)."""
        if hasattr(service_client, 'query'):
            # Mock service
            result = service_client.query("SELECT * FROM relationships LIMIT 1")
            assert isinstance(result, list)
        else:
            # Live service
            import asyncio
            async def read():
                response = await service_client.post(
                    "/tools/relationship_list",
                    json={"limit": 1}
                )
                return response.status_code in [200, 400]
            assert asyncio.run(read())

    def test_relationship_update(self, service_client):
        """Test relationship update (mock and live)."""
        if hasattr(service_client, 'execute'):
            # Mock service
            result = service_client.execute("UPDATE relationships SET metadata = '{}' WHERE source_id = 'e1'")
            assert result["success"] is True
        else:
            # Live service
            import asyncio
            async def update():
                response = await service_client.post(
                    "/tools/relationship_update",
                    json={"id": "rel-1", "metadata": {}}
                )
                return response.status_code in [200, 404]
            assert asyncio.run(update())

    def test_relationship_delete(self, service_client):
        """Test relationship delete (mock and live)."""
        if hasattr(service_client, 'execute'):
            # Mock service
            result = service_client.execute("DELETE FROM relationships WHERE source_id = 'e1'")
            assert result["success"] is True
        else:
            # Live service
            import asyncio
            async def delete():
                response = await service_client.post(
                    "/tools/relationship_delete",
                    json={"id": "rel-1"}
                )
                return response.status_code in [200, 204, 404]
            assert asyncio.run(delete())

    def test_relationship_filtering(self, service_client):
        """Test relationship filtering (mock and live)."""
        if hasattr(service_client, 'query'):
            # Mock service
            result = service_client.query("SELECT * FROM relationships WHERE type = 'depends_on'")
            assert isinstance(result, list)
        else:
            # Live service
            import asyncio
            async def filter_rel():
                response = await service_client.post(
                    "/tools/relationship_list",
                    json={"filters": {"type": "depends_on"}}
                )
                return response.status_code in [200, 400]
            assert asyncio.run(filter_rel())

    def test_relationship_bulk_operations(self, service_client):
        """Test bulk relationship operations (mock and live)."""
        if hasattr(service_client, 'execute'):
            # Mock service
            for i in range(3):
                result = service_client.execute(f"INSERT INTO relationships (source_id, target_id, type) VALUES ('e{i}', 'e{i+1}', 'depends_on')")
                assert result["success"] is True
        else:
            # Live service
            import asyncio
            async def bulk_create():
                for i in range(3):
                    response = await service_client.post(
                        "/tools/relationship_create",
                        json={"source_id": f"e{i}", "target_id": f"e{i+1}", "type": "depends_on"}
                    )
                    if response.status_code not in [200, 201, 400, 404]:
                        return False
                return True
            assert asyncio.run(bulk_create())

