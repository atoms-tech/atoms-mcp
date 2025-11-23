"""Tools Module: Consolidated, Agent-Optimized MCP Tools.

This module provides 5 consolidated, agent-optimized tools for the Atoms MCP
Server. Each tool is designed to be intuitive for AI agents while providing
comprehensive functionality for knowledge management operations.

Tools Provided:
    1. workspace_operation: Manage workspace context and organization
       - Set active workspace/project/team context
       - Get current context
       - List available workspaces
       - Create, update, delete workspaces

    2. entity_operation: CRUD operations on entities
       - Create new entities (documents, requirements, tasks)
       - Read entities by ID
       - Update entity properties
       - Delete entities
       - List entities with filters
       - Search entities by properties

    3. relationship_operation: Create and manage relationships
       - Create relationships between entities
       - Query relationships
       - Delete relationships
       - Support for multiple relationship types

    4. workflow_execute: Execute multi-step workflows
       - Execute predefined workflows
       - Support for multi-step operations
       - Transaction support
       - Error handling and rollback

    5. data_query: Search and query entities
       - Full-text search
       - Semantic search
       - Aggregation and analytics
       - Filtering and sorting

Design Principles:
    - Consolidated: 5 tools, not per-operation tools
    - Agent-Optimized: Designed for AI agent reasoning
    - Intuitive: Clear operation names and parameters
    - Comprehensive: Full functionality in each tool
    - Efficient: Markdown response serialization

Architecture:
    Each tool is implemented as an async function that:
    - Validates input parameters
    - Calls service layer for business logic
    - Handles errors gracefully
    - Returns structured responses
    - Supports agent reasoning and multi-turn conversations

Tool Response Format:
    All tools return a consistent response structure:
    {
        'success': bool,           # Whether operation succeeded
        'data': dict or list,      # Operation result data
        'error': str,              # Error message if failed
        'metadata': dict           # Additional metadata
    }

Example:
    Using tools in an agent:

    >>> from tools import entity_operation
    >>> result = await entity_operation(
    ...     operation='create',
    ...     entity_type='document',
    ...     properties={'title': 'My Document'}
    ... )
    >>> print(result)
    {'success': True, 'data': {'id': 'ent_123', 'title': 'My Document'}}

Note:
    - All tools are async and must be awaited
    - Tools are designed for agent interaction
    - Responses are serialized as Markdown
    - Tools support multi-turn conversations
    - Error handling is comprehensive

See Also:
    - workspace.py: workspace_operation implementation
    - entity.py: entity_operation implementation
    - relationship.py: relationship_operation implementation
    - workflow.py: workflow_execute implementation
    - query.py: data_query implementation
"""

# Import all tool operations with fallback for different environments
try:
    from .workspace import workspace_operation
    # Import entity directly from entity.py (not entity/ package)
    from tools.entity import entity_operation
    from .relationship import relationship_operation
    from .workflow import workflow_execute
    from .query import data_query
except ImportError:
    from tools.workspace import workspace_operation
    from tools.entity import entity_operation
    from tools.relationship import relationship_operation
    from tools.workflow import workflow_execute
    from tools.query import data_query

__all__ = [
    "workspace_operation",
    "entity_operation", 
    "relationship_operation",
    "workflow_execute",
    "data_query"
]