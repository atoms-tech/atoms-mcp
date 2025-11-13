# Aggressive Change Policy - Complete Guide

**Status**: ✅ **NOW ACTIVE IN AGENTS.md, CLAUDE.md, AND WARP.md**

## 🎯 Core Mandate

**Avoid ANY backwards compatibility shims, legacy fallbacks, or gentle migrations.**

**Always perform FULL, COMPLETE changes when refactoring or modernizing code.**

---

## ❌ What NOT to Do

### Don't Preserve Deprecated Patterns
```python
# ❌ WRONG: Keeping old code for "compatibility"
def process_data(data, use_legacy=False):
    if use_legacy:
        return old_process(data)  # Don't leave this!
    else:
        return new_process(data)
```

### Don't Leave Conditional Logic for Migration
```python
# ❌ WRONG: Feature flag for gradual rollout
if FEATURE_FLAG_USE_NEW_API:
    result = new_implementation()
else:
    result = old_implementation()  # Don't do this!
```

### Don't Perform Partial Migrations
```python
# ❌ WRONG: Some callers updated, others not
# In moduleA.py
from new_api import process  # ✅ Updated

# In moduleB.py
from old_api import process  # ❌ Still using old version
```

### Don't Leave Legacy Code Behind with Conditionals
```python
# ❌ WRONG: Comment saying "TODO: remove this when migrated"
def handle_request(request):
    # TODO: Remove this legacy path once all clients upgrade
    if old_request_format(request):
        return legacy_handler(request)  # Don't leave this!
    return new_handler(request)
```

---

## ✅ What TO Do Instead

### 1. Identify ALL Callers FIRST
```python
# Use ripgrep to find every call site
# rg "old_function\(" --type py
# rg "import old_module" --type py
# Find every reference BEFORE making changes
```

### 2. Update ALL Code Paths Simultaneously
```python
# ✅ CORRECT: Change everything at once

# Step 1: Identify all callers (5 files)
#  - services/auth.py:42
#  - tools/workspace.py:15
#  - infrastructure/db.py:89
#  - tests/test_auth.py:23
#  - tests/test_db.py:67

# Step 2: Update ALL 5 files in ONE commit
# Don't merge partial changes; do it all together

# Step 3: Run full test suite
# Ensure ALL tests pass (not just the ones you think matter)

# Step 4: Commit with full description
# "refactor: migrate from old_api to new_api (5 files)"
```

### 3. Remove Old Implementations Entirely
```python
# ✅ CORRECT: Delete completely
# Step 1: Change all callers to use new_process()
# Step 2: DELETE the old_process() function entirely
# Step 3: Delete old_process() tests
# Step 4: Delete any old_process imports

# Don't leave it "for reference" or "in case we need to rollback"
# Clean deletion forces you to think through the change
```

### 4. No Feature Flags or Shims
```python
# ❌ WRONG: Shim for compatibility
class NewAPI:
    @staticmethod
    def process(data):
        # Shim to old implementation
        return old_implementation(data)

# ✅ CORRECT: Direct implementation
class NewAPI:
    @staticmethod
    def process(data):
        # Your new logic here
        return direct_new_logic(data)
```

### 5. Ensure ALL Tests Pass
```bash
# ❌ WRONG
pytest tests/unit/auth.py        # ✅ Passes
# But you haven't run:
pytest tests/integration/
pytest tests/e2e/

# ✅ CORRECT
pytest                           # Full test suite must pass
# OR at minimum:
pytest tests/unit
pytest tests/integration
pytest tests/e2e
```

---

## 🔄 Refactoring Workflow

### Phase 1: Discovery (Before any code changes)
```bash
# 1. Search for all usages
rg "old_signature" --type py -n

# 2. Document all callers
# - File: infrastructure/adapters.py, Line: 42
# - File: services/auth.py, Line: 15
# - File: tools/workspace.py, Line: 89
# - etc.

# 3. Plan the atomic change
# You WILL change all these files together
```

### Phase 2: Implementation (Single atomic commit)
```bash
# 1. Update implementation
# Edit: services/embedding_factory.py
#   - Change function signature
#   - Update logic
#   - Remove old code paths

# 2. Update ALL callers
# Edit: tools/workspace.py
# Edit: infrastructure/adapters.py
# Edit: services/auth.py
# ... (all 7 files that use this function)

# 3. Update ALL tests
# Edit: tests/unit/test_embedding_factory.py
# Edit: tests/integration/test_workspace.py
# ... (all test files that reference old API)

# All changes in ONE commit
```

### Phase 3: Validation
```bash
# 1. Full test run
pytest

# 2. Type checking (if configured)
mypy

# 3. Linting
ruff check

# 4. Verify no legacy code remains
rg "old_function" --type py  # Should find NOTHING
```

### Phase 4: Commit
```bash
git add <all changed files>
git commit -m "refactor: migrate from old_api to new_api

This refactoring updates:
- services/embedding_factory.py (signature change)
- infrastructure/adapters.py (caller update)
- tools/workspace.py (caller update)
- services/auth.py (caller update)
- 4 test files (updated for new signature)

All tests pass. No legacy code paths remain."
```

---

## 🎯 When This Applies

### Apply Aggressive Changes To:

1. **Signature Changes**
   - Function/method parameter updates
   - Return type changes
   - Exception changes
   → Update ALL callers at once

2. **API Redesigns**
   - Class/module interface changes
   - Module reorganization
   - Pattern migrations
   → Update ALL callers at once

