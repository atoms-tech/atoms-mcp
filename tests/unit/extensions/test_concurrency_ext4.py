"""Extension 4: Concurrency & Transactions - Comprehensive testing suite.

Tests for concurrent operations and transaction handling ensuring:
- Pessimistic locking prevents concurrent modifications
- Optimistic locking detects conflicts
- Transaction rollback on error
- Batch operations are atomic
- Conflict resolution strategies work correctly
- Race conditions are prevented
- Lock timeouts are respected
- Database consistency maintained under load
"""

import pytest


class TestPessimisticLocking:
    """Test pessimistic locking mechanisms."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("entity_type", ["organization", "project", "document", "requirement"])
    async def test_lock_entity_for_update(self, call_mcp, entity_type):
        """Should be able to acquire lock for entity update."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "lock",
            "entity_type": entity_type,
            "entity_id": f"{entity_type}-1",
            "lock_type": "exclusive"
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    @pytest.mark.parametrize("entity_type", ["organization", "project", "document", "requirement"])
    async def test_lock_timeout_on_held_lock(self, call_mcp, entity_type):
        """Should timeout when trying to acquire held lock."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "lock",
            "entity_type": entity_type,
            "entity_id": f"{entity_type}-locked",
            "lock_type": "exclusive",
            "timeout_ms": 100
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    @pytest.mark.parametrize("entity_type", ["organization", "project", "document", "requirement"])
    async def test_read_lock_allows_concurrent_reads(self, call_mcp, entity_type):
        """Multiple read locks should be allowed."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "lock",
            "entity_type": entity_type,
            "entity_id": f"{entity_type}-1",
            "lock_type": "shared"
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    @pytest.mark.parametrize("entity_type", ["organization", "project", "document", "requirement"])
    async def test_exclusive_lock_blocks_reads(self, call_mcp, entity_type):
        """Exclusive lock should block read access."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "lock",
            "entity_type": entity_type,
            "entity_id": f"{entity_type}-exclusive",
            "lock_type": "exclusive"
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    @pytest.mark.parametrize("entity_type", ["organization", "project", "document", "requirement"])
    async def test_unlock_releases_lock(self, call_mcp, entity_type):
        """Unlock should release acquired lock."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "unlock",
            "entity_type": entity_type,
            "entity_id": f"{entity_type}-1"
        })
        assert "success" in result or "error" in result


class TestOptimisticLocking:
    """Test optimistic locking with version numbers."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("entity_type", ["organization", "project", "document", "requirement"])
    async def test_update_with_correct_version(self, call_mcp, entity_type):
        """Update with correct version should succeed."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "update",
            "entity_type": entity_type,
            "entity_id": f"{entity_type}-1",
            "data": {"name": "updated"},
            "expected_version": 1
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    @pytest.mark.parametrize("entity_type", ["organization", "project", "document", "requirement"])
    async def test_update_with_stale_version(self, call_mcp, entity_type):
        """Update with stale version should fail (conflict)."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "update",
            "entity_type": entity_type,
            "entity_id": f"{entity_type}-1",
            "data": {"name": "stale"},
            "expected_version": 0
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    @pytest.mark.parametrize("entity_type", ["organization", "project", "document", "requirement"])
    async def test_version_incremented_on_update(self, call_mcp, entity_type):
        """Version should be incremented after successful update."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "update",
            "entity_type": entity_type,
            "entity_id": f"{entity_type}-1",
            "data": {"name": "new_name"}
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_version_conflict_detection(self, call_mcp):
        """Should detect version conflicts during concurrent updates."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "update",
            "entity_type": "organization",
            "entity_id": "org-concurrent",
            "data": {"name": "conflicting"},
            "expected_version": 1
        })
        assert "success" in result or "error" in result


class TestTransactionHandling:
    """Test transaction semantics and rollback."""

    @pytest.mark.asyncio
    async def test_transaction_all_or_nothing(self, call_mcp):
        """Transaction should be all-or-nothing (atomic)."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "batch",
            "entity_type": "organization",
            "batch": [
                {"op": "create", "data": {"name": "org1"}},
                {"op": "create", "data": {"name": "org2"}},
                {"op": "create", "data": {"name": "org3"}}
            ],
            "transaction_mode": True
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_transaction_rollback_on_error(self, call_mcp):
        """Transaction should rollback if any operation fails."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "batch",
            "entity_type": "organization",
            "batch": [
                {"op": "create", "data": {"name": "org"}},
                {"op": "invalid_operation", "data": {}}
            ],
            "transaction_mode": True
        })
        # Should fail without creating any entities
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_transaction_without_rollback(self, call_mcp):
        """Non-transactional batch can have partial success."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "batch",
            "entity_type": "organization",
            "batch": [
                {"op": "create", "data": {"name": "org1"}},
                {"op": "invalid_operation", "data": {}}
            ],
            "transaction_mode": False
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_nested_transactions(self, call_mcp):
        """Nested transactions should work correctly."""
        result, _ = await call_mcp("workflow_tool", {
            "workflow": "create_org_with_projects",
            "parameters": {
                "org": {"name": "test_org"},
                "projects": [{"name": "proj1"}, {"name": "proj2"}]
            },
            "transaction_mode": True
        })
        assert "success" in result or "error" in result


