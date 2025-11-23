# Atoms MCP Server - Comprehensive Documentation Suite Plan
## Complete Plan for Web-Facing, Internal Dev, and Codebase Documentation

**Status**: ✅ FINAL COMPREHENSIVE PLAN  
**Date**: 2025-11-23  
**Version**: 1.0  
**Scope**: Not open source | Internal dev docs | Web-facing agent docs

---

## 📚 Documentation Suite Overview

Three integrated documentation layers:

1. **Web-Facing Documentation** (Public)
   - Agent-focused demonstrations
   - Getting started guides
   - Tool reference
   - Advanced patterns

2. **Internal Developer Documentation** (Private)
   - Architecture and design
   - Code organization
   - Development setup
   - Testing and deployment

3. **Codebase Documentation** (Embedded)
   - Module docstrings
   - Function docstrings
   - Type hints and comments
   - README files in subdirectories

---

## 🎯 Documentation Architecture

```
atoms-mcp-prod/
├── README.md (Root - Project Overview)
├── DEVELOPMENT.md (Root - Internal Dev Guide)
├── ARCHITECTURE.md (Root - System Design)
│
├── docs/
│   ├── README.md (Web-facing docs index)
│   ├── SUITE_OVERVIEW.md (This suite)
│   ├── 01-agent-demonstrations/
│   ├── 02-getting-started/
│   ├── 03-tool-reference/
│   ├── 04-advanced-patterns/
│   └── 05-developer-setup/
│
├── server.py (with comprehensive docstring)
├── app.py (with comprehensive docstring)
│
├── tools/
│   ├── README.md (Tools module overview)
│   ├── __init__.py (with module docstring)
│   ├── workspace.py (with comprehensive docstrings)
│   ├── entity.py (with comprehensive docstrings)
│   ├── relationship.py (with comprehensive docstrings)
│   ├── workflow.py (with comprehensive docstrings)
│   └── query.py (with comprehensive docstrings)
│
├── services/
│   ├── README.md (Services module overview)
│   ├── __init__.py (with module docstring)
│   ├── entity_service.py (with comprehensive docstrings)
│   ├── relationship_service.py (with comprehensive docstrings)
│   ├── workflow_service.py (with comprehensive docstrings)
│   └── query_service.py (with comprehensive docstrings)
│
├── infrastructure/
│   ├── README.md (Infrastructure module overview)
│   ├── __init__.py (with module docstring)
│   ├── database.py (with comprehensive docstrings)
│   ├── auth.py (with comprehensive docstrings)
│   ├── cache.py (with comprehensive docstrings)
│   └── storage.py (with comprehensive docstrings)
│
├── auth/
│   ├── README.md (Auth module overview)
│   ├── __init__.py (with module docstring)
│   ├── provider.py (with comprehensive docstrings)
│   ├── session.py (with comprehensive docstrings)
│   └── middleware.py (with comprehensive docstrings)
│
└── tests/
    ├── README.md (Testing guide)
    ├── conftest.py (with comprehensive docstrings)
    ├── unit/
    │   ├── README.md (Unit tests overview)
    │   ├── test_entity.py (with comprehensive docstrings)
    │   ├── test_relationship.py (with comprehensive docstrings)
    │   ├── test_workflow.py (with comprehensive docstrings)
    │   └── test_query.py (with comprehensive docstrings)
    └── integration/
        ├── README.md (Integration tests overview)
        ├── test_entity_integration.py
        ├── test_workflow_integration.py
        └── test_auth_integration.py
```

---

## 📋 Root-Level Documentation

### README.md (Project Overview)
```markdown
# Atoms MCP Server

Brief description of what Atoms MCP is and does.

## Quick Links
- [Web-Facing Documentation](./docs/README.md)
- [Internal Developer Guide](./DEVELOPMENT.md)
- [Architecture Overview](./ARCHITECTURE.md)
- [Getting Started (Developers)](./DEVELOPMENT.md#getting-started)

## For Agents
See [Web-Facing Documentation](./docs/README.md)

## For Internal Developers
See [Internal Developer Guide](./DEVELOPMENT.md)

## For Contributors
See [Development Setup](./DEVELOPMENT.md#development-setup)
```

### DEVELOPMENT.md (Internal Dev Guide)
Complete guide for internal developers:
- Development setup
- Architecture overview
- Code organization
- Testing procedures
- Deployment process
- Debugging tips
- Performance optimization

