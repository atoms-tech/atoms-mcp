# Row-Level Security (RLS) Policy Validators

## Overview

The `schemas/rls.py` module provides Python implementations of Supabase Row-Level Security (RLS) policies for server-side validation and permission checking. These validators replicate the logic of database RLS policies to provide:

1. **Pre-validation** - Check permissions before database calls
2. **Clear error messages** - Better feedback than generic database errors
3. **Testable authorization** - Unit test permission logic independently
4. **Application-level decisions** - Make authorization decisions in code

> **Note**: Database RLS policies are still enforced. These validators provide a first line of defense and better error messages.

## Quick Start

### Basic Usage

```python
from schemas.rls import PolicyValidator, PermissionDeniedError
from infrastructure.factory import get_adapters

# Get database adapter
db = get_adapters()["database"]
user_id = "user-123"

# Create policy validator
validator = PolicyValidator(user_id=user_id, db_adapter=db)

# Check if user can read an organization
org_record = {"id": "org-456", "name": "Acme Corp"}
can_read = await validator.can_select("organizations", org_record)

if can_read:
    # Proceed with read operation
    result = await db.query("organizations", filters={"id": org_record["id"]})
else:
    # Return permission denied error
    raise PermissionDeniedError("organizations", "SELECT", "Not a member")
```

### Table-Specific Policies

```python
from schemas.rls import OrganizationPolicy, DocumentPolicy

# Use table-specific policy for more control
org_policy = OrganizationPolicy(user_id="user-123", db_adapter=db)

# Option 1: Check and handle manually
can_update = await org_policy.can_update(org_record, {"name": "New Name"})
if can_update:
    await db.update("organizations", {"name": "New Name"}, filters={"id": org_record["id"]})

# Option 2: Validate and raise exception on denial
try:
    await org_policy.validate_update(org_record, {"name": "New Name"})
    # If we get here, permission is granted
    await db.update("organizations", {"name": "New Name"}, filters={"id": org_record["id"]})
except PermissionDeniedError as e:
    print(f"Access denied: {e.reason}")
```

### Pre-validating Before Database Operations

```python
from schemas.rls import ProjectPolicy

project_policy = ProjectPolicy(user_id="user-123", db_adapter=db)

# Validate BEFORE making expensive database call
new_project = {
    "name": "My Project",
    "organization_id": "org-456"
}

try:
    await project_policy.validate_insert(new_project)

    # Permission granted, proceed with database insert
    result = await db.insert("projects", new_project)
    return {"success": True, "project": result}

except PermissionDeniedError as e:
    # Return error without making database call
    return {"success": False, "error": e.reason}
```

## Available Policies

### Core Policies

| Policy Class | Table | Description |
|--------------|-------|-------------|
| `OrganizationPolicy` | `organizations` | Organization access control |
| `ProjectPolicy` | `projects` | Project access control |
| `DocumentPolicy` | `documents` | Document access control |
| `RequirementPolicy` | `requirements` | Requirement access control |
| `TestPolicy` | `test_req` | Test access control |
| `ProfilePolicy` | `profiles` | User profile access control |

### Relationship Policies

| Policy Class | Table | Description |
|--------------|-------|-------------|
| `OrganizationMemberPolicy` | `organization_members` | Organization membership control |
| `ProjectMemberPolicy` | `project_members` | Project membership control |

## Helper Functions

These functions replicate database functions used in RLS policies:

### `user_can_access_project(project_id, user_id, db_adapter)`

Check if user can access a project. Returns `True` if:
- User is a direct member of the project, OR
- User is a member of the project's organization, OR
- The project visibility is 'public'

```python
from schemas.rls import user_can_access_project

can_access = await user_can_access_project("project-123", "user-456", db)
```

### `is_project_owner_or_admin(project_id, user_id, db_adapter)`

Check if user is owner or admin of a project.

```python
from schemas.rls import is_project_owner_or_admin

is_admin = await is_project_owner_or_admin("project-123", "user-456", db)
```

### `is_super_admin(user_id, db_adapter)`

Check if user is a super admin.

```python
from schemas.rls import is_super_admin

is_admin = await is_super_admin("user-123", db)
```

### `get_user_organization_ids(user_id, db_adapter)`

Get all organization IDs that a user is a member of.

```python
from schemas.rls import get_user_organization_ids

org_ids = await get_user_organization_ids("user-123", db)
# Returns: ["org-1", "org-2", "org-3"]
```

### `is_organization_owner_or_admin(org_id, user_id, db_adapter)`

Check if user is owner or admin of an organization.

```python
from schemas.rls import is_organization_owner_or_admin

is_admin = await is_organization_owner_or_admin("org-123", "user-456", db)
```

## Permission Rules by Table

