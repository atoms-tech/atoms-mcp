# Consolidation Implementation Guide - Step-by-Step

## Phase 1: Test Consolidation (1 day)

### Step 1.1: Delete Non-Canonical Test File
```bash
# Remove non-canonical test file
rm tests/unit/test_batch_phase24_ultra_comprehensive.py

# Verify deletion
git status
```

### Step 1.2: Merge Auth Integration Tests
```bash
# Current state:
# - tests/integration/test_auth_integration.py (skipped)
# - tests/e2e/test_auth_integration.py (canonical)

# Action: Delete integration version, keep e2e version
rm tests/integration/test_auth_integration.py

# Verify e2e version has all tests
pytest tests/e2e/test_auth_integration.py -v
```

### Step 1.3: Merge Database Operation Tests
```bash
# Current state:
# - tests/integration/test_database_operations.py (skipped)
# - tests/unit/infrastructure/test_database.py (canonical)

# Action: Delete integration version, consolidate into unit
rm tests/integration/test_database_operations.py

# Verify unit version has all tests
pytest tests/unit/infrastructure/test_database.py -v
```

### Step 1.4: Consolidate Documentation
```bash
# Archive old governance docs to session folder
mv TEST_GOVERNANCE.md docs/sessions/20251123-db-review-mcp-enhancements/
mv tests/REFACTORING_COMPLETE.md docs/sessions/20251123-db-review-mcp-enhancements/
mv tests/conftest_canonical.md docs/sessions/20251123-db-review-mcp-enhancements/

# Keep docs/TESTING.md as canonical
# Update it to reference archived docs if needed
```

### Step 1.5: Verify Tests Pass
```bash
# Run all tests
pytest tests/ -v

# Run by category
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/e2e/ -v
```

---

## Phase 2: Service Decomposition (1.5 days)

### Step 2.1: Check Service Line Counts
```bash
# Check current line counts
wc -l services/embedding_vertex.py
wc -l services/vector_search.py
wc -l services/enhanced_vector_search.py
wc -l services/progressive_embedding.py
```

### Step 2.2: Decompose if Needed
**If embedding_vertex.py > 350 lines**:
```bash
# Create submodule
mkdir -p services/embedding
touch services/embedding/__init__.py

# Move and split
mv services/embedding_vertex.py services/embedding/vertex.py
# Create cache.py, factory.py, etc. as needed

# Update __init__.py to export public API
cat > services/embedding/__init__.py << 'EOF'
from .vertex import VertexAIEmbeddingService
from .cache import EmbeddingCache
from .factory import get_embedding_service

__all__ = [
    "VertexAIEmbeddingService",
    "EmbeddingCache",
    "get_embedding_service"
]
EOF
```

### Step 2.3: Update All Imports
```bash
# Find all imports of embedding_vertex
grep -r "from services.embedding_vertex" --include="*.py"
grep -r "from services import.*embedding" --include="*.py"

# Update to new path
# from services.embedding_vertex import X
# → from services.embedding import X
```

### Step 2.4: Verify Tests Pass
```bash
pytest tests/unit/services/ -v
pytest tests/integration/ -v
```

---

## Phase 3: Infrastructure Consolidation (1 day)

### Step 3.1: Check advanced_features_adapter Line Count
```bash
wc -l infrastructure/advanced_features_adapter.py
```

### Step 3.2: Decision Tree
**If < 200 lines**: Keep separate (good separation)  
**If 200-350 lines**: Consider consolidation  
**If > 350 lines**: Must consolidate  

### Step 3.3: If Consolidating
```bash
# Option 1: Merge into supabase_db.py
# Add advanced features methods to SupabaseDatabaseAdapter class

# Option 2: Create submodule
mkdir -p infrastructure/supabase
mv infrastructure/supabase_db.py infrastructure/supabase/db.py
mv infrastructure/supabase_storage.py infrastructure/supabase/storage.py
mv infrastructure/supabase_realtime.py infrastructure/supabase/realtime.py
mv infrastructure/advanced_features_adapter.py infrastructure/supabase/advanced.py

# Update __init__.py
cat > infrastructure/supabase/__init__.py << 'EOF'
from .db import SupabaseDatabaseAdapter
from .storage import SupabaseStorageAdapter
from .realtime import SupabaseRealtimeAdapter
from .advanced import AdvancedFeaturesAdapter

__all__ = [
    "SupabaseDatabaseAdapter",
    "SupabaseStorageAdapter",
    "SupabaseRealtimeAdapter",
    "AdvancedFeaturesAdapter"
]
EOF
```