### ARCHITECTURE.md (System Design)
Deep dive into system architecture:
- System components
- Data flow
- Authentication flow
- Tool execution flow
- Error handling
- Performance considerations
- Security model

---

## 🌐 Web-Facing Documentation

### docs/README.md (Index)
Entry point for web-facing docs:
- What is Atoms MCP?
- Quick links to sections
- Learning paths
- Search functionality

### docs/SUITE_OVERVIEW.md
Overview of entire documentation suite:
- What's documented
- How to navigate
- For different audiences
- Search tips

### docs/01-agent-demonstrations/ (40%)
Agent-focused demonstrations:
- What agents can do
- Creating entities (with vhs)
- Searching and linking (with vhs)
- Complex workflows (with vhs)
- Error handling (with vhs)
- Real-world examples (with vhs)

### docs/02-getting-started/ (20%)
Getting started guides:
- Quick start
- Connect Claude
- Connect Cursor
- Custom agent
- First interaction

### docs/03-tool-reference/ (20%)
Tool reference from agent perspective:
- workspace_operation
- entity_operation
- relationship_operation
- workflow_execute
- data_query

### docs/04-advanced-patterns/ (15%)
Advanced topics:
- Multi-step workflows
- Error recovery
- Performance optimization
- Custom strategies

### docs/05-developer-setup/ (5%)
For MCP server developers:
- Local development
- Extending tools
- Custom tools

---

## 💻 Codebase Documentation

### Module-Level Documentation

Each module has:
1. **README.md** - Module overview
2. **__init__.py** - Module docstring
3. **Comprehensive docstrings** - Every file

### tools/ Module

**README.md**:
```markdown
# Tools Module

The 5 consolidated MCP tools.

## Tools
- workspace_operation
- entity_operation
- relationship_operation
- workflow_execute
- data_query

## Architecture
[Diagram of tool flow]

## Adding New Tools
[Instructions]
```

**workspace.py** (Example):
```python
"""Workspace operation tool.

This module implements the workspace_operation tool for managing
workspace context and organization.

Tool Operations:
    - set_context: Set active workspace context
    - get_context: Get current context
    - list_workspaces: List available workspaces
    - create_workspace: Create new workspace
    - update_workspace: Update workspace
    - delete_workspace: Delete workspace

Parameters:
    operation (str): Operation to perform
    context_type (str): Type of context (project, team, workspace)
    entity_id (str): Entity ID for context
    properties (dict): Entity properties

Returns:
    dict: Operation result with success status and data

Raises:
    ValueError: If operation is invalid
    AuthenticationError: If auth fails
    PermissionError: If user lacks permission

Example:
    >>> result = await workspace_operation(
    ...     operation='set_context',
    ...     context_type='project',
    ...     entity_id='proj_123'
    ... )
    >>> print(result)
    {'success': True, 'data': {'active_project': 'proj_123'}}
"""

async def workspace_operation(
    operation: str,
    context_type: str,
    entity_id: Optional[str] = None,
    properties: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Perform workspace operations.
    
    Args:
        operation: Operation to perform (set_context, get_context, etc.)
        context_type: Type of context (project, team, workspace)
        entity_id: Entity ID for context (optional)
        properties: Entity properties (optional)
        
    Returns:
        dict: {
            'success': bool,
            'data': dict,  # Operation result
            'error': str   # Error message if failed
        }
        
    Raises:
        ValueError: If operation is invalid
        AuthenticationError: If authentication fails
        PermissionError: If user lacks permission
        
    Note:
        This is a consolidated tool that handles all workspace
        operations. It's the primary interface for agents to
        manage workspace context.
    """
```

### services/ Module

**README.md**:
```markdown
# Services Module

Business logic layer for Atoms MCP.

## Services
- EntityService: Entity CRUD and search
- RelationshipService: Relationship management
- WorkflowService: Workflow execution
- QueryService: Data querying and search

## Architecture
[Diagram of service layer]

## Adding New Services
[Instructions]
```

### infrastructure/ Module

**README.md**:
```markdown
# Infrastructure Module

Adapters for external services.

## Adapters
- Database: Supabase adapter
- Auth: OAuth + Bearer token provider
- Cache: Redis adapter
- Storage: File storage adapter

## Architecture
[Diagram of adapter pattern]

## Adding New Adapters
[Instructions]
```

