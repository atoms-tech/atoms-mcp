# Database Triggers - Python Implementation

## Overview

This document describes the Python implementation of database triggers in `schemas/triggers.py`. These functions replicate database-level trigger logic, allowing client-side validation and data transformation before sending data to the database.

## Why Client-Side Triggers?

1. **Validation Before Database**: Catch errors before making database calls
2. **Consistency**: Ensure data is transformed the same way client-side and server-side
3. **Performance**: Reduce failed database operations by validating first
4. **Testing**: Test trigger logic without database connection
5. **Documentation**: Makes trigger logic explicit and discoverable

## Architecture

```
┌─────────────────────┐
│   Tools/Client      │
│                     │
│  1. Create data     │
│  2. Run triggers    │ ← TriggerEmulator
│  3. Validate        │
│  4. Send to DB      │
└─────────────────────┘
           │
           ▼
┌─────────────────────┐
│   Database          │
│                     │
│  1. Receive data    │
│  2. Run triggers    │ ← Database triggers
│  3. Store           │
└─────────────────────┘
```

## Core Functions

### Slug Normalization

#### `normalize_slug(slug: str) -> str`

Normalizes a slug to database-compatible format.

**Replicates**: Database trigger for slug normalization

**Rules**:
- Converts to lowercase
- Replaces non-alphanumeric with hyphens
- Removes leading/trailing hyphens
- Must start with a letter (database constraint)

**Example**:
```python
from schemas.triggers import normalize_slug

slug = normalize_slug("Hello World!")  # → "hello-world"
slug = normalize_slug("Test & Co.")    # → "test-co"
slug = normalize_slug("My-Company")    # → "my-company"

# Invalid - raises ValueError
slug = normalize_slug("123-test")  # ❌ Must start with letter
```

#### `auto_generate_slug(name: str, fallback: str = "entity") -> str`

Auto-generates slug from entity name.

**Replicates**: Database behavior for auto-slug generation on INSERT

**Example**:
```python
from schemas.triggers import auto_generate_slug

slug = auto_generate_slug("Test Project")  # → "test-project"
slug = auto_generate_slug("My Org")        # → "my-org"
slug = auto_generate_slug("", "document")  # → "document" (fallback)
```

### Timestamp Management

#### `handle_updated_at(data: Dict[str, Any]) -> Dict[str, Any]`

Sets `updated_at` to current UTC time.

**Replicates**: Database BEFORE UPDATE trigger on `updated_at`

**Used on**: All tables with `updated_at` column

**Example**:
```python
from schemas.triggers import handle_updated_at

data = {"name": "Updated Name"}
data = handle_updated_at(data)
# data["updated_at"] = "2024-10-09T12:34:56.789Z"
```

#### `set_created_timestamps(data: Dict[str, Any]) -> Dict[str, Any]`

Sets both `created_at` and `updated_at` for new records.

**Replicates**: Database BEFORE INSERT trigger for timestamps

**Example**:
```python
from schemas.triggers import set_created_timestamps

data = {"name": "New Entity"}
data = set_created_timestamps(data)
# data["created_at"] = "2024-10-09T12:34:56.789Z"
# data["updated_at"] = "2024-10-09T12:34:56.789Z"
```

### ID Generation

#### `generate_external_id(entity_type: str, prefix: Optional[str] = None) -> str`

Generates external ID for requirements and other entities.

**Replicates**: Database trigger for `external_id` auto-generation

**Format**: `{PREFIX}-{8-char-uuid}`

**Default Prefixes**:
- `requirement` → `REQ-`
- `test` → `TEST-`
- `document` → `DOC-`
- `project` → `PROJ-`
- Other → `ENT-`

**Example**:
```python
from schemas.triggers import generate_external_id

external_id = generate_external_id("requirement")  # → "REQ-A1B2C3D4"
external_id = generate_external_id("test")         # → "TEST-E5F6G7H8"
external_id = generate_external_id("custom", prefix="CUST")  # → "CUST-I9J0K1L2"
```

#### `generate_uuid() -> str`

Generates UUID for primary keys.

**Replicates**: Database `DEFAULT gen_random_uuid()`

**Example**:
```python
from schemas.triggers import generate_uuid

id = generate_uuid()  # → "550e8400-e29b-41d4-a716-446655440000"
```

### Requirement Triggers

#### `sync_requirements_properties(requirement_data: Dict[str, Any]) -> Dict[str, Any]`

Syncs requirement fields into properties JSONB.

**Replicates**: Database trigger for requirements property sync

**Synced Fields**: `status`, `priority`, `format`, `level`, `type`

**Example**:
```python
from schemas.triggers import sync_requirements_properties

data = {
    "name": "REQ-001",
    "status": "active",
    "priority": "high",
    "format": "incose"
}

data = sync_requirements_properties(data)
# data["properties"] = {
#     "status": "active",
#     "priority": "high",
#     "format": "incose"
# }
```

