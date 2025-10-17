"""
Test RLS Policy Edge Cases (8 tests)

Tests edge cases and security scenarios:
- Null/missing owner scenarios
- Deleted user access
- Suspended user access
- Permission escalation attempts

Run with: pytest tests/phase3/rls_policies/test_edge_cases.py -v
"""

from unittest.mock import AsyncMock
import pytest

from schemas import ProjectRole, UserRoleType
from schemas.constants import Tables
from schemas.rls import (
    DocumentPolicy,
    OrganizationMemberPolicy,
    OrganizationPolicy,
    ProfilePolicy,
    ProjectMemberPolicy,
    ProjectPolicy,
    is_organization_owner_or_admin,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_db_adapter():
    """Create mock database adapter."""
    mock = AsyncMock()
    mock.get_single = AsyncMock()
    mock.query = AsyncMock()
    return mock


@pytest.fixture
def test_user_id():
    """Test user ID."""
    return "user-test-001"


@pytest.fixture
def deleted_user_id():
    """Deleted user ID."""
    return "user-deleted-999"


@pytest.fixture
def test_org_id():
    """Test organization ID."""
    return "org-test-001"


@pytest.fixture
def test_project_id():
    """Test project ID."""
    return "project-test-001"


# =============================================================================
# NULL/MISSING OWNER SCENARIOS
# =============================================================================


@pytest.mark.asyncio
async def test_null_organization_id_denies_access(
    mock_db_adapter, test_user_id
):
    """
    Given a record with null/missing organization_id
    When checking access policies
    Then access is denied

    Tests that null IDs are handled safely without errors.
    """
    policy = OrganizationPolicy(test_user_id, mock_db_adapter)

    # When: Check access with null ID
    can_read_null = await policy.can_select({"id": None})

    # Then: Access denied safely
    assert can_read_null is False, "Null org ID should deny access"

    # When: Check access with missing ID
    can_read_missing = await policy.can_select({})

    # Then: Access denied safely
    assert can_read_missing is False, "Missing org ID should deny access"


@pytest.mark.asyncio
async def test_null_project_id_in_document_denies_access(
    mock_db_adapter, test_user_id
):
    """
    Given a document with null/missing project_id
    When checking access policies
    Then access is denied

    Tests that orphaned documents are not accessible.
    """
    policy = DocumentPolicy(test_user_id, mock_db_adapter)

    # When: Check access to document with null project_id
    can_read = await policy.can_select({
        "id": "doc-001",
        "project_id": None,
    })

    # Then: Access denied
    assert can_read is False, "Null project_id should deny access"


@pytest.mark.asyncio
async def test_missing_owner_in_organization_prevents_deletion(
    mock_db_adapter, test_user_id, test_org_id
):
    """
    Given an organization with no owner record
    When a user tries to delete it
    Then access is denied

    Tests that missing ownership records prevent dangerous operations.
    """
    policy = OrganizationPolicy(test_user_id, mock_db_adapter)

    # Setup: No membership record found
    mock_db_adapter.get_single.return_value = None

    # When: Try to delete organization
    can_delete = await policy.can_delete({"id": test_org_id})

    # Then: Access denied
    assert can_delete is False, "No owner record should prevent deletion"


# =============================================================================
# DELETED USER ACCESS TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_deleted_user_cannot_access_organization(
    mock_db_adapter, deleted_user_id, test_org_id
):
    """
    Given a user marked as deleted (is_deleted=True)
    When they try to access an organization
    Then access is denied

    Tests that soft-deleted users lose access immediately.
    """
    policy = OrganizationPolicy(deleted_user_id, mock_db_adapter)

    # Setup: User membership exists but is_deleted=True
    mock_db_adapter.get_single.return_value = {
        "id": "member-001",
        "organization_id": test_org_id,
        "user_id": deleted_user_id,
        "role": UserRoleType.MEMBER.value,
        "is_deleted": True,  # User deleted
    }

    # When: Deleted user tries to access
    can_read = await policy.can_select({"id": test_org_id})

    # Then: Access denied (query filters is_deleted=False)
    assert can_read is False, "Deleted user should not access organization"


@pytest.mark.asyncio
async def test_deleted_member_record_denies_project_access(
    mock_db_adapter, test_user_id, test_project_id
):
    """
    Given a deleted project membership record
    When the user tries to access the project
    Then access is denied

    Tests that deleted memberships are properly filtered.
    """
    policy = ProjectPolicy(test_user_id, mock_db_adapter)

    # Setup: Membership record exists but is deleted
    mock_db_adapter.get_single.return_value = {
        "id": "member-001",
        "project_id": test_project_id,
        "user_id": test_user_id,
        "role": ProjectRole.OWNER.value,
        "is_deleted": True,  # Membership deleted
    }

    # When: Try to access project
    can_read = await policy.can_select({"id": test_project_id})

    # Then: Access denied
    assert can_read is False, "Deleted membership should deny access"


