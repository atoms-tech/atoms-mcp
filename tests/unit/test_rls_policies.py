"""
Unit tests for RLS policy validators.

Tests the Python implementations of Row-Level Security policies
to ensure they correctly replicate database RLS behavior.
"""

import pytest
from unittest.mock import AsyncMock

from schemas.rls import (
    PolicyValidator,
    PermissionDeniedError,
    OrganizationPolicy,
    ProjectPolicy,
    DocumentPolicy,
    ProfilePolicy,
    user_can_access_project,
    is_project_owner_or_admin,
    is_super_admin,
    get_user_organization_ids,
)
# Import from generated schemas
from schemas import UserRoleType, ProjectRole, Visibility
from schemas.constants import Tables


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
def user_id():
    """Test user ID."""
    return "user-123"


@pytest.fixture
def other_user_id():
    """Another user ID for testing."""
    return "user-456"


# =============================================================================
# HELPER FUNCTION TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_user_can_access_project_as_member(mock_db_adapter, user_id):
    """Test user can access project as direct member."""
    project_id = "project-123"

    # User is project member
    mock_db_adapter.get_single.return_value = {
        "id": "member-1",
        "project_id": project_id,
        "user_id": user_id,
        "role": "editor"
    }

    result = await user_can_access_project(project_id, user_id, mock_db_adapter)

    assert result is True
    mock_db_adapter.get_single.assert_called_once()


@pytest.mark.asyncio
async def test_user_can_access_public_project(mock_db_adapter, user_id):
    """Test user can access public project."""
    project_id = "project-123"

    # Not a project member
    mock_db_adapter.get_single.side_effect = [
        None,  # No project membership
        {  # But project is public
            "id": project_id,
            "visibility": Visibility.PUBLIC.value,
            "organization_id": "org-123"
        }
    ]

    result = await user_can_access_project(project_id, user_id, mock_db_adapter)

    assert result is True


@pytest.mark.asyncio
async def test_user_can_access_project_via_org(mock_db_adapter, user_id):
    """Test user can access project via organization membership."""
    project_id = "project-123"
    org_id = "org-123"

    mock_db_adapter.get_single.side_effect = [
        None,  # Not a project member
        {"id": project_id, "visibility": "private", "organization_id": org_id},  # Private project
        {"id": "member-1", "organization_id": org_id, "user_id": user_id}  # But org member
    ]

    result = await user_can_access_project(project_id, user_id, mock_db_adapter)

    assert result is True


@pytest.mark.asyncio
async def test_is_project_owner_or_admin_owner(mock_db_adapter, user_id):
    """Test project owner detection."""
    project_id = "project-123"

    mock_db_adapter.get_single.return_value = {
        "id": "member-1",
        "project_id": project_id,
        "user_id": user_id,
        "role": ProjectRole.OWNER.value
    }

    result = await is_project_owner_or_admin(project_id, user_id, mock_db_adapter)

    assert result is True


@pytest.mark.asyncio
async def test_is_project_owner_or_admin_editor(mock_db_adapter, user_id):
    """Test editor is not considered owner/admin."""
    project_id = "project-123"

    mock_db_adapter.get_single.return_value = {
        "id": "member-1",
        "project_id": project_id,
        "user_id": user_id,
        "role": ProjectRole.EDITOR.value
    }

    result = await is_project_owner_or_admin(project_id, user_id, mock_db_adapter)

    assert result is False


@pytest.mark.asyncio
async def test_is_super_admin_true(mock_db_adapter, user_id):
    """Test super admin detection."""
    mock_db_adapter.get_single.return_value = {
        "id": "member-1",
        "user_id": user_id,
        "role": UserRoleType.SUPER_ADMIN.value
    }

    result = await is_super_admin(user_id, mock_db_adapter)

    assert result is True


@pytest.mark.asyncio
async def test_is_super_admin_false(mock_db_adapter, user_id):
    """Test non-super admin detection."""
    mock_db_adapter.get_single.return_value = None

    result = await is_super_admin(user_id, mock_db_adapter)

    assert result is False


