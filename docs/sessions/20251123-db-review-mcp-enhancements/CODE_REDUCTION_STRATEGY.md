# Code Reduction Strategy - 50-60% Consolidation

## 🎯 CONSOLIDATION TARGETS

### 1. MOCK ADAPTERS (1000+ lines → 200 lines)

**Current**: Single monolithic file with 5 adapters

**Target**: Submodule with focused files

```
infrastructure/mocks/
├── __init__.py (exports public API)
├── database.py (InMemoryDatabaseAdapter - 150 lines)
├── storage.py (InMemoryStorageAdapter - 100 lines)
├── auth.py (InMemoryAuthAdapter - 80 lines)
├── realtime.py (InMemoryRealtimeAdapter - 80 lines)
└── client.py (HttpMcpClient - 100 lines)
```

**Reduction**: 1000+ → 510 lines (50% reduction)

**Effort**: 1 day

---

### 2. VALIDATION LOGIC (200+ lines → 50 lines)

**Current**: 
- `infrastructure/input_validator.py` (custom)
- `tools/entity_modules/validators.py` (custom)
- Scattered validation in services

**Target**: Single Pydantic-based validation

```python
# schemas/validators.py - NEW
from pydantic import BaseModel, Field, validator

class EntityInput(BaseModel):
    name: str = Field(..., min_length=1, max_length=1000)
    description: str = Field(..., max_length=5000)
    
    @validator('name')
    def validate_name(cls, v):
        if v.startswith('_'):
            raise ValueError('Invalid name')
        return v
```

**Reduction**: 200+ → 50 lines (75% reduction)

**Effort**: 1 day

---

### 3. SCHEMAS (Multiple sources → Single source)

**Current**:
- `schemas/generated/` (auto-generated)
- `schemas/manual/` (legacy)
- `tools/entity_modules/schemas.py` (entity-specific)

**Target**: Single canonical source

```python
# schemas/__init__.py
from .generated import *  # Canonical source
from .validators import *  # Validation logic
```

**Reduction**: 3 sources → 1 source

**Effort**: 0.5 days

---

### 4. TOOLS (5 standalone → Integrated)

**Current**:
- `tools/compliance_verification.py` (standalone)
- `tools/duplicate_detection.py` (standalone)
- `tools/entity_resolver.py` (standalone)
- `tools/admin.py` (standalone)
- `tools/context.py` (standalone)

**Target**: Integrate into 5 main tools

```python
# tools/entity.py - ENHANCED
async def entity_operation(operation: str, **kwargs):
    if operation == "verify_compliance":
        return await _verify_compliance(**kwargs)
    elif operation == "detect_duplicates":
        return await _detect_duplicates(**kwargs)
    elif operation == "resolve_entity":
        return await _resolve_entity(**kwargs)
    # ... more operations
```

**Reduction**: 5 files → 0 files (consolidate into main tools)

**Effort**: 3 days

---

### 5. SERVICES (Multiple implementations → Unified)

**Current**:
- `services/auth/hybrid_auth_provider.py`
- `services/auth/workos_token_verifier.py`
- `services/auth/token_cache.py`
- `services/search/` (multiple search implementations)
- `services/embedding_cache.py` (custom caching)

**Target**: Unified service layer

```
services/
├── auth/
│  ├── __init__.py (exports public API)
│  ├── providers.py (unified auth)
│  ├── verifiers.py (token verification)
│  └── cache.py (token caching)
├── search/
│  ├── __init__.py (exports public API)
│  ├── semantic.py (semantic search)
│  ├── keyword.py (keyword search)
│  └── hybrid.py (combined search)
└── cache/
   ├── __init__.py (exports public API)
   ├── embedding.py (embedding cache)
   └── query.py (query result cache)
```

**Reduction**: 15+ files → 10 files (30% reduction)

**Effort**: 2 days

---

### 6. ADAPTERS (Multiple → Consolidated)

**Current**:
- `infrastructure/supabase_db.py`
- `infrastructure/advanced_features_adapter.py`
- `infrastructure/supabase_storage.py`
- `infrastructure/supabase_realtime.py`

**Target**: Consolidated adapters

```
infrastructure/
├── adapters.py (abstract interfaces)
├── supabase/
│  ├── __init__.py (exports public API)
│  ├── database.py (SupabaseDatabaseAdapter)
│  ├── storage.py (SupabaseStorageAdapter)
│  └── realtime.py (SupabaseRealtimeAdapter)
└── mocks/
   ├── __init__.py (exports public API)
   ├── database.py (InMemoryDatabaseAdapter)
   ├── storage.py (InMemoryStorageAdapter)
   └── realtime.py (InMemoryRealtimeAdapter)
```

**Reduction**: 8+ files → 6 files (25% reduction)

**Effort**: 2 days

---

### 7. TESTS (84 files → 25-30 files)

**Current**: 84 test files with duplication

**Target**: Consolidated test files with parametrization

```
tests/
├── unit/
│  ├── test_entity.py (all entity tests)
│  ├── test_relationship.py (all relationship tests)
│  ├── test_workspace.py (all workspace tests)
│  ├── test_auth.py (all auth tests)
│  └── test_search.py (all search tests)
├── integration/
│  ├── test_entity_integration.py
│  ├── test_relationship_integration.py
│  └── test_search_integration.py
└── e2e/
   ├── test_workflows.py
   └── test_scenarios.py
```

**Reduction**: 84 files → 25-30 files (65% reduction)

**Effort**: 2 days

---

## 📊 TOTAL CODE REDUCTION

| Component | Before | After | Reduction |
|-----------|--------|-------|-----------|
| Mock adapters | 1000+ | 510 | 50% |
| Validation | 200+ | 50 | 75% |
| Schemas | 3 sources | 1 | 66% |
| Tools | 5 standalone | 0 | 100% |
| Services | 15+ files | 10 | 30% |
| Adapters | 8+ files | 6 | 25% |
| Tests | 84 files | 25-30 | 65% |
| **TOTAL** | **150+ files** | **90-100 files** | **40-50%** |

---

## 🎯 IMPLEMENTATION ORDER

1. **Mock adapters** (1 day) - Immediate 50% reduction
2. **Validation** (1 day) - Immediate 75% reduction
3. **Schemas** (0.5 days) - Immediate 66% reduction
4. **Tools** (3 days) - Consolidate standalone tools
5. **Services** (2 days) - Unify service layer
6. **Adapters** (2 days) - Consolidate infrastructure
7. **Tests** (2 days) - Consolidate test files

**TOTAL: 11.5 days (92 hours)**

---

## 💡 QUICK WINS (4 DAYS)

1. Mock adapters (1 day) - 50% reduction
2. Validation (1 day) - 75% reduction
3. Schemas (0.5 days) - 66% reduction
4. Tests (1.5 days) - 65% reduction

**TOTAL: 4 days for 40% code reduction**

---

## ✅ VERIFICATION CHECKLIST

- [ ] All tests passing
- [ ] No import errors
- [ ] No circular dependencies
- [ ] All files ≤350 lines (target)
- [ ] All files ≤500 lines (hard limit)
- [ ] No duplicate code
- [ ] Public APIs exported correctly
- [ ] Documentation updated

