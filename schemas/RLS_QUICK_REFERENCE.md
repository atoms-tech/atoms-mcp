# RLS Policy Validators - Quick Reference

## Import

```python
from schemas.rls import (
    PolicyValidator,
    PermissionDeniedError,
    # Table-specific policies
    OrganizationPolicy,
    ProjectPolicy,
    DocumentPolicy,
    RequirementPolicy,
    TestPolicy,
    ProfilePolicy,
    OrganizationMemberPolicy,
    ProjectMemberPolicy,
    # Helper functions
    user_can_access_project,
    is_project_owner_or_admin,
    is_super_admin,
)
```

## Basic Usage

### Check Permission (Returns bool)

```python
policy = OrganizationPolicy(user_id, db)
can_delete = await policy.can_delete(record)
if can_delete:
    # Proceed with delete
```

### Validate Permission (Raises if denied)

```python
try:
    await policy.validate_delete(record)
    # Permission granted, proceed
except PermissionDeniedError as e:
    # Handle denial: e.table, e.operation, e.reason
```

## Permission Rules

### Organizations
- **Read**: Must be member
- **Create**: Any authenticated user
- **Update**: Owner or admin
- **Delete**: Owner only

### Projects
- **Read**: Member OR org member OR public
- **Create**: Member of parent org
- **Update**: Owner or admin
- **Delete**: Owner only

### Documents
- **Read**: Can access parent project
- **Create**: Editor+ role in project
- **Update**: Editor+ role in project
- **Delete**: Project owner or admin

### Requirements
- **Read**: Can access parent project
- **Create/Update/Delete**: Editor+ role

### Tests
- **Read**: Can access parent project
- **Create/Update**: Editor+ role
- **Delete**: Project owner or admin

### Profiles
- **Read**: Any authenticated user
- **Create/Delete**: Super admin only
- **Update**: Own profile only

## Common Patterns

### Pre-validate Before Database

```python
from schemas.rls import DocumentPolicy, PermissionDeniedError

async def create_document(user_id: str, data: dict):
    policy = DocumentPolicy(user_id, db)
    try:
        await policy.validate_insert(data)
        return await db.insert("documents", data)
    except PermissionDeniedError as e:
        return {"error": e.reason, "code": 403}
```

### Batch Permission Check

```python
validator = PolicyValidator(user_id, db)
accessible = [
    p for p in projects
    if await validator.can_select("projects", p)
]
```

### Tool Integration

```python
class MyTool(ToolBase):
    async def update_project(self, user_id: str, project_id: str, data: dict):
        project = await self._db_get_single("projects", id=project_id)

        # Validate permission
        policy = ProjectPolicy(user_id, self._get_adapters()["database"])
        await policy.validate_update(project, data)

        # Proceed with update
        return await self._db_update("projects", data, {"id": project_id})
```

## Helper Functions

```python
# Check project access
can_access = await user_can_access_project(project_id, user_id, db)

# Check project ownership
is_owner = await is_project_owner_or_admin(project_id, user_id, db)

# Check super admin
is_admin = await is_super_admin(user_id, db)

# Get user's organizations
org_ids = await get_user_organization_ids(user_id, db)
```

## Error Handling

```python
try:
    await policy.validate_update(record, data)
except PermissionDeniedError as e:
    print(f"Table: {e.table}")        # "organizations"
    print(f"Operation: {e.operation}") # "UPDATE"
    print(f"Reason: {e.reason}")       # "Not organization owner or admin"
```

## Testing

### Run Tests
```bash
pytest tests/unit/test_rls_policies.py -v
```

### Run Examples
```bash
python3 schemas/rls_examples.py
```

### Mock Testing
```python
from unittest.mock import AsyncMock
from schemas.rls import OrganizationPolicy

mock_db = AsyncMock()
mock_db.get_single.return_value = {"id": "member-1", "user_id": "user-123"}

policy = OrganizationPolicy("user-123", mock_db)
result = await policy.can_select({"id": "org-123"})
```

## Files

| File | Description |
|------|-------------|
| `schemas/rls.py` | Core implementation |
| `schemas/README_RLS.md` | Full documentation |
| `schemas/rls_examples.py` | Usage examples |
| `tests/unit/test_rls_policies.py` | Unit tests |

## See Also

- [Full Documentation](./README_RLS.md)
- [Schema Reference](../SCHEMA_REFERENCE.md)
- [Examples](./rls_examples.py)
