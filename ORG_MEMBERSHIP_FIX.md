# Organization Membership Auto-Add Fix

## Problem

When a user creates an organization using the Atoms MCP `workspace_tool`, they are **not automatically added** as a member of that organization. This causes RLS policy violations when they try to create projects:

```
Error: new row violates row-level security policy for table "projects"
```

## Root Cause

1. The `organizations` table has no trigger to auto-add the creator to `organization_members`
2. RLS policies on `projects` table require active membership in `organization_members`
3. User flow breaks: create org → set as active → try to create project → RLS denies

## Solution

### 1. Database Trigger (REQUIRED)

Apply the SQL trigger that automatically adds the creator as "owner" when an organization is created:

**File**: `infrastructure/sql/add_auto_org_membership_trigger.sql`

**To Apply**:
```bash
# Method 1: Supabase Dashboard (Recommended)
# 1. Go to: https://supabase.com/dashboard/project/ydogoylwenufckscqijp/sql/new
# 2. Copy contents of add_auto_org_membership_trigger.sql
# 3. Paste and click RUN

# Method 2: psql
psql "your-connection-string" -f infrastructure/sql/add_auto_org_membership_trigger.sql
```

### 2. Improved Error Messages (DONE)

Enhanced `errors.py` to transform cryptic RLS errors into user-friendly messages:

**Before**:
```json
{
  "error": "INTERNAL_SERVER_ERROR: {'message': 'new row violates row-level security policy for table \"projects\"', ...}"
}
```

**After**:
```json
{
  "code": "UNAUTHORIZED_ORG_ACCESS",
  "message": "You don't have permission to create projects in this organization. Please ensure you're a member of the organization first.",
  "status": 403,
  "details": {
    "hint": "Use the workspace_tool to verify your organization membership or contact an organization owner."
  }
}
```

## How It Works

### Trigger Flow

```sql
1. User creates organization → INSERT INTO organizations
2. Trigger fires: auto_add_org_owner()
3. Automatically inserts into organization_members:
   - organization_id: NEW org ID
   - user_id: creator's ID
   - role: 'owner'
   - status: 'active'
   - is_deleted: false
4. User can now create projects (RLS policies satisfied)
```

### Error Transformation

The `normalize_error()` function now detects common database errors and provides context:

- **RLS violations** → `UNAUTHORIZED_ORG_ACCESS` with membership hint
- **Unique constraints** → `DUPLICATE_ENTRY`
- **Foreign keys** → `INVALID_REFERENCE`

## Expected User Flow

### Before Fix
```
1. Create org → Success
2. Set as active → Success
3. Create project → ❌ RLS error (not a member)
```

### After Fix
```
1. Create org → Success (trigger adds user as owner)
2. Set as active → Success
3. Create project → ✅ Success (user is owner)
```

## Testing

After applying the trigger:

```python
# Test 1: Create organization (should auto-add membership)
result = mcp.workspace_tool(
    operation="set_context",
    context_type="organization",
    entity_id="new-org-id"
)

# Test 2: Verify membership was created
# Query organization_members table to confirm

# Test 3: Create project (should succeed now)
result = mcp.entity_tool(
    operation="create",
    entity_type="project",
    data={
        "name": "Test Project",
        "description": "Testing auto-membership",
        "organization_id": "auto"
    }
)
# Expected: Success
```

## Verification

### Check Trigger Exists
```sql
SELECT
    trigger_name,
    event_manipulation,
    event_object_table,
    action_statement
FROM information_schema.triggers
WHERE trigger_name = 'trigger_auto_add_org_owner';
```

### Check Membership After Org Creation
```sql
SELECT
    om.user_id,
    om.role,
    om.status,
    om.is_deleted
FROM organization_members om
WHERE om.organization_id = 'your-org-id-here';
```

Expected: Creator appears as 'owner' with 'active' status

## Deployment

### 1. Apply Database Trigger
- **Status**: ⏳ Pending
- **Action**: Run SQL script via Supabase dashboard
- **Impact**: Immediate effect on new organizations

### 2. Deploy Error Handling Improvements
- **Status**: ✅ Code updated
- **Action**: Deploy to Render
- **Impact**: Better error messages for users

```bash
# Commit and push changes
git add errors.py
git commit -m "Improve RLS error messages with user-friendly context"
git push origin vecfin-latest

# Render will auto-deploy if configured
```

## Rollback

If issues occur, drop the trigger:

```sql
DROP TRIGGER IF EXISTS trigger_auto_add_org_owner ON organizations;
DROP FUNCTION IF EXISTS auto_add_org_owner();
```

## Benefits

1. **Seamless UX**: Users don't need manual membership setup
2. **Clear Errors**: When RLS blocks actions, users understand why
3. **Security Maintained**: RLS policies still enforce proper access control
4. **Convention over Configuration**: Creators automatically own their organizations

## Related Files

- `infrastructure/sql/add_auto_org_membership_trigger.sql` - Trigger definition
- `errors.py` - Error transformation logic
- `tools/entity.py:85-87` - Already sets `owned_by` for projects
- `RLS_FIX_REPORT.md` - Related RLS policy documentation

## Status

- [x] Trigger SQL created
- [x] Error handling improved
- [ ] Trigger applied to database
- [ ] MCP server redeployed
- [ ] End-to-end testing completed

---

**Created**: 2025-10-02
**Priority**: High - Blocks basic user workflows
**Impact**: All new organization creation flows
