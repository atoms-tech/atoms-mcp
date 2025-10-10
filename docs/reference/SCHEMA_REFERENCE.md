# Database Schema Reference

## Overview

This document provides the authoritative reference for all database schemas in Atoms MCP. All code (tests and production) MUST use these schemas to ensure type safety and prevent runtime errors.

## Schema Package Structure

```
schemas/
├── __init__.py              # Public exports
├── enums.py                 # All enum definitions (type-safe)
├── constants.py             # Table names, field names, mappings
├── validation.py            # Runtime validation utilities
└── database/
    ├── __init__.py
    ├── entities.py          # TypedDict for core entity tables
    └── relationships.py     # TypedDict for junction tables
```

## Core Entities

### Organization

**Table**: `organizations`

**Required Fields** (for create):
- `name` (string) - Organization name
- `slug` (string) - URL-safe identifier (lowercase, alphanumeric + hyphens, must start with letter)
- `type` (OrganizationType) - Organization type

**Valid Organization Types**:
- `"team"` (default) ✅
- `"enterprise"` ✅
- ~~`"business"`~~ ❌ **NOT VALID** - Will cause 500 error

**Auto-Generated Fields**:
- `id`, `created_at`, `updated_at`, `created_by`, `updated_by`

**Optional Fields**:
- `description`, `is_deleted`, `deleted_at`, `deleted_by`, `embedding`

**Example**:
```python
from schemas.enums import OrganizationType

org_data = {
    "name": "Acme Corp",
    "slug": "acme-corp",
    "type": OrganizationType.TEAM.value,  # ✅ Correct
    "description": "Test organization"
}

# ❌ WRONG - Will fail with 500 error
bad_data = {
    "name": "Acme Corp",
    "slug": "acme-corp",
    "type": "business"  # ❌ Invalid enum value
}
```

### Project

**Table**: `projects`

**Required Fields**:
- `name` (string) - Project name
- `organization_id` (string) - Parent organization ID

**Auto-Generated Fields**:
- `id`, `created_at`, `updated_at`, `created_by`, `updated_by`
- `slug` (auto-generated from name if not provided)

**Optional Fields**:
- `description`, `status`, `owned_by`, `is_deleted`, `deleted_at`, `deleted_by`, `embedding`

**Valid Status Values**:
- `"active"`, `"draft"`, `"pending"`, `"approved"`, `"rejected"`, `"archived"`, `"deprecated"`, `"deleted"`

**Example**:
```python
from schemas.enums import EntityStatus

project_data = {
    "name": "My Project",
    "organization_id": "org_123",  # Must be real org ID
    "status": EntityStatus.ACTIVE.value,
    "description": "Test project"
}
```

### Document

**Table**: `documents`

**Required Fields**:
- `name` (string) - Document name
- `project_id` (string) - Parent project ID

**Auto-Generated Fields**:
- `id`, `created_at`, `updated_at`, `created_by`, `updated_by`

**Optional Fields**:
- `title`, `slug`, `content`, `description`, `doc_type`, `status`, `is_deleted`, `deleted_at`, `deleted_by`, `embedding`

**Valid Document Types**:
- `"technical"`, `"api"`, `"specification"`, `"design"`, `"requirement"`, `"test_plan"`

**Example**:
```python
from schemas.enums import DocumentType

doc_data = {
    "name": "Requirements Doc",
    "project_id": "proj_123",
    "doc_type": DocumentType.REQUIREMENT.value,
    "content": "# Requirements\n\n..."
}
```

### Requirement

**Table**: `requirements`

**Required Fields**:
- `name` (string) - Requirement name
- `document_id` (string) - Parent document ID

**Auto-Generated Fields**:
- `id`, `created_at`, `updated_at`, `created_by`, `updated_by`, `version`, `external_id`

**Optional Fields**:
- `title`, `description`, `block_id`, `status`, `priority`, `type`, `requirement_type`, `properties`, `is_deleted`, `deleted_at`, `deleted_by`, `embedding`

**Valid Priority Values**:
- `"low"`, `"medium"`, `"high"`, `"critical"`

**Example**:
```python
from schemas.enums import Priority, EntityStatus

req_data = {
    "name": "REQ-001",
    "description": "User shall be able to login",
    "document_id": "doc_123",
    "priority": Priority.HIGH.value,
    "status": EntityStatus.ACTIVE.value
}
```

### Test

**Table**: `test_req`

**Required Fields**:
- `title` (string) - Test title
- `project_id` (string) - Parent project ID

**Auto-Generated Fields**:
- `id`, `created_at`, `updated_at`, `created_by`

**Optional Fields**:
- `description`, `test_type`, `status`, `priority`, `is_active`

**Important Notes**:
- ⚠️ `test_req` table does NOT have `updated_by`, `is_deleted`, `deleted_at`, `deleted_by` fields
- ⚠️ RLS policies may be restrictive - ensure proper user context

**Valid Test Types**:
- `"unit"`, `"integration"`, `"functional"`, `"security"`, `"performance"`, `"e2e"`

**Valid Test Status Values**:
- `"pending"`, `"running"`, `"passed"`, `"failed"`, `"skipped"`, `"error"`

