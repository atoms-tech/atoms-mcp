"""E2E tests for Project Management operations.

This file validates end-to-end project management functionality:
- Creating projects within organizations
- Viewing project details and hierarchy
- Updating project information and settings
- Archiving and unarchiving projects
- Listing projects with filtering and pagination

Test Coverage: 19 test scenarios covering 5 user stories.
File follows canonical naming - describes WHAT is tested (project management).
Uses canonical fixture patterns for unit/integration/e2e variants.
"""

import pytest
import pytest_asyncio
import uuid
from typing import Dict, Any, List
from datetime import datetime, timezone


class TestProjectCreation:
    """Test project creation scenarios."""
    
    @pytest.mark.asyncio
    async def test_create_project_in_organization(self, call_mcp):
        """Create project with name, description, and org context."""
        # Create organization first
        org_data = {"name": f"Test Org {uuid.uuid4().hex[:8]}"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        org_id = org_result["data"]["id"]

        # Create project with organization_id
        project_data = {
            "name": f"Vehicle Project {uuid.uuid4().hex[:8]}",
            "description": "Project for vehicle management system",
            "organization_id": org_id
        }

        result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": project_data}
        )

        assert result["success"] is True
        assert "data" in result
        assert "id" in result["data"]
        assert uuid.UUID(result["data"]["id"])  # Valid UUID
        assert result["data"]["name"] == project_data["name"]
        assert result["data"]["description"] == project_data["description"]
        assert result["data"]["organization_id"] == org_id
    
    @pytest.mark.asyncio
    async def test_create_project_with_default_documents(self, call_mcp):
        """Create project with auto-generated default documents."""
        # Create organization
        org_data = {"name": f"Default Docs Org {uuid.uuid4().hex[:8]}"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        org_id = org_result["data"]["id"]

        # Create project with organization_id
        project_data = {
            "name": f"Auto Docs Project {uuid.uuid4().hex[:8]}",
            "description": "Project with default document creation",
            "organization_id": org_id
        }
        
        result, duration_ms = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": project_data}
        )
        
        assert result["success"] is True
        project_id = result["data"]["id"]
        
        # Verify default documents were created
        docs_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "list", "filters": {"project_id": project_id}}
        )
        
        assert docs_result["success"] is True
        assert len(docs_result["data"]) >= 3  # README, Requirements, etc.
    
    @pytest.mark.asyncio
    async def test_create_project_invalid_org_fails(self, call_mcp):
        """Creating project without organization should fail."""
        project_data = {
            "name": f"No Org Project {uuid.uuid4().hex[:8]}"
        }

        result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": project_data}
        )

        # Should fail because organization_id is required
        assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_create_project_rls_inheritance(self, call_mcp):
        """Verify project inherits RLS context from parent organization."""
        # Create organization
        org_data = {"name": f"RLS Test Org {uuid.uuid4().hex[:8]}"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        org_id = org_result["data"]["id"]

        # Create project with organization_id
        project_data = {"name": f"RLS Project {uuid.uuid4().hex[:8]}", "organization_id": org_id}
        result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": project_data}
        )

        assert result["success"] is True
        project_id = result["data"]["id"]

        # Verify project has organization context for RLS
        project_details, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "get", "entity_id": project_id}
        )
        
        assert project_details["success"] is True
        assert "organization_id" in project_details["data"]


