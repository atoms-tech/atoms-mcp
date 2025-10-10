"""Unified entity CRUD operations tool."""

from __future__ import annotations

import asyncio
import re
from datetime import UTC, datetime
from typing import Any, Literal

try:
    from .base import ToolBase
except ImportError:
    from tools.base import ToolBase

# Import logging
from schemas.validators import (
    ValidationError,
    validate_before_create,
    validate_before_update,
)

from schemas.constants import (
    REQUIRED_FIELDS,
    TABLES_WITHOUT_AUDIT_FIELDS,
    TABLES_WITHOUT_SOFT_DELETE,
    Fields,
    Tables,
)

# Import schema infrastructure
from schemas.enums import (
    EntityStatus,
    EntityType,
    OrganizationType,
    Priority,
)
from schemas.rls import (
    DocumentPolicy,
    OrganizationPolicy,
    PermissionDeniedError,
    ProjectPolicy,
    RequirementPolicy,
    TestPolicy,
)
from schemas.triggers import TriggerEmulator
from utils.logging_setup import get_logger

slug_pattern = re.compile(r"[^a-z0-9]+")


def _slugify(value: str) -> str:
    """Convert a string to a URL-friendly slug."""
    slug = slug_pattern.sub("-", value.strip().lower()).strip("-")
    return slug or "document"


