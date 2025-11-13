"""
User Story Mapping for PM View

Maps test patterns to actual user stories in user-centric language.
Format: "As a [user], I can [action] so that [benefit]"
"""

from typing import Dict, List


class UserStoryMapper:
    """Maps tests to user stories for PM reporting."""
    
    # Epic: Entity Management
    # User stories in plain language
    USER_STORIES = {
        # Epic 1: Organization Management
        "User can create an organization": [
            "test_create_entity_parametrized[unit-organization",
            "test_create_organization",
        ],
        "User can view organization details": [
            "test_read_organization",
            "test_read",
        ],
        "User can update organization settings": [
            "test_update_organization",
            "test_update",
        ],
        "User can delete an organization": [
            "test_soft_delete",
            "test_hard_delete",
        ],
        "User can list all organizations": [
            "test_list",
            "test_search",
        ],
        
        # Epic 2: Project Management
        "User can create a project": [
            "test_create_entity_parametrized[unit-project",
            "test_create_project",
        ],
        "User can view project details": [
            "test_read_project",
            "test_read",
        ],
        "User can update project information": [
            "test_update_project",
            "test_update",
        ],
        "User can archive a project": [
            "test_hard_delete",
            "test_archive",
        ],
        "User can list projects in organization": [
            "test_list",
        ],
        
        # Epic 3: Document Management
        "User can create a document": [
            "test_create_document",
            "test_create_entity_parametrized[unit-document",
        ],
        "User can view document content": [
            "test_read_document",
            "test_read",
        ],
        "User can list documents in project": [
            "test_list_documents",
            "test_list",
        ],
        
        # Epic 4: Requirements Management
        "User can create requirements": [
            "test_create_requirement",
            "test_create_entity_parametrized[unit-requirement",
        ],
        "User can pull requirements from system": [
            "test_read_requirement",
            "test_read",
        ],
        "User can search requirements": [
            "test_search_requirement",
            "test_search",
        ],
        
        # Epic 5: Test Management
        "User can create test cases": [
            "test_create_test",
            "test_create_entity_parametrized[unit-test",
        ],
        "User can view test results": [
            "test_read_test",
            "test_read",
        ],
        
        # Epic 6: Workspace Management
        "User can view current workspace context": [
            "test_get_current_context",
            "test_get_context",
        ],
        "User can switch to organization workspace": [
            "test_set_organization_context",
            "test_set_context",
        ],
        "User can switch to project workspace": [
            "test_set_project_context",
            "test_set_context",
        ],
        "User can switch to document workspace": [
            "test_set_document_context",
            "test_set_context",
        ],
        "User can list all available workspaces": [
            "test_list_all_workspaces",
            "test_list_workspaces",
        ],
        "User can get workspace defaults": [
            "test_get_defaults",
        ],
        
        # Epic 7: Relationship Management
        "User can link entities together": [
            "test_link_basic",
            "test_link_with_metadata",
            "test_link",
        ],
        "User can unlink related entities": [
            "test_unlink_basic",
            "test_unlink",
        ],
        "User can view entity relationships": [
            "test_list_relationships",
            "test_list_related",
        ],
        "User can check if entities are related": [
            "test_check_relationship",
            "test_is_related",
        ],
        "User can trace links between requirements and tests": [
            "test_trace",
            "test_link",
        ],
        
        # Epic 8: Search & Query
        "User can search across all entities": [
            "test_basic_search",
            "test_search_multiple",
            "test_search",
        ],
        "User can filter search results": [
            "test_search_with_conditions",
            "test_search_with_filters",
            "test_filter",
        ],
        "User can perform semantic search": [
            "test_rag_search_semantic",
            "test_semantic_search",
        ],
        "User can perform keyword search": [
            "test_rag_search_keyword",
            "test_keyword_search",
        ],
        "User can perform hybrid search": [
            "test_rag_search_hybrid",
            "test_hybrid_search",
        ],
        "User can get entity count aggregates": [
            "test_aggregate_count",
            "test_aggregate",
        ],
        "User can find similar entities": [
            "test_similarity_search",
            "test_similar",
        ],
        
        # Epic 9: Workflow Automation
        "User can set up new project workflow": [
            "test_setup_project_workflow",
            "test_setup_project",
        ],
        "User can import requirements via workflow": [
            "test_import_requirements_workflow",
            "test_import_requirements",
        ],
        "User can bulk update statuses": [
            "test_bulk_status_update",
            "test_bulk_update",
        ],
        "User can onboard new organization": [
            "test_organization_onboarding",
            "test_onboarding",
        ],
        "User can run workflows with transactions": [
            "test_with_transaction_mode",
            "test_transaction",
        ],
        
        # Epic 10: Data Operations
        "User can batch create multiple entities": [
            "test_batch_create",
            "test_batch",
        ],
        "User can paginate through large lists": [
            "test_list_with_pagination",
            "test_pagination",
        ],
        "User can sort query results": [
            "test_search_with_ordering",
            "test_ordering",
            "test_sort",
        ],
        
        # Epic 11: Authentication & Security
        "User can log in with AuthKit": [
            "test_authkit_jwt_validation",
            "test_authkit_session_creation",
            "test_login",
        ],
        "User can maintain active session": [
            "test_authkit_session_validation",
            "test_session_validation",
        ],
        "User can log out securely": [
            "test_authkit_logout",
            "test_logout",
        ],
        "User data is protected by row-level security": [
            "test_supabase_rls",
            "test_rls",
        ],
    }
    
    # Epic grouping for hierarchical view
    EPICS = {
        "Organization Management": [
            "User can create an organization",
            "User can view organization details",
            "User can update organization settings",
            "User can delete an organization",
            "User can list all organizations",
        ],
        "Project Management": [
            "User can create a project",
            "User can view project details",
            "User can update project information",
            "User can archive a project",
            "User can list projects in organization",
        ],
        "Document Management": [
            "User can create a document",
            "User can view document content",
            "User can list documents in project",
        ],
        "Requirements Traceability": [
            "User can create requirements",
            "User can pull requirements from system",
            "User can search requirements",
            "User can trace links between requirements and tests",
        ],
        "Test Case Management": [
            "User can create test cases",
            "User can view test results",
        ],
        "Workspace Navigation": [
            "User can view current workspace context",
            "User can switch to organization workspace",
            "User can switch to project workspace",
            "User can switch to document workspace",
            "User can list all available workspaces",
            "User can get workspace defaults",
        ],
        "Entity Relationships": [
            "User can link entities together",
            "User can unlink related entities",
            "User can view entity relationships",
            "User can check if entities are related",
        ],
        "Search & Discovery": [
            "User can search across all entities",
            "User can filter search results",
            "User can perform semantic search",
            "User can perform keyword search",
            "User can perform hybrid search",
            "User can get entity count aggregates",
            "User can find similar entities",
        ],
        "Workflow Automation": [
            "User can set up new project workflow",
            "User can import requirements via workflow",
            "User can bulk update statuses",
            "User can onboard new organization",
            "User can run workflows with transactions",
        ],
        "Data Management": [
            "User can batch create multiple entities",
            "User can paginate through large lists",
            "User can sort query results",
        ],
        "Security & Access": [
            "User can log in with AuthKit",
            "User can maintain active session",
            "User can log out securely",
            "User data is protected by row-level security",
        ],
    }
    
    @classmethod
    def get_all_user_stories(cls) -> List[str]:
        """Get list of all user stories."""
        return list(cls.USER_STORIES.keys())
    
    @classmethod
    def get_epics(cls) -> List[str]:
        """Get list of all epics."""
        return list(cls.EPICS.keys())
    
    @classmethod
    def get_stories_for_epic(cls, epic: str) -> List[str]:
        """Get user stories for a specific epic."""
        return cls.EPICS.get(epic, [])
    
    @classmethod
    def get_test_patterns_for_story(cls, story: str) -> List[str]:
        """Get test patterns that validate a user story."""
        return cls.USER_STORIES.get(story, [])
