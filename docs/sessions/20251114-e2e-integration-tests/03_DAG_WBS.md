# DAG & Work Breakdown Structure (WBS)

**Date:** November 14, 2025  
**Focus:** Task dependencies, critical path, and effort estimates

## Dependency Graph (DAG)

### Phase Dependencies
```
Phase 1: Foundation
    ↓ (depends on)
Phase 2: Core E2E Tests
    ├─ 2.1 Entity CRUD
    ├─ 2.2 Workspace Context (depends on 2.1)
    ├─ 2.3 Relationships (depends on 2.1)
    ├─ 2.4 Search (depends on 2.1)
    └─ 2.5 Workflow (depends on 2.1, 2.3)
    ↓ (all complete)
Phase 3: Integration Tests
    ├─ 3.1 Database (depends on nothing new)
    ├─ 3.2 Auth (depends on nothing new)
    ├─ 3.3 Cache (depends on nothing new)
    └─ 3.4 Infrastructure (depends on 3.1, 3.2, 3.3)
    ↓ (all complete)
Phase 4: Consolidation & Optimization
    ├─ 4.1 File consolidation (depends on phase 2, 3 complete)
    ├─ 4.2 Performance optimization (depends on 4.1)
    ├─ 4.3 Coverage achievement (depends on 4.1, 4.2)
    └─ 4.4 Fix slow/flaky tests (depends on 4.2)
    ↓ (all complete)
Phase 5: Archive & Documentation
    ├─ 5.1 Complete session docs
    ├─ 5.2 Archive OpenSpec
    ├─ 5.3 Update canonical docs
    ├─ 5.4 Update README
    └─ 5.5 Final validation
```

## User Story Dependencies

### Foundation User Stories (No Dependencies)
```
Epic 1: Organization Management
└─ Story 1.1: Create organization (FOUNDATION)
   ├─ Story 1.2: View org details (→ 1.1)
   ├─ Story 1.3: Update org settings (→ 1.1)
   ├─ Story 1.4: Delete org (→ 1.1)
   └─ Story 1.5: List orgs (→ 1.1)
```

### Project Dependency Chain
```
Story 1.1 (Create Org)
    ↓
Epic 2: Project Management
└─ Story 2.1: Create project (→ 1.1)
   ├─ Story 2.2: View project (→ 2.1)
   ├─ Story 2.3: Update project (→ 2.1)
   ├─ Story 2.4: Archive project (→ 2.1)
   └─ Story 2.5: List projects (→ 2.1)
        ↓
    Epic 3: Document Management
    └─ Story 3.1: Create document (→ 2.1)
         ├─ Story 3.2: View document (→ 3.1)
         └─ Story 3.3: List documents (→ 3.1)
              ↓
          Epic 4: Requirements Traceability
          └─ Story 4.1: Create requirement (→ 3.1)
               ├─ Story 4.2: Import requirements (→ 4.1)
               ├─ Story 4.3: Search requirements (→ 4.1)
               └─ Story 4.4: Trace links (→ 4.1)
```

### Workspace Dependencies
```
Epic 6: Workspace Navigation (Independent)
├─ Story 6.1: Get context (→ auth)
├─ Story 6.2-6.5: Set context (→ 1.1, 2.1, 3.1)
└─ Story 6.6: Get defaults (→ 6.1)
```

### Cross-Cutting Dependencies
```
Epic 7: Entity Relationships
├─ Story 7.1: Link entities (→ 1.1, 2.1, 3.1, 4.1, 5.1)
├─ Story 7.2: Unlink (→ 7.1)
├─ Story 7.3: View relationships (→ 7.1)
└─ Story 7.4: Check exists (→ 7.1)

Epic 8: Search & Discovery
├─ Story 8.1-8.5: Search (→ any entity)
├─ Story 8.6: Similar entities (→ 8.1-8.5)
└─ Story 8.7: Advanced operators (→ 8.1)

Epic 9: Workflow Automation
├─ Story 9.1: Run workflows (DONE ✓)
├─ Story 9.2: Project setup workflow (→ 1.1, 2.1, 3.1)
├─ Story 9.3: Import workflow (→ 4.1)
├─ Story 9.4: Bulk update workflow (→ any entity)
└─ Story 9.5: Onboarding workflow (→ 1.1, 2.1, 3.1)

Epic 10: Data Management
├─ Story 10.1: Batch create (→ 1.1)
├─ Story 10.2: Paginate (→ 10.1)
└─ Story 10.3: Sort (→ 10.1)

Epic 11: Security & Access
├─ Story 11.1: OAuth sign-in (→ auth config)
├─ Story 11.2: Session maintenance (→ 11.1)
├─ Story 11.3: Logout (→ 11.2)
└─ Story 11.4: RLS enforcement (→ 1.1)
```

