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

# Import Atoms-specific data fixtures
from .atoms_data import (
    bulk_test_data,
    cleanup_test_data,
    persistent_test_workspace,
    realistic_document_data,
    realistic_workspace_structure,
    sample_entity_data,
    sample_user_data,
    sample_workspace_data,
    test_data_factory,
)
from .auth import (
    auth_session_broker,
    authenticated_client,
    authenticated_credentials,
    github_client,
    google_client,
)
from .tools import (
    entity_client,
    query_client,
    relationship_client,
    tool_client_factory,
    workflow_client,
    workspace_client,
)

# OAuth providers are now in pheno-sdk/pheno/testing/mcp_qa/oauth/oauth_automation/providers/
# Import generic DataGenerator from mcp_qa
try:
    from pheno.testing.mcp_qa.core.data_generators import DataGenerator
except ImportError:
    DataGenerator = None

# Export all fixtures for easy importing
__all__ = [
    "DataGenerator",  # Generic data generator from mcp_qa
    "auth_session_broker",
    # Auth fixtures
    "authenticated_client",
    "authenticated_credentials",
    "bulk_test_data",
    "cleanup_test_data",
    "entity_client",
    "github_client",
    "google_client",
    "persistent_test_workspace",
    "query_client",
    "realistic_document_data",
    "realistic_workspace_structure",
    "relationship_client",
    "sample_entity_data",
    "sample_user_data",
    # Data fixtures (Atoms-specific)
    "sample_workspace_data",
    "test_data_factory",
    "tool_client_factory",
    "workflow_client",
    # Tool-specific fixtures
    "workspace_client",
]