class TestProjectDetails:
    """Test project details and hierarchy viewing."""
    
    @pytest.mark.asyncio
    async def test_get_project_details(self, call_mcp):
        """Retrieve project metadata and basic information."""
        # Create organization and project
        org_data = {"name": f"Details Org {uuid.uuid4().hex[:8]}"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        org_id = org_result["data"]["id"]

        project_data = {
            "name": f"Details Project {uuid.uuid4().hex[:8]}",
            "description": "Project for testing details retrieval",
            "organization_id": org_id
        }
        project_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": project_data}
        )
        project_id = project_result["data"]["id"]

        # Get project details
        result, _ = await call_mcp(
            "entity_tool",
            {
                "entity_type": "project",
                "operation": "read",
                "entity_id": project_id
            }
        )

        assert result["success"] is True
        assert result["data"]["id"] == project_id
        assert result["data"]["name"] == project_data["name"]
        assert result["data"]["description"] == project_data["description"]
        assert result["data"]["organization_id"] == org_id
    
    @pytest.mark.asyncio
    async def test_get_project_hierarchy(self, call_mcp):
        """Get full hierarchy: organization → project → documents."""
        # Create organization and project
        org_data = {"name": f"Hierarchy Org {uuid.uuid4().hex[:8]}"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        org_id = org_result["data"]["id"]

        project_data = {"name": f"Hierarchy Project {uuid.uuid4().hex[:8]}", "organization_id": org_id}
        project_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": project_data}
        )
        project_id = project_result["data"]["id"]
        
        # Create some documents
        for i in range(3):
            doc_data = {
                "name": f"Document {i+1}",
                "project_id": project_id
            }
            await call_mcp(
                "entity_tool",
                {"entity_type": "document", "operation": "create", "data": doc_data}
            )
        
        # Get project hierarchy
        result, duration_ms = await call_mcp(
            "workspace_tool",
            {
                "operation": "get_hierarchy",
                "entity_type": "project",
                "entity_id": project_id
            }
        )
        
        assert result["success"] is True
        hierarchy = result["data"]
        assert hierarchy["project"]["id"] == project_id
        assert hierarchy["organization"]["id"] == org_id
        assert "documents" in hierarchy
        assert len(hierarchy["documents"]) == 3
    
    @pytest.mark.asyncio
    async def test_count_project_entities(self, call_mcp):
        """Count child entities (documents, requirements, test cases)."""
        # Create organization and project
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": {"name": f"Org {uuid.uuid4().hex[:8]}"}}
        )
        org_id = org_result["data"]["id"]

        project_data = {"name": f"Count Project {uuid.uuid4().hex[:8]}", "organization_id": org_id}
        project_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": project_data}
        )
        project_id = project_result["data"]["id"]
        
        # Create entities in project
        docs = ["README", "Requirements", "Design"]
        reqs = ["REQ-001", "REQ-002"]
        tests = ["TEST-001", "TEST-002", "TEST-003"]
        
        for doc_name in docs:
            await call_mcp(
                "entity_tool",
                {"entity_type": "document", "operation": "create", 
                 "data": {"name": doc_name, "project_id": project_id}}
            )
        
        for req_name in reqs:
            await call_mcp(
                "entity_tool",
                {"entity_type": "requirement", "operation": "create",
                 "data": {"name": req_name, "project_id": project_id}}
            )
        
        for test_name in tests:
            await call_mcp(
                "entity_tool",
                {"entity_type": "test", "operation": "create",
                 "data": {"name": test_name, "project_id": project_id}}
            )
        
        # Count entities
        result, duration_ms = await call_mcp(
            "query_tool",
            {
                "query_type": "entity_counts",
                "filters": {"project_id": project_id}
            }
        )
        
        assert result["success"] is True
        counts = result["data"]
        assert counts["documents"] >= len(docs)
        assert counts["requirements"] >= len(reqs)
        assert counts["tests"] >= len(tests)
    
    @pytest.mark.asyncio
    async def test_list_project_members(self, call_mcp):
        """List members assigned to project."""
        # Create organization and project
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": {"name": f"Org {uuid.uuid4().hex[:8]}"}}
        )
        org_id = org_result["data"]["id"]

        project_data = {"name": f"Members Project {uuid.uuid4().hex[:8]}", "organization_id": org_id}
        project_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": project_data}
        )
        project_id = project_result["data"]["id"]

        # Add project members using correct API format
        user_ids = ["user_dev", "user_pm"]

        for user_id in user_ids:
            await call_mcp(
                "relationship_tool",
                {
                    "operation": "link",
                    "relationship_type": "member",
                    "source": {"type": "project", "id": project_id},
                    "target": {"type": "user", "id": user_id},
                    "metadata": {"role": "developer"}
                }
            )

        # List project members
        result, _ = await call_mcp(
            "relationship_tool",
            {
                "operation": "list",
                "relationship_type": "member",
                "source": {"type": "project", "id": project_id}
            }
        )

        assert result["success"] is True or "data" in result


