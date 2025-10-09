# Archive Index
**Created:** 2025-10-08  
**Purpose:** Reference for all archived files during consolidation

---

## 📁 Archive Structure

```
archive/
├── backup_broken/          # Broken/backup files
├── logs_output/            # Test logs and reports
├── sql_redundant/          # Redundant SQL migration files
└── framework_redundant/    # Redundant framework components
```

---

## 🗂️ Backup/Broken Files (`backup_broken/`)

### Files Archived
1. **persistent_authkit_provider_BROKEN.py**
   - Original: `auth/persistent_authkit_provider_BROKEN.py`
   - Reason: Broken implementation, replaced by working version
   - Date: 2025-10-08

2. **authkit-client.backup/**
   - Original: `authkit-client.backup/`
   - Reason: Backup directory, superseded by lib/authkit-client
   - Date: 2025-10-08

3. **temp_fix.txt**
   - Original: `temp_fix.txt`
   - Reason: Temporary fix notes, no longer needed
   - Date: 2025-10-08

4. **full_test_output.txt**
   - Original: `full_test_output.txt`
   - Reason: Old test output, superseded by new test reports
   - Date: 2025-10-08

5. **test_run_with_logs.txt**
   - Original: `test_run_with_logs.txt`
   - Reason: Old test logs, superseded by new logging system
   - Date: 2025-10-08

---

## 📊 Log/Output Files (`logs_output/`)

### Files Archived
1. **tui.log**
   - Original: `tui.log`
   - Reason: Old TUI logs, regenerated on each run
   - Date: 2025-10-08

2. **integration_test_report.json**
   - Original: `tests/integration_test_report.json`
   - Reason: Old test report, superseded by new reporting system
   - Date: 2025-10-08

3. **performance_report.json**
   - Original: `tests/performance_report.json`
   - Reason: Old performance report, superseded by new system
   - Date: 2025-10-08

4. **workflow_live_test_report.json**
   - Original: `tests/workflow_live_test_report.json`
   - Reason: Old workflow test report
   - Date: 2025-10-08

5. **workflow_test_matrix_report.json**
   - Original: `tests/workflow_test_matrix_report.json`
   - Reason: Old workflow matrix report
   - Date: 2025-10-08

---

## 🗄️ SQL Redundancies (`sql_redundant/`)

### RLS Fix Files (6 versions)
**Active Version:** `COMPLETE_RLS_FIX.sql` (kept in root)

1. **RLS_FIX_STEP_BY_STEP.sql**
   - Original: `RLS_FIX_STEP_BY_STEP.sql`
   - Reason: Superseded by COMPLETE_RLS_FIX.sql
   - Date: 2025-10-08

2. **STEP1_FIX_RECURSION.sql**
   - Original: `STEP1_FIX_RECURSION.sql`
   - Reason: Partial fix, included in COMPLETE_RLS_FIX.sql
   - Date: 2025-10-08

3. **STEP2_FIX_PROJECT_ACCESS.sql**
   - Original: `STEP2_FIX_PROJECT_ACCESS.sql`
   - Reason: Partial fix, included in COMPLETE_RLS_FIX.sql
   - Date: 2025-10-08

4. **fix_rls_policies.sql**
   - Original: `scripts/fix_rls_policies.sql`
   - Reason: Older version, superseded by COMPLETE_RLS_FIX.sql
   - Date: 2025-10-08

5. **fix_all_rls_for_service_role.sql**
   - Original: `infrastructure/sql/fix_all_rls_for_service_role.sql`
   - Reason: Older version, superseded by COMPLETE_RLS_FIX.sql
   - Date: 2025-10-08

### Organization Membership Triggers (3 versions)
**Active Version:** `infrastructure/sql/add_auto_org_membership_CORRECT.sql` (kept)

6. **add_auto_org_membership_trigger.sql**
   - Original: `infrastructure/sql/add_auto_org_membership_trigger.sql`
   - Reason: v1, superseded by CORRECT version
   - Date: 2025-10-08

7. **add_auto_org_membership_trigger_v2.sql**
   - Original: `infrastructure/sql/add_auto_org_membership_trigger_v2.sql`
   - Reason: v2, superseded by CORRECT version
   - Date: 2025-10-08

### Vector RPC Files (4 versions)
**Active Version:** `infrastructure/sql/vector_rpcs_updated.sql` (kept)

8. **vector_rpcs.sql**
   - Original: `infrastructure/sql/vector_rpcs.sql`
   - Reason: Original version, superseded by updated version
   - Date: 2025-10-08

9. **vector_rpcs_progressive.sql**
   - Original: `infrastructure/sql/vector_rpcs_progressive.sql`
   - Reason: Experimental version, superseded by updated version
   - Date: 2025-10-08

10. **vector_rpcs_no_enum_filters.sql**
    - Original: `infrastructure/sql/vector_rpcs_no_enum_filters.sql`
    - Reason: Alternative version, superseded by updated version
    - Date: 2025-10-08

### Other SQL Files

11. **ADD_JWT_CLAIMS.sql**
    - Original: `ADD_JWT_CLAIMS.sql`
    - Reason: No longer needed (stateless AuthKit, no Supabase JWT)
    - Date: 2025-10-08

12. **APPLY_ALL_FIXES.sql**
    - Original: `APPLY_ALL_FIXES.sql`
    - Reason: Consolidated into individual fix files
    - Date: 2025-10-08

13. **fix_crud_issues.sql**
    - Original: `fix_crud_issues.sql`
    - Reason: Issues resolved, fix applied
    - Date: 2025-10-08

14. **apply_trigger_fix_to_all_tables.sql**
    - Original: `apply_trigger_fix_to_all_tables.sql`
    - Reason: Fix applied, no longer needed
    - Date: 2025-10-08

---

## 🧩 Framework Redundancies (`framework_redundant/`)

### Files Archived

1. **health_checks_old.py**
   - Original: `tests/framework/health_checks_old.py`
   - Reason: Superseded by health_checks.py
   - Date: 2025-10-08

2. **oauth_progress.py**
   - Original: `tests/framework/oauth_progress.py`
   - Reason: Superseded by oauth_progress_enhanced.py
   - Date: 2025-10-08

3. **example_tui_with_status.py**
   - Original: `tests/framework/example_tui_with_status.py`
   - Reason: Example file, functionality in tui_enhanced.py
   - Date: 2025-10-08

---

## 📋 Future Archive Plans

### Pending (Phase 2+)
These will be archived in subsequent phases:

**Test Reports** (→ `archive/test_reports/`):
- 7 functionality_matrix_*.md files
- 14 test_report_*.json/md files

**Status Documents** (→ `archive/status_reports/`):
- DEPLOYMENT_STATUS.md
- DEPLOYMENT_SUMMARY.md
- FINAL_FIXES_SUMMARY.md
- FINAL_OPTIMIZATION_SUMMARY.md
- FIXES_SUMMARY.md
- MIGRATION_SUMMARY.md
- AUTHKIT_CLEANUP_COMPLETE.md
- TDD_SYSTEM_IMPLEMENTATION_COMPLETE.md
- TESTS_FIXED.md

**Implementation Notes** (→ `archive/implementation_notes/`):
- ORG_MEMBERSHIP_FIX.md
- CRUD_ISSUES_ROOT_CAUSES.md
- PYTEST_MIGRATION.md
- REMOVE_MCP_SESSIONS.md
- WORKFLOW_TEST_FIX.md
- ZEN_TEST_FEATURES_INTEGRATION.md
- ZEN_TUI_INTEGRATION.md

**QA/Audit Docs** (→ `archive/qa_audits/`):
- COMPREHENSIVE_QA_MATRIX.md
- FINAL_COMPLETE_TEST_MATRIX.md
- RLS_AUDIT_RESULTS.md
- SQL_VERIFICATION_CHECKLIST.md
- DEMO_DATA_PLAN.md

---

## 🔍 How to Find Archived Files

### By Original Location
```bash
# Search by original filename
grep -r "filename.ext" archive/

# List all archived files
find archive/ -type f -name "*.py" -o -name "*.sql" -o -name "*.md"
```

### By Archive Date
All files in this archive were moved on **2025-10-08** during Phase 1 consolidation.

### By Category
- **Broken/Backup:** `archive/backup_broken/`
- **Logs/Reports:** `archive/logs_output/`
- **SQL Files:** `archive/sql_redundant/`
- **Framework:** `archive/framework_redundant/`

---

## ⚠️ Important Notes

1. **Do Not Delete:** These files are archived for reference, not deleted
2. **Version Control:** All archived files are still in git history
3. **Restoration:** Files can be restored if needed by copying from archive/
4. **Active Versions:** See CONSOLIDATION_PLAN.md for active file locations

---

## 📚 Related Documentation

- **CONSOLIDATION_PLAN.md** - Overall consolidation strategy
- **README.md** - Main project documentation
- **CHANGELOG.md** - Track of all changes (to be created)

---

**Last Updated:** 2025-10-08  
**Phase:** 1 (Archival) Complete

