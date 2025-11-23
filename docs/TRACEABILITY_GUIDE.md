# Test Traceability Guide

## Overview

Tests are linked to requirements and user stories using pytest markers. This enables:
- ✅ Traceability from requirements to tests
- ✅ Coverage reporting by feature
- ✅ Test discovery by story
- ✅ PM-friendly reporting

## Story Marker System

### Format

```python
@pytest.mark.story("Epic Name - User story description")
async def test_something(fixtures):
    """Test description."""
    ...
```

### Example

```python
@pytest.mark.story("Organization Management - User can create an organization")
@pytest.mark.unit
async def test_create_organization(mcp_client):
    """Create organization with valid data."""
    result = await mcp_client.call_tool("entity_tool", {
        "entity_type": "organization",
        "operation": "create",
        "data": {"name": "Acme Corp"}
    })
    assert result["success"] is True
```

## Test Layers

Tests are organized by layer with markers:

- **@pytest.mark.unit** - Fast, isolated, mocked (< 100ms)
- **@pytest.mark.integration** - Real database, real services
- **@pytest.mark.e2e** - Real HTTP, real server, real auth

## Running Tests by Story

### Run all tests for a story
```bash
pytest -k "create_organization" -v
```

### Run tests by layer
```bash
pytest -m unit -v          # Unit tests only
pytest -m integration -v   # Integration tests only
pytest -m e2e -v          # E2E tests only
```

### Run tests by priority
```bash
pytest -m "not slow" -v    # Skip slow tests
pytest -m slow -v          # Only slow tests
```

## User Stories

See `tests/framework/user_story_mapping.py` for complete list of:
- 11 Epics
- 50+ User Stories
- Test patterns for each story

## Traceability Report

Generate coverage report:
```bash
pytest tests/ --tb=no -v 2>&1 | grep "PASSED\|FAILED\|SKIPPED"
```

## Adding New Tests

1. **Identify the user story** - Which epic/story does this test cover?
2. **Add story marker** - Link test to story
3. **Add layer marker** - Mark as unit/integration/e2e
4. **Add priority marker** - Mark as slow if > 1s

Example:
```python
@pytest.mark.story("Project Management - User can create a project")
@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_project(mcp_client):
    """Create project with valid data."""
    ...
```

## Coverage Goals

- ✅ 100% of user stories have tests
- ✅ Each story has unit + integration + e2e tests
- ✅ All tests passing
- ✅ Clear traceability from story to test