### Organizations

| Operation | Permission Required |
|-----------|---------------------|
| SELECT (read) | User is member of organization |
| INSERT (create) | Any authenticated user |
| UPDATE | Organization owner or admin |
| DELETE | Organization owner only |

### Projects

| Operation | Permission Required |
|-----------|---------------------|
| SELECT (read) | User can access project (member, org member, or public) |
| INSERT (create) | User is member of parent organization |
| UPDATE | Project owner or admin |
| DELETE | Project owner only |

### Documents

| Operation | Permission Required |
|-----------|---------------------|
| SELECT (read) | User can access parent project |
| INSERT (create) | User has editor+ role in parent project |
| UPDATE | User has editor+ role in parent project |
| DELETE | Project owner or admin |

### Requirements

| Operation | Permission Required |
|-----------|---------------------|
| SELECT (read) | User can access parent document's project |
| INSERT (create) | User has editor+ role in parent project |
| UPDATE | User has editor+ role in parent project |
| DELETE | User has editor+ role in parent project |

### Tests

| Operation | Permission Required |
|-----------|---------------------|
| SELECT (read) | User can access parent project |
| INSERT (create) | User has editor+ role in parent project |
| UPDATE | User has editor+ role in parent project |
| DELETE | Project owner or admin |

### Profiles

| Operation | Permission Required |
|-----------|---------------------|
| SELECT (read) | Any authenticated user (for collaboration) |
| INSERT (create) | Super admin only (auto-created on signup) |
| UPDATE | Own profile only |
| DELETE | Super admin only |

### Organization Members

| Operation | Permission Required |
|-----------|---------------------|
| SELECT (read) | User is member of the organization |
| INSERT (create) | Organization owner or admin |
| UPDATE | Organization owner or admin |
| DELETE | Organization owner or admin |

### Project Members

| Operation | Permission Required |
|-----------|---------------------|
| SELECT (read) | User can access the project |
| INSERT (create) | Project owner or admin |
| UPDATE | Project owner or admin |
| DELETE | Project owner or admin |

## Integration with Tools

### Example: Document Creation Tool

```python
from schemas.rls import DocumentPolicy, PermissionDeniedError

class DocumentTool:
    def __init__(self):
        self.db = get_adapters()["database"]

    async def create_document(self, user_id: str, data: dict):
        """Create a document with permission validation."""
        # Validate permissions first
        policy = DocumentPolicy(user_id=user_id, db_adapter=self.db)

        try:
            # This will raise PermissionDeniedError if not allowed
            await policy.validate_insert(data)

            # Permission granted, proceed with creation
            result = await self.db.insert("documents", data)

            return {
                "success": True,
                "document": result,
                "message": "Document created successfully"
            }

        except PermissionDeniedError as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Permission denied: {e.reason}"
            }
```

### Example: Batch Permission Checking

```python
from schemas.rls import PolicyValidator

async def get_accessible_projects(user_id: str):
    """Get all projects user can access."""
    db = get_adapters()["database"]
    validator = PolicyValidator(user_id=user_id, db_adapter=db)

    # Get all projects
    all_projects = await db.query("projects", filters={"is_deleted": False})

    # Filter to only accessible projects
    accessible = []
    for project in all_projects:
        if await validator.can_select("projects", project):
            accessible.append(project)

    return accessible
```

## Error Handling

### PermissionDeniedError

All `validate_*` methods raise `PermissionDeniedError` when permission is denied.

```python
from schemas.rls import PermissionDeniedError

try:
    await policy.validate_delete(record)
except PermissionDeniedError as e:
    print(f"Table: {e.table}")        # "organizations"
    print(f"Operation: {e.operation}")  # "DELETE"
    print(f"Reason: {e.reason}")       # "Not organization owner"
    print(f"Full message: {e}")        # "Permission denied for DELETE on organizations: Not organization owner"
```

### Graceful Degradation

```python
# Option 1: Check permission without raising
can_delete = await policy.can_delete(record)
if not can_delete:
    return {"error": "Permission denied", "code": 403}

# Option 2: Catch and convert to API response
try:
    await policy.validate_delete(record)
    # Proceed with delete...
except PermissionDeniedError as e:
    return {
        "error": {
            "message": str(e),
            "table": e.table,
            "operation": e.operation,
            "reason": e.reason
        },
        "code": 403
    }
```

## Testing

### Unit Tests

The module includes comprehensive unit tests in `tests/unit/test_rls_policies.py`:

```bash
# Run RLS policy tests
pytest tests/unit/test_rls_policies.py -v
```

### Mock Testing

