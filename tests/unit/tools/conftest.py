"""Fixtures for unit tool tests using in-memory FastMCP Client.

This conftest provides:
- mcp_server: Session-scoped FastMCP server with registered tools
- mcp_client_inmemory: In-memory async client for fast deterministic tests
- mcp_client: Parametrized client fixture (canonical, supports unit/integration/e2e)
- call_mcp: Helper to call tools with timing info (uses mcp_client)
- Parametrization helpers for entity types, operations, scenarios
"""

import pytest
import pytest_asyncio
import time
from unittest.mock import AsyncMock, MagicMock
from typing import List, Dict, Any, Tuple


class ResultWrapper:
    """Wraps a dict result to provide both dict and attribute access.
    
    This allows tests to use either:
    - result["success"] (dict-style)
    - result.success (attribute-style)
    """
    def __init__(self, data: Dict[str, Any]):
        self._data = data if isinstance(data, dict) else {}
    
    def __getitem__(self, key):
        return self._data[key]
    
    def __getattr__(self, name):
        if name.startswith('_'):
            return object.__getattribute__(self, name)
        return self._data.get(name)
    
    def __setitem__(self, key, value):
        self._data[key] = value
    
    def __setattr__(self, name, value):
        if name.startswith('_'):
            object.__setattr__(self, name, value)
        else:
            self._data[name] = value
    
    def get(self, key, default=None):
        return self._data.get(key, default)
    
    def __contains__(self, key):
        return key in self._data
    
    def __repr__(self):
        return repr(self._data)
    
    def __str__(self):
        return str(self._data)


def unwrap_mcp_response(response):
    """Extract data and success flag from FastMCP client response.
    
    FastMCP client may return either:
    - MCPResult(data={'success': ..., 'data': ...})
    - dict {'success': ..., 'data': ...}
    - ResultWrapper({...})
    - list [...] (for search results)
    
    Returns tuple (success: bool, data: dict|list)
    """
    # Handle list responses (e.g., search results)
    if isinstance(response, list):
        return True, response
    
    # Handle dict-like objects (dict, ResultWrapper, or object with .get())
    if isinstance(response, dict) or hasattr(response, 'get'):
        # Try to extract nested structure
        if hasattr(response, "data") and isinstance(getattr(response, "data"), dict):
            # MCPResult object with nested data
            inner = response.data
            return inner.get("success", False), inner.get("data", {})
        else:
            # Direct dict or ResultWrapper - check for success field
            return response.get("success", False), response.get("data", response)
    
    # Fallback - wrap unknown response
    return False, response


# Note: mcp_server moved to fast_mcp_server above

@pytest_asyncio.fixture
async def mcp_client_inmemory(fast_mcp_server):
    """Provide in-memory MCP client for fast unit tests.
    
    Usage:
        @pytest.mark.unit
        async def test_entity_creation(mcp_client_inmemory):
            result = await mcp_client_inmemory.call_tool(
                "entity_tool",
                {"operation": "create", "entity_type": "organization", ...}
            )
            assert result.success
    
    Benefits:
        - Deterministic (no network)
        - Fast (<1ms per call)
        - Full debugger support
        - No external service dependencies
    """
    from fastmcp import Client

    async with Client(fast_mcp_server) as client:
        yield client


@pytest.fixture(
    params=[
        pytest.param("mcp_client_inmemory", marks=pytest.mark.unit, id="unit"),
    ]
)
def mcp_client(request):
    """Parametrized client fixture for unit test variants.
    
    For now, unit tests only use in-memory client. This fixture allows
    tests to be written once and run with parametrization when integration/e2e
    fixtures are added to conftest.
    
    Canonical fixture: use this instead of mcp_client_inmemory directly in tests.
    
    Usage:
        async def test_entity_creation(mcp_client):
            result = await mcp_client.call_tool(
                "entity_tool",
                {"operation": "create", "entity_type": "organization", ...}
            )
            assert result.success
    
    To add integration/e2e variants:
        1. Add mcp_client_http fixture to tests/integration/conftest.py
        2. Add end_to_end_client fixture to tests/e2e/conftest.py
        3. Update this parametrize to include both
        4. Conftest will auto-parametrize based on test location
    """
    return request.getfixturevalue(request.param)


