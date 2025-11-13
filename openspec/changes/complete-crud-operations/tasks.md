# Implementation Tasks for Complete CRUD Operations

**Change ID**: complete-crud-operations  
**Total Estimated Effort**: 40-50 hours across 3 phases  
**Timeline**: 4-5 weeks (Phase 1: 1 week, Phase 2: 1 week, Phase 3: 1+ weeks)

---

## Phase 1: Blocking Operations (Week 1 - ~15 hours)

### 1. LIST Operations for All Entity Types

**Epic**: Add comprehensive LIST/search with pagination, filtering, sorting for all entities

#### 1.1 Add LIST to entity_tool (core implementation)
- **Description**: Extend entity.py to support LIST operation with pagination, filtering, sorting
- **Acceptance Criteria**:
  - LIST returns paginated results (offset/limit)
  - Support filter objects with operators (eq, ne, gt, lt, gte, lte, in, contains, starts_with)
  - Support sort arrays with field/direction
  - Return total count + results
  - All entity types supported (organization, project, document, requirement, test, user, profile)
- **Testing**: Unit test in `test_entity_list.py` (new file)
  - Test pagination (offset, limit, total)
  - Test filtering by status, priority, created_date
  - Test sorting by multiple fields
  - Test empty results
  - Test large result sets (1000+)
  - Parametrized across all entity types
- **Effort**: 3-4 hours

#### 1.2 User story tests for LIST operations
- **Description**: Add user story acceptance tests for entity listing
- **Acceptance Criteria**:
  - "User can list all organizations"
  - "User can list all projects in an organization"
  - "User can list all documents in a project"
  - "User can list all requirements in a document"
  - "User can list all test cases in a project"
  - "User can filter by status, priority, date range"
  - "User can sort by name, date, priority"
  - "User can paginate results"
- **Testing**: User story acceptance tests in `test_entity_list.py`
- **Effort**: 2-3 hours

#### 1.3 Integration tests for LIST performance
- **Description**: Verify LIST performance with realistic data volumes
- **Acceptance Criteria**:
  - LIST with 1000+ results completes in <1s
  - Pagination works smoothly
  - Filtering/sorting doesn't degrade performance
  - Memory usage stays reasonable
- **Testing**: Performance tests in `tests/performance/test_entity_list_performance.py`
- **Effort**: 1-2 hours

---

### 2. ARCHIVE & RESTORE Operations

**Epic**: Implement soft-delete with restore capability for all entities

#### 2.1 Add ARCHIVE and RESTORE operations to entity_tool
- **Description**: Extend entity.py with archive (soft-delete) and restore operations
- **Acceptance Criteria**:
  - ARCHIVE operation sets is_deleted = true
  - RESTORE operation sets is_deleted = false
  - Archived entities are hidden from LIST by default
  - Archive includes timestamp and user tracking
  - Restore works only for soft-deleted entities
  - Cannot restore already-deleted entities (if hard-delete exists)
- **Testing**: Unit tests in `test_entity_archive.py` (new file)
  - Test archive operation
  - Test restore operation
  - Test archived items hidden from LIST
  - Test archive with relationships (cascade behavior)
  - Parametrized across all entity types
- **Effort**: 2-3 hours

#### 2.2 User story tests for ARCHIVE/RESTORE
- **Description**: Add user story acceptance tests for archival
- **Acceptance Criteria**:
  - "User can archive an organization"
  - "User can restore an archived organization"
  - "User can archive a project"
  - "User can archive a document"
  - "User can archive a requirement"
  - "Archived entities appear in a separate list"
  - "User can view archived items"
- **Testing**: User story acceptance tests in `test_entity_archive.py`
- **Effort**: 1-2 hours