## Critical Path Analysis

### Critical Path = Longest Dependency Chain
```
Phase 1 (1 day)
    ↓ (4h for planning)
Phase 2.1 Entity CRUD (2 days)
    ├→ Phase 2.2 Workspace (1 day)
    ├→ Phase 2.3 Relationships (1.5 days)
    ├→ Phase 2.4 Search (1.5 days)
    └→ Phase 2.5 Workflow (1 day)
    ↓ (all complete: 2 days max)
Phase 3 Integration (1.5 days)
    ↓
Phase 4 Consolidation (1 day)
    ↓
Phase 5 Archive & Docs (0.5 day)
```

**Critical Path Length:** 6 days
**Critical Tasks:** Foundation → Entity CRUD → Integration → Consolidation

### Parallel Opportunities
```
Phase 2 can parallelize:
┌─────────────────────────────────────────┐
│ Phase 2.1: Entity CRUD (2 days) - CRITICAL
│ Phase 2.2: Workspace (1 day) - can run in parallel
│ Phase 2.3: Relationships (1.5 days) - can run in parallel
│ Phase 2.4: Search (1.5 days) - can run in parallel
│ Phase 2.5: Workflow (1 day) - can run in parallel
└─────────────────────────────────────────┘
Effective time with parallelization: 2 days (instead of 5.5)

Phase 3 can parallelize:
┌─────────────────────────────────────────┐
│ 3.1 Database tests (0.5 day) - CRITICAL
│ 3.2 Auth tests (0.5 day) - can parallel
│ 3.3 Cache tests (0.5 day) - can parallel
│ 3.4 Infrastructure (0.5 day) - depends on 3.1,3.2,3.3
└─────────────────────────────────────────┘
Effective time with parallelization: 1 day (instead of 2)
```

## Work Breakdown Structure (WBS)

### Phase 1: Foundation (4 hours - Day 1)

**1.1 Session Documentation Setup (0.5h)**
- [ ] Create session folder: `docs/sessions/20251114-e2e-integration-tests/`
- [ ] Create all 6 core documents
- [ ] Setup OpenSpec change

**1.2 Existing Pattern Research (1.5h)**
- [ ] Analyze existing test infrastructure (conftest, fixtures)
- [ ] Review client variants and authentication patterns
- [ ] Document fixtures, markers, test patterns
- [ ] Identify non-canonical file names

**1.3 User Story Mapping (1h)**
- [ ] Extract all 48 user stories from epic summary
- [ ] Map each story to tools and operations
- [ ] Define test scenarios per story
- [ ] Create dependency matrix

**1.4 Architecture & Fixture Design (1h)**
- [ ] Design parametrized fixture strategy
- [ ] Plan marker categorization
- [ ] Define file organization
- [ ] Document patterns (assertions, errors, cleanup)

**Total Phase 1 Effort:** 4 hours (COMPLETED ✓)

---

### Phase 2.1: Entity CRUD E2E Tests (16 hours - Days 2-3)

**2.1.1 Organization Management Tests (3h)**
- [ ] Story 1.1: Create org tests (4 tests)
- [ ] Story 1.2: Read org tests (4 tests)
- [ ] Story 1.3: Update org tests (4 tests)
- [ ] Story 1.4: Delete org tests (4 tests)
- [ ] Story 1.5: List orgs tests (5 tests)
- [ ] **Total: 21 tests in `test_organization_management.py`**

**2.1.2 Project Management Tests (3h)**
- [ ] Story 2.1: Create project tests (4 tests)
- [ ] Story 2.2: Read project tests (4 tests)
- [ ] Story 2.3: Update project tests (4 tests)
- [ ] Story 2.4: Archive project tests (3 tests)
- [ ] Story 2.5: List projects tests (4 tests)
- [ ] **Total: 19 tests in `test_project_management.py`**

**2.1.3 Document Management Tests (2h)**
- [ ] Story 3.1: Create document tests (4 tests)
- [ ] Story 3.2: Read document tests (3 tests)
- [ ] Story 3.3: List documents tests (3 tests)
- [ ] **Total: 10 tests in `test_document_management.py`**

**2.1.4 Data Management Tests (2h)**
- [ ] Story 10.1: Batch create tests (3 tests)
- [ ] Story 10.2: Pagination tests (4 tests)
- [ ] Story 10.3: Sorting tests (5 tests)
- [ ] **Total: 12 tests in `test_data_management.py`**

