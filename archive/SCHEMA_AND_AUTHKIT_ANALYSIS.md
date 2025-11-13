# Schema & AuthKit Analysis

## Question 1: Do we use sb-pydantic for schema generation?

### Answer: ⚠️ **PARTIALLY / NOT CURRENTLY**

### Evidence

**1. References to sb-pydantic exist:**
```python
# build/lib/schemas/triggers.py lines 19-28
# OrganizationType needs to be added - database has it but sb-pydantic didn't generate it
# Temporary inline definition until we add it to generated file

# OrganizationType is missing from generated (bug in sb-pydantic)
from schemas.generated.fastapi.schema_public_latest import (
    PublicUserRoleTypeEnum as UserRoleType,
)
```

**2. But no generated schemas found:**
```bash
$ ls -la build/lib/schemas/generated/
No generated directory

$ ls -la schemas/
No schemas directory at root
```

**3. Current approach: Manual Pydantic models**
- `build/lib/schemas/enums.py` - Manual enum definitions
- `tools/entity.py` - Manual schema dictionaries
- `tools/base.py` - Manual entity table mappings
- No auto-generated Pydantic models from Supabase

**4. Newer architecture (vecfin-latest):**
```python
# src/atoms_mcp/domain/models/entity.py
@dataclass
class Entity:
    """Base entity class with common attributes."""
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    # ... manual dataclasses
```

### Conclusion

❌ **NOT using sb-pydantic/supabase-pydantic for type generation**

**Current approach:**
- Manual Pydantic models
- Manual schema dictionaries
- Manual enum definitions
- Comments reference sb-pydantic but it's not actually used

**Recommendation:**
1. ✅ Add sb-pydantic to generate types from Supabase
2. ✅ Replace manual schemas with generated ones
3. ✅ Keep type safety and auto-completion

---

## Question 2: Update to Native AuthKit Pattern

### Current Implementation (Standalone Connect)

**File**: `server.py` lines 340-357

```python
# Configure AuthKitProvider for OAuth with Standalone Connect
authkit_domain = os.getenv("FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN")
if not authkit_domain:
    raise ValueError("FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN required")

# Use PersistentAuthKitProvider for stateless deployments with Supabase sessions
from auth.persistent_authkit_provider import PersistentAuthKitProvider

auth_provider = PersistentAuthKitProvider(
    authkit_domain=authkit_domain,
    base_url=base_url,
    required_scopes=None,  # Don't require specific scopes
)

mcp = FastMCP(
    name="atoms-fastmcp-consolidated",
    instructions="...",
    auth=auth_provider,  # Custom provider
)
```

**Custom files needed:**
- `auth/persistent_authkit_provider.py` - Custom auth provider
- `auth/session_middleware.py` - Session handling
- `auth/session_manager.py` - Supabase session persistence
- Custom OAuth endpoints

**Complexity**: HIGH

---

### Native AuthKit Pattern (Recommended)

**File**: Update `server.py`

```python
from fastmcp import FastMCP
from fastmcp.auth import AuthKitProvider

# Simple native configuration
mcp = FastMCP(
    name="atoms-fastmcp-consolidated",
    instructions="...",
    auth=AuthKitProvider(
        authkit_domain=os.getenv("FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN"),
        # FastMCP handles everything else automatically
    ),
)
```

**Custom files needed:**
- None! FastMCP handles it all

**Complexity**: LOW

---

### Comparison

| Feature | Standalone Connect (Current) | Native AuthKit (Recommended) |
|---------|------------------------------|------------------------------|
| **Lines of code** | ~500 (custom auth files) | ~5 (config only) |
| **Custom files** | 3 files | 0 files |
| **Session management** | Custom Supabase | Built-in |
| **OAuth endpoints** | Custom routes | Auto-generated |
| **Maintenance** | High | Low |
| **Stateless support** | Yes (custom) | Yes (built-in) |
| **Works on Vercel** | Yes | Yes |

---

### Migration Plan

#### Step 1: Update server.py

**Remove:**
```python
# Lines 340-357 - Custom auth provider setup
# Lines 662-694 - Custom OAuth endpoints
# Lines 697-702 - SessionMiddleware
```

**Add:**
```python
from fastmcp.auth import AuthKitProvider

auth_provider = AuthKitProvider(
    authkit_domain=os.getenv("FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN"),
)

mcp = FastMCP(
    name="atoms-fastmcp-consolidated",
    instructions="...",
    auth=auth_provider,
)
```

#### Step 2: Remove custom auth files

```bash
# These are no longer needed
rm auth/persistent_authkit_provider.py
rm auth/session_middleware.py
rm auth/session_manager.py
```

#### Step 3: Update environment variables

**Keep:**
```bash
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN=https://auth.workos.com/...
```

**Remove (no longer needed):**
```bash
ATOMS_FASTMCP_BASE_URL
ATOMS_FASTMCP_PUBLIC_BASE_URL
# FastMCP auto-detects these
```

#### Step 4: Test

```bash
# Test locally
python -m server

# Test OAuth flow
# FastMCP will auto-generate:
# - /.well-known/oauth-protected-resource
# - /.well-known/oauth-authorization-server
# - /auth/start
# - /auth/complete
```

---

### Benefits of Native AuthKit

1. ✅ **Less code** - 500 lines → 5 lines
2. ✅ **Less maintenance** - No custom auth logic
3. ✅ **Better tested** - FastMCP team maintains it
4. ✅ **Auto-updates** - Get fixes with FastMCP updates
5. ✅ **Simpler deployment** - Fewer files to deploy
6. ✅ **Better docs** - Official FastMCP documentation

---

### Risks

⚠️ **Potential issues:**

1. **Session persistence** - Current uses Supabase for sessions
   - Native: Uses FastMCP's built-in session management
   - **Impact**: May need to migrate existing sessions

2. **Custom token handling** - Current has custom JWT extraction
   - Native: Uses FastMCP's standard token handling
   - **Impact**: Should work the same

3. **RLS context** - Current passes token to Supabase
   - Native: Same - token still available via `get_access_token()`
   - **Impact**: No change needed

---

### Recommendation

✅ **DO IT** - Benefits far outweigh risks

**Timeline:**
1. **Now**: Test native AuthKit in development
2. **This week**: Deploy to preview
3. **Next week**: Deploy to production

**Rollback plan:**
- Keep current code in git
- Can revert if issues found

---

## Summary

### Schema Generation
- ❌ **NOT currently using sb-pydantic**
- ✅ **Should add it** for type safety

### AuthKit Pattern
- ⚠️ **Currently using Standalone Connect** (complex)
- ✅ **Should migrate to Native AuthKit** (simple)

### Action Items

**Immediate:**
1. ✅ Update to native AuthKit pattern
2. ✅ Test OAuth flow
3. ✅ Deploy to preview

**Short term:**
1. ⚠️ Add sb-pydantic for schema generation
2. ⚠️ Replace manual schemas
3. ⚠️ Add type safety

**Long term:**
1. ⚠️ Migrate to hexagonal architecture
2. ⚠️ Add comprehensive tests
3. ⚠️ Performance optimization

