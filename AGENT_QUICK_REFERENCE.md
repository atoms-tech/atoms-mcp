# Agent Quick Reference Guide
## Test Coverage Enhancement Project

**Purpose**: Fast reference for agents working on test coverage tasks
**Related Documents**: WBS_80_PERCENT_COVERAGE.md, PRD_TEST_COVERAGE_80_PERCENT.md

---

## Agent Assignments & Tasks

### Phase 1: Foundation (Week 1)

#### Agent A - Relationship & Analytics Queries
**Tier**: T1.1, T1.4
**Tests**: 60 tests
**Hours**: 18 hours
**Files**:
- `tests/unit/test_relationship_queries_complete.py` (40 tests)
- `tests/unit/test_analytics_queries_complete.py` (20 tests)

**Tasks**:
1. Create test_relationship_queries_complete.py
   - GetRelationshipsQuery tests (10)
   - FindPathQuery tests (10)
   - GetRelatedEntitiesQuery tests (10)
   - GetDescendantsQuery tests (10)
2. Create test_analytics_queries_complete.py
   - Analytics query tests (20)

**Dependencies**: conftest.py setup (2 hours first)
**Start**: Immediately after conftest.py

---

#### Agent B - Workflow Queries
**Tier**: T1.2
**Tests**: 20 tests
**Hours**: 8 hours
**Files**:
- `tests/unit/test_workflow_queries_complete.py` (20 tests)

**Tasks**:
1. Bulk Create Workflow Tests (8)
2. Bulk Update Workflow Tests (8)
3. Bulk Delete Workflow Tests (4)

**Dependencies**: None
**Start**: Immediately

---

#### Agent C - Workflow Commands
**Tier**: T1.3
**Tests**: 30 tests
**Hours**: 10 hours
**Files**:
- `tests/unit/test_workflow_commands_complete.py` (30 tests)

**Tasks**:
1. Execute Workflow Command Tests (15)
2. Workflow State Management Tests (15)

**Dependencies**: None
**Start**: Immediately

---

#### Agent D - Logging & Serialization
**Tier**: T2.1, T2.2
**Tests**: 55 tests
**Hours**: 16 hours
**Files**:
- `tests/unit/test_logging_comprehensive.py` (30 tests)
- `tests/unit/test_serialization_comprehensive.py` (25 tests)

**Tasks**:
1. StdLibLogger Tests (15)
2. Logger Setup Tests (10)
3. Logger Integration Tests (5)
4. DomainJSONEncoder Tests (15)
5. Safe Serialization Tests (10)

**Dependencies**: None
**Start**: Immediately

---

#### Agent E - Error Handling
**Tier**: T2.3
**Tests**: 15 tests
**Hours**: 5 hours
**Files**:
- `tests/unit/test_error_handling_comprehensive.py` (15 tests)

**Tasks**:
1. Exception Hierarchy Tests (8)
2. Error Handler Tests (7)

**Dependencies**: None
**Start**: Immediately

---

### Phase 2: Adapters (Week 2)

#### Agent F - Supabase Repository
**Tier**: T3.1
**Tests**: 50 tests
**Hours**: 14 hours
**Files**:
- `tests/unit/test_supabase_repository_complete.py` (50 tests)

**Tasks**:
1. Repository CRUD Tests (20)
2. Repository Error Handling Tests (15)
3. Repository Query Builder Tests (15)

**Dependencies**: conftest.py from Phase 1
**Start**: After Phase 1 conftest.py complete

---

#### Agent G - Vertex AI Adapters
**Tier**: T3.2
**Tests**: 40 tests
**Hours**: 13 hours
**Files**:
- `tests/unit/test_vertex_adapter_complete.py` (40 tests)

**Tasks**:
1. Embedding Generation Tests (20)
2. LLM Generation Tests (15)
3. Vertex Client Tests (5)

**Dependencies**: conftest.py from Phase 1
**Start**: After Phase 1 conftest.py complete

---

#### Agent H - Cache Adapters
**Tier**: T3.3
**Tests**: 30 tests
**Hours**: 10 hours
**Files**:
- `tests/unit/test_cache_adapters_complete.py` (30 tests)

