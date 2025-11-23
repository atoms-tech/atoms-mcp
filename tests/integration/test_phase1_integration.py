"""Integration tests for Phase 1: Extended Context, Query Consolidation, Smart Defaults.

Tests the complete workflow of Phase 1 features working together.
"""

import pytest
from services.context_manager import get_context
from services.fuzzy_matcher import FuzzyMatcher


class TestPhase1Integration:
    """Integration tests for Phase 1 features."""

    @pytest.fixture
    def context(self):
        """Get global context instance."""
        ctx = get_context()
        ctx.clear()
        return ctx

    # ========== Extended Context + Smart Defaults Integration ==========

    def test_context_persistence_across_operations(self, context):
        """Test context persists across multiple operations."""
        # Set context
        context.set_workspace_id("ws-1")
        context.set_project_id("proj-1")
        context.set_document_id("doc-1")

        # Record multiple operations
        for i in range(3):
            result = {
                "success": True,
                "entity_id": f"req-{i}",
                "data": {"name": f"Requirement {i}"}
            }
            context.record_operation("create", "requirement", result)

        # Verify context still set
        assert context.get_workspace_id() == "ws-1"
        assert context.get_project_id() == "proj-1"
        assert context.get_document_id() == "doc-1"

        # Verify operations recorded
        history = context.get_operation_history()
        assert len(history) == 3

    def test_batch_context_with_pagination(self, context):
        """Test batch context tracking with pagination."""
        # Record batch create
        for i in range(5):
            result = {
                "success": True,
                "entity_id": f"req-{i}",
                "data": {"name": f"Requirement {i}"}
            }
            context.record_operation("create", "requirement", result)

        # Set pagination state
        context.set_pagination_state("requirement", limit=20, offset=0, total=100)

        # Verify last created
        last = context.get_last_created_entity("requirement")
        assert last["id"] == "req-4"

        # Verify pagination
        state = context.get_pagination_state("requirement")
        assert state["has_next"] is True
        assert state["current_page"] == 1

    def test_multiple_entity_types_context(self, context):
        """Test tracking multiple entity types independently."""
        # Create requirements
        for i in range(3):
            result = {
                "success": True,
                "entity_id": f"req-{i}",
                "data": {"name": f"Requirement {i}"}
            }
            context.record_operation("create", "requirement", result)

        # Create tests
        for i in range(2):
            result = {
                "success": True,
                "entity_id": f"test-{i}",
                "data": {"name": f"Test {i}"}
            }
            context.record_operation("create", "test", result)

        # Verify independent tracking
        last_req = context.get_last_created_entity("requirement")
        last_test = context.get_last_created_entity("test")

        assert last_req["id"] == "req-2"
        assert last_test["id"] == "test-1"

    # ========== Query Consolidation + Context Integration ==========

    def test_context_with_search_operation(self, context):
        """Test context is available for search operations."""
        # Set context
        context.set_workspace_id("ws-1")
        context.set_project_id("proj-1")

        # Verify context can be retrieved (sync methods)
        workspace = context.get_workspace_id()
        project = context.get_project_id()

        assert workspace == "ws-1"
        assert project == "proj-1"

    def test_parameter_resolution_priority(self, context):
        """Test parameter resolution priority (explicit > context > None)."""
        # Set context
        context.set_workspace_id("ws-from-context")
        context.set_project_id("proj-from-context")
        context.set_document_id("doc-from-context")

        # Test explicit takes priority (sync methods)
        assert context.resolve_project_id("proj-explicit") == "proj-explicit"
        assert context.resolve_document_id("doc-explicit") == "doc-explicit"

        # Test context used when explicit is None
        assert context.resolve_project_id(None) == "proj-from-context"
        assert context.resolve_document_id(None) == "doc-from-context"

    # ========== Smart Defaults + Error Handling Integration ==========

    def test_error_recovery_with_fuzzy_matching(self, context):
        """Test error recovery using fuzzy matching."""
        # Create some entities
        entities = [
            {"id": "req-1", "name": "Security Requirement"},
            {"id": "req-2", "name": "Performance Requirement"},
            {"id": "proj-1", "name": "My Project"}
        ]

        # Try to find similar to invalid ID
        invalid_id = "req-123"
        suggestions = FuzzyMatcher.find_similar_entities(
            invalid_id,
            entities,
            threshold=0.5,
            limit=2
        )

        # Verify suggestions
        assert len(suggestions) > 0
        assert suggestions[0]["entity"]["id"].startswith("req")

    def test_operation_history_with_context(self, context):
        """Test operation history tracks context changes."""
        # Set initial context
        context.set_workspace_id("ws-1")
        context.set_project_id("proj-1")

        # Record operations
        for i in range(3):
            result = {
                "success": True,
                "entity_id": f"req-{i}",
                "data": {"name": f"Requirement {i}"}
            }
            context.record_operation("create", "requirement", result)

        # Change context
        context.set_project_id("proj-2")

        # Record more operations
        for i in range(3, 5):
            result = {
                "success": True,
                "entity_id": f"req-{i}",
                "data": {"name": f"Requirement {i}"}
            }
            context.record_operation("create", "requirement", result)

        # Verify history
        history = context.get_operation_history()
        assert len(history) == 5
        assert history[0]["entity_id"] == "req-0"
        assert history[-1]["entity_id"] == "req-4"

    # ========== Complete Workflow Integration ==========

    def test_complete_phase1_workflow(self, context):
        """Test complete Phase 1 workflow."""
        # 1. Set context
        context.set_workspace_id("ws-1")
        context.set_project_id("proj-1")
        context.set_document_id("doc-1")

        # 2. Create entities (simulated)
        entities = []
        for i in range(3):
            result = {
                "success": True,
                "entity_id": f"req-{i}",
                "data": {"name": f"Requirement {i}"}
            }
            context.record_operation("create", "requirement", result)
            # Store as entity dict for fuzzy matching
            entities.append({
                "id": f"req-{i}",
                "name": f"Requirement {i}"
            })

        # 3. Set pagination
        context.set_pagination_state("requirement", limit=20, offset=0, total=100)

        # 4. Verify all features work together
        assert context.get_workspace_id() == "ws-1"
        assert context.get_project_id() == "proj-1"
        assert context.get_document_id() == "doc-1"

        last = context.get_last_created_entity("requirement")
        assert last["id"] == "req-2"

        state = context.get_pagination_state("requirement")
        assert state["has_next"] is True

        history = context.get_operation_history()
        assert len(history) == 3

        # 5. Test error recovery
        invalid_id = "req-999"
        suggestions = FuzzyMatcher.find_similar_entities(
            invalid_id,
            entities,
            threshold=0.5,
            limit=2
        )
        assert len(suggestions) > 0

    def test_context_clearing(self, context):
        """Test context clearing resets all state."""
        # Set everything
        context.set_workspace_id("ws-1")
        context.set_project_id("proj-1")
        context.set_document_id("doc-1")

        for i in range(3):
            result = {
                "success": True,
                "entity_id": f"req-{i}",
                "data": {}
            }
            context.record_operation("create", "requirement", result)

        context.set_pagination_state("requirement", limit=20, offset=0, total=100)

        # Clear
        context.clear()

        # Verify all cleared
        assert context.get_workspace_id() is None
        assert context.get_project_id() is None
        assert context.get_document_id() is None
        assert len(context.get_operation_history()) == 0
        assert context.get_pagination_state("requirement") is None