class EntityManager(ToolBase):
    """Manages CRUD operations for all entity types."""

    def __init__(self):
        super().__init__()
        self.trigger_emulator = TriggerEmulator()
        # User context will be set when auth is validated

    def _is_uuid_format(self, value: str) -> bool:
        """Check if string is a valid UUID format."""
        import re
        uuid_pattern = re.compile(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
            re.IGNORECASE
        )
        return bool(uuid_pattern.match(value))

    def _get_rls_policy(self, entity_type: str):
        """Get RLS policy validator for entity type."""
        user_id = self._get_user_id()
        db_adapter = self._get_adapters()["database"]

        # Map entity types to policy classes
        policy_classes = {
            EntityType.ORGANIZATION.value: OrganizationPolicy,
            EntityType.PROJECT.value: ProjectPolicy,
            EntityType.DOCUMENT.value: DocumentPolicy,
            EntityType.REQUIREMENT.value: RequirementPolicy,
            EntityType.TEST.value: TestPolicy,
        }

        policy_class = policy_classes.get(entity_type.lower())
        if policy_class:
            return policy_class(user_id=user_id, db_adapter=db_adapter)
        return None

    def _get_entity_schema(self, entity_type: str) -> dict[str, Any]:
        """Get schema information for entity type using schemas.constants."""
        # Auto-generated fields (set by database)
        auto_fields = [Fields.ID, Fields.CREATED_AT, Fields.UPDATED_AT]

        schemas = {
            "organization": {
                "required_fields": list(REQUIRED_FIELDS.get("organization", set())),
                "auto_fields": auto_fields,
                "default_values": {Fields.IS_DELETED: False, Fields.TYPE: OrganizationType.TEAM.value},
                "relationships": ["members", "projects", "invitations"]
            },
            "project": {
                "required_fields": list(REQUIRED_FIELDS.get("project", set())),
                "auto_fields": auto_fields,
                "default_values": {Fields.IS_DELETED: False},
                "relationships": ["members", "documents", "organization"],
                "auto_slug": True
            },
            "document": {
                "required_fields": list(REQUIRED_FIELDS.get("document", set())),
                "auto_fields": auto_fields,
                "default_values": {Fields.IS_DELETED: False},
                "relationships": ["blocks", "requirements", "project"]
            },
            "requirement": {
                "required_fields": list(REQUIRED_FIELDS.get("requirement", set())),
                "auto_fields": auto_fields + [Fields.VERSION, Fields.EXTERNAL_ID],
                "default_values": {
                    Fields.IS_DELETED: False,
                    Fields.STATUS: EntityStatus.ACTIVE.value,
                    Fields.PROPERTIES: {},
                    Fields.PRIORITY: Priority.LOW.value,
                    Fields.TYPE: "component",
                    Fields.BLOCK_ID: None
                },
                "relationships": ["document", "tests", "trace_links"]
            },
            "test": {
                "required_fields": list(REQUIRED_FIELDS.get("test", set())),
                "auto_fields": auto_fields,
                "default_values": {
                    "is_active": True,
                    Fields.STATUS: EntityStatus.PENDING.value,
                    Fields.PRIORITY: Priority.MEDIUM.value
                },
                "relationships": ["requirements", "project"]
            },
            "user": {
                "required_fields": [Fields.ID],  # User/profile lookup by ID
                "auto_fields": [Fields.CREATED_AT, Fields.UPDATED_AT],
                "default_values": {},
                "relationships": ["organizations", "projects"]
            },
            "profile": {
                "required_fields": [Fields.ID],  # Profile lookup by ID
                "auto_fields": [Fields.CREATED_AT, Fields.UPDATED_AT],
                "default_values": {},
                "relationships": ["organizations", "projects"]
            }
        }
        return schemas.get(entity_type.lower(), {})

    def _apply_defaults(self, entity_type: str, data: dict[str, Any]) -> dict[str, Any]:
        """Apply default values and auto-generated fields."""
        schema = self._get_entity_schema(entity_type)
        result = data.copy()

        # Apply defaults
        for field, value in schema.get("default_values", {}).items():
            if field not in result:
                result[field] = value

        # Apply auto fields
        user_id = self._get_user_id()

        # Ensure created_by and updated_by are always set (required NOT NULL columns)
        if Fields.CREATED_BY not in result:
            if not user_id:
                raise ValueError(f"Cannot create {entity_type}: user_id not available in context. Check authentication.")
            result[Fields.CREATED_BY] = user_id

        # updated_by is also required on create for most tables
        if Fields.UPDATED_BY not in result:
            if not user_id:
                raise ValueError(f"Cannot create {entity_type}: user_id not available in context for updated_by.")
            result[Fields.UPDATED_BY] = user_id

        # Special handling for projects - set owned_by
        if entity_type.lower() == EntityType.PROJECT.value and "owned_by" not in result and user_id:
            result["owned_by"] = user_id

        # Generate external_id for requirements
        if entity_type.lower() == EntityType.REQUIREMENT.value and Fields.EXTERNAL_ID not in result:
            # This would be generated by the database trigger normally
            result[Fields.EXTERNAL_ID] = f"REQ-{int(datetime.now().timestamp())}"

        # Auto-generate slug for entities that need it
        if schema.get("auto_slug") and not result.get(Fields.SLUG) and result.get(Fields.NAME):
            result[Fields.SLUG] = _slugify(result[Fields.NAME])

        # Auto-generate slug for organizations and documents if not provided
        if entity_type.lower() in [EntityType.ORGANIZATION.value, EntityType.DOCUMENT.value]:
            if not result.get(Fields.SLUG) and result.get(Fields.NAME):
                result[Fields.SLUG] = _slugify(result[Fields.NAME])

        return result

    def _validate_required_fields(self, entity_type: str, data: dict[str, Any]) -> None:
        """Validate that required fields are present."""
        schema = self._get_entity_schema(entity_type)
        required = schema.get("required_fields", [])

        missing = [field for field in required if field not in data]
        if missing:
            raise ValueError(f"Missing required fields for {entity_type}: {missing}")

    async def _resolve_smart_defaults(self, entity_type: str, data: dict[str, Any]) -> dict[str, Any]:
        """Resolve smart defaults like 'auto' for organization_id."""
        result = data.copy()
        user_id = self._get_user_id()

        # Import workspace manager to get defaults
        from .workspace import _workspace_manager
        defaults = await _workspace_manager.get_smart_defaults(user_id)

        # Apply smart defaults
        if result.get(Fields.ORGANIZATION_ID) == "auto":
            if defaults[Fields.ORGANIZATION_ID]:
                result[Fields.ORGANIZATION_ID] = defaults[Fields.ORGANIZATION_ID]
            else:
                raise ValueError("No active organization found for 'auto' resolution")

        if result.get(Fields.PROJECT_ID) == "auto":
            if defaults[Fields.PROJECT_ID]:
                result[Fields.PROJECT_ID] = defaults[Fields.PROJECT_ID]
            else:
                raise ValueError("No active project found for 'auto' resolution")

        if result.get(Fields.DOCUMENT_ID) == "auto":
            if defaults[Fields.DOCUMENT_ID]:
                result[Fields.DOCUMENT_ID] = defaults[Fields.DOCUMENT_ID]
            else:
                raise ValueError("No active document found for 'auto' resolution")

        return result

    async def create_entity(
        self,
        entity_type: str,
        data: dict[str, Any],
        include_relations: bool = False
    ) -> dict[str, Any]:
        """Create a new entity."""
        # Resolve smart defaults
        data = await self._resolve_smart_defaults(entity_type, data)

        # Apply defaults and validate
        data = self._apply_defaults(entity_type, data)
        self._validate_required_fields(entity_type, data)

        # Validate data against database schema
        try:
            validate_before_create(entity_type, data)
        except ValidationError as e:
            raise ValueError(f"Schema validation failed: {e}")

        # Get table name
        table = self._resolve_entity_table(entity_type)

        # Set user context for trigger emulation
        user_id = self._get_user_id()
        if user_id:
            self.trigger_emulator.set_user_context(user_id)

        # Emulate BEFORE INSERT triggers - transform data
        try:
            data = self.trigger_emulator.before_insert(table, data)
        except ValueError as e:
            raise ValueError(f"Trigger validation failed: {e}")

        # Validate RLS policy before insert
        policy = self._get_rls_policy(entity_type)
        if policy:
            try:
                await policy.validate_insert(data)
            except PermissionDeniedError as e:
                raise ValueError(f"Permission denied: {e.reason}")

        # Create entity
        result = await self._db_insert(table, data, returning="*")

        # Emulate AFTER INSERT triggers - handle side effects
        side_effects = self.trigger_emulator.after_insert(table, result)
        for effect_table, effect_data in side_effects:
            try:
                await self._db_insert(effect_table, effect_data)
            except Exception as e:
                # Log side effect failures but don't fail the main operation
                logger = get_logger(__name__)
                logger.warning(f"Side effect insert failed for {effect_table}: {e}")

        # Skip relationship inclusion for create to avoid Supabase client issues
        # Relationships can be fetched separately with read operation if needed

        # Generate embedding asynchronously for searchable entities
        # This runs in background and won't block the response
        if entity_type in ["organization", "project", "document", "requirement"]:
            asyncio.create_task(self._generate_embedding_async(entity_type, result))

        return result

    async def _generate_embedding_async(self, entity_type: str, entity_data: dict[str, Any]):
        """Generate embedding for entity in background.

        This method runs asynchronously and won't block entity creation.
        Errors are logged but don't fail the entity creation operation.
        """
        try:
            from config.vector import (
                get_embedding_service,
                get_progressive_embedding_service,
            )

            # Initialize services
            embedding_service = get_embedding_service()
            progressive_service = get_progressive_embedding_service(self.supabase)

            # Get table name for this entity type
            table_name = progressive_service._get_table_name(entity_type)

            # Generate embedding
            await progressive_service.generate_embedding_on_demand(
                table_name,
                entity_data["id"],
                entity_data
            )

        except Exception as e:
            # Log error but don't fail entity creation
            # In production, this should use proper logging
            print(f"Warning: Failed to generate embedding for {entity_type} {entity_data.get('id')}: {e}")

    async def read_entity(
        self,
        entity_type: str,
        entity_id: str,
        include_relations: bool = False
    ) -> dict[str, Any] | None:
        """Read an entity by ID."""
        table = self._resolve_entity_table(entity_type)

        result = await self._db_get_single(
            table,
            filters={"id": entity_id}
        )

        # Validate RLS policy after fetch
        if result:
            policy = self._get_rls_policy(entity_type)
            if policy:
                try:
                    await policy.validate_select(result)
                except PermissionDeniedError as e:
                    raise ValueError(f"Permission denied: {e.reason}")

        if result and include_relations:
            result = await self._include_relationships(entity_type, result)

        return result

    async def update_entity(
        self,
        entity_type: str,
        entity_id: str,
        data: dict[str, Any],
        include_relations: bool = False
    ) -> dict[str, Any]:
        """Update an entity."""
        logger = get_logger(__name__)

        # Validate data against database schema (for updates, partial data is OK)
        try:
            validate_before_update(entity_type, data)
        except ValidationError as e:
            raise ValueError(f"Schema validation failed: {e}")

        table = self._resolve_entity_table(entity_type)

        # Fetch existing record for RLS validation
        existing_record = await self._db_get_single(
            table,
            filters={"id": entity_id}
        )

        if not existing_record:
            raise ValueError(f"{entity_type} with ID '{entity_id}' not found")

        # Validate RLS policy before update
        policy = self._get_rls_policy(entity_type)
        if policy:
            try:
                await policy.validate_update(existing_record, data)
            except PermissionDeniedError as e:
                raise ValueError(f"Permission denied: {e.reason}")

        # Get user_id for trigger emulation with fallback
        user_id = self._get_user_id()
        if not user_id and table not in TABLES_WITHOUT_AUDIT_FIELDS:
            # Fallback: Get from existing record
            print("⚠️ UPDATE: No user_id in context, using fallback from existing record")
            logger.info("⚠️ UPDATE: No user_id in context, using fallback from existing record")
            user_id = existing_record.get(Fields.CREATED_BY) or existing_record.get(Fields.UPDATED_BY)
            if user_id:
                print(f"✅ UPDATE: Got user_id from existing record: {user_id}")
                logger.info(f"✅ UPDATE: Got user_id from existing record: {user_id}")

        # Validate user_id is available for tables that require it
        if not user_id and table not in TABLES_WITHOUT_AUDIT_FIELDS:
            print(f"❌ UPDATE: Could not determine user_id. Context: {self._user_context}")
            logger.error(f"❌ UPDATE: Could not determine user_id. Context: {self._user_context}")
            raise ValueError(f"Could not determine user_id for update operation. Context: {self._user_context}")

        # Set user context for trigger emulation
        if user_id:
            self.trigger_emulator.set_user_context(user_id)

        # Emulate BEFORE UPDATE triggers - transform data
        try:
            update_data = self.trigger_emulator.before_update(table, existing_record, data)
        except ValueError as e:
            raise ValueError(f"Trigger validation failed: {e}")

        # Update entity
        result = await self._db_update(
            table,
            update_data,
            filters={"id": entity_id},
            returning="*"
        )

        # Emulate AFTER UPDATE triggers - handle side effects (mainly for soft delete cascading)
        side_effects = self.trigger_emulator.after_update(table, existing_record, result)
        for effect_table, effect_data in side_effects:
            try:
                await self._db_insert(effect_table, effect_data)
            except Exception as e:
                # Log side effect failures but don't fail the main operation
                logger.warning(f"Side effect from update failed for {effect_table}: {e}")

        if include_relations and isinstance(result, dict):
            result = await self._include_relationships(entity_type, result)

        return result

    async def delete_entity(
        self,
        entity_type: str,
        entity_id: str,
        soft_delete: bool = True
    ) -> bool:
        """Delete an entity (soft delete by default)."""
        table = self._resolve_entity_table(entity_type)

        # Fetch existing record for RLS validation
        existing_record = await self._db_get_single(
            table,
            filters={"id": entity_id}
        )

        if not existing_record:
            raise ValueError(f"{entity_type} with ID '{entity_id}' not found")

        # Validate RLS policy before delete
        policy = self._get_rls_policy(entity_type)
        if policy:
            try:
                await policy.validate_delete(existing_record)
            except PermissionDeniedError as e:
                raise ValueError(f"Permission denied: {e.reason}")

        if soft_delete:
            # Soft delete
            delete_data = {
                Fields.IS_DELETED: True,
                Fields.DELETED_AT: datetime.now(UTC).isoformat()
                # Don't set updated_at - let database trigger handle it
            }

            # Get user_id with fallback
            user_id = self._get_user_id()
            if not user_id:
                # Fallback: Query existing record to get created_by
                try:
                    result = self.supabase.table(table).select(f"{Fields.CREATED_BY}, {Fields.UPDATED_BY}").eq(Fields.ID, entity_id).execute()
                    if result.data and len(result.data) > 0:
                        user_id = result.data[0].get(Fields.CREATED_BY) or result.data[0].get(Fields.UPDATED_BY)
                except Exception:
                    pass

            # Ensure user fields are set
            if not user_id:
                raise ValueError(f"Could not determine user_id for delete operation. Context: {self._user_context}")

            delete_data[Fields.DELETED_BY] = user_id
            delete_data[Fields.UPDATED_BY] = user_id

            result = await self._db_update(
                table,
                delete_data,
                filters={"id": entity_id}
            )
            return bool(result)
        # Hard delete
        count = await self._db_delete(table, filters={"id": entity_id})
        return count > 0

    async def search_entities(
        self,
        entity_type: str,
        filters: dict[str, Any] | None = None,
        search_term: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        order_by: str | None = None
    ) -> list[dict[str, Any]]:
        """Search for entities with filters."""
        table = self._resolve_entity_table(entity_type)

        # Build query filters
        query_filters = filters.copy() if filters else {}

        # Add default filters (but skip is_deleted for tables that don't have it)
        if Fields.IS_DELETED not in query_filters and table not in TABLES_WITHOUT_SOFT_DELETE:
            query_filters[Fields.IS_DELETED] = False

        # Handle search term
        if search_term:
            # This is simplified - in practice you'd use full-text search
            query_filters[Fields.NAME] = {"ilike": f"%{search_term}%"}

        # Set default ordering
        if not order_by:
            order_by = "created_at:desc"

        # Safety: Enforce maximum limit to prevent oversized responses
        # Cap at 100, default to 20 if not specified (for MCP token limits)
        if limit is None:
            limit = 20
        elif limit > 100:
            limit = 100

        return await self._db_query(
            table,
            filters=query_filters,
            limit=limit,
            offset=offset,
            order_by=order_by
        )

    async def list_entities(
        self,
        entity_type: str,
        parent_type: str | None = None,
        parent_id: str | None = None,
        limit: int | None = None
    ) -> list[dict[str, Any]]:
        """List entities, optionally filtered by parent."""
        # Build filters - skip is_deleted for tables that don't have it
        table = self._resolve_entity_table(entity_type)

        filters = {}
        if table not in TABLES_WITHOUT_SOFT_DELETE:
            filters[Fields.IS_DELETED] = False

        # Add parent filter
        if parent_type and parent_id:
            parent_key = f"{parent_type}_id"
            filters[parent_key] = parent_id

        # Safety: Always enforce a maximum limit to prevent oversized responses
        # Default to 20, max 100 for MCP token limits
        if limit is None:
            limit = 20
        elif limit > 100:
            limit = 100

        return await self.search_entities(
            entity_type,
            filters=filters,
            limit=limit
        )

    async def _include_relationships(
        self,
        entity_type: str,
        entity: dict[str, Any]
    ) -> dict[str, Any]:
        """Include related entities in the response."""
        result = entity.copy()
        entity_id = entity[Fields.ID]

        if entity_type.lower() == EntityType.ORGANIZATION.value:
            # Include member count and recent projects
            member_count = await self._db_count(
                Tables.ORGANIZATION_MEMBERS,
                filters={Fields.ORGANIZATION_ID: entity_id, Fields.STATUS: "active"}
            )
            result["member_count"] = member_count

            recent_projects = await self._db_query(
                Tables.PROJECTS,
                filters={Fields.ORGANIZATION_ID: entity_id, Fields.IS_DELETED: False},
                limit=5,
                order_by=f"{Fields.UPDATED_AT}:desc"
            )
            result["recent_projects"] = recent_projects

        elif entity_type.lower() == EntityType.PROJECT.value:
            # Include document count and members
            doc_count = await self._db_count(
                Tables.DOCUMENTS,
                filters={Fields.PROJECT_ID: entity_id, Fields.IS_DELETED: False}
            )
            result["document_count"] = doc_count

            members = await self._db_query(
                Tables.PROJECT_MEMBERS,
                select=f"*, {Tables.PROFILES}(*)",
                filters={Fields.PROJECT_ID: entity_id, Fields.STATUS: "active"}
            )
            result["members"] = members

        elif entity_type.lower() == EntityType.DOCUMENT.value:
            # Include requirement count and blocks
            req_count = await self._db_count(
                Tables.REQUIREMENTS,
                filters={Fields.DOCUMENT_ID: entity_id, Fields.IS_DELETED: False}
            )
            result["requirement_count"] = req_count

            blocks = await self._db_query(
                Tables.BLOCKS,
                filters={Fields.DOCUMENT_ID: entity_id, Fields.IS_DELETED: False},
                order_by="position"
            )
            result["blocks"] = blocks

        return result


