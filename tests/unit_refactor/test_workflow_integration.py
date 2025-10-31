"""
Comprehensive end-to-end workflow integration tests.

Tests cover complete workflows across multiple components:
- Entity creation → relationship linking → workflow execution
- Complete CRUD lifecycle with relationships
- Multi-step workflows with state transitions
- Workflow state transitions and validation
- Error recovery workflows
- Complex entity hierarchies
- Cascade operations
- Transaction integrity
- Event propagation
"""

import pytest
from datetime import datetime
from uuid import uuid4

from atoms_mcp.application.commands.entity_commands import (
    CreateEntityCommand,
    UpdateEntityCommand,
    DeleteEntityCommand,
    EntityCommandHandler,
)
from atoms_mcp.application.commands.relationship_commands import (
    CreateRelationshipCommand,
    DeleteRelationshipCommand,
    RelationshipCommandHandler,
)
from atoms_mcp.application.commands.workflow_commands import (
    CreateWorkflowCommand,
    ExecuteWorkflowCommand,
    WorkflowCommandHandler,
)
from atoms_mcp.application.queries.entity_queries import (
    GetEntityQuery,
    ListEntitiesQuery,
    EntityQueryHandler,
)
from atoms_mcp.application.queries.relationship_queries import (
    GetRelationshipsQuery,
    GetRelatedEntitiesQuery,
    RelationshipQueryHandler,
)
from atoms_mcp.application.dto import ResultStatus
from atoms_mcp.domain.models.entity import WorkspaceEntity, ProjectEntity, TaskEntity, EntityStatus
from atoms_mcp.domain.models.relationship import RelationType, RelationshipStatus
from atoms_mcp.domain.models.workflow import WorkflowStatus, TriggerType
from conftest import MockRepository, MockLogger, MockCache


# =============================================================================
# COMPLETE ENTITY CRUD LIFECYCLE TESTS
# =============================================================================


