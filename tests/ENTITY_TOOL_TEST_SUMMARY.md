# Entity Tool Comprehensive Testing - Summary & Matrix

## Quick Start

```bash
# 1. Start the MCP server
python -m uvicorn server:app --port 8000

# 2. Run comprehensive tests
./tests/run_comprehensive_tests.sh

# 3. View the test matrix report
cat tests/entity_tool_test_matrix_report.md
```

## Test Coverage Matrix Template

The comprehensive test suite validates the following operations across all entity types:

### Entity Types × Operations Matrix

| Entity Type | CREATE | READ | READ+Relations | UPDATE | DELETE (Soft) | DELETE (Hard) | SEARCH | LIST | BATCH |
|-------------|--------|------|----------------|--------|---------------|---------------|--------|------|-------|
| organization| ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ |
| project     | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| document    | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ |
| requirement | ⚠️ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ |
| test        | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ |
| property    | 🚧 | 🚧 | 🚧 | 🚧 | 🚧 | 🚧 | 🚧 | 🚧 | 🚧 |

**Legend:**
- ✅ **PASS** - Test passes successfully
- ❌ **FAIL** - Test fails (expected or known issue)
- ⚠️ **PARTIAL** - Test passes with caveats or edge cases
- 🚧 **NOT TESTED** - Not yet implemented in test suite

## Test Categories

### 1. CREATE Operations (TestEntityCreate)
Tests entity creation with various scenarios:

- ✅ **Organization Creation**
  - Explicit field values
  - Auto-generated slugs
  - Type validation (team, personal)

- ✅ **Project Creation**
  - With "auto" context (uses workspace)
  - With explicit organization_id
  - Auto-generated slugs

- ✅ **Document Creation**
  - Requires valid project_id
  - Auto-generated slugs
  - Description and metadata

- ⚠️ **Requirement Creation**
  - Requires valid block_id (FK constraint)
  - Auto-generated external_id
  - Status and priority defaults

- ✅ **Test Entity Creation**
  - Requires valid project_id
  - Status defaults to "pending"
  - Priority validation

### 2. READ Operations (TestEntityRead)
Tests entity retrieval with different options:

- ✅ **Basic Read** (`include_relations=False`)
  - Returns entity data only
  - No additional queries
  - Fast retrieval

- ✅ **Read with Relations** (`include_relations=True`)
  - Organization: member_count, recent_projects
  - Project: document_count, members
  - Document: requirement_count, blocks

- ✅ **Error Cases**
  - Non-existent entity IDs
  - Invalid entity types
  - Permission violations

### 3. UPDATE Operations (TestEntityUpdate)
Tests entity modification:

- ✅ **Field Updates**
  - Single field updates
  - Multiple field updates
  - Auto-updated timestamps

- ✅ **User Tracking**
  - updated_by field set automatically
  - updated_at timestamp refreshed

- ✅ **Error Cases**
  - Invalid entity IDs
  - Non-existent entities
  - Validation failures

### 4. DELETE Operations (TestEntityDelete)
Tests entity removal:

- ✅ **Soft Delete** (default)
  - Sets is_deleted=true
  - Sets deleted_at timestamp
  - Entity still queryable with filters

- ⚠️ **Hard Delete**
  - Permanent removal from database
  - May fail due to FK constraints
  - Tested on projects only

### 5. SEARCH Operations (TestEntitySearch)
Tests querying and filtering:

- ✅ **Text Search**
  - Search by name (ilike pattern)
  - Case-insensitive matching

- ✅ **Custom Filters**
  - type, status, priority
  - is_deleted filtering
  - Multiple filter combinations

- ✅ **Ordering**
  - created_at:asc/desc
  - name:asc/desc
  - Custom field ordering

- ✅ **Pagination**
  - limit parameter
  - offset parameter
  - No overlap validation

### 6. LIST Operations (TestEntityList)
Tests hierarchical listing:

- ✅ **Parent Filtering**
  - Projects by organization
  - Documents by project
  - Requirements by document

- ✅ **Pagination**
  - limit parameter
  - offset parameter (via search)

- ✅ **Default Filters**
  - Excludes deleted items
  - Includes active items only

### 7. BATCH Operations (TestBatchOperations)
Tests bulk operations:

- ✅ **Batch Create**
  - Organizations (3+ entities)
  - Projects (3+ entities)
  - Single request, multiple results

- ⚠️ **Performance**
  - Sequential processing (not parallel)
  - Higher latency than individual ops

### 8. Format Types (TestFormatTypes)
Tests response formatting:

- ✅ **Detailed Format** (default)
  ```json
  {
    "success": true,
    "data": {...},
    "count": 1,
    "user_id": "...",
    "timestamp": "..."
  }
  ```

- ✅ **Summary Format**
  ```json
  {
    "count": 5,
    "items": [...],
    "truncated": true
  }
  ```

- ✅ **Raw Format**
  ```json
  {
    "data": {...}
  }
  ```

