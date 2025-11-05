# Quick Start Test Guide

## Running the Application & Integration Tests

### Prerequisites
```bash
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/atoms-mcp-prod
pip install pytest pytest-asyncio pytest-cov
```

### Quick Test Commands

#### Run All New Tests
```bash
pytest tests/unit_refactor/test_application_commands.py \
       tests/unit_refactor/test_application_queries.py \
       tests/integration_refactor/ -v
```

#### Run with Coverage Report
```bash
pytest tests/unit_refactor/test_application_commands.py \
       tests/unit_refactor/test_application_queries.py \
       tests/integration_refactor/ \
       --cov=tools \
       --cov-report=html \
       --cov-report=term-missing
```

#### Run Specific Test File
```bash
# Commands only
pytest tests/unit_refactor/test_application_commands.py -v

# Queries only
pytest tests/unit_refactor/test_application_queries.py -v

# Integration only
pytest tests/integration_refactor/test_domain_application_integration.py -v

# CLI only
pytest tests/integration_refactor/test_cli_integration.py -v

# MCP only
pytest tests/integration_refactor/test_mcp_integration.py -v
```

#### Run Specific Test Class
```bash
pytest tests/unit_refactor/test_application_commands.py::TestCreateEntityCommand -v
```

#### Run Specific Test Method
```bash
pytest tests/unit_refactor/test_application_commands.py::TestCreateEntityCommand::test_create_organization_success -v
```

#### Run with Verbose Output
```bash
pytest tests/unit_refactor/ tests/integration_refactor/ -vv
```

#### Run in Parallel (if pytest-xdist installed)
```bash
pip install pytest-xdist
pytest tests/unit_refactor/ tests/integration_refactor/ -n auto
```

### Expected Output

#### Successful Run
```
tests/unit_refactor/test_application_commands.py::TestCreateEntityCommand::test_create_organization_success PASSED
tests/unit_refactor/test_application_commands.py::TestCreateEntityCommand::test_create_project_with_slug_generation PASSED
...

====== 150 passed in 5.23s ======
```

#### With Coverage
```
---------- coverage: platform darwin, python 3.11.x -----------
Name                              Stmts   Miss  Cover   Missing
---------------------------------------------------------------
tools/entity/entity.py              450     10    98%   234-237, 456
tools/entity/relationship.py        320      5    98%   123-125
tools/query.py                      380      8    98%   234, 567-570
tools/workflow/workflow.py          280      6    98%   123-128
---------------------------------------------------------------
TOTAL                              1430     29    98%
```

### Test Organization

```
tests/
├── unit_refactor/
│   ├── conftest.py              - Fixtures and mocks
│   ├── test_application_commands.py  - Command handler tests
│   └── test_application_queries.py   - Query handler tests
└── integration_refactor/
    ├── test_domain_application_integration.py  - Domain flows
    ├── test_cli_integration.py                  - CLI interface
    └── test_mcp_integration.py                  - MCP protocol
```

### Test Markers

Tests can be run by marker:
```bash
# Run only unit tests
pytest tests/ -m unit -v

# Run only integration tests
pytest tests/ -m integration -v

# Run only async tests
pytest tests/ -m asyncio -v
```

### Debugging Failed Tests

#### Show stdout/stderr
```bash
pytest tests/unit_refactor/test_application_commands.py -s
```

#### Stop at first failure
```bash
pytest tests/unit_refactor/ -x
```

#### Show local variables on failure
```bash
pytest tests/unit_refactor/ -l
```

#### Enter debugger on failure
```bash
pytest tests/unit_refactor/ --pdb
```

### Common Issues

#### Import Errors
```bash
# Fix: Install dependencies
pip install -e .
pip install -r requirements.txt
```

#### Missing Fixtures
```bash
# Fix: Ensure conftest.py is in correct location
ls tests/unit_refactor/conftest.py
```

#### Async Errors
```bash
# Fix: Install pytest-asyncio
pip install pytest-asyncio
```

### Performance Testing

#### Time Each Test
```bash
pytest tests/unit_refactor/ --durations=10
```

#### Profile Tests
```bash
pip install pytest-profiling
pytest tests/unit_refactor/ --profile
```

### Continuous Integration

#### GitHub Actions Example
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest tests/unit_refactor/ tests/integration_refactor/ --cov --cov-report=xml
      - uses: codecov/codecov-action@v2
```

### Test Data

All tests use mocked data with UUID generation:
- No database connection required
- No external services needed
- Fast execution (< 10 seconds total)
- Deterministic results

### Key Test Files

| File | Purpose | Lines | Tests |
|------|---------|-------|-------|
| test_application_commands.py | Command handlers | 903 | ~40 |
| test_application_queries.py | Query handlers | 876 | ~35 |
| test_domain_application_integration.py | E2E flows | 825 | ~25 |
| test_cli_integration.py | CLI interface | 776 | ~25 |
| test_mcp_integration.py | MCP protocol | 769 | ~25 |

### Success Criteria

✅ All tests should pass
✅ Coverage > 95% for tested modules
✅ No flaky tests
✅ Fast execution (< 10 seconds)
✅ Clear error messages

### Next Steps

1. Run tests locally to verify setup
2. Fix any import or dependency issues
3. Review coverage report
4. Add tests to CI/CD pipeline
5. Monitor test health over time

### Support

For issues or questions:
- Check test logs with `-vv` flag
- Review conftest.py for fixture definitions
- Check import paths in test files
- Verify all dependencies are installed

---

**Created:** 2025-10-30
**Test Suite Version:** 1.0
**Total Tests:** ~150
**Total LOC:** 4,149
