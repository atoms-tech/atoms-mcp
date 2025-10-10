"""
Fast Workflow Tool Tests using FastHTTPClient

These tests use direct HTTP calls instead of the MCP decorator framework,
providing ~20x speed improvement while still validating real workflow operations,
Supabase data integrity, RLS policies, and business logic.

Converted from: tests/test_workflow_comprehensive.py

Run with: pytest tests/unit/test_workflow_fast.py -v
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime
from typing import Any

import pytest

# ============================================================================
# Helper Functions
# ============================================================================


def generate_uuid() -> str:
    """Generate a random UUID string."""
    return str(uuid.uuid4())


def generate_requirements(count: int, **kwargs) -> list[dict[str, Any]]:
    """Generate a list of requirement data.

    Args:
        count: Number of requirements to generate
        **kwargs: Override default values

    Returns:
        List of requirement dictionaries
    """
    requirements = []
    for i in range(count):
        uid = uuid.uuid4().hex[:8]
        req = {
            "name": kwargs.get("name", f"Requirement {uid}"),
            "block_id": kwargs.get("block_id", f"block_{uid}"),
            "description": kwargs.get("description", f"Generated requirement {i+1}"),
            "priority": kwargs.get("priority", ["high", "medium", "low"][i % 3]),
            "status": kwargs.get("status", "active"),
            "external_id": kwargs.get("external_id", f"EXT-{uid}"),
        }
        requirements.append(req)
    return requirements


def generate_document_names(count: int) -> list[str]:
    """Generate a list of document names.

    Args:
        count: Number of document names to generate

    Returns:
        List of document names
    """
    templates = [
        "Requirements Specification",
        "Technical Design",
        "User Manual",
        "Test Plan",
        "API Documentation",
        "Architecture Overview",
        "Security Guidelines",
        "Deployment Guide"
    ]

    if count <= len(templates):
        return templates[:count]

    # Generate additional names if needed
    names = templates.copy()
    for i in range(count - len(templates)):
        names.append(f"Document {uuid.uuid4().hex[:8]}")

    return names


# ============================================================================
# Setup Project Workflow Tests
# ============================================================================


@pytest.mark.asyncio
async def test_setup_project_minimal_params(authenticated_client):
    """Test setup_project with minimal required parameters."""
    # First create an organization
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    org_result = await authenticated_client.call_tool(
        "entity_tool",
        {
            "operation": "create",
            "entity_type": "organization",
            "data": {
                "name": f"Test Org {timestamp}",
                "slug": f"test-org-{timestamp}"
            }
        }
    )

    if not org_result.get("success"):
        pytest.skip(f"Cannot create organization: {org_result.get('error')}")

    org_id = org_result["data"]["id"]

    # Execute workflow with minimal params
    start_time = time.time()
    result = await authenticated_client.call_tool(
        "workflow_tool",
        {
            "workflow": "setup_project",
            "parameters": {
                "name": "Minimal Test Project",
                "organization_id": org_id
            }
        }
    )
    duration_ms = (time.time() - start_time) * 1000

    # Assertions
    assert result.get("success") is not False, \
        f"Workflow failed: {result.get('error')}"
    assert result.get("project_id") or (result.get("data", {}).get("project_id") if isinstance(result.get("data"), dict) else None), \
        f"No project_id in response, got keys: {list(result.get('response', {}).keys())}"
    assert result.get("steps_completed", 0) >= 2, \
        f"Should complete at least 2 steps, got {result.get('response', {}).get('steps_completed')}"
    assert duration_ms < 5000, \
        f"Workflow took {duration_ms:.0f}ms, should be < 5000ms with FastHTTPClient"


@pytest.mark.asyncio
async def test_setup_project_with_description(authenticated_client):
    """Test setup_project with description parameter."""
    # Create organization
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    org_result = await authenticated_client.call_tool(
        "entity_tool",
        {
            "operation": "create",
            "entity_type": "organization",
            "data": {
                "name": f"Test Org {timestamp}",
                "slug": f"test-org-{timestamp}"
            }
        }
    )

    if not org_result.get("success"):
        pytest.skip(f"Cannot create organization: {org_result.get('error')}")

    org_id = org_result["data"]["id"]

    # Execute workflow with description
    description = "This is a comprehensive project description for testing purposes."
    result = await authenticated_client.call_tool(
        "workflow_tool",
        {
            "workflow": "setup_project",
            "parameters": {
                "name": "Described Project",
                "organization_id": org_id,
                "description": description
            }
        }
    )

    assert result.get("success") is not False, \
        f"Workflow failed: {result.get('error')}"
    assert result.get("project_id") or (result.get("data", {}).get("project_id") if isinstance(result.get("data"), dict) else None), \
        "No project_id in response"

    # Verify description was set
    project_id = result.get("project_id") or result.get("data", {}).get("id")
    project_result = await authenticated_client.call_tool(
        "entity_tool",
        {
            "operation": "read",
            "entity_type": "project",
            "entity_id": project_id
        }
    )

    assert project_result["data"]["description"] == description, \
        f"Description mismatch: expected '{description}', got '{project_result['response']['data']['description']}'"


@pytest.mark.asyncio
async def test_setup_project_add_creator_as_admin_true(authenticated_client):
    """Test setup_project with add_creator_as_admin=True."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    org_result = await authenticated_client.call_tool(
        "entity_tool",
        {
            "operation": "create",
            "entity_type": "organization",
            "data": {
                "name": f"Test Org {timestamp}",
                "slug": f"test-org-{timestamp}"
            }
        }
    )

    if not org_result.get("success"):
        pytest.skip(f"Cannot create organization: {org_result.get('error')}")

    org_id = org_result["data"]["id"]

    result = await authenticated_client.call_tool(
        "workflow_tool",
        {
            "workflow": "setup_project",
            "parameters": {
                "name": "Admin Project",
                "organization_id": org_id,
                "add_creator_as_admin": True
            }
        }
    )

    assert result.get("success") is not False, \
        f"Workflow failed: {result.get('error')}"

    # Check that add_creator_member step was executed
    results = result.get("results", [])
    assert any(
        step.get("step") == "add_creator_member" and step.get("status") == "success"
        for step in results
    ), f"Creator should be added as admin. Steps executed: {[s.get('step') for s in results]}"


