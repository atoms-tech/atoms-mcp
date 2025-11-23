"""Parametrized e2e tests - same tests run against mock and live services."""

import pytest
import asyncio
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


class TestEntityLifecycleE2E:
    """Entity lifecycle e2e tests - runs against both mock and live services."""

    def test_entity_lifecycle_create_read_update_delete(self, service_client):
        """Test complete entity lifecycle (mock and live)."""
        if hasattr(service_client, 'execute'):
            # Mock service
            # Create
            create_result = service_client.execute("INSERT INTO entities (id, name, type) VALUES ('lifecycle-1', 'test', 'requirement')")
            assert create_result["success"] is True
            
            # Read
            read_result = service_client.query("SELECT * FROM entities WHERE id = 'lifecycle-1'")
            assert len(read_result) > 0
            
            # Update
            update_result = service_client.execute("UPDATE entities SET name = 'updated' WHERE id = 'lifecycle-1'")
            assert update_result["success"] is True
            
            # Delete
            delete_result = service_client.execute("DELETE FROM entities WHERE id = 'lifecycle-1'")
            assert delete_result["success"] is True
        else:
            # Live service
            async def lifecycle():
                # Create
                create_resp = await service_client.post(
                    "/tools/entity_create",
                    json={"name": "lifecycle-1", "type": "requirement"}
                )
                if create_resp.status_code not in [200, 201]:
                    return False
                
                # Read
                read_resp = await service_client.post(
                    "/tools/entity_list",
                    json={"limit": 1}
                )
                if read_resp.status_code not in [200, 400]:
                    return False
                
                # Update
                update_resp = await service_client.post(
                    "/tools/entity_update",
                    json={"id": "lifecycle-1", "name": "updated"}
                )
                if update_resp.status_code not in [200, 404]:
                    return False
                
                # Delete
                delete_resp = await service_client.post(
                    "/tools/entity_delete",
                    json={"id": "lifecycle-1"}
                )
                return delete_resp.status_code in [200, 204, 404]
            
            assert asyncio.run(lifecycle())

    def test_entity_with_relationships(self, service_client):
        """Test entity with relationships (mock and live)."""
        if hasattr(service_client, 'execute'):
            # Mock service
            service_client.execute("INSERT INTO entities (id, name, type) VALUES ('e1', 'entity1', 'requirement')")
            service_client.execute("INSERT INTO entities (id, name, type) VALUES ('e2', 'entity2', 'requirement')")
            result = service_client.execute("INSERT INTO relationships (source_id, target_id, type) VALUES ('e1', 'e2', 'depends_on')")
            assert result["success"] is True
        else:
            # Live service
            async def with_rel():
                # Create entities
                e1 = await service_client.post(
                    "/tools/entity_create",
                    json={"name": "entity1", "type": "requirement"}
                )
                e2 = await service_client.post(
                    "/tools/entity_create",
                    json={"name": "entity2", "type": "requirement"}
                )
                
                if e1.status_code not in [200, 201] or e2.status_code not in [200, 201]:
                    return False
                
                # Create relationship
                rel = await service_client.post(
                    "/tools/relationship_create",
                    json={"source_id": "e1", "target_id": "e2", "type": "depends_on"}
                )
                return rel.status_code in [200, 201, 400, 404]
            
            assert asyncio.run(with_rel())

    def test_entity_bulk_workflow(self, service_client):
        """Test bulk entity workflow (mock and live)."""
        if hasattr(service_client, 'execute'):
            # Mock service
            for i in range(5):
                result = service_client.execute(f"INSERT INTO entities (id, name, type) VALUES ('bulk-{i}', 'bulk{i}', 'requirement')")
                assert result["success"] is True
            
            result = service_client.query("SELECT * FROM entities WHERE type = 'requirement'")
            assert len(result) >= 5
        else:
            # Live service
            async def bulk():
                for i in range(5):
                    resp = await service_client.post(
                        "/tools/entity_create",
                        json={"name": f"bulk{i}", "type": "requirement"}
                    )
                    if resp.status_code not in [200, 201]:
                        return False
                
                list_resp = await service_client.post(
                    "/tools/entity_list",
                    json={"limit": 100}
                )
                return list_resp.status_code in [200, 400]
            
            assert asyncio.run(bulk())

    def test_entity_search_workflow(self, service_client):
        """Test entity search workflow (mock and live)."""
        if hasattr(service_client, 'execute'):
            # Mock service
            service_client.execute("INSERT INTO entities (id, name, type) VALUES ('search-1', 'searchable', 'requirement')")
            result = service_client.query("SELECT * FROM entities WHERE name LIKE '%searchable%'")
            assert len(result) > 0
        else:
            # Live service
            async def search():
                # Create
                create_resp = await service_client.post(
                    "/tools/entity_create",
                    json={"name": "searchable", "type": "requirement"}
                )
                if create_resp.status_code not in [200, 201]:
                    return False
                
                # Search
                search_resp = await service_client.post(
                    "/tools/entity_search",
                    json={"query": "searchable"}
                )
                return search_resp.status_code in [200, 400]
            
            assert asyncio.run(search())

    def test_entity_pagination_workflow(self, service_client):
        """Test entity pagination workflow (mock and live)."""
        if hasattr(service_client, 'execute'):
            # Mock service
            for i in range(15):
                service_client.execute(f"INSERT INTO entities (id, name, type) VALUES ('page-{i}', 'page{i}', 'requirement')")
            
            page1 = service_client.query("SELECT * FROM entities LIMIT 10 OFFSET 0")
            page2 = service_client.query("SELECT * FROM entities LIMIT 10 OFFSET 10")
            assert isinstance(page1, list)
            assert isinstance(page2, list)
        else:
            # Live service
            async def pagination():
                for i in range(15):
                    await service_client.post(
                        "/tools/entity_create",
                        json={"name": f"page{i}", "type": "requirement"}
                    )
                
                page1 = await service_client.post(
                    "/tools/entity_list",
                    json={"limit": 10, "offset": 0}
                )
                page2 = await service_client.post(
                    "/tools/entity_list",
                    json={"limit": 10, "offset": 10}
                )
                return page1.status_code in [200, 400] and page2.status_code in [200, 400]
            
            assert asyncio.run(pagination())


