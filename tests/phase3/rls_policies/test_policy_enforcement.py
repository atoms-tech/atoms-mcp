"""
Test RLS Policy Enforcement (10 tests)

Tests that Row-Level Security policies are correctly enforced at the database level.
Validates policy variables, row-level filtering, and policy logic correctness.

Run with: pytest tests/phase3/rls_policies/test_policy_enforcement.py -v
"""

from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta
import pytest

from schemas import ProjectRole, UserRoleType, Visibility
from schemas.constants import Tables
from schemas.rls import (
    DocumentPolicy,
    OrganizationPolicy,
    PermissionDeniedError,
    PolicyValidator,
    ProfilePolicy,
    ProjectPolicy,
    get_user_organization_ids,
    is_project_owner_or_admin,
    is_super_admin,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_db_adapter():
    """Create mock database adapter with proper async support."""
    mock = AsyncMock()
    mock.get_single = AsyncMock()
    mock.query = AsyncMock()
    return mock


@pytest.fixture
def test_user_id():
    """Primary test user ID."""
    return "user-test-001"


@pytest.fixture
def test_org_id():
    """Primary test organization ID."""
    return "org-test-001"


@pytest.fixture
def test_project_id():
    """Primary test project ID."""
    return "project-test-001"


# =============================================================================
# POLICY ENFORCEMENT TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_organization_select_policy_enforces_membership(
    mock_db_adapter, test_user_id, test_org_id
):
    """
    Given a user who is a member of an organization
    When the SELECT policy is evaluated
    Then access is granted

    Tests that the organization SELECT policy correctly checks membership.
    """
    policy = OrganizationPolicy(test_user_id, mock_db_adapter)

    # Setup: User is organization member
    mock_db_adapter.get_single.return_value = {
        "id": "member-001",
        "organization_id": test_org_id,
        "user_id": test_user_id,
        "role": UserRoleType.MEMBER.value,
        "is_deleted": False,
    }

    # When: Check SELECT permission
    can_read = await policy.can_select({"id": test_org_id})

    # Then: Access granted
    assert can_read is True, "Organization member should have SELECT access"

    # Verify: Correct query was made
    mock_db_adapter.get_single.assert_called_once_with(
        Tables.ORGANIZATION_MEMBERS,
        filters={
            "organization_id": test_org_id,
            "user_id": test_user_id,
            "is_deleted": False,
        }
    )


@pytest.mark.asyncio
async def test_organization_select_policy_denies_non_member(
    mock_db_adapter, test_user_id, test_org_id
):
    """
    Given a user who is NOT a member of an organization
    When the SELECT policy is evaluated
    Then access is denied

    Tests row-level filtering for non-members.
    """
    policy = OrganizationPolicy(test_user_id, mock_db_adapter)

    # Setup: User is NOT a member
    mock_db_adapter.get_single.return_value = None

    # When: Check SELECT permission
    can_read = await policy.can_select({"id": test_org_id})

    # Then: Access denied
    assert can_read is False, "Non-member should not have SELECT access"


@pytest.mark.asyncio
async def test_project_select_policy_uses_current_user_id_variable(
    mock_db_adapter, test_user_id, test_project_id
):
    """
    Given a project with specific members
    When the SELECT policy is evaluated
    Then it correctly uses the current_user_id policy variable

    Tests that policy variables (current_user_id) work correctly.
    """
    policy = ProjectPolicy(test_user_id, mock_db_adapter)

    # Setup: User is project member (simulates auth.uid() = current_user_id)
    mock_db_adapter.get_single.return_value = {
        "id": "member-001",
        "project_id": test_project_id,
        "user_id": test_user_id,  # This should match auth.uid()
        "role": ProjectRole.VIEWER.value,
        "is_deleted": False,
    }

    # When: Check SELECT permission
    can_read = await policy.can_select({"id": test_project_id})

    # Then: Access granted based on current_user_id
    assert can_read is True, "Policy should use current_user_id correctly"


