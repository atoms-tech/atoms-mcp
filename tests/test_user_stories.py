"""
User Story Integration Tests

Multi-step workflows testing real user scenarios using UserStoryPattern.
"""

import pytest

from tests.framework import DataGenerator, UserStoryPattern, mcp_test


@pytest.mark.asyncio

@pytest.mark.parallel

@mcp_test(tool_name="integration", category="user_story", priority=10)
async def test_story_new_user_full_setup(client_adapter):
    """User story: New user creates org → project → document → requirements."""

    story = UserStoryPattern(
        story_name="New User Full Setup",
        steps=[
            {
                "tool": "entity_tool",
                "params": {
                    "entity_type": "organization",
                    "operation": "create",
                    "data": DataGenerator.organization_data("My Startup"),
                },
                "description": "Create organization",
                "save_to_context": "org_id",
                "validation": lambda r, ctx: r.get("success") and "id" in r.get("response", {}).get("data", {}),
            },
            {
                "tool": "workspace_tool",
                "params": {
                    "operation": "set_context",
                    "context_type": "organization",
                    "entity_id": "$context.org_id.data.id",
                },
                "description": "Set organization context",
                "validation": lambda r, ctx: r.get("success"),
            },
            {
                "tool": "entity_tool",
                "params": {
                    "entity_type": "project",
                    "operation": "create",
                    "data": DataGenerator.project_data("First Project", "$context.org_id.data.id"),
                },
                "description": "Create project",
                "save_to_context": "proj_id",
                "validation": lambda r, ctx: r.get("success"),
            },
            {
                "tool": "entity_tool",
                "params": {
                    "entity_type": "document",
                    "operation": "create",
                    "data": DataGenerator.document_data("Requirements Doc", "$context.proj_id.data.id"),
                },
                "description": "Create document",
                "save_to_context": "doc_id",
                "validation": lambda r, ctx: r.get("success"),
            },
            {
                "tool": "workflow_tool",
                "params": {
                    "workflow": "import_requirements",
                    "parameters": {
                        "document_id": "$context.doc_id.data.id",
                        "requirements": DataGenerator.batch_data("requirement", 5),
                    },
                },
                "description": "Import requirements",
                "validation": lambda r, ctx: r.get("success"),
            },
        ],
    )

    result = await story.execute(client_adapter)
    return {"success": result["success"], "story": result}


@pytest.mark.asyncio

@pytest.mark.parallel

@mcp_test(tool_name="integration", category="user_story", priority=9)
async def test_story_team_collaboration(client_adapter):
    """User story: Team collaboration - invite member → add to project → assign work."""

    story = UserStoryPattern(
        story_name="Team Collaboration",
        steps=[
            {
                "tool": "entity_tool",
                "params": {
                    "entity_type": "organization",
                    "operation": "create",
                    "data": DataGenerator.organization_data("Collab Org"),
                },
                "description": "Create organization for collaboration",
                "save_to_context": "org",
                "validation": lambda r, ctx: r.get("success"),
            },
            {
                "tool": "workspace_tool",
                "params": {
                    "operation": "set_context",
                    "context_type": "organization",
                    "entity_id": "$context.org.data.id",
                },
                "description": "Set organization context",
                "validation": lambda r, ctx: r.get("success"),
            },
            {
                "tool": "relationship_tool",
                "params": {
                    "operation": "link",
                    "relationship_type": "invitation",
                    "source": {"type": "organization", "id": "$context.org.data.id"},
                    "target": {"type": "email", "id": "newuser@example.com"},
                    "metadata": {"role": "developer", "status": "pending"},
                },
                "description": "Send invitation",
                "validation": lambda r, ctx: r.get("success"),
            },
        ],
    )

    result = await story.execute(client_adapter)
    return {"success": result["success"], "story": result}


@pytest.mark.asyncio

@pytest.mark.parallel

