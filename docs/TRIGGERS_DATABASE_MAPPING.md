# Database Trigger Mapping Reference

This document maps Python trigger functions to their corresponding database triggers and constraints.

## Table-Specific Trigger Mapping

### organizations

| Operation | Database Trigger | Python Function | What it does |
|-----------|-----------------|-----------------|--------------|
| BEFORE INSERT | `normalize_slug()` | `normalize_slug()` | Converts slug to lowercase, replaces non-alphanumeric with hyphens |
| BEFORE INSERT | `set_defaults()` | `before_insert()` | Sets default type='personal', billing_plan='free' |
| BEFORE INSERT | `gen_random_uuid()` | `generate_uuid()` | Generates UUID for id |
| BEFORE INSERT | `NOW()` | `set_created_timestamps()` | Sets created_at, updated_at |
| BEFORE UPDATE | `NOW()` | `handle_updated_at()` | Updates updated_at timestamp |
| AFTER INSERT | `add_owner_to_members()` | `auto_add_org_owner()` | Adds owner to organization_members |
| CHECK CONSTRAINT | `slug_format` | `normalize_slug()` | Validates slug starts with letter |

### projects

| Operation | Database Trigger | Python Function | What it does |
|-----------|-----------------|-----------------|--------------|
| BEFORE INSERT | `auto_slug()` | `auto_generate_slug()` | Generates slug from name if not provided |
| BEFORE INSERT | `gen_random_uuid()` | `generate_uuid()` | Generates UUID for id |
| BEFORE INSERT | `NOW()` | `set_created_timestamps()` | Sets created_at, updated_at |
| BEFORE UPDATE | `NOW()` | `handle_updated_at()` | Updates updated_at timestamp |

### documents

| Operation | Database Trigger | Python Function | What it does |
|-----------|-----------------|-----------------|--------------|
| BEFORE INSERT | `auto_slug()` | `auto_generate_slug()` | Generates slug from name if not provided |
| BEFORE INSERT | `set_version()` | `before_insert()` | Sets version=1 for new documents |
| BEFORE INSERT | `gen_random_uuid()` | `generate_uuid()` | Generates UUID for id |
| BEFORE INSERT | `NOW()` | `set_created_timestamps()` | Sets created_at, updated_at |
| BEFORE UPDATE | `NOW()` | `handle_updated_at()` | Updates updated_at timestamp |
| BEFORE UPDATE | `increment_version()` | `before_update()` | Increments version on update |

### requirements

| Operation | Database Trigger | Python Function | What it does |
|-----------|-----------------|-----------------|--------------|
| BEFORE INSERT | `gen_external_id()` | `generate_external_id()` | Generates REQ-XXXXXXXX external ID |
| BEFORE INSERT | `sync_properties()` | `sync_requirements_properties()` | Syncs status, priority, format to properties JSONB |
| BEFORE INSERT | `set_version()` | `before_insert()` | Sets version=1 for new requirements |
| BEFORE INSERT | `gen_random_uuid()` | `generate_uuid()` | Generates UUID for id |
| BEFORE INSERT | `NOW()` | `set_created_timestamps()` | Sets created_at, updated_at |
| BEFORE UPDATE | `NOW()` | `handle_updated_at()` | Updates updated_at timestamp |
| BEFORE UPDATE | `sync_properties()` | `sync_requirements_properties()` | Syncs fields to properties on update |
| BEFORE UPDATE | `increment_version()` | `before_update()` | Increments version on update |
| AFTER INSERT | `update_closure_table()` | `handle_requirement_hierarchy()` | Maintains requirements_closure for hierarchy |
| CHECK CONSTRAINT | `prevent_cycles()` | `check_requirement_cycle()` | Prevents circular parent-child relationships |

### test_req

| Operation | Database Trigger | Python Function | What it does |
|-----------|-----------------|-----------------|--------------|
| BEFORE INSERT | `gen_random_uuid()` | `generate_uuid()` | Generates UUID for id |
| BEFORE INSERT | `NOW()` | `set_created_timestamps()` | Sets created_at, updated_at |
| BEFORE UPDATE | `NOW()` | `handle_updated_at()` | Updates updated_at timestamp |