# Global manager instance
_entity_manager = EntityManager()


async def entity_operation(
    auth_token: str,
    operation: Literal["create", "read", "update", "delete", "search", "list"],
    entity_type: str,
    data: dict[str, Any] | None = None,
    filters: dict[str, Any] | None = None,
    entity_id: str | None = None,
    include_relations: bool = False,
    batch: list[dict[str, Any]] | None = None,
    search_term: str | None = None,
    parent_type: str | None = None,
    parent_id: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
    order_by: str | None = None,
    soft_delete: bool = True,
    format_type: str = "detailed"
) -> dict[str, Any]:
    """Unified CRUD operations with performance timing."""
    import time
    timings = {}
    start_total = time.time()

    try:
        # Validate authentication
        t_auth_start = time.time()
        await _entity_manager._validate_auth(auth_token)
        timings["auth_validation"] = time.time() - t_auth_start

        # Fuzzy resolution for entity_id if needed
        if entity_id and not _entity_manager._is_uuid_format(entity_id):
            t_resolve_start = time.time()
            from tools.entity_resolver import EntityResolver
            resolver = EntityResolver(_entity_manager._get_adapters()["database"])
            resolution = await resolver.resolve_entity_id(
                entity_type,
                entity_id,
                filters=filters,
                threshold=70
            )
            timings["fuzzy_resolution"] = time.time() - t_resolve_start

            if not resolution["success"]:
                # Return suggestions if available
                if "suggestions" in resolution:
                    return {
                        "success": False,
                        "error": resolution["error"],
                        "suggestions": resolution["suggestions"],
                        "hint": "Use the exact entity_id from suggestions or be more specific"
                    }
                return {"success": False, "error": resolution["error"]}

            # Use resolved entity_id
            entity_id = resolution["entity_id"]
            if "note" in resolution:
                # Store note about fuzzy match for user awareness
                timings["fuzzy_match_note"] = resolution["note"]

        if operation == "create":
            if not data:
                raise ValueError("data is required for create operation")

            t_op_start = time.time()
            if batch:
                # Batch create with parallelization
                tasks = [
                    _entity_manager.create_entity(entity_type, item, include_relations)
                    for item in batch
                ]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Handle exceptions
                final_results = []
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        final_results.append({"error": str(result), "index": i})
                    else:
                        final_results.append(result)

                timings["batch_create"] = time.time() - t_op_start
                timings["total"] = time.time() - start_total
                formatted = _entity_manager._format_result(final_results, format_type)
                return _entity_manager._add_timing_metrics(formatted, timings)
            # Single create
            result = await _entity_manager.create_entity(
                entity_type, data, include_relations
            )
            timings["create"] = time.time() - t_op_start
            timings["total"] = time.time() - start_total
            formatted = _entity_manager._format_result(result, format_type)
            return _entity_manager._add_timing_metrics(formatted, timings)

        if operation == "read":
            if not entity_id:
                raise ValueError("entity_id is required for read operation")

            t_op_start = time.time()
            result = await _entity_manager.read_entity(
                entity_type, entity_id, include_relations
            )
            timings["read"] = time.time() - t_op_start

            if result is None:
                # Entity not found - provide helpful suggestions
                from tools.entity_resolver import EntityResolver
                resolver = EntityResolver(_entity_manager._get_adapters()["database"])

                # Search for similar entities
                suggestions_result = await resolver.resolve_entity_id(
                    entity_type,
                    entity_id,
                    filters=filters,
                    threshold=50,  # Lower threshold for suggestions
                    return_suggestions=True
                )

                error_response = {
                    "success": False,
                    "error": f"{entity_type} with ID '{entity_id}' not found"
                }

                if "suggestions" in suggestions_result:
                    error_response["suggestions"] = suggestions_result["suggestions"]
                    error_response["hint"] = "Did you mean one of these? Use the exact ID or name from suggestions."

                return error_response

            timings["total"] = time.time() - start_total
            formatted = _entity_manager._format_result(result, format_type)
            return _entity_manager._add_timing_metrics(formatted, timings)

        if operation == "update":
            if not entity_id or not data:
                raise ValueError("entity_id and data are required for update operation")

            t_op_start = time.time()
            result = await _entity_manager.update_entity(
                entity_type, entity_id, data, include_relations
            )
            timings["update"] = time.time() - t_op_start
            timings["total"] = time.time() - start_total
            formatted = _entity_manager._format_result(result, format_type)
            return _entity_manager._add_timing_metrics(formatted, timings)

        if operation == "delete":
            if not entity_id:
                raise ValueError("entity_id is required for delete operation")

            t_op_start = time.time()
            success = await _entity_manager.delete_entity(
                entity_type, entity_id, soft_delete
            )
            timings["delete"] = time.time() - t_op_start
            timings["total"] = time.time() - start_total

            result = {
                "success": success,
                "entity_id": entity_id,
                "entity_type": entity_type,
                "soft_delete": soft_delete
            }
            return _entity_manager._add_timing_metrics(result, timings)

        if operation == "search":
            t_op_start = time.time()
            result = await _entity_manager.search_entities(
                entity_type, filters, search_term, limit, offset, order_by
            )
            timings["search"] = time.time() - t_op_start
            timings["total"] = time.time() - start_total
            formatted = _entity_manager._format_result(result, format_type)
            return _entity_manager._add_timing_metrics(formatted, timings)

        if operation == "list":
            t_op_start = time.time()
            result = await _entity_manager.list_entities(
                entity_type, parent_type, parent_id, limit
            )
            timings["list"] = time.time() - t_op_start
            timings["total"] = time.time() - start_total
            formatted = _entity_manager._format_result(result, format_type)
            return _entity_manager._add_timing_metrics(formatted, timings)

        raise ValueError(f"Unknown operation: {operation}")

    except PermissionDeniedError as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": "permission_denied",
            "table": e.table,
            "operation": operation,
            "entity_type": entity_type
        }
    except ValueError as e:
        # Check if this is a permission error (converted from PermissionDeniedError)
        error_msg = str(e)
        error_type = "permission_denied" if "Permission denied:" in error_msg else "validation_error"
        return {
            "success": False,
            "error": error_msg,
            "error_type": error_type,
            "operation": operation,
            "entity_type": entity_type
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": "server_error",
            "operation": operation,
            "entity_type": entity_type
        }
