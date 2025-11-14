"""Advanced features database adapter for search, export, import, and permissions."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from datetime import datetime
from uuid import UUID

if TYPE_CHECKING:
    from supabase import Client

try:
    from .supabase_db import SupabaseDatabaseAdapter
    from ..errors import normalize_error
except ImportError:
    from infrastructure.supabase_db import SupabaseDatabaseAdapter
    from errors import normalize_error

logger = logging.getLogger(__name__)


class AdvancedFeaturesAdapter:
    """Adapter for advanced search, export, import, and permission management."""

    def __init__(self, db: SupabaseDatabaseAdapter):
        self.db = db

    # =====================================================
    # SEARCH OPERATIONS
    # =====================================================

    async def index_entity(
        self,
        entity_type: str,
        entity_id: str,
        workspace_id: str,
        title: str,
        content: str,
        facets: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Index an entity for full-text search.
        
        Args:
            entity_type: Type of entity
            entity_id: Entity ID
            workspace_id: Workspace ID
            title: Entity title
            content: Entity content for indexing
            facets: Faceted search data
            metadata: Additional metadata
        
        Returns:
            Index record
        """
        try:
            index_data = {
                "entity_type": entity_type,
                "entity_id": entity_id,
                "workspace_id": workspace_id,
                "title": title,
                "content": content,
                "facets": facets or {},
                "metadata": metadata or {},
                "is_deleted": False
            }

            # Check if already indexed
            existing = await self.db.get_single(
                "search_index",
                filters={
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "is_deleted": False
                }
            )

            if existing:
                # Update existing index
                result = await self.db.update(
                    "search_index",
                    filters={"id": existing["id"]},
                    data=index_data,
                    return_updated=True
                )
                return result[0] if result else existing
            else:
                # Create new index
                result = await self.db.insert(
                    "search_index",
                    index_data
                )
                return result
        except Exception as e:
            logger.error(f"Error indexing entity: {e}")
            raise normalize_error(e, "Failed to index entity for search")

    async def advanced_search(
        self,
        workspace_id: str,
        entity_type: str,
        query: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 20,
        offset: int = 0
    ) -> tuple[List[Dict[str, Any]], int, Dict[str, Any]]:
        """Advanced full-text search with facets.
        
        Args:
            workspace_id: Workspace ID
            entity_type: Entity type to search
            query: Search query string
            filters: Additional filters
            limit: Results per page
            offset: Pagination offset
        
        Returns:
            Tuple of (results, total, facets)
        """
        try:
            base_filters = {
                "workspace_id": workspace_id,
                "entity_type": entity_type,
                "is_deleted": False
            }

            # Build query with FTS if provided
            search_query = None
            if query:
                search_query = query
                # PostgreSQL FTS would be used here in real implementation
                # For now, using ILIKE for title/content search
                base_filters["search_vector"] = search_query

            # Apply additional filters
            if filters:
                base_filters.update(filters)

            # Execute search
            results = await self.db.query(
                "search_index",
                filters=base_filters,
                limit=limit,
                offset=offset,
                order_by="updated_at DESC"
            )

            # Get total count
            total = await self.db.count_rows(
                "search_index",
                filters=base_filters
            )

            # Extract facets from results
            facets = self._extract_facets(results)

            return results, total, facets
        except Exception as e:
            logger.error(f"Error in advanced search: {e}")
            raise normalize_error(e, "Operation failed")

    def _extract_facets(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract facet information from search results.
        
        Args:
            results: Search results
        
        Returns:
            Facet data
        """
        facets = {}
        for result in results:
            if "facets" in result and result["facets"]:
                for facet_key, facet_values in result["facets"].items():
                    if facet_key not in facets:
                        facets[facet_key] = {}
                    for value in facet_values if isinstance(facet_values, list) else [facet_values]:
                        facets[facet_key][value] = facets[facet_key].get(value, 0) + 1
        return facets

    # =====================================================
    # EXPORT OPERATIONS
    # =====================================================

    async def create_export_job(
        self,
        workspace_id: str,
        entity_type: str,
        format: str,
        requested_by: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create an export job.
        
        Args:
            workspace_id: Workspace ID
            entity_type: Type of entity to export
            format: Export format (json, csv)
            requested_by: User ID requesting export
            filters: Export filters
        
        Returns:
            Export job record
        """
        try:
            job_data = {
                "workspace_id": workspace_id,
                "entity_type": entity_type,
                "format": format,
                "filters": filters or {},
                "requested_by": requested_by,
                "status": "queued"
            }

            result = await self.db.insert(
                "export_jobs",
                job_data,
                return_inserted=True
            )
            return result
        except Exception as e:
            logger.error(f"Error creating export job: {e}")
            raise normalize_error(e, "Operation failed")

    async def update_export_job(
        self,
        job_id: str,
        status: str,
        file_path: Optional[str] = None,
        file_size: Optional[int] = None,
        row_count: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update an export job.
        
        Args:
            job_id: Job ID
            status: New status
            file_path: Path to exported file
            file_size: Size of exported file
            row_count: Number of rows exported
            error_message: Error message if failed
        
        Returns:
            Updated job record
        """
        try:
            update_data = {
                "status": status,
                "updated_at": datetime.utcnow().isoformat()
            }

            if file_path:
                update_data["file_path"] = file_path
            if file_size is not None:
                update_data["file_size"] = file_size
            if row_count is not None:
                update_data["row_count"] = row_count
            if error_message:
                update_data["error_message"] = error_message

            if status == "completed":
                update_data["completed_at"] = datetime.utcnow().isoformat()

            result = await self.db.update(
                "export_jobs",
                filters={"id": job_id},
                data=update_data,
                return_updated=True
            )

            return result[0] if result else {}
        except Exception as e:
            logger.error(f"Error updating export job: {e}")
            raise normalize_error(e, "Operation failed")

    # =====================================================
    # IMPORT OPERATIONS
    # =====================================================

    async def create_import_job(
        self,
        workspace_id: str,
        entity_type: str,
        format: str,
        file_name: str,
        file_size: int,
        requested_by: str
    ) -> Dict[str, Any]:
        """Create an import job.
        
        Args:
            workspace_id: Workspace ID
            entity_type: Type of entity to import
            format: Import format (json, csv)
            file_name: Name of uploaded file
            file_size: Size of file in bytes
            requested_by: User ID requesting import
        
        Returns:
            Import job record
        """
        try:
            job_data = {
                "workspace_id": workspace_id,
                "entity_type": entity_type,
                "format": format,
                "file_name": file_name,
                "file_size": file_size,
                "requested_by": requested_by,
                "status": "queued",
                "total_rows": 0,
                "imported_rows": 0,
                "skipped_rows": 0,
                "error_rows": 0
            }

            result = await self.db.insert(
                "import_jobs",
                job_data,
                return_inserted=True
            )
            return result
        except Exception as e:
            logger.error(f"Error creating import job: {e}")
            raise normalize_error(e, "Operation failed")

    async def update_import_job(
        self,
        job_id: str,
        status: str,
        total_rows: Optional[int] = None,
        imported_rows: Optional[int] = None,
        skipped_rows: Optional[int] = None,
        error_rows: Optional[int] = None,
        error_details: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update an import job.
        
        Args:
            job_id: Job ID
            status: New status
            total_rows: Total rows in file
            imported_rows: Rows successfully imported
            skipped_rows: Rows skipped
            error_rows: Rows with errors
            error_details: Detailed error information
            error_message: General error message
        
        Returns:
            Updated job record
        """
        try:
            update_data = {
                "status": status,
                "updated_at": datetime.utcnow().isoformat()
            }

            if total_rows is not None:
                update_data["total_rows"] = total_rows
            if imported_rows is not None:
                update_data["imported_rows"] = imported_rows
            if skipped_rows is not None:
                update_data["skipped_rows"] = skipped_rows
            if error_rows is not None:
                update_data["error_rows"] = error_rows
            if error_details:
                update_data["error_details"] = error_details
            if error_message:
                update_data["error_message"] = error_message

            if status == "completed":
                update_data["completed_at"] = datetime.utcnow().isoformat()

            result = await self.db.update(
                "import_jobs",
                filters={"id": job_id},
                data=update_data,
                return_updated=True
            )

            return result[0] if result else {}
        except Exception as e:
            logger.error(f"Error updating import job: {e}")
            raise normalize_error(e, "Operation failed")

    # =====================================================
    # PERMISSION OPERATIONS
    # =====================================================

    async def get_entity_permissions(
        self,
        entity_type: str,
        entity_id: str
    ) -> List[Dict[str, Any]]:
        """Get all permissions for an entity.
        
        Args:
            entity_type: Entity type
            entity_id: Entity ID
        
        Returns:
            List of permission records
        """
        try:
            permissions = await self.db.query(
                "entity_permissions",
                filters={
                    "entity_type": entity_type,
                    "entity_id": entity_id
                },
                order_by="created_at DESC"
            )
            return permissions
        except Exception as e:
            logger.error(f"Error getting entity permissions: {e}")
            raise normalize_error(e, "Failed to get entity permissions")

    async def grant_permission(
        self,
        entity_type: str,
        entity_id: str,
        workspace_id: str,
        user_id: Optional[str] = None,
        role_id: Optional[str] = None,
        permission_level: str = "view",
        granted_by: Optional[str] = None,
        expires_at: Optional[str] = None
    ) -> Dict[str, Any]:
        """Grant a permission on an entity.
        
        Args:
            entity_type: Entity type
            entity_id: Entity ID
            workspace_id: Workspace ID
            user_id: User to grant permission to
            role_id: Role to grant permission to
            permission_level: Permission level (view, edit, admin)
            granted_by: User granting permission
            expires_at: Optional expiration date
        
        Returns:
            Created permission record
        """
        try:
            permission_data = {
                "entity_type": entity_type,
                "entity_id": entity_id,
                "workspace_id": workspace_id,
                "user_id": user_id,
                "role_id": role_id,
                "permission_level": permission_level,
                "granted_by": granted_by,
                "expires_at": expires_at
            }

            result = await self.db.insert(
                "entity_permissions",
                permission_data,
                return_inserted=True
            )
            return result
        except Exception as e:
            logger.error(f"Error granting permission: {e}")
            raise normalize_error(e, "Operation failed")

    async def revoke_permission(
        self,
        permission_id: str
    ) -> bool:
        """Revoke a permission.
        
        Args:
            permission_id: Permission ID
        
        Returns:
            True if revoked, False otherwise
        """
        try:
            result = await self.db.delete(
                "entity_permissions",
                filters={"id": permission_id}
            )
            return bool(result)
        except Exception as e:
            logger.error(f"Error revoking permission: {e}")
            raise normalize_error(e, "Failed to revoke permission")

    async def update_permission(
        self,
        permission_id: str,
        permission_level: Optional[str] = None,
        expires_at: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update a permission.
        
        Args:
            permission_id: Permission ID
            permission_level: New permission level
            expires_at: New expiration date
        
        Returns:
            Updated permission record
        """
        try:
            update_data = {
                "updated_at": datetime.utcnow().isoformat()
            }

            if permission_level:
                update_data["permission_level"] = permission_level
            if expires_at:
                update_data["expires_at"] = expires_at

            result = await self.db.update(
                "entity_permissions",
                filters={"id": permission_id},
                data=update_data,
                return_updated=True
            )

            return result[0] if result else {}
        except Exception as e:
            logger.error(f"Error updating permission: {e}")
            raise normalize_error(e, "Operation failed")
