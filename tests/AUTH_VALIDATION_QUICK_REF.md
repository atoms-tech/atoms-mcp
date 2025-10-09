# Auth Validation - Quick Reference

## What Is It?

Comprehensive authentication validation that runs **after OAuth** and **before tests**.

## Flow

```
1. OAuth Authentication (user login)
   ↓
2. ✅ Authentication complete
   ↓
3. 🔍 Validating authentication...
   ├─ ✓ Token captured (JWT validation)
   ├─ ✓ HTTP endpoint accessible (200 OK)
   ├─ ✓ Tool call successful (list_tools)
   └─ ✓ Response structure valid
   ↓
4. ✅ Auth validation complete
   ↓
5. 🚀 Running tests (131 tests)
```

## Validation Checks

| Check | What It Does | Pass Criteria |
|-------|--------------|---------------|
| **Token** | Validates JWT structure, expiration | Token exists, not expired, valid format |
| **HTTP** | Tests endpoint with auth headers | 200 OK (not 401/403) |
| **Tool Call** | Calls list_tools() | Returns list of tools, no error |
| **Structure** | Validates response format | List with expected fields |

## Output Examples

### ✅ Success
```
🔍 Validating authentication...
   ✓ Token captured - 45ms
      eyJhbG... (expires in 23h 59m)
   ✓ HTTP endpoint accessible - 145ms
      (200 OK)
   ✓ Tool call successful - 423ms
      list_tools returned 15 tools
   ✓ Response structure valid - 10ms
      Structure valid (15 tools)

✅ Auth validation complete - Ready for test execution
```

### ❌ Failure
```
🔍 Validating authentication...
   ✓ Token captured - 32ms
   ✗ HTTP endpoint accessible - 2145ms
      401 Unauthorized - token may be invalid
   ✗ Tool call successful - 189ms
      Tool call failed: Unauthorized

❌ Auth validation failed
   → Token may be invalid or expired
   → Try clearing cache and retrying...
```

## Usage

### Automatic (Default)
```python
from tests.framework import AtomsMCPTestRunner

async with AtomsMCPTestRunner(
    mcp_endpoint="https://mcp.atoms.tech/api/mcp",
    verbose=True
) as runner:
    # Validation happens automatically
    summary = await runner.run_all()
```

### Manual
```python
from mcp_qa.testing.auth_validator import validate_auth

result = await validate_auth(
    client=client,
    credentials=credentials,
    mcp_endpoint=mcp_endpoint
)

if not result.valid:
    print(f"Failed: {result.error}")
```

## Troubleshooting

### Clear Cache
```bash
rm -rf ~/.atoms_mcp_test_cache
```

### Run Validation Only
```bash
python tests/test_auth_validation.py
```

### Check Credentials
```bash
cat .env | grep TEST_
```

## Configuration

```python
from mcp_qa.testing.auth_validator import AuthValidator

validator = AuthValidator(
    client=client,
    credentials=credentials,
    mcp_endpoint=mcp_endpoint,
    timeout=60.0,      # Default: 30s
    verbose=True       # Default: True
)
```

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `Token is placeholder` | Token not captured from OAuth | Clear cache, re-authenticate |
| `401 Unauthorized` | Invalid/expired token | Clear cache, check credentials |
| `Tool call timeout` | Slow/unresponsive server | Increase timeout, check network |
| `Endpoint not accessible` | Server down/unreachable | Check URL, firewall, network |

## Files

- **Core Module:** `mcp_qa/testing/auth_validator.py`
- **Integration:** `mcp_qa/testing/unified_runner.py` (line 99-121)
- **Test Script:** `tests/test_auth_validation.py`
- **Example:** `tests/example_auth_validation.py`
- **Docs:** `mcp_qa/testing/README_AUTH_VALIDATION.md`

## Benefits

✅ **Catches auth issues early** (before running 131 tests)
✅ **Clear error messages** (not "test 47 failed")
✅ **Faster debugging** (know what's broken immediately)
✅ **Better UX** (progress indicators, timing)
✅ **Automatic retry** (handles transient failures)

## Timeline

- **Before:** OAuth → Run tests → Many failures → Debug
- **After:** OAuth → Validate → Pass/Fail → Run tests (if valid)

Time saved: **~5-10 minutes** per debug cycle

## Quick Test

```bash
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/atoms_mcp-old
python tests/test_auth_validation.py
```

Expected output:
```
🔐 Authenticating...
✅ Authentication complete

🔍 Validating authentication...
   ✓ Token captured - 45ms
   ✓ HTTP endpoint accessible - 145ms
   ✓ Tool call successful - 423ms
   ✓ Response structure valid - 10ms

✅ Auth validation passed - Ready for test execution
```

## Summary

**What:** Validates auth after OAuth, before tests
**Where:** UnifiedMCPTestRunner.initialize()
**When:** After line 93 (OAuth), before line 124 (parallel pool)
**Why:** Catch auth issues early, save time debugging
**How:** 4 checks (token, HTTP, tool call, structure)
**Result:** Pass → run tests, Fail → abort with clear error
