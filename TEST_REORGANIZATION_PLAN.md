# Test Reorganization Plan

## Current Issues

### Misclassified Tests
Several test files in `tests/unit/` are actually E2E or integration tests:

1. **test_workflow_automation.py** (13 tests)
   - Currently: `tests/unit/tools/test_workflow_automation.py`
   - Should be: `tests/integration/workflows/` (needs real database)
   - Reason: Tests create real entities in database

2. **test_workflow_advanced.py** (multiple tests)
   - Currently: `tests/unit/tools/test_workflow_advanced.py`
   - Should be: `tests/integration/workflows/`
   - Reason: Tests complex workflows with database

3. **test_workspace.py** (multiple tests)
   - Currently: `tests/unit/tools/test_workspace.py`
   - Should be: `tests/integration/workspace/`
   - Reason: Tests workspace context management

4. **test_workspace_navigation.py** (multiple tests)
   - Currently: `tests/unit/tools/test_workspace_navigation.py`
   - Should be: `tests/integration/workspace/`
   - Reason: Tests navigation with database

## Reorganization Strategy

### Phase 1: Identify Test Types
- [ ] Audit all 158 failing tests
- [ ] Classify as: unit (mock), integration (real DB), or e2e (real HTTP)
- [ ] Document classification

### Phase 2: Move Tests
- [ ] Move integration tests to `tests/integration/`
- [ ] Keep e2e tests in `tests/e2e/`
- [ ] Keep unit tests in `tests/unit/` with proper mocks

### Phase 3: Fix Tests
- [ ] Add proper mocks to unit tests
- [ ] Add database setup/teardown to integration tests
- [ ] Verify e2e tests make real HTTP calls

### Phase 4: Verify
- [ ] Run full test suite
- [ ] Achieve 100% pass rate
- [ ] Document test organization

## Expected Outcome

After reorganization:
- **Unit tests:** Fast, isolated, mocked (< 100ms each)
- **Integration tests:** Real database, proper setup/teardown
- **E2E tests:** Real HTTP, real server, real auth

All tests passing with clear organization and governance.

