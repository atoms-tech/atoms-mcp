# Complete CRUD Operations for All Entities

**Change ID**: complete-crud-operations  
**Created**: 2025-11-13  
**Status**: Proposal  
**Author**: Claude (Agent)

---

## Summary

Currently, the Atoms MCP system has incomplete CRUD operations across all entity types. While basic CREATE/READ/UPDATE/DELETE operations exist, **critical operations are missing** that are essential for a production-ready system:

- **LIST operations** (essential for navigation and UI)
- **ARCHIVE operations** (data integrity without permanent deletion)
- **BULK operations** (efficiency for power users)
- **Relationship management** (CREATE/DELETE missing)
- **Workspace management** (only LIST implemented)
- **Search enhancements** (saved searches, facets, suggestions)
- **Version history** (document change tracking)
- **Traceability** (requirement-to-test mapping)

This proposal implements comprehensive CRUD operations in three phases, starting with blocking issues.

---

## Motivation

**Current State**: Basic CRUD operations exist, but production use is severely limited:

1. **No LIST operations** - Users cannot browse entities, see all items, paginate, filter, or sort
2. **Permanent DELETE only** - No soft-delete/archive means data loss and audit trail breaks
3. **Relationship gaps** - Can only list/update relationships; cannot create or delete them
4. **Workspace incomplete** - Only LIST; users cannot create, update, or switch workspaces
5. **No version history** - Document changes are not tracked; cannot restore previous versions
6. **Search is basic** - No saved searches, autocomplete, or advanced filters
7. **No bulk operations** - Power users stuck with one-at-a-time updates

**Why This Matters**:
- Users need to navigate entities (list, filter, sort, paginate)
- Organizations need audit trails (soft-delete, archive, restore)
- Teams need efficiency (bulk operations, templates, cloning)
- Content management requires history (version tracking, restore)
- Discovery requires search features (saved queries, suggestions)

---

## Scope

### Included in This Change

**Phase 1: Blocking Operations (Weeks 1-2)**
- LIST operations for all entity types (with pagination, filtering, sorting)
- Relationship CREATE and DELETE operations
- Soft-DELETE/ARCHIVE for all entities (with restore capability)
- Workspace CRUD (CREATE, READ, UPDATE, DELETE)

**Phase 2: Important Operations (Weeks 3-4)**
- Document version history (track changes, restore)
- Requirement traceability (link tests to requirements)
- Bulk operations (bulk update, bulk delete, bulk archive)
- Workflow management (LIST, CREATE, UPDATE, DELETE, ENABLE/DISABLE)

**Phase 3: Polish & Integration (Week 5+)**
- Search enhancements (saved searches, facets, suggestions)
- Data export/import (CSV, JSON)
- Advanced permissions (per-entity access control)
- Workflow templates and cloning

### NOT Included

- Real-time collaboration (comment threads, live cursors)
- Advanced analytics (search statistics, usage insights)
- External integrations (Jira, GitHub, Azure DevOps)
- Custom field definitions (low-priority enhancement)

---

## Design Decisions

### 1. Soft-Delete / Archive Pattern

**Decision**: Implement soft-delete using `is_deleted` flag + archive workflow.

**Rationale**:
- Preserves audit trail (no permanent data loss)
- Allows restore/undelete
- Follows industry-standard practice
- Enables data recovery for accidental deletion

**Implementation**:
```python
# DELETE → Archive (soft-delete)
operation: "delete"  # Deletes via soft-delete
operation: "archive" # Explicit archive operation
operation: "restore" # Un-archive deleted entity

# Database side (existing)
UPDATE entities SET is_deleted = true WHERE id = ?
```

### 2. LIST with Pagination, Filtering, Sorting

**Decision**: Use offset-based pagination with filter objects and sort arrays.

**Rationale**:
- Consistent with REST/GraphQL patterns
- Efficient for large datasets
- Flexible filtering and sorting
- Backwards compatible with existing list_entities

