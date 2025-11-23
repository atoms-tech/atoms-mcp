# Implementation Strategy: QOL Enhancements

## Architecture Decisions

### 1. Context Extension Pattern
**Decision**: Extend SessionContext with new context types (project, document, entity_type)
**Rationale**: Proven pattern, minimal risk, consistent with workspace_id
**Implementation**:
```python
# services/context_manager.py
class SessionContext:
    async def set_context(self, context_type: str, entity_id: str)
    async def get_context(self, context_type: str) -> Optional[str]
    async def resolve_context(self, context_type: str) -> Optional[str]
```

### 2. Query Consolidation Approach
**Decision**: Add search/aggregate/analyze as entity_tool operations
**Rationale**: Unified API, shared context, simpler mental model
**Implementation**:
- New operations: "search", "aggregate", "analyze", "rag_search", "similarity"
- Reuse existing query_engine from query_tool
- Keep query_tool as deprecated wrapper

### 3. Parameter Consolidation
**Decision**: Support both old and new names with deprecation warnings
**Rationale**: Backwards compatibility, gradual migration path
**Implementation**:
- Accept `entities` and `entity_types` (prefer new)
- Accept `conditions` and `filters` (prefer new)
- Log deprecation warnings for old names

## File Organization
- `services/context_manager.py` - Extended SessionContext (+50 lines)
- `tools/context.py` - Extended context_tool (+30 lines)
- `tools/entity.py` - Add search/aggregate operations (+100 lines)
- `tools/query.py` - Deprecation wrapper (no changes)
- `server.py` - Register new operations (no changes)

## Decomposition Strategy
If entity_tool exceeds 350 lines:
- Extract search operations → `tools/entity_search.py`
- Extract aggregate operations → `tools/entity_aggregate.py`
- Keep CRUD in `tools/entity.py`

## Testing Strategy
- Unit tests for each context type
- Integration tests for context resolution
- Backwards compatibility tests
- E2E tests for consolidated operations

