# Query Tool Migration Guide

**Status:** query_tool is deprecated and being consolidated into entity_tool.

## Timeline

| Version | Status | Action |
|---------|--------|--------|
| **v1.x** (current) | Available with warnings | Migrate at your convenience |
| **v2.x** | Still works but discouraged | Migration strongly recommended |
| **v3.x** | **REMOVED** | Must use entity_tool |

## Why Consolidate?

**Problems with current approach:**
- Two separate tools for data operations (query_tool + entity_tool)
- Duplicated parameters and functionality
- Confusing API - users unsure which tool to use
- Parameter naming inconsistencies (entities vs entity_type, conditions vs filters)

**Benefits of consolidation:**
- ✅ Single unified API for all data operations
- ✅ 30-40% fewer parameters needed
- ✅ Consistent naming across the system
- ✅ Easier to add new features
- ✅ Better context auto-injection support
- ✅ Cleaner documentation

## Migration Mapping

### Basic Search Operations

#### Old: query_tool (search)
```python
# Search across multiple entity types
await query_tool(
    query_type="search",
    entities=["project", "requirement", "document"],
    search_term="api design",
    conditions={"workspace_id": "ws-123"},
    limit=20
)
```

#### New: entity_tool (search - one per entity type)
```python
# For each entity type, use entity_tool with search operation
await entity_tool(
    entity_type="project",
    operation="search",
    search_term="api design",
    filters={"workspace_id": "ws-123"},
    limit=20
)
```

**Better approach with context:**
```python
# Set context once
await context_tool("set_context", context_type="workspace", context_id="ws-123")

# Now operations auto-filter by workspace
await entity_tool(
    entity_type="project",
    operation="search",
    search_term="api design",
    limit=20
)
```

---

### Semantic/Keyword/Hybrid Search

#### Old: query_tool (variants)
```python
# Semantic search
await query_tool(
    query_type="semantic_search",
    entity_types=["requirement"],
    search_term="user authentication",
    rag_mode="semantic"
)

# Keyword search
await query_tool(
    query_type="keyword_search",
    entity_types=["document"],
    search_term="security policy"
)

# Hybrid search
await query_tool(
    query_type="hybrid_search",
    entity_types=["requirement"],
    search_term="performance optimization",
    keyword_weight=0.6,
    semantic_weight=0.4
)
```

#### New: entity_tool (unified rag_search)
```python
# RAG search with automatic mode selection
await entity_tool(
    entity_type="requirement",
    operation="rag_search",
    content="user authentication flow",
    rag_mode="auto"  # auto, semantic, keyword, hybrid
)

# Keyword-focused RAG search
await entity_tool(
    entity_type="document",
    operation="rag_search",
    content="security policy",
    rag_mode="keyword"
)

# Semantic search with threshold
await entity_tool(
    entity_type="requirement",
    operation="rag_search",
    content="performance optimization",
    rag_mode="semantic",
    similarity_threshold=0.75
)
```

---

### Similarity Search

#### Old: query_tool
```python
await query_tool(
    query_type="similarity",
    content="Login system requirements",
    entity_type="requirement",
    similarity_threshold=0.7,
    limit=10
)
```

#### New: entity_tool
```python
await entity_tool(
    entity_type="requirement",
    operation="similarity",
    content="Login system requirements",
    similarity_threshold=0.7,
    limit=10
)
```

---

### Aggregation / Statistics

#### Old: query_tool
```python
# Get counts for multiple entity types
await query_tool(
    query_type="aggregate",
    entities=["project", "requirement", "document"],
    aggregate_type="count"
)

# Get grouped counts
await query_tool(
    query_type="aggregate",
    entities=["requirement"],
    aggregate_type="count",
    group_by=["status", "priority"]
)
```

#### New: entity_tool
```python
# Count projects
await entity_tool(
    entity_type="project",
    operation="aggregate",
    aggregate_type="count"
)

# Count requirements by status
await entity_tool(
    entity_type="requirement",
    operation="aggregate",
    aggregate_type="count",
    group_by=["status"]
)

# Count requirements by multiple fields
await entity_tool(
    entity_type="requirement",
    operation="aggregate",
    aggregate_type="count",
    group_by=["status", "priority"]
)
```

---

### Analysis with Relationships

#### Old: query_tool
```python
await query_tool(
    query_type="analyze",
    entities=["requirement"],
    conditions={"status": "active"}
)
```

#### New: entity_tool
```python
await entity_tool(
    entity_type="requirement",
    operation="analyze",
    filters={"status": "active"},
    include_relations=True  # Include relationship analysis
)
```

---

## Parameter Mapping Reference

