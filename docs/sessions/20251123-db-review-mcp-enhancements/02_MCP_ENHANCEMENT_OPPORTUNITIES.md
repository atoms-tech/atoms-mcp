# MCP Enhancement Opportunities
**Based on New Database Tables & QoL Paradigms**

## 1. Workflow Management Tool (NEW)
**Leverage**: workflows, workflow_versions, workflow_executions tables

### Proposed Operations
```
workflow_management(
  operation: "list" | "create" | "update" | "delete" | "execute" | "get_history" | "rollback_version",
  workflow_id?: string,
  entity_type?: string,
  definition?: dict,
  version?: int,
  input_data?: dict
)
```

### QoL Enhancements
- **Smart Defaults**: Auto-detect entity_type from context
- **Version Rollback**: Revert to previous workflow definition
- **Execution History**: Track all runs with status/results
- **Dry-Run Mode**: Preview workflow without executing

---

## 2. Search & Discovery Tool (NEW)
**Leverage**: search_index table with FTS

### Proposed Operations
```
search_discovery(
  operation: "search" | "faceted_search" | "suggestions" | "similar" | "index_entity",
  query?: string,
  entity_type?: string,
  facets?: dict,
  limit?: int,
  offset?: int
)
```

### QoL Enhancements
- **Faceted Search**: Filter by type, status, owner, date
- **Auto-Suggestions**: Suggest search terms
- **Similarity Search**: Find similar entities by embedding
- **Index Management**: Reindex entities, check index status

---

## 3. Data Import/Export Tool (NEW)
**Leverage**: export_jobs, import_jobs tables

### Proposed Operations
```
data_transfer(
  operation: "export" | "import" | "get_job_status" | "list_jobs" | "cancel_job",
  entity_type?: string,
  format?: "json" | "csv" | "xlsx",
  filters?: dict,
  job_id?: string
)
```

### QoL Enhancements
- **Format Detection**: Auto-detect format from file extension
- **Progress Tracking**: Real-time job status updates
- **Error Recovery**: Detailed error reports per row
- **Batch Operations**: Export/import multiple entity types

---

## 4. Permission Management Tool (NEW)
**Leverage**: entity_permissions table

### Proposed Operations
```
permission_control(
  operation: "grant" | "revoke" | "list" | "check" | "update_level" | "set_expiration",
  entity_type?: string,
  entity_id?: string,
  user_id?: string,
  permission_level?: "view" | "edit" | "admin",
  expires_at?: datetime
)
```

### QoL Enhancements
- **Bulk Permissions**: Grant to multiple users/roles
- **Permission Expiration**: Auto-revoke after date
- **Audit Trail**: Track who granted/revoked permissions
- **Role-Based**: Support role-based permissions

---

## 5. Enhanced entity_operation
**Consolidate** existing operations with new capabilities

### New Parameters
- `include_search_index`: Auto-index on create/update
- `track_permissions`: Include permission info in responses
- `workflow_context`: Auto-apply workflow rules
- `export_format`: Return data in export format

### New Operations
- `reindex_search`: Rebuild search index for entity type
- `bulk_permission_grant`: Grant to multiple users
- `export_with_relations`: Export entity + related entities
- `import_with_validation`: Import with schema validation

---

## 6. Workspace Context Enhancements
**Extend** workspace_operation with new capabilities

### New Operations
- `get_search_config`: Get workspace search settings
- `set_search_config`: Configure FTS, facets, suggestions
- `get_export_history`: List recent exports
- `get_import_history`: List recent imports
- `get_permission_summary`: Overview of all permissions

---

## Implementation Priority

### Phase 1 (High Impact, Low Effort)
1. Workflow Management Tool
2. Search & Discovery Tool
3. Enhanced entity_operation

### Phase 2 (Medium Impact, Medium Effort)
4. Data Import/Export Tool
5. Permission Management Tool

### Phase 3 (Polish & Integration)
6. Workspace Context Enhancements
7. Cross-tool integration & workflows