#### 2.3 Test cascade behavior for related entities
- **Description**: Define and test archive cascade rules
- **Acceptance Criteria**:
  - Archiving project doesn't auto-archive documents (explicit archive only)
  - Archiving document doesn't auto-archive requirements (explicit archive only)
  - Define cascade rules per relationship (document_level)
  - Restore works only if parent isn't archived
  - Return appropriate error if parent archived
- **Testing**: Integration tests in `test_entity_archive.py`
- **Effort**: 1-2 hours

---

### 3. Relationship CREATE & DELETE Operations

**Epic**: Complete relationship CRUD (currently missing CREATE and DELETE)

#### 3.1 Add CREATE relationship to relationship_tool
- **Description**: Implement relationship creation
- **Acceptance Criteria**:
  - Can create relationships between entities
  - Validates relationship_type exists
  - Validates from_id and to_id are valid entities
  - Prevents duplicate relationships
  - Supports optional metadata (JSON)
  - Returns created relationship with ID
- **Testing**: Unit tests in `test_relationship_crud.py` (new file)
  - Test create valid relationship
  - Test invalid entity IDs
  - Test duplicate prevention
  - Test with metadata
  - Parametrized across relationship types
- **Effort**: 2-3 hours

#### 3.2 Add DELETE relationship to relationship_tool
- **Description**: Implement relationship deletion
- **Acceptance Criteria**:
  - Can delete relationships by ID
  - Can delete specific relationship (from_id, to_id, relationship_type)
  - Returns success/failure
  - Handles already-deleted relationships gracefully
- **Testing**: Unit tests in `test_relationship_crud.py`
  - Test delete by ID
  - Test delete by (from, to, type)
  - Test non-existent relationship
- **Effort**: 1-2 hours

#### 3.3 User story tests for relationship management
- **Description**: Add user story acceptance tests for relationship operations
- **Acceptance Criteria**:
  - "User can create a relationship between entities"
  - "User can delete a relationship"
  - "User can link requirement to test"
  - "User can link requirement to requirement (parent-child)"
- **Testing**: User story acceptance tests in `test_relationship_crud.py`
- **Effort**: 1 hour

---

### 4. Workspace CRUD Completion

**Epic**: Complete workspace management (currently only LIST)

#### 4.1 Add CREATE workspace
- **Description**: Allow users to create new workspaces
- **Acceptance Criteria**:
  - Create workspace with name, optional description
  - Auto-generate slug from name
  - Set creator as owner
  - Return created workspace with ID
  - Validates required fields
- **Testing**: Unit tests in `test_workspace_crud.py` (new file)
  - Test create with required fields
  - Test create with optional description
  - Test slug generation
  - Test validation
- **Effort**: 1-2 hours

#### 4.2 Add READ workspace
- **Description**: Fetch workspace details
- **Acceptance Criteria**:
  - Get workspace by ID
  - Return all workspace metadata
  - Return error if not found
- **Testing**: Unit tests in `test_workspace_crud.py`
- **Effort**: 0.5 hours

#### 4.3 Add UPDATE workspace
- **Description**: Update workspace name, description, settings
- **Acceptance Criteria**:
  - Update name, description, settings
  - Regenerate slug if name changes
  - Only owner/admin can update
  - Return updated workspace
- **Testing**: Unit tests in `test_workspace_crud.py`
- **Effort**: 1 hour

#### 4.4 Add DELETE workspace
- **Description**: Delete or soft-delete workspace
- **Acceptance Criteria**:
  - DELETE (hard) or ARCHIVE (soft)
  - Only owner/admin can delete
  - Prevent deletion if entities exist (or cascade)
  - Return success/error
- **Testing**: Unit tests in `test_workspace_crud.py`
- **Effort**: 1 hour

#### 4.5 Add SWITCH workspace
- **Description**: Change current workspace context
- **Acceptance Criteria**:
  - Switch to different workspace
  - Update context state
  - Return success/error
  - Optional: Set as default
- **Testing**: Unit tests in `test_workspace_crud.py`
- **Effort**: 1 hour

