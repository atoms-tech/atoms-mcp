# Prompts & Resources Summary: Exposing Guidance & Documentation

## Executive Summary

We can expose **12 high-value MCP prompts and resources** that will significantly improve agent experience and reduce errors. These are currently available in the codebase but not exposed via MCP.

## What We're Exposing

### 6 Essential MCP Prompts (Agent Guides)
1. **entity_creation_guide** - How to create entities
2. **entity_search_guide** - How to search entities
3. **relationship_guide** - How to link entities
4. **workflow_guide** - How to execute workflows
5. **context_guide** - How to use context management
6. **error_recovery_guide** - How to handle errors

### 6 Essential MCP Resources (Documentation)
1. **entity_types_reference** - All 20 entity types with fields
2. **operation_reference** - All operations per tool
3. **workflow_templates** - Pre-built workflow examples
4. **schema_definitions** - JSON schemas for all entities
5. **best_practices** - Agent best practices guide
6. **api_reference** - Complete API documentation

## Why This Matters

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

## Implementation Overview

### File Structure
```
tools/
├── prompts.py          # NEW: 6 MCP prompts
└── resources.py        # NEW: 6 MCP resources

server.py
├── Import prompts & resources
└── Register with @mcp.prompt() and @mcp.resource()
```

### Prompts Pattern
```python
@mcp.prompt()
def entity_creation_guide(entity_type: str = "project"):
    """Guide for creating entities."""
    return f"""
# Creating {entity_type} Entities

## Quick Start
entity_tool(
    operation="create",
    entity_type="{entity_type}",
    data={{"name": "My {entity_type}"}}
)

## With Context
context_tool("set_context", context_type="workspace", entity_id="ws-1")
entity_tool(operation="create", entity_type="{entity_type}", data={{...}})

## Best Practices
1. Always set workspace context first
2. Use batch_create for 3+ entities
3. Include all required fields
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

## Integration with Phase 1

### Timeline
- **Week 1-2**: Extended context
- **Week 3**: Query consolidation
- **Week 4**: Smart defaults & error handling
- **Week 4 (Parallel)**: Prompts & resources ⭐ NEW

### Effort
- 6 Prompts: 2 days
- 6 Resources: 2 days
- Integration: 1 day
- Testing: 1 day
- Documentation: 1 day
- **Total: 7 days** (fits within Phase 1)

### Impact
- ✅ Significantly improves agent experience
- ✅ Reduces errors and trial-and-error
- ✅ Self-documenting API
- ✅ Non-breaking, additive only
- ✅ Low risk, high value

## Detailed Content

### Prompt 1: Entity Creation Guide
**Purpose**: Guide agents on creating entities
**Content**:
- Quick start example
- With context example
- Batch creation example
- Best practices
- Common mistakes

### Prompt 2: Entity Search Guide
**Purpose**: Guide agents on searching entities
**Content**:
- Text search example
- Semantic search example
- Hybrid search example
- With filters example
- Best practices

### Prompt 3: Relationship Guide
**Purpose**: Guide agents on linking entities
**Content**:
- Link entities example
- List relationships example
- Check relationship example
- Unlink entities example
- Best practices

### Prompt 4: Workflow Guide
**Purpose**: Guide agents on executing workflows
**Content**:
- Setup project example
- Bulk status update example
- Import requirements example
- Best practices
- Error handling

### Prompt 5: Context Guide
**Purpose**: Guide agents on managing context
**Content**:
- Set workspace context example
- Set project context example
- Get current context example
- Clear context example
- Best practices

### Prompt 6: Error Recovery Guide
**Purpose**: Guide agents on handling errors
**Content**:
- Entity not found recovery
- Missing required field recovery
- Permission denied recovery
- Best practices
- Debugging tips

### Resource 1: Entity Types Reference
**Purpose**: Reference for all entity types
**Content**:
- 20 entity types
- Description for each
- Fields for each
- Operations for each
- Table mapping

### Resource 2: Operation Reference
**Purpose**: Reference for all operations
**Content**:
- All operations (create, read, update, delete, etc.)
- Description for each
- Required parameters
- Optional parameters
- Return type

### Resource 3: Workflow Templates
**Purpose**: Pre-built workflow examples
**Content**:
- setup_project template
- import_requirements template
- setup_test_matrix template
- bulk_status_update template
- organization_onboarding template

### Resource 4: Schema Definitions
**Purpose**: JSON schemas for all entities
**Content**:
- Project schema
- Requirement schema
- Test schema
- Document schema
- And 16 more

### Resource 5: Best Practices Guide
**Purpose**: Agent best practices
**Content**:
- Context management best practices
- Entity operations best practices
- Search operations best practices
- Error handling best practices
- Performance tips

### Resource 6: API Reference
**Purpose**: Complete API documentation
**Content**:
- Tools overview
- Operations overview
- Context types overview
- Relationship types overview
- Quick reference

## Testing Strategy

### Unit Tests
```python
def test_prompts():
    assert entity_creation_guide("project") is not None
    assert entity_search_guide("requirement") is not None
    assert relationship_guide() is not None
    assert workflow_guide() is not None
    assert context_guide() is not None
    assert error_recovery_guide() is not None

def test_resources():
    assert get_entity_types_reference() is not None
    assert get_operation_reference() is not None
    assert get_workflow_templates() is not None
    assert get_project_schema() is not None
    assert get_best_practices() is not None
    assert get_api_reference() is not None
```

### Integration Tests
- Verify prompts are registered with MCP
- Verify resources are accessible via MCP
- Verify content is valid Markdown/JSON
- Verify links and references are correct

## Success Criteria

- ✅ 6 prompts implemented and tested
- ✅ 6 resources implemented and tested
- ✅ Integrated with server.py
- ✅ All tests passing
- ✅ Documentation updated
- ✅ No breaking changes
- ✅ Agent experience improved

## Recommendation

**Add to Phase 1 of QOL Plan** as **Phase 1.5: Prompts & Resources**:
- Implement 6 essential prompts
- Implement 6 essential resources
- Integrate with server.py
- Write tests
- Update documentation

**Timeline**: 1 week (fits within Phase 1)
**Impact**: Significantly improves agent experience
**Risk**: Low (non-breaking, additive only)
**Value**: High (reduces errors, improves UX)

## Next Steps

1. Review [15_PROMPTS_RESOURCES_ANALYSIS.md](15_PROMPTS_RESOURCES_ANALYSIS.md)
2. Review [16_PROMPTS_RESOURCES_IMPLEMENTATION.md](16_PROMPTS_RESOURCES_IMPLEMENTATION.md)
3. Approve Phase 1.5 scope
4. Start implementation
5. Write tests
6. Update documentation
7. Deploy with Phase 1

---

**Status**: ✅ Analysis complete, implementation guide ready

**Recommendation**: Include in Phase 1 for maximum impact