**2.1.5 Test Implementation & Validation (6h)**
- [ ] Implement all entity CRUD tests
- [ ] Run against unit, integration, e2e
- [ ] Fix failures and flaky tests
- [ ] Verify all 50+ tests passing
- [ ] Document any issues in `05_KNOWN_ISSUES.md`

**Total Phase 2.1 Effort:** 16 hours

---

### Phase 2.2: Workspace Context Tests (8 hours - Days 3-4)

**2.2.1 Workspace Navigation Tests (2h)**
- [ ] Story 6.1: Get context tests (2 tests)
- [ ] Story 6.2-6.5: Set context tests (8 tests)
- [ ] Story 6.6: Get defaults tests (2 tests)
- [ ] **Total: 12 tests in `test_workspace_navigation.py`**

**2.2.2 Implementation & Validation (6h)**
- [ ] Implement workspace fixture architecture
- [ ] Implement all 12 tests
- [ ] Test against 3 client variants
- [ ] Verify all passing

**Total Phase 2.2 Effort:** 8 hours (can parallel with 2.1)

---

### Phase 2.3: Relationship Management Tests (12 hours - Days 4-5)

**2.3.1 Entity Relationships Tests (3h)**
- [ ] Story 7.1: Link tests (8 tests)
- [ ] Story 7.2: Unlink tests (4 tests)
- [ ] Story 7.3: View relationships tests (4 tests)
- [ ] Story 7.4: Check exists tests (2 tests)
- [ ] **Total: 18 tests in `test_entity_relationships.py`**

**2.3.2 Requirements Traceability Tests (3h)**
- [ ] Story 4.1: Create requirement tests (4 tests)
- [ ] Story 4.2: Import requirement tests (3 tests)
- [ ] Story 4.3: Search requirement tests (4 tests)
- [ ] Story 4.4: Trace links tests (3 tests)
- [ ] **Total: 14 tests in `test_requirements_traceability.py`**

**2.3.3 Test Case Management Tests (1h)**
- [ ] Story 5.1: Create test case tests (3 tests)
- [ ] Story 5.2: View test results tests (3 tests)
- [ ] **Total: 6 tests in `test_case_management.py`**

**2.3.4 Implementation & Validation (5h)**
- [ ] Implement all relationship/requirement/testcase tests
- [ ] Test across variants
- [ ] Fix failures

**Total Phase 2.3 Effort:** 12 hours (can parallel with 2.1)

---

### Phase 2.4: Search & Discovery Tests (12 hours - Days 5-6)

**2.4.1 Search & Discovery Tests (4h)**
- [ ] Story 8.1-8.5: Search operation tests (20 tests)
- [ ] Story 8.6: Similar entities tests (2 tests)
- [ ] Story 8.7: Advanced operators tests (3 tests)
- [ ] **Total: 25 tests in `test_search_and_discovery.py`**

**2.4.2 Implementation & Validation (8h)**
- [ ] Implement all search tests
- [ ] Setup test data for search
- [ ] Test across variants
- [ ] Performance validation

**Total Phase 2.4 Effort:** 12 hours (can parallel with 2.1)

---

### Phase 2.5: Workflow Automation Tests (6 hours - Days 6)

**2.5.1 Workflow Automation Tests (2h)**
- [ ] Story 9.2: Project setup workflow tests (3 tests)
- [ ] Story 9.3: Import workflow tests (3 tests)
- [ ] Story 9.4: Bulk update workflow tests (3 tests)
- [ ] Story 9.5: Onboarding workflow tests (3 tests)
- [ ] **Total: 13 tests in `test_workflow_automation.py`** (9.1 done)

**2.5.2 Implementation & Validation (4h)**
- [ ] Implement all workflow tests
- [ ] Test transaction semantics
- [ ] Test error recovery

**Total Phase 2.5 Effort:** 6 hours (can parallel with 2.1)

**Phase 2 Total (with parallelization):** ~2 days (8 hours/day work, 6 hours actual elapsed)

---

### Phase 3: Integration Tests (10 hours - Days 6-7)

**3.1 Auth Integration Tests (2.5h)**
- [ ] Story 11.1: OAuth sign-in tests (3 tests)
- [ ] Story 11.2: Session maintenance tests (3 tests)
- [ ] Story 11.3: Logout tests (2 tests)
- [ ] Story 11.4: RLS enforcement tests (4 tests)
- [ ] **Total: 12 tests in `test_auth_integration.py`**

