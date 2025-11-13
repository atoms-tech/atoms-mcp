# Test Coverage Improvement Plan - Rich Error Reporting & User Story Mapping

## Current Status Analysis

### ✅ What's Working
- **Test Infrastructure**: 100% refactored per AGENTS.md
- **Test Discovery**: 9 tests found in test_entity_organization.py
- **Test Execution**: Tests pass successfully (1/1 passed)
- **File Structure**: Canonical naming enforced across codebase

### ⚠️ What Needs Improvement
- **User Story Mapping**: Stories not automatically mapped to tests (shows "No matching tests found")
- **Error Reporting**: Need rich, descriptive error messages instead of generic failures
- **Test Coverage**: Some user stories lack explicit test implementations

---

## Phase 1: Rich Error Classification System

### Current Gap
Tests fail but don't explain **why** they fail or suggest fixes.

### Solution: Enhanced Error Reporter
```python
# New: tests/framework/error_reporter.py

class RichErrorReport:
    """Transforms raw test failures into descriptive, actionable error messages."""
    
    def __init__(self, test_name: str, error: Exception, context: Dict):
        self.test_name = test_name
        self.error = error
        self.context = context
    
    def classify_error(self) -> ErrorCategory:
        """Classify as INFRASTRUCTURE, PRODUCT, TEST_DATA, or ASSERTION."""
        # Analyze error type, message, stack trace
        # Return: ERROR_INFRA | ERROR_PRODUCT | ERROR_TEST_DATA | ERROR_ASSERTION
    
    def generate_report(self) -> str:
        """Generate rich, actionable error message."""
        return f"""
        ❌ TEST FAILURE: {self.test_name}
        
        Category: {self.error_category}
        Root Cause: {self.root_cause}
        
        What went wrong:
        {self.detailed_explanation}
        
        How to fix it:
        {self.fix_suggestions}
        
        Code snippets:
        {self.code_samples}
        """
```

### Error Categories with Natural Language Explanations

```
🔴 INFRASTRUCTURE ERROR (Setup/DB/API failure)
   "Database connection failed: Connection timeout after 30s"
   → Suggests: Check DB_URL, restart postgres, increase timeout
   
🟠 PRODUCT ERROR (Business logic bug)
   "Entity creation returned null ID"
   → Suggests: Check entity service, verify payload validation
   
🟡 TEST DATA ERROR (Invalid test fixtures)
   "Organization payload missing required 'name' field"
   → Suggests: Update test factory, check fixture definition
   
🟢 ASSERTION ERROR (Test expectation mismatch)
   "Expected 'Active' status, got 'Pending'"
   → Suggests: Review business logic, update test expectations
```

---

## Phase 2: User Story Test Mapper

### Current Gap
Framework shows "No matching tests found" for user stories, even when tests exist.

### Solution: Automatic Test Discovery with Markers
```python
# tests/framework/user_story_mapper.py

class UserStoryMapper:
    """Maps tests to user stories via markers and naming conventions."""
    
    @staticmethod
    def collect_story_mappings(test_items) -> Dict[str, List[TestItem]]:
        """Scan tests for story markers and infer from test names."""
        # Strategy 1: @pytest.mark.story("US-001")
        # Strategy 2: Test name contains "organization_create" → maps to org story
        # Strategy 3: Test class name TestOrganizationCRUD → maps to org stories
        
        return {
            "User can create an organization": [test_create_org_basic],
            "User can list organizations": [test_list_organizations],
            "User can update organization": [test_update_organization],
        }
    
    @staticmethod
    def print_story_coverage(mappings):
        """Pretty-print user story coverage with explanations."""
        for story, tests in mappings.items():
            if not tests:
                print(f"❌ {story} - No tests found (TODO: implement)")
            else:
                print(f"✅ {story} - {len(tests)} test(s): {[t.name for t in tests]}")
```

### Test Story Markers
```python
# Example: tests/unit/tools/test_entity_organization.py

@pytest.mark.story("Organization Management - User can create an organization")
@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_organization_basic(call_mcp):
    """Test basic organization creation.
    
    User Story: User can create an organization
    Acceptance Criteria:
    - POST /organizations creates new org
    - Returns org ID and timestamp
    - Name is required
    """
    ...
```