| Old (query_tool) | New (entity_tool) | Notes |
|------------------|-------------------|-------|
| `query_type` | `operation` | See mapping table below |
| `entities` | `entity_type` | Single type per call (iterate if multiple) |
| `entity_types` | `entity_type` | Use first value or iterate |
| `conditions` | `filters` | Identical structure |
| `search_term` | `search_term` | Same in search/rag_search ops |
| `aggregate_type` | `aggregate_type` | Same in aggregate operation |
| `group_by` | `group_by` | Same in aggregate operation |
| `content` | `content` | Same in rag_search/similarity ops |
| `rag_mode` | `rag_mode` | Same for RAG operations |
| `similarity_threshold` | `similarity_threshold` | Same for similarity ops |
| `format_type` | `format_type` | Same output format control |

---

## Operation Type Mapping

| Old query_type | New operation | Notes |
|---|---|---|
| `search` | `search` | Basic text search |
| `keyword_search` | `rag_search` | Set `rag_mode="keyword"` |
| `semantic_search` | `rag_search` | Set `rag_mode="semantic"` |
| `hybrid_search` | `rag_search` | Set `rag_mode="hybrid"` |
| `rag_search` | `rag_search` | Direct mapping |
| `similarity` | `similarity` | Direct mapping |
| `aggregate` | `aggregate` | Direct mapping |
| `analyze` | `analyze` | Direct mapping |
| `relationships` | `analyze` | Use with `include_relations=True` |

---

## Context Integration (New Capability)

The consolidated entity_tool supports automatic context injection. You no longer need to pass workspace_id repeatedly.

### Old Way (query_tool)
```python
await query_tool(
    query_type="search",
    entities=["project"],
    search_term="dashboard",
    conditions={"workspace_id": "ws-123", "status": "active"}
)

# Every call needs workspace_id
await query_tool(
    query_type="search",
    entities=["requirement"],
    search_term="ui",
    conditions={"workspace_id": "ws-123"}
)
```

### New Way (entity_tool + context)
```python
# Set context once
await context_tool("set_context", context_type="workspace", context_id="ws-123")

# Now all operations auto-filter by workspace - no need to repeat it
await entity_tool(
    entity_type="project",
    operation="search",
    search_term="dashboard",
    filters={"status": "active"}
)

await entity_tool(
    entity_type="requirement",
    operation="search",
    search_term="ui"
)
```

**Benefits:**
- Fewer parameters per call
- Consistent filtering across operations
- Context persists across requests

---

## Examples: Step-by-Step Migration

### Example 1: Dashboard Requirements Search

**Old Code (v1.x)**
```python
# Search multiple entity types for "dashboard"
results = await query_tool(
    query_type="search",
    entities=["project", "requirement", "document"],
    search_term="dashboard",
    conditions={"workspace_id": "ws-prod", "environment": "production"},
    limit=50,
    format_type="summary"
)
```

**Migrated Code (v2.x+)**
```python
# Approach 1: Use context (recommended)
await context_tool("set_context", context_type="workspace", context_id="ws-prod")

# Search each entity type as needed
project_results = await entity_tool(
    entity_type="project",
    operation="search",
    search_term="dashboard",
    filters={"environment": "production"},
    limit=50,
    format_type="summary"
)

requirement_results = await entity_tool(
    entity_type="requirement",
    operation="search",
    search_term="dashboard",
    filters={"environment": "production"},
    limit=50,
    format_type="summary"
)

document_results = await entity_tool(
    entity_type="document",
    operation="search",
    search_term="dashboard",
    filters={"environment": "production"},
    limit=50,
    format_type="summary"
)

# Combine results as needed
all_results = {
    "projects": project_results["results"],
    "requirements": requirement_results["results"],
    "documents": document_results["results"]
}
```

---

### Example 2: Statistics Dashboard

**Old Code (v1.x)**
```python
# Get project count
stats = await query_tool(
    query_type="aggregate",
    entities=["project"],
    aggregate_type="count",
    conditions={"workspace_id": "ws-prod"}
)

project_count = stats["total_count"]

# Get requirement stats by status
req_stats = await query_tool(
    query_type="aggregate",
    entities=["requirement"],
    aggregate_type="count",
    group_by=["status"],
    conditions={"workspace_id": "ws-prod"}
)
```

**Migrated Code (v2.x+)**
```python
# Set context once
await context_tool("set_context", context_type="workspace", context_id="ws-prod")

# Get project count
project_stats = await entity_tool(
    entity_type="project",
    operation="aggregate",
    aggregate_type="count"
)
project_count = project_stats["total_count"]

# Get requirement stats by status
req_stats = await entity_tool(
    entity_type="requirement",
    operation="aggregate",
    aggregate_type="count",
    group_by=["status"]
)
```