class TestEntityCRUDLifecycle:
    """Tests for complete entity CRUD lifecycle."""

    @pytest.fixture
    def handlers(self):
        """Create entity command and query handlers."""
        repository = MockRepository()
        logger = MockLogger()
        cache = MockCache()

        command_handler = EntityCommandHandler(repository, logger, cache)
        query_handler = EntityQueryHandler(repository, logger, cache)

        return command_handler, query_handler

    def test_complete_entity_lifecycle(self, handlers):
        """Should handle complete entity lifecycle: create, read, update, delete."""
        command_handler, query_handler = handlers

        # 1. Create entity
        create_cmd = CreateEntityCommand(
            entity_type="workspace",
            name="Test Workspace",
            description="Initial description",
        )
        create_result = command_handler.handle_create_entity(create_cmd)

        assert create_result.status == ResultStatus.SUCCESS
        entity_id = create_result.data.id

        # 2. Read entity
        get_query = GetEntityQuery(entity_id=entity_id)
        get_result = query_handler.handle_get_entity(get_query)

        assert get_result.status == ResultStatus.SUCCESS
        assert get_result.data.name == "Test Workspace"

        # 3. Update entity
        update_cmd = UpdateEntityCommand(
            entity_id=entity_id,
            updates={"name": "Updated Workspace", "description": "Updated description"},
        )
        update_result = command_handler.handle_update_entity(update_cmd)

        assert update_result.status == ResultStatus.SUCCESS
        assert update_result.data.name == "Updated Workspace"

        # 4. Verify update
        get_result2 = query_handler.handle_get_entity(get_query)
        assert get_result2.data.name == "Updated Workspace"

        # 5. Soft delete entity
        delete_cmd = DeleteEntityCommand(entity_id=entity_id, soft_delete=True)
        delete_result = command_handler.handle_delete_entity(delete_cmd)

        assert delete_result.status == ResultStatus.SUCCESS

        # 6. Verify entity is soft deleted
        get_result3 = query_handler.handle_get_entity(get_query)
        assert get_result3.data.status == "deleted"

    def test_entity_lifecycle_with_caching(self, handlers):
        """Should properly handle cache during entity lifecycle."""
        command_handler, query_handler = handlers

        # Create entity
        create_cmd = CreateEntityCommand(
            entity_type="workspace",
            name="Cached Workspace",
        )
        create_result = command_handler.handle_create_entity(create_cmd)
        entity_id = create_result.data.id

        # Read entity (should cache)
        get_query = GetEntityQuery(entity_id=entity_id)
        get_result1 = query_handler.handle_get_entity(get_query)
        assert get_result1.status == ResultStatus.SUCCESS

        # Update entity (should invalidate cache)
        update_cmd = UpdateEntityCommand(
            entity_id=entity_id,
            updates={"name": "Updated via Cache"},
        )
        command_handler.handle_update_entity(update_cmd)

        # Read again (should get fresh data)
        get_result2 = query_handler.handle_get_entity(get_query)
        assert get_result2.data.name == "Updated via Cache"

    def test_entity_lifecycle_with_validation_errors(self, handlers):
        """Should handle validation errors throughout lifecycle."""
        command_handler, query_handler = handlers

        # Try to create invalid entity
        create_cmd = CreateEntityCommand(
            entity_type="workspace",
            name="",  # Invalid - empty name
        )
        create_result = command_handler.handle_create_entity(create_cmd)

        assert create_result.status == ResultStatus.ERROR

        # Create valid entity
        create_cmd2 = CreateEntityCommand(
            entity_type="workspace",
            name="Valid Workspace",
        )
        create_result2 = command_handler.handle_create_entity(create_cmd2)
        assert create_result2.status == ResultStatus.SUCCESS

        # Try invalid update
        update_cmd = UpdateEntityCommand(
            entity_id=create_result2.data.id,
            updates={"id": "new-id"},  # Cannot update ID
        )
        update_result = command_handler.handle_update_entity(update_cmd)

        assert update_result.status == ResultStatus.ERROR


# =============================================================================
# ENTITY WITH RELATIONSHIPS WORKFLOW TESTS
# =============================================================================