@pytest.mark.asyncio
async def test_setup_project_with_initial_documents(authenticated_client):
    """Test setup_project with 3 initial documents."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    org_result = await authenticated_client.call_tool(
        "entity_tool",
        {
            "operation": "create",
            "entity_type": "organization",
            "data": {
                "name": f"Test Org {timestamp}",
                "slug": f"test-org-{timestamp}"
            }
        }
    )

    if not org_result.get("success"):
        pytest.skip(f"Cannot create organization: {org_result.get('error')}")

    org_id = org_result["data"]["id"]

    doc_names = generate_document_names(3)
    result = await authenticated_client.call_tool(
        "workflow_tool",
        {
            "workflow": "setup_project",
            "parameters": {
                "name": "Project with 3 Docs",
                "organization_id": org_id,
                "initial_documents": doc_names
            }
        }
    )

    assert result.get("success") is not False, \
        f"Workflow failed: {result.get('error')}"

    # Check that documents were created
    results = result.get("results", [])
    doc_steps = [
        step for step in results
        if step.get("step", "").startswith("create_document_")
    ]
    assert len(doc_steps) == 3, \
        f"Should create 3 documents, found {len(doc_steps)} document creation steps"


@pytest.mark.asyncio
async def test_setup_project_invalid_organization_id(authenticated_client):
    """Test setup_project with invalid organization ID."""
    # Use a properly formatted UUID that doesn't exist
    invalid_org_id = str(uuid.uuid4())

    result = await authenticated_client.call_tool(
        "workflow_tool",
        {
            "workflow": "setup_project",
            "parameters": {
                "name": "Invalid Org Project",
                "organization_id": invalid_org_id
            }
        }
    )

    assert result.get("success") is False, \
        "Should fail with invalid org ID, but got success"
    assert "error" in result, \
        f"Expected 'error' in result, got keys: {list(result.keys())}"


# ============================================================================
# Import Requirements Workflow Tests
# ============================================================================


async def setup_document(authenticated_client) -> tuple[str, str, str]:
    """Create organization, project and document for testing.

    Returns:
        Tuple of (organization_id, project_id, document_id)
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create organization
    org_result = await authenticated_client.call_tool(
        "entity_tool",
        {
            "operation": "create",
            "entity_type": "organization",
            "data": {
                "name": f"Test Org {timestamp}",
                "slug": f"test-org-{timestamp}"
            }
        }
    )

    if not org_result.get("success"):
        pytest.skip(f"Cannot create organization: {org_result.get('error')}")

    org_id = org_result["data"]["id"]

    # Create project
    project_result = await authenticated_client.call_tool(
        "entity_tool",
        {
            "operation": "create",
            "entity_type": "project",
            "data": {
                "name": f"Test Project {timestamp}",
                "organization_id": org_id
            }
        }
    )

    if not project_result.get("success"):
        pytest.skip(f"Cannot create project: {project_result.get('error')}")

    project_id = project_result["data"]["id"]

    # Create document
    doc_result = await authenticated_client.call_tool(
        "entity_tool",
        {
            "operation": "create",
            "entity_type": "document",
            "data": {
                "name": f"Test Document {timestamp}",
                "project_id": project_id
            }
        }
    )

    if not doc_result.get("success"):
        pytest.skip(f"Cannot create document: {doc_result.get('error')}")

    doc_id = doc_result["data"]["id"]

    return org_id, project_id, doc_id


