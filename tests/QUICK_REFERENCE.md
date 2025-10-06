# Entity Tool Testing - Quick Reference Card

## 🚀 Quick Start

```bash
# 1. Start server
python -m uvicorn server:app --port 8000

# 2. Run tests
./tests/run_comprehensive_tests.sh

# 3. View results
cat tests/entity_tool_test_matrix_report.md
```

## 📊 Test Matrix

| Entity | CREATE | READ | UPDATE | DELETE | SEARCH | LIST | BATCH |
|--------|--------|------|--------|--------|--------|------|-------|
| org    | ✅     | ✅   | ✅     | ✅     | ✅     | ✅   | ✅    |
| proj   | ✅     | ✅   | ✅     | ✅     | ✅     | ✅   | ✅    |
| doc    | ✅     | ✅   | ✅     | ✅     | ✅     | ✅   | ⏭️    |
| req    | ⚠️     | ✅   | ✅     | ✅     | ✅     | ✅   | ⏭️    |
| test   | ✅     | ✅   | ✅     | ✅     | ✅     | ✅   | ⏭️    |

## 🔧 Common Commands

### Run Specific Tests
```bash
# By entity type
pytest tests/test_entity_tool_comprehensive.py -k "organization" -v

# By operation
pytest tests/test_entity_tool_comprehensive.py::TestEntityCreate -v

# Single test
pytest tests/test_entity_tool_comprehensive.py::TestEntityCreate::test_create_organization -v
```

### Coverage Analysis
```bash
pytest tests/test_entity_tool_comprehensive.py \
    --cov=tools.entity \
    --cov-report=html \
    --cov-report=term-missing
```

### Performance Profiling
```bash
pytest tests/test_entity_tool_comprehensive.py \
    --durations=10 \
    --tb=short
```

## 📝 Test Categories

### CREATE Operations
- ✅ With explicit fields
- ✅ With "auto" context
- ✅ Batch creation
- ⚠️ FK constraint validation

### READ Operations
- ✅ Basic read
- ✅ With relations
- ✅ Error handling

### UPDATE Operations
- ✅ Field updates
- ✅ Auto timestamps
- ✅ User tracking

### DELETE Operations
- ✅ Soft delete
- ⚠️ Hard delete (FK constraints)

### SEARCH Operations
- ✅ Text search
- ✅ Custom filters
- ✅ Ordering
- ✅ Pagination

### LIST Operations
- ✅ Parent filtering
- ✅ Pagination
- ✅ Default filters

## ⚡ Performance Benchmarks

| Operation | Expected Time | P95    |
|-----------|---------------|--------|
| CREATE    | 150ms         | 300ms  |
| READ      | 100ms         | 200ms  |
| UPDATE    | 180ms         | 300ms  |
| DELETE    | 150ms         | 250ms  |
| SEARCH    | 250ms         | 500ms  |
| LIST      | 200ms         | 350ms  |
| BATCH(3)  | 500ms         | 1000ms |

## ⚠️ Known Issues

### 1. Requirement Creation
```python
# ❌ Fails - requires valid block_id
{"entity_type": "requirement", "data": {"block_id": "fake-id"}}
```

### 2. Auto Context
```python
# ❌ Fails without workspace
{"data": {"organization_id": "auto"}}  # Needs workspace context
```

### 3. Hard Delete
```python
# ❌ Fails with FK constraints
{"operation": "delete", "soft_delete": False}  # May fail
```

## 🛠️ Utility Usage

### EntityFactory
```python
from test_utils import EntityFactory

# Create test data
org_data = EntityFactory.organization(name="Test Org")
proj_data = EntityFactory.project(org_id, name="Test Project")
```

### EntityHierarchyBuilder
```python
from test_utils import EntityHierarchyBuilder

builder = EntityHierarchyBuilder(call_mcp)
entities = await builder.build_full_hierarchy(
    org_count=1,
    projects_per_org=2,
    docs_per_project=2
)
await builder.cleanup()
```

### AssertionHelpers
```python
from test_utils import AssertionHelpers

AssertionHelpers.assert_entity_created(result, "organization")
AssertionHelpers.assert_search_results(result, min_count=1)
```

## 📋 Environment Setup

### Required Variables
```bash
export NEXT_PUBLIC_SUPABASE_URL="https://your-project.supabase.co"
export NEXT_PUBLIC_SUPABASE_ANON_KEY="your-anon-key"
export ATOMS_TEST_EMAIL="test@example.com"
export ATOMS_TEST_PASSWORD="password"
export ATOMS_FASTMCP_BASE_URL="http://127.0.0.1:8000"
```

