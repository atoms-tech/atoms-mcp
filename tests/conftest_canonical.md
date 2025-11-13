# Canonical Test Organization

## Structure

```
tests/
├── conftest.py                          # Shared fixtures and configuration
│
├── unit/                               # Unit tests (fast, isolated, no dependencies)
│   ├── __init__.py
│   ├── mcp/
│   │   ├── __init__.py
│   │   ├── test_server.py             # MCP server initialization, registration
│   │   ├── test_routing.py            # Tool request routing, validation
│   │   └── test_serialization.py      # Response/error serialization
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── test_workspace.py          # Workspace tool interface
│   │   ├── test_entity.py             # Entity CRUD operations
│   │   ├── test_relationship.py       # Relationship operations
│   │   ├── test_workflow.py           # Workflow execution
│   │   └── test_query.py              # Data query operations
│   │
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   ├── test_auth.py               # AuthKit JWT validation
│   │   ├── test_database.py           # Database adapter operations
│   │   └── test_rls.py                # Row-level security enforcement
│   │
│   └── security/
│       ├── __init__.py
│       ├── test_injection.py          # SQL, XSS, code injection prevention
│       ├── test_auth_security.py      # Auth bypass prevention
│       └── test_input_validation.py   # Malformed input handling
│
├── integration/                        # Integration tests (medium speed, multiple components)
│   ├── __init__.py
│   ├── test_mcp_workflows.py          # Complete MCP workflows
│   ├── test_database_auth.py          # Database + Auth integration
│   ├── test_tool_integration.py       # Multi-tool workflows
│   └── test_error_recovery.py         # Error scenarios, circuit breakers
│
├── e2e/                                # End-to-end tests (slow, full stack)
│   ├── __init__.py
│   ├── test_mcp_client.py             # MCP client usage patterns
│   ├── test_user_workflows.py         # Real-world user journeys
│   └── test_deployment_targets.py     # Local, dev, prod, serverless
│
└── performance/                        # Performance tests (benchmarks, load)
    ├── __init__.py
    ├── test_query_performance.py      # Query response times
    ├── test_concurrent_access.py      # Concurrent user handling
    └── test_resource_limits.py        # Memory, CPU, connection limits
```

## Naming Conventions

- **Test modules**: `test_<component>.py` (lowercase, underscores)
- **Test classes**: `Test<Feature>` (PascalCase, feature-focused)
- **Test methods**: `test_<scenario>_<expected_behavior>` (lowercase_underscore)
- **Fixtures**: `<resource>_fixture` or `mock_<service>`

## Example Structure

```python
# tests/unit/mcp/test_server.py
"""Unit tests for MCP server initialization and tool registration."""

import pytest
from tools import workspace_operation, entity_operation


class TestMCPServerInitialization:
    """Test MCP server setup and lifecycle."""
    
    def test_server_initializes_with_all_tools(self):
        """Server should register all 5 tools on startup."""
        ...
    
    def test_server_validates_tool_schemas(self):
        """Tool schemas should be valid JSON Schema."""
        ...


class TestMCPToolRegistration:
    """Test tool registration mechanisms."""
    
    def test_workspace_tool_registered(self):
        """Workspace tool should be available."""
        ...
```

## Test Execution

```bash
# Run all tests
pytest tests/

# Run by category
pytest tests/unit/               # Fast unit tests (~30s)
pytest tests/integration/        # Integration tests (~60s)
pytest tests/e2e/               # End-to-end tests (~120s)

# Run specific component
pytest tests/unit/mcp/          # MCP server tests
pytest tests/unit/tools/        # Tool interface tests
pytest tests/unit/security/     # Security tests

# Run with markers
pytest -m "not slow"            # Skip slow tests
pytest -m "security"            # Run security tests only
```

## Markers

```python
@pytest.mark.unit              # Fast, isolated tests
@pytest.mark.integration       # Tests multiple components
@pytest.mark.e2e               # Full stack tests
@pytest.mark.security          # Security-focused tests
@pytest.mark.performance       # Performance/load tests
@pytest.mark.slow              # Tests taking >5 seconds
@pytest.mark.mock_only         # Use mocks (CI/CD safe)
@pytest.mark.requires_db       # Requires live database
```

## Coverage Goals

- Unit tests: 70% of codebase
- Integration tests: 20% of codebase  
- E2E tests: 10% of codebase
- Combined: 100% coverage with meaningful tests
