# Supabase Database Functions

Complete reference for all custom database functions in the Atoms MCP system.

**Last Updated:** 2025-10-09
**Project ID:** ydogoylwenufckscqijp

---

## Table of Contents

1. [Authentication & Authorization](#authentication--authorization)
2. [Organization Management](#organization-management)
3. [Requirements Hierarchy (Closure Table)](#requirements-hierarchy-closure-table)
4. [Vector Search Functions](#vector-search-functions)
5. [Full-Text Search Functions](#full-text-search-functions)
6. [Utility Functions](#utility-functions)
7. [Billing & Resource Management](#billing--resource-management)
8. [Session Management](#session-management)
9. [Debug & Validation Functions](#debug--validation-functions)

---

## Authentication & Authorization

### `user_can_access_project`

**Purpose:** Check if a user has access to a project (as creator, member, or org member).

**Signature:**
```sql
user_can_access_project(p_project_id uuid, p_user_id uuid) RETURNS boolean
```

**Properties:**
- Language: SQL
- Volatility: STABLE
- Security: SECURITY DEFINER

**Implementation:**
```sql
CREATE OR REPLACE FUNCTION public.user_can_access_project(p_project_id uuid, p_user_id uuid)
 RETURNS boolean
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public', 'pg_temp'
AS $function$
    SELECT EXISTS (
        SELECT 1
        FROM projects p
        WHERE p.id = p_project_id
          AND (
                p.created_by = p_user_id
             OR EXISTS (
                    SELECT 1
                    FROM project_members pm
                    WHERE pm.project_id = p.id
                      AND pm.user_id = p_user_id
                      AND pm.status = 'active'
                      AND pm.is_deleted = false
                )
             OR EXISTS (
                    SELECT 1
                    FROM organization_members om
                    WHERE om.organization_id = p.organization_id
                      AND om.user_id = p_user_id
                      AND om.status = 'active'
                      AND om.is_deleted = false
                )
          )
    );
$function$
```

---

### `has_project_access`

**Purpose:** Check if user has project access with optional role requirement.

**Signature:**
```sql
has_project_access(
    project_id uuid,
    user_id uuid,
    required_role project_role DEFAULT NULL
) RETURNS boolean
```

**Properties:**
- Language: PL/pgSQL
- Volatility: VOLATILE
- Security: SECURITY DEFINER

**Implementation:**
```sql
CREATE OR REPLACE FUNCTION public.has_project_access(project_id uuid, user_id uuid, required_role project_role DEFAULT NULL::project_role)
 RETURNS boolean
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare
  project_record projects%rowtype;
  member_role project_role;
begin
  -- Get project details
  select * into project_record from projects where id = project_id;

  -- Check if project exists
  if project_record is null then
    return false;
  end if;

  -- Check public access
  if project_record.visibility = 'public' and required_role is null then
    return true;
  end if;

  -- Get user's role in project
  select role into member_role
  from project_members
  where project_id = project_id
  and user_id = user_id
  and status = 'active';

  -- If no specific role required, any membership is sufficient
  if required_role is null then
    return member_role is not null;
  end if;

  -- Check if user's role meets the required level
  return case member_role
    when 'owner' then true
    when 'admin' then required_role != 'owner'
    when 'maintainer' then required_role in ('maintainer', 'contributor', 'viewer')
    when 'contributor' then required_role in ('contributor', 'viewer')
    when 'viewer' then required_role = 'viewer'
    else false
  end;
end;
$function$
```

---

### `is_project_owner_or_admin`

**Purpose:** Check if user is owner or admin of a project.

**Signature:**
```sql
is_project_owner_or_admin(project_id uuid, user_id uuid) RETURNS boolean
```

**Properties:**
- Language: PL/pgSQL
- Volatility: VOLATILE
- Security: SECURITY DEFINER

**Implementation:**
```sql
CREATE OR REPLACE FUNCTION public.is_project_owner_or_admin(project_id uuid, user_id uuid)
 RETURNS boolean
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public', 'pg_temp'
AS $function$
begin
  return exists (
    select 1 from project_members pm
    where pm.project_id = is_project_owner_or_admin.project_id
    and pm.user_id = is_project_owner_or_admin.user_id
    and pm.role in ('owner', 'admin')
    and pm.status = 'active'
  );
end;
$function$
```

---

### `project_member_can_manage`

**Purpose:** Check if user can manage a project (owner/admin or org owner/admin).

**Signature:**
```sql
project_member_can_manage(p_project_id uuid, p_user_id uuid) RETURNS boolean
```

**Properties:**
- Language: SQL
- Volatility: STABLE
- Security: SECURITY DEFINER

**Implementation:**
```sql
CREATE OR REPLACE FUNCTION public.project_member_can_manage(p_project_id uuid, p_user_id uuid)
 RETURNS boolean
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public', 'pg_temp'
AS $function$
    SELECT EXISTS (
        SELECT 1
        FROM project_members pm
        WHERE pm.project_id = p_project_id
          AND pm.user_id = p_user_id
          AND pm.role IN ('owner', 'admin')
          AND pm.status = 'active'
          AND pm.is_deleted = false
    )
    OR EXISTS (
        SELECT 1
        FROM projects p
        WHERE p.id = p_project_id
          AND p.created_by = p_user_id
    )
    OR EXISTS (
        SELECT 1
        FROM organization_members om
        JOIN projects p ON p.organization_id = om.organization_id
        WHERE p.id = p_project_id
          AND om.user_id = p_user_id
          AND om.role IN ('owner', 'admin')
          AND om.status = 'active'
          AND om.is_deleted = false
    );
$function$
```

---

### `project_has_members`

**Purpose:** Check if a project has any members.

**Signature:**
```sql
project_has_members(p_project_id uuid) RETURNS boolean
```

**Properties:**
- Language: SQL
- Volatility: STABLE
- Security: SECURITY DEFINER

**Implementation:**
```sql
CREATE OR REPLACE FUNCTION public.project_has_members(p_project_id uuid)
 RETURNS boolean
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public', 'pg_temp'
AS $function$
    SELECT EXISTS (
        SELECT 1
        FROM project_members pm
        WHERE pm.project_id = p_project_id
          AND pm.is_deleted = false
    );
$function$
```

---

### `is_super_admin`

**Purpose:** Check if user has super admin privileges.

**Signature:**
```sql
is_super_admin(p_user_id uuid) RETURNS boolean
```

**Properties:**
- Language: SQL
- Volatility: STABLE
- Security: SECURITY DEFINER

**Implementation:**
```sql
CREATE OR REPLACE FUNCTION public.is_super_admin(p_user_id uuid)
 RETURNS boolean
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public', 'pg_temp'
AS $function$
    SELECT EXISTS (
        SELECT 1
        FROM user_roles
        WHERE user_id = p_user_id
          AND admin_role = 'super_admin'
    );
$function$
```

---

## Organization Management

### `create_personal_organization`

**Purpose:** Create a personal organization for a user.

**Signature:**
```sql
create_personal_organization(user_id uuid, name text) RETURNS uuid
```

**Properties:**
- Language: PL/pgSQL
- Volatility: VOLATILE
- Security: SECURITY DEFINER

**Implementation:**
```sql
CREATE OR REPLACE FUNCTION public.create_personal_organization(user_id uuid, name text)
 RETURNS uuid
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare
  org_id uuid;
begin
  -- Create the personal organization
  insert into organizations (
    name,
    slug,
    type,
    created_by,
    updated_by,
    billing_plan,
    settings,
    max_members,
    max_monthly_requests
  ) values (
    name || '''s Playground',
    generate_slug(name || '''s Playground'),
    'personal',
    user_id,
    user_id,
    'free',
    jsonb_build_object(
      'default_access_level', 'private',
      'allow_public_projects', false,
      'require_2fa', false
    ),
    1,  -- personal orgs limited to 1 member
    50
  )
  returning id into org_id;

  -- Add the user as owner
  insert into organization_members (
    organization_id,
    user_id,
    role,
    status
  ) values (
    org_id,
    user_id,
    'owner',
    'active'
  );

  return org_id;
end;
$function$
```

---

### `get_user_organizations`

**Purpose:** Get all organizations a user belongs to.

**Signature:**
```sql
get_user_organizations(
    user_id uuid,
    include_inactive boolean DEFAULT false
) RETURNS TABLE(
    id uuid,
    name text,
    slug text,
    role user_role_type,
    type organization_type,
    billing_plan billing_plan,
    member_count integer,
    is_personal boolean,
    status user_status
)
```

**Properties:**
- Language: SQL
- Volatility: STABLE
- Security: SECURITY DEFINER

**Implementation:**
```sql
CREATE OR REPLACE FUNCTION public.get_user_organizations(user_id uuid, include_inactive boolean DEFAULT false)
 RETURNS TABLE(id uuid, name text, slug text, role user_role_type, type organization_type, billing_plan billing_plan, member_count integer, is_personal boolean, status user_status)
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public', 'pg_temp'
AS $function$
  select
    o.id,
    o.name,
    o.slug,
    om.role,
    o.type,
    o.billing_plan,
    o.member_count,
    o.type = 'personal' as is_personal,
    o.status
  from organizations o
  join organization_members om on om.organization_id = o.id
  where om.user_id = user_id
  and (include_inactive or o.status = 'active')
  order by
    o.type = 'personal' desc,  -- Personal org first
    o.name asc;                -- Then alphabetically
$function$
```

---

### `get_user_organization_ids`

**Purpose:** Get IDs of organizations a user belongs to.

**Signature:**
```sql
get_user_organization_ids(p_user_id uuid) RETURNS TABLE(organization_id uuid)
```

**Properties:**
- Language: SQL
- Volatility: STABLE
- Security: SECURITY DEFINER

**Implementation:**
```sql
CREATE OR REPLACE FUNCTION public.get_user_organization_ids(p_user_id uuid)
 RETURNS TABLE(organization_id uuid)
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public', 'pg_temp'
AS $function$
    SELECT organization_id
    FROM organization_members
    WHERE user_id = p_user_id
      AND status = 'active'
      AND is_deleted = false;
$function$
```

---

### `switch_organization`

**Purpose:** Switch user's current organization context.

**Signature:**
```sql
switch_organization(user_id uuid, org_id uuid) RETURNS boolean
```

**Properties:**
- Language: PL/pgSQL
- Volatility: VOLATILE
- Security: SECURITY DEFINER

**Implementation:**
```sql
CREATE OR REPLACE FUNCTION public.switch_organization(user_id uuid, org_id uuid)
 RETURNS boolean
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public', 'pg_temp'
AS $function$
begin
  -- Verify user is a member of the organization
  if not exists (
    select 1 from organization_members
    where organization_id = org_id
    and user_id = user_id
    and status = 'active'
  ) then
    return false;
  end if;

  -- Update current organization
  update profiles
  set current_organization_id = org_id
  where id = user_id;

  return true;
end;
$function$
```

---

### `invite_organization_member`

**Purpose:** Create an invitation for a new organization member.

**Signature:**
```sql
invite_organization_member(
    org_id uuid,
    email text,
    role user_role_type DEFAULT 'member'
) RETURNS uuid
```

**Properties:**
- Language: PL/pgSQL
- Volatility: VOLATILE
- Security: SECURITY DEFINER

**Implementation:**
```sql
CREATE OR REPLACE FUNCTION public.invite_organization_member(org_id uuid, email text, role user_role_type DEFAULT 'member'::user_role_type)
 RETURNS uuid
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public', 'pg_temp'
AS $function$
declare
  invitation_id uuid;
begin
  -- Verify invoker has permission
  if not exists (
    select 1 from organization_members
    where organization_id = org_id
    and user_id = auth.uid()
    and role in ('owner', 'admin')
    and status = 'active'
  ) then
    raise exception 'Insufficient permissions';
  end if;

  -- Check organization type
  if exists (
    select 1 from organizations
    where id = org_id
    and type = 'personal'
  ) then
    raise exception 'Cannot invite members to personal organizations';
  end if;

  -- Create invitation
  insert into organization_invitations (
    organization_id,
    email,
    role,
    invited_by
  ) values (
    org_id,
    email,
    role,
    auth.uid()
  )
  returning id into invitation_id;

  return invitation_id;
end;
$function$
```

---

### `accept_invitation`

**Purpose:** Accept an organization invitation.

**Signature:**
```sql
accept_invitation(invitation_token uuid) RETURNS boolean
```

**Properties:**
- Language: PL/pgSQL
- Volatility: VOLATILE
- Security: SECURITY DEFINER

**Implementation:**
```sql
CREATE OR REPLACE FUNCTION public.accept_invitation(invitation_token uuid)
 RETURNS boolean
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public', 'pg_temp'
AS $function$
declare
  inv record;
begin
  -- Get and validate invitation
  select * into inv
  from organization_invitations
  where token = invitation_token
  and status = 'pending'
  and expires_at > now();

  if not found then
    return false;
  end if;

  -- Add member
  insert into organization_members (
    organization_id,
    user_id,
    role
  ) values (
    inv.organization_id,
    auth.uid(),
    inv.role
  );

  -- Update invitation status
  update organization_invitations
  set status = 'accepted'
  where token = invitation_token;

  return true;
end;
$function$
```

---

## Requirements Hierarchy (Closure Table)

### `check_requirement_cycle`

**Purpose:** Check if creating a relationship would create a cycle.

**Signature:**
```sql
check_requirement_cycle(p_ancestor_id uuid, p_descendant_id uuid) RETURNS boolean
```

**Properties:**
- Language: PL/pgSQL
- Volatility: VOLATILE

**Returns:** `TRUE` if cycle exists, `FALSE` otherwise

---

### `create_requirement_relationship`

**Purpose:** Create a parent-child relationship between requirements using closure table pattern.

**Signature:**
```sql
create_requirement_relationship(
    p_ancestor_id uuid,
    p_descendant_id uuid,
    p_created_by uuid
) RETURNS TABLE(
    success boolean,
    error_code text,
    message text,
    relationships_created integer
)
```

**Properties:**
- Language: PL/pgSQL
- Volatility: VOLATILE

**Error Codes:**
- `INVALID_INPUT` - Missing required parameters
- `ANCESTOR_NOT_FOUND` - Ancestor requirement doesn't exist
- `DESCENDANT_NOT_FOUND` - Descendant requirement doesn't exist
- `RELATIONSHIP_EXISTS` - Relationship already exists
- `CYCLE_DETECTED` - Would create circular reference

---

### `delete_requirement_relationship`

**Purpose:** Delete a parent-child relationship and all transitive paths through it.

**Signature:**
```sql
delete_requirement_relationship(
    p_ancestor_id uuid,
    p_descendant_id uuid,
    p_updated_by uuid
) RETURNS TABLE(
    success boolean,
    error_code text,
    message text,
    relationships_deleted integer
)
```

**Properties:**
- Language: PL/pgSQL
- Volatility: VOLATILE

**Algorithm:**
Deletes all paths (X, Y) where:
- X has a path to p_ancestor_id
- p_descendant_id has a path to Y

---

### `get_requirement_ancestors`

**Purpose:** Get all ancestor requirements (parents) of a requirement.

**Signature:**
```sql
get_requirement_ancestors(
    p_descendant_id uuid,
    p_max_depth integer DEFAULT NULL
) RETURNS TABLE(
    requirement_id uuid,
    title text,
    depth integer,
    direct_parent boolean
)
```

**Properties:**
- Language: PL/pgSQL
- Volatility: VOLATILE

---

### `get_requirement_descendants`

**Purpose:** Get all descendant requirements (children) of a requirement.

**Signature:**
```sql
get_requirement_descendants(
    p_ancestor_id uuid,
    p_max_depth integer DEFAULT NULL
) RETURNS TABLE(
    requirement_id uuid,
    title text,
    depth integer,
    direct_parent boolean
)
```

**Properties:**
- Language: PL/pgSQL
- Volatility: VOLATILE

---

### `get_requirement_tree`

**Purpose:** Get hierarchical tree view of requirements for a project.

**Signature:**
```sql
get_requirement_tree(p_project_id uuid DEFAULT NULL)
RETURNS TABLE(
    requirement_id uuid,
    title text,
    parent_id uuid,
    depth integer,
    path text,
    has_children boolean
)
```

**Properties:**
- Language: PL/pgSQL
- Volatility: VOLATILE
- Security: SECURITY DEFINER

---

## Vector Search Functions

All vector search functions use cosine similarity with pgvector extension.

### `match_documents`

**Purpose:** Semantic search for documents using vector embeddings.

**Signature:**
```sql
match_documents(
    query_embedding vector,
    match_count integer DEFAULT 10,
    similarity_threshold double precision DEFAULT 0.7,
    filters jsonb DEFAULT NULL
) RETURNS TABLE(
    id text,
    content text,
    metadata jsonb,
    similarity double precision
)
```

**Properties:**
- Language: SQL
- Volatility: STABLE

**Filters:**
- `project_id` - Filter by project

---

### `match_projects`

**Purpose:** Semantic search for projects using vector embeddings.

**Signature:**
```sql
match_projects(
    query_embedding vector,
    match_count integer DEFAULT 10,
    similarity_threshold double precision DEFAULT 0.7,
    filters jsonb DEFAULT NULL
) RETURNS TABLE(
    id text,
    content text,
    metadata jsonb,
    similarity double precision
)
```

**Properties:**
- Language: SQL
- Volatility: STABLE

**Filters:**
- `organization_id` - Filter by organization

---

### `match_organizations`

**Purpose:** Semantic search for organizations using vector embeddings.

**Signature:**
```sql
match_organizations(
    query_embedding vector,
    match_count integer DEFAULT 10,
    similarity_threshold double precision DEFAULT 0.7,
    filters jsonb DEFAULT NULL
) RETURNS TABLE(
    id text,
    content text,
    metadata jsonb,
    similarity double precision
)
```

**Properties:**
- Language: SQL
- Volatility: STABLE

---

### `match_requirements`

**Purpose:** Semantic search for requirements using vector embeddings.

**Signature:**
```sql
match_requirements(
    query_embedding vector,
    match_count integer DEFAULT 10,
    similarity_threshold double precision DEFAULT 0.7,
    filters jsonb DEFAULT NULL
) RETURNS TABLE(
    id text,
    content text,
    metadata jsonb,
    similarity double precision
)
```

**Properties:**
- Language: SQL
- Volatility: STABLE

**Filters:**
- `document_id` - Filter by document

---

### `match_tests`

**Purpose:** Placeholder for test vector search (currently disabled due to permission issues).

**Signature:**
```sql
match_tests(
    query_embedding vector,
    match_count integer DEFAULT 10,
    similarity_threshold double precision DEFAULT 0.7,
    filters jsonb DEFAULT NULL
) RETURNS TABLE(
    id text,
    content text,
    metadata jsonb,
    similarity double precision
)
```

**Properties:**
- Language: SQL
- Volatility: STABLE

**Note:** Returns empty result set.

---

## Full-Text Search Functions

All FTS functions use PostgreSQL's `websearch_to_tsquery` for natural language queries.

### `search_documents_fts`

**Purpose:** Full-text search for documents.

**Signature:**
```sql
search_documents_fts(
    search_query text,
    match_limit integer DEFAULT 10,
    filters jsonb DEFAULT NULL
) RETURNS TABLE(
    id text,
    name text,
    description text,
    rank real
)
```

---

### `search_projects_fts`

**Purpose:** Full-text search for projects.

**Signature:**
```sql
search_projects_fts(
    search_query text,
    match_limit integer DEFAULT 10,
    filters jsonb DEFAULT NULL
) RETURNS TABLE(
    id text,
    name text,
    description text,
    rank real
)
```

---

### `search_organizations_fts`

**Purpose:** Full-text search for organizations.

**Signature:**
```sql
search_organizations_fts(
    search_query text,
    match_limit integer DEFAULT 10,
    filters jsonb DEFAULT NULL
) RETURNS TABLE(
    id text,
    name text,
    description text,
    rank real
)
```

---

### `search_requirements_fts`

**Purpose:** Full-text search for requirements.

**Signature:**
```sql
search_requirements_fts(
    search_query text,
    match_limit integer DEFAULT 10,
    filters jsonb DEFAULT NULL
) RETURNS TABLE(
    id text,
    name text,
    description text,
    rank real
)
```

---

## Utility Functions

### `generate_slug`

**Purpose:** Generate a unique URL-safe slug from a name.

**Signature:**
```sql
generate_slug(name text) RETURNS text
```

**Properties:**
- Language: PL/pgSQL
- Volatility: VOLATILE

**Algorithm:**
1. Convert to lowercase
2. Replace special chars with hyphens
3. Remove consecutive hyphens
4. Ensure 2-63 character length
5. Add counter suffix if not unique

---

### `normalize_slug`

**Purpose:** Normalize a slug to standard format.

**Signature:**
```sql
normalize_slug(input_slug text) RETURNS text
```

**Properties:**
- Language: PL/pgSQL
- Volatility: VOLATILE

---

### `is_valid_slug`

**Purpose:** Validate slug format.

**Signature:**
```sql
is_valid_slug(slug text) RETURNS boolean
```

**Properties:**
- Language: PL/pgSQL
- Volatility: IMMUTABLE

**Pattern:** `^[a-z0-9][a-z0-9-]{1,61}[a-z0-9]$`

---

### `is_valid_email`

**Purpose:** Validate email address format.

**Signature:**
```sql
is_valid_email(email text) RETURNS boolean
```

**Properties:**
- Language: PL/pgSQL
- Volatility: IMMUTABLE

**Pattern:** `^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$`

---

### `create_columns_for_table_block`

**Purpose:** Create columns for a table block from base properties.

**Signature:**
```sql
create_columns_for_table_block(block_id uuid, p_org_id uuid) RETURNS void
```

**Properties:**
- Language: PL/pgSQL
- Volatility: VOLATILE

---

### `reorder_blocks`

**Purpose:** Reorder blocks in a document.

**Signature:**
```sql
reorder_blocks(
    p_document_id uuid,
    p_block_ids uuid[],
    p_user_id uuid
) RETURNS void
```

**Properties:**
- Language: PL/pgSQL
- Volatility: VOLATILE

---

### `handle_entity_update`

**Purpose:** Placeholder for entity update audit logging.

**Signature:**
```sql
handle_entity_update() RETURNS void
```

**Properties:**
- Language: PL/pgSQL
- Volatility: VOLATILE

**Note:** Currently does nothing but can be extended for audit trails.

---

## Billing & Resource Management

### `can_use_resource`

**Purpose:** Check if organization can use a resource based on billing limits.

**Signature:**
```sql
can_use_resource(
    org_id uuid,
    resource_type text,
    quantity integer
) RETURNS boolean
```

**Properties:**
- Language: PL/pgSQL
- Volatility: VOLATILE
- Security: SECURITY DEFINER

---

### `log_resource_usage`

**Purpose:** Log resource usage and update billing cache.

**Signature:**
```sql
log_resource_usage(
    org_id uuid,
    user_id uuid,
    feature text,
    quantity integer,
    unit_type text,
    metadata jsonb DEFAULT '{}'
) RETURNS boolean
```

**Properties:**
- Language: PL/pgSQL
- Volatility: VOLATILE
- Security: SECURITY DEFINER

**Returns:** `FALSE` if resource limit exceeded

---

### `get_organization_usage`

**Purpose:** Get usage statistics for an organization in a time period.

**Signature:**
```sql
get_organization_usage(
    org_id uuid,
    start_date timestamptz DEFAULT date_trunc('month', CURRENT_TIMESTAMP),
    end_date timestamptz DEFAULT date_trunc('month', CURRENT_TIMESTAMP) + interval '1 month'
) RETURNS jsonb
```

**Properties:**
- Language: PL/pgSQL
- Volatility: STABLE
- Security: SECURITY DEFINER

**Returns:**
```json
{
  "period": {"start": "...", "end": "..."},
  "usage": {
    "tokens": 0,
    "storage": 0,
    "api_calls": 0
  },
  "features": [...],
  "users": [...]
}
```

---

### `initialize_billing`

**Purpose:** Initialize billing cache for a new organization.

**Signature:**
```sql
initialize_billing(user_id uuid, org_id uuid) RETURNS void
```

**Properties:**
- Language: PL/pgSQL
- Volatility: VOLATILE
- Security: SECURITY DEFINER

---

### `sync_billing_data`

**Purpose:** Sync billing data from Stripe and update cache.

**Signature:**
```sql
sync_billing_data(org_id uuid) RETURNS jsonb
```

**Properties:**
- Language: PL/pgSQL
- Volatility: VOLATILE
- Security: SECURITY DEFINER

---

### `create_notification`

**Purpose:** Create a notification for a user.

**Signature:**
```sql
create_notification(
    user_id uuid,
    type notification_type,
    title text,
    message text DEFAULT NULL,
    metadata jsonb DEFAULT '{}'
) RETURNS uuid
```

**Properties:**
- Language: PL/pgSQL
- Volatility: VOLATILE
- Security: SECURITY DEFINER

**Returns:** Notification ID

---

## Session Management

### `get_active_session`

**Purpose:** Retrieve active MCP session data.

**Signature:**
```sql
get_active_session(p_session_id text)
RETURNS TABLE(
    session_id text,
    user_id uuid,
    oauth_data jsonb,
    mcp_state jsonb,
    created_at timestamptz,
    updated_at timestamptz,
    expires_at timestamptz
)
```

**Properties:**
- Language: PL/pgSQL
- Volatility: VOLATILE
- Security: SECURITY DEFINER

---

### `update_session_activity`

**Purpose:** Update session expiration time (keep-alive).

**Signature:**
```sql
update_session_activity(
    p_session_id text,
    p_ttl_hours integer DEFAULT 24
) RETURNS boolean
```

**Properties:**
- Language: PL/pgSQL
- Volatility: VOLATILE
- Security: SECURITY DEFINER

---

### `cleanup_expired_sessions`

**Purpose:** Delete expired MCP sessions.

**Signature:**
```sql
cleanup_expired_sessions() RETURNS void
```

**Properties:**
- Language: SQL
- Volatility: VOLATILE

---

### `cleanup_expired_oauth_tokens`

**Purpose:** Delete expired OAuth tokens (auth codes, access tokens, refresh tokens).

**Signature:**
```sql
cleanup_expired_oauth_tokens() RETURNS void
```

**Properties:**
- Language: PL/pgSQL
- Volatility: VOLATILE
- Security: SECURITY DEFINER

---

### `update_embedding_backfill`

**Purpose:** Update embedding for a record during backfill process.

**Signature:**
```sql
update_embedding_backfill(
    p_table_name text,
    p_record_id uuid,
    p_embedding vector,
    p_updated_by uuid
) RETURNS void
```

**Properties:**
- Language: PL/pgSQL
- Volatility: VOLATILE
- Security: SECURITY DEFINER

**Note:** Uses dynamic SQL with `format()`.

---

## Debug & Validation Functions

### `debug_closure_state`

**Purpose:** View entire requirements closure table state with names.

**Signature:**
```sql
debug_closure_state()
RETURNS TABLE(
    ancestor_name text,
    descendant_name text,
    depth integer,
    relationship_type text,
    ancestor_id uuid,
    descendant_id uuid
)
```

**Properties:**
- Language: PL/pgSQL
- Volatility: VOLATILE

---

### `debug_delete_logic_step_by_step`

**Purpose:** Debug deletion logic step-by-step to understand what will be deleted.

**Signature:**
```sql
debug_delete_logic_step_by_step(p_ancestor_id uuid, p_descendant_id uuid)
RETURNS TABLE(step_name text, result_count integer, details text)
```

**Properties:**
- Language: PL/pgSQL
- Volatility: VOLATILE

---

### `debug_deletion_preview`

**Purpose:** Preview what will be deleted with detailed reasoning.

**Signature:**
```sql
debug_deletion_preview(p_ancestor_id uuid, p_descendant_id uuid)
RETURNS TABLE(
    will_delete_ancestor_name text,
    will_delete_descendant_name text,
    will_delete_depth integer,
    deletion_reason text,
    path_to_ancestor_id uuid,
    path_from_descendant_id uuid
)
```

**Properties:**
- Language: PL/pgSQL
- Volatility: VOLATILE

---

### `validate_closure_integrity`

**Purpose:** Validate closure table integrity with multiple checks.

**Signature:**
```sql
validate_closure_integrity()
RETURNS TABLE(
    check_name text,
    is_valid boolean,
    issue_count integer,
    details text
)
```

**Properties:**
- Language: PL/pgSQL
- Volatility: VOLATILE

**Checks:**
1. Self-relationships exist for all requirements
2. Transitive closure property is maintained
3. No duplicate relationships
4. Depth consistency (no negative depths)

---

### `setup_debug_test_scenario`

**Purpose:** Create test data for debugging closure table operations.

**Signature:**
```sql
setup_debug_test_scenario() RETURNS text
```

**Properties:**
- Language: PL/pgSQL
- Volatility: VOLATILE

**Creates:**
- Grand Requirement
- Parent Requirement
- Child Requirement
- Sibling Requirement

**Structure:**
```
Grand
├── Parent
│   └── Child
└── Sibling
```

---

### `test_specific_deletion`

**Purpose:** Test deletion of a specific relationship with preview.

**Signature:**
```sql
test_specific_deletion(p_ancestor_id uuid, p_descendant_id uuid)
RETURNS TABLE(test_step text, result_count integer, details text)
```

**Properties:**
- Language: PL/pgSQL
- Volatility: VOLATILE

---

## Function Dependencies

### High-Level Dependencies

```
Authentication & Authorization
├── has_project_access
│   └── (called by RLS policies)
├── user_can_access_project
│   └── (called by RLS policies)
└── project_member_can_manage
    └── (called by RLS policies)

Organization Management
├── create_personal_organization
│   └── generate_slug
└── invite_organization_member
    └── accept_invitation

Requirements Hierarchy
├── create_requirement_relationship
│   └── check_requirement_cycle
├── delete_requirement_relationship
│   └── (uses closure table algorithm)
└── get_requirement_tree
    └── (recursive CTE)

Billing & Resource Management
├── log_resource_usage
│   ├── can_use_resource
│   └── sync_billing_data
└── get_organization_usage
    └── (aggregates usage_logs)

Session Management
├── get_active_session
└── update_session_activity
```

---

## Best Practices

### When to use SECURITY DEFINER

Functions marked `SECURITY DEFINER` run with the privileges of the function owner, not the caller:

- ✅ Use for: Authentication checks, billing operations, cross-table operations
- ❌ Avoid for: Simple queries, functions called very frequently
- ⚠️ Always set `search_path` to prevent schema injection

### Vector Search Performance

1. Ensure embeddings are indexed with HNSW or IVFFlat
2. Adjust `similarity_threshold` based on use case (0.5-0.8 typical)
3. Use `match_count` wisely - lower is faster
4. Consider using FTS for exact keyword matches

### Closure Table Operations

1. Always use provided functions, never modify closure table directly
2. Run `validate_closure_integrity()` after bulk operations
3. Use debug functions to understand deletions before executing
4. Self-relationships (depth=0) must exist for all requirements

---

## Migration Notes

### Adding New Vector Search Functions

Template for new entity type:

```sql
CREATE OR REPLACE FUNCTION match_<entity_type>(
    query_embedding vector,
    match_count integer DEFAULT 10,
    similarity_threshold double precision DEFAULT 0.7,
    filters jsonb DEFAULT NULL
) RETURNS TABLE(
    id text,
    content text,
    metadata jsonb,
    similarity double precision
) LANGUAGE sql STABLE
SET search_path TO 'public', 'pg_temp'
AS $$
  SELECT
    e.id::text,
    COALESCE(e.description, e.name, 'No content')::text as content,
    jsonb_build_object(
      'name', e.name,
      -- Add relevant metadata fields
    ) as metadata,
    GREATEST(0, 1 - (e.embedding <=> query_embedding)) as similarity
  FROM <entity_table> e
  WHERE e.embedding IS NOT NULL
    AND COALESCE(e.is_deleted, false) = false
    AND GREATEST(0, 1 - (e.embedding <=> query_embedding)) >= similarity_threshold
    -- Add filter logic
  ORDER BY similarity DESC
  LIMIT GREATEST(match_count, 1);
$$;
```

---

## Related Documentation

- [Database Schema Reference](./schema.md)
- [RLS Policies](./rls_policies.md)
- [Triggers](./triggers.md)
- [Vector Search Guide](../docs/VECTOR_SEARCH.md)
- [Closure Table Pattern](../docs/CLOSURE_TABLE.md)

---

*Generated: 2025-10-09*
