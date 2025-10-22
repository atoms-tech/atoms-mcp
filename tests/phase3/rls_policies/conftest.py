"""
Shared fixtures for RLS policy tests.

Provides common test data, mock database adapters, and helper utilities
for testing Row-Level Security policies.
"""

from typing import Any
from unittest.mock import AsyncMock

import pytest

from schemas import ProjectRole, UserRoleType, Visibility
from schemas.constants import Tables

# =============================================================================
# TEST USER FIXTURES
# =============================================================================


@pytest.fixture
def test_users():
    """Fixture providing a set of test users with different roles."""
    return {
        "owner": {
            "id": "user-owner-001",
            "email": "owner@example.com",
            "full_name": "Test Owner",
        },
        "admin": {
            "id": "user-admin-002",
            "email": "admin@example.com",
            "full_name": "Test Admin",
        },
        "member": {
            "id": "user-member-003",
            "email": "member@example.com",
            "full_name": "Test Member",
        },
        "editor": {
            "id": "user-editor-004",
            "email": "editor@example.com",
            "full_name": "Test Editor",
        },
        "viewer": {
            "id": "user-viewer-005",
            "email": "viewer@example.com",
            "full_name": "Test Viewer",
        },
        "external": {
            "id": "user-external-999",
            "email": "external@example.com",
            "full_name": "External User",
        },
    }


@pytest.fixture
def test_organizations():
    """Fixture providing test organizations."""
    return {
        "org_a": {
            "id": "org-a-001",
            "name": "Organization A",
            "slug": "org-a",
        },
        "org_b": {
            "id": "org-b-002",
            "name": "Organization B",
            "slug": "org-b",
        },
    }


@pytest.fixture
def test_projects():
    """Fixture providing test projects."""
    return {
        "private_project": {
            "id": "project-private-001",
            "name": "Private Project",
            "visibility": Visibility.PRIVATE.value,
            "organization_id": "org-a-001",
        },
        "public_project": {
            "id": "project-public-002",
            "name": "Public Project",
            "visibility": Visibility.PUBLIC.value,
            "organization_id": "org-a-001",
        },
    }


# =============================================================================
# DATABASE ADAPTER FIXTURES
# =============================================================================


@pytest.fixture
def mock_db_adapter():
    """
    Create a mock database adapter with standard async methods.

    This is the base mock - individual tests can customize behavior
    via side_effect or return_value overrides.
    """
    mock = AsyncMock()
    mock.get_single = AsyncMock()
    mock.query = AsyncMock()
    mock.insert = AsyncMock()
    mock.update = AsyncMock()
    mock.delete = AsyncMock()
    return mock


@pytest.fixture
def configured_db_adapter(test_users, test_organizations, test_projects):
    """
    Pre-configured database adapter with test data.

    Simulates a database with:
    - Organization A: owner, admin, member, editor, viewer
    - Organization B: external user only
    - Private project in org A
    - Public project in org A
    """
    mock = AsyncMock()

    # Database state
    org_memberships = [
        # Org A members
        {
            "id": "orgmem-001",
            "organization_id": "org-a-001",
            "user_id": "user-owner-001",
            "role": UserRoleType.OWNER.value,
            "is_deleted": False,
        },
        {
            "id": "orgmem-002",
            "organization_id": "org-a-001",
            "user_id": "user-admin-002",
            "role": UserRoleType.ADMIN.value,
            "is_deleted": False,
        },
        {
            "id": "orgmem-003",
            "organization_id": "org-a-001",
            "user_id": "user-member-003",
            "role": UserRoleType.MEMBER.value,
            "is_deleted": False,
        },
        # Org B members
        {
            "id": "orgmem-004",
            "organization_id": "org-b-002",
            "user_id": "user-external-999",
            "role": UserRoleType.MEMBER.value,
            "is_deleted": False,
        },
    ]

    project_memberships = [
        # Private project members
        {
            "id": "projmem-001",
            "project_id": "project-private-001",
            "user_id": "user-owner-001",
            "role": ProjectRole.OWNER.value,
            "is_deleted": False,
        },
        {
            "id": "projmem-002",
            "project_id": "project-private-001",
            "user_id": "user-editor-004",
            "role": ProjectRole.EDITOR.value,
            "is_deleted": False,
        },
        {
            "id": "projmem-003",
            "project_id": "project-private-001",
            "user_id": "user-viewer-005",
            "role": ProjectRole.VIEWER.value,
            "is_deleted": False,
        },
    ]

    def mock_get_single(table: str, filters: dict[str, Any]) -> dict[str, Any] | None:
        """Simulate get_single queries."""
        if table == Tables.ORGANIZATION_MEMBERS:
            for member in org_memberships:
                if all(member.get(k) == v for k, v in filters.items()):
                    return member
            return None

        if table == Tables.PROJECT_MEMBERS:
            for member in project_memberships:
                if all(member.get(k) == v for k, v in filters.items()):
                    return member
            return None

        if table == Tables.PROJECTS:
            project_id = filters.get("id")
            for proj_key, proj_data in test_projects.items():
                if proj_data["id"] == project_id:
                    return {**proj_data, "is_deleted": False}
            return None

        return None

    def mock_query(table: str, filters: dict[str, Any] = None) -> list[dict[str, Any]]:
        """Simulate query (returns multiple records)."""
        filters = filters or {}

        if table == Tables.ORGANIZATION_MEMBERS:
            results = []
            for member in org_memberships:
                if all(member.get(k) == v for k, v in filters.items()):
                    results.append(member)
            return results

        if table == Tables.PROJECT_MEMBERS:
            results = []
            for member in project_memberships:
                if all(member.get(k) == v for k, v in filters.items()):
                    results.append(member)
            return results

        return []

    mock.get_single = AsyncMock(side_effect=mock_get_single)
    mock.query = AsyncMock(side_effect=mock_query)

    return mock


