"""E2E performance monitoring and disaster recovery fixtures."""

import time
from contextlib import asynccontextmanager
from typing import Dict, Any
import pytest
import pytest_asyncio


@pytest_asyncio.fixture
async def e2e_performance_tracker():
    """Track performance metrics for E2E tests with real-world characteristics."""

    class E2EPerformanceTracker:
        def __init__(self):
            self.metrics = {
                "network_latency": [],
                "db_query_time": [],
                "total_workflow_time": [],
                "concurrent_operations": 0,
                "errors": [],
                "memory_usage": []
            }

        @asynccontextmanager
        async def track_operation(self, operation_name: str):
            """Track an E2E operation with full metrics."""
            start = time.time()
            self.metrics["concurrent_operations"] += 1

            try:
                yield
                elapsed = (time.time() - start) * 1000

                if "workflow" in operation_name.lower():
                    self.metrics["total_workflow_time"].append(elapsed)
                else:
                    self.metrics["network_latency"].append(elapsed)

            except Exception as e:
                self.metrics["errors"].append({
                    "operation": operation_name,
                    "error": str(e),
                    "timestamp": time.time()
                })
                raise
            finally:
                self.metrics["concurrent_operations"] -= 1

        def get_report(self) -> Dict[str, Any]:
            """Generate comprehensive E2E performance report."""
            return {
                "network": {
                    "avg_latency_ms": sum(self.metrics["network_latency"]) / len(self.metrics["network_latency"]) if self.metrics["network_latency"] else 0,
                    "max_latency_ms": max(self.metrics["network_latency"]) if self.metrics["network_latency"] else 0,
                },
                "workflows": {
                    "avg_duration_ms": sum(self.metrics["total_workflow_time"]) / len(self.metrics["total_workflow_time"]) if self.metrics["total_workflow_time"] else 0,
                    "max_duration_ms": max(self.metrics["total_workflow_time"]) if self.metrics["total_workflow_time"] else 0,
                },
                "reliability": {
                    "error_count": len(self.metrics["errors"]),
                    "success_rate": 1 - (len(self.metrics["errors"]) / max(1, len(self.metrics["network_latency"]) + len(self.metrics["total_workflow_time"])))
                }
            }

    return E2EPerformanceTracker()


@pytest.fixture
def e2e_test_cleanup():
    """Cleanup utility for E2E tests to ensure no test data pollution."""
    created_entities = []
    created_relationships = []

    def track_entity(entity_type: str, entity_id: str):
        """Track created entity for cleanup."""
        created_entities.append((entity_type, entity_id))
        return entity_id

    def track_relationship(relationship_id: str):
        """Track created relationship for cleanup."""
        created_relationships.append(relationship_id)
        return relationship_id

    yield track_entity, track_relationship

    # In real E2E, would perform actual database cleanup
    # For now, just clear the tracking lists
    created_entities.clear()
    created_relationships.clear()


@pytest_asyncio.fixture
async def disaster_recovery_scenario():
    """Simulate disaster recovery scenarios for E2E testing."""

    class DisasterSimulator:
        async def simulate_database_failure(self):
            """Simulate temporary database failure."""
            return {
                "success": False,
                "error": "Database connection failed",
                "recovery_available": True,
                "estimated_recovery_time": 30  # seconds
            }

        async def simulate_network_partition(self):
            """Simulate network partition between components."""
            return {
                "success": False,
                "error": "Network partition detected",
                "affected_components": ["database", "auth-service"],
                "retry_after": 10
            }

        async def simulate_authentication_failure(self):
            """Simulate authentication service failure."""
            return {
                "success": False,
                "error": "Authentication service unavailable",
                "fallback_auth": True
            }

    return DisasterSimulator()