@pytest.fixture
def call_mcp(mcp_client):
    """Return a helper that invokes MCP tools with timing info (uses parametrized mcp_client).
    
    This is the canonical fixture for calling tools. It uses the parametrized
    mcp_client which supports unit/integration/e2e variants.

    Returns:
        async callable: async function(tool_name: str, params: Dict) -> Tuple[ResultWrapper, float]
                       Returns (result_wrapper, duration_ms)
                       where result_wrapper supports both dict and attribute access
    
    Usage:
        async def test_something(call_mcp):
            result, duration_ms = await call_mcp("entity_tool", {...})
            assert result["success"]  # dict-style
            assert result.success     # attribute-style
    """
    async def _call(tool_name: str, params: Dict[str, Any]) -> Tuple[ResultWrapper, float]:
        start_time = time.perf_counter()
        try:
            res = await mcp_client.call_tool(tool_name, params)
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Normalize to dict for backward compatibility
            if isinstance(res, dict):  # if underlying client already returns dict
                return ResultWrapper(res), duration_ms

            # FastMCP CallToolResult has is_error, data, and content
            # data field contains the tool's response dict with {success, data, error, ...}
            response_dict = getattr(res, "data", None)

            if not isinstance(response_dict, dict):
                response_dict = {"success": False, "error": "Invalid response from tool"}

            # Return the tool's response wrapped for both dict and attribute access
            return ResultWrapper(response_dict), duration_ms
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            return ResultWrapper({"success": False, "error": str(e)}), duration_ms

    return _call


# Removed duplicate mcp_client_inmemory fixture - using fast_mcp_server version above
    # Duplicate function removed - using fast_mcp_server version above


@pytest.fixture
def mcp_server_mock():
    """Mock MCP server for testing error conditions."""
    mock_server = AsyncMock()
    mock_server.call_tool = AsyncMock()
    mock_server.list_tools = MagicMock()
    return mock_server


# Test Data Factories

@pytest.fixture
def entity_factory():
    """Factory for generating test entities with context."""
    from tests.framework.test_data_generators import DataGeneratorHelper
    return DataGeneratorHelper()

@pytest.fixture
def test_data_fixtures(entity_factory):
    """Provides a collection of entity data for testing."""
    return {
        "organizations": [
            entity_factory.create_entity_data("organization", {"name": "basic"}),
            entity_factory.create_entity_data("organization", {"name": "with_type_team"}),
        ],
        "projects": [
            entity_factory.create_entity_data("project", {"name": "with_auto_context"}),
            entity_factory.create_entity_data("project", {"name": "with_explicit_id"}),
        ],
        "documents": [
            entity_factory.create_entity_data("document", {"name": "basic"}),
            entity_factory.create_entity_data("document", {"name": "with_auto_context"}),
        ],
        "requirements": [
            entity_factory.create_entity_data("requirement", {"name": "basic"}),
            entity_factory.create_entity_data("requirement", {"name": "with_high_priority"}),
        ],
    }

# Test Helper Fixtures

# Monkeypatch auth and permission checks for unit tests
import sys
import os

# Set test mode to skip actual auth/permission checks
os.environ["ATOMS_TEST_MODE"] = "true"
# Set Supabase to mock mode for unit tests
os.environ["ATOMS_SUPABASE_MODE"] = "mock"
os.environ["ATOMS_SERVICE_MODE"] = "mock"
# Set dummy Supabase env vars to prevent get_supabase() from raising errors
# These are only used if code paths bypass the factory and call get_supabase() directly
os.environ.setdefault("NEXT_PUBLIC_SUPABASE_URL", "https://mock.supabase.co")
os.environ.setdefault("NEXT_PUBLIC_SUPABASE_ANON_KEY", "mock-anon-key-for-testing")

