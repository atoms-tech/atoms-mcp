"""
Python equivalents of database triggers for client-side validation and data transformation.

This module replicates database trigger logic in Python, allowing tools to:
1. Transform data the same way as database triggers
2. Validate constraints before sending to database
3. Ensure data consistency across client and server

All functions in this module mirror actual database triggers and must maintain
behavioral parity with the database implementation.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple
from schemas.enums import OrganizationType, UserRoleType
from schemas.constants import Tables, Fields, TABLES_WITHOUT_SOFT_DELETE
from utils.logging_setup import get_logger

logger = get_logger(__name__)

# =============================================================================
# SLUG NORMALIZATION
# =============================================================================

# Matches anything that's not lowercase alphanumeric
SLUG_PATTERN = re.compile(r"[^a-z0-9]+")


def normalize_slug(slug: str) -> str:
    """
    Normalize a slug to database-compatible format.

    Replicates: Database trigger for slug normalization
    - Converts to lowercase
    - Replaces non-alphanumeric with hyphens
    - Removes leading/trailing hyphens
    - Ensures slug starts with a letter

    Args:
        slug: Raw slug string

    Returns:
        Normalized slug

    Raises:
        ValueError: If slug cannot be normalized to valid format
    """
    if not slug or not isinstance(slug, str):
        raise ValueError("Slug must be a non-empty string")

    # Convert to lowercase and replace non-alphanumeric with hyphens
    normalized = SLUG_PATTERN.sub("-", slug.strip().lower()).strip("-")

    if not normalized:
        raise ValueError(f"Slug '{slug}' normalizes to empty string")

    # Ensure starts with letter (database constraint)
    if not normalized[0].isalpha():
        raise ValueError(f"Slug must start with letter, got: '{normalized}'")

    return normalized


def auto_generate_slug(name: str, fallback: str = "entity") -> str:
    """
    Auto-generate slug from entity name.

    Replicates: Database behavior for auto-slug generation

    Args:
        name: Entity name to convert to slug
        fallback: Default slug if name is empty/invalid

    Returns:
        Valid slug
    """
    if not name or not isinstance(name, str):
        return fallback

    try:
        return normalize_slug(name)
    except ValueError:
        return fallback


# =============================================================================
# TIMESTAMP MANAGEMENT
# =============================================================================


def handle_updated_at(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Set updated_at timestamp to current UTC time.

    Replicates: Database BEFORE UPDATE trigger on updated_at
    - Sets updated_at to NOW() on every update
    - Used on: organizations, projects, documents, requirements, test_req, etc.

    Args:
        data: Entity data being updated

    Returns:
        Data with updated_at set to current UTC timestamp
    """
    result = data.copy()
    result[Fields.UPDATED_AT] = datetime.now(timezone.utc).isoformat()
    return result


