"""Relationship management tool for entity associations."""

from __future__ import annotations

from typing import Dict, Any, Optional, List, Literal
from datetime import datetime, timezone

try:
    from .base import ToolBase
except ImportError:
    from tools.base import ToolBase

from schemas import (
    RelationshipType,
    MemberRole,
    InvitationStatus,
    EntityStatus,
    Tables,
)
from schemas.rls import (
    PermissionDeniedError,
    OrganizationPolicy,
    ProjectPolicy,
    OrganizationMemberPolicy,
    ProjectMemberPolicy,
    is_organization_owner_or_admin,
    is_project_owner_or_admin,
    user_can_access_project,
)


class RelationshipManager(ToolBase):
    """Manages relationships between entities."""
    
    def __init__(self):
        super().__init__()
    
    def _get_relationship_config(self, relationship_type: str) -> Dict[str, Any]:
        """Get configuration for relationship type."""
        configs = {
            RelationshipType.MEMBER: {
                "organization": {
                    "table": Tables.ORGANIZATION_MEMBERS,
                    "source_field": "organization_id",
                    "target_field": "user_id",
                    "metadata_fields": ["role", "status"],
                    "defaults": {"status": EntityStatus.ACTIVE}
                },
                "project": {
                    "table": Tables.PROJECT_MEMBERS,
                    "source_field": "project_id",
                    "target_field": "user_id",
                    "metadata_fields": ["role", "status", "org_id"],
                    "defaults": {"status": EntityStatus.ACTIVE}
                }
            },
            RelationshipType.ASSIGNMENT: {
                "table": Tables.ASSIGNMENTS,
                "source_field": "entity_id",
                "target_field": "assignee_id",
                "metadata_fields": ["entity_type", "role", "status"],
                "defaults": {"status": EntityStatus.ACTIVE}
            },
            RelationshipType.TRACE_LINK: {
                "table": Tables.TRACE_LINKS,
                "source_field": "source_id",
                "target_field": "target_id",
                "metadata_fields": ["source_type", "target_type", "link_type", "version"],
                "defaults": {"version": 1, "is_deleted": False}
            },
            RelationshipType.REQUIREMENT_TEST: {
                "table": Tables.REQUIREMENT_TESTS,
                "source_field": "requirement_id",
                "target_field": "test_id",
                "metadata_fields": ["relationship_type", "coverage_level"],
                "defaults": {"relationship_type": "tests"}
            },
            RelationshipType.INVITATION: {
                "table": Tables.ORGANIZATION_INVITATIONS,
                "source_field": "organization_id",
                "target_field": "email",
                "metadata_fields": ["role", "status", "created_by"],
                "defaults": {"status": InvitationStatus.PENDING}
            }
        }
        return configs.get(relationship_type.lower(), {})
    
    async def link_entities(
        self,
        relationship_type: str,
        source: Dict[str, str],
        target: Dict[str, str],
        metadata: Optional[Dict[str, Any]] = None,
        source_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a link between two entities."""
        config = self._get_relationship_config(relationship_type)
        if not config:
            raise ValueError(f"Unknown relationship type: {relationship_type}")

        user_id = self._get_user_id()
        adapters = self._get_adapters()
        db_adapter = adapters["database"]

        # RLS validation for member relationships
        if relationship_type == RelationshipType.MEMBER:
            if source.get("type") == "organization":
                # Validate user can manage organization members
                org_id = source["id"]
                if not await is_organization_owner_or_admin(org_id, user_id, db_adapter):
                    raise PermissionDeniedError(
                        "organization_members",
                        "INSERT",
                        "Only organization owners and admins can add members"
                    )
            elif source.get("type") == "project":
                # Validate user can manage project members
                project_id = source["id"]
                if not await is_project_owner_or_admin(project_id, user_id, db_adapter):
                    raise PermissionDeniedError(
                        "project_members",
                        "INSERT",
                        "Only project owners and admins can add members"
                    )

        # RLS validation for assignment relationships
        elif relationship_type == RelationshipType.ASSIGNMENT:
            # User must be able to access the source entity
            source_type = source.get("type")
            if source_type in ["requirement", "test", "document"]:
                # These all require project access - get project_id
                source_entity = await self._db_get_single(
                    self._resolve_entity_table(source_type),
                    filters={"id": source["id"]}
                )
                if source_entity:
                    project_id = source_entity.get("project_id")
                    if project_id:
                        if not await user_can_access_project(project_id, user_id, db_adapter):
                            raise PermissionDeniedError(
                                "assignments",
                                "INSERT",
                                "User does not have access to create assignments for this entity"
                            )

        # RLS validation for trace links
        elif relationship_type == RelationshipType.TRACE_LINK:
            # User must be able to access both source and target entities
            source_type = source.get("type")
            target_type = target.get("type")

            # Validate source access
            if source_type in ["requirement", "test", "document"]:
                source_entity = await self._db_get_single(
                    self._resolve_entity_table(source_type),
                    filters={"id": source["id"]}
                )
                if source_entity:
                    project_id = source_entity.get("project_id")
                    if project_id and not await user_can_access_project(project_id, user_id, db_adapter):
                        raise PermissionDeniedError(
                            "trace_links",
                            "INSERT",
                            "User does not have access to source entity"
                        )

            # Validate target access
            if target_type in ["requirement", "test", "document"]:
                target_entity = await self._db_get_single(
                    self._resolve_entity_table(target_type),
                    filters={"id": target["id"]}
                )
                if target_entity:
                    project_id = target_entity.get("project_id")
                    if project_id and not await user_can_access_project(project_id, user_id, db_adapter):
                        raise PermissionDeniedError(
                            "trace_links",
                            "INSERT",
                            "User does not have access to target entity"
                        )

        # Handle special cases for member relationships
        if relationship_type == RelationshipType.MEMBER:
            if source.get("type") in ["organization", "project"]:
                table_config = config[source["type"]]
                table = table_config["table"]
                
                link_data = {
                    table_config["source_field"]: source["id"],
                    table_config["target_field"]: target["id"]
                }
                
                # Apply defaults
                link_data.update(table_config["defaults"])
                
                # Add metadata
                if metadata:
                    for field in table_config["metadata_fields"]:
                        if field in metadata:
                            link_data[field] = metadata[field]
                
                # Add context-specific fields
                if source["type"] == "project" and source_context:
                    link_data["org_id"] = source_context
                
            else:
                raise ValueError(f"Invalid source type for member relationship: {source.get('type')}")
        
        else:
            # General relationship handling
            table = config["table"]
            link_data = {
                config["source_field"]: source["id"],
                config["target_field"]: target["id"]
            }
            
            # Apply defaults
            link_data.update(config["defaults"])
            
            # Add metadata
            if metadata:
                for field in config["metadata_fields"]:
                    if field in metadata:
                        link_data[field] = metadata[field]
            
            # Add required type fields for certain relationships
            if relationship_type == RelationshipType.TRACE_LINK:
                link_data["source_type"] = source.get("type", "unknown")
                link_data["target_type"] = target.get("type", "unknown")
            elif relationship_type == RelationshipType.ASSIGNMENT:
                link_data["entity_type"] = source.get("type", "unknown")
        
        # Add audit fields (only for tables that have created_by column)
        # Note: organization_members and project_members don't have created_by
        user_id = self._get_user_id()
        if user_id and relationship_type not in [RelationshipType.MEMBER]:
            link_data["created_by"] = user_id

        # Create the link
        result = await self._db_insert(table, link_data, returning="*")
        return result
    
    async def unlink_entities(
        self,
        relationship_type: str,
        source: Dict[str, str],
        target: Dict[str, str],
        soft_delete: bool = True
    ) -> bool:
        """Remove a link between two entities."""
        config = self._get_relationship_config(relationship_type)
        if not config:
            raise ValueError(f"Unknown relationship type: {relationship_type}")

        user_id = self._get_user_id()
        adapters = self._get_adapters()
        db_adapter = adapters["database"]

        # RLS validation for member relationships
        if relationship_type == RelationshipType.MEMBER:
            if source.get("type") == "organization":
                # Validate user can manage organization members
                org_id = source["id"]
                if not await is_organization_owner_or_admin(org_id, user_id, db_adapter):
                    raise PermissionDeniedError(
                        "organization_members",
                        "DELETE",
                        "Only organization owners and admins can remove members"
                    )
            elif source.get("type") == "project":
                # Validate user can manage project members
                project_id = source["id"]
                if not await is_project_owner_or_admin(project_id, user_id, db_adapter):
                    raise PermissionDeniedError(
                        "project_members",
                        "DELETE",
                        "Only project owners and admins can remove members"
                    )

        # Handle special cases for member relationships
        if relationship_type == RelationshipType.MEMBER:
            if source.get("type") in ["organization", "project"]:
                table_config = config[source["type"]]
                table = table_config["table"]
                
                filters = {
                    table_config["source_field"]: source["id"],
                    table_config["target_field"]: target["id"]
                }
            else:
                raise ValueError(f"Invalid source type for member relationship: {source.get('type')}")
        else:
            table = config["table"]
            filters = {
                config["source_field"]: source["id"],
                config["target_field"]: target["id"]
            }
        
        if soft_delete and "is_deleted" in config.get("defaults", {}):
            # Soft delete
            update_data = {
                "is_deleted": True,
                "deleted_at": datetime.now(timezone.utc).isoformat()
            }
            if self._get_user_id():
                update_data["deleted_by"] = self._get_user_id()
            
            result = await self._db_update(table, update_data, filters)
            return bool(result)
        else:
            # Hard delete
            count = await self._db_delete(table, filters)
            return count > 0
    
    async def list_relationships(
        self,
        relationship_type: str,
        source: Optional[Dict[str, str]] = None,
        target: Optional[Dict[str, str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = 100,
        offset: Optional[int] = 0
    ) -> List[Dict[str, Any]]:
        """List relationships of a given type."""
        config = self._get_relationship_config(relationship_type)
        if not config:
            raise ValueError(f"Unknown relationship type: {relationship_type}")
        
        # Handle special cases for member relationships
        if relationship_type == RelationshipType.MEMBER:
            if source and source.get("type") in ["organization", "project"]:
                table_config = config[source["type"]]
                table = table_config["table"]
                query_filters = {}
                
                if source:
                    query_filters[table_config["source_field"]] = source["id"]
                if target:
                    query_filters[table_config["target_field"]] = target["id"]
            else:
                # If no source type specified, we need to query both tables
                # For simplicity, default to organization members
                table_config = config["organization"]
                table = table_config["table"]
                query_filters = {}
                
                if source:
                    query_filters[table_config["source_field"]] = source["id"]
                if target:
                    query_filters[table_config["target_field"]] = target["id"]
        else:
            table = config["table"]
            query_filters = {}
            
            if source:
                query_filters[config["source_field"]] = source["id"]
            if target:
                query_filters[config["target_field"]] = target["id"]
        
        # Add additional filters
        if filters:
            query_filters.update(filters)
        
        # Add default filters
        if "is_deleted" not in query_filters and "is_deleted" in config.get("defaults", {}):
            query_filters["is_deleted"] = False
        
        # Query the relationship table with pagination
        relationships = await self._db_query(
            table,
            select="*",
            filters=query_filters,
            limit=limit,
            offset=offset,
            order_by="created_at:desc"
        )

        # RLS filtering - check user can access these relationships
        user_id = self._get_user_id()
        adapters = self._get_adapters()
        db_adapter = adapters["database"]

        filtered_relationships = []
        for rel in relationships:
            try:
                # Validate access based on relationship type
                if relationship_type == RelationshipType.MEMBER:
                    # Check if user is member of the organization/project
                    if source and source.get("type") == "organization":
                        org_member = await db_adapter.get_single(
                            Tables.ORGANIZATION_MEMBERS,
                            filters={"organization_id": rel.get("organization_id"), "user_id": user_id, "is_deleted": False}
                        )
                        if not org_member:
                            continue
                    elif source and source.get("type") == "project":
                        if not await user_can_access_project(rel.get("project_id"), user_id, db_adapter):
                            continue

                filtered_relationships.append(rel)
            except Exception:
                # Skip relationships we can't validate
                continue

        relationships = filtered_relationships

        # For member relationships, manually join profile data (workaround for missing FK)
        if relationship_type == RelationshipType.MEMBER and relationships:
            # Extract unique user IDs
            user_ids = list(set([
                rel.get(table_config["target_field"])
                for rel in relationships
                if rel.get(table_config["target_field"])
            ]))

            if user_ids:
                # Fetch profiles
                profiles = await self._db_query(
                    Tables.PROFILES,
                    filters={"id": {"in": user_ids}}
                )

                # Create lookup map
                profile_map = {p["id"]: p for p in profiles}

                # Join profiles to relationships
                for rel in relationships:
                    user_id = rel.get(table_config["target_field"])
                    if user_id and user_id in profile_map:
                        rel["profiles"] = profile_map[user_id]

        return relationships
    
    async def check_relationship(
        self,
        relationship_type: str,
        source: Dict[str, str],
        target: Dict[str, str]
    ) -> Optional[Dict[str, Any]]:
        """Check if a relationship exists."""
        relationships = await self.list_relationships(
            relationship_type, source, target
        )
        return relationships[0] if relationships else None
    
    async def update_relationship(
        self,
        relationship_type: str,
        source: Dict[str, str],
        target: Dict[str, str],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update relationship metadata."""
        config = self._get_relationship_config(relationship_type)
        if not config:
            raise ValueError(f"Unknown relationship type: {relationship_type}")

        user_id = self._get_user_id()
        adapters = self._get_adapters()
        db_adapter = adapters["database"]

        # RLS validation for member relationships
        if relationship_type == RelationshipType.MEMBER:
            if source.get("type") == "organization":
                # Validate user can manage organization members
                org_id = source["id"]
                if not await is_organization_owner_or_admin(org_id, user_id, db_adapter):
                    raise PermissionDeniedError(
                        "organization_members",
                        "UPDATE",
                        "Only organization owners and admins can update member roles"
                    )
            elif source.get("type") == "project":
                # Validate user can manage project members
                project_id = source["id"]
                if not await is_project_owner_or_admin(project_id, user_id, db_adapter):
                    raise PermissionDeniedError(
                        "project_members",
                        "UPDATE",
                        "Only project owners and admins can update member roles"
                    )

        # Build filters to find the relationship
        if relationship_type == RelationshipType.MEMBER:
            if source.get("type") in ["organization", "project"]:
                table_config = config[source["type"]]
                table = table_config["table"]
                filters = {
                    table_config["source_field"]: source["id"],
                    table_config["target_field"]: target["id"]
                }
            else:
                raise ValueError(f"Invalid source type for member relationship: {source.get('type')}")
        else:
            table = config["table"]
            filters = {
                config["source_field"]: source["id"],
                config["target_field"]: target["id"]
            }
        
        # Update the relationship
        update_data = metadata.copy()
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        if self._get_user_id():
            update_data["updated_by"] = self._get_user_id()
        
        result = await self._db_update(table, update_data, filters, returning="*")
        return result


# Global manager instance
_relationship_manager = RelationshipManager()


async def relationship_operation(
    auth_token: str,
    operation: Literal["link", "unlink", "list", "check", "update"],
    relationship_type: str,
    source: Dict[str, str],
    target: Optional[Dict[str, str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    filters: Optional[Dict[str, Any]] = None,
    source_context: Optional[str] = None,
    soft_delete: bool = True,
    limit: Optional[int] = 100,
    offset: Optional[int] = 0,
    format_type: str = "detailed"
) -> Dict[str, Any]:
    """Manage relationships between entities.
    
    Args:
        auth_token: Authentication token
        operation: Operation to perform
        relationship_type: Type of relationship (member, assignment, trace_link, etc.)
        source: Source entity {type: "organization", id: "123"}
        target: Target entity {type: "user", id: "456"}
        metadata: Additional relationship data (role, status, etc.)
        filters: Additional filters for list operations
        source_context: Additional context (e.g., org_id for project members)
        soft_delete: Use soft delete for unlink operations
        format_type: Result format (detailed, summary, raw)
    
    Returns:
        Dict containing operation result
    """
    try:
        # Validate authentication
        await _relationship_manager._validate_auth(auth_token)
        
        if operation == "link":
            if not target:
                raise ValueError("target is required for link operation")
            
            result = await _relationship_manager.link_entities(
                relationship_type, source, target, metadata, source_context
            )
            return _relationship_manager._format_result(result, format_type)
        
        elif operation == "unlink":
            if not target:
                raise ValueError("target is required for unlink operation")
            
            success = await _relationship_manager.unlink_entities(
                relationship_type, source, target, soft_delete
            )
            return {
                "success": success,
                "relationship_type": relationship_type,
                "source": source,
                "target": target
            }
        
        elif operation == "list":
            result = await _relationship_manager.list_relationships(
                relationship_type, source, target, filters, limit, offset
            )
            return _relationship_manager._format_result(result, format_type)
        
        elif operation == "check":
            if not target:
                raise ValueError("target is required for check operation")
            
            result = await _relationship_manager.check_relationship(
                relationship_type, source, target
            )
            return {
                "exists": result is not None,
                "relationship": result,
                "relationship_type": relationship_type
            }
        
        elif operation == "update":
            if not target or not metadata:
                raise ValueError("target and metadata are required for update operation")
            
            result = await _relationship_manager.update_relationship(
                relationship_type, source, target, metadata
            )
            return _relationship_manager._format_result(result, format_type)
        
        else:
            raise ValueError(f"Unknown operation: {operation}")
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "operation": operation,
            "relationship_type": relationship_type
        }