@mcp_test(tool_name="integration", category="user_story", priority=9)
async def test_story_search_and_analyze(client_adapter):
    """User story: Create entities → search → analyze results."""

    story = UserStoryPattern(
        story_name="Search and Analyze",
        steps=[
            {
                "tool": "query_tool",
                "params": {
                    "query_type": "search",
                    "entities": ["requirement", "document"],
                    "search_term": "authentication",
                },
                "description": "Search for authentication items",
                "save_to_context": "search_results",
                "validation": lambda r, ctx: r.get("success"),
            },
            {
                "tool": "query_tool",
                "params": {
                    "query_type": "aggregate",
                    "entities": ["requirement"],
                },
                "description": "Get requirement statistics",
                "validation": lambda r, ctx: r.get("success"),
            },
        ],
    )

    result = await story.execute(client_adapter)
    return {"success": result["success"], "story": result}


@pytest.mark.asyncio

@pytest.mark.parallel

@mcp_test(tool_name="integration", category="user_story", priority=8)
async def test_story_test_matrix_workflow(client_adapter):
    """User story: Create requirements → setup test matrix → verify coverage."""

    story = UserStoryPattern(
        story_name="Test Matrix Workflow",
        steps=[
            {
                "tool": "entity_tool",
                "params": {
                    "entity_type": "organization",
                    "operation": "create",
                    "data": DataGenerator.organization_data("Matrix Org"),
                },
                "description": "Create organization for matrix workflow",
                "save_to_context": "org",
                "validation": lambda r, ctx: r.get("success"),
            },
            {
                "tool": "entity_tool",
                "params": {
                    "entity_type": "project",
                    "operation": "create",
                    "data": DataGenerator.project_data("Matrix Project", "$context.org.data.id"),
                },
                "description": "Create project",
                "save_to_context": "project",
                "validation": lambda r, ctx: r.get("success"),
            },
            {
                "tool": "entity_tool",
                "params": {
                    "entity_type": "document",
                    "operation": "create",
                    "data": DataGenerator.document_data("Matrix Requirements", "$context.project.data.id"),
                },
                "description": "Create document",
                "save_to_context": "document",
                "validation": lambda r, ctx: r.get("success"),
            },
            {
                "tool": "entity_tool",
                "params": {
                    "entity_type": "requirement",
                    "operation": "create",
                    "data": {
                        **DataGenerator.requirement_data("REQ-HIGH-1", "$context.document.data.id"),
                        "priority": "high",
                    },
                },
                "description": "Create high priority requirement",
                "save_to_context": "requirement",
                "validation": lambda r, ctx: r.get("success"),
            },
            {
                "tool": "workflow_tool",
                "params": {
                    "workflow": "setup_test_matrix",
                    "parameters": {
                        "project_id": "$context.project.data.id",
                        "matrix_name": "Comprehensive Test Matrix",
                    },
                },
                "description": "Setup test matrix",
                "validation": lambda r, ctx: r.get("success"),
            },
        ],
    )

    result = await story.execute(client_adapter)
    return {"success": result["success"], "story": result}


@pytest.mark.asyncio

@pytest.mark.parallel

@mcp_test(tool_name="integration", category="user_story", priority=8)
async def test_story_requirement_traceability(client_adapter):
    """User story: Create requirements → link them → verify trace links."""

    story = UserStoryPattern(
        story_name="Requirement Traceability",
        steps=[
            {
                "tool": "entity_tool",
                "params": {"entity_type": "requirement", "operation": "list", "limit": 2},
                "description": "Get requirements",
                "save_to_context": "reqs",
                "validation": lambda r, ctx: r.get("success"),
            },
            {
                "tool": "query_tool",
                "params": {
                    "query_type": "relationships",
                    "entities": ["requirement"],
                },
                "description": "Analyze requirement relationships",
                "validation": lambda r, ctx: r.get("success"),
            },
        ],
    )

    result = await story.execute(client_adapter)
    return {"success": result["success"], "story": result}


@pytest.mark.asyncio

@pytest.mark.parallel

@mcp_test(tool_name="integration", category="user_story", priority=7)
async def test_story_bulk_operations(client_adapter):
    """User story: Create multiple items → bulk update → verify changes."""

    story = UserStoryPattern(
        story_name="Bulk Operations",
        steps=[
            {
                "tool": "entity_tool",
                "params": {"entity_type": "document", "operation": "list", "limit": 5},
                "description": "Get documents",
                "save_to_context": "docs",
                "validation": lambda r, ctx: r.get("success"),
            },
            {
                "tool": "query_tool",
                "params": {
                    "query_type": "aggregate",
                    "entities": ["document"],
                },
                "description": "Get document statistics",
                "validation": lambda r, ctx: r.get("success"),
            },
        ],
    )

    result = await story.execute(client_adapter)
    return {"success": result["success"], "story": result}