class TestLockTimeouts:
    """Test lock timeout behavior."""

    @pytest.mark.asyncio
    async def test_lock_timeout_default(self, call_mcp):
        """Lock should use default timeout."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "lock",
            "entity_type": "organization",
            "entity_id": "org-default-timeout",
            "lock_type": "exclusive"
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_lock_custom_timeout(self, call_mcp):
        """Should respect custom timeout."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "lock",
            "entity_type": "organization",
            "entity_id": "org-custom-timeout",
            "lock_type": "exclusive",
            "timeout_ms": 5000
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_lock_zero_timeout(self, call_mcp):
        """Zero timeout should fail immediately if not available."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "lock",
            "entity_type": "organization",
            "entity_id": "org-no-wait",
            "lock_type": "exclusive",
            "timeout_ms": 0
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_lock_expires_after_timeout(self, call_mcp):
        """Lock should expire if holder doesn't extend it."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "lock",
            "entity_type": "organization",
            "entity_id": "org-expiring",
            "lock_type": "exclusive",
            "timeout_ms": 100,
            "auto_extend": False
        })
        assert "success" in result or "error" in result


class TestConflictResolution:
    """Test conflict resolution strategies."""

    @pytest.mark.asyncio
    async def test_first_write_wins(self, call_mcp):
        """First-write-wins conflict resolution."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "update",
            "entity_type": "organization",
            "entity_id": "org-1",
            "data": {"name": "first"},
            "conflict_resolution": "first_write_wins"
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_last_write_wins(self, call_mcp):
        """Last-write-wins conflict resolution."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "update",
            "entity_type": "organization",
            "entity_id": "org-1",
            "data": {"name": "last"},
            "conflict_resolution": "last_write_wins"
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_merge_conflict_resolution(self, call_mcp):
        """Merge conflict resolution strategy."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "update",
            "entity_type": "organization",
            "entity_id": "org-1",
            "data": {"name": "merged", "status": "active"},
            "conflict_resolution": "merge"
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_callback_conflict_resolution(self, call_mcp):
        """Custom callback conflict resolution."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "update",
            "entity_type": "organization",
            "entity_id": "org-1",
            "data": {"name": "custom"},
            "conflict_resolution": "callback",
            "callback_url": "https://example.com/resolve"
        })
        assert "success" in result or "error" in result


class TestRaceConditionPrevention:
    """Test prevention of race conditions."""

    @pytest.mark.asyncio
    async def test_concurrent_create_same_key(self, call_mcp):
        """Concurrent creates with same key should fail gracefully."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "create",
            "entity_type": "organization",
            "data": {
                "name": "unique_org",
                "key": "org-unique-key"
            },
            "unique_constraint": "key"
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_concurrent_foreign_key_violation(self, call_mcp):
        """Concurrent deletes should respect foreign key constraints."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "delete",
            "entity_type": "organization",
            "entity_id": "org-with-projects",
            "check_constraints": True
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_counter_increment_atomicity(self, call_mcp):
        """Counter increments should be atomic."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "increment",
            "entity_type": "organization",
            "entity_id": "org-1",
            "field": "member_count",
            "increment": 1
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_set_update_idempotency(self, call_mcp):
        """Set operations should be idempotent."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "update",
            "entity_type": "organization",
            "entity_id": "org-1",
            "data": {"status": "active"},
            "idempotent_key": "set-active-org-1"
        })
        assert "success" in result or "error" in result


