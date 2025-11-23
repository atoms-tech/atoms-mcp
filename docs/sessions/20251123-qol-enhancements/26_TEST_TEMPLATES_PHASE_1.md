# Test Templates: Phase 1 Testing

## Test Structure

```
tests/
├── unit/
│   ├── test_context_manager.py
│   ├── test_entity_tool.py
│   ├── test_prompts.py
│   └── test_resources.py
├── integration/
│   ├── test_context_integration.py
│   ├── test_entity_integration.py
│   └── test_prompts_resources_integration.py
└── e2e/
    └── test_phase1_workflows.py
```

## Template 1: Unit Tests - Context Manager

```python
# tests/unit/test_context_manager.py

import pytest
from services.context_manager import SessionContext

class TestSessionContext:
    @pytest.fixture
    def context(self):
        """Create test context."""
        return SessionContext(session_id="test-session")
    
    # ========== Workspace Context Tests ==========
    
    async def test_set_workspace_context(self, context):
        """Test setting workspace context."""
        await context.set_context("workspace", "ws-1")
        
        result = await context.resolve_context("workspace")
        assert result == "ws-1"
    
    async def test_get_workspace_context(self, context):
        """Test getting workspace context."""
        await context.set_context("workspace", "ws-1")
        
        ctx = await context.get_context()
        assert ctx["workspace_id"] == "ws-1"
    
    # ========== Project Context Tests ==========
    
    async def test_set_project_context(self, context):
        """Test setting project context."""
        await context.set_context("project", "proj-1")
        
        result = await context.resolve_context("project")
        assert result == "proj-1"
    
    async def test_project_context_auto_inject(self, context):
        """Test project context auto-injection."""
        await context.set_context("project", "proj-1")
        
        # Verify context is available for auto-injection
        project_id = await context.resolve_context("project")
        assert project_id == "proj-1"
    
    # ========== Document Context Tests ==========
    
    async def test_set_document_context(self, context):
        """Test setting document context."""
        await context.set_context("document", "doc-1")
        
        result = await context.resolve_context("document")
        assert result == "doc-1"
    
    # ========== Entity Type Context Tests ==========
    
    async def test_set_entity_type_context(self, context):
        """Test setting entity type context."""
        await context.set_context("entity_type", "requirement")
        
        result = await context.resolve_context("entity_type")
        assert result == "requirement"
    
    # ========== Parent ID Context Tests ==========
    
    async def test_set_parent_id_context(self, context):
        """Test setting parent ID context."""
        await context.set_context("parent_id", "parent-1")
        
        result = await context.resolve_context("parent_id")
        assert result == "parent-1"
    
    # ========== Multiple Context Tests ==========
    
    async def test_set_multiple_contexts(self, context):
        """Test setting multiple contexts."""
        await context.set_context("workspace", "ws-1")
        await context.set_context("project", "proj-1")
        await context.set_context("document", "doc-1")
        
        ctx = await context.get_context()
        assert ctx["workspace_id"] == "ws-1"
        assert ctx["project_id"] == "proj-1"
        assert ctx["document_id"] == "doc-1"
    
    # ========== Context Persistence Tests ==========
    
    async def test_context_persists_to_session(self, context):
        """Test context persists to session storage."""
        await context.set_context("workspace", "ws-1")
        
        # Create new context instance
        new_context = SessionContext(session_id="test-session")
        
        # Should load from session storage
        result = await new_context.resolve_context("workspace")
        assert result == "ws-1"
    
    # ========== Context Clearing Tests ==========
    
    async def test_clear_context(self, context):
        """Test clearing context."""
        await context.set_context("workspace", "ws-1")
        await context.clear_context()
        
        result = await context.resolve_context("workspace")
        assert result is None
    
    # ========== 3-Level Resolution Tests ==========
    
    async def test_3_level_resolution_context_var(self, context):
        """Test 3-level resolution: context var."""
        # Set via context var
        context._context_vars["workspace"].set("ws-1")
        
        result = await context.resolve_context("workspace")
        assert result == "ws-1"
    
    async def test_3_level_resolution_session(self, context):
        """Test 3-level resolution: session storage."""
        # Set via session storage
        await context._persist_to_session("workspace", "ws-1")
        
        result = await context.resolve_context("workspace")
        assert result == "ws-1"
```

## Template 2: Unit Tests - Entity Tool with Context

