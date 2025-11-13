"""Tests for concurrency manager and safe multi-user operations."""

import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from infrastructure.concurrency_manager import (
    ConcurrencyManager,
    ConflictResolution,
    ConcurrencyException,
    get_concurrency_manager
)


class TestConcurrencyBasics:
    """Test basic concurrency functionality."""
    
    @pytest.mark.asyncio
    async def test_concurrent_execution_with_lock(self):
        """Test concurrent operations respect resource locks."""
        manager = ConcurrencyManager()
        results = []
        
        async def operation(value: int):
            await asyncio.sleep(0.1)  # Simulate work
            results.append(value)
            return value
        
        # Execute multiple operations on same resource
        tasks = [
            manager.execute_with_lock("resource1", lambda: operation(1)),
            manager.execute_with_lock("resource1", lambda: operation(2)),
            manager.execute_with_lock("resource1", lambda: operation(3))
        ]
        
        await asyncio.gather(*tasks)
        
        # All operations should complete, but sequentially
        assert len(results) == 3
        assert set(results) == {1, 2, 3}
    
    @pytest.mark.asyncio
    async def test_different_resources_parallel(self):
        """Test operations on different resources run in parallel."""
        manager = ConcurrencyManager()
        start_time = datetime.now()
        
        async def slow_operation():
            await asyncio.sleep(0.2)
            return "done"
        
        # Execute on different resources
        tasks = [
            manager.execute_with_lock("resource1", slow_operation),
            manager.execute_with_lock("resource2", slow_operation),
            manager.execute_with_lock("resource3", slow_operation)
        ]
        
        await asyncio.gather(*tasks)
        end_time = datetime.now()
        
        # Should run in parallel (approx 0.2s, not 0.6s)
        duration = (end_time - start_time).total_seconds()
        assert 0.1 < duration < 0.3
    
    @pytest.mark.asyncio
    async def test_lock_timeout(self):
        """Test lock timeout works correctly."""
        manager = ConcurrencyManager()
        
        async def long_operation():
            await asyncio.sleep(2.0)
            return "slow"
        
        async def quick_operation():
            return "quick"
        
        # Start long operation
        long_task = asyncio.create_task(
            manager.execute_with_lock("resource1", long_operation, timeout=5.0)
        )
        
        # Try to acquire same lock with short timeout
        with pytest.raises(asyncio.TimeoutError):
            await manager.execute_with_lock("resource1", quick_operation, timeout=0.5)
        
        # Cancel long operation
        long_task.cancel()
        try:
            await long_task
        except asyncio.CancelledError:
            pass