@pytest.mark.asyncio
async def test_import_requirements_small_batch(authenticated_client):
    """Test import_requirements with 3 requirements."""
    _, _, doc_id = await setup_document(authenticated_client)

    requirements = generate_requirements(3)

    start_time = time.time()
    result = await authenticated_client.call_tool(
        "workflow_tool",
        {
            "workflow": "import_requirements",
            "parameters": {
                "document_id": doc_id,
                "requirements": requirements
            }
        }
    )
    duration_ms = (time.time() - start_time) * 1000

    assert result.get("success") is not False, \
        f"Workflow failed: {result.get('error')}"
    assert result.get("imported_count") == 3, \
        f"Expected 3 imported, got {result.get('response', {}).get('imported_count')}"
    assert result.get("failed_count", 0) == 0, \
        f"Expected 0 failures, got {result.get('response', {}).get('failed_count')}"
    assert duration_ms < 5000, \
        f"Import took {duration_ms:.0f}ms, should be < 5000ms with FastHTTPClient"


@pytest.mark.asyncio
async def test_import_requirements_with_full_metadata(authenticated_client):
    """Test import_requirements with complete metadata."""
    _, _, doc_id = await setup_document(authenticated_client)

    requirements = [
        {
            "name": "Full Metadata Req 1",
            "block_id": "block_full_1",
            "description": "Complete requirement with all metadata",
            "status": "active",
            "priority": "high",
            "external_id": "EXT-001",
            "tags": ["critical", "security"],
            "version": "1.0.0"
        },
        {
            "name": "Full Metadata Req 2",
            "block_id": "block_full_2",
            "description": "Another complete requirement",
            "status": "approved",
            "priority": "medium",
            "external_id": "EXT-002",
            "tags": ["performance"],
            "version": "1.0.0"
        }
    ]

    result = await authenticated_client.call_tool(
        "workflow_tool",
        {
            "workflow": "import_requirements",
            "parameters": {
                "document_id": doc_id,
                "requirements": requirements
            }
        }
    )

    assert result.get("success") is not False, \
        f"Workflow failed: {result.get('error')}"
    assert result.get("imported_count") == 2, \
        f"Expected 2 imported, got {result.get('response', {}).get('imported_count')}"

    # Verify metadata was preserved
    results = result.get("results", [])
    for step in results:
        if step.get("status") == "success" and "result" in step:
            req = step["result"]
            assert req.get("status") in ["active", "approved"], \
                f"Invalid status: {req.get('status')}"
            assert req.get("priority") in ["high", "medium"], \
                f"Invalid priority: {req.get('priority')}"


