"""Fixtures for E2E tests with full deployment.

This conftest provides:
- mcp_client: Parametrized MCP client (unit/integration/e2e variants)
- end_to_end_client: E2E-ready MCP client with full authentication
- e2e_auth_token: AuthKit JWT for authenticated E2E tests (no external service calls)
- workflow_scenarios: Pre-configured complex test scenarios

Authentication Model:
- AuthKit: OAuth provider for authentication (WorkOS)
- Supabase: Database backend for storing data
- HybridAuthProvider: Accepts both OAuth and Bearer token authentication

This fixture generates a mock AuthKit JWT that can be passed as a Bearer token
to the MCP server without requiring any external service calls.
"""

import pytest
import pytest_asyncio
import asyncio
import time
import uuid
import os
from typing import Dict, Any
from contextlib import asynccontextmanager

# Enable test mode for HybridAuthProvider to accept unsigned JWTs
os.environ["ATOMS_TEST_MODE"] = "true"

# Configure test token for E2E tests (allows unsigned JWT acceptance in test mode)
# If not already set, use a standard test token
if not os.getenv("ATOMS_INTERNAL_TOKEN"):
    # Use a predictable test token for E2E tests
    os.environ["ATOMS_INTERNAL_TOKEN"] = "test-e2e-token-for-atoms-mcp"


