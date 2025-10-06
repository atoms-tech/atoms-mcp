# Query Tool Testing - Quick Reference Guide

## Prerequisites

### 1. Environment Setup
```bash
# Ensure environment variables are set
export NEXT_PUBLIC_SUPABASE_URL="your-supabase-url"
export NEXT_PUBLIC_SUPABASE_ANON_KEY="your-anon-key"
export ATOMS_TEST_EMAIL="test@example.com"
export ATOMS_TEST_PASSWORD="your-password"

# Or use .env file
cp .env.example .env
# Edit .env with your credentials
```

### 2. Start MCP Server
```bash
# Start local server
./start_local.sh

# Verify server is running
curl http://127.0.0.1:8000/health
```

### 3. Install Test Dependencies
```bash
pip install pytest pytest-asyncio httpx supabase
```

## Quick Test Commands

### Run All Tests
```bash
# Full test suite
pytest tests/test_query_tool_comprehensive.py -v

# With detailed output
pytest tests/test_query_tool_comprehensive.py -v -s

# With HTML report
pytest tests/test_query_tool_comprehensive.py --html=report.html --self-contained-html
```

### Run Specific Test Categories

```bash
# Search query tests
pytest tests/test_query_tool_comprehensive.py::TestQueryTypeSearch -v

# RAG search tests
pytest tests/test_query_tool_comprehensive.py::TestQueryTypeRAGSearch -v

# Error handling tests
pytest tests/test_query_tool_comprehensive.py::TestErrorHandling -v

# Performance tests
pytest tests/test_query_tool_comprehensive.py::TestPerformance -v
```

### Run Individual Tests

```bash
# Single test
pytest tests/test_query_tool_comprehensive.py::TestQueryTypeSearch::test_search_single_entity -v

# RAG mode comparison
pytest tests/test_query_tool_comprehensive.py::TestRAGModeComparison::test_compare_rag_modes -v -s
```

### Generate Comprehensive Report

```bash
# Python report generator
python tests/generate_query_test_report.py

# Automated test script
./tests/run_query_tests.sh
```

## Test Output Examples

### Successful Test
```
test_search_single_entity PASSED                                        [ 10%]
✓ Search with single entity working correctly
```

### Failed Test
```
test_search_invalid_entity FAILED                                       [ 20%]
✗ Invalid entity type should be rejected
AssertionError: Expected error but got success
```

### Performance Test
```
test_search_performance PASSED                                          [ 50%]
✓ Search completed in 234ms (threshold: 5000ms)
```

### RAG Mode Comparison
```
=== RAG Mode Comparison ===
auto: {'success': True, 'result_count': 5, 'mode_used': 'semantic', 'search_time_ms': 1234}
semantic: {'success': True, 'result_count': 4, 'mode_used': 'semantic', 'search_time_ms': 1456}
keyword: {'success': True, 'result_count': 6, 'mode_used': 'keyword', 'search_time_ms': 345}
hybrid: {'success': True, 'result_count': 7, 'mode_used': 'hybrid', 'search_time_ms': 1678}
```

## Common Test Scenarios

### Test Search Functionality
```bash
# Basic search
pytest tests/test_query_tool_comprehensive.py::TestQueryTypeSearch::test_search_single_entity -v

# Search with multiple entities
pytest tests/test_query_tool_comprehensive.py::TestQueryTypeSearch::test_search_multiple_entities -v
```

### Test RAG Search
```bash
# All RAG modes
pytest tests/test_query_tool_comprehensive.py::TestQueryTypeRAGSearch -v

# Specific mode
pytest tests/test_query_tool_comprehensive.py::TestQueryTypeRAGSearch::test_rag_search_semantic_mode -v
```

### Test Aggregation
```bash
# Aggregate queries
pytest tests/test_query_tool_comprehensive.py::TestQueryTypeAggregate -v
```

### Test Error Handling
```bash
# All error scenarios
pytest tests/test_query_tool_comprehensive.py::TestErrorHandling -v

# Specific error
pytest tests/test_query_tool_comprehensive.py::TestErrorHandling::test_invalid_query_type -v
```

## Test Coverage Commands

### Generate Coverage Report
```bash
# Coverage with pytest
pytest tests/test_query_tool_comprehensive.py --cov=tools.query --cov-report=html

# View coverage
open htmlcov/index.html
```

### Coverage by Category
```bash
# Line coverage
pytest tests/test_query_tool_comprehensive.py --cov=tools.query --cov-report=term-missing

# Branch coverage
pytest tests/test_query_tool_comprehensive.py --cov=tools.query --cov-branch
```

