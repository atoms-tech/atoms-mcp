"""
Example usage of RLS policy validators.

This file demonstrates how to use the RLS policy validators in different scenarios.
"""

import asyncio

from infrastructure.factory import get_adapters
from schemas.rls import (
    DocumentPolicy,
    OrganizationPolicy,
    PermissionDeniedError,
    PolicyValidator,
    ProjectPolicy,
    is_super_admin,
    user_can_access_project,
)

# =============================================================================
# EXAMPLE 1: Basic Permission Checking
# =============================================================================

async def example_basic_permission_check():
    """Check if user has permission to read an organization."""
    # Get database adapter
    adapters = get_adapters()
    db = adapters["database"]

    # User making the request
    user_id = "user-123"

    # Create policy validator
    validator = PolicyValidator(user_id=user_id, db_adapter=db)

    # Organization record to check
    org_record = {
        "id": "org-456",
        "name": "Acme Corp",
        "type": "team"
    }

    # Check if user can read this organization
    can_read = await validator.can_select("organizations", org_record)

    if can_read:
        print(f"✅ User {user_id} can read organization {org_record['id']}")
    else:
        print(f"❌ User {user_id} cannot read organization {org_record['id']}")


# =============================================================================
# EXAMPLE 2: Using Table-Specific Policies
# =============================================================================

async def example_table_specific_policy():
    """Use table-specific policy for more detailed control."""
    adapters = get_adapters()
    db = adapters["database"]
    user_id = "user-123"

    # Create organization-specific policy
    org_policy = OrganizationPolicy(user_id=user_id, db_adapter=db)

    # Check permissions
    org_record = {"id": "org-456"}

    # Option 1: Check and handle manually
    can_update = await org_policy.can_update(org_record, {"name": "New Name"})
    if can_update:
        # Proceed with update
        print("✅ User can update organization")
    else:
        print("❌ User cannot update organization")

    # Option 2: Validate and raise exception on denial
    try:
        await org_policy.validate_update(org_record, {"name": "New Name"})
        print("✅ Permission validated, proceeding with update")
        # Proceed with update...
    except PermissionDeniedError as e:
        print(f"❌ Permission denied: {e}")


# =============================================================================
# EXAMPLE 3: Pre-validating Before Database Operations
# =============================================================================

async def example_prevalidate_before_db_operation():
    """Validate permissions before making database calls."""
    adapters = get_adapters()
    db = adapters["database"]
    user_id = "user-123"

    # Data to insert
    new_project = {
        "name": "My Project",
        "organization_id": "org-456",
        "description": "A new project"
    }

    # Create project policy
    project_policy = ProjectPolicy(user_id=user_id, db_adapter=db)

    # Validate BEFORE database operation
    try:
        await project_policy.validate_insert(new_project)

        # Permission granted, proceed with database insert
        result = await db.insert("projects", new_project)
        print(f"✅ Project created: {result['id']}")

    except PermissionDeniedError as e:
        print(f"❌ Cannot create project: {e.reason}")
        # Return error to client without making database call


# =============================================================================
# EXAMPLE 4: Using Helper Functions
# =============================================================================

async def example_helper_functions():
    """Use helper functions for common permission checks."""
    adapters = get_adapters()
    db = adapters["database"]

    user_id = "user-123"
    project_id = "project-789"

    # Check if user can access a project
    can_access = await user_can_access_project(project_id, user_id, db)
    print(f"Can access project: {can_access}")

    # Check if user is super admin
    is_admin = await is_super_admin(user_id, db)
    print(f"Is super admin: {is_admin}")


# =============================================================================
# EXAMPLE 5: Handling Different Operations
# =============================================================================

async def example_crud_operations():
    """Check permissions for all CRUD operations."""
    adapters = get_adapters()
    db = adapters["database"]
    user_id = "user-123"

    doc_policy = DocumentPolicy(user_id=user_id, db_adapter=db)

    document = {
        "id": "doc-123",
        "name": "Requirements Doc",
        "project_id": "project-789"
    }

    # Check SELECT (read) permission
    can_read = await doc_policy.can_select(document)
    print(f"Can read document: {can_read}")

    # Check INSERT (create) permission
    new_doc = {
        "name": "New Document",
        "project_id": "project-789"
    }
    can_create = await doc_policy.can_insert(new_doc)
    print(f"Can create document: {can_create}")

    # Check UPDATE permission
    can_update = await doc_policy.can_update(document, {"name": "Updated Name"})
    print(f"Can update document: {can_update}")

    # Check DELETE permission
    can_delete = await doc_policy.can_delete(document)
    print(f"Can delete document: {can_delete}")


