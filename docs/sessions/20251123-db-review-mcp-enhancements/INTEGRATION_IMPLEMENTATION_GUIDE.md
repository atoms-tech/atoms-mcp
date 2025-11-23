# Integration Implementation Guide

## How to Integrate Into Existing Tools

### Pattern 1: Add Operations to Literal Type

**File**: `tools/entity.py` (line ~1658)

```python
async def entity_operation(
    auth_token: str,
    operation: Literal[
        # Existing operations
        "create", "read", "update", "delete", "archive", "restore",
        "search", "list", "batch_create", "bulk_update", "bulk_delete",
        
        # NEW: Traceability operations
        "get_trace",
        "list_linked_tests",
        "list_linked_requirements",
        "coverage_analysis",
        
        # NEW: Audit operations
        "get_audit_log",
        "list_audit_logs",
        
        # NEW: Notification operations
        "list_notifications",
        "mark_notification_read",
        
        # NEW: Test matrix operations
        "get_test_matrix",
        
        # Existing (keep)
        "advanced_search", "export", "import", "get_permissions", "update_permissions"
    ],
    # ... rest of parameters
)
```

### Pattern 2: Add New Parameters

```python
async def entity_operation(
    auth_token: str,
    operation: Literal[...],
    entity_type: str,
    # ... existing parameters ...
    
    # NEW: Traceability parameters
    include_trace: bool = False,
    trace_depth: int = 1,
    
    # NEW: Audit parameters
    include_audit_history: bool = False,
    audit_filters: Optional[Dict[str, Any]] = None,
    
    # NEW: Notification parameters
    notification_status: str = "unread",
    
    # NEW: Test matrix parameters
    matrix_format: str = "summary",
) -> Dict[str, Any]:
```

### Pattern 3: Add Operation Routing

In the operation routing section (after auth validation):

```python
if operation == "get_trace":
    result = await _entity_manager.get_trace(
        entity_type, entity_id, trace_depth
    )
    return _entity_manager._format_result(result, format_type)

elif operation == "list_linked_tests":
    result = await _entity_manager.list_linked_tests(
        entity_type, entity_id
    )
    return _entity_manager._format_result(result, format_type)

elif operation == "coverage_analysis":
    result = await _entity_manager.coverage_analysis(
        entity_type, filters
    )
    return _entity_manager._format_result(result, format_type)

elif operation == "get_audit_log":
    result = await _entity_manager.get_audit_log(
        entity_type, entity_id, audit_filters
    )
    return _entity_manager._format_result(result, format_type)

# ... etc for other operations
```

### Pattern 4: Add Methods to Manager Class

In `EntityManager` class:

```python
async def get_trace(self, entity_type: str, entity_id: str, depth: int = 1):
    """Get trace links for entity."""
    # Query trace_links table
    result = await self._db.query(
        "trace_links",
        filters={
            "source_entity_type": entity_type,
            "source_entity_id": entity_id
        }
    )
    return result

async def list_linked_tests(self, entity_type: str, entity_id: str):
    """Get tests linked to requirement."""
    # Query requirement_tests junction table
    result = await self._db.query(
        "requirement_tests",
        filters={
            "requirement_id": entity_id
        }
    )
    return result

async def coverage_analysis(self, entity_type: str, filters: Dict):
    """Analyze test coverage."""
    # Query test_matrix_views and aggregate
    result = await self._db.query(
        "test_matrix_views",
        filters=filters
    )
    # Calculate coverage stats
    return self._calculate_coverage(result)

async def get_audit_log(self, entity_type: str, entity_id: str, filters: Dict = None):
    """Get audit trail for entity."""
    query_filters = {
        "entity_type": entity_type,
        "entity_id": entity_id
    }
    if filters:
        query_filters.update(filters)
    
    result = await self._db.query(
        "audit_logs",
        filters=query_filters,
        order_by="created_at DESC"
    )
    return result
```

---

## Integration Into relationship_operation

### Add to Literal Type

```python
async def relationship_operation(
    auth_token: str,
    operation: Literal[
        # Existing
        "link", "unlink", "list", "check", "update",
        
        # NEW: Trace operations
        "link_trace",
        "unlink_trace",
        "list_traces",
        "check_trace",
        
        # NEW: Permission operations
        "grant_permission",
        "revoke_permission",
        "list_permissions",
        "check_permission",
        "update_permission_level"
    ],
    # ... rest of parameters
)
```

### Add Parameters

```python
async def relationship_operation(
    auth_token: str,
    operation: Literal[...],
    relationship_type: str,
    # ... existing parameters ...
    
    # NEW: Permission parameters
    permission_level: str = "view",
    expires_at: Optional[str] = None,
    granted_by: Optional[str] = None,
) -> Dict[str, Any]:
```