### 9. Error Cases (TestErrorCases)
Tests validation and error handling:

- ✅ **Missing Required Fields**
  - Validates required field presence
  - Returns clear error messages

- ✅ **Invalid Entity IDs**
  - Handles non-existent IDs gracefully
  - Returns "Entity not found" error

- ✅ **Invalid Entity Types**
  - Rejects unknown entity types
  - Returns "Unknown entity type" error

- ⚠️ **Auto Context Failures**
  - Fails when no workspace set
  - Requires workspace context setup

## Performance Benchmarks

### Expected Operation Times

| Operation | Min (ms) | Avg (ms) | Max (ms) | P95 (ms) | P99 (ms) |
|-----------|----------|----------|----------|----------|----------|
| CREATE    | 80       | 150      | 400      | 300      | 350      |
| READ      | 40       | 100      | 250      | 200      | 230      |
| READ+Rel  | 100      | 200      | 500      | 400      | 450      |
| UPDATE    | 80       | 180      | 350      | 300      | 330      |
| DELETE    | 80       | 150      | 300      | 250      | 280      |
| SEARCH    | 100      | 250      | 600      | 500      | 550      |
| LIST      | 80       | 200      | 400      | 350      | 380      |
| BATCH (3) | 250      | 500      | 1200     | 1000     | 1100     |

### Performance Factors

1. **Embedding Generation** (CREATE only)
   - Runs asynchronously
   - Adds 50-150ms overhead
   - Non-blocking

2. **Relationship Loading** (READ+Relations)
   - Additional DB queries
   - 2-5x slower than basic read
   - Caching recommended

3. **Search Complexity**
   - Text search: slower than filters
   - Multiple filters: additive overhead
   - Pagination: minimal overhead

4. **Batch Operations**
   - Sequential processing
   - ~150ms per entity
   - Not parallelized

## Known Issues & Edge Cases

### 1. Foreign Key Constraints

**Issue**: Requirements need valid `block_id` which may not exist yet

```python
# This will fail with FK constraint error
{
    "entity_type": "requirement",
    "data": {
        "document_id": "...",
        "block_id": str(uuid.uuid4()),  # Non-existent block
        ...
    }
}
```

**Solution**: Create blocks first or use transaction-based workflows

### 2. Auto Context Resolution

**Issue**: Using "auto" requires active workspace context

```python
# Fails if no workspace set
{
    "entity_type": "project",
    "data": {
        "organization_id": "auto",  # Needs workspace context
        ...
    }
}
```

**Solution**: Set workspace context first:
```python
await call_mcp("workspace_tool", {
    "operation": "set_context",
    "context_type": "organization",
    "entity_id": org_id
})
```

### 3. Hard Delete Constraints

**Issue**: Hard delete fails if entity has dependent records

```python
# Fails if organization has projects
{
    "operation": "delete",
    "entity_type": "organization",
    "entity_id": org_id,
    "soft_delete": False  # Will fail if FK constraints exist
}
```

**Solution**: Use soft delete or cascade delete dependencies first

### 4. RLS Policy Violations

**Issue**: User must have proper permissions for entity access

```python
# Fails if user doesn't have access
{
    "operation": "read",
    "entity_type": "project",
    "entity_id": other_users_project
}
```

**Solution**: Ensure user is member of organization/project

### 5. Embedding Generation Delays

**Issue**: Async embedding generation can cause eventual consistency issues

**Impact**:
- Immediate read may not have embeddings
- Search by semantic similarity may miss new entities

**Solution**:
- Wait 100-200ms before semantic search
- Use progressive embedding backfill

## Test Execution Guide

### Prerequisites Checklist

- [ ] MCP server running on port 8000
- [ ] Supabase credentials configured
- [ ] Test user credentials available
- [ ] pytest and dependencies installed
- [ ] Environment variables set

### Running Tests

#### 1. Full Test Suite
```bash
./tests/run_comprehensive_tests.sh
```

#### 2. Specific Entity Type
```bash
pytest tests/test_entity_tool_comprehensive.py -k "organization" -v
```

#### 3. Specific Operation
```bash
pytest tests/test_entity_tool_comprehensive.py::TestEntityCreate -v
```

#### 4. With Coverage
```bash
pytest tests/test_entity_tool_comprehensive.py \
    --cov=tools.entity \
    --cov-report=html \
    --cov-report=term-missing
```

#### 5. Performance Profiling
```bash
pytest tests/test_entity_tool_comprehensive.py \
    --profile \
    --profile-svg
```

### Interpreting Results

#### Success Output
```
tests/test_entity_tool_comprehensive.py::TestEntityCreate::test_create_organization PASSED
✅ PASS: organization.create (145.23ms)
```

#### Failure Output
```
tests/test_entity_tool_comprehensive.py::TestEntityCreate::test_create_requirement FAILED
❌ FAIL: requirement.create (234.56ms)
Error: foreign key constraint "requirements_block_id_fkey"
```