#### `handle_requirement_hierarchy(requirement_data: Dict[str, Any], existing_closure: Optional[List[Dict]] = None) -> List[Dict]`

Manages requirement hierarchy closure table.

**Replicates**: Database trigger for `requirements_closure` management

**Returns**: Closure table entries to insert

**Example**:
```python
from schemas.triggers import handle_requirement_hierarchy

# New requirement with parent
data = {"id": "req-2", "parent_id": "req-1"}
existing_closure = [
    {"ancestor_id": "req-1", "descendant_id": "req-1", "depth": 0}
]

closure_entries = handle_requirement_hierarchy(data, existing_closure)
# Returns:
# [
#     {"ancestor_id": "req-2", "descendant_id": "req-2", "depth": 0},  # self
#     {"ancestor_id": "req-1", "descendant_id": "req-2", "depth": 1}   # parent
# ]
```

### User & Organization Triggers

#### `handle_new_user(user_data: Dict[str, Any]) -> Tuple[Dict, Dict]`

Creates personal organization for new user.

**Replicates**: Database AFTER INSERT trigger on `profiles`

**Returns**: `(updated_profile_data, personal_org_data)`

**Example**:
```python
from schemas.triggers import handle_new_user

user_data = {
    "id": "user-123",
    "email": "test@example.com",
    "full_name": "Test User"
}

updated_profile, personal_org = handle_new_user(user_data)

# updated_profile has personal_organization_id set
# personal_org = {
#     "id": "...",
#     "name": "Test User's Workspace",
#     "slug": "test-personal",
#     "type": "personal",
#     "owner_id": "user-123"
# }
```

#### `auto_add_org_owner(org_id: str, user_id: str) -> Dict[str, Any]`

Adds organization owner to `organization_members`.

**Replicates**: Database AFTER INSERT trigger on `organizations`

**Example**:
```python
from schemas.triggers import auto_add_org_owner

member_data = auto_add_org_owner("org-123", "user-456")
# member_data = {
#     "id": "...",
#     "organization_id": "org-123",
#     "user_id": "user-456",
#     "role": "owner",
#     "status": "active"
# }
```

### Soft Delete Triggers

#### `handle_soft_delete(data: Dict[str, Any], user_id: str) -> Dict[str, Any]`

Marks entity as soft deleted.

**Replicates**: Database BEFORE UPDATE trigger for soft delete

**Sets**:
- `is_deleted` = `true`
- `deleted_at` = current timestamp
- `deleted_by` = user_id

**Example**:
```python
from schemas.triggers import handle_soft_delete

data = {"id": "entity-123", "name": "Test"}
data = handle_soft_delete(data, "user-456")
# data["is_deleted"] = True
# data["deleted_at"] = "2024-10-09T12:34:56.789Z"
# data["deleted_by"] = "user-456"
```

#### `handle_restore(data: Dict[str, Any]) -> Dict[str, Any]`

Restores soft-deleted entity.

**Replicates**: Database logic for restoring soft-deleted records

**Example**:
```python
from schemas.triggers import handle_restore

data = {
    "id": "entity-123",
    "is_deleted": True,
    "deleted_at": "2024-10-09T12:34:56.789Z",
    "deleted_by": "user-456"
}

data = handle_restore(data)
# data["is_deleted"] = False
# data["deleted_at"] = None
# data["deleted_by"] = None
```

### Validation Helpers

#### `check_member_limits(org_data: Dict[str, Any], current_member_count: int) -> None`

Verifies organization membership limits.

**Replicates**: Database constraint check for member limits

**Limits**:
- Free plan: 5 members max
- Pro plan: 50 members max
- Enterprise: unlimited

**Example**:
```python
from schemas.triggers import check_member_limits

org_data = {"billing_plan": "free", "max_members": 5}

check_member_limits(org_data, 3)  # ✅ OK
check_member_limits(org_data, 5)  # ❌ Raises ValueError
```

#### `check_version_and_update(table: str, entity_id: str, current_version: int, new_data: Dict) -> Dict`

Implements optimistic locking via version check.

**Replicates**: Database trigger for version-based optimistic locking

**Example**:
```python
from schemas.triggers import check_version_and_update

new_data = {"name": "Updated"}
result = check_version_and_update("requirements", "req-123", 1, new_data)
# result["version"] = 2
```

#### `check_requirement_cycle(requirement_id: str, parent_id: str, closure_data: List[Dict]) -> None`

Prevents cycles in requirement hierarchy.

**Replicates**: Database constraint to prevent circular dependencies

