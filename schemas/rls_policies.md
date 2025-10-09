# Row Level Security (RLS) Policies Documentation

**Database:** Supabase Project `ydogoylwenufckscqijp`
**Schema:** public
**Generated:** 2025-10-09

## Overview

This document provides comprehensive documentation of all Row Level Security (RLS) policies in the database. RLS policies control which rows users can access in each table based on their authentication status and relationships.

### Tables with RLS Enabled: 35
### Tables without RLS: 3
- `embedding_cache`
- `excalidraw_element_links`
- `project_invitations`
- `rag_embeddings`
- `rag_search_analytics`

### Total Policies: 97

---

## Policy Summary by Table

| Table | Policy Count | RLS Enabled |
|-------|--------------|-------------|
| assignments | 1 | ✓ |
| audit_logs | 1 | ✓ |
| billing_cache | 1 | ✓ |
| blocks | 4 | ✓ |
| columns | 4 | ✓ |
| diagram_element_links | 4 | ✓ |
| documents | 1 | ✓ |
| excalidraw_diagrams | 4 | ✓ |
| external_documents | 2 | ✓ |
| mcp_sessions | 6 | ✓ |
| notifications | 2 | ✓ |
| oauth_access_tokens | 2 | ✓ |
| oauth_authorization_codes | 2 | ✓ |
| oauth_clients | 1 | ✓ |
| oauth_refresh_tokens | 2 | ✓ |
| organization_invitations | 1 | ✓ |
| organization_members | 4 | ✓ |
| organizations | 4 | ✓ |
| profiles | 2 | ✓ |
| project_members | 2 | ✓ |
| projects | 4 | ✓ |
| properties | 4 | ✓ |
| react_flow_diagrams | 4 | ✓ |
| requirement_tests | 4 | ✓ |
| requirements | 4 | ✓ |
| requirements_closure | 1 | ✓ |
| stripe_customers | 1 | ✓ |
| table_rows | 4 | ✓ |
| test_matrix_views | 4 | ✓ |
| test_req | 1 | ✓ |
| trace_links | 1 | ✓ |
| usage_logs | 1 | ✓ |
| user_roles | 3 | ✓ |

---

## Detailed Policy Documentation

### Table: assignments

**RLS Enabled:** Yes
**Policy Count:** 1

#### Policy: "Users can view assignments they have access to"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:**
  ```sql
  ((assignee_id = auth.uid()) OR
   (EXISTS (
     SELECT 1
     FROM project_members pm
     JOIN documents d ON d.project_id = pm.project_id
     WHERE (
       ((assignments.entity_type = 'document'::entity_type AND assignments.entity_id = d.id) OR
        (assignments.entity_type = 'requirement'::entity_type AND
         EXISTS (SELECT 1 FROM requirements r WHERE assignments.entity_id = r.id AND r.document_id = d.id)))
       AND pm.user_id = auth.uid()
       AND pm.status = 'active'::user_status
     )
   )))
  ```
- **WITH CHECK Expression:** None

---

### Table: audit_logs

**RLS Enabled:** Yes
**Policy Count:** 1

#### Policy: "Super admins can view audit logs"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:**
  ```sql
  (auth.uid() IN (
    SELECT user_id FROM user_roles
    WHERE admin_role = 'super_admin'::user_role_type
  ))
  ```
- **WITH CHECK Expression:** None

---

### Table: billing_cache

**RLS Enabled:** Yes
**Policy Count:** 1

#### Policy: "Members can view their organization's billing"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:**
  ```sql
  (EXISTS (
    SELECT 1 FROM organization_members
    WHERE organization_id = billing_cache.organization_id
    AND user_id = auth.uid()
  ))
  ```
- **WITH CHECK Expression:** None

---

### Table: blocks

**RLS Enabled:** Yes
**Policy Count:** 4

#### Policy: "Organization members can create blocks"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:** None
- **WITH CHECK Expression:**
  ```sql
  (document_id IN (
    SELECT d.id
    FROM documents d
    JOIN projects p ON d.project_id = p.id
    WHERE p.organization_id IN (
      SELECT organization_id FROM organization_members
      WHERE user_id = auth.uid()
      AND status = 'active'::user_status
    )
  ))
  ```