### Verify Setup
```bash
# Check server
curl http://127.0.0.1:8000/health

# Check auth
python -c "from supabase import create_client; \
    client = create_client('$NEXT_PUBLIC_SUPABASE_URL', '$NEXT_PUBLIC_SUPABASE_ANON_KEY'); \
    print('Auth OK' if client else 'Auth Failed')"
```

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Server not running | `python -m uvicorn server:app --port 8000` |
| Auth failed | Check `ATOMS_TEST_EMAIL` and `ATOMS_TEST_PASSWORD` |
| FK constraint | Expected for requirements without blocks |
| Timeout | Increase httpx timeout in conftest.py |
| Rate limit | Use session-scoped JWT fixture |

## 📁 File Locations

```
tests/
├── test_entity_tool_comprehensive.py  # Main test suite
├── test_utils.py                      # Test utilities
├── run_comprehensive_tests.sh         # Test runner
├── conftest.py                        # Pytest config
├── COMPREHENSIVE_TESTS_README.md      # Full documentation
├── ENTITY_TOOL_TEST_SUMMARY.md        # Summary & matrix
└── QUICK_REFERENCE.md                 # This file
```

## 🔍 Debugging Tips

### Enable Verbose Logging
```bash
pytest tests/test_entity_tool_comprehensive.py -v -s --log-cli-level=DEBUG
```

### Inspect HTTP Calls
```python
# In test
result, duration = await call_mcp("entity_tool", params)
print(f"Request: {params}")
print(f"Response: {result}")
print(f"Duration: {duration}ms")
```

### Check Database State
```python
# Direct Supabase query
from supabase import create_client
client = create_client(url, key)
result = client.table("organizations").select("*").execute()
print(result.data)
```

## 📈 CI/CD Integration

### GitHub Actions
```yaml
- run: python -m uvicorn server:app --port 8000 &
- run: sleep 5
- run: ./tests/run_comprehensive_tests.sh
- uses: actions/upload-artifact@v3
  with:
    name: test-reports
    path: tests/entity_tool_test_*.{md,html,log}
```

### Pre-commit Hook
```bash
#!/bin/bash
./tests/run_comprehensive_tests.sh || exit 1
```

## 🎯 Test Execution Patterns

### Full Suite
```bash
./tests/run_comprehensive_tests.sh
```

### By Entity Type
```bash
pytest -k "organization" -v
pytest -k "project" -v
pytest -k "document" -v
```

### By Operation
```bash
pytest tests/test_entity_tool_comprehensive.py::TestEntityCreate -v
pytest tests/test_entity_tool_comprehensive.py::TestEntityRead -v
pytest tests/test_entity_tool_comprehensive.py::TestEntityUpdate -v
```

### Quick Smoke Test
```bash
pytest tests/test_entity_tool_comprehensive.py::TestEntityCreate::test_create_organization -v
```

### With Report Generation
```bash
pytest tests/test_entity_tool_comprehensive.py \
    --html=report.html \
    --self-contained-html \
    --tb=short
```

## 📊 Expected Results

### Successful Run
```
PASSED (38/45 tests)
✅ Test Matrix Report: tests/entity_tool_test_matrix_report.md
✅ HTML Report: tests/entity_tool_test_report.html
✅ Pass Rate: 84.4%
```

### With Known Failures
```
FAILED: requirement.create (FK constraint - EXPECTED)
FAILED: organization.hard_delete (FK constraint - EXPECTED)
```

## 🔗 Quick Links

- Full Docs: `tests/COMPREHENSIVE_TESTS_README.md`
- Summary: `tests/ENTITY_TOOL_TEST_SUMMARY.md`
- Test Suite: `tests/test_entity_tool_comprehensive.py`
- Utilities: `tests/test_utils.py`
- Entity Tool: `tools/entity.py`

## 💡 Pro Tips

1. **Use Session Fixtures** - Avoid recreating test orgs per test
2. **Batch Operations** - Test batch create for better coverage
3. **Check Performance** - Monitor P95 latency trends
4. **Document Edge Cases** - Use `test_results.add_issue()`
5. **Clean Up** - Use fixtures for automatic cleanup

## 🏁 Success Criteria

- ✅ All CREATE operations pass
- ✅ All READ operations pass
- ✅ All UPDATE operations pass
- ✅ SEARCH with filters works
- ✅ LIST with pagination works
- ✅ Batch operations functional
- ✅ Error cases handled gracefully
- ✅ Performance within benchmarks

---

**Last Updated**: 2025-10-02
**Test Suite Version**: 1.0.0
**Entity Tool Version**: See tools/entity.py
