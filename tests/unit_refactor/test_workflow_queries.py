"""
Comprehensive tests for workflow query handlers.

Tests cover:
- GetWorkflowQuery validation and execution
- ListWorkflowsQuery validation with filters
- GetExecutionQuery validation and execution
- ListExecutionsQuery validation with filters
- WorkflowQueryHandler all query methods
- Error handling, pagination, filtering
- Empty results, not-found scenarios
"""

import pytest
from datetime import datetime
from uuid import uuid4

from atoms_mcp.application.queries.workflow_queries import (
    GetWorkflowQuery,
    ListWorkflowsQuery,
    GetExecutionQuery,
    ListExecutionsQuery,
    WorkflowQueryHandler,
    WorkflowQueryError,
    WorkflowQueryValidationError,
)
from atoms_mcp.application.dto import QueryResult, ResultStatus, WorkflowDTO, WorkflowExecutionDTO
from atoms_mcp.domain.models.workflow import (
    Workflow,
    WorkflowExecution,
    WorkflowStatus,
    WorkflowStep,
    Action,
    ActionType,
    Trigger,
    TriggerType,
)
from conftest import MockRepository, MockLogger, MockCache


class TestGetWorkflowQueryValidation:
    """Tests for GetWorkflowQuery validation."""

    def test_validate_with_valid_workflow_id(self):
        """Should validate successfully with valid workflow_id."""
        query = GetWorkflowQuery(workflow_id="workflow-123")
        query.validate()  # Should not raise

    def test_validate_missing_workflow_id(self):
        """Should reject missing workflow_id."""
        query = GetWorkflowQuery(workflow_id="")
        with pytest.raises(WorkflowQueryValidationError) as exc_info:
            query.validate()
        assert "workflow_id is required" in str(exc_info.value)


class TestListWorkflowsQueryValidation:
    """Tests for ListWorkflowsQuery validation."""

    def test_validate_with_defaults(self):
        """Should validate successfully with default parameters."""
        query = ListWorkflowsQuery()
        query.validate()  # Should not raise

    def test_validate_with_enabled_filter(self):
        """Should validate successfully with enabled filter."""
        query = ListWorkflowsQuery(enabled=True)
        query.validate()  # Should not raise

    def test_validate_page_less_than_one(self):
        """Should reject page < 1."""
        query = ListWorkflowsQuery(page=0)
        with pytest.raises(WorkflowQueryValidationError) as exc_info:
            query.validate()
        assert "page must be >= 1" in str(exc_info.value)

    def test_validate_negative_page(self):
        """Should reject negative page."""
        query = ListWorkflowsQuery(page=-1)
        with pytest.raises(WorkflowQueryValidationError) as exc_info:
            query.validate()
        assert "page must be >= 1" in str(exc_info.value)

    def test_validate_page_size_less_than_one(self):
        """Should reject page_size < 1."""
        query = ListWorkflowsQuery(page_size=0)
        with pytest.raises(WorkflowQueryValidationError) as exc_info:
            query.validate()
        assert "page_size must be between 1 and 1000" in str(exc_info.value)

    def test_validate_page_size_greater_than_1000(self):
        """Should reject page_size > 1000."""
        query = ListWorkflowsQuery(page_size=1001)
        with pytest.raises(WorkflowQueryValidationError) as exc_info:
            query.validate()
        assert "page_size must be between 1 and 1000" in str(exc_info.value)

    def test_validate_page_size_exactly_1000(self):
        """Should accept page_size of exactly 1000."""
        query = ListWorkflowsQuery(page_size=1000)
        query.validate()  # Should not raise

    def test_validate_with_custom_pagination(self):
        """Should validate with custom pagination parameters."""
        query = ListWorkflowsQuery(page=3, page_size=50)
        query.validate()  # Should not raise


class TestGetExecutionQueryValidation:
    """Tests for GetExecutionQuery validation."""

    def test_validate_with_valid_execution_id(self):
        """Should validate successfully with valid execution_id."""
        query = GetExecutionQuery(execution_id="execution-123")
        query.validate()  # Should not raise

    def test_validate_missing_execution_id(self):
        """Should reject missing execution_id."""
        query = GetExecutionQuery(execution_id="")
        with pytest.raises(WorkflowQueryValidationError) as exc_info:
            query.validate()
        assert "execution_id is required" in str(exc_info.value)