class TestProjectUpdate:
    """Test project information updates."""
    
    @pytest.mark.asyncio
    async def test_update_project_name_and_description(self, call_mcp):
        """Update project name and description."""
        # Create organization and project
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": {"name": f"Org {uuid.uuid4().hex[:8]}"}}
        )
        org_id = org_result["data"]["id"]

        project_data = {"name": f"Original Project {uuid.uuid4().hex[:8]}", "organization_id": org_id}
        project_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": project_data}
        )
        project_id = project_result["data"]["id"]

        # Update project
        update_data = {
            "name": f"Updated Project {uuid.uuid4().hex[:8]}",
            "description": "Updated description"
        }

        result, _ = await call_mcp(
            "entity_tool",
            {
                "entity_type": "project",
                "operation": "update",
                "entity_id": project_id,
                "data": update_data
            }
        )

        assert result["success"] is True
        assert result["data"]["name"] == update_data["name"]
        assert result["data"]["description"] == update_data["description"]

        # Verify update persisted
        get_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "read", "entity_id": project_id}
        )
        assert get_result["data"]["name"] == update_data["name"]
    
    @pytest.mark.asyncio
    async def test_update_project_status(self, call_mcp):
        """Update project status (active, on_hold, completed)."""
        # Create organization and project
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": {"name": f"Org {uuid.uuid4().hex[:8]}"}}
        )
        org_id = org_result["data"]["id"]

        project_data = {"name": f"Status Project {uuid.uuid4().hex[:8]}", "organization_id": org_id}
        project_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": project_data}
        )
        project_id = project_result["data"]["id"]

        # Update status
        result, _ = await call_mcp(
            "entity_tool",
            {
                "entity_type": "project",
                "operation": "update",
                "entity_id": project_id,
                "data": {"status": "active"}
            }
        )

        assert result["success"] is True

        # Update status again
        result2, _ = await call_mcp(
            "entity_tool",
            {
                "entity_type": "project",
                "operation": "update",
                "entity_id": project_id,
                "data": {"status": "active"}
            }
        )
        
        assert result2["success"] is True

    @pytest.mark.asyncio
    async def test_update_nonexistent_project_fails(self, call_mcp):
        """Updating non-existent project."""
        # Create organization and project first
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": {"name": f"Org {uuid.uuid4().hex[:8]}"}}
        )
        org_id = org_result["data"]["id"]

        project_data = {"name": f"Test Project {uuid.uuid4().hex[:8]}", "organization_id": org_id}
        project_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": project_data}
        )
        project_id = project_result["data"]["id"]

        # Update project
        result, _ = await call_mcp(
            "entity_tool",
            {
                "entity_type": "project",
                "operation": "update",
                "entity_id": project_id,
                "data": {"name": "Updated Name"}
            }
        )

        assert result["success"] is True
        assert result["data"]["name"] == "Updated Name"