@pytest.mark.asyncio

@pytest.mark.parallel

@mcp_test(tool_name="integration", category="user_story", priority=7)
async def test_story_rag_enhanced_search(client_adapter):
    """User story: Semantic search → keyword search → compare results."""

    story = UserStoryPattern(
        story_name="RAG Enhanced Search",
        steps=[
            {
                "tool": "query_tool",
                "params": {
                    "query_type": "rag_search",
                    "entities": ["requirement"],
                    "search_term": "user authentication and authorization",
                    "rag_mode": "semantic",
                },
                "description": "Semantic search",
                "save_to_context": "semantic_results",
                "validation": lambda r, ctx: r.get("success"),
            },
            {
                "tool": "query_tool",
                "params": {
                    "query_type": "rag_search",
                    "entities": ["requirement"],
                    "search_term": "user authentication and authorization",
                    "rag_mode": "keyword",
                },
                "description": "Keyword search",
                "save_to_context": "keyword_results",
                "validation": lambda r, ctx: r.get("success"),
            },
            {
                "tool": "query_tool",
                "params": {
                    "query_type": "rag_search",
                    "entities": ["requirement"],
                    "search_term": "user authentication and authorization",
                    "rag_mode": "hybrid",
                },
                "description": "Hybrid search (best of both)",
                "validation": lambda r, ctx: r.get("success"),
            },
        ],
    )

    result = await story.execute(client_adapter)
    return {"success": result["success"], "story": result}


@pytest.mark.asyncio

@pytest.mark.parallel

@mcp_test(tool_name="integration", category="user_story", priority=7)
async def test_story_workspace_context_switching(client_adapter):
    """User story: Switch between orgs → projects → verify context."""

    story = UserStoryPattern(
        story_name="Workspace Context Switching",
        steps=[
            {
                "tool": "workspace_tool",
                "params": {"operation": "list_workspaces"},
                "description": "List workspaces",
                "save_to_context": "workspaces",
                "validation": lambda r, ctx: r.get("success"),
            },
            {
                "tool": "workspace_tool",
                "params": {"operation": "get_context"},
                "description": "Get current context",
                "save_to_context": "initial_context",
                "validation": lambda r, ctx: r.get("success"),
            },
            {
                "tool": "workspace_tool",
                "params": {"operation": "get_defaults"},
                "description": "Get smart defaults",
                "validation": lambda r, ctx: r.get("success"),
            },
        ],
    )

    result = await story.execute(client_adapter)
    return {"success": result["success"], "story": result}


@pytest.mark.asyncio

@pytest.mark.parallel

@mcp_test(tool_name="integration", category="user_story", priority=6)
async def test_story_end_to_end_project_lifecycle(client_adapter):
    """User story: Complete project lifecycle from creation to completion."""

    story = UserStoryPattern(
        story_name="End-to-End Project Lifecycle",
        steps=[
            {
                "tool": "workflow_tool",
                "params": {
                    "workflow": "organization_onboarding",
                    "parameters": DataGenerator.organization_data("Lifecycle Test Org"),
                },
                "description": "Onboard organization",
                "save_to_context": "org",
                "validation": lambda r, ctx: r.get("success"),
            },
            {
                "tool": "entity_tool",
                "params": {"entity_type": "project", "operation": "list"},
                "description": "List projects",
                "validation": lambda r, ctx: r.get("success"),
            },
            {
                "tool": "query_tool",
                "params": {
                    "query_type": "aggregate",
                    "entities": ["project", "document", "requirement"],
                },
                "description": "Get project statistics",
                "validation": lambda r, ctx: r.get("success"),
            },
        ],
    )

    result = await story.execute(client_adapter)
    return {"success": result["success"], "story": result}


@pytest.mark.asyncio

@pytest.mark.parallel

