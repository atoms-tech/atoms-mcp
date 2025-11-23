# Deep Dive: Additional Analysis on Specific Topics

## Topic 1: Tool Design Patterns & Consolidation Strategy

### Current State Analysis
- **5 consolidated tools** (workspace, entity, relationship, workflow, query)
- **52+ parameters** across entity_tool + query_tool
- **Duplicate logic** (search in both entity_tool and query_tool)
- **Inconsistent naming** (entities vs entity_types, conditions vs filters)

### Consolidation Strategy

#### Phase 1: Parameter Reduction (47%)
**Goal**: Reduce parameters through context-driven design

**Current Pattern**:
```python
# 15+ parameters per workflow
entity_tool(
    operation="create",
    entity_type="requirement",
    data={...},
    workspace_id="ws-1",      # Redundant
    project_id="proj-1",      # Redundant
    parent_id="doc-1",        # Redundant
    format_type="detailed",   # Redundant
    include_relations=False   # Redundant
)
```

**After Consolidation**:
```python
# 3 parameters + context
context_tool("set_context", context_type="workspace", entity_id="ws-1")
context_tool("set_context", context_type="project", entity_id="proj-1")
entity_tool(
    operation="create",
    entity_type="requirement",
    data={...}
    # workspace_id, project_id, parent_id auto-injected
)
```

**Implementation**:
1. Extend SessionContext with 5 context types
2. Add context resolution to entity_tool
3. Auto-inject context into all operations
4. Update tests to verify auto-injection

#### Phase 2: Query Consolidation (50%)
**Goal**: Merge query_tool into entity_tool

**Current Pattern**:
```python
# Two separate tools
entity_tool(operation="read", entity_type="project", entity_id="...")
query_tool(query_type="search", entities=["project"], search_term="...")
```

**After Consolidation**:
```python
# One unified tool
entity_tool(operation="read", entity_type="project", entity_id="...")
entity_tool(operation="search", entity_type="project", search_term="...")
```

**Implementation**:
1. Add search/aggregate/analyze operations to entity_tool
2. Reuse query_engine from query_tool
3. Keep query_tool as deprecated wrapper
4. Consolidate parameter naming

#### Phase 3: Parameter Consolidation
**Goal**: Consistent naming across tools

**Current Inconsistencies**:
- `entities` vs `entity_types`
- `conditions` vs `filters`
- `search_term` vs `search_query`

**Solution**:
```python
# Accept both old and new names
async def entity_operation(
    entity_type: str = None,
    entity_types: List[str] = None,  # New name
    filters: Dict = None,
    conditions: Dict = None,  # Old name
    ...
):
    # Normalize parameters
    entity_types = entity_types or [entity_type]
    filters = filters or conditions or {}
    
    if conditions and not filters:
        logger.warning("'conditions' is deprecated, use 'filters'")
```

### Tool Design Principles

#### 1. Single Responsibility
Each tool should have one clear purpose:
- **context_tool**: Session state management
- **entity_tool**: CRUD + search + analysis
- **relationship_tool**: Entity associations
- **workflow_tool**: Complex multi-step operations

#### 2. Consistent Interface
All tools should follow same patterns:
- Same parameter naming
- Same response format
- Same error handling
- Same pagination

#### 3. Context-Driven Design
Use context to eliminate redundant parameters:
- Workspace context (auto-injected)
- Project context (auto-injected)
- Document context (auto-injected)
- Entity type context (auto-injected)
- Pagination state (auto-applied)

#### 4. Composition Over Monoliths
Small, composable operations > large monolithic tools:
- Each operation does one thing well
- Operations can be combined
- Easier to test and maintain
- Better for agents

#### 5. Backwards Compatibility
Never break existing APIs:
- Support old parameter names
- Deprecation warnings
- Migration guide
- Gradual transition

## Topic 2: Context Management Deep Dive

### 3-Level Resolution Pattern

```python
# Level 1: Explicit parameter
entity_tool(operation="create", entity_type="project", workspace_id="ws-1")

# Level 2: Context variable (if no explicit param)
context_tool("set_context", context_type="workspace", entity_id="ws-1")
entity_tool(operation="create", entity_type="project")
# workspace_id resolved from context

# Level 3: Session storage (if no context var)
# Persisted to Supabase mcp_sessions table
# Survives across requests
```