```python
# tests/unit/test_entity_tool_context.py

import pytest
from tools.entity import entity_tool
from services.context_manager import SessionContext

class TestEntityToolContext:
    @pytest.fixture
    def context(self):
        """Create test context."""
        return SessionContext(session_id="test-session")
    
    # ========== Auto-Injection Tests ==========
    
    async def test_entity_create_auto_injects_workspace(self, context):
        """Test entity creation auto-injects workspace_id."""
        await context.set_context("workspace", "ws-1")
        
        result = await entity_tool(
            operation="create",
            entity_type="project",
            data={"name": "Test Project"}
        )
        
        assert result["data"]["workspace_id"] == "ws-1"
    
    async def test_entity_create_auto_injects_project(self, context):
        """Test entity creation auto-injects project_id."""
        await context.set_context("project", "proj-1")
        
        result = await entity_tool(
            operation="create",
            entity_type="requirement",
            data={"name": "Test Requirement"}
        )
        
        assert result["data"]["project_id"] == "proj-1"
    
    async def test_entity_create_auto_injects_document(self, context):
        """Test entity creation auto-injects document_id."""
        await context.set_context("document", "doc-1")
        
        result = await entity_tool(
            operation="create",
            entity_type="requirement",
            data={"name": "Test Requirement"}
        )
        
        assert result["data"]["document_id"] == "doc-1"
    
    # ========== Parameter Override Tests ==========
    
    async def test_explicit_param_overrides_context(self, context):
        """Test explicit parameter overrides context."""
        await context.set_context("workspace", "ws-1")
        
        result = await entity_tool(
            operation="create",
            entity_type="project",
            data={"name": "Test Project"},
            workspace_id="ws-2"  # Override context
        )
        
        assert result["data"]["workspace_id"] == "ws-2"
    
    # ========== List with Context Tests ==========
    
    async def test_entity_list_filters_by_context(self, context):
        """Test entity list filters by context."""
        await context.set_context("workspace", "ws-1")
        
        result = await entity_tool(
            operation="list",
            entity_type="project"
        )
        
        # All results should be in ws-1
        for item in result["data"]:
            assert item["workspace_id"] == "ws-1"
    
    # ========== Search with Context Tests ==========
    
    async def test_entity_search_filters_by_context(self, context):
        """Test entity search filters by context."""
        await context.set_context("project", "proj-1")
        
        result = await entity_tool(
            operation="search",
            entity_type="requirement",
            search_term="security"
        )
        
        # All results should be in proj-1
        for item in result["data"]:
            assert item["project_id"] == "proj-1"
```

## Template 3: Integration Tests - Context Integration

```python
# tests/integration/test_context_integration.py

import pytest
from services.context_manager import SessionContext
from tools.entity import entity_tool
from tools.relationship import relationship_tool

class TestContextIntegration:
    @pytest.fixture
    async def setup_context(self):
        """Setup test context with data."""
        context = SessionContext(session_id="test-session")
        
        # Create test workspace
        ws = await entity_tool(
            operation="create",
            entity_type="workspace",
            data={"name": "Test Workspace"}
        )
        
        # Create test project
        proj = await entity_tool(
            operation="create",
            entity_type="project",
            data={"name": "Test Project", "workspace_id": ws["data"]["id"]}
        )
        
        # Set context
        await context.set_context("workspace", ws["data"]["id"])
        await context.set_context("project", proj["data"]["id"])
        
        return context, ws["data"]["id"], proj["data"]["id"]
    
    async def test_nested_workflow_with_context(self, setup_context):
        """Test nested workflow uses context correctly."""
        context, ws_id, proj_id = setup_context
        
        # Create requirement (should auto-inject project_id)
        req = await entity_tool(
            operation="create",
            entity_type="requirement",
            data={"name": "Test Requirement"}
        )
        
        # Create test (should auto-inject project_id)
        test = await entity_tool(
            operation="create",
            entity_type="test",
            data={"name": "Test Case"}
        )
        
        # Link them (should use context)
        link = await relationship_tool(
            operation="link",
            relationship_type="requirement_test",
            source={"type": "requirement", "id": req["data"]["id"]},
            target={"type": "test", "id": test["data"]["id"]}
        )
        
        assert link["success"]
    
    async def test_context_switch_workflow(self, setup_context):
        """Test switching context between projects."""
        context, ws_id, proj_id = setup_context
        
        # Create second project
        proj2 = await entity_tool(
            operation="create",
            entity_type="project",
            data={"name": "Project 2", "workspace_id": ws_id}
        )
        
        # Switch context
        await context.set_context("project", proj2["data"]["id"])
        
        # Create requirement in new project
        req = await entity_tool(
            operation="create",
            entity_type="requirement",
            data={"name": "Req in Project 2"}
        )
        
        assert req["data"]["project_id"] == proj2["data"]["id"]
```

## Template 4: E2E Tests - Phase 1 Workflows

