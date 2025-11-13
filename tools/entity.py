"""Unified entity CRUD operations tool."""

from __future__ import annotations

import re
import asyncio
from typing import Dict, Any, Optional, List, Literal
from datetime import datetime, timezone

try:
    from .base import ToolBase
except ImportError:
    from tools.base import ToolBase

# Import schema helpers for Pydantic validation
try:
    from schemas.helpers import (
        partial_validate,
        get_required_fields,
        get_model_fields,
    )
    _HAS_SCHEMAS = True
except ImportError:
    _HAS_SCHEMAS = False


slug_pattern = re.compile(r"[^a-z0-9]+")


def _slugify(value: str) -> str:
    """Convert a string to a URL-friendly slug."""
    if value is None:
        return "document"
    slug = slug_pattern.sub("-", value.strip().lower()).strip("-")
    return slug or "document"


class EntityManager(ToolBase):
    """Manages CRUD operations for all entity types."""

    def __init__(self) -> None:
        super().__init__()

    def _is_uuid_format(self, value: str) -> bool:
        """Check if string is a valid UUID format."""
        if value is None:
            return False
        import re
        uuid_pattern = re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            re.IGNORECASE
        )
        return bool(uuid_pattern.match(value))
    
    def _get_entity_schema(self, entity_type: str) -> Dict[str, Any]:
        """Get schema information for entity type.

        Uses manual schemas which define auto_slug and other logic.
        Pydantic models are strict and don't understand our auto-generation patterns.
        """
        # Manual schemas - source of truth for our auto-generation patterns
        schemas = {
            "organization": {
                "required_fields": ["name"],
                "auto_fields": ["id", "created_at", "updated_at"],
                "default_values": {"is_deleted": False, "type": "team"},
                "relationships": ["members", "projects", "invitations"],
                "auto_slug": True
            },
            "project": {
                "required_fields": ["name", "organization_id"],
                "auto_fields": ["id", "created_at", "updated_at"],
                "default_values": {"is_deleted": False},
                "relationships": ["members", "documents", "organization"],
                "auto_slug": True
            },
            "document": {
                "required_fields": ["name", "project_id"],
                "auto_fields": ["id", "created_at", "updated_at"],
                "default_values": {"is_deleted": False},
                "relationships": ["blocks", "requirements", "project"],
                "auto_slug": True
            },
            "requirement": {
                "required_fields": ["name", "document_id"],
                "auto_fields": ["id", "created_at", "updated_at", "version", "external_id"],
                "default_values": {"is_deleted": False, "status": "active", "properties": {}, "priority": "low", "type": "component", "block_id": None},
                "relationships": ["document", "tests", "trace_links"]
            },
            "test": {
                "required_fields": ["title", "project_id"],
                "auto_fields": ["id", "created_at", "updated_at"],
                "default_values": {"is_active": True, "status": "pending", "priority": "medium"},
                "relationships": ["requirements", "project"]
            },
            "user": {
                "required_fields": ["id"],
                "auto_fields": ["created_at", "updated_at"],
                "default_values": {},
                "relationships": ["organizations", "projects"]
            },
            "profile": {
                "required_fields": ["id"],
                "auto_fields": ["created_at", "updated_at"],
                "default_values": {},
                "relationships": ["organizations", "projects"]
            }
        }
        return schemas.get(entity_type.lower(), {})
    
    def _apply_defaults(self, entity_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
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
        if "created_by" not in result:
            if not user_id:
                raise ValueError(f"Cannot create {entity_type}: user_id not available in context. Check authentication.")
            result["created_by"] = user_id

        # updated_by is also required on create for most tables
        if "updated_by" not in result:
            if not user_id:
                raise ValueError(f"Cannot create {entity_type}: user_id not available in context for updated_by.")
            result["updated_by"] = user_id

        # Special handling for projects - set owned_by
        if entity_type.lower() == "project" and "owned_by" not in result and user_id:
            result["owned_by"] = user_id
        
        # Generate external_id for requirements
        if entity_type.lower() == "requirement" and "external_id" not in result:
            # This would be generated by the database trigger normally
            result["external_id"] = f"REQ-{int(datetime.now().timestamp())}"

        # Auto-generate slug for entities that need it
        if schema.get("auto_slug") and not result.get("slug") and result.get("name"):
            result["slug"] = _slugify(result["name"])

        # Auto-generate slug for organizations and documents if not provided
        if entity_type.lower() in ["organization", "document"]:
            if not result.get("slug") and result.get("name"):
                result["slug"] = _slugify(result["name"])
        
        return result
    
    def _validate_required_fields(self, entity_type: str, data: Dict[str, Any]) -> None:
        """Validate that required fields are present."""
        schema = self._get_entity_schema(entity_type)
        required = schema.get("required_fields", [])
        auto_fields = schema.get("auto_fields", [])
        
        # Exclude auto-generated fields from validation
        required_non_auto = [field for field in required if field not in auto_fields]
        
        missing = [field for field in required_non_auto if field not in data]
        if missing:
            raise ValueError(f"Missing required fields for {entity_type}: {missing}")
    
    async def _resolve_smart_defaults(self, entity_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve smart defaults like 'auto' for organization_id."""
        result = data.copy()
        user_id = self._get_user_id()
        
        # Import workspace manager to get defaults
        from .workspace import _workspace_manager
        defaults = await _workspace_manager.get_smart_defaults(user_id)
        
        # Apply smart defaults
        if result.get("organization_id") == "auto":
            if defaults["organization_id"]:
                result["organization_id"] = defaults["organization_id"]
            else:
                raise ValueError("No active organization found for 'auto' resolution")
        
        if result.get("project_id") == "auto":
            if defaults["project_id"]:
                result["project_id"] = defaults["project_id"]
            else:
                raise ValueError("No active project found for 'auto' resolution")
        
        if result.get("document_id") == "auto":
            if defaults["document_id"]:
                result["document_id"] = defaults["document_id"]
            else:
                raise ValueError("No active document found for 'auto' resolution")
        
        return result
    
    async def create_entity(
        self,
        entity_type: str,
        data: Dict[str, Any],
        include_relations: bool = False
    ) -> Dict[str, Any]:
        """Create a new entity with Pydantic validation."""
        # Resolve smart defaults
        data = await self._resolve_smart_defaults(entity_type, data)

        # Apply defaults
        data = self._apply_defaults(entity_type, data)

        # Validate with Pydantic if available
        if _HAS_SCHEMAS:
            try:
                data = partial_validate(entity_type, data)
            except Exception as e:
                # Log validation error but continue with manual validation
                print(f"Pydantic validation warning for {entity_type}: {e}")

        # Manual validation (fallback)
        self._validate_required_fields(entity_type, data)

        # Get table name
        table = self._resolve_entity_table(entity_type)

        # Create entity
        result = await self._db_insert(table, data, returning="*")

        # Skip relationship inclusion for create to avoid Supabase client issues
        # Relationships can be fetched separately with read operation if needed

        # Generate embedding asynchronously for searchable entities
        # This runs in background and won't block the response
        if entity_type in ["organization", "project", "document", "requirement"]:
            asyncio.create_task(self._generate_embedding_async(entity_type, result))

        return result

    async def _generate_embedding_async(self, entity_type: str, entity_data: Dict[str, Any]):
        """Generate embedding for entity in background.

        This method runs asynchronously and won't block entity creation.
        Errors are logged but don't fail the entity creation operation.
        """
        try:
            from services.progressive_embedding import ProgressiveEmbeddingService
            from services.embedding_factory import get_embedding_service

            # Initialize services
            embedding_service = get_embedding_service()
            progressive_service = ProgressiveEmbeddingService(self.supabase, embedding_service)

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
    ) -> Optional[Dict[str, Any]]:
        """Read an entity by ID."""
        table = self._resolve_entity_table(entity_type)
        
        result = await self._db_get_single(
            table,
            filters={"id": entity_id}
        )
        
        if result and include_relations:
            result = await self._include_relationships(entity_type, result)
        
        return result
    
    async def update_entity(
        self,
        entity_type: str,
        entity_id: str,
        data: Dict[str, Any],
        include_relations: bool = False
    ) -> Dict[str, Any]:
        """Update an entity with Pydantic validation."""
        import logging
        logger = logging.getLogger(__name__)

        table = self._resolve_entity_table(entity_type)

        # Prepare update data
        update_data = data.copy()

        # Validate with Pydantic if available (partial validation for updates)
        if _HAS_SCHEMAS:
            try:
                update_data = partial_validate(entity_type, update_data)
            except Exception as e:
                # Log validation error but continue
                print(f"Pydantic validation warning for {entity_type} update: {e}")
        # Don't set updated_at manually - let database trigger handle it
        # This prevents "Concurrent update detected" errors from optimistic locking

        # Tables that don't have updated_by column
        tables_without_updated_by = {'profiles', 'test_req', 'properties'}

        # Set updated_by if the table has this column
        if table not in tables_without_updated_by:
            user_id = self._get_user_id()
            print(f"🔍 UPDATE: user_id from context: '{user_id}', full context: {self._user_context}")
            logger.info(f"🔍 UPDATE: user_id from context: '{user_id}', full context: {self._user_context}")

            if not user_id:
                # Fallback: Query existing record to get created_by
                print("⚠️ UPDATE: No user_id in context, using fallback query")
                logger.info("⚠️ UPDATE: No user_id in context, using fallback query")
                try:
                    # Use RLS-compliant database adapter instead of bypassing RLS
                    result = await self._db_get_single(
                        table,
                        filters={"id": entity_id},
                        select="created_by, updated_by"
                    )
                    print(f"🔍 UPDATE: Fallback query result: {result if result else 'None'}")
                    logger.info(f"🔍 UPDATE: Fallback query result: {result if result else 'None'}")
                    if result:
                        user_id = result.get("created_by") or result.get("updated_by")
                        print(f"✅ UPDATE: Got user_id from fallback: {user_id}")
                        logger.info(f"✅ UPDATE: Got user_id from fallback: {user_id}")
                except Exception as e:
                    print(f"❌ UPDATE: Fallback query failed: {e}")
                    logger.error(f"❌ UPDATE: Fallback query failed: {e}")
                    pass

            # Ensure updated_by is always set for tables that require it
            if not user_id:
                print(f"❌ UPDATE: Could not determine user_id. Context: {self._user_context}")
                logger.error(f"❌ UPDATE: Could not determine user_id. Context: {self._user_context}")
                raise ValueError(f"Could not determine user_id for update operation. Context: {self._user_context}")

            update_data["updated_by"] = user_id
            print(f"✅ UPDATE: Set updated_by to: {user_id}")
            logger.info(f"✅ UPDATE: Set updated_by to: {user_id}")

        result = await self._db_update(
            table,
            update_data,
            filters={"id": entity_id},
            returning="*"
        )

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
        
        if soft_delete:
            # Soft delete
            delete_data = {
                "is_deleted": True,
                "deleted_at": datetime.now(timezone.utc).isoformat()
                # Don't set updated_at - let database trigger handle it
            }

            # Get user_id with fallback
            user_id = self._get_user_id()
            if not user_id:
                # Fallback: Query existing record to get created_by
                try:
                    result = self.supabase.table(table).select("created_by, updated_by").eq("id", entity_id).execute()
                    if result.data and len(result.data) > 0:
                        user_id = result.data[0].get("created_by") or result.data[0].get("updated_by")
                except Exception:
                    pass

            # Ensure user fields are set
            if not user_id:
                raise ValueError(f"Could not determine user_id for delete operation. Context: {self._user_context}")

            delete_data["deleted_by"] = user_id
            delete_data["updated_by"] = user_id
            
            result = await self._db_update(
                table,
                delete_data,
                filters={"id": entity_id}
            )
            return bool(result)
        else:
            # Hard delete
            count = await self._db_delete(table, filters={"id": entity_id})
            return count > 0
    
    async def search_entities(
        self,
        entity_type: str,
        filters: Optional[Dict[str, Any]] = None,
        search_term: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for entities with filters."""
        table = self._resolve_entity_table(entity_type)

        # Build query filters
        query_filters = filters.copy() if filters else {}

        # Add default filters (but skip is_deleted for tables that don't have it)
        # test_req and properties tables don't have is_deleted column
        tables_without_soft_delete = {'test_req', 'properties'}
        if "is_deleted" not in query_filters and table not in tables_without_soft_delete:
            query_filters["is_deleted"] = False

        # Handle search term - search across multiple fields
        if search_term:
            # Search across name, description, content, and properties fields
            # Build OR filter for multi-field search
            search_pattern = f"%{search_term}%"
            search_fields = []

            # Always search name
            search_fields.append({"name": {"ilike": search_pattern}})

            # Add description if the table has it
            if table not in {'test_req', 'blocks'}:
                search_fields.append({"description": {"ilike": search_pattern}})

            # Add content for documents and blocks
            if table in {'documents', 'blocks', 'requirements'}:
                search_fields.append({"content": {"ilike": search_pattern}})

            # Add properties search for JSON fields (if supported by your schema)
            # This searches within JSON properties
            if table in {'requirements', 'tests'}:
                # Note: This requires Supabase supports JSON search operators
                # If properties is JSONB, we could search it
                search_fields.append({"properties": {"contains": search_term}})

            # Use OR logic for multi-field search
            if len(search_fields) > 1:
                query_filters["_or"] = search_fields
            elif len(search_fields) == 1:
                query_filters.update(search_fields[0])

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
    
    async def bulk_update_entities(
        self,
        entity_type: str,
        entity_ids: List[str],
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Bulk update multiple entities with the same data.
        
        Args:
            entity_type: Type of entities to update
            entity_ids: List of entity IDs to update
            data: Data to apply to all entities
        
        Returns:
            Dict with updated count, failed count, and details
        """
        if not entity_ids:
            return {"updated": 0, "failed": 0, "errors": []}
        
        table = self._resolve_entity_table(entity_type)
        updated_count = 0
        failed_count = 0
        errors = []
        
        # Update each entity (or use batch update if database supports it)
        for entity_id in entity_ids:
            try:
                result = await self.update_entity(entity_type, entity_id, data, include_relations=False)
                if result:
                    updated_count += 1
            except Exception as e:
                failed_count += 1
                errors.append({"entity_id": entity_id, "error": str(e)})
        
        return {
            "updated": updated_count,
            "failed": failed_count,
            "total": len(entity_ids),
            "errors": errors if errors else None
        }
    
    async def bulk_delete_entities(
        self,
        entity_type: str,
        entity_ids: List[str],
        soft_delete: bool = True
    ) -> Dict[str, Any]:
        """Bulk delete (soft-delete or hard-delete) multiple entities.
        
        Args:
            entity_type: Type of entities to delete
            entity_ids: List of entity IDs to delete
            soft_delete: If True, soft-delete (is_deleted=true); if False, hard-delete
        
        Returns:
            Dict with deleted count, failed count, and details
        """
        if not entity_ids:
            return {"deleted": 0, "failed": 0, "errors": []}
        
        deleted_count = 0
        failed_count = 0
        errors = []
        
        # Delete each entity
        for entity_id in entity_ids:
            try:
                success = await self.delete_entity(entity_type, entity_id, soft_delete=soft_delete)
                if success:
                    deleted_count += 1
            except Exception as e:
                failed_count += 1
                errors.append({"entity_id": entity_id, "error": str(e)})
        
        return {
            "deleted": deleted_count,
            "failed": failed_count,
            "total": len(entity_ids),
            "soft_delete": soft_delete,
            "errors": errors if errors else None
        }
    
    async def bulk_archive_entities(
        self,
        entity_type: str,
        entity_ids: List[str]
    ) -> Dict[str, Any]:
        """Bulk archive (soft-delete) multiple entities.
        
        Args:
            entity_type: Type of entities to archive
            entity_ids: List of entity IDs to archive
        
        Returns:
            Dict with archived count, failed count, and details
        """
        if not entity_ids:
            return {"archived": 0, "failed": 0, "errors": []}
        
        archived_count = 0
        failed_count = 0
        errors = []
        
        # Archive each entity (soft-delete)
        for entity_id in entity_ids:
            try:
                success = await self.delete_entity(entity_type, entity_id, soft_delete=True)
                if success:
                    archived_count += 1
            except Exception as e:
                failed_count += 1
                errors.append({"entity_id": entity_id, "error": str(e)})
        
        return {
            "archived": archived_count,
            "failed": failed_count,
            "total": len(entity_ids),
            "errors": errors if errors else None
        }
    
    async def get_entity_history(
        self,
        entity_type: str,
        entity_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get version history for an entity.
        
        Args:
            entity_type: Type of entity
            entity_id: Entity ID to get history for
            limit: Number of versions to return
            offset: Offset for pagination
        
        Returns:
            Dict with versions, total count, and pagination info
        """
        # For now, return a placeholder implementation
        # In production, this would query from entity_versions table
        return {
            "entity_id": entity_id,
            "entity_type": entity_type,
            "versions": [],
            "total": 0,
            "limit": limit,
            "offset": offset,
            "note": "Version history tracking not yet configured in database"
        }
    
    async def restore_entity_version(
        self,
        entity_type: str,
        entity_id: str,
        version: int
    ) -> Dict[str, Any]:
        """Restore entity to a specific version.
        
        Args:
            entity_type: Type of entity
            entity_id: Entity ID to restore
            version: Version number to restore to
        
        Returns:
            Dict with restored entity and new version info
        """
        # For now, return a placeholder implementation
        # In production, this would restore from entity_versions table
        return {
            "success": False,
            "entity_id": entity_id,
            "entity_type": entity_type,
            "version": version,
            "note": "Version restore not yet configured in database"
        }
    
    async def get_entity_trace(
        self,
        entity_type: str,
        entity_id: str
    ) -> Dict[str, Any]:
        """Get traceability information for an entity.
        
        Args:
            entity_type: Type of entity
            entity_id: Entity ID to get trace for
        
        Returns:
            Dict with related entities and trace information
        """
        # For now, return a placeholder implementation
        # In production, this would query from relationship tables
        return {
            "entity_id": entity_id,
            "entity_type": entity_type,
            "trace_links": [],
            "linked_tests": [],
            "linked_requirements": [],
            "total_links": 0,
            "note": "Traceability feature requires database configuration"
        }
    
    async def get_entity_coverage(
        self,
        entity_type: str,
        parent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get coverage analysis for entities.
        
        Args:
            entity_type: Type of entity to analyze
            parent_id: Optional parent ID for scoped analysis
        
        Returns:
            Dict with coverage statistics
        """
        # For now, return a placeholder implementation
        # In production, this would analyze requirement-to-test relationships
        return {
            "entity_type": entity_type,
            "parent_id": parent_id,
            "coverage_percentage": 0.0,
            "covered_count": 0,
            "uncovered_count": 0,
            "total_count": 0,
            "by_priority": {},
            "note": "Coverage analysis requires database configuration"
        }
    
    async def list_workflows(
        self,
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """List all configured workflows.
        
        Args:
            limit: Number of workflows to return
            offset: Offset for pagination
        
        Returns:
            Dict with workflows and pagination info
        """
        return {
            "workflows": [],
            "total": 0,
            "limit": limit,
            "offset": offset,
            "note": "Workflow management requires database configuration"
        }
    
    async def create_workflow(
        self,
        name: str,
        description: Optional[str] = None,
        entity_type: Optional[str] = None,
        definition: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new workflow.
        
        Args:
            name: Workflow name
            description: Optional description
            entity_type: Entity type this workflow applies to
            definition: Workflow definition/configuration
        
        Returns:
            Dict with created workflow
        """
        return {
            "success": False,
            "id": None,
            "name": name,
            "note": "Workflow creation requires database configuration"
        }
    
    async def update_workflow(
        self,
        workflow_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update an existing workflow.
        
        Args:
            workflow_id: ID of workflow to update
            data: Update data
        
        Returns:
            Dict with updated workflow
        """
        return {
            "success": False,
            "workflow_id": workflow_id,
            "note": "Workflow update requires database configuration"
        }
    
    async def delete_workflow(
        self,
        workflow_id: str
    ) -> Dict[str, Any]:
        """Delete a workflow.
        
        Args:
            workflow_id: ID of workflow to delete
        
        Returns:
            Dict with result
        """
        return {
            "success": False,
            "workflow_id": workflow_id,
            "note": "Workflow deletion requires database configuration"
        }
    
    async def execute_workflow(
        self,
        workflow_id: str,
        input_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a workflow.
        
        Args:
            workflow_id: ID of workflow to execute
            input_data: Input data for workflow
        
        Returns:
            Dict with execution result
        """
        return {
            "success": False,
            "workflow_id": workflow_id,
            "execution_id": None,
            "status": "pending",
            "note": "Workflow execution requires database configuration"
        }
    
    # Phase 3 - Advanced Features
    
    async def advanced_search(
        self,
        entity_type: str,
        query: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Advanced search with facets and suggestions.
        
        Args:
            entity_type: Type of entity to search
            query: Search query string
            filters: Advanced filters
            limit: Results per page
            offset: Pagination offset
        
        Returns:
            Dict with search results and facets
        """
        return {
            "results": [],
            "total": 0,
            "facets": {},
            "suggestions": [],
            "limit": limit,
            "offset": offset,
            "note": "Advanced search requires database configuration"
        }
    
    async def export_entities(
        self,
        entity_type: str,
        format: str = "json",
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Export entities in specified format.
        
        Args:
            entity_type: Type of entity to export
            format: Export format (json, csv)
            filters: Filter entities before export
        
        Returns:
            Dict with export status and data
        """
        return {
            "success": False,
            "format": format,
            "entity_type": entity_type,
            "record_count": 0,
            "file_url": None,
            "note": "Export requires database configuration"
        }
    
    async def import_entities(
        self,
        entity_type: str,
        format: str = "json",
        file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Import entities from file.
        
        Args:
            entity_type: Type of entity to import
            format: File format (json, csv)
            file_path: Path to import file
        
        Returns:
            Dict with import results
        """
        return {
            "success": False,
            "entity_type": entity_type,
            "format": format,
            "imported_count": 0,
            "failed_count": 0,
            "note": "Import requires database configuration"
        }
    
    async def get_entity_permissions(
        self,
        entity_type: str,
        entity_id: str
    ) -> Dict[str, Any]:
        """Get permissions for an entity.
        
        Args:
            entity_type: Type of entity
            entity_id: Entity ID
        
        Returns:
            Dict with permission information
        """
        return {
            "entity_id": entity_id,
            "entity_type": entity_type,
            "permissions": {},
            "owner": None,
            "note": "Permissions require database configuration"
        }
    
    async def update_entity_permissions(
        self,
        entity_type: str,
        entity_id: str,
        permissions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update permissions for an entity.
        
        Args:
            entity_type: Type of entity
            entity_id: Entity ID
            permissions: Permission updates
        
        Returns:
            Dict with result
        """
        return {
            "success": False,
            "entity_id": entity_id,
            "entity_type": entity_type,
            "note": "Permission updates require database configuration"
        }

    async def list_entities(
        self,
        entity_type: str,
        parent_type: Optional[str] = None,
        parent_id: Optional[str] = None,
        limit: Optional[int] = None,
        pagination: Optional[Dict[str, Any]] = None,
        filters_list: Optional[List[Dict[str, Any]]] = None,
        sort_list: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """List entities with pagination, filtering, and sorting.
        
        Args:
            entity_type: Type of entity to list
            parent_type: Optional parent entity type for filtering
            parent_id: Optional parent entity ID for filtering
            limit: Legacy limit parameter (for backwards compatibility)
            pagination: Dict with 'offset' and 'limit' keys
            filters_list: List of filter dicts with 'field', 'operator', 'value'
            sort_list: List of sort dicts with 'field' and 'direction'
        
        Returns:
            Dict with results, total, offset, limit, has_more
        """
        # Parse pagination
        offset = 0
        if pagination:
            offset = pagination.get("offset", 0)
            limit = pagination.get("limit", 20)
        elif limit is None:
            limit = 20
        
        # Enforce limits
        limit = max(1, min(limit, 100))  # 1-100
        offset = max(0, offset)
        
        # Build base filters - skip is_deleted for tables that don't have it
        table = self._resolve_entity_table(entity_type)
        tables_without_soft_delete = {'test_req', 'properties'}

        base_filters = {}
        if table not in tables_without_soft_delete:
            base_filters["is_deleted"] = False

        # Add parent filter
        if parent_type and parent_id:
            parent_key = f"{parent_type}_id"
            base_filters[parent_key] = parent_id

        # Apply additional filters from filters_list
        if filters_list:
            for f in filters_list:
                field = f.get("field")
                operator = f.get("operator", "eq")
                value = f.get("value")
                
                if not field:
                    continue
                
                # Handle different operators
                if operator == "eq":
                    base_filters[field] = value
                elif operator == "ne":
                    # Not equal - add to query logic
                    base_filters[f"{field}_ne"] = value
                elif operator == "in":
                    # In list
                    base_filters[f"{field}_in"] = value if isinstance(value, list) else [value]
                elif operator == "contains":
                    # String contains
                    base_filters[f"{field}_contains"] = value
                elif operator == "starts_with":
                    # String starts with
                    base_filters[f"{field}_starts"] = value
                elif operator == "gte":
                    # Greater than or equal
                    base_filters[f"{field}_gte"] = value
                elif operator == "lte":
                    # Less than or equal
                    base_filters[f"{field}_lte"] = value
                elif operator == "gt":
                    # Greater than
                    base_filters[f"{field}_gt"] = value
                elif operator == "lt":
                    # Less than
                    base_filters[f"{field}_lt"] = value

        # Get total count before pagination
        total = await self._db_count(table, filters=base_filters)

        # Query with pagination
        order_by = None
        if sort_list:
            # Build order_by from sort list
            order_clauses = []
            for sort in sort_list:
                field = sort.get("field")
                direction = sort.get("direction", "asc").lower()
                if field:
                    order_clauses.append(f"{field}.{direction}")
            if order_clauses:
                order_by = ",".join(order_clauses)

        # Execute query
        results = await self.search_entities(
            entity_type,
            filters=base_filters,
            limit=limit,
            offset=offset,
            order_by=order_by
        )

        # Ensure results is a list
        if not isinstance(results, list):
            results = []

        return {
            "results": results,
            "total": total,
            "offset": offset,
            "limit": limit,
            "has_more": (offset + limit) < total
        }
    
    async def _include_relationships(
        self,
        entity_type: str,
        entity: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Include related entities in the response."""
        result = entity.copy()
        entity_id = entity["id"]
        
        if entity_type.lower() == "organization":
            # Include member count and recent projects
            member_count = await self._db_count(
                "organization_members",
                filters={"organization_id": entity_id, "status": "active"}
            )
            result["member_count"] = member_count
            
            recent_projects = await self._db_query(
                "projects",
                filters={"organization_id": entity_id, "is_deleted": False},
                limit=5,
                order_by="updated_at:desc"
            )
            result["recent_projects"] = recent_projects
        
        elif entity_type.lower() == "project":
            # Include document count and members
            doc_count = await self._db_count(
                "documents", 
                filters={"project_id": entity_id, "is_deleted": False}
            )
            result["document_count"] = doc_count
            
            members = await self._db_query(
                "project_members",
                select="*, profiles(*)",
                filters={"project_id": entity_id, "status": "active"}
            )
            result["members"] = members
        
        elif entity_type.lower() == "document":
            # Include requirement count and blocks
            req_count = await self._db_count(
                "requirements",
                filters={"document_id": entity_id, "is_deleted": False}
            )
            result["requirement_count"] = req_count
            
            blocks = await self._db_query(
                "blocks",
                filters={"document_id": entity_id, "is_deleted": False},
                order_by="position"
            )
            result["blocks"] = blocks
        
        return result


# Global manager instance
_entity_manager = EntityManager()


async def entity_operation(
    auth_token: str,
    operation: Literal["create", "read", "update", "delete", "archive", "restore", "search", "list", "batch_create", "bulk_update", "bulk_delete", "bulk_archive", "history", "restore_version", "trace", "coverage", "list_workflows", "create_workflow", "update_workflow", "delete_workflow", "execute_workflow", "advanced_search", "export", "import", "get_permissions", "update_permissions"],
    entity_type: str,
    data: Optional[Dict[str, Any]] = None,
    filters: Optional[Dict[str, Any]] = None,
    entity_id: Optional[str] = None,
    include_relations: bool = False,
    batch: Optional[List[Dict[str, Any]]] = None,
    search_term: Optional[str] = None,
    parent_type: Optional[str] = None,
    parent_id: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    order_by: Optional[str] = None,
    soft_delete: bool = True,
    format_type: str = "detailed",
    pagination: Optional[Dict[str, Any]] = None,
    filter_list: Optional[List[Dict[str, Any]]] = None,
    sort_list: Optional[List[Dict[str, Any]]] = None,
    entity_ids: Optional[List[str]] = None,
    version: Optional[int] = None,
    workflow_id: Optional[str] = None,
    input_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
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
        # Handle case where _entity_manager might be mocked (AsyncMock returns coroutines)
        is_uuid_result = _entity_manager._is_uuid_format(entity_id)
        if asyncio.iscoroutine(is_uuid_result):
            is_uuid = await is_uuid_result
        else:
            is_uuid = is_uuid_result
        if entity_id and not is_uuid:
            t_resolve_start = time.time()
            from tools.entity_resolver import EntityResolver
            # Handle case where _entity_manager might be mocked (AsyncMock returns coroutines)
            adapters_result = _entity_manager._get_adapters()
            if asyncio.iscoroutine(adapters_result):
                adapters = await adapters_result
            else:
                adapters = adapters_result
            resolver = EntityResolver(adapters["database"])
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

        if operation in ("create", "batch_create"):
            # Allow batch-only create (data optional when batch provided)
            if not data and not batch:
                raise ValueError("data or batch is required for create operation")

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
                # Back-compat fields expected by some tests
                if isinstance(formatted, dict):
                    payload = formatted.get("data", final_results)
                    # Ensure base data is present
                    formatted.setdefault("data", payload)
                    # Some tests expect keys within data
                    if isinstance(payload, list):
                        # Embed aliases inside data object if it's a dict; otherwise wrap
                        if isinstance(formatted["data"], dict):
                            formatted["data"].setdefault("created", len(payload))
                            formatted["data"].setdefault("results", payload)
                        else:
                            # Wrap into a dict providing aliases plus original list
                            formatted["data"] = {
                                "results": payload,
                                "created": len(payload)
                            }
                return _entity_manager._add_timing_metrics(formatted, timings)
            else:
                # Single create
                result = await _entity_manager.create_entity(
                    entity_type, data, include_relations
                )
                timings["create"] = time.time() - t_op_start
                timings["total"] = time.time() - start_total
                formatted = _entity_manager._format_result(result, format_type)
                return _entity_manager._add_timing_metrics(formatted, timings)
        
        elif operation == "read":
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
        
        elif operation == "update":
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
        
        elif operation == "delete":
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

        elif operation == "archive":
            if not entity_id:
                raise ValueError("entity_id is required for archive operation")
            t_op_start = time.time()
            # Archive is soft-delete with is_deleted=true
            success = await _entity_manager.delete_entity(
                entity_type, entity_id, soft_delete=True
            )
            timings["archive"] = time.time() - t_op_start
            timings["total"] = time.time() - start_total
            result = {
                "success": success,
                "entity_id": entity_id,
                "entity_type": entity_type,
                "operation": "archive",
                "message": f"{entity_type} archived successfully"
            }
            return _entity_manager._add_timing_metrics(result, timings)

        elif operation == "restore":
            if not entity_id:
                raise ValueError("entity_id is required for restore operation")
            t_op_start = time.time()
            # Restore is update setting is_deleted=false
            result = await _entity_manager.update_entity(
                entity_type, entity_id, {"is_deleted": False}, include_relations
            )
            timings["restore"] = time.time() - t_op_start
            timings["total"] = time.time() - start_total
            formatted = _entity_manager._format_result(result, format_type)
            restore_result = {
                "success": result is not None,
                "entity_id": entity_id,
                "entity_type": entity_type,
                "operation": "restore",
                "data": formatted
            }
            return _entity_manager._add_timing_metrics(restore_result, timings)

        elif operation == "search":
            t_op_start = time.time()
            result = await _entity_manager.search_entities(
                entity_type, filters, search_term, limit, offset, order_by
            )
            timings["search"] = time.time() - t_op_start
            timings["total"] = time.time() - start_total
            formatted = _entity_manager._format_result(result, format_type)
            return _entity_manager._add_timing_metrics(formatted, timings)

        elif operation == "list":
            t_op_start = time.time()
            # Extract pagination, filters, sort from parameters (new API) or data (legacy)
            pag = pagination
            filt_list = filter_list
            srt_list = sort_list
            
            if data:
                # Also check data dict for backwards compatibility
                pag = pag or data.get("pagination")
                filt_list = filt_list or data.get("filters")
                srt_list = srt_list or data.get("sort")
            
            # If offset/limit provided, build pagination dict
            if offset is not None or limit is not None:
                pag = pag or {}
                if offset is not None:
                    pag["offset"] = offset
                if limit is not None:
                    pag["limit"] = limit
            
            result = await _entity_manager.list_entities(
                entity_type,
                parent_type=parent_type,
                parent_id=parent_id,
                limit=limit,
                pagination=pag,
                filters_list=filt_list,
                sort_list=srt_list
            )
            timings["list"] = time.time() - t_op_start
            timings["total"] = time.time() - start_total
            # Result is already a dict with structure, format it appropriately
            if isinstance(result, dict) and "results" in result:
                return _entity_manager._add_timing_metrics(result, timings)
            else:
                formatted = _entity_manager._format_result(result, format_type)
                return _entity_manager._add_timing_metrics(formatted, timings)
        
        elif operation == "bulk_update":
            if entity_ids is None or data is None:
                raise ValueError("entity_ids and data are required for bulk_update operation")
            t_op_start = time.time()
            result = await _entity_manager.bulk_update_entities(
                entity_type, entity_ids, data
            )
            timings["bulk_update"] = time.time() - t_op_start
            timings["total"] = time.time() - start_total
            result["operation"] = "bulk_update"
            return _entity_manager._add_timing_metrics(result, timings)

        elif operation == "bulk_delete":
            if entity_ids is None:
                raise ValueError("entity_ids are required for bulk_delete operation")
            t_op_start = time.time()
            result = await _entity_manager.bulk_delete_entities(
                entity_type, entity_ids, soft_delete
            )
            timings["bulk_delete"] = time.time() - t_op_start
            timings["total"] = time.time() - start_total
            result["operation"] = "bulk_delete"
            return _entity_manager._add_timing_metrics(result, timings)

        elif operation == "bulk_archive":
            if entity_ids is None:
                raise ValueError("entity_ids are required for bulk_archive operation")
            t_op_start = time.time()
            result = await _entity_manager.bulk_archive_entities(
                entity_type, entity_ids
            )
            timings["bulk_archive"] = time.time() - t_op_start
            timings["total"] = time.time() - start_total
            result["operation"] = "bulk_archive"
            return _entity_manager._add_timing_metrics(result, timings)

        elif operation == "history":
            if not entity_id:
                raise ValueError("entity_id is required for history operation")
            t_op_start = time.time()
            result = await _entity_manager.get_entity_history(
                entity_type, entity_id, limit=limit or 20, offset=offset or 0
            )
            timings["history"] = time.time() - t_op_start
            timings["total"] = time.time() - start_total
            return _entity_manager._add_timing_metrics(result, timings)

        elif operation == "restore_version":
            if not entity_id or version is None:
                raise ValueError("entity_id and version are required for restore_version operation")
            t_op_start = time.time()
            result = await _entity_manager.restore_entity_version(
                entity_type, entity_id, version
            )
            timings["restore_version"] = time.time() - t_op_start
            timings["total"] = time.time() - start_total
            result["operation"] = "restore_version"
            return _entity_manager._add_timing_metrics(result, timings)

        elif operation == "trace":
            if not entity_id:
                raise ValueError("entity_id is required for trace operation")
            t_op_start = time.time()
            result = await _entity_manager.get_entity_trace(entity_type, entity_id)
            timings["trace"] = time.time() - t_op_start
            timings["total"] = time.time() - start_total
            return _entity_manager._add_timing_metrics(result, timings)

        elif operation == "coverage":
            t_op_start = time.time()
            result = await _entity_manager.get_entity_coverage(
                entity_type, parent_id
            )
            timings["coverage"] = time.time() - t_op_start
            timings["total"] = time.time() - start_total
            return _entity_manager._add_timing_metrics(result, timings)

        elif operation == "list_workflows":
            t_op_start = time.time()
            result = await _entity_manager.list_workflows(
                limit=limit or 20,
                offset=offset or 0
            )
            timings["list_workflows"] = time.time() - t_op_start
            timings["total"] = time.time() - start_total
            return _entity_manager._add_timing_metrics(result, timings)

        elif operation == "create_workflow":
            if not data or "name" not in data:
                raise ValueError("data with 'name' is required for create_workflow operation")
            t_op_start = time.time()
            result = await _entity_manager.create_workflow(
                name=data.get("name"),
                description=data.get("description"),
                entity_type=entity_type,
                definition=data.get("definition")
            )
            timings["create_workflow"] = time.time() - t_op_start
            timings["total"] = time.time() - start_total
            result["operation"] = "create_workflow"
            return _entity_manager._add_timing_metrics(result, timings)

        elif operation == "update_workflow":
            if not workflow_id or not data:
                raise ValueError("workflow_id and data are required for update_workflow operation")
            t_op_start = time.time()
            result = await _entity_manager.update_workflow(
                workflow_id, data
            )
            timings["update_workflow"] = time.time() - t_op_start
            timings["total"] = time.time() - start_total
            result["operation"] = "update_workflow"
            return _entity_manager._add_timing_metrics(result, timings)

        elif operation == "delete_workflow":
            if not workflow_id:
                raise ValueError("workflow_id is required for delete_workflow operation")
            t_op_start = time.time()
            result = await _entity_manager.delete_workflow(workflow_id)
            timings["delete_workflow"] = time.time() - t_op_start
            timings["total"] = time.time() - start_total
            result["operation"] = "delete_workflow"
            return _entity_manager._add_timing_metrics(result, timings)

        elif operation == "execute_workflow":
            if not workflow_id:
                raise ValueError("workflow_id is required for execute_workflow operation")
            t_op_start = time.time()
            result = await _entity_manager.execute_workflow(
                workflow_id, input_data
            )
            timings["execute_workflow"] = time.time() - t_op_start
            timings["total"] = time.time() - start_total
            result["operation"] = "execute_workflow"
            return _entity_manager._add_timing_metrics(result, timings)

        # Phase 3 Operations
        elif operation == "advanced_search":
            t_op_start = time.time()
            result = await _entity_manager.advanced_search(
                entity_type,
                query=search_term,
                filters=filters,
                limit=limit or 20,
                offset=offset or 0
            )
            timings["advanced_search"] = time.time() - t_op_start
            timings["total"] = time.time() - start_total
            return _entity_manager._add_timing_metrics(result, timings)

        elif operation == "export":
            t_op_start = time.time()
            result = await _entity_manager.export_entities(
                entity_type,
                format=data.get("format", "json") if data else "json",
                filters=filters
            )
            timings["export"] = time.time() - t_op_start
            timings["total"] = time.time() - start_total
            result["operation"] = "export"
            return _entity_manager._add_timing_metrics(result, timings)

        elif operation == "import":
            if not data or "file_path" not in data:
                raise ValueError("data with 'file_path' is required for import operation")
            t_op_start = time.time()
            result = await _entity_manager.import_entities(
                entity_type,
                format=data.get("format", "json"),
                file_path=data.get("file_path")
            )
            timings["import"] = time.time() - t_op_start
            timings["total"] = time.time() - start_total
            result["operation"] = "import"
            return _entity_manager._add_timing_metrics(result, timings)

        elif operation == "get_permissions":
            if not entity_id:
                raise ValueError("entity_id is required for get_permissions operation")
            t_op_start = time.time()
            result = await _entity_manager.get_entity_permissions(
                entity_type, entity_id
            )
            timings["get_permissions"] = time.time() - t_op_start
            timings["total"] = time.time() - start_total
            return _entity_manager._add_timing_metrics(result, timings)

        elif operation == "update_permissions":
            if not entity_id or not data:
                raise ValueError("entity_id and data are required for update_permissions operation")
            t_op_start = time.time()
            result = await _entity_manager.update_entity_permissions(
                entity_type, entity_id, data
            )
            timings["update_permissions"] = time.time() - t_op_start
            timings["total"] = time.time() - start_total
            result["operation"] = "update_permissions"
            return _entity_manager._add_timing_metrics(result, timings)
        
        else:
            raise ValueError(f"Unknown operation: {operation}")
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "operation": operation,
            "entity_type": entity_type
        }
