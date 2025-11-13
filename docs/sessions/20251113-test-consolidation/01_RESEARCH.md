# Research: Test File Structure & Consolidation

## Canonical Naming Standard (from AGENTS.md § Test File Governance)

### What Makes a Test File Name Canonical?

✅ **Good (canonical - concern-based):**
- `test_entity.py` - Tests the entity tool
- `test_entity_crud.py` - Tests CREATE/READ/UPDATE/DELETE operations
- `test_entity_validation.py` - Tests entity validation logic
- `test_auth_supabase.py` - Tests Supabase-specific auth integration
- `test_soft_delete_consistency.py` - Tests soft-delete functionality

❌ **Bad (metadata-based - violates canonical standard):**
- `test_entity_fast.py` - "fast" describes speed, not content (use `@pytest.mark.performance`)
- `test_entity_unit.py` - "unit" describes scope, not what's tested (use conftest fixtures)
- `test_entity_integration.py` - "integration" describes client type (use fixture parametrization)
- `test_entity_e2e.py` - "e2e" describes test stage (use markers)
- `test_entity_old.py`, `test_entity_new.py` - Temporal metadata (refactor, merge, or delete)
- `test_entity_ext1.py`, `test_entity_ext2.py` - Version/extension suffix (use fixtures instead)
- `test_working_extension.py` - "working" describes state, not component (rename by concern)

### Key Principle
**Test file name must answer: "What component/concern does this test?" — NOT "How fast is it?" or "What variant?"**

## Current Repository State

### Extension Files (Primary Consolidation Target)

All 11 extension files use **_ext{N}** suffix pattern, which violates canonical naming:

```bash
tests/unit/extensions/
├── test_advanced_features_ext9.py      # _ext9 = non-canonical metadata
├── test_audit_trails_ext7.py           # _ext7 = non-canonical metadata
├── test_concurrency_ext4.py            # _ext4 = non-canonical metadata
├── test_entity_operations_ext12.py     # _ext12 = non-canonical metadata
├── test_error_handling_ext8.py         # _ext8 = non-canonical metadata
├── test_multi_tenant_ext5.py           # _ext5 = non-canonical metadata
├── test_performance_ext11.py           # _ext11 = non-canonical metadata
├── test_permission_manager_ext2.py     # _ext2 = non-canonical metadata
├── test_relationship_cascading_ext6.py # _ext6 = non-canonical metadata
├── test_soft_delete_ext3.py            # _ext3 = non-canonical metadata
└── test_workflows_ext10.py             # _ext10 = non-canonical metadata
```

**Why _extN is non-canonical:**
- Numeric metadata (ext1, ext2, ..., ext12) describes version or sequence, NOT concern
- Pattern violates canonical standard: should name by component/tool/concern
- Suggests temporal progression (ext1 → ext2) which doesn't apply in canonical naming
- Makes consolidation difficult: `test_entity_ext1.py` + `test_entity_ext2.py` + `test_entity.py` have unclear relationship

### The "Working Extension" File

```
tests/unit/tools/test_working_extension.py
```

**Why "working" is non-canonical:**
- "working" is a **semantic state descriptor** ("this one works")
- Does NOT describe the component/concern being tested
- Bad naming: next developer sees "working" and wonders "does the non-working version exist?"
- Should be named by concern: tests basic entity operations → `test_entity_operations.py`

### Canonical Test Structure (Existing)

Already well-organized by concern:

```bash
tests/unit/tools/
├── test_entity_*.py              # Entity tool tests (core, bulk, list, etc.)
├── test_workflow*.py             # Workflow tests
├── test_relationship*.py          # Relationship tests
├── test_workspace*.py            # Workspace tests
├── test_query*.py                # Query tests
├── test_error_handling.py        # Error handling (canonical)
├── test_audit_trails.py          # Audit functionality (canonical)
├── test_advanced_features.py     # Advanced features (canonical)
└── test_working_extension.py     # ❌ NON-CANONICAL (semantic state)

tests/unit/infrastructure/
├── test_permissions.py           # Permission adapter tests
├── test_auth_adapter.py          # Auth adapter tests
├── test_concurrency_manager.py   # Concurrency tests (canonical)
├── test_distributed_rate_limiter.py
└── ... other infrastructure tests (canonical)
```

## Consolidation Mapping Analysis

### 1. test_entity_operations_ext12.py Analysis

**Location:** `tests/unit/extensions/test_entity_operations_ext12.py`

**What it tests:**
- CRUD operations across 20+ entity types
- Parametrized tests with different entity types
- Core operations (create, read, update, delete)
- Extended operations (archive, restore, list, search)
- Bulk operations (bulk_create, bulk_update, bulk_delete, bulk_archive)

**File size:** 304 lines

**Canonical target:** `test_entity_core.py` (already exists, 291 lines)
- Both test core entity operations across types
- Both use parametrized fixtures for entity types
- Obvious merge: same concern, same approach

**Consolidation action:** 
- Extract parametrized tests from _ext12
- Merge into test_entity_core.py using fixtures
- Delete test_entity_operations_ext12.py

### 2. test_working_extension.py Analysis

**Location:** `tests/unit/tools/test_working_extension.py`

**What it tests:**
- Basic search operations (doc creation, search, filtering)
- Archive/restore operations (archive, verify deletion, restore)
- List filtering operations (filter by status, limit)
- Error handling (invalid entity type, missing fields)
- Bulk operations (bulk_create documents)

**File size:** 262 lines

**Canonical target:** `test_entity_core.py` (already exists)
- Both test basic entity operations
- Both use similar test fixtures (call_mcp, test_organization, test_project)
- Both test CRUD + archive/restore + search
- Obvious merge: same tool, same concern

