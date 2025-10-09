# Testing Auth Validation

## Test Plan

### Phase 1: Unit Tests (Auth Validator)

Test the auth validator module in isolation.

#### Test 1: Token Validation

**File:** `test_auth_validation.py`

**What to test:**
- Valid JWT token parsing
- Expired token detection
- Invalid token format handling
- Non-JWT token handling (warning but continue)
- Placeholder token detection

**Expected results:**
```python
# Valid token
success, msg = await validator.validate_token()
assert success == True
assert "expires in" in msg

# Expired token
success, msg = await validator.validate_token()
assert success == False
assert "expired" in msg

# Placeholder token
success, msg = await validator.validate_token()
assert success == False
assert "placeholder" in msg
```

#### Test 2: HTTP Endpoint Validation

**What to test:**
- Successful connection (200 OK)
- Unauthorized (401) detection
- Forbidden (403) detection
- Connection timeout
- Endpoint not found

**Expected results:**
```python
# Success
success, msg = await validator.validate_http_endpoint()
assert success == True
assert "200" in msg or "OK" in msg

# Unauthorized
success, msg = await validator.validate_http_endpoint()
assert success == False
assert "401" in msg or "Unauthorized" in msg
```

#### Test 3: Tool Call Validation

**What to test:**
- Successful list_tools() call
- Tool call timeout
- Tool call authorization failure
- Empty tool list
- Invalid response format

**Expected results:**
```python
# Success
success, msg = await validator.validate_tool_call()
assert success == True
assert "list_tools succeeded" in msg

# Timeout
success, msg = await validator.validate_tool_call()
assert success == False
assert "timeout" in msg.lower()
```

#### Test 4: Response Structure Validation

**What to test:**
- Valid list response
- Invalid response type (not a list)
- Missing required fields
- Empty response
- Malformed response

**Expected results:**
```python
# Valid
success, msg = await validator.validate_response_structure()
assert success == True
assert "valid" in msg.lower()

# Invalid type
success, msg = await validator.validate_response_structure()
assert success == False
assert "expected list" in msg.lower()
```

### Phase 2: Integration Tests (Unified Runner)

Test auth validation integration with UnifiedMCPTestRunner.

#### Test 5: Successful Validation Flow

**Script:** `test_auth_validation.py`

**Steps:**
1. Initialize UnifiedMCPTestRunner
2. Call initialize()
3. Check _auth_validated flag
4. Verify validation_result is set
5. Verify validation_result.valid is True

**Expected output:**
```
✅ Authentication complete
🔍 Validating authentication...
   ✓ Token captured
   ✓ HTTP endpoint accessible
   ✓ Tool call successful
   ✓ Response structure valid
✅ Auth validation complete - Ready for test execution
```

#### Test 6: Failed Validation Flow

**Setup:** Use invalid credentials or expired token

**Steps:**
1. Initialize UnifiedMCPTestRunner
2. Call initialize()
3. Expect RuntimeError
4. Verify error message contains validation details

**Expected behavior:**
```python
try:
    await runner.initialize()
    assert False, "Should have raised RuntimeError"
except RuntimeError as e:
    assert "Authentication validation failed" in str(e)
    assert runner.validation_result.valid == False
```

#### Test 7: Validation Result Access

**Steps:**
1. Initialize runner
2. Access runner.validation_result
3. Verify checks dict is populated
4. Verify duration_ms is set
5. Verify error field (if failed)

**Expected structure:**
```python
result = runner.validation_result
assert isinstance(result, ValidationResult)
assert 'token' in result.checks
assert 'http_endpoint' in result.checks
assert 'tool_call' in result.checks
assert 'response_structure' in result.checks
assert result.duration_ms > 0
```

### Phase 3: End-to-End Tests (Atoms Runner)

Test complete flow with AtomsMCPTestRunner.

#### Test 8: Full Test Suite with Validation

**Script:** `tests/run_tests.py` or `example_auth_validation.py`

