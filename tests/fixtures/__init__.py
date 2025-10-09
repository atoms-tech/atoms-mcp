"""Importable pytest fixtures for TDD-friendly testing.

This module provides all fixtures that can be imported into any test file:
- from tests.fixtures import authenticated_client
- from tests.fixtures import workspace_client, entity_client

Key features:
- Session-scoped OAuth (authenticate once, use everywhere)
- Direct HTTP tool calls (no MCP client overhead)
- Granular tool-specific clients
- Parallel test friendly
- Multi-provider support
"""

from .auth import (
    authenticated_client,
    authenticated_credentials,
    auth_session_broker,
    github_client,
    google_client,
)

from .tools import (
    workspace_client,
    entity_client, 
    relationship_client,
    workflow_client,
    query_client,
    tool_client_factory,
)

from .data import (
    sample_workspace_data,
    sample_entity_data,
    sample_user_data,
    test_data_factory,
    cleanup_test_data,
)

from .providers import (
    parametrized_provider,
    all_providers,
    authkit_provider,
    github_provider,
)

# Export all fixtures for easy importing
__all__ = [
    # Auth fixtures
    "authenticated_client",
    "authenticated_credentials", 
    "auth_session_broker",
    "github_client",
    "google_client",
    
    # Tool-specific fixtures
    "workspace_client",
    "entity_client",
    "relationship_client", 
    "workflow_client",
    "query_client",
    "tool_client_factory",
    
    # Data fixtures
    "sample_workspace_data",
    "sample_entity_data",
    "sample_user_data",
    "test_data_factory",
    "cleanup_test_data",
    
    # Provider fixtures
    "parametrized_provider",
    "all_providers",
    "authkit_provider",
    "github_provider",
]