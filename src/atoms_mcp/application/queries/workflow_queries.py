"""
Workflow queries for the application layer.

This module implements query handlers for workflow and execution retrieval.
"""

from dataclasses import dataclass
from typing import Any, Optional

from ...domain.models.workflow import Workflow, WorkflowExecution, WorkflowStatus
from ...domain.ports.cache import Cache
from ...domain.ports.logger import Logger
from ...domain.ports.repository import Repository, RepositoryError
from ...domain.services.workflow_service import WorkflowService
from ..dto import QueryResult, ResultStatus, WorkflowDTO, WorkflowExecutionDTO


class WorkflowQueryError(Exception):
    """Base exception for workflow query errors."""

    pass


class WorkflowQueryValidationError(WorkflowQueryError):
    """Exception raised for query validation failures."""

    pass


@dataclass
class GetWorkflowQuery:
    """
    Query to get a single workflow by ID.

    Attributes:
        workflow_id: Workflow ID to retrieve
    """

    workflow_id: str

    def validate(self) -> None:
        """
        Validate query parameters.

        Raises:
            WorkflowQueryValidationError: If validation fails
        """
        if not self.workflow_id:
            raise WorkflowQueryValidationError("workflow_id is required")


@dataclass
class ListWorkflowsQuery:
    """
    Query to list workflows with filters.

    Attributes:
        enabled: Filter by enabled status
        page: Page number (1-indexed)
        page_size: Number of items per page
    """

    enabled: Optional[bool] = None
    page: int = 1
    page_size: int = 20

    def validate(self) -> None:
        """
        Validate query parameters.

        Raises:
            WorkflowQueryValidationError: If validation fails
        """
        if self.page < 1:
            raise WorkflowQueryValidationError("page must be >= 1")
        if self.page_size < 1 or self.page_size > 1000:
            raise WorkflowQueryValidationError(
                "page_size must be between 1 and 1000"
            )


@dataclass
class GetExecutionQuery:
    """
    Query to get a single workflow execution by ID.

    Attributes:
        execution_id: Execution ID to retrieve
    """

    execution_id: str

    def validate(self) -> None:
        """
        Validate query parameters.

        Raises:
            WorkflowQueryValidationError: If validation fails
        """
        if not self.execution_id:
            raise WorkflowQueryValidationError("execution_id is required")


@dataclass
class ListExecutionsQuery:
    """
    Query to list workflow executions with filters.

    Attributes:
        workflow_id: Filter by workflow ID
        status: Filter by execution status
        page: Page number (1-indexed)
        page_size: Number of items per page
    """

    workflow_id: Optional[str] = None
    status: Optional[str] = None
    page: int = 1
    page_size: int = 20

    def validate(self) -> None:
        """
        Validate query parameters.

        Raises:
            WorkflowQueryValidationError: If validation fails
        """
        if self.page < 1:
            raise WorkflowQueryValidationError("page must be >= 1")
        if self.page_size < 1 or self.page_size > 1000:
            raise WorkflowQueryValidationError(
                "page_size must be between 1 and 1000"
            )

        if self.status:
            try:
                WorkflowStatus(self.status)
            except ValueError:
                raise WorkflowQueryValidationError(f"Invalid status: {self.status}")


