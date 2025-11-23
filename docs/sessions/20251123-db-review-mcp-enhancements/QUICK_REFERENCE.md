# Quick Reference Guide

## New Database Tables

| Table | Purpose | Key Columns | Indexes |
|-------|---------|------------|---------|
| workflows | Workflow definitions | id, workspace_id, entity_type, definition, is_active | 4 |
| workflow_versions | Version history | id, workflow_id, version_number, definition | 1 |
| workflow_executions | Execution tracking | id, workflow_id, entity_id, status, result_data | 4 |
| search_index | FTS indexing | id, entity_type, entity_id, search_vector, facets | 3 (GIN) |
| export_jobs | Export tracking | id, workspace_id, entity_type, format, status | 3 |
| import_jobs | Import tracking | id, workspace_id, entity_type, format, status | 3 |
| entity_permissions | Access control | id, entity_type, entity_id, user_id, permission_level | 4 |

## Proposed New Tools

### search_discovery
```python
search_discovery(
  operation: "search" | "faceted_search" | "suggestions" | "similar" | "index_entity",
  query?: str,
  entity_type?: str,
  facets?: list,
  limit?: int = 50,
  offset?: int = 0
)
```

### data_transfer
```python
data_transfer(
  operation: "export" | "import" | "get_job_status" | "list_jobs" | "cancel_job",
  entity_type?: str,
  format?: "json" | "csv" | "xlsx",
  job_id?: str
)
```

### permission_control
```python
permission_control(
  operation: "grant" | "revoke" | "list" | "check" | "update_level" | "set_expiration",
  entity_type?: str,
  entity_id?: str,
  user_id?: str,
  permission_level?: "view" | "edit" | "admin"
)
```

### workflow_management
```python
workflow_management(
  operation: "list" | "create" | "update" | "delete" | "execute" | "get_history" | "rollback_version",
  workflow_id?: str,
  entity_type?: str,
  definition?: dict
)
```

## Enhanced entity_operation

### New Parameters
```python
entity_operation(
  operation: str,
  entity_type: str,
  # ... existing params ...
  include_search_index: bool = False,      # Auto-index on create/update
  track_permissions: bool = False,         # Include permissions in response
  apply_workflow: str = None,              # Auto-apply workflow rules
  export_format: str = None                # Return in export format
)
```

### New Operations
- `reindex_search` - Rebuild search index
- `bulk_permission_grant` - Grant to multiple users
- `export_with_relations` - Export + related entities
- `import_with_validation` - Import with validation

## Enhanced workspace_operation

### New Operations
- `get_search_config` - Get FTS settings
- `set_search_config` - Configure FTS
- `get_export_history` - List recent exports
- `get_import_history` - List recent imports
- `get_permission_summary` - Permission overview

## Adapter Classes to Create

```
infrastructure/
├── search_index_adapter.py      (NEW)
├── export_import_adapter.py     (NEW)
├── permission_adapter.py        (NEW)
└── workflow_management_adapter.py (NEW)
```

## Tool Files to Create

```
tools/
├── search.py                    (NEW)
├── transfer.py                  (NEW)
├── permissions.py               (NEW)
└── workflow_mgmt.py             (NEW)
```

## Implementation Checklist

### Phase 1 (1.5 days)
- [ ] Create SearchIndexAdapter
- [ ] Create ExportImportAdapter
- [ ] Implement search_discovery tool
- [ ] Implement data_transfer tool
- [ ] Write unit tests for adapters
- [ ] Write integration tests

### Phase 2 (1.5 days)
- [ ] Create PermissionAdapter
- [ ] Create WorkflowManagementAdapter
- [ ] Implement permission_control tool
- [ ] Implement workflow_management tool
- [ ] Enhance entity_operation
- [ ] Integration testing

### Phase 3 (2 days)
- [ ] Enhance workspace_operation
- [ ] Cross-tool integration
- [ ] Performance optimization
- [ ] Documentation & examples
- [ ] E2E testing

## Key Files to Review

### Database Schema
- `infrastructure/sql/010_phase_2_4_phase_3_schema.sql` - New tables

### Existing Adapters (Reference)
- `infrastructure/workflow_adapter.py` - Workflow storage
- `infrastructure/advanced_features_adapter.py` - Advanced features

### Existing Tools (Reference)
- `tools/entity.py` - Entity operations
- `tools/workspace.py` - Workspace operations
- `tools/relationship.py` - Relationship operations

### Server Registration
- `server.py` - Tool registration with FastMCP

## Performance Targets

| Operation | Target | Notes |
|-----------|--------|-------|
| search | < 150ms | With FTS indexes |
| faceted_search | < 200ms | With aggregations |
| export_job | < 50ms | Job creation only |
| import_job | < 50ms | Job creation only |
| grant_permission | < 75ms | With indexing |
| list_workflows | < 100ms | With pagination |
| execute_workflow | < 150ms | Depends on workflow |

## Testing Strategy

### Unit Tests
- Adapter methods in isolation
- Mock database responses
- Error handling paths

### Integration Tests
- Full tool operations
- Database interactions
- RLS policy enforcement

### E2E Tests
- Complete workflows
- Cross-tool interactions
- Performance benchmarks

## Documentation Structure

```
docs/sessions/20251123-db-review-mcp-enhancements/
├── EXECUTIVE_SUMMARY.md              (Start here!)
├── 00_SESSION_OVERVIEW.md            (Session goals & findings)
├── 01_DATABASE_SCHEMA_REVIEW.md      (Schema analysis)
├── 02_MCP_ENHANCEMENT_OPPORTUNITIES.md (Proposals)
├── 03_IMPLEMENTATION_ROADMAP.md      (Step-by-step plan)
├── 04_DETAILED_FEATURE_SPECS.md      (Complete specs)
├── 05_CODE_EXAMPLES_AND_PATTERNS.md  (Code examples)
├── 06_ARCHITECTURE_DIAGRAMS.md       (System design)
└── QUICK_REFERENCE.md                (This file)
```

## Quick Start

1. **Read**: EXECUTIVE_SUMMARY.md (5 min)
2. **Review**: 02_MCP_ENHANCEMENT_OPPORTUNITIES.md (10 min)
3. **Plan**: 03_IMPLEMENTATION_ROADMAP.md (10 min)
4. **Code**: 05_CODE_EXAMPLES_AND_PATTERNS.md (reference)
5. **Implement**: Follow checklist above

## Questions?

Refer to the detailed documents:
- **"How do I implement X?"** → 05_CODE_EXAMPLES_AND_PATTERNS.md
- **"What are the specs for X?"** → 04_DETAILED_FEATURE_SPECS.md
- **"What's the architecture?"** → 06_ARCHITECTURE_DIAGRAMS.md
- **"What's the plan?"** → 03_IMPLEMENTATION_ROADMAP.md

