# Trigger Usage Examples

## Quick Start

```python
from schemas.triggers import TriggerEmulator
from schemas.constants import Tables

# Initialize the emulator
emulator = TriggerEmulator()
emulator.set_user_context("user-123")

# Create an organization
org_data = {"name": "My Company"}
org_data = emulator.before_insert(Tables.ORGANIZATIONS, org_data)
# Now org_data has: id, slug, timestamps, defaults, etc.

# Insert to database
result = await db.insert(Tables.ORGANIZATIONS, org_data)

# Handle side effects (auto-add owner to members)
side_effects = emulator.after_insert(Tables.ORGANIZATIONS, result)
for table, data in side_effects:
    await db.insert(table, data)
```

## Integration with Entity Tool

Here's how to integrate triggers into the existing entity tool:

```python
# In tools/entity.py

from schemas.triggers import TriggerEmulator
from schemas.constants import Tables

class EntityTool(ToolBase):
    def __init__(self):
        super().__init__()
        self._emulator = TriggerEmulator()

    async def _create_entity(
        self,
        entity_type: str,
        data: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """Create entity with trigger emulation."""

        # 1. Get table name
        table = self._resolve_entity_table(entity_type)

        # 2. Set user context for audit fields
        self._emulator.set_user_context(user_id)

        # 3. Run BEFORE INSERT triggers
        data = self._emulator.before_insert(table, data)

        # 4. Insert into database
        result = await self._db_insert(table, data)

        # 5. Run AFTER INSERT triggers (side effects)
        side_effects = self._emulator.after_insert(table, result)

        # 6. Execute side effects
        for side_table, side_data in side_effects:
            try:
                await self._db_insert(side_table, side_data)
            except Exception as e:
                logger.warning(f"Side effect failed for {side_table}: {e}")

        return result

    async def _update_entity(
        self,
        entity_type: str,
        entity_id: str,
        updates: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """Update entity with trigger emulation."""

        # 1. Get table name
        table = self._resolve_entity_table(entity_type)

        # 2. Get existing data (for old_data comparison)
        old_data = await self._db_get_single(table, id=entity_id)
        if not old_data:
            raise ValueError(f"{entity_type} not found: {entity_id}")

        # 3. Set user context
        self._emulator.set_user_context(user_id)

        # 4. Run BEFORE UPDATE triggers
        updates = self._emulator.before_update(table, old_data, updates)

        # 5. Update in database
        result = await self._db_update(
            table,
            updates,
            filters={"id": entity_id}
        )

        # 6. Run AFTER UPDATE triggers (side effects)
        side_effects = self._emulator.after_update(table, old_data, result)

        # 7. Execute side effects
        for side_table, side_data in side_effects:
            try:
                await self._db_insert(side_table, side_data)
            except Exception as e:
                logger.warning(f"Side effect failed for {side_table}: {e}")

        return result
```

## Common Patterns

### 1. Organization Creation

```python
from schemas.triggers import TriggerEmulator, handle_new_user
from schemas.constants import Tables

async def create_organization_with_owner(org_data: Dict, user_id: str):
    """Create organization and automatically add owner to members."""

    emulator = TriggerEmulator()
    emulator.set_user_context(user_id)

    # Process organization data
    org_data = emulator.before_insert(Tables.ORGANIZATIONS, org_data)

    # Insert organization
    org = await db.insert(Tables.ORGANIZATIONS, org_data)

    # Auto-add owner to members (from AFTER INSERT trigger)
    side_effects = emulator.after_insert(Tables.ORGANIZATIONS, org)
    for table, data in side_effects:
        await db.insert(table, data)

    return org
```

### 2. New User Signup

```python
from schemas.triggers import TriggerEmulator
from schemas.constants import Tables

async def signup_new_user(email: str, full_name: str):
    """Handle new user signup with personal org creation."""

    emulator = TriggerEmulator()

    # Create profile
    profile_data = {
        "email": email,
        "full_name": full_name
    }

    # BEFORE INSERT on profile
    profile_data = emulator.before_insert(Tables.PROFILES, profile_data)

    # Insert profile
    profile = await db.insert(Tables.PROFILES, profile_data)

    # AFTER INSERT creates personal org
    side_effects = emulator.after_insert(Tables.PROFILES, profile)

    personal_org = None
    for table, data in side_effects:
        if table == Tables.ORGANIZATIONS:
            # Set user context for org creation
            emulator.set_user_context(profile["id"])
            data = emulator.before_insert(table, data)
            personal_org = await db.insert(table, data)

            # Org AFTER INSERT adds owner to members
            org_side_effects = emulator.after_insert(table, personal_org)
            for org_table, org_data in org_side_effects:
                await db.insert(org_table, org_data)

    # Update profile with personal_organization_id
    await db.update(
        Tables.PROFILES,
        {"personal_organization_id": personal_org["id"]},
        {"id": profile["id"]}
    )

    return profile, personal_org
```