@pytest.fixture(scope="session", autouse=True)
def mock_auth_for_unit_tests():
    """Mock authentication and permission checks for unit tests.
    
    This ensures unit tests don't require actual auth tokens or database access.
    """
    from unittest.mock import AsyncMock, patch, MagicMock
    from tools.base import ToolBase
    
    # Create mock auth that accepts test tokens
    async def mock_validate_auth(self, auth_token: str) -> Dict[str, Any]:
        """Mock auth validation for testing."""
        # For unit tests, any token is valid and returns a mock user context
        user_info = {
            "user_id": "12345678-1234-1234-1234-123456789012",
            "username": "test_user",
            "email": "test_user@example.com",
            "access_token": "mock-token-for-testing",
            "workspace_memberships": {
                "default": {"role": "admin", "status": "active"}
            },
            "is_system_admin": True  # Admin in tests to bypass permission checks
        }
        # Cache user context for this operation (same as real implementation)
        self._user_context = user_info
        return user_info
    
    # Patch the _validate_auth method
    ToolBase._validate_auth = mock_validate_auth
    
    # Patch get_supabase() to return a mock client in test mode
    # This prevents errors when code paths bypass the factory and call get_supabase() directly
    def mock_get_supabase(access_token=None):
        """Mock Supabase client for unit tests."""
        mock_client = MagicMock()
        # Configure mock client to return empty results by default
        mock_client.table.return_value.select.return_value.execute.return_value.data = []
        mock_client.table.return_value.insert.return_value.execute.return_value.data = {}
        mock_client.table.return_value.update.return_value.execute.return_value.data = {}
        mock_client.table.return_value.delete.return_value.execute.return_value.data = {}
        return mock_client
    
    # Patch get_supabase in both possible import locations
    # Use start() and stop() to keep patches active for the entire test session
    patches = [
        patch('supabase_client.get_supabase', side_effect=mock_get_supabase),
        patch('infrastructure.supabase_db.get_supabase', side_effect=mock_get_supabase),
        patch('infrastructure.supabase_storage.get_supabase', side_effect=mock_get_supabase),
        patch('infrastructure.supabase_realtime.get_supabase', side_effect=mock_get_supabase),
    ]
    
    # Start all patches
    for p in patches:
        p.start()
    
    try:
        yield
    finally:
        # Stop all patches
        for p in patches:
            p.stop()

