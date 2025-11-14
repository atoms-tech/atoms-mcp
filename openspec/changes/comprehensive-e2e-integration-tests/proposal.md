# Comprehensive E2E & Integration Test Coverage

## Summary

Build out complete end-to-end and integration test suites to achieve 95%+ coverage across all MCP tools and user stories. Currently only 1/48 user stories have test coverage (2%). This proposal maps all 48 user stories to concrete test scenarios and delivers production-grade test implementations across all tool layers.

## Motivation

**Current State:**
- E2E tests exist but are sparse: only 115/1415 tests execute (rest skipped)
- User story coverage: 1/48 (2%) - only "run workflows with transactions" is tested
- Test gaps across all major features: CRUD, workspace, relationships, search, auth, security
- The deployment is working (mcpdev.atoms.tech) but test coverage doesn't reflect actual capabilities

**Why This Matters:**
- Incomplete test coverage hides regressions and bugs
- Deployment confidence is low with 2% story coverage
- New features added without test protection
- Team cannot safely refactor or optimize
- Missing acceptance tests for business requirements

## Scope

### Included in This Change
1. **Comprehensive user story mapping** - All 48 stories mapped to specific test scenarios
2. **E2E test implementation** - Full-flow tests for entity CRUD, workspace, relationships, search, workflow
3. **Integration tests** - Database, auth, storage, infrastructure layer tests
4. **Test file consolidation** - Apply canonical naming; eliminate duplicate concerns
5. **Fixture and marker optimization** - Use parametrization instead of file duplication
6. **Coverage validation** - Ensure 95%+ code coverage across all layers
7. **Performance baseline tests** - Document and test latency/throughput targets

### Not Included (Out of Scope)
- Load testing at scale (>1000 concurrent users) - separate performance work
- Cross-region deployment testing - infrastructure testing phase
- Client SDK tests - only MCP tool interface
- Visual/UI regression tests - frontend work
- Security penetration testing - dedicated security phase

## User Story Mapping

### Organization Management (5 stories)
- [ ] Create organization with metadata
- [ ] View organization details and members
- [ ] Update organization settings (name, description, rate limits)
- [ ] Delete organization (soft delete + cascade)
- [ ] List all organizations for authenticated user

**Tools Required:** `entity_tool` (org create/read/list), `relationship_tool` (members)

### Project Management (5 stories)
- [ ] Create project within organization
- [ ] View project details and hierarchy
- [ ] Update project info (name, status, archived)
- [ ] Archive/unarchive project
- [ ] List projects in organization (with pagination)

**Tools Required:** `entity_tool`, `relationship_tool` (org→project membership)

### Document Management (3 stories)
- [ ] Create document within project
- [ ] View document content and metadata
- [ ] List documents in project (with filtering)

**Tools Required:** `entity_tool`, `relationship_tool` (project→document)

### Requirements Traceability (4 stories)
- [ ] Create requirements from structured templates
- [ ] Import requirements via workflow
- [ ] Search requirements by text/tags/status
- [ ] Trace links: requirement→test→implementation

**Tools Required:** `entity_tool`, `data_query`, `relationship_tool` (requirement_test)

### Test Case Management (2 stories)
- [ ] Create test cases linked to requirements
- [ ] View test results and coverage metrics

**Tools Required:** `entity_tool`, `relationship_tool` (requirement_test)

### Workspace Navigation (6 stories)
- [ ] Get current workspace context (org/project/document)
- [ ] Switch to organization workspace
- [ ] Switch to project workspace
- [ ] Switch to document workspace
- [ ] List all available workspaces
- [ ] Get workspace defaults (templates, rate limits)

**Tools Required:** `workspace_tool` (all operations)

### Entity Relationships (4 stories)
- [ ] Link entities (member, assignment, trace_link, etc.)
- [ ] Unlink related entities
- [ ] View entity relationships (inbound/outbound)
- [ ] Check if entities are related (exists check)

