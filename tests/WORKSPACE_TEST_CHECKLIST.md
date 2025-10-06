# Workspace Tool Test Execution Checklist

## Pre-Execution Checklist

### Environment Setup
- [ ] MCP server is running
  ```bash
  python -m atoms_mcp
  # Verify: curl http://127.0.0.1:8000/health
  ```

- [ ] Environment variables configured
  - [ ] `NEXT_PUBLIC_SUPABASE_URL` is set
  - [ ] `NEXT_PUBLIC_SUPABASE_ANON_KEY` is set
  - [ ] `ATOMS_TEST_EMAIL` is set (optional)
  - [ ] `ATOMS_TEST_PASSWORD` is set (optional)

- [ ] Dependencies installed
  ```bash
  pip install pytest pytest-asyncio httpx supabase
  ```

- [ ] Test user can authenticate
  ```bash
  # Should succeed with valid credentials
  ```

## Test Execution

### Run All Tests
- [ ] Execute full test suite
  ```bash
  ./tests/run_workspace_tests.sh
  # OR
  pytest tests/test_workspace_tool_comprehensive.py -v -s
  ```

- [ ] Verify all 40+ tests pass
- [ ] Check execution time is reasonable (< 30s typical)
- [ ] Review console output for errors

### Run Test Classes Individually

#### 1. TestGetContext
- [ ] Run get_context tests
  ```bash
  pytest tests/test_workspace_tool_comprehensive.py::TestGetContext -v
  ```
- [ ] ✅ test_get_context_basic - PASSED
- [ ] ✅ test_get_context_detailed_format - PASSED
- [ ] ✅ test_get_context_summary_format - PASSED
- [ ] ✅ test_get_context_after_set - PASSED

#### 2. TestSetContext
- [ ] Run set_context tests
  ```bash
  pytest tests/test_workspace_tool_comprehensive.py::TestSetContext -v
  ```
- [ ] ✅ test_set_organization_context - PASSED
- [ ] ✅ test_set_project_context - PASSED
- [ ] ✅ test_set_document_context - PASSED
- [ ] ✅ test_set_context_invalid_type - PASSED
- [ ] ✅ test_set_context_invalid_id - PASSED
- [ ] ✅ test_set_context_missing_entity_id - PASSED
- [ ] ✅ test_switching_contexts - PASSED

#### 3. TestListWorkspaces
- [ ] Run list_workspaces tests
  ```bash
  pytest tests/test_workspace_tool_comprehensive.py::TestListWorkspaces -v
  ```
- [ ] ✅ test_list_workspaces_basic - PASSED
- [ ] ✅ test_list_workspaces_detailed_format - PASSED
- [ ] ✅ test_list_workspaces_summary_format - PASSED
- [ ] ✅ test_list_workspaces_includes_test_org - PASSED

#### 4. TestGetDefaults
- [ ] Run get_defaults tests
  ```bash
  pytest tests/test_workspace_tool_comprehensive.py::TestGetDefaults -v
  ```
- [ ] ✅ test_get_defaults_basic - PASSED
- [ ] ✅ test_get_defaults_detailed_format - PASSED
- [ ] ✅ test_get_defaults_summary_format - PASSED
- [ ] ✅ test_get_defaults_with_context - PASSED

#### 5. TestErrorHandling
- [ ] Run error handling tests
  ```bash
  pytest tests/test_workspace_tool_comprehensive.py::TestErrorHandling -v
  ```
- [ ] ✅ test_invalid_operation - PASSED
- [ ] ✅ test_missing_operation - PASSED
- [ ] ✅ test_empty_context_type - PASSED
- [ ] ✅ test_null_entity_id - PASSED

#### 6. TestConcurrentOperations
- [ ] Run concurrent operation tests
  ```bash
  pytest tests/test_workspace_tool_comprehensive.py::TestConcurrentOperations -v
  ```
- [ ] ✅ test_concurrent_get_context - PASSED
- [ ] ✅ test_concurrent_list_workspaces - PASSED

#### 7. TestResponseFormats
- [ ] Run response format tests
  ```bash
  pytest tests/test_workspace_tool_comprehensive.py::TestResponseFormats -v
  ```
- [ ] ✅ test_all_operations_detailed_format - PASSED
- [ ] ✅ test_all_operations_summary_format - PASSED
- [ ] ✅ test_invalid_format_type - PASSED

## Coverage Verification