### auth/ Module

**README.md**:
```markdown
# Auth Module

Authentication and session management.

## Components
- Provider: Hybrid auth provider (OAuth + Bearer)
- Session: Session management
- Middleware: Auth middleware

## Flows
- OAuth PKCE flow
- Bearer token validation
- Session persistence

## Architecture
[Diagram of auth flow]
```

### tests/ Module

**README.md**:
```markdown
# Tests Module

Test suite for Atoms MCP.

## Test Organization
- unit/: Unit tests (fast, isolated)
- integration/: Integration tests (slower, real services)

## Running Tests
```bash
python cli.py test run --scope unit
python cli.py test run --scope integration
python cli.py test run --coverage
```

## Test Patterns
[Common patterns and examples]

## Adding Tests
[Instructions]
```

---

## 📝 Docstring Standards

### Module Docstring
```python
"""Module name and brief description.

Longer description of what this module does, its purpose,
and how it fits into the system.

Key Components:
    - Component 1: Description
    - Component 2: Description

Architecture:
    [Brief architecture description]

Example:
    >>> from module import function
    >>> result = function(param)
    >>> print(result)
"""
```

### Function Docstring
```python
def function(param1: str, param2: int) -> Dict[str, Any]:
    """Brief description of what function does.
    
    Longer description explaining the function's purpose,
    behavior, and any important details.
    
    Args:
        param1 (str): Description of param1
        param2 (int): Description of param2
        
    Returns:
        Dict[str, Any]: Description of return value with structure
        
    Raises:
        ValueError: When param1 is invalid
        TypeError: When param2 is not int
        
    Note:
        Any important notes about the function
        
    Example:
        >>> result = function("test", 42)
        >>> print(result)
        {'success': True, 'data': {...}}
    """
```

### Class Docstring
```python
class MyClass:
    """Brief description of class.
    
    Longer description of class purpose and usage.
    
    Attributes:
        attr1 (str): Description of attr1
        attr2 (int): Description of attr2
        
    Example:
        >>> obj = MyClass("test", 42)
        >>> obj.method()
        {'result': 'value'}
    """
    
    def __init__(self, attr1: str, attr2: int):
        """Initialize MyClass.
        
        Args:
            attr1: Description
            attr2: Description
        """
```

---

## 🎯 Documentation Maintenance

### Update Triggers
- Code changes → Update docstrings
- New features → Add documentation
- Bug fixes → Update relevant docs
- Performance changes → Update performance docs

### Validation
- All public functions have docstrings
- All modules have docstrings
- All classes have docstrings
- All parameters documented
- All return values documented
- All exceptions documented

### Tools
- `python cli.py lint check` - Check docstring coverage
- `python cli.py format` - Format docstrings
- `sphinx-apidoc` - Generate API reference

---

## 📊 Documentation Statistics

| Layer | Documents | Docstrings | Code Examples | Diagrams |
|-------|-----------|-----------|----------------|----------|
| Web-Facing | 23 | 0 | 50+ | 10+ |
| Internal Dev | 3 | 0 | 20+ | 5+ |
| Codebase | 0 | 100+ | 30+ | 0 |
| **Total** | **26** | **100+** | **100+** | **15+** |

---

## 🚀 Implementation Phases

### Phase 1: Codebase Documentation (Week 1)
- Add module docstrings
- Add function docstrings
- Add class docstrings
- Add README files to subdirectories

### Phase 2: Internal Dev Documentation (Week 2)
- Write DEVELOPMENT.md
- Write ARCHITECTURE.md
- Create internal guides
- Add code examples

### Phase 3: Web-Facing Documentation (Weeks 3-5)
- Create agent demonstrations
- Write getting started guides
- Write tool reference
- Write advanced patterns

### Phase 4: Polish & Integration (Week 6)
- Cross-link all documentation
- Validate all links
- Optimize for search
- Deploy to Vercel

---

## ✨ Key Principles

1. **Comprehensive** - Document everything
2. **Layered** - Different docs for different audiences
3. **Embedded** - Docstrings in code
4. **Maintained** - Keep docs in sync with code
5. **Searchable** - Easy to find information
6. **Examples** - Show real usage
7. **Accessible** - Clear and understandable


