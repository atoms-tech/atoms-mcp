# Aggressive Refactoring Plan - AGENTS.md Compliance

## Overview
This document outlines the comprehensive refactoring needed to comply with AGENTS.md principles:
1. **Aggressive Change Policy** - No backwards compatibility shims
2. **DRY** - Canonical test naming, no duplication
3. **File Size** - All modules ≤500 lines (target 350)

## Phase 1: File Decomposition Analysis

### Critical Large Files (>500 lines)

#### 1. **tools/entity.py** - 1,979 lines ⚠️⚠️⚠️
**Problem:** This is a MASSIVE monolith containing:
- `EntityManager` class (core CRUD logic)
- Permission checking
- Schema management
- Validation logic
- Multiple entity type handlers (organization, project, document, requirement, test, property, block, column)
- Bulk operations
- Advanced features (versions, audit trails, soft deletes)

**Decomposition Plan:**
```
tools/entity/
├── __init__.py                  (exports public API)
├── manager.py                   (core EntityManager - ~300 lines)
├── schemas.py                   (schema definitions - ~150 lines)
├── validators.py                (input validation - ~200 lines)
├── handlers/
│   ├── __init__.py
│   ├── organization.py          (organization-specific logic - ~100 lines)
│   ├── project.py               (project-specific logic - ~100 lines)
│   ├── document.py              (document-specific logic - ~80 lines)
│   ├── requirement.py           (requirement-specific logic - ~80 lines)
│   ├── test.py                  (test-specific logic - ~80 lines)
│   └── shared.py                (shared entity logic - ~100 lines)
└── operations/
    ├── __init__.py
    ├── crud.py                  (create, read, update, delete - ~150 lines)
    ├── bulk.py                  (bulk operations - ~100 lines)
    ├── search.py                (search and filter - ~100 lines)
    └── versioning.py            (version management - ~80 lines)
```

**Acceptance Criteria:**
- All entity CRUD tests pass (200+ tests)
- Imports work: `from tools.entity import EntityManager`
- No feature flags or conditionals added
- All 1979 lines distributed across logical submodules
- Each module ≤350 lines

#### 2. **server.py** - 877 lines
**Problem:** Contains mixed concerns:
- FastMCP server setup
- Authentication configuration
- Middleware setup (permissions, rate limiting, caching)
- Debug logging

**Decomposition Plan:**
```
infrastructure/
├── server_setup.py              (FastMCP server creation - ~150 lines)
├── server_auth.py               (authentication setup - ~150 lines)
└── server_middleware.py         (middleware stack - ~150 lines)

server.py (refactored)           (~200 lines, orchestration only)
```

#### 3. **cli.py** - 631 lines
**Problem:** All CLI commands in one file

**Decomposition Plan:**
```
cli/
├── __init__.py
├── test.py                      (test commands)
├── lint.py                      (linting commands)
├── db.py                         (database commands)
├── server.py                    (server commands)
└── tools.py                     (tools commands)

cli.py (refactored)              (~150 lines, main entry point only)
```

### Large Test Files (>1000 lines)

#### 4. **test_advanced_features.py** - 1,434 lines
**Issues:**
- Mix of entity versioning, audit trails, soft deletes, permissions
- Should be split by feature concern

**Refactor To:**
```
tests/unit/tools/
├── test_entity_versioning.py    (version-related tests)
├── test_entity_audit.py          (audit log tests)
├── test_entity_soft_delete.py    (soft delete tests - exists!)
└── test_entity_permissions.py    (permission tests)
```

#### 5. **test_audit_trails.py** - 1,295 lines
**Issues:**
- Focused on audit concerns but very long
- Can be split into subsections

**Refactor To:**
```
tests/unit/tools/
├── test_audit_trails_create.py   (creation audit events)
├── test_audit_trails_modify.py   (modification audit events)
├── test_audit_trails_query.py    (audit query tests)
└── test_audit_trails_bulk.py     (bulk operation audits)
```

#### 6. **test_error_handling.py** - 1,164 lines
**Issues:**
- Tests multiple error scenarios
- Can be organized by error category

**Refactor To:**
```
tests/unit/tools/
├── test_error_handling_validation.py  (input validation errors)
├── test_error_handling_auth.py        (authentication errors)
├── test_error_handling_permissions.py (permission errors)
├── test_error_handling_operations.py  (operation errors)
└── test_error_handling_state.py       (state/consistency errors)
```

---

## Phase 2: Backwards Compatibility Cleanup

