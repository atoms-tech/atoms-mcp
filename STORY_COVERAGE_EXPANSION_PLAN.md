# Story Coverage Expansion Plan - Path to 100%

## Current Status
- **Implemented**: 27/48 stories (56%)
- **Missing**: 21/48 stories (44%)
- **Target**: 48/48 stories (100%)

## Missing Stories by Category

### Organization & Workspace Management (5 stories)
1. **User can onboard new organization** 
   - Location: test_organization_crud.py
   - Type: Organization creation with full setup
   - Status: Needs implementation

2. **User can list all available workspaces**
   - Location: test_workspace_navigation.py
   - Type: Workspace listing/discovery
   - Status: Needs implementation

3. **User can switch to organization workspace**
   - Location: test_workspace_navigation.py
   - Type: Workspace context switching
   - Status: Needs implementation

4. **User can switch to project workspace**
   - Location: test_workspace_navigation.py
   - Type: Workspace context switching
   - Status: Needs implementation

5. **User can switch to document workspace**
   - Location: test_workspace_navigation.py
   - Type: Workspace context switching
   - Status: Needs implementation

6. **User can get workspace defaults**
   - Location: test_workspace_navigation.py
   - Type: Workspace configuration retrieval
   - Status: Needs implementation

### Entity Relationships (4 stories)
7. **User can link entities together**
   - Location: test_entity_relationships.py
   - Type: Entity linking operation
   - Status: Needs implementation

8. **User can unlink related entities**
   - Location: test_entity_relationships.py
   - Type: Entity unlinking operation
   - Status: Needs implementation

9. **User can view entity relationships**
   - Location: test_entity_relationships.py
   - Type: Relationship viewing
   - Status: Needs implementation

### Search & Discovery (3 stories)
10. **User can perform keyword search**
    - Location: test_search_and_discovery.py
    - Type: Search functionality
    - Status: Needs implementation

11. **User can find similar entities**
    - Location: test_search_and_discovery.py
    - Type: Similarity search
    - Status: Needs implementation

12. **User can get entity count aggregates**
    - Location: test_search_and_discovery.py
    - Type: Search analytics
    - Status: Needs implementation

### Data Management (2 stories)
13. **User can paginate through large lists**
    - Location: test_data_management.py
    - Type: Pagination functionality
    - Status: Needs implementation

14. **User can pull requirements from system**
    - Location: test_requirements_traceability.py
    - Type: Requirements retrieval
    - Status: Needs implementation

### Workflow & Testing (4 stories)
15. **User can set up new project workflow**
    - Location: test_workflow_automation.py
    - Type: Workflow creation
    - Status: Needs implementation

16. **User can import requirements via workflow**
    - Location: test_workflow_automation.py
    - Type: Workflow execution with imports
    - Status: Needs implementation

17. **User can bulk update statuses**
    - Location: test_workflow_automation.py
    - Type: Bulk operations
    - Status: Needs implementation

18. **User can run workflows with transactions**
    - Location: test_workflow_automation.py
    - Type: Transactional workflows
    - Status: Needs implementation (partial - some tests exist)

### Test Case Management (1 story)
19. **User can view test results**
    - Location: test_document_management.py or new file
    - Type: Test result viewing
    - Status: Needs implementation

20. **User can create test cases**
    - Location: test_document_management.py or new file
    - Type: Test case creation
    - Status: Needs implementation

### Security & Access (1 story)
21. **User data is protected by row-level security**
    - Location: test_security.py (new file)
    - Type: Security verification
    - Status: Needs implementation

---

## Implementation Strategy

### Phase 1: Quick Wins (High Confidence)
These stories have obvious test implementations in existing test files:

1. **test_workspace_navigation.py** (add 6 story markers to existing tests)
   - `User can list all available workspaces`
   - `User can switch to organization workspace`
   - `User can switch to project workspace`
   - `User can switch to document workspace`
   - `User can get workspace defaults`
   - `User can view current workspace context` (already has marker)

2. **test_entity_relationships.py** (add 3 story markers)
   - `User can link entities together`
   - `User can unlink related entities`
   - `User can view entity relationships`

3. **test_search_and_discovery.py** (add 3 story markers)
   - `User can perform keyword search`
   - `User can find similar entities`
   - `User can get entity count aggregates`

