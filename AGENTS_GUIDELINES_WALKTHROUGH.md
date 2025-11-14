# AGENTS.md Guidelines Deep Dive

## Three Core Principles

### 1. **AGGRESSIVE CHANGE POLICY** (No Backwards Compatibility)

#### The Rule
```
NO backwards compatibility. NO gentle migrations. NO MVP-grade implementations.
```

#### What This Means

**❌ FORBIDDEN:**
```python
# BAD: Keeping old code for "transition period"
def new_function():
    """New implementation."""
    return compute()

def old_function():
    """Deprecated - use new_function instead."""
    # Still here for backwards compatibility
    return new_function()

if use_new_api:
    result = new_function()
else:
    result = old_function()  # ❌ Conditional branching = technical debt
```

**✅ REQUIRED:**
```python
# GOOD: Complete replacement, all callers updated
def compute():
    """Implementation (renamed from both old and new functions)."""
    return ...

# Old function DELETED entirely
# All callers updated to use compute()

# Single code path - no branches
result = compute()
```

#### Why This Matters

1. **Clarity**: One way to do something, not multiple
2. **Performance**: No conditional checks on every call
3. **Maintainability**: Less surface area = fewer bugs
4. **Testing**: Single path = simpler tests

#### Real-World Impact

**Before (with backwards compat):**
```python
# services/auth.py - 150 lines
def validate_token_old(token):  # Legacy pattern
    ...

def validate_token(token):      # New pattern
    ...

def validate_token_hybrid(token):
    if legacy_mode:             # 🚨 Branch on every call
        return validate_token_old(token)
    return validate_token(token)

# Called everywhere:
result = validate_token_hybrid(token)  # Slow, unclear
```

**After (aggressive):**
```python
# services/auth.py - 50 lines
def validate_token(token):      # Single, clear implementation
    ...

# Called everywhere:
result = validate_token(token)  # Fast, clear
```

---

### 2. **DRY (Don't Repeat Yourself)** - Canonical Test Naming

#### The Rule
```
Test file names must answer: "What component/concern does this test?"
NOT: "How fast is it?" or "What variant?"
```

#### The Problem: Non-Canonical Naming

**❌ BAD NAMES (Metadata-Based):**
```
test_entity_fast.py          # "fast" = speed metadata, not what's tested
test_entity_slow.py          # "slow" = speed metadata
test_entity_unit.py          # "unit" = scope/execution metadata
test_entity_integration.py   # "integration" = client type metadata
test_entity_e2e.py           # "e2e" = test stage metadata
test_entity_v2.py            # "v2" = version metadata (belongs in git)
test_entity_old.py           # "old" = temporal metadata
test_entity_new.py           # "new" = temporal metadata
```

**Why these are bad:**
- File names don't describe WHAT is being tested
- Make it hard to find related tests
- Encourage duplication (same test written 3 times for 3 variants)
- File names become cluttered with metadata noise

#### The Solution: Concern-Based Naming

**✅ GOOD NAMES (Concern-Based):**
```
test_entity.py               # All entity tool tests
test_entity_crud.py          # Focused on CREATE/READ/UPDATE/DELETE
test_entity_validation.py    # Focused on input validation
test_auth_supabase.py        # Supabase-specific auth integration
test_auth_authkit.py         # AuthKit integration (different provider)
test_relationship_member.py  # Member relationship type tests
test_database_adapter.py     # All database adapter tests
```

**Why these are good:**
- File name immediately tells you what's being tested
- No temporal/speed/version noise
- Easier to find related tests
- Encourages consolidation of duplicate tests

#### Real Example: The Variant Problem

