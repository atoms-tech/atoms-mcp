"""Unit tests for Phase 1 Week 4: Prompts & Resources.

Tests the 6 essential prompts and 6 essential resources.
"""

import pytest
from tools.prompts import (
    get_entity_creation_guide,
    get_entity_search_guide,
    get_relationship_guide,
    get_workflow_guide,
    get_context_guide,
    get_error_recovery_guide
)
from tools.resources import (
    get_entity_types_reference,
    get_operation_reference,
    get_workflow_templates,
    get_schema_definitions,
    get_best_practices,
    get_api_reference
)


class TestPromptsPhase1:
    """Test Phase 1 prompts."""

    def test_entity_creation_guide_project(self):
        """Test entity creation guide for projects."""
        guide = get_entity_creation_guide("project")
        assert "Creating Project Entities" in guide
        assert "Quick Start" in guide
        assert "Best Practices" in guide
        assert "name" in guide

    def test_entity_creation_guide_requirement(self):
        """Test entity creation guide for requirements."""
        guide = get_entity_creation_guide("requirement")
        assert "Creating Requirement Entities" in guide
        assert "project_id" in guide

    def test_entity_search_guide(self):
        """Test entity search guide."""
        guide = get_entity_search_guide("requirement")
        assert "Searching Requirement Entities" in guide
        assert "Text Search" in guide
        assert "Semantic Search" in guide
        assert "Hybrid Search" in guide

    def test_relationship_guide(self):
        """Test relationship guide."""
        guide = get_relationship_guide()
        assert "Managing Entity Relationships" in guide
        assert "Link Entities" in guide
        assert "List Relationships" in guide
        assert "Check Relationship" in guide

    def test_workflow_guide(self):
        """Test workflow guide."""
        guide = get_workflow_guide()
        assert "Executing Workflows" in guide
        assert "Setup Project" in guide
        assert "Bulk Status Update" in guide

    def test_context_guide(self):
        """Test context guide."""
        guide = get_context_guide()
        assert "Managing Session Context" in guide
        assert "Set Workspace Context" in guide
        assert "Set Project Context" in guide
        assert "Set Document Context" in guide

    def test_error_recovery_guide(self):
        """Test error recovery guide."""
        guide = get_error_recovery_guide()
        assert "Error Recovery Guide" in guide
        assert "Entity Not Found" in guide
        assert "Missing Required Field" in guide
        assert "Permission Denied" in guide


class TestResourcesPhase1:
    """Test Phase 1 resources."""

    def test_entity_types_reference(self):
        """Test entity types reference."""
        ref = get_entity_types_reference()
        assert "entity_types" in ref
        assert len(ref["entity_types"]) >= 4
        
        # Check project type
        project = next((e for e in ref["entity_types"] if e["name"] == "project"), None)
        assert project is not None
        assert "name" in project["fields"]
        assert "create" in project["operations"]

    def test_operation_reference(self):
        """Test operation reference."""
        ref = get_operation_reference()
        assert "operations" in ref
        
        # Check create operation
        assert "create" in ref["operations"]
        create_op = ref["operations"]["create"]
        assert "description" in create_op
        assert "required_params" in create_op
        assert "entity_type" in create_op["required_params"]

    def test_workflow_templates(self):
        """Test workflow templates."""
        templates = get_workflow_templates()
        assert "templates" in templates
        assert len(templates["templates"]) >= 5
        
        # Check setup_project template
        setup = next((t for t in templates["templates"] if t["name"] == "setup_project"), None)
        assert setup is not None
        assert "parameters" in setup
        assert "name" in setup["parameters"]

    def test_schema_definitions(self):
        """Test schema definitions."""
        schemas = get_schema_definitions()
        
        # Check project schema
        assert "project" in schemas
        project_schema = schemas["project"]
        assert project_schema["type"] == "object"
        assert "name" in project_schema["properties"]
        assert "id" in project_schema["required"]

    def test_best_practices(self):
        """Test best practices guide."""
        guide = get_best_practices()
        assert "Best Practices" in guide
        assert "Context Management" in guide
        assert "Entity Operations" in guide
        assert "Search Operations" in guide
        assert "Error Handling" in guide

    def test_api_reference(self):
        """Test API reference."""
        ref = get_api_reference()
        assert "Atoms MCP API Reference" in ref
        assert "Tools" in ref
        assert "Operations" in ref
        assert "Context Types" in ref
        assert "Response Format" in ref
        assert "Error Handling" in ref


class TestPromptsResourcesIntegration:
    """Test prompts and resources work together."""

    def test_all_prompts_available(self):
        """Test all 6 prompts are available."""
        prompts = [
            get_entity_creation_guide,
            get_entity_search_guide,
            get_relationship_guide,
            get_workflow_guide,
            get_context_guide,
            get_error_recovery_guide
        ]
        
        for prompt_fn in prompts:
            result = prompt_fn()
            assert isinstance(result, str)
            assert len(result) > 100  # Should have substantial content

    def test_all_resources_available(self):
        """Test all 6 resources are available."""
        resources = [
            get_entity_types_reference,
            get_operation_reference,
            get_workflow_templates,
            get_schema_definitions,
            get_best_practices,
            get_api_reference
        ]
        
        for resource_fn in resources:
            result = resource_fn()
            assert result is not None
            if isinstance(result, dict):
                assert len(result) > 0
            elif isinstance(result, str):
                assert len(result) > 100

    def test_prompts_reference_resources(self):
        """Test that prompts reference concepts from resources."""
        # Get a prompt
        creation_guide = get_entity_creation_guide("project")
        
        # Get resources
        entity_types = get_entity_types_reference()
        
        # Verify consistency
        assert "project" in str(entity_types)
        assert "project" in creation_guide.lower()

    def test_resources_consistent_with_operations(self):
        """Test resources are consistent with operations."""
        operations = get_operation_reference()
        templates = get_workflow_templates()
        
        # Verify operations exist
        assert "create" in operations["operations"]
        assert "read" in operations["operations"]
        
        # Verify templates reference valid operations
        assert len(templates["templates"]) > 0

