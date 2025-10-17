"""
Test Access Control Scenarios (12 tests)

Tests real-world access control scenarios:
- Owner access to own records
- Workspace member access
- Organization member access
- Cross-org/workspace access denial

Run with: pytest tests/phase3/rls_policies/test_access_control.py -v
"""

from unittest.mock import AsyncMock
import pytest

from schemas import ProjectRole, UserRoleType, Visibility
from schemas.constants import Tables
from schemas.rls import (
    DocumentPolicy,
    OrganizationMemberPolicy,
    OrganizationPolicy,
    ProjectMemberPolicy,
    ProjectPolicy,
    user_can_access_project,
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
def owner_user_id():
    """Organization/project owner user ID."""
    return "user-owner-001"


@pytest.fixture
def member_user_id():
    """Regular member user ID."""
    return "user-member-002"


@pytest.fixture
def external_user_id():
    """External user (not a member) ID."""
    return "user-external-999"


@pytest.fixture
def org_a_id():
    """Organization A ID."""
    return "org-a-001"


@pytest.fixture
def org_b_id():
    """Organization B ID."""
    return "org-b-002"


@pytest.fixture
def project_a_id():
    """Project A ID (in org A)."""
    return "project-a-001"


@pytest.fixture
def project_b_id():
    """Project B ID (in org B)."""
    return "project-b-002"


# =============================================================================
# OWNER ACCESS TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_owner_can_read_own_organization(
    mock_db_adapter, owner_user_id, org_a_id
):
    """
    Given a user who owns an organization
    When they try to read it
    Then access is granted

    Tests owner can access their own organization records.
    """
    policy = OrganizationPolicy(owner_user_id, mock_db_adapter)

    # Setup: User is owner
    mock_db_adapter.get_single.return_value = {
        "id": "member-001",
        "organization_id": org_a_id,
        "user_id": owner_user_id,
        "role": UserRoleType.OWNER.value,
        "is_deleted": False,
    }

    # When: Owner reads organization
    can_read = await policy.can_select({"id": org_a_id})

    # Then: Access granted
    assert can_read is True, "Owner should read their organization"


@pytest.mark.asyncio
async def test_owner_can_update_own_organization(
    mock_db_adapter, owner_user_id, org_a_id
):
    """
    Given a user who owns an organization
    When they try to update it
    Then access is granted

    Tests owner can modify their own organization.
    """
    policy = OrganizationPolicy(owner_user_id, mock_db_adapter)

    # Setup: User is owner
    mock_db_adapter.get_single.return_value = {
        "id": "member-001",
        "organization_id": org_a_id,
        "user_id": owner_user_id,
        "role": UserRoleType.OWNER.value,
        "is_deleted": False,
    }

    # When: Owner updates organization
    can_update = await policy.can_update(
        {"id": org_a_id},
        {"name": "Updated Name"}
    )

    # Then: Access granted
    assert can_update is True, "Owner should update their organization"


@pytest.mark.asyncio
async def test_owner_can_delete_own_organization(
    mock_db_adapter, owner_user_id, org_a_id
):
    """
    Given a user who owns an organization
    When they try to delete it
    Then access is granted

    Tests owner can delete their organization.
    """
    policy = OrganizationPolicy(owner_user_id, mock_db_adapter)

    # Setup: User is owner
    mock_db_adapter.get_single.return_value = {
        "id": "member-001",
        "organization_id": org_a_id,
        "user_id": owner_user_id,
        "role": UserRoleType.OWNER.value,
        "is_deleted": False,
    }

    # When: Owner deletes organization
    can_delete = await policy.can_delete({"id": org_a_id})

    # Then: Access granted
    assert can_delete is True, "Owner should delete their organization"


# =============================================================================
# WORKSPACE MEMBER ACCESS TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_workspace_member_can_access_workspace_data(
    mock_db_adapter, member_user_id, project_a_id
):
    """
    Given a user who is a member of a workspace/project
    When they try to access workspace data
    Then access is granted

    Tests workspace members can access workspace resources.
    """
    # Test project member can read project
    project_policy = ProjectPolicy(member_user_id, mock_db_adapter)

    mock_db_adapter.get_single.return_value = {
        "id": "member-002",
        "project_id": project_a_id,
        "user_id": member_user_id,
        "role": ProjectRole.EDITOR.value,
        "is_deleted": False,
    }

    can_read_project = await project_policy.can_select({"id": project_a_id})
    assert can_read_project is True, "Workspace member should read project"