@pytest.mark.asyncio
async def test_project_policy_filters_by_org_id_variable(
    mock_db_adapter, test_user_id, test_org_id
):
    """
    Given a user creating a project in an organization
    When the INSERT policy is evaluated
    Then it correctly validates organization membership using org_id variable

    Tests that org_id policy variable is properly enforced.
    """
    policy = ProjectPolicy(test_user_id, mock_db_adapter)

    # Setup: User is org member
    mock_db_adapter.get_single.return_value = {
        "id": "member-001",
        "organization_id": test_org_id,
        "user_id": test_user_id,
        "is_deleted": False,
    }

    # When: Check INSERT permission with org_id
    can_create = await policy.can_insert({
        "organization_id": test_org_id,
        "name": "New Project",
    })

    # Then: Access granted based on org membership
    assert can_create is True, "Policy should validate org_id correctly"

    # Verify: Correct filter used
    mock_db_adapter.get_single.assert_called_once_with(
        Tables.ORGANIZATION_MEMBERS,
        filters={
            "organization_id": test_org_id,
            "user_id": test_user_id,
            "is_deleted": False,
        }
    )


@pytest.mark.asyncio
async def test_document_policy_enforces_row_level_filtering(
    mock_db_adapter, test_user_id, test_project_id
):
    """
    Given multiple documents in different projects
    When SELECT policies are evaluated
    Then only documents in accessible projects are visible

    Tests row-level filtering based on project access.
    """
    policy = DocumentPolicy(test_user_id, mock_db_adapter)

    # Setup: User can access project-001 but not project-002
    def mock_get_single(table, filters):
        if filters.get("project_id") == test_project_id:
            return {
                "id": "member-001",
                "project_id": test_project_id,
                "user_id": test_user_id,
                "is_deleted": False,
            }
        return None

    mock_db_adapter.get_single.side_effect = mock_get_single

    # When: Check access to document in accessible project
    can_read_allowed = await policy.can_select({
        "id": "doc-001",
        "project_id": test_project_id,
    })

    # Then: Access granted
    assert can_read_allowed is True, "Should access document in accessible project"

    # When: Check access to document in inaccessible project
    can_read_denied = await policy.can_select({
        "id": "doc-002",
        "project_id": "project-999-unauthorized",
    })

    # Then: Access denied
    assert can_read_denied is False, "Should not access document in inaccessible project"


@pytest.mark.asyncio
async def test_policy_validator_routes_to_correct_table_policy(
    mock_db_adapter, test_user_id, test_org_id
):
    """
    Given a PolicyValidator instance
    When checking permissions for different tables
    Then it routes to the correct table-specific policy

    Tests that the validator correctly dispatches to table policies.
    """
    validator = PolicyValidator(test_user_id, mock_db_adapter)

    # Setup: User is org member
    mock_db_adapter.get_single.return_value = {
        "id": "member-001",
        "organization_id": test_org_id,
        "user_id": test_user_id,
        "is_deleted": False,
    }

    # When: Check SELECT on organizations table
    can_read_org = await validator.can_select(
        Tables.ORGANIZATIONS,
        {"id": test_org_id}
    )

    # Then: Routes to OrganizationPolicy
    assert can_read_org is True, "Should route to OrganizationPolicy"

    # When: Check on unsupported table
    can_read_unknown = await validator.can_select(
        "unknown_table",
        {"id": "test-001"}
    )

    # Then: Denies by default
    assert can_read_unknown is False, "Should deny access to unknown tables"


@pytest.mark.asyncio
async def test_profile_policy_allows_all_authenticated_users_to_read(
    mock_db_adapter, test_user_id
):
    """
    Given any authenticated user
    When reading any profile
    Then access is always granted

    Tests that profile SELECT policy allows all authenticated reads.
    """
    policy = ProfilePolicy(test_user_id, mock_db_adapter)

    # When: Read own profile
    can_read_own = await policy.can_select({"id": test_user_id})

    # Then: Access granted
    assert can_read_own is True, "Should read own profile"

    # When: Read other user's profile
    can_read_other = await policy.can_select({"id": "user-other-999"})

    # Then: Access granted (profiles are publicly readable for collaboration)
    assert can_read_other is True, "Should read other profiles"