**Tasks**:
1. Redis Cache Tests (15)
2. Memory Cache Tests (10)
3. Cache Provider Tests (5)

**Dependencies**: conftest.py from Phase 1
**Start**: After Phase 1 conftest.py complete

---

#### Agent I - Pheno Integration
**Tier**: T3.4
**Tests**: 20 tests
**Hours**: 6 hours
**Files**:
- `tests/unit/test_pheno_integration_complete.py` (20 tests)

**Tasks**:
1. Pheno Logger Tests (10)
2. Pheno Tunnel Tests (10)

**Dependencies**: conftest.py from Phase 1
**Start**: After Phase 1 conftest.py complete

---

### Phase 3: Integration (Week 3)

#### Agent J - CLI Commands
**Tier**: T4.1
**Tests**: 60 tests
**Hours**: 19 hours
**Files**:
- `tests/unit/test_cli_commands_complete.py` (60 tests)

**Tasks**:
1. Entity CLI Commands (20)
2. Relationship CLI Commands (15)
3. Workflow CLI Commands (15)
4. Config CLI Commands (10)

**Dependencies**: Phase 1 application tests complete
**Start**: After Phase 1 complete

---

#### Agent K - MCP Server
**Tier**: T4.2
**Tests**: 40 tests
**Hours**: 13 hours
**Files**:
- `tests/unit/test_mcp_server_complete.py` (40 tests)

**Tasks**:
1. Server Initialization Tests (10)
2. Request Handling Tests (15)
3. Tool Integration Tests (15)

**Dependencies**: Phase 1 application tests complete
**Start**: After Phase 1 complete

---

#### Agent L - Tool Integration
**Tier**: T4.3
**Tests**: 30 tests
**Hours**: 9 hours
**Files**:
- `tests/unit/test_mcp_tools_integration_complete.py` (30 tests)

**Tasks**:
1. Entity Tools Integration (10)
2. Relationship Tools Integration (10)
3. Workflow Tools Integration (10)

**Dependencies**: Phase 1 application tests complete
**Start**: After Phase 1 complete

---

### Phase 4: Performance & Quality (Week 4)

#### Agent M - Performance Tests
**Tier**: T5.1, T5.2
**Tests**: 35 tests
**Hours**: 12.5 hours
**Files**:
- `tests/performance/test_benchmarks_comprehensive.py` (20 tests)
- `tests/performance/test_response_times_comprehensive.py` (15 tests)

**Tasks**:
1. Repository Performance Tests (8)
2. API Response Time Tests (7)
3. Concurrent Load Tests (5)
4. Database Query Latency Tests (10)
5. API Endpoint Latency Tests (5)

**Dependencies**: Phase 2 adapter tests complete
**Start**: After Phase 2 complete

---

#### Agent N - Quality Tests
**Tier**: T5.3, T5.4
**Tests**: 30 tests
**Hours**: 10 hours
**Files**:
- `tests/unit/test_api_usability_comprehensive.py` (20 tests)
- `tests/performance/test_concurrent_load.py` (10 tests)

**Tasks**:
1. Error Message Quality Tests (10)
2. API Consistency Tests (10)
3. Concurrent Write Tests (5)
4. Concurrent Read Tests (5)

**Dependencies**: Phase 2 adapter tests complete
**Start**: After Phase 2 complete

---

## Test Pattern Templates

### Command Handler Test Pattern

```python
"""
Tests for [Component] command handlers.
"""
import pytest
from unittest.mock import Mock
from atoms_mcp.application.commands.[module] import [CommandHandler], [Command]
from atoms_mcp.application.dto import CommandResult, ResultStatus

@pytest.fixture
def mock_repository():
    """Mock repository."""
    repo = Mock()
    repo.save = Mock(return_value=test_entity)
    return repo

@pytest.fixture
def handler(mock_repository, mock_logger):
    """Create command handler."""
    return [CommandHandler](mock_repository, mock_logger)

class Test[Command]:
    """Test [command] execution."""

    def test_command_success(self, handler):
        """Test successful execution."""
        command = [Command](param="value")
        result = handler.handle(command)

        assert result.status == ResultStatus.SUCCESS
        assert result.data is not None

    def test_command_validation_error(self, handler):
        """Test validation failure."""
        command = [Command](param="")  # Invalid
        result = handler.handle(command)

        assert result.status == ResultStatus.ERROR
        assert "validation" in result.error.lower()

    def test_command_repository_error(self, handler, mock_repository):
        """Test repository error handling."""
        mock_repository.save.side_effect = RepositoryError("DB error")
        command = [Command](param="value")
        result = handler.handle(command)

        assert result.status == ResultStatus.ERROR
```

