# User Story to Test Scenario Mapping

**Date:** November 14, 2025  
**Focus:** Complete mapping of all 48 user stories → MCP tools → test scenarios

## Overview

This document maps each of the 48 user stories from the epic summary to:
1. **Required MCP Tools** - Which tools must be called
2. **Operations** - Specific tool operations needed
3. **Test File** - Where the test will live
4. **Test Scenario** - What the test will validate
5. **Dependencies** - Other stories this depends on
6. **Estimated Tests** - How many test cases needed

---

## Epic 1: Organization Management (5 Stories)

### Story 1.1: Create Organization
**User Story:** User can create an organization

**Test Scenario:**
- Create org with minimal data (name only)
- Create org with full metadata (description, type, rate limits)
- Verify org ID is auto-generated and unique
- Verify created_by is set to authenticated user
- Verify created_at timestamp is set

**Required Tools:**
- `entity_tool` (operation: create, entity_type: organization)

**Test File:** `tests/e2e/test_organization_management.py`

**Operations:**
```
entity_tool(
  entity_type="organization",
  operation="create",
  data={"name": "Acme Corp", "description": "...", "type": "enterprise"}
)
```

**Assertions:**
- ✅ `result["success"] == True`
- ✅ `result["data"]["id"]` exists and is UUID
- ✅ `result["data"]["created_by"]` equals authenticated user
- ✅ `result["data"]["created_at"]` is ISO timestamp

**Dependencies:** None (foundation story)

**Estimated Tests:** 4
- Create with minimal data
- Create with full metadata
- Create with duplicate name (should allow, separate entity)
- Create with invalid data (empty name) → should fail

---

### Story 1.2: View Organization Details
**User Story:** User can view organization details and member count

**Test Scenario:**
- Read org by ID (UUID)
- Read org by fuzzy name match
- Verify all metadata fields returned (name, description, type, created_at, updated_at, member_count)
- Verify RLS enforces access control

**Required Tools:**
- `entity_tool` (operation: read, entity_type: organization)
- `relationship_tool` (implicit for member_count calculation)

**Test File:** `tests/e2e/test_organization_management.py`

**Operations:**
```
entity_tool(
  entity_type="organization",
  operation="read",
  entity_id="<org_id_or_fuzzy_name>"
)
```

**Assertions:**
- ✅ Returns full org metadata
- ✅ Includes member_count field
- ✅ Fuzzy name matching works (accepts "Acme" for "Acme Corp")
- ✅ RLS prevents access by non-members

**Dependencies:** Story 1.1 (requires existing org)

**Estimated Tests:** 4
- Read by ID
- Read by fuzzy name (70%+ match)
- Read with include_relations=True
- Read with RLS (non-member denied)

---

### Story 1.3: Update Organization Settings
**User Story:** User can update organization name, description, rate limits

**Test Scenario:**
- Update org name
- Update description
- Update rate limits
- Verify partial update (only changed fields)
- Verify updated_at timestamp changes
- Verify audit trail (who updated, when)

**Required Tools:**
- `entity_tool` (operation: update, entity_type: organization)

**Test File:** `tests/e2e/test_organization_management.py`

**Operations:**
```
entity_tool(
  entity_type="organization",
  entity_id="<org_id>",
  operation="update",
  data={"name": "New Name", "rate_limit_per_minute": 100}
)
```

**Assertions:**
- ✅ Only specified fields updated
- ✅ Unspecified fields unchanged
- ✅ updated_at changes
- ✅ RLS prevents non-owner update

**Dependencies:** Story 1.1 (requires existing org)

**Estimated Tests:** 4
- Update name only
- Update multiple fields
- Update with invalid data → fails
- RLS prevents non-owner update

---

### Story 1.4: Delete Organization (Soft Delete)
**User Story:** User can delete organization with cascade to projects/documents

**Test Scenario:**
- Soft delete org (deleted_at set)
- Cascade deletes projects but keeps documents (soft)
- Org not returned in list queries after delete
- Can restore org from soft delete
- Hard delete requires explicit flag + audit approval

**Required Tools:**
- `entity_tool` (operation: delete, entity_type: organization)

**Test File:** `tests/e2e/test_organization_management.py`

**Operations:**
```
entity_tool(
  entity_type="organization",
  entity_id="<org_id>",
  operation="delete",
  soft_delete=True  # Default
)
```

