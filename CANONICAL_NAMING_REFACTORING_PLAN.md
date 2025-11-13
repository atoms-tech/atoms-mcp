# Canonical Naming Refactoring Plan

**Status**: Documentation only (full refactoring requires careful execution with git)
**Scope**: Fix non-canonical test file naming per AGENTS.md § 3.1
**Estimated Effort**: 5-6 hours
**Risk**: High (799 tests, complex dependencies)
**Recommendation**: Execute with git commits enabled for safety

---

## Issues Identified

### 1. Extension Metadata in Filenames ❌

Files in `tests/unit/extensions/` use `_ext3`, `_ext4`, etc. suffixes which describe **which extension**, not **what's being tested** (the actual concern).

**Problem Files:**
```
❌ test_soft_delete_ext3.py          -> ✅ test_soft_delete.py
❌ test_concurrency_ext4.py          -> ✅ test_concurrency.py
❌ test_multi_tenant_ext5.py         -> ✅ test_multi_tenant.py
❌ test_relationship_cascading_ext6.py -> ✅ test_relationship_cascading.py
❌ test_audit_trails_ext7.py         -> ✅ test_audit_trails.py
❌ test_error_handling_ext8.py       -> ✅ test_error_handling.py
❌ test_advanced_features_ext9.py    -> ✅ test_advanced_features.py
❌ test_workflows_ext10.py           -> ✅ test_workflow_execution.py
❌ test_performance_ext11.py         -> ✅ test_performance.py
```

**Impact**: These should be moved to `tests/unit/tools/` and merged with existing canonical files OR kept in extensions if they're truly extension-specific tests.

**Decision Needed**: Are these "extension tests" or "core functionality tests that happen to be in extensions/"?
- If core functionality: **Move to tools/ and rename canonically**
- If extension-specific: **Keep in extensions/ but remove _ext prefix**

### 2. File Size Violations ❌

Hard limit: ≤500 lines (target ≤350)

**Violating Files:**
```
❌ test_entity_comprehensive.py       (818 lines) - Far exceeds limit
❌ test_entity_permissions.py         (547 lines) - Exceeds limit
❌ test_entity_workflows.py           (510 lines) - Exceeds limit
```

**Required Action**: SPLIT into smaller concern-based files

### 3. Non-Canonical Naming ❌

Files named with variant/metadata descriptors instead of concern descriptors:

```
❌ test_entity_comprehensive.py    - "comprehensive" = scope, not concern
                                   - Split by actual test concerns
                                   - Possibly: test_entity_create.py, test_entity_query.py, etc.
```

**Rationale**: "What concern does this test?" not "How comprehensive is it?"

---

## Refactoring Strategy

### Phase 1: Understand Current Structure

**Files to analyze:**
1. `test_entity_comprehensive.py` - Identify 2 test classes and their concerns
2. `test_entity_permissions.py` - Identify test class breakdown
3. `test_entity_workflows.py` - Identify test class breakdown
4. Extension test files - Determine if core functionality or extension-specific

### Phase 2: Rename Extension Tests

