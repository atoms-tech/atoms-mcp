# Code Patterns: QOL Enhancements Implementation

## Pattern 1: Extended SessionContext

```python
# services/context_manager.py
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
        
        self._context_vars[context_type].set(entity_id)
        await self._persist_to_session(context_type, entity_id)
    
    async def resolve_context(self, context_type: str) -> Optional[str]:
        """3-level resolution: param → context → session."""
        # 1. Check context vars
        try:
            return self._context_vars[context_type].get()
        except LookupError:
            pass
        
        # 2. Load from session
        return await self._load_from_session(context_type)
```

## Pattern 2: Context Auto-Injection in entity_tool

```python
# tools/entity.py
async def entity_operation(..., project_id=None, document_id=None):
    # Resolve context
    project_id = project_id or await context.resolve_context("project_id")
    document_id = document_id or await context.resolve_context("document_id")
    
    # Auto-inject into data
    if operation == "create":
        if project_id:
            data["project_id"] = project_id
        if document_id:
            data["document_id"] = document_id
```

## Pattern 3: Query Operations in entity_tool

```python
# tools/entity.py
async def entity_operation(operation: str, ...):
    if operation == "search":
        return await _search_operation(entity_types, search_query, filters)
    elif operation == "aggregate":
        return await _aggregate_operation(entity_types, filters)
    elif operation == "analyze":
        return await _analyze_operation(entity_types, filters)
    elif operation == "rag_search":
        return await _rag_search_operation(entity_types, search_query, rag_mode)
```

## Pattern 4: Parameter Consolidation with Backwards Compat

```python
# tools/entity.py
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

## Pattern 5: Batch Context

```python
# services/context_manager.py
class SessionContext:
    async def set_batch_context(self, entity_ids: List[str]):
        """Remember created IDs for auto-linking."""
        self._batch_ids = entity_ids
    
    async def get_batch_context(self) -> List[str]:
        """Get last created IDs."""
        return self._batch_ids or []
```

## Pattern 6: Error Suggestions

```python
# tools/entity.py
async def _suggest_similar_ids(invalid_id: str, entity_type: str):
    """Fuzzy match invalid ID against existing entities."""
    from difflib import get_close_matches
    
    existing = await _get_all_ids(entity_type)
    matches = get_close_matches(invalid_id, existing, n=3, cutoff=0.6)
    
    return {
        "error": f"Entity not found: {invalid_id}",
        "suggestions": matches
    }
```

## Pattern 7: Operation History

```python
# services/context_manager.py
class SessionContext:
    _operation_history = []
    
    async def track_operation(self, operation: Dict):
        """Track operation for undo."""
        self._operation_history.append(operation)
    
    async def undo_last_operation(self):
        """Undo last operation."""
        if not self._operation_history:
            raise ValueError("No operations to undo")
        
        last_op = self._operation_history.pop()
        return await self._reverse_operation(last_op)
```

## Integration Points
- `services/context_manager.py` - Core context logic
- `tools/context.py` - Context tool operations
- `tools/entity.py` - Auto-injection and consolidation
- `tools/query.py` - Deprecation wrapper
- `server.py` - Tool registration (no changes)