## Debugging Failed Tests

### Verbose Output
```bash
# Show full output
pytest tests/test_query_tool_comprehensive.py -vv -s

# Show local variables on failure
pytest tests/test_query_tool_comprehensive.py -vv -l

# Stop on first failure
pytest tests/test_query_tool_comprehensive.py -x
```

### Print Debugging
```bash
# Enable print statements
pytest tests/test_query_tool_comprehensive.py -s

# Show captured output even on pass
pytest tests/test_query_tool_comprehensive.py -s --capture=no
```

### Test Specific Failure
```bash
# Re-run failed tests only
pytest tests/test_query_tool_comprehensive.py --lf

# Re-run failed tests first, then others
pytest tests/test_query_tool_comprehensive.py --ff
```

## Performance Benchmarking

### Individual Query Performance
```bash
# Search performance
pytest tests/test_query_tool_comprehensive.py::TestPerformance::test_search_performance -v -s

# RAG search performance
pytest tests/test_query_tool_comprehensive.py::TestPerformance::test_rag_search_performance -v -s
```

### Performance Report
```bash
# Generate performance report
pytest tests/test_query_tool_comprehensive.py::TestPerformance -v -s --durations=10
```

## Test Data Management

### Setup Test Data
Test data is automatically created and cleaned up by the test suite.

### Manual Cleanup
If tests fail and leave data:
```bash
# View test data
pytest tests/test_query_tool_comprehensive.py::test_data_setup -v -s

# Tests automatically clean up in finally block
```

## Continuous Integration

### CI/CD Integration
```yaml
# .github/workflows/test.yml
- name: Run Query Tool Tests
  run: |
    pytest tests/test_query_tool_comprehensive.py -v --junitxml=results.xml

- name: Upload Results
  uses: actions/upload-artifact@v2
  with:
    name: test-results
    path: results.xml
```

### Pre-commit Hook
```bash
# .git/hooks/pre-commit
#!/bin/bash
pytest tests/test_query_tool_comprehensive.py --tb=short
```

## Troubleshooting

### Server Not Running
```bash
Error: MCP server not running on http://127.0.0.1:8000

Solution:
./start_local.sh
```

### Authentication Failed
```bash
Error: Could not authenticate

Solution:
1. Check .env file has correct credentials
2. Verify Supabase user exists
3. Check password is correct
```

### Tests Timing Out
```bash
Error: Test timeout after 60s

Solution:
1. Check network connectivity
2. Verify Supabase is accessible
3. Check embedding service availability
```

### Import Errors
```bash
Error: ModuleNotFoundError: No module named 'pytest'

Solution:
pip install -r tests/requirements.txt
```

## Test Markers

### Run by Marker
```bash
# Integration tests only
pytest tests/test_query_tool_comprehensive.py -m integration

# HTTP tests only
pytest tests/test_query_tool_comprehensive.py -m http

# Async tests only
pytest tests/test_query_tool_comprehensive.py -m asyncio
```

## Quick Validation

### Smoke Test (1 minute)
```bash
# Run essential tests only
pytest tests/test_query_tool_comprehensive.py::TestQueryTypeSearch::test_search_single_entity \
       tests/test_query_tool_comprehensive.py::TestQueryTypeRAGSearch::test_rag_search_auto_mode \
       -v
```

### Full Test Suite (5-10 minutes)
```bash
# Complete test run
./tests/run_query_tests.sh
```

### Quick Report (30 seconds)
```bash
# Generate report without full tests
python tests/generate_query_test_report.py
```

## Test Metrics

### Expected Metrics
- **Total Tests:** 50+
- **Pass Rate:** 100%
- **Total Duration:** 5-10 minutes
- **Coverage:** 100% line, 100% branch

### Performance Targets
- Search: < 5s
- Aggregate: < 5s
- Analyze: < 5s
- RAG Semantic: < 10s
- RAG Keyword: < 5s
- RAG Hybrid: < 10s

## Additional Resources

### Documentation
- `QUERY_TOOL_TEST_DOCUMENTATION.md` - Full documentation
- `QUERY_TOOL_TEST_SUMMARY.md` - Executive summary

### Test Files
- `test_query_tool_comprehensive.py` - Main test suite
- `run_query_tests.sh` - Automated runner
- `generate_query_test_report.py` - Report generator

### Support
For issues or questions:
1. Check test documentation
2. Review test output
3. Check server logs
4. Verify environment configuration
