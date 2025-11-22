# Session Overview: E2E Integration Tests & Canonical Organization

**Date:** 2025-11-22  
**OpenSpec Change:** `comprehensive-e2e-integration-tests`  
**Goal:** Complete E2E test coverage (95%+), fix skipped/flaky tests, organize with canonical naming following AGENTS.md governance

## Current State

- ✅ 236 E2E tests passing
- ⚠️ 8 tests skipped (permission middleware)
- ⚠️ 2 flaky tests (database_connection_retry, workflow_with_retry)
- ❌ 1546 tests deselected (not marked as e2e)
- ❌ Coverage unknown (need to measure)

## Key Decisions

1. **Canonical Test Naming:** Use concern-based names (test_entity_crud.py), not speed/variant-based (test_entity_fast.py)
2. **Fixture Parametrization:** Use @pytest.fixture(params=[...]) for unit/integration/e2e variants instead of separate files
3. **Test Consolidation:** Merge overlapping test files (e.g., test_auth.py + test_auth_patterns.py)
4. **Marker Usage:** Use @pytest.mark.slow, @pytest.mark.smoke, etc. for categorization
5. **Coverage Target:** 95%+ across all layers (services, infrastructure, tools)

## Phases

1. ✅ **Phase 1:** Fix OpenSpec proposal, create spec deltas
2. 🔄 **Phase 2:** Analyze test state, create session docs
3. ⏳ **Phase 3:** Consolidate test files with canonical naming
4. ⏳ **Phase 4:** Fix skipped & flaky tests
5. ⏳ **Phase 5:** Achieve 95%+ coverage, optimize performance
6. ⏳ **Phase 6:** Archive OpenSpec change, final validation

## Success Criteria

- ✅ All 48 user stories have passing E2E tests
- ✅ Code coverage ≥95% across all layers
- ✅ No test duplication (canonical naming)
- ✅ All tests pass consistently (no flakiness)
- ✅ No slow tests (>5s) unless marked @pytest.mark.slow
- ✅ Session documentation complete

## Related Documents

- `01_RESEARCH.md` - Test pattern analysis
- `02_SPECIFICATIONS.md` - User story mapping
- `03_DAG_WBS.md` - Task dependencies
- `04_IMPLEMENTATION_STRATEGY.md` - Technical approach
- `05_KNOWN_ISSUES.md` - Findings & blockers
- `06_TESTING_STRATEGY.md` - Test approach & fixtures

## OpenSpec Reference

See `openspec/changes/comprehensive-e2e-integration-tests/` for:
- `proposal.md` - Why, what, scope, design decisions
- `tasks.md` - Implementation checklist (170 tasks)
- `specs/testing/spec.md` - Requirements and scenarios