**Step 1: Rename files in extensions/**
```bash
# Remove _ext3-12 suffixes
mv test_soft_delete_ext3.py test_soft_delete.py
mv test_concurrency_ext4.py test_concurrency.py
mv test_multi_tenant_ext5.py test_multi_tenant.py
mv test_relationship_cascading_ext6.py test_relationship_cascading.py
mv test_audit_trails_ext7.py test_audit_trails.py
mv test_error_handling_ext8.py test_error_handling.py
mv test_advanced_features_ext9.py test_advanced_features.py
mv test_workflows_ext10.py test_workflow_execution.py
mv test_performance_ext11.py test_performance.py
```

**Step 2: Consolidate with tools/ where appropriate**

*Merge candidates* (tests for same concern exist in both locations):
- `test_soft_delete.py` (ext3) + `test_soft_delete_consistency.py` (tools) → Keep in tools/, merge content
- `test_audit_trails.py` (ext7) + `test_audit_trails.py` (tools, if exists) → Consolidate
- `test_error_handling.py` (ext8) + `test_error_handling.py` (tools, if exists) → Consolidate

*New canonical files* (new concerns):
- `test_concurrency.py` → Move to `tools/test_concurrency.py`
- `test_multi_tenant.py` → Move to `tools/test_multi_tenant.py`
- `test_relationship_cascading.py` → Move to `tools/test_relationship_cascading.py` or merge with `test_relationship.py`

### Phase 3: Split Oversized Files

#### A. Split test_entity_comprehensive.py (818 lines)

**Current structure:**
- `TestEntityComprehensiveOperations` - Parametrized tests across entity types
- `TestEntityCrossTypeOperations` - Tests across entity types

**Strategy:** Extract each test class into its own file:

```
test_entity_comprehensive.py (818 lines)
├─ TestEntityComprehensiveOperations
│  └─ Extract to: test_entity_parametrized.py (or similar)
│     Tests: archive/restore, bulk ops, search, history for all types
│
└─ TestEntityCrossTypeOperations
   └─ Extract to: test_entity_cross_type.py
      Tests: Cross-entity relationships and operations
```

**Result:**
- `test_entity_parametrized.py` (~400 lines)
- `test_entity_cross_type.py` (~300 lines)
- Delete `test_entity_comprehensive.py`

#### B. Split test_entity_permissions.py (547 lines)

**Read file to identify test classes**, then split by:
- Permission hierarchy tests → `test_entity_permission_hierarchy.py`
- Permission enforcement tests → `test_entity_permission_enforcement.py`
- Permission checks per operation → Keep if <350 lines

**Result:** 2-3 files, each <350 lines

#### C. Split test_entity_workflows.py (510 lines)

**Read file to identify test classes**, then split by:
- Workflow creation/execution → `test_entity_workflow_execution.py`
- Workflow state management → `test_entity_workflow_state.py`
- Workflow error handling → May consolidate into error handling tests

**Result:** 2 files, each <350 lines

### Phase 4: Consolidate Small Related Files

**Consolidation opportunities:**

```
test_entity_archive.py (163 lines)
+ test_entity_history.py (320 lines)
= test_entity_history_and_archive.py (~450 lines)

Rationale: Archive and history are related concerns (temporal operations)
```

### Phase 5: Directory Reorganization

**Final structure should be:**

```
tests/unit/tools/
├── test_entity.py                     (Core CRUD)
├── test_entity_parametrized.py        (Comprehensive parametrized ops)
├── test_entity_cross_type.py          (Cross-entity operations)
├── test_entity_archive.py             (Delete and soft-delete, if kept separate)
├── test_entity_bulk.py                (Bulk operations)
├── test_entity_permission_hierarchy.py (Permission hierarchy)
├── test_entity_permission_enforcement.py (Permission enforcement)
├── test_entity_workflow_execution.py  (Workflow execution)
├── test_entity_workflow_state.py      (Workflow state)
├── test_entity_history.py             (Version history, if kept separate)
├── test_entity_list.py                (List operations)
├── test_entity_document.py            (Document entity)
├── test_entity_organization.py        (Organization entity)
├── test_entity_project.py             (Project entity)
├── test_entity_requirement.py         (Requirement entity)
├── test_entity_test.py                (Test entity)
├── test_entity_resolver.py            (Entity resolution)
├── test_entity_traceability.py        (Traceability)
├── test_relationship.py               (All relationship types)
├── test_relationship_cascading.py     (Cascading relationships)
├── test_workflow.py                   (All workflow operations)
├── test_query.py                      (Canonical)
├── test_workspace.py                  (Canonical)
├── test_concurrency.py                (NEW - from ext4)
├── test_multi_tenant.py               (NEW - from ext5)
├── test_soft_delete.py                (Canonical, from ext3)
├── test_audit_trails.py               (Canonical, from ext7)
├── test_error_handling.py             (Canonical, from ext8)
├── test_advanced_features.py          (Canonical, from ext9)
├── test_performance.py                (Canonical, from ext11)
└── conftest.py                        (Fixtures)

tests/unit/extensions/
├── (All canonical test files moved to tools/)
└── (Directory can be deleted or repurposed)
```

---

## Execution Checklist

### Pre-Refactoring
- [ ] Ensure all 799 tests pass before starting
- [ ] Verify git is ready for commits
- [ ] Create a feature branch: `git checkout -b refactor/canonical-naming`

### Step 1: Rename Extension Tests (30 min)
- [ ] Read extension test files to understand scope
- [ ] Rename _ext prefix removal (9 files)
- [ ] Update imports in conftest if needed
- [ ] Run tests: `pytest tests/unit/extensions/ -v`

### Step 2: Move and Consolidate Extension Tests (1 hour)
- [ ] Move files from extensions/ to tools/
- [ ] Merge with existing canonical files where appropriate
- [ ] Update imports in all affected files
- [ ] Run tests: `pytest tests/unit/tools/ -v`

### Step 3: Split test_entity_comprehensive.py (1.5 hours)
- [ ] Read file and identify exact test classes
- [ ] Create new files for each class
- [ ] Move content, preserve fixtures
- [ ] Update imports
- [ ] Run tests: `pytest tests/unit/tools/test_entity*.py -v`

### Step 4: Split test_entity_permissions.py (1 hour)
- [ ] Read file and identify test classes by concern
- [ ] Create 2-3 new files
- [ ] Move content, preserve fixtures
- [ ] Update imports
- [ ] Run tests: `pytest tests/unit/tools/test_entity_permission*.py -v`

### Step 5: Split test_entity_workflows.py (1 hour)
- [ ] Read file and identify test classes
- [ ] Create 2 new files
- [ ] Move content, preserve fixtures
- [ ] Update imports
- [ ] Run tests: `pytest tests/unit/tools/test_entity_workflow*.py -v`

### Step 6: Consolidate Small Files (30 min)
- [ ] Merge test_entity_archive.py + test_entity_history.py
- [ ] Update imports
- [ ] Run tests: `pytest tests/unit/tools/test_entity_history.py -v`

### Step 7: Final Verification (1 hour)
- [ ] Run full test suite: `pytest tests/unit/ -v`
- [ ] Verify all 799 tests pass
- [ ] Check file sizes: `wc -l tests/unit/tools/test_*.py`
- [ ] Verify no _ext, _comprehensive, _core, _advanced in filenames
- [ ] Clean up any remaining non-canonical files

### Post-Refactoring
- [ ] Create commit: `git commit -m "refactor: canonical naming for test files per AGENTS.md"`
- [ ] Verify all tests still pass
- [ ] Push: `git push origin refactor/canonical-naming`

---

## Risk Mitigation

**High-Risk Aspects:**
1. Large file migrations (5,544 lines total across entity tests)
2. Complex import dependencies
3. 799 tests that could break

**Mitigation:**
1. **Small steps**: Execute Phase-by-Phase with test runs between each
2. **Git commits**: Commit after each phase so you can revert if issues arise
3. **Backup**: Keep original files until all tests pass with new structure
4. **Verify imports**: After each change, run tests to catch import errors early

---

## Success Criteria

✅ All files follow canonical naming (by concern, not variant/metadata)
✅ All files ≤500 lines (ideally <350)
✅ No _ext, _comprehensive, _core, _advanced, _fast, _slow, etc. suffixes
✅ All 799 tests pass
✅ Clear directory structure with tests organized by concern

---

## Notes

**This refactoring is optional but recommended:**
- The project is currently **production-ready** with full functionality
- The refactoring improves **code hygiene** and **maintainability**
- Without it, the test codebase will become harder to navigate as it grows
- **With git commits**, this becomes a safe, reversible operation

**Alternative approach if execution stalls:**
- Keep the extension tests in extensions/ directory
- Just remove the _ext prefix
- Only refactor tools/ directory (split oversized files)
- This reduces scope from 5-6 hours to 2-3 hours