@pytest.fixture
def fast_mcp_server():
    """Configure FastMCP server for optimal test performance."""
    from fastmcp import FastMCP
    from tools import (
        workspace_operation,
        entity_operation,
        relationship_operation,
        workflow_execute,
        data_query,
    )

    server = FastMCP("atoms-test-server")

    # Register tools manually for testing (same as server.py but without auth)
    @server.tool(tags={"workspace", "context"})
    async def workspace_tool(
        operation: str,
        context_type: str = None,
        entity_id: str = None,
        organization_id: str = None,
        project_id: str = None,
        include_hierarchy: bool = None,
        include_members: bool = None,
        include_recent_activity: bool = None,
        defaults: dict = None,
        view_state: dict = None,
        entity_type: str = None,
        format_type: str = "detailed",
        limit: int = None,
        offset: int = None,
    ) -> dict:
        """Manage workspace context and get smart defaults."""
        try:
            # Handle alternative parameters for set_context (test compatibility)
            final_context_type = context_type
            final_entity_id = entity_id

            if operation == "set_context":
                if organization_id:
                    final_context_type = "organization"
                    final_entity_id = organization_id
                elif project_id:
                    final_context_type = "project"
                    final_entity_id = project_id

            # For testing, use a mock auth token
            return await workspace_operation(
                auth_token="test-token",
                operation=operation,
                context_type=final_context_type,
                entity_id=final_entity_id,
                include_hierarchy=include_hierarchy,
                include_members=include_members,
                include_recent_activity=include_recent_activity,
                defaults=defaults,
                view_state=view_state,
                entity_type=entity_type,
                format_type=format_type,
                limit=limit,
                offset=offset,
            )
        except Exception as e:
            return {"success": False, "error": str(e), "operation": operation}

    @server.tool(tags={"entity", "crud"})
    async def entity_tool(
        entity_type: str,
        operation: str = None,
        data: dict = None,
        filters: dict = None,
        entity_id: str = None,
        include_relations: bool = False,
        batch: list = None,
        search_term: str = None,
        query: str = None,  # Alias for search_term
        parent_type: str = None,
        parent_id: str = None,
        limit: int = None,
        offset: int = None,
        order_by: str = None,
        format_type: str = "detailed",
        soft_delete: bool = True,
        pagination: dict = None,
        filter_list: list = None,
        sort_list: list = None,
        entity_ids: list = None,
        version: int = None,
        workflow_id: str = None,
        input_data: dict = None,
    ) -> dict:
        """Entity CRUD operations."""
        try:
            # Use query as alias for search_term if search_term not provided
            search_term_final = search_term or query
            return await entity_operation(
                auth_token="test-token",
                entity_type=entity_type,
                operation=operation,
                data=data,
                filters=filters,
                entity_id=entity_id,
                include_relations=include_relations,
                batch=batch,
                search_term=search_term_final,
                parent_type=parent_type,
                parent_id=parent_id,
                limit=limit,
                offset=offset,
                order_by=order_by,
                format_type=format_type,
                soft_delete=soft_delete,
                pagination=pagination,
                filter_list=filter_list,
                sort_list=sort_list,
                entity_ids=entity_ids,
                version=version,
                workflow_id=workflow_id,
                input_data=input_data,
            )
        except Exception as e:
            return {"success": False, "error": str(e), "operation": operation}

    @server.tool(tags={"relationship", "association"})
    async def relationship_tool(
        operation: str,
        relationship_type: str,
        source: dict,
        target: dict = None,
        metadata: dict = None,
        filters: dict = None,
        source_context: str = None,
        soft_delete: bool = True,
        limit: int = 100,
        offset: int = 0,
        format_type: str = "detailed",
    ) -> dict:
        """Manage relationships between entities."""
        try:
            return await relationship_operation(
                auth_token="test-token",
                operation=operation,
                relationship_type=relationship_type,
                source=source,
                target=target,
                metadata=metadata,
                filters=filters,
                source_context=source_context,
                soft_delete=soft_delete,
                limit=limit,
                offset=offset,
                format_type=format_type,
            )
        except Exception as e:
            return {"success": False, "error": str(e), "operation": operation, "relationship_type": relationship_type}

    @server.tool(tags={"workflow", "automation"})
    async def workflow_tool(
        workflow: str,
        parameters: dict,
        transaction_mode: bool = True,
        format_type: str = "detailed",
    ) -> dict:
        """Execute complex multi-step workflows."""
        try:
            return await workflow_execute(
                auth_token="test-token",
                workflow=workflow,
                parameters=parameters,
                transaction_mode=transaction_mode,
                format_type=format_type,
            )
        except Exception as e:
            return {"success": False, "error": str(e), "workflow": workflow}

    # Alias for backward compatibility with tests
    @server.tool(tags={"workflow", "automation"})
    async def workflow_execute(
        workflow_name: str = None,
        workflow: str = None,
        parameters: dict = None,
        transaction_mode: bool = True,
        format_type: str = "detailed",
    ) -> dict:
        """Execute complex multi-step workflows (alias for workflow_tool)."""
        # Support both workflow_name (test API) and workflow (server API)
        workflow_final = workflow or workflow_name
        if not workflow_final:
            return {"success": False, "error": "workflow or workflow_name required"}
        try:
            from tools.workflow import workflow_execute as workflow_execute_impl
            return await workflow_execute_impl(
                auth_token="test-token",
                workflow=workflow_final,
                parameters=parameters or {},
                transaction_mode=transaction_mode,
                format_type=format_type,
            )
        except Exception as e:
            return {"success": False, "error": str(e), "workflow": workflow_final}

    @server.tool(tags={"query", "analysis", "rag"})
    async def query_tool(
        query_type: str,
        entities: list = None,
        entity_types: list = None,  # Alias for entities (test compatibility)
        conditions: dict = None,
        filters: dict = None,  # Alias for conditions (test compatibility)
        projections: list = None,
        search_term: str = None,
        limit: int = None,
        format_type: str = "detailed",
        rag_mode: str = "auto",
        similarity_threshold: float = 0.7,
        content: str = None,
        entity_type: str = None,
        exclude_id: str = None,
        # Hybrid search weights (test compatibility)
        keyword_weight: float = None,
        semantic_weight: float = None,
        # Aggregate-specific parameters (test compatibility)
        aggregate_type: str = None,
        group_by: list = None,  # For group_by aggregate operations
        # Advanced search operators (test compatibility)
        search_terms: list = None,  # Plural form for multiple terms
        operator: str = None,  # AND, OR, NOT
        exclude_terms: list = None,  # Terms to exclude
        # Additional test API compatibility parameters
        sort: list = None,
        aggregations: dict = None,
        include_coverage: bool = False,
        use_index: bool = False,
        # Search mode parameters
        search_mode: str = None,
        fuzzy_threshold: float = None,
        case_sensitive: bool = None,
        exclude_deleted: bool = None,
        max_results: int = None,
    ) -> dict:
        """Query and analyze data across multiple entity types with RAG capabilities."""
        try:
            # Map test query types to server query types
            query_type_map = {
                "keyword_search": "search",
                "semantic_search": "rag_search",
                "hybrid_search": "rag_search",  # Use rag_search with hybrid mode
            }
            final_query_type = query_type_map.get(query_type, query_type)
            
            # Handle aliases for test compatibility
            final_entities = entity_types if entity_types is not None else entities
            if final_entities is None:
                final_entities = []
            
            # If entity_type is provided but entities is not, convert
            if entity_type and not final_entities:
                final_entities = [entity_type]
            
            # Convert filters to conditions
            final_conditions = filters if filters is not None else conditions
            
            # Convert sort from dict to list if needed (test API compatibility)
            if sort and isinstance(sort, dict):
                sort = [sort]
            
            # Use limit or max_results
            final_limit = limit or max_results
            
            # Set rag_mode for hybrid search
            final_rag_mode = rag_mode
            if query_type == "hybrid_search":
                final_rag_mode = "hybrid"
            
            # Handle aggregate_type and group_by
            if query_type == "aggregate":
                if not final_conditions:
                    final_conditions = {}
                if aggregate_type:
                    final_conditions["_aggregate_type"] = aggregate_type
                if group_by:
                    final_conditions["_group_by"] = group_by
            
            # Handle search_terms (plural) - convert to search_term if needed
            final_search_term = search_term
            if search_terms and not search_term:
                if operator == "AND":
                    final_search_term = " AND ".join(search_terms)
                elif operator == "OR":
                    final_search_term = " OR ".join(search_terms)
                elif operator == "NOT" and exclude_terms:
                    final_search_term = " ".join(search_terms) + " -" + " -".join(exclude_terms)
                else:
                    final_search_term = " ".join(search_terms)
            
            # Import the actual implementation to avoid recursive call
            from tools.query import data_query as data_query_impl
            
            # Build kwargs with all accepted parameters
            kwargs = {
                "auth_token": "test-token",
                "query_type": final_query_type,
                "entities": final_entities,
                "conditions": final_conditions,
                "projections": projections,
                "search_term": final_search_term,
                "limit": final_limit,
                "format_type": format_type,
                "rag_mode": final_rag_mode,
                "similarity_threshold": similarity_threshold,
                "content": content,
                "entity_type": entity_type,
                "exclude_id": exclude_id,
                "keyword_weight": keyword_weight,
                "semantic_weight": semantic_weight,
            }
            # Remove None values to avoid passing unsupported parameters
            kwargs = {k: v for k, v in kwargs.items() if v is not None}
            
            # Ensure entities is a list (required parameter)
            if "entities" not in kwargs or not kwargs["entities"]:
                kwargs["entities"] = []
            
            return await data_query_impl(**kwargs)
        except Exception as e:
            return {"success": False, "error": str(e), "query_type": query_type}

    # Alias for backward compatibility with tests
    @server.tool(tags={"query", "analysis", "rag"})
    async def data_query(
        query_type: str,
        entity_type: str = None,
        entity_types: list = None,  # Test API uses entity_types
        entities: list = None,
        conditions: dict = None,
        filters: dict = None,
        sort: list = None,
        aggregations: dict = None,
        search_term: str = None,
        search_mode: str = None,  # Test API parameter
        limit: int = None,
        offset: int = None,
        format_type: str = "detailed",
        include_coverage: bool = False,
        use_index: bool = False,
        projections: list = None,
        rag_mode: str = "auto",
        similarity_threshold: float = 0.7,
        content: str = None,
        exclude_id: str = None,
        # Additional test API parameters
        fuzzy_threshold: float = None,
        case_sensitive: bool = None,
        exclude_deleted: bool = None,
        max_results: int = None,
        keyword_weight: float = None,
        semantic_weight: float = None,
    ) -> dict:
        """Query and analyze data (alias for query_tool with test API compatibility)."""
        try:
            from tools.query import data_query as data_query_impl
            # Convert test API to server API
            if entity_types and not entities:
                entities = entity_types
            elif entity_type and not entities:
                entities = [entity_type]
            
            if filters and not conditions:
                conditions = filters
            
            # Use limit or max_results
            final_limit = limit or max_results
            
            # Note: aggregations, include_coverage, use_index, offset, search_mode,
            # fuzzy_threshold, case_sensitive, exclude_deleted, keyword_weight, semantic_weight
            # are not yet supported but we accept them to avoid validation errors
            
            return await data_query_impl(
                auth_token="test-token",
                query_type=query_type,
                entities=entities or [],
                conditions=conditions,
                projections=projections,
                search_term=search_term,
                limit=final_limit,
                format_type=format_type,
                rag_mode=rag_mode,
                similarity_threshold=similarity_threshold,
                content=content,
                entity_type=entity_type,
                exclude_id=exclude_id,
                sort=sort,
            )
        except Exception as e:
            return {"success": False, "error": str(e), "query_type": query_type}

    return server

