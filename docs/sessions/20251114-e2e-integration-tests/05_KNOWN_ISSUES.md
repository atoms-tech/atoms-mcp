# Known Issues & Findings

**Date:** November 14, 2025  
**Purpose:** Track blockers, findings, and workarounds discovered during session

## Pre-Implementation Issues (Before Testing Begins)

### Issue #1: Bearer Auth Slow Test
**Category:** Performance Issue  
**Severity:** Low (acceptable with @pytest.mark.slow)  
**Location:** `tests/e2e/test_auth_patterns.py::TestBearerTokenAuthentication::test_bearer_auth_invalid_token`  
**Duration:** 5.44s (threshold: 5.0s)

**Root Cause:** TBD - likely network delay in invalid token validation

**Investigation Needed:**
- [ ] Profile the test to find bottleneck
- [ ] Is it network latency or server-side validation?
- [ ] Can be optimized with mocking?

**Current Status:** Marked as slow, acceptable for now

**Resolution:** Will debug in Phase 4 if time permits

---

### Issue #2: Flaky Database Retry Test
**Category:** Test Flakiness  
**Severity:** Low (passes consistently on most runs)  
**Location:** `tests/e2e/test_resilience.py::TestErrorRecoveryResilience::test_database_connection_retry`  
**Behavior:** Sometimes passes on first try, sometimes requires retry

**Root Cause:** TBD - likely race condition or timing sensitivity

**Investigation Needed:**
- [ ] Add logging to understand retry triggers
- [ ] Check if test is truly flaky or test framework issue
- [ ] Review test logic for timing assumptions

**Current Status:** Monitoring, will fix in Phase 4

**Resolution:** Add deterministic assertions, remove timing sensitivity

---

### Issue #3: Non-Canonical Test File Names
**Category:** Code Organization  
**Severity:** Medium (consolidation opportunity)  
**Files:** TBD - identified in Phase 1 research

**Issue:** Some test files use non-canonical names:
- Speed suffixes: `_fast`, `_slow`, `_unit`, `_integration`
- Temporal: `_old`, `_new`, `_final`, `_v2`, `_draft`
- Variant metadata: `_mock`, `_with_db`

**Action Required:**
- [ ] Identify all non-canonical files
- [ ] Plan consolidation strategy
- [ ] Execute consolidation in Phase 4

**Resolution:** Consolidation in Phase 4

---

### Issue #4: mcpdev Deployment Availability
**Category:** Infrastructure Risk  
**Severity:** Medium (has fallback)  
**Risk:** mcpdev.atoms.tech could become unavailable during testing

**Mitigation:**
1. Can fallback to local HTTP server (`http://localhost:8000`)
2. Can use mock/unit tests only (but less realistic)
3. Can disable rate limiting for test runs if needed

**Workaround:**
```bash
# If mcpdev down, test locally
export MCP_E2E_BASE_URL=http://127.0.0.1:8000
python cli.py test run --scope integration
```

**Status:** Preventative measure, monitoring

---

### Issue #5: Rate Limiting Blocking Tests
**Category:** Infrastructure Risk  
**Severity:** Low (not observed yet)  
**Risk:** Rate limiting could block test requests if too aggressive

**Observation:** Tests sustained 50+ req/s without blocking  
**Threshold:** Unknown - monitor during Phase 2+

**Mitigation:**
1. Use dedicated test API key (if available)
2. Space out requests with backoff
3. Reduce concurrent test parallelism

**Status:** Monitor during execution, adjust if needed

---

### Issue #6: Test User Data Conflicts
**Category:** Test Data Management  
**Severity:** Low (with proper isolation)  
**Risk:** Test user's real data could conflict with test data

**Details:**
- Test user: kooshapari@kooshapari.com
- Already has organizations, projects, documents
- Tests will create thousands of new entities

**Mitigation:**
1. Use unique identifiers (UUIDs in test data)
2. Use test org isolation (no cross-test pollution)
3. Cleanup via soft delete + periodic hard delete

**Best Practice:**
```python
@pytest_asyncio.fixture
async def isolated_org(mcp_client):
    """Each test gets unique org."""
    result = await mcp_client.entity_tool(
        entity_type="organization",
        operation="create",
        data={"name": f"Test {uuid.uuid4().hex[:8]}"}
    )
    yield result["data"]["id"]
    # Cleanup
    await mcp_client.entity_tool(
        entity_type="organization",
        entity_id=result["data"]["id"],
        operation="delete"
    )
```

**Status:** Preventative measures in place

---

## Implementation-Phase Issues (Discovered During Testing)

*Will be filled in as tests are implemented*

