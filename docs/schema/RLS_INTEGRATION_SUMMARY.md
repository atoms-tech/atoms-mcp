# RLS Policy Validators Integration Summary

## Overview
Successfully integrated Row-Level Security (RLS) policy validators into `/tools/entity.py` to provide server-side permission validation before database operations.

## Changes Made

### 1. Added Imports (Lines 39-46)
```python
from schemas.rls import (
    OrganizationPolicy,
    ProjectPolicy,
    DocumentPolicy,
    RequirementPolicy,
    TestPolicy,
    PermissionDeniedError,
)
```

### 2. Added Helper Method (Lines 75-92)
Created `_get_rls_policy()` method to map entity types to their corresponding RLS policy validators:
- `organization` → `OrganizationPolicy`
- `project` → `ProjectPolicy`  
- `document` → `DocumentPolicy`
- `requirement` → `RequirementPolicy`
- `test` → `TestPolicy`

### 3. CREATE Operations (Lines 275-281)
Added RLS validation **BEFORE** database insert in `create_entity()`:
```python
# Validate RLS policy before insert
policy = self._get_rls_policy(entity_type)
if policy:
    try:
        await policy.validate_insert(data)
    except PermissionDeniedError as e:
        raise ValueError(f"Permission denied: {e.reason}")
```

**Validation Rules:**
- **Organizations**: Any authenticated user can create (will become owner)
- **Projects**: User must be member of parent organization
- **Documents**: User must have editor+ role in parent project
- **Requirements**: User must have editor+ role in parent document's project
- **Tests**: User must have editor+ role in parent project

### 4. READ Operations (Lines 351-358)
Added RLS validation **AFTER** fetch in `read_entity()`:
```python
# Validate RLS policy after fetch
if result:
    policy = self._get_rls_policy(entity_type)
    if policy:
        try:
            await policy.validate_select(result)
        except PermissionDeniedError as e:
            raise ValueError(f"Permission denied: {e.reason}")
```

**Validation Rules:**
- **Organizations**: User must be a member
- **Projects**: User must be member OR org member OR project is public
- **Documents**: User must have access to parent project
- **Requirements**: User must have access to parent document's project
- **Tests**: User must have access to parent project

### 5. UPDATE Operations (Lines 383-398)
Added RLS validation **BEFORE** update in `update_entity()`:
```python
# Fetch existing record for RLS validation
existing_record = await self._db_get_single(
    table,
    filters={"id": entity_id}
)

if not existing_record:
    raise ValueError(f"{entity_type} with ID '{entity_id}' not found")

# Validate RLS policy before update
policy = self._get_rls_policy(entity_type)
if policy:
    try:
        await policy.validate_update(existing_record, data)
    except PermissionDeniedError as e:
        raise ValueError(f"Permission denied: {e.reason}")
```

**Validation Rules:**
- **Organizations**: Owner or admin only
- **Projects**: Owner or admin only
- **Documents**: Editor+ role required
- **Requirements**: Editor+ role required
- **Tests**: Editor+ role required

### 6. DELETE Operations (Lines 460-475)
Added RLS validation **BEFORE** delete in `delete_entity()`:
```python
# Fetch existing record for RLS validation
existing_record = await self._db_get_single(
    table,
    filters={"id": entity_id}
)

if not existing_record:
    raise ValueError(f"{entity_type} with ID '{entity_id}' not found")

# Validate RLS policy before delete
policy = self._get_rls_policy(entity_type)
if policy:
    try:
        await policy.validate_delete(existing_record)
    except PermissionDeniedError as e:
        raise ValueError(f"Permission denied: {e.reason}")
```

**Validation Rules:**
- **Organizations**: Owner only
- **Projects**: Owner only
- **Documents**: Owner or admin only
- **Requirements**: Editor+ role required
- **Tests**: Owner or admin only

### 7. Enhanced Error Handling (Lines 840-867)
Updated exception handling in `entity_operation()` to provide detailed error responses:

```python
except PermissionDeniedError as e:
    return {
        "success": False,
        "error": str(e),
        "error_type": "permission_denied",
        "table": e.table,
        "operation": operation,
        "entity_type": entity_type
    }
except ValueError as e:
    # Check if this is a permission error (converted from PermissionDeniedError)
    error_msg = str(e)
    error_type = "permission_denied" if "Permission denied:" in error_msg else "validation_error"
    return {
        "success": False,
        "error": error_msg,
        "error_type": error_type,
        "operation": operation,
        "entity_type": entity_type
    }
```

## Validation Flow

### Create Flow:
1. Resolve smart defaults
2. Apply defaults and validate required fields
3. Schema validation (`validate_before_create`)
4. Trigger emulation (`before_insert`)
5. **RLS validation (`validate_insert`)** ✨ NEW
6. Database insert
7. Side effects and embedding generation

### Read Flow:
1. Database fetch
2. **RLS validation (`validate_select`)** ✨ NEW
3. Include relationships (if requested)
4. Return result

### Update Flow:
1. Schema validation (`validate_before_update`)
2. Fetch existing record
3. **RLS validation (`validate_update`)** ✨ NEW
4. Prepare update data
5. Database update
6. Include relationships (if requested)

### Delete Flow:
1. Fetch existing record
2. **RLS validation (`validate_delete`)** ✨ NEW
3. Prepare delete data (soft or hard)
4. Database operation

## Error Response Format

### Permission Denied:
```json
{
  "success": false,
  "error": "Permission denied for INSERT on Organization: User does not have permission to create this record",
  "error_type": "permission_denied",
  "table": "Organization",
  "operation": "create",
  "entity_type": "organization"
}
```

### Validation Error:
```json
{
  "success": false,
  "error": "Schema validation failed: name is required",
  "error_type": "validation_error",
  "operation": "create",
  "entity_type": "organization"
}
```

## Benefits

1. **Defense in Depth**: Server-side validation complements database RLS policies
2. **Better Error Messages**: Clear, actionable permission error messages
3. **Early Validation**: Catch permission issues before database round-trip
4. **Consistent Authorization**: Centralized permission logic in policy classes
5. **Testing**: Easier to test authorization logic without database

## Database RLS Policies Still Active

These server-side validators provide a **first line of defense** but do NOT replace database RLS policies. The database RLS policies remain active and will catch any attempts to bypass the application layer.

## Files Modified

- `/tools/entity.py` - Integrated RLS policy validators

## Files Referenced

- `/schemas/rls.py` - RLS policy validator classes and helpers

## Testing Recommendations

1. Test permission denied scenarios for each operation
2. Verify error messages are clear and actionable
3. Test role-based access (owner, admin, editor, viewer)
4. Test cross-entity permissions (org members accessing projects)
5. Verify database RLS policies still enforce security

## Next Steps

Consider integrating RLS validators into:
1. Batch operations
2. Search/list operations (for fine-grained filtering)
3. Relationship operations
4. Workflow operations
