"""Provider fixtures for multi-provider OAuth testing with pheno-sdk integration."""

import pytest
from typing import List, Dict, Any
from ..framework.auth_session import AuthenticatedHTTPClient

# Use pheno-sdk authkit-client (required)
from authkit_client import AuthKitClient, OAuthFlow, OAuthConfig, Session


@pytest.fixture(params=["authkit", "github", "google"])
def parametrized_provider(request) -> str:
    """Parametrized fixture that runs tests across multiple OAuth providers.
    
    Usage:
        def test_oauth_flow(parametrized_provider, auth_session_broker):
            client = await auth_session_broker.get_authenticated_credentials(parametrized_provider)
            # Test runs 3 times: once for each provider
    """
    return request.param


@pytest.fixture
def all_providers() -> List[str]:
    """List of all supported OAuth providers."""
    return ["authkit", "github", "google", "azure"]


@pytest.fixture
def authkit_provider() -> Dict[str, Any]:
    """AuthKit provider configuration."""
    return {
        "name": "authkit",
        "display_name": "WorkOS AuthKit",
        "supports_mfa": True,
        "flow_steps": ["email", "password", "allow"],
    }


@pytest.fixture  
def github_provider() -> Dict[str, Any]:
    """GitHub provider configuration."""
    return {
        "name": "github", 
        "display_name": "GitHub",
        "supports_mfa": True,
        "flow_steps": ["username", "password", "authorize"],
    }


@pytest.fixture
def google_provider() -> Dict[str, Any]:
    """Google provider configuration."""
    return {
        "name": "google",
        "display_name": "Google",
        "supports_mfa": True,
        "flow_steps": ["email", "password", "consent"],
    }


@pytest.fixture
def azure_provider() -> Dict[str, Any]:
    """Azure AD provider configuration."""
    return {
        "name": "azure",
        "display_name": "Azure AD",
        "supports_mfa": True,
        "flow_steps": ["email", "password", "consent"],
    }


# Provider-specific client fixtures using authkit-client
@pytest.fixture(scope="session")
def authkit_client():
    """AuthKit client using pheno-sdk authkit-client."""
    import os
    config = OAuthConfig(
        client_id=os.getenv("WORKOS_CLIENT_ID"),
        client_secret=os.getenv("WORKOS_CLIENT_SECRET"),
        redirect_uri=os.getenv("WORKOS_REDIRECT_URI", "http://localhost:8000/auth/callback"),
        scopes=["openid", "profile", "email"]
    )
    return AuthKitClient(config=config)


@pytest.fixture(scope="session")
def oauth_flow(authkit_client):
    """OAuth flow using pheno-sdk authkit-client."""
    return OAuthFlow(config=authkit_client.config)


@pytest.fixture(scope="session")
async def authkit_authenticated_client(auth_session_broker) -> AuthenticatedHTTPClient:
    """AuthKit-authenticated client."""
    from ..framework.auth_session import AuthenticatedHTTPClient
    credentials = await auth_session_broker.get_authenticated_credentials("authkit")
    return AuthenticatedHTTPClient(credentials)