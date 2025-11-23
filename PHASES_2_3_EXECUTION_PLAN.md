# Phase 2 & 3 Comprehensive Execution Plan

## Executive Summary

**Goal:** Comprehensive UX overhaul through query consolidation + auto-context injection

**Approach:** Pragmatic consolidation with backward compatibility

**Timeline:** 15-18 hours of focused implementation

---

## Phase 2: Query → Entity Tool Consolidation

### Strategy: Pragmatic Consolidation

Instead of a full merge (risky), we'll do **smart operation mapping**:

```
Current State:
- entity_tool: create, read, update, delete, list, batch_create, archive, restore
- query_tool: search, aggregate, analyze, relationships, rag_search, similarity

New State (Unified):
- entity_tool now supports BOTH entity operations AND query operations
- query_tool deprecated (old calls still work with warnings)
- Users can use one tool for everything
```

### Implementation Plan

#### 2.1: Add Query Operations to entity_tool Signature (30 min)

Add new operations to entity_tool:
- `operation="search"` (from query_tool)
- `operation="aggregate"` (from query_tool)
- `operation="analyze"` (from query_tool)
- `operation="rag_search"` (from query_tool)

```python
@mcp.tool(tags={"entity", "crud", "search", "analysis"})
async def entity_tool(
    # Existing params...
    entity_type: str,
    operation: Optional[str] = None,
    
    # NEW: Add query operation params
    search_term: Optional[str] = None,        # For search/rag_search
    aggregate_type: Optional[str] = None,      # For aggregate
    group_by: Optional[list] = None,           # For aggregate
    rag_mode: str = "auto",                    # For rag_search
    similarity_threshold: float = 0.7,         # For similarity
    content: Optional[str] = None,             # For rag_search/similarity
    # ... other query params
)
```

#### 2.2: Implement Search in entity_tool (1 hour)

Copy search logic from query_tool → entity_tool:

```python
if operation == "search":
    # Use existing search implementation from query_tool
    # Auto-filter by workspace/project/entity_type from context
    return await _query_engine._search_query(
        entities=[entity_type],
        search_term=search_term,
        conditions=filters,
        limit=limit
    )
```

#### 2.3: Implement Aggregate in entity_tool (45 min)

```python
elif operation == "aggregate":
    # Copy aggregate logic from query_tool
    # Auto-group by entity_type if not specified
    return await _query_engine._aggregate_query(...)
```

#### 2.4: Implement Analyze in entity_tool (45 min)

```python
elif operation == "analyze":
    # Copy analyze logic
    return await _query_engine._analyze_query(...)
```

#### 2.5: Implement RAG Search in entity_tool (45 min)

```python
elif operation == "rag_search":
    # Copy RAG logic
    return await _query_engine._rag_search_query(...)
```

#### 2.6: Parameter Consolidation (1 hour)

Standardize parameter names across tools:

```python
# Support BOTH old and new param names
entity_types = entity_types or entities  # Support old 'entities' param
conditions = conditions or filters       # Support old 'filters' param

# Resolve entity_type from parameter OR context
if not entity_type:
    entity_type = context.get_entity_type()
    
# Auto-filter by workspace/project from context
if not workspace_id:
    workspace_id = context.resolve_workspace_id()
if not project_id:
    project_id = context.resolve_project_id()
```

#### 2.7: Add Deprecation to query_tool (30 min)

Mark query_tool operations as deprecated:

```python
async def query_tool(...):
    """DEPRECATED: Use entity_tool with operation='search'/'aggregate'/etc instead.
    
    This tool is maintained for backward compatibility only.
    New code should use entity_tool for all data operations.
    """
    import logging
    logger.warning("query_tool is deprecated. Use entity_tool instead.")
    
    # Forward to entity_tool for backward compat
    return await entity_tool(...)
```

#### 2.8: Create Migration Guide (1 hour)

Document how to migrate from query_tool → entity_tool:

```markdown
# Migration Guide: query_tool → entity_tool

## Old Way (Deprecated)
```python
await query_tool(
    query_type="search",
    entities=["requirement"],
    search_term="security",
    conditions={"status": "active"}
)
```

## New Way (Recommended)
```python
await entity_tool(
    operation="search",
    entity_type="requirement",
    search_term="security",
    conditions={"status": "active"}
)
```

## Parameter Mapping
- entities → entity_type (singular)
- query_type → operation
- filters → conditions (still supported)
- entity_types → entity_type (singular)
```

### Phase 2 Summary

**Changes:**
- entity_tool: +150 lines (new operation handlers)
- query_tool: +30 lines (deprecation + forwarding)
- server.py: +20 lines (doc update)
- guides: +200 lines (migration guide)

**Risk:** LOW (backward compat maintained, old API still works)
**Benefit:** HIGH (unified API, one tool for everything)
**Breaking changes:** NONE (old queries still work, just deprecated)

---

## Phase 3: Auto-Context Injection to Tools

### Strategy: Smart Parameter Resolution

Auto-inject resolved context values into operations.

### Implementation Plan

#### 3.1: Wire project_id Context into entity_tool (1 hour)

In entity_tool, resolve project_id from context:

```python
async def entity_tool(
    entity_type: str,
    operation: Optional[str] = None,
    data: Optional[dict] = None,
    parent_id: Optional[str] = None,  # For nested entities
    project_id: Optional[str] = None,
    # ... other params
):
    # Resolve project_id from context if not provided
    if not project_id:
        try:
            from services.context_manager import get_context
            context = get_context()
            project_id = context.resolve_project_id()
        except Exception as e:
            logger.debug(f"Could not resolve project context: {e}")
    
    # For nested operations, resolve parent_id
    if not parent_id and operation in ["create", "list"]:
        try:
            parent_id = context.resolve_parent_id()
        except Exception:
            pass
    
    # Inject into data if creating
    if operation == "create" and data and project_id:
        if "project_id" not in data:
            data["project_id"] = project_id
    
    # Inject into filters if listing
    if operation == "list" and filters and project_id:
        if "project_id" not in filters:
            filters["project_id"] = project_id
```

#### 3.2: Wire entity_type Context (30 min)

If entity_type not provided, resolve from context:

```python
# Resolve entity_type from parameter or context
if not entity_type:
    context = get_context()
    entity_type = context.resolve_entity_type()
    if not entity_type:
        return {"success": False, "error": "entity_type required"}
```

#### 3.3: Wire Context into relationship_tool (45 min)

Auto-apply source/target type context:

```python
async def relationship_tool(
    operation: str,
    relationship_type: str,
    source: Optional[dict] = None,
    target: Optional[dict] = None,
    ...
):
    # If source/target type not specified, use context
    if source and "type" not in source:
        context = get_context()
        source_type = context.resolve_entity_type()
        if source_type:
            source["type"] = source_type
```

#### 3.4: Wire Context into workflow_tool (30 min)

Auto-apply workspace/project context to workflows:

```python
async def workflow_tool(
    workflow: str,
    parameters: dict,
    ...
):
    # Auto-inject context into parameters
    context = get_context()
    
    if workspace_id := context.resolve_workspace_id():
        parameters.setdefault("workspace_id", workspace_id)
    if project_id := context.resolve_project_id():
        parameters.setdefault("project_id", project_id)
```

#### 3.5: Extend query_tool Context (15 min)

Auto-filter by context:

```python
async def query_tool(
    query_type: str,
    entities: Optional[list] = None,
    conditions: Optional[dict] = None,
    ...
):
    # Auto-filter by workspace/project context
    context = get_context()
    
    if conditions is None:
        conditions = {}
    
    if workspace_id := context.resolve_workspace_id():
        if "workspace_id" not in conditions:
            conditions["workspace_id"] = workspace_id
    
    if project_id := context.resolve_project_id():
        if "project_id" not in conditions:
            conditions["project_id"] = project_id
```

### Phase 3 Summary

**Changes:**
- entity_tool: +30 lines (context resolution)
- relationship_tool: +20 lines (context resolution)
- workflow_tool: +15 lines (context resolution)
- query_tool: +15 lines (context resolution)

