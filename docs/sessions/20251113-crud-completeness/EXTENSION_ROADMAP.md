# CRUD Completeness Extension Roadmap

**Date**: 2025-11-13  
**Goal**: Extend coverage from 20% to 100%  
**Timeline**: 5-7 days (full-time equivalent)  
**Priority**: Security first, then consistency, then completeness

---

## 🚀 Quick Start: Top 5 Extensions

### **1. Permission Checks on All Operations** 🔴 CRITICAL

Add authorization validation to every operation:

```python
# In entity_operation (tools/entity.py)

async def _check_permission(user_id, entity_type, entity_id, action):
    """Check if user has permission for action on entity."""
    permissions_adapter = AdvancedFeaturesAdapter(db)
    perms = await permissions_adapter.get_entity_permissions(entity_type, entity_id)
    
    user_perms = [p for p in perms if p['user_id'] == user_id]
    if not user_perms:
        raise PermissionError(f"User {user_id} has no permissions on {entity_type} {entity_id}")
    
    perm_level = user_perms[0]['permission_level']
    required_levels = {
        'read': ['view', 'edit', 'admin'],
        'update': ['edit', 'admin'],
        'delete': ['admin'],
        'admin': ['admin']
    }
    
    if action not in required_levels[perm_level]:
        raise PermissionError(f"User permission '{perm_level}' insufficient for '{action}'")

# Usage in operations:
# await _check_permission(user_id, entity_type, entity_id, 'update')
# result = await entity_manager.update_entity(...)
```

**Test Template**:
```python
# tests/unit/tools/test_entity_permissions.py

class TestPermissionEnforcement:
    async def test_user_cannot_read_without_permission(self, call_mcp):
        """Verify user cannot read entity without permission."""
        result = await call_mcp("entity_tool", {
            "operation": "read",
            "entity_type": "document",
            "entity_id": "doc-123",
            "user_id": "user-without-permission"
        })
        assert result["success"] == False
        assert "permission" in result["error"].lower()
    
    async def test_user_cannot_update_without_edit_permission(self, call_mcp):
        """Verify user cannot update with only view permission."""
        # Setup: grant user 'view' permission
        # Action: try to update
        # Assert: fails with permission error
        pass
    
    async def test_user_cannot_delete_without_admin_permission(self, call_mcp):
        """Verify delete requires admin permission."""
        pass
    
    async def test_bulk_operations_respect_permissions(self, call_mcp):
        """Verify bulk operations check permission for each entity."""
        pass
```

**Effort**: 2-3 days | **Impact**: CRITICAL

---

### **2. Soft-Delete Consistency Across All Entities** ⚠️ HIGH

Ensure soft-deleted items excluded from all operations:

```python
# In base.py _sanitize_filters()

def _apply_soft_delete_filter(filters, entity_type, table_name):
    """Add soft-delete filter to operations on entities that support it."""
    tables_with_soft_delete = {
        'organizations', 'projects', 'documents', 'requirements',
        'workflow_executions', 'export_jobs', 'import_jobs',
        'entity_permissions', 'search_index'
    }
    
    if table_name in tables_with_soft_delete:
        filters = filters or {}
        filters['is_deleted'] = False  # Exclude soft-deleted
    
    return filters

# Usage in list_entities:
# filters = _apply_soft_delete_filter(filters, entity_type, table)
# results = await db.query(table, filters=filters)
```

**Test Template**:
```python
# tests/unit/tools/test_soft_delete_consistency.py

class TestSoftDeleteConsistency:
    @pytest.mark.parametrize("entity_type", [
        "organization", "project", "document", "requirement",
        "property", "block", "column", "trace_link"
    ])
    async def test_list_excludes_soft_deleted(self, call_mcp, entity_type):
        """Verify soft-deleted items excluded from list."""
        # Create entity
        # Soft-delete it
        # List should not return it
        # Assert: item not in results
        pass
    
    @pytest.mark.parametrize("entity_type", [
        "organization", "project", "document", "requirement"
    ])
    async def test_search_excludes_soft_deleted(self, call_mcp, entity_type):
        """Verify search excludes soft-deleted items."""
        pass
    
    async def test_restore_un_deletes_item(self, call_mcp):
        """Verify restore makes soft-deleted item visible again."""
        pass
    
    async def test_restore_cascades_to_relationships(self, call_mcp):
        """Verify restoring entity also restores related items."""
        pass
```