### profiles

| Operation | Database Trigger | Python Function | What it does |
|-----------|-----------------|-----------------|--------------|
| BEFORE INSERT | `set_defaults()` | `before_insert()` | Sets status='active', is_approved=true |
| BEFORE INSERT | `gen_random_uuid()` | `generate_uuid()` | Generates UUID for id |
| BEFORE INSERT | `NOW()` | `set_created_timestamps()` | Sets created_at, updated_at |
| BEFORE UPDATE | `NOW()` | `handle_updated_at()` | Updates updated_at timestamp |
| AFTER INSERT | `create_personal_org()` | `handle_new_user()` | Creates personal organization for user |

### blocks

| Operation | Database Trigger | Python Function | What it does |
|-----------|-----------------|-----------------|--------------|
| BEFORE INSERT | `set_version()` | `before_insert()` | Sets version=1 for new blocks |
| BEFORE INSERT | `gen_random_uuid()` | `generate_uuid()` | Generates UUID for id |
| BEFORE INSERT | `NOW()` | `set_created_timestamps()` | Sets created_at, updated_at |
| BEFORE UPDATE | `NOW()` | `handle_updated_at()` | Updates updated_at timestamp |
| BEFORE UPDATE | `increment_version()` | `before_update()` | Increments version on update |

### organization_members

| Operation | Database Trigger | Python Function | What it does |
|-----------|-----------------|-----------------|--------------|
| BEFORE INSERT | `gen_random_uuid()` | `generate_uuid()` | Generates UUID for id |
| BEFORE INSERT | `NOW()` | `set_created_timestamps()` | Sets created_at, updated_at |
| BEFORE INSERT | `set_status()` | `before_insert()` | Sets status='active' if not provided |
| BEFORE UPDATE | `NOW()` | `handle_updated_at()` | Updates updated_at timestamp |
| CHECK CONSTRAINT | `member_limit()` | `check_member_limits()` | Validates org hasn't exceeded member limit |

### project_members

| Operation | Database Trigger | Python Function | What it does |
|-----------|-----------------|-----------------|--------------|
| BEFORE INSERT | `gen_random_uuid()` | `generate_uuid()` | Generates UUID for id |
| BEFORE INSERT | `NOW()` | `set_created_timestamps()` | Sets created_at, updated_at |
| BEFORE INSERT | `set_status()` | `before_insert()` | Sets status='active' if not provided |
| BEFORE UPDATE | `NOW()` | `handle_updated_at()` | Updates updated_at timestamp |

### trace_links

| Operation | Database Trigger | Python Function | What it does |
|-----------|-----------------|-----------------|--------------|
| BEFORE INSERT | `set_version()` | `before_insert()` | Sets version=1 for new links |
| BEFORE INSERT | `gen_random_uuid()` | `generate_uuid()` | Generates UUID for id |
| BEFORE INSERT | `NOW()` | `set_created_timestamps()` | Sets created_at, updated_at |
| BEFORE UPDATE | `NOW()` | `handle_updated_at()` | Updates updated_at timestamp |
| BEFORE UPDATE | `increment_version()` | `before_update()` | Increments version on update |

### assignments

| Operation | Database Trigger | Python Function | What it does |
|-----------|-----------------|-----------------|--------------|
| BEFORE INSERT | `set_version()` | `before_insert()` | Sets version=1 for new assignments |
| BEFORE INSERT | `gen_random_uuid()` | `generate_uuid()` | Generates UUID for id |
| BEFORE INSERT | `NOW()` | `set_created_timestamps()` | Sets created_at, updated_at |
| BEFORE UPDATE | `NOW()` | `handle_updated_at()` | Updates updated_at timestamp |
| BEFORE UPDATE | `increment_version()` | `before_update()` | Increments version on update |

## Universal Triggers

These apply to ALL tables:

### Audit Fields

| Field | Database Default | Python Function | When Applied |
|-------|-----------------|-----------------|--------------|
| `id` | `gen_random_uuid()` | `generate_uuid()` | BEFORE INSERT if not provided |
| `created_at` | `NOW()` | `set_created_timestamps()` | BEFORE INSERT |
| `updated_at` | `NOW()` | `set_created_timestamps()` | BEFORE INSERT |
| `updated_at` | `NOW()` | `handle_updated_at()` | BEFORE UPDATE |
| `created_by` | From auth context | `before_insert()` | BEFORE INSERT |
| `updated_by` | From auth context | `before_update()` | BEFORE UPDATE |

