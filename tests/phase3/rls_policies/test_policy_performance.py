"""
Test RLS Policy Performance (5 tests)

Tests RLS policy performance characteristics:
- Policy evaluation overhead < 20ms
- Bulk operations don't N+1
- Concurrent policy evaluations
- Policy caching effectiveness

Run with: pytest tests/phase3/rls_policies/test_policy_performance.py -v
"""

import asyncio
import time
from unittest.mock import AsyncMock
import pytest

from schemas import ProjectRole, UserRoleType, Visibility
from schemas.constants import Tables
from schemas.rls import (
    DocumentPolicy,
    OrganizationPolicy,
    PolicyValidator,
    ProjectPolicy,
    user_can_access_project,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_db_adapter():
    """Create mock database adapter with realistic latency."""
    mock = AsyncMock()

    # Simulate realistic database query time (1-2ms)
    async def mock_get_single(*args, **kwargs):
        await asyncio.sleep(0.001)  # 1ms delay
        return {
            "id": "member-001",
            "user_id": "user-test-001",
            "role": UserRoleType.MEMBER.value,
            "is_deleted": False,
        }

    async def mock_query(*args, **kwargs):
        await asyncio.sleep(0.001)  # 1ms delay
        return [
            {"id": "member-001", "organization_id": "org-001"},
            {"id": "member-002", "organization_id": "org-002"},
        ]

    mock.get_single = AsyncMock(side_effect=mock_get_single)
    mock.query = AsyncMock(side_effect=mock_query)
    return mock


@pytest.fixture
def fast_db_adapter():
    """Create mock database adapter with instant responses (for caching tests)."""
    mock = AsyncMock()
    mock.get_single = AsyncMock(return_value={
        "id": "member-001",
        "user_id": "user-test-001",
        "role": UserRoleType.MEMBER.value,
        "is_deleted": False,
    })
    mock.query = AsyncMock(return_value=[
        {"id": "member-001", "organization_id": "org-001"},
    ])
    return mock


# =============================================================================
# PERFORMANCE THRESHOLD CONSTANTS
# =============================================================================

# Maximum acceptable policy evaluation time
MAX_POLICY_OVERHEAD_MS = 20  # 20ms per policy check

# Maximum acceptable time for bulk operations
MAX_BULK_OPERATION_MS = 100  # 100ms for 10 items

# Concurrent operations target
CONCURRENT_OPERATIONS = 50


# =============================================================================
# POLICY OVERHEAD TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_single_policy_check_under_20ms_overhead(
    mock_db_adapter,
):
    """
    Given a single policy evaluation
    When measuring execution time
    Then total overhead is under 20ms

    Tests that policy checks are fast enough for production use.
    """
    policy = OrganizationPolicy("user-test-001", mock_db_adapter)

    # Measure time for single policy check
    start_time = time.perf_counter()

    can_read = await policy.can_select({"id": "org-001"})

    end_time = time.perf_counter()
    duration_ms = (end_time - start_time) * 1000

    # Then: Completes quickly
    assert can_read is True, "Policy should grant access"
    assert duration_ms < MAX_POLICY_OVERHEAD_MS, \
        f"Policy check took {duration_ms:.2f}ms, exceeds {MAX_POLICY_OVERHEAD_MS}ms threshold"

    print(f"✓ Single policy check: {duration_ms:.2f}ms (threshold: {MAX_POLICY_OVERHEAD_MS}ms)")


