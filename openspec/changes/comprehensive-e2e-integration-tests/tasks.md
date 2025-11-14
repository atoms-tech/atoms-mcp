# Comprehensive E2E & Integration Tests - Implementation Tasks

## Phase 1: Foundation (Days 1-2)

### 1.1 Create session documentation structure
- [ ] Create `docs/sessions/20251114-e2e-integration-tests/` directory
- [ ] Create `00_SESSION_OVERVIEW.md` with goals and decisions
- [ ] Create `01_RESEARCH.md` (findings on existing patterns)
- [ ] Create `02_SPECIFICATIONS.md` (user story specs, tool mappings)
- [ ] Create `03_DAG_WBS.md` (task dependencies)
- [ ] Create `04_IMPLEMENTATION_STRATEGY.md` (architecture, patterns)
- [ ] Create `05_KNOWN_ISSUES.md` (placeholder for findings)
- [ ] Create `06_TESTING_STRATEGY.md` (approach, fixtures, markers)

**Acceptance:** All session docs exist and reference this OpenSpec change

### 1.2 Analyze existing test patterns
- [ ] Review current E2E test files: structure, patterns, naming
- [ ] Review existing conftest fixtures: client types, parametrization
- [ ] Review existing integration tests: database, auth, infrastructure
- [ ] Document findings in `01_RESEARCH.md`
- [ ] List all non-canonical test file names for consolidation
- [ ] Identify test duplication candidates

**Acceptance:** Comprehensive research doc showing existing patterns and consolidation candidates

### 1.3 Map user stories to test scenarios
- [ ] Extract all 48 user stories from epic summary
- [ ] For each story: identify required MCP tools and operations
- [ ] Create test scenario matrix (story → tools → test file → assertions)
- [ ] Document in `02_SPECIFICATIONS.md`
- [ ] Identify dependencies between user stories
- [ ] Flag circular dependencies or complex sequences

**Acceptance:** Complete mapping doc with all 48 stories → test scenarios

### 1.4 Design test fixture architecture
- [ ] Define base fixtures for each client variant (unit, integration, e2e)
- [ ] Plan parametrization strategy for test variants
- [ ] Define marker categories (@pytest.mark.slow, @pytest.mark.smoke, etc.)
- [ ] Document fixture usage patterns
- [ ] Plan auth fixture for different providers (Supabase, AuthKit)
- [ ] Document in `04_IMPLEMENTATION_STRATEGY.md`

**Acceptance:** Architecture doc with fixture code examples and markers

### 1.5 Define test file organization
- [ ] Create canonical test file list (by tool/concern)
- [ ] Plan file consolidation (which existing files to merge)
- [ ] Plan directory structure (tests/e2e vs tests/integration)
- [ ] Document naming conventions in `02_SPECIFICATIONS.md`

**Acceptance:** Clear mapping of all test files and their canonical names

## Phase 2: Core E2E Tests (Days 3-5)

### 2.1 Implement entity CRUD E2E tests
- [ ] Create `tests/e2e/test_entity_crud.py` (canonical)
- [ ] Implement tests for all entity types (org, project, document, requirement, test_case)
- [ ] Test CREATE with auth and validation
- [ ] Test READ with entity ID and fuzzy matching
- [ ] Test UPDATE with validation and soft delete
- [ ] Test DELETE (soft and hard)
- [ ] Test BATCH create with transaction
- [ ] Test error handling (invalid input, unauthorized, not found)
- [ ] Test pagination (limit, offset, ordering)
- [ ] Parametrize for unit/integration/e2e variants
- [ ] Add performance markers for slow tests

**Acceptance:** 
- All entity CRUD operations tested (50+ tests)
- All tests pass on mcpdev.atoms.tech
- No tests marked @pytest.mark.skip
- Coverage for entity_tool ≥95%