**Effort**: 1-2 days | **Impact**: HIGH

---

### **3. Concurrency & Transaction Testing** 🔴 CRITICAL

Test simultaneous operations and race conditions:

```python
# tests/unit/tools/test_concurrency.py

import asyncio

class TestConcurrency:
    async def test_concurrent_updates_same_entity(self, call_mcp, test_organization):
        """Verify concurrent updates don't corrupt data."""
        entity_id = "req-123"
        
        async def update_field(field_name, value):
            return await call_mcp("entity_tool", {
                "operation": "update",
                "entity_type": "requirement",
                "entity_id": entity_id,
                "data": {field_name: value}
            })
        
        # Launch 5 concurrent updates
        results = await asyncio.gather(
            update_field("status", "draft"),
            update_field("priority", "high"),
            update_field("title", "Title A"),
            update_field("title", "Title B"),  # Last write wins
            update_field("status", "review")
        )
        
        # Verify all succeeded
        assert all(r["success"] for r in results)
        
        # Read final state
        final = await call_mcp("entity_tool", {
            "operation": "read",
            "entity_type": "requirement",
            "entity_id": entity_id
        })
        
        # Verify data consistency
        assert final["data"]["title"] in ["Title A", "Title B"]
        assert final["data"]["status"] in ["draft", "review"]
    
    async def test_bulk_update_partial_failure_consistency(self, call_mcp):
        """Verify bulk update handles some items failing."""
        entity_ids = ["req-1", "req-2", "req-3"]
        
        result = await call_mcp("entity_tool", {
            "operation": "bulk_update",
            "entity_type": "requirement",
            "entity_ids": entity_ids,
            "data": {"status": "verified"}
        })
        
        # Should show which succeeded/failed
        assert "succeeded" in result or "failed" in result
    
    async def test_concurrent_create_no_duplicates(self, call_mcp):
        """Verify concurrent creates don't create duplicates."""
        async def create_with_unique_id():
            return await call_mcp("entity_tool", {
                "operation": "create",
                "entity_type": "requirement",
                "data": {"title": "Concurrent", "external_id": "unique-123"}
            })
        
        results = await asyncio.gather(
            create_with_unique_id(),
            create_with_unique_id(),
            create_with_unique_id()
        )
        
        # Should have exactly 1 successful, 2 failures (duplicate constraint)
        successful = [r for r in results if r.get("success")]
        assert len(successful) == 1, "Only one should succeed with unique constraint"
```

**Effort**: 2-3 days | **Impact**: CRITICAL

---

### **4. Relationship Cascade Testing** ⚠️ HIGH

Validate cascading operations across relationships:

```python
# tests/unit/tools/test_relationship_cascades.py

class TestRelationshipCascades:
    async def test_delete_requirement_cascades_to_tests(self, call_mcp, test_organization):
        """Verify deleting requirement soft-deletes related tests."""
        # Create requirement
        req = await call_mcp("entity_tool", {
            "operation": "create",
            "entity_type": "requirement",
            "data": {"title": "Req with tests"}
        })
        req_id = req["data"]["id"]
        
        # Create related test
        test = await call_mcp("entity_tool", {
            "operation": "create",
            "entity_type": "test",
            "data": {"title": "Test for req"}
        })
        test_id = test["data"]["id"]
        
        # Link them
        await call_mcp("relationship_tool", {
            "operation": "link",
            "source": f"requirement:{req_id}",
            "target": f"test:{test_id}",
            "relationship_type": "verifies"
        })
        
        # Delete requirement
        await call_mcp("entity_tool", {
            "operation": "delete",
            "entity_type": "requirement",
            "entity_id": req_id,
            "soft_delete": True
        })
        
        # Verify relationship deleted
        links = await call_mcp("relationship_tool", {
            "operation": "list",
            "entity_type": "requirement",
            "entity_id": req_id
        })
        assert len(links) == 0, "Links should be deleted"
    
    async def test_archive_requirement_archives_related_items(self, call_mcp):
        """Verify archiving requirement cascades to related tests."""
        pass
    
    async def test_restore_requirement_restores_relationships(self, call_mcp):
        """Verify restoring requirement restores related items."""
        pass
```