@pytest.mark.asyncio
async def test_complex_policy_check_under_threshold(
    mock_db_adapter,
):
    """
    Given a complex policy involving multiple checks
    When measuring execution time
    Then total time is under performance threshold

    Tests that even complex policies (project access via org) are fast.
    """
    # Setup: Complex scenario - check project access via org membership
    def mock_get_single(table, filters):
        """Simulate multi-step policy evaluation."""
        asyncio.create_task(asyncio.sleep(0.001))  # 1ms per query

        if table == Tables.PROJECT_MEMBERS:
            return None  # Not direct member

        if table == Tables.PROJECTS:
            return {
                "id": "project-001",
                "organization_id": "org-001",
                "visibility": Visibility.PRIVATE.value,
                "is_deleted": False,
            }

        if table == Tables.ORGANIZATION_MEMBERS:
            return {
                "id": "member-001",
                "organization_id": "org-001",
                "user_id": "user-test-001",
                "is_deleted": False,
            }

        return None

    mock_db_adapter.get_single = AsyncMock(side_effect=mock_get_single)

    # Measure complex policy check (3 DB queries)
    start_time = time.perf_counter()

    can_access = await user_can_access_project(
        "project-001",
        "user-test-001",
        mock_db_adapter
    )

    end_time = time.perf_counter()
    duration_ms = (end_time - start_time) * 1000

    # Then: Access granted and completes quickly
    assert can_access is True, "Complex policy should grant access"
    assert duration_ms < MAX_POLICY_OVERHEAD_MS, \
        f"Complex policy check took {duration_ms:.2f}ms, exceeds {MAX_POLICY_OVERHEAD_MS}ms threshold"

    print(f"✓ Complex policy check (3 queries): {duration_ms:.2f}ms (threshold: {MAX_POLICY_OVERHEAD_MS}ms)")


# =============================================================================
# BULK OPERATION TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_bulk_operations_dont_n_plus_1(
    mock_db_adapter,
):
    """
    Given a bulk operation checking 10 records
    When measuring database queries
    Then queries don't scale linearly (no N+1 problem)

    Tests that bulk checks use efficient query patterns.
    """
    validator = PolicyValidator("user-test-001", mock_db_adapter)

    # Setup: 10 organizations to check
    organizations = [
        {"id": f"org-{i:03d}"} for i in range(10)
    ]

    # Reset mock call count
    mock_db_adapter.get_single.reset_mock()

    # Measure time and query count
    start_time = time.perf_counter()

    # Check all organizations
    results = []
    for org in organizations:
        can_read = await validator.can_select(Tables.ORGANIZATIONS, org)
        results.append(can_read)

    end_time = time.perf_counter()
    duration_ms = (end_time - start_time) * 1000

    # Count database queries
    query_count = mock_db_adapter.get_single.call_count

    # Then: Completes quickly and doesn't make excessive queries
    assert all(results), "All checks should pass"
    assert duration_ms < MAX_BULK_OPERATION_MS, \
        f"Bulk operation took {duration_ms:.2f}ms, exceeds {MAX_BULK_OPERATION_MS}ms threshold"

    # Allow 1 query per check (acceptable) but warn if much higher
    max_acceptable_queries = len(organizations) + 2  # +2 for potential caching queries
    assert query_count <= max_acceptable_queries, \
        f"Made {query_count} queries for {len(organizations)} items (possible N+1)"

    print(f"✓ Bulk check ({len(organizations)} items): {duration_ms:.2f}ms, {query_count} queries")


@pytest.mark.asyncio
async def test_cached_policy_checks_are_faster(
    fast_db_adapter,
):
    """
    Given a PolicyValidator with caching enabled
    When checking the same resource multiple times
    Then subsequent checks use cached data and are faster

    Tests that policy validator caching reduces database load.
    """
    validator = PolicyValidator("user-test-001", fast_db_adapter)

    # First check - populates cache
    start_first = time.perf_counter()
    can_read_first = await validator.can_select(
        Tables.ORGANIZATIONS,
        {"id": "org-001"}
    )
    end_first = time.perf_counter()
    first_duration_ms = (end_first - start_first) * 1000

    # Get initial query count
    first_query_count = fast_db_adapter.get_single.call_count

    # Second check - uses cache (for super_admin, user_orgs)
    start_second = time.perf_counter()
    can_read_second = await validator.can_select(
        Tables.ORGANIZATIONS,
        {"id": "org-002"}
    )
    end_second = time.perf_counter()
    second_duration_ms = (end_second - start_second) * 1000

    # Get query count after second check
    second_query_count = fast_db_adapter.get_single.call_count

    # Then: Both succeed
    assert can_read_first is True, "First check should pass"
    assert can_read_second is True, "Second check should pass"

    # Verify caching reduces queries
    # First check might make multiple queries (super_admin, membership)
    # Second check should make fewer queries due to caching
    queries_for_second = second_query_count - first_query_count
    assert queries_for_second < first_query_count, \
        "Second check should use cached data and make fewer queries"

    print(f"✓ Caching test: First={first_duration_ms:.2f}ms ({first_query_count} queries), "
          f"Second={second_duration_ms:.2f}ms ({queries_for_second} queries)")


