# Implementation Strategy: Test Consolidation & Canonicalization

## Overall Approach

**Strategy:** Incremental consolidation with test verification at each step

**Key principles:**
1. Merge extension files into existing canonical files by concern
2. Delete _extN files after successful merge
3. Run tests after each merge to catch issues early
4. Use fixtures and markers for variant handling (not separate files)
5. Verify coverage maintained throughout

## Consolidation Order (Dependency-based)

### Phase 1: Core Entity Operations (Foundation)
**Dependency:** None (no other files depend on these)

**Step 1.1: Consolidate test_working_extension.py into test_entity_core.py**

Files involved:
- Source: `tests/unit/tools/test_working_extension.py` (262 lines)
- Target: `tests/unit/tools/test_entity_core.py` (291 lines)

Process:
1. Extract test classes and methods from test_working_extension.py:
   - `TestWorkingExtensions` → merge into core tests
   - `TestErrorHandling` → merge with error handling tests
   - `TestBulkOperations` → merge with bulk operation tests

2. Analyze fixture requirements:
   - `call_mcp` - verify compatible with target
   - `test_organization` - check fixture definitions
   - `test_project` - check fixture definitions

3. Merge test methods:
   - Rename classes to avoid duplicates if needed
   - Keep test names descriptive (concern-based)
   - Preserve docstrings and assertions

4. Verify imports and dependencies

5. Delete source file after merge

6. Run tests:
   ```bash
   python cli.py test run --scope unit --path tests/unit/tools/test_entity_core.py
   ```

**Rollback plan:** If merge fails, restore from git

---

**Step 1.2: Consolidate test_entity_operations_ext12.py into test_entity_core.py**

Files involved:
- Source: `tests/unit/extensions/test_entity_operations_ext12.py` (304 lines)
- Target: `tests/unit/tools/test_entity_core.py` (now ~553 lines after step 1.1)

**Issue:** Combined size would be 553+ lines, exceeds 350-line target