**Risk:** LOW (just adds defaults, doesn't break anything)
**Benefit:** HIGH (major parameter reduction, simpler API)
**Breaking changes:** NONE

---

## Combined Phase 2+3 Impact

### Before (Current)
```python
# Must specify everything
await context_tool("set_context", context_type="workspace", context_id="ws-1")
await context_tool("set_context", context_type="project", context_id="proj-1")

await entity_tool(
    operation="create",
    entity_type="requirement",
    data={"name": "REQ-1"},
    workspace_id="ws-1",
    project_id="proj-1"
)

await query_tool(
    query_type="search",
    entities=["requirement"],
    search_term="security",
    conditions={"workspace_id": "ws-1", "project_id": "proj-1"}
)
```

### After (Phase 2+3)
```python
# Set context once
await context_tool("set_context", context_type="workspace", context_id="ws-1")
await context_tool("set_context", context_type="project", context_id="proj-1")
await context_tool("set_context", context_type="entity_type", context_id="requirement")

# All operations auto-use context
await entity_tool(operation="create", data={"name": "REQ-1"})  # ✅ Auto-injects ws-1, proj-1

await entity_tool(operation="search", search_term="security")   # ✅ Auto-filters by context

# Old query_tool still works but deprecated
await query_tool(query_type="search", entities=["requirement"], search_term="security")  # ⚠️ Deprecated
```

### Metrics
- **Parameter reduction:** 60-80% fewer params per call
- **Lines per tool call:** 2-3 lines instead of 10-15
- **API surface:** One tool for data access instead of two
- **Code duplication:** Eliminated (consolidated in entity_tool)

---

## Implementation Sequence

### Day 1: Phase 2 (Query Consolidation)
1. (30 min) Add query operation params to entity_tool signature
2. (4 hours) Implement search, aggregate, analyze, rag_search
3. (30 min) Parameter consolidation
4. (30 min) Add deprecation to query_tool
5. (1 hour) Write migration guide

**Total: 6.5 hours**

### Day 2: Phase 3 (Auto-Context)
1. (1 hour) Wire project_id context into entity_tool
2. (30 min) Wire entity_type context
3. (45 min) Wire context into relationship_tool
4. (30 min) Wire context into workflow_tool
5. (15 min) Wire context into query_tool
6. (1 hour) Comprehensive testing

**Total: 4.5 hours**

### Day 3: Integration & Testing
1. (2 hours) End-to-end testing
2. (1 hour) Documentation updates
3. (1 hour) Migration guide refinement
4. (1 hour) Buffer/issue resolution

**Total: 5 hours**

**Grand Total: 15.5 hours**

---

## Risk Mitigation

### Backward Compatibility
- ✅ Old `query_tool` still works (deprecated warnings)
- ✅ Old parameter names still work (`entities` → `entity_type`)
- ✅ No breaking changes to any API

### Testing Strategy
1. **Unit tests:** Each new operation in entity_tool
2. **Integration tests:** entity_tool + context together
3. **E2E tests:** Full workflows with context
4. **Regression tests:** Ensure query_tool backward compat

### Rollout Plan
1. Implement both phases
2. Comprehensive testing
3. Merge with deprecation warnings
4. Monitor for issues
5. Gather feedback
6. Fully remove query_tool in future release (with notice period)

---

## Success Criteria

**Phase 2 Complete When:**
- ✅ entity_tool supports search, aggregate, analyze, rag_search
- ✅ All query_tool operations work via entity_tool
- ✅ query_tool works with deprecation warnings
- ✅ Migration guide is clear and complete
- ✅ All tests pass

**Phase 3 Complete When:**
- ✅ project_id auto-injected from context
- ✅ entity_type auto-resolved from context
- ✅ relationship/workflow tools use context
- ✅ Tests verify context auto-application
- ✅ All tools work with minimal parameters

**Overall Success:**
- 60% reduction in typical tool call parameters
- One tool for all entity data operations
- Seamless context propagation
- Zero breaking changes
- Clear migration path

---

## Decision Gate

**Ready to proceed?** This plan is:
- ✅ Detailed (hour-by-hour breakdown)
- ✅ Low-risk (backward compatible)
- ✅ High-impact (major UX improvement)
- ✅ Achievable (15-18 hours)

**Approve to start implementation.**