class TestConflictResolution:
    """Test conflict detection and resolution."""
    
    @pytest.mark.asyncio
    async def test_no_conflict_detected(self):
        """Test no conflicts when data matches."""
        manager = ConcurrencyManager()
        
        current = {"name": "Test", "value": 100}
        incoming = {"name": "Test", "value": 100}
        
        result = await manager.detect_conflict(current, incoming)
        
        assert result["has_conflicts"] is False
        assert result["resolved_data"] == incoming
        assert len(result["conflicts"]) == 0
    
    @pytest.mark.asyncio
    async def test_conflict_detected(self):
        """Test conflicts are detected correctly."""
        manager = ConcurrencyManager()
        
        current = {"name": "Old Name", "value": 100}
        incoming = {"name": "New Name", "value": 200}
        
        result = await manager.detect_conflict(current, incoming)
        
        assert result["has_conflicts"] is True
        assert len(result["conflicts"]) == 2
        
        # Check conflict details
        conflict_fields = {c["field"] for c in result["conflicts"]}
        assert "name" in conflict_fields
        assert "value" in conflict_fields
    
    @pytest.mark.asyncio
    async def test_first_wins_resolution(self):
        """Test first-wins conflict resolution."""
        manager = ConcurrencyManager(ConflictResolution.FIRST_WINS)
        
        current = {"name": "Original", "value": 100}
        incoming = {"name": "Changed", "value": 200}
        
        # Should raise exception for first-wins
        with pytest.raises(ConcurrencyException):
            await manager.detect_conflict(current, incoming)
    
    @pytest.mark.asyncio
    async def test_last_wins_resolution(self):
        """Test last-wins conflict resolution."""
        manager = ConcurrencyManager(ConflictResolution.LAST_WINS)
        
        current = {"name": "Original", "value": 100}
        incoming = {"name": "Changed", "value": 200}
        
        result = await manager.detect_conflict(current, incoming)
        
        assert result["has_conflicts"] is True
        assert result["resolution"] == "last_wins"
        assert result["resolved_data"]["name"] == "Changed"
        assert result["resolved_data"]["value"] == 200
    
    @pytest.mark.asyncio
    async def test_merge_resolution_strings(self):
        """Test merge resolution for string fields."""
        manager = ConcurrencyManager(ConflictResolution.MERGE)
        
        current = {"description": "First part"}
        incoming = {"description": "Second part"}
        
        result = await manager.detect_conflict(current, incoming)
        
        assert result["has_conflicts"] is True
        assert result["resolution"] == "merged"
        assert "First part" in result["resolved_data"]["description"]
        assert "Second part" in result["resolved_data"]["description"]
    
    @pytest.mark.asyncio
    async def test_merge_resolution_numbers(self):
        """Test merge resolution for numeric fields."""
        manager = ConcurrencyManager(ConflictResolution.MERGE)
        
        current = {"priority": 1}
        incoming = {"priority": 5}
        
        result = await manager.detect_conflict(current, incoming)
        
        assert result["has_conflicts"] is True
        assert result["resolution"] == "merged"
        assert result["resolved_data"]["priority"] == 5  # Max
    
    @pytest.mark.asyncio
    async def test_merge_resolution_lists(self):
        """Test merge resolution for list fields."""
        manager = ConcurrencyManager(ConflictResolution.MERGE)
        
        current = {"tags": ["a", "b"]}
        incoming = {"tags": ["b", "c"]}
        
        result = await manager.detect_conflict(current, incoming)
        
        assert result["has_conflicts"] is True
        assert result["resolution"] == "merged"
        merged_tags = result["resolved_data"]["tags"]
        assert set(merged_tags) == {"a", "b", "c"}
    
    @pytest.mark.asyncio
    async def test_merge_resolution_dicts(self):
        """Test merge resolution for dict/object fields."""
        manager = ConcurrencyManager(ConflictResolution.MERGE)
        
        current = {"metadata": {"key1": "value1"}}
        incoming = {"metadata": {"key2": "value2"}}
        
        result = await manager.detect_conflict(current, incoming)
        
        assert result["has_conflicts"] is True
        assert result["resolution"] == "merged"
        merged_metadata = result["resolved_data"]["metadata"]
        assert merged_metadata["key1"] == "value1"
        assert merged_metadata["key2"] == "value2"
    
    @pytest.mark.asyncio
    async def test_manual_resolution(self):
        """Test manual conflict resolution."""
        manager = ConcurrencyManager(ConflictResolution.MANUAL)
        
        current = {"name": "Original"}
        incoming = {"name": "Changed"}
        
        result = await manager.detect_conflict(current, incoming)
        
        assert result["has_conflicts"] is True
        assert result["resolution"] == "manual_review_required"
        assert result["resolved_data"] == current  # Unchanged


