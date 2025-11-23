"""E2E test scenarios and test data fixtures."""

import uuid
import asyncio
import pytest_asyncio


@pytest_asyncio.fixture
async def workflow_scenarios(end_to_end_client):
    """Pre-configured complex workflow scenarios for E2E testing."""

    async def create_complete_project_scenario():
        """Create a complete project scenario with org → project → docs → reqs."""
        # Step 1: Create organization
        org_result = await end_to_end_client.call_tool("entity_tool", {
            "operation": "create",
            "entity_type": "organization",
            "data": {
                "name": f"E2E Test Org {uuid.uuid4().hex[:8]}",
                "description": "Organization created for E2E testing",
                "type": "team"
            }
        })

        if not org_result.get("success"):
            raise Exception("Failed to create organization in E2E scenario")

        org_id = org_result["data"]["id"]

        # Step 2: Create project
        project_result = await end_to_end_client.call_tool("entity_tool", {
            "operation": "create",
            "entity_type": "project",
            "data": {
                "name": f"E2E Test Project {uuid.uuid4().hex[:8]}",
                "description": "Project created for E2E testing",
                "organization_id": org_id,
                "status": "active"
            }
        })

        if not project_result.get("success"):
            raise Exception("Failed to create project in E2E scenario")

        project_id = project_result["data"]["id"]

        # Step 3: Create documents
        doc_results = []
        for i in range(3):
            doc_result = await end_to_end_client.call_tool("entity_tool", {
                "operation": "create",
                "entity_type": "document",
                "data": {
                    "name": f"E2E Test Doc {i+1}",
                    "content": f"Test document content {i+1}",
                    "project_id": project_id,
                    "version": "1.0.0"
                }
            })
            if doc_result.get("success"):
                doc_results.append(doc_result["data"]["id"])

        # Step 4: Create requirements
        req_results = []
        for i in range(2):
            target_doc = doc_results[i % len(doc_results)] if doc_results else None
            req_payload = {
                "name": f"E2E Requirement {i+1}",
                "description": f"Test requirement description {i+1}",
                "priority": "high" if i == 0 else "medium",
                "project_id": project_id,
            }
            if target_doc:
                req_payload["document_id"] = target_doc
            req_result = await end_to_end_client.call_tool("entity_tool", {
                "operation": "create",
                "entity_type": "requirement",
                "data": req_payload
            })
            if req_result.get("success"):
                req_results.append(req_result["data"]["id"])

        # Step 5: Create relationships
        for doc_id in doc_results:
            for req_id in req_results:
                await end_to_end_client.call_tool("relationship_tool", {
                    "operation": "create",
                    "source_type": "document",
                    "source_id": doc_id,
                    "target_type": "requirement",
                    "target_id": req_id,
                    "relationship_type": "references"
                })

        return {
            "organization_id": org_id,
            "project_id": project_id,
            "document_ids": doc_results,
            "requirement_ids": req_results,
            "total_entities": 1 + 1 + len(doc_results) + len(req_results)
        }

    async def create_parallel_workflow_scenario():
        """Create scenario for testing parallel workflows."""
        # Create multiple organizations in parallel
        tasks = []
        for i in range(5):
            task = end_to_end_client.call_tool("entity_tool", {
                "operation": "create",
                "entity_type": "organization",
                "data": {
                    "name": f"Parallel Org {i+1}",
                    "description": f"Organization {i+1} for parallel testing",
                    "type": "department"
                }
            })
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        successful_orgs = []
        for i, result in enumerate(results):
            if isinstance(result, dict) and result.get("success"):
                successful_orgs.append({
                    "index": i,
                    "id": result["data"]["id"],
                    "name": result["data"]["name"]
                })

        return {
            "total_created": len(tasks),
            "successful": len(successful_orgs),
            "organizations": successful_orgs
        }

    async def create_error_recovery_scenario():
        """Create scenario with intentional errors for recovery testing."""
        return {
            "invalid_entity_type": "invalid_type",
            "missing_required_data": {},
            "circular_relationship": {
                "source_type": "organization",
                "source_id": "same-id",
                "target_type": "organization",
                "target_id": "same-id",
                "relationship_type": "relates_to"
            }
        }

    return {
        "complete_project": create_complete_project_scenario,
        "parallel_workflow": create_parallel_workflow_scenario,
        "error_recovery": create_error_recovery_scenario,
    }


@pytest_asyncio.fixture
async def test_data_setup(end_to_end_client):
    """Comprehensive test data setup for e2e tests.

    Creates a complete test environment with organizations, projects, documents,
    requirements, and test cases.

    Returns:
        Dict with all created entities for use in tests
    """
    test_id = uuid.uuid4().hex[:8]
    data = {}

    try:
        # Create organization
        org_result = await end_to_end_client.call_tool("entity_tool", {
            "operation": "create",
            "entity_type": "organization",
            "data": {
                "name": f"Test Org {test_id}",
                "description": "Test organization"
            }
        })
        
        if org_result.get("success"):
            data["organization"] = org_result["data"]
            org_id = org_result["data"]["id"]

            # Create projects
            for i in range(2):
                proj_result = await end_to_end_client.call_tool("entity_tool", {
                    "operation": "create",
                    "entity_type": "project",
                    "data": {
                        "name": f"Test Project {i+1}",
                        "organization_id": org_id,
                        "status": "active"
                    }
                })
                if proj_result.get("success"):
                    if "projects" not in data:
                        data["projects"] = []
                    data["projects"].append(proj_result["data"])

        yield data

    finally:
        # Cleanup would happen here in production
        pass


@pytest_asyncio.fixture
async def test_data_with_relationships(test_data_setup):
    """Extend test data with relationships between entities."""
    data = test_data_setup
    
    if "organization" in data and "projects" in data:
        relationships = []
        for project in data["projects"]:
            rel_result = await end_to_end_client.call_tool(
                "relationship_tool",
                {
                    "operation": "create",
                    "source_type": "organization",
                    "source_id": data["organization"]["id"],
                    "target_type": "project",
                    "target_id": project["id"],
                    "relationship_type": "contains"
                }
            )
            if rel_result.get("success"):
                relationships.append(rel_result["data"])
        
        data["relationships"] = relationships
    
    return data
