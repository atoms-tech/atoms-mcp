# Prompts & Resources Analysis: What We Have & What We Can Expose

## Current State: What's Available

### ✅ Currently Exposed
1. **5 Consolidated Tools** (via @mcp.tool decorators)
   - context_tool
   - entity_tool
   - relationship_tool
   - workflow_tool
   - query_tool
   - health_check

2. **Server Instructions** (in FastMCP initialization)
   ```
   "Atoms MCP server with consolidated, agent-optimized tools. 
    Authenticate via OAuth (AuthKit). 
    Use workspace_tool to manage context, entity_tool for CRUD, 
    relationship_tool for associations, workflow_tool for complex tasks, 
    and query_tool for data exploration including RAG search."
   ```

3. **OAuth Metadata Endpoints**
   - `/.well-known/oauth-protected-resource`
   - `/.well-known/oauth-authorization-server`

### ❌ Currently NOT Exposed
1. **Prompts** - No MCP prompts defined
2. **Resources** - No MCP resources exposed
3. **Documentation** - No structured resources for guides
4. **Schemas** - No schema resources exposed
5. **Examples** - No example workflows or templates
6. **Configuration** - No config resources

## MCP Prompts & Resources Overview

### What Are MCP Prompts?
- **Purpose**: Pre-written instructions for agents to use
- **Use Case**: "How to use this tool", "Best practices", "Common workflows"
- **Format**: Markdown text with optional arguments
- **Example**:
  ```python
  @mcp.prompt()
  def entity_creation_guide(entity_type: str = "project"):
      """Guide for creating entities of a specific type."""
      return f"To create a {entity_type}..."
  ```

### What Are MCP Resources?
- **Purpose**: Expose data/files that agents can read
- **Use Case**: Documentation, schemas, examples, templates
- **Format**: Text, JSON, or binary data
- **Example**:
  ```python
  @mcp.resource("file:///schemas/project.json")
  def get_project_schema():
      """Project entity schema."""
      return {...}
  ```

## Opportunities: 18 Prompts & Resources to Expose

### TIER 1: High Value Prompts (6 items)

1. **entity_creation_guide** - How to create entities
2. **entity_search_guide** - How to search entities
3. **relationship_guide** - How to link entities
4. **workflow_guide** - How to execute workflows
5. **context_guide** - How to use context management
6. **error_recovery_guide** - How to handle errors

### TIER 2: High Value Resources (6 items)

7. **entity_types_reference** - All 20 entity types with fields
8. **operation_reference** - All operations per tool
9. **workflow_templates** - Pre-built workflow examples
10. **schema_definitions** - JSON schemas for all entities
11. **best_practices** - Agent best practices guide
12. **api_reference** - Complete API documentation

### TIER 3: Advanced Prompts (3 items)

13. **advanced_search_guide** - RAG, semantic, hybrid search
14. **bulk_operations_guide** - Batch operations best practices
15. **performance_guide** - Optimization tips

### TIER 4: Advanced Resources (3 items)

16. **performance_benchmarks** - Latency/throughput data
17. **troubleshooting_guide** - Common issues & solutions
18. **migration_guide** - Upgrade path documentation

## Recommended Implementation

### Phase 1: Essential Prompts & Resources (1 week)

**Prompts** (6 items):
- entity_creation_guide
- entity_search_guide
- relationship_guide
- workflow_guide
- context_guide
- error_recovery_guide

**Resources** (6 items):
- entity_types_reference
- operation_reference
- workflow_templates
- schema_definitions
- best_practices
- api_reference

### Phase 2: Advanced Features (1 week)

**Prompts** (3 items):
- advanced_search_guide
- bulk_operations_guide
- performance_guide

**Resources** (3 items):
- performance_benchmarks
- troubleshooting_guide
- migration_guide

## Implementation Strategy

### Prompts Pattern
```python
@mcp.prompt()
def entity_creation_guide(entity_type: str = "project"):
    """Guide for creating entities."""
    return f"""
# Creating {entity_type} Entities

## Basic Creation
Use entity_tool with operation="create":
```python
entity_tool(
    operation="create",
    entity_type="{entity_type}",
    data={{"name": "My {entity_type}"}}
)
```

## With Context
Set context first to auto-inject workspace/project:
```python
context_tool("set_context", context_type="workspace", entity_id="ws-1")
entity_tool(operation="create", entity_type="{entity_type}", data={...})
```

## Best Practices
- Always set workspace context first
- Use batch_create for multiple entities
- Include required fields in data
"""
```

### Resources Pattern
```python
@mcp.resource("file:///reference/entity_types.json")
def get_entity_types_reference():
    """Reference for all entity types."""
    return {
        "entity_types": [
            {
                "name": "project",
                "description": "A project container",
                "fields": ["name", "description", "status"],
                "operations": ["create", "read", "update", "delete", "list", "search"]
            },
            # ... 19 more entity types
        ]
    }
```

## Benefits

### For Agents
- ✅ Clear guidance on tool usage
- ✅ Best practices built-in
- ✅ Reduced trial-and-error
- ✅ Better error recovery
- ✅ Faster onboarding

### For Developers
- ✅ Self-documenting API
- ✅ Reduced support burden
- ✅ Consistent guidance
- ✅ Easy to update
- ✅ Version-aware

### For System
- ✅ Better tool utilization
- ✅ Fewer errors
- ✅ Faster operations
- ✅ Improved reliability
- ✅ Better observability

## Integration with QOL Plan

### Phase 1 (Month 1)
- Add 6 essential prompts
- Add 6 essential resources
- Update server instructions

### Phase 2 (Month 2)
- Add 3 advanced prompts
- Add 3 advanced resources
- Add deprecation warnings

### Phase 3+ (Months 3-6)
- Keep prompts/resources in sync with new features
- Add prompts for new operations
- Add resources for new capabilities

## Effort Estimate

| Item | Effort | Impact |
|------|--------|--------|
| 6 Essential Prompts | 2 days | High |
| 6 Essential Resources | 2 days | High |
| 3 Advanced Prompts | 1 day | Medium |
| 3 Advanced Resources | 1 day | Medium |
| Integration & Testing | 1 day | High |
| **TOTAL** | **7 days** | **High** |

## Recommendation

**Add to Phase 1 of QOL Plan** (Month 1):
- Implement 6 essential prompts
- Implement 6 essential resources
- Update server instructions
- Add to documentation

**Effort**: 4 days (fits within Phase 1 timeline)
**Impact**: Significantly improves agent experience
**Risk**: Low (non-breaking, additive only)

