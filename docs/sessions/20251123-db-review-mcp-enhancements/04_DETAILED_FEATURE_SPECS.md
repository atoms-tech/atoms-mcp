# Detailed Feature Specifications

## Tool 1: search_discovery

### Operations

#### search
Full-text search across entities
```python
search_discovery(
  operation="search",
  entity_type="requirement",  # or None for all types
  query="api authentication",
  filters={"status": "active", "priority": "high"},
  limit=50,
  offset=0
)
```
**Returns**: Ranked results with relevance scores

#### faceted_search
Search with facet aggregations
```python
search_discovery(
  operation="faceted_search",
  entity_type="requirement",
  query="test",
  facets=["status", "priority", "owner"],
  limit=50
)
```
**Returns**: Results + facet counts

#### suggestions
Auto-complete suggestions
```python
search_discovery(
  operation="suggestions",
  entity_type="requirement",
  prefix="req",
  limit=10
)
```
**Returns**: List of suggested terms

#### similar
Find similar entities
```python
search_discovery(
  operation="similar",
  entity_type="requirement",
  entity_id="req-123",
  limit=10
)
```
**Returns**: Similar entities by embedding distance

#### index_entity
Manually index/reindex entity
```python
search_discovery(
  operation="index_entity",
  entity_type="requirement",
  entity_id="req-123",
  title="REQ-123: API Auth",
  content="Full requirement text..."
)
```
**Returns**: Index status

---

## Tool 2: data_transfer

### Operations

#### export
Create async export job
```python
data_transfer(
  operation="export",
  entity_type="requirement",
  format="csv",  # json, csv, xlsx
  filters={"status": "active"},
  include_relations=True
)
```
**Returns**: Job ID + status

#### import
Create async import job
```python
data_transfer(
  operation="import",
  entity_type="requirement",
  format="csv",
  file_name="requirements.csv",
  file_size=1024,
  validation_mode="strict"  # strict, lenient
)
```
**Returns**: Job ID + status

#### get_job_status
Check job progress
```python
data_transfer(
  operation="get_job_status",
  job_id="export-123"
)
```
**Returns**: Status, progress, errors

#### list_jobs
List recent jobs
```python
data_transfer(
  operation="list_jobs",
  entity_type="requirement",
  status="completed",  # queued, processing, completed, failed
  limit=50
)
```
**Returns**: Job list with metadata

#### cancel_job
Cancel running job
```python
data_transfer(
  operation="cancel_job",
  job_id="export-123"
)
```
**Returns**: Cancellation status

---

## Tool 3: permission_control

### Operations

#### grant
Grant permission to user
```python
permission_control(
  operation="grant",
  entity_type="requirement",
  entity_id="req-123",
  user_id="user-456",
  permission_level="edit",  # view, edit, admin
  expires_at="2025-12-23T00:00:00Z"
)
```
**Returns**: Permission record

#### revoke
Revoke permission
```python
permission_control(
  operation="revoke",
  permission_id="perm-789"
)
```
**Returns**: Revocation status

#### list
List permissions for entity
```python
permission_control(
  operation="list",
  entity_type="requirement",
  entity_id="req-123",
  limit=50
)
```
**Returns**: Permission list

#### check
Check if user has permission
```python
permission_control(
  operation="check",
  entity_type="requirement",
  entity_id="req-123",
  user_id="user-456",
  required_level="edit"
)
```
**Returns**: Boolean + permission details

#### update_level
Change permission level
```python
permission_control(
  operation="update_level",
  permission_id="perm-789",
  permission_level="admin"
)
```
**Returns**: Updated permission

#### set_expiration
Set/update expiration
```python
permission_control(
  operation="set_expiration",
  permission_id="perm-789",
  expires_at="2025-12-31T00:00:00Z"
)
```
**Returns**: Updated permission

---

## Tool 4: workflow_management

### Operations

#### list
List workflows
```python
workflow_management(
  operation="list",
  entity_type="requirement",
  is_active=True,
  limit=50
)
```
**Returns**: Workflow list

#### create
Create workflow
```python
workflow_management(
  operation="create",
  entity_type="requirement",
  name="Auto-validate Requirements",
  description="...",
  definition={
    "steps": [
      {"type": "validate", "rules": [...]},
      {"type": "notify", "recipients": [...]}
    ]
  }
)
```
**Returns**: Workflow record

#### update
Update workflow
```python
workflow_management(
  operation="update",
  workflow_id="wf-123",
  definition={...}
)
```
**Returns**: Updated workflow

#### delete
Delete workflow
```python
workflow_management(
  operation="delete",
  workflow_id="wf-123"
)
```
**Returns**: Deletion status

#### execute
Execute workflow
```python
workflow_management(
  operation="execute",
  workflow_id="wf-123",
  entity_id="req-456",
  input_data={...}
)
```
**Returns**: Execution ID + status

#### get_history
Get execution history
```python
workflow_management(
  operation="get_history",
  workflow_id="wf-123",
  limit=50
)
```
**Returns**: Execution list

#### rollback_version
Revert to previous version
```python
workflow_management(
  operation="rollback_version",
  workflow_id="wf-123",
  version=2
)
```
**Returns**: Rolled-back workflow