**❌ BAD: Three Separate Files (Code Duplication)**
```
# tests/unit/tools/test_entity_unit.py
async def test_entity_creation(mcp_client_inmemory):
    result = await mcp_client_inmemory.call_tool("entity_tool", {...})
    assert result.success

# tests/integration/tools/test_entity_integration.py
async def test_entity_creation(mcp_client_http):  # Same test name!
    result = await mcp_client_http.call_tool("entity_tool", {...})
    assert result.success

# tests/e2e/tools/test_entity_e2e.py
async def test_entity_creation(mcp_client_e2e):   # Same test name AGAIN!
    result = await mcp_client_e2e.call_tool("entity_tool", {...})
    assert result.success
```

**Problems:**
- Same test logic written 3 times (DRY violation)
- Hard to maintain - change in one place = change in 3 places
- File names hide that these are duplicates

**✅ GOOD: Single File with Parametrized Fixture**
```python
# tests/unit/tools/test_entity.py

@pytest.fixture(params=["unit", "integration", "e2e"])
def mcp_client(request):
    """Parametrized client: tests run 3 times, once per variant."""
    if request.param == "unit":
        return InMemoryMcpClient()         # Fast, deterministic
    elif request.param == "integration":
        return HttpMcpClient(...)          # Live database
    elif request.param == "e2e":
        return DeploymentMcpClient(...)    # Production setup
    return get_client(request.param)

async def test_entity_creation(mcp_client):
    """Runs 3 times automatically: unit, integration, e2e."""
    result = await mcp_client.call_tool("entity_tool", {...})
    assert result.success
```

**Benefits:**
- Single source of truth (one test method)
- Same logic runs across all 3 variants automatically
- Change once = all variants update
- Adding new variant only requires fixture change
- No code duplication

---

### 3. **NO BACKWARDS COMPATIBILITY (Full, Complete Changes)**

#### The Rule
```
When refactoring, update ALL callers and code paths simultaneously.
Remove old code entirely. Don't leave conditional branches.
```

#### Decision Tree

**When you find old code patterns:**

| Situation | Wrong ❌ | Right ✅ |
|-----------|---------|---------|
| **Old function exists, new function added** | Keep both + shim | Delete old, update all callers |
| **Old file + new file with same concern** | Maintain both | Merge, keep one canonical file |
| **Feature flag for old behavior** | Keep as toggle | Remove flag, commit to new behavior |
| **Deprecated parameter** | Support both | Remove old param, update all calls |
| **Legacy error handling** | Try new, fallback to old | Use new error handling only |

#### Real-World Example: Auth Refactoring

**❌ WRONG (With Backwards Compat Shim)**
```python
# infrastructure/auth.py

# Old method (still here for backwards compat)
def validate_token_legacy(token: str) -> bool:
    """Legacy validation - DO NOT USE."""
    # Still 100 lines of old code
    ...

# New method
def validate_token_modern(token: str) -> bool:
    """New validation approach."""
    ...

# Shim to support both ❌
def validate_token(token: str) -> bool:
    """Router function (technical debt!)."""
    if os.getenv("USE_NEW_AUTH"):  # Feature flag (more debt!)
        return validate_token_modern(token)
    return validate_token_legacy(token)

# All callers have branches ❌
if use_new_auth:
    from .auth import validate_token_modern
else:
    from .auth import validate_token_legacy
```

**✅ RIGHT (Complete Replacement)**
```python
# infrastructure/auth.py

# Single, authoritative implementation
def validate_token(token: str) -> bool:
    """Validate authentication token.
    
    Uses the modern validation approach with JWT parsing and
    workspace membership verification.
    """
    ...

# Old code deleted entirely
# Feature flag removed
# All callers use the same function
result = validate_token(token)  # Simple, fast, clear
```

#### Benefits of Aggressive Changes

| Aspect | With Compat | Aggressive |
|--------|------------|-----------|
| **Code Lines** | 200 (100 old + 100 new + shim) | 100 (new only) |
| **Execution Speed** | Feature flag check on every call | Direct execution |
| **Test Coverage** | Must test both paths | Single path |
| **Maintenance** | Update 2 implementations | Update 1 |
| **Learning Curve** | New developers confused | Clear pattern |

---

## Implementation Guidelines Summary

