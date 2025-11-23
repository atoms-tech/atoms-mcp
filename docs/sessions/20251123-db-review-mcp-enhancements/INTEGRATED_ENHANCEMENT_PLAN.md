# Integrated Enhancement Plan - Wrap Into Existing Tools

## Design Philosophy
**NO new tools.** Integrate all 26 tables and features into the 5 existing tools following established patterns.

---

## 1. entity_operation (Primary Tool)
**Already handles**: CRUD, search, workflows, permissions, export/import

### Add Operations (Wrap existing features)
```python
operation: Literal[
    # Existing
    "create", "read", "update", "delete", "archive", "restore",
    "search", "list", "batch_create", "bulk_update", "bulk_delete",
    
    # TRACEABILITY (trace_links, requirement_tests)
    "get_trace",              # Get all linked entities
    "list_linked_tests",      # Get tests for requirement
    "list_linked_requirements", # Get requirements for test
    "coverage_analysis",      # Test coverage stats
    
    # AUDIT (audit_logs)
    "get_audit_log",          # Get mutation history
    "list_audit_logs",        # List audit entries
    
    # NOTIFICATIONS (notifications)
    "list_notifications",     # Get user notifications
    "mark_notification_read", # Mark as read
    
    # TEST MATRIX (test_matrix_views)
    "get_test_matrix",        # Get test coverage matrix
    
    # EXISTING (already there)
    "advanced_search", "export", "import", "get_permissions", "update_permissions"
]
```

### New Parameters
```python
# Traceability
include_trace: bool = False,        # Include linked entities
trace_depth: int = 1,               # How deep to trace

# Audit
include_audit_history: bool = False, # Include mutation history
audit_filters: Dict = None,         # Filter audit logs

# Notifications
notification_status: str = "unread", # Filter by status

# Test Matrix
matrix_format: str = "summary",     # summary, detailed, grid
```

---

## 2. relationship_operation (Relationships)
**Already handles**: link, unlink, list, check, update

### Add Operations
```python
operation: Literal[
    # Existing
    "link", "unlink", "list", "check", "update",
    
    # TRACEABILITY (trace_links)
    "link_trace",             # Link requirement to test
    "unlink_trace",           # Unlink requirement from test
    "list_traces",            # List all trace links
    "check_trace",            # Check if linked
    
    # PERMISSIONS (entity_permissions)
    "grant_permission",       # Grant access
    "revoke_permission",      # Revoke access
    "list_permissions",       # List entity permissions
    "check_permission",       # Check if user has access
    "update_permission_level" # Change permission level
]
```

### New Parameters
```python
# Permissions
permission_level: str = "view",     # view, edit, admin
expires_at: Optional[str] = None,   # Expiration date
granted_by: Optional[str] = None,   # Who granted it
```

---

## 3. workspace_operation (Context & Config)
**Already handles**: context, defaults, favorites, view_state

### Add Operations
```python
operation: Literal[
    # Existing
    "get_context", "set_context", "list_workspaces",
    "get_defaults", "set_defaults", "add_favorite", "remove_favorite",
    "save_view_state", "get_breadcrumbs",
    
    # SEARCH CONFIG (search_index)
    "get_search_config",      # Get FTS settings
    "set_search_config",      # Configure FTS, facets
    
    # EXPORT/IMPORT HISTORY
    "get_export_history",     # List recent exports
    "get_import_history",     # List recent imports
    
    # AUDIT SUMMARY
    "get_audit_summary",      # Audit stats for workspace
    
    # PERMISSIONS SUMMARY
    "get_permission_summary"  # Overview of all permissions
]
```

### New Parameters
```python
# Search config
fts_enabled: bool = True,
facets: List[str] = None,
suggestions_enabled: bool = True,

# History
history_limit: int = 50,
history_status: str = None,  # completed, failed, etc.
```

---