@pytest.mark.asyncio
async def test_workspace_member_can_read_workspace_documents(
    mock_db_adapter, member_user_id, project_a_id
):
    """
    Given a workspace member
    When they try to access documents in the workspace
    Then access is granted

    Tests workspace members can read workspace documents.
    """
    policy = DocumentPolicy(member_user_id, mock_db_adapter)

    # Setup: User is project member
    mock_db_adapter.get_single.return_value = {
        "id": "member-002",
        "project_id": project_a_id,
        "user_id": member_user_id,
        "role": ProjectRole.VIEWER.value,
        "is_deleted": False,
    }

    # When: Member reads document
    can_read = await policy.can_select({
        "id": "doc-001",
        "project_id": project_a_id,
    })

    # Then: Access granted
    assert can_read is True, "Workspace member should read documents"


@pytest.mark.asyncio
async def test_workspace_editor_can_create_documents(
    mock_db_adapter, member_user_id, project_a_id
):
    """
    Given a workspace member with editor role
    When they try to create a document
    Then access is granted

    Tests editors can create workspace content.
    """
    policy = DocumentPolicy(member_user_id, mock_db_adapter)

    # Setup: User is editor
    mock_db_adapter.get_single.return_value = {
        "id": "member-002",
        "project_id": project_a_id,
        "user_id": member_user_id,
        "role": ProjectRole.EDITOR.value,
        "is_deleted": False,
    }

    # When: Editor creates document
    can_create = await policy.can_insert({
        "project_id": project_a_id,
        "name": "New Document",
    })

    # Then: Access granted
    assert can_create is True, "Editor should create documents"


@pytest.mark.asyncio
async def test_workspace_viewer_cannot_create_documents(
    mock_db_adapter, member_user_id, project_a_id
):
    """
    Given a workspace member with viewer role
    When they try to create a document
    Then access is denied

    Tests viewers cannot create workspace content.
    """
    policy = DocumentPolicy(member_user_id, mock_db_adapter)

    # Setup: User is viewer only
    mock_db_adapter.get_single.return_value = {
        "id": "member-002",
        "project_id": project_a_id,
        "user_id": member_user_id,
        "role": ProjectRole.VIEWER.value,
        "is_deleted": False,
    }

    # When: Viewer tries to create document
    can_create = await policy.can_insert({
        "project_id": project_a_id,
        "name": "New Document",
    })

    # Then: Access denied
    assert can_create is False, "Viewer should not create documents"


# =============================================================================
# ORGANIZATION MEMBER ACCESS TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_org_member_can_access_org_data(
    mock_db_adapter, member_user_id, org_a_id
):
    """
    Given a user who is a member of an organization
    When they try to access organization data
    Then access is granted

    Tests org members can access org-level resources.
    """
    policy = OrganizationPolicy(member_user_id, mock_db_adapter)

    # Setup: User is org member
    mock_db_adapter.get_single.return_value = {
        "id": "member-002",
        "organization_id": org_a_id,
        "user_id": member_user_id,
        "role": UserRoleType.MEMBER.value,
        "is_deleted": False,
    }

    # When: Member reads organization
    can_read = await policy.can_select({"id": org_a_id})

    # Then: Access granted
    assert can_read is True, "Org member should read organization"


@pytest.mark.asyncio
async def test_org_member_can_create_projects_in_org(
    mock_db_adapter, member_user_id, org_a_id
):
    """
    Given an organization member
    When they try to create a project in the organization
    Then access is granted

    Tests org members can create projects in their org.
    """
    policy = ProjectPolicy(member_user_id, mock_db_adapter)

    # Setup: User is org member
    mock_db_adapter.get_single.return_value = {
        "id": "member-002",
        "organization_id": org_a_id,
        "user_id": member_user_id,
        "is_deleted": False,
    }

    # When: Member creates project
    can_create = await policy.can_insert({
        "organization_id": org_a_id,
        "name": "New Project",
    })

    # Then: Access granted
    assert can_create is True, "Org member should create projects"


@pytest.mark.asyncio
async def test_org_member_can_access_private_org_projects(
    mock_db_adapter, member_user_id, org_a_id, project_a_id
):
    """
    Given an org member accessing a private project in their org
    When they are not a direct project member
    Then access is granted through org membership

    Tests org-level access grants project access.
    """
    # Setup complex scenario:
    # 1. User is NOT direct project member
    # 2. User IS org member
    # 3. Project is private
    def mock_get_single(table, filters):
        # Not a project member
        if table == Tables.PROJECT_MEMBERS:
            return None
        # Is org member
        if table == Tables.ORGANIZATION_MEMBERS:
            return {
                "id": "member-002",
                "organization_id": org_a_id,
                "user_id": member_user_id,
                "is_deleted": False,
            }
        # Project exists and is private
        if table == Tables.PROJECTS:
            return {
                "id": project_a_id,
                "organization_id": org_a_id,
                "visibility": Visibility.PRIVATE.value,
                "is_deleted": False,
            }
        return None

    mock_db_adapter.get_single.side_effect = mock_get_single

    # When: Org member accesses private project
    can_access = await user_can_access_project(
        project_a_id,
        member_user_id,
        mock_db_adapter
    )

    # Then: Access granted via org membership
    assert can_access is True, "Org member should access private org projects"


