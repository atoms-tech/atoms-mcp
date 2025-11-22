# Research: Existing Test Patterns & Consolidation Analysis

## Current Test File Structure (25 E2E test files)

### Canonical Names (Good)
- `test_search_and_discovery.py` - Search operations
- `test_workspace_navigation.py` - Workspace context
- `test_entity_relationships.py` - Relationship management
- `test_workflow_execution.py` - Workflow operations
- `test_workflow_scenarios.py` - Workflow scenarios
- `test_workflow_automation.py` - Workflow automation
- `test_requirements_traceability.py` - Requirements tracing
- `test_resilience.py` - Error recovery
- `test_security.py` - Security tests
- `test_performance.py` - Performance tests

### Non-Canonical Names (Consolidation Candidates)
- `test_auth.py` + `test_auth_patterns.py` → Merge into `test_auth_integration.py`
- `test_crud.py` + `test_organization_crud.py` + `test_project_management.py` + `test_document_management.py` → Consolidate into `test_entity_crud.py`
- `test_data_management.py` - Pagination/sorting (merge into `test_entity_crud.py`)
- `test_database.py` - Database operations (move to integration tests)
- `test_error_recovery.py` - Error handling (merge into `test_resilience.py`)
- `test_concurrent_workflows.py` - Concurrency (merge into `test_workflow_execution.py`)
- `test_project_workflow.py` - Project workflows (merge into `test_workflow_execution.py`)
- `test_permission_middleware.py` - Permission tests (8 skipped)
- `test_redis_end_to_end.py` - Redis caching (move to integration tests)
- `test_simple_e2e.py` - Simple tests (consolidate)

## Test Markers Used

```
@pytest.mark.e2e              # E2E tests
@pytest.mark.unit             # Unit tests (in-memory)
@pytest.mark.integration      # Integration tests (HTTP)
@pytest.mark.slow             # Slow tests (>5s)
@pytest.mark.story            # User story mapping
@pytest.mark.three_variant    # Unit/integration/e2e variants
@pytest.mark.mock_only        # Mock-only tests
@pytest.mark.regression       # Regression tests
@pytest.mark.full_workflow    # Full workflow tests
@pytest.mark.performance      # Performance tests
@pytest.mark.live_services    # Requires live services
```

## Fixture Patterns

- `end_to_end_client` - HTTP client for E2E tests
- `mcp_client` - Generic MCP client (parametrized?)
- `auth_token` - Authentication token
- `workspace_context` - Workspace setup

## Skipped Tests (8 total)

All in `test_permission_middleware.py`:
- `test_create_permission_denied_cross_workspace`
- `test_create_permission_missing_workspace_id`
- `test_permission_error_messages_descriptive`
- `test_workspace_membership_validation`
- `test_role_based_permission_differences`
- `test_list_permission_works`
- `test_list_permission_missing_workspace_id`
- `test_create_permission_allowed_in_workspace`

**Reason:** Likely permission middleware not fully implemented or test setup incomplete.

## Flaky Tests (2 total)

1. `test_database_connection_retry` - Database connection retry logic
2. `test_workflow_with_retry` - Workflow retry logic

**Cause:** Likely timing issues or race conditions in retry logic.

## Coverage Gaps

Need to measure with `pytest --cov` to identify:
- Uncovered code paths in services/
- Uncovered infrastructure adapters
- Uncovered tool implementations
- Uncovered auth providers