#### Policy: "Organization members can delete blocks"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:**
  ```sql
  (document_id IN (
    SELECT d.id
    FROM documents d
    JOIN projects p ON d.project_id = p.id
    WHERE (
      p.organization_id IN (
        SELECT organization_id FROM organization_members
        WHERE user_id = auth.uid()
        AND status = 'active'::user_status
        AND is_deleted = false
      ) OR
      p.id IN (
        SELECT project_id FROM project_members
        WHERE user_id = auth.uid()
        AND status = 'active'::user_status
        AND is_deleted = false
      )
    )
  ))
  ```
- **WITH CHECK Expression:** None

#### Policy: "Organization members can update blocks"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:** (Same as delete policy)
- **WITH CHECK Expression:** None

#### Policy: "Organization members can view blocks"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:** (Same as delete policy)
- **WITH CHECK Expression:** None

---

### Table: columns

**RLS Enabled:** Yes
**Policy Count:** 4

#### Policy: "Org members can create columns"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:** None
- **WITH CHECK Expression:**
  ```sql
  (block_id IN (
    SELECT b.id
    FROM blocks b
    JOIN documents d ON b.document_id = d.id
    JOIN projects p ON d.project_id = p.id
    WHERE p.organization_id IN (
      SELECT organization_id FROM organization_members
      WHERE user_id = auth.uid()
      AND status = 'active'::user_status
    )
  ))
  ```

#### Policy: "Org members can delete columns"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** authenticated
- **USING Expression:**
  ```sql
  (block_id IN (
    SELECT b.id
    FROM blocks b
    JOIN documents d ON b.document_id = d.id
    JOIN projects p ON d.project_id = p.id
    WHERE (
      p.organization_id IN (
        SELECT organization_id FROM organization_members
        WHERE user_id = auth.uid()
        AND status = 'active'::user_status
        AND is_deleted = false
      ) OR
      p.id IN (
        SELECT project_id FROM project_members
        WHERE user_id = auth.uid()
        AND status = 'active'::user_status
        AND is_deleted = false
      )
    )
  ))
  ```
- **WITH CHECK Expression:** None

#### Policy: "Org members can update columns"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** authenticated
- **USING Expression:** (Same as delete policy)
- **WITH CHECK Expression:** None

#### Policy: "Org members can view columns"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** authenticated
- **USING Expression:** (Same as delete policy)
- **WITH CHECK Expression:** None

---

### Table: diagram_element_links

**RLS Enabled:** Yes
**Policy Count:** 4

#### Policy: "Users can create links in their project diagrams"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:** None
- **WITH CHECK Expression:**
  ```sql
  (diagram_id IN (
    SELECT ed.id
    FROM excalidraw_diagrams ed
    JOIN projects p ON ed.project_id = p.id
    JOIN project_members pm ON p.id = pm.project_id
    WHERE pm.user_id = auth.uid()
  ))
  ```

#### Policy: "Users can delete links in their project diagrams"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:** (Same as create policy)
- **WITH CHECK Expression:** None

#### Policy: "Users can update links in their project diagrams"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:** (Same as create policy)
- **WITH CHECK Expression:** None

#### Policy: "Users can view links in their project diagrams"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:** (Same as create policy)
- **WITH CHECK Expression:** None

---

### Table: documents

**RLS Enabled:** Yes
**Policy Count:** 1

#### Policy: "Project members can manage documents"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** authenticated
- **USING Expression:**
  ```sql
  user_can_access_project(project_id, auth.uid())
  ```
- **WITH CHECK Expression:**
  ```sql
  user_can_access_project(project_id, auth.uid())
  ```
- **Dependencies:** Function `user_can_access_project`

---

### Table: excalidraw_diagrams

**RLS Enabled:** Yes
**Policy Count:** 4

#### Policy: "Users can create diagrams in their projects"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:** None
- **WITH CHECK Expression:**
  ```sql
  (project_id IN (
    SELECT p.id
    FROM projects p
    JOIN project_members pm ON p.id = pm.project_id
    WHERE pm.user_id = auth.uid()
  ))
  ```

#### Policy: "Users can delete diagrams in their projects"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:** (Same as create policy)
- **WITH CHECK Expression:** None

#### Policy: "Users can update diagrams in their projects"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:** (Same as create policy)
- **WITH CHECK Expression:** None

