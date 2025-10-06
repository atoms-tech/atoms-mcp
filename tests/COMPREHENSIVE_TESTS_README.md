# Entity Tool Comprehensive Test Suite

## Overview

This comprehensive test suite validates the `entity_tool` MCP across all supported entity types and operations. It provides detailed coverage analysis, performance metrics, and identifies edge cases and issues.

## Entity Types Covered

- **organization** - Team/company organizations
- **project** - Projects within organizations
- **document** - Documents within projects
- **requirement** - Requirements within documents
- **test** - Test cases within projects
- **property** - Custom properties (planned)

## Operations Tested

### 1. CREATE Operations
- Creating entities with explicit field values
- Creating entities with "auto" context resolution
- Batch creation of multiple entities
- Validation of required fields
- Auto-generation of slugs and external IDs

### 2. READ Operations
- Reading entities by ID
- Reading with `include_relations=False` (basic read)
- Reading with `include_relations=True` (with related data)
- Handling non-existent entity IDs

### 3. UPDATE Operations
- Updating entity fields
- Automatic timestamp and user tracking
- Validation of entity existence
- Handling invalid entity IDs

### 4. DELETE Operations
- Soft delete (marking as deleted)
- Hard delete (permanent removal)
- Verification of delete operations

### 5. SEARCH Operations
- Text-based search with search terms
- Custom filters (type, status, etc.)
- Custom ordering (asc/desc)
- Pagination with limit and offset

### 6. LIST Operations
- Listing entities by parent (e.g., projects by organization)
- Pagination support
- Default filtering (excluding deleted items)

### 7. BATCH Operations
- Batch creation of multiple entities
- Performance analysis of batch vs individual operations

## Test Format Types

- **detailed** - Full response with metadata (count, user_id, timestamp)
- **summary** - Condensed response with key information
- **raw** - Direct data response without wrapper

## Error Cases & Edge Conditions

- Missing required fields
- Invalid entity types
- Non-existent entity IDs
- Auto context without workspace set
- Foreign key constraint violations
- Authentication/authorization failures

## Running the Tests

### Prerequisites

1. **MCP Server Running**
   ```bash
   python -m uvicorn server:app --port 8000
   ```

2. **Environment Variables Set**
   ```bash
   export NEXT_PUBLIC_SUPABASE_URL="your_supabase_url"
   export NEXT_PUBLIC_SUPABASE_ANON_KEY="your_anon_key"
   export ATOMS_TEST_EMAIL="test@example.com"
   export ATOMS_TEST_PASSWORD="test_password"
   ```

3. **Dependencies Installed**
   ```bash
   pip install pytest pytest-asyncio httpx supabase pytest-html
   ```

### Running Tests

#### Option 1: Using the Shell Script (Recommended)
```bash
./tests/run_comprehensive_tests.sh
```

This will:
- Check server availability
- Validate environment configuration
- Run all tests with detailed output
- Generate HTML and Markdown reports
- Display the test matrix

#### Option 2: Using pytest Directly
```bash
pytest tests/test_entity_tool_comprehensive.py -v -s
```

#### Option 3: Run Specific Test Classes
```bash
# Test only CREATE operations
pytest tests/test_entity_tool_comprehensive.py::TestEntityCreate -v

# Test only READ operations
pytest tests/test_entity_tool_comprehensive.py::TestEntityRead -v

# Test only error cases
pytest tests/test_entity_tool_comprehensive.py::TestErrorCases -v
```

#### Option 4: Run with Coverage
```bash
pytest tests/test_entity_tool_comprehensive.py --cov=tools.entity --cov-report=html
```

## Generated Reports

After running tests, the following reports are generated:

### 1. Test Matrix Report (`entity_tool_test_matrix_report.md`)
A comprehensive matrix showing:
- Pass/Fail status for each entity type × operation combination
- Performance metrics (duration in ms)
- Issues and edge cases discovered
- Summary statistics

Example format:
```
| Entity Type | create | read | update | delete | search | list | batch |
|-------------|--------|------|--------|--------|--------|------|-------|
| organization| ✅ PASS| ✅ PASS| ✅ PASS| ✅ PASS| ✅ PASS| ✅ PASS| ✅ PASS|
| project     | ✅ PASS| ✅ PASS| ✅ PASS| ✅ PASS| ✅ PASS| ✅ PASS| ✅ PASS|
```

### 2. HTML Report (`entity_tool_test_report.html`)
Interactive HTML report with:
- Test results with pass/fail indicators
- Stack traces for failures
- Test execution timeline
- Filter and search capabilities

### 3. Text Output Log (`entity_tool_test_output.log`)
Complete console output including:
- All test execution details
- API request/response information
- Timing information
- Error messages and stack traces

## Test Architecture

