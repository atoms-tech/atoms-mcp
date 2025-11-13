# CRUD Completeness Audit

**Session**: 20251113-crud-completeness  
**Date**: 2025-11-13  
**Goal**: Identify incomplete CRUD operations across all entities and propose comprehensive user stories

---

## Executive Summary

Analysis of the codebase reveals **significant gaps in CRUD operations** across multiple entity types. Current implementation focuses on basic CREATE/READ/UPDATE/DELETE but **missing many essential operations** for production use:

### Gap Categories

| Category | Current | Needed | Gap |
|----------|---------|--------|-----|
| **Organization** | C,R,U,D (basic) | LIST, ARCHIVE, INVITE, CLONE | 4+ ops |
| **Project** | C,R,U,D (basic) | LIST, ARCHIVE, CLONE, SETTINGS | 4+ ops |
| **Document** | C,R,U,D (basic) | LIST, VERSION HISTORY, COPY, MOVE, PERMISSIONS | 5+ ops |
| **Requirement** | C,R,U,D (basic) | LIST, ARCHIVE, VERSION TRACKING, LINK/UNLINK, TRACE | 5+ ops |
| **Test Case** | C,R,U,D (basic) | LIST, ARCHIVE, CLONE, RUN, RESULTS | 5+ ops |
| **Relationship** | partial (LIST, UPDATE) | CREATE, DELETE, BULK, METADATA | 3+ ops |
| **Workspace** | LIST only | CREATE, READ, UPDATE, DELETE, SWITCH | 4+ ops |
| **Search** | basic query | SAVED SEARCHES, RECENT, FACETS, SUGGESTIONS | 4+ ops |
| **Workflow** | 5 workflows | LIST, UPDATE, DELETE, ENABLE/DISABLE, CLONE | 4+ ops |
| **Data Management** | basic CRUD | BULK DELETE, ARCHIVE, CLEANUP, EXPORT | 4+ ops |

---

## Entity-by-Entity Analysis

### 1. Organization

**Current Operations:**
- ✅ CREATE (create_entity)
- ✅ READ (read_entity)
- ✅ UPDATE (update_entity)
- ✅ DELETE (delete_entity)

**Missing Operations:**
- ❌ LIST organizations (no pagination, filtering, sorting)
- ❌ ARCHIVE organization (soft-delete with restore)
- ❌ INVITE members (batch invitations)
- ❌ CLONE organization (with members, projects, settings)
- ❌ SETTINGS management (per-organization feature flags)
- ❌ MEMBER roles/permissions (granular access control)
- ❌ AUDIT log (organization activity tracking)

**User Stories Needed:**
- "As an admin, I can list all organizations with filtering and pagination"
- "As an admin, I can archive an organization without losing data"
- "As an admin, I can invite multiple members to an organization"
- "As an admin, I can clone an organization with all its settings"

---

### 2. Project

**Current Operations:**
- ✅ CREATE (create_entity)
- ✅ READ (read_entity)
- ✅ UPDATE (update_entity)
- ✅ DELETE (delete_entity)

**Missing Operations:**
- ❌ LIST projects (by organization, with pagination, filtering)
- ❌ ARCHIVE project (soft-delete with restore)
- ❌ CLONE project (with documents, workflows, members)
- ❌ PROJECT settings (metadata, tags, custom fields)
- ❌ PROJECT templates (reusable project structure)
- ❌ TEAM management (assign members, roles)
- ❌ STATUS tracking (active, archived, completed)

**User Stories Needed:**
- "As a user, I can list all projects in my organization with filtering"
- "As a PM, I can archive a project to clean up old work"
- "As a PM, I can clone a project to reuse its structure"
- "As a PM, I can manage project settings and team members"

---

### 3. Document

**Current Operations:**
- ✅ CREATE (create_entity)
- ✅ READ (read_entity)
- ✅ UPDATE (update_entity)
- ✅ DELETE (delete_entity)

**Missing Operations:**
- ❌ LIST documents (by project, with pagination, filtering, sorting)
- ❌ VERSION history (track document changes, restore previous versions)
- ❌ COPY document (clone with relationships)
- ❌ MOVE document (change project/parent)
- ❌ PERMISSIONS (per-document access control)
- ❌ COMMENTS/ANNOTATIONS (document-level discussions)
- ❌ SHARING (public/private, shareable links)
- ❌ LOCK document (prevent concurrent edits)

**User Stories Needed:**
- "As a user, I can list all documents in a project with filtering"
- "As a user, I can view document version history and restore previous versions"
- "As a user, I can copy a document to create a variant"
- "As a user, I can move a document between projects"
- "As a user, I can set document permissions for team members"

---

### 4. Requirement