#### Policy: "Users can view diagrams in their projects"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:** (Same as create policy)
- **WITH CHECK Expression:** None

---

### Table: external_documents

**RLS Enabled:** Yes
**Policy Count:** 2

#### Policy: "insert"
- **Type:** PERMISSIVE
- **Command:** INSERT
- **Roles:** authenticated
- **USING Expression:** None
- **WITH CHECK Expression:** `true`

#### Policy: "select"
- **Type:** PERMISSIVE
- **Command:** SELECT
- **Roles:** authenticated
- **USING Expression:** `true`
- **WITH CHECK Expression:** None

---

### Table: mcp_sessions

**RLS Enabled:** Yes
**Policy Count:** 6

#### Policy: "Anonymous users can create sessions"
- **Type:** PERMISSIVE
- **Command:** INSERT
- **Roles:** public
- **USING Expression:** None
- **WITH CHECK Expression:** `true`

#### Policy: "Service role has full access"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** service_role
- **USING Expression:** `true`
- **WITH CHECK Expression:** None

#### Policy: "Users can create own sessions"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:** None
- **WITH CHECK Expression:**
  ```sql
  (user_id = auth.uid())
  ```

#### Policy: "Users can delete own sessions"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:**
  ```sql
  (user_id = auth.uid())
  ```
- **WITH CHECK Expression:** None

#### Policy: "Users can update own sessions"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:**
  ```sql
  (user_id = auth.uid())
  ```
- **WITH CHECK Expression:** None

#### Policy: "Users can view own sessions"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:**
  ```sql
  ((auth.uid() = user_id) OR
   ((auth.jwt() ->> 'role'::text) = 'service_role'::text))
  ```
- **WITH CHECK Expression:** None

---

### Table: notifications

**RLS Enabled:** Yes
**Policy Count:** 2

#### Policy: "Users can update own notifications"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:**
  ```sql
  (auth.uid() = user_id)
  ```
- **WITH CHECK Expression:** None

#### Policy: "Users can view own notifications"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:**
  ```sql
  (auth.uid() = user_id)
  ```
- **WITH CHECK Expression:** None

---

### Table: oauth_access_tokens

**RLS Enabled:** Yes
**Policy Count:** 2

#### Policy: "Users can delete own access tokens"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:**
  ```sql
  (user_id = auth.uid())
  ```
- **WITH CHECK Expression:** None

#### Policy: "Users can view own access tokens"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:**
  ```sql
  (user_id = auth.uid())
  ```
- **WITH CHECK Expression:** None

---

### Table: oauth_authorization_codes

**RLS Enabled:** Yes
**Policy Count:** 2

#### Policy: "Users can delete own oauth codes"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:**
  ```sql
  (user_id = auth.uid())
  ```
- **WITH CHECK Expression:** None

#### Policy: "Users can view own oauth codes"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:**
  ```sql
  (user_id = auth.uid())
  ```
- **WITH CHECK Expression:** None

---

### Table: oauth_clients

**RLS Enabled:** Yes
**Policy Count:** 1

#### Policy: "Public can view oauth clients"
- **Type:** PERMISSIVE
- **Command:** SELECT
- **Roles:** public
- **USING Expression:**
  ```sql
  (is_public = true)
  ```
- **WITH CHECK Expression:** None

---

### Table: oauth_refresh_tokens

**RLS Enabled:** Yes
**Policy Count:** 2

#### Policy: "Users can delete own refresh tokens"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:**
  ```sql
  (user_id = auth.uid())
  ```
- **WITH CHECK Expression:** None

#### Policy: "Users can view own refresh tokens"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:**
  ```sql
  (user_id = auth.uid())
  ```
- **WITH CHECK Expression:** None

---

### Table: organization_invitations

**RLS Enabled:** Yes
**Policy Count:** 1

#### Policy: "Owners and admins can manage invitations"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:**
  ```sql
  (EXISTS (
    SELECT 1 FROM organization_members member
    WHERE member.organization_id = organization_invitations.organization_id
    AND member.user_id = auth.uid()
    AND member.role = ANY (ARRAY['owner'::user_role_type, 'admin'::user_role_type])
    AND member.status = 'active'::user_status
  ))
  ```
- **WITH CHECK Expression:** None

---

### Table: organization_members

**RLS Enabled:** Yes
**Policy Count:** 4