# =============================================================================
# SUSPENDED USER ACCESS TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_suspended_user_role_prevents_admin_actions(
    mock_db_adapter, test_user_id, test_org_id
):
    """
    Given a user with suspended status/role
    When they try to perform admin actions
    Then access is denied

    Tests that suspended users cannot perform privileged operations.
    Note: This assumes a SUSPENDED role exists in UserRoleType.
    If not, this tests that non-admin roles can't perform admin actions.
    """
    policy = OrganizationMemberPolicy(test_user_id, mock_db_adapter)

    # Setup: User is suspended or has non-admin role
    mock_db_adapter.get_single.return_value = {
        "id": "member-001",
        "organization_id": test_org_id,
        "user_id": test_user_id,
        "role": UserRoleType.MEMBER.value,  # Not admin
        "is_deleted": False,
    }

    # When: Try to add new member (admin action)
    can_add_member = await policy.can_insert({
        "organization_id": test_org_id,
        "user_id": "user-new-999",
        "role": UserRoleType.MEMBER.value,
    })

    # Then: Access denied
    assert can_add_member is False, "Non-admin should not add members"


# =============================================================================
# PERMISSION ESCALATION ATTEMPTS
# =============================================================================


@pytest.mark.asyncio
async def test_member_cannot_escalate_to_admin_role(
    mock_db_adapter, test_user_id, test_org_id
):
    """
    Given a regular member
    When they try to update their own role to admin
    Then access is denied

    Tests against self-service privilege escalation.
    """
    policy = OrganizationMemberPolicy(test_user_id, mock_db_adapter)

    # Setup: User is regular member (not admin)
    mock_db_adapter.get_single.return_value = {
        "id": "member-001",
        "organization_id": test_org_id,
        "user_id": test_user_id,
        "role": UserRoleType.MEMBER.value,
        "is_deleted": False,
    }

    # When: Try to update membership (requires admin)
    can_update = await policy.can_update(
        {
            "id": "member-001",
            "organization_id": test_org_id,
            "user_id": test_user_id,
            "role": UserRoleType.MEMBER.value,
        },
        {"role": UserRoleType.ADMIN.value}  # Trying to escalate
    )

    # Then: Access denied (is_organization_owner_or_admin returns False)
    assert can_update is False, "Member should not escalate privileges"


@pytest.mark.asyncio
async def test_editor_cannot_grant_admin_role_to_others(
    mock_db_adapter, test_user_id, test_project_id
):
    """
    Given a project editor
    When they try to add a new admin member
    Then access is denied

    Tests that only owners/admins can grant admin roles.
    """
    policy = ProjectMemberPolicy(test_user_id, mock_db_adapter)

    # Setup: User is editor (not admin/owner)
    mock_db_adapter.get_single.return_value = {
        "id": "member-001",
        "project_id": test_project_id,
        "user_id": test_user_id,
        "role": ProjectRole.EDITOR.value,
        "is_deleted": False,
    }

    # When: Try to add admin member
    can_add_admin = await policy.can_insert({
        "project_id": test_project_id,
        "user_id": "user-new-999",
        "role": ProjectRole.ADMIN.value,
    })

    # Then: Access denied
    assert can_add_admin is False, "Editor should not add admins"


@pytest.mark.asyncio
async def test_profile_update_restricted_to_own_profile(
    mock_db_adapter, test_user_id
):
    """
    Given any user
    When they try to update another user's profile
    Then access is denied

    Tests against profile takeover/modification attacks.
    """
    policy = ProfilePolicy(test_user_id, mock_db_adapter)

    # When: Try to update another user's profile
    can_update_other = await policy.can_update(
        {"id": "user-other-999"},  # Different user
        {"full_name": "Hacked Name"}
    )

    # Then: Access denied
    assert can_update_other is False, "Should not update other profiles"

    # When: Update own profile
    can_update_own = await policy.can_update(
        {"id": test_user_id},  # Own profile
        {"full_name": "Updated Name"}
    )

    # Then: Access granted
    assert can_update_own is True, "Should update own profile"


# =============================================================================
# ADDITIONAL EDGE CASES
# =============================================================================


@pytest.mark.asyncio
async def test_empty_user_id_denies_all_access(mock_db_adapter):
    """
    Given an empty or invalid user_id
    When checking any policy
    Then access is denied

    Tests that unauthenticated/invalid requests are rejected.
    """
    # Test with empty string
    policy_empty = OrganizationPolicy("", mock_db_adapter)
    can_read_empty = await policy_empty.can_select({"id": "org-001"})
    assert can_read_empty is False, "Empty user_id should deny access"

    # Test with None (if accidentally passed)
    # Note: This might raise an error in real implementation,
    # but policy should handle gracefully
    try:
        policy_none = OrganizationPolicy(None, mock_db_adapter)
        can_read_none = await policy_none.can_select({"id": "org-001"})
        assert can_read_none is False, "None user_id should deny access"
    except (TypeError, AttributeError):
        # Expected - None is invalid user_id
        pass


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
