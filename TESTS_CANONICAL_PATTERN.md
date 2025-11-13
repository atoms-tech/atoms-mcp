# Canonical Test Pattern for Atoms MCP Tools

## Overview

This document defines the canonical pattern for writing unit tests for Atoms MCP tools. All future tests should follow this pattern to maintain consistency, readability, and reliability.

## Core Pattern

### 1. File Structure

```python
"""Tool Tests - Unit Tests Only.

This test suite validates [tool_name] functionality:
- parameter1: description
- parameter2: description

Run with: pytest tests/unit/tools/test_[tool_name].py -v
"""

import pytest

pytestmark = [pytest.mark.asyncio, pytest.mark.unit]


class TestFeatureArea:
    """Test [feature area]."""
    
    async def test_specific_case(self, call_mcp):
        """Test [specific case]."""
        # Test implementation
```

### 2. Using the call_mcp Fixture

The `call_mcp` fixture is the canonical way to invoke MCP tools:

```python
async def test_example(self, call_mcp):
    """Test description."""
    # Call the tool
    result, duration_ms = await call_mcp("tool_name", {
        "param1": "value1",
        "param2": "value2",
    })
    
    # Assert the result
    assert result is not None, "Should return a result"
    # ... more assertions
```

**Result Structure:**
- `result`: Dict containing response from tool (may include success, data, error fields)
- `duration_ms`: Execution time in milliseconds
- Always use `result is not None` for basic checks
- Use `result.get("success")` only when tool explicitly returns it

### 3. Test Organization

Organize tests into logical classes:

```python
class TestFeatureArea:
    """Test [feature area of the tool]."""
    
    async def test_happy_path(self, call_mcp):
        """Test normal successful operation."""
        ...
    
    async def test_variant(self, call_mcp):
        """Test variant or edge case."""
        ...


class TestAnotherFeature:
    """Test [another feature]."""
    ...


class TestErrorHandling:
    """Test error cases."""
    ...


class TestEdgeCases:
    """Test edge cases."""
    ...
```

## Naming Conventions

- **File**: `test_[tool_name].py` (e.g., `test_query.py`)
- **Class**: `Test[Feature]` (e.g., `TestQuerySearch`)
- **Method**: `test_[specific_case]` (e.g., `test_search_by_term`)
- **Docstring**: Clear description of what is being tested

### Good Examples

```python
class TestQuerySearch:
    """Test search query type."""
    
    async def test_basic_search(self, call_mcp):
        """Test basic text search across entities."""
        ...
    
    async def test_search_with_filters(self, call_mcp):
        """Test search combined with conditions."""
        ...
    
    async def test_search_empty_results(self, call_mcp):
        """Test search returning no matches."""
        ...
```

### Bad Examples (Avoid)

```python
class TestQueries:  # Too generic
    async def test_1(self, call_mcp):  # No description
        ...

class TestQueryOperations:  # Redundant "Test"
    async def test_query_tool_search(self, call_mcp):  # Redundant "test_query_tool"
        ...
```

## Test Coverage Areas

### 1. Happy Path Tests

Test normal, successful operations:

```python
async def test_create_entity(self, call_mcp):
    """Test basic entity creation."""
    result, _ = await call_mcp("entity_tool", {
        "operation": "create",
        "entity_type": "project",
        "data": {"name": "Test Project"}
    })
    
    assert result is not None, "Should return result"
    assert result.get("success"), "Should succeed"
    assert "id" in result.get("data", {}), "Should return entity ID"
```

### 2. Parameter Variations

Test different parameter combinations:

```python
async def test_search_with_different_entity_types(self, call_mcp):
    """Test search works for all entity types."""
    entity_types = ["project", "document", "requirement"]
    
    for entity_type in entity_types:
        result, _ = await call_mcp("query_tool", {
            "query_type": "search",
            "entities": [entity_type],
            "search_term": "test",
            "limit": 10
        })
        
        assert result is not None, f"Should handle {entity_type}"
```

### 3. Edge Cases

Test boundary conditions:

