"""
MCP tools for workflow operations.

This module defines FastMCP tools for creating and executing workflows.
"""

from typing import TYPE_CHECKING, Any, Optional

from .....application.commands.workflow_commands import (
    CreateWorkflowCommand,
    ExecuteWorkflowCommand,
)

if TYPE_CHECKING:
    from ..server import AtomsServer


def register_workflow_tools(mcp: Any, server: "AtomsServer") -> None:
    """
    Register all workflow tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        server: AtomsServer instance with handlers
    """

    @mcp.tool()
    async def create_workflow(
        name: str,
        description: str = "",
        trigger_type: str = "manual",
        steps: Optional[list[dict[str, Any]]] = None,
        enabled: bool = True,
        created_by: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Create a new workflow.

        Args:
            name: Workflow name
            description: Workflow description
            trigger_type: Trigger type (manual, scheduled, event)
            steps: List of workflow steps
            enabled: Whether workflow is enabled
            created_by: User ID creating the workflow

        Returns:
            Created workflow details

        Examples:
            Create manual workflow:
            ```
            create_workflow(
                name="Daily Standup",
                description="Create daily standup tasks",
                trigger_type="manual",
                steps=[
                    {"action": "create_entity", "params": {"entity_type": "task"}},
                    {"action": "send_notification", "params": {"channel": "slack"}}
                ]
            )
            ```

            Create scheduled workflow:
            ```
            create_workflow(
                name="Weekly Report",
                trigger_type="scheduled",
                steps=[
                    {"action": "aggregate_data", "params": {"period": "week"}},
                    {"action": "generate_report", "params": {"format": "pdf"}}
                ]
            )
            ```
        """
        command = CreateWorkflowCommand(
            name=name,
            description=description,
            trigger_type=trigger_type,
            steps=steps or [],
            enabled=enabled,
            created_by=created_by,
        )

        result = server.workflow_command_handler.handle_create_workflow(command)

        if result.is_error:
            raise Exception(result.error)

        return result.to_dict()

    @mcp.tool()
    async def execute_workflow(
        workflow_id: str,
        parameters: Optional[dict[str, Any]] = None,
        async_execution: bool = False,
        executed_by: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Execute a workflow.

        Args:
            workflow_id: Workflow ID to execute
            parameters: Parameters to pass to workflow
            async_execution: Whether to execute asynchronously
            executed_by: User ID executing the workflow

        Returns:
            Execution result or execution ID if async

        Examples:
            Execute workflow synchronously:
            ```
            execute_workflow(
                workflow_id="wf_123",
                parameters={"project_id": "proj_456"}
            )
            ```

            Execute workflow asynchronously:
            ```
            execute_workflow(
                workflow_id="wf_123",
                async_execution=True
            )
            ```
        """
        command = ExecuteWorkflowCommand(
            workflow_id=workflow_id,
            parameters=parameters or {},
            async_execution=async_execution,
            executed_by=executed_by,
        )

        result = server.workflow_command_handler.handle_execute_workflow(command)

        if result.is_error:
            raise Exception(result.error)

        return result.to_dict()

    # Note: Workflow query handlers would be implemented in future iterations
    # For now, workflows are managed through command handlers only


__all__ = ["register_workflow_tools"]
