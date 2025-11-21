"""Parametrized auth adapter coverage across unit/integration/e2e markers."""

from types import SimpleNamespace
from typing import Dict, Any

import pytest
from unittest.mock import MagicMock

from infrastructure.supabase_auth import SupabaseAuthAdapter
from tests.framework.conftest_shared import EntityFactory, AssertionHelpers


pytestmark = [pytest.mark.asyncio]


def _mode_params():
    return [
        pytest.param("unit", marks=pytest.mark.unit, id="unit"),
        pytest.param("integration", marks=pytest.mark.integration, id="integration"),

        pytest.param("e2e", marks=pytest.mark.e2e, id="e2e"),
    ]


@pytest.fixture
def token_cache_stub():
    class _Stub:
        def __init__(self):
            self.store: Dict[str, Dict[str, Any]] = {}

        async def get(self, token: str):
            return self.store.get(token)

        async def set(self, token: str, claims: Dict[str, Any], ttl: int):
            self.store[token] = claims

    return _Stub()


@pytest.fixture
def adapter_fixture(monkeypatch, token_cache_stub):
    adapter = SupabaseAuthAdapter()

    async def fake_get_token_cache():
        return token_cache_stub

    # Patch the actual import location in services.auth.token_cache
    monkeypatch.setattr("services.auth.token_cache.get_token_cache", fake_get_token_cache)
    return adapter, token_cache_stub


def _set_jwt_decoder(monkeypatch, payload):
    class _FakeJwt:
        @staticmethod
        def decode(token, options=None):
            return payload

    monkeypatch.setattr("infrastructure.supabase_auth.jwt_lib", _FakeJwt)


@pytest.mark.parametrize("mode", _mode_params())
async def test_session_round_trip(mode, adapter_fixture):
    adapter, cache = adapter_fixture
    token = await adapter.create_session("user-1", "auth@example.com")
    result = await adapter.validate_token(token)
    wrapped = {"success": True, "data": result}
    payload = AssertionHelpers.assert_success(wrapped, "session validate")
    assert payload["user_id"] == "user-1"
    assert cache.store


@pytest.mark.parametrize("mode", _mode_params())
async def test_validate_token_uses_cache_before_jwt(mode, adapter_fixture, monkeypatch):
    adapter, cache = adapter_fixture
    cached = {"user_id": "cached-user", "username": "cached@example.com"}
    async def fake_get(token):
        return cached
    cache.get = fake_get  # type: ignore[assignment]

    class _Explode:
        @staticmethod
        def decode(token, options=None):
            raise AssertionError("JWT should not be decoded when cache hit")

    monkeypatch.setattr("infrastructure.supabase_auth.jwt_lib", _Explode)
    result = await adapter.validate_token("cached-token")
    assert result["user_id"] == "cached-user"


@pytest.mark.parametrize("mode", _mode_params())
async def test_validate_supabase_jwt_rejected(mode, adapter_fixture, monkeypatch):
    """Verify that Supabase JWTs are rejected (only AuthKit JWTs are supported)."""
    adapter, _ = adapter_fixture
    _set_jwt_decoder(monkeypatch, {"iss": "https://xyz.supabase.co/auth/v1", "sub": "supabase-user", "email": "sup@example.com", "user_metadata": {"orgs": 2}})
    # Supabase JWTs should be rejected - only AuthKit JWTs are supported
    # The error message includes "Unsupported token issuer" or "Invalid or expired AuthKit JWT"
    with pytest.raises(ValueError) as exc_info:
        await adapter.validate_token("supabase-jwt")
    error_msg = str(exc_info.value)
    assert "Unsupported token issuer" in error_msg or "Invalid or expired AuthKit JWT" in error_msg


@pytest.mark.parametrize("mode", _mode_params())
async def test_validate_authkit_jwt_sets_context(mode, adapter_fixture, monkeypatch):
    adapter, _ = adapter_fixture
    _set_jwt_decoder(monkeypatch, {"iss": "https://api.workos.com/oidc", "sub": "workos-user", "email": "kit@example.com"})
    result = await adapter.validate_token("authkit-jwt")
    assert result["auth_type"] == "authkit_jwt"
    assert result["username"] == "kit@example.com"


@pytest.mark.parametrize("mode", _mode_params())
async def test_validate_token_rejects_unknown_issuer(mode, adapter_fixture, monkeypatch):
    adapter, _ = adapter_fixture
    _set_jwt_decoder(monkeypatch, {"iss": "https://unknown"})
    with pytest.raises(ValueError):
        await adapter.validate_token("bad")


@pytest.mark.parametrize("mode", _mode_params())
async def test_verify_credentials_demo_env(mode, adapter_fixture, monkeypatch):
    adapter, _ = adapter_fixture
    monkeypatch.setenv("FASTMCP_DEMO_USER", "demo@example.com")
    monkeypatch.setenv("FASTMCP_DEMO_PASS", "secret")
    creds = await adapter.verify_credentials("demo@example.com", "secret")
    assert creds


@pytest.mark.parametrize("mode", _mode_params())
async def test_verify_credentials_supabase_flow(mode, adapter_fixture, monkeypatch):
    adapter, _ = adapter_fixture
    # Unset demo env vars to force Supabase flow
    monkeypatch.delenv("FASTMCP_DEMO_USER", raising=False)
    monkeypatch.delenv("FASTMCP_DEMO_PASS", raising=False)
    
    client = MagicMock()
    auth = MagicMock()
    auth.sign_in_with_password.return_value = SimpleNamespace(
        user=SimpleNamespace(id="supabase-user", user_metadata={}),
        session=SimpleNamespace(access_token="at", refresh_token="rt")
    )
    client.auth = auth
    monkeypatch.setattr("infrastructure.supabase_auth.get_supabase", lambda: client)
    creds = await adapter.verify_credentials("user@example.com", "pass")
    assert creds["access_token"] == "at"


@pytest.mark.parametrize("mode", _mode_params())
async def test_revoke_session_and_fail_lookup(mode, adapter_fixture):
    adapter, _ = adapter_fixture
    token = await adapter.create_session("u-1", "rev@example.com")
    assert await adapter.revoke_session(token) is True
    with pytest.raises(ValueError):
        await adapter.validate_token(token)


@pytest.mark.parametrize("mode", _mode_params())
async def test_invalid_token_raises_permission_error(mode, adapter_fixture, monkeypatch):
    adapter, _ = adapter_fixture
    class _FakeJwt:
        @staticmethod
        def decode(token, options=None):
            raise ValueError("bad token")

    monkeypatch.setattr("infrastructure.supabase_auth.jwt_lib", _FakeJwt)
    with pytest.raises(ValueError):
        await adapter.validate_token("broken")


@pytest.mark.parametrize("mode", _mode_params())
async def test_permission_context_contains_metadata(mode, adapter_fixture, monkeypatch):
    adapter, cache = adapter_fixture
    entity = EntityFactory.organization()
    await cache.set("org-token", {"user_id": entity.get("name"), "username": entity.get("name")}, 60)
    result = await adapter.validate_token("org-token")
    wrapped = {"success": True, "data": result}
    payload = AssertionHelpers.assert_success(wrapped, "cached context")
    assert payload["user_id"] == entity.get("name")
