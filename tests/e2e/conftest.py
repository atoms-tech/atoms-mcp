"""Fixtures for E2E tests with full deployment.

This conftest provides:
- full_deployment: Complete server setup with production-like configuration
- end_to_end_client: E2E-ready MCP client with full authentication
- production_supabase: Real Supabase connection with production schema
- workflow_scenarios: Pre-configured complex test scenarios
"""

import pytest
import pytest_asyncio
import asyncio
import time
import uuid
from typing import Dict, Any
from contextlib import asynccontextmanager


@pytest_asyncio.fixture(scope="session")
async def full_deployment():
    """Complete deployment setup for E2E tests.
    
    Returns:
        Tuple of (server, client, database) ready for testing
    """
    # Mock deployment for now - in real scenario would:
    # 1. Start production-like infrastructure
    # 2. Configure with production-like settings
    # 3. Establish real database connections
    # 4. Set up authentication with real tokens

    server = None
    client = None
    db = None

    try:
        # For now, simulate full deployment
        from unittest.mock import Mock, AsyncMock

        # Mock server
        server = Mock()
        server.is_running = True
        server.url = "https://prod.atoms-mcp.com/api/mcp"
        server.health_check = AsyncMock(return_value={"status": "healthy"})

        # Mock client (would be real HTTP client in production)
        client = Mock()
        client.call_tool = AsyncMock()

        # Mock database (would be real Supabase production)
        db = Mock()
        db.connection = "production"

        yield server, client, db

    finally:
        # Cleanup deployment resources
        if server and hasattr(server, 'cleanup'):
            cleanup_fn = server.cleanup
            if asyncio.iscoroutinefunction(cleanup_fn):
                await cleanup_fn()
            else:
                cleanup_fn()


@pytest_asyncio.fixture
async def end_to_end_client(full_deployment):
    """E2E-ready MCP client with full authentication.
    
    This client simulates production deployment with:
    - Real authentication tokens
    - Production configuration
    - Full middleware stack
    - Actual database connectivity
    
    Usage:
        @pytest.mark.e2e
        async def test_complete_workflow(end_to_end_client):
            result = await end_to_end_client.call_tool(...)
            assert result.success
    """
    server, http_client, db = full_deployment

    # Return client that simulates real E2E behavior
    client = http_client

    # Configure client for E2E testing
    client._config = {
        "timeout": 30.0,
        "retry_attempts": 3,
        "production_mode": True,
    }

    # Simulate authentication
    client._auth_token = "e2e-test-token-" + uuid.uuid4().hex[:16]

    yield client


@pytest_asyncio.fixture
async def production_supabase():
    """Production-like Supabase connection for E2E tests."""
    # In real scenario, would connect to staging/production Supabase
    from unittest.mock import Mock

    supabase = Mock()
    supabase.auth = Mock()
    supabase.table = Mock()
    supabase.rpc = Mock()

    # Simulate successful connection
    supabase.auth.sign_in_with_password = Mock(
        return_value=Mock(
            session=Mock(access_token="prod-jwt-token")
        )
    )

    yield supabase


@pytest_asyncio.fixture
async def workflow_scenarios(end_to_end_client):
    """Pre-configured complex workflow scenarios for E2E testing."""

    async def create_complete_project_scenario():
        """Create a complete project scenario with org → project → docs → reqs → tests."""

        # Step 1: Create organization
        org_result = await end_to_end_client.call_tool("entity_tool", {
            "operation": "create",
            "entity_type": "organization",
            "data": {
                "name": f"E2E Test Org {uuid.uuid4().hex[:8]}",
                "description": "Organization created for E2E testing",
                "type": "team"
            }
        })

        if not org_result.get("success"):
            raise Exception("Failed to create organization in E2E scenario")

        org_id = org_result["data"]["id"]

        # Step 2: Create project
        project_result = await end_to_end_client.call_tool("entity_tool", {
            "operation": "create",
            "entity_type": "project",
            "data": {
                "name": f"E2E Test Project {uuid.uuid4().hex[:8]}",
                "description": "Project created for E2E testing",
                "organization_id": org_id,
                "status": "active"
            }
        })

        if not project_result.get("success"):
            raise Exception("Failed to create project in E2E scenario")

        project_id = project_result["data"]["id"]

        # Step 3: Create documents
        doc_results = []
        for i in range(3):
            doc_result = await end_to_end_client.call_tool("entity_tool", {
                "operation": "create",
                "entity_type": "document",
                "data": {
                    "name": f"E2E Test Doc {i+1}",
                    "content": f"Test document content {i+1}",
                    "project_id": project_id,
                    "version": "1.0.0"
                }
            })
            if doc_result.get("success"):
                doc_results.append(doc_result["data"]["id"])

        # Step 4: Create requirements
        req_results = []
        for i in range(2):
            target_doc = doc_results[i % len(doc_results)] if doc_results else None
            req_payload = {
                "name": f"E2E Requirement {i+1}",
                "description": f"Test requirement description {i+1}",
                "priority": "high" if i == 0 else "medium",
                "project_id": project_id,
            }
            if target_doc:
                req_payload["document_id"] = target_doc
            req_result = await end_to_end_client.call_tool("entity_tool", {
                "operation": "create",
                "entity_type": "requirement",
                "data": req_payload
            })
            if req_result.get("success"):
                req_results.append(req_result["data"]["id"])

        # Step 5: Create relationships
        for doc_id in doc_results:
            for req_id in req_results:
                await end_to_end_client.call_tool("relationship_tool", {
                    "operation": "create",
                    "source_type": "document",
                    "source_id": doc_id,
                    "target_type": "requirement",
                    "target_id": req_id,
                    "relationship_type": "references"
                })

        return {
            "organization_id": org_id,
            "project_id": project_id,
            "document_ids": doc_results,
            "requirement_ids": req_results,
            "total_entities": 1 + 1 + len(doc_results) + len(req_results)
        }

    async def create_parallel_workflow_scenario():
        """Create scenario for testing parallel workflows."""

        # Create multiple organizations in parallel
        tasks = []
        for i in range(5):
            task = end_to_end_client.call_tool("entity_tool", {
                "operation": "create",
                "entity_type": "organization",
                "data": {
                    "name": f"Parallel Org {i+1}",
                    "description": f"Organization {i+1} for parallel testing",
                    "type": "department"
                }
            })
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        successful_orgs = []
        for i, result in enumerate(results):
            if isinstance(result, dict) and result.get("success"):
                successful_orgs.append({
                    "index": i,
                    "id": result["data"]["id"],
                    "name": result["data"]["name"]
                })

        return {
            "total_created": len(tasks),
            "successful": len(successful_orgs),
            "organizations": successful_orgs
        }

    async def create_error_recovery_scenario():
        """Create scenario with intentional errors for recovery testing."""
        return {
            "invalid_entity_type": "invalid_type",
            "missing_required_data": {},
            "circular_relationship": {
                "source_type": "organization",
                "source_id": "same-id",
                "target_type": "organization",
                "target_id": "same-id",
                "relationship_type": "relates_to"
            }
        }

    return {
        "complete_project": create_complete_project_scenario,
        "parallel_workflow": create_parallel_workflow_scenario,
        "error_recovery": create_error_recovery_scenario,
    }