**Implementation**:
```python
# List operation structure
operation: "list"
entity_type: "requirement"
filters: [
  {field: "status", operator: "eq", value: "active"},
  {field: "priority", operator: "in", value: ["high", "critical"]},
  {field: "created_at", operator: "gte", value: "2025-01-01"}
]
sort: [
  {field: "priority", direction: "desc"},
  {field: "created_at", direction: "asc"}
]
pagination: {
  offset: 0,
  limit: 50
}
```

### 3. Bulk Operations

**Decision**: Single `bulk_update` and `bulk_delete` operations that accept lists of IDs.

**Rationale**:
- Reduces network round-trips
- Atomic transaction per bulk operation
- Same validation per item
- Efficient for power users

**Implementation**:
```python
# Bulk update
operation: "bulk_update"
entity_type: "requirement"
updates: {
  "status": "approved",
  "assigned_to": "team-lead-1"
}
entity_ids: ["req-1", "req-2", "req-3"]

# Bulk archive
operation: "bulk_archive"
entity_type: "requirement"
entity_ids: ["req-1", "req-2", "req-3"]
```

### 4. Relationship Management

**Decision**: Add CREATE and DELETE operations to relationship_tool; update LIST and UPDATE to support bulk.

**Rationale**:
- Completes the CRUD lifecycle for relationships
- Bulk operations improve efficiency
- Relationships are first-class entities

**Implementation**:
```python
# Create relationship
operation: "create"
relationship_type: "requirement_test"
from_id: "req-1"
to_id: "test-5"
metadata: {coverage_type: "functional"}

# Delete relationship
operation: "delete"
relationship_type: "requirement_test"
from_id: "req-1"
to_id: "test-5"
```

### 5. Version History

**Decision**: Implement as separate `versions` table with change tracking; restore via update with version ID.

**Rationale**:
- Preserves complete change history
- Allows point-in-time recovery
- Tracks who changed what when
- Supports audit requirements

**Implementation** (in Phase 2):
```python
# Get version history
operation: "history"
entity_type: "document"
entity_id: "doc-1"

# Restore to version
operation: "restore_version"
entity_type: "document"
entity_id: "doc-1"
version_id: "v-123"
```

### 6. Workspace Management

**Decision**: Full CRUD for workspaces; treat as first-class navigational entity.

**Rationale**:
- Users need to create and manage workspaces
- Context switching is essential for multi-team users
- Workspace is a session concept, not just a container

**Implementation**:
```python
# Workspace CRUD
operation: "create"
entity_type: "workspace"
data: {name: "Q1 Planning", description: "..."}

operation: "switch"  # or use update?
entity_type: "workspace"
entity_id: "ws-1"
make_default: true
```

---

## Implementation Tasks

See `tasks.md` for detailed task breakdown with dependencies, estimates, and test criteria.

**High-level phases:**

1. **Phase 1** (Blocking):
   - Add LIST to entity_tool for all types ✓
   - Add ARCHIVE/RESTORE to entity_tool ✓
   - Add CREATE/DELETE to relationship_tool ✓
   - Complete workspace CRUD ✓

2. **Phase 2** (Important):
   - Add bulk operations ✓
   - Implement version history ✓
   - Add traceability search ✓
   - Implement workflow management ✓

3. **Phase 3** (Polish):
   - Add saved searches ✓
   - Implement data export/import ✓
   - Add advanced permissions ✓
   - Optimize search performance ✓

---

## Rollout Plan

### Deployment Strategy

1. **Phase 1** (T+0 days):
   - Deploy LIST, ARCHIVE, relationship CRUD, workspace CRUD
   - Backwards compatible (new operations only)
   - No schema changes required
   - Internal-only initially

2. **Phase 2** (T+7 days):
   - Deploy bulk operations, version history, traceability
   - Requires schema changes (add version table)
   - Migrate existing data
   - Beta feature flags for version history

3. **Phase 3** (T+14 days):
   - Deploy search enhancements, export/import
   - Full public availability
   - Remove beta feature flags

### Migration Path