@pytest.mark.asyncio
async def test_import_requirements_invalid_document_id(authenticated_client):
    """Test import_requirements with invalid document ID."""
    requirements = generate_requirements(3)
    # Use a properly formatted UUID that doesn't exist
    invalid_doc_id = str(uuid.uuid4())

    result = await authenticated_client.call_tool(
        "workflow_tool",
        {
            "workflow": "import_requirements",
            "parameters": {
                "document_id": invalid_doc_id,
                "requirements": requirements
            }
        }
    )

    assert result.get("success") is False, \
        "Should fail with invalid document ID, but got success"
    assert "error" in result, \
        f"Expected 'error' in result, got keys: {list(result.keys())}"


@pytest.mark.asyncio
async def test_import_requirements_empty_list(authenticated_client):
    """Test import_requirements with empty requirements list."""
    _, _, doc_id = await setup_document(authenticated_client)

    result = await authenticated_client.call_tool(
        "workflow_tool",
        {
            "workflow": "import_requirements",
            "parameters": {
                "document_id": doc_id,
                "requirements": []
            }
        }
    )

    assert result.get("success") is False, \
        "Should fail with empty requirements list, but got success"
    error = result.get("error", "").lower()
    assert "empty" in error or "non-empty" in error, \
        f"Expected 'empty' error message, got: {result.get('error')}"


# ============================================================================
# Setup Test Matrix Workflow Tests
# ============================================================================


async def setup_project_with_requirements(
    authenticated_client, requirement_count: int = 5
) -> tuple[str, str, list[str]]:
    """Create project with requirements for testing.

    Returns:
        Tuple of (project_id, document_id, requirement_ids)
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create organization
    org_result = await authenticated_client.call_tool(
        "entity_tool",
        {
            "operation": "create",
            "entity_type": "organization",
            "data": {
                "name": f"Test Org {timestamp}",
                "slug": f"test-org-{timestamp}"
            }
        }
    )

    if not org_result.get("success"):
        pytest.skip(f"Cannot create organization: {org_result.get('error')}")

    org_id = org_result["data"]["id"]

    # Create project
    project_result = await authenticated_client.call_tool(
        "entity_tool",
        {
            "operation": "create",
            "entity_type": "project",
            "data": {
                "name": f"Test Project {timestamp}",
                "organization_id": org_id
            }
        }
    )

    if not project_result.get("success"):
        pytest.skip(f"Cannot create project: {project_result.get('error')}")

    project_id = project_result["data"]["id"]

    # Create document
    doc_result = await authenticated_client.call_tool(
        "entity_tool",
        {
            "operation": "create",
            "entity_type": "document",
            "data": {
                "name": f"Test Document {timestamp}",
                "project_id": project_id
            }
        }
    )

    if not doc_result.get("success"):
        pytest.skip(f"Cannot create document: {doc_result.get('error')}")

    doc_id = doc_result["data"]["id"]

    # Create requirements
    req_ids = []
    for i in range(requirement_count):
        req_data = {
            "name": f"Requirement {i+1}",
            "document_id": doc_id,
            "block_id": f"block_{i}",
            "priority": ["high", "medium", "low"][i % 3]
        }
        req_result = await authenticated_client.call_tool(
            "entity_tool",
            {"operation": "create", "entity_type": "requirement", "data": req_data}
        )

        if req_result.get("success"):
            req_ids.append(req_result["data"]["id"])

    return project_id, doc_id, req_ids


@pytest.mark.asyncio
async def test_setup_test_matrix_default_name(authenticated_client):
    """Test setup_test_matrix with default matrix name."""
    project_id, _, _ = await setup_project_with_requirements(authenticated_client, 5)

    result = await authenticated_client.call_tool(
        "workflow_tool",
        {
            "workflow": "setup_test_matrix",
            "parameters": {
                "project_id": project_id
                # matrix_name not provided, should use default
            }
        }
    )

    assert result.get("success") is not False, \
        f"Workflow failed: {result.get('error')}"
    assert result.get("matrix_view_id"), \
        "No matrix_view_id in response"
    assert result.get("requirements_found") == 5, \
        f"Expected 5 requirements, found {result.get('response', {}).get('requirements_found')}"


@pytest.mark.asyncio
async def test_setup_test_matrix_custom_name(authenticated_client):
    """Test setup_test_matrix with custom matrix name."""
    project_id, _, _ = await setup_project_with_requirements(authenticated_client, 3)

    result = await authenticated_client.call_tool(
        "workflow_tool",
        {
            "workflow": "setup_test_matrix",
            "parameters": {
                "project_id": project_id,
                "matrix_name": "Custom Test Coverage Matrix"
            }
        }
    )

    assert result.get("success") is not False, \
        f"Workflow failed: {result.get('error')}"
    assert result.get("matrix_view_id"), \
        "No matrix_view_id in response"

    # Verify matrix name
    results = result.get("results", [])
    for step in results:
        if step.get("step") == "create_matrix_view" and "result" in step:
            assert step["result"].get("name") == "Custom Test Coverage Matrix", \
                f"Matrix name mismatch: {step['result'].get('name')}"
            break


@pytest.mark.asyncio
async def test_setup_test_matrix_empty_project(authenticated_client):
    """Test setup_test_matrix with empty project (no requirements)."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create organization
    org_result = await authenticated_client.call_tool(
        "entity_tool",
        {
            "operation": "create",
            "entity_type": "organization",
            "data": {
                "name": f"Test Org {timestamp}",
                "slug": f"test-org-{timestamp}"
            }
        }
    )

    if not org_result.get("success"):
        pytest.skip(f"Cannot create organization: {org_result.get('error')}")

    org_id = org_result["data"]["id"]

    # Create project without requirements
    project_result = await authenticated_client.call_tool(
        "entity_tool",
        {
            "operation": "create",
            "entity_type": "project",
            "data": {
                "name": f"Empty Project {timestamp}",
                "organization_id": org_id
            }
        }
    )

    if not project_result.get("success"):
        pytest.skip(f"Cannot create project: {project_result.get('error')}")

    project_id = project_result["data"]["id"]

    result = await authenticated_client.call_tool(
        "workflow_tool",
        {
            "workflow": "setup_test_matrix",
            "parameters": {
                "project_id": project_id
            }
        }
    )

    assert result.get("success") is not False, \
        f"Workflow failed: {result.get('error')}"
    assert result.get("requirements_found") == 0, \
        f"Expected 0 requirements, found {result.get('response', {}).get('requirements_found')}"
    assert result.get("test_cases_created", 0) == 0, \
        f"Expected 0 test cases, created {result.get('response', {}).get('test_cases_created')}"


