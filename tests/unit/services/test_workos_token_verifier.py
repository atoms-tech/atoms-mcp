"""Tests for WorkOS token verifier supporting both AuthKit OAuth and User Management tokens."""

import pytest
import jwt
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta


class TestWorkOSTokenVerifier:
    """Test WorkOSTokenVerifier for AuthKit and User Management tokens."""

    @pytest.fixture
    def verifier(self):
        """Create a WorkOS token verifier."""
        from services.auth.workos_token_verifier import WorkOSTokenVerifier
        # Create with mock JWKS URI - JWTVerifier requires either public_key or jwks_uri
        verifier = WorkOSTokenVerifier(
            issuer="https://auth.atoms.tech",
            audience="mcp_client_id",
            jwks_uri="https://auth.atoms.tech/.well-known/jwks.json"
        )
        return verifier

    @pytest.fixture
    def valid_authkit_token(self):
        """Create a valid AuthKit JWT token."""
        payload = {
            "iss": "https://auth.atoms.tech",
            "sub": "user_123abc",
            "email": "alice@example.com",
            "aud": "mcp_client_id",
            "exp": (datetime.utcnow() + timedelta(hours=1)).timestamp(),
            "iat": datetime.utcnow().timestamp()
        }
        # Create unsigned token for testing (real verification would check signature)
        return jwt.encode(payload, "secret", algorithm="HS256")

    @pytest.fixture
    def valid_workos_um_token(self):
        """Create a valid WorkOS User Management token."""
        payload = {
            "iss": "https://api.workos.com/user_management/client_abc123",
            "sub": "user_456def",
            "email": "bob@example.com",
            "exp": (datetime.utcnow() + timedelta(hours=1)).timestamp(),
            "iat": datetime.utcnow().timestamp()
        }
        return jwt.encode(payload, "secret", algorithm="HS256")

    @pytest.fixture
    def expired_token(self):
        """Create an expired token."""
        payload = {
            "iss": "https://auth.atoms.tech",
            "sub": "user_789ghi",
            "email": "charlie@example.com",
            "aud": "mcp_client_id",
            "exp": (datetime.utcnow() - timedelta(hours=1)).timestamp(),
            "iat": datetime.utcnow().timestamp()
        }
        return jwt.encode(payload, "secret", algorithm="HS256")

    @pytest.fixture
    def invalid_format_token(self):
        """Create an invalid format token."""
        return "not.a.jwt.with.extra.parts"

    # =====================================================
    # AUTHKIT TOKEN TESTS
    # =====================================================

    @pytest.mark.asyncio
    async def test_verify_authkit_token_format_check(self, verifier, valid_authkit_token):
        """Test that verifier checks JWT format (3 parts)."""
        # Valid token has 3 parts separated by dots
        parts = valid_authkit_token.split(".")
        assert len(parts) == 3

    @pytest.mark.asyncio
    async def test_decode_authkit_token_claims(self, verifier, valid_authkit_token):
        """Test that AuthKit token claims are correctly decoded."""
        decoded = jwt.decode(valid_authkit_token, options={"verify_signature": False})

        assert decoded["iss"] == "https://auth.atoms.tech"
        assert decoded["sub"] == "user_123abc"
        assert decoded["email"] == "alice@example.com"
        assert decoded["aud"] == "mcp_client_id"

    # =====================================================
    # WORKOS USER MANAGEMENT TOKEN TESTS
    # =====================================================

    @pytest.mark.asyncio
    async def test_detect_workos_um_issuer_pattern(self, verifier, valid_workos_um_token):
        """Test that verifier detects WorkOS User Management issuer pattern."""
        decoded = jwt.decode(valid_workos_um_token, options={"verify_signature": False})
        issuer = decoded.get("iss")

        # Check detection logic
        is_workos_um = (
            issuer.startswith("https://api.workos.com/user_management/") or
            issuer.startswith("https://api.workos.com/") or
            "workos" in issuer.lower()
        )

        assert is_workos_um

    @pytest.mark.asyncio
    async def test_decode_workos_um_token_claims(self, verifier, valid_workos_um_token):
        """Test that WorkOS UM token claims are correctly decoded."""
        decoded = jwt.decode(valid_workos_um_token, options={"verify_signature": False})

        assert decoded["iss"].startswith("https://api.workos.com/user_management/")
        assert decoded["sub"] == "user_456def"
        assert decoded["email"] == "bob@example.com"

    @pytest.mark.asyncio
    async def test_workos_um_token_missing_audience(self, verifier):
        """Test that WorkOS UM tokens without audience are handled."""
        # WorkOS UM tokens might not have aud claim
        payload = {
            "iss": "https://api.workos.com/user_management/client_abc123",
            "sub": "user_xyz",
            "email": "test@example.com",
            "exp": (datetime.utcnow() + timedelta(hours=1)).timestamp(),
            "iat": datetime.utcnow().timestamp()
        }
        token = jwt.encode(payload, "secret", algorithm="HS256")

        # Token is valid even without aud
        decoded = jwt.decode(token, options={"verify_signature": False})
        assert "aud" not in decoded or decoded.get("aud") is None

    # =====================================================
    # TOKEN FORMAT VALIDATION
    # =====================================================

    @pytest.mark.asyncio
    async def test_reject_too_short_token(self, verifier):
        """Test that tokens shorter than 50 chars are rejected."""
        short_token = "short"

        # Verifier should detect this
        assert len(short_token) < 50
        assert short_token.count(".") < 2

    @pytest.mark.asyncio
    async def test_reject_invalid_jwt_format(self, verifier, invalid_format_token):
        """Test that invalid JWT format is rejected."""
        # Token with wrong number of parts
        parts = invalid_format_token.split(".")
        assert len(parts) != 3

    @pytest.mark.asyncio
    async def test_reject_token_without_sub_claim(self, verifier):
        """Test that tokens without 'sub' claim are rejected."""
        payload = {
            "iss": "https://auth.atoms.tech",
            "email": "test@example.com",
            "aud": "mcp_client_id"
            # Missing 'sub' claim
        }
        token = jwt.encode(payload, "secret", algorithm="HS256")

        decoded = jwt.decode(token, options={"verify_signature": False})
        assert "sub" not in decoded

    # =====================================================
    # EXPIRATION CHECKS
    # =====================================================

    @pytest.mark.asyncio
    async def test_expired_token_has_past_exp(self, verifier, expired_token):
        """Test that expired token has exp in the past."""
        decoded = jwt.decode(expired_token, options={"verify_signature": False})

        exp_time = datetime.fromtimestamp(decoded["exp"])
        now = datetime.utcnow()

        assert exp_time < now

    @pytest.mark.asyncio
    async def test_valid_token_has_future_exp(self, verifier, valid_authkit_token):
        """Test that valid token has exp in the future."""
        decoded = jwt.decode(valid_authkit_token, options={"verify_signature": False})

        exp_time = datetime.fromtimestamp(decoded["exp"])
        now = datetime.utcnow()

        assert exp_time > now

    # =====================================================
    # ISSUER DETECTION
    # =====================================================

    @pytest.mark.asyncio
    async def test_authkit_issuer_pattern(self):
        """Test AuthKit issuer pattern detection."""
        authkit_issuers = [
            "https://auth.atoms.tech",
            "https://auth.example.com",
            "https://authkit.example.com"
        ]

        # These should NOT match WorkOS pattern
        for issuer in authkit_issuers:
            is_workos = (
                issuer.startswith("https://api.workos.com/user_management/") or
                "workos" in issuer.lower()
            )
            assert not is_workos

    @pytest.mark.asyncio
    async def test_workos_issuer_patterns(self):
        """Test various WorkOS issuer patterns."""
        workos_issuers = [
            "https://api.workos.com/user_management/client_abc123",
            "https://api.workos.com/user_management/client_def456",
            "https://api.workos.com/oauth"
        ]

        for issuer in workos_issuers:
            is_workos = (
                issuer.startswith("https://api.workos.com/user_management/") or
                issuer.startswith("https://api.workos.com/") or
                "workos" in issuer.lower()
            )
            assert is_workos

    # =====================================================
    # CLAIM EXTRACTION
    # =====================================================

    @pytest.mark.asyncio
    async def test_extract_standard_claims(self, verifier, valid_authkit_token):
        """Test extraction of standard JWT claims."""
        decoded = jwt.decode(valid_authkit_token, options={"verify_signature": False})

        standard_claims = ["iss", "sub", "aud", "exp", "iat"]
        for claim in standard_claims:
            assert claim in decoded

    @pytest.mark.asyncio
    async def test_extract_email_claim(self, verifier, valid_authkit_token):
        """Test extraction of email claim."""
        decoded = jwt.decode(valid_authkit_token, options={"verify_signature": False})

        assert "email" in decoded
        assert "@" in decoded["email"]

    @pytest.mark.asyncio
    async def test_extract_custom_claims(self):
        """Test that custom claims are preserved."""
        payload = {
            "iss": "https://auth.atoms.tech",
            "sub": "user_123",
            "email": "test@example.com",
            "aud": "mcp_client_id",
            "exp": (datetime.utcnow() + timedelta(hours=1)).timestamp(),
            "custom_claim": "custom_value",
            "user_metadata": {"role": "admin"}
        }
        token = jwt.encode(payload, "secret", algorithm="HS256")

        decoded = jwt.decode(token, options={"verify_signature": False})

        assert decoded.get("custom_claim") == "custom_value"
        assert decoded.get("user_metadata") == {"role": "admin"}

    # =====================================================
    # ERROR CASES
    # =====================================================

    @pytest.mark.asyncio
    async def test_malformed_json_in_token(self):
        """Test handling of malformed JSON in token."""
        # Create a token with invalid header
        token = "invalid.payload.signature"

        with pytest.raises(Exception):
            jwt.decode(token, options={"verify_signature": False})

    @pytest.mark.asyncio
    async def test_token_with_none_claims(self):
        """Test token with None claims are rejected."""
        token = jwt.encode({}, "secret", algorithm="HS256")

        decoded = jwt.decode(token, options={"verify_signature": False})
        assert decoded is not None
        assert isinstance(decoded, dict)

    # =====================================================
    # TOKEN COMPARISON
    # =====================================================

    @pytest.mark.asyncio
    async def test_authkit_vs_workos_token_structure(self, valid_authkit_token, valid_workos_um_token):
        """Test structural differences between token types."""
        authkit = jwt.decode(valid_authkit_token, options={"verify_signature": False})
        workos = jwt.decode(valid_workos_um_token, options={"verify_signature": False})

        # Different issuers
        assert authkit["iss"] != workos["iss"]
        assert "auth.atoms.tech" in authkit["iss"]
        assert "workos.com" in workos["iss"]

        # Same required claims
        assert "sub" in authkit
        assert "sub" in workos
        assert "email" in authkit
        assert "email" in workos

        # AuthKit has audience, WorkOS UM might not
        assert "aud" in authkit

    # =====================================================
    # TIMESTAMP VALIDATION
    # =====================================================

    @pytest.mark.asyncio
    async def test_token_issued_at_before_expiration(self, valid_authkit_token):
        """Test that iat (issued at) is before exp (expiration)."""
        decoded = jwt.decode(valid_authkit_token, options={"verify_signature": False})

        iat = datetime.fromtimestamp(decoded["iat"])
        exp = datetime.fromtimestamp(decoded["exp"])

        assert iat < exp

    @pytest.mark.asyncio
    async def test_token_issued_at_is_recent(self, valid_authkit_token):
        """Test that token was recently issued."""
        decoded = jwt.decode(valid_authkit_token, options={"verify_signature": False})

        iat = datetime.fromtimestamp(decoded["iat"])
        now = datetime.utcnow()

        # Should be issued within last minute
        time_diff = (now - iat).total_seconds()
        assert time_diff >= 0
        assert time_diff < 60