**Current Operations:**
- ✅ CREATE (create_entity)
- ✅ READ (read_entity)
- ✅ UPDATE (update_entity)
- ✅ DELETE (delete_entity)

**Missing Operations:**
- ❌ LIST requirements (by document, with filtering, sorting, pagination)
- ❌ ARCHIVE requirement (soft-delete with restore)
- ❌ VERSION tracking (track requirement changes over time)
- ❌ LINK requirements (parent-child, related)
- ❌ UNLINK requirements (remove relationships)
- ❌ TRACE traceability (linked to tests, code)
- ❌ BULK update (change status/priority for multiple)
- ❌ BULK assign (assign multiple requirements to team members)
- ❌ STATUS transitions (workflow: draft → review → approved → implemented)
- ❌ PRIORITY management (change priority for multiple)

**User Stories Needed:**
- "As a user, I can list all requirements in a document with filtering and sorting"
- "As a user, I can archive a requirement without losing its history"
- "As a user, I can link requirements to create parent-child relationships"
- "As a user, I can view requirement traceability (which tests cover it)"
- "As a user, I can bulk update requirement status across multiple items"

---

### 5. Test Case

**Current Operations:**
- ✅ CREATE (create_entity)
- ✅ READ (read_entity)
- ✅ UPDATE (update_entity)
- ✅ DELETE (delete_entity)

**Missing Operations:**
- ❌ LIST test cases (by project, by requirement, with pagination, filtering)
- ❌ ARCHIVE test case (soft-delete with restore)
- ❌ CLONE test case (duplicate with new ID)
- ❌ RUN test case (execute test, record result)
- ❌ TEST results (store execution results, history)
- ❌ TEST coverage (map to requirements)
- ❌ BULK run tests (run multiple, collect results)
- ❌ TEST status (active, deprecated, pending)
- ❌ EXPORT test cases (generate test scripts)

**User Stories Needed:**
- "As a QA, I can list all test cases for a project with filtering"
- "As a QA, I can clone a test case to create a variant"
- "As a QA, I can run a test case and record results"
- "As a QA, I can archive test cases no longer in use"
- "As a QA, I can view test coverage for requirements"

---

### 6. Relationship

**Current Operations:**
- ✅ LIST relationships (list_relationships)
- ✅ UPDATE relationship (update_relationship)

**Missing Operations:**
- ❌ CREATE relationship (create_relationship)
- ❌ DELETE relationship (delete_relationship)
- ❌ BULK create (create multiple relationships)
- ❌ BULK delete (delete multiple relationships)
- ❌ METADATA on relationships (relationship-specific data)
- ❌ VALIDATE relationships (check for cycles, validity)
- ❌ RELATIONSHIP types (define valid relationship patterns)

**User Stories Needed:**
- "As a user, I can create relationships between entities"
- "As a user, I can delete relationships"
- "As a user, I can bulk create multiple relationships"
- "As a user, I can add metadata to relationships"

---

### 7. Workspace

**Current Operations:**
- ✅ LIST workspaces (list_workspaces)

**Missing Operations:**
- ❌ CREATE workspace (create_workspace)
- ❌ READ workspace (read_workspace)
- ❌ UPDATE workspace (update_workspace, rename)
- ❌ DELETE workspace (delete_workspace)
- ❌ SWITCH workspace (change current workspace context)
- ❌ DEFAULT workspace (set default workspace)
- ❌ WORKSPACE settings (metadata, custom fields)
- ❌ WORKSPACE members (manage access)

**User Stories Needed:**
- "As a user, I can create a new workspace"
- "As a user, I can read workspace details"
- "As a user, I can update workspace name and settings"
- "As a user, I can delete a workspace"
- "As a user, I can switch between workspaces"
- "As a user, I can set a default workspace"

---

### 8. Search & Discovery

**Current Operations:**
- ✅ search_entity (basic full-text search)
- ✅ aggregate_entity (basic aggregation)

**Missing Operations:**
- ❌ SAVED searches (store search queries for reuse)
- ❌ RECENT searches (track recent search history)
- ❌ FACETED search (facets for filtering)
- ❌ SEARCH suggestions (autocomplete, recommendations)
- ❌ ADVANCED search (complex queries with operators)
- ❌ SEARCH analytics (track popular searches)
- ❌ SEARCH filters (by type, status, date range)
- ❌ SEARCH sorting (by relevance, date, name)

**User Stories Needed:**
- "As a user, I can save frequently-used searches"
- "As a user, I can view my recent searches"
- "As a user, I can use faceted search to drill down into results"
- "As a user, I can get search suggestions as I type"

---

### 9. Workflow

**Current Operations:**
- ✅ _setup_project_workflow
- ✅ _import_requirements_workflow
- ✅ _setup_test_matrix_workflow
- ✅ _bulk_status_update_workflow
- ✅ _organization_onboarding_workflow