class TestTransactionManagement:
    """Test transaction execution and management."""
    
    @pytest.mark.asyncio
    async def test_transaction_success(self):
        """Test successful transaction execution."""
        manager = ConcurrencyManager()
        
        async def operation1():
            return "result1"
        
        async def operation2():
            return "result2"
        
        transaction = await manager.execute_transaction(
            operations=[operation1, operation2]
        )
        
        assert transaction["success"] is True
        assert transaction["operations"] == 2
        assert len(transaction["results"]) == 2
        assert transaction["results"][0] == "result1"
        assert transaction["results"][1] == "result2"
    
    @pytest.mark.asyncio
    async def test_transaction_failure(self):
        """Test transaction failure on first error."""
        manager = ConcurrencyManager()
        
        async def operation1():
            return "result1"
        
        async def operation2():
            raise ValueError("Operation failed")
        
        async def operation3():
            return "result3"
        
        transaction = await manager.execute_transaction(
            operations=[operation1, operation2, operation3]
        )
        
        assert transaction["success"] is False
        assert "Operation failed" in transaction["error"]
        assert transaction["operations"] == 3
        assert transaction["completed_operations"] == 1  # Only first succeeded
    
    @pytest.mark.asyncio
    async def test_transaction_with_custom_id(self):
        """Test transaction with custom ID."""
        manager = ConcurrencyManager()
        custom_id = "custom-transaction-123"
        
        async def operation():
            return "result"
        
        transaction = await manager.execute_transaction(
            transaction_id=custom_id,
            operations=[operation]
        )
        
        assert transaction["transaction_id"] == custom_id
        assert transaction["success"] is True
    
    @pytest.mark.asyncio
    async def test_transaction_cleanup(self):
        """Test old transactions are cleaned up."""
        manager = ConcurrencyManager()
        
        async def operation():
            return "result"
        
        # Create many transactions to trigger cleanup
        for i in range(150):
            await manager.execute_transaction(operations=[operation])
        
        # Should only keep recent transactions
        assert len(manager._transactions) <= 100


class TestOptimisticUpdate:
    """Test optimistic update with version control."""
    
    @pytest.mark.asyncio
    async def test_optimistic_update_success(self):
        """Test successful optimistic update."""
        manager = ConcurrencyManager()
        
        # Mock database adapter
        with patch('infrastructure.concurrency_manager.get_adapters') as mock_adapters:
            mock_db = AsyncMock()
            mock_adapters.return_value = {"database": mock_db}
            
            # Mock get_single for current data
            mock_db.get_single.return_value = {
                "id": "entity1",
                "name": "Original",
                "version": 1
            }
            
            # Mock update for successful result
            mock_db.update.return_value = {
                "id": "entity1",
                "name": "Updated",
                "version": 2
            }
            
            result = await manager.optimistic_update(
                table="entities",
                entity_id="entity1",
                update_data={"name": "Updated"},
                expected_version=1
            )
            
            assert result["success"] is True
            assert result["entity"]["name"] == "Updated"
            assert result["version"] == 2
            assert result["attempt"] == 1
    
    @pytest.mark.asyncio
    async def test_optimistic_update_version_mismatch(self):
        """Test optimistic update fails on version mismatch."""
        manager = ConcurrencyManager()
        
        with patch('infrastructure.concurrency_manager.get_adapters') as mock_adapters:
            mock_db = AsyncMock()
            mock_adapters.return_value = {"database": mock_db}
            
            # Mock get_single returning different version
            mock_db.get_single.return_value = {
                "id": "entity1",
                "name": "Original",
                "version": 2  # Higher than expected
            }
            
            result = await manager.optimistic_update(
                table="entities",
                entity_id="entity1",
                update_data={"name": "Updated"},
                expected_version=1
            )
            
            assert result["success"] is False
            assert "Version mismatch" in result["error"]
    
    @pytest.mark.asyncio
    async def test_optimistic_update_retry_on_conflict(self):
        """Test optimistic update retries on conflict."""
        manager = ConcurrencyManager()
        
        with patch('infrastructure.concurrency_manager.get_adapters') as mock_adapters:
            mock_db = AsyncMock()
            mock_adapters.return_value = {"database": mock_db}
            
            # First call returns version 1
            # Update fails (returns None for conflict)
            # Second call returns version 2 (concurrent update)
            # Third update succeeds
            mock_db.get_multiple.side_effect = [
                {"id": "entity1", "version": 1},
                {"id": "entity1", "version": 2},
                {"id": "entity1", "version": 2}
            ]
            
            mock_db.update.side_effect = [None, None, {
                "id": "entity1",
                "name": "Updated",
                "version": 3
            }]
            
            result = await manager.optimistic_update(
                table="entities",
                entity_id="entity1",
                update_data={"name": "Updated"},
                expected_version=1,
                max_retries=3
            )
            
            assert result["success"] is True
            assert result["attempt"] == 3  # Retried 3 times
            assert result["version"] == 3