@pytest.mark.asyncio
async def test_project_update_policy_enforces_admin_role(
    mock_db_adapter, test_user_id, test_project_id
):
    """
    Given users with different project roles
    When UPDATE policy is evaluated
    Then only owners and admins can update

    Tests role-based UPDATE policy enforcement.
    """
    policy = ProjectPolicy(test_user_id, mock_db_adapter)

    # Test: Owner can update
    mock_db_adapter.get_single.return_value = {
        "id": "member-001",
        "project_id": test_project_id,
        "user_id": test_user_id,
        "role": ProjectRole.OWNER.value,
        "is_deleted": False,
    }

    can_update_owner = await policy.can_update(
        {"id": test_project_id},
        {"name": "Updated Name"}
    )
    assert can_update_owner is True, "Owner should update project"

    # Test: Admin can update
    mock_db_adapter.get_single.return_value = {
        "id": "member-002",
        "project_id": test_project_id,
        "user_id": test_user_id,
        "role": ProjectRole.ADMIN.value,
        "is_deleted": False,
    }

    can_update_admin = await policy.can_update(
        {"id": test_project_id},
        {"name": "Updated Name"}
    )
    assert can_update_admin is True, "Admin should update project"

    # Test: Editor cannot update
    mock_db_adapter.get_single.return_value = {
        "id": "member-003",
        "project_id": test_project_id,
        "user_id": test_user_id,
        "role": ProjectRole.EDITOR.value,
        "is_deleted": False,
    }

    can_update_editor = await policy.can_update(
        {"id": test_project_id},
        {"name": "Updated Name"}
    )
    assert can_update_editor is False, "Editor should not update project"


@pytest.mark.asyncio
async def test_organization_delete_policy_restricts_to_owner_only(
    mock_db_adapter, test_user_id, test_org_id
):
    """
    Given users with different organization roles
    When DELETE policy is evaluated
    Then only the owner can delete

    Tests strict DELETE policy for organization ownership.
    """
    policy = OrganizationPolicy(test_user_id, mock_db_adapter)

    # Test: Owner can delete
    mock_db_adapter.get_single.return_value = {
        "id": "member-001",
        "organization_id": test_org_id,
        "user_id": test_user_id,
        "role": UserRoleType.OWNER.value,
        "is_deleted": False,
    }

    can_delete_owner = await policy.can_delete({"id": test_org_id})
    assert can_delete_owner is True, "Owner should delete organization"

    # Test: Admin cannot delete
    mock_db_adapter.get_single.return_value = {
        "id": "member-002",
        "organization_id": test_org_id,
        "user_id": test_user_id,
        "role": UserRoleType.ADMIN.value,
        "is_deleted": False,
    }

    can_delete_admin = await policy.can_delete({"id": test_org_id})
    assert can_delete_admin is False, "Admin should not delete organization"


@pytest.mark.asyncio
async def test_validate_methods_raise_permission_denied_error(
    mock_db_adapter, test_user_id, test_org_id
):
    """
    Given a policy check that fails
    When using validate_* methods
    Then PermissionDeniedError is raised with correct details

    Tests error handling and error message quality.
    """
    policy = OrganizationPolicy(test_user_id, mock_db_adapter)

    # Setup: User is not a member
    mock_db_adapter.get_single.return_value = None

    # When/Then: validate_select raises PermissionDeniedError
    with pytest.raises(PermissionDeniedError) as exc_info:
        await policy.validate_select({"id": test_org_id})

    error = exc_info.value
    assert error.operation == "SELECT", "Error should specify SELECT operation"
    assert "Organization" in error.table, "Error should specify table"
    assert "does not have read access" in error.reason, "Error should have clear reason"

    # Verify error message is informative
    error_msg = str(error)
    assert "Permission denied" in error_msg
    assert "SELECT" in error_msg
    assert "Organization" in error_msg


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
