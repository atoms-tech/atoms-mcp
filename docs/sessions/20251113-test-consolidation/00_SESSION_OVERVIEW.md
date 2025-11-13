# Test File Consolidation & Canonicalization Session

**Date:** 2025-11-13  
**Goal:** Consolidate non-canonical test files (_extN suffixes and "working" semantic names) into proper concern-based structure  
**Priority:** High (improves maintainability and follows AGENTS.md § Test File Governance)

## Current State

**Non-canonical files identified:** 12 total
- 11 extension test files (`test_*_ext{N}.py`)
- 1 "working" semantic file (`test_working_extension.py`)

**Issues:**
- Numeric extensions (_ext1, _ext2, etc.) violate canonical naming (should describe concern, not metadata)
- "working" prefix is semantic state descriptor, not component/concern
- Duplicate test code across multiple files for same concern (e.g., entity operations tested in ext12 AND in working_extension AND in entity_core)
- Increases test collection time, complicates maintenance

## Consolidation Plan

### Phase 1: Map Extensions to Canonical Files ✓
Identified existing canonical files and their relationship to extension files:

| Extension File | Canonical Target | Overlap | Action |
|---|---|---|---|
| `test_entity_operations_ext12.py` | `test_entity_core.py` | Full (both test entity CRUD) | **Merge** |
| `test_working_extension.py` | `test_entity_core.py` | Partial (entity operations) | **Merge** |
| `test_soft_delete_ext3.py` | `test_soft_delete_consistency.py` | Full | **Merge** |
| `test_error_handling_ext8.py` | `test_error_handling.py` | Full | **Merge** |
| `test_audit_trails_ext7.py` | `test_audit_trails.py` | Full | **Merge** |
| `test_advanced_features_ext9.py` | `test_advanced_features.py` | Full | **Merge** |
| `test_workflows_ext10.py` | `test_workflow_coverage.py` | Full | **Merge** |
| `test_performance_ext11.py` | N/A (use markers) | N/A | **Extract & use @pytest.mark.performance** |
| `test_multi_tenant_ext5.py` | Create `test_multi_tenant.py` | New concern | **Create canonical file** |
| `test_permission_manager_ext2.py` | `test_permissions.py` (infrastructure) | Full | **Merge** |
| `test_relationship_cascading_ext6.py` | `test_relationship.py` | Full | **Merge** |
| `test_concurrency_ext4.py` | `test_concurrency_manager.py` (infrastructure) | Full | **Merge** |

### Phase 2: Merge Strategy
For each extension file:
1. Extract test logic and docstrings from _extN file
2. Merge into canonical target file with same test names/concerns
3. Use `@pytest.fixture(params=[...])` for parametrized variants
4. Use `@pytest.mark` for categorization (performance, smoke, integration, etc.)
5. Delete _extN file after merge
6. Run full test suite to verify coverage maintained

### Phase 3: Validation
- [ ] All tests passing
- [ ] No duplicate test names across files
- [ ] No _extN files remaining
- [ ] No "working" semantic files
- [ ] All file names are canonical (concern-based)
- [ ] Test coverage metrics maintained or improved

## Success Criteria
- ✓ 11 extension files consolidated to canonical forms
- ✓ `test_working_extension.py` consolidated or renamed
- ✓ All existing tests passing
- ✓ Reduced test collection overhead
- ✓ Clear, canonical test file structure

## Known Issues
- Some extension files may have tests with hardcoded mock data (may need fixtures)
- Performance tests may need special handling (markers, separate suites)
- Coverage metrics should be verified post-consolidation

## Next Steps
1. Analyze each extension file individually (01_RESEARCH.md)
2. Create consolidation checklist for each merge (03_DAG_WBS.md)
3. Execute merges in dependency order
4. Run tests and verify coverage
5. Commit consolidated changes