### 2.2 Implement workspace context E2E tests
- [ ] Create `tests/e2e/test_workspace_context.py` (canonical)
- [ ] Test get_context for each context type (org, project, document)
- [ ] Test set_context (switching workspaces)
- [ ] Test list_workspaces (all available contexts)
- [ ] Test get_defaults (smart defaults per context)
- [ ] Test context persistence across operations
- [ ] Test context switching with invalid IDs
- [ ] Test with fuzzy entity name resolution

**Acceptance:**
- All workspace operations tested (20+ tests)
- All tests pass
- Coverage for workspace_tool ≥95%

### 2.3 Implement relationship management E2E tests
- [ ] Create `tests/e2e/test_relationship_management.py` (canonical)
- [ ] Test LINK operations for each relationship type:
  - [ ] member (org/project members)
  - [ ] assignment (task assignments)
  - [ ] trace_link (requirement traceability)
  - [ ] requirement_test (test coverage)
- [ ] Test UNLINK (remove relationships)
- [ ] Test LIST (relationships for entity)
- [ ] Test CHECK (relationship exists)
- [ ] Test UPDATE (relationship metadata)
- [ ] Test error handling (invalid types, circular links)
- [ ] Test cascading behavior (soft delete → relationship update)

**Acceptance:**
- All relationship operations tested (40+ tests)
- All relationship types covered
- All tests pass
- Coverage for relationship_tool ≥95%

### 2.4 Implement search and discovery E2E tests
- [ ] Create `tests/e2e/test_search_and_discovery.py` (canonical)
- [ ] Test keyword search (text-based, partial matches)
- [ ] Test filter operations (by type, owner, status, date)
- [ ] Test semantic search (embedding-based similarity)
- [ ] Test hybrid search (keyword + semantic combined)
- [ ] Test aggregates (count by type, status, owner)
- [ ] Test similar entities (find by embedding distance)
- [ ] Test advanced search operators (AND, OR, NOT)
- [ ] Test pagination in search results
- [ ] Test performance on large result sets (1000+ items)

**Acceptance:**
- All search operations tested (35+ tests)
- All search types working
- All tests pass
- Coverage for data_query search ≥95%

### 2.5 Implement workflow execution E2E tests
- [ ] Create `tests/e2e/test_workflow_execution.py` (canonical)
- [ ] Test simple workflow (single tool call)
- [ ] Test multi-step workflow (chained operations)
- [ ] Test workflow with transactions (all-or-nothing)
- [ ] Test rollback on error (partial failure recovery)
- [ ] Test workflow with retry logic (transient failures)
- [ ] Test workflow performance (execution time)
- [ ] Test concurrent workflow execution (no conflicts)
- [ ] Test workflow state persistence

**Acceptance:**
- All workflow operations tested (25+ tests)
- Transaction semantics verified
- All tests pass
- Coverage for workflow_execute ≥95%

### 2.6 Organize and consolidate existing E2E tests
- [ ] Review all existing E2E test files
- [ ] Identify files with non-canonical names (suffixes: _fast, _slow, _unit, _integration, _old, _new, _final)
- [ ] Plan consolidation strategy (which files to merge)
- [ ] Merge `test_auth.py` + `test_auth_patterns.py` → organize by provider
- [ ] Apply fixture parametrization to eliminate file duplication
- [ ] Remove temporal suffixes and cleanup
- [ ] Verify all tests still pass after consolidation

**Acceptance:**
- All E2E test files use canonical names
- No duplicate test code
- All existing tests still pass

## Phase 3: Integration Tests (Days 5-7)

### 3.1 Implement database integration tests
- [ ] Create `tests/integration/test_database_operations.py` (canonical)
- [ ] Test connection pooling and lifecycle
- [ ] Test transaction isolation (read committed, etc.)
- [ ] Test query performance (basic and complex queries)
- [ ] Test row-level security (RLS) enforcement
- [ ] Test soft delete and restore operations
- [ ] Test cascade behavior (delete org → projects, documents)
- [ ] Test concurrent operations (no race conditions)
- [ ] Test database error handling (timeout, constraint violations)