#### 4.6 User story tests for workspace management
- **Description**: Add user story acceptance tests
- **Acceptance Criteria**:
  - "User can create a workspace"
  - "User can view workspace details"
  - "User can update workspace name and description"
  - "User can delete a workspace"
  - "User can switch between workspaces"
  - "User can set a default workspace"
- **Testing**: User story acceptance tests in `test_workspace_crud.py`
- **Effort**: 1-2 hours

---

### 5. Comprehensive Test Coverage for Phase 1

#### 5.1 Create test_entity_list.py (canonical)
- Parametrized LIST tests across all entity types
- Filter/sort/pagination tests
- Performance tests
- Baseline: 150-200 lines

#### 5.2 Create test_entity_archive.py (canonical)
- ARCHIVE/RESTORE operation tests
- Cascade behavior tests
- Baseline: 100-150 lines

#### 5.3 Create test_relationship_crud.py (canonical)
- Relationship CREATE/DELETE tests
- Validation tests
- Baseline: 100-120 lines

#### 5.4 Create test_workspace_crud.py (canonical)
- Workspace CREATE/READ/UPDATE/DELETE tests
- User story acceptance tests
- Baseline: 120-150 lines

#### 5.5 Run full test suite
- All Phase 1 tests pass
- No regressions in existing tests
- Coverage reports generated
- Effort: 1 hour

---

## Phase 2: Important Operations (Week 2 - ~15 hours)

### 6. Bulk Operations

**Epic**: Bulk update, bulk delete, bulk archive for efficiency

#### 6.1 Add BULK_UPDATE operation
- **Description**: Update multiple entities at once
- **Acceptance Criteria**:
  - Update list of entity IDs with same data
  - Atomic transaction (all-or-nothing)
  - Return list of updated IDs or errors
  - Validate each entity before update
- **Testing**: Unit tests in `test_entity_bulk.py` (new file)
- **Effort**: 2-3 hours

#### 6.2 Add BULK_DELETE operation
- **Description**: Soft-delete multiple entities
- **Acceptance Criteria**:
  - Delete list of entity IDs
  - Archive (soft-delete) by default
  - Atomic transaction
  - Return results per entity
- **Testing**: Unit tests in `test_entity_bulk.py`
- **Effort**: 1-2 hours

#### 6.3 Add BULK_ARCHIVE operation
- **Description**: Archive multiple entities (explicit)
- **Acceptance Criteria**:
  - Explicitly archive list of entities
  - Distinguish from delete
  - Return results
- **Testing**: Unit tests in `test_entity_bulk.py`
- **Effort**: 1 hour

#### 6.4 User story tests for bulk operations
- **Description**: User story acceptance tests
- **Acceptance Criteria**:
  - "User can bulk update requirements"
  - "User can bulk archive test cases"
  - "User can bulk delete old records"
  - "User receives detailed results for each item"
- **Testing**: User story tests in `test_entity_bulk.py`
- **Effort**: 1-2 hours

---

### 7. Document Version History

**Epic**: Track document changes, support restore to previous version

#### 7.1 Create entity_versions schema migration
- **Description**: Add entity_versions table to track all changes
- **Acceptance Criteria**:
  - Table structure: id, entity_id, entity_type, version_num, data (JSON), changed_by, changed_at
  - Auto-populate on every entity update
  - Index on (entity_id, entity_type, version_num)
  - Trigger or application-level tracking
- **Effort**: 1-2 hours

#### 7.2 Add HISTORY operation to entity_tool
- **Description**: Retrieve version history for an entity
- **Acceptance Criteria**:
  - Get all versions of an entity
  - Return version list with timestamps, author, changes
  - Support filtering by date range
  - Pagination support
- **Testing**: Unit tests in `test_entity_history.py` (new file)
- **Effort**: 2 hours

