"""Concurrency management for safe multi-user operations."""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Dict, Any, Optional, Callable, Awaitable, List
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger(__name__)


class ConflictResolution(Enum):
    """Strategies for resolving concurrent updates."""
    
    FIRST_WINS = "first_wins"  # First update succeeds, later ones are rejected
    LAST_WINS = "last_wins"  # Last update succeeds, overwrites previous
    MERGE = "merge"  # Attempt to merge changes
    MANUAL = "manual"  # Requires manual resolution


class ConcurrencyException(Exception):
    """Raised when concurrent operations conflict."""
    
    def __init__(self, message: str, conflict_data: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.conflict_data = conflict_data or {}


class ConcurrencyManager:
    """Manages concurrent access and conflict resolution."""
    
    def __init__(self, default_resolution: ConflictResolution = ConflictResolution.FIRST_WINS):
        """Initialize concurrency manager.
        
        Args:
            default_resolution: Default conflict resolution strategy
        """
        self.default_resolution = default_resolution
        self._locks: Dict[str, asyncio.Lock] = {}
        self._transactions: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
    
    async def execute_with_lock(
        self,
        resource_id: str,
        operation: Callable[[], Awaitable[Any]],
        timeout: float = 30.0
    ) -> Any:
        """Execute operation with exclusive lock on resource.
        
        Args:
            resource_id: Unique identifier for the resource
            operation: Async function to execute
            timeout: Lock timeout in seconds
            
        Returns:
            Result of operation
            
        Raises:
            asyncio.TimeoutError: If lock cannot be acquired
        """
        # Get or create lock for resource
        async with self._lock:
            if resource_id not in self._locks:
                self._locks[resource_id] = asyncio.Lock()
            resource_lock = self._locks[resource_id]
        
        # Execute operation with lock (with timeout on lock acquisition)
        try:
            async with asyncio.timeout(timeout):
                async with resource_lock:
                    return await operation()
        except asyncio.TimeoutError:
            raise asyncio.TimeoutError(
                f"Could not acquire lock for resource {resource_id} within {timeout}s"
            )
    
    async def execute_transaction(
        self,
        transaction_id: Optional[str] = None,
        operations: List[Callable[[], Awaitable[Any]]] = None
    ) -> Dict[str, Any]:
        """Execute multiple operations as a transaction.
        
        Args:
            transaction_id: Optional transaction ID
            operations: List of operations to execute
            
        Returns:
            Transaction result with status and details
        """
        if not transaction_id:
            transaction_id = str(uuid.uuid4())
        
        if not operations:
            operations = []
        
        transaction = {
            "transaction_id": transaction_id,
            "status": "pending",
            "operations": len(operations),
            "results": [],
            "errors": [],
            "created_at": datetime.now(timezone.utc),
            "started_at": None,
            "completed_at": None
        }
        
        # Store transaction
        self._transactions[transaction_id] = transaction
        
        try:
            transaction["status"] = "running"
            transaction["started_at"] = datetime.now(timezone.utc)
            
            # Execute operations
            completed = 0
            for operation in operations:
                try:
                    result = await operation()
                    transaction["results"].append(result)
                    completed += 1
                except Exception as e:
                    error = str(e)
                    transaction["errors"].append(error)
                    
                    # For now, fail fast on first error
                    # In production, might continue depending on operation type
                    transaction["status"] = "failed"
                    transaction["completed_at"] = datetime.now(timezone.utc)
                    
                    return {
                        "success": False,
                        "transaction_id": transaction_id,
                        "error": error,
                        "operations": len(operations),
                        "completed_operations": completed
                    }
            
            transaction["status"] = "completed"
            transaction["completed_at"] = datetime.now(timezone.utc)
            
            return {
                "success": True,
                "transaction_id": transaction_id,
                "results": transaction["results"],
                "operations": len(operations)
            }
            
        finally:
            # Clean up old transactions (keep last 100)
            if len(self._transactions) > 100:
                oldest_ids = sorted(self._transactions.keys())[:50]
                for old_id in oldest_ids:
                    del self._transactions[old_id]
    
    async def detect_conflict(
        self,
        current_data: Dict[str, Any],
        incoming_data: Dict[str, Any],
        last_modified: Optional[datetime] = None,
        resolution: Optional[ConflictResolution] = None
    ) -> Dict[str, Any]:
        """Detect and resolve conflicts between data versions.
        
        Args:
            current_data: Current stored data
            incoming_data: New data being applied
            last_modified: When current data was last modified
            resolution: Conflict resolution strategy
            
        Returns:
            Dict with resolved data and conflict info
        """
        resolution = resolution or self.default_resolution
        
        # Detect conflicts
        conflicts = []
        for field, new_value in incoming_data.items():
            if field in current_data:
                current_value = current_data[field]
                if current_value != new_value:
                    conflicts.append({
                        "field": field,
                        "current": current_value,
                        "incoming": new_value
                    })
        
        if not conflicts:
            return {
                "has_conflicts": False,
                "resolved_data": incoming_data,
                "conflicts": []
            }
        
        # Resolve conflicts based on strategy
        if resolution == ConflictResolution.FIRST_WINS:
            # Reject incoming changes
            raise ConcurrencyException(
                "Concurrent modification detected - changes rejected",
                {
                    "conflicts": conflicts,
                    "current_data": current_data,
                    "rejected_data": incoming_data
                }
            )
        
        elif resolution == ConflictResolution.LAST_WINS:
            # Accept incoming changes, overwriting current
            return {
                "has_conflicts": True,
                "resolved_data": {**current_data, **incoming_data},
                "conflicts": conflicts,
                "resolution": "last_wins"
            }
        
        elif resolution == ConflictResolution.MERGE:
            # Attempt to merge changes
            merged_data = current_data.copy()
            
            for conflict in conflicts:
                field = conflict["field"]
                
                # Simple merge strategy:
                # - For strings, concatenate
                # - For numbers, take max
                # - For lists/objects, merge
                current_value = conflict["current"]
                incoming_value = conflict["incoming"]
                
                if isinstance(current_value, str) and isinstance(incoming_value, str):
                    merged_data[field] = f"{current_value} | {incoming_value}"
                elif isinstance(current_value, (int, float)) and isinstance(incoming_value, (int, float)):
                    merged_data[field] = max(current_value, incoming_value)
                elif isinstance(current_value, dict) and isinstance(incoming_value, dict):
                    merged_data[field] = {**current_value, **incoming_value}
                elif isinstance(current_value, list) and isinstance(incoming_value, list):
                    merged_data[field] = list(set(current_value + incoming_value))
                else:
                    # Can't merge, take incoming
                    merged_data[field] = incoming_value
            
            return {
                "has_conflicts": True,
                "resolved_data": merged_data,
                "conflicts": conflicts,
                "resolution": "merged"
            }
        
        else:  # MANUAL
            # Return conflict for manual resolution
            return {
                "has_conflicts": True,
                "resolved_data": current_data,  # Don't change
                "conflicts": conflicts,
                "resolution": "manual_review_required"
            }
    
    async def optimistic_update(
        self,
        table: str,
        entity_id: str,
        update_data: Dict[str, Any],
        expected_version: Optional[int] = None,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """Perform optimistic update with retry logic.
        
        Args:
            table: Database table
            entity_id: Entity ID to update
            update_data: Data to update
            expected_version: Expected version number
            max_retries: Maximum retry attempts
            
        Returns:
            Update result
            
        Raises:
            ConcurrencyException: If max retries exceeded
        """
        from .factory import get_adapters
        
        adapters = get_adapters()
        db = adapters["database"]
        
        for attempt in range(max_retries):
            try:
                # Get current entity
                current = await db.get_single(
                    table,
                    filters={"id": entity_id}
                )
                
                if not current:
                    raise ConcurrencyException(f"Entity {entity_id} not found")
                
                # Check version if provided
                if expected_version is not None:
                    current_version = current.get("version", 0)
                    if current_version != expected_version:
                        raise ConcurrencyException(
                            f"Version mismatch: expected {expected_version}, got {current_version}",
                            {
                                "current_data": current,
                                "attempt": attempt + 1
                            }
                        )
                
                # Detect conflicts
                conflict_result = await self.detect_conflict(
                    current, update_data
                )
                
                if conflict_result["has_conflicts"]:
                    resolution = conflict_result.get("resolution", "")
                    if resolution == "manual_review_required":
                        raise ConcurrencyException(
                            "Manual conflict resolution required",
                            {
                                "conflicts": conflict_result["conflicts"],
                                "current_data": current
                            }
                        )
                    
                    update_data = conflict_result["resolved_data"]
                
                # Increment version for optimistic locking
                update_data["version"] = (current.get("version", 0) + 1)
                update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
                
                # Perform update with version check
                result = await db.update(
                    table,
                    update_data,
                    filters={
                        "id": entity_id,
                        "version": current.get("version", 0)  # Match current version
                    },
                    returning="*"
                )
                
                if result:
                    return {
                        "success": True,
                        "entity": result,
                        "attempt": attempt + 1,
                        "version": result.get("version")
                    }
                else:
                    # Version mismatch, retry
                    if attempt == max_retries - 1:
                        raise ConcurrencyException(
                            f"Failed to update after {max_retries} attempts - concurrent modifications",
                            {
                                "current_data": current,
                                "attempts": max_retries
                            }
                        )
                    continue
                    
            except ConcurrencyException:
                # Re-raise concurrency exceptions
                raise
            except Exception as e:
                # Unexpected error
                if attempt == max_retries - 1:
                    raise
                # Brief delay before retry
                await asyncio.sleep(0.1 * (attempt + 1))
    
    async def bulk_operation_with_concurrency(
        self,
        operation_type: str,
        entity_type: str,
        entity_ids: List[str],
        operation_data: Dict[str, Any],
        max_concurrent: int = 10
    ) -> Dict[str, Any]:
        """Execute bulk operations with concurrency control.
        
        Args:
            operation_type: Type of operation (update, delete, archive)
            entity_type: Type of entities
            entity_ids: List of entity IDs
            operation_data: Data for operations
            max_concurrent: Maximum concurrent operations
            
        Returns:
            Bulk operation result
        """
        if not entity_ids:
            return {
                "success": True,
                "processed": 0,
                "failed": 0,
                "results": []
            }
        
        # Create semaphore to limit concurrency
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_entity(entity_id: str) -> Dict[str, Any]:
            async with semaphore:
                try:
                    # Use resource lock for each entity
                    return await self.execute_with_lock(
                        f"{entity_type}:{entity_id}",
                        lambda: self._process_single_entity(
                            operation_type, entity_type, entity_id, operation_data
                        ),
                        timeout=10.0
                    )
                except Exception as e:
                    return {
                        "entity_id": entity_id,
                        "success": False,
                        "error": str(e)
                    }
        
        # Process all entities concurrently
        tasks = [process_entity(eid) for eid in entity_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        processed = 0
        failed = 0
        successful_results = []
        errors = []
        
        for result in results:
            if isinstance(result, Exception):
                failed += 1
                errors.append(str(result))
            else:
                if result.get("success", False):
                    processed += 1
                    successful_results.append(result)
                else:
                    failed += 1
                    errors.append(result.get("error", "Unknown error"))
        
        return {
            "success": failed == 0,
            "processed": processed,
            "failed": failed,
            "total": len(entity_ids),
            "results": successful_results,
            "errors": errors if errors else None
        }
    
    async def _process_single_entity(
        self,
        operation_type: str,
        entity_type: str,
        entity_id: str,
        operation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process single entity operation."""
        from .factory import get_adapters
        
        adapters = get_adapters()
        db = adapters["database"]
        table = self._get_table_name(entity_type)
        
        if operation_type == "update":
            result = await db.update(
                table,
                operation_data,
                filters={"id": entity_id},
                returning="*"
            )
            return {
                "entity_id": entity_id,
                "success": bool(result),
                "entity": result
            }
        
        elif operation_type == "delete" or operation_type == "archive":
            # Soft delete/archive
            delete_data = {
                "is_deleted": True,
                "deleted_at": datetime.now(timezone.utc).isoformat(),
                **operation_data
            }
            
            result = await db.update(
                table,
                delete_data,
                filters={"id": entity_id}
            )
            
            return {
                "entity_id": entity_id,
                "success": bool(result),
                "operation": operation_type
            }
        
        else:
            raise ValueError(f"Unknown operation type: {operation_type}")
    
    def _get_table_name(self, entity_type: str) -> str:
        """Get table name for entity type."""
        # Simple mapping - could be more sophisticated
        type_to_table = {
            "organization": "organizations",
            "project": "projects",
            "document": "documents",
            "requirement": "requirements",
            "test": "tests",
            "property": "properties",
            "block": "blocks",
            "column": "columns",
            "workflow": "workflows",
            "invitation": "invitations",
            "member": "members",
            "comment": "comments"
        }
        
        return type_to_table.get(entity_type.lower(), f"{entity_type}s")
    
    async def cleanup(self):
        """Clean up resources and old transactions."""
        # Clear locks that might be stuck
        async with self._lock:
            self._locks.clear()
        
        # Clear very old transactions
        cutoff = datetime.now(timezone.utc).timestamp() - 3600  # 1 hour ago
        
        for tid, transaction in list(self._transactions.items()):
            if transaction["created_at"].timestamp() < cutoff:
                del self._transactions[tid]


# Global concurrency manager instance
_concurrency_manager = None


def get_concurrency_manager() -> ConcurrencyManager:
    """Get the global concurrency manager instance."""
    global _concurrency_manager
    if _concurrency_manager is None:
        _concurrency_manager = ConcurrencyManager()
    return _concurrency_manager