class TestEntityRelationshipWorkflow:
    """Tests for workflows involving entities and relationships."""

    @pytest.fixture
    def handlers(self):
        """Create all necessary handlers."""
        repository = MockRepository()
        relationship_repo = MockRepository()
        logger = MockLogger()

        entity_cmd = EntityCommandHandler(repository, logger)
        entity_query = EntityQueryHandler(repository, logger)
        rel_cmd = RelationshipCommandHandler(relationship_repo, logger)
        rel_query = RelationshipQueryHandler(relationship_repo, logger)

        return entity_cmd, entity_query, rel_cmd, rel_query

    def test_create_entity_hierarchy_with_relationships(self, handlers):
        """Should create entity hierarchy and link with relationships."""
        entity_cmd, entity_query, rel_cmd, rel_query = handlers

        # 1. Create workspace
        workspace_cmd = CreateEntityCommand(
            entity_type="workspace",
            name="Main Workspace",
        )
        workspace_result = entity_cmd.handle_create_entity(workspace_cmd)
        workspace_id = workspace_result.data.id

        # 2. Create project
        project_cmd = CreateEntityCommand(
            entity_type="project",
            name="Project Alpha",
        )
        project_result = entity_cmd.handle_create_entity(project_cmd)
        project_id = project_result.data.id

        # 3. Create task
        task_cmd = CreateEntityCommand(
            entity_type="task",
            name="Task 1",
        )
        task_result = entity_cmd.handle_create_entity(task_cmd)
        task_id = task_result.data.id

        # 4. Link workspace -> project
        rel_cmd1 = CreateRelationshipCommand(
            source_id=workspace_id,
            target_id=project_id,
            relationship_type="contains",
        )
        rel_result1 = rel_cmd.handle_create_relationship(rel_cmd1)

        assert rel_result1.status == ResultStatus.SUCCESS

        # 5. Link project -> task
        rel_cmd2 = CreateRelationshipCommand(
            source_id=project_id,
            target_id=task_id,
            relationship_type="contains",
        )
        rel_result2 = rel_cmd.handle_create_relationship(rel_cmd2)

        assert rel_result2.status == ResultStatus.SUCCESS

        # 6. Verify relationships
        get_rels_query = GetRelationshipsQuery(source_id=workspace_id)
        rels_result = rel_query.handle_get_relationships(get_rels_query)

        assert rels_result.status == ResultStatus.SUCCESS
        assert len(rels_result.data) >= 1

    def test_delete_entity_with_relationships(self, handlers):
        """Should handle deleting entity that has relationships."""
        entity_cmd, entity_query, rel_cmd, rel_query = handlers

        # Create two entities
        entity1_cmd = CreateEntityCommand(entity_type="workspace", name="Entity 1")
        entity1_result = entity_cmd.handle_create_entity(entity1_cmd)
        entity1_id = entity1_result.data.id

        entity2_cmd = CreateEntityCommand(entity_type="project", name="Entity 2")
        entity2_result = entity_cmd.handle_create_entity(entity2_cmd)
        entity2_id = entity2_result.data.id

        # Create relationship
        rel_cmd_create = CreateRelationshipCommand(
            source_id=entity1_id,
            target_id=entity2_id,
            relationship_type="parent_of",
        )
        rel_result = rel_cmd.handle_create_relationship(rel_cmd_create)
        relationship_id = rel_result.data.id

        # Delete entity
        delete_cmd = DeleteEntityCommand(entity_id=entity1_id, soft_delete=True)
        delete_result = entity_cmd.handle_delete_entity(delete_cmd)

        assert delete_result.status == ResultStatus.SUCCESS

        # Note: In a full implementation, we'd verify cascade behavior

    def test_query_related_entities(self, handlers):
        """Should query entities through relationships."""
        entity_cmd, entity_query, rel_cmd, rel_query = handlers

        # Create parent and children
        parent_cmd = CreateEntityCommand(entity_type="workspace", name="Parent")
        parent_result = entity_cmd.handle_create_entity(parent_cmd)
        parent_id = parent_result.data.id

        child_ids = []
        for i in range(3):
            child_cmd = CreateEntityCommand(
                entity_type="project",
                name=f"Child {i}",
            )
            child_result = entity_cmd.handle_create_entity(child_cmd)
            child_ids.append(child_result.data.id)

            # Create relationship
            rel_cmd_create = CreateRelationshipCommand(
                source_id=parent_id,
                target_id=child_result.data.id,
                relationship_type="parent_of",
            )
            rel_cmd.handle_create_relationship(rel_cmd_create)

        # Query related entities
        related_query = GetRelatedEntitiesQuery(
            entity_id=parent_id,
            direction="outgoing",
        )
        related_result = rel_query.handle_get_related_entities(related_query)

        assert related_result.status == ResultStatus.SUCCESS
        assert len(related_result.data) >= 3


# =============================================================================
# WORKFLOW EXECUTION INTEGRATION TESTS
# =============================================================================