@pytest.mark.asyncio
async def test_get_user_organization_ids(mock_db_adapter, user_id):
    """Test getting user's organization IDs."""
    mock_db_adapter.query.return_value = [
        {"id": "member-1", "organization_id": "org-1", "user_id": user_id},
        {"id": "member-2", "organization_id": "org-2", "user_id": user_id}
    ]

    result = await get_user_organization_ids(user_id, mock_db_adapter)

    assert result == ["org-1", "org-2"]


# =============================================================================
# ORGANIZATION POLICY TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_organization_policy_can_select_member(mock_db_adapter, user_id):
    """Test organization member can read organization."""
    policy = OrganizationPolicy(user_id, mock_db_adapter)

    mock_db_adapter.get_single.return_value = {
        "id": "member-1",
        "organization_id": "org-123",
        "user_id": user_id
    }

    result = await policy.can_select({"id": "org-123"})

    assert result is True


@pytest.mark.asyncio
async def test_organization_policy_can_select_non_member(mock_db_adapter, user_id):
    """Test non-member cannot read organization."""
    policy = OrganizationPolicy(user_id, mock_db_adapter)

    mock_db_adapter.get_single.return_value = None

    result = await policy.can_select({"id": "org-123"})

    assert result is False


@pytest.mark.asyncio
async def test_organization_policy_can_insert(mock_db_adapter, user_id):
    """Test authenticated user can create organization."""
    policy = OrganizationPolicy(user_id, mock_db_adapter)

    result = await policy.can_insert({"name": "New Org", "slug": "new-org"})

    assert result is True


@pytest.mark.asyncio
async def test_organization_policy_can_update_admin(mock_db_adapter, user_id):
    """Test organization admin can update."""
    policy = OrganizationPolicy(user_id, mock_db_adapter)

    mock_db_adapter.get_single.return_value = {
        "id": "member-1",
        "organization_id": "org-123",
        "user_id": user_id,
        "role": UserRoleType.ADMIN.value
    }

    result = await policy.can_update({"id": "org-123"}, {"name": "Updated"})

    assert result is True


@pytest.mark.asyncio
async def test_organization_policy_can_delete_owner_only(mock_db_adapter, user_id):
    """Test only owner can delete organization."""
    policy = OrganizationPolicy(user_id, mock_db_adapter)

    # Admin cannot delete
    mock_db_adapter.get_single.return_value = {
        "id": "member-1",
        "organization_id": "org-123",
        "user_id": user_id,
        "role": UserRoleType.ADMIN.value
    }

    result = await policy.can_delete({"id": "org-123"})
    assert result is False

    # Owner can delete
    mock_db_adapter.get_single.return_value = {
        "id": "member-1",
        "organization_id": "org-123",
        "user_id": user_id,
        "role": UserRoleType.OWNER.value
    }

    result = await policy.can_delete({"id": "org-123"})
    assert result is True


# =============================================================================
# PROJECT POLICY TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_project_policy_can_select(mock_db_adapter, user_id):
    """Test project member can read project."""
    policy = ProjectPolicy(user_id, mock_db_adapter)

    mock_db_adapter.get_single.return_value = {
        "id": "member-1",
        "project_id": "project-123",
        "user_id": user_id
    }

    result = await policy.can_select({"id": "project-123"})

    assert result is True


@pytest.mark.asyncio
async def test_project_policy_can_insert_org_member(mock_db_adapter, user_id):
    """Test org member can create project."""
    policy = ProjectPolicy(user_id, mock_db_adapter)

    mock_db_adapter.get_single.return_value = {
        "id": "member-1",
        "organization_id": "org-123",
        "user_id": user_id
    }

    result = await policy.can_insert({"organization_id": "org-123", "name": "New Project"})

    assert result is True


@pytest.mark.asyncio
async def test_project_policy_can_insert_non_org_member(mock_db_adapter, user_id):
    """Test non-org member cannot create project."""
    policy = ProjectPolicy(user_id, mock_db_adapter)

    mock_db_adapter.get_single.return_value = None

    result = await policy.can_insert({"organization_id": "org-123", "name": "New Project"})

    assert result is False


# =============================================================================
# DOCUMENT POLICY TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_document_policy_can_select(mock_db_adapter, user_id):
    """Test user can read document if can access project."""
    policy = DocumentPolicy(user_id, mock_db_adapter)

    # User is project member
    mock_db_adapter.get_single.return_value = {
        "id": "member-1",
        "project_id": "project-123",
        "user_id": user_id
    }

    result = await policy.can_select({"id": "doc-123", "project_id": "project-123"})

    assert result is True