---

### Example 3: AI-Powered Search

**Old Code (v1.x)**
```python
# Semantic search for architecture requirements
results = await query_tool(
    query_type="semantic_search",
    entity_types=["requirement"],
    search_term="microservices architecture patterns",
    conditions={"workspace_id": "ws-prod", "status": "active"},
    rag_mode="semantic"
)
```

**Migrated Code (v2.x+)**
```python
# Set workspace context
await context_tool("set_context", context_type="workspace", context_id="ws-prod")

# Use RAG search with semantic mode
results = await entity_tool(
    entity_type="requirement",
    operation="rag_search",
    content="microservices architecture patterns",
    rag_mode="semantic",
    filters={"status": "active"}
)
```

---

## Common Pitfalls & Solutions

### Pitfall 1: Passing Multiple Entity Types

**❌ Won't work in entity_tool:**
```python
# This won't work - entity_type is a single string
await entity_tool(
    entity_type=["project", "requirement"],  # ERROR: must be string
    operation="search"
)
```

**✅ Correct approach:**
```python
# Call entity_tool once per entity type
for entity_type in ["project", "requirement"]:
    result = await entity_tool(
        entity_type=entity_type,
        operation="search",
        search_term="...
    )
```

### Pitfall 2: Forgetting Parameter Name Changes

**❌ Old parameter names won't work:**
```python
await entity_tool(
    entity_type="requirement",
    operation="search",
    conditions={"status": "active"}  # ERROR: should be 'filters'
)
```

**✅ Use new names:**
```python
await entity_tool(
    entity_type="requirement",
    operation="search",
    filters={"status": "active"}  # ✓ Correct
)
```

### Pitfall 3: Forgetting to Migrate query_type to operation

**❌ Old way won't work:**
```python
await entity_tool(
    entity_type="project",
    query_type="search",  # ERROR: should be 'operation'
    search_term="..."
)
```

**✅ Correct way:**
```python
await entity_tool(
    entity_type="project",
    operation="search",
    search_term="..."
)
```

---

## Testing Your Migration

### Quick Checklist

Before deploying your migrated code:

- [ ] Update all `query_tool` calls to `entity_tool`
- [ ] Change `query_type` to `operation`
- [ ] Change `entities` to `entity_type` (single value)
- [ ] Change `conditions` to `filters`
- [ ] Update RAG search modes (keyword_search → rag_search with rag_mode)
- [ ] Test aggregate operations with new parameter names
- [ ] Verify results match old output (accounting for format changes)
- [ ] Remove any workspace_id from filters if using context injection
- [ ] Run all integration tests

### Integration Testing Example

```python
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_migration_search():
    """Verify migrated search works identically."""
    
    # Set context
    await context_tool("set_context", context_type="workspace", context_id="test-ws")
    
    # Old way (for comparison)
    old_result = await query_tool(
        query_type="search",
        entities=["requirement"],
        search_term="api",
        conditions={"workspace_id": "test-ws"}
    )
    
    # New way
    new_result = await entity_tool(
        entity_type="requirement",
        operation="search",
        search_term="api"
        # workspace auto-injected from context
    )
    
    # Verify results are equivalent
    assert old_result["success"] == new_result["success"]
    assert len(old_result["results"]) == len(new_result["results"])
```

---

## FAQ

**Q: Will my old query_tool calls break?**
A: No, query_tool will continue to work through v2.x with deprecation warnings. Plan migration before v3.x.

**Q: Should I migrate all calls at once?**
A: No, migrate gradually. entity_tool works alongside query_tool. You can transition per-feature.

**Q: How does context injection work?**
A: Once you call `context_tool("set_context", ...)`, that context persists for all subsequent operations in that session. No need to pass it in filters each time.

**Q: What about performance?**
A: entity_tool is more efficient (unified code path). No performance regression expected.

**Q: Will deprecation warnings appear in logs?**
A: Yes, one warning per query_tool call to `logger.warning()`. Use log level filtering if needed.

**Q: Can I use both tools in same project?**
A: Yes, but plan complete migration before v3.x.

---

## Support

**Need help?**
- Review examples above for your use case
- Check the CLAUDE.md and AGENTS.md for architecture context
- Raise an issue if migration blocker found
- Ask team for guidance on approach

**Timeline Questions?**
- Current stable (v1.x): query_tool works with warnings
- Next major (v2.x): Still functional but strongly discouraged
- Future (v3.x): Removed entirely

Start migration now to be ahead of the curve! 🚀
