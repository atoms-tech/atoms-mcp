# Specifications: User Story Mapping & Test Coverage

## Current Test Coverage Status

**Total Tests:** 1790  
**E2E Tests:** 244 selected (236 passing, 8 skipped)  
**Coverage:** ~13% of total tests are E2E (rest are unit/integration)

## User Story Mapping

### ✅ Implemented & Tested (236 tests)

1. **Organization Management** (5 stories)
   - Create organization with metadata ✅
   - View organization details and members ✅
   - Update organization settings ✅
   - Delete organization (soft delete + cascade) ✅
   - List all organizations ✅

2. **Project Management** (5 stories)
   - Create project within organization ✅
   - View project details and hierarchy ✅
   - Update project info ✅
   - Archive/unarchive project ✅
   - List projects with pagination ✅

3. **Document Management** (3 stories)
   - Create document within project ✅
   - View document content and metadata ✅
   - List documents with filtering ✅

4. **Requirements Traceability** (4 stories)
   - Create requirements from templates ✅
   - Import requirements via workflow ✅
   - Search requirements by text/tags/status ✅
   - Trace links: requirement→test→implementation ✅

5. **Test Case Management** (2 stories)
   - Create test cases linked to requirements ✅
   - View test results and coverage metrics ✅

6. **Workspace Navigation** (6 stories)
   - Get current workspace context ✅
   - Switch to organization workspace ✅
   - Switch to project workspace ✅
   - Switch to document workspace ✅
   - List all available workspaces ✅
   - Get workspace defaults ✅

7. **Entity Relationships** (4 stories)
   - Link entities (member, assignment, trace_link) ✅
   - Unlink related entities ✅
   - View entity relationships ✅
   - Check if entities are related ✅

8. **Search & Discovery** (7 stories)
   - Keyword search across all entity types ✅
   - Filter search results ✅
   - Semantic search using embeddings ✅
   - Hybrid search (keyword + semantic) ✅
   - Get entity count aggregates ✅
   - Find similar entities by embedding ✅
   - Advanced search with AND/OR/NOT ✅

9. **Workflow Automation** (5 stories)
   - Run workflows with transactions ✅
   - Set up new project workflow ✅
   - Import requirements via workflow ✅
   - Bulk update statuses ✅
   - Onboard new organization ✅

10. **Data Management** (3 stories)
    - Batch create multiple entities ✅
    - Paginate through large lists ✅
    - Sort query results ✅

11. **Security & Access** (4 stories)
    - Authenticate via AuthKit OAuth ✅
    - Maintain active session ✅
    - Log out securely ✅
    - Row-level security prevents cross-user access ✅

### ⏳ Pending (8 tests skipped)

12. **Permission Middleware** (8 stories)
    - Create permission denied cross-workspace ⏳
    - Create permission missing workspace_id ⏳
    - Permission error messages descriptive ⏳
    - Workspace membership validation ⏳
    - Role-based permission differences ⏳
    - List permission works ⏳
    - List permission missing workspace_id ⏳
    - Create permission allowed in workspace ⏳

**Reason:** Auth token validation pending - requires WorkOS token refresh mechanism

## Test File Organization

### Canonical Names (Good - 15 files)
- test_search_and_discovery.py
- test_workspace_navigation.py
- test_entity_relationships.py
- test_workflow_execution.py
- test_workflow_scenarios.py
- test_workflow_automation.py
- test_requirements_traceability.py
- test_resilience.py
- test_security.py
- test_performance.py
- test_organization_crud.py
- test_project_management.py
- test_document_management.py
- test_data_management.py
- test_crud.py

### Non-Canonical Names (Consolidation Candidates - 10 files)
- test_auth.py + test_auth_patterns.py → merge
- test_database.py → move to integration
- test_error_recovery.py → merge with test_resilience.py
- test_concurrent_workflows.py → merge with test_workflow_execution.py
- test_project_workflow.py → merge with test_workflow_execution.py
- test_permission_middleware.py → keep (8 skipped)
- test_redis_end_to_end.py → move to integration
- test_simple_e2e.py → consolidate

## Coverage Gaps

- Permission middleware (8 tests) - auth token validation
- Integration tests for database, auth, cache layers
- Performance baselines for large datasets
- Flaky test fixes (2 tests with retry logic)

