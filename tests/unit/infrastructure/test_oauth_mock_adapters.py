"""Tests for OAuth PKCE and DCR mock adapters.

FastMCP Pattern References:
- https://fastmcp.wiki/en/servers/auth/remote-oauth
- https://fastmcp.wiki/en/patterns/testing

Tests cover:
- OAuth PKCE (Proof Key for Code Exchange) per RFC 7231
- DCR (Dynamic Client Registration) per RFC 6749
- OpenID Connect (ID tokens with nonce)
- Pending authentication (AuthKit Standalone Connect pattern)
- Token exchange and validation
- Authorization code flow
- PKCE verification (SHA256)

All tests follow FastMCP Pytest patterns:
- @pytest.fixture for adapter setup
- @pytest.mark.parametrize for variant testing
- @pytest.mark.asyncio for async operations
- Zero external dependencies
"""

import pytest
import base64
import hashlib
import secrets
from infrastructure.mock_oauth_adapters import MockOAuthAuthAdapter, create_pkce_pair


class TestOAuthPKCEFlow:
    """Test OAuth 2.0 PKCE (Proof Key for Code Exchange) flow."""

    @pytest.mark.asyncio
    async def test_create_authorization_request(self):
        """Test creating an authorization request with PKCE."""
        adapter = MockOAuthAuthAdapter()
        code_verifier, code_challenge = create_pkce_pair()

        auth_code = adapter.create_authorization_request(
            client_id="test-client",
            redirect_uri="http://localhost:3000/callback",
            code_challenge=code_challenge,
            code_challenge_method="S256",
            state="state-123",
        )

        assert auth_code.startswith("auth_code_")
        assert len(auth_code) > 20

    @pytest.mark.asyncio
    async def test_pkce_code_exchange(self):
        """Test exchanging authorization code for tokens using PKCE."""
        adapter = MockOAuthAuthAdapter()
        code_verifier, code_challenge = create_pkce_pair()

        # Step 1: Create authorization request
        auth_code = adapter.create_authorization_request(
            client_id="test-client",
            redirect_uri="http://localhost:3000/callback",
            code_challenge=code_challenge,
            code_challenge_method="S256",
        )

        # Step 2: Exchange code for tokens
        tokens = await adapter.exchange_code_for_token(
            code=auth_code,
            client_id="test-client",
            redirect_uri="http://localhost:3000/callback",
            code_verifier=code_verifier,
        )

        assert "access_token" in tokens
        assert "id_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "Bearer"
        assert tokens["expires_in"] == 3600

    @pytest.mark.asyncio
    async def test_pkce_verification_fails_with_wrong_verifier(self):
        """Test that PKCE verification fails with incorrect code verifier."""
        adapter = MockOAuthAuthAdapter()
        code_verifier, code_challenge = create_pkce_pair()
        wrong_verifier = secrets.token_urlsafe(32)

        auth_code = adapter.create_authorization_request(
            client_id="test-client",
            redirect_uri="http://localhost:3000/callback",
            code_challenge=code_challenge,
        )

        with pytest.raises(ValueError, match="PKCE verification failed"):
            await adapter.exchange_code_for_token(
                code=auth_code,
                client_id="test-client",
                redirect_uri="http://localhost:3000/callback",
                code_verifier=wrong_verifier,
            )

    @pytest.mark.asyncio
    async def test_pkce_plain_method(self):
        """Test PKCE with plain (unencoded) method."""
        adapter = MockOAuthAuthAdapter()
        code_verifier = secrets.token_urlsafe(32)

        auth_code = adapter.create_authorization_request(
            client_id="test-client",
            redirect_uri="http://localhost:3000/callback",
            code_challenge=code_verifier,
            code_challenge_method="plain",
        )

        tokens = await adapter.exchange_code_for_token(
            code=auth_code,
            client_id="test-client",
            redirect_uri="http://localhost:3000/callback",
            code_verifier=code_verifier,
        )

        assert "access_token" in tokens

    @pytest.mark.asyncio
    async def test_authorization_code_expires(self):
        """Test that authorization codes expire."""
        adapter = MockOAuthAuthAdapter()
        code_verifier, code_challenge = create_pkce_pair()

        auth_code = adapter.create_authorization_request(
            client_id="test-client",
            redirect_uri="http://localhost:3000/callback",
            code_challenge=code_challenge,
        )

        # Manually expire the code
        if auth_code in adapter._auth_codes:
            adapter._auth_codes[auth_code]["expires_at"] = 0

        with pytest.raises(ValueError, match="expired"):
            await adapter.exchange_code_for_token(
                code=auth_code,
                client_id="test-client",
                redirect_uri="http://localhost:3000/callback",
                code_verifier=code_verifier,
            )

    @pytest.mark.asyncio
    async def test_client_id_mismatch_fails(self):
        """Test that mismatched client IDs fail verification."""
        adapter = MockOAuthAuthAdapter()
        code_verifier, code_challenge = create_pkce_pair()

        auth_code = adapter.create_authorization_request(
            client_id="client-1",
            redirect_uri="http://localhost:3000/callback",
            code_challenge=code_challenge,
        )

        with pytest.raises(ValueError, match="Client ID mismatch"):
            await adapter.exchange_code_for_token(
                code=auth_code,
                client_id="client-2",  # Wrong client ID
                redirect_uri="http://localhost:3000/callback",
                code_verifier=code_verifier,
            )

    @pytest.mark.asyncio
    async def test_redirect_uri_mismatch_fails(self):
        """Test that mismatched redirect URIs fail verification."""
        adapter = MockOAuthAuthAdapter()
        code_verifier, code_challenge = create_pkce_pair()

        auth_code = adapter.create_authorization_request(
            client_id="test-client",
            redirect_uri="http://localhost:3000/callback",
            code_challenge=code_challenge,
        )

        with pytest.raises(ValueError, match="Redirect URI mismatch"):
            await adapter.exchange_code_for_token(
                code=auth_code,
                client_id="test-client",
                redirect_uri="http://localhost:4000/callback",  # Wrong URI
                code_verifier=code_verifier,
            )

    @pytest.mark.asyncio
    async def test_openid_nonce_in_id_token(self):
        """Test that nonce is included in ID token."""
        adapter = MockOAuthAuthAdapter()
        code_verifier, code_challenge = create_pkce_pair()
        nonce = "nonce-123"

        auth_code = adapter.create_authorization_request(
            client_id="test-client",
            redirect_uri="http://localhost:3000/callback",
            code_challenge=code_challenge,
            nonce=nonce,
        )

        tokens = await adapter.exchange_code_for_token(
            code=auth_code,
            client_id="test-client",
            redirect_uri="http://localhost:3000/callback",
            code_verifier=code_verifier,
        )

        # Decode ID token to verify nonce
        id_token = tokens["id_token"]
        parts = id_token.split(".")
        # Decode payload (add padding if needed)
        payload = parts[1]
        payload += "=" * (4 - len(payload) % 4)
        import json
        payload_data = json.loads(base64.urlsafe_b64decode(payload))

        assert payload_data.get("nonce") == nonce


