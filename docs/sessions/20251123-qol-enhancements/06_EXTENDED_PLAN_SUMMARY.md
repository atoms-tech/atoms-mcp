# Extended Plan Summary: QOL Enhancements & Tool Consolidation

## Executive Summary

This session extends the MCP tool architecture with **5 major QOL improvements**:

1. **Project/Document Context** - Reduce parameter spam by 47%
2. **Query→Entity Consolidation** - Unify data access into single tool
3. **Parameter Consolidation** - Consistent naming across tools
4. **Smart Defaults** - Auto-populate context-aware values
5. **Error Suggestions** - Fuzzy matching and operation history

## Roadmap (10 days)

### Phase 1: Extended SessionContext (2 days)
- Extend SessionContext with project_id, document_id, parent_id, entity_type
- Extend context_tool with new operations
- Integrate context into entity_tool
- Write comprehensive tests

**Deliverable**: Project/document context working end-to-end

### Phase 2: Query→Entity Consolidation (3 days)
- Add search/aggregate/analyze/rag_search operations to entity_tool
- Consolidate parameter naming (entities→entity_types, conditions→filters)
- Keep query_tool as deprecated wrapper
- Write backwards compatibility tests

**Deliverable**: Unified entity_tool with all query operations

### Phase 3: Smart Defaults & Batch Context (2 days)
- Add batch context (remember last created IDs)
- Add pagination state tracking
- Add relationship context defaults
- Write tests

**Deliverable**: Smart defaults working in nested workflows

### Phase 4: Error Suggestions & History (1 day)
- Add fuzzy matching for invalid IDs
- Add operation history tracking
- Add undo capability
- Write tests

**Deliverable**: Error suggestions and operation history working

### Phase 5: Full Testing & Verification (2 days)
- Run complete test suite
- Verify backwards compatibility
- Performance verification
- Documentation updates

**Deliverable**: 100% test pass rate, zero breaking changes

## Key Improvements

### Parameter Reduction
- Nested workflows: 15+ → 8 parameters (-47%)
- Context auto-injection: workspace, project, document, parent_id
- Smart defaults: pagination, entity_type, relationship context

### API Simplification
- 2 tools (entity + query) → 1 unified tool
- Consistent parameter naming
- Shared context across all operations

### Developer Experience
- Fewer parameters to remember
- Clearer mental model (one tool = all entity operations)
- Better error messages with suggestions
- Operation history for debugging

## Success Criteria
- ✅ 100% test pass rate
- ✅ Zero breaking changes (backwards compatible)
- ✅ 47% parameter reduction in nested workflows
- ✅ All context types working (workspace, project, document, entity_type)
- ✅ Query operations merged into entity_tool
- ✅ Parameter consolidation complete
- ✅ Smart defaults implemented
- ✅ Error suggestions working
- ✅ Operation history tracking

## Risk Mitigation
- **Backwards compatibility**: Keep query_tool as wrapper, support old parameter names
- **File size**: Decompose if entity_tool exceeds 350 lines
- **Performance**: Cache context resolution, measure overhead
- **Complexity**: Clear documentation and migration guide

## Next Steps
1. Review and approve extended plan
2. Start Phase 1: Extended SessionContext
3. Follow task breakdown in `04_DETAILED_TASKS.md`
4. Update task list as phases complete