# =============================================================================
# HELPER UTILITIES
# =============================================================================


@pytest.fixture
def make_membership():
    """Factory fixture for creating membership records."""
    def _make_membership(
        user_id: str,
        org_id: str = None,
        project_id: str = None,
        role: str = None,
        is_deleted: bool = False,
    ) -> dict[str, Any]:
        """Create a membership record."""
        membership = {
            "user_id": user_id,
            "is_deleted": is_deleted,
        }

        if org_id:
            membership["organization_id"] = org_id
            membership["role"] = role or UserRoleType.MEMBER.value
            membership["id"] = f"orgmem-{user_id}"

        if project_id:
            membership["project_id"] = project_id
            membership["role"] = role or ProjectRole.VIEWER.value
            membership["id"] = f"projmem-{user_id}"

        return membership

    return _make_membership


@pytest.fixture
def assert_policy_enforced():
    """Helper for asserting policy enforcement."""
    async def _assert_enforced(policy, record, expected_access: bool, operation: str = "select"):
        """
        Assert that a policy enforces expected access control.

        Args:
            policy: Policy instance
            record: Record to check
            expected_access: Expected access result (True/False)
            operation: Operation type (select, insert, update, delete)
        """
        if operation == "select":
            result = await policy.can_select(record)
        elif operation == "insert":
            result = await policy.can_insert(record)
        elif operation == "update":
            result = await policy.can_update(record, {})
        elif operation == "delete":
            result = await policy.can_delete(record)
        else:
            raise ValueError(f"Unknown operation: {operation}")

        assert result == expected_access, \
            f"Expected {operation} access to be {expected_access}, got {result}"

    return _assert_enforced


# =============================================================================
# CLEANUP FIXTURES
# =============================================================================


@pytest.fixture
def cleanup_test_data():
    """
    Cleanup fixture for removing test data after tests.

    Use with @pytest.mark.harmful decorator for tests that create data.
    """
    created_records = []

    def _register_cleanup(table: str, record_id: str):
        """Register a record for cleanup."""
        created_records.append((table, record_id))

    yield _register_cleanup

    # Cleanup happens automatically after test
    # In real implementation, would delete from database
    # For unit tests with mocks, this is mostly documentation
    if created_records:
        print(f"\n🧹 Would cleanup {len(created_records)} test records")


# =============================================================================
# PERFORMANCE TESTING FIXTURES
# =============================================================================


@pytest.fixture
def performance_db_adapter():
    """
    Mock database adapter with realistic timing for performance tests.

    Simulates 1-2ms database query latency.
    """
    import asyncio

    mock = AsyncMock()

    async def mock_get_single_with_delay(*args, **kwargs):
        await asyncio.sleep(0.001)  # 1ms delay
        return {
            "id": "member-001",
            "user_id": "user-test-001",
            "role": UserRoleType.MEMBER.value,
            "is_deleted": False,
        }

    async def mock_query_with_delay(*args, **kwargs):
        await asyncio.sleep(0.0015)  # 1.5ms delay
        return [
            {"id": "member-001", "organization_id": "org-001"},
        ]

    mock.get_single = AsyncMock(side_effect=mock_get_single_with_delay)
    mock.query = AsyncMock(side_effect=mock_query_with_delay)

    return mock


# =============================================================================
# MARKERS
# =============================================================================

def pytest_configure(config):
    """Register custom markers for RLS tests."""
    config.addinivalue_line(
        "markers",
        "harmful: marks tests that modify data (requires cleanup)"
    )
    config.addinivalue_line(
        "markers",
        "performance: marks performance tests (may be slower)"
    )
    config.addinivalue_line(
        "markers",
        "security: marks security-critical tests"
    )