---

## Phase 3: Intelligent Assertion Messages

### Current Gap
Assertions fail silently without context.

### Solution: Rich Assertion Helpers
```python
# tests/framework/assertions.py

class SmartAssert:
    """Assertions with descriptive, context-aware error messages."""
    
    @staticmethod
    def entity_was_created(response, entity_type="organization"):
        """Assert entity creation with rich error message."""
        try:
            assert response.status_code == 200
            assert response.data.id is not None
            assert response.data.created_at is not None
        except AssertionError as e:
            # Instead of generic failure, provide:
            raise AssertionError(f"""
            ❌ Failed to create {entity_type}
            
            Expected: HTTP 200 with valid ID and timestamp
            Got: HTTP {response.status_code}
            Response: {response.data}
            
            Likely cause:
            - Database not accessible ({entity_type} insert failed)
            - Validation error ({list validation failures})
            - Service timeout (check service health)
            
            How to debug:
            1. Check {entity_type} service logs: `docker logs atoms_mcp`
            2. Verify database connection: `pytest --db-health-check`
            3. Run with verbose logging: `pytest -vv --log-level=DEBUG`
            """) from e
    
    @staticmethod
    def list_contains_items(items, expected_count, item_type="items"):
        """Assert list has expected count with diagnostics."""
        ...
```

---

## Phase 4: Test Status Dashboard with Remediation Guidance

### Current Gap
Dashboard shows "❌ No matching tests" but doesn't suggest action.

### Enhanced Dashboard Output
```
╔════════════════════════════════════════════════════════════════════╗
║              ATOMS MCP - TEST COVERAGE ANALYSIS                    ║
╠════════════════════════════════════════════════════════════════════╣
║ User Story                              │ Status  │ Tests  │ Action ║
╠──────────────────────────────────────────┼─────────┼────────┼────────╣
║ ✅ User can create organization         │ PASS    │ 1/1    │ None   ║
║ ❌ User can batch create entities       │ NO TESTS│ 0      │ TODO   ║
║    → Requires: test_entity_batch.py     │         │        │        ║
║    → Story: Batch create 100+ orgs      │         │        │        ║
║    → Effort: 2-3 hours (parametrized)   │         │        │        ║
║                                                                     ║
║ ⚠️  User can delete organization        │ FAIL    │ 1/1    │ DEBUG  ║
║    → Error: Soft delete not impl'd      │         │        │        ║
║    → Fix: Check tools/entity.py delete  │         │        │        ║
║    → Blocker: RLS constraint violation  │         │        │        ║
╠════════════════════════════════════════════════════════════════════╣
║ Overall: 1/48 stories pass (2%)                                    ║
║ Blocked: 4 stories (missing tests)                                 ║
║ Failing: 3 stories (implementation gaps)                           ║
╚════════════════════════════════════════════════════════════════════╝

REMEDIATION GUIDE
═══════════════════

Priority 1 (Blockers):
  ❌ User can batch create entities
     - Implement: tests/unit/tools/test_entity_batch.py
     - Copy from: test_entity_organization.py pattern
     - Est. time: 2 hours
  
  ❌ User can delete organization  
     - Root cause: tools/entity.py delete_entity() not implemented
     - Fix: See IMPLEMENTATION GUIDE below
     - Est. time: 1 hour

Priority 2 (High Value):
  ❌ User can search entities
     - Implement: tests/unit/tools/test_query_search.py
     - Depends on: vector embedding service working
     - Est. time: 3 hours

Priority 3 (Nice to Have):
  ❌ User can filter search results
     - Implement: test_query_filters.py
     - Depends on: search tests passing
     - Est. time: 1 hour

QUICK START
───────────
1. Copy test template: cp tests/framework/test_test_generation.py tests/unit/tools/test_entity_batch.py
2. Update class name: TestBatchOperations
3. Add story marker: @pytest.mark.story("User can batch create entities")
4. Run: pytest tests/unit/tools/test_entity_batch.py -v
```

---

## Phase 5: Implementation Roadmap

### Step 1: Add Rich Error Classification (2 hours)
- [ ] Create `tests/framework/error_reporter.py`
- [ ] Add error category detection (INFRA/PRODUCT/TEST_DATA/ASSERTION)
- [ ] Integrate into conftest.py pytest hooks
- [ ] Test with intentional failures

