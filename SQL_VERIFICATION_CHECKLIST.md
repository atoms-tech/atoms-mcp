# SQL Script Verification Checklist

## ✅ Pre-Deployment Verification

Before running `COMPREHENSIVE_RLS_SETUP.sql`, verify these corrections:

### 1. No NEW.* References in WITH CHECK Clauses
```bash
grep "NEW\." COMPREHENSIVE_RLS_SETUP.sql
# Should return: (no results)
```
✅ **Status**: Fixed - all 6 references removed

### 2. Properties Table Uses document_id
```bash
grep "requirement_id" COMPREHENSIVE_RLS_SETUP.sql | grep -i properties
# Should return: (no results)
```
✅ **Status**: Fixed - changed to document_id

### 3. All Required Policies Present
Expected policies per table:
- organizations: 4 policies (INSERT, SELECT, UPDATE, DELETE)
- organization_members: 4 policies
- projects: 4 policies
- documents: 4 policies
- requirements: 4 policies
- test_req: 4 policies
- properties: 4 policies
- blocks: 4 policies
- profiles: 2 policies (SELECT, UPDATE)

**Total**: 34 policies across 9 tables

## 🚀 Deployment Steps

### Step 1: Run the Script
```bash
psql "$DATABASE_URL" -f COMPREHENSIVE_RLS_SETUP.sql
```

### Step 2: Verify Execution
```sql
-- Check RLS is enabled on all tables
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN (
    'organizations', 'organization_members', 'projects',
    'documents', 'requirements', 'test_req',
    'properties', 'blocks', 'profiles'
)
ORDER BY tablename;
```

Expected result: All should show `rowsecurity = true`

### Step 3: Count Policies
```sql
-- Verify policy count
SELECT
    tablename,
    COUNT(*) as policy_count
FROM pg_policies
WHERE tablename IN (
    'organizations', 'organization_members', 'projects',
    'documents', 'requirements', 'test_req',
    'properties', 'blocks', 'profiles'
)
GROUP BY tablename
ORDER BY tablename;
```

Expected counts:
- Most tables: 4 policies
- profiles: 2 policies

### Step 4: Verify Grants
```sql
-- Check authenticated role has permissions
SELECT
    table_name,
    string_agg(privilege_type, ', ' ORDER BY privilege_type) as privileges
FROM information_schema.role_table_grants
WHERE grantee = 'authenticated'
AND table_schema = 'public'
AND table_name IN (
    'organizations', 'organization_members', 'projects',
    'documents', 'requirements', 'test_req',
    'properties', 'blocks', 'profiles'
)
GROUP BY table_name
ORDER BY table_name;
```

Expected: SELECT, INSERT, UPDATE, DELETE for most tables

### Step 5: Test Organization Creation
```sql
-- Switch to a test user context
SET LOCAL role authenticated;
SET LOCAL request.jwt.claims TO '{"sub": "test-user-uuid"}';

-- Try creating an organization
INSERT INTO organizations (name, slug, type, created_by)
VALUES ('Test Org', 'test-org', 'team', 'test-user-uuid')
RETURNING id, name;
```

Expected: Success (no permission errors)

## 🔍 Common Issues & Solutions

### Issue 1: "missing FROM-clause entry for table NEW"
**Cause**: `NEW.` prefix used in WITH CHECK clause
**Solution**: Already fixed - no NEW.* references in script

### Issue 2: "column requirement_id does not exist"
**Cause**: Wrong column name for properties table
**Solution**: Already fixed - uses `document_id` now

### Issue 3: "permission denied for table X"
**Cause**: Missing GRANT statements
**Solution**: Script includes all necessary GRANTs

### Issue 4: Policies not applying
**Cause**: RLS not enabled on table
**Solution**: Script enables RLS on all tables

## ✨ Post-Deployment Tests

After successful deployment, test these operations:

### Test 1: Organization Creation
```python
# Should succeed
result = entity_tool(
    operation="create",
    entity_type="organization",
    data={"name": "Test Org", "type": "team"}
)
```

### Test 2: Project Creation
```python
# Should succeed (after org membership added)
result = entity_tool(
    operation="create",
    entity_type="project",
    data={"name": "Test Project", "organization_id": org_id}
)
```

### Test 3: Properties Access
```python
# Should succeed
result = entity_tool(
    operation="list",
    entity_type="property",
    parent_type="document",
    parent_id=doc_id
)
```

### Test 4: test_req Access
```python
# Should succeed
result = entity_tool(
    operation="list",
    entity_type="test",
    parent_type="project",
    parent_id=project_id
)
```

## 📊 Success Criteria

✅ Script runs without errors
✅ All 9 tables have RLS enabled
✅ 34 total policies created
✅ All grants applied correctly
✅ Organization creation works
✅ Project creation works (with membership)
✅ Properties and test_req accessible
✅ No "permission denied" errors

## 🎯 Next Steps After Verification

1. Test all MCP tool operations
2. Monitor for any permission errors in logs
3. Validate production readiness metrics
4. Update documentation with any findings
