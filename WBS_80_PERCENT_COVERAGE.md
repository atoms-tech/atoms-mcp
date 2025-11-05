# Work Breakdown Structure (WBS): Achieving 80%+ Test Coverage for Atoms-MCP

**Project Goal**: Increase test coverage from current baseline to 80%+ through systematic testing of application, infrastructure, adapter, and primary layers.

**Executive Summary**: This WBS defines a comprehensive testing strategy targeting ~350 new tests across 5 tiers, organized for parallel execution by multiple agents. The approach leverages existing mock frameworks and test patterns while systematically covering untested code paths.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Current State Analysis](#current-state-analysis)
3. [Test Architecture & Patterns](#test-architecture--patterns)
4. [Tier 1: Application Layer Tests (High Priority)](#tier-1-application-layer-tests-high-priority)
5. [Tier 2: Infrastructure & Support Tests (Medium Priority)](#tier-2-infrastructure--support-tests-medium-priority)
6. [Tier 3: Adapter Layer Tests (High Impact)](#tier-3-adapter-layer-tests-high-impact)
7. [Tier 4: Primary Adapter Tests (Integration)](#tier-4-primary-adapter-tests-integration)
8. [Tier 5: Performance & Quality Tests](#tier-5-performance--quality-tests)
9. [Mock Strategies & Dependencies](#mock-strategies--dependencies)
10. [Parallel Execution Plan](#parallel-execution-plan)
11. [Success Metrics & Validation](#success-metrics--validation)

---

## Project Overview

### Objectives
- Achieve 80%+ statement coverage across all source modules
- Create maintainable, pattern-consistent tests
- Enable parallel test execution for CI/CD efficiency
- Document test patterns for future development

### Scope
**Source Directories**:
- `src/atoms_mcp/application/` - Application layer (queries, commands, workflows)
- `src/atoms_mcp/infrastructure/` - Infrastructure components (logging, config, DI)
- `src/atoms_mcp/adapters/secondary/` - External adapters (Supabase, Vertex AI, Cache, Pheno)
- `src/atoms_mcp/adapters/primary/` - Entry points (CLI, MCP Server, Tools)
- `src/atoms_mcp/domain/` - Domain models and services

**Test Organization**:
- `tests/unit/` - Fast unit tests (<1s, no external deps)
- `tests/integration/` - Integration tests (require services)
- `tests/performance/` - Performance benchmarks
- `tests/framework/` - Test infrastructure and fixtures

### Key Constraints
- All tests must use existing pytest framework and fixtures
- Mock external services (Supabase, Vertex AI, Redis)
- Tests must be parallelizable (pytest-xdist compatible)
- Follow existing test patterns in `tests/unit/test_comprehensive_mock_framework.py`

---

## Current State Analysis

### Existing Test Infrastructure

**Test Framework Components**:
```python
# Location: tests/conftest.py (needs to be created/updated)
# Fixtures available:
- mock_supabase_client: MockSupabaseClient with table operations
- mock_vertex_client: Mock Vertex AI client
- mock_redis_cache: Mock Redis adapter
- mock_logger: Mock Logger implementation
- test_entities: Pre-populated test data

# Markers:
@pytest.mark.unit         # Fast tests, no external deps
@pytest.mark.integration  # Requires external services
@pytest.mark.asyncio      # Async test support
@pytest.mark.slow         # Tests >5s
```

**Existing Mock Framework**:
- File: `tests/unit/test_comprehensive_mock_framework.py`
- Provides: MockSupabaseClient, MockTable, MockRPC
- Supports: CRUD operations, filtering, pagination

**Test Patterns to Replicate**:
1. **Command Handler Pattern** (from test_tools_complete.py)
2. **Query Handler Pattern** (from test_relationship_fast.py)
3. **Service Layer Pattern** (from test_entity_modes.py)
4. **Adapter Pattern** (from test_config_focused.py)

---

## Test Architecture & Patterns

### Standard Test Structure

```python
"""
Test module following atoms-mcp conventions.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# Pattern 1: Command Handler Tests
class TestCommandHandler:
    """Test command handler with validation and error cases."""

    @pytest.fixture
    def mock_repository(self):
        """Mock repository with standard CRUD operations."""
        repo = Mock()
        repo.save = Mock(return_value=self._create_test_entity())
        repo.find_by_id = Mock(return_value=self._create_test_entity())
        repo.delete = Mock(return_value=True)
        return repo

    @pytest.fixture
    def mock_logger(self):
        """Mock logger tracking all calls."""
        logger = Mock()
        logger.info = Mock()
        logger.error = Mock()
        logger.debug = Mock()
        return logger

    @pytest.fixture
    def handler(self, mock_repository, mock_logger):
        """Create handler with mocked dependencies."""
        return CommandHandler(mock_repository, mock_logger)

    def test_handle_command_success(self, handler):
        """Test successful command execution."""
        command = CreateCommand(name="test", data={"field": "value"})
        result = handler.handle(command)

        assert result.status == ResultStatus.SUCCESS
        assert result.data is not None
        assert result.error is None

    def test_handle_command_validation_error(self, handler):
        """Test command validation failure."""
        command = CreateCommand(name="", data={})  # Invalid
        result = handler.handle(command)

        assert result.status == ResultStatus.ERROR
        assert "validation" in result.error.lower()

    def test_handle_command_repository_error(self, handler, mock_repository):
        """Test repository error handling."""
        mock_repository.save.side_effect = RepositoryError("DB error")
        command = CreateCommand(name="test", data={"field": "value"})
        result = handler.handle(command)

        assert result.status == ResultStatus.ERROR
        assert "repository" in result.error.lower()

# Pattern 2: Query Handler Tests
class TestQueryHandler:
    """Test query handler with pagination and filtering."""

    def test_handle_query_with_filters(self, handler):
        """Test query with multiple filters applied."""
        query = GetEntitiesQuery(
            filters={"status": "active"},
            page=1,
            page_size=20
        )
        result = handler.handle(query)

        assert result.status == ResultStatus.SUCCESS
        assert len(result.data) <= 20
        assert result.total_count >= len(result.data)

    def test_handle_query_pagination(self, handler):
        """Test pagination parameters."""
        # Test first page
        query = GetEntitiesQuery(page=1, page_size=10)
        page1 = handler.handle(query)

        # Test second page
        query = GetEntitiesQuery(page=2, page_size=10)
        page2 = handler.handle(query)

        # Pages should have different data
        if page1.total_count > 10:
            assert page1.data != page2.data

# Pattern 3: Adapter Tests
class TestAdapter:
    """Test adapter with external service mocking."""

    @pytest.fixture
    def mock_external_service(self):
        """Mock external service client."""
        service = Mock()
        service.query = Mock(return_value={"data": []})
        service.execute = Mock(return_value={"success": True})
        return service

    @patch('module.path.get_client')
    def test_adapter_operation(self, mock_get_client, mock_external_service):
        """Test adapter wrapping external service."""
        mock_get_client.return_value = mock_external_service

        adapter = Adapter()
        result = adapter.perform_operation({"param": "value"})

        assert result is not None
        mock_external_service.query.assert_called_once()
```

### Mock Strategy Guidelines

**Level 1: Repository Mocks** (Domain Layer)
```python
@pytest.fixture
def mock_repository():
    """Standard repository mock with CRUD operations."""
    repo = Mock(spec=Repository)
    repo.save = Mock(return_value=test_entity)
    repo.find_by_id = Mock(return_value=test_entity)
    repo.find_all = Mock(return_value=[test_entity])
    repo.delete = Mock(return_value=True)
    repo.exists = Mock(return_value=True)
    return repo
```

**Level 2: Service Mocks** (Application Layer)
```python
@pytest.fixture
def mock_service():
    """Application service mock."""
    service = Mock(spec=EntityService)
    service.create_entity = Mock(return_value=test_entity)
    service.get_entity = Mock(return_value=test_entity)
    service.update_entity = Mock(return_value=test_entity)
    service.delete_entity = Mock(return_value=True)
    return service
```

**Level 3: External Service Mocks** (Adapter Layer)
```python
@pytest.fixture
def mock_supabase_client():
    """Supabase client mock with query builder."""
    from tests.unit.test_comprehensive_mock_framework import MockSupabaseClient
    return MockSupabaseClient()

@pytest.fixture
def mock_vertex_client():
    """Vertex AI client mock."""
    client = Mock()
    client.generate_text = AsyncMock(return_value="Generated text")
    client.generate_embedding = AsyncMock(return_value=[0.1] * 768)
    return client

@pytest.fixture
def mock_redis_client():
    """Redis client mock."""
    client = Mock()
    client.get = AsyncMock(return_value=None)
    client.set = AsyncMock(return_value=True)
    client.delete = AsyncMock(return_value=1)
    return client
```

---

## Tier 1: Application Layer Tests (High Priority)

**Priority**: P0 (Critical Path)
**Expected Coverage Gain**: +3-4%
**Total Tests**: ~110 tests
**Estimated Effort**: 24-32 hours
**Parallelization**: 3 agents (Agent A, B, C)

### 1.1 Relationship Query Tests (~40 tests)

**Target File**: `src/atoms_mcp/application/queries/relationship_queries.py`
**Test File**: `tests/unit/test_relationship_queries_complete.py`
**Dependencies**: Domain models, Repository port, Logger port
**Agent Assignment**: Agent A

#### Task Breakdown

**WBS 1.1.1: GetRelationshipsQuery Tests (10 tests, 3 hours)**
```python
class TestGetRelationshipsQuery:
    """Test relationship retrieval queries."""

    # Validation tests (3 tests)
    def test_query_validation_page_negative(self):
        """Test page validation with negative value."""

    def test_query_validation_page_size_zero(self):
        """Test page_size validation with zero."""

    def test_query_validation_page_size_exceeds_max(self):
        """Test page_size validation exceeding 1000."""

    # Filter tests (4 tests)
    def test_query_with_source_id_filter(self):
        """Test filtering by source_id."""

    def test_query_with_target_id_filter(self):
        """Test filtering by target_id."""

    def test_query_with_relationship_type_filter(self):
        """Test filtering by relationship_type."""

    def test_query_with_combined_filters(self):
        """Test multiple filters simultaneously."""

    # Pagination tests (3 tests)
    def test_query_pagination_first_page(self):
        """Test first page retrieval."""

    def test_query_pagination_middle_page(self):
        """Test middle page retrieval."""

    def test_query_pagination_last_page(self):
        """Test last page with partial results."""
```

**Mock Setup**:
```python
@pytest.fixture
def mock_relationship_repository():
    """Mock repository returning test relationships."""
    repo = Mock(spec=Repository)
    relationships = [
        create_test_relationship(id=f"rel-{i}", source_id="src-1", target_id=f"tgt-{i}")
        for i in range(25)  # Create 25 test relationships
    ]
    repo.find_all = Mock(return_value=relationships)
    return repo

@pytest.fixture
def query_handler(mock_relationship_repository, mock_logger):
    """Create query handler with mocked dependencies."""
    return RelationshipQueryHandler(
        repository=mock_relationship_repository,
        logger=mock_logger
    )
```

**WBS 1.1.2: FindPathQuery Tests (10 tests, 3 hours)**
```python
class TestFindPathQuery:
    """Test path finding queries."""

    # Validation tests (3 tests)
    def test_path_query_validation_empty_start_id(self):
        """Test validation with empty start_id."""

    def test_path_query_validation_empty_end_id(self):
        """Test validation with empty end_id."""

    def test_path_query_validation_max_depth_range(self):
        """Test max_depth validation (1-100)."""

    # Path finding tests (5 tests)
    def test_find_path_direct_connection(self):
        """Test finding direct path (1 hop)."""

    def test_find_path_multi_hop(self):
        """Test finding path with multiple hops."""

    def test_find_path_no_path_exists(self):
        """Test when no path exists."""

    def test_find_path_max_depth_exceeded(self):
        """Test path exceeding max_depth."""

    def test_find_path_circular_reference(self):
        """Test handling of circular relationships."""

    # Error handling (2 tests)
    def test_find_path_repository_error(self):
        """Test repository error handling."""

    def test_find_path_service_error(self):
        """Test service layer error handling."""
```

**WBS 1.1.3: GetRelatedEntitiesQuery Tests (10 tests, 3 hours)**
```python
class TestGetRelatedEntitiesQuery:
    """Test related entities retrieval."""

    # Validation tests (3 tests)
    def test_related_entities_validation_empty_entity_id(self):
        """Test validation with empty entity_id."""

    def test_related_entities_validation_invalid_direction(self):
        """Test direction validation."""

    def test_related_entities_validation_invalid_relationship_type(self):
        """Test relationship_type validation."""

    # Direction tests (3 tests)
    def test_get_related_entities_outgoing(self):
        """Test getting outgoing relationships."""

    def test_get_related_entities_incoming(self):
        """Test getting incoming relationships."""

    def test_get_related_entities_both_directions(self):
        """Test getting bidirectional relationships."""

    # Filtering tests (4 tests)
    def test_get_related_entities_by_type(self):
        """Test filtering by relationship type."""

    def test_get_related_entities_multiple_types(self):
        """Test multiple relationship types."""

    def test_get_related_entities_no_results(self):
        """Test when entity has no relationships."""

    def test_get_related_entities_large_result_set(self):
        """Test with large number of related entities."""
```

**WBS 1.1.4: GetDescendantsQuery Tests (10 tests, 3 hours)**
```python
class TestGetDescendantsQuery:
    """Test descendant hierarchy queries."""

    # Tree traversal tests (6 tests)
    def test_get_descendants_single_level(self):
        """Test getting immediate children."""

    def test_get_descendants_multi_level(self):
        """Test getting nested descendants."""

    def test_get_descendants_max_depth_limit(self):
        """Test respecting max_depth parameter."""

    def test_get_descendants_leaf_nodes(self):
        """Test entity with no descendants."""

    def test_get_descendants_large_tree(self):
        """Test with large hierarchy."""

    def test_get_descendants_circular_prevention(self):
        """Test preventing infinite loops in circular hierarchies."""

    # Edge cases (4 tests)
    def test_get_descendants_invalid_entity_id(self):
        """Test with non-existent entity."""

    def test_get_descendants_orphaned_entity(self):
        """Test entity with broken parent references."""

    def test_get_descendants_empty_result(self):
        """Test when no descendants exist."""

    def test_get_descendants_repository_error(self):
        """Test repository error handling."""
```

**Test File Structure**:
```python
"""
Complete tests for relationship query handlers.
Tests all query types with validation, filtering, and error handling.
"""
import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime, UTC

from atoms_mcp.application.queries.relationship_queries import (
    RelationshipQueryHandler,
    GetRelationshipsQuery,
    FindPathQuery,
    GetRelatedEntitiesQuery,
    GetDescendantsQuery,
    RelationshipQueryValidationError,
)
from atoms_mcp.application.dto import ResultStatus
from atoms_mcp.domain.models.relationship import Relationship, RelationType, RelationshipStatus
from atoms_mcp.domain.ports.repository import Repository, RepositoryError


# Test fixtures
@pytest.fixture
def test_relationships():
    """Create test relationship data."""
    return [
        Relationship(
            id=f"rel-{i}",
            source_id="source-1",
            target_id=f"target-{i}",
            relationship_type=RelationType.PARENT_OF,
            status=RelationshipStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            created_by="test-user",
            properties={}
        )
        for i in range(25)
    ]

@pytest.fixture
def mock_repository(test_relationships):
    """Mock repository with test data."""
    repo = Mock(spec=Repository)
    repo.find_all = Mock(return_value=test_relationships)
    repo.find_by_id = Mock(return_value=test_relationships[0])
    return repo

@pytest.fixture
def mock_logger():
    """Mock logger."""
    logger = Mock()
    return logger

@pytest.fixture
def query_handler(mock_repository, mock_logger):
    """Create query handler."""
    return RelationshipQueryHandler(
        repository=mock_repository,
        logger=mock_logger
    )


# Test classes
class TestGetRelationshipsQuery:
    """Test GetRelationshipsQuery validation and execution."""

    def test_query_validation_page_negative(self):
        """Test page validation with negative value."""
        query = GetRelationshipsQuery(page=-1)
        with pytest.raises(RelationshipQueryValidationError, match="page must be >= 1"):
            query.validate()

    # ... rest of tests
```

### 1.2 Workflow Query Tests (~20 tests)

**Target File**: `src/atoms_mcp/application/workflows/bulk_operations.py`, `src/atoms_mcp/application/workflows/import_export.py`
**Test File**: `tests/unit/test_workflow_queries_complete.py`
**Agent Assignment**: Agent B

**WBS 1.2.1: Bulk Create Workflow Tests (8 tests, 3 hours)**
```python
class TestBulkCreateWorkflow:
    """Test bulk entity creation workflow."""

    def test_bulk_create_validation_empty_list(self):
        """Test validation with empty entities list."""

    def test_bulk_create_validation_exceeds_limit(self):
        """Test validation with >1000 entities."""

    def test_bulk_create_all_success(self):
        """Test successful bulk creation."""

    def test_bulk_create_partial_failure_continue(self):
        """Test continuing after failure with stop_on_error=False."""

    def test_bulk_create_stop_on_error(self):
        """Test stopping on first error."""

    def test_bulk_create_transaction_rollback(self):
        """Test transaction mode rollback on failure."""

    def test_bulk_create_no_transaction_mode(self):
        """Test non-transactional mode."""

    def test_bulk_create_repository_error(self):
        """Test repository error handling."""
```

**WBS 1.2.2: Bulk Update Workflow Tests (8 tests, 3 hours)**
```python
class TestBulkUpdateWorkflow:
    """Test bulk entity update workflow."""

    def test_bulk_update_validation_empty_list(self):
        """Test validation with empty updates list."""

    def test_bulk_update_all_success(self):
        """Test successful bulk update."""

    def test_bulk_update_partial_failure(self):
        """Test handling partial failures."""

    def test_bulk_update_transaction_rollback(self):
        """Test restoring original state on failure."""

    def test_bulk_update_optimistic_locking(self):
        """Test concurrent update detection."""

    def test_bulk_update_validation_errors(self):
        """Test validation error aggregation."""

    def test_bulk_update_nonexistent_entities(self):
        """Test updating non-existent entities."""

    def test_bulk_update_mixed_entity_types(self):
        """Test updating different entity types."""
```

**WBS 1.2.3: Bulk Delete Workflow Tests (4 tests, 2 hours)**
```python
class TestBulkDeleteWorkflow:
    """Test bulk entity deletion workflow."""

    def test_bulk_delete_soft_delete_mode(self):
        """Test soft delete (is_deleted flag)."""

    def test_bulk_delete_hard_delete_mode(self):
        """Test hard delete (physical removal)."""

    def test_bulk_delete_cascade_relationships(self):
        """Test cascading delete of relationships."""

    def test_bulk_delete_referential_integrity(self):
        """Test handling referenced entities."""
```

### 1.3 Workflow Command Tests (~30 tests)

**Target File**: `src/atoms_mcp/application/commands/workflow_commands.py`
**Test File**: `tests/unit/test_workflow_commands_complete.py`
**Agent Assignment**: Agent C

**WBS 1.3.1: Execute Workflow Command Tests (15 tests, 5 hours)**
```python
class TestExecuteWorkflowCommand:
    """Test workflow execution commands."""

    # Command validation (5 tests)
    def test_execute_command_validation_empty_workflow_name(self):
        """Test validation with empty workflow name."""

    def test_execute_command_validation_invalid_workflow(self):
        """Test validation with non-existent workflow."""

    def test_execute_command_validation_missing_parameters(self):
        """Test validation with missing required parameters."""

    def test_execute_command_validation_invalid_parameters(self):
        """Test validation with invalid parameter types."""

    def test_execute_command_validation_parameter_constraints(self):
        """Test parameter constraint validation."""

    # Workflow execution (10 tests)
    def test_execute_workflow_simple_success(self):
        """Test successful simple workflow execution."""

    def test_execute_workflow_with_dependencies(self):
        """Test workflow with step dependencies."""

    def test_execute_workflow_parallel_steps(self):
        """Test parallel step execution."""

    def test_execute_workflow_conditional_branching(self):
        """Test conditional workflow branches."""

    def test_execute_workflow_error_handling(self):
        """Test error handling in workflow steps."""

    def test_execute_workflow_retry_logic(self):
        """Test automatic retry on transient failures."""

    def test_execute_workflow_timeout(self):
        """Test workflow timeout handling."""

    def test_execute_workflow_compensation(self):
        """Test compensation actions on failure."""

    def test_execute_workflow_state_persistence(self):
        """Test workflow state saving."""

    def test_execute_workflow_resume_from_checkpoint(self):
        """Test resuming interrupted workflow."""
```

**WBS 1.3.2: Workflow State Management Tests (15 tests, 5 hours)**
```python
class TestWorkflowStateManagement:
    """Test workflow state persistence and recovery."""

    def test_workflow_state_initialization(self):
        """Test initial state creation."""

    def test_workflow_state_transition(self):
        """Test state transitions."""

    def test_workflow_state_persistence(self):
        """Test saving state to storage."""

    def test_workflow_state_recovery(self):
        """Test loading state from storage."""

    # ... more state management tests
```

**Coverage Summary for Tier 1**:
| Component | Tests | Hours | Agent | Files |
|-----------|-------|-------|-------|-------|
| Relationship Queries | 40 | 12 | A | test_relationship_queries_complete.py |
| Workflow Queries | 20 | 8 | B | test_workflow_queries_complete.py |
| Workflow Commands | 30 | 10 | C | test_workflow_commands_complete.py |
| Analytics Queries | 20 | 6 | A | test_analytics_queries_complete.py |
| **Total** | **110** | **36** | **3** | **4 files** |

---

## Tier 2: Infrastructure & Support Tests (Medium Priority)

**Priority**: P1 (Important)
**Expected Coverage Gain**: +2-3%
**Total Tests**: ~70 tests
**Estimated Effort**: 18-24 hours
**Parallelization**: 2 agents (Agent D, E)

### 2.1 Logging Component Tests (~30 tests)

**Target File**: `src/atoms_mcp/infrastructure/logging/logger.py`, `src/atoms_mcp/infrastructure/logging/setup.py`
**Test File**: `tests/unit/test_logging_comprehensive.py`
**Agent Assignment**: Agent D

**WBS 2.1.1: StdLibLogger Tests (15 tests, 4 hours)**
```python
class TestStdLibLogger:
    """Test standard library logger adapter."""

    @pytest.fixture
    def logger(self):
        """Create logger instance."""
        return StdLibLogger(name="test_logger")

    # Basic logging tests (5 tests)
    def test_logger_debug_message(self, logger, caplog):
        """Test debug level logging."""
        with caplog.at_level(logging.DEBUG):
            logger.debug("Debug message", key="value")
            assert "Debug message" in caplog.text

    def test_logger_info_message(self, logger, caplog):
        """Test info level logging."""

    def test_logger_warning_message(self, logger, caplog):
        """Test warning level logging."""

    def test_logger_error_message(self, logger, caplog):
        """Test error level logging."""

    def test_logger_critical_message(self, logger, caplog):
        """Test critical level logging."""

    # Context manager tests (5 tests)
    def test_logger_context_scope(self, logger, caplog):
        """Test context manager adding fields."""
        with caplog.at_level(logging.INFO):
            with logger.context(request_id="123", user="test"):
                logger.info("Inside context")
                assert "request_id" in caplog.text
                assert "123" in caplog.text

    def test_logger_context_nesting(self, logger, caplog):
        """Test nested context managers."""

    def test_logger_context_restoration(self, logger, caplog):
        """Test context restoration after scope."""

    def test_logger_context_exception_handling(self, logger, caplog):
        """Test context cleanup on exception."""

    def test_logger_context_empty_fields(self, logger, caplog):
        """Test context with no fields."""

    # Timer tests (5 tests)
    def test_logger_timer_basic(self, logger, caplog):
        """Test timing operation."""
        with caplog.at_level(logging.INFO):
            with logger.timer("test_operation"):
                time.sleep(0.1)
            assert "test_operation completed" in caplog.text
            assert "duration_seconds" in caplog.text

    def test_logger_timer_with_extra_fields(self, logger, caplog):
        """Test timer with additional context."""

    def test_logger_timer_exception_handling(self, logger, caplog):
        """Test timer logging on exception."""

    def test_logger_timer_nested(self, logger, caplog):
        """Test nested timers."""

    def test_logger_timer_precision(self, logger, caplog):
        """Test timing precision (3 decimal places)."""
```

**WBS 2.1.2: Logger Setup Tests (10 tests, 3 hours)**
```python
class TestLoggerSetup:
    """Test logger configuration and initialization."""

    def test_setup_default_configuration(self):
        """Test default logger setup."""

    def test_setup_custom_level(self):
        """Test custom log level configuration."""

    def test_setup_file_handler(self):
        """Test file output configuration."""

    def test_setup_json_formatter(self):
        """Test JSON log formatting."""

    def test_setup_structured_logging(self):
        """Test structured log output."""

    def test_setup_log_rotation(self):
        """Test log file rotation."""

    def test_setup_error_file_separation(self):
        """Test separate error log file."""

    def test_setup_from_environment(self):
        """Test configuration from environment variables."""

    def test_setup_multiple_handlers(self):
        """Test configuring multiple handlers."""

    def test_setup_filter_configuration(self):
        """Test log filtering configuration."""
```

**WBS 2.1.3: Logger Integration Tests (5 tests, 2 hours)**
```python
class TestLoggerIntegration:
    """Test logger integration with application."""

    def test_logger_with_fields_immutability(self, logger):
        """Test with_fields creates new instance."""

    def test_logger_exception_logging(self, logger, caplog):
        """Test exception info in error logs."""

    def test_logger_performance_overhead(self, logger, benchmark):
        """Test logging performance impact."""

    def test_logger_thread_safety(self, logger):
        """Test concurrent logging from multiple threads."""

    def test_logger_memory_usage(self, logger):
        """Test memory efficiency with large log volumes."""
```

### 2.2 Serialization Tests (~25 tests)

**Target File**: `src/atoms_mcp/infrastructure/serialization/json.py`
**Test File**: `tests/unit/test_serialization_comprehensive.py`
**Agent Assignment**: Agent D

**WBS 2.2.1: DomainJSONEncoder Tests (15 tests, 4 hours)**
```python
class TestDomainJSONEncoder:
    """Test custom JSON encoder for domain objects."""

    # Type-specific serialization (10 tests)
    def test_encode_uuid(self):
        """Test UUID serialization."""
        from uuid import uuid4
        obj = {"id": uuid4()}
        result = dumps(obj)
        assert isinstance(json.loads(result)["id"], str)

    def test_encode_datetime(self):
        """Test datetime serialization to ISO format."""
        from datetime import datetime, UTC
        obj = {"created": datetime.now(UTC)}
        result = dumps(obj)
        assert "T" in json.loads(result)["created"]  # ISO format

    def test_encode_date(self):
        """Test date serialization."""

    def test_encode_enum(self):
        """Test Enum serialization to value."""

    def test_encode_decimal(self):
        """Test Decimal serialization to float."""

    def test_encode_path(self):
        """Test Path serialization to string."""

    def test_encode_set(self):
        """Test Set serialization to list."""

    def test_encode_pydantic_v1_model(self):
        """Test Pydantic v1 model serialization."""

    def test_encode_pydantic_v2_model(self):
        """Test Pydantic v2 model serialization."""

    def test_encode_dataclass(self):
        """Test dataclass serialization."""

    # Complex object tests (5 tests)
    def test_encode_nested_objects(self):
        """Test nested object serialization."""

    def test_encode_mixed_types(self):
        """Test object with multiple special types."""

    def test_encode_circular_reference(self):
        """Test handling circular references."""

    def test_encode_large_object(self):
        """Test performance with large objects."""

    def test_encode_special_characters(self):
        """Test handling special characters in strings."""
```

**WBS 2.2.2: Safe Serialization Tests (10 tests, 3 hours)**
```python
class TestSafeSerialization:
    """Test safe serialization with fallback handling."""

    def test_safe_dumps_success(self):
        """Test safe_dumps with valid object."""

    def test_safe_dumps_failure_fallback(self):
        """Test safe_dumps returning fallback on error."""

    def test_safe_dumps_custom_fallback(self):
        """Test safe_dumps with custom fallback value."""

    def test_safe_loads_success(self):
        """Test safe_loads with valid JSON."""

    def test_safe_loads_failure_fallback(self):
        """Test safe_loads returning fallback on error."""

    def test_safe_loads_malformed_json(self):
        """Test safe_loads with malformed JSON."""

    def test_is_json_valid(self):
        """Test is_json with valid JSON string."""

    def test_is_json_invalid(self):
        """Test is_json with invalid JSON string."""

    def test_cache_serialization_roundtrip(self):
        """Test serialize_for_cache and deserialize_from_cache."""

    def test_pretty_print_formatting(self):
        """Test dumps_pretty output formatting."""
```

### 2.3 Error Handling Tests (~15 tests)

**Target File**: `src/atoms_mcp/infrastructure/errors/exceptions.py`, `src/atoms_mcp/infrastructure/errors/handlers.py`
**Test File**: `tests/unit/test_error_handling_comprehensive.py`
**Agent Assignment**: Agent E

**WBS 2.3.1: Exception Hierarchy Tests (8 tests, 2.5 hours)**
```python
class TestExceptionHierarchy:
    """Test custom exception classes."""

    def test_base_exception_initialization(self):
        """Test base exception creation."""

    def test_exception_with_context(self):
        """Test exception with additional context."""

    def test_exception_chaining(self):
        """Test exception chaining (from clause)."""

    def test_validation_error_details(self):
        """Test ValidationError with field details."""

    def test_not_found_error_entity_info(self):
        """Test NotFoundError with entity information."""

    def test_conflict_error_conflicting_data(self):
        """Test ConflictError with conflict details."""

    def test_authorization_error_permissions(self):
        """Test AuthorizationError with permission info."""

    def test_external_service_error_service_details(self):
        """Test ExternalServiceError with service information."""
```

**WBS 2.3.2: Error Handler Tests (7 tests, 2.5 hours)**
```python
class TestErrorHandlers:
    """Test error handling and transformation."""

    def test_handle_validation_error_response(self):
        """Test validation error to HTTP response."""

    def test_handle_not_found_error_response(self):
        """Test 404 error response generation."""

    def test_handle_authorization_error_response(self):
        """Test 403 error response generation."""

    def test_handle_generic_error_response(self):
        """Test generic error response."""

    def test_error_logging_integration(self):
        """Test errors are logged properly."""

    def test_error_sanitization(self):
        """Test sensitive data removal from error messages."""

    def test_error_stack_trace_in_dev_mode(self):
        """Test stack traces included in development."""
```

**Coverage Summary for Tier 2**:
| Component | Tests | Hours | Agent | Files |
|-----------|-------|-------|-------|-------|
| Logging Components | 30 | 9 | D | test_logging_comprehensive.py |
| Serialization | 25 | 7 | D | test_serialization_comprehensive.py |
| Error Handling | 15 | 5 | E | test_error_handling_comprehensive.py |
| **Total** | **70** | **21** | **2** | **3 files** |

---

## Tier 3: Adapter Layer Tests (High Impact)

**Priority**: P0 (Critical for Integration)
**Expected Coverage Gain**: +5-8%
**Total Tests**: ~140 tests
**Estimated Effort**: 36-48 hours
**Parallelization**: 4 agents (Agent F, G, H, I)

### 3.1 Supabase Repository Mocking (~50 tests)

**Target File**: `src/atoms_mcp/adapters/secondary/supabase/repository.py`
**Test File**: `tests/unit/test_supabase_repository_complete.py`
**Agent Assignment**: Agent F

**WBS 3.1.1: Repository CRUD Tests (20 tests, 6 hours)**
```python
class TestSupabaseRepositoryCRUD:
    """Test Supabase repository CRUD operations."""

    @pytest.fixture
    def mock_supabase():
        """Mock Supabase client."""
        from tests.unit.test_comprehensive_mock_framework import MockSupabaseClient
        return MockSupabaseClient()

    @pytest.fixture
    def repository(self, mock_supabase):
        """Create repository with mocked Supabase."""
        with patch('atoms_mcp.adapters.secondary.supabase.repository.get_client_with_retry', return_value=mock_supabase):
            return SupabaseRepository(
                table_name="entities",
                entity_type=Entity,
                id_field="id"
            )

    # Create tests (5 tests)
    def test_save_new_entity(self, repository, mock_supabase):
        """Test inserting new entity."""
        entity = Entity(id="test-1", name="Test", entity_type="project")
        result = repository.save(entity)

        assert result.id == "test-1"
        # Verify insert was called
        # (mock_supabase tracks operations)

    def test_save_existing_entity_update(self, repository, mock_supabase):
        """Test updating existing entity."""

    def test_save_with_uuid_serialization(self, repository):
        """Test UUID fields are serialized to strings."""

    def test_save_with_datetime_serialization(self, repository):
        """Test datetime fields are serialized to ISO format."""

    def test_save_with_json_fields(self, repository):
        """Test JSON field serialization."""

    # Read tests (5 tests)
    def test_find_by_id_existing(self, repository, mock_supabase):
        """Test retrieving existing entity by ID."""

    def test_find_by_id_nonexistent(self, repository):
        """Test retrieving non-existent entity returns None."""

    def test_find_all_with_filters(self, repository):
        """Test retrieving entities with filters."""

    def test_find_all_pagination(self, repository):
        """Test pagination parameters."""

    def test_exists_check(self, repository):
        """Test entity existence check."""

    # Update tests (5 tests)
    def test_update_entity_fields(self, repository):
        """Test updating specific entity fields."""

    def test_update_nonexistent_entity(self, repository):
        """Test updating non-existent entity."""

    def test_update_with_optimistic_locking(self, repository):
        """Test concurrent update detection."""

    def test_update_preserves_unchanged_fields(self, repository):
        """Test partial updates don't modify other fields."""

    def test_update_timestamps(self, repository):
        """Test updated_at timestamp is refreshed."""

    # Delete tests (5 tests)
    def test_delete_entity_soft(self, repository):
        """Test soft delete (is_deleted flag)."""

    def test_delete_entity_hard(self, repository):
        """Test hard delete (physical removal)."""

    def test_delete_nonexistent_entity(self, repository):
        """Test deleting non-existent entity."""

    def test_delete_cascade_relationships(self, repository):
        """Test cascade deletion of related entities."""

    def test_delete_referential_integrity(self, repository):
        """Test handling referenced entities on delete."""
```

**WBS 3.1.2: Repository Error Handling Tests (15 tests, 4 hours)**
```python
class TestSupabaseRepositoryErrorHandling:
    """Test repository error handling and retries."""

    # API error tests (8 tests)
    def test_handle_api_error_network(self, repository, mock_supabase):
        """Test handling network errors."""
        mock_supabase.table = Mock(side_effect=APIError("Network error"))

        with pytest.raises(RepositoryError, match="Network error"):
            repository.save(test_entity)

    def test_handle_api_error_timeout(self, repository):
        """Test handling timeout errors."""

    def test_handle_api_error_rate_limit(self, repository):
        """Test handling rate limit errors."""

    def test_handle_api_error_permission(self, repository):
        """Test handling permission errors."""

    def test_handle_api_error_constraint_violation(self, repository):
        """Test handling database constraint violations."""

    def test_handle_api_error_invalid_data(self, repository):
        """Test handling invalid data errors."""

    def test_retry_on_transient_error(self, repository):
        """Test automatic retry on transient failures."""

    def test_max_retries_exceeded(self, repository):
        """Test failing after max retries."""

    # Serialization error tests (7 tests)
    def test_handle_serialization_error_unsupported_type(self, repository):
        """Test handling unsupported type in entity."""

    def test_handle_deserialization_error_invalid_json(self, repository):
        """Test handling invalid JSON from database."""

    def test_handle_deserialization_error_missing_field(self, repository):
        """Test handling missing required field."""

    def test_handle_deserialization_error_type_mismatch(self, repository):
        """Test handling type mismatch in data."""

    def test_handle_validation_error_pydantic(self, repository):
        """Test handling Pydantic validation errors."""

    def test_handle_connection_error(self, repository):
        """Test handling database connection errors."""

    def test_handle_transaction_error(self, repository):
        """Test handling transaction failures."""
```

**WBS 3.1.3: Repository Query Builder Tests (15 tests, 4 hours)**
```python
class TestSupabaseRepositoryQueryBuilder:
    """Test query building and filtering."""

    # Filter tests (10 tests)
    def test_query_with_eq_filter(self, repository):
        """Test equality filter."""

    def test_query_with_in_filter(self, repository):
        """Test IN filter (multiple values)."""

    def test_query_with_like_filter(self, repository):
        """Test LIKE filter (pattern matching)."""

    def test_query_with_range_filter(self, repository):
        """Test range filter (between values)."""

    def test_query_with_or_conditions(self, repository):
        """Test OR filter conditions."""

    def test_query_with_and_conditions(self, repository):
        """Test AND filter conditions."""

    def test_query_with_nested_conditions(self, repository):
        """Test complex nested conditions."""

    def test_query_with_json_path_filter(self, repository):
        """Test filtering on JSON field paths."""

    def test_query_with_order_by(self, repository):
        """Test result ordering."""

    def test_query_with_limit_offset(self, repository):
        """Test pagination with limit/offset."""

    # Advanced query tests (5 tests)
    def test_query_with_joins(self, repository):
        """Test query with table joins."""

    def test_query_with_aggregation(self, repository):
        """Test aggregate functions (count, sum, avg)."""

    def test_query_with_grouping(self, repository):
        """Test GROUP BY queries."""

    def test_query_with_subquery(self, repository):
        """Test subquery support."""

    def test_query_optimization(self, repository):
        """Test query performance optimization."""
```

### 3.2 Vertex AI Adapter Tests (~40 tests)

**Target File**: `src/atoms_mcp/adapters/secondary/vertex/embeddings.py`, `src/atoms_mcp/adapters/secondary/vertex/llm.py`
**Test File**: `tests/unit/test_vertex_adapter_complete.py`
**Agent Assignment**: Agent G

**WBS 3.2.1: Embedding Generation Tests (20 tests, 6 hours)**
```python
class TestTextEmbedder:
    """Test Vertex AI text embedding generation."""

    @pytest.fixture
    def mock_vertex_model(self):
        """Mock Vertex AI embedding model."""
        model = Mock(spec=TextEmbeddingModel)
        # Mock embeddings response
        mock_embedding = Mock()
        mock_embedding.values = [0.1] * 768  # 768-dim vector
        model.get_embeddings = Mock(return_value=[mock_embedding])
        return model

    @pytest.fixture
    def embedder(self, mock_vertex_model):
        """Create embedder with mocked model."""
        with patch('atoms_mcp.adapters.secondary.vertex.embeddings.TextEmbeddingModel.from_pretrained', return_value=mock_vertex_model):
            return TextEmbedder(model_name="textembedding-gecko@003")

    # Single embedding tests (8 tests)
    def test_generate_embedding_success(self, embedder, mock_vertex_model):
        """Test successful embedding generation."""
        result = embedder.generate_embedding("Test text")

        assert isinstance(result, list)
        assert len(result) == 768
        assert all(isinstance(x, float) for x in result)
        mock_vertex_model.get_embeddings.assert_called_once()

    def test_generate_embedding_with_title(self, embedder):
        """Test embedding with document title."""

    def test_generate_embedding_retrieval_document_task(self, embedder):
        """Test RETRIEVAL_DOCUMENT task type."""

    def test_generate_embedding_retrieval_query_task(self, embedder):
        """Test RETRIEVAL_QUERY task type."""

    def test_generate_embedding_classification_task(self, embedder):
        """Test CLASSIFICATION task type."""

    def test_generate_embedding_empty_text(self, embedder):
        """Test handling empty text input."""

    def test_generate_embedding_long_text(self, embedder):
        """Test handling text exceeding token limit."""

    def test_generate_embedding_special_characters(self, embedder):
        """Test handling special characters."""

    # Batch embedding tests (7 tests)
    def test_generate_embeddings_batch_success(self, embedder):
        """Test batch embedding generation."""
        texts = ["text1", "text2", "text3"]
        results = embedder.generate_embeddings_batch(texts)

        assert len(results) == 3
        assert all(len(emb) == 768 for emb in results)

    def test_generate_embeddings_batch_with_titles(self, embedder):
        """Test batch embedding with titles."""

    def test_generate_embeddings_batch_size_limit(self, embedder):
        """Test respecting batch size limit (5 for Vertex AI)."""

    def test_generate_embeddings_batch_empty_list(self, embedder):
        """Test batch with empty list."""

    def test_generate_embeddings_batch_large_batch(self, embedder):
        """Test batching large number of texts."""

    def test_generate_embeddings_batch_partial_failure(self, embedder):
        """Test handling partial batch failures."""

    def test_generate_embeddings_batch_performance(self, embedder, benchmark):
        """Test batch performance vs individual calls."""

    # Caching tests (5 tests)
    def test_embedding_cache_hit(self, embedder):
        """Test cache hit on repeated text."""
        embedder.cache_embeddings = True

        result1 = embedder.generate_embedding("test")
        result2 = embedder.generate_embedding("test")  # Should hit cache

        assert result1 == result2
        # Verify model was only called once

    def test_embedding_cache_miss(self, embedder):
        """Test cache miss on different text."""

    def test_embedding_cache_key_includes_task(self, embedder):
        """Test cache key includes task type."""

    def test_embedding_cache_clear(self, embedder):
        """Test cache clearing."""

    def test_embedding_cache_size_tracking(self, embedder):
        """Test cache size reporting."""
```

**WBS 3.2.2: LLM Generation Tests (15 tests, 5 hours)**
```python
class TestVertexLLM:
    """Test Vertex AI LLM text generation."""

    # Generation tests (10 tests)
    def test_generate_text_success(self, llm):
        """Test successful text generation."""

    def test_generate_text_with_temperature(self, llm):
        """Test temperature parameter."""

    def test_generate_text_with_max_tokens(self, llm):
        """Test max token limit."""

    def test_generate_text_with_system_prompt(self, llm):
        """Test system prompt injection."""

    def test_generate_text_streaming(self, llm):
        """Test streaming response."""

    def test_generate_text_stop_sequences(self, llm):
        """Test stop sequences."""

    def test_generate_text_safety_filters(self, llm):
        """Test content safety filtering."""

    def test_generate_text_long_prompt(self, llm):
        """Test handling long prompts."""

    def test_generate_text_json_mode(self, llm):
        """Test JSON output mode."""

    def test_generate_text_function_calling(self, llm):
        """Test function calling capability."""

    # Error handling tests (5 tests)
    def test_handle_api_error_rate_limit(self, llm):
        """Test rate limit error handling."""

    def test_handle_api_error_quota_exceeded(self, llm):
        """Test quota exceeded error."""

    def test_handle_api_error_invalid_request(self, llm):
        """Test invalid request error."""

    def test_retry_on_transient_error(self, llm):
        """Test automatic retry logic."""

    def test_exponential_backoff(self, llm):
        """Test exponential backoff between retries."""
```

**WBS 3.2.3: Vertex Client Tests (5 tests, 2 hours)**
```python
class TestVertexClient:
    """Test Vertex AI client initialization and configuration."""

    def test_client_initialization_with_defaults(self):
        """Test client with default configuration."""

    def test_client_initialization_with_custom_config(self):
        """Test client with custom parameters."""

    def test_client_authentication(self):
        """Test authentication with service account."""

    def test_client_project_region_configuration(self):
        """Test project and region settings."""

    def test_client_error_on_missing_credentials(self):
        """Test error when credentials not found."""
```

### 3.3 Redis Cache Adapter Tests (~30 tests)

**Target File**: `src/atoms_mcp/adapters/secondary/cache/adapters/redis.py`, `src/atoms_mcp/adapters/secondary/cache/adapters/memory.py`
**Test File**: `tests/unit/test_cache_adapters_complete.py`
**Agent Assignment**: Agent H

**WBS 3.3.1: Redis Cache Tests (15 tests, 5 hours)**
```python
class TestRedisCache:
    """Test Redis cache adapter."""

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client."""
        redis = AsyncMock()
        redis.get = AsyncMock(return_value=None)
        redis.set = AsyncMock(return_value=True)
        redis.delete = AsyncMock(return_value=1)
        redis.exists = AsyncMock(return_value=False)
        redis.expire = AsyncMock(return_value=True)
        return redis

    @pytest.fixture
    def cache(self, mock_redis):
        """Create Redis cache with mocked client."""
        with patch('atoms_mcp.adapters.secondary.cache.adapters.redis.get_redis_client', return_value=mock_redis):
            return RedisCache(host="localhost", port=6379)

    # Basic operations (5 tests)
    @pytest.mark.asyncio
    async def test_cache_get_miss(self, cache, mock_redis):
        """Test cache miss returns None."""
        result = await cache.get("nonexistent_key")
        assert result is None
        mock_redis.get.assert_called_once_with("nonexistent_key")

    @pytest.mark.asyncio
    async def test_cache_get_hit(self, cache, mock_redis):
        """Test cache hit returns value."""
        mock_redis.get.return_value = json.dumps({"data": "value"})
        result = await cache.get("test_key")
        assert result == {"data": "value"}

    @pytest.mark.asyncio
    async def test_cache_set_success(self, cache, mock_redis):
        """Test setting cache value."""
        await cache.set("test_key", {"data": "value"})
        mock_redis.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_delete_success(self, cache, mock_redis):
        """Test deleting cache entry."""
        await cache.delete("test_key")
        mock_redis.delete.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_cache_exists_check(self, cache, mock_redis):
        """Test checking key existence."""
        mock_redis.exists.return_value = True
        result = await cache.exists("test_key")
        assert result is True

    # TTL tests (5 tests)
    @pytest.mark.asyncio
    async def test_cache_set_with_ttl(self, cache, mock_redis):
        """Test setting value with TTL."""
        await cache.set("test_key", "value", ttl=3600)
        # Verify expire was called with 3600 seconds

    @pytest.mark.asyncio
    async def test_cache_get_ttl(self, cache, mock_redis):
        """Test retrieving TTL for key."""

    @pytest.mark.asyncio
    async def test_cache_extend_ttl(self, cache, mock_redis):
        """Test extending TTL for existing key."""

    @pytest.mark.asyncio
    async def test_cache_expire_key(self, cache, mock_redis):
        """Test manually expiring key."""

    @pytest.mark.asyncio
    async def test_cache_persist_key(self, cache, mock_redis):
        """Test removing TTL (make permanent)."""

    # Advanced operations (5 tests)
    @pytest.mark.asyncio
    async def test_cache_multi_get(self, cache, mock_redis):
        """Test getting multiple keys at once."""

    @pytest.mark.asyncio
    async def test_cache_multi_set(self, cache, mock_redis):
        """Test setting multiple keys at once."""

    @pytest.mark.asyncio
    async def test_cache_increment(self, cache, mock_redis):
        """Test incrementing integer value."""

    @pytest.mark.asyncio
    async def test_cache_pattern_delete(self, cache, mock_redis):
        """Test deleting keys matching pattern."""

    @pytest.mark.asyncio
    async def test_cache_flush_all(self, cache, mock_redis):
        """Test clearing entire cache."""
```

**WBS 3.3.2: Memory Cache Tests (10 tests, 3 hours)**
```python
class TestMemoryCache:
    """Test in-memory cache adapter."""

    @pytest.fixture
    def cache(self):
        """Create memory cache instance."""
        return MemoryCache()

    # Basic operations (5 tests)
    @pytest.mark.asyncio
    async def test_memory_cache_get_miss(self, cache):
        """Test cache miss."""

    @pytest.mark.asyncio
    async def test_memory_cache_get_hit(self, cache):
        """Test cache hit."""

    @pytest.mark.asyncio
    async def test_memory_cache_set(self, cache):
        """Test setting value."""

    @pytest.mark.asyncio
    async def test_memory_cache_delete(self, cache):
        """Test deleting value."""

    @pytest.mark.asyncio
    async def test_memory_cache_clear(self, cache):
        """Test clearing all entries."""

    # Memory management (5 tests)
    @pytest.mark.asyncio
    async def test_memory_cache_max_size_eviction(self, cache):
        """Test LRU eviction when max size reached."""

    @pytest.mark.asyncio
    async def test_memory_cache_ttl_expiration(self, cache):
        """Test automatic TTL expiration."""

    @pytest.mark.asyncio
    async def test_memory_cache_memory_usage(self, cache):
        """Test memory usage tracking."""

    @pytest.mark.asyncio
    async def test_memory_cache_thread_safety(self, cache):
        """Test concurrent access safety."""

    @pytest.mark.asyncio
    async def test_memory_cache_performance(self, cache, benchmark):
        """Test access performance."""
```

**WBS 3.3.3: Cache Provider Tests (5 tests, 2 hours)**
```python
class TestCacheProvider:
    """Test cache provider selection and factory."""

    def test_provider_selects_redis(self):
        """Test Redis provider selection."""

    def test_provider_selects_memory(self):
        """Test memory provider selection."""

    def test_provider_fallback_on_redis_unavailable(self):
        """Test fallback to memory when Redis unavailable."""

    def test_provider_configuration_from_env(self):
        """Test provider configuration from environment."""

    def test_provider_health_check(self):
        """Test cache health checking."""
```

### 3.4 Pheno Integration Tests (~20 tests)

**Target File**: `src/atoms_mcp/adapters/secondary/pheno/logger.py`, `src/atoms_mcp/adapters/secondary/pheno/tunnel.py`
**Test File**: `tests/unit/test_pheno_integration_complete.py`
**Agent Assignment**: Agent I

**WBS 3.4.1: Pheno Logger Tests (10 tests, 3 hours)**
```python
class TestPhenoLogger:
    """Test Pheno logger integration."""

    def test_pheno_logger_initialization(self):
        """Test Pheno logger setup."""

    def test_pheno_logger_structured_output(self):
        """Test structured log formatting."""

    def test_pheno_logger_context_fields(self):
        """Test context field propagation."""

    def test_pheno_logger_performance_tracking(self):
        """Test performance metrics logging."""

    def test_pheno_logger_error_reporting(self):
        """Test error reporting to Pheno."""

    def test_pheno_logger_sampling(self):
        """Test log sampling configuration."""

    def test_pheno_logger_batching(self):
        """Test batch log submission."""

    def test_pheno_logger_fallback_on_failure(self):
        """Test fallback to stdout on Pheno failure."""

    def test_pheno_logger_sensitive_data_redaction(self):
        """Test automatic PII redaction."""

    def test_pheno_logger_performance_overhead(self, benchmark):
        """Test logging performance overhead."""
```

**WBS 3.4.2: Pheno Tunnel Tests (10 tests, 3 hours)**
```python
class TestPhenoTunnel:
    """Test Pheno tunnel (SSH/proxy) integration."""

    def test_tunnel_establishment(self):
        """Test SSH tunnel setup."""

    def test_tunnel_connection_pooling(self):
        """Test connection pool management."""

    def test_tunnel_retry_on_disconnect(self):
        """Test automatic reconnection."""

    def test_tunnel_health_monitoring(self):
        """Test tunnel health checks."""

    def test_tunnel_metrics_reporting(self):
        """Test metrics collection."""

    def test_tunnel_bandwidth_throttling(self):
        """Test bandwidth limiting."""

    def test_tunnel_authentication(self):
        """Test SSH key authentication."""

    def test_tunnel_timeout_handling(self):
        """Test timeout configuration."""

    def test_tunnel_error_handling(self):
        """Test connection error handling."""

    def test_tunnel_graceful_shutdown(self):
        """Test clean tunnel closure."""
```

**Coverage Summary for Tier 3**:
| Component | Tests | Hours | Agent | Files |
|-----------|-------|-------|-------|-------|
| Supabase Repository | 50 | 14 | F | test_supabase_repository_complete.py |
| Vertex AI Adapters | 40 | 13 | G | test_vertex_adapter_complete.py |
| Cache Adapters | 30 | 10 | H | test_cache_adapters_complete.py |
| Pheno Integration | 20 | 6 | I | test_pheno_integration_complete.py |
| **Total** | **140** | **43** | **4** | **4 files** |

---

## Tier 4: Primary Adapter Tests (Integration)

**Priority**: P1 (Important)
**Expected Coverage Gain**: +8-12%
**Total Tests**: ~130 tests
**Estimated Effort**: 32-40 hours
**Parallelization**: 3 agents (Agent J, K, L)

### 4.1 CLI Command Tests (~60 tests)

**Target File**: `src/atoms_mcp/adapters/primary/cli/commands.py`
**Test File**: `tests/unit/test_cli_commands_complete.py`
**Agent Assignment**: Agent J

**WBS 4.1.1: Entity CLI Commands (20 tests, 6 hours)**
```python
class TestEntityCLICommands:
    """Test CLI commands for entity management."""

    @pytest.fixture
    def cli_runner(self):
        """Create Typer CLI test runner."""
        from typer.testing import CliRunner
        return CliRunner()

    @pytest.fixture
    def mock_handlers(self):
        """Mock CLI handlers."""
        handlers = Mock(spec=CLIHandlers)
        handlers.create_entity = Mock(return_value={"id": "test-1", "name": "Test"})
        handlers.get_entity = Mock(return_value={"id": "test-1", "name": "Test"})
        handlers.list_entities = Mock(return_value=[{"id": "test-1"}])
        handlers.update_entity = Mock(return_value={"id": "test-1"})
        handlers.delete_entity = Mock(return_value=True)
        return handlers

    # Create command tests (5 tests)
    def test_entity_create_command_success(self, cli_runner, mock_handlers):
        """Test entity create command."""
        with patch('atoms_mcp.adapters.primary.cli.commands.get_handlers', return_value=mock_handlers):
            result = cli_runner.invoke(app, [
                "entity", "create",
                "project",
                "Test Project",
                "--description", "Test description",
                "--properties", '{"key": "value"}'
            ])

            assert result.exit_code == 0
            assert "Test Project" in result.stdout
            mock_handlers.create_entity.assert_called_once()

    def test_entity_create_command_validation_error(self, cli_runner):
        """Test create with invalid parameters."""

    def test_entity_create_command_json_output(self, cli_runner):
        """Test JSON output format."""

    def test_entity_create_command_table_output(self, cli_runner):
        """Test table output format."""

    def test_entity_create_command_missing_required(self, cli_runner):
        """Test error on missing required arguments."""

    # Get command tests (4 tests)
    def test_entity_get_command_success(self, cli_runner, mock_handlers):
        """Test entity get command."""

    def test_entity_get_command_not_found(self, cli_runner):
        """Test get non-existent entity."""

    def test_entity_get_command_multiple_formats(self, cli_runner):
        """Test different output formats."""

    def test_entity_get_command_verbose_mode(self, cli_runner):
        """Test verbose output."""

    # List command tests (5 tests)
    def test_entity_list_command_all(self, cli_runner):
        """Test listing all entities."""

    def test_entity_list_command_with_filters(self, cli_runner):
        """Test filtering results."""

    def test_entity_list_command_pagination(self, cli_runner):
        """Test pagination parameters."""

    def test_entity_list_command_sorting(self, cli_runner):
        """Test result sorting."""

    def test_entity_list_command_empty_results(self, cli_runner):
        """Test handling empty result set."""

    # Update command tests (3 tests)
    def test_entity_update_command_success(self, cli_runner):
        """Test entity update command."""

    def test_entity_update_command_partial(self, cli_runner):
        """Test partial update."""

    def test_entity_update_command_not_found(self, cli_runner):
        """Test updating non-existent entity."""

    # Delete command tests (3 tests)
    def test_entity_delete_command_success(self, cli_runner):
        """Test entity delete command."""

    def test_entity_delete_command_confirmation(self, cli_runner):
        """Test delete confirmation prompt."""

    def test_entity_delete_command_force(self, cli_runner):
        """Test force delete without confirmation."""
```

**WBS 4.1.2: Relationship CLI Commands (15 tests, 5 hours)**
**WBS 4.1.3: Workflow CLI Commands (15 tests, 5 hours)**
**WBS 4.1.4: Config CLI Commands (10 tests, 3 hours)**

### 4.2 MCP Server Tests (~40 tests)

**Target File**: `src/atoms_mcp/adapters/primary/mcp/server.py`
**Test File**: `tests/unit/test_mcp_server_complete.py`
**Agent Assignment**: Agent K

**WBS 4.2.1: Server Initialization Tests (10 tests, 3 hours)**
```python
class TestMCPServerInitialization:
    """Test MCP server initialization and configuration."""

    def test_server_initialization_defaults(self):
        """Test server with default configuration."""

    def test_server_initialization_custom_config(self):
        """Test server with custom settings."""

    def test_server_initialization_missing_env_vars(self):
        """Test handling missing environment variables."""

    def test_server_dependency_injection_setup(self):
        """Test DI container initialization."""

    def test_server_tool_registration(self):
        """Test MCP tool registration."""

    def test_server_middleware_setup(self):
        """Test middleware configuration."""

    def test_server_error_handler_registration(self):
        """Test error handler setup."""

    def test_server_health_check_endpoint(self):
        """Test health check availability."""

    def test_server_metrics_collection(self):
        """Test metrics initialization."""

    def test_server_graceful_shutdown(self):
        """Test clean server shutdown."""
```

**WBS 4.2.2: Request Handling Tests (15 tests, 5 hours)**
```python
class TestMCPServerRequestHandling:
    """Test MCP request processing."""

    @pytest.fixture
    def mock_server(self):
        """Create mock MCP server."""
        # Use FastMCP test utilities
        pass

    def test_handle_tool_call_request(self, mock_server):
        """Test processing tool call requests."""

    def test_handle_list_tools_request(self, mock_server):
        """Test tools/list request."""

    def test_handle_resource_request(self, mock_server):
        """Test resource retrieval."""

    def test_handle_prompt_request(self, mock_server):
        """Test prompt template request."""

    def test_handle_invalid_request(self, mock_server):
        """Test handling malformed requests."""

    def test_handle_authentication(self, mock_server):
        """Test request authentication."""

    def test_handle_authorization(self, mock_server):
        """Test request authorization."""

    def test_handle_rate_limiting(self, mock_server):
        """Test rate limit enforcement."""

    def test_handle_request_timeout(self, mock_server):
        """Test request timeout handling."""

    def test_handle_concurrent_requests(self, mock_server):
        """Test concurrent request processing."""

    # ... more request handling tests
```

**WBS 4.2.3: Tool Integration Tests (15 tests, 5 hours)**
```python
class TestMCPServerToolIntegration:
    """Test MCP tool integration."""

    def test_entity_tool_integration(self, mock_server):
        """Test entity tool calls."""

    def test_relationship_tool_integration(self, mock_server):
        """Test relationship tool calls."""

    def test_workflow_tool_integration(self, mock_server):
        """Test workflow tool calls."""

    def test_query_tool_integration(self, mock_server):
        """Test query tool calls."""

    # ... more tool integration tests
```

### 4.3 Tool Integration Tests (~30 tests)

**Target Files**: `src/atoms_mcp/adapters/primary/mcp/tools/*.py`
**Test File**: `tests/unit/test_mcp_tools_integration_complete.py`
**Agent Assignment**: Agent L

**WBS 4.3.1: Entity Tools Integration (10 tests, 3 hours)**
**WBS 4.3.2: Relationship Tools Integration (10 tests, 3 hours)**
**WBS 4.3.3: Workflow Tools Integration (10 tests, 3 hours)**

**Coverage Summary for Tier 4**:
| Component | Tests | Hours | Agent | Files |
|-----------|-------|-------|-------|-------|
| CLI Commands | 60 | 19 | J | test_cli_commands_complete.py |
| MCP Server | 40 | 13 | K | test_mcp_server_complete.py |
| Tool Integration | 30 | 9 | L | test_mcp_tools_integration_complete.py |
| **Total** | **130** | **41** | **3** | **3 files** |

---

## Tier 5: Performance & Quality Tests

**Priority**: P2 (Nice to Have)
**Expected Coverage Gain**: +1-2%
**Total Tests**: ~65 tests
**Estimated Effort**: 16-20 hours
**Parallelization**: 2 agents (Agent M, N)

### 5.1 Performance Benchmarks (~20 tests)

**Test File**: `tests/performance/test_benchmarks_comprehensive.py`
**Agent Assignment**: Agent M

**WBS 5.1.1: Repository Performance Tests (8 tests, 3 hours)**
```python
class TestRepositoryPerformance:
    """Benchmark repository operations."""

    def test_benchmark_single_entity_save(self, benchmark, repository):
        """Benchmark single entity save operation."""
        entity = create_test_entity()
        result = benchmark(repository.save, entity)
        assert result is not None

    def test_benchmark_bulk_entity_save(self, benchmark, repository):
        """Benchmark bulk save (100 entities)."""
        entities = [create_test_entity() for _ in range(100)]
        result = benchmark(lambda: [repository.save(e) for e in entities])
        assert len(result) == 100

    def test_benchmark_entity_query_simple(self, benchmark, repository):
        """Benchmark simple query."""

    def test_benchmark_entity_query_complex(self, benchmark, repository):
        """Benchmark complex filtered query."""

    def test_benchmark_relationship_traversal(self, benchmark, repository):
        """Benchmark relationship graph traversal."""

    def test_benchmark_cache_hit_performance(self, benchmark, cache):
        """Benchmark cache hit latency."""

    def test_benchmark_cache_miss_performance(self, benchmark, cache):
        """Benchmark cache miss + DB fetch latency."""

    def test_benchmark_serialization_performance(self, benchmark):
        """Benchmark JSON serialization speed."""
```

**WBS 5.1.2: API Response Time Tests (7 tests, 2.5 hours)**
**WBS 5.1.3: Concurrent Load Tests (5 tests, 2 hours)**

### 5.2 Response Time Tests (~15 tests)

**Test File**: `tests/performance/test_response_times_comprehensive.py`
**Agent Assignment**: Agent M

**WBS 5.2.1: API Endpoint Latency Tests (10 tests, 3 hours)**
**WBS 5.2.2: Database Query Latency Tests (5 tests, 2 hours)**

### 5.3 API Usability Tests (~20 tests)

**Test File**: `tests/unit/test_api_usability_comprehensive.py`
**Agent Assignment**: Agent N

**WBS 5.3.1: Error Message Quality Tests (10 tests, 3 hours)**
```python
class TestErrorMessageQuality:
    """Test error messages are clear and actionable."""

    def test_validation_error_message_clarity(self):
        """Test validation errors include field names and constraints."""
        # Invalid entity creation
        result = entity_handler.handle_create(CreateEntityCommand(name=""))

        assert result.status == ResultStatus.ERROR
        assert "name" in result.error.lower()
        assert "required" in result.error.lower() or "empty" in result.error.lower()

    def test_not_found_error_message_includes_id(self):
        """Test not found errors include searched ID."""

    def test_conflict_error_message_includes_details(self):
        """Test conflict errors explain the conflict."""

    def test_authorization_error_message_includes_permission(self):
        """Test auth errors specify required permission."""

    # ... more error message tests
```

**WBS 5.3.2: API Consistency Tests (10 tests, 3 hours)**
```python
class TestAPIConsistency:
    """Test API design consistency."""

    def test_command_result_structure_consistency(self):
        """Test all commands return consistent result structure."""

    def test_query_result_structure_consistency(self):
        """Test all queries return consistent result structure."""

    def test_pagination_parameter_consistency(self):
        """Test pagination uses consistent parameter names."""

    def test_filter_parameter_consistency(self):
        """Test filtering uses consistent parameter structure."""

    def test_error_response_consistency(self):
        """Test error responses have consistent structure."""

    # ... more consistency tests
```

### 5.4 Concurrent Load Tests (~10 tests)

**Test File**: `tests/performance/test_concurrent_load.py`
**Agent Assignment**: Agent N

**WBS 5.4.1: Concurrent Write Tests (5 tests, 2 hours)**
**WBS 5.4.2: Concurrent Read Tests (5 tests, 2 hours)**

**Coverage Summary for Tier 5**:
| Component | Tests | Hours | Agent | Files |
|-----------|-------|-------|-------|-------|
| Performance Benchmarks | 20 | 7.5 | M | test_benchmarks_comprehensive.py |
| Response Time Tests | 15 | 5 | M | test_response_times_comprehensive.py |
| API Usability Tests | 20 | 6 | N | test_api_usability_comprehensive.py |
| Concurrent Load Tests | 10 | 4 | N | test_concurrent_load.py |
| **Total** | **65** | **22.5** | **2** | **4 files** |

---

## Mock Strategies & Dependencies

### Global Mock Fixtures

**File**: `tests/conftest.py` (create/enhance)

```python
"""
Global test fixtures and mocks for atoms-mcp tests.
"""
import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, UTC
from uuid import uuid4

# ============================================================================
# Domain Model Fixtures
# ============================================================================

@pytest.fixture
def test_entity():
    """Create a test entity instance."""
    from atoms_mcp.domain.models.entity import Entity, EntityStatus
    return Entity(
        id=str(uuid4()),
        name="Test Entity",
        entity_type="project",
        status=EntityStatus.ACTIVE,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        created_by="test-user",
        properties={"key": "value"}
    )

@pytest.fixture
def test_relationship():
    """Create a test relationship instance."""
    from atoms_mcp.domain.models.relationship import Relationship, RelationType, RelationshipStatus
    return Relationship(
        id=str(uuid4()),
        source_id=str(uuid4()),
        target_id=str(uuid4()),
        relationship_type=RelationType.PARENT_OF,
        status=RelationshipStatus.ACTIVE,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        created_by="test-user",
        properties={}
    )

@pytest.fixture
def test_workflow():
    """Create a test workflow instance."""
    from atoms_mcp.domain.models.workflow import Workflow, WorkflowStatus
    return Workflow(
        id=str(uuid4()),
        name="Test Workflow",
        status=WorkflowStatus.ACTIVE,
        steps=[],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        created_by="test-user"
    )

# ============================================================================
# Repository Mocks
# ============================================================================

@pytest.fixture
def mock_repository(test_entity):
    """Mock repository with standard CRUD operations."""
    from atoms_mcp.domain.ports.repository import Repository

    repo = Mock(spec=Repository)
    repo.save = Mock(return_value=test_entity)
    repo.find_by_id = Mock(return_value=test_entity)
    repo.find_all = Mock(return_value=[test_entity])
    repo.delete = Mock(return_value=True)
    repo.exists = Mock(return_value=True)
    repo.count = Mock(return_value=1)
    return repo

@pytest.fixture
def mock_relationship_repository(test_relationship):
    """Mock repository for relationships."""
    from atoms_mcp.domain.ports.repository import Repository

    repo = Mock(spec=Repository)
    repo.save = Mock(return_value=test_relationship)
    repo.find_by_id = Mock(return_value=test_relationship)
    repo.find_all = Mock(return_value=[test_relationship])
    repo.delete = Mock(return_value=True)
    return repo

# ============================================================================
# Logger Mocks
# ============================================================================

@pytest.fixture
def mock_logger():
    """Mock logger tracking all calls."""
    from atoms_mcp.domain.ports.logger import Logger

    logger = Mock(spec=Logger)
    logger.debug = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    logger.critical = Mock()
    logger.context = Mock()
    logger.timer = Mock()
    return logger

# ============================================================================
# Cache Mocks
# ============================================================================

@pytest.fixture
def mock_cache():
    """Mock cache adapter."""
    from atoms_mcp.domain.ports.cache import Cache

    cache = Mock(spec=Cache)
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock(return_value=True)
    cache.delete = AsyncMock(return_value=True)
    cache.exists = AsyncMock(return_value=False)
    cache.clear = AsyncMock(return_value=True)
    return cache

# ============================================================================
# External Service Mocks
# ============================================================================

@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client with query builder."""
    from tests.unit.test_comprehensive_mock_framework import MockSupabaseClient
    return MockSupabaseClient()

@pytest.fixture
def mock_vertex_client():
    """Mock Vertex AI client."""
    client = Mock()

    # LLM methods
    client.generate_text = AsyncMock(return_value="Generated text response")
    client.generate_text_stream = AsyncMock()

    # Embedding methods
    mock_embedding = Mock()
    mock_embedding.values = [0.1] * 768  # 768-dim vector

    client.generate_embedding = AsyncMock(return_value=mock_embedding.values)
    client.generate_embeddings_batch = AsyncMock(return_value=[mock_embedding.values] * 5)

    return client

@pytest.fixture
def mock_redis_client():
    """Mock Redis client."""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=1)
    redis.exists = AsyncMock(return_value=False)
    redis.expire = AsyncMock(return_value=True)
    redis.ttl = AsyncMock(return_value=-1)
    redis.keys = AsyncMock(return_value=[])
    redis.flushdb = AsyncMock(return_value=True)
    return redis

# ============================================================================
# Service Mocks
# ============================================================================

@pytest.fixture
def mock_entity_service(test_entity):
    """Mock entity service."""
    from atoms_mcp.domain.services.entity_service import EntityService

    service = Mock(spec=EntityService)
    service.create_entity = Mock(return_value=test_entity)
    service.get_entity = Mock(return_value=test_entity)
    service.update_entity = Mock(return_value=test_entity)
    service.delete_entity = Mock(return_value=True)
    service.list_entities = Mock(return_value=[test_entity])
    return service

@pytest.fixture
def mock_relationship_service(test_relationship):
    """Mock relationship service."""
    from atoms_mcp.domain.services.relationship_service import RelationshipService

    service = Mock(spec=RelationshipService)
    service.create_relationship = Mock(return_value=test_relationship)
    service.get_relationship = Mock(return_value=test_relationship)
    service.get_relationships = Mock(return_value=[test_relationship])
    service.delete_relationship = Mock(return_value=True)
    service.find_path = Mock(return_value=[test_relationship])
    service.get_related_entities = Mock(return_value=[])
    service.get_descendants = Mock(return_value=set())
    return service

# ============================================================================
# Handler Fixtures
# ============================================================================

@pytest.fixture
def entity_command_handler(mock_repository, mock_logger):
    """Create entity command handler with mocked dependencies."""
    from atoms_mcp.application.commands.entity_commands import EntityCommandHandler
    return EntityCommandHandler(
        repository=mock_repository,
        logger=mock_logger
    )

@pytest.fixture
def entity_query_handler(mock_repository, mock_logger):
    """Create entity query handler with mocked dependencies."""
    from atoms_mcp.application.queries.entity_queries import EntityQueryHandler
    return EntityQueryHandler(
        repository=mock_repository,
        logger=mock_logger
    )

@pytest.fixture
def relationship_query_handler(mock_relationship_repository, mock_logger):
    """Create relationship query handler with mocked dependencies."""
    from atoms_mcp.application.queries.relationship_queries import RelationshipQueryHandler
    return RelationshipQueryHandler(
        repository=mock_relationship_repository,
        logger=mock_logger
    )

# ============================================================================
# Test Data Factories
# ============================================================================

def create_test_entities(count: int = 10):
    """Factory for creating multiple test entities."""
    from atoms_mcp.domain.models.entity import Entity, EntityStatus
    return [
        Entity(
            id=f"entity-{i}",
            name=f"Entity {i}",
            entity_type="project" if i % 2 == 0 else "task",
            status=EntityStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            created_by="test-user",
            properties={"index": i}
        )
        for i in range(count)
    ]

def create_test_relationships(count: int = 10, source_id: str = "source-1"):
    """Factory for creating multiple test relationships."""
    from atoms_mcp.domain.models.relationship import Relationship, RelationType, RelationshipStatus
    return [
        Relationship(
            id=f"rel-{i}",
            source_id=source_id,
            target_id=f"target-{i}",
            relationship_type=RelationType.PARENT_OF,
            status=RelationshipStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            created_by="test-user",
            properties={}
        )
        for i in range(count)
    ]
```

### Dependency Matrix

| Component | Dependencies | Mock Strategy |
|-----------|-------------|---------------|
| **Application Layer** | Repository, Logger, Cache | Use domain port mocks |
| **Domain Services** | Repository, Logger | Use repository mocks |
| **Supabase Repository** | Supabase Client | Use MockSupabaseClient |
| **Vertex AI Adapter** | Vertex AI SDK | Mock TextEmbeddingModel |
| **Redis Cache** | Redis Client | Mock redis.asyncio.Redis |
| **CLI Commands** | CLI Handlers | Mock CLIHandlers |
| **MCP Server** | Tools, DI Container | Mock tool functions |
| **MCP Tools** | Handlers, Services | Mock application handlers |

---

## Parallel Execution Plan

### Agent Assignment Matrix

| Agent | Tiers | Tests | Hours | Files | Start Dependencies |
|-------|-------|-------|-------|-------|-------------------|
| **A** | T1.1, T1.4 | 60 | 18 | 2 | None (can start immediately) |
| **B** | T1.2 | 20 | 8 | 1 | None (can start immediately) |
| **C** | T1.3 | 30 | 10 | 1 | None (can start immediately) |
| **D** | T2.1, T2.2 | 55 | 16 | 2 | None (can start immediately) |
| **E** | T2.3 | 15 | 5 | 1 | None (can start immediately) |
| **F** | T3.1 | 50 | 14 | 1 | conftest.py setup |
| **G** | T3.2 | 40 | 13 | 1 | conftest.py setup |
| **H** | T3.3 | 30 | 10 | 1 | conftest.py setup |
| **I** | T3.4 | 20 | 6 | 1 | conftest.py setup |
| **J** | T4.1 | 60 | 19 | 1 | T1 complete |
| **K** | T4.2 | 40 | 13 | 1 | T1 complete |
| **L** | T4.3 | 30 | 9 | 1 | T1 complete |
| **M** | T5.1, T5.2 | 35 | 12.5 | 2 | T3 complete |
| **N** | T5.3, T5.4 | 30 | 10 | 2 | T3 complete |

### Execution Phases

**Phase 1: Foundation (Week 1)**
*Agents: A, B, C, D, E (5 agents in parallel)*
- Create `conftest.py` with global fixtures (Agent A, 2 hours)
- Tier 1: Application Layer Tests (Agents A, B, C: 36 hours total, completes in ~12 hours with 3 agents)
- Tier 2: Infrastructure Tests (Agents D, E: 21 hours total, completes in ~11 hours with 2 agents)
- **Deliverable**: 180 tests, ~7% coverage gain

**Phase 2: Adapters (Week 2)**
*Agents: F, G, H, I (4 agents in parallel)*
*Prerequisites*: conftest.py from Phase 1
- Tier 3: Adapter Layer Tests (Agents F, G, H, I: 43 hours total, completes in ~14 hours with 4 agents)
- **Deliverable**: 140 tests, ~6% coverage gain

**Phase 3: Integration (Week 3)**
*Agents: J, K, L (3 agents in parallel)*
*Prerequisites*: Phase 1 complete
- Tier 4: Primary Adapter Tests (Agents J, K, L: 41 hours total, completes in ~19 hours with 3 agents)
- **Deliverable**: 130 tests, ~10% coverage gain

**Phase 4: Performance & Quality (Week 4)**
*Agents: M, N (2 agents in parallel)*
*Prerequisites*: Phase 2 complete
- Tier 5: Performance & Quality Tests (Agents M, N: 22.5 hours total, completes in ~12.5 hours with 2 agents)
- **Deliverable**: 65 tests, ~2% coverage gain

### Critical Path

```
conftest.py setup (2h)
    ↓
┌───────────┬──────────────┬──────────────┐
│ Phase 1   │ Phase 1      │ Phase 1      │
│ Agent A,B │ Agent C      │ Agent D,E    │
│ T1.1-1.2  │ T1.3         │ T2.1-2.3     │
│ 12h       │ 10h          │ 11h          │
└─────┬─────┴──────────────┴──────────────┘
      │ (Phase 1 complete: 180 tests)
      ↓
┌───────────┬──────────────┬──────────────┬──────────────┐
│ Phase 2   │ Phase 2      │ Phase 2      │ Phase 2      │
│ Agent F   │ Agent G      │ Agent H      │ Agent I      │
│ T3.1      │ T3.2         │ T3.3         │ T3.4         │
│ 14h       │ 13h          │ 10h          │ 6h           │
└─────┬─────┴──────────────┴──────────────┴──────────────┘
      │ (Phase 2 complete: 140 tests)
      ↓
┌───────────┬──────────────┬──────────────┐
│ Phase 3   │ Phase 3      │ Phase 3      │
│ Agent J   │ Agent K      │ Agent L      │
│ T4.1      │ T4.2         │ T4.3         │
│ 19h       │ 13h          │ 9h           │
└─────┬─────┴──────────────┴──────────────┘
      │ (Phase 3 complete: 130 tests)
      ↓
┌───────────┬──────────────┐
│ Phase 4   │ Phase 4      │
│ Agent M   │ Agent N      │
│ T5.1-5.2  │ T5.3-5.4     │
│ 12.5h     │ 10h          │
└───────────┴──────────────┘
      │ (Phase 4 complete: 65 tests)
      ↓
   COMPLETE
   515 tests
   25-30% coverage gain
```

**Total Timeline**: 4 weeks (with parallel execution)
**Total Effort**: 161 hours (distributed across 14 agents)
**Average per Agent**: 11.5 hours

---

## Success Metrics & Validation

### Coverage Targets

**Overall Target**: 80%+ statement coverage

**By Layer**:
| Layer | Current Est. | Target | Gain | Tests |
|-------|-------------|--------|------|-------|
| Domain | 75% | 85% | +10% | Existing |
| Application | 55% | 80% | +25% | 110 |
| Infrastructure | 60% | 80% | +20% | 70 |
| Adapters (Secondary) | 40% | 75% | +35% | 140 |
| Adapters (Primary) | 30% | 70% | +40% | 130 |
| Performance | N/A | 60% | +60% | 65 |

### Validation Checkpoints

**Phase 1 Completion Criteria**:
- [ ] All 180 tests passing
- [ ] Coverage reports show +7% gain
- [ ] conftest.py contains all required fixtures
- [ ] No test execution time >5s (unit tests)
- [ ] All tests parallelizable (no shared state)

**Phase 2 Completion Criteria**:
- [ ] All 140 tests passing
- [ ] Coverage reports show +6% gain (cumulative +13%)
- [ ] All external services properly mocked
- [ ] No actual network calls during tests
- [ ] Mock framework reusable for future tests

**Phase 3 Completion Criteria**:
- [ ] All 130 tests passing
- [ ] Coverage reports show +10% gain (cumulative +23%)
- [ ] CLI commands executable in test mode
- [ ] MCP server testable without running server
- [ ] Tool integration tests isolated

**Phase 4 Completion Criteria**:
- [ ] All 65 tests passing
- [ ] Coverage reports show +2% gain (cumulative +25%)
- [ ] Performance benchmarks establish baselines
- [ ] Load tests identify bottlenecks
- [ ] API usability validated

**Final Validation**:
- [ ] Total coverage ≥80%
- [ ] All 515 new tests passing
- [ ] Test suite runs in <5 minutes (parallel)
- [ ] No flaky tests (100 runs with 0 failures)
- [ ] Test documentation complete
- [ ] CI/CD pipeline configured

### Quality Gates

**Per Test File**:
- Must include module docstring
- Must include class docstrings for test classes
- Must include function docstrings for tests
- Must use pytest fixtures appropriately
- Must use descriptive test names (test_<component>_<scenario>)
- Must include assertions with meaningful messages
- Must mock external dependencies
- Must be idempotent (repeatable)

**Code Review Checklist**:
- [ ] Tests follow existing patterns
- [ ] Mocks are appropriate and minimal
- [ ] Test names clearly describe scenario
- [ ] Edge cases covered
- [ ] Error paths tested
- [ ] Async tests use proper markers
- [ ] No hardcoded credentials or secrets
- [ ] Performance tests have baseline expectations

---

## Appendix A: Test File Templates

### Template 1: Command Handler Tests

```python
"""
Tests for [Component] command handlers.

This module tests command validation, execution, and error handling
for [component] operations.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, UTC

from atoms_mcp.application.commands.[module] import (
    [CommandHandler],
    [Command],
    # ... other imports
)
from atoms_mcp.application.dto import CommandResult, ResultStatus
from atoms_mcp.domain.ports.repository import Repository, RepositoryError

# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_repository():
    """Mock repository with CRUD operations."""
    repo = Mock(spec=Repository)
    repo.save = Mock(return_value=test_entity)
    repo.find_by_id = Mock(return_value=test_entity)
    repo.delete = Mock(return_value=True)
    return repo

@pytest.fixture
def mock_logger():
    """Mock logger."""
    logger = Mock()
    logger.info = Mock()
    logger.error = Mock()
    logger.debug = Mock()
    return logger

@pytest.fixture
def handler(mock_repository, mock_logger):
    """Create command handler."""
    return [CommandHandler](
        repository=mock_repository,
        logger=mock_logger
    )

# ============================================================================
# Test Classes
# ============================================================================

class Test[Command]:
    """Test [command] validation and execution."""

    def test_command_success(self, handler):
        """Test successful command execution."""
        command = [Command](/* params */)
        result = handler.handle(command)

        assert result.status == ResultStatus.SUCCESS
        assert result.data is not None
        assert result.error is None

    def test_command_validation_error(self, handler):
        """Test command validation failure."""
        command = [Command](/* invalid params */)
        result = handler.handle(command)

        assert result.status == ResultStatus.ERROR
        assert "validation" in result.error.lower()

    def test_command_repository_error(self, handler, mock_repository):
        """Test repository error handling."""
        mock_repository.save.side_effect = RepositoryError("DB error")
        command = [Command](/* params */)
        result = handler.handle(command)

        assert result.status == ResultStatus.ERROR
        assert "repository" in result.error.lower()

    # Add more test methods...
```

### Template 2: Query Handler Tests

```python
"""
Tests for [Component] query handlers.

This module tests query validation, filtering, pagination, and
result transformation for [component] queries.
"""
import pytest
from unittest.mock import Mock
from datetime import datetime, UTC

from atoms_mcp.application.queries.[module] import (
    [QueryHandler],
    [Query],
    # ... other imports
)
from atoms_mcp.application.dto import QueryResult, ResultStatus

# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def test_data():
    """Create test data for queries."""
    return [
        # Create test entities
    ]

@pytest.fixture
def mock_repository(test_data):
    """Mock repository returning test data."""
    repo = Mock()
    repo.find_all = Mock(return_value=test_data)
    return repo

@pytest.fixture
def handler(mock_repository, mock_logger):
    """Create query handler."""
    return [QueryHandler](
        repository=mock_repository,
        logger=mock_logger
    )

# ============================================================================
# Test Classes
# ============================================================================

class Test[Query]:
    """Test [query] validation and execution."""

    def test_query_success(self, handler):
        """Test successful query execution."""
        query = [Query](/* params */)
        result = handler.handle(query)

        assert result.status == ResultStatus.SUCCESS
        assert isinstance(result.data, list)
        assert result.total_count >= len(result.data)

    def test_query_with_filters(self, handler):
        """Test query with filters applied."""
        query = [Query](filters={"key": "value"})
        result = handler.handle(query)

        assert result.status == ResultStatus.SUCCESS
        # Verify filtering worked

    def test_query_pagination(self, handler):
        """Test pagination parameters."""
        query = [Query](page=1, page_size=10)
        page1 = handler.handle(query)

        query = [Query](page=2, page_size=10)
        page2 = handler.handle(query)

        # Verify pagination

    # Add more test methods...
```

### Template 3: Adapter Tests

```python
"""
Tests for [Adapter] implementation.

This module tests the adapter's interaction with external services
and proper mocking of those services.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch

from atoms_mcp.adapters.secondary.[module] import [Adapter]

# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_external_service():
    """Mock external service client."""
    service = Mock()
    service.query = Mock(return_value={"data": []})
    service.execute = Mock(return_value={"success": True})
    return service

@pytest.fixture
def adapter(mock_external_service):
    """Create adapter with mocked external service."""
    with patch('[module].get_client', return_value=mock_external_service):
        return [Adapter](/* config */)

# ============================================================================
# Test Classes
# ============================================================================

class Test[Adapter]:
    """Test [adapter] operations and error handling."""

    def test_adapter_operation_success(self, adapter, mock_external_service):
        """Test successful adapter operation."""
        result = adapter.perform_operation(/* params */)

        assert result is not None
        mock_external_service.execute.assert_called_once()

    def test_adapter_error_handling(self, adapter, mock_external_service):
        """Test error handling when external service fails."""
        mock_external_service.execute.side_effect = Exception("Service error")

        with pytest.raises([AdapterError], match="Service error"):
            adapter.perform_operation(/* params */)

    # Add more test methods...
```

---

## Appendix B: CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/test-coverage.yml
name: Test Coverage

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11"]

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        pip install -e ".[dev]"

    - name: Run tests with coverage
      run: |
        pytest -n auto --cov=src/atoms_mcp --cov-report=xml --cov-report=term

    - name: Check coverage threshold
      run: |
        coverage report --fail-under=80

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: true
```

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Run tests before commit
pytest tests/unit/ -n auto -q

if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi

# Check coverage
coverage run -m pytest tests/unit/
coverage report --fail-under=80

if [ $? -ne 0 ]; then
    echo "Coverage below 80%. Commit aborted."
    exit 1
fi

exit 0
```

---

## Appendix C: Execution Commands

### Running Tests by Tier

```bash
# Tier 1: Application Layer Tests
pytest tests/unit/test_relationship_queries_complete.py \
       tests/unit/test_workflow_queries_complete.py \
       tests/unit/test_workflow_commands_complete.py \
       tests/unit/test_analytics_queries_complete.py \
       -n auto -v

# Tier 2: Infrastructure Tests
pytest tests/unit/test_logging_comprehensive.py \
       tests/unit/test_serialization_comprehensive.py \
       tests/unit/test_error_handling_comprehensive.py \
       -n auto -v

# Tier 3: Adapter Layer Tests
pytest tests/unit/test_supabase_repository_complete.py \
       tests/unit/test_vertex_adapter_complete.py \
       tests/unit/test_cache_adapters_complete.py \
       tests/unit/test_pheno_integration_complete.py \
       -n auto -v

# Tier 4: Primary Adapter Tests
pytest tests/unit/test_cli_commands_complete.py \
       tests/unit/test_mcp_server_complete.py \
       tests/unit/test_mcp_tools_integration_complete.py \
       -n auto -v

# Tier 5: Performance & Quality Tests
pytest tests/performance/test_benchmarks_comprehensive.py \
       tests/performance/test_response_times_comprehensive.py \
       tests/unit/test_api_usability_comprehensive.py \
       tests/performance/test_concurrent_load.py \
       -n auto -v

# All tests with coverage
pytest tests/ -n auto --cov=src/atoms_mcp --cov-report=html --cov-report=term
```

### Coverage Analysis

```bash
# Generate coverage report
coverage run -m pytest tests/
coverage report

# Generate HTML report
coverage html
open htmlcov/index.html

# Show missing lines
coverage report --show-missing

# Check specific module
coverage report --include=src/atoms_mcp/application/*
```

---

## Summary

This Work Breakdown Structure provides a comprehensive roadmap for achieving 80%+ test coverage for the atoms-mcp project through systematic testing across 5 tiers:

**Total Deliverables**:
- **515 new tests** organized across 18 test files
- **161 hours** of development effort (distributed across 14 agents)
- **25-30% coverage gain** (estimated final coverage: 80-85%)
- **4-week timeline** with parallel execution

**Key Success Factors**:
1. **Parallel Execution**: 14 agents working simultaneously on independent test tiers
2. **Reusable Patterns**: Consistent test structures and mock strategies
3. **Comprehensive Mocking**: No external dependencies during test execution
4. **Quality Gates**: Validation checkpoints at each phase
5. **CI/CD Integration**: Automated coverage tracking and enforcement

**Next Steps**:
1. Review and approve WBS
2. Set up conftest.py with global fixtures (2 hours)
3. Assign agents to tiers
4. Begin Phase 1 (Application Layer Tests)
5. Monitor progress and coverage metrics
6. Adjust plan based on findings

This structured approach ensures systematic coverage improvement while maintaining code quality and test maintainability.