# ============================================================================
# Bulk Status Update Workflow Tests
# ============================================================================


async def create_test_entities(
    authenticated_client, entity_type: str, count: int
) -> list[str]:
    """Create test entities for bulk update testing.

    Returns:
        List of entity IDs
    """
    entity_ids = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if entity_type == "requirement":
        # Create org -> project -> document -> requirements
        _, _, doc_id = await setup_document(authenticated_client)

        for i in range(count):
            req_data = {
                "name": f"Requirement {i+1} {timestamp}",
                "document_id": doc_id,
                "block_id": f"block_{i}_{timestamp}"
            }
            req_result = await authenticated_client.call_tool(
                "entity_tool",
                {"operation": "create", "entity_type": "requirement", "data": req_data}
            )

            if req_result.get("success"):
                entity_ids.append(req_result["data"]["id"])

    return entity_ids


@pytest.mark.asyncio
async def test_bulk_status_update_small_batch(authenticated_client):
    """Test bulk_status_update with 5 entities."""
    entity_ids = await create_test_entities(authenticated_client, "requirement", 5)

    if len(entity_ids) < 5:
        pytest.skip(f"Could not create enough entities, got {len(entity_ids)}")

    start_time = time.time()
    result = await authenticated_client.call_tool(
        "workflow_tool",
        {
            "workflow": "bulk_status_update",
            "parameters": {
                "entity_type": "requirement",
                "entity_ids": entity_ids,
                "new_status": "active"
            }
        }
    )
    duration_ms = (time.time() - start_time) * 1000

    assert result.get("success") is not False, \
        f"Workflow failed: {result.get('error')}"
    assert result.get("success_count") == 5, \
        f"Expected 5 successes, got {result.get('response', {}).get('success_count')}"
    assert duration_ms < 5000, \
        f"Bulk update took {duration_ms:.0f}ms, should be < 5000ms with FastHTTPClient"