#### Policy: "Users can create organization members"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:** None
- **WITH CHECK Expression:**
  ```sql
  (user_id = auth.uid())
  ```

#### Policy: "Users can delete organization members"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:**
  ```sql
  (user_id = auth.uid())
  ```
- **WITH CHECK Expression:** None

#### Policy: "Users can update organization members"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:**
  ```sql
  (user_id = auth.uid())
  ```
- **WITH CHECK Expression:** None

#### Policy: "Users can view org members"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:**
  ```sql
  (organization_id IN (
    SELECT get_user_organization_ids(auth.uid())
  ))
  ```
- **WITH CHECK Expression:** None
- **Dependencies:** Function `get_user_organization_ids`

---

### Table: organizations

**RLS Enabled:** Yes
**Policy Count:** 4

#### Policy: "Users can create organizations"
- **Type:** PERMISSIVE
- **Command:** INSERT
- **Roles:** authenticated
- **USING Expression:** None
- **WITH CHECK Expression:** `true`

#### Policy: "Users can delete organizations"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:**
  ```sql
  (created_by = auth.uid())
  ```
- **WITH CHECK Expression:** None

#### Policy: "Users can update organizations"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:**
  ```sql
  (created_by = auth.uid())
  ```
- **WITH CHECK Expression:** None

#### Policy: "Users can view organizations"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:**
  ```sql
  ((created_by = auth.uid()) OR
   (id IN (
     SELECT organization_id FROM organization_members
     WHERE user_id = auth.uid()
     AND status = 'active'::user_status
   )))
  ```
- **WITH CHECK Expression:** None

---

### Table: profiles

**RLS Enabled:** Yes
**Policy Count:** 2

#### Policy: "Users can update own profile"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:**
  ```sql
  (id = auth.uid())
  ```
- **WITH CHECK Expression:** None

#### Policy: "Users can view all profiles"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:**
  ```sql
  ((id IN (
     SELECT om.user_id
     FROM organization_members om
     WHERE om.organization_id IN (
       SELECT organization_id FROM organization_members
       WHERE user_id = auth.uid()
       AND status = 'active'::user_status
     )
   )) OR
   (id = auth.uid()))
  ```
- **WITH CHECK Expression:** None

---

### Table: project_members

**RLS Enabled:** Yes
**Policy Count:** 2

#### Policy: "Project owners and admins can manage members"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** authenticated
- **USING Expression:**
  ```sql
  project_member_can_manage(project_id, auth.uid())
  ```
- **WITH CHECK Expression:**
  ```sql
  (project_member_can_manage(project_id, auth.uid()) OR
   (NOT project_has_members(project_id)))
  ```
- **Dependencies:** Functions `project_member_can_manage`, `project_has_members`

#### Policy: "Users can view their project memberships"
- **Type:** PERMISSIVE
- **Command:** SELECT
- **Roles:** authenticated
- **USING Expression:**
  ```sql
  ((user_id = auth.uid()) OR
   is_project_owner_or_admin(project_id, auth.uid()))
  ```
- **WITH CHECK Expression:** None
- **Dependencies:** Function `is_project_owner_or_admin`

---

### Table: projects

**RLS Enabled:** Yes
**Policy Count:** 4

#### Policy: "Users can create projects"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:** None
- **WITH CHECK Expression:**
  ```sql
  ((organization_id IN (
     SELECT id FROM organizations
     WHERE created_by = auth.uid()
   )) OR
   (organization_id IN (
     SELECT organization_id FROM organization_members
     WHERE user_id = auth.uid()
     AND status = 'active'::user_status
   )))
  ```

#### Policy: "Users can delete projects"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:**
  ```sql
  (created_by = auth.uid())
  ```
- **WITH CHECK Expression:** None

#### Policy: "Users can update projects"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:**
  ```sql
  (created_by = auth.uid())
  ```
- **WITH CHECK Expression:** None

#### Policy: "Users can view projects"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:**
  ```sql
  ((created_by = auth.uid()) OR
   (organization_id IN (
     SELECT id FROM organizations
     WHERE created_by = auth.uid()
   )) OR
   (organization_id IN (
     SELECT organization_id FROM organization_members
     WHERE user_id = auth.uid()
     AND status = 'active'::user_status
     AND is_deleted = false
   )) OR
   (id IN (
     SELECT project_id FROM project_members
     WHERE user_id = auth.uid()
     AND status = 'active'::user_status
     AND is_deleted = false
   )))
  ```
