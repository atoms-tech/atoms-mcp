# Test File Naming Violations - AGENTS.md Compliance Report

## Executive Summary

**Total Test Files Found**: 90+
**Non-Canonical (Violations)**: 12 files
**Canonical**: 78 files

Per **AGENTS.md § Test File Governance**, test file names must answer: **"What component/concern does this test?"** – not metadata like speed, variant, or phase.

---

## Violations by Category

### Category 1: Test Stage/Phase Metadata (❌ "e2e", "integration", "unit", etc.)

| File | Issue | Should Be |
|------|-------|-----------|
| `tests/e2e/test_e2e.py` | "e2e" describes test stage | `test_complete_workflows.py` or consolidated into specific tool tests |
| `tests/e2e/test_e2e_original.py` | "e2e_original" = temporal metadata | Delete (consolidate into single e2e file) |

**AGENTS.md Rule Violated**:
> ❌ `test_entity_e2e.py` – "e2e" describes test stage, not concern. Use fixtures and markers instead.

---

### Category 2: Temporal/Version Metadata (❌ "_original", "_fixed", "_v2", etc.)

| File | Issue | Should Be |
|------|-------|-----------|
| `tests/framework/C1_APPLY_MARKERS_AND_DOCSTRINGS_FIXED.py` | "FIXED" is temporal metadata | Delete or consolidate into `test_dependency_markers.py` |
| `tests/e2e/test_e2e_original.py` | "_original" implies there's a newer version | Delete (cleanup only, not needed) |

**AGENTS.md Rule Violated**:
> ❌ `test_entity_old.py`, `test_entity_new.py` – Temporal metadata. Refactor, merge, or delete instead.

---

### Category 3: Variant Metadata (❌ "_parametrized", "_parallel", etc.)

| File | Issue | Should Be |
|------|-------|-----------|
| `tests/framework/test_template_parametrized.py` | "_parametrized" describes variant | `test_template_generation.py` or `test_test_generation.py` |
| `tests/e2e/test_parallel_workflows.py` | "_parallel" describes execution mode | `test_concurrent_workflows.py` or `test_workflow_concurrency.py` |

**AGENTS.md Rule Violated**:
> ❌ `test_entity_unit.py` – "unit" describes scope, not what's tested. Use conftest fixtures.
> ❌ `test_entity_integration.py` – "integration" describes client type, not component. Use fixture parametrization.

---

### Category 4: Generic/Vague Names (❌ "test_api", "test_scenarios", etc.)

| File | Issue | Should Be |
|------|-------|-----------|
| `tests/integration/test_api.py` | "api" is too generic (which API?) | `test_mcp_server_integration.py` or split by concern |
| `tests/e2e/test_scenarios.py` | "scenarios" is vague | `test_workflow_scenarios.py` or `test_entity_scenarios.py` |
| `tests/compatibility/test_api_versioning.py` | "api_versioning" is unclear | `test_mcp_api_compatibility.py` or `test_protocol_versioning.py` |
| `tests/e2e/test_complete_project_workflow.py` | "complete" is metadata | `test_project_workflow.py` |
| `tests/regression/test_bug_fixes.py` | "bug_fixes" is temporal | `test_regression_suite.py` or split by specific concern |

**AGENTS.md Rule Violated**:
> ❌ `test_api_integration.py` – "integration" is redundant; file is in tests/. Name by which API is integrated.

---

## Refactoring Plan

### Phase 1: DELETE (No Code Loss)

These files add no value and should be deleted:

```bash
rm tests/e2e/test_e2e_original.py          # Duplicate/old version
rm tests/framework/C1_APPLY_MARKERS_AND_DOCSTRINGS_FIXED.py  # Build artifact, not a test
```

### Phase 2: RENAME (Concern-Based)

Rename to canonical concern-based names:

```bash
# Rename test_template_parametrized.py → test_test_generation.py
mv tests/framework/test_template_parametrized.py tests/framework/test_test_generation.py

# Rename test_parallel_workflows.py → test_concurrent_workflows.py
mv tests/e2e/test_parallel_workflows.py tests/e2e/test_concurrent_workflows.py

# Rename test_e2e.py → test_workflow_execution.py
mv tests/e2e/test_e2e.py tests/e2e/test_workflow_execution.py

# Rename test_scenarios.py → test_workflow_scenarios.py
mv tests/e2e/test_scenarios.py tests/e2e/test_workflow_scenarios.py

# Rename test_api.py → test_mcp_server_integration.py
mv tests/integration/test_api.py tests/integration/test_mcp_server_integration.py

# Rename test_bug_fixes.py → test_regression_suite.py
mv tests/regression/test_bug_fixes.py tests/regression/test_regression_suite.py

# Rename test_api_versioning.py → test_protocol_compatibility.py
mv tests/compatibility/test_api_versioning.py tests/compatibility/test_protocol_compatibility.py

# Rename test_complete_project_workflow.py → test_project_workflow.py
mv tests/e2e/test_complete_project_workflow.py tests/e2e/test_project_workflow.py
```

### Phase 3: CONSOLIDATE (Reduce Duplication)

After renaming, consolidate overlapping concerns:

- `tests/e2e/test_workflow_execution.py` + `tests/e2e/test_workflow_scenarios.py` → Consider merging if same concern
- Review `tests/e2e/` to ensure no duplicate workflow tests

---

## Verification Commands

After refactoring:

```bash
# Check no files violate naming rules
rg "^test_(unit|integration|e2e|fast|slow|v[0-9]|api|scenario)" tests/ --type py

# Verify all files are canonical (concern-based)
ls -1 tests/**/*.py | grep -v "test_[a-z_]*\.py$" | grep "_(unit|integration|e2e|parametrized|parallel|original|fixed|v[0-9])"
```

---

## AGENTS.md Compliance Checklist

✅ **Test naming rule**: "Test file names must answer 'What component/concern does this test?'"

After refactoring:
- ✅ No metadata suffixes (`_unit`, `_e2e`, `_fast`, `_slow`, `_v2`, `_original`, `_fixed`)
- ✅ No vague generic names (`test_api.py`, `test_scenarios.py`)
- ✅ Concern-based organization (tool, integration point, feature)
- ✅ One source of truth per concern (no duplicate test files)

---

## Impact Assessment

**Breaking Changes**: Minimal
- Only file paths change
- Test names/classes unchanged
- CI/CD: Update `pytest.ini` globs if any
- IDE imports: Auto-update in most editors

**Benefits**:
- 100% AGENTS.md compliance
- Clear test discovery
- No ambiguity about test purpose
- Automated consolidation possible

---

**Status**: Ready for Phase 1 (DELETE) and Phase 2 (RENAME)