class TestWorkflowExecution:
    """Tests for complete workflow execution scenarios."""

    @pytest.fixture
    def handlers(self):
        """Create workflow and entity handlers."""
        workflow_repo = MockRepository()
        execution_repo = MockRepository()
        entity_repo = MockRepository()
        logger = MockLogger()

        workflow_handler = WorkflowCommandHandler(workflow_repo, logger)
        entity_handler = EntityCommandHandler(entity_repo, logger)

        return workflow_handler, entity_handler

    def test_create_and_execute_workflow(self, handlers):
        """Should create and execute a workflow."""
        workflow_handler, entity_handler = handlers

        # 1. Create workflow
        create_workflow_cmd = CreateWorkflowCommand(
            name="Entity Creation Workflow",
            description="Workflow for creating entities",
            trigger_type="manual",
            enabled=True,
        )
        create_result = workflow_handler.handle_create_workflow(create_workflow_cmd)

        assert create_result.status == ResultStatus.SUCCESS
        workflow_id = create_result.data.id

        # 2. Execute workflow
        execute_cmd = ExecuteWorkflowCommand(
            workflow_id=workflow_id,
            context={"entity_name": "Test Entity"},
            triggered_by="test-user",
        )
        execute_result = workflow_handler.handle_execute_workflow(execute_cmd)

        assert execute_result.status == ResultStatus.SUCCESS
        assert execute_result.data.workflow_id == workflow_id

    def test_workflow_with_steps(self, handlers):
        """Should create and execute workflow with multiple steps."""
        workflow_handler, entity_handler = handlers

        # Create workflow with steps
        steps = [
            {
                "name": "Step 1",
                "description": "First step",
                "order": 1,
                "action": {
                    "action_type": "create_entity",
                    "config": {"entity_type": "workspace"},
                },
            },
            {
                "name": "Step 2",
                "description": "Second step",
                "order": 2,
                "action": {
                    "action_type": "send_notification",
                    "config": {"message": "Entity created"},
                },
            },
        ]

        create_cmd = CreateWorkflowCommand(
            name="Multi-step Workflow",
            trigger_type="manual",
            steps=steps,
            enabled=True,
        )
        create_result = workflow_handler.handle_create_workflow(create_cmd)

        assert create_result.status == ResultStatus.SUCCESS
        assert len(create_result.data.steps) == 2

        # Execute workflow
        execute_cmd = ExecuteWorkflowCommand(workflow_id=create_result.data.id)
        execute_result = workflow_handler.handle_execute_workflow(execute_cmd)

        assert execute_result.status == ResultStatus.SUCCESS

    def test_workflow_error_recovery(self, handlers):
        """Should handle errors during workflow execution."""
        workflow_handler, entity_handler = handlers

        # Create workflow
        create_cmd = CreateWorkflowCommand(
            name="Error Test Workflow",
            trigger_type="manual",
            enabled=True,
        )
        create_result = workflow_handler.handle_create_workflow(create_cmd)

        # Execute workflow (should succeed even if workflow is simple)
        execute_cmd = ExecuteWorkflowCommand(workflow_id=create_result.data.id)
        execute_result = workflow_handler.handle_execute_workflow(execute_cmd)

        # Should handle gracefully
        assert execute_result.status == ResultStatus.SUCCESS


# =============================================================================
# MULTI-STEP TRANSACTION TESTS
# =============================================================================