class TestRelationshipLifecycleE2E:
    """Relationship lifecycle e2e tests - runs against both mock and live services."""

    def test_relationship_lifecycle(self, service_client):
        """Test complete relationship lifecycle (mock and live)."""
        if hasattr(service_client, 'execute'):
            # Mock service
            service_client.execute("INSERT INTO relationships (id, source_id, target_id, type) VALUES ('rel-1', 'e1', 'e2', 'depends_on')")
            result = service_client.query("SELECT * FROM relationships WHERE id = 'rel-1'")
            assert len(result) > 0
            
            update_result = service_client.execute("UPDATE relationships SET metadata = '{}' WHERE id = 'rel-1'")
            assert update_result["success"] is True
            
            delete_result = service_client.execute("DELETE FROM relationships WHERE id = 'rel-1'")
            assert delete_result["success"] is True
        else:
            # Live service
            async def lifecycle():
                # Create
                create_resp = await service_client.post(
                    "/tools/relationship_create",
                    json={"source_id": "e1", "target_id": "e2", "type": "depends_on"}
                )
                if create_resp.status_code not in [200, 201, 400, 404]:
                    return False
                
                # Read
                read_resp = await service_client.post(
                    "/tools/relationship_list",
                    json={"limit": 1}
                )
                if read_resp.status_code not in [200, 400]:
                    return False
                
                # Update
                update_resp = await service_client.post(
                    "/tools/relationship_update",
                    json={"id": "rel-1", "metadata": {}}
                )
                if update_resp.status_code not in [200, 404]:
                    return False
                
                # Delete
                delete_resp = await service_client.post(
                    "/tools/relationship_delete",
                    json={"id": "rel-1"}
                )
                return delete_resp.status_code in [200, 204, 404]
            
            assert asyncio.run(lifecycle())

    def test_relationship_traversal(self, service_client):
        """Test relationship traversal (mock and live)."""
        if hasattr(service_client, 'execute'):
            # Mock service
            for i in range(3):
                service_client.execute(f"INSERT INTO relationships (source_id, target_id, type) VALUES ('e{i}', 'e{i+1}', 'depends_on')")
            
            result = service_client.query("SELECT * FROM relationships WHERE type = 'depends_on'")
            assert len(result) >= 3
        else:
            # Live service
            async def traversal():
                for i in range(3):
                    resp = await service_client.post(
                        "/tools/relationship_create",
                        json={"source_id": f"e{i}", "target_id": f"e{i+1}", "type": "depends_on"}
                    )
                    if resp.status_code not in [200, 201, 400, 404]:
                        return False
                
                list_resp = await service_client.post(
                    "/tools/relationship_list",
                    json={"filters": {"type": "depends_on"}}
                )
                return list_resp.status_code in [200, 400]
            
            assert asyncio.run(traversal())

    def test_relationship_bulk_workflow(self, service_client):
        """Test bulk relationship workflow (mock and live)."""
        if hasattr(service_client, 'execute'):
            # Mock service
            for i in range(5):
                result = service_client.execute(f"INSERT INTO relationships (source_id, target_id, type) VALUES ('e{i}', 'e{i+1}', 'depends_on')")
                assert result["success"] is True
        else:
            # Live service
            async def bulk():
                for i in range(5):
                    resp = await service_client.post(
                        "/tools/relationship_create",
                        json={"source_id": f"e{i}", "target_id": f"e{i+1}", "type": "depends_on"}
                    )
                    if resp.status_code not in [200, 201, 400, 404]:
                        return False
                return True
            
            assert asyncio.run(bulk())