```python
async def test_invalid_limit(self, call_mcp):
    """Test with invalid limit values."""
    for limit_val in [0, -1, -100]:
        result, _ = await call_mcp("query_tool", {
            "query_type": "search",
            "entities": ["project"],
            "search_term": "test",
            "limit": limit_val
        })
        
        assert result is not None, f"Should handle limit={limit_val}"
```

### 4. Format Variations

Test different output formats:

```python
async def test_format_types(self, call_mcp):
    """Test all supported format types."""
    formats = ["detailed", "summary", "raw"]
    
    for fmt in formats:
        result, _ = await call_mcp("query_tool", {
            "query_type": "search",
            "entities": ["project"],
            "search_term": "test",
            "format_type": fmt
        })
        
        assert result is not None, f"Should support format={fmt}"
```

### 5. Sequential Operations

Test realistic workflows:

```python
async def test_create_then_read(self, call_mcp):
    """Test creating then reading an entity."""
    # Create
    create_result, _ = await call_mcp("entity_tool", {
        "operation": "create",
        "entity_type": "project",
        "data": {"name": "Test"}
    })
    
    assert create_result is not None, "Should create entity"
    entity_id = create_result.get("data", {}).get("id")
    
    if entity_id:
        # Read
        read_result, _ = await call_mcp("entity_tool", {
            "operation": "read",
            "entity_id": entity_id
        })
        
        assert read_result is not None, "Should read entity"
```

## Assertion Patterns

### Basic Checks

```python
# Check result exists
assert result is not None, "Should return a result"

# Check success field (only if tool returns it)
assert result.get("success"), "Should succeed"

# Check data structure
assert "data" in result, "Should have data field"
assert isinstance(result["data"], (list, dict)), "Data should be list or dict"
```

### Content Checks

```python
# Check response contains expected fields
assert "id" in result.get("data", {}), "Should return ID"
assert result.get("data", {}).get("name") == "Expected Name", "Should have correct name"

# Check error handling
assert not result.get("success"), "Should fail"
assert "error" in result, "Should have error message"
```

### Type Checks

```python
# Check list length
assert len(results) > 0, "Should return results"
assert len(results) <= limit, "Should respect limit"

# Check dict keys
assert all(key in item for key in ["id", "name"]), "Should have required fields"
```

## Anti-Patterns to Avoid

### ❌ Don't: Use complex fixture setup

```python
# BAD: Complex fixture
@pytest_asyncio.fixture
async def setup_complex_state(call_mcp):
    # 50 lines of setup code
    ...
```

### ✅ Do: Keep fixtures simple or use test data helpers

```python
# GOOD: Simple fixture or inline data
@pytest.fixture
def test_data():
    return {
        "name": "Test Project",
        "organization_id": "org_123"
    }
```

### ❌ Don't: Test implementation details

```python
# BAD: Testing internals
assert result["_internal_cache"] is not None
```

### ✅ Do: Test public API and behavior

```python
# GOOD: Testing behavior
assert result.get("success"), "Operation should succeed"
```

### ❌ Don't: Share state between tests

```python
# BAD: Tests depend on each other
# test_1 creates entity, test_2 uses its ID
```

### ✅ Do: Make tests independent

```python
# GOOD: Each test is self-contained
async def test_1(self, call_mcp):
    # Create its own data
    ...

async def test_2(self, call_mcp):
    # Creates its own data
    ...
```

### ❌ Don't: Leave commented-out code

```python
# BAD
async def test_something(self, call_mcp):
    # result = await call_mcp(...)  # Was testing this
    # assert result is not None
    pass
```

### ✅ Do: Remove or complete tests

```python
# GOOD: Either complete or delete
async def test_something(self, call_mcp):
    result, _ = await call_mcp("tool_name", {...})
    assert result is not None
```

## Running Tests

### Run all tool tests
```bash
python3 -m pytest tests/unit/tools/ -v
```

### Run specific test file
```bash
python3 -m pytest tests/unit/tools/test_query.py -v
```

### Run specific test class
```bash
python3 -m pytest tests/unit/tools/test_query.py::TestQuerySearch -v
```

### Run specific test
```bash
python3 -m pytest tests/unit/tools/test_query.py::TestQuerySearch::test_basic_search -v
```

