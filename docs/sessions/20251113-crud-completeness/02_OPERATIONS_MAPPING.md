# Current vs. Proposed Operations Mapping

**Purpose**: Clear mapping of existing operations to proposed additions

---

## Entity Tool (tools/entity.py)

### Current Operations

| Operation | Entity Types | Status | Tests |
|-----------|--------------|--------|-------|
| **CREATE** | organization, project, document, requirement, test, user, profile | ✅ Implemented | test_entity_core.py, type-specific files |
| **READ** | All | ✅ Implemented | test_entity_core.py, type-specific files |
| **UPDATE** | All | ✅ Implemented | test_entity_core.py, type-specific files |
| **DELETE** | All | ✅ Implemented (hard-delete) | test_entity_core.py |
| **SEARCH** | All | ⚠️ Basic (full-text) | test_entity_core.py |

### Proposed Additions (Phase 1)

| Operation | Entity Types | Effort | Dependencies |
|-----------|--------------|--------|--------------|
| **LIST** | All | 3-4h | Database indexes on entity_type, is_deleted |
| **ARCHIVE** | All | 2-3h | Soft-delete logic (is_deleted=true with tracking) |
| **RESTORE** | All | 1-2h | Archive/soft-delete tracking |

### Proposed Additions (Phase 2)

| Operation | Entity Types | Effort | Dependencies |
|-----------|--------------|--------|--------------|
| **HISTORY** | All | 2h | entity_versions table migration |
| **RESTORE_VERSION** | All | 1-2h | Version tracking infrastructure |
| **BULK_UPDATE** | All | 2-3h | Transaction support |
| **BULK_DELETE** | All | 1-2h | Bulk delete with soft-delete |
| **BULK_ARCHIVE** | All | 1h | Archive infrastructure |

### Proposed Additions (Phase 3)

| Operation | Entity Types | Effort | Dependencies |
|-----------|--------------|--------|--------------|
| **EXPORT** | All | 2-3h | CSV/JSON serialization |
| **IMPORT** | All | 2-3h | File parsing, validation |
| **VALIDATE** | All | 1h | Schema validation |

---

## Relationship Tool (tools/relationship.py)

### Current Operations

| Operation | Relationship Types | Status | Tests |
|-----------|-------------------|--------|-------|
| **LIST** | All | ✅ Implemented | test_relationship.py |
| **UPDATE** | All | ✅ Implemented | test_relationship.py |

**Gap**: Cannot CREATE or DELETE relationships

### Proposed Additions (Phase 1)

| Operation | Relationship Types | Effort | Dependencies |
|-----------|-------------------|--------|--------------|
| **CREATE** | All | 2-3h | Entity validation |
| **DELETE** | All | 1-2h | Relationship lookup by ID or (from, to, type) |

### Proposed Additions (Phase 2)

| Operation | Relationship Types | Effort | Dependencies |
|-----------|-------------------|--------|--------------|
| **BULK_CREATE** | All | 1-2h | Batch insert with validation |
| **BULK_DELETE** | All | 1h | Batch delete |
| **METADATA** | All | 1-2h | Extend relationship schema for JSON metadata |

---

## Workspace Tool (tools/workspace.py)

### Current Operations

| Operation | Status | Tests |
|-----------|--------|-------|
| **LIST** | ✅ Implemented | test_workspace.py |

**Gap**: Only LIST implemented; missing complete CRUD

### Proposed Additions (Phase 1)

| Operation | Effort | Dependencies |
|-----------|--------|--------------|
| **CREATE** | 1-2h | Slug generation, owner tracking |
| **READ** | 0.5h | By ID lookup |
| **UPDATE** | 1h | Name, description, settings |
| **DELETE** | 1h | Soft-delete or hard-delete |
| **SWITCH** | 1h | Context switching logic |

---

## Query Tool (tools/query.py)

### Current Operations

| Operation | Status | Tests |
|-----------|--------|-------|
| **SEARCH** | ⚠️ Basic | test_query.py |
| **AGGREGATE** | ⚠️ Basic | test_query.py |

### Proposed Additions (Phase 3)

| Operation | Effort | Dependencies |
|-----------|--------|--------------|
| **SAVED_SEARCH** | 2-3h | Search storage (new table or JSON) |
| **FACETED_SEARCH** | 2-3h | Facet aggregation logic |
| **SEARCH_SUGGESTIONS** | 1-2h | Trie/autocomplete index |
| **SEARCH_ANALYTICS** | 1h | Search logging, aggregation |

---