### 3. Requirement Creation with Hierarchy

```python
from schemas.triggers import TriggerEmulator, check_requirement_cycle
from schemas.constants import Tables

async def create_requirement_with_parent(req_data: Dict, parent_id: str, user_id: str):
    """Create requirement with parent relationship."""

    emulator = TriggerEmulator()
    emulator.set_user_context(user_id)

    # Check for cycles
    if parent_id:
        closure_data = await db.query(
            Tables.REQUIREMENTS_CLOSURE,
            filters={"descendant_id": parent_id}
        )
        check_requirement_cycle(req_data.get("id"), parent_id, closure_data)

    # Set parent
    req_data["parent_id"] = parent_id

    # BEFORE INSERT
    req_data = emulator.before_insert(Tables.REQUIREMENTS, req_data)

    # Insert requirement
    requirement = await db.insert(Tables.REQUIREMENTS, req_data)

    # Update closure table (simplified - actual would need parent's closure entries)
    from schemas.triggers import handle_requirement_hierarchy
    closure_entries = handle_requirement_hierarchy(requirement)

    for entry in closure_entries:
        await db.insert(Tables.REQUIREMENTS_CLOSURE, entry)

    return requirement
```

### 4. Soft Delete with Cascade

```python
from schemas.triggers import handle_soft_delete
from schemas.constants import Tables

async def soft_delete_organization(org_id: str, user_id: str):
    """Soft delete organization and cascade to projects."""

    # Soft delete organization
    org_update = handle_soft_delete({}, user_id)
    await db.update(Tables.ORGANIZATIONS, org_update, {"id": org_id})

    # Cascade to projects
    projects = await db.query(
        Tables.PROJECTS,
        filters={"organization_id": org_id, "is_deleted": False}
    )

    for project in projects:
        project_update = handle_soft_delete({}, user_id)
        await db.update(Tables.PROJECTS, project_update, {"id": project["id"]})

        # Cascade to documents
        documents = await db.query(
            Tables.DOCUMENTS,
            filters={"project_id": project["id"], "is_deleted": False}
        )

        for doc in documents:
            doc_update = handle_soft_delete({}, user_id)
            await db.update(Tables.DOCUMENTS, doc_update, {"id": doc["id"]})
```

### 5. Update with Version Check

```python
from schemas.triggers import check_version_and_update
from schemas.constants import Tables

async def update_requirement_optimistic(req_id: str, updates: Dict, expected_version: int, user_id: str):
    """Update requirement with optimistic locking."""

    emulator = TriggerEmulator()
    emulator.set_user_context(user_id)

    # Get current data
    current = await db.get_single(Tables.REQUIREMENTS, id=req_id)

    # Check version
    if current["version"] != expected_version:
        raise ValueError(
            f"Version mismatch: expected {expected_version}, "
            f"got {current['version']}. Record was modified by another user."
        )

    # BEFORE UPDATE (includes version increment)
    updates = emulator.before_update(Tables.REQUIREMENTS, current, updates)

    # Update (database will also check version)
    result = await db.update(
        Tables.REQUIREMENTS,
        updates,
        {"id": req_id, "version": expected_version}
    )

    return result
```

### 6. Validation Before Insert

```python
from schemas.triggers import TriggerEmulator, check_member_limits
from schemas.validation import SchemaValidator
from schemas.constants import Tables

async def add_organization_member(org_id: str, user_id: str, role: str, added_by: str):
    """Add member to organization with validation."""

    # Get organization
    org = await db.get_single(Tables.ORGANIZATIONS, id=org_id)

    # Check member limits
    current_count = await db.count(
        Tables.ORGANIZATION_MEMBERS,
        filters={"organization_id": org_id, "is_deleted": False}
    )
    check_member_limits(org, current_count)

    # Validate role enum
    member_data = {
        "organization_id": org_id,
        "user_id": user_id,
        "role": role
    }
    SchemaValidator.validate_and_raise("organization_member", member_data)

    # Apply triggers
    emulator = TriggerEmulator()
    emulator.set_user_context(added_by)
    member_data = emulator.before_insert(Tables.ORGANIZATION_MEMBERS, member_data)

    # Insert
    result = await db.insert(Tables.ORGANIZATION_MEMBERS, member_data)

    return result
```

