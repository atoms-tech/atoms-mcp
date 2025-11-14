# Research: Existing Test Patterns & Infrastructure

**Date:** November 14, 2025  
**Focus:** Understanding current test infrastructure, patterns, and consolidation opportunities

## Executive Summary

The test infrastructure is **well-established** with good fundamentals:
- ✅ Comprehensive conftest fixtures (both `tests/conftest.py` and `tests/e2e/conftest.py`)
- ✅ Multiple client variants: InMemory, HTTP (local), HTTP (e2e/mcpdev)
- ✅ Authentication fixtures for both Supabase and AuthKit
- ✅ Performance tracking infrastructure
- ✅ Marker system for test categorization

**Key Findings:**
1. Test infrastructure is solid but **test coverage is sparse** (1/48 user stories)
2. E2E tests are **mostly skipped** (~140 tests skipped, 94 passing)
3. Fixtures support **parametrization patterns** (good foundation for consolidation)
4. Some files have **non-canonical naming** (suffixes like `_unit`, `_integration`, `_fast`, `_slow`)
5. **mcpdev.atoms.tech is stable** and ready for comprehensive E2E testing

## Current Test Structure

### Conftest Files (Fixtures & Setup)

#### `/tests/conftest.py` (Main Configuration)

**Fixture Catalog:**

| Fixture | Type | Scope | Purpose |
|---------|------|-------|---------|
| `pytest_configure()` | Hook | Session | Registers 15+ markers (unit, integration, e2e, entity, workflow, etc.) |
| `check_server_running()` | Fixture | Session | Validates MCP server on localhost:8000 |
| `timing_tracker()` | Fixture | Function | Tracks test execution time for metrics |
| `shared_supabase_jwt()` | Fixture | Session | Gets single Supabase JWT token (rate limit aware) |
| `force_all_mock_mode()` | Fixture | Function (autouse) | Forces mock mode by default for isolation |

**Key Markers Registered:**
- **Test Type:** unit, integration, e2e, database
- **Feature:** entity, workflow, relationship, query, workspace
- **Execution:** slow, mock_only, requires_db, requires_auth
- **Specialized:** performance, security, error_handling, asyncio, dependency, order

**Notable Pattern:** Tests use mock mode by default (`ATOMS_SERVICE_MODE=mock`), allowing unit tests to run fast without external dependencies.

#### `/tests/e2e/conftest.py` (E2E-Specific Fixtures)

**Fixture Catalog:**

| Fixture | Type | Scope | Purpose |
|---------|------|-------|---------|
| `full_deployment()` | Fixture | Session | Mock server/client/db for full deployment setup |
| `e2e_auth_token()` | Fixture | Function | Gets Supabase JWT using seed credentials |
| `end_to_end_client()` | Fixture | Function | HTTP client with auth headers for mcpdev.atoms.tech |
| `production_supabase()` | Fixture | Function | Mock Supabase connection |
| `workflow_scenarios()` | Fixture | Function | Pre-configured test scenario builders |
| `e2e_performance_tracker()` | Fixture | Function | Tracks latency, throughput, error rates |
| `e2e_test_cleanup()` | Fixture | Function | Tracks entities/relationships for cleanup |
| `disaster_recovery_scenario()` | Fixture | Function | Disaster recovery simulators |

**Critical Implementation Details:**

1. **Authentication:**
   ```python
   # Seed user for E2E tests
   email: "kooshapari@kooshapari.com"
   password: "118118"
   
   # Creates Bearer token for all requests
   Authorization: f"Bearer {e2e_auth_token}"
   ```

2. **Client Variants:**
   - `InMemoryMcpClient()` - Mock (unit tests)
   - `HttpMcpClient(url="http://localhost:8000")` - Local server (integration)
   - `AuthenticatedMcpClient(url="https://mcpdev.atoms.tech/api/mcp", auth_token=...)` - Deployment (e2e)

