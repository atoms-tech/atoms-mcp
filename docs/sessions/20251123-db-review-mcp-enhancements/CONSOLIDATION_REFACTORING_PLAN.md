# Consolidation, Canonicalization & Refactoring Plan - AGENTS.md Governance

## 🎯 COMPREHENSIVE GOVERNANCE AUDIT

**Scope**: Consolidation, canonicalization, deduplication, and refactoring following AGENTS.md mandates

---

## 📊 AUDIT FINDINGS

### ✅ ALREADY COMPLIANT (Excellent!)
- **Test files**: Canonical naming (test_entity_core.py, test_entity_organization.py, etc.)
- **Test structure**: Properly organized (unit/, integration/, e2e/, performance/)
- **Infrastructure**: Clean adapter pattern (supabase_*.py, mock_*.py)
- **Services**: Well-organized (embedding_*.py, vector_search.py)
- **Tools**: Consolidated (5 tools, no proliferation)

### ⚠️ OPPORTUNITIES FOR IMPROVEMENT

#### 1. Test File Consolidation (CRITICAL)
**Issue**: Multiple test files with overlapping concerns
- `tests/unit/test_batch_phase24_ultra_comprehensive.py` - Non-canonical name
- `tests/integration/test_auth_integration.py` - Duplicate concern
- `tests/integration/test_database_operations.py` - Skipped, needs consolidation
- `tests/e2e/test_auth_integration.py` - Consolidates auth tests (GOOD!)

**Action**: Merge overlapping test files into canonical names

#### 2. Service Layer Decomposition (CRITICAL)
**Issue**: Some services approaching 350+ line limit
- `services/embedding_vertex.py` - Check line count
- `services/vector_search.py` - Check line count
- `services/enhanced_vector_search.py` - Wrapper pattern (good)

**Action**: Decompose into submodules if needed

#### 3. Infrastructure Adapter Consolidation (MEDIUM)
**Issue**: Adapter pattern could be more consistent
- `infrastructure/advanced_features_adapter.py` - Separate adapter (consider consolidation)
- `infrastructure/supabase_db.py` - Core adapter (good)
- `infrastructure/supabase_storage.py` - Separate adapter (good)
- `infrastructure/supabase_realtime.py` - Separate adapter (good)

**Action**: Evaluate if advanced_features_adapter should be in supabase_db.py

#### 4. Tool Layer Organization (MEDIUM)
**Issue**: Some tools may have multiple concerns
- `tools/compliance_verification.py` - Standalone tool (consider wrapping into entity_operation)
- `tools/duplicate_detection.py` - Standalone tool (consider wrapping)
- `tools/entity_resolver.py` - Standalone tool (consider wrapping)
- `tools/admin.py` - Standalone tool (consider wrapping)
- `tools/context.py` - Standalone tool (consider wrapping)

**Action**: Consolidate into 5 main tools as per integration plan

#### 5. Documentation Proliferation (MEDIUM)
**Issue**: Multiple documentation files with similar concerns
- `tests/REFACTORING_COMPLETE.md` - Session doc (good)
- `tests/conftest_canonical.md` - Reference doc (good)
- `docs/TESTING.md` - Canonical testing guide (good)
- `TEST_GOVERNANCE.md` - Duplicate concern (consolidate)

**Action**: Consolidate into single canonical TESTING.md

---

## 🔧 REFACTORING ROADMAP

### Phase 1: Test Consolidation (1 day)
**Canonical Test File Naming**:
- ✅ `test_entity_core.py` - Parametrized entity tests
- ✅ `test_entity_organization.py` - Organization-specific
- ✅ `test_entity_project.py` - Project-specific
- ✅ `test_entity_document.py` - Document-specific
- ✅ `test_entity_requirement.py` - Requirement-specific
- ✅ `test_entity_test.py` - Test-specific
- ✅ `test_query.py` - Query operations
- ✅ `test_relationship.py` - Relationship operations
- ✅ `test_workflow.py` - Workflow operations
- ✅ `test_workspace.py` - Workspace operations

**Consolidation Actions**:
1. Delete `tests/unit/test_batch_phase24_ultra_comprehensive.py` (non-canonical)
2. Merge `tests/integration/test_auth_integration.py` → `tests/e2e/test_auth_integration.py`
3. Merge `tests/integration/test_database_operations.py` → `tests/unit/infrastructure/test_database.py`
4. Consolidate `TEST_GOVERNANCE.md` → `docs/TESTING.md`

