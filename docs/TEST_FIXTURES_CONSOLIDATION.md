# Test Fixtures Consolidation Plan

## Overview

Analysis of test fixture duplication and consolidation opportunities across the test suite.

## Current State

### Fixture Locations

**Root Level:**
- `tests/conftest.py` - Global fixtures (auth tokens, service modes, mock services)

**Unit Tests:**
- `tests/unit/tools/conftest.py` - Unit test fixtures (mcp_client_inmemory, call_mcp)
- `tests/unit/extensions/conftest.py` - Extension-specific fixtures

**Integration Tests:**
- `tests/integration/conftest.py` - Integration fixtures (mcp_client_http, test_server)
- `tests/integration/workspace/conftest.py` - Workspace-specific fixtures

**E2E Tests:**
- `tests/e2e/conftest.py` - E2E fixtures (e2e_auth_token, imports from fixtures/)
- `tests/e2e/fixtures/client.py` - Client fixtures
- `tests/e2e/fixtures/scenarios.py` - Scenario fixtures
- `tests/e2e/fixtures/monitoring.py` - Monitoring fixtures

**Framework:**
- `tests/framework/conftest_shared.py` - Shared parametrized fixtures
- `tests/framework/test_base.py` - Base test classes with fixtures

### Duplicate Patterns Found

#### 1. Client Fixture Definitions

**Pattern:** Multiple definitions of similar client fixtures

**Locations:**
- `tests/unit/tools/conftest.py` - `mcp_client_inmemory` fixture
- `tests/framework/conftest_shared.py` - `parametrized_client` fixture
- `tests/framework/test_base.py` - `client_variants` fixture
- `tests/e2e/fixtures/client.py` - `mcp_client`, `end_to_end_client` fixtures

**Analysis:**
- `mcp_client_inmemory` defined in unit conftest
- `parametrized_client` in framework provides unified access
- `test_base.py` has similar parametrization pattern
- E2E has separate client fixtures

**Recommendation:**
- Consolidate into `tests/framework/conftest_shared.py`
- Use parametrized fixture pattern consistently
- Each layer (unit/integration/e2e) imports from framework

#### 2. Auth Token Fixtures

**Pattern:** Multiple auth token fixtures

**Locations:**
- `tests/conftest.py` - `authkit_auth_token` (function-scoped)
- `tests/e2e/conftest.py` - `e2e_auth_token` (uses WorkOS)
- `tests/integration/conftest.py` - May have auth fixtures

**Analysis:**
- Root conftest has `authkit_auth_token` with function scope
- E2E has `e2e_auth_token` using WorkOS
- Both serve similar purpose but for different test types

**Recommendation:**
- Keep separate (different auth methods for different test types)
- Document which to use when
- Consider unified interface if possible

#### 3. Entity Creation Helpers

**Pattern:** Multiple helpers for creating test entities

**Locations:**
- `tests/framework/data_generators.py` - `DataGenerator` class
- `tests/framework/conftest_shared.py` - `EntityFactory` class
- `tests/unit/tools/test_variant_utils.py` - `create_entity()` function
- `tests/e2e/fixtures/scenarios.py` - `test_data_setup` fixture

**Analysis:**
- `DataGenerator` and `EntityFactory` may have overlapping functionality
- `create_entity()` is a convenience wrapper
- `test_data_setup` provides pre-created entities

**Recommendation:**
- Consolidate `DataGenerator` and `EntityFactory` if they overlap
- Keep `create_entity()` as convenience wrapper
- Keep `test_data_setup` for E2E scenarios (different use case)

---

## Consolidation Plan

### Phase 1: Client Fixtures ✅

**Action:** Standardize on `tests/framework/conftest_shared.py` parametrized fixtures

**Changes:**
1. Update `tests/unit/tools/conftest.py` to import `parametrized_client` from framework
2. Update `tests/integration/conftest.py` to use framework fixtures
3. Update `tests/e2e/conftest.py` to use framework fixtures
4. Remove duplicate client fixture definitions

**Result:** Single source of truth for client fixtures

### Phase 2: Entity Creation Helpers

**Action:** Consolidate `DataGenerator` and `EntityFactory`

**Changes:**
1. Compare `DataGenerator` and `EntityFactory` functionality
2. Merge into single `EntityFactory` class
3. Update all imports to use consolidated class
4. Keep convenience wrappers (`create_entity()`) if needed

**Result:** Single entity creation utility

### Phase 3: Auth Token Fixtures

**Action:** Document and standardize auth token usage

**Changes:**
1. Document which auth fixture to use for each test type
2. Consider unified interface if possible
3. Keep separate implementations (different auth methods)

**Result:** Clear documentation, consistent usage

---

## Files to Modify

### High Priority
1. `tests/unit/tools/conftest.py` - Use framework fixtures
2. `tests/integration/conftest.py` - Use framework fixtures
3. `tests/e2e/conftest.py` - Use framework fixtures
4. `tests/framework/data_generators.py` - Consolidate with EntityFactory

### Medium Priority
5. `tests/framework/conftest_shared.py` - Ensure complete fixture set
6. `tests/framework/test_base.py` - Align with conftest_shared

### Low Priority
7. Documentation updates - Document fixture usage patterns

---

## Benefits

1. **Reduced Duplication** - Single source of truth for fixtures
2. **Easier Maintenance** - Update fixtures in one place
3. **Consistent Patterns** - All tests use same fixture patterns
4. **Better Discoverability** - Clear fixture organization
5. **Easier Testing** - Parametrized fixtures work across all layers

---

**Date:** 2025-11-23  
**Status:** Analysis Complete  
**Next Steps:** Implement Phase 1 consolidation