**Tools Required:** `relationship_tool` (all relationship types)

### Search & Discovery (7 stories)
- [ ] Keyword search across all entity types
- [ ] Filter search results (by type, owner, status, date)
- [ ] Semantic search using embeddings
- [ ] Hybrid search (keyword + semantic combined)
- [ ] Get entity count aggregates (summary stats)
- [ ] Find similar entities by embedding distance
- [ ] Advanced search with AND/OR/NOT operators

**Tools Required:** `data_query` (search operations)

### Workflow Automation (5 stories)
- [ ] ✅ Run workflows with transactions (DONE)
- [ ] Set up new project workflow (scaffold entities)
- [ ] Import requirements via workflow (batch create)
- [ ] Bulk update statuses (batch update + transaction)
- [ ] Onboard new organization (multi-step workflow)

**Tools Required:** `workflow_execute`, `entity_tool` (batch operations)

### Data Management (3 stories)
- [ ] Batch create multiple entities (>1000 items)
- [ ] Paginate through large lists (offset + limit)
- [ ] Sort query results (by name, date, custom fields)

**Tools Required:** `entity_tool` (batch, pagination, sorting)

### Security & Access (4 stories)
- [ ] Authenticate via AuthKit OAuth flow
- [ ] Maintain active session (token refresh)
- [ ] Log out securely (token revocation)
- [ ] Row-level security prevents cross-user access

**Tools Required:** Auth provider, `workspace_tool` (context verification)

## Design Decisions

### Test File Organization (Canonical Naming)

**Decision:** Use concern-based naming, not speed/variant-based.

**Rationale:**
- Fixtures + markers handle test variants (no separate files for unit/integration/e2e)
- File names describe "what's tested", not "how fast" or "which variant"
- Canonical naming makes duplicate concerns obvious → consolidation opportunity
- Reduces clutter (no `_fast`, `_slow`, `_unit`, `_integration`, `_final`, `_v2` suffixes)

**Structure:**
```
tests/
  e2e/
    test_entity_crud.py           # All entity CRUD tests (parametrized variants)
    test_workspace_context.py     # All workspace context tests
    test_relationship_management.py # All relationship tests
    test_search_and_discovery.py  # All search operations
    test_workflow_execution.py    # All workflow tests
    test_organization_management.py # All org management
    test_auth_patterns.py         # Auth scenarios (different providers)
  integration/
    test_database_operations.py   # All database integration
    test_auth_integration.py      # Auth provider integration (Supabase, AuthKit)
    test_cache_integration.py     # Upstash Redis caching
    test_infrastructure.py        # Full infrastructure stack
```

### Test Fixtures & Parametrization

**Decision:** Use `@pytest.fixture(params=[...])` for test variants, not separate files.

**Rationale:**
- One source of truth per test concern
- Same test logic runs across unit/integration/e2e variants automatically
- Adding variant only requires fixture change
- Eliminates code duplication

**Example:**
```python
@pytest.fixture(params=["unit", "integration", "e2e"])
def mcp_client(request):
    if request.param == "unit":
        return InMemoryMcpClient()  # Mock
    elif request.param == "integration":
        return HttpMcpClient(url="http://localhost:8000")
    elif request.param == "e2e":
        return HttpMcpClient(url="https://mcpdev.atoms.tech/api/mcp")
    return get_client(request.param)

async def test_entity_creation(mcp_client):
    """Runs 3 times: unit, integration, e2e."""
    result = await mcp_client.entity_tool(
        entity_type="project",
        operation="create",
        data={"name": "Test Project"}
    )
    assert result["success"]
```

### Consolidation Strategy

**Decision:** Merge test files with overlapping concerns; eliminate duplication.

**Action Items:**
1. Consolidate `test_auth.py` + `test_auth_patterns.py` → separate by provider (supabase vs authkit)
2. Merge `test_entity_*.py` files → single `test_entity_crud.py` with variant fixtures
3. Move slow/fast/unit/integration suffixes → markers/fixtures
4. Eliminate temporal suffixes (`_old`, `_new`, `_final`, `_v2`) → delete or consolidate

