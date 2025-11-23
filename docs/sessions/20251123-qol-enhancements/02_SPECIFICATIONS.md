# Specifications: QOL Enhancements & Tool Consolidation

## ARUs (Assumptions, Risks, Uncertainties)

### Assumptions
- SessionContext pattern (3-level resolution) is proven and scalable
- Backwards compatibility is critical (no breaking changes)
- Query operations can be cleanly merged into entity_tool
- Parameter consolidation won't break existing clients

### Risks
- **Parameter explosion**: Adding more context types could exceed 500-line limit
- **Backwards compatibility**: Old clients using query_tool might break
- **Performance**: Context resolution adds overhead (mitigated by caching)
- **Complexity**: Consolidation increases entity_tool complexity

### Uncertainties
- How many clients use query_tool directly?
- Will consolidation improve or hurt performance?
- Should we deprecate query_tool or keep it indefinitely?

## Feature Specifications

### 1. Extended SessionContext
**Requirement**: System SHALL support project_id, document_id, parent_id, entity_type context

**Scenario: Set project context**
- GIVEN: User has workspace context set
- WHEN: User calls `context_tool("set_context", context_type="project", entity_id="proj-1")`
- THEN: Project context is stored in session and auto-applied to entity operations

### 2. Query→Entity Consolidation
**Requirement**: System SHALL support search/aggregate/analyze as entity_tool operations

**Scenario: Search via entity_tool**
- GIVEN: User wants to search projects
- WHEN: User calls `entity_tool(operation="search", entity_type="project", search_query="test")`
- THEN: Results match query_tool search results

### 3. Parameter Consolidation
**Requirement**: System SHALL accept both old and new parameter names

**Scenario: Backwards compatibility**
- GIVEN: Old client uses `entities=["project"]`
- WHEN: Client calls query_tool with old parameter
- THEN: System accepts it and logs deprecation warning

## Implementation Constraints
- **File size**: Keep entity_tool ≤ 500 lines (target ≤ 350)
- **Backwards compatibility**: 100% (no breaking changes)
- **Test coverage**: Maintain 100%
- **Performance**: No regression in response times