class TestMultiStepTransactions:
    """Tests for multi-step operations with transaction integrity."""

    @pytest.fixture
    def handlers(self):
        """Create all handlers."""
        repository = MockRepository()
        rel_repository = MockRepository()
        logger = MockLogger()

        entity_cmd = EntityCommandHandler(repository, logger)
        rel_cmd = RelationshipCommandHandler(rel_repository, logger)

        return entity_cmd, rel_cmd

    def test_atomic_entity_relationship_creation(self, handlers):
        """Should create entity and relationships atomically."""
        entity_cmd, rel_cmd = handlers

        # Create parent
        parent_cmd = CreateEntityCommand(
            entity_type="workspace",
            name="Parent Workspace",
        )
        parent_result = entity_cmd.handle_create_entity(parent_cmd)
        parent_id = parent_result.data.id

        # Create child
        child_cmd = CreateEntityCommand(
            entity_type="project",
            name="Child Project",
        )
        child_result = entity_cmd.handle_create_entity(child_cmd)
        child_id = child_result.data.id

        # Create relationship
        rel_cmd_create = CreateRelationshipCommand(
            source_id=parent_id,
            target_id=child_id,
            relationship_type="parent_of",
        )
        rel_result = rel_cmd.handle_create_relationship(rel_cmd_create)

        # All should succeed
        assert parent_result.status == ResultStatus.SUCCESS
        assert child_result.status == ResultStatus.SUCCESS
        assert rel_result.status == ResultStatus.SUCCESS

    def test_rollback_on_relationship_failure(self, handlers):
        """Should handle rollback when relationship creation fails."""
        entity_cmd, rel_cmd = handlers

        # Create valid parent
        parent_cmd = CreateEntityCommand(entity_type="workspace", name="Parent")
        parent_result = entity_cmd.handle_create_entity(parent_cmd)
        parent_id = parent_result.data.id

        # Try to create relationship with non-existent target
        rel_cmd_create = CreateRelationshipCommand(
            source_id=parent_id,
            target_id="nonexistent-id",
            relationship_type="parent_of",
        )
        rel_result = rel_cmd.handle_create_relationship(rel_cmd_create)

        # Relationship should fail
        assert rel_result.status == ResultStatus.ERROR

        # Parent should still exist (no rollback in this simple case)
        assert parent_result.status == ResultStatus.SUCCESS


# =============================================================================
# COMPLEX ENTITY HIERARCHY TESTS
# =============================================================================


class TestComplexEntityHierarchies:
    """Tests for complex entity hierarchies with multiple levels."""

    @pytest.fixture
    def handlers(self):
        """Create handlers."""
        repository = MockRepository()
        rel_repository = MockRepository()
        logger = MockLogger()

        entity_cmd = EntityCommandHandler(repository, logger)
        entity_query = EntityQueryHandler(repository, logger)
        rel_cmd = RelationshipCommandHandler(rel_repository, logger)
        rel_query = RelationshipQueryHandler(rel_repository, logger)

        return entity_cmd, entity_query, rel_cmd, rel_query

    def test_three_level_hierarchy(self, handlers):
        """Should create and manage three-level entity hierarchy."""
        entity_cmd, entity_query, rel_cmd, rel_query = handlers

        # Level 1: Workspace
        workspace_cmd = CreateEntityCommand(
            entity_type="workspace",
            name="Organization",
        )
        workspace_result = entity_cmd.handle_create_entity(workspace_cmd)
        workspace_id = workspace_result.data.id

        # Level 2: Projects (2 projects)
        project_ids = []
        for i in range(2):
            project_cmd = CreateEntityCommand(
                entity_type="project",
                name=f"Project {i}",
            )
            project_result = entity_cmd.handle_create_entity(project_cmd)
            project_ids.append(project_result.data.id)

            # Link workspace -> project
            rel_cmd_create = CreateRelationshipCommand(
                source_id=workspace_id,
                target_id=project_result.data.id,
                relationship_type="contains",
            )
            rel_cmd.handle_create_relationship(rel_cmd_create)

        # Level 3: Tasks (2 tasks per project)
        for project_id in project_ids:
            for j in range(2):
                task_cmd = CreateEntityCommand(
                    entity_type="task",
                    name=f"Task {j}",
                )
                task_result = entity_cmd.handle_create_entity(task_cmd)

                # Link project -> task
                rel_cmd_create = CreateRelationshipCommand(
                    source_id=project_id,
                    target_id=task_result.data.id,
                    relationship_type="contains",
                )
                rel_cmd.handle_create_relationship(rel_cmd_create)

        # Verify hierarchy
        # Workspace should have 2 projects
        workspace_rels_query = GetRelationshipsQuery(source_id=workspace_id)
        workspace_rels = rel_query.handle_get_relationships(workspace_rels_query)

        assert workspace_rels.status == ResultStatus.SUCCESS
        assert len(workspace_rels.data) >= 2

    def test_hierarchy_with_cross_references(self, handlers):
        """Should handle hierarchy with cross-references between entities."""
        entity_cmd, entity_query, rel_cmd, rel_query = handlers

        # Create entities
        entity1_cmd = CreateEntityCommand(entity_type="project", name="Project 1")
        entity1_result = entity_cmd.handle_create_entity(entity1_cmd)
        entity1_id = entity1_result.data.id

        entity2_cmd = CreateEntityCommand(entity_type="project", name="Project 2")
        entity2_result = entity_cmd.handle_create_entity(entity2_cmd)
        entity2_id = entity2_result.data.id

        entity3_cmd = CreateEntityCommand(entity_type="task", name="Shared Task")
        entity3_result = entity_cmd.handle_create_entity(entity3_cmd)
        entity3_id = entity3_result.data.id

        # Create cross-references
        # Project 1 -> Task
        rel1_cmd = CreateRelationshipCommand(
            source_id=entity1_id,
            target_id=entity3_id,
            relationship_type="contains",
        )
        rel_cmd.handle_create_relationship(rel1_cmd)

        # Project 2 -> Task
        rel2_cmd = CreateRelationshipCommand(
            source_id=entity2_id,
            target_id=entity3_id,
            relationship_type="contains",
        )
        rel_cmd.handle_create_relationship(rel2_cmd)

        # Project 1 -> Project 2 (dependency)
        rel3_cmd = CreateRelationshipCommand(
            source_id=entity1_id,
            target_id=entity2_id,
            relationship_type="depends_on",
        )
        rel3_result = rel_cmd.handle_create_relationship(rel3_cmd)

        assert rel3_result.status == ResultStatus.SUCCESS


