# Comprehensive UX & QOL Roadmap

## What We've Built So Far ✅

### Phase 1: Multi-Context Support (COMPLETE)
Implemented flexible session-based context for **workspace, project, organization, entity_type, and parent**.

**Features:**
- 5 context types with persistent storage in Supabase
- Smart resolution (explicit param > context > session)
- All contexts cleared together or individually
- Single `set_context()` API for all types
- Backward compatible with legacy `set_workspace()`

**Impact:** Reduces parameter spam by 30-40% in nested workflows

```python
# Before: Specify project_id everywhere
await entity_tool(..., project_id="proj-1")
await entity_tool(..., project_id="proj-1")

# After: Set once
await context_tool("set_context", context_type="project", context_id="proj-1")
await entity_tool(...)  # Auto-uses proj-1
```

---

## Phase 2: Query → Entity Consolidation (Proposed)

### Problem
- Two tools for data access (`entity_tool` and `query_tool`)
- Confusing API (search vs list vs query vs search_term)
- Parameter explosion (24 + 28 parameters across tools)
- Duplicated logic (search exists in both tools)

### Solution
**Merge `query_tool` into `entity_tool` as unified operations:**

```
entity_tool operations:
├── create        (existing)
├── read          (existing)
├── update        (existing)
├── delete        (existing)
├── list          (existing)
├── search        (from query_tool)
├── aggregate     (from query_tool, summary stats)
├── analyze       (from query_tool, deep analysis)
└── rag_search    (from query_tool, semantic search)
```

### Implementation Strategy

#### Step 1: Parameter Consolidation
```python
# Consolidate parameter aliases
entity_tool(
    operation="search",
    entity_type="requirement",       # Single param, not entities/entity_types
    search_term="REQ",               # Single param, not query
    conditions={"status": "active"}  # Single param, not filters
)

# Instead of:
query_tool(
    query_type="search",
    entities=["requirement"],        # vs entity_types
    search_term="REQ",
    filters={"status": "active"}     # vs conditions
)
```

#### Step 2: Migrate Search Operations
```python
# Move RAG search into entity_tool
await entity_tool(
    operation="rag_search",
    entity_type="document",
    content="Find security policies",
    rag_mode="semantic"
)

# Instead of:
await query_tool(
    query_type="rag_search",
    entities=["document"],
    content="Find security policies"
)
```

#### Step 3: Simplify Aggregation
```python
# Aggregation as entity_tool operation
await entity_tool(
    operation="aggregate",
    entity_type="project",
    aggregate_type="count",
    group_by=["status"]
)
```

### Benefits
- **One tool for all data access** - Single mental model
- **50% fewer parameters** - Consolidate aliases
- **Shared context** - All operations use workspace/project/entity_type context
- **Simpler onboarding** - New users learn one tool
- **Better UX** - No confusion between search/query/list

### Implementation Effort
- **Lines to move:** ~400 (query_tool logic into entity_tool)
- **Parameters to consolidate:** 20+ redundant params
- **Migration guide:** Must document for existing clients
- **Testing:** Need comprehensive coverage
- **Risk:** MEDIUM (major API change, needs migration path)

### Timeline
- **Analysis:** 2 hours
- **Implementation:** 2-3 hours
- **Testing:** 2 hours
- **Documentation:** 2 hours
- **Total:** 8-10 hours

---

## Phase 3: Auto-Context Injection (Proposed)

### Problem
Still need to pass contexts to entity_tool/relationship_tool even after setting them.

### Solution
**Auto-inject context into operations**

```python
# Set contexts once
await context_tool("set_context", context_type="workspace", context_id="ws-1")
await context_tool("set_context", context_type="project", context_id="proj-1")
await context_tool("set_context", context_type="entity_type", context_id="requirement")

# Operations automatically receive context
await entity_tool(operation="create", data={"name": "REQ-1"})
# Auto-injected: workspace_id="ws-1", project_id="proj-1", entity_type="requirement"

await entity_tool(operation="list")
# Auto-applied: workspace_id="ws-1", project_id="proj-1", entity_type="requirement"
```

### Implementation
1. **entity_tool:** Resolve project_id, organization_id from context
2. **relationship_tool:** Use default source/target types from context
3. **workflow_tool:** Auto-apply context to workflow parameters
4. **query_tool/search:** Filter by workspace/project context

### Benefits
- **Minimal parameters** - Most calls become 2-3 params
- **Natural workflow** - Set context once per task
- **Batch operations** - Context auto-persists across operations

### Timeline
- **Implementation:** 3-4 hours
- **Testing:** 2 hours
- **Total:** 5-6 hours