- **WITH CHECK Expression:** None

---

### Table: properties

**RLS Enabled:** Yes
**Policy Count:** 4

#### Policy: "Org members can create properties"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:** None
- **WITH CHECK Expression:**
  ```sql
  ((document_id IN (
     SELECT d.id
     FROM documents d
     JOIN projects p ON d.project_id = p.id
     WHERE p.organization_id IN (
       SELECT organization_id FROM organization_members
       WHERE user_id = auth.uid()
       AND status = 'active'::user_status
     )
   )) OR
   (project_id IN (
     SELECT id FROM projects
     WHERE organization_id IN (
       SELECT organization_id FROM organization_members
       WHERE user_id = auth.uid()
       AND status = 'active'::user_status
     )
   )) OR
   (org_id IN (
     SELECT organization_id FROM organization_members
     WHERE user_id = auth.uid()
     AND status = 'active'::user_status
   )))
  ```

#### Policy: "Org members can delete properties"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** authenticated
- **USING Expression:**
  ```sql
  ((document_id IN (
     SELECT d.id
     FROM documents d
     JOIN projects p ON d.project_id = p.id
     WHERE (
       p.organization_id IN (
         SELECT organization_id FROM organization_members
         WHERE user_id = auth.uid()
         AND status = 'active'::user_status
         AND is_deleted = false
       ) OR
       p.id IN (
         SELECT project_id FROM project_members
         WHERE user_id = auth.uid()
         AND status = 'active'::user_status
         AND is_deleted = false
       )
     )
   )) OR
   (project_id IN (
     SELECT p.id FROM projects p
     WHERE (
       p.organization_id IN (
         SELECT organization_id FROM organization_members
         WHERE user_id = auth.uid()
         AND status = 'active'::user_status
         AND is_deleted = false
       ) OR
       p.id IN (
         SELECT project_id FROM project_members
         WHERE user_id = auth.uid()
         AND status = 'active'::user_status
         AND is_deleted = false
       )
     )
   )) OR
   (org_id IN (
     SELECT organization_id FROM organization_members
     WHERE user_id = auth.uid()
     AND status = 'active'::user_status
     AND is_deleted = false
   )))
  ```
- **WITH CHECK Expression:** None

#### Policy: "Org members can update properties"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** authenticated
- **USING Expression:** (Same as delete policy)
- **WITH CHECK Expression:** None

#### Policy: "Org members can view properties"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** authenticated
- **USING Expression:** (Same as delete policy)
- **WITH CHECK Expression:** None

---

### Table: react_flow_diagrams

**RLS Enabled:** Yes
**Policy Count:** 4

#### Policy: "Org members can create react_flow_diagrams"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:** None
- **WITH CHECK Expression:**
  ```sql
  (project_id IN (
    SELECT id FROM projects
    WHERE organization_id IN (
      SELECT organization_id FROM organization_members
      WHERE user_id = auth.uid()
      AND status = 'active'::user_status
    )
  ))
  ```

#### Policy: "Org members can delete react_flow_diagrams"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:** (Same as create policy)
- **WITH CHECK Expression:** None

#### Policy: "Org members can update react_flow_diagrams"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:** (Same as create policy)
- **WITH CHECK Expression:** None

#### Policy: "Org members can view react_flow_diagrams"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:** (Same as create policy)
- **WITH CHECK Expression:** None

---

### Table: requirement_tests

**RLS Enabled:** Yes
**Policy Count:** 4

#### Policy: "Org members can create requirement_tests"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:** None
- **WITH CHECK Expression:**
  ```sql
  (requirement_id IN (
    SELECT r.id
    FROM requirements r
    JOIN documents d ON r.document_id = d.id
    JOIN projects p ON d.project_id = p.id
    WHERE p.organization_id IN (
      SELECT organization_id FROM organization_members
      WHERE user_id = auth.uid()
      AND status = 'active'::user_status
    )
  ))
  ```

#### Policy: "Org members can delete requirement_tests"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:** (Same as create policy)
- **WITH CHECK Expression:** None

#### Policy: "Org members can update requirement_tests"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:** (Same as create policy)
- **WITH CHECK Expression:** None