**Example**:
```python
from schemas.enums import TestType, TestStatus, Priority

test_data = {
    "title": "Test user login",
    "description": "Verify user can login with valid credentials",
    "project_id": "proj_123",
    "test_type": TestType.FUNCTIONAL.value,
    "status": TestStatus.PENDING.value,
    "priority": Priority.MEDIUM.value
}
```

## Enum Reference

### OrganizationType

```python
from schemas.enums import OrganizationType

# Valid values
OrganizationType.TEAM         # "team" (default)
OrganizationType.ENTERPRISE   # "enterprise"

# ❌ INVALID
# "business" - NOT in database enum, will cause 500 error
```

### EntityStatus

```python
from schemas.enums import EntityStatus

EntityStatus.ACTIVE       # "active"
EntityStatus.DRAFT        # "draft"
EntityStatus.PENDING      # "pending"
EntityStatus.APPROVED     # "approved"
EntityStatus.REJECTED     # "rejected"
EntityStatus.ARCHIVED     # "archived"
EntityStatus.DEPRECATED   # "deprecated"
EntityStatus.DELETED      # "deleted"
```

### Priority

```python
from schemas.enums import Priority

Priority.LOW       # "low"
Priority.MEDIUM    # "medium"
Priority.HIGH      # "high"
Priority.CRITICAL  # "critical"
```

### TestStatus

```python
from schemas.enums import TestStatus

TestStatus.PENDING   # "pending"
TestStatus.RUNNING   # "running"
TestStatus.PASSED    # "passed"
TestStatus.FAILED    # "failed"
TestStatus.SKIPPED   # "skipped"
TestStatus.ERROR     # "error"
```

## Validation

### Using SchemaValidator

```python
from schemas.validation import SchemaValidator, ValidationError

# Validate before sending to database
data = {
    "name": "Test Org",
    "slug": "test-org",
    "type": "team"
}

# Get list of errors
errors = SchemaValidator.validate_entity("organization", data, operation="create")
if errors:
    print("Validation errors:")
    for error in errors:
        print(f"  - {error}")

# Or raise exception if invalid
try:
    SchemaValidator.validate_and_raise("organization", data, operation="create")
    # Data is valid, proceed with database operation
except ValidationError as e:
    print(f"Invalid data: {e}")
```

### Common Validation Errors

1. **Invalid Enum Value**
   ```
   Error: Invalid organization type: 'business'. Valid values: ['team', 'enterprise']
   Fix: Use OrganizationType.TEAM or OrganizationType.ENTERPRISE
   ```

2. **Invalid Slug Format**
   ```
   Error: Slug must start with letter, got: '123-org'
   Fix: Use 'org-123' or 'org123'
   ```

3. **Missing Required Field**
   ```
   Error: Missing required field: organization_id
   Fix: Include organization_id in data
   ```

4. **Auto-Generated Field**
   ```
   Error: Cannot set auto-generated field: id
   Fix: Remove id from data (database will generate it)
   ```

## Best Practices

### 1. Always Use Enums

```python
# ✅ GOOD - Type-safe, validated
from schemas.enums import OrganizationType, Priority

data = {
    "type": OrganizationType.TEAM.value,
    "priority": Priority.HIGH.value
}

# ❌ BAD - String literals, prone to typos
data = {
    "type": "team",  # Could typo as "tema"
    "priority": "high"  # Could typo as "hight"
}
```

### 2. Use Data Generators

```python
# ✅ GOOD - Uses schema-validated generators
from tests.framework.data_generators import DataGenerator

org_data = DataGenerator.organization_data(
    name="Test Org",
    org_type=OrganizationType.TEAM
)

# ❌ BAD - Manual dict construction
org_data = {
    "name": "Test Org",
    "slug": "test org",  # Invalid - has space
    "type": "business"   # Invalid - not in enum
}
```

### 3. Validate Before Database Operations

```python
# ✅ GOOD - Validate before sending
from schemas.validation import SchemaValidator

data = DataGenerator.organization_data()
SchemaValidator.validate_and_raise("organization", data)
result = await client.call_tool("entity_tool", {
    "entity_type": "organization",
    "operation": "create",
    "data": data
})

# ❌ BAD - No validation, fails at runtime
result = await client.call_tool("entity_tool", {
    "entity_type": "organization",
    "operation": "create",
    "data": {"name": "Test"}  # Missing required fields
})
```

## Troubleshooting

### "invalid input value for enum organization_type: 'business'"

**Cause**: Using invalid enum value for organization type

**Fix**:
```python
# Change from:
data = {"type": "business"}

# To:
from schemas.enums import OrganizationType
data = {"type": OrganizationType.TEAM.value}
```

### "Missing required field: slug"

**Cause**: Not providing required field for create operation

**Fix**:
```python
# Use DataGenerator which includes all required fields
from tests.framework.data_generators import DataGenerator
data = DataGenerator.organization_data()
```

### "Slug must start with letter"

**Cause**: Slug starts with number or special character

**Fix**:
```python
# Change from:
data = {"slug": "123-org"}

# To:
data = {"slug": "org-123"}
```

## See Also

- `schemas/enums.py` - All enum definitions
- `schemas/database/entities.py` - TypedDict definitions
- `schemas/validation.py` - Validation utilities
- `tests/framework/data_generators.py` - Test data generators
- `SCHEMA_IMPLEMENTATION_SUMMARY.md` - Implementation details

