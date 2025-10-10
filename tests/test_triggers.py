"""
Tests for trigger emulator - verify behavior matches database triggers.

These tests ensure that Python trigger functions produce the same results
as the actual database triggers, maintaining data consistency across
client-side and server-side operations.
"""

from datetime import UTC, datetime

import pytest

# Import from generated schemas and triggers (OrganizationType defined in triggers.py)
from schemas import UserRoleType
from schemas.constants import Fields, Tables
from schemas.triggers import (
    OrganizationType,
    TriggerEmulator,
    auto_add_org_owner,
    auto_generate_slug,
    check_member_limits,
    check_requirement_cycle,
    check_version_and_update,
    generate_external_id,
    generate_uuid,
    handle_new_user,
    handle_requirement_hierarchy,
    handle_restore,
    handle_soft_delete,
    handle_updated_at,
    normalize_slug,
    set_created_timestamps,
    sync_requirements_properties,
)

# =============================================================================
# SLUG NORMALIZATION TESTS
# =============================================================================


class TestSlugNormalization:
    """Test slug normalization matches database behavior."""

    def test_normalize_slug_basic(self):
        """Test basic slug normalization."""
        assert normalize_slug("Hello World") == "hello-world"
        assert normalize_slug("Test_Org") == "test-org"
        assert normalize_slug("My-Company") == "my-company"

    def test_normalize_slug_special_chars(self):
        """Test slug handles special characters."""
        assert normalize_slug("Test & Co.") == "test-co"
        assert normalize_slug("Hello@World!") == "hello-world"
        assert normalize_slug("Foo   Bar") == "foo-bar"

    def test_normalize_slug_strips_hyphens(self):
        """Test slug strips leading/trailing hyphens."""
        assert normalize_slug("-test-") == "test"
        assert normalize_slug("---hello---") == "hello"

    def test_normalize_slug_starts_with_letter(self):
        """Test slug must start with letter (database constraint)."""
        with pytest.raises(ValueError, match="must start with letter"):
            normalize_slug("123-test")
        with pytest.raises(ValueError, match="must start with letter"):
            normalize_slug("-test")

    def test_normalize_slug_empty(self):
        """Test slug handles empty/invalid input."""
        with pytest.raises(ValueError, match="non-empty string"):
            normalize_slug("")
        with pytest.raises(ValueError, match="non-empty string"):
            normalize_slug(None)

    def test_auto_generate_slug(self):
        """Test auto slug generation."""
        assert auto_generate_slug("Test Project") == "test-project"
        assert auto_generate_slug("My Org") == "my-org"
        assert auto_generate_slug("", "document") == "document"
        assert auto_generate_slug(None, "entity") == "entity"

    def test_auto_generate_slug_invalid_fallback(self):
        """Test auto slug uses fallback for invalid names."""
        assert auto_generate_slug("123", "org") == "org"
        assert auto_generate_slug("---", "proj") == "proj"


# =============================================================================
# TIMESTAMP TESTS
# =============================================================================


class TestTimestamps:
    """Test timestamp handling matches database triggers."""

    def test_handle_updated_at(self):
        """Test updated_at is set to current time."""
        data = {"name": "Test"}
        result = handle_updated_at(data)

        assert Fields.UPDATED_AT in result
        # Verify it's a recent timestamp
        updated_at = datetime.fromisoformat(result[Fields.UPDATED_AT])
        now = datetime.now(UTC)
        assert (now - updated_at).total_seconds() < 1

    def test_set_created_timestamps(self):
        """Test created_at and updated_at are set."""
        data = {"name": "Test"}
        result = set_created_timestamps(data)

        assert Fields.CREATED_AT in result
        assert Fields.UPDATED_AT in result
        assert result[Fields.CREATED_AT] == result[Fields.UPDATED_AT]

    def test_timestamps_preserve_other_fields(self):
        """Test timestamp functions preserve existing fields."""
        data = {"name": "Test", "description": "Desc"}
        result = set_created_timestamps(data)

        assert result["name"] == "Test"
        assert result["description"] == "Desc"