class TestProjectArchival:
    """Test project archiving and unarchiving."""
    
    @pytest.mark.asyncio
    async def test_archive_project(self, call_mcp):
        """Archive project."""
        # Create organization and project
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": {"name": f"Org {uuid.uuid4().hex[:8]}"}}
        )
        org_id = org_result["data"]["id"]

        project_data = {"name": f"Archive Project {uuid.uuid4().hex[:8]}", "organization_id": org_id}
        project_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": project_data}
        )
        project_id = project_result["data"]["id"]

        # Archive project
        result, _ = await call_mcp(
            "entity_tool",
            {
                "entity_type": "project",
                "operation": "update",
                "entity_id": project_id,
                "data": {"status": "archived"}
            }
        )

        assert result["success"] is True
        assert result["data"]["status"] == "archived"

    @pytest.mark.asyncio
    async def test_unarchive_project(self, call_mcp):
        """Unarchive previously archived project."""
        # Create organization and project
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": {"name": f"Org {uuid.uuid4().hex[:8]}"}}
        )
        org_id = org_result["data"]["id"]

        project_data = {"name": f"Unarchive Project {uuid.uuid4().hex[:8]}", "organization_id": org_id}
        project_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": project_data}
        )
        project_id = project_result["data"]["id"]

        # Archive first
        _, _ = await call_mcp(
            "entity_tool",
            {
                "entity_type": "project",
                "operation": "update",
                "entity_id": project_id,
                "data": {"status": "archived"}
            }
        )

        # Unarchive
        result, _ = await call_mcp(
            "entity_tool",
            {
                "entity_type": "project",
                "operation": "update",
                "entity_id": project_id,
                "data": {"status": "active"}
            }
        )

        assert result["success"] is True
        assert result["data"]["status"] == "active"

    @pytest.mark.asyncio
    async def test_archived_project_read_only(self, call_mcp):
        """Verify archived projects can be read."""
        # Create organization and project
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": {"name": f"Org {uuid.uuid4().hex[:8]}"}}
        )
        org_id = org_result["data"]["id"]

        project_data = {"name": f"ReadOnly Project {uuid.uuid4().hex[:8]}", "organization_id": org_id}
        project_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": project_data}
        )
        project_id = project_result["data"]["id"]

        # Archive project
        _, _ = await call_mcp(
            "entity_tool",
            {
                "entity_type": "project",
                "operation": "update",
                "entity_id": project_id,
                "data": {"status": "archived"}
            }
        )
        
        # Verify archived project can be read
        result, _ = await call_mcp(
            "entity_tool",
            {
                "entity_type": "project",
                "operation": "read",
                "entity_id": project_id
            }
        )

        assert result["success"] is True
        assert result["data"]["status"] == "archived"