## Workflow Tool (tools/workflow.py)

### Current Operations

| Operation | Workflow Type | Status | Tests |
|-----------|---------------|--------|-------|
| **setup_project_workflow** | Project Setup | ✅ Implemented | test_workflow.py |
| **import_requirements_workflow** | Requirements Import | ✅ Implemented | test_workflow.py |
| **setup_test_matrix_workflow** | Test Matrix | ✅ Implemented | test_workflow.py |
| **bulk_status_update_workflow** | Bulk Status | ✅ Implemented | test_workflow.py |
| **organization_onboarding_workflow** | Org Onboarding | ✅ Implemented | test_workflow.py |

**Gap**: Pre-defined workflows only; no management operations

### Proposed Additions (Phase 2)

| Operation | Effort | Dependencies |
|-----------|--------|--------------|
| **LIST** | 1-2h | Return all workflows with metadata |
| **CREATE** | 2-3h | Workflow definition schema, validation |
| **UPDATE** | 1-2h | Update workflow steps/triggers |
| **DELETE** | 1h | Archive or hard-delete |
| **ENABLE/DISABLE** | 1h | Workflow status toggle |

---

## Proposed New Operations Summary

### By Phase

**Phase 1 (Blocking)**: 11 operations
- Entity: LIST, ARCHIVE, RESTORE
- Relationship: CREATE, DELETE
- Workspace: CREATE, READ, UPDATE, DELETE, SWITCH
- **Effort**: 15 hours

**Phase 2 (Important)**: 13 operations
- Entity: HISTORY, RESTORE_VERSION, BULK_UPDATE, BULK_DELETE, BULK_ARCHIVE
- Relationship: BULK_CREATE, BULK_DELETE, METADATA
- Workflow: LIST, CREATE, UPDATE, DELETE, ENABLE/DISABLE
- **Effort**: 15 hours

**Phase 3 (Polish)**: 10 operations
- Entity: EXPORT, IMPORT, VALIDATE
- Query: SAVED_SEARCH, FACETED_SEARCH, SEARCH_SUGGESTIONS, SEARCH_ANALYTICS
- Permissions: GRANT, REVOKE, CHECK (new)
- Infrastructure: Performance optimization
- **Effort**: 10-15 hours

**Total**: ~34 new operations across all tools

---

## Test Files to Create

### Phase 1 (4 new files)

| Test File | Coverage | Lines |
|-----------|----------|-------|
| `test_entity_list.py` | LIST for all types, pagination, filtering, sorting | 150-200 |
| `test_entity_archive.py` | ARCHIVE/RESTORE, cascade behavior | 100-150 |
| `test_relationship_crud.py` | CREATE, DELETE relationships | 100-120 |
| `test_workspace_crud.py` | CRUD + SWITCH operations | 120-150 |

### Phase 2 (4 new files)

| Test File | Coverage | Lines |
|-----------|----------|-------|
| `test_entity_bulk.py` | Bulk operations, atomic transactions | 120-150 |
| `test_entity_history.py` | Version history, restore | 150-180 |
| `test_entity_traceability.py` | Requirement-test linking, coverage | 100-150 |
| `test_workflow_management.py` | Workflow CRUD + enable/disable | 150-180 |

### Phase 3 (4 new files)

| Test File | Coverage | Lines |
|-----------|----------|-------|
| `test_search_advanced.py` | Saved searches, facets, suggestions | 150-180 |
| `test_data_export.py` | CSV/JSON export | 100-150 |
| `test_data_import.py` | CSV/JSON import | 100-150 |
| `test_entity_permissions.py` | Grant, revoke, inheritance | 150-180 |

**Total**: 12 new canonical test files, ~1,600 lines of tests

---

## Code Changes Required

### Module Size Impact

**Before Phase 1**:
- `tools/entity.py`: 804 lines (currently at limit)
- `tools/relationship.py`: 470+ lines
- `tools/workspace.py`: 240+ lines
- `tools/workflow.py`: 420+ lines

**After Phase 1** (with decomposition):
- `tools/entity.py`: Split into submodules (operations, validation, schema)
- `tools/relationship.py`: Add CREATE/DELETE, keep <500 lines
- `tools/workspace.py`: Add CRUD operations, keep <350 lines
- `tools/workflow.py`: Add management operations, keep <500 lines

**Decomposition Strategy**:

1. **tools/entity/** (submodule):
   - `__init__.py` - exports public API
   - `crud.py` - CREATE, READ, UPDATE, DELETE
   - `list.py` - LIST with pagination/filtering/sorting
   - `archive.py` - ARCHIVE, RESTORE
   - `history.py` - HISTORY, RESTORE_VERSION
   - `bulk.py` - BULK_UPDATE, BULK_DELETE, BULK_ARCHIVE
   - `schema.py` - schema validation
   - `validators.py` - input validation

2. **tools/relationship** (inline, <500 lines):
   - Add CREATE, DELETE
   - Add BULK_CREATE, BULK_DELETE
   - Keep UPDATE, LIST

3. **tools/workspace/** (small file, <350):
   - Add CREATE, READ, UPDATE, DELETE, SWITCH
   - Keep LIST

4. **tools/workflow** (keep <500):
   - Add LIST, CREATE, UPDATE, DELETE, ENABLE/DISABLE
   - Keep existing workflows

---

## Dependencies Between Operations

### Blocker Analysis

**Blocking Phase 1**:
- None (all Phase 1 ops are independent or require only small changes)

**Blocking Phase 2**:
- Version history requires Phase 1 completion
- Bulk operations independent
- Traceability requires Phase 1 (relationship CREATE)
- Workflow management independent

**Blocking Phase 3**:
- Export/import independent
- Permissions requires Phase 1 (ACL model)
- Search enhancements independent

---

## Backwards Compatibility

### Phase 1
- ✅ **Fully backwards compatible**
- New operations only (no signature changes)
- No schema changes required
- Old clients continue to work

### Phase 2
- ⚠️ **Schema migration required** (entity_versions table)
- Backwards compatible if version operations are optional
- Can enable via feature flag

### Phase 3
- ✅ **Fully backwards compatible**
- New operations only
- No schema changes required

---

## Performance Impact

### Phase 1
- LIST with pagination: O(1) per page (with index)
- ARCHIVE: O(1) update
- Relationship CREATE/DELETE: O(1)
- **Impact**: Minimal (mostly reads)

### Phase 2
- Version history: +storage for versions table (estimate 10-20% size increase)
- Bulk operations: Better performance than N individual ops
- **Impact**: Moderate (new table, triggers)

### Phase 3
- Search indexes: +storage for facet/suggestion indexes
- Export/import: CPU-bound, suitable for background jobs
- **Impact**: Moderate (new indexes)

---

## Rollout Validation

### Phase 1 Validation
```
Validators:
- All CRUD operations work
- LIST returns paginated results
- ARCHIVE hides from LIST
- RESTORE works correctly
- Relationship CREATE/DELETE complete lifecycle
- Workspace CRUD fully functional
- No regressions in existing tests
```

### Phase 2 Validation
```
Validators:
- Version history tracks all changes
- RESTORE_VERSION works correctly
- Bulk operations atomic (all-or-nothing)
- Workflow management CRUD works
- Schema migration successful
- No data loss
```

### Phase 3 Validation
```
Validators:
- Saved searches persist and execute
- Faceted search returns correct counts
- Export produces valid CSV/JSON
- Import validates and stores correctly
- Permissions enforce correctly
- Performance meets benchmarks
```

---

## Success Metrics

| Metric | Phase 1 Target | Phase 2 Target | Phase 3 Target |
|--------|---|---|---|
| **Test Coverage** | 80%+ | 85%+ | 90%+ |
| **Operation Count** | 11 ops working | 24 ops working | 34 ops working |
| **User Stories** | 15 passing | 30 passing | 40+ passing |
| **File Size** | All <500 lines | All <500 lines | All <500 lines |
| **Test File Count** | 4 new files | 8 new files | 12 new files |
| **Integration Tests** | All pass | All pass | All pass |
| **E2E Tests** | Pass | Pass | Pass |
| **Performance** | <1s per query | <1s per query | <1s per query |

---

## Implementation Sequence

### Recommended Order

1. **LIST operations** (foundation for UI navigation)
2. **ARCHIVE/RESTORE** (data integrity)
3. **Relationship CREATE/DELETE** (complete data model)
4. **Workspace CRUD** (user context management)
5. **Bulk operations** (efficiency)
6. **Version history** (audit trail)
7. **Workflow management** (advanced automation)
8. **Search features** (discovery)
9. **Export/import** (integration)
10. **Permissions** (fine-grained access)

---

## Related Documentation

- **Proposal**: `openspec/changes/complete-crud-operations/proposal.md`
- **Tasks**: `openspec/changes/complete-crud-operations/tasks.md`
- **Audit**: `01_CRUD_AUDIT.md`
- **Overview**: `00_SESSION_OVERVIEW.md`