# Parametrization Fixtures - for use with @pytest.mark.parametrize

@pytest.fixture
def entity_types() -> List[str]:
    """Entity type variations for parametrization.
    
    Usage:
        @pytest.mark.unit
        @pytest.mark.parametrize("entity_type", ["organization", "project", "document"])
        async def test_entity_operation(mcp_client_inmemory, entity_type):
            result = await mcp_client_inmemory.call_tool(...)
            assert result.success
    """
    return [
        "organization",
        "project",
        "document",
        "requirement",
        "test_entity",
        "property",
    ]


@pytest.fixture
def operations() -> List[str]:
    """Operation variations (CRUD + search/list/batch)."""
    return [
        "create",
        "read",
        "update",
        "delete",
        "list",
        "search",
        "batch",
    ]


@pytest.fixture
def scenarios() -> List[Dict[str, Any]]:
    """Scenario variations (success, error, edge cases)."""
    return [
        {"name": "success", "expect_success": True},
        {"name": "invalid_input", "expect_success": False},
        {"name": "missing_required", "expect_success": False},
        {"name": "edge_case_empty", "expect_success": False},
    ]


@pytest.fixture
def create_scenarios() -> List[Dict[str, Any]]:
    """CREATE operation scenarios."""
    return [
        {"name": "basic", "expect_success": True, "auto_context": False},
        {"name": "with_auto_context", "expect_success": True, "auto_context": True},
        {"name": "with_explicit_id", "expect_success": True, "explicit_id": True},
        {"name": "missing_required", "expect_success": False, "data": {}},
    ]


