"""Tests for hybrid auth provider.

Tests OAuth + bearer token + JWT authentication flow.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from services.auth.hybrid_auth_provider import (
    HybridAuthProvider,
    create_hybrid_auth_provider
)


pytestmark = [pytest.mark.unit]


class TestHybridAuthProviderInitialization:
    """Hybrid auth provider initialization."""

    def test_initializes_with_oauth_provider(self):
        """Test initializing with OAuth provider only."""
        mock_oauth = MagicMock()
        mock_oauth.base_url = "https://oauth.example.com"
        mock_oauth.required_scopes = ["read:data"]
        mock_oauth.authkit_domain = "authkit.example.com"
        
        provider = HybridAuthProvider(oauth_provider=mock_oauth)
        
        assert provider.oauth_provider is mock_oauth
        assert provider.base_url == "https://oauth.example.com"
        assert provider.required_scopes == ["read:data"]
        assert provider.internal_token_verifier is None
        assert provider.authkit_jwt_verifier is None

    def test_initializes_with_internal_token(self):
        """Test initializing with internal bearer token."""
        mock_oauth = MagicMock()
        mock_oauth.base_url = "https://oauth.example.com"
        
        internal_token = "internal-secret-token"
        provider = HybridAuthProvider(
            oauth_provider=mock_oauth,
            internal_token=internal_token
        )
        
        assert provider.internal_token_verifier is not None

    def test_initializes_with_authkit_jwt_verifier(self):
        """Test initializing with AuthKit JWT configuration."""
        mock_oauth = MagicMock()
        mock_oauth.base_url = "https://oauth.example.com"
        
        provider = HybridAuthProvider(
            oauth_provider=mock_oauth,
            authkit_client_id="client-123",
            authkit_jwks_uri="https://authkit.example.com/.well-known/jwks.json"
        )
        
        assert provider.authkit_jwt_verifier is not None

    def test_exposes_oauth_provider_attributes(self):
        """Test that hybrid provider exposes OAuth provider attributes."""
        mock_oauth = MagicMock()
        mock_oauth.base_url = "https://oauth.example.com"
        mock_oauth.required_scopes = ["read:data", "write:data"]
        mock_oauth.authkit_domain = "authkit.example.com"
        mock_oauth.resource_server_url = "https://api.example.com"
        mock_oauth.authorization_servers = ["server-1"]
        
        provider = HybridAuthProvider(oauth_provider=mock_oauth)
        
        assert provider.base_url == mock_oauth.base_url
        assert provider.required_scopes == mock_oauth.required_scopes
        assert provider.authkit_domain == mock_oauth.authkit_domain
        assert provider.resource_server_url == mock_oauth.resource_server_url
        assert provider.authorization_servers == mock_oauth.authorization_servers


class TestHybridAuthProviderAuthentication:
    """Hybrid auth provider authentication flow."""

    @pytest.mark.asyncio
    async def test_authenticate_with_bearer_token_internal(self):
        """Test authentication with internal bearer token."""
        mock_oauth = MagicMock()
        mock_oauth.base_url = "https://oauth.example.com"
        
        mock_internal_verifier = AsyncMock()
        mock_internal_verifier.verify_token.return_value = {
            "client_id": "internal-service",
            "scopes": ["read:data"]
        }
        
        provider = HybridAuthProvider(oauth_provider=mock_oauth, internal_token="secret")
        provider.internal_token_verifier = mock_internal_verifier
        
        # Create mock request with bearer token
        mock_request = MagicMock()
        mock_request.headers = {"Authorization": "Bearer valid-internal-token"}
        
        result = await provider.authenticate(mock_request)
        
        assert result == {"client_id": "internal-service", "scopes": ["read:data"]}
        mock_internal_verifier.verify_token.assert_called_once()

    @pytest.mark.asyncio
    async def test_authenticate_with_bearer_token_authkit_jwt(self):
        """Test authentication with AuthKit JWT."""
        mock_oauth = MagicMock()
        mock_oauth.base_url = "https://oauth.example.com"
        
        mock_jwt_verifier = AsyncMock()
        mock_jwt_verifier.verify_token.return_value = {
            "sub": "user-123",
            "email": "user@example.com"
        }
        
        provider = HybridAuthProvider(
            oauth_provider=mock_oauth,
            authkit_client_id="client-123",
            authkit_jwks_uri="https://authkit.example.com/.well-known/jwks.json"
        )
        provider.authkit_jwt_verifier = mock_jwt_verifier
        
        # Create mock request with bearer token
        mock_request = MagicMock()
        mock_request.headers = {"Authorization": "Bearer jwt-token-123"}
        
        result = await provider.authenticate(mock_request)
        
        assert result == {"sub": "user-123", "email": "user@example.com"}

    @pytest.mark.asyncio
    async def test_authenticate_fallback_to_oauth(self):
        """Test fallback to OAuth when no bearer token."""
        mock_oauth = AsyncMock()
        mock_oauth.base_url = "https://oauth.example.com"
        mock_oauth.authenticate.return_value = {"user": "oauth-user"}
        
        provider = HybridAuthProvider(oauth_provider=mock_oauth)
        
        # Create mock request without bearer token
        mock_request = MagicMock()
        mock_request.headers = {}
        
        result = await provider.authenticate(mock_request)
        
        assert result == {"user": "oauth-user"}
        mock_oauth.authenticate.assert_called_once()

    @pytest.mark.asyncio
    async def test_authenticate_bearer_token_invalid_returns_none(self):
        """Test authentication returns None when bearer token invalid."""
        mock_oauth = MagicMock()
        
        mock_internal_verifier = AsyncMock()
        mock_internal_verifier.verify_token.side_effect = Exception("Invalid token")
        
        provider = HybridAuthProvider(oauth_provider=mock_oauth, internal_token="secret")
        provider.internal_token_verifier = mock_internal_verifier
        
        # Create mock request with invalid bearer token
        mock_request = MagicMock()
        mock_request.headers = {"Authorization": "Bearer invalid-token"}
        
        result = await provider.authenticate(mock_request)
        
        # Bearer token verification failed and no fallback to OAuth, should return None
        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_bearer_token_verification_returns_none(self):
        """Test authentication returns None when bearer token verification fails."""
        mock_oauth = MagicMock()
        
        mock_internal_verifier = AsyncMock()
        mock_internal_verifier.verify_token.side_effect = Exception("Token verification failed")
        
        provider = HybridAuthProvider(oauth_provider=mock_oauth, internal_token="secret")
        provider.internal_token_verifier = mock_internal_verifier
        
        # OAuth not available
        provider.oauth_provider = None
        
        # Create mock request
        mock_request = MagicMock()
        mock_request.headers = {"Authorization": "Bearer invalid-token"}
        
        result = await provider.authenticate(mock_request)
        
        # Should return None
        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_strips_bearer_prefix(self):
        """Test that Bearer prefix is stripped correctly."""
        mock_oauth = MagicMock()
        
        mock_internal_verifier = AsyncMock()
        mock_internal_verifier.verify_token.return_value = {"success": True}
        
        provider = HybridAuthProvider(oauth_provider=mock_oauth, internal_token="secret")
        provider.internal_token_verifier = mock_internal_verifier
        
        # Create mock request
        mock_request = MagicMock()
        mock_request.headers = {"Authorization": "Bearer   token-with-spaces  "}
        
        await provider.authenticate(mock_request)
        
        # Verify token was cleaned (spaces stripped)
        call_args = mock_internal_verifier.verify_token.call_args
        assert call_args[0][0] == "token-with-spaces"


class TestHybridAuthProviderOAuthDelegation:
    """Hybrid auth provider OAuth method delegation."""

    @pytest.mark.asyncio
    async def test_get_authorization_url_delegates_to_oauth(self):
        """Test get_authorization_url delegates to OAuth provider."""
        mock_oauth = AsyncMock()
        mock_oauth.get_authorization_url.return_value = "https://oauth.example.com/authorize"
        
        provider = HybridAuthProvider(oauth_provider=mock_oauth)
        
        mock_request = MagicMock()
        result = await provider.get_authorization_url(mock_request)
        
        assert result == "https://oauth.example.com/authorize"
        mock_oauth.get_authorization_url.assert_called_once_with(mock_request)

    @pytest.mark.asyncio
    async def test_handle_callback_delegates_to_oauth(self):
        """Test handle_callback delegates to OAuth provider."""
        mock_oauth = AsyncMock()
        mock_oauth.handle_callback.return_value = {"access_token": "token-123"}
        
        provider = HybridAuthProvider(oauth_provider=mock_oauth)
        
        mock_request = MagicMock()
        result = await provider.handle_callback(mock_request)
        
        assert result == {"access_token": "token-123"}
        mock_oauth.handle_callback.assert_called_once_with(mock_request)

    def test_get_routes_delegates_to_oauth(self):
        """Test get_routes delegates to OAuth provider."""
        mock_oauth = MagicMock()
        mock_oauth.get_routes.return_value = [
            {"path": "/authorize", "method": "GET"},
            {"path": "/callback", "method": "POST"}
        ]
        
        provider = HybridAuthProvider(oauth_provider=mock_oauth)
        
        result = provider.get_routes()
        
        assert len(result) == 2
        mock_oauth.get_routes.assert_called_once()

    def test_get_resource_metadata_url_delegates_to_oauth(self):
        """Test get_resource_metadata_url delegates to OAuth provider."""
        mock_oauth = MagicMock()
        mock_oauth.get_resource_metadata_url.return_value = "https://oauth.example.com/metadata"
        
        provider = HybridAuthProvider(oauth_provider=mock_oauth)
        
        result = provider.get_resource_metadata_url()
        
        assert result == "https://oauth.example.com/metadata"

    def test_get_middleware_delegates_to_oauth(self):
        """Test get_middleware delegates to OAuth provider."""
        mock_oauth = MagicMock()
        mock_oauth.get_middleware.return_value = [MagicMock()]
        
        provider = HybridAuthProvider(oauth_provider=mock_oauth)
        
        result = provider.get_middleware()
        
        assert len(result) == 1

    def test_get_middleware_returns_empty_if_not_available(self):
        """Test get_middleware returns empty list if not available on OAuth provider."""
        mock_oauth = MagicMock()
        # Remove get_middleware to simulate it not being available
        del mock_oauth.get_middleware
        
        provider = HybridAuthProvider(oauth_provider=mock_oauth)
        
        result = provider.get_middleware()
        
        assert result == []


class TestHybridAuthProviderProperties:
    """Hybrid auth provider properties."""

    def test_requires_browser_property(self):
        """Test requires_browser property."""
        mock_oauth = MagicMock()
        provider = HybridAuthProvider(oauth_provider=mock_oauth)
        
        # Should always be True (OAuth requires browser)
        assert provider.requires_browser is True

    def test_supports_bearer_tokens_with_internal_token(self):
        """Test supports_bearer_tokens when internal token configured."""
        mock_oauth = MagicMock()
        provider = HybridAuthProvider(oauth_provider=mock_oauth, internal_token="secret")
        
        assert provider.supports_bearer_tokens is True

    def test_supports_bearer_tokens_with_authkit_jwt(self):
        """Test supports_bearer_tokens when AuthKit JWT configured."""
        mock_oauth = MagicMock()
        provider = HybridAuthProvider(
            oauth_provider=mock_oauth,
            authkit_client_id="client-123",
            authkit_jwks_uri="https://authkit.example.com/.well-known/jwks.json"
        )
        
        assert provider.supports_bearer_tokens is True

    def test_supports_bearer_tokens_false_when_no_config(self):
        """Test supports_bearer_tokens is False when neither token nor JWT configured."""
        mock_oauth = MagicMock()
        provider = HybridAuthProvider(oauth_provider=mock_oauth)
        
        assert provider.supports_bearer_tokens is False


class TestHybridAuthProviderFactory:
    """Hybrid auth provider factory function."""

    def test_create_hybrid_auth_provider_factory(self):
        """Test creating hybrid auth provider via factory function."""
        with patch('services.auth.hybrid_auth_provider.AuthKitProvider') as mock_authkit_class:
            mock_oauth = MagicMock()
            mock_oauth.base_url = "https://oauth.example.com"
            mock_authkit_class.return_value = mock_oauth
            
            provider = create_hybrid_auth_provider(
                authkit_domain="authkit.example.com",
                base_url="https://api.example.com",
                internal_token="secret-token"
            )
            
            assert provider.oauth_provider is mock_oauth
            assert provider.internal_token_verifier is not None
            mock_authkit_class.assert_called_once_with(
                authkit_domain="authkit.example.com",
                base_url="https://api.example.com"
            )

    def test_create_hybrid_auth_provider_with_jwt_config(self):
        """Test creating hybrid auth provider with JWT configuration."""
        with patch('services.auth.hybrid_auth_provider.AuthKitProvider') as mock_authkit_class:
            mock_oauth = MagicMock()
            mock_oauth.base_url = "https://oauth.example.com"
            mock_authkit_class.return_value = mock_oauth
            
            provider = create_hybrid_auth_provider(
                authkit_domain="authkit.example.com",
                base_url="https://api.example.com",
                authkit_client_id="client-123",
                authkit_jwks_uri="https://authkit.example.com/.well-known/jwks.json"
            )
            
            assert provider.authkit_jwt_verifier is not None
