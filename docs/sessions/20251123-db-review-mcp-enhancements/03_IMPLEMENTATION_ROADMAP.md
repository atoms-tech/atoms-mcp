# Implementation Roadmap for MCP Enhancements

## Architecture Pattern (Following Existing QoL Paradigms)

### 1. Tool Consolidation Pattern
**Current**: 5 main tools (workspace, entity, relationship, workflow, query)  
**Enhanced**: Add 4 specialized tools while maintaining consolidation

```
workspace_operation      (context management)
entity_operation         (CRUD + search + analysis)
relationship_operation   (entity relationships)
workflow_execute         (complex workflows)
search_discovery         (NEW - FTS + faceted search)
data_transfer            (NEW - import/export)
permission_control       (NEW - granular access)
workflow_management      (NEW - workflow CRUD)
```

### 2. Parameter Standardization
All new tools follow existing patterns:

```python
async def tool_operation(
    auth_token: str,
    operation: Literal[...],
    entity_type: Optional[str] = None,
    filters: Optional[Dict] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    format_type: str = "detailed",
    workspace_id: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
```

### 3. Response Format Consistency
All tools return:
```python
{
    "success": bool,
    "data": {...},
    "error": str | None,
    "metrics": {"total_ms": int},
    "operation": str,
    "pagination": {"total": int, "limit": int, "offset": int}
}
```

## Implementation Steps

### Step 1: Create Adapter Classes
- `SearchIndexAdapter` - FTS operations
- `ExportImportAdapter` - Job management
- `PermissionAdapter` - Access control
- `WorkflowManagementAdapter` - Workflow CRUD

**Location**: `infrastructure/` directory  
**Pattern**: Follow `WorkflowStorageAdapter` and `AdvancedFeaturesAdapter`

### Step 2: Create Tool Functions
- `search_discovery()` in `tools/search.py`
- `data_transfer()` in `tools/transfer.py`
- `permission_control()` in `tools/permissions.py`
- `workflow_management()` in `tools/workflow_mgmt.py`

**Pattern**: Follow `entity_operation()` signature and error handling

### Step 3: Register with FastMCP
Update `server.py`:
```python
@mcp.tool()
async def search_discovery(...): ...

@mcp.tool()
async def data_transfer(...): ...

@mcp.tool()
async def permission_control(...): ...

@mcp.tool()
async def workflow_management(...): ...
```

### Step 4: Add Prompts & Resources
- Update `tools/prompts.py` with guides for new tools
- Update `tools/resources.py` with operation references
- Add examples for each new operation

### Step 5: Testing & Validation
- Unit tests for each adapter
- Integration tests with database
- E2E tests for tool operations
- Performance benchmarks

## QoL Design Principles Applied

### 1. Smart Defaults
- Auto-detect workspace from context
- Auto-detect entity_type from operation
- Use sensible defaults for pagination (limit=100, offset=0)

### 2. Graceful Degradation
- Fallback to basic search if FTS unavailable
- Continue import on row errors (not full failure)
- Partial permission grants on partial failures

### 3. Comprehensive Error Handling
- Detailed error messages with suggestions
- Error recovery recommendations
- Structured error responses

### 4. Performance Optimization
- Batch operations where possible
- Lazy loading of relationships
- Query result caching
- Index usage for large datasets

### 5. Audit & Observability
- Log all operations with user/timestamp
- Track permission changes
- Monitor job progress
- Metrics on all operations

## Timeline Estimate

| Phase | Tasks | Effort | Timeline |
|-------|-------|--------|----------|
| 1 | Adapters + search_discovery | 8h | 1 day |
| 2 | data_transfer + permission_control | 10h | 1.5 days |
| 3 | workflow_management + integration | 8h | 1 day |
| 4 | Testing + documentation | 12h | 1.5 days |
| **Total** | **All enhancements** | **38h** | **5 days** |

## Success Criteria

✅ All 4 new tools operational  
✅ 100% test coverage for adapters  
✅ Performance benchmarks met (< 200ms per operation)  
✅ Documentation complete with examples  
✅ Backward compatibility maintained  
✅ No breaking changes to existing tools