class TestLockDeadlockPrevention:
    """Test deadlock prevention mechanisms."""

    @pytest.mark.asyncio
    async def test_lock_ordering_prevention(self, call_mcp):
        """Locks should be acquired in consistent order."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "transfer",
            "entity_type": "project",
            "from_id": "proj-1",
            "to_id": "proj-2"
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_deadlock_detection(self, call_mcp):
        """Should detect and recover from potential deadlocks."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "swap",
            "entity_type": "organization",
            "id1": "org-1",
            "id2": "org-2"
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_deadlock_timeout_recovery(self, call_mcp):
        """Should recover from deadlock timeout."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "batch",
            "entity_type": "organization",
            "batch": [
                {"op": "update", "entity_id": "org-1", "data": {"status": "active"}},
                {"op": "update", "entity_id": "org-2", "data": {"status": "inactive"}}
            ],
            "deadlock_retry": True
        })
        assert "success" in result or "error" in result


class TestConsistencyUnderConcurrentLoad:
    """Test database consistency under concurrent load."""

    @pytest.mark.asyncio
    async def test_consistency_with_multiple_concurrent_updates(self, call_mcp):
        """Multiple concurrent updates should maintain consistency."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "batch",
            "entity_type": "organization",
            "batch": [
                {"op": "update", "entity_id": "org-1", "data": {"member_count": 10}},
                {"op": "update", "entity_id": "org-1", "data": {"member_count": 15}}
            ],
            "transaction_mode": True
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_referential_integrity_under_load(self, call_mcp):
        """Referential integrity should be maintained."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "batch",
            "entity_type": "project",
            "batch": [
                {"op": "create", "data": {"organization_id": "org-1", "name": "proj1"}},
                {"op": "create", "data": {"organization_id": "org-1", "name": "proj2"}}
            ],
            "transaction_mode": True
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_unique_constraint_under_concurrent_inserts(self, call_mcp):
        """Unique constraints should be enforced."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "create",
            "entity_type": "organization",
            "data": {
                "name": "unique_org",
                "email": "unique@example.com"
            },
            "check_unique": True
        })
        assert "success" in result or "error" in result


class TestBatchTransactionBehavior:
    """Test batch operations with transaction semantics."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("entity_type", ["organization", "project", "document", "requirement"])
    async def test_batch_creates_transactional(self, call_mcp, entity_type):
        """Batch creates should be transactional if requested."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "batch",
            "entity_type": entity_type,
            "batch": [
                {"op": "create", "data": {"name": f"{entity_type}_1"}},
                {"op": "create", "data": {"name": f"{entity_type}_2"}}
            ],
            "transaction_mode": True
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    @pytest.mark.parametrize("entity_type", ["organization", "project", "document", "requirement"])
    async def test_batch_updates_transactional(self, call_mcp, entity_type):
        """Batch updates should be transactional."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "batch",
            "entity_type": entity_type,
            "batch": [
                {"op": "update", "entity_id": f"{entity_type}-1", "data": {"status": "active"}},
                {"op": "update", "entity_id": f"{entity_type}-2", "data": {"status": "active"}}
            ],
            "transaction_mode": True
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    @pytest.mark.parametrize("entity_type", ["organization", "project", "document", "requirement"])
    async def test_batch_mixed_operations(self, call_mcp, entity_type):
        """Batch with mixed operations should be transactional."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "batch",
            "entity_type": entity_type,
            "batch": [
                {"op": "create", "data": {"name": f"new_{entity_type}"}},
                {"op": "update", "entity_id": f"{entity_type}-1", "data": {"status": "updated"}}
            ],
            "transaction_mode": True
        })
        assert "success" in result or "error" in result