### Implementation Details

```python
class SessionContext:
    _context_vars = {
        "workspace_id": contextvars.ContextVar("workspace_id"),
        "project_id": contextvars.ContextVar("project_id"),
        "document_id": contextvars.ContextVar("document_id"),
        "parent_id": contextvars.ContextVar("parent_id"),
        "entity_type": contextvars.ContextVar("entity_type"),
    }
    
    async def set_context(self, context_type: str, entity_id: str):
        """Set context and persist to session."""
        if context_type not in self._context_vars:
            raise ValueError(f"Unknown context type: {context_type}")
        
        # 1. Set context variable
        self._context_vars[context_type].set(entity_id)
        
        # 2. Persist to session storage
        await self._persist_to_session(context_type, entity_id)
    
    async def resolve_context(self, context_type: str) -> Optional[str]:
        """3-level resolution: param → context → session."""
        # 1. Check context vars
        try:
            return self._context_vars[context_type].get()
        except LookupError:
            pass
        
        # 2. Load from session storage
        return await self._load_from_session(context_type)
    
    async def _persist_to_session(self, context_type: str, entity_id: str):
        """Persist to Supabase mcp_sessions table."""
        session_id = self.session_id
        mcp_state = await self._get_mcp_state(session_id)
        mcp_state[context_type] = entity_id
        await self._update_mcp_state(session_id, mcp_state)
    
    async def _load_from_session(self, context_type: str) -> Optional[str]:
        """Load from Supabase mcp_sessions table."""
        session_id = self.session_id
        mcp_state = await self._get_mcp_state(session_id)
        return mcp_state.get(context_type)
```

### Context Lifecycle

```
Session Start
    ↓
Set Workspace Context
    ↓
Set Project Context
    ↓
Set Document Context
    ↓
Operations (auto-inject context)
    ↓
Switch Project
    ↓
Update Project Context
    ↓
Operations (auto-inject new project)
    ↓
Session End
    ↓
Clear Context
```

### Benefits

1. **Parameter Reduction**: 47% fewer parameters
2. **Consistency**: Same context across all operations
3. **Safety**: Prevents cross-workspace errors
4. **Performance**: Cached context resolution
5. **UX**: Cleaner API, easier to use

## Topic 3: Error Handling & Recovery Strategy

### Error Categories

#### 1. Validation Errors (400)
- Missing required fields
- Invalid parameter values
- Type mismatches

**Recovery**:
```python
# Check entity_types_reference for required fields
# Include all required fields
entity_tool(
    operation="create",
    entity_type="project",
    data={"name": "My Project"}  # Include required fields
)
```

#### 2. Authentication Errors (401)
- Missing auth token
- Invalid token
- Token expired

**Recovery**:
```python
# Re-authenticate
# Refresh token
# Retry operation
```

#### 3. Authorization Errors (403)
- Permission denied
- Wrong workspace context
- Insufficient privileges

**Recovery**:
```python
# Check context
context = context_tool(operation="get_context")

# Verify workspace
if context["workspace_id"] != expected_workspace:
    context_tool(
        operation="set_context",
        context_type="workspace",
        entity_id=expected_workspace
    )

# Retry operation
```

#### 4. Not Found Errors (404)
- Entity not found
- Workspace not found
- Invalid ID

**Recovery**:
```python
# List entities to find correct ID
entities = entity_tool(operation="list", entity_type="project")

# Find by name
target = next((e for e in entities if e["name"] == "My Project"), None)

# Use correct ID
if target:
    entity_tool(operation="read", entity_type="project", entity_id=target["id"])
```

#### 5. Server Errors (500)
- Database errors
- Service unavailable
- Timeout

**Recovery**:
```python
# Retry with exponential backoff
# Check service status
# Contact support
```

### Error Response Format

```python
{
    "success": False,
    "error": "Entity not found: 'proj-xyz'",
    "error_code": "NOT_FOUND",
    "suggestions": [
        "Project-1 (97% match)",
        "Projects-All (85% match)"
    ],
    "recovery_actions": [
        "Try: entity_tool('list', entity_type='project')",
        "Check: context_tool('get_context')"
    ],
    "trace_id": "trace-123",
    "timestamp": "2025-11-23T10:00:00Z"
}
```

### Fuzzy Matching for Suggestions