### Step 3.4: Update All Imports
```bash
# Find all imports
grep -r "from infrastructure.supabase_db" --include="*.py"
grep -r "from infrastructure.advanced_features" --include="*.py"

# Update to new paths
```

---

## Phase 4: Tool Consolidation (2 days)

### Step 4.1: Integrate Compliance Verification
```python
# In tools/entity.py, add to entity_operation:

async def entity_operation(operation: str, **kwargs):
    # ... existing operations ...
    
    # NEW: Compliance operations
    if operation == "verify_compliance":
        return await _verify_compliance(**kwargs)
    elif operation == "get_safety_critical":
        return await _get_safety_critical(**kwargs)
    # ... more compliance ops ...
```

### Step 4.2: Integrate Duplicate Detection
```python
# In tools/entity.py, add:

async def entity_operation(operation: str, **kwargs):
    # ... existing operations ...
    
    # NEW: Duplicate detection operations
    if operation == "detect_duplicates":
        return await _detect_duplicates(**kwargs)
    elif operation == "merge_duplicates":
        return await _merge_duplicates(**kwargs)
    # ... more duplicate ops ...
```

### Step 4.3: Integrate Entity Resolution
```python
# In tools/relationship.py, add:

async def relationship_operation(operation: str, **kwargs):
    # ... existing operations ...
    
    # NEW: Entity resolution operations
    if operation == "resolve_entity":
        return await _resolve_entity(**kwargs)
    elif operation == "link_entities":
        return await _link_entities(**kwargs)
    # ... more resolution ops ...
```

### Step 4.4: Integrate Admin & Context
```python
# In tools/workspace.py, add:

async def workspace_operation(operation: str, **kwargs):
    # ... existing operations ...
    
    # NEW: Admin operations
    if operation == "get_admin_stats":
        return await _get_admin_stats(**kwargs)
    # ... more admin ops ...
    
    # NEW: Context operations
    if operation == "get_context_hierarchy":
        return await _get_context_hierarchy(**kwargs)
    # ... more context ops ...
```

### Step 4.5: Update server.py Tool Registration
```python
# In server.py, update tool registration:

# Remove standalone tools
# - compliance_verification
# - duplicate_detection
# - entity_resolver
# - admin
# - context

# Keep only 5 main tools:
# - workspace_operation
# - entity_operation
# - relationship_operation
# - workflow_execute
# - data_query
```

### Step 4.6: Delete Standalone Tool Files
```bash
rm tools/compliance_verification.py
rm tools/duplicate_detection.py
rm tools/entity_resolver.py
rm tools/admin.py
rm tools/context.py
```

### Step 4.7: Verify Tests Pass
```bash
pytest tests/unit/tools/ -v
pytest tests/integration/ -v
pytest tests/e2e/ -v
```

---

## Phase 5: Documentation Consolidation (0.5 days)

### Step 5.1: Update docs/TESTING.md
```markdown
# Add sections for:
- Canonical test naming conventions
- Test file organization
- Running tests by category
- Markers and fixtures
- Coverage requirements
```

### Step 5.2: Archive Session Docs
```bash
# Move to session folder
mv TEST_GOVERNANCE.md docs/sessions/20251123-db-review-mcp-enhancements/
mv tests/REFACTORING_COMPLETE.md docs/sessions/20251123-db-review-mcp-enhancements/
mv tests/conftest_canonical.md docs/sessions/20251123-db-review-mcp-enhancements/
```

### Step 5.3: Update README References
```bash
# Update any README references to point to docs/TESTING.md
grep -r "TEST_GOVERNANCE\|REFACTORING_COMPLETE\|conftest_canonical" --include="*.md"
```

---

## ✅ VERIFICATION CHECKLIST

- [ ] All tests pass (`pytest tests/ -v`)
- [ ] No import errors
- [ ] No circular dependencies
- [ ] All files ≤350 lines (target)
- [ ] All files ≤500 lines (hard limit)
- [ ] Canonical naming conventions followed
- [ ] No duplicate test concerns
- [ ] Documentation updated
- [ ] Git history clean (no merge conflicts)

---

## 🔄 Rollback Plan

If issues arise:
```bash
# Revert to previous state
git reset --hard HEAD~1

# Or cherry-pick specific commits
git revert <commit-hash>
```