#### Expected Failures
Some tests document known issues and may fail:
- requirement.create - FK constraint (expected)
- organization.hard_delete - FK constraint (expected)

## Test Matrix Report Example

After running tests, the generated report will look like:

```markdown
# Entity Tool Comprehensive Test Matrix Report
Generated: 2025-10-02T15:30:00Z

## Summary
- Total Tests: 45
- Passed: 38
- Failed: 7
- Pass Rate: 84.4%

## Test Matrix

| Entity Type | create | read | update | delete | search | list | batch |
|-------------|--------|------|--------|--------|--------|------|-------|
| organization| ✅ PASS| ✅ PASS| ✅ PASS| ✅ PASS| ✅ PASS| ✅ PASS| ✅ PASS|
| project     | ✅ PASS| ✅ PASS| ✅ PASS| ✅ PASS| ✅ PASS| ✅ PASS| ✅ PASS|
| document    | ✅ PASS| ✅ PASS| ✅ PASS| ✅ PASS| ✅ PASS| ✅ PASS| ⏭️ N/A |
| requirement | ❌ FAIL| ✅ PASS| ✅ PASS| ✅ PASS| ✅ PASS| ✅ PASS| ⏭️ N/A |
| test        | ✅ PASS| ✅ PASS| ✅ PASS| ✅ PASS| ✅ PASS| ✅ PASS| ⏭️ N/A |

## Performance Analysis

### organization
- **create**: 145.32ms
- **read**: 89.45ms
- **update**: 167.23ms
- **delete**: 134.56ms
- **search**: 234.67ms
- **list**: 198.34ms
- **batch**: 567.89ms

## Issues Discovered

- **requirement.create**: Requires valid block_id - FK constraint expected
- **organization.hard_delete**: Cannot hard delete with existing projects
```

## Integration with CI/CD

### GitHub Actions
```yaml
- name: Run Comprehensive Entity Tool Tests
  run: |
    python -m uvicorn server:app --port 8000 &
    sleep 5
    ./tests/run_comprehensive_tests.sh
  env:
    NEXT_PUBLIC_SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
    NEXT_PUBLIC_SUPABASE_ANON_KEY: ${{ secrets.SUPABASE_ANON_KEY }}

- name: Upload Test Reports
  uses: actions/upload-artifact@v3
  if: always()
  with:
    name: entity-tool-test-reports
    path: |
      tests/entity_tool_test_matrix_report.md
      tests/entity_tool_test_report.html
      tests/entity_tool_test_output.log
```

### Pre-commit Hook
```bash
#!/bin/bash
# .git/hooks/pre-commit

echo "Running entity tool tests..."
if ! ./tests/run_comprehensive_tests.sh; then
    echo "Entity tool tests failed!"
    exit 1
fi
```

## Maintenance & Updates

### Adding New Entity Types

1. Update `EntityFactory` in `test_utils.py`
2. Add test class in `test_entity_tool_comprehensive.py`
3. Update test matrix template
4. Run tests and verify coverage

### Adding New Operations

1. Add test method to appropriate test class
2. Record results using `test_results.record()`
3. Update matrix generation
4. Document in this summary

### Performance Regression Detection

Monitor these metrics over time:
- Average operation duration
- 95th percentile latency
- Batch operation efficiency
- Search query performance

Set alerts for:
- >20% increase in average duration
- >50% increase in P95 latency
- >100% increase in error rate

## Troubleshooting

### Common Issues

1. **Server Not Running**
   ```
   Solution: python -m uvicorn server:app --port 8000
   ```

2. **Authentication Failed**
   ```
   Solution: Check ATOMS_TEST_EMAIL and ATOMS_TEST_PASSWORD
   ```

3. **FK Constraint Errors**
   ```
   Solution: These are expected for requirements without blocks
   ```

4. **Timeout Errors**
   ```
   Solution: Increase httpx timeout in conftest.py
   ```

5. **Rate Limiting**
   ```
   Solution: Add delays between tests or use session-scoped auth
   ```

## Next Steps

1. **Expand Coverage**
   - Add property entity tests
   - Add trace_link tests
   - Add audit_log tests

2. **Performance Testing**
   - Load testing with concurrent requests
   - Stress testing with large datasets
   - Endurance testing over time

3. **Security Testing**
   - Permission boundary testing
   - SQL injection attempts
   - XSS validation

4. **Chaos Engineering**
   - Database connection failures
   - Network timeouts
   - Partial failures

## Resources

- **Test Suite**: `/tests/test_entity_tool_comprehensive.py`
- **Test Utils**: `/tests/test_utils.py`
- **Test Runner**: `/tests/run_comprehensive_tests.sh`
- **README**: `/tests/COMPREHENSIVE_TESTS_README.md`
- **Entity Tool**: `/tools/entity.py`
- **Base Tool**: `/tools/base.py`
