# Testing Guide for Atoms MCP

## Overview

This project uses a comprehensive testing strategy with three test levels:
- **Unit Tests** (fast, in-memory, deterministic)
- **Integration Tests** (HTTP client, real services)
- **E2E Tests** (full system, real deployment)

## Running Tests

### Quick Start

```bash
# Run all E2E tests (recommended for development)
atoms test --scope e2e --env local

# Run unit tests only
atoms test --scope unit --env local

# Run integration tests
atoms test --scope integration --env local

# Run all tests with coverage
python -m pytest tests/ -p pytest_cov --cov=services --cov=tools --cov-report=term-missing
```

### Test Scopes

| Scope | Command | Speed | Dependencies | Use Case |
|-------|---------|-------|--------------|----------|
| **Unit** | `atoms test --scope unit` | <1s | None (mocked) | Development, CI/CD |
| **Integration** | `atoms test --scope integration` | 5-10s | Local services | Feature testing |
| **E2E** | `atoms test --scope e2e` | 3-5s | Full deployment | Regression testing |

## Test Organization

### Canonical Test File Naming

Test files use **concern-based naming** (what's tested), not speed/variant-based:

✅ **Good:**
- `test_entity_crud.py` - Entity CRUD operations
- `test_auth_integration.py` - Authentication integration
- `test_resilience.py` - Error recovery and resilience
- `test_workflow_automation.py` - Workflow automation

❌ **Bad:**
- `test_entity_fast.py` - Speed-based (use markers instead)
- `test_entity_unit.py` - Scope-based (use fixtures instead)
- `test_entity_old.py` - Temporal metadata (use git history)

### Test File Structure

```
tests/
├── unit/                    # Unit tests (in-memory, fast)
│   ├── tools/              # Tool-specific tests
│   ├── infrastructure/      # Infrastructure adapter tests
│   └── security/           # Security and RLS tests
├── integration/            # Integration tests (HTTP, real services)
│   ├── workflows/          # Workflow integration tests
│   └── workspace/          # Workspace integration tests
└── e2e/                    # End-to-end tests (full system)
    ├── test_entity_crud.py
    ├── test_auth_integration.py
    ├── test_resilience.py
    └── ...
```

## Test Patterns

### Fixture Parametrization (Not Separate Files)

Use `@pytest.fixture(params=[...])` for test variants instead of creating separate files:

```python
# ✅ GOOD: One file, multiple variants
@pytest.fixture(params=["unit", "integration", "e2e"])
def mcp_client(request):
    """Parametrized client: tests run 3 times automatically."""
    if request.param == "unit":
        return InMemoryMcpClient()
    elif request.param == "integration":
        return HttpMcpClient("http://localhost:8000")
    elif request.param == "e2e":
        return HttpMcpClient("https://mcpdev.atoms.tech")

async def test_entity_creation(mcp_client):
    """Runs 3 times: unit, integration, e2e."""
    result = await mcp_client.call_tool("entity_tool", {...})
    assert result.success
```

### Test Markers

Register markers in `pyproject.toml`:

```ini
[tool.pytest.ini_options]
markers = [
    "e2e: end-to-end tests",
    "unit: unit tests (in-memory)",
    "integration: integration tests (HTTP)",
    "slow: slow tests (>5s)",
    "flaky: potentially flaky tests",
    "story: user story mapping",
    "security: security tests",
]
```

Use markers for categorization:

```python
@pytest.mark.e2e
@pytest.mark.story("User can create organizations")
@pytest.mark.slow
async def test_create_organization(end_to_end_client):
    """Create organization with full workflow."""
    ...
```

## Test Coverage

### Current Status

- **E2E Tests:** 220 passing, 12 skipped
- **Unit Tests:** 703 passing, 67 failing (auth infrastructure issue)
- **Integration Tests:** Partial coverage
- **Overall:** ~13% of tests are E2E (rest are unit/integration)

### Coverage Goals

- **Services layer:** ≥95% coverage
- **Infrastructure adapters:** ≥95% coverage
- **Tools:** ≥90% coverage
- **Overall:** ≥85% coverage

## Known Issues

### 1. Permission Middleware Tests (12 skipped)
- **Issue:** WorkOS token validation not working
- **Status:** Pending auth token validation fix
- **Workaround:** Use mock-based permission enforcement tests

### 2. Unit Test Failures (67 failing)
- **Issue:** Unit tests using HTTP client instead of in-memory
- **Status:** Requires test infrastructure refactoring
- **Workaround:** Run E2E tests for validation

### 3. Flaky Tests (2)
- `test_database_connection_retry` - Marked with `@pytest.mark.flaky(reruns=3)`
- `test_workflow_with_retry` - Marked with `@pytest.mark.flaky(reruns=3)`

## Best Practices

1. **Use canonical test file names** (concern-based)
2. **Use fixture parametrization** for test variants
3. **Use markers** for categorization (not file names)
4. **Keep tests deterministic** (no randomness, no timing)
5. **Mock external services** in unit tests
6. **Use real services** in integration/E2E tests
7. **Document test scenarios** with docstrings
8. **Mark slow tests** with `@pytest.mark.slow`
9. **Mark flaky tests** with `@pytest.mark.flaky(reruns=3)`
10. **Run tests frequently** during development

## Continuous Integration

Tests run automatically on:
- Pull requests (all scopes)
- Commits to main (all scopes)
- Scheduled nightly runs (full coverage analysis)

See `.github/workflows/` for CI configuration.

