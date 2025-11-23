# SQL Migrations Audit

## Overview

Audit of SQL migration files in `infrastructure/sql/` to identify obsolete, duplicate, or consolidatable files.

## Files Found

**Total:** 27 SQL files

### Numbered Migrations (Sequential)
- `006_user_id_mapping.sql`
- `007_member_soft_delete.sql`
- `008_performance_indexes.sql`
- `009_fix_all_supabase_advisories.sql`
- `010_phase_2_4_phase_3_schema.sql`

**Status:** ✅ Keep - Sequential migrations, likely applied in order

### Vector RPC Files (Potential Duplicates)
- `vector_rpcs.sql` - Original
- `vector_rpcs_fixed.sql` - Fixed version
- `vector_rpcs_for_your_schema.sql` - Schema-specific
- `vector_rpcs_no_enum_filters.sql` - Variant without enum filters
- `vector_rpcs_progressive.sql` - Progressive version
- `vector_rpcs_updated.sql` - Updated version
- `vector_rpcs_working.sql` - Working version

**Analysis:** Multiple versions suggest iterative development. Need to identify which is current.

**Recommendation:** 
- Identify current/active version
- Archive or delete obsolete versions
- Document which version is in use

### Organization Membership Files
- `add_auto_org_membership_CORRECT.sql` - Corrected version
- `add_auto_org_membership_minimal.sql` - Minimal version
- `add_auto_org_membership_trigger.sql` - Trigger-only version

**Analysis:** Multiple versions for same feature.

**Recommendation:**
- Identify which version is applied
- Consolidate or archive others

### RLS Fix Files (Sequential)
- `rls_fix_01_helper_functions.sql`
- `rls_fix_02_drop_problematic_policies.sql`
- `rls_fix_03_core_tables_policies.sql`
- `rls_fix_04_mcp_tables_policies.sql`
- `rls_fix_05_chat_and_indexes.sql`

**Status:** ✅ Keep - Sequential fixes, likely applied in order

### Session Management Files
- `create_mcp_sessions_table.sql` - Create table
- `create_session_rls_policies.sql` - RLS policies
- `check_mcp_sessions_table.sql` - Verification script
- `test_session_operations.sql` - Test script

**Status:** ✅ Keep - Related files for session feature

### Other Files
- `add_embedding_columns.sql` - Embedding support
- `embedding_triggers_setup.sql` - Embedding triggers
- `check_org_members_table.sql` - Verification script

**Status:** ✅ Keep - Feature-specific files

---

## Consolidation Opportunities

### High Priority
1. **Vector RPC Files** - 7 files, likely only 1-2 are current
   - Action: Identify current version, archive others
   - Estimated reduction: 5-6 files

2. **Organization Membership Files** - 3 files, likely only 1 is current
   - Action: Identify current version, archive others
   - Estimated reduction: 2 files

### Medium Priority
3. **Check Scripts** - `check_*.sql` files
   - Action: Consider moving to `scripts/` directory
   - Or: Keep in place if used for verification

### Low Priority
4. **Test Scripts** - `test_*.sql` files
   - Action: Consider moving to `tests/` directory
   - Or: Keep if used for database testing

---

## Recommendations

### Immediate Actions
1. ✅ **Document current vector_rpcs version** - Which file is actually used?
2. ✅ **Document current org_membership version** - Which file is applied?
3. 📋 **Archive obsolete vector_rpcs files** - Move to `infrastructure/sql/archive/`
4. 📋 **Archive obsolete org_membership files** - Move to `infrastructure/sql/archive/`

### Long-term
5. 📋 **Create migration tracking** - Document which migrations are applied
6. 📋 **Version control** - Use git for migration history instead of multiple files
7. 📋 **Consolidate check scripts** - Move to dedicated scripts directory

---

## File Organization Proposal

```
infrastructure/sql/
├── migrations/              # Sequential numbered migrations
│   ├── 006_user_id_mapping.sql
│   ├── 007_member_soft_delete.sql
│   ├── 008_performance_indexes.sql
│   ├── 009_fix_all_supabase_advisories.sql
│   └── 010_phase_2_4_phase_3_schema.sql
├── features/                # Feature-specific migrations
│   ├── sessions/
│   │   ├── create_mcp_sessions_table.sql
│   │   ├── create_session_rls_policies.sql
│   │   └── check_mcp_sessions_table.sql
│   ├── embeddings/
│   │   ├── add_embedding_columns.sql
│   │   └── embedding_triggers_setup.sql
│   ├── vector_search/
│   │   └── vector_rpcs.sql  # Current version only
│   └── rls/
│       ├── rls_fix_01_helper_functions.sql
│       ├── rls_fix_02_drop_problematic_policies.sql
│       ├── rls_fix_03_core_tables_policies.sql
│       ├── rls_fix_04_mcp_tables_policies.sql
│       └── rls_fix_05_chat_and_indexes.sql
├── archive/                 # Obsolete versions
│   ├── vector_rpcs_fixed.sql
│   ├── vector_rpcs_for_your_schema.sql
│   ├── vector_rpcs_no_enum_filters.sql
│   ├── vector_rpcs_progressive.sql
│   ├── vector_rpcs_updated.sql
│   ├── vector_rpcs_working.sql
│   ├── add_auto_org_membership_CORRECT.sql
│   ├── add_auto_org_membership_minimal.sql
│   └── add_auto_org_membership_trigger.sql
└── scripts/                 # Utility scripts
    ├── check_org_members_table.sql
    └── test_session_operations.sql
```

---

**Date:** 2025-11-23  
**Status:** Audit Complete  
**Next Steps:** Identify current versions, archive obsolete files