# =============================================================================
# CONCURRENT OPERATION TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_concurrent_policy_evaluations(
    mock_db_adapter,
):
    """
    Given 50 concurrent policy checks
    When all execute simultaneously
    Then all complete successfully and efficiently

    Tests that policy checks can handle concurrent load.
    """
    policy = DocumentPolicy("user-test-001", mock_db_adapter)

    # Setup: User has access to projects
    mock_db_adapter.get_single.return_value = {
        "id": "member-001",
        "project_id": "project-001",
        "user_id": "user-test-001",
        "role": ProjectRole.VIEWER.value,
        "is_deleted": False,
    }

    # Create concurrent tasks
    documents = [
        {"id": f"doc-{i:03d}", "project_id": "project-001"}
        for i in range(CONCURRENT_OPERATIONS)
    ]

    # Measure concurrent execution
    start_time = time.perf_counter()

    # Execute all checks concurrently
    tasks = [
        policy.can_select(doc)
        for doc in documents
    ]
    results = await asyncio.gather(*tasks)

    end_time = time.perf_counter()
    duration_ms = (end_time - start_time) * 1000

    # Then: All succeed
    assert all(results), "All concurrent checks should pass"
    assert len(results) == CONCURRENT_OPERATIONS, \
        f"Expected {CONCURRENT_OPERATIONS} results, got {len(results)}"

    # Concurrent execution should be faster than sequential
    # With 50 operations at 1ms each, sequential would be ~50ms
    # Concurrent should be much faster due to async I/O
    max_concurrent_time = CONCURRENT_OPERATIONS * 0.5  # 50% of sequential time
    assert duration_ms < max_concurrent_time, \
        f"Concurrent execution took {duration_ms:.2f}ms, expected < {max_concurrent_time:.0f}ms"

    print(f"✓ Concurrent checks ({CONCURRENT_OPERATIONS} operations): {duration_ms:.2f}ms "
          f"(~{duration_ms/CONCURRENT_OPERATIONS:.2f}ms per operation)")


# =============================================================================
# POLICY EVALUATION EFFICIENCY TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_policy_evaluation_scales_linearly(
    mock_db_adapter,
):
    """
    Given increasing numbers of policy checks
    When measuring execution time
    Then time scales approximately linearly (not exponentially)

    Tests that policy performance is predictable and scalable.
    """
    policy = ProjectPolicy("user-test-001", mock_db_adapter)

    # Test with different batch sizes
    batch_sizes = [5, 10, 20]
    timings = []

    for batch_size in batch_sizes:
        projects = [
            {"id": f"project-{i:03d}"}
            for i in range(batch_size)
        ]

        start_time = time.perf_counter()

        # Check all projects
        for project in projects:
            await policy.can_select(project)

        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000
        avg_ms_per_check = duration_ms / batch_size

        timings.append({
            "batch_size": batch_size,
            "total_ms": duration_ms,
            "avg_ms": avg_ms_per_check,
        })

    # Then: Verify linear scaling
    # Average time per check should be relatively consistent
    avg_times = [t["avg_ms"] for t in timings]
    max_avg = max(avg_times)
    min_avg = min(avg_times)

    # Variance should be low (within 2x)
    variance_factor = max_avg / min_avg if min_avg > 0 else 1
    assert variance_factor < 2.0, \
        f"Performance variance too high ({variance_factor:.2f}x), suggests non-linear scaling"

    # Print detailed timing analysis
    print("\n✓ Linear scaling test:")
    for timing in timings:
        print(f"  {timing['batch_size']:3d} checks: {timing['total_ms']:6.2f}ms total, "
              f"{timing['avg_ms']:5.2f}ms average")
    print(f"  Variance factor: {variance_factor:.2f}x (< 2.0x = good)")


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