**Acceptance:**
- All database operations tested (40+ tests)
- RLS verified for access control
- Performance baselines established
- All tests pass
- Coverage for database adapter ≥95%

### 3.2 Implement auth integration tests
- [ ] Create `tests/integration/test_auth_integration.py` (canonical)
- [ ] Test Supabase JWT token validation
- [ ] Test AuthKit OAuth flow (sign-in, sign-out)
- [ ] Test token refresh (expiration handling)
- [ ] Test session lifecycle (creation, persistence, cleanup)
- [ ] Test permission validation (who can access what)
- [ ] Test rate limiting by user/API key
- [ ] Test auth errors (401, 403, expired token)
- [ ] Test mixed auth scenarios (different providers)

**Acceptance:**
- All auth flows tested (30+ tests)
- Both providers verified
- Token lifecycle working correctly
- All tests pass
- Coverage for auth layer ≥95%

### 3.3 Implement cache integration tests
- [ ] Create `tests/integration/test_cache_integration.py` (canonical)
- [ ] Test Upstash Redis connection
- [ ] Test cache hit/miss rates
- [ ] Test cache invalidation on entity changes
- [ ] Test TTL expiration behavior
- [ ] Test concurrent cache access (thread-safe)
- [ ] Test cache performance (latency impact)
- [ ] Test fallback if cache unavailable
- [ ] Test cache cleanup on app shutdown

**Acceptance:**
- All cache operations tested (25+ tests)
- Hit/miss tracking verified
- Invalidation strategy working
- All tests pass
- Coverage for caching layer ≥95%

### 3.4 Implement infrastructure layer tests
- [ ] Create `tests/integration/test_infrastructure.py` (canonical)
- [ ] Test health check endpoint
- [ ] Test rate limiting middleware
- [ ] Test request/response serialization
- [ ] Test error handling middleware
- [ ] Test auth middleware integration
- [ ] Test logging and observability
- [ ] Test configuration loading (env vars)
- [ ] Test graceful degradation (missing services)

**Acceptance:**
- All infrastructure components tested (30+ tests)
- All middleware functional
- Degradation paths verified
- All tests pass
- Coverage for server/app layers ≥95%

## Phase 4: Consolidation & Optimization (Days 7-8)

### 4.1 Consolidate test files with duplicate concerns
- [ ] Identify all test files with overlapping coverage
- [ ] Merge files with same component/tool focus
- [ ] Apply fixture parametrization for unit/integration/e2e variants
- [ ] Apply markers for categorization (speed, type, etc.)
- [ ] Delete old/redundant test files
- [ ] Verify no test count reduction (same tests, better organized)

**Acceptance:**
- No duplicate test files
- All test counts preserved (or increased)
- All tests still pass
- Canonical naming used throughout

### 4.2 Optimize test execution and performance
- [ ] Identify slow tests (>5s execution)
- [ ] Mark with @pytest.mark.slow
- [ ] Parallelize test execution where possible
- [ ] Optimize fixture setup/teardown
- [ ] Cache expensive operations (embeddings, etc.)
- [ ] Document performance baselines

**Acceptance:**
- No unintended slow tests
- Default test run <5 minutes
- Full suite (including slow) <15 minutes
- Performance baseline documented

### 4.3 Achieve and verify 95%+ coverage
- [ ] Run coverage report across all layers
- [ ] Identify uncovered code paths
- [ ] Add tests for missing coverage
- [ ] Mark intentional gaps with `# pragma: no cover`
- [ ] Verify ≥95% coverage for all modules

**Acceptance:**
- Overall coverage ≥95%
- All core modules ≥90% coverage
- No accidental uncovered code paths
- Coverage report saved to `tests/reports/coverage.html`

### 4.4 Fix slow and flaky tests
- [ ] Review test_bearer_auth_invalid_token (currently 5.44s)
- [ ] Review test_database_connection_retry (currently flaky)
- [ ] Identify root causes
- [ ] Implement fixes (optimize, stabilize, mock where needed)
- [ ] Verify no regressions in fixed tests