3. **Code Reorganization**
   - Moving code between modules
   - Consolidating duplicated logic
   - Splitting responsibilities
   → Update ALL imports at once

4. **Architecture Updates**
   - Database layer changes
   - Authentication provider updates
   - Infrastructure adapter changes
   → Update ALL dependent services at once

5. **Pattern Modernization**
   - Old async patterns → new async patterns
   - Old validation patterns → new validation patterns
   - Old error handling → new error handling
   → Update ALL usages at once

---

## 💡 Why This Approach?

### 1. **Clarity**
```
✅ Old way: Look at function X, read 5 paths to understand it
❌ New way: 1 clear path, easy to understand
```

### 2. **Performance**
```
✅ No runtime "if deprecated" checks
✅ No conditional branching for legacy support
✅ Straight through fast path
```

### 3. **Maintainability**
```
✅ Future developers inherit clean code
✅ No "this is for legacy support" comments
✅ No "TODO: remove this when upgraded" debt
```

### 4. **Testing**
```
✅ Test all paths—not "old path still works" vs "new path works"
✅ ALL tests pass or NONE pass (no partial states)
✅ Clear validation of complete changes
```

### 5. **Git History**
```
✅ Clean commits that do ONE thing
❌ Not: "Add new API (but keep old one for now)"
✅ But: "Migrate from old_api to new_api (5 files, all tests pass)"
```

---

## 🚀 Real Example

### Scenario: Refactor auth signature

**BEFORE**: `validate_token(token: str, issuer: str) -> Dict`

**AFTER**: `validate_token(token: str, required_scopes: List[str]) -> User`

#### ❌ OLD (WRONG) APPROACH
```python
# File: auth/validators.py
def validate_token(token: str, issuer: str = None, required_scopes: List[str] = None):
    if issuer is not None:
        # Legacy path - keep for compatibility
        return legacy_validate(token, issuer)
    else:
        # New path
        return new_validate(token, required_scopes)

# Files that use it: 8 different modules
# Some update to new signature, others don't
# Tests for both paths still exist
# Result: Confusion, complexity, technical debt
```

#### ✅ NEW (CORRECT) APPROACH

**Step 1: Find all callers**
```bash
rg "validate_token\(" --type py -n
# Results:
# infrastructure/supabase_auth.py:45
# services/auth/hybrid_auth_provider.py:78
# tools/workspace.py:23
# tools/entity.py:56
# tests/unit/test_auth.py:42
# tests/integration/test_workspace.py:15
# ... (all 8 locations)
```

**Step 2: Update ALL together**
```python
# File: auth/validators.py - CLEAN implementation
class User:
    user_id: str
    scopes: List[str]

def validate_token(token: str, required_scopes: List[str]) -> User:
    # Single clean path
    return User(...)

# File: infrastructure/supabase_auth.py - UPDATE
user = validate_token(token, required_scopes=["read:data"])

# File: services/auth/hybrid_auth_provider.py - UPDATE
user = validate_token(token, required_scopes=["write:data"])

# File: tools/workspace.py - UPDATE
user = validate_token(token, required_scopes=["admin"])

# ... ALL 8 files updated

# File: tests/unit/test_auth.py - UPDATE
def test_validate_token_with_scopes():
    user = validate_token(token, required_scopes=["read"])
    assert "read" in user.scopes

# ... ALL tests updated
```

**Step 3: Validate completely**
```bash
pytest  # All pass
rg "validate_token.*issuer" --type py  # Nothing (legacy gone)
```

**Step 4: Single commit**
```bash
git commit -m "refactor: update validate_token signature

Changes validate_token from:
  validate_token(token, issuer) -> Dict
to:
  validate_token(token, required_scopes) -> User

Updates 8 call sites across:
- infrastructure/supabase_auth.py
- services/auth/hybrid_auth_provider.py
- tools/workspace.py
- tools/entity.py
- 4 test files

All tests pass. No legacy code paths remain."
```

---

## 📋 Checklist Before Committing

- [ ] **Found ALL callers** (used ripgrep to search thoroughly)
- [ ] **Updated ALL callers** (not just some)
- [ ] **Removed old code entirely** (not left as fallback)
- [ ] **Updated ALL tests** (not just new ones)
- [ ] **ALL tests pass** (full suite, not partial)
- [ ] **No legacy code remains** (ripgrep finds nothing)
- [ ] **No feature flags** (deleted any migration flags)
- [ ] **No shims/adapters** (no backwards compatibility wrappers)
- [ ] **Commit message is clear** (explains what changed and why)

---

## 🎓 Key Principles

1. **Atomicity**: Changes go in ONE commit, not spread over time
2. **Completeness**: Update ALL callers, not some
3. **Cleanliness**: Remove old code, don't preserve it
4. **Clarity**: Single implementation per feature
5. **Confidence**: ALL tests pass or change failed

---

## 📖 References

See these files for full agent guidelines:
- **AGENTS.md** - Agent automation expectations
- **CLAUDE.md** - Claude-specific guidelines
- **WARP.md** - Warp terminal workflow

---

## ✅ Status

**This policy is now ACTIVE** in:
- ✅ AGENTS.md
- ✅ CLAUDE.md  
- ✅ WARP.md

All agents must follow this policy for:
- Refactoring
- API changes
- Pattern migrations
- Code reorganization
- Infrastructure updates
- Architecture decisions

**No backwards compatibility cruft. Full changes only.**
