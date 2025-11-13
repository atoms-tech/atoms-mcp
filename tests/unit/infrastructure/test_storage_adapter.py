"""Parametrized tests for Supabase storage adapter across 3 modes."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from unittest.mock import MagicMock

from infrastructure.supabase_storage import SupabaseStorageAdapter
from tests.framework.conftest_shared import EntityFactory, AssertionHelpers
from errors import ApiError


pytestmark = [pytest.mark.asyncio]


def _mode_params():
    return [
        pytest.param("unit", marks=pytest.mark.unit, id="unit"),
        pytest.param("integration", marks=pytest.mark.integration, id="integration"),
        pytest.param("e2e", marks=pytest.mark.e2e, id="e2e"),
    ]


@pytest.fixture
def adapter_fixture(monkeypatch):
    adapter = SupabaseStorageAdapter()
    client = MagicMock()
    storage = MagicMock()
    bucket = MagicMock()
    storage.from_.return_value = bucket
    client.storage = storage
    monkeypatch.setattr("infrastructure.supabase_storage.get_supabase", lambda: client)
    return adapter, bucket


@pytest.mark.parametrize("mode", _mode_params())
async def test_upload_sets_metadata_and_returns_url(mode, adapter_fixture, monkeypatch):
    adapter, bucket = adapter_fixture
    bucket.upload.return_value = SimpleNamespace(error=None)
    monkeypatch.setenv("NEXT_PUBLIC_SUPABASE_URL", "https://example.supabase.co")
    path = "test-document.txt"
    url = await adapter.upload("docs", path, b"data", content_type="text/plain", metadata={"x-upsert": "true"})
    wrapped = {"success": True, "data": {"url": url}}
    AssertionHelpers.assert_success(wrapped, "storage upload")
    bucket.upload.assert_called_once()
    assert url.endswith(f"docs/{path}")


@pytest.mark.parametrize("mode", _mode_params())
async def test_upload_raises_on_storage_error(mode, adapter_fixture):
    adapter, bucket = adapter_fixture
    bucket.upload.return_value = SimpleNamespace(error="failure")
    with pytest.raises(ApiError):
        await adapter.upload("docs", "bad.txt", b"", content_type="text/plain")


@pytest.mark.parametrize("mode", _mode_params())
async def test_download_returns_bytes(mode, adapter_fixture):
    adapter, bucket = adapter_fixture
    bucket.download.return_value = b"payload"
    data = await adapter.download("docs", "file.txt")
    assert data == b"payload"


@pytest.mark.parametrize("mode", _mode_params())
async def test_download_wraps_storage_error(mode, adapter_fixture):
    adapter, bucket = adapter_fixture
    bucket.download.return_value = SimpleNamespace(error="Missing")
    with pytest.raises(ApiError):
        await adapter.download("docs", "missing.txt")


@pytest.mark.parametrize("mode", _mode_params())
async def test_delete_success(mode, adapter_fixture):
    adapter, bucket = adapter_fixture
    bucket.remove.return_value = SimpleNamespace(error=None)
    assert await adapter.delete("docs", "file.txt") is True


@pytest.mark.parametrize("mode", _mode_params())
async def test_delete_handles_exception(mode, adapter_fixture):
    adapter, bucket = adapter_fixture
    bucket.remove.side_effect = RuntimeError("boom")
    assert await adapter.delete("docs", "file.txt") is False


@pytest.mark.parametrize("mode", _mode_params())
async def test_get_public_url_requires_env(mode, adapter_fixture, monkeypatch):
    adapter, _ = adapter_fixture
    monkeypatch.setenv("NEXT_PUBLIC_SUPABASE_URL", "https://example.supabase.co")
    url = adapter.get_public_url("docs", "file.txt")
    assert url == "https://example.supabase.co/storage/v1/object/public/docs/file.txt"


@pytest.mark.parametrize("mode", _mode_params())
async def test_get_public_url_missing_env(mode, adapter_fixture, monkeypatch):
    adapter, _ = adapter_fixture
    monkeypatch.delenv("NEXT_PUBLIC_SUPABASE_URL", raising=False)
    with pytest.raises(ApiError):
        adapter.get_public_url("docs", "file.txt")


@pytest.mark.parametrize("mode", _mode_params())
async def test_upload_size_limit_error_bubbles(mode, adapter_fixture):
    adapter, bucket = adapter_fixture
    bucket.upload.return_value = SimpleNamespace(error="Payload too large")
    with pytest.raises(ApiError):
        await adapter.upload("docs", "huge.bin", b"0" * 10_000_000, content_type="application/octet-stream")


@pytest.mark.parametrize("mode", _mode_params())
async def test_access_control_flags_pass_through(mode, adapter_fixture, monkeypatch):
    adapter, bucket = adapter_fixture
    bucket.upload.return_value = SimpleNamespace(error=None)
    monkeypatch.setenv("NEXT_PUBLIC_SUPABASE_URL", "https://example.supabase.co")
    await adapter.upload("private", "file.bin", b"bytes", metadata={"cache-control": "max-age=60"})
    options = bucket.upload.call_args.kwargs.get("file_options")
    assert options["cache-control"] == "max-age=60"
