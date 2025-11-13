# Test Infrastructure Fix - Execution Plan

## Current State Analysis

### ✅ What's Working
- **test_entity.py**: 12 tests PASSING
  - Uses correct `call_mcp()` interface with proper parametrization
  - Demonstrates proper fixture usage with `mcp_client` parametrized fixture
  - Follow this pattern for all other tools

### 🔴 What's Broken
1. **test_query.py**: 36 tests SKIPPED (with `_skip_outdated` marker)
   - Tests use non-existent API parameters: `query`, `entity_types`, `filters`, `offset`
   - Actual tool signature: `query_type`, `entities`, `conditions`, `projections`, `search_term`, `limit`, etc.
   - All tests explicitly marked as skipped with reason: "Tests use outdated query API"

2. **test_relationship.py**: Likely similar issue (untested)
3. **test_workflow.py**: Likely similar issue (untested)
4. **test_workspace.py**: Likely similar issue (untested)

## Root Cause

The test suite was designed for a different API contract than what's currently implemented in:
- `/tools/query.py` → `data_query()` function
- `/server.py` → Tool definitions with `@mcp.tool` decorators

The actual tool signatures don't match what the tests expect.

## Solution Strategy

### Phase 1: Fix test_query.py (HIGHEST PRIORITY)
The tests are explicitly marked as skipped. Either:

**Option A (Recommended)**: Rewrite tests to match actual tool signature
```python
# Current (WRONG):
await call_mcp("query_tool", {
    "query": "web development",
    "entity_types": ["project"],
    "filters": {...},
    "limit": 10
})

# Correct:
await call_mcp("query_tool", {
    "query_type": "search",  # or "rag_search", "aggregate", etc.
    "entities": ["project"],
    "search_term": "web development",
    "conditions": {...},  # not "filters"
    "limit": 10
})
```

**Option B**: Create adapter layer in tests (not recommended - adds complexity)

### Phase 2: Fix test_relationship.py
Follow same pattern as test_entity.py and verify with actual tool signature in server.py

### Phase 3: Fix test_workflow.py
Same pattern

### Phase 4: Fix test_workspace.py
Same pattern

## Implementation Steps

1. **Understand current tool signatures** (ALREADY DONE)
   - query_tool: query_type, entities, conditions, search_term, limit, rag_mode, etc.
   - relationship_tool: operation, source_id, target_id, relation_type, etc.
   - workflow_tool: workflow, parameters, etc.
   - workspace_tool: operation, name, etc.

2. **Remove skip markers** from test_query.py

3. **Rewrite test classes** to use correct parameters
   - Use test_entity.py as the canonical pattern
   - Match parameter names exactly to tool signatures
   - Preserve all test logic and assertions

4. **Run tests incrementally**
   - pytest tests/unit/tools/test_query.py -v
   - Fix failures iteratively
   - Ensure no new regressions in test_entity.py

5. **Document tool APIs**
   - Create a reference guide of all tool signatures
   - Keep tests and tools in sync with regular validation

## Key Files to Reference

- ✅ `/tests/unit/tools/test_entity.py` - CANONICAL PATTERN (use this as template)
- ✅ `/server.py` lines 694-754 - query_tool definition
- ✅ `/tools/query.py` - data_query() implementation
- ❌ `/tests/unit/tools/test_query.py` - NEEDS REWRITE

## Success Criteria

- [ ] test_query.py: All 36 tests running (not skipped)
- [ ] test_query.py: All tests passing
- [ ] test_relationship.py: Tests running and passing
- [ ] test_workflow.py: Tests running and passing
- [ ] test_workspace.py: Tests running and passing
- [ ] No regressions in test_entity.py
- [ ] All parameter names match server.py tool definitions exactly

## Time Estimate

- test_query.py: 1-2 hours (fix 36 tests)
- test_relationship.py: 1-2 hours
- test_workflow.py: 30-45 minutes
- test_workspace.py: 30-45 minutes
- **Total: 4-5 hours of focused work**

## Immediate Next Steps

1. Restore uv.lock to working state (if needed)
2. Rewrite test_query.py TestQuerySemanticSearch class as proof of concept
3. Run tests and iterate
4. Apply same pattern to remaining classes in test_query.py
5. Move to other test files