@pytest.mark.asyncio
async def test_document_policy_can_insert_editor(mock_db_adapter, user_id):
    """Test editor can create document."""
    policy = DocumentPolicy(user_id, mock_db_adapter)

    mock_db_adapter.get_single.return_value = {
        "id": "member-1",
        "project_id": "project-123",
        "user_id": user_id,
        "role": ProjectRole.EDITOR.value
    }

    result = await policy.can_insert({"project_id": "project-123", "name": "New Doc"})

    assert result is True


@pytest.mark.asyncio
async def test_document_policy_can_insert_viewer(mock_db_adapter, user_id):
    """Test viewer cannot create document."""
    policy = DocumentPolicy(user_id, mock_db_adapter)

    mock_db_adapter.get_single.return_value = {
        "id": "member-1",
        "project_id": "project-123",
        "user_id": user_id,
        "role": ProjectRole.VIEWER.value
    }

    result = await policy.can_insert({"project_id": "project-123", "name": "New Doc"})

    assert result is False


# =============================================================================
# PROFILE POLICY TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_profile_policy_can_select(mock_db_adapter, user_id):
    """Test all authenticated users can read profiles."""
    policy = ProfilePolicy(user_id, mock_db_adapter)

    result = await policy.can_select({"id": "other-user-123"})

    assert result is True


@pytest.mark.asyncio
async def test_profile_policy_can_update_own(mock_db_adapter, user_id):
    """Test user can update own profile."""
    policy = ProfilePolicy(user_id, mock_db_adapter)

    result = await policy.can_update({"id": user_id}, {"full_name": "New Name"})

    assert result is True


@pytest.mark.asyncio
async def test_profile_policy_cannot_update_other(mock_db_adapter, user_id, other_user_id):
    """Test user cannot update other's profile."""
    policy = ProfilePolicy(user_id, mock_db_adapter)

    result = await policy.can_update({"id": other_user_id}, {"full_name": "New Name"})

    assert result is False


# =============================================================================
# POLICY VALIDATOR TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_policy_validator_can_select(mock_db_adapter, user_id):
    """Test PolicyValidator.can_select routes to correct policy."""
    validator = PolicyValidator(user_id, mock_db_adapter)

    mock_db_adapter.get_single.return_value = {
        "id": "member-1",
        "organization_id": "org-123",
        "user_id": user_id
    }

    result = await validator.can_select(Tables.ORGANIZATIONS, {"id": "org-123"})

    assert result is True


@pytest.mark.asyncio
async def test_permission_denied_error():
    """Test PermissionDeniedError contains useful information."""
    error = PermissionDeniedError("organizations", "DELETE", "Not organization owner")

    assert error.table == "organizations"
    assert error.operation == "DELETE"
    assert error.reason == "Not organization owner"
    assert "Permission denied" in str(error)
    assert "DELETE" in str(error)
    assert "organizations" in str(error)


@pytest.mark.asyncio
async def test_validate_methods_raise_on_denial(mock_db_adapter, user_id):
    """Test validate_* methods raise PermissionDeniedError."""
    policy = OrganizationPolicy(user_id, mock_db_adapter)

    # User is not a member
    mock_db_adapter.get_single.return_value = None

    with pytest.raises(PermissionDeniedError) as exc_info:
        await policy.validate_select({"id": "org-123"})

    assert exc_info.value.operation == "SELECT"


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_full_permission_flow(mock_db_adapter, user_id):
    """Test complete permission flow for document creation."""
    # Setup: User is editor in project
    mock_db_adapter.get_single.return_value = {
        "id": "member-1",
        "project_id": "project-123",
        "user_id": user_id,
        "role": ProjectRole.EDITOR.value
    }

    # Check permission
    doc_policy = DocumentPolicy(user_id, mock_db_adapter)
    can_create = await doc_policy.can_insert({
        "project_id": "project-123",
        "name": "New Document"
    })

    assert can_create is True

    # Validate (should not raise)
    await doc_policy.validate_insert({
        "project_id": "project-123",
        "name": "New Document"
    })


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