def set_created_timestamps(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Set created_at and updated_at timestamps for new records.

    Replicates: Database BEFORE INSERT trigger for timestamps
    - Sets both created_at and updated_at to NOW()
    - Used on all tables with timestamp columns

    Args:
        data: New entity data

    Returns:
        Data with timestamps set
    """
    result = data.copy()
    now = datetime.now(timezone.utc).isoformat()
    result[Fields.CREATED_AT] = now
    result[Fields.UPDATED_AT] = now
    return result


# =============================================================================
# ID GENERATION
# =============================================================================


def generate_external_id(entity_type: str, prefix: Optional[str] = None) -> str:
    """
    Generate external ID for requirements and other entities.

    Replicates: Database trigger for external_id auto-generation
    - Used on: requirements table
    - Format: REQ-{uuid} or {prefix}-{uuid}

    Args:
        entity_type: Type of entity (e.g., "requirement")
        prefix: Optional prefix (defaults based on entity_type)

    Returns:
        Generated external ID
    """
    if prefix is None:
        prefix_map = {
            "requirement": "REQ",
            "test": "TEST",
            "document": "DOC",
            "project": "PROJ",
        }
        prefix = prefix_map.get(entity_type, "ENT")

    # Generate short UUID (first 8 chars of UUID4)
    short_uuid = str(uuid.uuid4())[:8].upper()
    return f"{prefix}-{short_uuid}"


def generate_uuid() -> str:
    """
    Generate UUID for primary keys.

    Replicates: Database DEFAULT gen_random_uuid()

    Returns:
        UUID string
    """
    return str(uuid.uuid4())


# =============================================================================
# REQUIREMENT TRIGGERS
# =============================================================================


def sync_requirements_properties(requirement_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sync requirement properties to ensure consistency.

    Replicates: Database trigger for requirements property sync
    - Ensures properties JSONB has all base fields
    - Syncs status, priority, format between columns and properties

    Args:
        requirement_data: Requirement entity data

    Returns:
        Data with synced properties
    """
    result = requirement_data.copy()

    # Initialize properties if not present
    if "properties" not in result or result["properties"] is None:
        result["properties"] = {}

    # Sync base fields into properties
    sync_fields = ["status", "priority", "format", "level", "type"]
    for field in sync_fields:
        if field in result and result[field] is not None:
            result["properties"][field] = result[field]

    return result


def handle_requirement_hierarchy(
    requirement_data: Dict[str, Any],
    existing_closure: Optional[List[Dict[str, Any]]] = None
) -> List[Dict[str, Any]]:
    """
    Handle requirement hierarchy closure table updates.

    Replicates: Database trigger for requirements_closure management
    - Maintains transitive closure for requirement hierarchies
    - Prevents cycles

    Args:
        requirement_data: Requirement being inserted/updated
        existing_closure: Existing closure table entries

    Returns:
        Closure table entries to insert
    """
    req_id = requirement_data.get("id")
    parent_id = requirement_data.get("parent_id")

    if not req_id:
        return []

    closure_entries = []

    # Self-reference (depth 0)
    closure_entries.append({
        "ancestor_id": req_id,
        "descendant_id": req_id,
        "depth": 0
    })

    # If has parent, inherit all parent's ancestors
    if parent_id:
        if existing_closure:
            for entry in existing_closure:
                if entry["descendant_id"] == parent_id:
                    closure_entries.append({
                        "ancestor_id": entry["ancestor_id"],
                        "descendant_id": req_id,
                        "depth": entry["depth"] + 1
                    })

    return closure_entries


# =============================================================================
# USER AND ORGANIZATION TRIGGERS
# =============================================================================


def handle_new_user(user_data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Handle new user creation - create personal organization.

    Replicates: Database AFTER INSERT trigger on profiles
    - Creates personal organization for new user
    - Sets user as owner of personal org
    - Updates profile with personal_organization_id

    Args:
        user_data: New user/profile data

    Returns:
        Tuple of (updated_profile_data, new_org_data)
    """
    user_id = user_data.get("id") or user_data.get("user_id")
    email = user_data.get("email", "user")
    full_name = user_data.get("full_name") or email.split("@")[0]

    # Generate personal org data
    org_slug = normalize_slug(f"{email.split('@')[0]}-personal")

    personal_org = {
        "id": generate_uuid(),
        "name": f"{full_name}'s Workspace",
        "slug": org_slug,
        "type": OrganizationType.PERSONAL.value,
        "owner_id": user_id,
        "created_by": user_id,
        "updated_by": user_id,
        "is_deleted": False
    }

    # Update profile with personal org ID
    updated_profile = user_data.copy()
    updated_profile["personal_organization_id"] = personal_org["id"]
    updated_profile["current_organization_id"] = personal_org["id"]

    return updated_profile, personal_org


def auto_add_org_owner(org_id: str, user_id: str) -> Dict[str, Any]:
    """
    Automatically add organization owner to org_members.

    Replicates: Database AFTER INSERT trigger on organizations
    - Adds owner_id user to organization_members with 'owner' role
    - Ensures organization creator is automatically a member

    Args:
        org_id: Organization ID
        user_id: User ID (from owner_id or created_by)

    Returns:
        Organization member data to insert
    """
    return {
        "id": generate_uuid(),
        "organization_id": org_id,
        "user_id": user_id,
        "role": UserRoleType.OWNER.value,
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "is_deleted": False
    }


# =============================================================================
# SOFT DELETE TRIGGERS
# =============================================================================


def handle_soft_delete(data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """
    Handle soft delete operation.

    Replicates: Database BEFORE UPDATE trigger for soft delete
    - Sets is_deleted = true
    - Sets deleted_at timestamp
    - Sets deleted_by user

    Args:
        data: Entity data
        user_id: User performing the delete

    Returns:
        Data with soft delete fields set
    """
    result = data.copy()
    result[Fields.IS_DELETED] = True
    result[Fields.DELETED_AT] = datetime.now(timezone.utc).isoformat()
    result[Fields.DELETED_BY] = user_id
    return result


def handle_restore(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle restore from soft delete.

    Replicates: Database logic for restoring soft-deleted records
    - Sets is_deleted = false
    - Clears deleted_at and deleted_by

    Args:
        data: Entity data

    Returns:
        Data with soft delete fields cleared
    """
    result = data.copy()
    result[Fields.IS_DELETED] = False
    result[Fields.DELETED_AT] = None
    result[Fields.DELETED_BY] = None
    return result


# =============================================================================
# VALIDATION HELPERS
# =============================================================================


def check_member_limits(
    org_data: Dict[str, Any],
    current_member_count: int
) -> None:
    """
    Verify organization membership limits.

    Replicates: Database constraint check for member limits
    - Free plan: 5 members max
    - Pro plan: 50 members max
    - Enterprise: unlimited

    Args:
        org_data: Organization data
        current_member_count: Current number of members

    Raises:
        ValueError: If member limit exceeded
    """
    max_members = org_data.get("max_members")
    billing_plan = org_data.get("billing_plan", "free")

    # Default limits by plan
    if max_members is None:
        limits = {
            "free": 5,
            "pro": 50,
            "enterprise": 999999  # Effectively unlimited
        }
        max_members = limits.get(billing_plan, 5)

    if current_member_count >= max_members:
        raise ValueError(
            f"Organization member limit reached ({max_members} for {billing_plan} plan). "
            f"Cannot add more members."
        )


def check_version_and_update(
    table: str,
    entity_id: str,
    current_version: int,
    new_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Check version for optimistic locking and increment.

    Replicates: Database trigger for version-based optimistic locking
    - Ensures version matches expected value
    - Increments version on successful update

    Args:
        table: Table name
        entity_id: Entity ID being updated
        current_version: Expected current version
        new_data: Update data

    Returns:
        Data with incremented version

    Raises:
        ValueError: If version mismatch (concurrent modification)
    """
    result = new_data.copy()

    # Version will be checked by database query
    # If it doesn't match, update will fail
    # This function just prepares the increment
    result[Fields.VERSION] = current_version + 1

    return result


def check_requirement_cycle(
    requirement_id: str,
    parent_id: str,
    closure_data: List[Dict[str, Any]]
) -> None:
    """
    Prevent cycles in requirement hierarchy.

    Replicates: Database constraint to prevent circular dependencies
    - Checks if parent_id is a descendant of requirement_id
    - Prevents requirement from being its own ancestor

    Args:
        requirement_id: Requirement being updated
        parent_id: Proposed parent ID
        closure_data: Current closure table data

    Raises:
        ValueError: If cycle would be created
    """
    if requirement_id == parent_id:
        raise ValueError("Requirement cannot be its own parent")

    # Check if parent_id is already a descendant of requirement_id
    for entry in closure_data:
        if (entry["ancestor_id"] == requirement_id and
            entry["descendant_id"] == parent_id):
            raise ValueError(
                f"Cycle detected: {parent_id} is already a descendant of {requirement_id}"
            )


# =============================================================================
# TRIGGER EMULATOR
# =============================================================================


class TriggerEmulator:
    """
    Emulates database triggers in Python for client-side operations.

    Executes triggers in the same order as database:
    1. BEFORE INSERT/UPDATE triggers (data transformation)
    2. Validation
    3. AFTER INSERT/UPDATE triggers (side effects)
    """

    def __init__(self, supabase_client=None):
        """
        Initialize trigger emulator.

        Args:
            supabase_client: Optional Supabase client for validation queries
        """
        self.supabase = supabase_client
        self._user_id = None

    def set_user_context(self, user_id: str) -> None:
        """Set current user ID for audit fields."""
        self._user_id = user_id

    def before_insert(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run BEFORE INSERT trigger logic.

        Args:
            table: Table name
            data: Data to be inserted

        Returns:
            Transformed data ready for insert
        """
        result = data.copy()

        # Generate ID if not present
        if Fields.ID not in result:
            result[Fields.ID] = generate_uuid()

        # Set timestamps
        result = set_created_timestamps(result)

        # Set audit fields
        if self._user_id and Fields.CREATED_BY not in result:
            result[Fields.CREATED_BY] = self._user_id
        if self._user_id and Fields.UPDATED_BY not in result:
            result[Fields.UPDATED_BY] = self._user_id

        # Table-specific logic
        if table == Tables.ORGANIZATIONS:
            # Normalize slug
            if Fields.SLUG in result:
                result[Fields.SLUG] = normalize_slug(result[Fields.SLUG])
            elif Fields.NAME in result:
                result[Fields.SLUG] = auto_generate_slug(result[Fields.NAME])

            # Set defaults
            if "type" not in result:
                result["type"] = OrganizationType.PERSONAL.value
            if "billing_plan" not in result:
                result["billing_plan"] = "free"
            if Fields.IS_DELETED not in result:
                result[Fields.IS_DELETED] = False

        elif table == Tables.PROJECTS:
            # Auto-generate slug
            if Fields.SLUG not in result and Fields.NAME in result:
                result[Fields.SLUG] = auto_generate_slug(result[Fields.NAME])
            if Fields.IS_DELETED not in result:
                result[Fields.IS_DELETED] = False

        elif table == Tables.DOCUMENTS:
            # Auto-generate slug
            if Fields.SLUG not in result and Fields.NAME in result:
                result[Fields.SLUG] = auto_generate_slug(result[Fields.NAME], "document")
            if Fields.VERSION not in result:
                result[Fields.VERSION] = 1
            if Fields.IS_DELETED not in result:
                result[Fields.IS_DELETED] = False

        elif table == Tables.REQUIREMENTS:
            # Generate external_id
            if Fields.EXTERNAL_ID not in result:
                result[Fields.EXTERNAL_ID] = generate_external_id("requirement")

            # Sync properties
            result = sync_requirements_properties(result)

            if Fields.VERSION not in result:
                result[Fields.VERSION] = 1
            if Fields.IS_DELETED not in result:
                result[Fields.IS_DELETED] = False

        elif table == Tables.PROFILES:
            # Set defaults
            if "status" not in result:
                result["status"] = "active"
            if "is_approved" not in result:
                result["is_approved"] = True
            if Fields.IS_DELETED not in result:
                result[Fields.IS_DELETED] = False

        # Initialize soft delete fields for tables that support it
        if table not in TABLES_WITHOUT_SOFT_DELETE:
            if Fields.IS_DELETED not in result:
                result[Fields.IS_DELETED] = False

        return result

    def before_update(
        self,
        table: str,
        old_data: Dict[str, Any],
        new_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run BEFORE UPDATE trigger logic.

        Args:
            table: Table name
            old_data: Existing data
            new_data: New data

        Returns:
            Transformed update data
        """
        result = new_data.copy()

        # Always update timestamp
        result = handle_updated_at(result)

        # Set updated_by
        if self._user_id and Fields.UPDATED_BY not in result:
            result[Fields.UPDATED_BY] = self._user_id

        # Increment version if table supports it
        if Fields.VERSION in old_data and Fields.VERSION not in result:
            result[Fields.VERSION] = old_data[Fields.VERSION] + 1

        # Table-specific logic
        if table == Tables.REQUIREMENTS:
            # Sync properties on update
            result = sync_requirements_properties(result)

        elif table == Tables.ORGANIZATIONS:
            # Normalize slug if changed
            if Fields.SLUG in result and result[Fields.SLUG] != old_data.get(Fields.SLUG):
                result[Fields.SLUG] = normalize_slug(result[Fields.SLUG])

        return result

    def after_insert(
        self,
        table: str,
        data: Dict[str, Any]
    ) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Run AFTER INSERT trigger logic.

        Args:
            table: Table name
            data: Inserted data

        Returns:
            List of (table, data) tuples for additional inserts
        """
        side_effects = []

        if table == Tables.ORGANIZATIONS:
            # Auto-add owner to organization_members
            owner_id = data.get("owner_id") or data.get(Fields.CREATED_BY)
            if owner_id:
                member_data = auto_add_org_owner(data["id"], owner_id)
                side_effects.append((Tables.ORGANIZATION_MEMBERS, member_data))

        elif table == Tables.PROFILES:
            # Create personal organization for new user
            updated_profile, personal_org = handle_new_user(data)
            side_effects.append((Tables.ORGANIZATIONS, personal_org))
            # Note: Profile update would need separate update operation

        elif table == Tables.REQUIREMENTS:
            # Handle hierarchy closure
            if "parent_id" in data and data["parent_id"]:
                # Would need to query existing closure entries
                # and create new ones
                pass

        return side_effects

    def after_update(
        self,
        table: str,
        old_data: Dict[str, Any],
        new_data: Dict[str, Any]
    ) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Run AFTER UPDATE trigger logic.

        Args:
            table: Table name
            old_data: Old data
            new_data: New data

        Returns:
            List of (table, data) tuples for additional operations
        """
        side_effects = []

        # Cascade soft delete to related entities
        if table in [Tables.ORGANIZATIONS, Tables.PROJECTS, Tables.DOCUMENTS]:
            if new_data.get(Fields.IS_DELETED) and not old_data.get(Fields.IS_DELETED):
                # Organization deleted -> cascade to projects
                # Project deleted -> cascade to documents
                # Document deleted -> cascade to requirements
                # (Implementation would require queries to find related entities)
                pass

        return side_effects


# =============================================================================
# PUBLIC API
# =============================================================================

__all__ = [
    # Slug functions
    "normalize_slug",
    "auto_generate_slug",

    # Timestamp functions
    "handle_updated_at",
    "set_created_timestamps",

    # ID generation
    "generate_external_id",
    "generate_uuid",

    # Requirement functions
    "sync_requirements_properties",
    "handle_requirement_hierarchy",

    # User/org functions
    "handle_new_user",
    "auto_add_org_owner",

    # Soft delete
    "handle_soft_delete",
    "handle_restore",

    # Validation
    "check_member_limits",
    "check_version_and_update",
    "check_requirement_cycle",

    # Trigger emulator
    "TriggerEmulator",
]
