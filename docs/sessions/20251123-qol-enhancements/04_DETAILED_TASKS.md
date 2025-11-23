# Detailed Task Breakdown

## Phase 1: Extended SessionContext (2 days)

### 1.1 Extend SessionContext class
- [ ] Add `project_id`, `document_id`, `parent_id`, `entity_type` context vars
- [ ] Add `set_context(context_type, entity_id)` method
- [ ] Add `get_context(context_type)` method
- [ ] Add `resolve_context(context_type)` method (3-level resolution)
- [ ] Add session persistence for new context types
- **Acceptance**: All context types resolve correctly through 3 levels

### 1.2 Extend context_tool
- [ ] Add operations: "set_project", "get_project", "set_document", "get_document"
- [ ] Add operations: "set_entity_type", "get_entity_type"
- [ ] Add "get_full_context" operation (debug)
- **Acceptance**: All operations work and persist to session

### 1.3 Integrate context into entity_tool
- [ ] Auto-apply project_id from context if not provided
- [ ] Auto-apply document_id from context if not provided
- [ ] Auto-apply parent_id from context if not provided
- **Acceptance**: entity_tool uses context automatically

### 1.4 Write Phase 1 tests
- [ ] Unit tests for SessionContext extensions
- [ ] Integration tests for context resolution
- [ ] E2E tests for entity_tool with context
- **Acceptance**: 100% test coverage, all tests pass

## Phase 2: Query→Entity Consolidation (3 days)

### 2.1 Add search operation to entity_tool
- [ ] Implement "search" operation
- [ ] Reuse query_engine._search_query
- [ ] Support search_query parameter
- **Acceptance**: search results match query_tool

### 2.2 Add aggregate/analyze operations
- [ ] Implement "aggregate" operation
- [ ] Implement "analyze" operation
- [ ] Implement "rag_search" operation
- **Acceptance**: Results match query_tool

### 2.3 Parameter consolidation
- [ ] Accept both `entities` and `entity_types`
- [ ] Accept both `conditions` and `filters`
- [ ] Log deprecation warnings
- **Acceptance**: Old and new names both work

### 2.4 Write Phase 2 tests
- [ ] Backwards compatibility tests
- [ ] Consolidated operation tests
- [ ] Parameter alias tests
- **Acceptance**: 100% coverage, all tests pass

## Phase 3: Smart Defaults (2 days)

### 3.1 Batch context
- [ ] Remember last created entity IDs
- [ ] Auto-link in subsequent operations
- **Acceptance**: Batch operations work seamlessly

### 3.2 Pagination state
- [ ] Remember sort/limit preferences
- [ ] Auto-apply to list operations
- **Acceptance**: Pagination state persists

### 3.3 Write Phase 3 tests
- [ ] Batch context tests
- [ ] Pagination state tests
- **Acceptance**: 100% coverage

## Phase 4: Error Suggestions (1 day)

### 4.1 Fuzzy matching
- [ ] Add fuzzy matching for invalid IDs
- [ ] Suggest similar entity names
- **Acceptance**: Suggestions are helpful

### 4.2 Operation history
- [ ] Track recent operations
- [ ] Support undo operation
- **Acceptance**: History works correctly

## Phase 5: Testing & Verification (2 days)

### 5.1 Full test suite
- [ ] Run all unit tests
- [ ] Run all integration tests
- [ ] Run all E2E tests
- **Acceptance**: 100% pass rate

### 5.2 Backwards compatibility
- [ ] Test old query_tool calls
- [ ] Test old parameter names
- [ ] Test old clients
- **Acceptance**: No breaking changes

### 5.3 Performance verification
- [ ] Measure context resolution overhead
- [ ] Measure consolidation impact
- **Acceptance**: No performance regression