### Query Handler Test Pattern

```python
"""
Tests for [Component] query handlers.
"""
import pytest
from unittest.mock import Mock
from atoms_mcp.application.queries.[module] import [QueryHandler], [Query]

@pytest.fixture
def test_data():
    """Create test data."""
    return [create_test_entity(i) for i in range(25)]

@pytest.fixture
def mock_repository(test_data):
    """Mock repository with test data."""
    repo = Mock()
    repo.find_all = Mock(return_value=test_data)
    return repo

@pytest.fixture
def handler(mock_repository, mock_logger):
    """Create query handler."""
    return [QueryHandler](mock_repository, mock_logger)

class Test[Query]:
    """Test [query] execution."""

    def test_query_success(self, handler):
        """Test successful query."""
        query = [Query](filters={})
        result = handler.handle(query)

        assert result.status == ResultStatus.SUCCESS
        assert isinstance(result.data, list)

    def test_query_with_filters(self, handler):
        """Test filtering."""
        query = [Query](filters={"status": "active"})
        result = handler.handle(query)

        assert result.status == ResultStatus.SUCCESS

    def test_query_pagination(self, handler):
        """Test pagination."""
        query = [Query](page=1, page_size=10)
        page1 = handler.handle(query)

        assert len(page1.data) <= 10
```

### Adapter Test Pattern

```python
"""
Tests for [Adapter] implementation.
"""
import pytest
from unittest.mock import Mock, patch
from atoms_mcp.adapters.secondary.[module] import [Adapter]

@pytest.fixture
def mock_external_service():
    """Mock external service."""
    service = Mock()
    service.query = Mock(return_value={"data": []})
    return service

@pytest.fixture
def adapter(mock_external_service):
    """Create adapter."""
    with patch('[module].get_client', return_value=mock_external_service):
        return [Adapter]()

class Test[Adapter]:
    """Test [adapter] operations."""

    def test_adapter_operation_success(self, adapter, mock_external_service):
        """Test successful operation."""
        result = adapter.perform_operation()

        assert result is not None
        mock_external_service.query.assert_called_once()

    def test_adapter_error_handling(self, adapter, mock_external_service):
        """Test error handling."""
        mock_external_service.query.side_effect = Exception("Error")

        with pytest.raises([AdapterError]):
            adapter.perform_operation()
```

---

## Common Fixtures (from conftest.py)

```python
# Entity fixtures
@pytest.fixture
def test_entity():
    """Create test entity."""
    return Entity(id="test-1", name="Test", ...)

@pytest.fixture
def test_relationship():
    """Create test relationship."""
    return Relationship(id="rel-1", ...)

# Repository mocks
@pytest.fixture
def mock_repository(test_entity):
    """Mock repository with CRUD."""
    repo = Mock(spec=Repository)
    repo.save = Mock(return_value=test_entity)
    repo.find_by_id = Mock(return_value=test_entity)
    repo.find_all = Mock(return_value=[test_entity])
    return repo

# Logger mock
@pytest.fixture
def mock_logger():
    """Mock logger."""
    logger = Mock()
    logger.info = Mock()
    logger.error = Mock()
    return logger

# External service mocks
@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client."""
    from tests.unit.test_comprehensive_mock_framework import MockSupabaseClient
    return MockSupabaseClient()

@pytest.fixture
def mock_vertex_client():
    """Mock Vertex AI client."""
    client = Mock()
    client.generate_embedding = AsyncMock(return_value=[0.1] * 768)
    return client

@pytest.fixture
def mock_redis_client():
    """Mock Redis client."""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    return redis
```