**Solution:** Decompose after merge
- Extract parametrized entity type tests into new `test_entity_parametrized.py`
- Extract bulk operations into `test_entity_bulk.py` (if doesn't exist)
- Extract extended operations (archive, restore) into appropriate tests

Process:
1. Extract parametrized test methods from _ext12:
   - `test_create_entity` (parametrized by entity_type)
   - `test_read_entity` (parametrized)
   - `test_update_entity` (parametrized)
   - etc.

2. Analyze parametrization:
   - ENTITY_TYPES constant has 20+ types
   - CORE_OPERATIONS constant
   - Use `@pytest.fixture(params=[...])` for entity types

3. Merge parametrized tests:
   - Keep fixture parametrization approach
   - Combine with existing entity_core tests
   - Avoid duplicate test names

4. Decompose if needed:
   - If file > 350 lines after merge, split:
     - test_entity_core.py: basic CRUD (create, read, update, delete)
     - test_entity_operations.py or test_entity_parametrized.py: parametrized variants
     - test_entity_bulk.py: bulk operations

5. Delete source file after merge

6. Run tests:
   ```bash
   python cli.py test run --scope unit --path tests/unit/tools/test_entity_*.py
   ```

---

### Phase 2: Soft-Delete Operations
**Dependency:** None

**Step 2.1: Consolidate test_soft_delete_ext3.py into test_soft_delete_consistency.py**

Files involved:
- Source: `tests/unit/extensions/test_soft_delete_ext3.py` (426 lines)
- Target: `tests/unit/tools/test_soft_delete_consistency.py` (unknown size)

Process:
1. Analyze test_soft_delete_consistency.py first (check current size)
2. Extract test methods from _ext3:
   - TestSoftDeleteBasics → merge
   - Cascade tests → merge
   - Version history tests → merge
   - Permission tests → merge
   - Audit trail tests → merge

3. Check for duplicate test names
4. Merge with fixture parametrization if needed
5. Run tests to verify coverage
6. Delete source file

---

### Phase 3: Tool-Specific Consolidations (Parallel)
**Dependency:** None (can run in parallel)

**Step 3.1: Consolidate test_error_handling_ext8.py**
- Target: `test_error_handling.py` (tools or infrastructure)
- Process: Same as 2.1

**Step 3.2: Consolidate test_audit_trails_ext7.py**
- Target: `test_audit_trails.py`
- Process: Same as 2.1

**Step 3.3: Consolidate test_advanced_features_ext9.py**
- Target: `test_advanced_features.py`
- Process: Same as 2.1

**Step 3.4: Consolidate test_workflows_ext10.py**
- Target: `test_workflow_coverage.py` or `test_workflow.py`
- Process: Same as 2.1

---

### Phase 4: Infrastructure Consolidations (Parallel)
**Dependency:** None

**Step 4.1: Consolidate test_permission_manager_ext2.py**
- Target: `tests/unit/infrastructure/test_permissions.py`
- Process: Extract and merge permission-specific tests

**Step 4.2: Consolidate test_concurrency_ext4.py**
- Target: `tests/unit/infrastructure/test_concurrency_manager.py`
- Process: Extract and merge concurrency tests

---

### Phase 5: Relationship Consolidation
**Dependency:** None

**Step 5.1: Consolidate test_relationship_cascading_ext6.py**
- Target: `test_relationship.py`
- Process: Extract cascading logic and merge

---

### Phase 6: Multi-Tenant & Performance (Special Handling)

**Step 6.1: Create test_multi_tenant.py from test_multi_tenant_ext5.py**
- Target: Create new `tests/unit/tools/test_multi_tenant.py`
- Process:
  1. Analyze test_multi_tenant_ext5.py
  2. Extract all test methods
  3. Create new canonical file with clean structure
  4. Move all tests to new file
  5. Delete _ext5

**Step 6.2: Handle test_performance_ext11.py (Special Case)**
- Don't merge into another file
- Instead: Extract performance tests and use `@pytest.mark.performance` marker
- Create performance test section in relevant test files
- Example:
  ```python
  @pytest.mark.performance
  async def test_entity_creation_performance(mcp_client):
      """Measure entity creation speed."""
      ...
  ```
- Delete test_performance_ext11.py

---

## Test Running & Validation Strategy

### Unit Tests During Consolidation

```bash
# After each merge step
python cli.py test run --scope unit --coverage

# Specific file validation
python cli.py test run --scope unit --path tests/unit/tools/test_entity_core.py

# Performance test validation (after step 6.2)
python cli.py test run -m performance
```

### Coverage Verification

```bash
# Before consolidation
python cli.py test run --coverage > coverage_before.txt

# After consolidation
python cli.py test run --coverage > coverage_after.txt

# Compare: same coverage, fewer files
```

### Integration Tests (Post-Phase-1)

```bash
# After core entity consolidation
python cli.py test run --scope integration
```

### Full Regression Test

```bash
# After all consolidations
python cli.py test run --coverage

# Verify:
# - All tests pass
# - Coverage metrics maintained or improved
# - No warnings or errors
```

---

## File Decomposition Guidelines

**If consolidated file exceeds 350 lines:**

1. **Identify cohesive responsibilities**
   - CRUD operations → separate
   - Parametrized variants → separate
   - Error handling → separate
   - Bulk operations → separate

2. **Create submodule structure**
   ```
   tests/unit/tools/
   ├── test_entity_core.py           # Basic CRUD
   ├── test_entity_parametrized.py   # Parametrized variants
   ├── test_entity_bulk.py           # Bulk operations
   └── test_entity_validation.py     # Validation logic
   ```

3. **Maintain concern-based naming**
   - Not: test_entity_unit.py, test_entity_fast.py
   - Yes: test_entity_crud.py, test_entity_validation.py

4. **Share fixtures** (conftest.py)
   - Common fixtures stay in conftest.py
   - Specific fixtures stay in test file

---

## Handling Fixture Dependencies

### Fixture Analysis

Before each merge, verify fixtures are compatible:

```bash
# List fixtures in target file
rg "@pytest.fixture" tests/unit/tools/test_entity_core.py

# List fixtures in source file
rg "@pytest.fixture" tests/unit/extensions/test_entity_operations_ext12.py

# Check conftest definitions
rg "@pytest.fixture" tests/unit/tools/conftest.py
```

### Fixture Consolidation

If source and target have duplicate fixtures:

1. **Keep the more robust version**
   - Check implementation details
   - Verify it covers both use cases

2. **Merge fixture logic** if needed
   - Combine parameters if parametrized
   - Extend coverage if needed

3. **Remove duplicate definitions**
   - Delete from source if moved to target
   - Verify all references updated

---

## Git Workflow

### Before Each Phase

```bash
# Create feature branch
git checkout -b consolidate-test-files-phase-N

# Verify current state
git status
python cli.py test run --scope unit
```

### After Each Consolidation Step

```bash
# Stage changes
git add tests/unit/...

# Commit with descriptive message
git commit -m "test: Consolidate test_X_extN.py into test_X.py

- Merged $(file1) and $(file2) into canonical $(target)
- Preserved all test cases and coverage
- Removed non-canonical _extN naming
- All unit tests passing"

# Verify
python cli.py test run --scope unit
```

### After All Phases

```bash
# Merge to main
git checkout main
git pull origin main
git merge consolidate-test-files-phase-N

# Push
git push origin main
```

---

## Rollback Plan

**If consolidation creates issues:**

1. **Identify the problem file** (which consolidation step failed)
2. **Restore from git:**
   ```bash
   git reset --hard HEAD~1  # Undo last commit
   git clean -fd            # Remove untracked files
   ```
3. **Investigate** why merge failed
4. **Fix** the issue in the consolidation plan
5. **Re-execute** that specific step

**If coverage drops:**

1. **Compare coverage:**
   ```bash
   python cli.py test run --coverage > coverage_current.txt
   diff coverage_before.txt coverage_current.txt
   ```
2. **Identify missing tests** from the extension file
3. **Verify they were merged** correctly
4. **Add missing tests** if they were accidentally omitted

---

## Success Criteria Checklist

- [ ] All 11 _extN files consolidated
- [ ] test_working_extension.py consolidated
- [ ] 0 non-canonical test files remain
- [ ] All test names are concern-based
- [ ] All tests passing (unit + integration)
- [ ] Coverage metrics maintained or improved
- [ ] No duplicate test names
- [ ] File sizes ≤500 lines (ideally ≤350)
- [ ] Fixtures properly consolidated
- [ ] Markers used for categorization (performance, smoke, etc.)
- [ ] Session documentation complete
- [ ] Changes committed with descriptive messages

---

## Estimated Timeline

- Phase 1 (core entity): 1-2 hours
- Phase 2 (soft-delete): 30 min - 1 hour
- Phase 3 (tool-specific): 1-2 hours (parallel)
- Phase 4 (infrastructure): 1 hour (parallel)
- Phase 5 (relationships): 30 min
- Phase 6 (multi-tenant, performance): 1 hour
- **Total: 4-8 hours** (depending on merge complexity and test verification)

---

## Notes

- Performance tests may require special handling (separate marked section)
- Multi-tenant tests may need new file creation (not merge into existing)
- File decomposition decisions made during execution based on actual sizes
- All changes validated against existing test coverage metrics