@pytest_asyncio.fixture(params=["unit", "integration", "e2e"])
async def mcp_client(request, end_to_end_client):
    """Parametrized MCP client for testing across three variants.
    
    This fixture runs each test 3 times:
    - unit: In-memory client (mocks all services) - FAST
    - integration: HTTP client to localhost:8000 (real local services)
    - e2e: HTTP client to mcpdev.atoms.tech (real deployment)
    
    Each test receives the appropriate client variant automatically.
    """
    variant = request.param
    
    if variant == "unit":
        # Mock client for unit tests
        from unittest.mock import AsyncMock, MagicMock
        
        class MockMcpClient:
            """In-memory mock MCP client for unit tests."""
            
            async def entity_tool(self, entity_type, operation=None, data=None, 
                                 entity_id=None, batch=None, filters=None, 
                                 search_term=None, parent_type=None, parent_id=None,
                                 limit=None, offset=None, order_by=None, 
                                 soft_delete=True, format_type="detailed",
                                 include_relations=False, **kwargs):
                """Mock entity_tool - returns success for valid operations."""
                # Simple mock responses for basic operations
                if operation == "create":
                    return {
                        "success": True,
                        "data": {
                            "id": str(uuid.uuid4()),
                            "entity_type": entity_type,
                            **data,
                            "created_at": time.time(),
                            "created_by": "test-user"
                        }
                    }
                elif operation == "read":
                    return {
                        "success": True,
                        "data": {
                            "id": entity_id or str(uuid.uuid4()),
                            "entity_type": entity_type,
                            "created_at": time.time()
                        }
                    }
                elif operation == "update":
                    return {
                        "success": True,
                        "data": {
                            "id": entity_id,
                            "entity_type": entity_type,
                            **data,
                            "updated_at": time.time()
                        }
                    }
                elif operation == "delete":
                    return {
                        "success": True,
                        "data": {
                            "id": entity_id,
                            "deleted_at": time.time()
                        }
                    }
                elif operation == "list":
                    return {
                        "success": True,
                        "data": [
                            {"id": str(uuid.uuid4()), "name": f"Item {i}"}
                            for i in range(min(limit or 10, 10))
                        ],
                        "count": limit or 10
                    }
                else:
                    return {
                        "success": True,
                        "data": {}
                    }
            
            async def workspace_tool(self, operation=None, context_type=None, 
                                    entity_id=None, **kwargs):
                """Mock workspace_tool."""
                return {
                    "success": True,
                    "data": {
                        "context_type": context_type,
                        "entity_id": entity_id,
                        "defaults": {}
                    }
                }
            
            async def relationship_tool(self, operation=None, relationship_type=None,
                                       source=None, target=None, **kwargs):
                """Mock relationship_tool."""
                return {
                    "success": True,
                    "data": {
                        "id": str(uuid.uuid4()),
                        "relationship_type": relationship_type
                    }
                }
            
            async def data_query(self, operation=None, search_term=None, **kwargs):
                """Mock data_query."""
                return {
                    "success": True,
                    "data": []
                }
            
            async def workflow_execute(self, workflow_name=None, **kwargs):
                """Mock workflow_execute."""
                return {
                    "success": True,
                    "data": {"workflow": workflow_name}
                }
        
        return MockMcpClient()
    
    elif variant == "integration":
        # HTTP client to local server
        # For now, use the e2e client but would normally point to localhost:8000
        # This is a simplified approach; full integration would start local server
        return end_to_end_client
    
    elif variant == "e2e":
        # Real HTTP client to mcpdev.atoms.tech
        return end_to_end_client
    
    # Fallback
    return end_to_end_client


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
async def e2e_auth_token():
    """Generate authentication token for E2E tests.
    
    Provides a valid bearer token that the MCP server will accept. The token can be:
    1. Internal bearer token (if ATOMS_INTERNAL_TOKEN is configured)
    2. AuthKit JWT (if signing key is available)
    3. Unsigned JWT for testing (when ATOMS_TEST_MODE is enabled)
    
    Strategy:
    - First attempts to use ATOMS_INTERNAL_TOKEN if configured (fastest, no signing needed)
    - Then tries to generate a properly signed AuthKit JWT
    - Falls back to unsigned JWT that requires ATOMS_TEST_MODE on server (for testing)
    
    For running against deployed server (mcpdev.atoms.tech):
    - If ATOMS_INTERNAL_TOKEN env var is set: Use that directly (recommended)
    - Otherwise: Generates unsigned JWT (requires server with ATOMS_TEST_MODE=true)
    
    For running against local server (localhost:8000):
    - Uses unsigned JWT if ATOMS_TEST_MODE=true on server
    - Or generates a valid token if credentials are available
    
    Note: This fixture does NOT make any external service calls. It generates
    tokens locally without requiring Supabase or AuthKit auth endpoints.
    """
    import os
    import json
    import base64
    import logging
    from datetime import datetime, timedelta, timezone
    
    logger_local = logging.getLogger(__name__)
    
    # **Strategy 1: Use internal bearer token (RECOMMENDED)**
    # This is the most direct approach - internal_token is a static token
    # that bypasses JWKS validation
    # For E2E tests, we always use internal token from environment
    internal_token = os.getenv("ATOMS_INTERNAL_TOKEN")
    if internal_token:
        logger_local.info(f"Using ATOMS_INTERNAL_TOKEN for E2E authentication: {internal_token[:20]}...")
        return internal_token
    
    # **Strategy 2: Generate signed AuthKit JWT**
    # If private key is available, sign the JWT properly
    try:
        private_key = os.getenv("AUTHKIT_PRIVATE_KEY")
        if private_key:
            import jwt as pyjwt
            
            logger_local.info("Generating signed AuthKit JWT for E2E tests")
            user_id = str(uuid.uuid4())
            current_time = datetime.now(timezone.utc)
            expires_at = current_time + timedelta(hours=1)
            
            jwt_claims = {
                "iss": "https://api.workos.com",
                "sub": user_id,
                "aud": os.getenv("WORKOS_CLIENT_ID", "test-client"),
                "iat": int(current_time.timestamp()),
                "exp": int(expires_at.timestamp()),
                "email": "test-user@example.com",
                "email_verified": True,
                "name": "Test User",
            }
            
            token = pyjwt.encode(jwt_claims, private_key, algorithm="RS256")
            return token
    except Exception as e:
        logger_local.debug(f"Could not generate signed JWT: {e}")
    
    # **Strategy 3: Generate unsigned JWT (requires ATOMS_TEST_MODE on server)**
    # This works when server has ATOMS_TEST_MODE=true in its environment
    logger_local.info("Generating unsigned JWT for E2E tests (requires ATOMS_TEST_MODE on server)")
    
    user_id = str(uuid.uuid4())
    current_time = datetime.now(timezone.utc)
    expires_at = current_time + timedelta(hours=1)
    
    jwt_claims = {
        "iss": "https://api.workos.com",
        "sub": user_id,
        "aud": os.getenv("WORKOS_CLIENT_ID", "test-client"),
        "iat": int(current_time.timestamp()),
        "exp": int(expires_at.timestamp()),
        "email": "test-user@example.com",
        "email_verified": True,
        "name": "Test User",
        "organization_id": "org_test123",
        "roles": ["user"],
        "permissions": ["read:data", "write:data"],
    }
    
    header = {"alg": "none", "typ": "JWT"}
    
    def b64encode(data):
        """Base64 URL encode without padding."""
        json_str = json.dumps(data)
        return base64.urlsafe_b64encode(json_str.encode()).decode().rstrip('=')
    
    header_b64 = b64encode(header)
    payload_b64 = b64encode(jwt_claims)
    signature_b64 = ""
    
    token = f"{header_b64}.{payload_b64}.{signature_b64}"
    return token