**Example**:
```python
from schemas.triggers import check_requirement_cycle

closure_data = [
    {"ancestor_id": "req-1", "descendant_id": "req-2", "depth": 1}
]

check_requirement_cycle("req-1", "req-2", closure_data)  # ❌ Raises ValueError (cycle)
check_requirement_cycle("req-3", "req-1", closure_data)  # ✅ OK
```

## TriggerEmulator Class

The `TriggerEmulator` class orchestrates all triggers in the correct order.

### Usage

```python
from schemas.triggers import TriggerEmulator
from schemas.constants import Tables

# Initialize
emulator = TriggerEmulator()
emulator.set_user_context("user-123")

# BEFORE INSERT
org_data = {
    "name": "My Company",
    "slug": "My Company"
}
org_data = emulator.before_insert(Tables.ORGANIZATIONS, org_data)

# Data now has:
# - id (generated UUID)
# - slug (normalized to "my-company")
# - created_at, updated_at (timestamps)
# - created_by, updated_by (user-123)
# - type (default "personal")
# - billing_plan (default "free")
# - is_deleted (False)

# AFTER INSERT (get side effects)
side_effects = emulator.after_insert(Tables.ORGANIZATIONS, org_data)

# side_effects = [
#     (Tables.ORGANIZATION_MEMBERS, {
#         "organization_id": org_data["id"],
#         "user_id": "user-123",
#         "role": "owner"
#     })
# ]
```

### Methods

#### `set_user_context(user_id: str) -> None`

Sets current user ID for audit fields (`created_by`, `updated_by`, etc.)

#### `before_insert(table: str, data: Dict[str, Any]) -> Dict[str, Any]`

Runs BEFORE INSERT trigger logic:
1. Generates ID if missing
2. Sets timestamps (`created_at`, `updated_at`)
3. Sets audit fields (`created_by`, `updated_by`)
4. Runs table-specific transformations
5. Initializes defaults

**Table-Specific Logic**:

**Organizations**:
- Normalizes slug
- Auto-generates slug from name if missing
- Sets default type (`personal`)
- Sets default billing plan (`free`)

**Projects**:
- Auto-generates slug from name

**Documents**:
- Auto-generates slug from name
- Sets version to 1

**Requirements**:
- Generates `external_id`
- Syncs properties
- Sets version to 1

**Profiles**:
- Sets status to `active`
- Sets `is_approved` to `true`

#### `before_update(table: str, old_data: Dict, new_data: Dict) -> Dict[str, Any]`

Runs BEFORE UPDATE trigger logic:
1. Sets `updated_at` timestamp
2. Sets `updated_by` audit field
3. Increments version if applicable
4. Runs table-specific transformations

**Table-Specific Logic**:

**Requirements**:
- Syncs properties

**Organizations**:
- Normalizes slug if changed

#### `after_insert(table: str, data: Dict[str, Any]) -> List[Tuple[str, Dict]]`

Runs AFTER INSERT trigger logic (side effects):

**Returns**: List of `(table, data)` tuples for additional inserts

**Organizations**:
- Creates `organization_members` entry for owner

**Profiles**:
- Creates personal organization
- (Profile update would need separate operation)

#### `after_update(table: str, old_data: Dict, new_data: Dict) -> List[Tuple[str, Dict]]`

Runs AFTER UPDATE trigger logic (side effects):

**Organizations/Projects/Documents**:
- Cascades soft delete to related entities (if implemented)

## Integration with Tools

Tools should use the `TriggerEmulator` before database operations:

```python
from schemas.triggers import TriggerEmulator
from schemas.constants import Tables

async def create_organization(data: Dict[str, Any], user_id: str):
    # 1. Initialize emulator
    emulator = TriggerEmulator()
    emulator.set_user_context(user_id)

    # 2. Run BEFORE INSERT triggers
    data = emulator.before_insert(Tables.ORGANIZATIONS, data)

    # 3. Insert into database
    result = await db.insert(Tables.ORGANIZATIONS, data)

    # 4. Run AFTER INSERT triggers
    side_effects = emulator.after_insert(Tables.ORGANIZATIONS, result)

    # 5. Execute side effects
    for table, side_data in side_effects:
        await db.insert(table, side_data)

    return result
```

## Testing

The trigger emulator has comprehensive tests in `tests/test_triggers.py`:

```bash
# Run all trigger tests
pytest tests/test_triggers.py -v

# Run specific test class
pytest tests/test_triggers.py::TestSlugNormalization -v

# Run specific test
pytest tests/test_triggers.py::TestTriggerEmulator::test_before_insert_organization -v
```

### Test Coverage

- ✅ Slug normalization (valid/invalid inputs)
- ✅ Timestamp handling
- ✅ ID generation (UUID, external_id)
- ✅ Requirement triggers (properties sync, hierarchy)
- ✅ User/org triggers (new user, auto-add owner)
- ✅ Soft delete/restore
- ✅ Validation helpers (member limits, version, cycles)
- ✅ TriggerEmulator (BEFORE/AFTER INSERT/UPDATE)
- ✅ Integration workflows (org creation, req update, user signup)