@pytest.mark.asyncio
async def test_bulk_status_update_different_statuses(authenticated_client):
    """Test bulk_status_update with different status values."""
    entity_ids = await create_test_entities(authenticated_client, "requirement", 3)

    if len(entity_ids) < 3:
        pytest.skip(f"Could not create enough entities, got {len(entity_ids)}")

    # Test different statuses
    for status in ["active", "approved", "rejected"]:
        result = await authenticated_client.call_tool(
            "workflow_tool",
            {
                "workflow": "bulk_status_update",
                "parameters": {
                    "entity_type": "requirement",
                    "entity_ids": entity_ids,
                    "new_status": status
                }
            }
        )

        assert result.get("success") is not False, \
            f"Workflow failed for status '{status}': {result.get('error')}"
        assert result.get("new_status") == status, \
            f"Status mismatch: expected '{status}', got '{result.get('response', {}).get('new_status')}'"


@pytest.mark.asyncio
async def test_bulk_status_update_partial_failure(authenticated_client):
    """Test bulk_status_update with some invalid IDs."""
    valid_ids = await create_test_entities(authenticated_client, "requirement", 3)

    if len(valid_ids) < 3:
        pytest.skip(f"Could not create enough entities, got {len(valid_ids)}")

    # Use properly formatted UUIDs that don't exist
    invalid_ids = [str(uuid.uuid4()), str(uuid.uuid4())]
    all_ids = valid_ids + invalid_ids

    result = await authenticated_client.call_tool(
        "workflow_tool",
        {
            "workflow": "bulk_status_update",
            "parameters": {
                "entity_type": "requirement",
                "entity_ids": all_ids,
                "new_status": "active"
            }
        }
    )

    # Should still be successful but with partial results
    assert result.get("success") is not False, \
        f"Workflow should handle partial failures, got: {result.get('error')}"
    assert result.get("success_count") == 3, \
        f"Expected 3 successes, got {result.get('response', {}).get('success_count')}"
    assert result.get("total_entities") == 5, \
        f"Expected 5 total entities, got {result.get('response', {}).get('total_entities')}"


# ============================================================================
# Organization Onboarding Workflow Tests
# ============================================================================


@pytest.mark.asyncio
async def test_organization_onboarding_minimal(authenticated_client):
    """Test organization_onboarding with minimal parameters (name only)."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    result = await authenticated_client.call_tool(
        "workflow_tool",
        {
            "workflow": "organization_onboarding",
            "parameters": {
                "name": f"Minimal Test Organization {timestamp}"
            }
        }
    )

    assert result.get("success") is not False, \
        f"Workflow failed: {result.get('error')}"
    assert result.get("organization_id"), \
        "No organization_id in response"
    assert result.get("steps_completed", 0) >= 3, \
        f"Should complete at least 3 steps, got {result.get('response', {}).get('steps_completed')}"


@pytest.mark.asyncio
async def test_organization_onboarding_with_slug(authenticated_client):
    """Test organization_onboarding with custom slug."""
    custom_slug = f"custom-slug-{uuid.uuid4().hex[:8]}"

    result = await authenticated_client.call_tool(
        "workflow_tool",
        {
            "workflow": "organization_onboarding",
            "parameters": {
                "name": "Organization with Custom Slug",
                "slug": custom_slug
            }
        }
    )

    assert result.get("success") is not False, \
        f"Workflow failed: {result.get('error')}"
    assert result.get("organization_id"), \
        "No organization_id in response"

    # Verify slug was set
    results = result.get("results", [])
    for step in results:
        if step.get("step") == "create_organization" and "result" in step:
            assert step["result"].get("slug") == custom_slug, \
                f"Slug mismatch: expected '{custom_slug}', got '{step['result'].get('slug')}'"
            break


@pytest.mark.asyncio
async def test_organization_onboarding_with_starter_project(authenticated_client):
    """Test organization_onboarding with create_starter_project=True."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    result = await authenticated_client.call_tool(
        "workflow_tool",
        {
            "workflow": "organization_onboarding",
            "parameters": {
                "name": f"Org with Starter Project {timestamp}",
                "create_starter_project": True
            }
        }
    )

    assert result.get("success") is not False, \
        f"Workflow failed: {result.get('error')}"
    assert result.get("organization_id"), \
        "No organization_id in response"

    # Check that starter project was created
    results = result.get("results", [])
    project_steps = [
        step for step in results
        if step.get("step") == "create_starter_project"
    ]
    assert len(project_steps) == 1, \
        f"Expected 1 starter project creation step, got {len(project_steps)}"
    assert project_steps[0].get("status") == "success", \
        f"Starter project creation failed: {project_steps[0].get('error')}"


