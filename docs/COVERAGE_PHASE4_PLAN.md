# Phase 4 Plan: Reaching 85% Coverage

**Current Status:** 65% coverage (5986 statements, 2104 missed)  
**Target:** 85% coverage (5986 statements, ~898 missed)  
**Gap:** 20% coverage improvement needed  
**Estimated Effort:** 20-30 hours  

---

## 🎯 COVERAGE GAP ANALYSIS

### Current Coverage by Category

**High Coverage (>80%):**
- infrastructure/permission_middleware.py: 90%
- infrastructure/permissions.py: 95%
- infrastructure/mock_oauth_adapters.py: 97%
- infrastructure/supabase_storage.py: 97%
- services/auth/token_cache.py: 92%
- infrastructure/input_validator.py: 89%

**Medium Coverage (50-80%):**
- infrastructure/supabase_db.py: 74%
- infrastructure/concurrency_manager.py: 80%
- infrastructure/distributed_rate_limiter.py: 69%
- infrastructure/upstash_provider.py: 67%
- infrastructure/adapters.py: 71%
- services/vector_search.py: 85%
- services/progressive_embedding.py: 79%
- tools/entity.py: 53%
- tools/query.py: 55%
- tools/relationship.py: 79%
- tools/workspace.py: 60%
- tools/workflow.py: 44%

**Low Coverage (<50%):**
- infrastructure/health.py: 37%
- infrastructure/supabase_realtime.py: 33%
- infrastructure/user_mapper.py: 53%
- infrastructure/workflow_adapter.py: 45%
- infrastructure/advanced_features_adapter.py: 25%
- infrastructure/redis_health.py: 40%
- infrastructure/redis_monitoring.py: 22%
- services/embedding_vertex.py: 40%
- services/enhanced_vector_search.py: 46%
- services/auth/hybrid_auth_provider.py: 48%
- tools/duplicate_detection.py: 42%
- tools/compliance_verification.py: 62%

---

## 📊 PRIORITY MODULES FOR PHASE 4

### Tier 1: High Impact (20-30% improvement potential)
1. **infrastructure/health.py** (37% → 85%+)
   - 97 statements, 61 missed
   - Effort: 3-4 hours
   - Impact: +48%

2. **infrastructure/supabase_realtime.py** (33% → 85%+)
   - 52 statements, 35 missed
   - Effort: 2-3 hours
   - Impact: +52%

3. **infrastructure/advanced_features_adapter.py** (25% → 85%+)
   - 143 statements, 107 missed
   - Effort: 4-5 hours
   - Impact: +60%

4. **infrastructure/redis_monitoring.py** (22% → 85%+)
   - 76 statements, 59 missed
   - Effort: 2-3 hours
   - Impact: +63%

### Tier 2: Medium Impact (10-20% improvement potential)
1. **tools/workflow.py** (44% → 85%+)
   - 326 statements, 181 missed
   - Effort: 5-6 hours
   - Impact: +41%

2. **services/enhanced_vector_search.py** (46% → 85%+)
   - 81 statements, 44 missed
   - Effort: 2-3 hours
   - Impact: +39%

3. **infrastructure/workflow_adapter.py** (45% → 85%+)
   - 94 statements, 52 missed
   - Effort: 3-4 hours
   - Impact: +40%

### Tier 3: Lower Impact (5-10% improvement potential)
1. **tools/entity.py** (53% → 85%+)
   - 792 statements, 376 missed
   - Effort: 6-8 hours
   - Impact: +32%

2. **tools/query.py** (55% → 85%+)
   - 310 statements, 138 missed
   - Effort: 4-5 hours
   - Impact: +30%

---

## 🚀 PHASE 4 IMPLEMENTATION STRATEGY

### Week 1: Tier 1 Modules (12-15 hours)
1. health.py (3-4h)
2. supabase_realtime.py (2-3h)
3. advanced_features_adapter.py (4-5h)
4. redis_monitoring.py (2-3h)

**Target: 70% coverage**

### Week 2: Tier 2 Modules (10-12 hours)
1. workflow.py (5-6h)
2. enhanced_vector_search.py (2-3h)
3. workflow_adapter.py (3-4h)

**Target: 75% coverage**

### Week 3: Tier 3 Modules (10-12 hours)
1. entity.py (6-8h)
2. query.py (4-5h)

**Target: 80% coverage**

### Week 4: Final Push (5-8 hours)
1. Remaining gaps
2. Edge cases
3. Error handling

**Target: 85% coverage**

---

## 📋 SUCCESS CRITERIA

- [ ] Overall coverage ≥85%
- [ ] All Tier 1 modules ≥85%
- [ ] All Tier 2 modules ≥85%
- [ ] All Tier 3 modules ≥85%
- [ ] All tests passing (100% pass rate)
- [ ] No regressions

---

## 📅 TIMELINE

- **Week 1:** Tier 1 modules (12-15 hours) → 70% coverage
- **Week 2:** Tier 2 modules (10-12 hours) → 75% coverage
- **Week 3:** Tier 3 modules (10-12 hours) → 80% coverage
- **Week 4:** Final push (5-8 hours) → 85% coverage

**Total: 4 weeks, 37-47 hours**

---

## 💡 APPROACH

1. **Focus on high-impact modules first** (Tier 1)
2. **Add comprehensive tests** for each module
3. **Test error handling** and edge cases
4. **Test integration points** between modules
5. **Verify no regressions** after each phase
6. **Document findings** in session docs

---

## ✨ CONCLUSION

Phase 4 focuses on reaching 85% coverage through systematic testing of high-impact modules. The 4-week timeline with 37-47 hours of effort should achieve the target.

**Ready to begin Phase 4!**

