# RLS Policy Issues and Fixes

## 🔍 Issues Found in V1 Script

### Issue 1: Organization Members DELETE - Users Can't Remove Themselves
**Problem**: DELETE policy only allows admins to remove members, but users should be able to leave organizations.

**V1 Policy (BROKEN)**:
```sql
CREATE POLICY "Admins can delete organization members"
ON organization_members
FOR DELETE
TO authenticated
USING (
  organization_id IN (
    SELECT organization_id
    FROM organization_members
    WHERE user_id = auth.uid()
    AND role IN ('owner', 'admin')  -- ❌ Only admins, no self-removal
    AND status = 'active'
    AND is_deleted = false
  )
);
```

**V2 Fix**:
```sql
CREATE POLICY "Admins can delete organization members"
ON organization_members
FOR DELETE
TO authenticated
USING (
  user_id = auth.uid()  -- ✅ User removing themselves
  OR
  organization_id IN (
    SELECT organization_id
    FROM organization_members
    WHERE user_id = auth.uid()
    AND role IN ('owner', 'admin')
    AND status = 'active'
  )
);
```

---

### Issue 2: Properties/test_req Lockdown - is_deleted Checks Causing JOIN Failures
**Problem**: Subquery JOINs include `is_deleted = false` checks on org_members, which can fail if soft-deleted records exist in the chain.

**V1 Policy (POTENTIAL ISSUE)**:
```sql
USING (
  document_id IN (
    SELECT d.id
    FROM documents d
    JOIN projects p ON d.project_id = p.id
    JOIN organization_members om ON p.organization_id = om.organization_id
    WHERE om.user_id = auth.uid()
    AND om.status = 'active'
    AND om.is_deleted = false  -- ❌ Could cause lockdown
  )
);
```

**V2 Fix - Removed is_deleted Checks**:
```sql
USING (
  document_id IN (
    SELECT d.id
    FROM documents d
    JOIN projects p ON d.project_id = p.id
    WHERE p.organization_id IN (
      SELECT organization_id
      FROM organization_members
      WHERE user_id = auth.uid()
      AND status = 'active'  -- ✅ Only status check, no is_deleted
    )
  )
);
```

**Rationale**: The `is_deleted` filtering is already handled at the application level in `entity.py`. RLS policies should only check **access permissions**, not data visibility.

---

### Issue 3: Documents Hard DELETE Missing
**Problem**: No DELETE policy was created for documents table in V1.

**V1**: Missing policy

**V2 Fix**: Added DELETE policy
```sql
CREATE POLICY "Organization members can delete documents"
ON documents
FOR DELETE
TO authenticated
USING (
  project_id IN (
    SELECT p.id
    FROM projects p
    WHERE p.organization_id IN (
      SELECT organization_id
      FROM organization_members
      WHERE user_id = auth.uid()
      AND status = 'active'
    )
  )
);
```

---

### Issue 4: Organization CREATE May Have Chicken-Egg Problem (ACTUALLY OK in V1)
**V1 Policy**:
```sql
WITH CHECK (
  auth.uid() IS NOT NULL  -- ✅ This is actually fine
);
```

**Status**: No issue - any authenticated user can create orgs

---

## 📋 Summary of Changes V1 → V2

| Issue | Table | Operation | V1 Status | V2 Fix |
|-------|-------|-----------|-----------|--------|
| Self-removal | organization_members | DELETE | ❌ Blocked | ✅ Allowed |
| is_deleted lockdown | properties | ALL | ⚠️ Potential | ✅ Removed |
| is_deleted lockdown | test_req | ALL | ⚠️ Potential | ✅ Removed |
| Hard delete | documents | DELETE | ❌ Missing | ✅ Added |
| Org creation | organizations | INSERT | ✅ OK | ✅ OK |

---

## 🎯 Should You Use V2?

**YES, use V2 if**:
- ❌ Users can't leave organizations (self-removal blocked)
- ❌ Properties or test_req tables are completely locked down
- ❌ Hard deletes on documents fail

**Maybe use V2 if**:
- ⚠️ Experiencing intermittent access issues with properties/test_req
- ⚠️ Soft-deleted organization_members records exist in database

**NO, keep V1 if**:
- ✅ Everything is working fine
- ✅ You specifically want to prevent users from self-removal

---

## 🔍 How to Diagnose Your Current Issues

### Test 1: Check if org_members DELETE is the problem
```sql
-- Try to delete your own membership
DELETE FROM organization_members
WHERE user_id = auth.uid()
AND organization_id = 'some-org-id';

-- Expected V1: FAIL (permission denied)
-- Expected V2: SUCCESS
```

### Test 2: Check if is_deleted is causing lockdown
```sql
-- Check for soft-deleted org_members
SELECT COUNT(*) FROM organization_members WHERE is_deleted = true;

-- If count > 0, is_deleted checks in JOINs could cause issues
```

### Test 3: Check if documents DELETE is missing
```sql
-- Try hard delete
DELETE FROM documents WHERE id = 'some-doc-id';

-- Expected V1: FAIL (no policy)
-- Expected V2: SUCCESS (if you're org member)
```

---

## 🚀 Recommendation

Based on your reported issues:
1. **No CREATE permissions on organizations** - V1 should work (check if auth.uid() returns null)
2. **No DELETE permissions on organization_members** - ✅ **V2 FIXES THIS**
3. **Complete lockdown on properties/test_req** - ✅ **V2 FIXES THIS**
4. **Hard delete blocked on documents** - ✅ **V2 FIXES THIS**

**Verdict**: **Use V2** to fix 3 out of 4 reported issues.

For issue #1 (org creation), verify that `auth.uid()` is actually returning a value. If it's null, the problem is with JWT validation, not RLS policies.