```python
from unittest.mock import AsyncMock
from schemas.rls import OrganizationPolicy

async def test_organization_access():
    # Create mock database
    mock_db = AsyncMock()
    mock_db.get_single.return_value = {
        "id": "member-1",
        "organization_id": "org-123",
        "user_id": "user-123"
    }

    # Test policy
    policy = OrganizationPolicy("user-123", mock_db)
    result = await policy.can_select({"id": "org-123"})

    assert result is True
```

## Examples

See `schemas/rls_examples.py` for comprehensive examples including:

1. Basic permission checking
2. Table-specific policies
3. Pre-validation before database operations
4. Using helper functions
5. CRUD operation checking
6. Tool integration
7. Batch permission checking
8. Custom permission logic

Run examples:

```bash
python3 schemas/rls_examples.py
```

## Performance Considerations

### Caching

The `PolicyValidator` class caches some checks to improve performance:

- `_check_super_admin()` - Cached super admin status
- `_get_user_orgs()` - Cached organization memberships

For long-running operations, create a new validator instance to refresh cache.

### Batch Operations

For multiple permission checks, reuse the same validator instance:

```python
validator = PolicyValidator(user_id, db)

for record in records:
    if await validator.can_select("documents", record):
        results.append(record)
```

### Database Queries

Each permission check may make 1-3 database queries. For performance-critical paths:

1. Use batch queries where possible
2. Pre-fetch membership data
3. Cache validation results for the request lifecycle

## Best Practices

### 1. Always Validate Before Database Operations

```python
# ✅ GOOD - Validate first
try:
    await policy.validate_insert(data)
    result = await db.insert("projects", data)
except PermissionDeniedError as e:
    return error_response(e)

# ❌ BAD - Let database RLS catch it
result = await db.insert("projects", data)  # May fail with cryptic error
```

### 2. Use Table-Specific Policies

```python
# ✅ GOOD - Explicit and clear
doc_policy = DocumentPolicy(user_id, db)
await doc_policy.validate_update(doc, data)

# ❌ BAD - Generic, less clear
validator = PolicyValidator(user_id, db)
await validator.can_update("documents", doc, data)
```

### 3. Provide Context in Error Messages

```python
# ✅ GOOD - Clear error with context
try:
    await policy.validate_delete(project)
except PermissionDeniedError as e:
    return {
        "error": f"Cannot delete project '{project['name']}': {e.reason}",
        "code": 403
    }

# ❌ BAD - Generic error
except PermissionDeniedError:
    return {"error": "Permission denied"}
```

### 4. Combine with Business Logic

```python
# ✅ GOOD - RLS + business logic
async def delete_project(user_id, project_id):
    project = await db.get_single("projects", filters={"id": project_id})

    # Check RLS permission
    policy = ProjectPolicy(user_id, db)
    await policy.validate_delete(project)

    # Additional business logic
    doc_count = await db.count("documents", filters={"project_id": project_id})
    if doc_count > 0:
        raise ValueError(f"Cannot delete project with {doc_count} documents")

    # Proceed with delete
    await db.delete("projects", filters={"id": project_id})
```

## Troubleshooting

### "Permission denied" but user should have access

1. Check user membership tables:
   ```python
   # Check organization membership
   org_members = await db.query("organization_members",
       filters={"user_id": user_id, "is_deleted": False})

   # Check project membership
   proj_members = await db.query("project_members",
       filters={"user_id": user_id, "is_deleted": False})
   ```

2. Verify role assignments:
   ```python
   member = await db.get_single("project_members",
       filters={"project_id": project_id, "user_id": user_id})
   print(f"User role: {member.get('role')}")
   ```

### Permission checks passing but database still denies

This means database RLS is more restrictive. Common causes:

1. Database RLS uses `auth.uid()` but validator uses passed `user_id`
2. Database has additional policies not replicated in validator
3. Soft-delete records (`is_deleted=true`) filtered by database

### Performance issues with many permission checks

1. Use batch queries to pre-fetch memberships:
   ```python
   # Pre-fetch all project memberships
   memberships = await db.query("project_members",
       filters={"user_id": user_id, "is_deleted": False})
   member_project_ids = {m["project_id"] for m in memberships}

   # Use set lookup instead of database query
   for project in projects:
       if project["id"] in member_project_ids:
           accessible.append(project)
   ```

2. Cache validator instances per request
3. Consider denormalizing permission data for read-heavy operations

## API Reference

See inline documentation in `schemas/rls.py` for complete API reference.

## See Also

- [Schema Reference](../SCHEMA_REFERENCE.md) - Database schema documentation
- [Schema Enums](./enums.py) - Enum definitions used in policies
- [Database Constants](./constants.py) - Table and field name constants
- [RLS Examples](./rls_examples.py) - Comprehensive usage examples
- [RLS Tests](../tests/unit/test_rls_policies.py) - Unit tests for policies