#### Policy: "Org members can view requirement_tests"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:** (Same as create policy)
- **WITH CHECK Expression:** None

---

### Table: requirements

**RLS Enabled:** Yes
**Policy Count:** 4

#### Policy: "Organization members can create requirements"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:** None
- **WITH CHECK Expression:**
  ```sql
  (document_id IN (
    SELECT d.id
    FROM documents d
    JOIN projects p ON d.project_id = p.id
    WHERE p.organization_id IN (
      SELECT organization_id FROM organization_members
      WHERE user_id = auth.uid()
      AND status = 'active'::user_status
    )
  ))
  ```

#### Policy: "Organization members can delete requirements"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:**
  ```sql
  (document_id IN (
    SELECT d.id
    FROM documents d
    JOIN projects p ON d.project_id = p.id
    WHERE (
      p.organization_id IN (
        SELECT organization_id FROM organization_members
        WHERE user_id = auth.uid()
        AND status = 'active'::user_status
        AND is_deleted = false
      ) OR
      p.id IN (
        SELECT project_id FROM project_members
        WHERE user_id = auth.uid()
        AND status = 'active'::user_status
        AND is_deleted = false
      )
    )
  ))
  ```
- **WITH CHECK Expression:** None

#### Policy: "Organization members can update requirements"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:** (Same as delete policy)
- **WITH CHECK Expression:** None

#### Policy: "Organization members can view requirements"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:** (Same as delete policy)
- **WITH CHECK Expression:** None

---

### Table: requirements_closure

**RLS Enabled:** Yes
**Policy Count:** 1

#### Policy: "authenticated_full_access"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** anon
- **USING Expression:** `true`
- **WITH CHECK Expression:** `true`

---

### Table: stripe_customers

**RLS Enabled:** Yes
**Policy Count:** 1

#### Policy: "Organization admins can view stripe data"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:**
  ```sql
  (EXISTS (
    SELECT 1 FROM organization_members
    WHERE organization_id = stripe_customers.organization_id
    AND user_id = auth.uid()
    AND role = ANY (ARRAY['owner'::user_role_type, 'admin'::user_role_type])
  ))
  ```
- **WITH CHECK Expression:** None

---

### Table: table_rows

**RLS Enabled:** Yes
**Policy Count:** 4

#### Policy: "table_rows_delete_authenticated"
- **Type:** PERMISSIVE
- **Command:** DELETE
- **Roles:** authenticated
- **USING Expression:** `true`
- **WITH CHECK Expression:** None

#### Policy: "table_rows_insert_authenticated"
- **Type:** PERMISSIVE
- **Command:** INSERT
- **Roles:** authenticated
- **USING Expression:** None
- **WITH CHECK Expression:** `true`

#### Policy: "table_rows_select_authenticated"
- **Type:** PERMISSIVE
- **Command:** SELECT
- **Roles:** authenticated
- **USING Expression:** `true`
- **WITH CHECK Expression:** None

#### Policy: "table_rows_update_authenticated"
- **Type:** PERMISSIVE
- **Command:** UPDATE
- **Roles:** authenticated
- **USING Expression:** `true`
- **WITH CHECK Expression:** `true`

---

### Table: test_matrix_views

**RLS Enabled:** Yes
**Policy Count:** 4

#### Policy: "Org members can create test_matrix_views"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:** None
- **WITH CHECK Expression:**
  ```sql
  (project_id IN (
    SELECT id FROM projects
    WHERE organization_id IN (
      SELECT organization_id FROM organization_members
      WHERE user_id = auth.uid()
      AND status = 'active'::user_status
    )
  ))
  ```

#### Policy: "Org members can delete test_matrix_views"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:** (Same as create policy)
- **WITH CHECK Expression:** None

#### Policy: "Org members can update test_matrix_views"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:** (Same as create policy)
- **WITH CHECK Expression:** None

#### Policy: "Org members can view test_matrix_views"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:** (Same as create policy)
- **WITH CHECK Expression:** None

---

### Table: test_req

**RLS Enabled:** Yes
**Policy Count:** 1

#### Policy: "Project members can manage tests"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** authenticated
- **USING Expression:**
  ```sql
  user_can_access_project(project_id, auth.uid())
  ```
- **WITH CHECK Expression:**
  ```sql
  user_can_access_project(project_id, auth.uid())
  ```
