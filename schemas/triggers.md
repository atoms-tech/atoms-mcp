# Database Triggers Reference

This document provides a comprehensive reference for all triggers and trigger functions in the database.

## Table of Contents
- [Overview](#overview)
- [Triggers by Table](#triggers-by-table)
- [Trigger Functions](#trigger-functions)
- [Dependencies](#dependencies)

## Overview

Total triggers: 27
Total trigger functions: 23

### Trigger Types
- **BEFORE triggers**: 17 (data validation, normalization, audit fields)
- **AFTER triggers**: 10 (cascading operations, logging, cleanup)

### Common Patterns
1. **Slug Normalization**: Applied to documents, organizations, and projects
2. **Audit Fields**: Automated tracking of created_by, updated_by, deleted_by
3. **Soft Delete**: Cascading soft deletes with timestamp tracking
4. **Version Control**: Optimistic locking for concurrent updates
5. **Limit Enforcement**: Organization and member limits based on billing
6. **Auto-membership**: Automatic owner assignment on creation

---

## Triggers by Table

### billing_cache

#### tr_log_billing_cache
- **Timing**: AFTER
- **Events**: INSERT, UPDATE
- **Orientation**: ROW
- **Function**: `handle_audit_log()`
- **Purpose**: Audit logging for billing cache changes

---

### blocks

#### after_insert_table_block
- **Timing**: AFTER
- **Events**: INSERT
- **Orientation**: ROW
- **Function**: `trigger_create_columns_for_table_block()`
- **Purpose**: Automatically create columns when a table block is inserted
- **Definition**:
```sql
CREATE TRIGGER after_insert_table_block
AFTER INSERT ON public.blocks
FOR EACH ROW
EXECUTE FUNCTION trigger_create_columns_for_table_block()
```

---

### diagram_element_links

#### update_diagram_element_links_updated_at
- **Timing**: BEFORE
- **Events**: UPDATE
- **Orientation**: ROW
- **Function**: `update_updated_at_column()`
- **Purpose**: Automatically update the updated_at timestamp

---

### documents

#### tr_check_document_version
- **Timing**: BEFORE
- **Events**: UPDATE
- **Orientation**: ROW
- **Function**: `check_version_and_update()`
- **Purpose**: Optimistic locking - prevents concurrent update conflicts
- **Special Logic**:
  - Allows embedding updates without version conflicts
  - Auto-increments version on updates
  - Raises exception on concurrent modifications

#### tr_normalize_slug_documents
- **Timing**: BEFORE
- **Events**: INSERT, UPDATE
- **Orientation**: ROW
- **Function**: `apply_slug_normalization()`
- **Purpose**: Normalize slugs to ensure consistent formatting

#### tr_soft_delete_documents
- **Timing**: BEFORE
- **Events**: UPDATE
- **Orientation**: ROW
- **Condition**: `WHEN (new.is_deleted IS DISTINCT FROM old.is_deleted)`
- **Function**: `handle_soft_delete()`
- **Purpose**: Cascading soft delete to related entities
- **Cascades to**:
  - blocks
  - document_property_schemas
  - requirements

---

### excalidraw_diagrams

#### update_excalidraw_diagrams_updated_at
- **Timing**: BEFORE
- **Events**: UPDATE
- **Orientation**: ROW
- **Function**: `update_updated_at_column()`
- **Purpose**: Automatically update the updated_at timestamp

---

### external_documents

#### before_insert_external_documents
- **Timing**: BEFORE
- **Events**: INSERT
- **Orientation**: ROW
- **Function**: `set_user_fields()`
- **Purpose**: Set created_by, updated_by, and owned_by to current user

---

### oauth_authorization_codes

#### oauth_cleanup_trigger
- **Timing**: AFTER
- **Events**: INSERT
- **Orientation**: STATEMENT
- **Function**: `cleanup_oauth_trigger()`
- **Purpose**: Clean up expired OAuth tokens when new codes are inserted

---

### oauth_clients

#### update_oauth_clients_updated_at
- **Timing**: BEFORE
- **Events**: UPDATE
- **Orientation**: ROW
- **Function**: `update_updated_at_column()`
- **Purpose**: Automatically update the updated_at timestamp

---

### organization_invitations

#### tr_update_org_invites
- **Timing**: BEFORE
- **Events**: UPDATE
- **Orientation**: ROW
- **Function**: `handle_updated_by()`
- **Purpose**: Update updated_at and updated_by fields, handle soft delete

---

### organization_members

#### check_member_limits
- **Timing**: BEFORE
- **Events**: INSERT
- **Orientation**: ROW
- **Function**: `check_organization_limits()`
- **Purpose**: Enforce organization member limits based on billing plan
- **Logic**:
  - Checks current member count vs billing plan limit
  - Raises exception if limit exceeded

#### tr_check_personal_org_member_limit
- **Timing**: BEFORE
- **Events**: INSERT, UPDATE
- **Orientation**: ROW
- **Function**: `enforce_personal_org_member_limit()`
- **Purpose**: Ensure personal organizations have only one member
- **Logic**:
  - Checks if organization type is 'personal'
  - Raises exception if adding more than one active member

#### tr_update_org_members
- **Timing**: BEFORE
- **Events**: UPDATE
- **Orientation**: ROW
- **Function**: `handle_updated_by()`
- **Purpose**: Update updated_at and updated_by fields, handle soft delete

---

### organizations

#### tr_normalize_slug_organizations
- **Timing**: BEFORE
- **Events**: INSERT, UPDATE
- **Orientation**: ROW
- **Function**: `apply_slug_normalization()`
- **Purpose**: Normalize slugs to ensure consistent formatting

#### tr_organization_audit
- **Timing**: BEFORE
- **Events**: INSERT, UPDATE
- **Orientation**: ROW
- **Function**: `handle_organization_audit_fields()`
- **Purpose**: Set created_by and updated_by audit fields
- **Logic**:
  - On INSERT: Sets both created_by and updated_by
  - On UPDATE: Only updates updated_by

#### trigger_auto_add_org_owner
- **Timing**: AFTER
- **Events**: INSERT
- **Orientation**: ROW
- **Function**: `auto_add_org_owner()`
- **Purpose**: Automatically add creator as owner in organization_members
- **Security**: SECURITY DEFINER
- **Logic**:
  - Inserts creator as 'owner' role with 'active' status
  - Uses ON CONFLICT to update existing memberships

---

### profiles

#### tr_log_profiles
- **Timing**: AFTER
- **Events**: INSERT, UPDATE, DELETE
- **Orientation**: ROW
- **Function**: `handle_audit_log()`
- **Purpose**: Audit logging for all profile changes

#### tr_update_profiles
- **Timing**: BEFORE
- **Events**: UPDATE
- **Orientation**: ROW
- **Function**: `handle_updated_at()`
- **Purpose**: Update updated_at timestamp and handle soft delete

---

### projects

#### after_project_insert
- **Timing**: AFTER
- **Events**: INSERT
- **Orientation**: ROW
- **Function**: `handle_new_project()`
- **Purpose**: Automatically add creator as owner in project_members
- **Security**: SECURITY DEFINER
- **Logic**:
  - Inserts creator as 'owner' role with 'active' status
  - Uses ON CONFLICT to update existing memberships

#### tr_normalize_slug_projects
- **Timing**: BEFORE
- **Events**: INSERT, UPDATE
- **Orientation**: ROW
- **Function**: `apply_slug_normalization()`
- **Purpose**: Normalize slugs to ensure consistent formatting

---

### react_flow_diagrams

#### update_react_flow_diagrams_updated_at
- **Timing**: BEFORE
- **Events**: UPDATE
- **Orientation**: ROW
- **Function**: `update_updated_at_column()`
- **Purpose**: Automatically update the updated_at timestamp

---

### requirements

#### update_requirements_properties
- **Timing**: BEFORE
- **Events**: UPDATE
- **Orientation**: ROW
- **Function**: `sync_requirements_properties()`
- **Purpose**: Sync core fields to properties JSONB column
- **Synced Fields**:
  - name → properties.Name.value
  - description → properties.Description.value
  - status → properties.Status.value
  - priority → properties.Priority.value
  - external_id → properties.External_ID.value

---

### stripe_customers

#### tr_log_stripe_customers
- **Timing**: AFTER
- **Events**: INSERT, UPDATE, DELETE
- **Orientation**: ROW
- **Function**: `handle_audit_log()`
- **Purpose**: Audit logging for stripe customer changes

#### tr_update_stripe_customers
- **Timing**: BEFORE
- **Events**: UPDATE
- **Orientation**: ROW
- **Function**: `handle_stripe_customer_update()`
- **Purpose**: Update updated_at timestamp

---

## Trigger Functions

### apply_slug_normalization()
**Returns**: trigger
**Language**: plpgsql

**Purpose**: Normalizes slug values using the normalize_slug() function

**Source**:
```sql
BEGIN
    IF NEW.slug IS NOT NULL THEN
        NEW.slug := public.normalize_slug(NEW.slug);
    END IF;
    RETURN NEW;
END;
```

**Used by**:
- documents (tr_normalize_slug_documents)
- organizations (tr_normalize_slug_organizations)
- projects (tr_normalize_slug_projects)

---

### auto_add_org_owner()
**Returns**: trigger
**Language**: plpgsql
**Security**: DEFINER
**Search Path**: public

**Purpose**: Automatically adds organization creator as owner member

**Source**:
```sql
BEGIN
    -- Insert creator as owner in organization_members
    INSERT INTO organization_members (
        organization_id,
        user_id,
        role,
        status,
        updated_by
    ) VALUES (
        NEW.id,
        NEW.created_by,
        'owner'::user_role_type,
        'active'::user_status,
        NEW.created_by
    )
    ON CONFLICT (organization_id, user_id)
    DO UPDATE SET
        role = 'owner'::user_role_type,
        status = 'active'::user_status,
        is_deleted = false,
        updated_by = EXCLUDED.updated_by,
        updated_at = timezone('utc'::text, now());

    RETURN NEW;
END;
```

**Used by**:
- organizations (trigger_auto_add_org_owner)

---

### check_organization_limits()
**Returns**: trigger
**Language**: plpgsql
**Security**: DEFINER
**Search Path**: public, pg_temp

**Purpose**: Enforces organization member limits based on billing plan

**Source**:
```sql
declare
  member_count integer;
  max_members integer;
begin
  -- Get current member count and limit
  select
    o.member_count,
    (bc.billing_status->'features'->>'max_members')::integer
  into member_count, max_members
  from organizations o
  join billing_cache bc on bc.organization_id = o.id
  where o.id = new.organization_id;

  -- Check if adding member would exceed limit
  if max_members is not null and member_count >= max_members then
    raise exception 'Organization member limit reached';
  end if;

  return new;
end;
```

**Used by**:
- organization_members (check_member_limits)

---

### check_version_and_update()
**Returns**: trigger
**Language**: plpgsql
**Search Path**: public, pg_temp

**Purpose**: Implements optimistic locking with special handling for embedding updates

**Source**:
```sql
BEGIN
  -- Skip version check if ONLY embedding column changed
  -- This allows embedding backfills to work without triggering optimistic locking
  IF (NEW.embedding IS DISTINCT FROM OLD.embedding) THEN
    -- Check if ONLY embedding changed (no other meaningful columns changed)
    -- We allow version to stay the same or increment
    IF (NEW.version = OLD.version OR NEW.version = OLD.version + 1) AND
       (NEW.name = OLD.name OR (NEW.name IS NULL AND OLD.name IS NULL)) AND
       (NEW.description  = OLD.description  OR (NEW.description  IS NULL AND OLD.description  IS NULL)) AND
       (NEW.is_deleted = OLD.is_deleted) THEN
      -- Only embedding changed, allow it without version check
      -- Keep the version as-is (don't increment)
      NEW.version = OLD.version;
      RETURN NEW;
    END IF;
  END IF;

  -- For all other updates, enforce optimistic locking
  -- Check for version conflicts (optimistic locking)
  -- This prevents concurrent updates from overwriting each other
  IF NEW.version < OLD.version THEN
    -- Version went backwards - this is a true concurrent update conflict
    RAISE EXCEPTION 'Concurrent update detected';
  ELSIF NEW.version = OLD.version THEN
    -- Version unchanged - auto-increment it
    -- This is the common case when users update without specifying version
    NEW.version = OLD.version + 1;
  END IF;
  -- If NEW.version > OLD.version, it was explicitly incremented - allow it

  -- Call the regular function (not as a trigger)
  -- This is where the error was occurring before
  PERFORM handle_entity_update();

  -- Return the new row to continue with the update
  RETURN NEW;
END;
```

**Used by**:
- documents (tr_check_document_version)

**Dependencies**:
- Calls: `handle_entity_update()`

---

### cleanup_oauth_trigger()
**Returns**: trigger
**Language**: plpgsql
**Search Path**: public, pg_temp

**Purpose**: Triggers cleanup of expired OAuth tokens

**Source**:
```sql
BEGIN
    -- Clean up expired tokens when new ones are inserted
    PERFORM cleanup_expired_oauth_tokens();
    RETURN NEW;
END;
```

**Used by**:
- oauth_authorization_codes (oauth_cleanup_trigger)

**Dependencies**:
- Calls: `cleanup_expired_oauth_tokens()`

---

### enforce_personal_org_member_limit()
**Returns**: trigger
**Language**: plpgsql
**Search Path**: public, pg_temp

**Purpose**: Ensures personal organizations have only one member

**Source**:
```sql
begin
    if (
        select o.type = 'personal'
        from organizations o
        where o.id = NEW.organization_id
    ) then
        if (
            select count(*) > 0
            from organization_members om
            where om.organization_id = NEW.organization_id
            and om.status = 'active'
            and om.id != COALESCE(NEW.id, '00000000-0000-0000-0000-000000000000')
        ) then
            raise exception 'Personal organizations can only have one member';
        end if;
    end if;
    return new;
end;
```

**Used by**:
- organization_members (tr_check_personal_org_member_limit)

---

### handle_audit_log()
**Returns**: trigger
**Language**: plpgsql
**Search Path**: public, pg_temp

**Purpose**: Creates audit log entries for data changes

**Source**:
```sql
DECLARE
  old_data jsonb;
  new_data jsonb;
  changed_fields jsonb;
  actor_id uuid;
  entity_id uuid;
BEGIN
  -- Determine the actor_id
  actor_id := coalesce(
    auth.uid(),  -- Normal authenticated actions
    '00000000-0000-0000-0000-000000000001'  -- System-initiated actions
  );

  -- Determine the entity_id based on the table being audited
  IF TG_TABLE_NAME = 'billing_cache' THEN
    entity_id := new.organization_id;  -- Use organization_id for billing_cache
  ELSE
    entity_id := coalesce(new.id, old.id);  -- Default to id for other tables
  END IF;

  -- Check if the user exists in auth.users
  IF EXISTS (SELECT 1 FROM auth.users WHERE id = actor_id) THEN
    -- Prepare the data based on operation type
    IF (TG_OP = 'DELETE') THEN
      old_data = row_to_json(old)::jsonb;
      new_data = null;
    ELSIF (TG_OP = 'UPDATE') THEN
      old_data = row_to_json(old)::jsonb;
      new_data = row_to_json(new)::jsonb;
    ELSIF (TG_OP = 'INSERT') THEN
      old_data = null;
      new_data = row_to_json(new)::jsonb;
    END IF;

    -- Insert audit log
    INSERT INTO audit_logs (
      entity_id,
      entity_type,
      action,
      actor_id,
      old_data,
      new_data
    )
    VALUES (
      entity_id,  -- Use the determined entity_id
      TG_TABLE_NAME,
      TG_OP,
      actor_id,
      old_data,
      new_data
    );
  END IF;

  RETURN coalesce(new, old);
END;
```

**Used by**:
- billing_cache (tr_log_billing_cache)
- profiles (tr_log_profiles)
- stripe_customers (tr_log_stripe_customers)

---

### handle_deleted_user()
**Returns**: trigger
**Language**: plpgsql
**Security**: DEFINER
**Search Path**: public

**Purpose**: Handles user deletion by soft deleting profile and memberships

**Source**:
```sql
declare
  personal_org_id uuid;
begin
  -- Get personal organization ID
  select personal_organization_id into personal_org_id
  from profiles
  where id = old.id;

  -- Soft delete the profile
  update profiles
  set status = 'inactive',
      updated_at = timezone('utc'::text, now())
  where id = old.id;

  -- Remove from all organizations except personal
  update organization_members
  set status = 'inactive',
      updated_at = timezone('utc'::text, now())
  where user_id = old.id
  and organization_id != personal_org_id;

  -- Log the deletion
  insert into audit_logs (
    entity_id,
    entity_type,
    action,
    actor_id,
    metadata
  ) values (
    old.id,
    'auth.users',
    'user_deleted',
    old.id,
    jsonb_build_object(
      'email', old.email,
      'deleted_at', timezone('utc'::text, now())
    )
  );

  return old;
end;
```

**Note**: This function is defined but not currently attached to any trigger.

---

### handle_new_project()
**Returns**: trigger
**Language**: plpgsql
**Security**: DEFINER
**Search Path**: public, pg_temp

**Purpose**: Automatically adds project creator as owner member

**Source**:
```sql
BEGIN
  INSERT INTO public.project_members (org_id, project_id, user_id, role, status)
  VALUES (
    NEW.organization_id,
    NEW.id,
    COALESCE(NEW.created_by, auth.uid()),
    'owner'::project_role,
    'active'::user_status
  )
  ON CONFLICT (project_id, user_id)
  DO UPDATE SET
    role = 'owner'::project_role,
    status = 'active'::user_status,
    is_deleted = false,
    updated_at = timezone('utc'::text, now());

  RETURN NEW;
END;
```

**Used by**:
- projects (after_project_insert)

---

### handle_new_user()
**Returns**: trigger
**Language**: plpgsql
**Security**: DEFINER
**Search Path**: public

**Purpose**: Sets up new user profile, personal organization, and billing

**Source**:
```sql
declare
  personal_org_id uuid;
  user_full_name text;
  user_avatar_url text;
begin
  -- Ensure the new record has an id field
  if new.id is null then
    raise exception 'New user record does not have an id field';
  end if;

  -- Extract user metadata or use defaults
  user_full_name := coalesce(new.raw_user_meta_data->>'full_name', 'User');
  user_avatar_url := new.raw_user_meta_data->>'avatar_url';

  -- Create personal organization for the user
  personal_org_id := create_personal_organization(new.id, user_full_name);

  -- Create user profile
  insert into profiles (
    id,
    email,
    full_name,
    avatar_url,
    personal_organization_id,
    current_organization_id,
    preferences
  ) values (
    new.id,
    new.email,
    user_full_name,
    user_avatar_url,
    personal_org_id,
    personal_org_id,  -- Set personal org as current
    jsonb_build_object(
      'theme', 'light',
      'notifications', 'all',
      'email_frequency', 'daily'
    )
  );

  -- Initialize billing/subscription records
  perform initialize_billing(new.id, personal_org_id);

  return new;
exception
  when others then
    -- Log the error in the audit logs
    insert into audit_logs (
      entity_id,
      entity_type,
      action,
      actor_id,
      metadata
    ) values (
      new.id,
      'auth.users',
      'registration_error',
      new.id,
      jsonb_build_object(
        'error', SQLERRM,
        'error_detail', SQLSTATE
      )
    );
    -- Re-raise the exception to ensure the transaction is rolled back
    raise;
end;
```

**Note**: This function is defined but not currently attached to any trigger in the public schema.

**Dependencies**:
- Calls: `create_personal_organization()`
- Calls: `initialize_billing()`

---

### handle_organization_audit_fields()
**Returns**: trigger
**Language**: plpgsql
**Security**: DEFINER

**Purpose**: Sets created_by and updated_by fields for organizations

**Source**:
```sql
BEGIN
    IF TG_OP = 'INSERT' THEN
        -- On INSERT, set both created_by and updated_by
        NEW.created_by = COALESCE(NEW.created_by, auth.uid());
        NEW.updated_by = COALESCE(NEW.updated_by, auth.uid());
    ELSIF TG_OP = 'UPDATE' THEN
        -- On UPDATE, only update updated_by
        NEW.updated_by = auth.uid();
    END IF;
    RETURN NEW;
END;
```

**Used by**:
- organizations (tr_organization_audit)

---

### handle_soft_delete()
**Returns**: trigger
**Language**: plpgsql
**Search Path**: public, pg_temp

**Purpose**: Handles soft delete with cascading to related entities

**Source**:
```sql
begin
  if NEW.is_deleted = true and OLD.is_deleted = false then
    NEW.deleted_at = COALESCE(NEW.deleted_at, now());

    -- Only set deleted_by if auth context is available
    IF auth.uid() IS NOT NULL THEN
      NEW.deleted_by = COALESCE(NEW.deleted_by, auth.uid());
    ELSE
      -- No auth context - use existing updated_by or leave NULL
      NEW.deleted_by = COALESCE(NEW.deleted_by, OLD.updated_by);
    END IF;

    -- Documents cascade to blocks, document_property_schemas, and requirements
    if TG_TABLE_NAME = 'documents' then
      update blocks
      set is_deleted = true, deleted_at = NEW.deleted_at, deleted_by = NEW.deleted_by
      where document_id = NEW.id and is_deleted = false;

      update document_property_schemas
      set is_deleted = true, deleted_at = NEW.deleted_at, deleted_by = NEW.deleted_by
      where document_id = NEW.id and is_deleted = false;

      update requirements
      set is_deleted = true, deleted_at = NEW.deleted_at, deleted_by = NEW.deleted_by
      where document_id = NEW.id and is_deleted = false;

    elsif TG_TABLE_NAME = 'blocks' then
      update block_property_schemas
      set is_deleted = true, deleted_at = NEW.deleted_at, deleted_by = NEW.deleted_by
      where block_id = NEW.id and is_deleted = false;

      update property_kv
      set is_deleted = true, deleted_at = NEW.deleted_at, deleted_by = NEW.deleted_by
      where block_id = NEW.id and is_deleted = false;

    elsif TG_TABLE_NAME = 'requirements' then
      update property_kv
      set is_deleted = true, deleted_at = NEW.deleted_at, deleted_by = NEW.deleted_by
      where requirement_id = NEW.id and is_deleted = false;
    end if;
  end if;
  return NEW;
end;
```

**Used by**:
- documents (tr_soft_delete_documents)

**Cascade Logic**:
- **documents** → blocks, document_property_schemas, requirements
- **blocks** → block_property_schemas, property_kv
- **requirements** → property_kv

---

### handle_stripe_customer_update()
**Returns**: trigger
**Language**: plpgsql
**Search Path**: public, pg_temp

**Purpose**: Updates timestamp on stripe customer changes

**Source**:
```sql
begin
    new.updated_at := timezone('utc'::text, now());
    return new;
end;
```

**Used by**:
- stripe_customers (tr_update_stripe_customers)

---

### handle_updated_at()
**Returns**: trigger
**Language**: plpgsql
**Search Path**: public, pg_temp

**Purpose**: Updates timestamp and handles soft delete fields

**Source**:
```sql
begin
    new.updated_at = timezone('utc'::text, now());

    -- Handle soft delete
    if (new.is_deleted = true and old.is_deleted = false) then
        new.deleted_at = timezone('utc'::text, now());
        new.deleted_by = auth.uid();
    elsif (new.is_deleted = false and old.is_deleted = true) then
        new.deleted_at = null;
        new.deleted_by = null;
    end if;
    return new;
end;
```

**Used by**:
- profiles (tr_update_profiles)

---

### handle_updated_by()
**Returns**: trigger
**Language**: plpgsql
**Search Path**: public, pg_temp

**Purpose**: Updates timestamp, updated_by, and handles soft delete

**Source**:
```sql
begin
    new.updated_at = timezone('utc'::text, now());

    IF new.updated_by IS DISTINCT FROM old.updated_by THEN
        NULL;
    ELSIF auth.uid() IS NOT NULL THEN
        new.updated_by = auth.uid();
    ELSE
        -- Fallback for service role: use created_by
        new.updated_by = COALESCE(old.updated_by, new.created_by, old.created_by);
    END IF;

    if (new.is_deleted = true and old.is_deleted = false) then
        new.deleted_at = timezone('utc'::text, now());
        new.deleted_by = COALESCE(auth.uid(), old.updated_by, old.created_by);
    elsif (new.is_deleted = false and old.is_deleted = true) then
        new.deleted_at = null;
        new.deleted_by = null;
    end if;

    return new;
end;
```

**Used by**:
- organization_invitations (tr_update_org_invites)
- organization_members (tr_update_org_members)

---

### handle_user_login()
**Returns**: trigger
**Language**: plpgsql
**Security**: DEFINER
**Search Path**: public

**Purpose**: Updates last login timestamp and login count

**Source**:
```sql
begin
  update profiles
  set
    last_login_at = timezone('utc'::text, now()),
    login_count = login_count + 1
  where id = new.user_id;
  return new;
end;
```

**Note**: This function is defined but not currently attached to any trigger in the public schema.

---

### set_user_fields()
**Returns**: trigger
**Language**: plpgsql
**Search Path**: public, pg_temp

**Purpose**: Sets user ownership fields on insert

**Source**:
```sql
begin
  -- Set the created_by, updated_by, and owned_by fields to the current user's ID
  new.created_by := (select auth.uid());
  new.updated_by := (select auth.uid());
  new.owned_by := (select auth.uid());
  return new;
end;
```

**Used by**:
- external_documents (before_insert_external_documents)

---

### sync_requirements_properties()
**Returns**: trigger
**Language**: plpgsql
**Search Path**: public, pg_temp

**Purpose**: Syncs requirement core fields to properties JSONB

**Source**:
```sql
BEGIN
    -- Update properties.value based on core fields
    IF NEW.name IS DISTINCT FROM OLD.name THEN
        NEW.properties = jsonb_set(NEW.properties, '{Name, value}', to_jsonb(NEW.name));
    END IF;

    IF NEW.description IS DISTINCT FROM OLD.description THEN
        NEW.properties = jsonb_set(NEW.properties, '{Description, value}', to_jsonb(NEW.description));
    END IF;

    IF NEW.status IS DISTINCT FROM OLD.status THEN
        NEW.properties = jsonb_set(NEW.properties, '{Status, value}', to_jsonb(NEW.status));
    END IF;

    IF NEW.priority IS DISTINCT FROM OLD.priority THEN
        NEW.properties = jsonb_set(NEW.properties, '{Priority, value}', to_jsonb(NEW.priority));
    END IF;

    IF NEW.external_id IS DISTINCT FROM OLD.external_id THEN
        NEW.properties = jsonb_set(NEW.properties, '{External_ID, value}', to_jsonb(NEW.external_id));
    END IF;

    RETURN NEW;
END;
```

**Used by**:
- requirements (update_requirements_properties)

---

### trigger_create_columns_for_table_block()
**Returns**: trigger
**Language**: plpgsql
**Search Path**: public, pg_temp

**Purpose**: Creates columns when a table block is inserted

**Source**:
```sql
BEGIN
    -- Check if the block type is 'table'
    IF NEW.type = 'table' THEN
        -- Call the function to create columns for the new block
        PERFORM create_columns_for_table_block(NEW.id, NEW.org_id);
    END IF;
    RETURN NEW;
END;
```

**Used by**:
- blocks (after_insert_table_block)

**Dependencies**:
- Calls: `create_columns_for_table_block()`

---

### update_requirement_data_updated_at()
**Returns**: trigger
**Language**: plpgsql
**Search Path**: public, pg_temp

**Purpose**: Updates timestamp on requirement data changes

**Source**:
```sql
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
```

**Note**: This function is defined but not currently attached to any trigger.

---

### update_updated_at_column()
**Returns**: trigger
**Language**: plpgsql
**Search Path**: public, pg_temp

**Purpose**: Generic function to update updated_at timestamp

**Source**:
```sql
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
```

**Used by**:
- diagram_element_links (update_diagram_element_links_updated_at)
- excalidraw_diagrams (update_excalidraw_diagrams_updated_at)
- oauth_clients (update_oauth_clients_updated_at)
- react_flow_diagrams (update_react_flow_diagrams_updated_at)

---

### validate_trace_link_insert_update()
**Returns**: trigger
**Language**: plpgsql
**Search Path**: public, pg_temp

**Purpose**: Validates trace links to prevent cycles and self-references

**Source**:
```sql
begin
    -- Prevent self-referential links
    if NEW.source_id = NEW.target_id then
        raise exception 'Self-referential links are not allowed';
    end if;

    -- Prevent cyclic relationships for parent/child relationships
    if NEW.link_type in ('parent_of', 'child_of') then
        if exists (
            with recursive cycle_check as (
                -- Base case
                select
                    target_id as id,
                    array[NEW.source_id, NEW.target_id] as path
                from
                    trace_links
                where
                    source_id = NEW.target_id
                    and link_type in ('parent_of', 'child_of')
                    and not is_deleted

                union all

                -- Recursive case
                select
                    tl.target_id,
                    cc.path || tl.target_id
                from
                    trace_links tl
                    join cycle_check cc on cc.id = tl.source_id
                where
                    tl.link_type in ('parent_of', 'child_of')
                    and not tl.is_deleted
                    and not tl.target_id = any(cc.path)
            )
            select 1 from cycle_check where id = NEW.source_id
        ) then
            raise exception 'Cyclic relationship detected';
        end if;
    end if;

    perform handle_entity_update();

    return NEW;
end;
```

**Note**: This function is defined but not currently attached to any trigger.

**Dependencies**:
- Calls: `handle_entity_update()`

---

## Dependencies

### Function Call Graph

```
Triggers → Trigger Functions → Other Functions
```

#### Trigger Functions that call other functions:

1. **check_version_and_update()** → `handle_entity_update()`
2. **cleanup_oauth_trigger()** → `cleanup_expired_oauth_tokens()`
3. **handle_new_user()** → `create_personal_organization()`, `initialize_billing()`
4. **trigger_create_columns_for_table_block()** → `create_columns_for_table_block()`
5. **validate_trace_link_insert_update()** → `handle_entity_update()`

#### Common External Dependencies:
- `auth.uid()` - Used by most triggers to get current user ID
- `normalize_slug()` - Called by apply_slug_normalization()

### Cascading Relationships

#### Soft Delete Cascades:
```
documents (soft delete)
├── blocks
├── document_property_schemas
└── requirements

blocks (soft delete)
├── block_property_schemas
└── property_kv

requirements (soft delete)
└── property_kv
```

#### Membership Cascades:
```
organizations (insert)
└── organization_members (auto-add owner)

projects (insert)
└── project_members (auto-add owner)

auth.users (insert via handle_new_user)
├── profiles
├── organizations (personal)
│   └── organization_members
└── billing records
```

### Security Considerations

**SECURITY DEFINER Functions** (run with elevated privileges):
- `auto_add_org_owner()` - Bypasses RLS to add org owner
- `check_organization_limits()` - Reads billing data
- `handle_deleted_user()` - Cleans up user data
- `handle_new_project()` - Adds project owner
- `handle_new_user()` - Creates user profile and org
- `handle_organization_audit_fields()` - Sets audit fields

These functions can bypass RLS policies, so they must be carefully reviewed for security implications.

---

## Summary

### Trigger Execution Order (by table)

**documents**:
1. BEFORE UPDATE: tr_normalize_slug_documents
2. BEFORE UPDATE: tr_check_document_version
3. BEFORE UPDATE: tr_soft_delete_documents (conditional)

**organizations**:
1. BEFORE INSERT/UPDATE: tr_normalize_slug_organizations
2. BEFORE INSERT/UPDATE: tr_organization_audit
3. AFTER INSERT: trigger_auto_add_org_owner

**organization_members**:
1. BEFORE INSERT: check_member_limits
2. BEFORE INSERT/UPDATE: tr_check_personal_org_member_limit
3. BEFORE UPDATE: tr_update_org_members

**profiles**:
1. BEFORE UPDATE: tr_update_profiles
2. AFTER INSERT/UPDATE/DELETE: tr_log_profiles

**projects**:
1. BEFORE INSERT/UPDATE: tr_normalize_slug_projects
2. AFTER INSERT: after_project_insert

### Key Patterns

1. **Normalization**: Slugs are normalized on insert/update for documents, organizations, and projects
2. **Audit Trails**: Changes are logged to audit_logs for billing_cache, profiles, and stripe_customers
3. **Automatic Ownership**: Creators are automatically added as owners for organizations and projects
4. **Soft Delete Cascades**: Deleting documents/blocks/requirements cascades to related entities
5. **Limit Enforcement**: Billing limits are enforced at the database level
6. **Version Control**: Optimistic locking prevents concurrent update conflicts
7. **Property Sync**: Requirements sync core fields to JSONB properties column

### Performance Considerations

- Triggers add overhead to INSERT/UPDATE/DELETE operations
- Cascading soft deletes can be expensive for large hierarchies
- Audit logging adds write overhead
- Recursive cycle detection for trace links can be expensive
- Consider disabling triggers during bulk operations if appropriate

---

*Last updated: 2025-10-09*