### Naming Hygiene
1. **Test files** - Name by concern, not metadata
2. **Functions** - Clear purpose, not version numbers
3. **Branches/flags** - Avoid, commit to decision
4. **Deprecated code** - Delete, not comment-out

### Code Quality
1. **No shims** - Remove old code entirely
2. **No feature flags** - Commit to behavior
3. **No fallbacks** - Use new approach only
4. **No TODOs** - Fix immediately or document in session notes

### Testing
1. **One file per concern** - Not one per variant
2. **Parametrized fixtures** - Run tests across variants
3. **Canonical names** - Describe what's tested
4. **No duplication** - Same test = same file

### Refactoring
1. **Update ALL callers** - Not partial migrations
2. **Full decomposition** - Not gentle transitions
3. **Delete old code** - Not preserve with warnings
4. **Verify everything passes** - No broken intermediate states

---

## Common Mistakes to Avoid

### ❌ Mistake 1: Keeping "Temporary" Code
```python
# BAD: "We'll clean this up later"
if new_auth_enabled:  # 🚨 This never gets cleaned up
    return validate_new(token)
return validate_old(token)
```

**Fix:** Choose one approach, update all callers, delete the other.

### ❌ Mistake 2: Creating Parallel Test Files
```
# BAD: Three files for one tool
test_entity_unit.py
test_entity_integration.py
test_entity_e2e.py
```

**Fix:** One file with parametrized fixture.

### ❌ Mistake 3: Version Numbers in File Names
```python
# BAD: Version metadata in filename
test_auth_v2.py      # What was v1?
test_entity_v3.py    # Where are v1 and v2?
```

**Fix:** Use git history. Name by concern.

### ❌ Mistake 4: Metadata Suffixes
```python
# BAD: Speed metadata
test_entity_slow.py  # Should be test_entity.py with @pytest.mark.performance
test_entity_fast.py  # Should be test_entity.py with @pytest.mark.smoke
```

**Fix:** Same file, use markers.

---

## When to NOT Be Aggressive

⚠️ **Only keep backwards compat if:**
1. **Production deployment** - Can't break clients
   - Solution: API versioning (v1/ vs v2/), not code shims
2. **Public library API** - External users depend on it
   - Solution: Deprecation warnings + version bump, not internal shims
3. **Database migration** - Data needs gradual transition
   - Solution: Migration scripts, not forever-conditional code

✅ **For internal code (repo like this):**
- No backwards compat needed
- Aggressive changes are the standard
- All callers updated simultaneously

---

## Applying These Principles

### Example: Refactoring Authentication

**Step 1: Identify all callers**
```bash
rg "validate_token\(" --type py
# Find every place it's called
```

**Step 2: Plan the change (all at once)**
- Remove old function
- Remove shim function
- Update all 15 callers
- Delete old tests

**Step 3: Execute the change**
```python
# Before: 3 functions with conditional logic
# After: 1 clean function, all callers use it
```

**Step 4: Verify**
```bash
# All tests pass
pytest tests/
# No callers still using old pattern
rg "validate_token_legacy" --type py  # Should find nothing
```

---

## Checklist for PRs

Before committing any refactoring:

- [ ] **No backwards compat shims** - All old code deleted
- [ ] **No feature flags** - Removed entirely or don't exist
- [ ] **All callers updated** - `rg` search confirms no stragglers
- [ ] **Test file names canonical** - Concern-based, not metadata
- [ ] **No test duplication** - Parametrized fixtures used
- [ ] **All tests pass** - No broken intermediate states
- [ ] **Line counts OK** - No files exceed 350 lines
- [ ] **Commit message clear** - Explains what changed and why

---

**TL;DR:**
1. ✅ **Aggressive**: Complete changes, all callers at once
2. ✅ **DRY tests**: One file per concern, parametrized fixtures
3. ✅ **Clean naming**: Describe what's tested, not how
4. ❌ **NO shims**: Remove old code entirely
5. ❌ **NO flags**: Commit to one behavior