4. **test_data_management.py** (add 1 story marker)
   - `User can paginate through large lists`

**Expected Result**: +13 stories = 40/48 (83%)

### Phase 2: Medium Effort (Existing Tests, Need Markers)
These tests likely exist but need story markers added:

1. **test_organization_crud.py** (add 1 marker)
   - `User can onboard new organization` (might be in create tests)

2. **test_requirements_traceability.py** (add 1 marker)
   - `User can pull requirements from system`

3. **test_workflow_automation.py** (add 4 markers)
   - `User can set up new project workflow`
   - `User can import requirements via workflow`
   - `User can bulk update statuses`
   - `User can run workflows with transactions` (already has partial coverage)

**Expected Result**: +6 stories = 46/48 (96%)

### Phase 3: Custom Test Implementation (New Tests)
These require writing new test cases:

1. **test_document_management.py** (add 2 story markers or new tests)
   - `User can view test results`
   - `User can create test cases`

2. **New: test_security.py** (1 story marker)
   - `User data is protected by row-level security`

**Expected Result**: +3 stories = 48/48 (100%)

---

## Action Items

### TODO: Add Story Markers to Existing Tests

**test_workspace_navigation.py** - Add 5 markers:
```python
@pytest.mark.story("User can list all available workspaces")
async def test_list_workspaces(self, mcp_client):
    ...

@pytest.mark.story("User can switch to organization workspace")
async def test_switch_organization(self, mcp_client):
    ...

@pytest.mark.story("User can switch to project workspace")
async def test_switch_project(self, mcp_client):
    ...

@pytest.mark.story("User can switch to document workspace")
async def test_switch_document(self, mcp_client):
    ...

@pytest.mark.story("User can get workspace defaults")
async def test_get_defaults(self, mcp_client):
    ...
```

**test_entity_relationships.py** - Add 3 markers:
```python
@pytest.mark.story("User can link entities together")
@pytest.mark.story("User can unlink related entities")
@pytest.mark.story("User can view entity relationships")
```

**test_search_and_discovery.py** - Add 3 markers:
```python
@pytest.mark.story("User can perform keyword search")
@pytest.mark.story("User can find similar entities")
@pytest.mark.story("User can get entity count aggregates")
```

**test_data_management.py** - Add 1 marker:
```python
@pytest.mark.story("User can paginate through large lists")
```

**test_organization_crud.py** - Add 1 marker:
```python
@pytest.mark.story("User can onboard new organization")
```

**test_requirements_traceability.py** - Add 1 marker:
```python
@pytest.mark.story("User can pull requirements from system")
```

**test_workflow_automation.py** - Add 4 markers:
```python
@pytest.mark.story("User can set up new project workflow")
@pytest.mark.story("User can import requirements via workflow")
@pytest.mark.story("User can bulk update statuses")
@pytest.mark.story("User can run workflows with transactions")
```

### TODO: Implement Missing Tests

**test_document_management.py** - Add 2 test methods with story markers:
```python
@pytest.mark.story("User can view test results")
async def test_view_test_results(self, mcp_client):
    ...

@pytest.mark.story("User can create test cases")
async def test_create_test_cases(self, mcp_client):
    ...
```

**New: tests/e2e/test_security.py** - Create file with security test:
```python
@pytest.mark.story("User data is protected by row-level security")
async def test_row_level_security(self, mcp_client):
    ...
```

---

## Expected Timeline

- **Phase 1** (Quick Wins): 15 minutes - Add markers to existing tests
- **Phase 2** (Medium Effort): 30 minutes - Find and mark existing tests
- **Phase 3** (Custom Tests): 1-2 hours - Write new test cases

**Total**: ~2-3 hours to reach 100% story coverage

---

## Success Criteria

- [ ] All 48 user stories have at least one test
- [ ] All tests have `@pytest.mark.story("...")` marker
- [ ] All story markers match `UserStoryMapper.EPICS` exactly
- [ ] Epic View report shows 48/48 stories complete
- [ ] All tests pass (or expected failures documented)

---

## Benefits of 100% Coverage

1. **Complete Test Suite** - Every user story has validation
2. **Better Reporting** - Epic View shows full picture
3. **Documentation** - Tests serve as behavior specification
4. **Quality Assurance** - No gaps in requirement coverage
5. **Stakeholder Confidence** - 100% traceability to requirements