**Steps:**
1. Run AtomsMCPTestRunner with verbose=True
2. Observe OAuth flow
3. Observe validation phase
4. Observe test execution
5. Check validation summary display

**Expected output:**
```
📡 Connecting to https://mcp.atoms.tech/api/mcp...
🔐 Authenticating...
✅ Authentication complete (21.0s)

🔍 Validating authentication...
   ✓ Token captured - 45ms
   ✓ HTTP endpoint accessible - 145ms
   ✓ Tool call successful - 423ms
   ✓ Response structure valid - 10ms

✅ Auth validation complete - Ready for test execution

📊 Auth Validation Summary:
   ✓ token: Token valid (expires in 23h 59m)
   ✓ http_endpoint: 200 OK
   ✓ tool_call: list_tools succeeded (15 tools, 423ms)
   ✓ response_structure: Structure valid (15 tools)

🚀 Running Atoms MCP tests...
   Endpoint: https://mcp.atoms.tech/api/mcp
   Parallel: True (16 workers)
   Cache: True

[Test execution continues...]
```

#### Test 9: Validation Retry on Transient Failure

**Setup:** Simulate transient failure (slow network, timeout)

**Steps:**
1. First validation fails (timeout)
2. Automatic retry triggered
3. Second validation succeeds
4. Tests proceed

**Expected output:**
```
🔍 Validating authentication...
   ✗ Tool call successful - 30001ms
      Tool call timed out after 30s

⚠️  Retrying validation...

🔍 Validating authentication...
   ✓ Token captured - 42ms
   ✓ HTTP endpoint accessible - 156ms
   ✓ Tool call successful - 398ms
   ✓ Response structure valid - 12ms

✅ Auth validation complete - Ready for test execution
```

### Phase 4: Error Handling Tests

#### Test 10: Invalid Token Handling

**Setup:** Modify credentials to have invalid token

**Steps:**
1. Set credentials.access_token = "INVALID_TEST_TOKEN_12345"  # Deliberately invalid for testing
2. Run validation
3. Verify token check fails
4. Verify helpful error message

**Expected:**
- Token validation fails
- HTTP endpoint fails (401)
- Tool call fails (Unauthorized)
- Clear error message with troubleshooting steps

#### Test 11: Network Timeout Handling

**Setup:** Use unreachable endpoint

**Steps:**
1. Set mcp_endpoint to unreachable URL
2. Run validation
3. Verify timeout handling
4. Verify error message

**Expected:**
- HTTP endpoint check times out
- Tool call check times out (or skipped)
- Error message includes timeout info

#### Test 12: Missing Token Handling

**Setup:** Set credentials.access_token = None or ""

**Steps:**
1. Run validation
2. Verify token check fails immediately
3. Verify other checks are skipped

**Expected:**
```
🔍 Validating authentication...
   ✗ Token captured - 5ms
      Token is placeholder or empty

❌ Auth validation failed:
   ✗ token: Token is placeholder or empty
```

### Phase 5: Performance Tests

#### Test 13: Validation Timing

**What to measure:**
- Total validation time
- Individual check times
- Overhead vs actual test runtime

**Expected:**
- Token validation: < 100ms
- HTTP endpoint: < 500ms
- Tool call: < 1000ms
- Response structure: < 100ms
- Total: < 2000ms (2 seconds)

**Verify:**
```python
result = await validator.validate_all()
assert result.duration_ms < 2000, f"Validation too slow: {result.duration_ms}ms"

for check_name, check_result in result.checks.items():
    # Each check should have timing info
    print(f"{check_name}: {check_result['duration']}ms")
```

#### Test 14: Parallel Validation (Future)

**Goal:** Validate multiple checks in parallel

**Current:** Sequential (token → HTTP → tool → structure)
**Future:** Parallel (all checks at once)

**Expected improvement:**
- Current: ~2000ms total
- Parallel: ~500ms total (limited by slowest check)

### Phase 6: Regression Tests