## Database Trigger Reference

These Python functions replicate the following database triggers:

### Auto-Generated Fields

| Database Trigger | Python Function |
|-----------------|-----------------|
| `DEFAULT gen_random_uuid()` | `generate_uuid()` |
| `DEFAULT NOW()` on `created_at` | `set_created_timestamps()` |
| `DEFAULT NOW()` on `updated_at` | `set_created_timestamps()` |

### BEFORE INSERT Triggers

| Table | Database Trigger | Python Function |
|-------|-----------------|-----------------|
| organizations | Normalize slug | `normalize_slug()` via `before_insert()` |
| organizations | Set defaults (type, billing) | `before_insert()` |
| projects | Auto-generate slug | `auto_generate_slug()` via `before_insert()` |
| documents | Auto-generate slug | `auto_generate_slug()` via `before_insert()` |
| documents | Set version = 1 | `before_insert()` |
| requirements | Generate external_id | `generate_external_id()` via `before_insert()` |
| requirements | Sync properties | `sync_requirements_properties()` |
| requirements | Set version = 1 | `before_insert()` |

### BEFORE UPDATE Triggers

| Table | Database Trigger | Python Function |
|-------|-----------------|-----------------|
| All tables | Set `updated_at = NOW()` | `handle_updated_at()` via `before_update()` |
| All versioned | Increment version | `before_update()` |
| requirements | Sync properties | `sync_requirements_properties()` |
| organizations | Normalize slug | `normalize_slug()` via `before_update()` |

### AFTER INSERT Triggers

| Table | Database Trigger | Python Function |
|-------|-----------------|-----------------|
| organizations | Add owner to org_members | `auto_add_org_owner()` via `after_insert()` |
| profiles | Create personal org | `handle_new_user()` via `after_insert()` |
| requirements | Update closure table | `handle_requirement_hierarchy()` |

### AFTER UPDATE Triggers

| Table | Database Trigger | Python Function |
|-------|-----------------|-----------------|
| organizations | Cascade soft delete | `after_update()` (placeholder) |
| projects | Cascade soft delete | `after_update()` (placeholder) |
| documents | Cascade soft delete | `after_update()` (placeholder) |

### Constraints & Validation

| Database Constraint | Python Function |
|--------------------|-----------------|
| Slug starts with letter | `normalize_slug()` |
| Member limits | `check_member_limits()` |
| Version-based locking | `check_version_and_update()` |
| Prevent requirement cycles | `check_requirement_cycle()` |

## Maintenance

### Adding New Triggers

When adding a new database trigger:

1. **Add function to `schemas/triggers.py`**:
   ```python
   def my_new_trigger(data: Dict[str, Any]) -> Dict[str, Any]:
       """
       Description of what this replicates.

       Replicates: Database BEFORE INSERT trigger on table_name
       """
       result = data.copy()
       # Transformation logic
       return result
   ```

2. **Add to `TriggerEmulator` if needed**:
   ```python
   def before_insert(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
       result = data.copy()
       # ... existing logic ...

       elif table == Tables.MY_TABLE:
           result = my_new_trigger(result)

       return result
   ```

3. **Add tests to `tests/test_triggers.py`**:
   ```python
   def test_my_new_trigger():
       data = {"field": "value"}
       result = my_new_trigger(data)
       assert result["transformed_field"] == "expected_value"
   ```

4. **Update this documentation**

### Verifying Parity

To verify Python triggers match database behavior:

1. **Create test data**:
   ```python
   # Python trigger
   emulator = TriggerEmulator()
   emulator.set_user_context("user-123")
   py_result = emulator.before_insert(Tables.ORGANIZATIONS, test_data)
   ```

2. **Insert via database**:
   ```python
   # Database trigger
   db_result = await db.insert(Tables.ORGANIZATIONS, test_data)
   ```

3. **Compare results**:
   ```python
   # Should produce identical transformations
   assert py_result["slug"] == db_result["slug"]
   assert py_result["type"] == db_result["type"]
   ```

## Best Practices

1. **Always use TriggerEmulator before database operations**
2. **Set user context for audit fields**
3. **Handle side effects from `after_insert`/`after_update`**
4. **Test trigger logic independently of database**
5. **Keep Python triggers in sync with database migrations**
6. **Document which database trigger each function replicates**

## See Also

- `schemas/triggers.py` - Implementation
- `tests/test_triggers.py` - Test suite
- `schemas/validation.py` - Schema validation
- `schemas/enums.py` - Enum definitions
- `schemas/constants.py` - Table and field constants
