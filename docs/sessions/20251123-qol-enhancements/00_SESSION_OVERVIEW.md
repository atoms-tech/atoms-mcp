# QOL Enhancements & Tool Consolidation - Session Overview

## Goals
Extend and enhance the MCP tool architecture with:
1. **Project/Document Context** - Reduce parameter spam in nested workflows
2. **Query→Entity Consolidation** - Merge query_tool into entity_tool for unified API
3. **Smart Defaults** - Auto-populate context-aware defaults
4. **Error Suggestions** - Fuzzy matching for invalid IDs/names
5. **Operation History** - Track and undo operations

## Current State
- ✅ Workspace context implemented (SessionContext, context_tool)
- ✅ 5 consolidated tools (workspace, entity, relationship, workflow, query)
- ✅ Comprehensive test suite (unit, integration, e2e)
- ❌ No project/document context
- ❌ Query operations separate from entity_tool
- ❌ Parameter explosion (24+ params in entity_tool, 28+ in query_tool)

## Scope
**IN SCOPE:**
- Extend SessionContext with project_id, document_id, parent_id, entity_type
- Merge query operations into entity_tool
- Consolidate parameter naming (entities→entity_types, conditions→filters)
- Add batch context and pagination state
- Add error suggestions and operation history

**OUT OF SCOPE:**
- Breaking changes to existing APIs (maintain backwards compatibility)
- New entity types or relationships
- Performance optimization (beyond consolidation)

## Phases
1. **Phase 1** (2 days): Project/document context
2. **Phase 2** (3 days): Query→entity consolidation
3. **Phase 3** (2 days): Smart defaults & batch context
4. **Phase 4** (1 day): Error suggestions & history
5. **Testing** (2 days): Full E2E verification

**Total: 10 days**

## Key Metrics
- Parameter reduction: 30-40% fewer parameters in nested workflows
- API surface: 5 tools → 5 tools (consolidated, not multiplied)
- Test coverage: Maintain 100% coverage
- Backwards compatibility: Full (with deprecation warnings)