class TestPendingAuthentication:
    """Test pending authentication (like AuthKit Standalone Connect)."""

    @pytest.mark.asyncio
    async def test_create_pending_authentication(self):
        """Test creating a pending authentication token."""
        adapter = MockOAuthAuthAdapter()

        token = adapter.create_pending_authentication(
            user_id="user-123",
            email="user@example.com",
            redirect_uri="http://localhost:3000/callback",
        )

        assert token.startswith("pending_auth_")
        assert len(token) > 20

    @pytest.mark.asyncio
    async def test_complete_pending_authentication(self):
        """Test completing pending authentication."""
        adapter = MockOAuthAuthAdapter()

        pending_token = adapter.create_pending_authentication(
            user_id="user-123",
            email="user@example.com",
            redirect_uri="http://localhost:3000/callback",
        )

        session_token = await adapter.complete_pending_authentication(
            pending_authentication_token=pending_token,
            external_auth_id="authkit-ext-id",
            user_data={"id": "user-123", "email": "user@example.com"},
        )

        assert session_token.startswith("session_")

        # Verify the session works
        user = await adapter.validate_token(session_token)
        assert user["email"] == "user@example.com"

    @pytest.mark.asyncio
    async def test_pending_authentication_expires(self):
        """Test that pending authentication tokens expire."""
        adapter = MockOAuthAuthAdapter()

        pending_token = adapter.create_pending_authentication(
            user_id="user-123",
            email="user@example.com",
            redirect_uri="http://localhost:3000/callback",
        )

        # Manually expire it
        adapter._pending_auth_tokens[pending_token]["expires_at"] = 0

        with pytest.raises(ValueError, match="expired"):
            await adapter.complete_pending_authentication(
                pending_authentication_token=pending_token,
                external_auth_id="ext-id",
                user_data={"id": "user-123"},
            )

    @pytest.mark.asyncio
    async def test_invalid_pending_token_fails(self):
        """Test that invalid pending tokens fail."""
        adapter = MockOAuthAuthAdapter()

        with pytest.raises(ValueError, match="Invalid pending"):
            await adapter.complete_pending_authentication(
                pending_authentication_token="invalid-token",
                external_auth_id="ext-id",
                user_data={"id": "user-123"},
            )