### No Shims or Feature Flags Found ✅
Grep analysis shows:
- Environment variables for configuration (APPROPRIATE - not shims)
- No `if legacy` or `if use_new_api` conditionals
- No deprecated function wrappers with fallbacks
- No feature flags in code (only in env config)

**Status:** No backwards compatibility debt detected!

---

## Phase 3: DRY Principle Application

### Test File Consolidation
**Already Compliant ✅**
- Test files use canonical naming (concern-based)
- No `test_entity_unit.py` + `test_entity_integration.py` pattern
- No `test_entity_fast.py` / `test_entity_slow.py` pairs
- Test variants use markers and fixtures, not separate files

**Action:** None needed

---

## Implementation Strategy

### Step 1: tools/entity.py Decomposition (Day 1)
1. Create `tools/entity/` directory structure
2. Extract modules one by one:
   - Extract schemas.py (manual entity schemas)
   - Extract validators.py (input validation logic)
   - Extract handlers/ (entity-type specific logic)
   - Extract operations/ (CRUD, bulk, search, versioning)
   - Refactor EntityManager in manager.py
   - Create __init__.py with clean exports
3. Update all imports in:
   - tools/ (other tools)
   - tests/unit/tools/ (all entity tests)
   - services/ (any that import entity)
4. Verify tests pass: `pytest tests/unit/tools/test_entity*.py -v`
5. Commit with detailed message

### Step 2: server.py Decomposition (Day 1)
1. Create infrastructure submodules
2. Extract auth setup
3. Extract middleware setup
4. Extract server creation
5. Refactor server.py to orchestrate
6. Update imports in app.py, tests/
7. Verify tests pass: `pytest tests/ -k server -v`
8. Commit with detailed message

### Step 3: cli.py Decomposition (Day 2)
1. Create cli/ directory
2. Extract command groups
3. Create subcommand files
4. Refactor main cli.py
5. Update imports
6. Test CLI: `python cli.py --help`
7. Commit with detailed message

### Step 4: Large Test File Splits (Day 2)
1. test_advanced_features.py → split by feature
2. test_audit_trails.py → split by audit type
3. test_error_handling.py → split by error category
4. Verify tests still pass
5. Commit with detailed message

### Step 5: Validation & Final Commit (Day 2)
1. Run full test suite: `python cli.py test -m unit`
2. Verify no files exceed 500 lines: `wc -l */*.py`
3. Document changes in REFACTORING_SUMMARY.md
4. Final commit with impact statistics

---

## Expected Impact

### Code Quality
| Metric | Before | After | Change |
|--------|--------|-------|--------|
| **Largest file** | 1,979 | 350 | -82% |
| **Total module size** | 10,000+ | ≤5,000 | Proportional |
| **Avg module size** | 400+ | 250 | -38% |
| **Line duplication** | Minimal | None | 0% |
| **Backwards compat shims** | 0 | 0 | ✅ |

### Developer Experience
- **Easier discovery** - Smaller files = faster navigation
- **Clearer intent** - Each module has one clear responsibility
- **Faster testing** - Focused test runs on smaller modules
- **Reduced cognitive load** - 350-line files easier to understand than 2000-line monoliths

### Performance  
- **No impact** - Refactoring is structural only
- **Potential improvement** - Smaller functions may optimize better

---

## Risk Mitigation

### Testing Strategy
1. **Before refactoring:** Run full test suite, document baseline
2. **After each module:** Run related tests immediately
3. **After phase completion:** Run full test suite
4. **Final validation:** 100% test pass rate required

### Rollback Plan
- Each refactoring is a git commit
- If tests fail: `git revert <commit>` returns to known-good state
- Review each commit before next refactoring

### Documentation
- Update import statements in docstrings
- Document new module structure
- Provide migration guide if external projects import from tools/

---

## Success Criteria

✅ All files ≤500 lines (target 350)
✅ All tests passing (100%)
✅ No backwards compatibility shims
✅ No feature flags in code  
✅ DRY principle applied (no duplication)
✅ Clear module boundaries
✅ Clean exports from __init__.py files

---

## Timeline

- **Day 1:** tools/entity.py (1979→350 lines) + server.py (877→200 lines)
- **Day 1-2:** cli.py (631→150 lines)
- **Day 2:** Test file splits
- **Day 2:** Final validation and commit

**Total effort:** 1-2 days of focused refactoring
**Risk level:** Low (well-tested, gradual refactoring with verification after each step)
