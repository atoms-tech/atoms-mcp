# Refactoring Implementation Guide - Leverage Libraries & Consolidate

## Phase 1: Consolidate Caching (1 day)

### Step 1.1: Create Caching Submodule
```bash
mkdir -p services/caching
touch services/caching/__init__.py
touch services/caching/upstash_wrapper.py
touch services/caching/embedding_cache.py
```

### Step 1.2: Wrap Upstash Libraries
```python
# services/caching/upstash_wrapper.py
from upstash_redis import Redis
from upstash_ratelimit import Ratelimit

class UpstashCache:
    """Thin wrapper around Upstash Redis."""
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
    
    async def get_or_fetch(self, key, fetch_fn, ttl=3600):
        """Get from cache or fetch and cache."""
        cached = await self.redis.get(key)
        if cached:
            return cached
        result = await fetch_fn()
        await self.redis.setex(key, ttl, result)
        return result
```

### Step 1.3: Migrate Embedding Cache
```python
# services/caching/embedding_cache.py
from .upstash_wrapper import UpstashCache

class EmbeddingCache(UpstashCache):
    """Embedding-specific caching logic."""
    CACHE_PREFIX = "embed"
    DEFAULT_TTL = 86400
    
    async def get_embedding(self, text_hash):
        return await self.get_or_fetch(
            f"{self.CACHE_PREFIX}:{text_hash}",
            lambda: self._generate_embedding(text_hash),
            self.DEFAULT_TTL
        )
```

### Step 1.4: Update Imports
```bash
# Find all imports of embedding_cache
grep -r "from services.embedding_cache" --include="*.py"
grep -r "from infrastructure.distributed_rate_limiter" --include="*.py"

# Update to new paths
# from services.embedding_cache import EmbeddingCache
# → from services.caching import EmbeddingCache
```

---

## Phase 2: Consolidate Validation (1 day)

### Step 2.1: Migrate to Pydantic
```python
# schemas/validators.py
from pydantic import BaseModel, Field, EmailStr, validator

class EntityInput(BaseModel):
    name: str = Field(..., min_length=1, max_length=1000)
    email: EmailStr
    description: str = Field(..., max_length=5000)
    
    @validator('name')
    def validate_name(cls, v):
        # Domain-specific validation only
        if v.startswith('_'):
            raise ValueError('Name cannot start with underscore')
        return v
```

### Step 2.2: Delete Custom InputValidator
```bash
# After migrating all validation to Pydantic:
rm infrastructure/input_validator.py

# Find all imports
grep -r "from infrastructure.input_validator" --include="*.py"

# Update to use Pydantic validators
```

### Step 2.3: Update All Callers
```bash
# Find all uses of InputValidator
grep -r "InputValidator\." --include="*.py"

# Replace with Pydantic validation
# InputValidator.validate_string(value)
# → EntityInput(name=value).name
```

---

## Phase 3: Consolidate Error Handling (0.5 days)

### Step 3.1: Create Error Module
```bash
mkdir -p services/errors
touch services/errors/__init__.py
touch services/errors/exceptions.py
touch services/errors/formatters.py
```

### Step 3.2: Domain-Specific Exceptions
```python
# services/errors/exceptions.py
class EntityNotFound(Exception):
    """Entity not found in database."""
    pass

class InvalidOperation(Exception):
    """Invalid operation for entity type."""
    pass

class PermissionDenied(Exception):
    """User lacks permission for operation."""
    pass
```

### Step 3.3: Use FastMCP Error Handling
```python
# services/errors/formatters.py
from fastmcp import ErrorResponse

def format_error(error: Exception) -> dict:
    """Format error for FastMCP response."""
    if isinstance(error, EntityNotFound):
        return {
            "success": False,
            "error": str(error),
            "error_code": 404
        }
    # ... more error types
```

### Step 3.4: Delete Custom ErrorHandler
```bash
# After migrating to FastMCP error handling:
rm services/error_handler.py

# Find all imports
grep -r "from services.error_handler" --include="*.py"

# Update to use FastMCP error handling
```

---

## Phase 4: Consolidate Adapters (1.5 days)