---

## Running Tests

### Run Your Tests
```bash
# Run specific test file
pytest tests/unit/test_relationship_queries_complete.py -v

# Run with coverage
pytest tests/unit/test_relationship_queries_complete.py \
  --cov=src/atoms_mcp/application/queries/relationship_queries \
  --cov-report=term

# Run in parallel
pytest tests/unit/test_relationship_queries_complete.py -n auto

# Run specific test
pytest tests/unit/test_relationship_queries_complete.py::TestGetRelationshipsQuery::test_query_success -v
```

### Check Coverage
```bash
# Generate coverage report
pytest tests/ --cov=src/atoms_mcp --cov-report=html

# View in browser
open htmlcov/index.html

# Check specific module
coverage report --include=src/atoms_mcp/application/queries/*
```

### Validate Tests
```bash
# Run flakiness check (10 runs)
for i in {1..10}; do
  pytest tests/unit/test_relationship_queries_complete.py -q
done

# Check test speed
pytest tests/unit/test_relationship_queries_complete.py --durations=0

# Verify parallel safety
pytest tests/unit/test_relationship_queries_complete.py -n 4
```

---

## Common Issues & Solutions

### Issue: Import Errors
```python
# Solution: Use absolute imports
from atoms_mcp.application.commands.entity_commands import EntityCommandHandler

# Not relative imports
from ..commands.entity_commands import EntityCommandHandler
```

### Issue: Fixture Not Found
```python
# Solution: Check conftest.py or define locally
@pytest.fixture
def my_fixture():
    return value

# Or use existing from conftest
def test_something(test_entity):  # From conftest.py
    pass
```

### Issue: Async Tests Failing
```python
# Solution: Use @pytest.mark.asyncio decorator
@pytest.mark.asyncio
async def test_async_operation():
    result = await async_function()
    assert result is not None
```

### Issue: Mock Not Working
```python
# Solution: Patch at the right location
# Patch where it's imported, not where it's defined
with patch('atoms_mcp.adapters.secondary.supabase.repository.get_client', ...):
    # Not: patch('atoms_mcp.adapters.secondary.supabase.connection.get_client')
```

### Issue: Tests Slow
```python
# Solution: Check for real I/O
# Ensure all external calls are mocked
# Use -n auto for parallel execution
pytest tests/unit/test_file.py -n auto
```

---

## Checklist Before Submitting

- [ ] All tests pass locally
- [ ] Coverage increased for target module
- [ ] No test takes >1s (unit tests)
- [ ] No external service calls (all mocked)
- [ ] Test names descriptive
- [ ] Docstrings on all tests
- [ ] Used fixtures from conftest.py
- [ ] Followed test pattern templates
- [ ] No hardcoded values (use factories)
- [ ] Tests are isolated (no shared state)
- [ ] Ran flakiness check (10 runs)
- [ ] Parallel execution works (-n auto)

---

## Communication

### Daily Standup Format
```
Agent [Letter]: [Name]
Yesterday: Completed X tests in [file]
Today: Working on Y tests in [file]
Blockers: [None / List blockers]
Coverage: +X% in [module]
```

### Blocker Escalation
If blocked for >2 hours:
1. Document blocker clearly
2. Notify in team channel
3. Tag relevant agent/PM
4. Provide context and what you've tried

---

## Useful Commands

```bash
# See what tests would run
pytest --collect-only tests/unit/test_file.py

# Run only failed tests
pytest --lf

# Run with verbose output
pytest -vv

# Stop on first failure
pytest -x

# Show local variables on failure
pytest -l

# Generate coverage HTML report
pytest --cov=src/atoms_mcp --cov-report=html tests/

# Check test markers
pytest --markers

# List all fixtures
pytest --fixtures
```

---

**Quick Links**:
- Full WBS: WBS_80_PERCENT_COVERAGE.md
- PRD: PRD_TEST_COVERAGE_80_PERCENT.md
- Test Framework: tests/unit/test_comprehensive_mock_framework.py
- Conftest: tests/conftest.py

**Questions?** Tag @PM in team channel