**Consolidation action:**
- Extract test methods from working_extension.py
- Merge into test_entity_core.py
- Delete test_working_extension.py
- Rename classes if necessary to avoid duplicates

### 3. test_soft_delete_ext3.py Analysis

**Location:** `tests/unit/extensions/test_soft_delete_ext3.py`

**What it tests:**
- Soft-delete marking entities as deleted
- Hard-delete permanently removing entities
- Restore recovering soft-deleted entities
- Cascading soft-deletes through relationships
- Version history preservation after soft-delete
- Permission checks on restore
- Audit trail tracking

**File size:** 426 lines

**Canonical target:** `test_soft_delete_consistency.py` (already exists)
- Both test soft-delete functionality
- Both have same concern scope
- Natural consolidation

**Consolidation action:**
- Merge into test_soft_delete_consistency.py
- Delete test_soft_delete_ext3.py

### 4-11. Other Extension Files

**Similar analysis applies:**
- `test_error_handling_ext8.py` → merge into `test_error_handling.py`
- `test_audit_trails_ext7.py` → merge into `test_audit_trails.py`
- `test_advanced_features_ext9.py` → merge into `test_advanced_features.py`
- `test_workflows_ext10.py` → merge into `test_workflow_coverage.py` or `test_workflow.py`
- `test_performance_ext11.py` → extract to use `@pytest.mark.performance` markers
- `test_multi_tenant_ext5.py` → create new canonical `test_multi_tenant.py`
- `test_permission_manager_ext2.py` → merge into `tests/unit/infrastructure/test_permissions.py`
- `test_relationship_cascading_ext6.py` → merge into `test_relationship.py`
- `test_concurrency_ext4.py` → merge into `tests/unit/infrastructure/test_concurrency_manager.py`

## Variant Testing Strategy

**Key insight from AGENTS.md:** Use **fixtures and markers**, NOT separate files, for variants.

### Pattern: Fixture Parametrization

Instead of having separate files for each variant:

```python
# ✅ GOOD: One file, fixture parametrization
@pytest.fixture(params=[
    InMemoryMcpClient(),      # unit
    HttpMcpClient(...),       # integration  
    DeploymentMcpClient(...)  # e2e
])
def mcp_client(request):
    return request.param

async def test_entity_creation(mcp_client):
    """Runs 3 times: unit, integration, e2e."""
    result = await mcp_client.call_tool(...)
    assert result.success
```

**Benefits:**
- Single file, not three
- Same test logic runs across variants automatically
- No code duplication
- Easier to maintain

### Pattern: Test Markers

Instead of separate files for speed/type variants:

```python
# ✅ GOOD: Markers for categorization within one file

@pytest.mark.asyncio
@pytest.mark.performance
async def test_bulk_operations_performance(mcp_client):
    """Use markers instead of file suffixes."""
    ...

@pytest.mark.asyncio
@pytest.mark.smoke
async def test_basic_operations(mcp_client):
    """Quick smoke test."""
    ...

@pytest.mark.asyncio
@pytest.mark.integration
async def test_with_real_database(mcp_client):
    """Requires real database."""
    ...
```

**CI/CD Usage:**
```bash
pytest -m smoke              # Quick (5 sec)
pytest -m "not integration"  # All except integration (30 sec)
pytest -m ""                 # Full suite (5 min)
pytest -m performance        # Performance only (2 min)
```

## File Size Analysis

### Large Files (Consolidation Candidates)

**Current structure:**
- `test_entity_core.py`: 291 lines
- `test_soft_delete_consistency.py`: Unknown (check during merge)
- `test_workflow_coverage.py`: Unknown
- Extension files: 200-426 lines each

**After consolidation:**
- Individual canonical files may grow, but stay ≤500 lines (target 350)
- If canonical file approaches 350 lines after merge:
  - Split by concern (e.g., entity → entity_crud, entity_validation)
  - Use fixtures to parametrize instead of creating new files

## Consolidation Dependency Graph

```
test_entity_operations_ext12.py ──┐
                                  ├──> merge into test_entity_core.py
test_working_extension.py         ┘
                          ↓
                    (Validate)
                          ↓
test_soft_delete_ext3.py ──────> merge into test_soft_delete_consistency.py
test_error_handling_ext8.py ────> merge into test_error_handling.py
test_audit_trails_ext7.py ──────> merge into test_audit_trails.py
test_advanced_features_ext9.py → merge into test_advanced_features.py
test_workflows_ext10.py ────────> merge into test_workflow_coverage.py
test_permission_manager_ext2.py → merge into tests/unit/infrastructure/test_permissions.py
test_relationship_cascading_ext6.py → merge into test_relationship.py
test_concurrency_ext4.py ───────> merge into tests/unit/infrastructure/test_concurrency_manager.py

Special cases:
test_performance_ext11.py ──────> Extract to use @pytest.mark.performance
test_multi_tenant_ext5.py ──────> Create new canonical test_multi_tenant.py
```

## Success Metrics

1. **Consolidation Complete:**
   - 0 files with _extN suffix
   - 0 files with semantic state names (working, old, new, etc.)
   - All tests renamed to concern-based canonical format

2. **No Loss of Coverage:**
   - All test cases from extension files preserved
   - Same number of test methods (or more, if consolidated)
   - All existing unit tests still pass

3. **Improved Maintenance:**
   - Reduced file count (12 files → 0)
   - Single source of truth per concern
   - Clear file naming for discoverability
   - Faster test collection

4. **Code Quality:**
   - All files ≤500 lines (ideally ≤350)
   - Proper use of fixtures for parametrization
   - Proper use of markers for categorization
   - No duplicate test logic