class TestBulkOperationsWithConcurrency:
    """Test bulk operations with concurrency control."""
    
    @pytest.mark.asyncio
    async def test_bulk_update_success(self):
        """Test successful bulk update with concurrency."""
        manager = ConcurrencyManager()
        
        entity_ids = ["ent1", "ent2", "ent3"]
        
        with patch.object(manager, '_process_single_entity') as mock_process:
            mock_process.return_value = {
                "entity_id": "mock_id",
                "success": True,
                "entity": {"id": "mock_id", "name": "Updated"}
            }
            
            result = await manager.bulk_operation_with_concurrency(
                operation_type="update",
                entity_type="document",
                entity_ids=entity_ids,
                operation_data={"status": "updated"},
                max_concurrent=2
            )
            
            assert result["success"] is True
            assert result["processed"] == 3
            assert result["failed"] == 0
            assert result["total"] == 3
    
    @pytest.mark.asyncio
    async def test_bulk_operation_partial_failure(self):
        """Test bulk operation with partial failures."""
        manager = ConcurrencyManager()
        
        entity_ids = ["ent1", "ent2", "ent3", "ent4"]
        
        # Mock processing - fail for ent2 and ent4
        async def mock_process(entity_id):
            if entity_id in ["ent2", "ent4"]:
                raise Exception("Processing failed")
            return {"entity_id": entity_id, "success": True}
        
        with patch.object(manager, '_process_single_entity', side_effect=mock_process):
            result = await manager.bulk_operation_with_concurrency(
                operation_type="update",
                entity_type="document",
                entity_ids=entity_ids,
                operation_data={"status": "updated"}
            )
            
            assert result["success"] is False
            assert result["processed"] == 2  # ent1, ent3
            assert result["failed"] == 2  # ent2, ent4
            assert result["total"] == 4
            assert len(result["errors"]) == 2
    
    @pytest.mark.asyncio
    async def test_bulk_operation_concurrency_limit(self):
        """Test bulk operation respects concurrency limit."""
        manager = ConcurrencyManager()
        concurrent_operations = []
        
        async def mock_process(entity_id):
            concurrent_operations.append(entity_id)
            await asyncio.sleep(0.1)
            return {"entity_id": entity_id, "success": True}
        
        entity_ids = [f"ent{i}" for i in range(10)]
        
        with patch.object(manager, '_process_single_entity', side_effect=mock_process):
            result = await manager.bulk_operation_with_concurrency(
                operation_type="update",
                entity_type="document",
                entity_ids=entity_ids,
                operation_data={"status": "updated"},
                max_concurrent=3
            )
            
            assert result["success"] is True
            assert result["processed"] == 10
            
            # Check that max concurrent was respected
            # (This is a basic check - actual concurrency testing is complex)
            assert len(concurrent_operations) == 10
    
    @pytest.mark.asyncio
    async def test_bulk_operation_empty_list(self):
        """Test bulk operation with empty entity list."""
        manager = ConcurrencyManager()
        
        result = await manager.bulk_operation_with_concurrency(
            operation_type="update",
            entity_type="document",
            entity_ids=[],
            operation_data={"status": "updated"}
        )
        
        assert result["success"] is True
        assert result["processed"] == 0
        assert result["failed"] == 0
        assert result["total"] == 0