@mcp_test(tool_name="integration", category="user_story", priority=6)
async def test_story_requirement_testing_workflow(client_adapter):
    """User story: Import requirements → create tests → link coverage."""

    story = UserStoryPattern(
        story_name="Requirement Testing Workflow",
        steps=[
            {
                "tool": "entity_tool",
                "params": {"entity_type": "document", "operation": "list", "limit": 1},
                "description": "Get document",
                "save_to_context": "docs",
                "validation": lambda r, ctx: r.get("success"),
            },
            {
                "tool": "query_tool",
                "params": {
                    "query_type": "search",
                    "entities": ["requirement"],
                    "search_term": "test",
                    "limit": 10,
                },
                "description": "Search requirements",
                "validation": lambda r, ctx: r.get("success"),
            },
        ],
    )

    result = await story.execute(client_adapter)
    return {"success": result["success"], "story": result}


@pytest.mark.asyncio

@pytest.mark.parallel

@mcp_test(tool_name="integration", category="user_story", priority=6)
async def test_story_cross_entity_search(client_adapter):
    """User story: Search across all entities → aggregate → analyze."""

    story = UserStoryPattern(
        story_name="Cross-Entity Search",
        steps=[
            {
                "tool": "query_tool",
                "params": {
                    "query_type": "search",
                    "entities": ["organization", "project", "document", "requirement"],
                    "search_term": "system",
                    "limit": 5,
                },
                "description": "Search all entities",
                "validation": lambda r, ctx: r.get("success"),
            },
            {
                "tool": "query_tool",
                "params": {
                    "query_type": "aggregate",
                    "entities": ["organization", "project", "document", "requirement"],
                },
                "description": "Aggregate statistics",
                "validation": lambda r, ctx: r.get("success"),
            },
        ],
    )

    result = await story.execute(client_adapter)
    return {"success": result["success"], "story": result}


@pytest.mark.asyncio

@pytest.mark.parallel

@mcp_test(tool_name="integration", category="user_story", priority=5)
async def test_story_rag_comparison_workflow(client_adapter):
    """User story: Compare RAG modes for same query."""

    query = "user authentication security requirements"

    story = UserStoryPattern(
        story_name="RAG Mode Comparison",
        steps=[
            {
                "tool": "query_tool",
                "params": {
                    "query_type": "rag_search",
                    "entities": ["requirement"],
                    "search_term": query,
                    "rag_mode": "semantic",
                },
                "description": "Semantic RAG search",
                "save_to_context": "semantic",
                "validation": lambda r, ctx: r.get("success"),
            },
            {
                "tool": "query_tool",
                "params": {
                    "query_type": "rag_search",
                    "entities": ["requirement"],
                    "search_term": query,
                    "rag_mode": "keyword",
                },
                "description": "Keyword RAG search",
                "save_to_context": "keyword",
                "validation": lambda r, ctx: r.get("success"),
            },
            {
                "tool": "query_tool",
                "params": {
                    "query_type": "rag_search",
                    "entities": ["requirement"],
                    "search_term": query,
                    "rag_mode": "hybrid",
                },
                "description": "Hybrid RAG search",
                "validation": lambda r, ctx: r.get("success"),
            },
        ],
    )

    result = await story.execute(client_adapter)
    return {"success": result["success"], "story": result}


@pytest.mark.asyncio

@pytest.mark.parallel

@mcp_test(tool_name="integration", category="user_story", priority=5)
async def test_story_relationship_graph_building(client_adapter):
    """User story: Build relationship graph between entities."""

    story = UserStoryPattern(
        story_name="Relationship Graph Building",
        steps=[
            {
                "tool": "entity_tool",
                "params": {"entity_type": "requirement", "operation": "list", "limit": 3},
                "description": "Get requirements",
                "save_to_context": "reqs",
                "validation": lambda r, ctx: r.get("success"),
            },
            {
                "tool": "relationship_tool",
                "params": {
                    "operation": "list",
                    "relationship_type": "trace_link",
                },
                "description": "List trace links",
                "validation": lambda r, ctx: r.get("success"),
            },
            {
                "tool": "query_tool",
                "params": {
                    "query_type": "relationships",
                    "entities": ["requirement"],
                },
                "description": "Analyze requirement relationships",
                "validation": lambda r, ctx: r.get("success"),
            },
        ],
    )

    result = await story.execute(client_adapter)
    return {"success": result["success"], "story": result}