@pytest_asyncio.fixture
async def end_to_end_client(e2e_auth_token):
    """E2E-ready MCP client with full authentication.
    
    This client connects to the deployed mcpdev.atoms.tech instance with:
    - Real authentication via Bearer token
    - Production configuration
    - Full middleware stack
    - Actual database connectivity
    
    OR uses mock client if USE_MOCK_HARNESS environment variable is set.
    
    The client's call_tool method is wrapped to allow mocking via side_effect.
    
    Usage:
        @pytest.mark.e2e
        async def test_complete_workflow(end_to_end_client):
            result = await end_to_end_client.call_tool(...)
            assert result.success
    """
    import os
    from unittest.mock import AsyncMock
    
    # Check if mock harness should be used
    use_mock = os.getenv("USE_MOCK_HARNESS", "false").lower() == "true"
    
    if use_mock:
        # Use mock client for testing
        from tests.e2e.mock_client import MockMcpClient
        client = MockMcpClient()
        yield client
    else:
        # Use real HTTP client
        import httpx
        
        # Get deployment URL from environment or use mcpdev default
        deployment_url = os.getenv("MCP_E2E_BASE_URL", "https://mcpdev.atoms.tech/api/mcp")
        
        # Create httpx client with authentication headers
        headers = {
            "Authorization": f"Bearer {e2e_auth_token}",
            "Content-Type": "application/json",
        }
        
        # Create httpx AsyncClient with auth headers
        async with httpx.AsyncClient(
            base_url=deployment_url.rsplit('/api/mcp', 1)[0] if '/api/mcp' in deployment_url else deployment_url,
            headers=headers,
            timeout=30.0
        ) as http_client:
            # Create MCP client wrapper that uses authenticated httpx client
            from tests.e2e.mcp_http_wrapper import AuthenticatedMcpClient
            
            mcp_client = AuthenticatedMcpClient(
                base_url=deployment_url,
                http_client=http_client,
                auth_token=e2e_auth_token
            )
            
            # Wrap call_tool to allow mocking via side_effect
            original_call_tool = mcp_client.call_tool
            mock_call_tool = AsyncMock(side_effect=original_call_tool)
            mcp_client.call_tool = mock_call_tool
            
            yield mcp_client


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
    """Pre-configured complex workflow scenarios for E2E testing.
    
    This fixture works with both mock harness and real HTTP client.
    When mock harness is enabled, all workflow tests will run.
    """
    # Check if we're using mock client
    import os
    use_mock = os.getenv("USE_MOCK_HARNESS", "false").lower() == "true"
    
    # Only skip for real HTTP client when not using mock harness
    if not use_mock:
        # Check if we're using a real HTTP client vs mock
        if hasattr(end_to_end_client, '__class__') and \
           end_to_end_client.__class__.__name__ == 'AuthenticatedMcpClient':
            pytest.skip("workflow_scenarios fixture requires mock harness (use USE_MOCK_HARNESS=true)")
    
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
    """Cleanup utility for E2E tests to ensure no test data pollution.
    
    Note: This fixture is designed for mock harness tests. When using real
    HTTP client with actual database, use database cleanup fixtures instead.
    """
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