### Test Result Tracking
The `TestResults` class tracks:
- Operation status (PASS/FAIL)
- Performance metrics (duration in milliseconds)
- Issues and edge cases discovered
- Detailed notes for each test

### Fixtures

- **`supabase_jwt`** - Session-scoped JWT for authentication
- **`call_mcp`** - Helper function for MCP tool invocation with timing
- **`test_organization`** - Session-scoped test organization (auto-cleanup)
- **`check_server_running`** - Validates MCP server availability

### Test Data Management

Tests use:
- Unique UUIDs for entity names to avoid conflicts
- Session-scoped fixtures for shared resources
- Automatic cleanup of test data (soft delete)
- Isolated test execution (no cross-test dependencies)

## Understanding Test Results

### Performance Benchmarks

Typical operation times (in milliseconds):
- **CREATE**: 100-300ms (includes embedding generation)
- **READ**: 50-150ms (basic), 100-250ms (with relations)
- **UPDATE**: 100-250ms
- **DELETE**: 100-200ms (soft), 150-300ms (hard)
- **SEARCH**: 150-400ms (depending on result count)
- **LIST**: 100-300ms (depending on pagination)
- **BATCH**: 300-1000ms (3-5 entities)

### Common Issues

1. **Foreign Key Constraints**
   - Requirements need valid `block_id`
   - Projects need valid `organization_id`
   - Documents need valid `project_id`

2. **Auto Context Resolution**
   - Requires active workspace context
   - Fails gracefully with clear error message

3. **RLS (Row Level Security)**
   - All operations require valid JWT
   - User must have appropriate permissions

4. **Embedding Generation**
   - Runs asynchronously (non-blocking)
   - Failures logged but don't fail entity creation

## Extending the Test Suite

### Adding New Entity Types

1. Add entity type to `TestEntityCreate`:
```python
@pytest.mark.asyncio
async def test_create_your_entity(self, call_mcp):
    result, duration = await call_mcp(
        "entity_tool",
        {
            "operation": "create",
            "entity_type": "your_entity",
            "data": {...},
        },
    )
    # Assertions...
```

2. Add READ, UPDATE, DELETE tests following existing patterns

3. Update test matrix generation to include new entity type

### Adding New Test Scenarios

1. Create new test class:
```python
class TestYourScenario:
    """Test description."""

    @pytest.mark.asyncio
    async def test_your_case(self, call_mcp):
        # Test implementation
        pass
```

2. Record results using `test_results.record()`

3. Add any issues using `test_results.add_issue()`

## Troubleshooting

### Server Not Running
```
ERROR: MCP server is not running on http://127.0.0.1:8000
```
**Solution**: Start the server with `python -m uvicorn server:app --port 8000`

### Authentication Failed
```
Could not obtain Supabase JWT
```
**Solution**: Verify `ATOMS_TEST_EMAIL` and `ATOMS_TEST_PASSWORD` are correct

### Foreign Key Constraint Errors
```
foreign key constraint "requirements_block_id_fkey"
```
**Solution**: This is expected for requirements - tests document this edge case

### RLS Policy Violations
```
new row violates row-level security policy
```
**Solution**: Ensure user has proper permissions in Supabase

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Entity Tool Comprehensive Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python -m uvicorn server:app --port 8000 &
      - run: sleep 5  # Wait for server
      - run: ./tests/run_comprehensive_tests.sh
        env:
          NEXT_PUBLIC_SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          NEXT_PUBLIC_SUPABASE_ANON_KEY: ${{ secrets.SUPABASE_ANON_KEY }}
      - uses: actions/upload-artifact@v3
        with:
          name: test-reports
          path: tests/entity_tool_test_*.{md,html,log}
```

## Performance Analysis

The test suite includes performance tracking:

1. **Operation Timing** - Each operation is timed individually
2. **Batch Performance** - Comparison of batch vs individual operations
3. **Pagination Impact** - Analysis of limit/offset performance
4. **Relationship Loading** - Cost of including related entities

Performance data is included in the generated reports for:
- Identifying slow operations
- Capacity planning
- Optimization opportunities
- SLA validation

## Best Practices

1. **Run tests before deployment** - Catch issues early
2. **Review the test matrix** - Ensure comprehensive coverage
3. **Monitor performance trends** - Track operation durations over time
4. **Document edge cases** - Use `test_results.add_issue()` for findings
5. **Update tests with new features** - Keep test suite current
6. **Use batch operations wisely** - Balance performance vs complexity

## Support

For issues or questions:
1. Check the test output log for detailed error messages
2. Review the test matrix report for patterns
3. Examine the HTML report for stack traces
4. Refer to the entity_tool implementation in `/tools/entity.py`

## Contributing

To contribute to the test suite:
1. Follow the existing test patterns
2. Add comprehensive assertions
3. Record results in the test matrix
4. Document any new edge cases discovered
5. Update this README with new test scenarios