### Issue Template
```
### Issue #[N]: [Title]
**Category:** [Performance/Flakiness/Test Logic/Infrastructure]
**Severity:** [Critical/High/Medium/Low]
**Location:** [File/Test path]

**Description:** [What's broken]

**Root Cause:** [Why it's happening]

**Workaround:** [How to work around it]

**Resolution:** [How to fix it]

**Status:** [Open/In Progress/Resolved/Deferred]
```

---

## Technical Debt & Future Work

### Debt #1: Auth Fixtures Could Be More Generic
**Priority:** Low  
**Effort:** 2h  
**Details:**
- Currently hardcoded to Supabase seed user
- Should support parametrized auth providers (AuthKit, etc.)
- Would improve test flexibility

**Resolution:** Refactor auth fixtures in future phase

---

### Debt #2: Mock Client Could Be More Complete
**Priority:** Low  
**Effort:** 4h  
**Details:**
- Current InMemoryMcpClient has limited validation
- Could improve to match real server validation
- Would catch more bugs in unit tests

**Resolution:** Enhance mock client after Phase 2

---

### Debt #3: Test Data Cleanup Could Be Automated
**Priority:** Medium  
**Effort:** 3h  
**Details:**
- Currently manual in fixtures
- Could create automated cleanup service
- Would reduce fixture complexity

**Resolution:** Implement cleanup service in Phase 5

---

### Debt #4: Performance Baselines Not Tracked
**Priority:** Low  
**Effort:** 2h  
**Details:**
- Tests run but no baseline comparison
- Could implement baseline tracking
- Would catch perf regressions early

**Resolution:** Add performance baseline tracking in Phase 4

---

## Assumptions That Need Verification

### Assumption 1: mcpdev Stable & Available
**Status:** ✅ Verified  
**Evidence:** E2E tests passing, 94/115 passing

---

### Assumption 2: Supabase JWT Works with Test User
**Status:** ⏳ To verify  
**Test:** Run e2e_auth_token fixture and attempt call_tool
**Expected:** JWT valid and authenticated calls succeed

---

### Assumption 3: Rate Limiting Not Blocking Tests
**Status:** ⏳ To verify  
**Test:** Run 1000+ requests during Phase 2 tests
**Expected:** No 429 (Too Many Requests) errors

---

### Assumption 4: Parametrized Fixtures Scale Well
**Status:** ⏳ To verify  
**Test:** Run single test with 3 variants, measure execution time
**Expected:** <2s total for all 3 variants

---

## Remediation Plan

### For Critical Issues (if discovered)
1. **Immediate:** Document in this file
2. **Analysis:** Debug and root cause analysis
3. **Workaround:** Implement temporary workaround
4. **Resolution:** Fix in code or tests
5. **Prevention:** Add safeguards to prevent recurrence

### For High Issues
- Same as critical, but can defer to next session if Phase deadline at risk

### For Medium Issues
- Document, plan for Phase 4 consolidation
- Don't block Phase 2 progression

### For Low Issues
- Track for future improvements
- Defer to post-Phase 5 work

---

## Session Learnings & Insights

*Will be updated throughout session with key findings*

### Learning #1: [TBD]
**When Discovered:** [Phase/Step]  
**Impact:** [High/Medium/Low]  
**Key Takeaway:** [What we learned]

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation | Status |
|------|-----------|--------|-----------|--------|
| mcpdev unavailable | Medium | High | Local fallback server | 🟡 Monitoring |
| Rate limit blocking | Medium | Medium | Use test API key | 🟡 Monitoring |
| Test data conflicts | High | Low | Unique test data | 🟢 Mitigated |
| Fixture complexity | Medium | Medium | Keep simple, expand gradually | 🟢 Design in place |
| Parametrization overhead | Low | Low | Benchmark single test | ⏳ To verify |
| RLS enforcement gaps | Low | High | Comprehensive RLS tests | 🟢 Planned |
| Network flakiness | Medium | Medium | Retry logic, timeout tuning | 🟡 Monitoring |
| Coverage gaps | Low | High | Track coverage continuously | 🟢 Planned |

---

## Issue Resolution Timeline

### Phase 2 (If Discovered)
- High priority items: Fix immediately
- Medium priority items: Note for Phase 4
- Low priority items: Add to "future work"

### Phase 4 (Consolidation)
- Review all Phase 2-3 issues
- Fix high/medium priority items
- Defer low priority to post-session

### Post-Session
- Low priority items tracked in repo
- Regular maintenance updates

---

**Last Updated:** 2025-11-14 (Session Start)  
**To Update:** As issues discovered during Phase 2+