## Testing Triggers

```python
import pytest
from schemas.triggers import TriggerEmulator
from schemas.constants import Tables

@pytest.fixture
def emulator():
    emulator = TriggerEmulator()
    emulator.set_user_context("test-user-123")
    return emulator

def test_organization_creation(emulator):
    """Test organization creation with triggers."""
    data = {
        "name": "Test Company",
        "slug": "Test Company!!!"
    }

    # BEFORE INSERT
    result = emulator.before_insert(Tables.ORGANIZATIONS, data)

    # Verify transformations
    assert result["slug"] == "test-company"
    assert result["id"]
    assert result["created_by"] == "test-user-123"
    assert result["type"] == "personal"
    assert result["billing_plan"] == "free"

def test_requirement_properties_sync(emulator):
    """Test requirement properties are synced."""
    data = {
        "name": "REQ-001",
        "document_id": "doc-123",
        "status": "active",
        "priority": "high"
    }

    result = emulator.before_insert(Tables.REQUIREMENTS, data)

    assert result["external_id"].startswith("REQ-")
    assert result["properties"]["status"] == "active"
    assert result["properties"]["priority"] == "high"

def test_after_insert_side_effects(emulator):
    """Test AFTER INSERT side effects."""
    org_data = {
        "id": "org-123",
        "name": "Test Org",
        "owner_id": "user-456"
    }

    side_effects = emulator.after_insert(Tables.ORGANIZATIONS, org_data)

    # Should create organization_member
    assert len(side_effects) == 1
    table, member_data = side_effects[0]
    assert table == Tables.ORGANIZATION_MEMBERS
    assert member_data["organization_id"] == "org-123"
    assert member_data["user_id"] == "user-456"
    assert member_data["role"] == "owner"
```

## Best Practices

1. **Always use TriggerEmulator before database operations**
   - Ensures data is properly transformed
   - Catches validation errors early
   - Maintains consistency with database

2. **Set user context for audit fields**
   ```python
   emulator.set_user_context(user_id)
   ```

3. **Handle side effects from after_insert/after_update**
   ```python
   side_effects = emulator.after_insert(table, data)
   for table, data in side_effects:
       await db.insert(table, data)
   ```

4. **Use validation helpers before database operations**
   ```python
   from schemas.triggers import check_member_limits, check_requirement_cycle

   # Check before adding member
   check_member_limits(org_data, current_count)

   # Check before setting parent
   check_requirement_cycle(req_id, parent_id, closure_data)
   ```

5. **Test trigger logic independently**
   - Test transformations without database
   - Verify behavior matches expectations
   - Catch regressions early

## Debugging

If data doesn't look right after triggers:

```python
# Print before and after
print("Before triggers:", data)
data = emulator.before_insert(table, data)
print("After triggers:", data)

# Check specific transformations
from schemas.triggers import normalize_slug, sync_requirements_properties

slug = normalize_slug("My Org!")  # Check slug normalization
print(f"Normalized slug: {slug}")

req_data = sync_requirements_properties({"status": "active"})  # Check property sync
print(f"Synced properties: {req_data['properties']}")
```

## Migration from Old Code

If you have existing entity creation code without triggers:

**Before:**
```python
async def create_entity(data: Dict):
    # Generate ID manually
    data["id"] = str(uuid.uuid4())

    # Set timestamps manually
    now = datetime.now(timezone.utc).isoformat()
    data["created_at"] = now
    data["updated_at"] = now

    # Normalize slug manually
    if "name" in data:
        data["slug"] = data["name"].lower().replace(" ", "-")

    result = await db.insert(table, data)
    return result
```

**After:**
```python
async def create_entity(data: Dict, user_id: str):
    emulator = TriggerEmulator()
    emulator.set_user_context(user_id)

    # All transformations handled by triggers
    data = emulator.before_insert(table, data)

    result = await db.insert(table, data)

    # Handle side effects
    side_effects = emulator.after_insert(table, result)
    for table, side_data in side_effects:
        await db.insert(table, side_data)

    return result
```

## See Also

- [TRIGGERS_DOCUMENTATION.md](./TRIGGERS_DOCUMENTATION.md) - Full trigger reference
- [SCHEMA_REFERENCE.md](../SCHEMA_REFERENCE.md) - Database schema
- `schemas/triggers.py` - Implementation
- `tests/test_triggers.py` - Test suite