@pytest.mark.asyncio
async def test_organization_onboarding_all_parameters(authenticated_client):
    """Test organization_onboarding with all available parameters."""
    custom_slug = f"complete-org-{uuid.uuid4().hex[:8]}"

    start_time = time.time()
    result = await authenticated_client.call_tool(
        "workflow_tool",
        {
            "workflow": "organization_onboarding",
            "parameters": {
                "name": "Complete Organization",
                "slug": custom_slug,
                "type": "enterprise",
                "description": "A fully configured organization with all parameters",
                "create_starter_project": True
            },
            "transaction_mode": True,
            "format_type": "detailed"
        }
    )
    duration_ms = (time.time() - start_time) * 1000

    assert result.get("success") is not False, \
        f"Workflow failed: {result.get('error')}"
    assert result.get("organization_id"), \
        "No organization_id in response"
    assert result.get("steps_successful", 0) >= 4, \
        f"Should complete at least 4 steps, got {result.get('response', {}).get('steps_successful')}"
    assert duration_ms < 8000, \
        f"Complex workflow took {duration_ms:.0f}ms, should be < 8000ms with FastHTTPClient"

    # Verify all parameters were applied
    results = result.get("results", [])
    for step in results:
        if step.get("step") == "create_organization" and "result" in step:
            org = step["result"]
            assert org.get("name") == "Complete Organization", \
                f"Name mismatch: {org.get('name')}"
            assert org.get("slug") == custom_slug, \
                f"Slug mismatch: {org.get('slug')}"
            assert org.get("type") == "enterprise", \
                f"Type mismatch: {org.get('type')}"
            assert org.get("description") == "A fully configured organization with all parameters", \
                f"Description mismatch: {org.get('description')}"
            break


@pytest.mark.asyncio
async def test_organization_onboarding_missing_name(authenticated_client):
    """Test organization_onboarding without required name parameter."""
    result = await authenticated_client.call_tool(
        "workflow_tool",
        {
            "workflow": "organization_onboarding",
            "parameters": {
                "type": "team"
                # name is missing
            }
        }
    )

    assert result.get("success") is False, \
        "Should fail with missing name, but got success"
    assert "error" in result, \
        f"Expected 'error' in result, got keys: {list(result.keys())}"
    error = result.get("error", "").lower()
    assert "name" in error, \
        f"Expected 'name' in error message, got: {result.get('error')}"


# ============================================================================
# Performance Validation
# ============================================================================


@pytest.mark.asyncio
async def test_workflow_performance(authenticated_client):
    """Validate that workflow operations are fast with FastHTTPClient."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create org for setup_project workflow
    org_result = await authenticated_client.call_tool(
        "entity_tool",
        {
            "operation": "create",
            "entity_type": "organization",
            "data": {
                "name": f"Perf Test Org {timestamp}",
                "slug": f"perf-test-org-{timestamp}"
            }
        }
    )

    if not org_result.get("success"):
        pytest.skip(f"Cannot create organization: {org_result.get('error')}")

    org_id = org_result["data"]["id"]

    # Measure workflow performance
    start_time = time.time()

    result = await authenticated_client.call_tool(
        "workflow_tool",
        {
            "workflow": "setup_project",
            "parameters": {
                "name": f"Performance Test Project {timestamp}",
                "organization_id": org_id
            }
        }
    )

    duration = time.time() - start_time

    assert result["success"], \
        f"Workflow failed: {result.get('error')}"
    assert duration < 3.0, \
        f"Workflow took {duration:.2f}s, expected < 3.0s. FastHTTPClient should provide ~20x speedup over MCP decorator framework."