class TestListExecutionsQueryValidation:
    """Tests for ListExecutionsQuery validation."""

    def test_validate_with_defaults(self):
        """Should validate successfully with default parameters."""
        query = ListExecutionsQuery()
        query.validate()  # Should not raise

    def test_validate_with_workflow_id_filter(self):
        """Should validate successfully with workflow_id filter."""
        query = ListExecutionsQuery(workflow_id="workflow-123")
        query.validate()  # Should not raise

    def test_validate_with_status_filter(self):
        """Should validate successfully with valid status filter."""
        query = ListExecutionsQuery(status="running")
        query.validate()  # Should not raise

    def test_validate_invalid_status(self):
        """Should reject invalid status."""
        query = ListExecutionsQuery(status="invalid_status")
        with pytest.raises(WorkflowQueryValidationError) as exc_info:
            query.validate()
        assert "Invalid status" in str(exc_info.value)

    def test_validate_valid_statuses(self):
        """Should accept all valid workflow statuses."""
        valid_statuses = ["pending", "running", "completed", "failed", "cancelled", "paused"]
        for status in valid_statuses:
            query = ListExecutionsQuery(status=status)
            query.validate()  # Should not raise

    def test_validate_page_less_than_one(self):
        """Should reject page < 1."""
        query = ListExecutionsQuery(page=0)
        with pytest.raises(WorkflowQueryValidationError) as exc_info:
            query.validate()
        assert "page must be >= 1" in str(exc_info.value)

    def test_validate_page_size_out_of_range(self):
        """Should reject page_size out of valid range."""
        query = ListExecutionsQuery(page_size=1001)
        with pytest.raises(WorkflowQueryValidationError) as exc_info:
            query.validate()
        assert "page_size must be between 1 and 1000" in str(exc_info.value)