**Effort**: 1-2 days | **Impact**: HIGH

---

### **5. Input Validation & Sanitization** 🔴 CRITICAL

Prevent injection attacks and malformed data:

```python
# infrastructure/validation.py (new file)

import re
from typing import Any, Dict

class InputValidator:
    """Validate and sanitize user inputs."""
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"('.*'|\".*\")\s*(;|--|\#|\/\*|\*\/)",
        r"\b(DROP|DELETE|INSERT|UPDATE|UNION|SELECT)\b",
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>",
        r"javascript:",
        r"on\w+\s*=",
    ]
    
    @staticmethod
    def validate_string(value: str, field_name: str, max_length: int = 1000) -> str:
        """Validate and sanitize string fields."""
        if not isinstance(value, str):
            raise ValueError(f"{field_name} must be a string")
        
        if len(value) > max_length:
            raise ValueError(f"{field_name} exceeds max length {max_length}")
        
        if len(value) == 0:
            raise ValueError(f"{field_name} cannot be empty")
        
        # Check for SQL injection
        for pattern in InputValidator.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                raise ValueError(f"{field_name} contains invalid characters")
        
        # Check for XSS
        for pattern in InputValidator.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                raise ValueError(f"{field_name} contains invalid HTML/JS")
        
        # Remove leading/trailing whitespace
        return value.strip()
    
    @staticmethod
    def validate_id(value: str, field_name: str) -> str:
        """Validate ID field (UUID or alphanumeric)."""
        if not isinstance(value, str):
            raise ValueError(f"{field_name} must be a string")
        
        # UUID or slug format
        if not re.match(r'^[a-zA-Z0-9_-]+$', value):
            raise ValueError(f"{field_name} contains invalid characters")
        
        if len(value) < 3 or len(value) > 100:
            raise ValueError(f"{field_name} invalid length")
        
        return value
    
    @staticmethod
    def validate_integer(value: Any, field_name: str, min_val: int = 0, max_val: int = 1000000) -> int:
        """Validate integer fields."""
        try:
            int_val = int(value)
        except (ValueError, TypeError):
            raise ValueError(f"{field_name} must be an integer")
        
        if int_val < min_val or int_val > max_val:
            raise ValueError(f"{field_name} out of range [{min_val}, {max_val}]")
        
        return int_val

# tests/unit/infrastructure/test_input_validation.py

class TestInputValidation:
    def test_sql_injection_prevention(self):
        """Verify SQL injection attempts are caught."""
        payloads = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
        ]
        for payload in payloads:
            with pytest.raises(ValueError):
                InputValidator.validate_string(payload, "name")
    
    def test_xss_prevention(self):
        """Verify XSS attempts are caught."""
        payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img onerror='alert(1)'>",
        ]
        for payload in payloads:
            with pytest.raises(ValueError):
                InputValidator.validate_string(payload, "name")
    
    def test_field_length_validation(self):
        """Verify field length limits enforced."""
        long_string = "x" * 2000
        with pytest.raises(ValueError):
            InputValidator.validate_string(long_string, "name", max_length=1000)
    
    def test_special_characters_allowed(self):
        """Verify allowed special characters work."""
        valid_inputs = [
            "John O'Brien",
            "test-name",
            "test_123",
            "user@example.com",
        ]
        for input_str in valid_inputs:
            result = InputValidator.validate_string(input_str, "name")
            assert result == input_str.strip()
```

