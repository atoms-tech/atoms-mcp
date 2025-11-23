# Research: QOL Enhancements & Tool Consolidation

## Current Architecture Analysis

### SessionContext Implementation (Existing)
- **Location**: `services/context_manager.py`
- **Pattern**: 3-level resolution (explicit param → context vars → session storage)
- **Storage**: Supabase `mcp_sessions.mcp_state` dict
- **Thread-safe**: Uses Python `contextvars`
- **Methods**: `set_workspace_id()`, `get_workspace_id()`, `resolve_workspace_id()`

### Tool Parameter Analysis
**entity_tool** (24 parameters):
- CRUD: operation, entity_type, entity_id, data, filters
- Pagination: limit, offset, pagination, filter_list, sort_list
- Relationships: include_relations, parent_type, parent_id
- Batch: batch, entity_ids, bulk operations
- Advanced: search_term, order_by, format_type, version, workflow_id
- Context: workspace_id (NEW)

**query_tool** (28 parameters):
- Query: query_type, entities, conditions, projections, search_term
- RAG: rag_mode, similarity_threshold, content, entity_type, exclude_id
- Weights: keyword_weight, semantic_weight
- Sort: sort, limit, format_type

### Consolidation Opportunities
1. **Duplicate search logic**: Both entity_tool (search_term) and query_tool (search)
2. **Parameter aliases**: entities vs entity_types, conditions vs filters
3. **Separate tools**: query_tool could be operations in entity_tool
4. **Context missing**: No project_id, document_id, entity_type context

## Implementation Strategy

### Phase 1: Context Extension
Extend SessionContext to support:
- `project_id` - Current project context
- `document_id` - Current document context
- `parent_id` - Current parent entity
- `entity_type` - Current entity type focus
- `pagination_state` - Remember sort/limit preferences

### Phase 2: Query Consolidation
Move query_tool operations to entity_tool:
- `operation="search"` (from query_type="search")
- `operation="aggregate"` (from query_type="aggregate")
- `operation="analyze"` (from query_type="analyze")
- `operation="rag_search"` (from query_type="rag_search")
- `operation="similarity"` (from query_type="similarity")

### Phase 3: Parameter Consolidation
Normalize parameter names:
- `entities` → `entity_types` (with backwards compat alias)
- `conditions` → `filters` (with backwards compat alias)
- `search_term` → `search_query` (with backwards compat alias)

## Backwards Compatibility
- Keep query_tool as deprecated wrapper around entity_tool
- Support both old and new parameter names
- Add deprecation warnings in logs
- Provide migration guide for clients

## Testing Strategy
- Unit tests for each context type
- Integration tests for context resolution
- E2E tests for consolidated operations
- Backwards compatibility tests
- Performance tests (parameter reduction impact)