## 4. workflow_execute (Complex Operations)
**Already handles**: batch_operation, resilient_operation, setup_project, etc.

### Add Workflows
```python
workflow: Literal[
    # Existing
    "create_entity", "batch_operation", "resilient_operation",
    "setup_project", "import_requirements", "setup_test_matrix",
    "bulk_status_update", "organization_onboarding",
    
    # NEW: Leverage existing tables
    "export_with_traceability",  # Export + trace links
    "import_with_validation",    # Import + audit trail
    "bulk_permission_grant",     # Grant to multiple users
    "generate_coverage_report",  # Test coverage analysis
    "audit_compliance_report"    # Compliance audit
]
```

---

## 5. data_query (Search & Analysis)
**Already handles**: search, aggregate, analyze, rag_search, similarity

### Enhance Existing Operations
```python
query_type: Literal[
    # Existing
    "search", "aggregate", "analyze", "relationships", "rag_search", "similarity",
    
    # ENHANCED with new tables
    # search: Now includes search_index FTS
    # relationships: Now includes trace_links, entity_permissions
    # analyze: Now includes audit_logs, test_matrix_views
]
```

### New Parameters
```python
# Traceability analysis
include_trace_analysis: bool = False,
trace_type: str = None,  # requirement_to_test, etc.

# Audit analysis
audit_analysis: bool = False,
audit_date_range: Dict = None,

# Test matrix analysis
matrix_analysis: bool = False,
coverage_threshold: float = 0.8,
```

---

## Implementation Strategy

### Phase 1: entity_operation (2 days)
- Add traceability operations (get_trace, list_linked_tests, coverage_analysis)
- Add audit operations (get_audit_log, list_audit_logs)
- Add notification operations (list_notifications, mark_notification_read)
- Add test_matrix operations (get_test_matrix)

### Phase 2: relationship_operation (1.5 days)
- Add trace_links operations (link_trace, unlink_trace, list_traces)
- Add entity_permissions operations (grant_permission, revoke_permission, check_permission)

### Phase 3: workspace_operation (1 day)
- Add search_config operations (get_search_config, set_search_config)
- Add history operations (get_export_history, get_import_history)
- Add summary operations (get_audit_summary, get_permission_summary)

### Phase 4: workflow_execute (1 day)
- Add new workflows (export_with_traceability, bulk_permission_grant, etc.)

### Phase 5: data_query (1 day)
- Enhance existing operations with new table support
- Add traceability and audit analysis

### Phase 6: Testing & Documentation (1 day)
- Unit tests for all new operations
- Integration tests
- Documentation updates

**TOTAL: 6.5 days (same as before, but NO new tools!)**

---

## Benefits of This Approach

✅ **Consolidation** - Stays at 5 tools, not 12  
✅ **Consistency** - Uses established patterns  
✅ **Simplicity** - Easier to learn and use  
✅ **Maintainability** - Less code to maintain  
✅ **Backward Compatible** - Existing code still works  
✅ **Composable** - Tools work together naturally  

---

## Example Usage

```python
# Traceability
await entity_operation(
  operation="get_trace",
  entity_type="requirement",
  entity_id="req-123",
  include_trace=True
)

# Permissions
await relationship_operation(
  operation="grant_permission",
  relationship_type="entity_permission",
  source={"entity_type": "requirement", "entity_id": "req-123"},
  target={"user_id": "user-456"},
  permission_level="edit"
)

# Audit
await entity_operation(
  operation="get_audit_log",
  entity_type="requirement",
  entity_id="req-123",
  include_audit_history=True
)

# Search Config
await workspace_operation(
  operation="set_search_config",
  facets=["status", "priority", "owner"]
)

# Workflows
await workflow_execute(
  workflow="bulk_permission_grant",
  parameters={
    "entity_type": "requirement",
    "entity_ids": ["req-1", "req-2", "req-3"],
    "user_id": "user-456",
    "permission_level": "view"
  }
)
```