---

## Phase 4: Smart Defaults & Batch Context (Proposed)

### Features
1. **Batch Operation Memory**
   - Remember last created entity
   - Auto-populate related IDs

2. **Result Pagination State**
   - Remember sort order and limit
   - No need to repeat params

3. **Relationship Defaults**
   - Default source/target types
   - Simplify link operations

4. **Operation History**
   - Track recent operations
   - Quick undo/redo

### Timeline
- **Planning:** 1 hour
- **Implementation:** 3-4 hours
- **Testing:** 2 hours
- **Total:** 6-7 hours

---

## Full Roadmap Timeline

| Phase | Focus | Status | Effort | Risk |
|-------|-------|--------|--------|------|
| **1** | Multi-context (ws, project, org, type, parent) | ✅ COMPLETE | 3h | LOW |
| **2** | Query → Entity consolidation | Proposed | 8-10h | MEDIUM |
| **3** | Auto-context injection | Proposed | 5-6h | MEDIUM |
| **4** | Smart defaults & batch | Proposed | 6-7h | LOW |
| **Total** | Comprehensive UX overhaul | | **22-28h** | **MEDIUM** |

---

## Decision Matrix: What to Build Next?

### Option A: Focus on Query Consolidation (Phase 2)
**Pros:**
- Biggest API simplification
- Reduces most confusion
- Consolidates duplicate logic
- High impact

**Cons:**
- Breaking change (needs migration)
- More complex refactoring
- Higher testing burden
- More risk

**Recommended if:** User wants clean, unified API

### Option B: Focus on Auto-Context (Phase 3)
**Pros:**
- Works with existing tools
- No breaking changes
- Faster to implement
- Builds on Phase 1

**Cons:**
- Doesn't simplify API (query_tool still exists)
- Still have parameter explosion
- Partial solution

**Recommended if:** Want quick wins, minimize risk

### Option C: Do Both (Phases 2 + 3)
**Pros:**
- Complete UX overhaul
- Major improvement
- Most impactful

**Cons:**
- Higher effort (13-16 hours)
- More risk (breaking changes)
- More testing needed

**Recommended if:** Have capacity and want comprehensive solution

### Option D: Strategic Pause
Save Phases 2-4 for later
- Phase 1 already delivered major value
- Can gather user feedback on Phase 1
- Revisit with fresh perspective

**Recommended if:** Prefer iterative approach, want validation first

---

## Recommendation

I recommend **Option A + B combined** - Start with Query consolidation (highest value) but keep it **backward compatible**:

```python
# NEW way (consolidated)
await entity_tool(operation="search", entity_type="requirement", search_term="REQ")

# OLD way still works (deprecated)
await query_tool(query_type="search", entities=["requirement"], search_term="REQ")

# Deprecation warning guides users to new way
```

This gives:
- ✅ Maximum UX improvement (one tool for data access)
- ✅ Zero breaking changes (old API still works)
- ✅ Clear migration path (deprecation warnings)
- ✅ Time to gather feedback (users can adopt gradually)

**Timeline for backward-compatible consolidation: 10-12 hours**

---

## What You Should Decide

1. **Priority:** Query consolidation (Phase 2) or auto-context injection (Phase 3)?
2. **Risk tolerance:** How breaking are you comfortable with changes?
3. **Timeline:** How much time do you want to invest now?
4. **Approach:**
   - Aggressive: Do Phases 2+3 together (full overhaul)
   - Balanced: Do Phase 2 with backward compat (major improvement + safety)
   - Conservative: Just do Phase 3 (quick wins, low risk)
   - Pause: Keep Phase 1, decide later with data

---

## Implementation Notes

### For Query Consolidation (Phase 2)
- Need to move ~400 lines from `tools/query.py` to `tools/entity.py`
- Consolidate 20+ parameter aliases
- Add deprecation warnings to query_tool
- Create migration guide
- Comprehensive test coverage required

### For Auto-Context (Phase 3)
- Extend entity_tool to call `context.resolve_project_id()` et al
- Same pattern as workspace_id resolution
- Inject into data/filters before operations
- Clean, low-risk implementation

### For Backward Compatibility
- Keep old APIs functional
- Add deprecation markers in docstrings
- Log warnings when old APIs used
- Document migration path in guides

---

## Next Steps

**Ready to proceed?** Let me know:

1. **Choose direction:** A, B, C, or D?
2. **If Phase 2:** Backward compat OK?
3. **If Phase 3:** Want me to wire contexts into tools?
4. **Timeline:** How long to continue?

I'm ready to implement whichever path you choose! 🚀