class TestDynamicClientRegistration:
    """Test DCR (Dynamic Client Registration) flow."""

    def test_register_client(self):
        """Test registering a new OAuth client."""
        adapter = MockOAuthAuthAdapter()

        result = adapter.register_client(
            client_name="Test App",
            redirect_uris=["http://localhost:3000/callback"],
            client_type="web",
            logo_uri="https://example.com/logo.png",
        )

        assert "client_id" in result
        assert "client_secret" in result
        assert result["client_name"] == "Test App"
        assert result["redirect_uris"] == ["http://localhost:3000/callback"]

    def test_get_registered_client(self):
        """Test retrieving registered client info."""
        adapter = MockOAuthAuthAdapter()

        registered = adapter.register_client(
            client_name="Test App",
            redirect_uris=["http://localhost:3000/callback"],
        )

        client_id = registered["client_id"]
        retrieved = adapter.get_client(client_id)

        assert retrieved is not None
        assert retrieved["client_name"] == "Test App"
        assert retrieved["client_id"] == client_id

    def test_validate_redirect_uri(self):
        """Test validating redirect URIs."""
        adapter = MockOAuthAuthAdapter()

        registered = adapter.register_client(
            client_name="Test App",
            redirect_uris=[
                "http://localhost:3000/callback",
                "http://localhost:3000/auth/callback",
            ],
        )

        client_id = registered["client_id"]

        # Valid redirects
        assert adapter.validate_redirect_uri(client_id, "http://localhost:3000/callback")
        assert adapter.validate_redirect_uri(client_id, "http://localhost:3000/auth/callback")

        # Invalid redirect
        assert not adapter.validate_redirect_uri(client_id, "http://evil.com/callback")

    def test_register_multiple_clients(self):
        """Test registering multiple clients."""
        adapter = MockOAuthAuthAdapter()

        client1 = adapter.register_client(
            client_name="App 1",
            redirect_uris=["http://app1:3000/callback"],
        )

        client2 = adapter.register_client(
            client_name="App 2",
            redirect_uris=["http://app2:3000/callback"],
        )

        assert client1["client_id"] != client2["client_id"]
        assert client1["client_secret"] != client2["client_secret"]


class TestPKCEUtility:
    """Test PKCE utility functions."""

    def test_create_pkce_pair(self):
        """Test creating PKCE code verifier and challenge."""
        verifier, challenge = create_pkce_pair()

        # Verifier should be 43 characters (standard base64url)
        assert len(verifier) >= 40

        # Challenge should be a valid SHA256 hash
        assert len(challenge) >= 40

        # Verify the relationship
        expected_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode()).digest()
        ).decode().rstrip("=")

        assert challenge == expected_challenge

    def test_pkce_uniqueness(self):
        """Test that PKCE pairs are unique."""
        pairs = [create_pkce_pair() for _ in range(10)]
        verifiers = [v for v, _ in pairs]

        # All should be unique
        assert len(set(verifiers)) == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
