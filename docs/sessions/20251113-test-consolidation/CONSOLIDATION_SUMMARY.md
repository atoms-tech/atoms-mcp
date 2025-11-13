# Test Consolidation Summary & Execution Guide

## Problem Statement

**12 non-canonical test files** violate AGENTS.md § Test File Governance:

```
✗ 11 files with _extN naming:
  - test_*_ext1.py through test_*_ext12.py
  - Uses numeric metadata, not concern-based naming
  - Suggests versioning/sequencing unrelated to canonical standard

✗ 1 file with semantic state naming:
  - test_working_extension.py ("working" = state, not component)
  - Should describe concern, not execution state
```

**Impact:**
- Duplicate test code (same concern tested multiple times)
- Increased test collection time (12 extra files to load)
- Maintenance burden (changes required in multiple places)
- Unclear structure (new developers can't tell what test file to use)

---

## Canonical Standard (AGENTS.md Reference)

### ✅ Correct Pattern (Concern-Based)
```
test_entity.py                    # What: entity tool
test_entity_crud.py               # What: CRUD operations
test_entity_validation.py         # What: validation logic
test_soft_delete_consistency.py   # What: soft-delete functionality
test_auth_supabase.py             # What: Supabase auth integration
```

### ❌ Incorrect Patterns (Metadata-Based)
```
test_entity_unit.py               # How: unit scope (use fixtures)
test_entity_integration.py        # How: integration variant (use fixtures)
test_entity_fast.py               # How: speed categorization (use @pytest.mark)
test_entity_old.py                # When: temporal state (refactor)
test_entity_ext1.py               # Numeric: version/sequence (consolidate)
test_working_extension.py         # State: semantic descriptor (rename)
```

**Key Rule:** File name answers "What component/concern?" NOT "How fast?" or "What variant?"

---

## Current Consolidation Status

### Files to Consolidate: 12 Total

| Type | Count | Action |
|------|-------|--------|
| Extension files (_extN) | 11 | Consolidate into canonical files |
| Semantic state files | 1 | Consolidate into canonical files |
| **Total** | **12** | **→ 0 after consolidation** |

### Consolidation Map

| File | Canonical Target | Line Count | Status |
|------|------------------|-----------|--------|
| `test_working_extension.py` | `test_entity_core.py` | 262 | Planned |
| `test_entity_operations_ext12.py` | `test_entity_core.py` | 304 | Planned |
| `test_soft_delete_ext3.py` | `test_soft_delete_consistency.py` | 426 | Planned |
| `test_error_handling_ext8.py` | `test_error_handling.py` | ~200 | Planned |
| `test_audit_trails_ext7.py` | `test_audit_trails.py` | ~200 | Planned |
| `test_advanced_features_ext9.py` | `test_advanced_features.py` | ~200 | Planned |
| `test_workflows_ext10.py` | `test_workflow_coverage.py` | ~200 | Planned |
| `test_performance_ext11.py` | Use markers (N/A) | ~200 | Extract |
| `test_multi_tenant_ext5.py` | Create canonical | ~200 | New file |
| `test_permission_manager_ext2.py` | `test_permissions.py` (infra) | ~200 | Planned |
| `test_relationship_cascading_ext6.py` | `test_relationship.py` | ~200 | Planned |
| `test_concurrency_ext4.py` | `test_concurrency_manager.py` (infra) | ~200 | Planned |

---

## 6-Phase Execution Plan

### Phase 1: Core Entity Operations (Foundation)
**Duration:** 1-2 hours  
**Risk:** Low (entity tests are well-isolated)

**Steps:**
1. ✓ Analyze `test_entity_core.py` (current size: 291 lines)
2. ✓ Merge `test_working_extension.py` (262 lines) → combined: 553 lines
3. ✓ Merge `test_entity_operations_ext12.py` (304 lines) → combined: 857 lines
4. ✓ **Decompose if needed:** Split into:
   - `test_entity_core.py` (CRUD: ≤350 lines)
   - `test_entity_parametrized.py` (parametrized variants: ≤350 lines)
   - `test_entity_bulk.py` (bulk operations: exists or create)
5. ✓ Delete source _extN files
6. ✓ Run: `python cli.py test run --scope unit --path tests/unit/tools/test_entity*.py`

**Files to delete after:**
- ✗ `test_working_extension.py`
- ✗ `test_entity_operations_ext12.py`

---

### Phase 2: Soft-Delete Operations (Parallel)
**Duration:** 1 hour  
**Risk:** Low (isolated concern)

**Steps:**
1. ✓ Analyze `test_soft_delete_consistency.py`
2. ✓ Merge `test_soft_delete_ext3.py` (426 lines)
3. ✓ Verify no duplicates
4. ✓ Delete source
5. ✓ Run: `python cli.py test run --scope unit --path tests/unit/tools/test_soft_delete*.py`

**Files to delete after:**
- ✗ `test_soft_delete_ext3.py`

---

### Phase 3: Tool-Specific Consolidations (Parallel)
**Duration:** 1-2 hours  
**Risk:** Low (each independent)

**3.1 Error Handling (30 min)**
- Merge `test_error_handling_ext8.py` → `test_error_handling.py`
- Delete source
- Run tests

**3.2 Audit Trails (30 min)**
- Merge `test_audit_trails_ext7.py` → `test_audit_trails.py`
- Delete source
- Run tests

**3.3 Advanced Features (30 min)**
- Merge `test_advanced_features_ext9.py` → `test_advanced_features.py`
- Delete source
- Run tests

**3.4 Workflows (30 min)**
- Merge `test_workflows_ext10.py` → `test_workflow_coverage.py`
- Delete source
- Run tests

**Files to delete after:**
- ✗ `test_error_handling_ext8.py`
- ✗ `test_audit_trails_ext7.py`
- ✗ `test_advanced_features_ext9.py`
- ✗ `test_workflows_ext10.py`

---

### Phase 4: Infrastructure Consolidations (Parallel)
**Duration:** 1 hour  
**Risk:** Low (infrastructure isolated)

**4.1 Permissions (30 min)**
- Merge `test_permission_manager_ext2.py` → `tests/unit/infrastructure/test_permissions.py`
- Delete source
- Run tests

**4.2 Concurrency (30 min)**
- Merge `test_concurrency_ext4.py` → `tests/unit/infrastructure/test_concurrency_manager.py`
- Delete source
- Run tests

**Files to delete after:**
- ✗ `test_permission_manager_ext2.py`
- ✗ `test_concurrency_ext4.py`

---

### Phase 5: Relationship Consolidation (Parallel)
**Duration:** 30 min  
**Risk:** Low

**Steps:**
1. ✓ Merge `test_relationship_cascading_ext6.py` → `test_relationship.py`
2. ✓ Delete source
3. ✓ Run tests

**Files to delete after:**
- ✗ `test_relationship_cascading_ext6.py`

---

### Phase 6: Special Cases (Sequential)
**Duration:** 1 hour  
**Risk:** Medium (new file creation + special markers)

**6.1 Multi-Tenant (30 min)**
- Create new canonical file: `tests/unit/tools/test_multi_tenant.py`
- Move all tests from `test_multi_tenant_ext5.py`
- Delete source
- Run tests

**6.2 Performance Tests (30 min)**
- Extract tests from `test_performance_ext11.py`
- Add to relevant test files with `@pytest.mark.performance` marker
- Delete source
- Example:
  ```python
  @pytest.mark.performance
  async def test_entity_creation_performance(mcp_client):
      """Measure entity creation speed."""
      ...
  ```

**Files to delete after:**
- ✗ `test_multi_tenant_ext5.py`
- ✗ `test_performance_ext11.py`

---

## Variant Testing Pattern Conversion

### OLD Pattern (Non-Canonical - Separate Files)
```python
# ❌ test_entity_unit.py
async def test_entity_creation(call_mcp):
    ...

# ❌ test_entity_integration.py
async def test_entity_creation(mcp_http_client):  # Same test, written 3 times!
    ...

# ❌ test_entity_e2e.py
async def test_entity_creation(mcp_e2e_client):   # Same test, written 3 times!
    ...
```

**Problems:**
- Code duplication (same test, 3 times)
- Maintenance burden (change test → update in 3 places)
- Confusing structure (why 3 files for 1 concern?)

### NEW Pattern (Canonical - Fixtures & Markers)
```python
# ✅ test_entity.py (one file, multiple variants)

@pytest.fixture(params=["unit", "integration", "e2e"])
def mcp_client(request):
    """Parametrized client fixture.
    
    Provides different clients based on variant:
    - unit: InMemoryMcpClient (fast)
    - integration: HttpMcpClient (live database)
    - e2e: DeploymentMcpClient (production setup)
    """
    if request.param == "unit":
        return InMemoryMcpClient()
    elif request.param == "integration":
        return HttpMcpClient(...)
    else:
        return DeploymentMcpClient(...)

async def test_entity_creation(mcp_client):
    """Test runs 3 times: unit, integration, e2e."""
    result = await mcp_client.call_tool(...)
    assert result.success

@pytest.mark.performance
async def test_entity_bulk_performance(mcp_client):
    """Performance test - marked separately."""
    ...

@pytest.mark.smoke
async def test_entity_basic(mcp_client):
    """Quick smoke test - marked separately."""
    ...
```

**Benefits:**
- ✓ One file, not three (no duplication)
- ✓ Same test logic runs 3 times automatically
- ✓ Fixtures parametrize variants
- ✓ Markers categorize by concern (performance, smoke, etc.)
- ✓ Easy to add new variant (update fixture once)

---

## Execution Checklist

### Pre-Consolidation Validation
- [ ] All current tests passing: `python cli.py test run --scope unit`
- [ ] Coverage baseline: `python cli.py test run --coverage`
- [ ] Line counts verified for all files

### Phase 1: Entity Operations
- [ ] `test_working_extension.py` analyzed
- [ ] `test_entity_operations_ext12.py` analyzed
- [ ] Fixtures compatibility verified
- [ ] Merge test methods into `test_entity_core.py`
- [ ] Decompose if > 350 lines
- [ ] Delete source files
- [ ] Tests passing: `python cli.py test run --scope unit`
- [ ] Commit: `git commit -m "test: Consolidate entity operation tests"`

### Phase 2-6: Remaining Consolidations
- [ ] Each phase follows same checklist
- [ ] Tests run after each phase
- [ ] No regressions detected
- [ ] All source _extN files deleted

### Post-Consolidation Validation
- [ ] Coverage metrics: `python cli.py test run --coverage`
- [ ] 0 _extN files remain: `find tests -name "*_ext*.py"`
- [ ] 0 semantic state files remain
- [ ] All test names are canonical
- [ ] Full integration test suite passes
- [ ] Session documentation complete

---

## Expected Outcome

**Before:**
```
tests/unit/extensions/
├── test_advanced_features_ext9.py
├── test_audit_trails_ext7.py
├── test_concurrency_ext4.py
├── test_entity_operations_ext12.py
├── test_error_handling_ext8.py
├── test_multi_tenant_ext5.py
├── test_performance_ext11.py
├── test_permission_manager_ext2.py
├── test_relationship_cascading_ext6.py
├── test_soft_delete_ext3.py
└── test_workflows_ext10.py     (11 files with _extN)

tests/unit/tools/
└── test_working_extension.py   (1 semantic state file)

Total: 12 non-canonical files
```

**After:**
```
tests/unit/extensions/
└── (empty - all consolidated)

tests/unit/tools/
├── test_entity_core.py         (merged working + ext12)
├── test_entity_parametrized.py (decomposed if needed)
├── test_soft_delete_consistency.py (merged ext3)
├── test_error_handling.py      (merged ext8)
├── test_audit_trails.py        (merged ext7)
├── test_advanced_features.py   (merged ext9)
├── test_workflow_coverage.py   (merged ext10)
├── test_multi_tenant.py        (created from ext5)
├── test_relationship.py        (merged ext6)
└── (performance markers in relevant files)

tests/unit/infrastructure/
├── test_concurrency_manager.py (merged ext4)
├── test_permissions.py         (merged ext2)
└── ...

Total: 0 non-canonical files ✓
```

---

## Next Steps

1. **Approve consolidation plan** (this document)
2. **Execute Phase 1** (core entity operations)
3. **Run full test suite** to verify no regressions
4. **Execute Phases 2-6** in sequence (with test verification each phase)
5. **Verify final state:**
   - All tests passing
   - Coverage maintained or improved
   - 0 non-canonical files
   - Session documentation complete
6. **Create PR** with consolidation changes
7. **Merge** to main

---

## Questions?

This consolidation plan is based on AGENTS.md § Test File Governance canonical naming standard. All decisions are documented in session notes:
- `00_SESSION_OVERVIEW.md` - Goals and consolidation map
- `01_RESEARCH.md` - Detailed analysis of each file
- `02_IMPLEMENTATION_STRATEGY.md` - Step-by-step execution guide