# =============================================================================
# ID GENERATION TESTS
# =============================================================================


class TestIdGeneration:
    """Test ID generation matches database triggers."""

    def test_generate_external_id_default(self):
        """Test external ID generation with default prefix."""
        external_id = generate_external_id("requirement")
        assert external_id.startswith("REQ-")
        assert len(external_id) == 12  # REQ- + 8 chars

    def test_generate_external_id_custom_prefix(self):
        """Test external ID with custom prefix."""
        external_id = generate_external_id("test", prefix="CUSTOM")
        assert external_id.startswith("CUSTOM-")

    def test_generate_external_id_entity_types(self):
        """Test external ID prefixes for different entity types."""
        assert generate_external_id("requirement").startswith("REQ-")
        assert generate_external_id("test").startswith("TEST-")
        assert generate_external_id("document").startswith("DOC-")
        assert generate_external_id("project").startswith("PROJ-")
        assert generate_external_id("unknown").startswith("ENT-")

    def test_generate_uuid(self):
        """Test UUID generation."""
        uuid1 = generate_uuid()
        uuid2 = generate_uuid()

        assert len(uuid1) == 36  # Standard UUID length
        assert uuid1 != uuid2  # UUIDs should be unique


# =============================================================================
# REQUIREMENT TRIGGER TESTS
# =============================================================================


class TestRequirementTriggers:
    """Test requirement-specific triggers."""

    def test_sync_requirements_properties(self):
        """Test requirement properties are synced."""
        data = {
            "name": "REQ-001",
            "status": "active",
            "priority": "high",
            "format": "incose"
        }
        result = sync_requirements_properties(data)

        assert "properties" in result
        assert result["properties"]["status"] == "active"
        assert result["properties"]["priority"] == "high"
        assert result["properties"]["format"] == "incose"

    def test_sync_requirements_properties_preserves_existing(self):
        """Test sync preserves existing properties."""
        data = {
            "name": "REQ-001",
            "status": "active",
            "properties": {"custom_field": "value"}
        }
        result = sync_requirements_properties(data)

        assert result["properties"]["status"] == "active"
        assert result["properties"]["custom_field"] == "value"

    def test_handle_requirement_hierarchy_self_reference(self):
        """Test hierarchy creates self-reference."""
        data = {"id": "req-1"}
        closure = handle_requirement_hierarchy(data)

        assert len(closure) == 1
        assert closure[0]["ancestor_id"] == "req-1"
        assert closure[0]["descendant_id"] == "req-1"
        assert closure[0]["depth"] == 0

    def test_handle_requirement_hierarchy_with_parent(self):
        """Test hierarchy with parent inherits ancestors."""
        data = {"id": "req-2", "parent_id": "req-1"}
        existing_closure = [
            {"ancestor_id": "req-0", "descendant_id": "req-1", "depth": 1},
            {"ancestor_id": "req-1", "descendant_id": "req-1", "depth": 0}
        ]

        closure = handle_requirement_hierarchy(data, existing_closure)

        # Should have self-reference + 2 inherited ancestors
        assert len(closure) == 3
        # Self-reference
        assert any(
            e["ancestor_id"] == "req-2" and e["descendant_id"] == "req-2" and e["depth"] == 0
            for e in closure
        )
        # Direct parent
        assert any(
            e["ancestor_id"] == "req-1" and e["descendant_id"] == "req-2" and e["depth"] == 1
            for e in closure
        )
        # Grandparent
        assert any(
            e["ancestor_id"] == "req-0" and e["descendant_id"] == "req-2" and e["depth"] == 2
            for e in closure
        )


# =============================================================================
# USER/ORGANIZATION TRIGGER TESTS
# =============================================================================