@pytest.fixture
def read_scenarios() -> List[Dict[str, Any]]:
    """READ operation scenarios."""
    return [
        {"name": "basic", "expect_success": True, "include_relations": False},
        {"name": "with_relations", "expect_success": True, "include_relations": True},
        {"name": "not_found", "expect_success": False, "entity_id": "invalid-id"},
    ]


@pytest.fixture
def update_scenarios() -> List[Dict[str, Any]]:
    """UPDATE operation scenarios."""
    return [
        {"name": "basic", "expect_success": True},
        {"name": "invalid_id", "expect_success": False},
        {"name": "missing_entity_id", "expect_success": False},
    ]


@pytest.fixture
def delete_scenarios() -> List[Dict[str, Any]]:
    """DELETE operation scenarios."""
    return [
        {"name": "soft_delete", "expect_success": True, "soft_delete": True},
        {"name": "hard_delete", "expect_success": True, "soft_delete": False},
        {"name": "not_found", "expect_success": False},
    ]


@pytest.fixture
def search_scenarios() -> List[Dict[str, Any]]:
    """SEARCH operation scenarios."""
    return [
        {"name": "by_term", "expect_success": True, "search_term": "test"},
        {"name": "with_filters", "expect_success": True, "filters": {}},
        {"name": "with_ordering", "expect_success": True, "order_by": "created_at"},
    ]