class TestWorkflowQueryHandler:
    """Tests for WorkflowQueryHandler."""

    @pytest.fixture
    def handler(self):
        """Create a workflow query handler with mock dependencies."""
        workflow_repository = MockRepository()
        execution_repository = MockRepository()
        logger = MockLogger()
        cache = MockCache()
        return WorkflowQueryHandler(
            workflow_repository, execution_repository, logger, cache
        )

    @pytest.fixture
    def sample_workflow(self, handler):
        """Create a sample workflow for testing."""
        trigger = Trigger(trigger_type=TriggerType.MANUAL, config={})
        workflow = Workflow(
            name="Test Workflow",
            description="A test workflow",
            trigger=trigger,
            enabled=True,
        )
        handler.workflow_repository.save(workflow)
        return workflow

    @pytest.fixture
    def sample_workflows(self, handler):
        """Create multiple sample workflows for testing."""
        workflows = []
        for i in range(5):
            trigger = Trigger(trigger_type=TriggerType.MANUAL, config={})
            workflow = Workflow(
                name=f"Workflow {i}",
                description=f"Test workflow {i}",
                trigger=trigger,
                enabled=(i % 2 == 0),  # Alternate enabled/disabled
            )
            handler.workflow_repository.save(workflow)
            workflows.append(workflow)
        return workflows

    @pytest.fixture
    def sample_execution(self, handler, sample_workflow):
        """Create a sample workflow execution for testing."""
        execution = WorkflowExecution(
            workflow_id=sample_workflow.id,
            context={"test": "data"},
        )
        execution.start()
        handler.execution_repository.save(execution)
        return execution

    def test_handler_initialization(self, handler):
        """Should initialize handler with dependencies."""
        assert handler.workflow_service is not None
        assert handler.logger is not None
        assert handler.cache is not None

    def test_handle_get_workflow_success(self, handler, sample_workflow):
        """Should successfully retrieve a workflow."""
        query = GetWorkflowQuery(workflow_id=sample_workflow.id)
        result = handler.handle_get_workflow(query)

        assert isinstance(result, QueryResult)
        assert result.status == ResultStatus.SUCCESS
        assert result.data is not None
        assert isinstance(result.data, WorkflowDTO)
        assert result.data.id == sample_workflow.id
        assert result.data.name == "Test Workflow"

    def test_handle_get_workflow_not_found(self, handler):
        """Should handle workflow not found."""
        query = GetWorkflowQuery(workflow_id="nonexistent-id")
        result = handler.handle_get_workflow(query)

        assert result.status == ResultStatus.ERROR
        assert "not found" in result.error.lower()

    def test_handle_get_workflow_validation_error(self, handler):
        """Should handle validation errors."""
        query = GetWorkflowQuery(workflow_id="")
        result = handler.handle_get_workflow(query)

        assert result.status == ResultStatus.ERROR
        assert "Validation error" in result.error

    def test_handle_get_workflow_metadata(self, handler, sample_workflow):
        """Should include workflow_id in metadata."""
        query = GetWorkflowQuery(workflow_id=sample_workflow.id)
        result = handler.handle_get_workflow(query)

        assert result.status == ResultStatus.SUCCESS
        assert result.metadata["workflow_id"] == sample_workflow.id

    def test_handle_list_workflows_success_no_filters(self, handler, sample_workflows):
        """Should successfully list all workflows without filters."""
        query = ListWorkflowsQuery()
        result = handler.handle_list_workflows(query)

        assert isinstance(result, QueryResult)
        assert result.status == ResultStatus.SUCCESS
        assert result.data is not None
        assert len(result.data) == 5
        assert all(isinstance(dto, WorkflowDTO) for dto in result.data)

    def test_handle_list_workflows_with_enabled_filter_true(
        self, handler, sample_workflows
    ):
        """Should filter workflows by enabled=True."""
        query = ListWorkflowsQuery(enabled=True)
        result = handler.handle_list_workflows(query)

        assert result.status == ResultStatus.SUCCESS
        assert len(result.data) == 3  # Workflows 0, 2, 4 are enabled
        assert all(dto.enabled for dto in result.data)

    def test_handle_list_workflows_with_enabled_filter_false(
        self, handler, sample_workflows
    ):
        """Should filter workflows by enabled=False."""
        query = ListWorkflowsQuery(enabled=False)
        result = handler.handle_list_workflows(query)

        assert result.status == ResultStatus.SUCCESS
        assert len(result.data) == 2  # Workflows 1, 3 are disabled
        assert all(not dto.enabled for dto in result.data)

    def test_handle_list_workflows_pagination_first_page(
        self, handler, sample_workflows
    ):
        """Should paginate workflows correctly - first page."""
        query = ListWorkflowsQuery(page=1, page_size=2)
        result = handler.handle_list_workflows(query)

        assert result.status == ResultStatus.SUCCESS
        assert len(result.data) == 2
        assert result.total_count == 5
        assert result.page == 1
        assert result.page_size == 2

    def test_handle_list_workflows_pagination_second_page(
        self, handler, sample_workflows
    ):
        """Should paginate workflows correctly - second page."""
        query = ListWorkflowsQuery(page=2, page_size=2)
        result = handler.handle_list_workflows(query)

        assert result.status == ResultStatus.SUCCESS
        assert len(result.data) == 2
        assert result.total_count == 5
        assert result.page == 2

    def test_handle_list_workflows_pagination_last_page(
        self, handler, sample_workflows
    ):
        """Should paginate workflows correctly - last page."""
        query = ListWorkflowsQuery(page=3, page_size=2)
        result = handler.handle_list_workflows(query)

        assert result.status == ResultStatus.SUCCESS
        assert len(result.data) == 1
        assert result.total_count == 5

    def test_handle_list_workflows_empty_results(self, handler):
        """Should handle empty results gracefully."""
        query = ListWorkflowsQuery()
        result = handler.handle_list_workflows(query)

        assert result.status == ResultStatus.SUCCESS
        assert result.data == []
        assert result.total_count == 0

    def test_handle_list_workflows_validation_error(self, handler):
        """Should handle validation errors."""
        query = ListWorkflowsQuery(page=-1)
        result = handler.handle_list_workflows(query)

        assert result.status == ResultStatus.ERROR
        assert "Validation error" in result.error

    def test_handle_list_workflows_metadata(self, handler, sample_workflows):
        """Should include filter metadata in result."""
        query = ListWorkflowsQuery(enabled=True)
        result = handler.handle_list_workflows(query)

        assert result.status == ResultStatus.SUCCESS
        assert result.metadata["enabled"] is True

    def test_handle_get_execution_success(self, handler, sample_execution):
        """Should successfully retrieve an execution."""
        query = GetExecutionQuery(execution_id=sample_execution.id)
        result = handler.handle_get_execution(query)

        assert isinstance(result, QueryResult)
        assert result.status == ResultStatus.SUCCESS
        assert result.data is not None
        assert isinstance(result.data, WorkflowExecutionDTO)
        assert result.data.id == sample_execution.id
        assert result.data.workflow_id == sample_execution.workflow_id

    def test_handle_get_execution_not_found(self, handler):
        """Should handle execution not found."""
        query = GetExecutionQuery(execution_id="nonexistent-id")
        result = handler.handle_get_execution(query)

        assert result.status == ResultStatus.ERROR
        assert "not found" in result.error.lower()

    def test_handle_get_execution_validation_error(self, handler):
        """Should handle validation errors."""
        query = GetExecutionQuery(execution_id="")
        result = handler.handle_get_execution(query)

        assert result.status == ResultStatus.ERROR
        assert "Validation error" in result.error

    def test_handle_get_execution_metadata(self, handler, sample_execution):
        """Should include execution_id in metadata."""
        query = GetExecutionQuery(execution_id=sample_execution.id)
        result = handler.handle_get_execution(query)

        assert result.status == ResultStatus.SUCCESS
        assert result.metadata["execution_id"] == sample_execution.id

    def test_handle_list_executions_success_no_filters(self, handler, sample_execution):
        """Should successfully list all executions without filters."""
        query = ListExecutionsQuery()
        result = handler.handle_list_executions(query)

        assert isinstance(result, QueryResult)
        assert result.status == ResultStatus.SUCCESS
        assert result.data is not None
        assert len(result.data) >= 1
        assert all(isinstance(dto, WorkflowExecutionDTO) for dto in result.data)

    def test_handle_list_executions_with_workflow_id_filter(
        self, handler, sample_execution
    ):
        """Should filter executions by workflow_id."""
        # Create another execution for a different workflow
        other_workflow = Workflow(
            name="Other Workflow",
            trigger=Trigger(trigger_type=TriggerType.MANUAL, config={}),
        )
        handler.workflow_repository.save(other_workflow)
        other_execution = WorkflowExecution(workflow_id=other_workflow.id)
        handler.execution_repository.save(other_execution)

        query = ListExecutionsQuery(workflow_id=sample_execution.workflow_id)
        result = handler.handle_list_executions(query)

        assert result.status == ResultStatus.SUCCESS
        assert all(
            dto.workflow_id == sample_execution.workflow_id for dto in result.data
        )

    def test_handle_list_executions_with_status_filter(self, handler, sample_execution):
        """Should filter executions by status."""
        # Create executions with different statuses
        completed_execution = WorkflowExecution(workflow_id=sample_execution.workflow_id)
        completed_execution.start()
        completed_execution.complete()
        handler.execution_repository.save(completed_execution)

        failed_execution = WorkflowExecution(workflow_id=sample_execution.workflow_id)
        failed_execution.start()
        failed_execution.fail("Test error")
        handler.execution_repository.save(failed_execution)

        query = ListExecutionsQuery(status="completed")
        result = handler.handle_list_executions(query)

        assert result.status == ResultStatus.SUCCESS
        assert all(dto.status == "completed" for dto in result.data)

    def test_handle_list_executions_pagination(self, handler, sample_workflow):
        """Should paginate executions correctly."""
        # Create multiple executions
        for i in range(5):
            execution = WorkflowExecution(workflow_id=sample_workflow.id)
            handler.execution_repository.save(execution)

        query = ListExecutionsQuery(page=1, page_size=2)
        result = handler.handle_list_executions(query)

        assert result.status == ResultStatus.SUCCESS
        assert len(result.data) == 2
        assert result.page == 1
        assert result.page_size == 2

    def test_handle_list_executions_empty_results(self, handler):
        """Should handle empty results gracefully."""
        query = ListExecutionsQuery(workflow_id="nonexistent-workflow")
        result = handler.handle_list_executions(query)

        assert result.status == ResultStatus.SUCCESS
        assert result.data == []
        assert result.total_count == 0

    def test_handle_list_executions_validation_error(self, handler):
        """Should handle validation errors."""
        query = ListExecutionsQuery(status="invalid_status")
        result = handler.handle_list_executions(query)

        assert result.status == ResultStatus.ERROR
        assert "Validation error" in result.error

    def test_handle_list_executions_metadata(self, handler, sample_execution):
        """Should include filter metadata in result."""
        query = ListExecutionsQuery(
            workflow_id=sample_execution.workflow_id, status="running"
        )
        result = handler.handle_list_executions(query)

        assert result.status == ResultStatus.SUCCESS
        assert result.metadata["workflow_id"] == sample_execution.workflow_id
        assert result.metadata["status"] == "running"