**Effort**: 2-3 days | **Impact**: CRITICAL

---

## 📋 Complete Extension Tasks (Priority Order)

### **Week 1: Security & Consistency**

**Day 1-2: Permission Checks** (120 tests)
- [ ] Add permission validation to all operations
- [ ] Test permission enforcement across operations
- [ ] Test workspace isolation
- [ ] Test permission inheritance

**Day 2-3: Soft-Delete Consistency** (75 tests)
- [ ] Audit all operations for soft-delete filtering
- [ ] Add soft-delete check to list, search, export
- [ ] Test restore cascading
- [ ] Validate deletion consistency

**Day 3-4: Concurrency** (50 tests)
- [ ] Test concurrent updates
- [ ] Test race conditions in bulk operations
- [ ] Test transaction isolation
- [ ] Test cascading under concurrency

### **Week 2: Completeness**

**Day 4-5: Entity-Specific Operations** (150 tests)
- [ ] Extended tests for all entities × operations
- [ ] Relationship-aware operations
- [ ] Search on all entity types
- [ ] Export/import for all types

**Day 5-6: Audit & Advanced Features** (65 tests)
- [ ] Audit logging for all mutations
- [ ] Workflow execution tracking
- [ ] Search facet accuracy
- [ ] Import duplicate detection

**Day 6-7: Error Handling & Performance** (50 tests)
- [ ] Database connection failures
- [ ] Timeout scenarios
- [ ] Large dataset handling
- [ ] Performance benchmarks

---

## 📊 Expected Test Growth

```
Current:  86 tests
↓
+ Security & Consistency:  120 + 75 + 50 = 245 tests
= After Week 1: 331 tests

↓
+ Feature Completeness:  150 + 65 + 50 = 265 tests
= After Week 2: 596 tests

Note: Some overlap, realistic total: ~460-480 tests
```

---

## 🎯 Success Criteria

### **Security**
- ✅ All operations enforce permissions
- ✅ All user inputs validated
- ✅ Multi-tenant isolation verified
- ✅ No SQL injection vectors
- ✅ No XSS vectors

### **Consistency**
- ✅ Soft-delete applied everywhere
- ✅ Relationship cascades work
- ✅ Concurrent operations safe
- ✅ Transaction isolation verified
- ✅ No orphaned records

### **Completeness**
- ✅ All entities tested with all operations
- ✅ All error cases handled
- ✅ Audit trails complete
- ✅ Advanced features working
- ✅ Performance benchmarks set

### **Coverage**
- ✅ 450+ total tests
- ✅ 95%+ code coverage
- ✅ 100% operation-entity matrix covered
- ✅ All edge cases tested

---

## 🚀 Implementation Strategy

### **Recommended Approach**

1. **Start with Security** (foundation)
   - Permission checks block bad actors
   - Input validation prevents exploits
   - Multi-tenant isolation is critical

2. **Add Consistency** (reliability)
   - Soft-delete consistency prevents data leaks
   - Concurrency testing prevents corruption
   - Cascading prevents orphaned records

3. **Extend Features** (completeness)
   - Entity-specific tests for breadth
   - Advanced features for depth
   - Error handling for robustness

### **Parallelization Opportunities**

- **Security & Consistency** can be done in parallel (separate concerns)
- **Entity-specific tests** can be auto-generated (parametrized)
- **Error handling** can be added incrementally per operation

---

## 💡 Quick Wins (Start Here)

**Easiest to Implement** (1-2 hours each):
1. Parametrized entity tests for archive/restore
2. Soft-delete filter audit
3. Input validation basics
4. Simple concurrency tests

**High Impact** (2-4 hours):
1. Permission validation
2. Relationship cascade testing
3. Audit logging
4. Batch validation tests

**Comprehensive** (4+ hours):
1. Full concurrency suite
2. Entity-specific extended operations
3. Advanced features testing
4. Performance benchmarking

---

**Recommendation**: Start with the "Top 5 Extensions" and implement in priority order. Security-first approach ensures production safety while building out feature completeness.