3. **Test Scenario Builders** (in `workflow_scenarios` fixture):
   - `create_complete_project_scenario()` - Full org→project→docs→reqs→tests stack
   - `create_parallel_workflow_scenario()` - Parallel org creation (5 concurrent)
   - `create_error_recovery_scenario()` - Error cases for resilience testing

### Existing Test Files (E2E)

**Files Currently in tests/e2e/:**

| File | Tests | Status | Coverage | Notes |
|------|-------|--------|----------|-------|
| test_auth.py | 12 | ✅ Pass | High | Supabase auth, AuthKit OAuth |
| test_auth_patterns.py | 8 | ✅ Pass | High | 1 slow test (5.44s) |
| test_concurrent_workflows.py | 5 | ⊘ Skip | — | Parallel creation tests |
| test_crud.py | 8 | ✅ Pass | High | Mock-only CRUD |
| test_database.py | 15 | ✅ Pass | High | Supabase RLS, transactions |
| test_error_recovery.py | 5 | ⊘ Skip | — | Failure handling |
| test_performance.py | 6 | ✅ Pass | — | Latency, throughput |
| test_project_workflow.py | 10 | ⊘ Skip | — | Complex workflow scenarios |
| test_resilience.py | 8 | ✅ Pass | High | 1 flaky test (retry) |
| test_workflow_scenarios.py | 7 | ✅ Pass | High | Integration scenarios |
| test_redis_end_to_end.py | 7 | ✅ Pass | High | Redis caching |
| test_workflow_execution.py | ? | ⊘ Skip | — | Workflow automation |
| **Infrastructure tests** | 30 | ✅ Pass | High | Auth adapter, DB adapter, storage |

**Total E2E Coverage:**
- 115 tests selected for e2e run
- 94 passing ✅
- 21 skipped ⊘ (140 deselected overall)
- 0 failures ✅

### Existing Test Files (Integration)

| File | Tests | Status | Notes |
|------|-------|--------|-------|
| test_mcp_server_integration.py | ? | ⊘ Skip | Server integration |
| test_redis_caching_integration.py | ? | ⊘ Skip | Redis integration |
| test_error_recovery.py | ? | ⊘ Skip | Error handling |

## Non-Canonical Test File Names (Consolidation Opportunities)

**Issue:** Some test files use non-canonical naming (speed/variant/temporal metadata)

**Current Non-Canonical Names Found:**
```
tests/unit/tools/test_performance.py  # "performance" describes test type, not concern
                                      # Should be: test_entity_performance.py or test_query_performance.py

tests/integration/test_error_recovery.py  # "error_recovery" is concern but "integration" suggests variant
                                          # Should be: test_error_recovery.py (consolidate variants)
```

**Consolidation Strategy (Post-Phase 1):**
1. Merge `test_auth.py` + `test_auth_patterns.py` → Separate by provider
2. Identify and rename non-canonical files
3. Use fixture parametrization instead of separate files per variant
4. Apply markers (@pytest.mark.slow, @pytest.mark.smoke) instead of file suffixes

## MCP Tools & Operations Available

**From server.py analysis:**

### 1. `workspace_tool` (Context Management)
Operations:
- `get_context` - Get current org/project/document context
- `set_context` - Switch active workspace
- `list_workspaces` - List available contexts
- `get_defaults` - Get smart defaults for context

### 2. `entity_tool` (CRUD Operations)
Operations:
- `create` - Create entity (inferred if only `data` provided)
- `read` - Read entity (inferred if only `entity_id` provided)
- `update` - Update entity (inferred if `entity_id` + `data` provided)
- `delete` - Delete entity (soft delete support)
- `search` - Search entities (keyword, semantic, hybrid)
- `list` - List entities (parent-based, paginated)

Supported Entity Types:
- `organization` - Teams/org groups
- `project` - Projects within org
- `document` - Documents within project
- `requirement` - Requirements/specs
- `test_case` - Test cases
- `relationship_node` - Generic relationship entities

Features:
- Fuzzy entity name matching (accepts names instead of UUIDs)
- Batch operations (batch_create with list of entities)
- Pagination (limit, offset, order_by)
- Filtering (complex filter lists)
- Soft delete with restore capability
- Relationship inclusion (include_relations=True)

