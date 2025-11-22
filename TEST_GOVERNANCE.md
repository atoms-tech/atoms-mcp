# Test Governance Framework

## Overview

This document defines the TDD and traceability governance for the atoms-mcp test suite, following agents.md requirements for complete, real, and well-organized tests.

## Test Organization

### Layer Structure

```
tests/
├── unit/              # Fast, isolated, mocked dependencies
│   ├── services/      # Service layer tests
│   ├── tools/         # Tool implementation tests
│   ├── infrastructure/# Infrastructure layer tests
│   └── framework/     # Framework/utility tests
├── integration/       # Real database, real services
│   ├── database/      # Supabase integration
│   ├── services/      # Service integration
│   └── workflows/     # Workflow integration
└── e2e/              # Real HTTP, real server
    ├── organization/ # Organization workflows
    ├── project/      # Project workflows
    ├── permissions/  # Permission enforcement
    └── concurrent/   # Concurrent operations
```

## Test Naming Convention

### Format
```
test_<feature>_<scenario>[_<variation>]
```

### Examples
- `test_create_organization_basic` - Basic creation
- `test_create_organization_with_members` - With additional data
- `test_create_organization_duplicate_name_fails` - Error case
- `test_create_organization_concurrent_requests` - Concurrency

## Traceability Markers

### Decorator Format
```python
@pytest.mark.traceability(
    feature="organization_management",
    requirement="ORG-001",
    test_type="unit",
    priority="high"
)
```

### Marker Fields
- `feature`: Feature being tested (e.g., "organization_management")
- `requirement`: Requirement ID (e.g., "ORG-001")
- `test_type`: "unit", "integration", or "e2e"
- `priority`: "critical", "high", "medium", "low"

## Test Execution

### Run All Tests
```bash
pytest tests/ -v
```

### Run by Layer
```bash
pytest tests/unit -v
pytest tests/integration -v
pytest tests/e2e -v
```

### Run by Feature
```bash
pytest -m "traceability[feature=organization_management]" -v
```

### Run by Priority
```bash
pytest -m "traceability[priority=critical]" -v
```

## Test Quality Standards

### Unit Tests
- ✅ No database access
- ✅ No HTTP calls
- ✅ Fast execution (<100ms)
- ✅ Isolated dependencies
- ✅ Clear assertions

### Integration Tests
- ✅ Real database (Supabase)
- ✅ Real services
- ✅ Proper setup/teardown
- ✅ Data isolation
- ✅ Transactional rollback

### E2E Tests
- ✅ Real HTTP calls
- ✅ Real server
- ✅ Real authentication
- ✅ End-to-end workflows
- ✅ Production-like scenarios

## Continuous Improvement

- Review failing tests weekly
- Update governance as needed
- Maintain 90%+ pass rate
- Document all skipped tests