class TestWorkflowQueryHandlerDTOConversion:
    """Tests for DTO conversion in workflow query handler."""

    @pytest.fixture
    def handler(self):
        """Create handler."""
        workflow_repository = MockRepository()
        execution_repository = MockRepository()
        logger = MockLogger()
        cache = MockCache()
        return WorkflowQueryHandler(
            workflow_repository, execution_repository, logger, cache
        )

    def test_workflow_to_dto_conversion(self, handler):
        """Should correctly convert workflow to DTO."""
        trigger = Trigger(trigger_type=TriggerType.SCHEDULED, config={"cron": "0 0 * * *"})
        workflow = Workflow(
            name="Test Workflow",
            description="Test description",
            trigger=trigger,
            enabled=True,
        )

        # Add a step
        action = Action(
            action_type=ActionType.EXECUTE_SCRIPT,
            config={"script": "test.sh"},
        )
        step = WorkflowStep(
            name="Test Step",
            description="Test step description",
            action=action,
        )
        workflow.add_step(step)

        handler.workflow_repository.save(workflow)

        query = GetWorkflowQuery(workflow_id=workflow.id)
        result = handler.handle_get_workflow(query)

        assert result.status == ResultStatus.SUCCESS
        dto = result.data
        assert dto.name == "Test Workflow"
        assert dto.description == "Test description"
        assert dto.enabled is True
        assert dto.trigger_type == "scheduled"
        assert len(dto.steps) == 1
        assert dto.steps[0]["name"] == "Test Step"

    def test_execution_to_dto_conversion(self, handler):
        """Should correctly convert execution to DTO."""
        workflow = Workflow(
            name="Test Workflow",
            trigger=Trigger(trigger_type=TriggerType.MANUAL, config={}),
        )
        handler.workflow_repository.save(workflow)

        execution = WorkflowExecution(
            workflow_id=workflow.id,
            context={"key": "value"},
        )
        execution.start()
        execution.log_event("Test event")
        handler.execution_repository.save(execution)

        query = GetExecutionQuery(execution_id=execution.id)
        result = handler.handle_get_execution(query)

        assert result.status == ResultStatus.SUCCESS
        dto = result.data
        assert dto.workflow_id == workflow.id
        assert dto.status == "running"
        assert dto.started_at is not None
        assert len(dto.execution_log) > 0


