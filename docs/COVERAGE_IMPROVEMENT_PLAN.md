# Coverage Improvement Plan: 58% → 85%-95%

**Current Status:** 58% coverage (5986 statements, 2510 missed)  
**Target:** 85%-95% coverage  
**Estimated Effort:** 20-30 hours  
**Priority:** High

---

## Coverage Analysis by Category

### 🔴 CRITICAL: Zero Coverage (0%) - 8 modules
**Effort: 15-20 hours | Impact: High**

1. **infrastructure/redis_health.py** (42 statements)
   - Health checks for Redis
   - Tests needed: connection, status, metrics

2. **infrastructure/redis_monitoring.py** (76 statements)
   - Redis monitoring and metrics
   - Tests needed: metrics collection, reporting

3. **services/embedding_vertex.py** (195 statements)
   - Vertex AI embeddings
   - Tests needed: API calls, error handling

4. **tools/compliance_verification.py** (37 statements)
   - Compliance checks
   - Tests needed: validation logic

5. **tools/duplicate_detection.py** (52 statements)
   - Duplicate detection
   - Tests needed: detection algorithms

6. **infrastructure/mcp_client_adapter.py** (26 statements)
   - MCP client adapter
   - Tests needed: client operations

7. **services/workos_token_verifier.py** (57 statements)
   - WorkOS token verification
   - Tests needed: token validation

8. **infrastructure/health.py** (97 statements, 37% coverage)
   - Health checks
   - Tests needed: health endpoints

### 🟠 CRITICAL: Very Low Coverage (<25%) - 5 modules
**Effort: 10-15 hours | Impact: High**

1. **tools/workflow.py** (6% - 326/6 statements)
   - Workflow execution
   - Tests needed: workflow operations, state management

2. **tools/workspace.py** (9% - 169/15 statements)
   - Workspace operations
   - Tests needed: context management, navigation

3. **infrastructure/workflow_adapter.py** (23% - 94/72 statements)
   - Workflow adapter
   - Tests needed: adapter operations

4. **infrastructure/advanced_features_adapter.py** (25% - 143/107 statements)
   - Advanced features
   - Tests needed: feature operations

5. **infrastructure/user_mapper.py** (53% - 97/46 statements)
   - User mapping
   - Tests needed: mapping logic

### 🟡 HIGH: Low Coverage (25-50%) - 8 modules
**Effort: 8-12 hours | Impact: Medium**

1. **tools/entity.py** (53% - 792/376 statements)
   - Entity CRUD operations
   - Tests needed: edge cases, error handling

2. **tools/query.py** (55% - 310/138 statements)
   - Query operations
   - Tests needed: complex queries, filters

3. **services/auth/hybrid_auth_provider.py** (48% - 208/108 statements)
   - Auth provider
   - Tests needed: auth flows, token handling

4. **infrastructure/supabase_db.py** (74% - 246/63 statements)
   - Database adapter
   - Tests needed: edge cases

5. **services/enhanced_vector_search.py** (46% - 81/44 statements)
   - Vector search
   - Tests needed: search operations

6. **infrastructure/distributed_rate_limiter.py** (69% - 105/33 statements)
   - Rate limiting
   - Tests needed: rate limit enforcement

7. **infrastructure/concurrency_manager.py** (80% - 181/37 statements)
   - Concurrency management
   - Tests needed: edge cases

8. **infrastructure/supabase_realtime.py** (33% - 52/35 statements)
   - Realtime adapter
   - Tests needed: realtime operations

---

## Implementation Strategy

### Phase 1: Zero-Coverage Modules (15-20 hours)
1. Create test files for each zero-coverage module
2. Add basic functionality tests
3. Add error handling tests
4. Target: 70%+ coverage per module

### Phase 2: Very Low-Coverage Modules (10-15 hours)
1. Analyze existing tests
2. Add missing test cases
3. Add edge case tests
4. Target: 80%+ coverage per module

### Phase 3: Low-Coverage Modules (8-12 hours)
1. Review existing tests
2. Add missing scenarios
3. Add error handling tests
4. Target: 85%+ coverage per module

### Phase 4: Verification (2-3 hours)
1. Run full coverage analysis
2. Verify target reached
3. Document results

---

## Coverage Targets by Module

| Module | Current | Target | Effort |
|--------|---------|--------|--------|
| redis_health.py | 0% | 80% | 2h |
| redis_monitoring.py | 0% | 80% | 2h |
| embedding_vertex.py | 0% | 70% | 3h |
| workflow.py | 6% | 85% | 4h |
| workspace.py | 9% | 85% | 4h |
| entity.py | 53% | 85% | 3h |
| query.py | 55% | 85% | 3h |
| **TOTAL** | **58%** | **85%** | **24h** |

---

## Success Criteria

✅ Overall coverage ≥85%  
✅ No module <70% coverage  
✅ All critical paths tested  
✅ All error cases tested  
✅ All edge cases tested  

---

## Timeline

- **Week 1:** Phase 1 (Zero-coverage modules)
- **Week 2:** Phase 2 (Very low-coverage modules)
- **Week 3:** Phase 3 (Low-coverage modules)
- **Week 4:** Phase 4 (Verification & polish)

**Total: 4 weeks, 24-30 hours**