### Soft Delete

For tables with soft delete support:

| Field | Database Trigger | Python Function | When Applied |
|-------|-----------------|-----------------|--------------|
| `is_deleted` | `false` | `before_insert()` | BEFORE INSERT (default) |
| `is_deleted` | `true` | `handle_soft_delete()` | Soft delete operation |
| `deleted_at` | `NOW()` | `handle_soft_delete()` | Soft delete operation |
| `deleted_by` | From auth context | `handle_soft_delete()` | Soft delete operation |
| `is_deleted` | `false` | `handle_restore()` | Restore operation |
| `deleted_at` | `NULL` | `handle_restore()` | Restore operation |
| `deleted_by` | `NULL` | `handle_restore()` | Restore operation |

### Version Control

For tables with version column:

| Field | Database Trigger | Python Function | When Applied |
|-------|-----------------|-----------------|--------------|
| `version` | `1` | `before_insert()` | BEFORE INSERT |
| `version` | `version + 1` | `before_update()` | BEFORE UPDATE |

## Constraint Validation

### Slug Constraints

| Constraint | Database | Python Function | Validation |
|-----------|----------|-----------------|------------|
| `slug_format` | CHECK | `normalize_slug()` | Must start with letter |
| `slug_lowercase` | CHECK | `normalize_slug()` | Must be lowercase |
| `slug_alphanumeric` | CHECK | `normalize_slug()` | Only letters, numbers, hyphens |
| `slug_unique` | UNIQUE | Database enforced | Not validated in Python (DB handles) |

### Member Limits

| Plan | Max Members | Database | Python Function |
|------|-------------|----------|-----------------|
| free | 5 | Constraint | `check_member_limits()` |
| pro | 50 | Constraint | `check_member_limits()` |
| enterprise | unlimited | Constraint | `check_member_limits()` |

### Hierarchy Constraints

| Constraint | Database | Python Function | Validation |
|-----------|----------|-----------------|------------|
| No self-parent | CHECK | `check_requirement_cycle()` | requirement_id ≠ parent_id |
| No cycles | Trigger + closure | `check_requirement_cycle()` | Parent can't be descendant |

### Optimistic Locking

| Mechanism | Database | Python Function | How It Works |
|-----------|----------|-----------------|--------------|
| Version check | WHERE version = ? | `check_version_and_update()` | Update fails if version mismatch |
| Version increment | version + 1 | `before_update()` | Version incremented on success |

## Side Effect Triggers

### Organization Creation

```
INSERT organizations
  ↓ (AFTER INSERT trigger)
INSERT organization_members (owner)
```

**Python:**
```python
org_data = emulator.before_insert(Tables.ORGANIZATIONS, org_data)
org = await db.insert(Tables.ORGANIZATIONS, org_data)

side_effects = emulator.after_insert(Tables.ORGANIZATIONS, org)
# Returns: [(Tables.ORGANIZATION_MEMBERS, member_data)]

for table, data in side_effects:
    await db.insert(table, data)
```

### User Signup

```
INSERT profiles
  ↓ (AFTER INSERT trigger)
INSERT organizations (personal org)
  ↓ (AFTER INSERT trigger)
INSERT organization_members (owner)
  ↓
UPDATE profiles (set personal_organization_id)
```

**Python:**
```python
profile_data = emulator.before_insert(Tables.PROFILES, profile_data)
profile = await db.insert(Tables.PROFILES, profile_data)

side_effects = emulator.after_insert(Tables.PROFILES, profile)
# Returns: [(Tables.ORGANIZATIONS, org_data)]

for table, data in side_effects:
    org_data = emulator.before_insert(table, data)
    org = await db.insert(table, org_data)

    org_side_effects = emulator.after_insert(table, org)
    for org_table, org_member_data in org_side_effects:
        await db.insert(org_table, org_member_data)

await db.update(Tables.PROFILES, {"personal_organization_id": org["id"]}, {"id": profile["id"]})
```

