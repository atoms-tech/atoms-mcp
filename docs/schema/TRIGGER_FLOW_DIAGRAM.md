# Trigger Emulation Flow Diagram

## CREATE ENTITY Flow

```
User Request (create_entity)
         ↓
1. Resolve smart defaults ("auto" → actual IDs)
         ↓
2. Apply defaults (_apply_defaults)
         ↓
3. Validate required fields
         ↓
4. Schema validation (validate_before_create)
         ↓
5. Get table name
         ↓
6. Set user context
   └→ trigger_emulator.set_user_context(user_id)
         ↓
7. BEFORE INSERT TRIGGER EMULATION ⚡
   └→ trigger_emulator.before_insert(table, data)
      ├─ Generate ID if missing
      ├─ Set timestamps (created_at, updated_at)
      ├─ Set audit fields (created_by, updated_by)
      ├─ Normalize slugs
      ├─ Set table-specific defaults
      ├─ Generate external_id (requirements)
      └─ Sync properties (requirements)
         ↓
8. RLS Policy validation
         ↓
9. Database INSERT
         ↓
10. AFTER INSERT TRIGGER EMULATION ⚡
    └→ trigger_emulator.after_insert(table, result)
       ├─ Auto-add org owner to members
       ├─ Create personal organization
       └─ Handle requirement hierarchy
         ↓
11. Generate embedding (async, non-blocking)
         ↓
12. Return result to user
```

## UPDATE ENTITY Flow

```
User Request (update_entity)
         ↓
1. Schema validation (validate_before_update)
         ↓
2. Get table name
         ↓
3. Fetch existing record
         ↓
4. RLS Policy validation
         ↓
5. Get user_id (with fallback to existing record)
         ↓
6. Set user context
   └→ trigger_emulator.set_user_context(user_id)
         ↓
7. BEFORE UPDATE TRIGGER EMULATION ⚡
   └→ trigger_emulator.before_update(table, old_data, new_data)
      ├─ Update timestamp (updated_at)
      ├─ Set updated_by
      ├─ Increment version
      ├─ Normalize slug if changed
      └─ Sync properties (requirements)
         ↓
8. Database UPDATE
         ↓
9. AFTER UPDATE TRIGGER EMULATION ⚡
   └→ trigger_emulator.after_update(table, old_data, new_data)
      ├─ Cascade soft delete
      └─ Update requirement hierarchies
         ↓
10. Include relationships (if requested)
         ↓
11. Return result to user
```

## Error Handling Flow

```
Trigger Validation Error
         ↓
Caught in try-except
         ↓
Re-raised as: "Trigger validation failed: {error}"
         ↓
Returned to user with error context
```

```
Side Effect Failure
         ↓
Caught in try-except
         ↓
Logged as warning
         ↓
Main operation continues ✓
```

## Key Components

### TriggerEmulator Class
- **Location:** `/schemas/triggers.py`
- **Methods:**
  - `set_user_context(user_id)` - Set current user
  - `before_insert(table, data)` - Transform data before insert
  - `before_update(table, old, new)` - Transform data before update
  - `after_insert(table, data)` - Generate side effects after insert
  - `after_update(table, old, new)` - Generate side effects after update

### Integration Points
- **Location:** `/tools/entity.py`
- **Initialization:** Line 63 - `self.trigger_emulator = TriggerEmulator()`
- **CREATE:** Lines 265-294
- **UPDATE:** Lines 400-442

## Data Transformations

### Before Insert
| Field | Transformation | Tables |
|-------|---------------|--------|
| `id` | Generate UUID if missing | All |
| `created_at` | Set to NOW() | All |
| `updated_at` | Set to NOW() | All |
| `created_by` | Set to user_id | All (with audit) |
| `updated_by` | Set to user_id | All (with audit) |
| `slug` | Normalize to lowercase, hyphenated | orgs, projects, docs |
| `external_id` | Generate REQ-{uuid} | requirements |
| `properties` | Sync with base fields | requirements |
| `billing_plan` | Default to "free" | organizations |
| `version` | Set to 1 | documents, requirements |

### Before Update
| Field | Transformation | Tables |
|-------|---------------|--------|
| `updated_at` | Set to NOW() | All |
| `updated_by` | Set to user_id | All (with audit) |
| `version` | Increment by 1 | documents, requirements |
| `slug` | Normalize if changed | orgs, projects, docs |
| `properties` | Sync with base fields | requirements |

### Side Effects

#### After Insert
| Table | Side Effect | Result |
|-------|------------|--------|
| `organizations` | Auto-add owner | Insert into `organization_members` |
| `profiles` | Create personal org | Insert into `organizations` + update profile |
| `requirements` | Update hierarchy | Insert into `requirements_closure` |

#### After Update
| Table | Side Effect | Result |
|-------|------------|--------|
| `organizations` | Cascade soft delete | Update related `projects` |
| `projects` | Cascade soft delete | Update related `documents` |
| `documents` | Cascade soft delete | Update related `requirements` |

## Testing Coverage

### Unit Tests Needed
- ✅ Slug normalization (valid/invalid inputs)
- ✅ External ID generation
- ✅ Timestamp setting
- ✅ Version incrementing
- ✅ Property syncing (requirements)
- ✅ User context handling
- ✅ Error handling (validation failures)
- ✅ Side effect handling (success/failure)

### Integration Tests Needed
- ✅ Full CREATE flow with triggers
- ✅ Full UPDATE flow with triggers
- ✅ Organization creation → owner auto-add
- ✅ User creation → personal org creation
- ✅ Soft delete → cascade to children
- ✅ Concurrent updates (version locking)

## Performance Considerations

### Benefits
- ✅ Reduced database round-trips (client-side transformations)
- ✅ Early validation (catch errors before DB)
- ✅ Parallel side effects possible
- ✅ Async embedding generation (non-blocking)

### Optimizations
- ✅ Side effects logged but don't block main operation
- ✅ User context cached per operation
- ✅ Existing record fetched once (shared for RLS + triggers)
- ✅ Embedding generation runs in background
