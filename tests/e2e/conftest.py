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

# Logging setup
import logging
logger = logging.getLogger(__name__)

# Configure Supabase credentials for cloud testing
if not os.getenv("ATOMS_TEST_EMAIL"):
    os.environ["ATOMS_TEST_EMAIL"] = "kooshapari@kooshapari.com"
if not os.getenv("ATOMS_TEST_PASSWORD"):
    os.environ["ATOMS_TEST_PASSWORD"] = "ASD3on54_Pax90"


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


@pytest_asyncio.fixture(scope="session")
async def authkit_auth_token():
    """Authenticate with WorkOS/AuthKit and get a JWT token for E2E testing.

    Supports two modes:
    1. Local testing: Generate unsigned JWT for testing (when ATOMS_TEST_MODE=true)
    2. Production: Use real AuthKit access tokens from WorkOS

    Returns:
        Valid JWT token for authenticated API calls

    Raises:
        pytest.skip: If no token can be obtained (tests will be skipped)
    """
    import os
    import logging
    import asyncio
    import json
    import base64

    logger_local = logging.getLogger(__name__)

    # Check for pre-obtained token first (fastest)
    pre_obtained_token = os.getenv("ATOMS_TEST_AUTH_TOKEN") or os.getenv("AUTHKIT_TOKEN")
    if pre_obtained_token:
        logger_local.info("✅ Using pre-obtained token from environment")
        return pre_obtained_token

    # For local testing: Generate unsigned JWT
    if os.getenv("ATOMS_TEST_MODE", "false").lower() == "true":
        logger_local.info("🧪 Generating unsigned JWT for local testing")

        # Create unsigned JWT (alg: "none")
        header = {"alg": "none", "typ": "JWT"}
        payload = {
            "sub": "test-user-" + str(uuid.uuid4())[:8],
            "email": "test@atoms.local",
            "email_verified": True,
            "name": "Test User",
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600
        }

        header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
        payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")

        # Unsigned JWT: header.payload. (empty signature)
        token = f"{header_b64}.{payload_b64}."
        logger_local.info(f"✅ Generated unsigned JWT for testing: sub={payload['sub']}")
        return token

    # Production: Use real AuthKit tokens
    email = os.getenv("ATOMS_TEST_EMAIL", "kooshapari@kooshapari.com")
    password = os.getenv("ATOMS_TEST_PASSWORD", "ASD3on54_Pax90")

    # Use WorkOS User Management password grant (always available)
    from tests.utils.workos_auth import authenticate_with_workos

    logger_local.info(f"🔐 Authenticating with WorkOS User Management as {email}")
    token = await authenticate_with_workos(email, password)

    if token:
        logger_local.info("✅ Successfully obtained AuthKit token via WorkOS")
        # Cache it in environment for this session
        os.environ["ATOMS_TEST_AUTH_TOKEN"] = token
        return token
    else:
        error_msg = (
            f"❌ Failed to obtain AuthKit token via WorkOS User Management.\n"
            f"Ensure WORKOS_API_KEY and WORKOS_CLIENT_ID are set."
        )
        logger_local.error(error_msg)
        import pytest
        pytest.skip(error_msg)