**3.2 Database Integration Tests (3h)**
- [ ] Connection pooling tests (3 tests)
- [ ] Transaction isolation tests (4 tests)
- [ ] Query performance tests (5 tests)
- [ ] RLS enforcement tests (4 tests)
- [ ] Cascade behavior tests (4 tests)
- [ ] Concurrent operation tests (4 tests)
- [ ] Error handling tests (3 tests)
- [ ] **Total: 27 tests in `test_database_operations.py`**

**3.3 Cache Integration Tests (2h)**
- [ ] Redis connection tests (3 tests)
- [ ] Cache hit/miss tests (3 tests)
- [ ] Invalidation strategy tests (4 tests)
- [ ] TTL behavior tests (3 tests)
- [ ] Concurrency tests (3 tests)
- [ ] Fallback tests (2 tests)
- [ ] **Total: 18 tests in `test_cache_integration.py`**

**3.4 Infrastructure Tests (2.5h)**
- [ ] Health check tests (2 tests)
- [ ] Rate limiting tests (4 tests)
- [ ] Serialization tests (3 tests)
- [ ] Error middleware tests (4 tests)
- [ ] Auth middleware tests (4 tests)
- [ ] Logging tests (3 tests)
- [ ] Config loading tests (3 tests)
- [ ] Degradation tests (2 tests)
- [ ] **Total: 25 tests in `test_infrastructure.py`**

**Phase 3 Total (with parallelization):** ~1.5 days

---

### Phase 4: Consolidation & Optimization (6 hours - Days 7-8)

**4.1 Test File Consolidation (2h)**
- [ ] Identify all non-canonical files
- [ ] Merge files with duplicate concerns
- [ ] Apply fixture parametrization
- [ ] Delete old/redundant files
- [ ] Verify no test count reduction

**4.2 Performance Optimization (2h)**
- [ ] Identify slow tests (>5s)
- [ ] Optimize or mark @pytest.mark.slow
- [ ] Parallelize where possible
- [ ] Document baselines

**4.3 Coverage Achievement (1h)**
- [ ] Run coverage report
- [ ] Identify uncovered paths
- [ ] Add missing tests or mark intentional gaps
- [ ] Verify ≥95% coverage

**4.4 Fix Slow/Flaky Tests (1h)**
- [ ] Debug bearer auth test (5.44s)
- [ ] Debug database retry test (flaky)
- [ ] Implement fixes
- [ ] Verify stability

**Phase 4 Total:** 6 hours

---

### Phase 5: Archive & Documentation (4 hours - Day 8)

**5.1 Complete Session Documentation (1h)**
- [ ] Finalize all 6 session docs
- [ ] Cross-reference throughout
- [ ] Review for completeness

**5.2 Archive OpenSpec Change (0.5h)**
- [ ] Verify all tasks checked
- [ ] Run final test suite
- [ ] Run openspec archive command
- [ ] Verify specs merged

**5.3 Update Canonical Docs (1h)**
- [ ] Update `docs/TESTING.md`
- [ ] Document canonical naming
- [ ] Add fixture examples
- [ ] Add marker reference

**5.4 Update Project README (1h)**
- [ ] Add test running examples
- [ ] Document test coverage
- [ ] Add test results dashboard link
- [ ] Add troubleshooting

**5.5 Final Validation (0.5h)**
- [ ] Run full suite locally
- [ ] Run full suite on deployment
- [ ] Generate coverage report
- [ ] Create git commit

**Phase 5 Total:** 4 hours

---

## Overall Effort Summary

| Phase | Duration | Effort (hours) | Status |
|-------|----------|----------------|--------|
| **Phase 1: Foundation** | Day 1 | 4h | ✅ COMPLETED |
| **Phase 2: Core E2E** | Days 2-5 | 54h work / 2d elapsed* | ⏳ Ready to start |
| **Phase 3: Integration** | Days 6-7 | 10h work / 1.5d elapsed* | ⏳ Queued |
| **Phase 4: Consolidation** | Days 7-8 | 6h work / 1d elapsed* | ⏳ Queued |
| **Phase 5: Archive** | Day 8 | 4h work / 0.5d elapsed* | ⏳ Queued |
| **TOTAL** | ~5 days | 78h work / 5d elapsed* | **Ready** |

*With parallelization of Phase 2 subtasks

## Resource Allocation

- **Primary:** 1 AI agent (Claude Code) - autonomous
- **Time:** 5 consecutive days, ~8 hours/day
- **Deployment:** mcpdev.atoms.tech (stable, available)
- **Test Environment:** Supabase (configured), AuthKit (available)

---

**Last Updated:** 2025-11-14 (WBS/DAG)