class TestUserOrgTriggers:
    """Test user and organization triggers."""

    def test_handle_new_user(self):
        """Test new user creates personal org."""
        user_data = {
            "id": "user-1",
            "email": "test@example.com",
            "full_name": "Test User"
        }

        updated_profile, personal_org = handle_new_user(user_data)

        # Check profile update
        assert "personal_organization_id" in updated_profile
        assert "current_organization_id" in updated_profile
        assert updated_profile["personal_organization_id"] == personal_org["id"]

        # Check org creation
        assert personal_org["name"] == "Test User's Workspace"
        assert personal_org["type"] == OrganizationType.PERSONAL.value
        assert personal_org["owner_id"] == "user-1"
        assert personal_org["slug"].startswith("test-personal")

    def test_handle_new_user_email_only(self):
        """Test new user with email only."""
        user_data = {
            "id": "user-2",
            "email": "john@example.com"
        }

        updated_profile, personal_org = handle_new_user(user_data)

        assert personal_org["name"] == "john's Workspace"
        assert personal_org["slug"].startswith("john-personal")

    def test_auto_add_org_owner(self):
        """Test org owner is auto-added to members."""
        member_data = auto_add_org_owner("org-1", "user-1")

        assert member_data["organization_id"] == "org-1"
        assert member_data["user_id"] == "user-1"
        assert member_data["role"] == UserRoleType.OWNER.value
        assert member_data["status"] == "active"
        assert member_data[Fields.IS_DELETED] is False


# =============================================================================
# SOFT DELETE TESTS
# =============================================================================


class TestSoftDelete:
    """Test soft delete triggers."""

    def test_handle_soft_delete(self):
        """Test soft delete sets correct fields."""
        data = {"id": "entity-1", "name": "Test"}
        result = handle_soft_delete(data, "user-1")

        assert result[Fields.IS_DELETED] is True
        assert Fields.DELETED_AT in result
        assert result[Fields.DELETED_BY] == "user-1"

    def test_handle_restore(self):
        """Test restore clears soft delete fields."""
        data = {
            "id": "entity-1",
            Fields.IS_DELETED: True,
            Fields.DELETED_AT: "2024-01-01T00:00:00Z",
            Fields.DELETED_BY: "user-1"
        }
        result = handle_restore(data)

        assert result[Fields.IS_DELETED] is False
        assert result[Fields.DELETED_AT] is None
        assert result[Fields.DELETED_BY] is None


# =============================================================================
# VALIDATION TESTS
# =============================================================================


class TestValidation:
    """Test validation helpers."""

    def test_check_member_limits_within_limit(self):
        """Test member limits pass when under limit."""
        org_data = {"billing_plan": "free", "max_members": 5}
        # Should not raise
        check_member_limits(org_data, 3)

    def test_check_member_limits_at_limit(self):
        """Test member limits fail at limit."""
        org_data = {"billing_plan": "free", "max_members": 5}
        with pytest.raises(ValueError, match="member limit reached"):
            check_member_limits(org_data, 5)

    def test_check_member_limits_default_plans(self):
        """Test default limits by plan."""
        # Free plan default: 5
        with pytest.raises(ValueError):
            check_member_limits({"billing_plan": "free"}, 5)

        # Pro plan default: 50
        check_member_limits({"billing_plan": "pro"}, 25)  # Should pass

    def test_check_version_and_update(self):
        """Test version increment for optimistic locking."""
        data = {"name": "Updated"}
        result = check_version_and_update("requirements", "req-1", 1, data)

        assert result[Fields.VERSION] == 2

    def test_check_requirement_cycle_self(self):
        """Test cycle detection - self reference."""
        with pytest.raises(ValueError, match="cannot be its own parent"):
            check_requirement_cycle("req-1", "req-1", [])

    def test_check_requirement_cycle_descendant(self):
        """Test cycle detection - parent is descendant."""
        closure = [
            {"ancestor_id": "req-1", "descendant_id": "req-2", "depth": 1}
        ]
        with pytest.raises(ValueError, match="Cycle detected"):
            check_requirement_cycle("req-1", "req-2", closure)

    def test_check_requirement_cycle_valid(self):
        """Test valid parent assignment."""
        closure = [
            {"ancestor_id": "req-1", "descendant_id": "req-2", "depth": 1}
        ]
        # Should not raise - req-3 can have req-1 as parent
        check_requirement_cycle("req-3", "req-1", closure)