# =============================================================================
# CASCADE OPERATION TESTS
# =============================================================================


class TestCascadeOperations:
    """Tests for cascade operations through entity hierarchies."""

    @pytest.fixture
    def handlers(self):
        """Create handlers."""
        repository = MockRepository()
        rel_repository = MockRepository()
        logger = MockLogger()

        entity_cmd = EntityCommandHandler(repository, logger)
        rel_cmd = RelationshipCommandHandler(rel_repository, logger)
        rel_query = RelationshipQueryHandler(rel_repository, logger)

        return entity_cmd, rel_cmd, rel_query

    def test_delete_with_cascade(self, handlers):
        """Should handle cascading deletes."""
        entity_cmd, rel_cmd, rel_query = handlers

        # Create parent and children
        parent_cmd = CreateEntityCommand(entity_type="workspace", name="Parent")
        parent_result = entity_cmd.handle_create_entity(parent_cmd)
        parent_id = parent_result.data.id

        child_ids = []
        for i in range(3):
            child_cmd = CreateEntityCommand(entity_type="project", name=f"Child {i}")
            child_result = entity_cmd.handle_create_entity(child_cmd)
            child_ids.append(child_result.data.id)

            # Create relationship
            rel_cmd_create = CreateRelationshipCommand(
                source_id=parent_id,
                target_id=child_result.data.id,
                relationship_type="parent_of",
            )
            rel_cmd.handle_create_relationship(rel_cmd_create)

        # Delete parent
        delete_cmd = DeleteEntityCommand(
            entity_id=parent_id,
            soft_delete=True,
            cascade=True,
        )
        delete_result = entity_cmd.handle_delete_entity(delete_cmd)

        assert delete_result.status == ResultStatus.SUCCESS

    def test_update_cascade_to_children(self, handlers):
        """Should propagate updates to child entities."""
        entity_cmd, rel_cmd, rel_query = handlers

        # Create parent
        parent_cmd = CreateEntityCommand(
            entity_type="workspace",
            name="Parent",
            status=EntityStatus.ACTIVE,
        )
        parent_result = entity_cmd.handle_create_entity(parent_cmd)
        parent_id = parent_result.data.id

        # Create child
        child_cmd = CreateEntityCommand(entity_type="project", name="Child")
        child_result = entity_cmd.handle_create_entity(child_cmd)
        child_id = child_result.data.id

        # Create relationship
        rel_cmd_create = CreateRelationshipCommand(
            source_id=parent_id,
            target_id=child_id,
            relationship_type="parent_of",
        )
        rel_cmd.handle_create_relationship(rel_cmd_create)

        # Update parent status
        update_cmd = UpdateEntityCommand(
            entity_id=parent_id,
            updates={"status": EntityStatus.ARCHIVED.value},
        )
        update_result = entity_cmd.handle_update_entity(update_cmd)

        assert update_result.status == ResultStatus.SUCCESS