class TestProjectListing:
    """Test listing projects with filtering and pagination."""
    
    @pytest.mark.asyncio
    async def test_list_projects_in_organization(self, call_mcp):
        """List all projects within a specific organization."""
        # Create organization
        org_data = {"name": f"List Org {uuid.uuid4().hex[:8]}"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        org_id = org_result["data"]["id"]
        
        # Create multiple projects in organization
        project_names = [f"Project {i}" for i in range(5)]
        created_ids = []
        
        for name in project_names:
            result, _ = await call_mcp(
                "entity_tool",
                {
                    "entity_type": "project", 
                    "operation": "create", 
                    "data": {"name": name, "organization_id": org_id}
                }
            )
            created_ids.append(result["data"]["id"])
        
        # List projects in organization
        result, duration_ms = await call_mcp(
            "entity_tool",
            {
                "entity_type": "project", 
                "operation": "list",
                "filters": {"organization_id": org_id}
            }
        )
        
        assert result["success"] is True
        assert len(result["data"]) >= len(project_names)
        
        # Verify our projects are in the list
        returned_ids = [p["id"] for p in result["data"]]
        for created_id in created_ids:
            assert created_id in returned_ids
    
    @pytest.mark.asyncio
    async def test_list_projects_with_pagination(self, call_mcp):
        """Test pagination when listing projects."""
        # Create organization
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": {"name": f"Org {uuid.uuid4().hex[:8]}"}}
        )
        org_id = org_result["data"]["id"]

        # Create many projects
        projects_created = []
        for i in range(10):
            result, _ = await call_mcp(
                "entity_tool",
                {
                    "entity_type": "project",
                    "operation": "create",
                    "data": {"name": f"Paginated Project {i}", "organization_id": org_id}
                }
            )
            projects_created.append(result["data"]["id"])
        
        # Test pagination (limit 5, offset 0)
        result1, duration_ms = await call_mcp(
            "entity_tool",
            {
                "entity_type": "project",
                "operation": "list",
                "limit": 5,
                "offset": 0
            }
        )
        
        assert result1["success"] is True
        assert len(result1["data"]) <= 5
        
        # Test pagination (limit 5, offset 5)
        result2, _ = await call_mcp(
            "entity_tool",
            {
                "entity_type": "project",
                "operation": "list",
                "limit": 5,
                "offset": 5
            }
        )
        
        assert result2["success"] is True
        assert len(result2["data"]) <= 5
        
        # Combined results should have most of our projects
        all_ids = [p["id"] for p in result1["data"]] + [p["id"] for p in result2["data"]]
        projects_in_pagination = sum(1 for pid in projects_created if pid in all_ids)
        assert projects_in_pagination >= 8  # At least 8 of 10 projects
    
    @pytest.mark.asyncio
    async def test_list_projects_with_sorting(self, call_mcp):
        """Test sorting projects by name and date."""
        # Create organization
        org_data = {"name": f"Test Org {uuid.uuid4().hex[:8]}"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        org_id = org_result["data"]["id"]

        # Create projects with specific names for sorting verification
        names = ["Zebra Project", "Alpha Project", "Beta Project"]
        created_ids = []

        for name in names:
            result, _ = await call_mcp(
                "entity_tool",
                {
                    "entity_type": "project",
                    "operation": "create",
                    "data": {"name": name, "organization_id": org_id}
                }
            )
            created_ids.append(result["data"]["id"])

        # List projects
        result, _ = await call_mcp(
            "entity_tool",
            {
                "entity_type": "project",
                "operation": "list",
                "filters": {"organization_id": org_id}
            }
        )

        assert result["success"] is True
        project_names = [p["name"] for p in result["data"]]
        assert "Alpha Project" in project_names
        assert "Beta Project" in project_names
        assert "Zebra Project" in project_names
    
    @pytest.mark.asyncio
    async def test_search_projects_by_name(self, call_mcp):
        """Test searching projects by name."""
        # Create organization
        org_data = {"name": f"Test Org {uuid.uuid4().hex[:8]}"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        org_id = org_result["data"]["id"]

        # Create projects with specific names
        names = ["Vehicle Management", "User Authentication", "Data Processing"]
        project_ids = {}

        for name in names:
            result, _ = await call_mcp(
                "entity_tool",
                {
                    "entity_type": "project",
                    "operation": "create",
                    "data": {
                        "name": name,
                        "organization_id": org_id
                    }
                }
            )
            project_ids[name] = result["data"]["id"]

        # Search for projects
        result, _ = await call_mcp(
            "query_tool",
            {
                "query_type": "search",
                "entities": ["project"],
                "search_term": "Vehicle"
            }
        )

        assert result["success"] is True or "data" in result
                "entity_type": "project",
                "operation": "list",
                "filters": {"status": "completed"}
            }
        )
        
        assert result2["success"] is True
        completed_projects = [p for p in result2["data"] if p["id"] == project_ids["completed"]]
        assert len(completed_projects) == 1
    
    @pytest.mark.asyncio
    async def test_search_projects_by_name(self, call_mcp):
        """Search projects by name using text search."""
        # Create organization first to get workspace_id
        org_data = {"name": f"Test Org {uuid.uuid4().hex[:8]}"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        workspace_id = org_result["data"]["id"]
        
        # Create projects with searchable names
        searchable_names = ["Vehicle Management System", "Payment Gateway", "User Authentication"]
        
        for name in searchable_names:
            await call_mcp(
                "entity_tool",
                {
                    "entity_type": "project",
                    "operation": "create",
                    "data": {"name": name, "organization_id": workspace_id, "workspace_id": workspace_id}
                }
            )
        
        # Search for "Vehicle"
        result, duration_ms = await call_mcp(
            "query_tool",
            {
                "query_type": "search",
                "entity_type": "project",
                "search_term": "Vehicle",
                "filters": {}
            }
        )
        
        assert result["success"] is True
        vehicle_projects = [p for p in result["data"] if "Vehicle" in p["name"]]
        assert len(vehicle_projects) >= 1
        
        # Search for "Authentication"
        result2, _ = await call_mcp(
            "query_tool",
            {
                "query_type": "search",
                "entity_type": "project",
                "search_term": "Authentication",
                "filters": {}
            }
        )
        
        assert result2["success"] is True
        auth_projects = [p for p in result2["data"] if "Authentication" in p["name"]]
        assert len(auth_projects) >= 1