# =============================================================================
# CROSS-ORG ACCESS DENIAL TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_cross_org_access_is_denied(
    mock_db_adapter, member_user_id, org_a_id, org_b_id
):
    """
    Given a user who is a member of Organization A
    When they try to access Organization B
    Then access is denied

    Tests cross-organization isolation.
    """
    policy = OrganizationPolicy(member_user_id, mock_db_adapter)

    # Setup: User is member of org A only
    def mock_get_single(table, filters):
        org_id = filters.get("organization_id")
        if org_id == org_a_id:
            return {
                "id": "member-002",
                "organization_id": org_a_id,
                "user_id": member_user_id,
                "is_deleted": False,
            }
        return None  # Not member of org B

    mock_db_adapter.get_single.side_effect = mock_get_single

    # When: Try to access org B
    can_read_org_b = await policy.can_select({"id": org_b_id})

    # Then: Access denied
    assert can_read_org_b is False, "Should not access other organizations"


@pytest.mark.asyncio
async def test_cross_org_project_access_is_denied(
    mock_db_adapter, member_user_id, org_a_id, org_b_id, project_b_id
):
    """
    Given a user in Organization A
    When they try to access a project in Organization B
    Then access is denied

    Tests cross-org project isolation.
    """
    # Setup: User is member of org A, trying to access project in org B
    def mock_get_single(table, filters):
        # Not a project member
        if table == Tables.PROJECT_MEMBERS:
            return None
        # Project is in org B
        if table == Tables.PROJECTS:
            return {
                "id": project_b_id,
                "organization_id": org_b_id,
                "visibility": Visibility.PRIVATE.value,
                "is_deleted": False,
            }
        # Not member of org B
        if table == Tables.ORGANIZATION_MEMBERS:
            org_id = filters.get("organization_id")
            if org_id == org_b_id:
                return None
        return None

    mock_db_adapter.get_single.side_effect = mock_get_single

    # When: Try to access project in org B
    can_access = await user_can_access_project(
        project_b_id,
        member_user_id,
        mock_db_adapter
    )

    # Then: Access denied
    assert can_access is False, "Should not access cross-org projects"


# =============================================================================
# CROSS-WORKSPACE ACCESS DENIAL TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_cross_workspace_access_is_denied(
    mock_db_adapter, member_user_id, project_a_id, project_b_id
):
    """
    Given a user who is a member of Workspace A
    When they try to access Workspace B
    Then access is denied (unless public or org member)

    Tests workspace isolation within same org.
    """
    policy = ProjectPolicy(member_user_id, mock_db_adapter)

    # Setup: User is member of project A only
    def mock_get_single(table, filters):
        project_id = filters.get("project_id")

        # Member of project A
        if table == Tables.PROJECT_MEMBERS and project_id == project_a_id:
            return {
                "id": "member-002",
                "project_id": project_a_id,
                "user_id": member_user_id,
                "is_deleted": False,
            }

        # Project B exists but user not member
        if table == Tables.PROJECTS and filters.get("id") == project_b_id:
            return {
                "id": project_b_id,
                "organization_id": org_b_id,
                "visibility": Visibility.PRIVATE.value,
                "is_deleted": False,
            }

        return None

    mock_db_adapter.get_single.side_effect = mock_get_single

    # When: Try to read project B
    can_read_b = await policy.can_select({"id": project_b_id})

    # Then: Access denied (not member, not org member, not public)
    assert can_read_b is False, "Should not access other workspaces"


@pytest.mark.asyncio
async def test_public_project_allows_cross_workspace_access(
    mock_db_adapter, external_user_id, project_a_id
):
    """
    Given a public project
    When any authenticated user tries to access it
    Then access is granted

    Tests public visibility overrides workspace isolation.
    """
    # Setup: User is NOT project member, NOT org member, but project is PUBLIC
    def mock_get_single(table, filters):
        # Not a project member
        if table == Tables.PROJECT_MEMBERS:
            return None
        # Project is public
        if table == Tables.PROJECTS:
            return {
                "id": project_a_id,
                "organization_id": org_a_id,
                "visibility": Visibility.PUBLIC.value,
                "is_deleted": False,
            }
        return None

    mock_db_adapter.get_single.side_effect = mock_get_single

    # When: External user accesses public project
    can_access = await user_can_access_project(
        project_a_id,
        external_user_id,
        mock_db_adapter
    )

    # Then: Access granted due to public visibility
    assert can_access is True, "Public projects should be accessible to all"


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