### Step 2: Implement User Story Mapper (1 hour)
- [ ] Create `tests/framework/user_story_mapper.py`
- [ ] Add @pytest.mark.story() markers to existing tests
- [ ] Auto-discover tests by naming convention
- [ ] Generate story-to-test mapping report

### Step 3: Add Smart Assertions (1.5 hours)
- [ ] Create `tests/framework/assertions.py`
- [ ] Implement for: entity_created, list_contains, etc.
- [ ] Update existing tests to use smart assertions
- [ ] Verify error messages are descriptive

### Step 4: Enhanced Dashboard (1 hour)
- [ ] Update `tests/conftest.py` reporting
- [ ] Add remediation guidance
- [ ] Show implementation templates
- [ ] Link to failing test code

### Step 5: Test Coverage Expansion (3+ hours per story)
- [ ] Implement batch create tests
- [ ] Implement search/filter tests
- [ ] Implement delete/cascade tests
- [ ] Implement auth/RLS tests

---

## Benefits of This Approach

### For Developers
✅ Clear error messages explain **what failed and why**  
✅ Automatic fix suggestions reduce debugging time  
✅ Rich assertions catch issues early  
✅ Test templates accelerate new test writing  

### For Product
✅ User story progress transparently tracked  
✅ Missing tests identified (gaps in requirements)  
✅ Implementation blockers highlighted  
✅ Time estimates for story completion  

### For CI/CD
✅ Failures fail **fast with actionable info**  
✅ No ambiguous "test failed" messages  
✅ Automatic categorization (infra vs product)  
✅ Remediation guidance in logs  

---

## Example: From Failure to Fix

### Current Behavior
```
FAILED tests/unit/tools/test_entity_organization.py::test_delete_organization
AssertionError: assert False
```
**(Unhelpful - no context)**

### New Behavior (Phase 5 Complete)
```
❌ TEST FAILURE: test_delete_organization

Category: PRODUCT ERROR (Business logic)
Root Cause: Delete endpoint not implemented

What went wrong:
  tools/entity.py delete_entity() raises NotImplementedError
  Expected: HTTP 200 with deleted entity details
  Got: HTTP 501 Not Implemented

How to fix it:
  1. Implement delete_entity() in tools/entity.py
  2. Add soft-delete check (is_deleted flag)
  3. Verify RLS policy allows deletion
  4. Update entity.py DELETE handler
  
Code snippet to add:
  async def delete_entity(self, entity_id: str) -> EntityResponse:
      """Delete entity by marking as deleted."""
      return await self.db.update(
          "entities",
          {"is_deleted": True, "deleted_at": now()},
          {"id": entity_id}
      )

Suggested test update:
  @pytest.mark.story("User can delete an organization")
  async def test_delete_organization_soft_delete(call_mcp):
      # Create org
      org = await call_mcp("entity_tool", {"action": "create", ...})
      
      # Delete org
      result = await call_mcp("entity_tool", {"action": "delete", "id": org.id})
      
      # Assert soft delete
      assert result.is_deleted == True
      assert result.deleted_at is not None
      
      # Assert not returned in list
      orgs = await call_mcp("entity_tool", {"action": "list"})
      assert org.id not in [o.id for o in orgs]

Time estimate: 30 minutes (implementation + test)
```
**(Highly actionable - clear next steps)**

---

## Integration with AGENTS.md

This improvement plan aligns with AGENTS.md requirements:

✅ **Aggressive Change Policy**: Remove generic "test failed" messages entirely  
✅ **Production-Grade Implementation**: Every error provides diagnostic info  
✅ **File Size Constraints**: Keep error_reporter.py <350 lines (modular)  
✅ **Comprehensive Testing**: Tests for the error reporter itself  

---

## Status & Next Steps

**Current**: Test infrastructure refactored, basic tests passing  
**Next**: Implement Phases 1-2 (error reporting + story mapping)  
**Then**: Expand test coverage for remaining user stories  

Estimated timeline: **1-2 weeks for full implementation**

---

**Document Created**: November 13, 2024  
**Status**: Ready for implementation  
**Priority**: High (dramatically improves developer experience)