**Acceptance:**
- All tests pass consistently
- No test >5s unless marked @pytest.mark.slow
- No flaky tests (all pass on first run)
- All tests deterministic (no randomness issues)

## Phase 5: Archive & Documentation (Day 8)

### 5.1 Complete session documentation
- [ ] Update `00_SESSION_OVERVIEW.md` with completion summary
- [ ] Finalize `01_RESEARCH.md` with all findings
- [ ] Complete `02_SPECIFICATIONS.md` with test scenarios
- [ ] Document `03_DAG_WBS.md` with actual execution times
- [ ] Finalize `04_IMPLEMENTATION_STRATEGY.md` with lessons learned
- [ ] Document findings in `05_KNOWN_ISSUES.md`
- [ ] Complete `06_TESTING_STRATEGY.md` with results

**Acceptance:** All session docs complete and cross-referenced

### 5.2 Archive OpenSpec change
- [ ] Verify all tasks in this file checked off
- [ ] Run final test suite: `python cli.py test run --coverage`
- [ ] Verify coverage ≥95%
- [ ] Update OpenSpec specs with final mappings
- [ ] Run `openspec archive comprehensive-e2e-integration-tests -y`
- [ ] Verify change moved to archive

**Acceptance:** OpenSpec change archived; specs merged into main specs/

### 5.3 Update canonical test documentation
- [ ] Update `docs/TESTING.md` with new test structure
- [ ] Document canonical test naming rules
- [ ] Document how to run different test scopes
- [ ] Document fixture and marker patterns
- [ ] Add examples for adding new tests

**Acceptance:** Test documentation complete and up-to-date

### 5.4 Update project README
- [ ] Add test running examples
- [ ] Document test coverage expectations
- [ ] Add test results dashboard link
- [ ] Document test layers (unit/integration/e2e)
- [ ] Add troubleshooting guide

**Acceptance:** README includes complete test guidance

### 5.5 Final validation and commit
- [ ] Run full test suite locally: `python cli.py test run`
- [ ] Run full test suite on deployment: `python cli.py test run:e2e`
- [ ] Verify all 48 user stories have passing tests
- [ ] Generate final coverage report
- [ ] Create git commit with summary of changes
- [ ] Push to feature branch and create PR (if needed)

**Acceptance Criteria:**
- ✅ All 48 user stories have passing tests
- ✅ Code coverage ≥95% across all layers
- ✅ All tests pass in CI/CD pipeline
- ✅ No test duplication
- ✅ Canonical test naming throughout
- ✅ Session documentation complete and archived
- ✅ Ready for merge to main

---

## Execution Notes

### How to Track Progress
1. Update this file as you complete each task
2. Mark complete with `[x]` 
3. Update todo list in parallel: `TodoWrite` tool
4. Document blockers or findings in session docs

### Key Commands
```bash
# Run all tests
python cli.py test run

# Run specific scope
python cli.py test run --scope unit
python cli.py test run --scope integration
python cli.py test run --scope e2e

# Run with coverage
python cli.py test run --coverage

# Run specific test file
uv run pytest tests/e2e/test_entity_crud.py -v

# Run specific marker
uv run pytest -m "not slow" -v

# Generate coverage report
uv run pytest --cov=. --cov-report=html
```

### Git Commands
```bash
# Check status
git status

# See changes
git diff

# Create feature branch (if needed)
git checkout -b feature/e2e-integration-tests

# Commit progress
git add .
git commit -m "feat: Add E2E tests for [feature]"
```

### How to Handle Failures
1. **Test fails** → Debug, fix, re-run. Don't skip without understanding.
2. **Coverage drops** → Add missing tests, not reducing expectations.
3. **Deployment breaks** → Revert, understand, fix forward. No rollbacks.
4. **Slow test** → Investigate (mock, parallelize, optimize), mark as @pytest.mark.slow if justified.
5. **Flaky test** → Fix root cause (race condition, timing), add deterministic assertions.