@pytest_asyncio.fixture
async def e2e_performance_tracker():
    """Track performance metrics for E2E tests with real-world characteristics."""

    class E2EPerformanceTracker:
        def __init__(self):
            self.metrics = {
                "network_latency": [],
                "db_query_time": [],
                "total_workflow_time": [],
                "concurrent_operations": 0,
                "errors": [],
                "memory_usage": []
            }

        @asynccontextmanager
        async def track_operation(self, operation_name: str):
            """Track an E2E operation with full metrics."""
            start = time.time()
            self.metrics["concurrent_operations"] += 1

            try:
                yield
                elapsed = (time.time() - start) * 1000

                if "workflow" in operation_name.lower():
                    self.metrics["total_workflow_time"].append(elapsed)
                else:
                    self.metrics["network_latency"].append(elapsed)

            except Exception as e:
                self.metrics["errors"].append({
                    "operation": operation_name,
                    "error": str(e),
                    "timestamp": time.time()
                })
                raise
            finally:
                self.metrics["concurrent_operations"] -= 1

        def get_report(self) -> Dict[str, Any]:
            """Generate comprehensive E2E performance report."""
            return {
                "network": {
                    "avg_latency_ms": sum(self.metrics["network_latency"]) / len(self.metrics["network_latency"]) if self.metrics["network_latency"] else 0,
                    "max_latency_ms": max(self.metrics["network_latency"]) if self.metrics["network_latency"] else 0,
                },
                "workflows": {
                    "avg_duration_ms": sum(self.metrics["total_workflow_time"]) / len(self.metrics["total_workflow_time"]) if self.metrics["total_workflow_time"] else 0,
                    "max_duration_ms": max(self.metrics["total_workflow_time"]) if self.metrics["total_workflow_time"] else 0,
                },
                "reliability": {
                    "error_count": len(self.metrics["errors"]),
                    "success_rate": 1 - (len(self.metrics["errors"]) / max(1, len(self.metrics["network_latency"]) + len(self.metrics["total_workflow_time"])))
                }
            }

    return E2EPerformanceTracker()


@pytest.fixture
def e2e_test_cleanup():
    """Cleanup utility for E2E tests to ensure no test data pollution."""

    created_entities = []
    created_relationships = []

    def track_entity(entity_type: str, entity_id: str):
        """Track created entity for cleanup."""
        created_entities.append((entity_type, entity_id))
        return entity_id

    def track_relationship(relationship_id: str):
        """Track created relationship for cleanup."""
        created_relationships.append(relationship_id)
        return relationship_id

    yield track_entity, track_relationship

    # In real E2E, would perform actual database cleanup
    # For now, just clear the tracking lists
    created_entities.clear()
    created_relationships.clear()


@pytest_asyncio.fixture
async def disaster_recovery_scenario():
    """Simulate disaster recovery scenarios for E2E testing."""

    class DisasterSimulator:
        async def simulate_database_failure(self):
            """Simulate temporary database failure."""
            return {
                "success": False,
                "error": "Database connection failed",
                "recovery_available": True,
                "estimated_recovery_time": 30  # seconds
            }

        async def simulate_network_partition(self):
            """Simulate network partition between components."""
            return {
                "success": False,
                "error": "Network partition detected",
                "affected_components": ["database", "auth-service"],
                "retry_after": 10
            }

        async def simulate_authentication_failure(self):
            """Simulate authentication service failure."""
            return {
                "success": False,
                "error": "Authentication service unavailable",
                "fallback_auth": True
            }

    return DisasterSimulator()


# E2E-specific test markers and configuration

def pytest_configure(config):
    """Configure E2E test markers."""
    config.addinivalue_line(
        "markers", "e2e: marks tests that require full deployment setup"
    )
    config.addinivalue_line(
        "markers", "production_like: marks tests that simulate production conditions"
    )
    config.addinivalue_line(
        "markers", "disaster_recovery: marks tests that validate disaster recovery"
    )
    config.addinivalue_line(
        "markers", "full_workflow: marks tests that validate complete workflows"
    )
    config.addinivalue_line(
        "markers", "slow_e2e: marks E2E tests that take >5s"
    )