- **Phase 1**: No migration needed (additive)
- **Phase 2**: Create `entity_versions` table; background job to populate history
- **Phase 3**: No migration needed

### Rollback Plan

1. **Phase 1**: Disable new operations via feature flag; fallback to old behavior
2. **Phase 2**: Drop `entity_versions` table; disable version operations
3. **Phase 3**: Disable export/import endpoints; revert to search_v1

---

## Risks & Mitigations

### ARU: Assumptions, Risks, Uncertainties

| Category | Description | Mitigation |
|----------|-------------|-----------|
| **Risk**: Pagination complexity | Offset-based pagination may not work well with frequent inserts | Use cursor-based pagination for large result sets; add option for both |
| **Risk**: Archive cascading | Archiving parent entities might need child cascade logic | Define cascade rules per entity type; document clearly |
| **Risk**: Bulk operation rollback | What if one item in bulk update fails? | All-or-nothing transaction; return detailed errors per item |
| **Assumption**: Existing list_entities works | Current pagination/filtering implementation | Verify with integration tests |
| **Uncertainty**: Relationship metadata storage | How to store relationship-specific data? | Use JSON column; define schema per relationship type |
| **Uncertainty**: Workspace context switching | How does workspace affect query scoping? | Document workspace-aware query patterns |

---

## Success Criteria

### Phase 1 Complete When:
- ✅ LIST operations work for all entity types with pagination/filtering/sorting
- ✅ ARCHIVE/RESTORE operations work for all entity types
- ✅ Relationship CREATE/DELETE operations work
- ✅ Workspace CRUD fully implemented
- ✅ All operations have comprehensive tests (unit + integration)
- ✅ User can navigate all entities via UI
- ✅ All tests pass

### Phase 2 Complete When:
- ✅ Bulk operations work and are tested
- ✅ Version history is tracked and restorable
- ✅ Requirement-to-test traceability works
- ✅ Workflow management CRUD works
- ✅ Integration tests verify cascading operations
- ✅ All tests pass

### Phase 3 Complete When:
- ✅ Saved searches work and persist
- ✅ Search suggestions/autocomplete works
- ✅ Export/import supports CSV and JSON
- ✅ Advanced permissions per entity work
- ✅ Performance optimizations complete
- ✅ All tests pass

---

## Technical Notes

### Code Organization

**Changes to `tools/entity.py`**:
- Add LIST operation with pagination, filtering, sorting
- Add ARCHIVE and RESTORE operations
- Extend existing CREATE/READ/UPDATE/DELETE

**Changes to `tools/relationship.py`**:
- Add CREATE operation
- Add DELETE operation
- Add bulk operations

**Changes to `tools/workspace.py`**:
- Add CREATE, READ, UPDATE, DELETE operations
- Add SWITCH operation
- Complete CRUD lifecycle

**New schema migrations** (Phase 2):
- `entity_versions` table for version history
- Triggers to auto-populate versions on entity updates

**Test Changes**:
- New test classes for LIST operations
- New test classes for ARCHIVE/RESTORE
- New test classes for bulk operations
- Update conftest with additional fixtures

### Performance Considerations

- LIST operations need DB indexes (entity_type, is_deleted, created_at, status)
- Pagination with large offsets (>10k) can be slow; use cursor-based for large datasets
- Bulk operations should batch in groups of 100-1000
- Version history queries should use filtered queries (not full table scans)

### Backwards Compatibility

- All new operations are additive (no breaking changes)
- Existing CREATE/READ/UPDATE/DELETE signatures unchanged
- Feature flags for Phase 2+ features during rollout
- Old clients work with Phase 1 (no schema changes)

---

## Related Documentation

- See `tasks.md` for detailed implementation task breakdown
- See `specs/` directory for detailed operation specifications
- Current state documented in `01_CRUD_AUDIT.md`

---

## Approval & Sign-Off

This proposal is ready for implementation planning. Review and approve to proceed with Phase 1 task breakdown.

**Next**: Review proposal → Approve → Create detailed task breakdown in `tasks.md` → Begin Phase 1 implementation.