### Step 4.1: Merge Advanced Features
```python
# infrastructure/supabase_db.py - ADD these methods
class SupabaseDatabaseAdapter(DatabaseAdapter):
    # ... existing methods ...
    
    # From advanced_features_adapter
    async def search_full_text(self, table, query, limit=10):
        """Full-text search."""
        # Implementation
    
    async def export_data(self, table, format="json"):
        """Export data."""
        # Implementation
    
    async def import_data(self, table, data, format="json"):
        """Import data."""
        # Implementation
```

### Step 4.2: Decompose Mock Adapters
```bash
mkdir -p infrastructure/mocks
touch infrastructure/mocks/__init__.py
touch infrastructure/mocks/database.py
touch infrastructure/mocks/storage.py
touch infrastructure/mocks/auth.py
touch infrastructure/mocks/realtime.py
touch infrastructure/mocks/client.py
```

### Step 4.3: Move Mock Classes
```bash
# Split infrastructure/mock_adapters.py into:
# - infrastructure/mocks/database.py (InMemoryDatabaseAdapter)
# - infrastructure/mocks/storage.py (InMemoryStorageAdapter)
# - infrastructure/mocks/auth.py (InMemoryAuthAdapter)
# - infrastructure/mocks/realtime.py (InMemoryRealtimeAdapter)
# - infrastructure/mocks/client.py (HttpMcpClient)
```

### Step 4.4: Update Imports
```bash
# Find all imports of mock_adapters
grep -r "from infrastructure.mock_adapters" --include="*.py"

# Update to new paths
# from infrastructure.mock_adapters import InMemoryDatabaseAdapter
# → from infrastructure.mocks import InMemoryDatabaseAdapter
```

---

## Phase 5: Consolidate Tools (2 days)

### Step 5.1: Integrate Compliance into entity_operation
```python
# tools/entity.py - ADD these operations
async def entity_operation(operation: str, **kwargs):
    # ... existing operations ...
    
    if operation == "verify_compliance":
        return await _verify_compliance(**kwargs)
    elif operation == "get_safety_critical":
        return await _get_safety_critical(**kwargs)
```

### Step 5.2: Delete Standalone Tools
```bash
rm tools/compliance_verification.py
rm tools/duplicate_detection.py
rm tools/entity_resolver.py
rm tools/admin.py
rm tools/context.py
```

### Step 5.3: Update server.py
```python
# server.py - Remove standalone tool registrations
# Keep only 5 main tools:
# - workspace_operation
# - entity_operation
# - relationship_operation
# - workflow_execute
# - data_query
```

---

## Phase 6: Consolidate Auth (1 day)

### Step 6.1: Create Auth Module
```bash
mkdir -p auth
touch auth/__init__.py
touch auth/providers.py
touch auth/verifiers.py
touch auth/session.py
```

### Step 6.2: Merge Auth Implementations
```python
# auth/providers.py
from infrastructure.auth_composite import CompositeAuthProvider
# Consolidate all auth logic here
```

### Step 6.3: Use Python's Deprecation Warnings
```python
# auth/deprecation.py
import warnings
import functools

def deprecated(message):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            warnings.warn(message, DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)
        return wrapper
    return decorator
```

### Step 6.4: Delete Duplicate Auth Files
```bash
rm services/deprecation_manager.py
rm services/auth/hybrid_auth_provider.py (if merged)
```

---

## Phase 7: Consolidate Schemas (0.5 days)

### Step 7.1: Use Generated Schemas
```python
# schemas/__init__.py
# Import from generated/ as canonical source
from .generated import *

# Delete schemas/manual/ (legacy)
```

### Step 7.2: Delete Manual Schemas
```bash
rm -rf schemas/manual/
```

### Step 7.3: Update Imports
```bash
# Find all imports of manual schemas
grep -r "from schemas.manual" --include="*.py"

# Update to use generated schemas
# from schemas.manual import Organization
# → from schemas import Organization
```

---

## ✅ VERIFICATION CHECKLIST

- [ ] All tests pass (`pytest tests/ -v`)
- [ ] No import errors
- [ ] No circular dependencies
- [ ] All files ≤350 lines (target)
- [ ] All files ≤500 lines (hard limit)
- [ ] No duplicate code
- [ ] Libraries properly leveraged
- [ ] Git history clean

---

## 🔄 Rollback Plan

```bash
# If issues arise:
git reset --hard HEAD~1

# Or cherry-pick specific commits:
git revert <commit-hash>
```