# =============================================================================
# EXAMPLE 6: Integration with Tool Base Class
# =============================================================================

class ExampleTool:
    """Example tool using RLS validation."""

    def __init__(self):
        self.adapters = get_adapters()
        self.db = self.adapters["database"]

    async def create_document(self, user_id: str, data: dict):
        """Create a document with permission validation."""
        # Validate permissions first
        policy = DocumentPolicy(user_id=user_id, db_adapter=self.db)

        try:
            # This will raise PermissionDeniedError if not allowed
            await policy.validate_insert(data)

            # Permission granted, proceed with creation
            result = await self.db.insert("documents", data)

            return {
                "success": True,
                "document": result,
                "message": "Document created successfully"
            }

        except PermissionDeniedError as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Permission denied: {e.reason}"
            }

    async def update_document(self, user_id: str, doc_id: str, data: dict):
        """Update a document with permission validation."""
        # Get existing document
        document = await self.db.get_single("documents", filters={"id": doc_id})

        if not document:
            return {
                "success": False,
                "error": "Document not found"
            }

        # Validate permissions
        policy = DocumentPolicy(user_id=user_id, db_adapter=self.db)

        try:
            await policy.validate_update(document, data)

            # Permission granted, proceed with update
            result = await self.db.update("documents", data, filters={"id": doc_id})

            return {
                "success": True,
                "document": result,
                "message": "Document updated successfully"
            }

        except PermissionDeniedError as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Permission denied: {e.reason}"
            }


# =============================================================================
# EXAMPLE 7: Batch Permission Checking
# =============================================================================

async def example_batch_permission_check():
    """Check permissions for multiple records."""
    adapters = get_adapters()
    db = adapters["database"]
    user_id = "user-123"

    validator = PolicyValidator(user_id=user_id, db_adapter=db)

    # Get all projects
    projects = await db.query("projects", filters={"is_deleted": False})

    # Filter to only projects user can access
    accessible_projects = []
    for project in projects:
        if await validator.can_select("projects", project):
            accessible_projects.append(project)

    print(f"User can access {len(accessible_projects)} of {len(projects)} projects")
    return accessible_projects


# =============================================================================
# EXAMPLE 8: Custom Permission Logic
# =============================================================================

async def example_custom_permission_logic():
    """Implement custom permission logic on top of RLS policies."""
    adapters = get_adapters()
    db = adapters["database"]
    user_id = "user-123"

    # Check if user can delete a project
    # Custom rule: Only allow deletion if project has no documents
    project_id = "project-789"

    # First check RLS policy
    policy = ProjectPolicy(user_id=user_id, db_adapter=db)
    project = await db.get_single("projects", filters={"id": project_id})

    if not await policy.can_delete(project):
        print("❌ User doesn't have permission to delete project")
        return False

    # Additional business logic check
    doc_count = await db.count("documents", filters={"project_id": project_id, "is_deleted": False})

    if doc_count > 0:
        print(f"❌ Cannot delete project with {doc_count} documents")
        return False

    print("✅ User can delete empty project")
    return True


# =============================================================================
# RUN EXAMPLES
# =============================================================================

async def run_all_examples():
    """Run all examples."""
    print("=" * 80)
    print("EXAMPLE 1: Basic Permission Check")
    print("=" * 80)
    await example_basic_permission_check()

    print("\n" + "=" * 80)
    print("EXAMPLE 2: Table-Specific Policy")
    print("=" * 80)
    await example_table_specific_policy()

    print("\n" + "=" * 80)
    print("EXAMPLE 3: Pre-validate Before DB Operation")
    print("=" * 80)
    await example_prevalidate_before_db_operation()

    print("\n" + "=" * 80)
    print("EXAMPLE 4: Helper Functions")
    print("=" * 80)
    await example_helper_functions()

    print("\n" + "=" * 80)
    print("EXAMPLE 5: CRUD Operations")
    print("=" * 80)
    await example_crud_operations()

    print("\n" + "=" * 80)
    print("EXAMPLE 7: Batch Permission Check")
    print("=" * 80)
    await example_batch_permission_check()

    print("\n" + "=" * 80)
    print("EXAMPLE 8: Custom Permission Logic")
    print("=" * 80)
    await example_custom_permission_logic()


if __name__ == "__main__":
    # Run examples
    asyncio.run(run_all_examples())
