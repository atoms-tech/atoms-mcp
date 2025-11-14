"""Workflow management database adapter."""

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


class WorkflowStorageAdapter:
    """Adapter for workflow storage and execution tracking."""

    def __init__(self, db: SupabaseDatabaseAdapter):
        self.db = db

    async def list_workflows(
        self,
        workspace_id: str,
        limit: int = 20,
        offset: int = 0,
        entity_type: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> tuple[List[Dict[str, Any]], int]:
        """List workflows with optional filtering.
        
        Args:
            workspace_id: Workspace ID to list workflows from
            limit: Number of results per page
            offset: Pagination offset
            entity_type: Filter by entity type (optional)
            is_active: Filter by active status (optional)
        
        Returns:
            Tuple of (workflows list, total count)
        """
        try:
            filters = {
                "workspace_id": workspace_id,
                "is_deleted": False
            }
            if entity_type:
                filters["entity_type"] = entity_type
            if is_active is not None:
                filters["is_active"] = is_active

            workflows = await self.db.query(
                "workflows",
                filters=filters,
                order_by="created_at DESC",
                limit=limit,
                offset=offset
            )

            total = await self.db.count_rows(
                "workflows",
                filters={
                    "workspace_id": workspace_id,
                    "is_deleted": False,
                    **({"entity_type": entity_type} if entity_type else {}),
                    **({"is_active": is_active} if is_active is not None else {})
                }
            )

            return workflows, total
        except Exception as e:
            logger.error(f"Error listing workflows: {e}")
            raise normalize_error(e, "Operation failed")

    async def create_workflow(
        self,
        workspace_id: str,
        name: str,
        entity_type: str,
        created_by: str,
        description: Optional[str] = None,
        definition: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new workflow.
        
        Args:
            workspace_id: Workspace ID
            name: Workflow name
            entity_type: Entity type this workflow applies to
            created_by: User ID creating the workflow
            description: Optional description
            definition: Workflow definition/configuration
        
        Returns:
            Created workflow record
        """
        try:
            workflow_data = {
                "workspace_id": workspace_id,
                "name": name,
                "entity_type": entity_type,
                "description": description or "",
                "definition": definition or {},
                "created_by": created_by,
                "updated_by": created_by,
                "is_active": True,
                "is_deleted": False
            }

            result = await self.db.insert(
                "workflows",
                workflow_data,
                return_inserted=True
            )

            return result
        except Exception as e:
            logger.error(f"Error creating workflow: {e}")
            raise normalize_error(e, "Operation failed")

    async def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific workflow by ID.
        
        Args:
            workflow_id: Workflow ID
        
        Returns:
            Workflow record or None if not found
        """
        try:
            return await self.db.get_single(
                "workflows",
                filters={
                    "id": workflow_id,
                    "is_deleted": False
                }
            )
        except Exception as e:
            logger.error(f"Error getting workflow: {e}")
            raise normalize_error(e, "Failed to get workflow")

    async def update_workflow(
        self,
        workflow_id: str,
        updated_by: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Update a workflow.
        
        Args:
            workflow_id: Workflow ID
            updated_by: User ID performing update
            **kwargs: Fields to update
        
        Returns:
            Updated workflow record
        """
        try:
            update_data = {
                **kwargs,
                "updated_by": updated_by,
                "updated_at": datetime.utcnow().isoformat()
            }

            result = await self.db.update(
                "workflows",
                filters={"id": workflow_id},
                data=update_data,
                return_updated=True
            )

            if not result:
                raise ValueError(f"Workflow {workflow_id} not found")

            return result[0]
        except Exception as e:
            logger.error(f"Error updating workflow: {e}")
            raise normalize_error(e, "Operation failed")

    async def delete_workflow(self, workflow_id: str) -> bool:
        """Soft-delete a workflow.
        
        Args:
            workflow_id: Workflow ID
        
        Returns:
            True if deleted, False otherwise
        """
        try:
            result = await self.db.update(
                "workflows",
                filters={"id": workflow_id},
                data={
                    "is_deleted": True,
                    "deleted_at": datetime.utcnow().isoformat()
                }
            )
            return bool(result)
        except Exception as e:
            logger.error(f"Error deleting workflow: {e}")
            raise normalize_error(e, "Failed to delete workflow")

    async def create_execution(
        self,
        workflow_id: str,
        entity_id: str,
        entity_type: str,
        created_by: str,
        input_data: Optional[Dict[str, Any]] = None,
        status: str = "pending"
    ) -> Dict[str, Any]:
        """Create a workflow execution record.
        
        Args:
            workflow_id: Workflow ID
            entity_id: Entity being processed
            entity_type: Type of entity
            created_by: User ID starting execution
            input_data: Input parameters
            status: Initial status
        
        Returns:
            Created execution record
        """
        try:
            execution_data = {
                "workflow_id": workflow_id,
                "entity_id": entity_id,
                "entity_type": entity_type,
                "status": status,
                "input_data": input_data or {},
                "created_by": created_by
            }

            result = await self.db.insert(
                "workflow_executions",
                execution_data,
                return_inserted=True
            )

            return result
        except Exception as e:
            logger.error(f"Error creating execution: {e}")
            raise normalize_error(e, "Operation failed")

    async def update_execution(
        self,
        execution_id: str,
        status: str,
        result_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update a workflow execution.
        
        Args:
            execution_id: Execution ID
            status: New status
            result_data: Execution results
            error_message: Error message if failed
        
        Returns:
            Updated execution record
        """
        try:
            update_data = {
                "status": status,
                "updated_at": datetime.utcnow().isoformat()
            }

            if result_data is not None:
                update_data["result_data"] = result_data

            if error_message:
                update_data["error_message"] = error_message

            if status in ("completed", "failed"):
                update_data["completed_at"] = datetime.utcnow().isoformat()

            result = await self.db.update(
                "workflow_executions",
                filters={"id": execution_id},
                data=update_data,
                return_updated=True
            )

            if not result:
                raise ValueError(f"Execution {execution_id} not found")

            return result[0]
        except Exception as e:
            logger.error(f"Error updating execution: {e}")
            raise normalize_error(e, "Operation failed")

    async def list_executions(
        self,
        workflow_id: str,
        limit: int = 20,
        offset: int = 0,
        status: Optional[str] = None
    ) -> tuple[List[Dict[str, Any]], int]:
        """List workflow executions.
        
        Args:
            workflow_id: Workflow ID
            limit: Results per page
            offset: Pagination offset
            status: Filter by status (optional)
        
        Returns:
            Tuple of (executions list, total count)
        """
        try:
            filters = {"workflow_id": workflow_id}
            if status:
                filters["status"] = status

            executions = await self.db.query(
                "workflow_executions",
                filters=filters,
                order_by="created_at DESC",
                limit=limit,
                offset=offset
            )

            total = await self.db.count_rows(
                "workflow_executions",
                filters=filters
            )

            return executions, total
        except Exception as e:
            logger.error(f"Error listing executions: {e}")
            raise normalize_error(e, "Operation failed")