## Implementation Tasks

See `tasks.md` for detailed step-by-step checklist.

## Rollout Plan

### Phase 1: Foundation (Days 1-2)
- Create OpenSpec proposal (this document)
- Map all 48 user stories to test scenarios
- Define test fixture architecture
- Set up session documentation in `docs/sessions/`

### Phase 2: Core E2E Tests (Days 3-5)
- Implement E2E tests for 5 major tools (entity, workspace, relationship, workflow, query)
- Organize tests with canonical naming
- Apply fixture parametrization for variants
- Run and validate against mcpdev deployment

### Phase 3: Integration Tests (Days 5-7)
- Implement database integration tests
- Implement auth integration tests (Supabase, AuthKit)
- Implement caching integration tests (Upstash Redis)
- Implement infrastructure layer tests

### Phase 4: Consolidation & Optimization (Day 7-8)
- Consolidate test files with duplicate concerns
- Apply markers for categorization
- Verify 95%+ coverage across layers
- Fix slow/flaky tests

### Phase 5: Archive & Documentation (Day 8)
- Archive OpenSpec change after all tests pass
- Update canonical test documentation
- Move session docs to archive
- Update README with test running instructions

## Rollback Plan

**If tests fail during implementation:**
1. **Revert to previous git state** - `git reset --hard HEAD~1`
2. **Identify failure type** - Infrastructure (DB/auth), test logic, or fixture issue
3. **Fix and re-test** - Don't stash; fix forward
4. **Document in 05_KNOWN_ISSUES.md** if bug found in production code

**If coverage drops below 95%:**
1. **Identify uncovered code paths** - Run coverage report
2. **Add missing tests** - Don't reduce coverage target
3. **Document any intentional gaps** - Mark with `# pragma: no cover` if truly untestable

**If deployment breaks:**
1. **Restore mcpdev to last known good state**
2. **Run integration tests locally** first before re-deploying
3. **Document findings in 05_KNOWN_ISSUES.md**

## Success Criteria

- ✅ All 48 user stories have passing E2E tests
- ✅ Code coverage ≥ 95% across all layers
- ✅ No test duplication (consolidated with canonical naming)
- ✅ All tests pass in CI/CD pipeline
- ✅ Performance baselines established (<5s for single operations, <30s for batch)
- ✅ No slow tests (>5s) except explicitly marked `@pytest.mark.slow`
- ✅ No flaky tests (all pass consistently, no retry logic needed)
- ✅ Session documentation complete and archived

## ARUs (Assumptions, Risks, Uncertainties)

### Assumptions
- ✅ mcpdev.atoms.tech deployment is stable and will remain available during testing
- ✅ Supabase database has test user account (kooshapari@kooshapari.com)
- ✅ AuthKit OAuth integration is working as deployed
- ✅ Rate limiting middleware is not blocking test requests

### Risks
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| **mcpdev deployment unavailable** | Medium | High | Have fallback to local HTTP server; use mocks if needed |
| **Test user data conflicts** | High | Medium | Use isolated test workspaces; clean up after each test |
| **Rate limiting blocks tests** | Medium | Medium | Disable rate limiting in test config or add test API key |
| **Auth token expiration** | Low | Low | Refresh tokens automatically in fixture; handle 401 gracefully |
| **Database performance** | Low | Low | Monitor slow queries; index as needed |
| **Fixture complexity** | Medium | Medium | Start simple; add parametrization gradually |

### Uncertainties
- **Which user story tests are already partial?** - Will discover during review phase
- **Are there hidden test dependencies?** - Will identify during test execution
- **Does mcpdev have enough rate limit quota?** - May need to adjust test concurrency
- **Will all tests pass on first try?** - Unlikely; expect iteration cycle