# =============================================================================
# TRIGGER EMULATOR TESTS
# =============================================================================


class TestTriggerEmulator:
    """Test the TriggerEmulator class."""

    @pytest.fixture
    def emulator(self):
        """Create emulator instance."""
        emulator = TriggerEmulator()
        emulator.set_user_context("user-123")
        return emulator

    def test_before_insert_organization(self, emulator):
        """Test BEFORE INSERT for organization."""
        data = {
            "name": "Test Org",
            "slug": "Test Org"
        }
        result = emulator.before_insert(Tables.ORGANIZATIONS, data)

        # Check generated fields
        assert Fields.ID in result
        assert Fields.CREATED_AT in result
        assert Fields.UPDATED_AT in result
        assert result[Fields.CREATED_BY] == "user-123"
        assert result[Fields.UPDATED_BY] == "user-123"

        # Check slug normalization
        assert result[Fields.SLUG] == "test-org"

        # Check defaults
        assert result["type"] == OrganizationType.PERSONAL.value
        assert result["billing_plan"] == "free"
        assert result[Fields.IS_DELETED] is False

    def test_before_insert_project(self, emulator):
        """Test BEFORE INSERT for project."""
        data = {
            "name": "Test Project",
            "organization_id": "org-123"
        }
        result = emulator.before_insert(Tables.PROJECTS, data)

        # Check auto-generated slug
        assert result[Fields.SLUG] == "test-project"
        assert result[Fields.IS_DELETED] is False

    def test_before_insert_requirement(self, emulator):
        """Test BEFORE INSERT for requirement."""
        data = {
            "name": "REQ-001",
            "document_id": "doc-123",
            "status": "active",
            "priority": "high"
        }
        result = emulator.before_insert(Tables.REQUIREMENTS, data)

        # Check external_id generation
        assert Fields.EXTERNAL_ID in result
        assert result[Fields.EXTERNAL_ID].startswith("REQ-")

        # Check properties sync
        assert "properties" in result
        assert result["properties"]["status"] == "active"
        assert result["properties"]["priority"] == "high"

        # Check version
        assert result[Fields.VERSION] == 1

    def test_before_update_basic(self, emulator):
        """Test BEFORE UPDATE basic functionality."""
        old_data = {"id": "entity-1", "name": "Old", Fields.VERSION: 1}
        new_data = {"name": "New"}

        result = emulator.before_update(Tables.PROJECTS, old_data, new_data)

        # Check updated_at set
        assert Fields.UPDATED_AT in result

        # Check updated_by set
        assert result[Fields.UPDATED_BY] == "user-123"

        # Check version increment
        assert result[Fields.VERSION] == 2

    def test_before_update_requirement(self, emulator):
        """Test BEFORE UPDATE for requirement syncs properties."""
        old_data = {"id": "req-1", Fields.VERSION: 1}
        new_data = {"status": "approved", "priority": "critical"}

        result = emulator.before_update(Tables.REQUIREMENTS, old_data, new_data)

        # Check properties synced
        assert "properties" in result
        assert result["properties"]["status"] == "approved"
        assert result["properties"]["priority"] == "critical"

    def test_after_insert_organization(self, emulator):
        """Test AFTER INSERT for organization creates member."""
        data = {
            "id": "org-1",
            "name": "Test Org",
            "owner_id": "user-123"
        }

        side_effects = emulator.after_insert(Tables.ORGANIZATIONS, data)

        # Should create organization_member
        assert len(side_effects) == 1
        table, member_data = side_effects[0]
        assert table == Tables.ORGANIZATION_MEMBERS
        assert member_data["organization_id"] == "org-1"
        assert member_data["user_id"] == "user-123"
        assert member_data["role"] == UserRoleType.OWNER.value

    def test_after_insert_profile(self, emulator):
        """Test AFTER INSERT for profile creates personal org."""
        data = {
            "id": "user-1",
            "email": "test@example.com",
            "full_name": "Test User"
        }

        side_effects = emulator.after_insert(Tables.PROFILES, data)

        # Should create personal organization
        assert len(side_effects) == 1
        table, org_data = side_effects[0]
        assert table == Tables.ORGANIZATIONS
        assert org_data["type"] == OrganizationType.PERSONAL.value
        assert org_data["owner_id"] == "user-1"

    def test_emulator_preserves_data(self, emulator):
        """Test emulator preserves original data."""
        original = {"name": "Test", "custom_field": "value"}
        result = emulator.before_insert(Tables.PROJECTS, original)

        # Original should be unchanged
        assert "id" not in original
        assert Fields.CREATED_AT not in original

        # Result should have both original and new fields
        assert result["name"] == "Test"
        assert result["custom_field"] == "value"
        assert "id" in result
        assert Fields.CREATED_AT in result


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestTriggerIntegration:
    """Integration tests for complete trigger workflows."""

    def test_organization_creation_workflow(self):
        """Test complete organization creation workflow."""
        emulator = TriggerEmulator()
        emulator.set_user_context("user-123")

        # 1. BEFORE INSERT
        org_data = {
            "name": "My Company",
            "slug": "My Company!",
            "type": OrganizationType.TEAM.value
        }
        org_data = emulator.before_insert(Tables.ORGANIZATIONS, org_data)

        # Check transformations
        assert org_data[Fields.ID]
        assert org_data[Fields.SLUG] == "my-company"
        assert org_data[Fields.CREATED_BY] == "user-123"

        # 2. AFTER INSERT
        side_effects = emulator.after_insert(Tables.ORGANIZATIONS, org_data)

        # Check member creation
        assert len(side_effects) == 1
        table, member_data = side_effects[0]
        assert table == Tables.ORGANIZATION_MEMBERS
        assert member_data["organization_id"] == org_data[Fields.ID]

    def test_requirement_update_workflow(self):
        """Test complete requirement update workflow."""
        emulator = TriggerEmulator()
        emulator.set_user_context("user-456")

        old_data = {
            "id": "req-1",
            "name": "REQ-001",
            Fields.VERSION: 3,
            "status": "draft"
        }

        new_data = {
            "status": "approved",
            "priority": "high"
        }

        # BEFORE UPDATE
        result = emulator.before_update(Tables.REQUIREMENTS, old_data, new_data)

        # Check all transformations
        assert result[Fields.UPDATED_AT]
        assert result[Fields.UPDATED_BY] == "user-456"
        assert result[Fields.VERSION] == 4
        assert result["properties"]["status"] == "approved"
        assert result["properties"]["priority"] == "high"

    def test_user_signup_workflow(self):
        """Test complete new user signup workflow."""
        emulator = TriggerEmulator()

        # 1. User profile inserted
        user_data = {
            "id": "user-new",
            "email": "newuser@example.com",
            "full_name": "New User"
        }

        # BEFORE INSERT on profiles
        user_data = emulator.before_insert(Tables.PROFILES, user_data)

        assert user_data["status"] == "active"
        assert user_data["is_approved"] is True

        # AFTER INSERT on profiles
        side_effects = emulator.after_insert(Tables.PROFILES, user_data)

        # Should create personal org
        assert len(side_effects) == 1
        table, org_data = side_effects[0]
        assert table == Tables.ORGANIZATIONS
        assert org_data["type"] == OrganizationType.PERSONAL.value

        # Then org AFTER INSERT would create membership
        # (This would be a second step in the actual workflow)