### Requirement Hierarchy

```
INSERT requirements (with parent_id)
  ↓ (AFTER INSERT trigger)
INSERT requirements_closure (self-reference + inherited ancestors)
```

**Python:**
```python
req_data = emulator.before_insert(Tables.REQUIREMENTS, req_data)
req = await db.insert(Tables.REQUIREMENTS, req_data)

# Get parent's closure entries
parent_closure = await db.query(
    Tables.REQUIREMENTS_CLOSURE,
    filters={"descendant_id": req_data["parent_id"]}
)

closure_entries = handle_requirement_hierarchy(req, parent_closure)
for entry in closure_entries:
    await db.insert(Tables.REQUIREMENTS_CLOSURE, entry)
```

### Soft Delete Cascade

```
UPDATE organizations SET is_deleted = true
  ↓ (AFTER UPDATE trigger)
UPDATE projects SET is_deleted = true WHERE organization_id = ?
  ↓ (AFTER UPDATE trigger)
UPDATE documents SET is_deleted = true WHERE project_id = ?
  ↓ (AFTER UPDATE trigger)
UPDATE requirements SET is_deleted = true WHERE document_id = ?
```

**Python:**
```python
# Soft delete org
org_update = handle_soft_delete({}, user_id)
await db.update(Tables.ORGANIZATIONS, org_update, {"id": org_id})

# Cascade to projects
projects = await db.query(Tables.PROJECTS, filters={"organization_id": org_id})
for project in projects:
    proj_update = handle_soft_delete({}, user_id)
    await db.update(Tables.PROJECTS, proj_update, {"id": project["id"]})

    # Cascade to documents
    documents = await db.query(Tables.DOCUMENTS, filters={"project_id": project["id"]})
    for doc in documents:
        doc_update = handle_soft_delete({}, user_id)
        await db.update(Tables.DOCUMENTS, doc_update, {"id": doc["id"]})

        # Cascade to requirements
        requirements = await db.query(Tables.REQUIREMENTS, filters={"document_id": doc["id"]})
        for req in requirements:
            req_update = handle_soft_delete({}, user_id)
            await db.update(Tables.REQUIREMENTS, req_update, {"id": req["id"]})
```

## Database Functions (RPCs)

Some triggers call database functions that don't have direct Python equivalents:

| Database Function | Purpose | Python Approach |
|------------------|---------|-----------------|
| `gen_random_uuid()` | Generate UUID | `uuid.uuid4()` |
| `NOW()` | Current timestamp | `datetime.now(timezone.utc)` |
| `get_user_id()` | Get current user from auth | Pass explicitly via `set_user_context()` |
| `update_member_count()` | Update org member count | Database handles (async) |
| `update_fts_vector()` | Update full-text search | Database handles (async) |
| `generate_embedding()` | Generate vector embedding | Separate process (not in triggers) |

## Database Defaults Not Replicated

Some database defaults are intentionally NOT replicated in Python:

| Field | Database Default | Why Not in Python |
|-------|-----------------|-------------------|
| `fts_vector` | Auto-generated | Too complex, let DB handle |
| `embedding` | NULL initially | Generated async, separate process |
| `member_count` | 0 | Calculated field, DB maintains |
| `storage_used` | 0 | Calculated field, DB maintains |
| `star_count` | 0 | Calculated field, DB maintains |

These fields are managed by the database or separate background processes.

## Verification Checklist

To verify Python triggers match database:

- [ ] Slug normalization produces identical results
- [ ] Timestamps are in same format (ISO 8601)
- [ ] External IDs use same format (PREFIX-XXXXXXXX)
- [ ] Default values match database defaults
- [ ] Version increments work correctly
- [ ] Side effects create same records
- [ ] Constraints validate the same way
- [ ] Soft delete sets same fields
- [ ] Audit fields (created_by, updated_by) set correctly

## See Also

- `schemas/triggers.py` - Python implementation
- `docs/TRIGGERS_DOCUMENTATION.md` - Full reference
- `docs/TRIGGERS_USAGE_EXAMPLE.md` - Usage examples
- Database schema documentation (Supabase dashboard)
