# Deploy RLS Fix - Quick Guide

## 🎯 This Fix Addresses Your Exact Issues

Based on tester agent results:

| Issue | Current | After Fix |
|-------|---------|-----------|
| Organizations INSERT | ❌ | ✅ `WITH CHECK (true)` |
| Projects INSERT | ❌ | ✅ Org member check |
| Properties ALL | ❌ | ✅ All operations enabled |
| test_req ALL | ❌ | ✅ All operations enabled |
| DELETE operations | ❌ Most blocked | ✅ All enabled |

## 🚀 Deploy Command

```bash
psql "$DATABASE_URL" -f FIX_RLS_COMPLETE.sql
```

## ✅ What This Script Does

1. **Drops ALL existing policies** (clean slate)
2. **Re-enables RLS** on all tables
3. **Re-applies grants** to authenticated role
4. **Creates correct policies**:
   - Organizations: `WITH CHECK (true)` for INSERT
   - Organization_members: Allows self-removal
   - Properties: Full access via org membership
   - test_req: Full access via org membership
   - All tables: DELETE policies added

## 📊 Expected Results After Running

All operations should show ✅:

```
| Table                | SELECT | INSERT | UPDATE | DELETE |
|----------------------|--------|--------|--------|--------|
| organizations        | ✅      | ✅      | ✅      | ✅      |
| projects             | ✅      | ✅      | ✅      | ✅      |
| documents            | ✅      | ✅      | ✅      | ✅      |
| requirements         | ✅      | ✅      | ✅      | ✅      |
| organization_members | ✅      | ✅      | ✅      | ✅      |
| properties           | ✅      | ✅      | ✅      | ✅      |
| test_req             | ✅      | ✅      | ✅      | ✅      |
```

## 🧪 Verification Queries

The script runs these automatically at the end:

1. Check RLS enabled
2. Check policy count (should be 4 per table, except profiles = 2)

## 🔧 If It Still Doesn't Work

Check if `auth.uid()` is null:

```sql
SELECT auth.uid();
-- Should return your user UUID, not NULL
```

If it returns NULL, the issue is JWT validation, not RLS policies.

## 📝 Key Differences from Previous Scripts

- **Drops existing policies first** (previous scripts kept old policies)
- **Simplified queries** (removed unnecessary is_deleted checks in subqueries)
- **Self-removal enabled** (organization_members DELETE)
- **All DELETE policies added** (including hard deletes)