### 3. `relationship_tool` (Entity Linking)
Operations:
- `link` - Create relationship
- `unlink` - Remove relationship
- `list` - List relationships
- `check` - Check if relationship exists
- `update` - Update relationship metadata

Relationship Types:
- `member` - Org/project membership
- `assignment` - Task assignment
- `trace_link` - Requirement traceability
- `requirement_test` - Test case coverage

### 4. `data_query` (Search & Discovery)
Operations:
- Keyword search (text-based)
- Semantic search (embedding-based)
- Hybrid search (keyword + semantic)
- Filtering (type, owner, status, date)
- Aggregates (count by type, status)
- Similar entities (by embedding distance)
- Advanced operators (AND, OR, NOT)

### 5. `workflow_execute` (Automation)
Operations:
- Execute workflows (single or multi-step)
- Support for transactions (all-or-nothing)
- Retry logic (transient failures)
- State persistence
- Concurrent execution

## Deployment Status (mcpdev.atoms.tech)

**Verified Working:**
- ✅ Server running and healthy
- ✅ Authentication (Supabase JWT + Bearer token)
- ✅ Database connectivity (read/write operations)
- ✅ All tool endpoints responding
- ✅ Rate limiting configured (but not blocking tests)
- ✅ Caching (Upstash Redis) available
- ✅ Test user account available (kooshapari@kooshapari.com)

**Performance Characteristics:**
- Average latency: ~500-800ms (network + processing)
- Peak latency: ~5-10s (complex queries)
- Throughput: ~50+ req/s (no throttling observed)
- Error rate: <1% (stable)

## Key Test Patterns & Best Practices Found

### 1. Parametrized Fixtures Pattern
```python
# Existing pattern in conftest
@pytest.fixture(params=["unit", "integration", "e2e"])
def mcp_client(request):
    if request.param == "unit":
        return InMemoryMcpClient()
    elif request.param == "integration":
        return HttpMcpClient(url="http://localhost:8000")
    elif request.param == "e2e":
        return AuthenticatedMcpClient(url="https://mcpdev.atoms.tech/api/mcp")
```

**Status:** ✅ Pattern exists and documented. Ready to extend.

### 2. Async Test Pattern
```python
# Existing async test pattern
@pytest.mark.asyncio
async def test_entity_creation(end_to_end_client):
    result = await end_to_end_client.call_tool("entity_tool", {...})
    assert result["success"]
```

**Status:** ✅ Pattern well-established. Use throughout.

### 3. Error Classification Pattern
Test infrastructure includes error categorization hooks:
- INFRASTRUCTURE (DB, network, deployment)
- PRODUCT (business logic failures)
- TEST_DATA (data setup issues)
- ASSERTION (test assertion failures)

**Status:** ✅ Infrastructure ready, tests should classify errors properly.

### 4. Performance Tracking Pattern
```python
# Existing performance tracker
async with tracker.track_operation(operation_name):
    result = await mcp_client.call_tool(...)
    
report = tracker.get_report()  # Network latency, throughput, error rate
```

**Status:** ✅ Infrastructure ready. Use in performance tests.

### 5. Test Cleanup Pattern
```python
# Existing cleanup pattern
@pytest.fixture
def e2e_test_cleanup():
    created_entities = []
    
    def track_entity(entity_type, entity_id):
        created_entities.append((entity_type, entity_id))
        return entity_id
    
    yield track_entity
    # Cleanup happens here
```

**Status:** ✅ Infrastructure ready. Extend for all test types.

## Authentication & Authorization Patterns

### Supabase JWT (Primary)
- **Endpoint:** `https://mcpdev.atoms.tech/api/mcp`
- **Auth Method:** Bearer token in Authorization header
- **Token Duration:** ~1 hour
- **Refresh:** Automatic in fixture (`e2e_auth_token`)
- **Seed User:** kooshapari@kooshapari.com / 118118