#### 7.3 Add RESTORE_VERSION operation
- **Description**: Restore entity to specific version
- **Acceptance Criteria**:
  - Restore entity to any previous version
  - Create new version entry (don't overwrite)
  - Return restored entity
  - Track who restored and when
- **Testing**: Unit tests in `test_entity_history.py`
- **Effort**: 1-2 hours

#### 7.4 User story tests for version history
- **Description**: User story acceptance tests
- **Acceptance Criteria**:
  - "User can view document version history"
  - "User can see who changed what and when"
  - "User can restore a previous version"
  - "User can compare two versions"
- **Testing**: User story tests in `test_entity_history.py`
- **Effort**: 1-2 hours

---

### 8. Requirement Traceability

**Epic**: Link requirements to tests, track coverage

#### 8.1 Add TRACE operation to entity_tool
- **Description**: Get traceability info (what tests cover this requirement)
- **Acceptance Criteria**:
  - Query requirement -> get linked test cases
  - Query test case -> get linked requirements
  - Return relationship metadata
  - Support filtering by test status
- **Testing**: Unit tests in `test_entity_traceability.py` (new file)
- **Effort**: 2 hours

#### 8.2 Add COVERAGE operation
- **Description**: Get coverage analysis (how many requirements are tested)
- **Acceptance Criteria**:
  - Calculate coverage percentage per document/project
  - Return untested requirements
  - Return over-tested requirements
  - Return coverage by priority
- **Testing**: Unit tests in `test_entity_traceability.py`
- **Effort**: 2 hours

#### 8.3 User story tests for traceability
- **Description**: User story acceptance tests
- **Acceptance Criteria**:
  - "User can see which tests cover a requirement"
  - "User can see which requirements a test covers"
  - "User can view overall test coverage percentage"
  - "User can find untested requirements"
- **Testing**: User story tests in `test_entity_traceability.py`
- **Effort**: 1-2 hours

---

### 9. Workflow Management CRUD

**Epic**: Full lifecycle management for workflows

#### 9.1 Add LIST workflows
- **Description**: List all configured workflows
- **Acceptance Criteria**:
  - Return all workflows with metadata
  - Filter by status (enabled/disabled/archived)
  - Return workflow triggers, steps, conditions
  - Pagination support
- **Testing**: Unit tests in `test_workflow_management.py` (new file)
- **Effort**: 1-2 hours

#### 9.2 Add CREATE workflow
- **Description**: Define custom workflow
- **Acceptance Criteria**:
  - Create workflow with name, description, entity_type
  - Define workflow steps/triggers
  - Validate workflow definition (no cycles, valid conditions)
  - Return created workflow with ID
- **Testing**: Unit tests in `test_workflow_management.py`
- **Effort**: 2-3 hours

#### 9.3 Add UPDATE workflow
- **Description**: Modify existing workflow
- **Acceptance Criteria**:
  - Update workflow definition
  - Validate changes
  - Don't allow invalid states
  - Track modification timestamp
- **Testing**: Unit tests in `test_workflow_management.py`
- **Effort**: 1-2 hours

#### 9.4 Add DELETE workflow
- **Description**: Remove workflow
- **Acceptance Criteria**:
  - DELETE (hard) or ARCHIVE (soft)
  - Only owner/admin can delete
  - Cannot delete active workflows (must disable first)
  - Return success/error
- **Testing**: Unit tests in `test_workflow_management.py`
- **Effort**: 1 hour

#### 9.5 Add ENABLE/DISABLE workflow
- **Description**: Toggle workflow active state
- **Acceptance Criteria**:
  - ENABLE activates workflow
  - DISABLE deactivates workflow
  - Cannot enable invalid workflows
  - Track state changes
- **Testing**: Unit tests in `test_workflow_management.py`
- **Effort**: 1 hour

#### 9.6 User story tests for workflow management
- **Description**: User story acceptance tests
- **Acceptance Criteria**:
  - "Admin can create custom workflows"
  - "Admin can list all workflows"
  - "Admin can update workflow definitions"
  - "Admin can enable/disable workflows"
  - "Admin can delete unused workflows"
- **Testing**: User story tests in `test_workflow_management.py`
- **Effort**: 1-2 hours

---

### 10. Phase 2 Test Coverage

#### 10.1 Create test_entity_bulk.py (canonical)
- Bulk operation tests
- Baseline: 120-150 lines

#### 10.2 Create test_entity_history.py (canonical)
- Version history tests
- Baseline: 150-180 lines

#### 10.3 Create test_entity_traceability.py (canonical)
- Traceability and coverage tests
- Baseline: 100-150 lines

#### 10.4 Create test_workflow_management.py (canonical)
- Workflow CRUD tests
- Baseline: 150-180 lines

#### 10.5 Run full test suite
- Phase 1 + Phase 2 tests pass
- No regressions
- Coverage maintained/improved

---

## Phase 3: Polish & Integration (Week 3+ - ~10-15 hours)

### 11. Search Enhancements

**Epic**: Saved searches, facets, suggestions, advanced filters

#### 11.1 Add SAVED_SEARCH operations
- **Description**: Store and retrieve frequently-used searches
- **Acceptance Criteria**:
  - CREATE saved search (name, query, filters, sorts)
  - LIST saved searches
  - UPDATE saved search
  - DELETE saved search
  - Execute saved search by ID
- **Testing**: Unit tests in `test_search_advanced.py` (new file)
- **Effort**: 2-3 hours

#### 11.2 Add FACETED_SEARCH
- **Description**: Browse results by facets (status, priority, created_date, etc.)
- **Acceptance Criteria**:
  - Return facets with counts
  - Support drilling down into facets
  - Combine multiple facet selections
  - Return results filtered by facets
- **Testing**: Unit tests in `test_search_advanced.py`
- **Effort**: 2-3 hours

#### 11.3 Add SEARCH_SUGGESTIONS
- **Description**: Autocomplete and recommendations
- **Acceptance Criteria**:
  - As-you-type suggestions
  - Popular terms suggestions
  - Entity name suggestions
  - Smart filtering (show relevant suggestions only)
- **Testing**: Unit tests in `test_search_advanced.py`
- **Effort**: 1-2 hours

#### 11.4 User story tests for search
- **Description**: User story acceptance tests
- **Acceptance Criteria**:
  - "User can save frequently-used searches"
  - "User can view recent searches"
  - "User can get search suggestions as they type"
  - "User can use facets to filter results"
- **Testing**: User story tests in `test_search_advanced.py`
- **Effort**: 1-2 hours

---

### 12. Data Export/Import

**Epic**: CSV and JSON export/import support

#### 12.1 Add EXPORT operation
- **Description**: Export entities to CSV or JSON
- **Acceptance Criteria**:
  - Export to CSV with column selection
  - Export to JSON with full entity data
  - Include relationships in export (JSON only)
  - Respect filters/sorts in export
  - Stream large exports
- **Testing**: Unit tests in `test_data_export.py` (new file)
- **Effort**: 2-3 hours

#### 12.2 Add IMPORT operation
- **Description**: Bulk import from CSV/JSON
- **Acceptance Criteria**:
  - Parse CSV/JSON format
  - Validate data before import
  - Handle duplicates (skip/merge/fail)
  - Batch process for large files
  - Return import report (success/failures)
- **Testing**: Unit tests in `test_data_import.py` (new file)
- **Effort**: 2-3 hours

#### 12.3 User story tests for export/import
- **Description**: User story acceptance tests
- **Acceptance Criteria**:
  - "User can export requirements to CSV"
  - "User can export with filters/sorts"
  - "User can import requirements from CSV"
  - "User receives import report with errors"
- **Testing**: User story tests in `test_data_export.py` and `test_data_import.py`
- **Effort**: 1-2 hours

---

### 13. Advanced Permissions

**Epic**: Fine-grained access control per entity

#### 13.1 Add per-entity permissions
- **Description**: Define who can read/edit/delete each entity
- **Acceptance Criteria**:
  - Grant permissions to users/teams per entity
  - Support role-based permissions (owner, editor, viewer)
  - Check permissions on operations
  - Return 403 if not authorized
- **Testing**: Unit tests in `test_entity_permissions.py` (new file)
- **Effort**: 2-3 hours

#### 13.2 Add permission inheritance
- **Description**: Child entities inherit parent permissions
- **Acceptance Criteria**:
  - Documents inherit project permissions
  - Requirements inherit document permissions
  - Override inheritance per entity
  - Track permission overrides
- **Testing**: Unit tests in `test_entity_permissions.py`
- **Effort**: 1-2 hours

#### 13.3 User story tests for permissions
- **Description**: User story acceptance tests
- **Acceptance Criteria**:
  - "User can grant read/edit permissions to team members"
  - "User can revoke permissions"
  - "Permission inheritance works correctly"
- **Testing**: User story tests in `test_entity_permissions.py`
- **Effort**: 1 hour

---

### 14. Performance Optimization

#### 14.1 Add database indexes
- **Description**: Optimize query performance
- **Acceptance Criteria**:
  - Index on entity_type, is_deleted, status, priority
  - Index on relationship (from_id, to_id, type)
  - Index on created_at, updated_at for sorting
  - Verify query plans use indexes
- **Testing**: Performance tests
- **Effort**: 1-2 hours

#### 14.2 Caching strategy
- **Description**: Cache frequently-accessed data
- **Acceptance Criteria**:
  - Cache entity by ID
  - Cache LIST results (invalidate on CREATE/UPDATE/DELETE)
  - Cache saved searches
  - Configurable TTL
- **Testing**: Unit tests for cache behavior
- **Effort**: 1-2 hours

---

### 15. Phase 3 Test Coverage

#### 15.1 Create test_search_advanced.py (canonical)
- Saved searches, facets, suggestions
- Baseline: 150-180 lines

#### 15.2 Create test_data_export.py (canonical)
- Export functionality tests
- Baseline: 100-150 lines

#### 15.3 Create test_data_import.py (canonical)
- Import functionality tests
- Baseline: 100-150 lines

#### 15.4 Create test_entity_permissions.py (canonical)
- Permission tests
- Baseline: 150-180 lines

#### 15.5 Performance and integration tests
- Full test suite validation
- No regressions
- Performance benchmarks met

---

## Completion Checklist

### Phase 1 Completion ✓
- [ ] LIST operations implemented and tested
- [ ] ARCHIVE/RESTORE operations implemented and tested
- [ ] Relationship CREATE/DELETE implemented and tested
- [ ] Workspace CRUD completed and tested
- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] User stories validated
- [ ] No regressions in existing tests

### Phase 2 Completion ✓
- [ ] Bulk operations implemented and tested
- [ ] Version history implemented and tested
- [ ] Traceability/coverage implemented and tested
- [ ] Workflow management CRUD implemented and tested
- [ ] Schema migrations applied successfully
- [ ] All tests passing (Phases 1+2)
- [ ] Performance requirements met
- [ ] Backwards compatibility verified

### Phase 3 Completion ✓
- [ ] Search enhancements implemented and tested
- [ ] Export/import functionality working
- [ ] Advanced permissions implemented
- [ ] Performance optimizations complete
- [ ] All tests passing (all phases)
- [ ] Documentation complete
- [ ] Ready for production release

---

## Notes

- Each task includes specific acceptance criteria
- Testing strategy: unit + integration + user story acceptance tests
- Use canonical naming for new test files (see CLAUDE.md § 3.1)
- Fixtures and parametrization for variant testing
- No separate fast/slow test files; use markers instead
- All test files should follow existing patterns in `tests/unit/tools/`
