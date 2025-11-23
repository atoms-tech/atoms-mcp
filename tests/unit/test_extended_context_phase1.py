"""Unit tests for Phase 1: Extended Context implementation.

Tests the new document_id context type and auto-injection into entity_tool.
"""

import pytest
from services.context_manager import get_context


class TestExtendedContextPhase1:
    """Test Phase 1 extended context functionality."""

    @pytest.fixture
    def context(self):
        """Get global context instance."""
        ctx = get_context()
        ctx.clear()  # Clear before each test
        return ctx

    # ========== Document ID Context Tests ==========

    def test_set_document_id(self, context):
        """Test setting document_id context."""
        context.set_document_id("doc-123")
        assert context.get_document_id() == "doc-123"

    def test_get_document_id_when_not_set(self, context):
        """Test getting document_id when not set returns None."""
        assert context.get_document_id() is None

    def test_resolve_document_id_explicit(self, context):
        """Test resolve_document_id with explicit parameter."""
        context.set_document_id("doc-from-context")
        result = context.resolve_document_id("doc-explicit")
        assert result == "doc-explicit"  # Explicit takes priority

    def test_resolve_document_id_from_context(self, context):
        """Test resolve_document_id from context."""
        context.set_document_id("doc-from-context")
        result = context.resolve_document_id()
        assert result == "doc-from-context"

    def test_resolve_document_id_none(self, context):
        """Test resolve_document_id returns None when not set."""
        result = context.resolve_document_id()
        assert result is None

    # ========== Multiple Context Types Tests ==========

    def test_set_multiple_contexts(self, context):
        """Test setting multiple context types."""
        context.set_workspace_id("ws-1")
        context.set_project_id("proj-1")
        context.set_document_id("doc-1")

        assert context.get_workspace_id() == "ws-1"
        assert context.get_project_id() == "proj-1"
        assert context.get_document_id() == "doc-1"

    def test_clear_all_contexts(self, context):
        """Test clearing all contexts."""
        context.set_workspace_id("ws-1")
        context.set_project_id("proj-1")
        context.set_document_id("doc-1")

        context.clear()

        assert context.get_workspace_id() is None
        assert context.get_project_id() is None
        assert context.get_document_id() is None

    # ========== Context Isolation Tests ==========

    def test_context_isolation(self, context):
        """Test that context changes don't affect other context types."""
        context.set_workspace_id("ws-1")
        context.set_document_id("doc-1")

        # Change workspace
        context.set_workspace_id("ws-2")

        # Document should remain unchanged
        assert context.get_document_id() == "doc-1"
        assert context.get_workspace_id() == "ws-2"

    # ========== Context Overwrite Tests ==========

    def test_overwrite_document_id(self, context):
        """Test overwriting document_id context."""
        context.set_document_id("doc-1")
        assert context.get_document_id() == "doc-1"

        context.set_document_id("doc-2")
        assert context.get_document_id() == "doc-2"

    # ========== Resolution Priority Tests ==========

    def test_resolution_priority_explicit_over_context(self, context):
        """Test that explicit parameter has priority over context."""
        context.set_document_id("doc-from-context")
        context.set_workspace_id("ws-from-context")

        # Explicit should take priority (document_id is sync, workspace_id is async)
        assert context.resolve_document_id("doc-explicit") == "doc-explicit"
        # Note: resolve_workspace_id is async, so we test the sync version
        assert context.resolve_project_id("proj-explicit") == "proj-explicit"

    def test_resolution_priority_context_over_none(self, context):
        """Test that context is used when explicit is None."""
        context.set_document_id("doc-from-context")

        # Should use context when explicit is None
        assert context.resolve_document_id(None) == "doc-from-context"
        assert context.resolve_document_id() == "doc-from-context"