### Add Methods to RelationshipManager

```python
async def grant_permission(self, entity_type: str, entity_id: str, 
                          user_id: str, permission_level: str, 
                          expires_at: Optional[str] = None):
    """Grant permission to user."""
    perm_data = {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "user_id": user_id,
        "permission_level": permission_level,
        "expires_at": expires_at
    }
    result = await self._db.insert("entity_permissions", perm_data, returning="*")
    return result

async def check_permission(self, entity_type: str, entity_id: str, 
                          user_id: str, required_level: str):
    """Check if user has permission."""
    perm = await self._db.get_single(
        "entity_permissions",
        filters={
            "entity_type": entity_type,
            "entity_id": entity_id,
            "user_id": user_id
        }
    )
    
    if not perm:
        return False
    
    # Check expiration
    if perm.get("expires_at"):
        if datetime.fromisoformat(perm["expires_at"]) < datetime.utcnow():
            return False
    
    # Check level
    levels = {"view": 1, "edit": 2, "admin": 3}
    return levels.get(perm["permission_level"], 0) >= levels.get(required_level, 0)
```

---

## Integration Into workspace_operation

### Add Operations

```python
async def workspace_operation(
    auth_token: Optional[str],
    operation: str,
    # ... existing parameters ...
    
    # NEW: Search config parameters
    fts_enabled: bool = True,
    facets: Optional[List[str]] = None,
    suggestions_enabled: bool = True,
    
    # NEW: History parameters
    history_limit: int = 50,
    history_status: Optional[str] = None,
) -> Dict[str, Any]:
```

### Add Methods

```python
async def get_search_config(self, workspace_id: str):
    """Get FTS configuration."""
    # Query workspace settings or return defaults
    return {
        "fts_enabled": True,
        "facets": ["status", "priority", "owner"],
        "suggestions_enabled": True
    }

async def get_export_history(self, workspace_id: str, limit: int = 50):
    """Get recent exports."""
    result = await self._db.query(
        "export_jobs",
        filters={"workspace_id": workspace_id},
        order_by="created_at DESC",
        limit=limit
    )
    return result

async def get_permission_summary(self, workspace_id: str):
    """Get permission overview."""
    result = await self._db.query(
        "entity_permissions",
        filters={"workspace_id": workspace_id}
    )
    # Aggregate by permission level
    return self._aggregate_permissions(result)
```

---

## Integration Into workflow_execute

### Add Workflows

```python
async def workflow_execute(
    auth_token: str,
    workflow: str,
    parameters: Dict[str, Any],
    # ... existing parameters ...
) -> Dict[str, Any]:
    
    # ... existing workflows ...
    
    elif workflow == "bulk_permission_grant":
        result = await self._bulk_permission_grant_workflow(parameters)
    
    elif workflow == "export_with_traceability":
        result = await self._export_with_traceability_workflow(parameters)
    
    elif workflow == "generate_coverage_report":
        result = await self._generate_coverage_report_workflow(parameters)
```

### Add Workflow Methods

```python
async def _bulk_permission_grant_workflow(self, parameters: Dict):
    """Grant permission to multiple users."""
    entity_type = parameters["entity_type"]
    entity_ids = parameters["entity_ids"]
    user_id = parameters["user_id"]
    permission_level = parameters["permission_level"]
    
    results = []
    for entity_id in entity_ids:
        result = await self._db.insert(
            "entity_permissions",
            {
                "entity_type": entity_type,
                "entity_id": entity_id,
                "user_id": user_id,
                "permission_level": permission_level
            }
        )
        results.append(result)
    
    return {
        "success": True,
        "granted": len(results),
        "results": results
    }
```

---

## Testing Pattern

```python
async def test_entity_operation_get_trace():
    """Test traceability operation."""
    # Create requirement and test
    req = await entity_operation(
        operation="create",
        entity_type="requirement",
        data={"name": "REQ-1"}
    )
    
    test = await entity_operation(
        operation="create",
        entity_type="test_req",
        data={"name": "TEST-1"}
    )
    
    # Link them
    await relationship_operation(
        operation="link_trace",
        relationship_type="requirement_test",
        source={"entity_type": "requirement", "entity_id": req["id"]},
        target={"entity_type": "test_req", "entity_id": test["id"]}
    )
    
    # Get trace
    result = await entity_operation(
        operation="get_trace",
        entity_type="requirement",
        entity_id=req["id"]
    )
    
    assert result["success"]
    assert len(result["data"]) > 0
```