### Generate Coverage Report
- [ ] Run tests with coverage
  ```bash
  pytest tests/test_workspace_tool_comprehensive.py -v -s \
    --cov=atoms_mcp --cov-report=html:coverage_workspace_tool
  ```

### Review Coverage Metrics
- [ ] Line coverage ≥ 95%
- [ ] Branch coverage ≥ 95%
- [ ] Function coverage = 100%
- [ ] Operation coverage = 100%

### Coverage Areas
- [ ] All 4 operations covered
  - [ ] get_context: 100%
  - [ ] set_context: 100%
  - [ ] list_workspaces: 100%
  - [ ] get_defaults: 100%

- [ ] All format types covered
  - [ ] detailed format: 100%
  - [ ] summary format: 100%

- [ ] All context types covered
  - [ ] organization: 100%
  - [ ] project: 100%
  - [ ] document: 100%

- [ ] All error paths covered
  - [ ] Invalid operations: ✅
  - [ ] Missing parameters: ✅
  - [ ] Invalid parameters: ✅

## Performance Verification

### Response Time Checks
Review test output for response times:

- [ ] get_context response time < 500ms
  - Actual: _____ ms

- [ ] set_context response time < 750ms
  - Actual: _____ ms

- [ ] list_workspaces response time < 1000ms
  - Actual: _____ ms

- [ ] get_defaults response time < 500ms
  - Actual: _____ ms

### Concurrent Performance
- [ ] 5 concurrent get_context calls < 2s total
  - Actual: _____ s

- [ ] 3 concurrent list_workspaces calls < 3s total
  - Actual: _____ s

## Post-Execution Verification

### Review Output Files
- [ ] workspace_test_output.log exists and is complete
- [ ] test-results-workspace-tool.xml is valid JUnit XML
- [ ] coverage_workspace_tool/index.html is accessible (if coverage run)

### Verify Test Results
- [ ] All tests passed (0 failures)
- [ ] No skipped tests (unless server unavailable)
- [ ] No warnings or errors in output
- [ ] Test data cleaned up successfully

### Performance Analysis
- [ ] All response times within acceptable range
- [ ] No significant performance regression
- [ ] Concurrent operations succeeded
- [ ] No timeout errors

## Issue Tracking

### Issues Found During Testing
Record any issues discovered:

#### Issue 1
- Test Case: _________________
- Status: PASSED / FAILED / ERROR
- Issue: _________________
- Response Time: _____ ms
- Notes: _________________

#### Issue 2
- Test Case: _________________
- Status: PASSED / FAILED / ERROR
- Issue: _________________
- Response Time: _____ ms
- Notes: _________________

#### Issue 3
- Test Case: _________________
- Status: PASSED / FAILED / ERROR
- Issue: _________________
- Response Time: _____ ms
- Notes: _________________

## Final Verification

### Test Summary
- [ ] Total tests run: _____ (expected: 40+)
- [ ] Tests passed: _____ (expected: 100%)
- [ ] Tests failed: _____ (expected: 0)
- [ ] Tests skipped: _____ (expected: 0)
- [ ] Total execution time: _____ seconds

### Coverage Summary
- [ ] Line coverage: _____% (target: ≥95%)
- [ ] Branch coverage: _____% (target: ≥95%)
- [ ] Function coverage: _____% (target: 100%)
- [ ] Operation coverage: 100% ✅

### Performance Summary
- [ ] All response times acceptable: YES / NO
- [ ] Concurrent operations successful: YES / NO
- [ ] No performance regressions: YES / NO

### Sign-off
- [ ] All tests executed successfully
- [ ] Coverage meets requirements
- [ ] Performance within acceptable range
- [ ] No critical issues found
- [ ] Documentation updated if needed

**Tested By**: _________________
**Date**: _________________
**Time**: _________________
**Environment**: _________________
**Server Version**: _________________

## Next Steps

### If All Tests Pass
- [ ] Archive test results
- [ ] Update test documentation
- [ ] Proceed with deployment/release
- [ ] Schedule next test run

### If Tests Fail
- [ ] Document failure details
- [ ] Create bug tickets for issues
- [ ] Investigate root causes
- [ ] Implement fixes
- [ ] Re-run tests
- [ ] Update test cases if needed

## Notes

Additional observations or comments:

```
[Space for notes]
```

---

**Checklist Version**: 1.0
**Last Updated**: 2025-10-02