@pytest.fixture
def list_scenarios() -> List[Dict[str, Any]]:
    """LIST operation scenarios."""
    return [
        {"name": "basic", "expect_success": True},
        {"name": "with_pagination", "expect_success": True, "limit": 10, "offset": 0},
        {"name": "by_parent", "expect_success": True, "parent_id": "test-parent"},
    ]


@pytest.fixture
def batch_scenarios() -> List[Dict[str, Any]]:
    """BATCH operation scenarios."""
    return [
        {"name": "create_multiple", "expect_success": True, "count": 3},
        {"name": "create_organizations", "expect_success": True, "entity_type": "organization", "count": 5},
    ]


@pytest.fixture
def workflow_types() -> List[str]:
    """Workflow type variations."""
    return [
        "standard_workflow",
        "branching_workflow",
        "parallel_workflow",
        "error_recovery_workflow",
        "transaction_workflow",
    ]


@pytest.fixture
def relationship_types() -> List[str]:
    """Relationship type variations."""
    return [
        "traces_to",
        "relates_to",
        "depends_on",
        "parent_of",
        "references",
    ]


@pytest.fixture
def query_types() -> List[str]:
    """Query type variations."""
    return [
        "semantic_search",
        "filter_query",
        "full_text_search",
        "field_search",
        "aggregation",
    ]


@pytest_asyncio.fixture
async def test_organization(call_mcp):
    """Create and return a test organization."""
    result, _ = await call_mcp("entity_tool", {
        "operation": "create",
        "entity_type": "organization",
        "data": {
            "name": f"Test Organization {time.time()}",
        }
    })
    
    if result.get("success"):
        # Result format: {"success": True, "data": {...}, "count": 1, ...}
        # The entity data is in result["data"]
        entity_data = result.get("data")
        if isinstance(entity_data, dict) and "id" in entity_data:
            org_id = entity_data["id"]
        elif isinstance(entity_data, dict):
            # If data is a dict without 'id', it might be the entity itself
            org_id = entity_data.get("id")
        else:
            yield None
            return
            
        yield org_id
        # Cleanup
        await call_mcp("entity_tool", {
            "operation": "delete",
            "entity_id": org_id,
            "entity_type": "organization"
        })
    else:
        yield None


@pytest_asyncio.fixture
async def test_user():
    """Return a test user ID (UUID)."""
    import uuid
    return str(uuid.uuid4())


@pytest_asyncio.fixture
async def test_project(call_mcp, test_organization):
    """Create and return a test project."""
    result, _ = await call_mcp("entity_tool", {
        "operation": "create",
        "entity_type": "project",
        "data": {
            "name": f"Test Project {time.time()}",
            "organization_id": test_organization
        }
    })
    
    if result.get("success"):
        # Result format: {"success": True, "data": {...}, "count": 1, ...}
        entity_data = result.get("data")
        if isinstance(entity_data, dict) and "id" in entity_data:
            project_id = entity_data["id"]
        elif isinstance(entity_data, dict):
            project_id = entity_data.get("id")
        else:
            yield None
            return
            
        yield project_id
        # Cleanup
        await call_mcp("entity_tool", {
            "operation": "delete",
            "entity_id": project_id,
            "entity_type": "project"
        })
    else:
        yield None