class WorkflowQueryHandler:
    """
    Handler for workflow queries.

    This class handles workflow and execution retrieval using the domain service.

    Attributes:
        workflow_service: Domain service for workflow operations
        logger: Logger for recording events
    """

    def __init__(
        self,
        workflow_repository: Repository[Workflow],
        execution_repository: Repository[WorkflowExecution],
        logger: Logger,
        cache: Optional[Cache] = None,
    ):
        """
        Initialize workflow query handler.

        Args:
            workflow_repository: Repository for workflow persistence
            execution_repository: Repository for execution persistence
            logger: Logger for recording events
            cache: Optional cache for performance
        """
        self.workflow_service = WorkflowService(
            workflow_repository, execution_repository, logger
        )
        self.workflow_repository = workflow_repository
        self.execution_repository = execution_repository
        self.logger = logger
        self.cache = cache

    def handle_get_workflow(self, query: GetWorkflowQuery) -> QueryResult[WorkflowDTO]:
        """
        Handle get workflow query.

        Args:
            query: Get workflow query

        Returns:
            Query result with workflow DTO
        """
        try:
            # Validate query
            query.validate()

            # Get workflow using service
            workflow = self.workflow_service.get_workflow(query.workflow_id)

            if not workflow:
                return QueryResult(
                    status=ResultStatus.ERROR,
                    error=f"Workflow {query.workflow_id} not found",
                )

            # Convert to DTO
            dto = self._workflow_to_dto(workflow)

            return QueryResult(
                status=ResultStatus.SUCCESS,
                data=dto,
                total_count=1,
                page=1,
                page_size=1,
                metadata={"workflow_id": query.workflow_id},
            )

        except WorkflowQueryValidationError as e:
            self.logger.error(f"Workflow query validation failed: {e}")
            return QueryResult(
                status=ResultStatus.ERROR,
                error=f"Validation error: {str(e)}",
            )

        except Exception as e:
            self.logger.error(f"Unexpected error during workflow retrieval: {e}")
            return QueryResult(
                status=ResultStatus.ERROR,
                error=f"Unexpected error: {str(e)}",
            )

    def handle_list_workflows(
        self, query: ListWorkflowsQuery
    ) -> QueryResult[list[WorkflowDTO]]:
        """
        Handle list workflows query.

        Args:
            query: List workflows query

        Returns:
            Query result with list of workflow DTOs
        """
        try:
            # Validate query
            query.validate()

            # Build filters
            filters = {}
            if query.enabled is not None:
                filters["enabled"] = query.enabled

            # Get workflows from repository
            workflows = self.workflow_repository.list(filters=filters)

            # Apply pagination
            total_count = len(workflows)
            start_idx = (query.page - 1) * query.page_size
            end_idx = start_idx + query.page_size
            paginated_workflows = workflows[start_idx:end_idx]

            # Convert to DTOs
            dtos = [self._workflow_to_dto(wf) for wf in paginated_workflows]

            return QueryResult(
                status=ResultStatus.SUCCESS,
                data=dtos,
                total_count=total_count,
                page=query.page,
                page_size=query.page_size,
                metadata={"enabled": query.enabled},
            )

        except WorkflowQueryValidationError as e:
            self.logger.error(f"Workflow query validation failed: {e}")
            return QueryResult(
                status=ResultStatus.ERROR,
                error=f"Validation error: {str(e)}",
            )

        except RepositoryError as e:
            self.logger.error(f"Repository error during workflow listing: {e}")
            return QueryResult(
                status=ResultStatus.ERROR,
                error=f"Failed to list workflows: {str(e)}",
            )

        except Exception as e:
            self.logger.error(f"Unexpected error during workflow listing: {e}")
            return QueryResult(
                status=ResultStatus.ERROR,
                error=f"Unexpected error: {str(e)}",
            )

    def handle_get_execution(
        self, query: GetExecutionQuery
    ) -> QueryResult[WorkflowExecutionDTO]:
        """
        Handle get execution query.

        Args:
            query: Get execution query

        Returns:
            Query result with execution DTO
        """
        try:
            # Validate query
            query.validate()

            # Get execution from repository
            execution = self.execution_repository.get(query.execution_id)

            if not execution:
                return QueryResult(
                    status=ResultStatus.ERROR,
                    error=f"Execution {query.execution_id} not found",
                )

            # Convert to DTO
            dto = self._execution_to_dto(execution)

            return QueryResult(
                status=ResultStatus.SUCCESS,
                data=dto,
                total_count=1,
                page=1,
                page_size=1,
                metadata={"execution_id": query.execution_id},
            )

        except WorkflowQueryValidationError as e:
            self.logger.error(f"Workflow query validation failed: {e}")
            return QueryResult(
                status=ResultStatus.ERROR,
                error=f"Validation error: {str(e)}",
            )

        except Exception as e:
            self.logger.error(f"Unexpected error during execution retrieval: {e}")
            return QueryResult(
                status=ResultStatus.ERROR,
                error=f"Unexpected error: {str(e)}",
            )

    def handle_list_executions(
        self, query: ListExecutionsQuery
    ) -> QueryResult[list[WorkflowExecutionDTO]]:
        """
        Handle list executions query.

        Args:
            query: List executions query

        Returns:
            Query result with list of execution DTOs
        """
        try:
            # Validate query
            query.validate()

            # Build filters
            filters = {}
            if query.workflow_id:
                filters["workflow_id"] = query.workflow_id
            if query.status:
                filters["status"] = query.status

            # Get executions from repository
            executions = self.execution_repository.list(filters=filters)

            # Apply pagination
            total_count = len(executions)
            start_idx = (query.page - 1) * query.page_size
            end_idx = start_idx + query.page_size
            paginated_executions = executions[start_idx:end_idx]

            # Convert to DTOs
            dtos = [self._execution_to_dto(ex) for ex in paginated_executions]

            return QueryResult(
                status=ResultStatus.SUCCESS,
                data=dtos,
                total_count=total_count,
                page=query.page,
                page_size=query.page_size,
                metadata={
                    "workflow_id": query.workflow_id,
                    "status": query.status,
                },
            )

        except WorkflowQueryValidationError as e:
            self.logger.error(f"Workflow query validation failed: {e}")
            return QueryResult(
                status=ResultStatus.ERROR,
                error=f"Validation error: {str(e)}",
            )

        except RepositoryError as e:
            self.logger.error(f"Repository error during execution listing: {e}")
            return QueryResult(
                status=ResultStatus.ERROR,
                error=f"Failed to list executions: {str(e)}",
            )

        except Exception as e:
            self.logger.error(f"Unexpected error during execution listing: {e}")
            return QueryResult(
                status=ResultStatus.ERROR,
                error=f"Unexpected error: {str(e)}",
            )

    def _workflow_to_dto(self, workflow: Workflow) -> WorkflowDTO:
        """
        Convert workflow to DTO.

        Args:
            workflow: Workflow to convert

        Returns:
            WorkflowDTO instance
        """
        steps_data = []
        for step in workflow.steps:
            step_data = {
                "id": step.id,
                "name": step.name,
                "description": step.description,
                "action": {
                    "action_type": step.action.action_type.value if step.action else None,
                    "config": step.action.config if step.action else {},
                },
                "next_step_id": step.next_step_id,
            }
            steps_data.append(step_data)

        return WorkflowDTO(
            id=workflow.id,
            name=workflow.name,
            description=workflow.description,
            enabled=workflow.enabled,
            trigger_type=workflow.trigger.trigger_type.value if workflow.trigger else "manual",
            steps=steps_data,
            created_at=workflow.created_at,
            updated_at=workflow.updated_at,
            metadata=workflow.metadata,
        )

    def _execution_to_dto(self, execution: WorkflowExecution) -> WorkflowExecutionDTO:
        """
        Convert workflow execution to DTO.

        Args:
            execution: Execution to convert

        Returns:
            WorkflowExecutionDTO instance
        """
        return WorkflowExecutionDTO(
            id=execution.id,
            workflow_id=execution.workflow_id,
            status=execution.status.value,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
            error_message=execution.error_message,
            execution_log=execution.execution_log,
        )


__all__ = [
    "GetWorkflowQuery",
    "ListWorkflowsQuery",
    "GetExecutionQuery",
    "ListExecutionsQuery",
    "WorkflowQueryHandler",
    "WorkflowQueryError",
    "WorkflowQueryValidationError",
]
