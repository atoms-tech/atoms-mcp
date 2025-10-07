# CRUD Issues - Root Cause Analysis

**Date:** October 6th, 2025
**Environment:** Main Branch at Commit 6412be9
**Database:** Supabase (Production)

## Executive Summary

Analyzed 13 CRUD operations across Organizations, Projects, and Documents. Found **6 critical database-level issues** requiring SQL fixes, **3 UI-level issues** requiring frontend changes, and **4 working correctly**.

## Critical Issues (Database Level)

### 1. 🟥 Project Creation - RLS Policy Violation

**Error:** `new row violates row-level security policy for table "project_members"`

**Root Cause:**
- The `handle_new_project()` trigger attempts to insert the project creator into `project_members` table
- RLS policy on `project_members` requires user to already be an owner/admin via `is_project_owner_or_admin()`
- **Chicken-and-egg problem:** User cannot be inserted as owner because they're not yet an owner
- The trigger function lacks `SECURITY DEFINER`, so it runs with user permissions (not superuser)

**Impact:** Users cannot create projects, even if they're org members

**Fix:** Add `SECURITY DEFINER` to `handle_new_project()` function to bypass RLS during owner insertion

---

### 2. 🟥 Project Duplication - Same as Project Creation

**Error:** `Failed to create duplicated project {}`

**Root Cause:** Identical to Project Creation issue - the `handle_new_project()` trigger fails

**Impact:** Cannot duplicate projects

**Fix:** Same as Project Creation - `SECURITY DEFINER` on trigger function

---

### 3. 🟥 Organization Update - Overly Restrictive RLS

**Symptom:** Edit button visible to all org members but non-functional

**Root Cause:**
- RLS policy: `"Users can update organizations"` only allows `created_by = auth.uid()`
- Organization admins and owners should be able to update org settings
- Current policy ignores `organization_members` table roles

**Impact:** Only the org creator can update org name/settings, not other admins

**Fix:** Update RLS policy to check `organization_members` with `role IN ('owner', 'admin')`

---

### 4. 🟨 Project Update - Overly Restrictive RLS

**Symptom:** UI doesn't update on project name change, but reload shows it worked

**Root Cause:**
- RLS policy only allows `created_by = auth.uid()`
- Should also allow:
  - Organization admins/owners
  - Project owners/admins/maintainers/editors

**Impact:** Only project creator can update project metadata

**Fix:** Update RLS policy to check both `organization_members` and `project_members` tables

---

### 5. 🟥 Document Update - Overly Restrictive RLS

**Error:** `Failed to update document: {}`

**Root Cause:**
- RLS policy only allows `created_by = auth.uid()`
- Should allow project members and org admins to edit documents

**Impact:** Cannot update document title/description unless you're the creator

**Fix:** Update RLS policy to check `project_members` (with appropriate roles) and org admins

---

### 6. 🟥 Document Duplication - Block Transfer Failure

**Symptom:** Document duplicates but blocks don't transfer over

**Root Cause:**
- RLS policies on `blocks` table appear correct (checked org/project membership)
- Likely an **application logic issue**, not database
- Possible causes:
  - Frontend not calling block duplication endpoint
  - Backend not implementing block copy logic
  - Transaction/timing issue where blocks are queried before insert completes

**Impact:** Duplicated documents are empty shells

**Fix:**
- Database RLS appears correct
- Check application code in document duplication handler
- Ensure blocks are copied in same transaction as document creation
- Consider creating a backend endpoint that handles full duplication atomically

---

## UI-Level Issues (Frontend)

### 7. 🟨 Organization Creation - UI Doesn't Refresh

**Symptom:** Error message shown, but org actually created (visible after reload)

**Root Cause:**
- Database operation succeeds (org created, user added as owner via trigger)
- Frontend error handling or state management issue
- Possibly catching a non-error response as error

**Impact:** User sees error but operation succeeded - confusing UX

**Fix:**
- Check frontend error handling in org creation flow
- Use optimistic updates or proper success callbacks
- Ensure state refreshes after creation

---

### 8. 🟥 Organization Delete - Missing UI

**Symptom:** No delete button/option in UI

**Root Cause:**
- Database RLS policy allows deletion by creators and owners (working correctly)
- Frontend simply doesn't implement delete functionality

**Impact:** Cannot delete organizations from UI

**Fix:** Add delete button to org settings with confirmation dialog

---

### 9. 🟨 Project Update - UI Doesn't Refresh

**Symptom:** Update succeeds but UI doesn't reflect changes until reload

**Root Cause:**
- Database update works correctly (after applying RLS fix)
- Frontend state not updated after successful API call
- Missing state refresh or optimistic update

**Impact:** Confusing UX - appears broken but actually works

**Fix:** Update frontend to refresh state after successful project update

---

## Working Correctly ✅

### 10. Organization Read
- RLS policies correctly check `created_by` and `organization_members`
- Users can see orgs they created or are members of

### 11. Project Read
- RLS checks creator, org membership, and project membership
- **Note:** User reports needing manual invitation - this suggests org membership might not be working
- Verify users are actually being added to `organization_members` table

### 12. Project Delete
- Already working correctly

### 13. Document Create/Read/Delete
- All working correctly
- Proper RLS checks for project/org membership

---

## Database Schema Issues Found

### RLS Policy Patterns

**❌ Bad Pattern (too restrictive):**
```sql
USING (created_by = auth.uid())
```

**✅ Good Pattern (role-based):**
```sql
USING (
  created_by = auth.uid()
  OR
  id IN (
    SELECT organization_id FROM organization_members
    WHERE user_id = auth.uid()
      AND role IN ('owner', 'admin')
      AND status = 'active'
      AND is_deleted = false
  )
)
```

### Trigger Function Issues

**❌ Missing SECURITY DEFINER:**
```sql
CREATE FUNCTION handle_new_project()
RETURNS trigger
LANGUAGE plpgsql
-- Missing: SECURITY DEFINER
```

**✅ With SECURITY DEFINER:**
```sql
CREATE FUNCTION handle_new_project()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER  -- Bypasses RLS for trigger operations
SET search_path TO 'public', 'pg_temp'
```

---

## Recommendations

### Immediate (Apply SQL Fixes)

1. **Run `fix_crud_issues.sql`** to fix all 6 database-level issues
2. **Test project creation** with org members
3. **Test document updates** with project editors
4. **Verify org admin permissions** work correctly

### Short Term (Frontend Fixes)

1. **Add org delete UI** with owner-only visibility
2. **Fix state refresh issues** in org creation and project update
3. **Implement document duplication** block copy logic
4. **Add role-based UI visibility** for edit buttons

### Long Term (Architecture)

1. **Standardize RLS patterns** across all tables
2. **Document role hierarchy:**
   - Organization: owner > admin > member
   - Project: owner > admin > maintainer > editor > viewer
3. **Add comprehensive RLS tests** for all operations
4. **Consider using Supabase RLS helper functions** for common patterns

---

## Testing Checklist

After applying fixes, test:

- [ ] Create org as new user → should succeed and show in UI
- [ ] Update org as org admin → should succeed
- [ ] Create project as org member → should succeed (no RLS error)
- [ ] Duplicate project → should succeed with owner record created
- [ ] Update project as project editor → should succeed
- [ ] Update document as project editor → should succeed
- [ ] Duplicate document → should copy all blocks
- [ ] Delete org as owner → should work (after UI implemented)

---

## Files Generated

1. `fix_crud_issues.sql` - Comprehensive SQL fix script with all changes
2. `CRUD_ISSUES_ROOT_CAUSES.md` - This document

Apply the SQL script to fix all database-level issues.
