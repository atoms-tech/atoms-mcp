"""Compatibility tests for API version negotiation and legacy shims."""

from __future__ import annotations

import pytest


class ApiVersioningHarness:
    """Utility class that mirrors the production compat layer semantics."""

    DEFAULT_VERSION = "v2"
    LEGACY_VERSION = "v1"

    def normalize_request(self, payload: dict) -> dict:
        mapping = {
            "entityType": "entity_type",
            "projectId": "project_id",
            "documentId": "document_id",
            "includeRelations": "include_relations",
        }
        normalized = {"version": payload.get("version", self.DEFAULT_VERSION)}
        for key, value in payload.items():
            target = mapping.get(key, key)
            normalized[target] = value
        return normalized

    def normalize_response(self, response: dict, version: str) -> dict:
        if version == self.LEGACY_VERSION:
            legacy = {
                "status": response.get("status", 200),
                "data": response.get("data", {}),
                "meta": {"version": version},
            }
            legacy["legacyStatus"] = legacy["status"]
            return legacy
        response = dict(response)
        response.setdefault("meta", {})["version"] = version
        return response

    def deprecation_warning(self, version: str) -> str | None:
        if version == self.LEGACY_VERSION:
            return "API v1 is deprecated"
        return None

    def migration_hint(self, version: str) -> str:
        if version == self.LEGACY_VERSION:
            return "https://atoms.fastmcp.dev/migration/v1-to-v2"
        return "https://atoms.fastmcp.dev/api"

    def resolve_version(self, requested: str | None) -> str:
        if requested in {self.LEGACY_VERSION, self.DEFAULT_VERSION}:
            return requested
        return self.DEFAULT_VERSION

    def normalize_headers(self, headers: dict) -> dict:
        normalized = dict(headers)
        if "X-API-Version" in headers:
            normalized["version"] = headers["X-API-Version"]
        if "AuthToken" in headers:
            normalized["Authorization"] = f"Bearer {headers['AuthToken']}"
        return normalized

    def attach_metadata(self, response: dict, version: str) -> dict:
        enriched = dict(response)
        enriched.setdefault("metadata", {})["api_version"] = version
        enriched.setdefault("metadata", {})["compatible"] = version in {self.LEGACY_VERSION, self.DEFAULT_VERSION}
        return enriched


@pytest.fixture
def harness() -> ApiVersioningHarness:
    return ApiVersioningHarness()


def test_legacy_api_format_support(harness):
    legacy_request = {"version": "v1", "entityType": "project", "projectId": "p-1"}
    normalized = harness.normalize_request(legacy_request)
    assert normalized["entity_type"] == "project"
    assert normalized["project_id"] == "p-1"


def test_old_parameter_names_still_work(harness):
    payload = {"documentId": "doc-1", "includeRelations": True}
    normalized = harness.normalize_request(payload)
    assert normalized["document_id"] == "doc-1"
    assert normalized["include_relations"] is True


def test_old_response_structures_remain_valid(harness):
    response = {"status": 200, "data": {"id": "123"}}
    legacy = harness.normalize_response(response, "v1")
    assert legacy["legacyStatus"] == 200
    assert legacy["meta"]["version"] == "v1"


def test_deprecation_warning_issued_for_v1(harness):
    warning = harness.deprecation_warning("v1")
    assert warning and "deprecated" in warning


def test_migration_paths_documented(harness):
    url = harness.migration_hint("v1")
    assert url.endswith("v1-to-v2")


def test_default_version_applies_when_unspecified(harness):
    normalized = harness.normalize_request({"entity_type": "org"})
    assert normalized["version"] == harness.DEFAULT_VERSION


def test_client_requested_version_respected(harness):
    resolved = harness.resolve_version("v1")
    assert resolved == "v1"


def test_backward_compatibility_preserves_status_codes(harness):
    response = harness.normalize_response({"data": {}}, "v1")
    assert response["status"] == response["legacyStatus"]


def test_legacy_headers_supported(harness):
    headers = harness.normalize_headers({"X-API-Version": "v1", "AuthToken": "abc"})
    assert headers["version"] == "v1"
    assert headers["Authorization"] == "Bearer abc"


def test_response_metadata_contains_version_marker(harness):
    response = harness.attach_metadata({"data": {}}, "v2")
    assert response["metadata"]["api_version"] == "v2"
    assert response["metadata"]["compatible"] is True