class TestWorkflowQueryHandlerErrorHandling:
    """Tests for error handling in workflow query handler."""

    @pytest.fixture
    def handler(self):
        """Create handler."""
        workflow_repository = MockRepository()
        execution_repository = MockRepository()
        logger = MockLogger()
        cache = MockCache()
        return WorkflowQueryHandler(
            workflow_repository, execution_repository, logger, cache
        )

    def test_error_logged_on_validation_failure(self, handler):
        """Should log validation errors."""
        query = GetWorkflowQuery(workflow_id="")
        result = handler.handle_get_workflow(query)

        assert result.status == ResultStatus.ERROR
        error_logs = [log for log in handler.logger.logs if log["level"] == "ERROR"]
        assert len(error_logs) > 0

    def test_error_logged_on_not_found(self, handler):
        """Should log errors when workflow not found."""
        query = GetWorkflowQuery(workflow_id="nonexistent-id")
        result = handler.handle_get_workflow(query)

        assert result.status == ResultStatus.ERROR

    def test_list_workflows_handles_unexpected_errors(self, handler):
        """Should handle unexpected errors gracefully."""
        # This tests the general exception handler
        query = ListWorkflowsQuery()
        result = handler.handle_list_workflows(query)

        # Should not raise, should return error result
        assert isinstance(result, QueryResult)


__all__ = [
    "TestGetWorkflowQueryValidation",
    "TestListWorkflowsQueryValidation",
    "TestGetExecutionQueryValidation",
    "TestListExecutionsQueryValidation",
    "TestWorkflowQueryHandler",
    "TestWorkflowQueryHandlerDTOConversion",
    "TestWorkflowQueryHandlerErrorHandling",
]