**Assertions:**
- ✅ deleted_at is set
- ✅ Org not returned in list()
- ✅ Can restore org (update deleted_at to null)
- ✅ Child projects soft-deleted
- ✅ Hard delete forbidden without explicit audit

**Dependencies:** Story 1.1 (requires existing org)

**Estimated Tests:** 4
- Soft delete org
- Soft-deleted org not in list
- Restore org from soft delete
- Cascade soft delete to children

---

### Story 1.5: List Organizations for User
**User Story:** User can list all organizations they belong to

**Test Scenario:**
- List orgs for authenticated user
- Pagination (limit, offset)
- Sorting (by name, by created_at, by member_count)
- Filter by type (team, enterprise, etc.)
- RLS enforcement (only user's orgs returned)

**Required Tools:**
- `entity_tool` (operation: list, entity_type: organization)

**Test File:** `tests/e2e/test_organization_management.py`

**Operations:**
```
entity_tool(
  entity_type="organization",
  operation="list",
  limit=50,
  offset=0,
  order_by="name",
  filters={"type": "enterprise"}
)
```

**Assertions:**
- ✅ Returns paginated list
- ✅ Sorting applied correctly
- ✅ Filters applied correctly
- ✅ Only user's orgs returned (RLS)
- ✅ Excludes soft-deleted orgs

**Dependencies:** Story 1.1 (requires existing orgs)

**Estimated Tests:** 5
- List all orgs
- Pagination (limit/offset)
- Sorting by name
- Sorting by date
- Filter by type

**Total for Epic 1:** 21 tests across 5 stories

---

## Epic 2: Project Management (5 Stories)

### Story 2.1: Create Project in Organization
**User Story:** User can create a project within an organization

**Test Scenario:**
- Create project with name, description
- Link to parent organization (implicit via workspace context)
- Auto-create default documents (README, Requirements, etc.)
- Set initial status (active, archived, etc.)
- Verify project inherits org's RLS context

**Required Tools:**
- `entity_tool` (create project)
- `workspace_tool` (set org context)
- `relationship_tool` (org→project membership)

**Test File:** `tests/e2e/test_project_management.py`

**Operations:**
```
workspace_tool(operation="set_context", context_type="organization", entity_id="<org_id>")
entity_tool(
  entity_type="project",
  operation="create",
  data={"name": "Vehicle Project", "description": "..."}
)
```

**Assertions:**
- ✅ Project created with parent org
- ✅ Default documents created (if applicable)
- ✅ Status set to active
- ✅ RLS inherited from org

**Dependencies:** Story 1.1 (requires org)

**Estimated Tests:** 4
- Create project in org
- Create with default documents
- Verify RLS inheritance
- Create with invalid org → fails

---

### Story 2.2: View Project Details & Hierarchy
**User Story:** User can view project details and its organization context

**Test Scenario:**
- Read project metadata (name, description, org, status)
- Get full hierarchy (org → project → documents)
- Count child entities (documents, requirements, test cases)
- List members assigned to project

**Required Tools:**
- `entity_tool` (read project, list documents)
- `workspace_tool` (get parent context)
- `relationship_tool` (list project members)

**Test File:** `tests/e2e/test_project_management.py`

**Operations:**
```
entity_tool(
  entity_type="project",
  entity_id="<project_id>",
  operation="read",
  include_relations=True
)
```

**Assertions:**
- ✅ Returns full project metadata
- ✅ Parent org included
- ✅ Child documents included (if include_relations=True)
- ✅ Member list included

**Dependencies:** Story 2.1 (requires project)

**Estimated Tests:** 4
- Read project by ID
- Read with include_relations
- Verify hierarchy (org context)
- List project members

---

### Story 2.3: Update Project Information
**User Story:** User can update project name, status, archived state

**Test Scenario:**
- Update project name
- Update status (active, archived, completed)
- Archive project (set archived_at timestamp)
- Unarchive project
- Partial updates only change specified fields

**Required Tools:**
- `entity_tool` (update project)

**Test File:** `tests/e2e/test_project_management.py`

**Operations:**
```
entity_tool(
  entity_type="project",
  entity_id="<project_id>",
  operation="update",
  data={"status": "archived"}
)
```

**Assertions:**
- ✅ Status updates correctly
- ✅ archived_at set when archived
- ✅ archived_at cleared when unarchived
- ✅ Partial updates work

**Dependencies:** Story 2.1 (requires project)

**Estimated Tests:** 4
- Update name
- Update status
- Archive/unarchive
- Partial update

---

### Story 2.4: Archive Project (Soft Delete)
**User Story:** User can soft-delete/archive a project

**Test Scenario:**
- Archive project (soft delete with archived_at)
- Project not returned in list() after archive
- Can restore archived project
- Child documents soft-deleted with project

**Required Tools:**
- `entity_tool` (delete with soft_delete=True)

**Test File:** `tests/e2e/test_project_management.py`

**Operations:**
```
entity_tool(
  entity_type="project",
  entity_id="<project_id>",
  operation="delete",
  soft_delete=True
)
```

**Assertions:**
- ✅ archived_at set
- ✅ Not in list() (unless include_archived=True)
- ✅ Can restore
- ✅ Children also soft-deleted

**Dependencies:** Story 2.1 (requires project)

**Estimated Tests:** 3
- Archive project
- Restore archived project
- Children cascade

---

### Story 2.5: List Projects in Organization
**User Story:** User can list projects in organization with pagination/filtering

**Test Scenario:**
- List projects by org (parent_type=organization, parent_id=org_id)
- Pagination (limit 50 per page)
- Sorting (by name, by created_at, by document_count)
- Filter by status (active, archived)
- Exclude soft-deleted unless include_archived=True

**Required Tools:**
- `entity_tool` (list with parent filtering)

**Test File:** `tests/e2e/test_project_management.py`

**Operations:**
```
entity_tool(
  entity_type="project",
  operation="list",
  parent_type="organization",
  parent_id="<org_id>",
  limit=50,
  offset=0,
  order_by="name"
)
```

**Assertions:**
- ✅ Returns org's projects only
- ✅ Pagination works
- ✅ Sorting applied
- ✅ Archived projects excluded

**Dependencies:** Story 2.1 (requires projects)

**Estimated Tests:** 4
- List by org
- Pagination
- Sorting
- Filter by status

**Total for Epic 2:** 19 tests across 5 stories

---

## Epic 3: Document Management (3 Stories)

### Story 3.1: Create Document
**User Story:** User can create document within project

**Required Tools:** `entity_tool` (create document), `workspace_tool` (context)

**Test File:** `tests/e2e/test_document_management.py`

**Dependencies:** Story 2.1 (requires project)

**Estimated Tests:** 4
- Create with minimal data
- Create with full metadata
- Auto-create outline/sections
- Invalid project → fails

---

### Story 3.2: View Document Content & Metadata
**User Story:** User can view document content with full metadata

**Required Tools:** `entity_tool` (read document), `relationship_tool` (related entities)

**Test File:** `tests/e2e/test_document_management.py`

**Dependencies:** Story 3.1

**Estimated Tests:** 3
- Read by ID
- Read with related requirements
- Version history retrieval

---

### Story 3.3: List Documents in Project
**User Story:** User can list documents with pagination/filtering

**Required Tools:** `entity_tool` (list with parent)

**Test File:** `tests/e2e/test_document_management.py`

**Dependencies:** Story 3.1

**Estimated Tests:** 3
- List by project
- Pagination
- Filter by status

**Total for Epic 3:** 10 tests across 3 stories

---

## Epic 4: Requirements Traceability (4 Stories)

### Story 4.1: Create Requirements
**User Story:** User can create requirements from templates

**Required Tools:** `entity_tool` (create requirement), `relationship_tool` (link to document)

**Test File:** `tests/e2e/test_requirements_traceability.py`

**Dependencies:** Story 3.1 (requires document)

**Estimated Tests:** 4
- Create with minimal data
- Create from template
- Link to document
- Link to project

---

### Story 4.2: Pull Requirements via Workflow
**User Story:** User can import requirements via workflow (batch create)

**Required Tools:** `entity_tool` (batch create), `workflow_execute` (execute workflow)

**Test File:** `tests/e2e/test_requirements_traceability.py`

**Dependencies:** Story 4.1

**Estimated Tests:** 3
- Batch import 10 requirements
- Batch import with validation
- Rollback on partial failure

---

### Story 4.3: Search Requirements
**User Story:** User can search requirements by text/tags/status

**Required Tools:** `data_query` (search), `entity_tool` (list with filters)

**Test File:** `tests/e2e/test_requirements_traceability.py`

**Dependencies:** Story 4.1

**Estimated Tests:** 4
- Keyword search
- Filter by status
- Filter by priority
- Hybrid search (keyword + filters)

---

### Story 4.4: Trace Requirement Links
**User Story:** User can trace links between requirement and test cases

**Required Tools:** `relationship_tool` (list relationships), `data_query` (graph traversal)

**Test File:** `tests/e2e/test_requirements_traceability.py`

**Dependencies:** Story 4.1, 5.1

**Estimated Tests:** 3
- List trace links
- Get full traceability chain
- Update trace link metadata

**Total for Epic 4:** 14 tests across 4 stories

---

## Epic 5: Test Case Management (2 Stories)

### Story 5.1: Create Test Cases
**User Story:** User can create test cases linked to requirements

**Required Tools:** `entity_tool` (create test_case), `relationship_tool` (link to requirement)

**Test File:** `tests/e2e/test_case_management.py`

**Dependencies:** Story 4.1 (requires requirement)

**Estimated Tests:** 3
- Create test case
- Link to requirement
- Set test status (pending, passed, failed)

---

### Story 5.2: View Test Results
**User Story:** User can view test results and coverage metrics

**Required Tools:** `data_query` (search test results), `entity_tool` (read)

**Test File:** `tests/e2e/test_case_management.py`

**Dependencies:** Story 5.1

**Estimated Tests:** 3
- View test result
- List results per requirement
- Calculate coverage percentage

**Total for Epic 5:** 6 tests across 2 stories

---

## Epic 6: Workspace Navigation (6 Stories)

### Story 6.1: Get Current Workspace Context
**User Story:** User can view current workspace context

**Required Tools:** `workspace_tool` (get_context)

**Test File:** `tests/e2e/test_workspace_navigation.py`

**Dependencies:** None

**Estimated Tests:** 2
- Get context at org level
- Get context at project level

---

### Story 6.2-6.5: Switch Workspace Context
**User Story:** User can switch to different workspace contexts

**Required Tools:** `workspace_tool` (set_context)

**Test File:** `tests/e2e/test_workspace_navigation.py`

**Dependencies:** Story 1.1, 2.1, 3.1

**Estimated Tests:** 8 (2 per context type)
- Switch to org context
- Switch to project context
- Switch to document context
- Switch with fuzzy name resolution

---

### Story 6.6: Get Workspace Defaults
**User Story:** User can get smart defaults for active workspace

**Required Tools:** `workspace_tool` (get_defaults)

**Test File:** `tests/e2e/test_workspace_navigation.py`

**Dependencies:** Story 6.1-6.5

**Estimated Tests:** 2
- Get defaults for org context
- Get defaults per context type

**Total for Epic 6:** 12 tests across 6 stories

---

## Epic 7: Entity Relationships (4 Stories)

### Story 7.1: Link Entities (All Relationship Types)
**User Story:** User can link entities together

**Required Tools:** `relationship_tool` (link)

**Test File:** `tests/e2e/test_entity_relationships.py`

**Dependencies:** Varies by relationship type

**Estimated Tests:** 8
- Link member (add to org/project)
- Link assignment (assign to user)
- Link trace_link (requirement → implementation)
- Link requirement_test (requirement → test)
- Link with metadata
- Invalid links → fail
- Circular link → fail
- Duplicate link → fail (or update)

---

### Story 7.2: Unlink Related Entities
**User Story:** User can remove entity relationships

**Required Tools:** `relationship_tool` (unlink)

**Test File:** `tests/e2e/test_entity_relationships.py`

**Dependencies:** Story 7.1

**Estimated Tests:** 4
- Unlink member
- Unlink assignment
- Unlink trace_link
- Unlink non-existent → fails gracefully

---

### Story 7.3: View Entity Relationships
**User Story:** User can view inbound/outbound relationships

**Required Tools:** `relationship_tool` (list)

**Test File:** `tests/e2e/test_entity_relationships.py`

**Dependencies:** Story 7.1

**Estimated Tests:** 4
- List inbound relationships
- List outbound relationships
- List filtered by type
- Pagination of relationships

---

### Story 7.4: Check Relationship Exists
**User Story:** User can check if entities are related

**Required Tools:** `relationship_tool` (check)

**Test File:** `tests/e2e/test_entity_relationships.py`

**Dependencies:** Story 7.1

**Estimated Tests:** 2
- Check exists (true case)
- Check exists (false case)

**Total for Epic 7:** 18 tests across 4 stories

---

## Epic 8: Search & Discovery (7 Stories)

### Story 8.1-8.5: Search Operations
**User Story:** User can search across all entity types with various methods

**Required Tools:** `data_query` (keyword, semantic, hybrid, filter, aggregate)

**Test File:** `tests/e2e/test_search_and_discovery.py`

**Dependencies:** Requires entities (story 1.1+)

**Estimated Tests:** 20
- Keyword search (5 tests: basic, partial match, fuzzy, case-insensitive, exclude deleted)
- Semantic search (3 tests: embedding-based, similar threshold, performance)
- Hybrid search (3 tests: combined keyword+semantic, weight tuning)
- Filtering (4 tests: by type, by owner, by status, by date range)
- Aggregates (5 tests: count by type, count by owner, count by status, total count, group by)

---

### Story 8.6: Find Similar Entities
**User Story:** User can find similar entities by embedding distance

**Required Tools:** `data_query` (semantic search)

**Test File:** `tests/e2e/test_search_and_discovery.py`

**Dependencies:** Story 8.3

**Estimated Tests:** 2
- Find similar by embedding
- Threshold tuning

---

### Story 8.7: Advanced Search Operators
**User Story:** User can use AND/OR/NOT operators in searches

**Required Tools:** `data_query` (search with operators)

**Test File:** `tests/e2e/test_search_and_discovery.py`

**Dependencies:** Story 8.1

**Estimated Tests:** 3
- Search with AND
- Search with OR
- Search with NOT

**Total for Epic 8:** 25 tests across 7 stories

---

## Epic 9: Workflow Automation (5 Stories)

### Story 9.1: Run Workflows with Transactions ✅ (DONE)
**Status:** Already implemented and passing

---

### Story 9.2: Set Up New Project Workflow
**User Story:** User can execute workflow to scaffold new project

**Required Tools:** `workflow_execute`, `entity_tool` (batch create)

**Test File:** `tests/e2e/test_workflow_automation.py`

**Dependencies:** Story 1.1, 2.1, 3.1

**Estimated Tests:** 3
- Execute project scaffolding workflow
- Verify all default entities created
- Workflow rollback on error

---

### Story 9.3: Import Requirements via Workflow
**User Story:** User can execute batch import workflow

**Required Tools:** `workflow_execute`, `entity_tool` (batch create)

**Test File:** `tests/e2e/test_workflow_automation.py`

**Dependencies:** Story 4.2

**Estimated Tests:** 3
- Execute import workflow
- Verify all requirements created
- Error handling

---

### Story 9.4: Bulk Update Status Workflow
**User Story:** User can bulk update entity statuses with transaction

**Required Tools:** `workflow_execute`, `entity_tool` (batch update)

**Test File:** `tests/e2e/test_workflow_automation.py`

**Dependencies:** Story 1.1+

**Estimated Tests:** 3
- Bulk update 100 entities
- Transaction rollback on error
- Partial failure handling

---

### Story 9.5: Organization Onboarding Workflow
**User Story:** User can execute multi-step organization setup workflow

**Required Tools:** `workflow_execute`, all entity/relationship tools

**Test File:** `tests/e2e/test_workflow_automation.py`

**Dependencies:** All org/project/doc stories

**Estimated Tests:** 3
- Execute complete onboarding
- Verify all steps executed
- Error recovery per step

**Total for Epic 9:** 13 tests across 5 stories (1 done, 4 to do)

---

## Epic 10: Data Management (3 Stories)

### Story 10.1: Batch Create Entities
**User Story:** User can create 1000+ entities in single batch

**Required Tools:** `entity_tool` (batch create), `workflow_execute` (transaction)

**Test File:** `tests/e2e/test_data_management.py`

**Dependencies:** Story 1.1

**Estimated Tests:** 3
- Create 100 entities
- Create 1000 entities
- Performance baseline (<30s)

---

### Story 10.2: Paginate Large Lists
**User Story:** User can paginate through large result sets

**Required Tools:** `entity_tool` (list with pagination)

**Test File:** `tests/e2e/test_data_management.py`

**Dependencies:** Story 10.1

**Estimated Tests:** 4
- Paginate with limit 50
- Paginate with limit 1000
- Cursor-based pagination (if supported)
- Total count accuracy

---

### Story 10.3: Sort Query Results
**User Story:** User can sort results by various fields

**Required Tools:** `entity_tool` (list with order_by)

**Test File:** `tests/e2e/test_data_management.py`

**Dependencies:** Story 10.1

**Estimated Tests:** 5
- Sort by name (ascending/descending)
- Sort by created_at
- Sort by custom fields
- Multi-field sort (if supported)
- Sort with pagination

**Total for Epic 10:** 12 tests across 3 stories

---

## Epic 11: Security & Access (4 Stories)

### Story 11.1: Authenticate via AuthKit OAuth
**User Story:** User can log in with AuthKit OAuth flow

**Required Tools:** Auth middleware, `workspace_tool` (get_context to verify session)

**Test File:** `tests/integration/test_auth_integration.py`

**Dependencies:** AuthKit configured (deployment requirement)

**Estimated Tests:** 3
- OAuth sign-in flow
- Token generation
- Invalid credentials → fail

---

### Story 11.2: Maintain Active Session
**User Story:** User can maintain active session with token refresh

**Required Tools:** Auth middleware, token refresh logic

**Test File:** `tests/integration/test_auth_integration.py`

**Dependencies:** Story 11.1

**Estimated Tests:** 3
- Token refresh before expiration
- Extended session duration
- Token expiration → re-auth required

---

### Story 11.3: Log Out Securely
**User Story:** User can log out with token revocation

**Required Tools:** Auth middleware, logout endpoint

**Test File:** `tests/integration/test_auth_integration.py`

**Dependencies:** Story 11.2

**Estimated Tests:** 2
- Logout revokes token
- Revoked token denied

---

### Story 11.4: Row-Level Security Enforcement
**User Story:** User data protected by RLS (can't access other users' data)

**Required Tools:** Database RLS policies, `entity_tool` (read with RLS checks)

**Test File:** `tests/integration/test_auth_integration.py`

**Dependencies:** Story 1.1

**Estimated Tests:** 4
- User A can't read User B's org
- User A can't modify User B's project
- Cross-user relationship prevented
- RLS policy enforcement verified

**Total for Epic 11:** 12 tests across 4 stories

---

## Summary Statistics

| Epic | Stories | Tests | Status |
|------|---------|-------|--------|
| 1. Organization Management | 5 | 21 | ⏳ Not started |
| 2. Project Management | 5 | 19 | ⏳ Not started |
| 3. Document Management | 3 | 10 | ⏳ Not started |
| 4. Requirements Traceability | 4 | 14 | ⏳ Not started |
| 5. Test Case Management | 2 | 6 | ⏳ Not started |
| 6. Workspace Navigation | 6 | 12 | ⏳ Not started |
| 7. Entity Relationships | 4 | 18 | ⏳ Not started |
| 8. Search & Discovery | 7 | 25 | ⏳ Not started |
| 9. Workflow Automation | 5 | 13 | ✅ 1/5 done |
| 10. Data Management | 3 | 12 | ⏳ Not started |
| 11. Security & Access | 4 | 12 | ⏳ Not started |
| **TOTAL** | **48** | **172** | **1/48 done (2%)** |

## Test File Organization (Canonical)

```
tests/
  e2e/
    test_organization_management.py      (21 tests)
    test_project_management.py           (19 tests)
    test_document_management.py          (10 tests)
    test_requirements_traceability.py    (14 tests)
    test_test_case_management.py         (6 tests)
    test_workspace_navigation.py         (12 tests)
    test_entity_relationships.py         (18 tests)
    test_search_and_discovery.py         (25 tests)
    test_workflow_automation.py          (13 tests)
    test_data_management.py              (12 tests)
  integration/
    test_auth_integration.py             (12 tests)
    
  Total: 172 tests across 11 canonical files
```

---

**Last Updated:** 2025-11-14 (Specification Phase)
