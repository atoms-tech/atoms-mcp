"""
Test Dependencies Registry

Central registry of test dependencies for the Atoms MCP test suite.
Defines the dependency graph for automatic test ordering and smart skipping.
"""

from typing import Dict, List, Set


class TestDependencies:
    """
    Central registry of test dependencies.
    
    Usage in tests:
        @pytest.mark.dependency(name="test_server_starts")
        @pytest.mark.order(1)
        async def test_server_starts():
            ...
        
        @pytest.mark.dependency(depends=["test_server_starts"])
        async def test_database_connection():
            ...
    """
    
    # ========================================================================
    # FOUNDATION LAYER - Must pass first
    # ========================================================================
    # These are the absolute foundation tests that everything else depends on
    
    FOUNDATION = {
        # E2E foundation tests
        "test_server_initialization": {
            "layer": "e2e",
            "file": "tests/e2e/test_workflow_execution.py",
            "order": 1,
            "description": "Server must start successfully",
            "depends_on": [],
        },
        "test_database_connection": {
            "layer": "e2e",
            "file": "tests/e2e/test_database.py",
            "order": 2,
            "description": "Database must be accessible",
            "depends_on": ["test_server_initialization"],
        },
        "test_auth_provider_configured": {
            "layer": "e2e",
            "file": "tests/e2e/test_auth.py",
            "order": 3,
            "description": "Auth provider must be configured",
            "depends_on": ["test_server_initialization"],
        },
        "test_mock_services_available": {
            "layer": "unit",
            "file": "tests/unit/test_mock_clients.py",
            "order": 1,
            "description": "Mock services must be available for unit tests",
            "depends_on": [],
        },
    }
    
    # ========================================================================
    # INFRASTRUCTURE LAYER - Core adapters and services
    # ========================================================================
    
    INFRASTRUCTURE = {
        # Database adapters
        "test_supabase_adapter_initialized": {
            "layer": "unit",
            "file": "tests/unit/infrastructure/test_adapters.py",
            "depends_on": ["test_mock_services_available"],
            "description": "Supabase adapter must initialize",
        },
        "test_database_adapter_crud": {
            "layer": "unit",
            "file": "tests/unit/infrastructure/test_database_adapter.py",
            "depends_on": ["test_supabase_adapter_initialized"],
            "description": "Database adapter CRUD operations work",
        },
        
        # Auth adapters
        "test_auth_adapter_initialized": {
            "layer": "unit",
            "file": "tests/unit/infrastructure/test_auth_adapter.py",
            "depends_on": ["test_mock_services_available"],
            "description": "Auth adapter must initialize",
        },
        
        # Storage adapters
        "test_storage_adapter_initialized": {
            "layer": "unit",
            "file": "tests/unit/infrastructure/test_storage_adapter.py",
            "depends_on": ["test_mock_services_available"],
            "description": "Storage adapter must initialize",
        },
        
        # Rate limiting
        "test_rate_limiter_initialized": {
            "layer": "unit",
            "file": "tests/unit/infrastructure/test_distributed_rate_limiter.py",
            "depends_on": ["test_mock_services_available"],
            "description": "Rate limiter must initialize",
        },
    }
    
    # ========================================================================
    # SERVICES LAYER - Business logic services
    # ========================================================================
    
    SERVICES = {
        # Embedding services
        "test_embedding_service_initialized": {
            "layer": "unit",
            "file": "tests/unit/services/test_services.py",
            "depends_on": ["test_database_adapter_crud"],
            "description": "Embedding service must initialize",
        },
        
        # Search services
        "test_search_service_initialized": {
            "layer": "unit",
            "file": "tests/unit/services/test_services.py",
            "depends_on": ["test_database_adapter_crud", "test_embedding_service_initialized"],
            "description": "Search service must initialize",
        },
        
        # Cache services
        "test_cache_service_initialized": {
            "layer": "unit",
            "file": "tests/unit/services/test_embedding_cache.py",
            "depends_on": ["test_database_adapter_crud"],
            "description": "Cache service must initialize",
        },
    }
    
    # ========================================================================
    # TOOLS LAYER - MCP tools (depend on services)
    # ========================================================================
    
    TOOLS = {
        # Entity tool
        "test_entity_create": {
            "layer": "unit",
            "file": "tests/unit/tools/test_entity_core.py",
            "depends_on": ["test_database_adapter_crud"],
            "description": "Entity creation works",
        },
        "test_entity_read": {
            "layer": "unit",
            "file": "tests/unit/tools/test_entity_core.py",
            "depends_on": ["test_entity_create"],
            "description": "Entity reading depends on creation",
        },
        "test_entity_update": {
            "layer": "unit",
            "file": "tests/unit/tools/test_entity_core.py",
            "depends_on": ["test_entity_create", "test_entity_read"],
            "description": "Entity update depends on create and read",
        },
        "test_entity_delete": {
            "layer": "unit",
            "file": "tests/unit/tools/test_entity_core.py",
            "depends_on": ["test_entity_create", "test_entity_read"],
            "description": "Entity delete depends on create and read",
        },
        
        # Workspace tool
        "test_workspace_create": {
            "layer": "unit",
            "file": "tests/unit/tools/test_workspace.py",
            "depends_on": ["test_entity_create"],
            "description": "Workspace creation depends on entity tool",
        },
        
        # Relationship tool
        "test_relationship_create": {
            "layer": "unit",
            "file": "tests/unit/tools/test_relationship.py",
            "depends_on": ["test_entity_create"],
            "description": "Relationship creation depends on entities existing",
        },
        
        # Query tool
        "test_query_execute": {
            "layer": "unit",
            "file": "tests/unit/tools/test_query.py",
            "depends_on": ["test_search_service_initialized", "test_entity_create"],
            "description": "Query execution depends on search service and entities",
        },
        
        # Workflow tool
        "test_workflow_create": {
            "layer": "unit",
            "file": "tests/unit/tools/test_workflow.py",
            "depends_on": ["test_entity_create"],
            "description": "Workflow creation depends on entity tool",
        },
    }
    
    # ========================================================================
    # INTEGRATION TESTS - Depend on unit tests passing
    # ========================================================================
    
    INTEGRATION = {
        "test_api_health": {
            "layer": "integration",
            "file": "tests/integration/test_mcp_server_integration.py",
            "depends_on": ["test_server_initialization"],
            "description": "API health check works",
        },
        "test_api_entity_endpoints": {
            "layer": "integration",
            "file": "tests/integration/test_mcp_server_integration.py",
            "depends_on": ["test_api_health", "test_entity_create"],
            "description": "Entity API endpoints work",
        },
    }
    
    # ========================================================================
    # E2E TESTS - Depend on integration tests passing
    # ========================================================================
    
    E2E = {
        "test_complete_workflow": {
            "layer": "e2e",
            "file": "tests/e2e/test_complete_project_workflow.py",
            "depends_on": [
                "test_database_connection",
                "test_auth_provider_configured",
                "test_entity_create",
                "test_workspace_create",
                "test_workflow_create",
            ],
            "description": "Complete end-to-end workflow",
        },
    }
    
    @classmethod
    def get_all_dependencies(cls) -> Dict[str, Dict]:
        """Get all test dependencies across all layers."""
        all_deps = {}
        all_deps.update(cls.FOUNDATION)
        all_deps.update(cls.INFRASTRUCTURE)
        all_deps.update(cls.SERVICES)
        all_deps.update(cls.TOOLS)
        all_deps.update(cls.INTEGRATION)
        all_deps.update(cls.E2E)
        return all_deps
    
    @classmethod
    def get_dependencies_for_test(cls, test_name: str) -> List[str]:
        """Get list of dependencies for a specific test."""
        all_deps = cls.get_all_dependencies()
        if test_name in all_deps:
            return all_deps[test_name].get("depends_on", [])
        return []
    
    @classmethod
    def get_execution_order(cls) -> List[str]:
        """
        Get tests in execution order (topological sort).
        
        Returns list of test names in order they should execute.
        """
        all_deps = cls.get_all_dependencies()
        
        # Topological sort using DFS
        visited = set()
        temp_marked = set()
        order = []
        
        def visit(test_name: str):
            if test_name in visited:
                return
            if test_name in temp_marked:
                raise ValueError(f"Circular dependency detected involving {test_name}")
            
            temp_marked.add(test_name)
            
            # Visit dependencies first
            if test_name in all_deps:
                for dep in all_deps[test_name].get("depends_on", []):
                    visit(dep)
            
            temp_marked.remove(test_name)
            visited.add(test_name)
            order.append(test_name)
        
        # Visit all tests
        for test_name in all_deps:
            visit(test_name)
        
        return order
    
    @classmethod
    def validate_dependencies(cls) -> List[str]:
        """
        Validate dependency graph for issues.
        
        Returns list of error messages, empty if valid.
        """
        errors = []
        all_deps = cls.get_all_dependencies()
        
        # Check for circular dependencies
        try:
            cls.get_execution_order()
        except ValueError as e:
            errors.append(str(e))
        
        # Check for missing dependencies
        for test_name, test_info in all_deps.items():
            for dep in test_info.get("depends_on", []):
                if dep not in all_deps:
                    errors.append(
                        f"Test '{test_name}' depends on '{dep}' which is not defined"
                    )
        
        return errors
    
    @classmethod
    def get_dependency_graph(cls) -> str:
        """
        Generate ASCII art dependency graph.
        
        Returns multi-line string showing test dependencies.
        """
        lines = []
        lines.append("=" * 70)
        lines.append("TEST DEPENDENCY GRAPH")
        lines.append("=" * 70)
        
        all_deps = cls.get_all_dependencies()
        
        for layer_name, layer_deps in [
            ("FOUNDATION", cls.FOUNDATION),
            ("INFRASTRUCTURE", cls.INFRASTRUCTURE),
            ("SERVICES", cls.SERVICES),
            ("TOOLS", cls.TOOLS),
            ("INTEGRATION", cls.INTEGRATION),
            ("E2E", cls.E2E),
        ]:
            if not layer_deps:
                continue
            
            lines.append(f"\n{layer_name}:")
            for test_name, test_info in layer_deps.items():
                deps = test_info.get("depends_on", [])
                if deps:
                    deps_str = ", ".join(deps)
                    lines.append(f"  • {test_name}")
                    lines.append(f"    └─> depends on: {deps_str}")
                else:
                    lines.append(f"  • {test_name} (no dependencies)")
        
        lines.append("\n" + "=" * 70)
        return "\n".join(lines)


# Convenience function for tests to check dependencies
def requires(*dependencies: str):
    """
    Decorator to mark test dependencies.
    
    Usage:
        @requires("test_server_starts", "test_database_connection")
        async def test_my_feature():
            ...
    """
    import pytest
    return pytest.mark.dependency(depends=list(dependencies))