**Missing Operations:**
- ❌ LIST workflows (list all configured workflows)
- ❌ CREATE workflow (define custom workflow)
- ❌ UPDATE workflow (modify existing workflow)
- ❌ DELETE workflow (remove workflow)
- ❌ ENABLE/DISABLE workflow (toggle workflow on/off)
- ❌ CLONE workflow (duplicate workflow configuration)
- ❌ WORKFLOW status (track execution)
- ❌ WORKFLOW templates (reusable workflow patterns)

**User Stories Needed:**
- "As an admin, I can create custom workflows"
- "As an admin, I can list all configured workflows"
- "As an admin, I can update workflow definitions"
- "As an admin, I can enable/disable workflows"
- "As an admin, I can clone workflows"

---

### 10. Data Management

**Current Operations:**
- ✅ Basic CREATE/READ/UPDATE/DELETE per entity

**Missing Operations:**
- ❌ BULK delete (delete multiple entities at once)
- ❌ BULK archive (archive multiple without losing data)
- ❌ DATA cleanup (remove orphaned records)
- ❌ DATA export (export to CSV/JSON)
- ❌ DATA import (bulk import from files)
- ❌ DATA merge (consolidate duplicate entities)
- ❌ DATA validation (check data integrity)
- ❌ AUDIT trail (track all data changes)

**User Stories Needed:**
- "As an admin, I can bulk delete old records"
- "As an admin, I can bulk archive records"
- "As an admin, I can export data to CSV/JSON"
- "As an admin, I can import bulk data from files"
- "As an admin, I can validate data integrity"

---

## Test Coverage Analysis

### Current Test Files

| File | Entity | Operations Tested | Gaps |
|------|--------|------------------|------|
| `test_entity_core.py` | All | CREATE, READ (basic), SEARCH | BULK, ARCHIVE, CLONE |
| `test_entity_organization.py` | Organization | CREATE, READ, UPDATE | LIST, ARCHIVE, INVITE |
| `test_entity_project.py` | Project | CREATE, READ, UPDATE | LIST, ARCHIVE, CLONE |
| `test_entity_document.py` | Document | CREATE, READ, UPDATE | LIST, VERSION, COPY |
| `test_entity_requirement.py` | Requirement | CREATE, READ, UPDATE | LIST, ARCHIVE, LINK, TRACE |
| `test_entity_test.py` | Test Case | CREATE, READ, UPDATE | LIST, CLONE, RUN |
| `test_relationship.py` | Relationship | LIST, UPDATE | CREATE, DELETE, BULK |
| `test_workspace.py` | Workspace | LIST | CREATE, READ, UPDATE, DELETE |
| `test_workflow.py` | Workflow | 5 workflows | LIST, CREATE, UPDATE, DELETE |

### Test Coverage by Operation

| Operation | Coverage | Status |
|-----------|----------|--------|
| CREATE | High | ✅ Most entities covered |
| READ | High | ✅ Most entities covered |
| UPDATE | High | ✅ Most entities covered |
| DELETE | Medium | ⚠️ Basic deletion, no archive |
| LIST | Medium | ⚠️ Basic listing, no filtering/pagination |
| ARCHIVE | Low | ❌ Not tested |
| BULK operations | Low | ❌ Not tested |
| VERSION history | None | ❌ Not tested |
| SEARCH | Medium | ⚠️ Basic search only |
| RELATIONSHIPS | Low | ⚠️ LIST/UPDATE only |

---

## Recommended Priority for Implementation

### Phase 1: Critical (Blocking Production Use)
1. **LIST operations** (all entities) - Essential for UI navigation
2. **Relationship CREATE/DELETE** - Core to data model
3. **Document version history** - Required for content management
4. **Search improvements** - Users need discovery

### Phase 2: Important (Production Quality)
5. **ARCHIVE operations** (all entities) - Data integrity
6. **BULK operations** - Efficiency for power users
7. **Workspace CRUD** - Full navigation support
8. **Requirement traceability** - Requirements management

### Phase 3: Nice-to-Have (Polish)
9. **Workflow management** - Advanced automation
10. **Data export/import** - Integration support
11. **Search analytics** - Insights
12. **Advanced permissions** - Fine-grained control

---

## Next Steps

1. **Create OpenSpec proposal** for Phase 1 operations
2. **Define user stories** with acceptance criteria
3. **Implement Phase 1** operations
4. **Add comprehensive tests** for each operation
5. **Validate consolidation** of story markers
6. **Run full test suite** to verify completeness

---

## Notes

- Current implementation prioritizes basic CRUD functionality
- Missing operations are necessary for production-ready system
- Test structure supports easy addition of new test files
- Each operation should follow existing patterns (parametrization, fixtures)
- Consolidation should happen across related entity types
