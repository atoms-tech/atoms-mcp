"""
Unit tests for bearer token authentication from HTTP headers.

Tests the new functionality that allows frontend clients to pass
AuthKit JWT tokens via the Authorization header.
"""

from unittest.mock import Mock, patch

import pytest

from server.auth import BearerToken, extract_bearer_token


class TestBearerTokenExtraction:
    """Test bearer token extraction from various sources."""

    def test_extract_from_http_authorization_header(self):
        """Test extracting bearer token from HTTP Authorization header."""
        # Mock HTTP headers with Bearer token
        mock_headers = {"authorization": "Bearer test-jwt-token-12345"}

        with patch("server.auth.get_http_headers", return_value=mock_headers):
            with patch("server.auth.get_access_token", return_value=None):
                token = extract_bearer_token()

        assert token is not None
        assert isinstance(token, BearerToken)
        assert token.token == "test-jwt-token-12345"
        assert token.source == "http.authorization.bearer"
        assert token.claims is None

    def test_extract_from_http_authorization_header_with_whitespace(self):
        """Test extracting bearer token with extra whitespace."""
        mock_headers = {"authorization": "Bearer   test-jwt-token-12345   "}

        with patch("server.auth.get_http_headers", return_value=mock_headers):
            with patch("server.auth.get_access_token", return_value=None):
                token = extract_bearer_token()

        assert token is not None
        assert token.token == "test-jwt-token-12345"

    def test_extract_from_http_authorization_header_case_insensitive(self):
        """Test that authorization header is case-insensitive."""
        # HTTP headers are case-insensitive, but dict keys are not
        # FastMCP's get_http_headers() should normalize to lowercase
        mock_headers = {"authorization": "Bearer test-token"}

        with patch("server.auth.get_http_headers", return_value=mock_headers):
            with patch("server.auth.get_access_token", return_value=None):
                token = extract_bearer_token()

        assert token is not None
        assert token.token == "test-token"

    def test_no_bearer_prefix_returns_none(self):
        """Test that non-Bearer auth schemes are ignored."""
        mock_headers = {"authorization": "Basic dXNlcjpwYXNz"}

        with patch("server.auth.get_http_headers", return_value=mock_headers):
            with patch("server.auth.get_access_token", return_value=None):
                token = extract_bearer_token()

        # Should return None since it's not a Bearer token
        assert token is None

    def test_empty_bearer_token_returns_none(self):
        """Test that empty Bearer token is ignored."""
        mock_headers = {"authorization": "Bearer "}

        with patch("server.auth.get_http_headers", return_value=mock_headers):
            with patch("server.auth.get_access_token", return_value=None):
                token = extract_bearer_token()

        assert token is None

    def test_fallback_to_fastmcp_oauth(self):
        """Test fallback to FastMCP OAuth when no HTTP header present."""
        # Mock no HTTP headers
        mock_headers = {}

        # Mock FastMCP OAuth access token
        mock_access_token = Mock()
        mock_access_token.token = "oauth-token-12345"
        mock_access_token.claims = {"sub": "user_123", "email": "user@example.com"}

        with patch("server.auth.get_http_headers", return_value=mock_headers):
            with patch("server.auth.get_access_token", return_value=mock_access_token):
                token = extract_bearer_token()

        assert token is not None
        assert token.token == "oauth-token-12345"
        assert token.source == "authkit.token"
        assert token.claims == {"sub": "user_123", "email": "user@example.com"}

    def test_http_header_takes_priority_over_oauth(self):
        """Test that HTTP Authorization header takes priority over OAuth."""
        # Mock both HTTP header and OAuth token
        mock_headers = {"authorization": "Bearer http-header-token"}
        mock_access_token = Mock()
        mock_access_token.token = "oauth-token"

        with patch("server.auth.get_http_headers", return_value=mock_headers):
            with patch("server.auth.get_access_token", return_value=mock_access_token):
                token = extract_bearer_token()

        # HTTP header should take priority
        assert token is not None
        assert token.token == "http-header-token"
        assert token.source == "http.authorization.bearer"

    def test_http_headers_exception_fallback(self):
        """Test graceful fallback when get_http_headers() raises exception."""
        # Mock get_http_headers to raise exception (e.g., not in HTTP context)
        def raise_exception():
            raise RuntimeError("Not in HTTP context")

        # Mock OAuth token as fallback
        mock_access_token = Mock()
        mock_access_token.token = "oauth-fallback-token"
        mock_access_token.claims = None

        with patch("server.auth.get_http_headers", side_effect=raise_exception):
            with patch("server.auth.get_access_token", return_value=mock_access_token):
                token = extract_bearer_token()

        # Should fall back to OAuth token
        assert token is not None
        assert token.token == "oauth-fallback-token"
        assert token.source == "authkit.token"

    def test_claims_dict_fallback(self):
        """Test fallback to claims dict when token attribute not present."""
        mock_headers = {}

        # Mock access token with claims but no token attribute
        mock_access_token = Mock()
        mock_access_token.token = None
        mock_access_token.claims = {"access_token": "claims-token-12345"}

        with patch("server.auth.get_http_headers", return_value=mock_headers):
            with patch("server.auth.get_access_token", return_value=mock_access_token):
                token = extract_bearer_token()

        assert token is not None
        assert token.token == "claims-token-12345"
        assert token.source == "authkit.claims.access_token"

    def test_no_token_anywhere_returns_none(self):
        """Test that None is returned when no token is found anywhere."""
        mock_headers = {}

        with patch("server.auth.get_http_headers", return_value=mock_headers):
            with patch("server.auth.get_access_token", return_value=None):
                token = extract_bearer_token()

        assert token is None

    def test_bearer_token_masking(self):
        """Test that BearerToken masks the token in string representation."""
        token = BearerToken(
            token="very-long-secret-token-12345",
            source="test",
            claims=None
        )

        token_str = str(token)
        assert "very" in token_str
        assert "2345" in token_str
        assert "secret" not in token_str
        assert "..." in token_str

    def test_short_bearer_token_masking(self):
        """Test that short tokens are fully masked."""
        token = BearerToken(token="short", source="test", claims=None)
        assert str(token) == "***"


class TestBearerTokenIntegration:
    """Integration tests for bearer token authentication flow."""

    @pytest.mark.asyncio
    async def test_bearer_token_with_rate_limiting(self):
        """Test that bearer tokens work with rate limiting."""
        from server.auth import apply_rate_limit_if_configured

        mock_headers = {"authorization": "Bearer test-token"}

        with patch("server.auth.get_http_headers", return_value=mock_headers):
            with patch("server.auth.get_access_token", return_value=None):
                # Should extract token without rate limiter
                token = await apply_rate_limit_if_configured(rate_limiter=None)

        assert token is not None
        assert token.token == "test-token"

    def test_real_authkit_jwt_format(self):
        """Test with a realistic AuthKit JWT format."""
        # Example JWT format (not a real token)
        jwt_token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyXzEyMyIsImVtYWlsIjoidXNlckBleGFtcGxlLmNvbSIsImlhdCI6MTYxNjIzOTAyMn0.signature"

        mock_headers = {"authorization": f"Bearer {jwt_token}"}

        with patch("server.auth.get_http_headers", return_value=mock_headers):
            with patch("server.auth.get_access_token", return_value=None):
                token = extract_bearer_token()

        assert token is not None
        assert token.token == jwt_token
        assert token.source == "http.authorization.bearer"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