#### Test 15: Backward Compatibility

**Verify:**
- Tests still run without validation (if disabled)
- Existing test code doesn't break
- Validation is opt-in (can be disabled)

**Test:**
```python
# Should work without validation
runner = UnifiedMCPTestRunner(
    mcp_endpoint=endpoint,
    validate_auth=False  # Disable validation (if implemented)
)
```

#### Test 16: Cache Handling

**Verify:**
- Cached credentials work
- Validation uses cached credentials
- Cache is cleared on validation failure

**Test:**
```bash
# Run once (creates cache)
python tests/test_auth_validation.py

# Run again (uses cache)
python tests/test_auth_validation.py

# Should complete faster (no OAuth)
```

## Test Execution

### Run All Tests

```bash
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/atoms_mcp-old

# Unit tests
python tests/test_auth_validation.py

# Integration tests
python tests/example_auth_validation.py

# Full test suite
python tests/run_tests.py
```

### Run Specific Tests

```bash
# Token validation only
python -c "
import asyncio
from mcp_qa.testing.auth_validator import AuthValidator
# ... setup ...
success, msg = await validator.validate_token()
print(f'Token: {success} - {msg}')
"

# HTTP endpoint only
python -c "
import asyncio
from mcp_qa.testing.auth_validator import AuthValidator
# ... setup ...
success, msg = await validator.validate_http_endpoint()
print(f'HTTP: {success} - {msg}')
"
```

### Debug Mode

```bash
# Run with verbose output
OAUTH_DEBUG=1 python tests/test_auth_validation.py

# Run with Python debugger
python -m pdb tests/test_auth_validation.py
```

## Test Results Checklist

- [ ] Token validation works
- [ ] HTTP endpoint validation works
- [ ] Tool call validation works
- [ ] Response structure validation works
- [ ] Integration with UnifiedMCPTestRunner works
- [ ] Integration with AtomsMCPTestRunner works
- [ ] Validation summary displays correctly
- [ ] Failed validation raises RuntimeError
- [ ] Retry on failure works
- [ ] Error messages are clear
- [ ] Troubleshooting steps are helpful
- [ ] Performance is acceptable (< 2s)
- [ ] No regressions in existing tests

## Success Criteria

1. **Functionality**
   - All 4 validation checks work correctly
   - Integration with runners works
   - Error handling is robust

2. **User Experience**
   - Clear progress indicators
   - Helpful error messages
   - Reasonable performance

3. **Reliability**
   - Handles transient failures (retry)
   - Detects invalid credentials
   - Prevents tests from running with bad auth

4. **Documentation**
   - Code is well-commented
   - Examples are clear
   - Troubleshooting is comprehensive

## Known Issues / Future Improvements

### Known Issues
1. Token format validation assumes JWT (warns on non-JWT)
2. HTTP endpoint validation tries multiple paths (might be slow)
3. Tool call validation only tests list_tools (could test other tools)

### Future Improvements
1. **Parallel validation** - run checks concurrently
2. **Custom checks** - allow projects to add their own checks
3. **Validation cache** - cache successful validation for X minutes
4. **More checks** - test additional MCP operations
5. **Configurable timeout** - per-check timeout settings
6. **Validation report** - detailed report with timing breakdown

## Rollback Plan

If validation causes issues:

1. **Disable validation:**
   ```python
   # In unified_runner.py, comment out validation block
   # Lines 99-121
   ```

2. **Remove import:**
   ```python
   # Remove line 27
   # from mcp_qa.testing.auth_validator import validate_auth
   ```

3. **Revert files:**
   ```bash
   git diff mcp_qa/testing/unified_runner.py
   git checkout mcp_qa/testing/unified_runner.py
   ```

## Contact

For issues or questions:
- Check documentation: `mcp_qa/testing/README_AUTH_VALIDATION.md`
- Review examples: `tests/example_auth_validation.py`
- Run test: `python tests/test_auth_validation.py`