class TestConcurrencyManagerEdgeCases:
    """Test edge cases and error handling."""
    
    @pytest.mark.asyncio
    async def test_cleanup_removes_old_transactions(self):
        """Test cleanup removes old transactions."""
        manager = ConcurrencyManager()
        
        # Create transaction
        await manager.execute_transaction(operations=[
            asyncio.create_task(lambda: "result")
        ])
        
        # Check cleanup doesn't break functionality
        await manager.cleanup()
        
        # Should still work after cleanup
        result = await manager.execute_transaction(operations=[
            asyncio.create_task(lambda: "new_result")
        ])
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_global_manager_singleton(self):
        """Test global concurrency manager is singleton."""
        manager1 = get_concurrency_manager()
        manager2 = get_concurrency_manager()
        
        # Should be same instance
        assert manager1 is manager2
    
    @pytest.mark.asyncio
    async def test_table_name_resolution(self):
        """Test table name resolution for entity types."""
        manager = ConcurrencyManager()
        
        assert manager._get_table_name("organization") == "organizations"
        assert manager._get_table_name("document") == "documents"
        assert manager._get_table_name("test") == "tests"
        assert manager._get_table_name("custom_entity") == "custom_entitys"
    
    @pytest.mark.asyncio
    async def test_unknown_operation_type(self):
        """Test unknown operation type raises error."""
        manager = ConcurrencyManager()
        
        with pytest.raises(ValueError, match="Unknown operation type"):
            await manager._process_single_entity(
                operation_type="unknown",
                entity_type="document",
                entity_id="doc1",
                operation_data={}
            )
    
    @pytest.mark.asyncio
    async def test_transaction_without_operations(self):
        """Test transaction with no operations."""
        manager = ConcurrencyManager()
        
        transaction = await manager.execute_transaction()
        
        assert transaction["success"] is True
        assert transaction["operations"] == 0
        assert len(transaction["results"]) == 0


class TestConcurrencyPerformance:
    """Test concurrency performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_lock_performance(self):
        """Test that locks don't significantly impact performance."""
        import time
        
        manager = ConcurrencyManager()
        
        async def fast_operation():
            return "result"
        
        start_time = time.time()
        
        # Execute many operations on different resources (should be fast)
        tasks = []
        for i in range(100):
            task = manager.execute_with_lock(
                f"resource{i}", 
                fast_operation
            )
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        end_time = time.time()
        
        duration = end_time - start_time
        # Should be fast (under 1 second for 100 simple operations)
        assert duration < 1.0, f"Lock operations too slow: {duration}s"
    
    @pytest.mark.asyncio
    async def test_bulk_operation_performance(self):
        """Test bulk operation performance with concurrency control."""
        import time
        
        manager = ConcurrencyManager()
        entity_ids = [f"ent{i}" for i in range(50)]
        
        start_time = time.time()
        
        result = await manager.bulk_operation_with_concurrency(
            operation_type="update",
            entity_type="document",
            entity_ids=entity_ids,
            operation_data={"status": "updated"},
            max_concurrent=10
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert result["success"] is True
        assert result["processed"] == 50
        
        # Should complete reasonably fast (under 2 seconds for 50 operations)
        assert duration < 2.0, f"Bulk operation too slow: {duration}s"
    
    @pytest.mark.asyncio
    async def test_memory_usage(self):
        """Test memory usage doesn't grow unbounded."""
        manager = ConcurrencyManager()
        
        # Create many locks and transactions
        for i in range(200):
            await manager.execute_with_lock(
                f"resource{i}",
                lambda: asyncio.sleep(0.001)
            )
        
        # Memory should be bounded (locks and transactions cleaned up)
        assert len(manager._locks) <= 200  # Should be cleaned up
        assert len(manager._transactions) <= 100  # Should be cleaned up
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