```python
async def _suggest_similar_ids(invalid_id: str, entity_type: str):
    """Fuzzy match invalid ID against existing entities."""
    from difflib import get_close_matches
    
    # Get all entities of type
    entities = await entity_adapter.list(entity_type)
    
    # Extract IDs and names
    candidates = [e["id"] for e in entities] + [e["name"] for e in entities]
    
    # Find close matches
    matches = get_close_matches(invalid_id, candidates, n=3, cutoff=0.6)
    
    return {
        "error": f"Entity not found: {invalid_id}",
        "suggestions": matches,
        "recovery_actions": [
            f"Try: entity_tool('read', entity_type='{entity_type}', entity_id='{m}')"
            for m in matches
        ]
    }
```

## Topic 4: Performance Optimization Strategy

### Caching Strategy

#### 1. Context Caching
```python
# Cache context resolution
_context_cache = {}

async def resolve_context(self, context_type: str) -> Optional[str]:
    cache_key = f"{self.session_id}:{context_type}"
    
    # Check cache
    if cache_key in _context_cache:
        return _context_cache[cache_key]
    
    # Resolve and cache
    value = await self._resolve_from_storage(context_type)
    _context_cache[cache_key] = value
    
    return value
```

#### 2. Entity Caching
```python
# Cache frequently accessed entities
_entity_cache = {}

async def read_entity(self, entity_type: str, entity_id: str):
    cache_key = f"{entity_type}:{entity_id}"
    
    # Check cache
    if cache_key in _entity_cache:
        return _entity_cache[cache_key]
    
    # Read and cache
    entity = await self._read_from_db(entity_type, entity_id)
    _entity_cache[cache_key] = entity
    
    return entity
```

#### 3. Cache Invalidation
```python
# Invalidate cache on write
async def update_entity(self, entity_type: str, entity_id: str, data: dict):
    # Update in DB
    entity = await self._update_in_db(entity_type, entity_id, data)
    
    # Invalidate cache
    cache_key = f"{entity_type}:{entity_id}"
    if cache_key in _entity_cache:
        del _entity_cache[cache_key]
    
    return entity
```

### Query Optimization

#### 1. Pagination
```python
# Always paginate large result sets
entity_tool(
    operation="list",
    entity_type="requirement",
    limit=50,
    offset=0
)
```

#### 2. Filtering
```python
# Filter early to reduce result size
entity_tool(
    operation="search",
    entity_type="requirement",
    search_term="security",
    filters={"status": "active"}
)
```

#### 3. Projection
```python
# Only fetch needed fields
entity_tool(
    operation="list",
    entity_type="requirement",
    projections=["id", "name", "status"]
)
```

### Batch Operations

```python
# Batch operations are more efficient
entity_tool(
    operation="batch_create",
    entity_type="requirement",
    batch=[...],
    transaction_mode=True,
    parallel=True,
    batch_size=100
)
```

## Topic 5: Testing Strategy

### Unit Tests
```python
def test_context_resolution():
    # Test 3-level resolution
    # Test context persistence
    # Test context clearing
    pass

def test_parameter_consolidation():
    # Test old parameter names work
    # Test new parameter names work
    # Test deprecation warnings
    pass

def test_error_suggestions():
    # Test fuzzy matching
    # Test suggestion accuracy
    # Test recovery actions
    pass
```

### Integration Tests
```python
def test_entity_creation_with_context():
    # Set context
    # Create entity
    # Verify context auto-injected
    pass

def test_query_consolidation():
    # Test search via entity_tool
    # Test aggregate via entity_tool
    # Test results match query_tool
    pass
```

### E2E Tests
```python
def test_complete_workflow():
    # Set workspace context
    # Set project context
    # Create entities
    # Search entities
    # Link entities
    # Verify all operations used context
    pass
```

## Summary

This deep dive covers:
1. **Tool Design Patterns** - Consolidation strategy, principles
2. **Context Management** - 3-level resolution, lifecycle
3. **Error Handling** - Categories, recovery, suggestions
4. **Performance** - Caching, optimization, batching
5. **Testing** - Unit, integration, E2E strategies

**Key Takeaways**:
- ✅ Consolidation reduces parameters by 47%
- ✅ Context-driven design improves UX
- ✅ Error suggestions help debugging
- ✅ Caching improves performance
- ✅ Comprehensive testing ensures quality