### Run with coverage
```bash
python3 -m pytest tests/unit/tools/ -v --cov=tools --cov-report=html
```

## Tool Signature Reference

Always check these first when writing tests:

- **server.py** (lines 477-846): Tool definitions with full signatures
- **conftest.py** (tests/unit/tools/): Mock tool implementations for testing

**Key Tools:**
- `entity_tool`: CRUD operations for all entity types
- `relationship_tool`: Managing relationships between entities
- `query_tool`: Searching and analyzing data
- `workflow_tool`: Executing complex workflows
- `workspace_tool`: Managing workspace context

## Examples by Tool

### test_query.py Example

```python
class TestQuerySearch:
    """Test search query type."""
    
    async def test_basic_search(self, call_mcp):
        """Test basic text search across entities."""
        result, duration_ms = await call_mcp("query_tool", {
            "query_type": "search",
            "entities": ["project", "document"],
            "search_term": "application",
            "limit": 10
        })
        
        assert result is not None, "Should return result"
        assert isinstance(result.get("data"), (list, dict)), "Data should be iterable"
    
    async def test_search_with_conditions(self, call_mcp):
        """Test search combined with filter conditions."""
        result, _ = await call_mcp("query_tool", {
            "query_type": "search",
            "entities": ["project"],
            "search_term": "project",
            "conditions": {"status": "active"},
            "limit": 10
        })
        
        assert result is not None, "Should return result"
```

### test_relationship.py Example

```python
class TestRelationshipLink:
    """Test linking operations."""
    
    async def test_link_basic(self, call_mcp):
        """Test basic relationship link operation."""
        result, _ = await call_mcp("relationship_tool", {
            "operation": "link",
            "relationship_type": "member",
            "source": {"type": "organization", "id": "org_123"},
            "target": {"type": "user", "id": "user_456"},
        })
        
        assert result is not None, "Should return result"
        assert "success" in result, "Should have success field"
    
    async def test_link_with_metadata(self, call_mcp):
        """Test linking with relationship metadata."""
        result, _ = await call_mcp("relationship_tool", {
            "operation": "link",
            "relationship_type": "member",
            "source": {"type": "organization", "id": "org_123"},
            "target": {"type": "user", "id": "user_456"},
            "metadata": {"role": "admin"}
        })
        
        assert result is not None, "Should return result"
```

## Checklist for New Tests

- [ ] File named `test_[tool_name].py`
- [ ] Module docstring describes what's being tested
- [ ] `pytestmark = [pytest.mark.asyncio, pytest.mark.unit]`
- [ ] Test classes logically group related tests
- [ ] Test names are descriptive (`test_[specific_case]`)
- [ ] Docstrings explain what's being tested
- [ ] Using `call_mcp` fixture (not direct imports)
- [ ] Assertions are clear and meaningful
- [ ] No shared state between tests
- [ ] No commented-out code
- [ ] Tests are independent and can run in any order
- [ ] Edge cases and error conditions covered
- [ ] Parameter variations tested where applicable

## Maintenance

### When Tool Signatures Change

1. Update `tests/unit/tools/conftest.py` with new signature
2. Update all affected test files to use new parameters
3. Run tests to ensure all pass: `python3 -m pytest tests/unit/tools/ -v`
4. Update this document if pattern changes

### When Tests Fail

1. Check if tool signature changed (compare with server.py)
2. If signature changed, update conftest.py and tests together
3. Run tests in isolation to debug: `pytest tests/unit/tools/test_[tool].py::TestClass::test_method -vvs`
4. Never commit broken tests

### Code Review Checklist

- [ ] Follows canonical pattern
- [ ] Clear, descriptive names
- [ ] No redundant code
- [ ] No commented-out code
- [ ] Tests are independent
- [ ] Proper use of fixtures
- [ ] Good assertion messages
- [ ] No implementation details tested
- [ ] Covers edge cases
- [ ] All tests pass

---

This canonical pattern ensures that:
- ✅ Tests are easy to read and understand
- ✅ Tests match actual tool signatures
- ✅ Tests are maintainable long-term
- ✅ Tests provide good documentation
- ✅ New developers can easily add tests
- ✅ Tests can be automated in CI/CD