- **Dependencies:** Function `user_can_access_project`

---

### Table: trace_links

**RLS Enabled:** Yes
**Policy Count:** 1

#### Policy: "Users can manage trace links"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:**
  ```sql
  (EXISTS (
    SELECT 1
    FROM project_members pm
    JOIN documents d ON d.project_id = pm.project_id
    WHERE pm.user_id = auth.uid()
    AND pm.status = 'active'::user_status
    AND (
      ((trace_links.source_type = 'document'::entity_type AND trace_links.source_id = d.id) OR
       (trace_links.target_type = 'document'::entity_type AND trace_links.target_id = d.id) OR
       (EXISTS (
         SELECT 1 FROM requirements r
         WHERE r.document_id = d.id
         AND (
           ((trace_links.source_type = 'requirement'::entity_type AND trace_links.source_id = r.id) OR
            (trace_links.target_type = 'requirement'::entity_type AND trace_links.target_id = r.id))
         )
       )))
    )
  ))
  ```
- **WITH CHECK Expression:** (Same as USING)

---

### Table: usage_logs

**RLS Enabled:** Yes
**Policy Count:** 1

#### Policy: "Members can view their organization's usage"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:**
  ```sql
  (EXISTS (
    SELECT 1 FROM organization_members
    WHERE organization_id = usage_logs.organization_id
    AND user_id = auth.uid()
  ))
  ```
- **WITH CHECK Expression:** None

---

### Table: user_roles

**RLS Enabled:** Yes
**Policy Count:** 3

#### Policy: "Only super admins can create user roles"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:** None
- **WITH CHECK Expression:**
  ```sql
  is_super_admin(auth.uid())
  ```
- **Dependencies:** Function `is_super_admin`

#### Policy: "Only super admins can update user roles"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:**
  ```sql
  is_super_admin(auth.uid())
  ```
- **WITH CHECK Expression:** None
- **Dependencies:** Function `is_super_admin`

#### Policy: "Users can view their own roles"
- **Type:** PERMISSIVE
- **Command:** ALL
- **Roles:** public
- **USING Expression:**
  ```sql
  (auth.uid() = user_id)
  ```
- **WITH CHECK Expression:** None

---

## Function Dependencies

The following PostgreSQL functions are used by RLS policies:

1. **`auth.uid()`** - Supabase built-in function to get current user ID
2. **`auth.jwt()`** - Supabase built-in function to get JWT claims
3. **`user_can_access_project(project_id, user_id)`** - Custom function
4. **`get_user_organization_ids(user_id)`** - Custom function
5. **`project_member_can_manage(project_id, user_id)`** - Custom function
6. **`project_has_members(project_id)`** - Custom function
7. **`is_project_owner_or_admin(project_id, user_id)`** - Custom function
8. **`is_super_admin(user_id)`** - Custom function

---

## Security Notes

### Key Security Patterns

1. **Owner-based Access**: Users can only modify resources they created (organizations, projects)
2. **Membership-based Access**: Access granted through organization or project membership
3. **Role-based Access**: Some operations restricted to specific roles (owner, admin, super_admin)
4. **Status Checks**: Most policies check `status = 'active'` and `is_deleted = false`
5. **Service Role Override**: `mcp_sessions` table allows service role full access

### Tables with Open Policies

- **table_rows**: All authenticated users have full CRUD access (`true` policies)
- **external_documents**: All authenticated users can SELECT and INSERT
- **requirements_closure**: Even anonymous users have full access (role: anon)

### Tables Without RLS

These tables have no row-level security and should be carefully managed:
- `embedding_cache`
- `excalidraw_element_links`
- `project_invitations`
- `rag_embeddings`
- `rag_search_analytics`

---

## Recommendations

1. **Enable RLS on all tables** currently without it, especially:
   - `project_invitations` (contains sensitive invitation data)
   - `rag_embeddings` (may contain sensitive content)

2. **Review open policies** on `table_rows` and `requirements_closure` to ensure they match security requirements

3. **Audit custom functions** used by policies to ensure they correctly implement access control logic

4. **Add logging** for super admin actions (audit_logs, user_roles modifications)

5. **Consider separate policies** for different operations instead of using `ALL` command where possible

---

*Generated using Supabase MCP tools on 2025-10-09*