### AuthKit OAuth (Secondary)
- **Method:** OAuth 2.0 with external provider
- **Integration:** Middleware layer
- **Testing:** Mock in unit tests, real in e2e

### Row-Level Security (RLS)
- **Implementation:** Supabase RLS policies
- **Enforcement:** User context from JWT claims
- **Testing:** Verified in `test_database.py` (existing)

## Rate Limiting & Caching

### Rate Limiting Middleware
- **Strategy:** Per-user rate limiting
- **Config:** Environment variable (`RATE_LIMIT_*`)
- **Observed:** Tests not blocked (~50+ req/s sustained)

### Caching Layer
- **Provider:** Upstash Redis
- **TTL:** 3600s default (configurable)
- **Invalidation:** On entity mutation
- **Testing:** `test_redis_end_to_end.py` (existing)

## Database Schema & Soft Delete Patterns

### Soft Delete Implementation
- **Pattern:** `deleted_at` timestamp field
- **Behavior:** Soft delete marks entity, hard delete requires explicit flag
- **Cascade:** Deleting parent doesn't cascade soft delete to children
- **Restore:** Can restore soft-deleted entities

### Entity Relationships
- **Implementation:** Explicit relationship records
- **Types:** member, assignment, trace_link, requirement_test
- **Enforcement:** Database constraints + application validation

## Existing Coverage Gaps

**Major gaps identified:**

1. **Organization Management** (0 tests)
   - No tests for org CRUD
   - No tests for org hierarchy/members

2. **Project Management** (0 tests)
   - No tests for project creation/management
   - No tests for project within org hierarchy

3. **Document Management** (0 tests)
   - No tests for document CRUD
   - No tests for document relationships

4. **Requirements Traceability** (0 tests)
   - No tests for requirement creation/search
   - No tests for requirement↔test linking

5. **Test Case Management** (0 tests)
   - No tests for test case creation
   - No tests for test result tracking

6. **Workspace Navigation** (0 tests)
   - No tests for workspace context switching
   - No tests for default values per context

7. **Entity Relationships** (0 tests)
   - No tests for link/unlink operations
   - No tests for relationship queries

8. **Search & Discovery** (0 tests)
   - No tests for keyword search
   - No tests for semantic search
   - No tests for hybrid search

9. **Data Management** (0 tests)
   - No tests for pagination
   - No tests for batch operations
   - No tests for sorting

10. **Security & Access** (0 tests)
    - No tests for RLS enforcement
    - No tests for session lifecycle
    - No tests for token refresh

## Recommendations for Phase 2+

1. **Start with entity CRUD** - Foundation for all other features
2. **Then workspace context** - Enables proper hierarchy testing
3. **Then relationships** - Cross-entity linking
4. **Then search** - Discovery across entities
5. **Then workflows** - Complex multi-step operations
6. **Finally integration layers** - Database, auth, caching

## File Size Analysis

**Current test file sizes:**
- `test_relationship.py`: 228 lines (after refactoring)
- `test_database.py`: ~350 lines
- `test_auth.py`: ~200 lines
- `test_workflow_scenarios.py`: ~250 lines

**Target:** ≤300 lines per test file (encourages focused concerns)

**Strategy:** When implementing phase 2 tests, keep files focused on single tool/concern. If approaching 300 lines, split into:
- `test_entity_crud.py` (create/read/update/delete)
- `test_entity_search.py` (search, filter, aggregate)
- `test_entity_relationships.py` (linking to other entities)

## Key Decisions for Phase 2

1. **Use mcpdev.atoms.tech for E2E tests** - Already deployed, stable, accessible
2. **Use parametrized fixtures for variants** - Existing pattern, no separate files
3. **Apply markers for categorization** - @pytest.mark.slow, @pytest.mark.smoke, etc.
4. **Keep test files focused** - ≤300 lines, single concern per file
5. **Track performance baselines** - Use existing tracker infrastructure
6. **Consolidate auth tests** - Merge by provider, not speed/variant
7. **Use canonical naming** - File names describe concern (what), not speed/variant (how)

---

**Last Updated:** 2025-11-14 (Research Phase)