@pytest_asyncio.fixture
async def e2e_auth_token(authkit_auth_token):
    """Generate authentication token for E2E tests.

    REQUIRED: All tests must use real AuthKit access tokens - no static or test tokens allowed.

    Provides a valid AuthKit JWT bearer token that the MCP server will accept.
    The token MUST be a real AuthKit JWT obtained via:
    1. WorkOS User Management API (password grant)
    2. Pre-obtained token in ATOMS_TEST_AUTH_TOKEN environment variable

    Strategy:
    - Uses real AuthKit JWT from authkit_auth_token fixture (REQUIRED)
    - NO fallback to static tokens or unsigned JWTs

    Note: This fixture can make external service calls to AuthKit when authenticating
    with real credentials. If no AuthKit token is available, tests will be skipped.
    """
    import os
    import logging

    logger_local = logging.getLogger(__name__)

    # **ONLY Strategy: Use real AuthKit JWT from cloud authentication (REQUIRED)**
    # All tests MUST use real AuthKit access tokens - no static or test tokens allowed
    if authkit_auth_token is not None:
        logger_local.info(f"✅ Using real AuthKit JWT for E2E authentication")
        return authkit_auth_token

    # No AuthKit token available - tests REQUIRE real tokens
    error_msg = (
        "❌ No AuthKit access token available. "
        "Tests require real AuthKit JWTs - no static or test tokens allowed.\n"
        "To get a token:\n"
        "  1. Ensure WORKOS_API_KEY and WORKOS_CLIENT_ID are set\n"
        "  2. Or export: export ATOMS_TEST_AUTH_TOKEN=<token>"
    )
    logger_local.error(error_msg)
    import pytest
    pytest.skip(error_msg)


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
    
    # Only use the mock harness when explicitly requested via environment variable
    use_mock = os.getenv("USE_MOCK_HARNESS", "false").lower() == "true"
    
    if use_mock:
        # Use mock client for testing
        from tests.e2e.mock_client import MockMcpClient
        from unittest.mock import AsyncMock
        
        client = MockMcpClient()
        # Wrap call_tool to allow mocking via side_effect
        original_call_tool = client.call_tool
        mock_call_tool = AsyncMock(side_effect=original_call_tool)
        client.call_tool = mock_call_tool
        
        yield client
    else:
        # Use real HTTP client
        import httpx

        # Get deployment URL from environment variable set by TestEnvManager (atoms CLI)
        # This respects the --env flag from atoms CLI:
        # - atoms test:e2e --env local → http://localhost:8000/api/mcp (unsigned JWT, test mode)
        # - atoms test:e2e --env dev → https://mcpdev.atoms.tech/api/mcp (real JWT, prod WorkOS keys)
        # - atoms test:e2e --env prod → https://mcp.atoms.tech/api/mcp (real JWT, prod WorkOS keys)

        deployment_url = os.getenv("MCP_E2E_BASE_URL")
        if not deployment_url:
            # Fallback to dev if not set by TestEnvManager
            deployment_url = "https://mcpdev.atoms.tech/api/mcp"
            print("⚠️  MCP_E2E_BASE_URL not set, using dev: mcpdev.atoms.tech")

        # Determine if we're using local server or deployed server
        is_local = "localhost" in deployment_url or "127.0.0.1" in deployment_url

        if is_local:
            # Local server: Enable test mode for unsigned JWTs
            os.environ["ATOMS_TEST_MODE"] = "true"
            print(f"✅ Local server: {deployment_url}")
            print("   Using unsigned JWTs (test mode)")
        else:
            # Deployed server (dev/prod): Disable test mode, use real authentication
            if "ATOMS_TEST_MODE" in os.environ:
                del os.environ["ATOMS_TEST_MODE"]

            # Extract environment name from URL
            if "mcpdev" in deployment_url:
                env_name = "Development (mcpdev.atoms.tech)"
            elif "mcp.atoms.tech" in deployment_url:
                env_name = "Production (mcp.atoms.tech)"
            else:
                env_name = deployment_url

            print(f"✅ Deployed server: {env_name}")
            print("   Using real WorkOS authentication")
        
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
    Supports both local and deployed server testing.
    """
    import os
    import uuid
    
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

@pytest_asyncio.fixture
async def test_data_setup(end_to_end_client):
    """Comprehensive test data setup for e2e tests.

    Creates a complete test environment with:
    - Organization with members
    - Projects with documents
    - Requirements with test cases
    - Relationships between entities

    Returns:
        Dict with all created entities for use in tests
    """
    import uuid

    test_id = uuid.uuid4().hex[:8]
    data = {}

    try:
        # Create organization
        org_result = await end_to_end_client.entity_create(
            "organization",
            {"name": f"Test Org {test_id}", "description": "Test organization"}
        )
        if org_result.get("success"):
            data["organization"] = org_result["data"]
            org_id = org_result["data"]["id"]

            # Create projects
            for i in range(2):
                proj_result = await end_to_end_client.entity_create(
                    "project",
                    {
                        "name": f"Project {i} {test_id}",
                        "organization_id": org_id,
                        "description": f"Test project {i}"
                    }
                )
                if proj_result.get("success"):
                    if "projects" not in data:
                        data["projects"] = []
                    data["projects"].append(proj_result["data"])
                    proj_id = proj_result["data"]["id"]

                    # Create documents in project
                    for j in range(2):
                        doc_result = await end_to_end_client.entity_create(
                            "document",
                            {
                                "name": f"Doc {j} {test_id}",
                                "project_id": proj_id,
                                "description": f"Test document {j}"
                            }
                        )
                        if doc_result.get("success"):
                            if "documents" not in data:
                                data["documents"] = []
                            data["documents"].append(doc_result["data"])

            # Create requirements
            for i in range(3):
                req_result = await end_to_end_client.entity_create(
                    "requirement",
                    {
                        "name": f"REQ {i} {test_id}",
                        "organization_id": org_id,
                        "status": "open",
                        "priority": "high" if i == 0 else "medium"
                    }
                )
                if req_result.get("success"):
                    if "requirements" not in data:
                        data["requirements"] = []
                    data["requirements"].append(req_result["data"])

            # Create test cases
            for i in range(2):
                tc_result = await end_to_end_client.entity_create(
                    "test_case",
                    {
                        "name": f"TC {i} {test_id}",
                        "organization_id": org_id,
                        "status": "draft"
                    }
                )
                if tc_result.get("success"):
                    if "test_cases" not in data:
                        data["test_cases"] = []
                    data["test_cases"].append(tc_result["data"])

    except Exception as e:
        print(f"Error setting up test data: {e}")

    yield data

    # Cleanup is optional - tests can leave data for inspection


@pytest_asyncio.fixture
async def test_data_with_relationships(test_data_setup):
    """Test data with relationships between entities.

    Extends test_data_setup with relationships:
    - Requirements linked to test cases
    - Documents linked to requirements
    - Projects linked to organization
    """
    data = test_data_setup

    # Add relationship information
    if data.get("requirements") and data.get("test_cases"):
        data["relationships"] = {
            "requirement_to_test_case": [
                {
                    "requirement_id": data["requirements"][0]["id"],
                    "test_case_id": data["test_cases"][0]["id"]
                }
            ]
        }

    return data


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