```python
# tests/e2e/test_phase1_workflows.py

import pytest
from services.context_manager import SessionContext
from tools.entity import entity_tool
from tools.relationship import relationship_tool
from tools.context import context_tool

class TestPhase1Workflows:
    async def test_complete_project_setup_workflow(self):
        """Test complete project setup with context."""
        
        # 1. Set workspace context
        await context_tool(
            operation="set_context",
            context_type="workspace",
            entity_id="ws-1"
        )
        
        # 2. Create project
        proj = await entity_tool(
            operation="create",
            entity_type="project",
            data={"name": "E2E Test Project"}
        )
        
        # 3. Set project context
        await context_tool(
            operation="set_context",
            context_type="project",
            entity_id=proj["data"]["id"]
        )
        
        # 4. Create document
        doc = await entity_tool(
            operation="create",
            entity_type="document",
            data={"name": "E2E Test Document"}
        )
        
        # 5. Create requirements
        reqs = []
        for i in range(3):
            req = await entity_tool(
                operation="create",
                entity_type="requirement",
                data={"name": f"Requirement {i+1}"}
            )
            reqs.append(req["data"])
        
        # 6. Create tests
        tests = []
        for i in range(3):
            test = await entity_tool(
                operation="create",
                entity_type="test",
                data={"name": f"Test {i+1}"}
            )
            tests.append(test["data"])
        
        # 7. Link requirements to tests
        for req in reqs:
            for test in tests:
                await relationship_tool(
                    operation="link",
                    relationship_type="requirement_test",
                    source={"type": "requirement", "id": req["id"]},
                    target={"type": "test", "id": test["id"]}
                )
        
        # 8. Verify all created
        assert proj["success"]
        assert doc["success"]
        assert len(reqs) == 3
        assert len(tests) == 3
    
    async def test_batch_operations_with_context(self):
        """Test batch operations use context."""
        
        # Set context
        await context_tool(
            operation="set_context",
            context_type="workspace",
            entity_id="ws-1"
        )
        
        # Batch create requirements
        batch_result = await entity_tool(
            operation="batch_create",
            entity_type="requirement",
            batch=[
                {"name": "Batch Req 1"},
                {"name": "Batch Req 2"},
                {"name": "Batch Req 3"}
            ]
        )
        
        assert batch_result["success"]
        assert len(batch_result["data"]) == 3
        
        # All should have workspace_id from context
        for req in batch_result["data"]:
            assert req["workspace_id"] == "ws-1"
    
    async def test_search_with_context_filters(self):
        """Test search respects context filters."""
        
        # Set context
        await context_tool(
            operation="set_context",
            context_type="project",
            entity_id="proj-1"
        )
        
        # Search should filter by project
        result = await entity_tool(
            operation="search",
            entity_type="requirement",
            search_term="security"
        )
        
        # All results should be in proj-1
        for item in result["data"]:
            assert item["project_id"] == "proj-1"
```

## Template 5: Test Configuration

```python
# tests/conftest.py

import pytest
import asyncio
from services.context_manager import SessionContext

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def context():
    """Create test context."""
    return SessionContext(session_id="test-session")

@pytest.fixture
async def db_session():
    """Create test database session."""
    # Setup test database
    # Yield session
    # Cleanup
    pass

@pytest.fixture
async def mock_entities():
    """Create mock entities for testing."""
    return {
        "workspace": {"id": "ws-1", "name": "Test Workspace"},
        "project": {"id": "proj-1", "name": "Test Project", "workspace_id": "ws-1"},
        "requirement": {"id": "req-1", "name": "Test Requirement", "project_id": "proj-1"},
        "test": {"id": "test-1", "name": "Test Case", "project_id": "proj-1"}
    }
```

## Running Tests

```bash
# Run all tests
python cli.py test run

# Run unit tests only
python cli.py test run --scope unit

# Run integration tests only
python cli.py test run --scope integration

# Run E2E tests only
python cli.py test run --scope e2e

# Run with coverage
python cli.py test run --coverage

# Run specific test file
python cli.py test run tests/unit/test_context_manager.py

# Run specific test class
python cli.py test run tests/unit/test_context_manager.py::TestSessionContext

# Run specific test
python cli.py test run tests/unit/test_context_manager.py::TestSessionContext::test_set_workspace_context
```

## Test Coverage Goals

- **Unit Tests**: 100% coverage of context_manager.py
- **Integration Tests**: 100% coverage of context integration
- **E2E Tests**: All Phase 1 workflows
- **Overall**: 95%+ coverage

## Acceptance Criteria

- ✅ All unit tests pass
- ✅ All integration tests pass
- ✅ All E2E tests pass
- ✅ 95%+ code coverage
- ✅ No breaking changes
- ✅ All context types working
- ✅ Auto-injection verified
- ✅ Parameter override verified