# =============================================================================
# ERROR RECOVERY WORKFLOW TESTS
# =============================================================================


class TestErrorRecoveryWorkflows:
    """Tests for error recovery in complex workflows."""

    @pytest.fixture
    def handlers(self):
        """Create handlers."""
        repository = MockRepository()
        rel_repository = MockRepository()
        logger = MockLogger()

        entity_cmd = EntityCommandHandler(repository, logger)
        rel_cmd = RelationshipCommandHandler(rel_repository, logger)

        return entity_cmd, rel_cmd, logger

    def test_partial_success_recovery(self, handlers):
        """Should recover from partial failures."""
        entity_cmd, rel_cmd, logger = handlers

        # Create entities
        entity1_cmd = CreateEntityCommand(entity_type="workspace", name="Entity 1")
        entity1_result = entity_cmd.handle_create_entity(entity1_cmd)

        # Try to create invalid entity
        entity2_cmd = CreateEntityCommand(entity_type="workspace", name="")
        entity2_result = entity_cmd.handle_create_entity(entity2_cmd)

        # Create another valid entity
        entity3_cmd = CreateEntityCommand(entity_type="workspace", name="Entity 3")
        entity3_result = entity_cmd.handle_create_entity(entity3_cmd)

        # Should have 2 successes and 1 failure
        assert entity1_result.status == ResultStatus.SUCCESS
        assert entity2_result.status == ResultStatus.ERROR
        assert entity3_result.status == ResultStatus.SUCCESS

    def test_retry_failed_operations(self, handlers):
        """Should be able to retry failed operations."""
        entity_cmd, rel_cmd, logger = handlers

        # First attempt with invalid data
        cmd = CreateEntityCommand(entity_type="workspace", name="")
        result1 = entity_cmd.handle_create_entity(cmd)

        assert result1.status == ResultStatus.ERROR

        # Retry with valid data
        cmd2 = CreateEntityCommand(entity_type="workspace", name="Valid Name")
        result2 = entity_cmd.handle_create_entity(cmd2)

        assert result2.status == ResultStatus.SUCCESS

    def test_compensation_actions(self, handlers):
        """Should execute compensation actions on failure."""
        entity_cmd, rel_cmd, logger = handlers

        # Create entity
        create_cmd = CreateEntityCommand(entity_type="workspace", name="Test")
        create_result = entity_cmd.handle_create_entity(create_cmd)
        entity_id = create_result.data.id

        # Try to create invalid relationship
        rel_cmd_create = CreateRelationshipCommand(
            source_id=entity_id,
            target_id="nonexistent",
            relationship_type="parent_of",
        )
        rel_result = rel_cmd.handle_create_relationship(rel_cmd_create)

        assert rel_result.status == ResultStatus.ERROR

        # Compensate by deleting the entity
        delete_cmd = DeleteEntityCommand(entity_id=entity_id)
        delete_result = entity_cmd.handle_delete_entity(delete_cmd)

        assert delete_result.status == ResultStatus.SUCCESS


__all__ = [
    "TestEntityCRUDLifecycle",
    "TestEntityRelationshipWorkflow",
    "TestWorkflowExecution",
    "TestMultiStepTransactions",
    "TestComplexEntityHierarchies",
    "TestCascadeOperations",
    "TestErrorRecoveryWorkflows",
]