### Phase 2: Service Layer Decomposition (1.5 days)
**Check line counts and decompose if needed**:
```
services/
  embedding/
    __init__.py (exports public API)
    vertex.py (Vertex AI implementation)
    cache.py (embedding caching)
    factory.py (factory pattern)
  vector_search/
    __init__.py (exports public API)
    search.py (core search logic)
    enhanced.py (enhanced search with prefetch)
    progressive.py (progressive embedding)
```

### Phase 3: Infrastructure Consolidation (1 day)
**Evaluate advanced_features_adapter**:
- If <200 lines: Keep separate (good separation of concerns)
- If >200 lines: Merge into supabase_db.py as submodule

**Action**: Check line count and decide

### Phase 4: Tool Layer Consolidation (2 days)
**Wrap standalone tools into 5 main tools**:
- `compliance_verification.py` → `entity_operation` (compliance ops)
- `duplicate_detection.py` → `entity_operation` (duplicate ops)
- `entity_resolver.py` → `relationship_operation` (resolution ops)
- `admin.py` → `workspace_operation` (admin ops)
- `context.py` → `workspace_operation` (context ops)

**Action**: Integrate into main tools per integration plan

### Phase 5: Documentation Consolidation (0.5 days)
**Consolidate testing documentation**:
1. Keep `docs/TESTING.md` as canonical
2. Delete `TEST_GOVERNANCE.md`
3. Archive `tests/REFACTORING_COMPLETE.md` → `docs/sessions/`
4. Archive `tests/conftest_canonical.md` → `docs/sessions/`

---

## 📋 IMPLEMENTATION CHECKLIST

### Test Consolidation
- [ ] Delete `tests/unit/test_batch_phase24_ultra_comprehensive.py`
- [ ] Merge auth integration tests
- [ ] Merge database operation tests
- [ ] Verify all tests pass
- [ ] Update test documentation

### Service Decomposition
- [ ] Check `services/embedding_vertex.py` line count
- [ ] Check `services/vector_search.py` line count
- [ ] Decompose if >350 lines
- [ ] Update imports in all callers
- [ ] Run tests to verify

### Infrastructure Consolidation
- [ ] Check `infrastructure/advanced_features_adapter.py` line count
- [ ] Decide: keep separate or merge
- [ ] Update imports if merged
- [ ] Run tests to verify

### Tool Consolidation
- [ ] Integrate compliance_verification into entity_operation
- [ ] Integrate duplicate_detection into entity_operation
- [ ] Integrate entity_resolver into relationship_operation
- [ ] Integrate admin into workspace_operation
- [ ] Integrate context into workspace_operation
- [ ] Update server.py tool registration
- [ ] Run tests to verify

### Documentation Consolidation
- [ ] Consolidate TESTING.md
- [ ] Delete TEST_GOVERNANCE.md
- [ ] Archive session docs
- [ ] Update README references

---

## 🎯 EXPECTED OUTCOMES

✅ **Canonical naming** - All files follow AGENTS.md conventions  
✅ **No duplication** - No overlapping test concerns  
✅ **Modular services** - All services ≤350 lines  
✅ **Consolidated tools** - 5 tools, no standalone tools  
✅ **Clean documentation** - Single source of truth  
✅ **100% test pass** - All tests passing after refactoring  
✅ **Zero technical debt** - No legacy code paths  

---

## 📊 EFFORT ESTIMATE

- **Phase 1**: 1 day (test consolidation)
- **Phase 2**: 1.5 days (service decomposition)
- **Phase 3**: 1 day (infrastructure consolidation)
- **Phase 4**: 2 days (tool consolidation)
- **Phase 5**: 0.5 days (documentation consolidation)

**TOTAL: 6 days (48 hours)**

---

## 🔗 INTEGRATION WITH MAIN PLAN

This consolidation work:
- Reduces codebase complexity
- Improves maintainability
- Enables easier testing
- Follows AGENTS.md governance
- Complements performance optimization
- Prepares for Phase 1 implementation

**Combined effort**: 7 days (performance) + 6 days (consolidation) = **13 days (104 hours)**

