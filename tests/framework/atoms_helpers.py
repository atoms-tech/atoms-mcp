"""
Atoms-Specific Test Helpers

Provides helpers for Atoms MCP Server testing:
- Entity ID resolution (organization, project, document, etc.)
- Nested entity creation with auto-parent resolution
- Test entity factories for Atoms domain model
"""


# Import from pheno_vendor for generic validation
from pheno_vendor.mcp_qa.core.validators import ResponseValidator as BaseValidator


class AtomsTestHelpers:
    """Atoms-specific test helpers extending generic mcp_qa validators."""

    @staticmethod
    async def get_existing_entity_id(client, entity_type: str) -> str | None:
        """Get an existing entity ID from Atoms entity_tool.

        Returns the ID of the first entity of the given type, or None if none exist.
        """
        list_result = await client.call_tool("entity_tool", {
            "entity_type": entity_type,
            "operation": "list",
            "limit": 1
        })

        if not list_result.get("success"):
            return None

        entities = list_result.get("response", {}).get("data", [])
        if not entities:
            return None

        return entities[0].get("id")

    @staticmethod
    async def create_test_entity(client, entity_type: str, data_generator_func, **data_kwargs) -> str | None:
        """Create Atoms test entity and return ID, or None if create fails.

        This helper ensures proper CREATE→OPERATE→DELETE pattern with skip propagation.
        Automatically resolves parent IDs for nested Atoms entities:
        - project → organization_id
        - document → project_id
        - requirement → document_id
        - test → project_id

        Args:
            client: MCP client
            entity_type: Atoms entity type (organization, project, document, requirement, test)
            data_generator_func: Function that returns entity data dict
            **data_kwargs: Additional keyword arguments to pass to data_generator_func

        Returns:
            entity_id if create succeeded, None if failed (caller should skip/return)
        """

        # Auto-resolve parent IDs for Atoms nested entity types
        if entity_type == "project" and "organization_id" not in data_kwargs:
            org_id = await AtomsTestHelpers.get_or_create_organization(client)
            if org_id:
                data_kwargs["organization_id"] = org_id

        elif entity_type == "document" and "project_id" not in data_kwargs:
            project_id = await AtomsTestHelpers.get_or_create_project(client)
            if project_id:
                data_kwargs["project_id"] = project_id

        elif entity_type == "requirement" and "document_id" not in data_kwargs:
            doc_id = await AtomsTestHelpers.get_or_create_document(client)
            if doc_id:
                data_kwargs["document_id"] = doc_id

        elif entity_type == "test" and "project_id" not in data_kwargs:
            project_id = await AtomsTestHelpers.get_or_create_project(client)
            if project_id:
                data_kwargs["project_id"] = project_id

        data = data_generator_func(**data_kwargs)
        create_result = await client.call_tool("entity_tool", {
            "entity_type": entity_type,
            "operation": "create",
            "data": data
        })

        if not create_result.get("success"):
            return None

        return BaseValidator.extract_id(create_result.get("response", {}))

    @staticmethod
    async def get_or_create_organization(client) -> str | None:
        """Get existing Atoms organization ID or create a new test organization.

        Returns:
            organization_id if successful, None otherwise
        """
        # Try to get existing org first
        org_id = await AtomsTestHelpers.get_existing_entity_id(client, "organization")
        if org_id:
            return org_id

        # Create new org
        from .data_generators import DataGenerator
        return await AtomsTestHelpers.create_test_entity(
            client, "organization", DataGenerator.organization_data
        )

    @staticmethod
    async def get_or_create_project(client, organization_id: str | None = None) -> str | None:
        """Get existing Atoms project ID or create a new test project.

        Args:
            organization_id: Optional organization ID. If not provided, will get/create one.

        Returns:
            project_id if successful, None otherwise
        """
        # Get org_id if not provided
        if not organization_id:
            organization_id = await AtomsTestHelpers.get_or_create_organization(client)
            if not organization_id:
                return None

        # Try to get existing project first
        project_id = await AtomsTestHelpers.get_existing_entity_id(client, "project")
        if project_id:
            return project_id

        # Create new project
        from .data_generators import DataGenerator
        return await AtomsTestHelpers.create_test_entity(
            client, "project", DataGenerator.project_data,
            organization_id=organization_id
        )

    @staticmethod
    async def get_or_create_document(client, project_id: str | None = None) -> str | None:
        """Get existing Atoms document ID or create a new test document.

        Args:
            project_id: Optional project ID. If not provided, will get/create one.

        Returns:
            document_id if successful, None otherwise
        """
        # Get project_id if not provided
        if not project_id:
            project_id = await AtomsTestHelpers.get_or_create_project(client)
            if not project_id:
                return None

        # Try to get existing document first
        doc_id = await AtomsTestHelpers.get_existing_entity_id(client, "document")
        if doc_id:
            return doc_id

        # Create new document
        from .data_generators import DataGenerator
        return await AtomsTestHelpers.create_test_entity(
            client, "document", DataGenerator.document_data,
            project_id=project_id
        )


# Backward compatibility aliases
ResponseValidator = BaseValidator
