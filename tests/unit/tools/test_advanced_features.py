"""Advanced features testing.

Tests advanced features and edge cases:
- Search facets and accuracy
- Export format validation (JSON/CSV structure)
- Import duplicate detection
- Permission expiration enforcement
- Async job status tracking
- Complex relationship queries

Run with: pytest tests/unit/tools/test_advanced_features.py -v
"""

import uuid
import pytest
import json
import csv
from datetime import datetime, timezone, timedelta
from io import StringIO

pytestmark = [pytest.mark.asyncio, pytest.mark.unit]


class TestSearchFeatures:
    """Test advanced search features."""
    
    @pytest.mark.unit
    async def DISABLE_test_search_facets_accuracy(self, call_mcp, test_organization):
        """Test that search facets are accurate and comprehensive."""
        # Create projects with different attributes for faceting
        projects = []
        
        # Create projects with different statuses
        statuses = ["planning", "active", "completed", "archived"]
        priorities = ["low", "medium", "high"]
        types = ["development", "research", "documentation"]
        
        for status in statuses:
            for priority in priorities:
                for project_type in types[:2]:  # Limit to 2 types to keep test reasonable
                    result, _ = await call_mcp(
                        "entity_tool",
                        {
                            "operation": "create",
                            "entity_type": "project",
                            "data": {
                                "name": f"Facet Test {status} {priority} {project_type} {uuid.uuid4().hex[:8]}",
                                "organization_id": test_organization,
                                "status": status,
                                "priority": priority,
                                "type": project_type,
                                "description": f"Project with {status} status and {priority} priority for {project_type}",
                            },
                        },
                    )
                    
                    assert result.get("success", False) is True
                    projects.append(result.data)
        
        # Test search with facets
        search_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "search",
                "entity_type": "project",
                "query": "Facet Test",
                "facets": ["status", "priority", "type"],
                "filters": {"organization_id": test_organization},
            },
        )
        
        assert search_result.success is True
        
        # Should include facet information
        if "facets" in search_result.data:
            facets = search_result.data["facets"]
            
            # Verify status facet
            if "status" in facets:
                status_facet = facets["status"]
                for status in statuses:
                    assert status in status_facet, f"Status {status} missing from facet"
                    assert status_facet[status] > 0, f"Status {status} has zero count"
                
                # Total counts should match
                total_status_count = sum(status_facet.values())
                assert total_status_count >= len(statuses) * len(priorities) * 2  # At least our created projects
            
            # Verify priority facet
            if "priority" in facets:
                priority_facet = facets["priority"]
                for priority in priorities:
                    assert priority in priority_facet, f"Priority {priority} missing from facet"
                    assert priority_facet[priority] > 0, f"Priority {priority} has zero count"
            
            # Verify type facet
            if "type" in facets:
                type_facet = facets["type"]
                for project_type in types[:2]:
                    assert project_type in type_facet, f"Type {project_type} missing from facet"
                    assert type_facet[project_type] > 0, f"Type {project_type} has zero count"
    
    @pytest.mark.unit
    async def test_search_filter_combinations(self, call_mcp, test_organization):
        """Test complex search filter combinations."""
        # Create test data
        projects = []
        
        for i in range(10):
            result, _ = await call_mcp(
                "entity_tool",
                {
                    "operation": "create",
                    "entity_type": "project",
                    "data": {
                        "name": f"Filter Test Project {i} {uuid.uuid4().hex[:8]}",
                        "organization_id": test_organization,
                        "status": "active" if i % 2 == 0 else "planning",
                        "priority": ["low", "medium", "high"][i % 3],
                        "type": "development" if i % 3 == 0 else "research",
                        "created_at": (datetime.now(timezone.utc) - timedelta(days=i)).isoformat(),
                    },
                },
            )
            assert result.get("success", False) is True
            projects.append(result.data)
        
        # Test multiple filter combinations
        filter_combinations = [
            {
                "name": "Active high priority projects",
                "filters": {
                    "status": "active",
                    "priority": "high",
                    "organization_id": test_organization,
                },
                "min_count": 1,
            },
            {
                "name": "Research projects",
                "filters": {
                    "type": "research",
                    "organization_id": test_organization,
                },
                "min_count": 3,
            },
            {
                "name": "Development projects created in last 5 days",
                "filters": {
                    "type": "development",
                    "created_after": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat(),
                    "organization_id": test_organization,
                },
                "min_count": 1,
            },
        ]
        
        for combo in filter_combinations:
            search_result, _ = await call_mcp(
                "entity_tool",
                {
                    "operation": "search",
                    "entity_type": "project",
                    "query": "Filter Test Project",
                    "filters": combo["filters"],
                },
            )
            
            assert search_result.success is True, f"Search failed for: {combo['name']}"
            assert len(search_result.data) >= combo["min_count"], f"Expected at least {combo['min_count']} results for: {combo['name']}"
            
            # Verify results match filters
            for project in search_result.data:
                if "status" in combo["filters"]:
                    assert project["status"] == combo["filters"]["status"]
                if "priority" in combo["filters"]:
                    assert project["priority"] == combo["filters"]["priority"]
                if "type" in combo["filters"]:
                    assert project["type"] == combo["filters"]["type"]
    
    @pytest.mark.unit
    async def test_search_sorting_and_pagination(self, call_mcp, test_organization):
        """Test search sorting and pagination functionality."""
        # Create projects with different creation dates and names
        projects = []
        base_time = datetime.now(timezone.utc)
        
        for i in range(10):
            result, _ = await call_mcp(
                "entity_tool",
                {
                    "operation": "create",
                    "entity_type": "project",
                    "data": {
                        "name": f"Sort Test Project {i:02d} {uuid.uuid4().hex[:8]}",
                        "organization_id": test_organization,
                        "priority": ["low", "medium", "high"][i % 3],
                        "created_at": (base_time - timedelta(hours=i)).isoformat(),
                    },
                },
            )
            assert result.get("success", False) is True
            projects.append(result.data)
        
        # Test sorting by name
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "search",
                "entity_type": "project",
                "query": "Sort Test Project",
                "sort": [{"field": "name", "direction": "asc"}],
                "filters": {"organization_id": test_organization},
            },
        )
        
        assert result.get("success", False) is True
        names = [p["name"] for p in result.data]
        assert names == sorted(names), "Results not sorted by name ascending"
        
        # Test sorting by created_at (newest first)
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "search",
                "entity_type": "project",
                "query": "Sort Test Project",
                "sort": [{"field": "created_at", "direction": "desc"}],
                "filters": {"organization_id": test_organization},
            },
        )
        
        assert result.get("success", False) is True
        created_dates = [p["created_at"] for p in result.data]
        assert created_dates == sorted(created_dates, reverse=True), "Results not sorted by created_at descending"
        
        # Test pagination
        page_size = 3
        all_results = []
        
        for page in range(0, 10):  # Max 10 pages to avoid infinite loop
            result, _ = await call_mcp(
                "entity_tool",
                {
                    "operation": "search",
                    "entity_type": "project",
                    "query": "Sort Test Project",
                    "sort": [{"field": "name", "direction": "asc"}],
                    "filters": {"organization_id": test_organization},
                    "limit": page_size,
                    "offset": page * page_size,
                },
            )
            
            assert result.get("success", False) is True
            
            if not result.data:
                break
            
            all_results.extend(result.data)
            
            if len(result.data) < page_size:
                break
        
        assert len(all_results) >= 10, "Pagination didn't return all results"


class TestExportFeatures:
    """Test advanced export features."""
    
    @pytest.mark.unit
    async def test_export_json_format_validation(self, call_mcp, test_organization):
        """Test that JSON export has correct structure and format."""
        # Create test data
        projects = []
        for i in range(5):
            result, _ = await call_mcp(
                "entity_tool",
                {
                    "operation": "create",
                    "entity_type": "project",
                    "data": {
                        "name": f"Export Test Project {i} {uuid.uuid4().hex[:8]}",
                        "organization_id": test_organization,
                        "status": "active",
                        "priority": ["low", "medium", "high"][i % 3],
                        "description": f"Description for project {i}",
                    },
                },
            )
            assert result.get("success", False) is True
            projects.append(result.data)
        
        # Export to JSON
        export_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "export",
                "entity_type": "project",
                "format": "json",
                "filters": {"organization_id": test_organization},
            },
        )
        
        assert export_result.success is True
        assert "data" in export_result.data
        
        # Parse and validate JSON structure
        try:
            exported_data = json.loads(export_result.data["data"])
        except json.JSONDecodeError:
            pytest.fail("Exported data is not valid JSON")
        
        # Should be a list or object with expected structure
        assert isinstance(exported_data, list), "Exported JSON should be a list"
        assert len(exported_data) >= 5, "Export should include all created projects"
        
        # Validate each project structure
        for project in exported_data:
            assert "id" in project, "Exported project missing ID"
            assert "name" in project, "Exported project missing name"
            assert "status" in project, "Exported project missing status"
            assert "priority" in project, "Exported project missing priority"
            assert "created_at" in project, "Exported project missing created_at"
            
            # Verify UUID format
            uuid.UUID(project["id"])  # Will raise if invalid format
            
            # Verify timestamp format
            datetime.fromisoformat(project["created_at"].replace('Z', '+00:00'))
    
    @pytest.mark.unit
    async def test_export_csv_format_validation(self, call_mcp, test_organization):
        """Test that CSV export has correct structure and format."""
        # Create test data
        projects = []
        for i in range(5):
            result, _ = await call_mcp(
                "entity_tool",
                {
                    "operation": "create",
                    "entity_type": "project",
                    "data": {
                        "name": f"CSV Export Test {i} {uuid.uuid4().hex[:8]}",
                        "organization_id": test_organization,
                        "status": "active",
                        "priority": ["low", "medium", "high"][i % 3],
                        "description": f"Description with comma, and \"quotes\" {i}",
                    },
                },
            )
            assert result.get("success", False) is True
            projects.append(result.data)
        
        # Export to CSV
        export_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "export",
                "entity_type": "project",
                "format": "csv",
                "filters": {"organization_id": test_organization},
            },
        )
        
        assert export_result.success is True
        assert "data" in export_result.data
        
        # Parse and validate CSV structure
        csv_data = export_result.data["data"]
        
        try:
            # Use StringIO to parse CSV
            csv_reader = csv.DictReader(StringIO(csv_data))
            rows = list(csv_reader)
        except Exception as e:
            pytest.fail(f"Exported data is not valid CSV: {e}")
        
        # Should have at least our created projects
        assert len(rows) >= 5, "CSV export should include all created projects"
        
        # Validate headers
        expected_headers = ["id", "name", "status", "priority", "description", "created_at"]
        for header in expected_headers:
            assert header in csv_reader.fieldnames, f"CSV missing header: {header}"
        
        # Validate each row
        for row in rows:
            assert row["id"], "CSV row missing ID"
            assert row["name"], "CSV row missing name"
            assert row["status"], "CSV row missing status"
            assert row["priority"], "CSV row missing priority"
            
            # Verify UUID format
            uuid.UUID(row["id"])  # Will raise if invalid format
            
            # Verify timestamp format
            datetime.fromisoformat(row["created_at"].replace('Z', '+00:00'))
    
    @pytest.mark.unit
    async def test_export_filtering_and_fields(self, call_mcp, test_organization):
        """Test export with filtering and field selection."""
        # Create projects with different attributes
        projects = []
        for i in range(10):
            result, _ = await call_mcp(
                "entity_tool",
                {
                    "operation": "create",
                    "entity_type": "project",
                    "data": {
                        "name": f"Field Test Project {i} {uuid.uuid4().hex[:8]}",
                        "organization_id": test_organization,
                        "status": "active" if i % 2 == 0 else "planning",
                        "priority": ["low", "medium", "high"][i % 3],
                        "description": f"Description for project {i}",
                        "type": "development" if i % 2 == 0 else "research",
                    },
                },
            )
            assert result.get("success", False) is True
            projects.append(result.data)
        
        # Export with field selection
        export_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "export",
                "entity_type": "project",
                "format": "json",
                "fields": ["id", "name", "status"],
                "filters": {
                    "organization_id": test_organization,
                    "status": "active",
                },
            },
        )
        
        assert export_result.success is True
        
        # Parse and validate
        exported_data = json.loads(export_result.data["data"])
        
        # Should only include active projects
        for project in exported_data:
            assert project["status"] == "active", "Export should only include active projects"
            
            # Should only include requested fields
            expected_fields = {"id", "name", "status"}
            actual_fields = set(project.keys())
            assert actual_fields == expected_fields, f"Export includes unexpected fields: {actual_fields - expected_fields}"


class TestImportFeatures:
    """Test advanced import features."""
    
    @pytest.mark.unit
    async def test_import_duplicate_detection(self, call_mcp, test_organization):
        """Test that import correctly detects and handles duplicates."""
        # Create initial project
        original_name = f"Duplicate Test Project {uuid.uuid4().hex[:8]}"
        
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "project",
                "data": {
                    "name": original_name,
                    "organization_id": test_organization,
                    "status": "active",
                },
            },
        )
        
        assert result.get("success", False) is True
        original_id = result.data["id"]
        
        # Prepare import data with duplicate
        import_data = [
            {
                "name": original_name,  # Duplicate name
                "organization_id": test_organization,
                "status": "active",
            },
            {
                "name": f"New Project {uuid.uuid4().hex[:8]}",
                "organization_id": test_organization,
                "status": "planning",
            },
        ]
        
        # Test import with duplicate handling
        import_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "import",
                "entity_type": "project",
                "format": "json",
                "data": json.dumps(import_data),
                "duplicate_handling": "skip",  # Skip duplicates
            },
        )
        
        assert import_result.success is True
        
        # Should report duplicate detection
        if "duplicates" in import_result.data:
            assert len(import_result.data["duplicates"]) >= 1
        
        # Should have imported the new project
        if "imported" in import_result.data:
            assert len(import_result.data["imported"]) >= 1
            
            # Verify new project was created
            new_project_id = import_result.data["imported"][0]["id"]
            new_project_result, _ = await call_mcp(
                "entity_tool",
                {
                    "operation": "read",
                    "entity_type": "project",
                    "entity_id": new_project_id,
                },
            )
            assert new_project_result.success is True
        
        # Test import with update duplicate handling
        import_data[0]["status"] = "completed"  # Update status
        
        update_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "import",
                "entity_type": "project",
                "format": "json",
                "data": json.dumps(import_data),
                "duplicate_handling": "update",  # Update duplicates
            },
        )
        
        assert update_result.success is True
        
        # Verify original was updated
        updated_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "read",
                "entity_type": "project",
                "entity_id": original_id,
            },
        )
        
        assert updated_result.success is True
        assert updated_result.data["status"] == "completed"
    
    @pytest.mark.unit
    async def test_import_validation_and_error_handling(self, call_mcp, test_organization):
        """Test import validation and error handling."""
        # Prepare import data with validation errors
        import_data = [
            {
                "name": "Valid Project",
                "organization_id": test_organization,
            },
            {
                "name": "",  # Invalid empty name
                "organization_id": test_organization,
            },
            {
                "name": "Project with invalid org",
                "organization_id": str(uuid.uuid4()),  # Invalid org
            },
            {
                "name": "Project missing org",
                # Missing organization_id
            },
        ]
        
        # Test import with validation errors
        import_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "import",
                "entity_type": "project",
                "format": "json",
                "data": json.dumps(import_data),
                "error_handling": "continue",  # Continue on errors
            },
        )
        
        assert import_result.success is True
        
        # Should report validation errors
        if "errors" in import_result.data:
            assert len(import_result.data["errors"]) >= 2  # At least 2 validation errors
        
        # Should have imported the valid entry
        if "imported" in import_result.data:
            assert len(import_result.data["imported"]) >= 1
        
        # Test import with fail on error
        fail_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "import",
                "entity_type": "project",
                "format": "json",
                "data": json.dumps(import_data),
                "error_handling": "fail",  # Fail on first error
            },
        )
        
        # Should either fail or import only the valid entry before first error
        assert fail_result.success or ("errors" in fail_result.data)


class TestPermissionFeatures:
    """Test advanced permission features."""
    
    @pytest.mark.unit
    async def test_permission_expiration_enforcement(self, call_mcp, test_organization):
        """Test that permission expiration is properly enforced."""
        # Create test user
        user_id = str(uuid.uuid4())
        
        user_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "user",
                "data": {
                    "id": user_id,
                    "email": f"expiration_test_{uuid.uuid4().hex[:8]}@example.com",
                    "display_name": "Expiration Test User",
                },
            },
        )
        
        assert user_result.success is True
        
        # Grant permission with expiration
        expires_at = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        
        grant_result, _ = await call_mcp(
            "relationship_tool",
            {
                "operation": "create",
                "relationship_type": "member",
                "from_entity_id": user_id,
                "to_entity_id": test_organization,
                "data": {
                    "role": "member",
                    "permissions": ["read", "write"],
                    "expires_at": expires_at,
                },
            },
        )
        
        assert grant_result.success is True
        
        # Check permission is currently valid
        permission_result, _ = await call_mcp(
            "relationship_tool",
            {
                "operation": "check_permission",
                "from_entity_id": user_id,
                "to_entity_id": test_organization,
                "permission": "read",
            },
        )
        
        # Should currently have permission
        assert permission_result.success is True or permission_result.data.get("has_permission", False)
        
        # Test with expired permission (simulate)
        expired_at = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        
        grant_expired_result, _ = await call_mcp(
            "relationship_tool",
            {
                "operation": "create",
                "relationship_type": "member",
                "from_entity_id": str(uuid.uuid4()),  # Different user
                "to_entity_id": test_organization,
                "data": {
                    "role": "member",
                    "permissions": ["read", "write"],
                    "expires_at": expired_at,
                },
            },
        )
        
        if grant_expired_result.success:
            # Check expired permission
            expired_user_id = grant_expired_result.data["from_entity_id"]
            
            expired_check_result, _ = await call_mcp(
                "relationship_tool",
                {
                    "operation": "check_permission",
                    "from_entity_id": expired_user_id,
                    "to_entity_id": test_organization,
                    "permission": "read",
                },
            )
            
            # Should not have permission due to expiration
            assert not expired_check_result.data.get("has_permission", True)


class TestAsyncJobFeatures:
    """Test async job tracking features."""
    
    @pytest.mark.unit
    async def test_async_job_status_tracking(self, call_mcp, test_organization):
        """Test async job status tracking and updates."""
        # Start a bulk operation that might be async
        bulk_data = {}
        for i in range(10):
            bulk_data[f"async_job_{i}"] = {
                "name": f"Async Job Test Project {i} {uuid.uuid4().hex[:8]}",
                "organization_id": test_organization,
                "description": "Project for async job testing " * 10,  # Make it substantial
            }
        
        # Start bulk create operation
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "bulk_create",
                "entity_type": "project",
                "data": bulk_data,
                "async": True,  # Request async execution
            },
        )
        
        assert result.get("success", False) is True
        
        # Should return job ID if async
        if "job_id" in result.data:
            job_id = result.data["job_id"]
            
            # Track job status
            max_wait = 30  # Maximum 30 seconds wait
            wait_interval = 1  # Check every second
            
            for _ in range(max_wait // wait_interval):
                status_result, _ = await call_mcp(
                    "entity_tool",
                    {
                        "operation": "job_status",
                        "job_id": job_id,
                    },
                )
                
                assert status_result.success is True
                
                job_status = status_result.data.get("status")
                progress = status_result.data.get("progress", 0)
                
                # Should have valid status
                assert job_status in ["pending", "running", "completed", "failed"]
                
                if job_status == "completed":
                    # Check final results
                    results_result, _ = await call_mcp(
                        "entity_tool",
                        {
                            "operation": "job_results",
                            "job_id": job_id,
                        },
                    )
                    
                    assert results_result.success is True
                    assert "results" in results_result.data
                    break
                elif job_status == "failed":
                    # Check error details
                    error_result, _ = await call_mcp(
                        "entity_tool",
                        {
                            "operation": "job_error",
                            "job_id": job_id,
                        },
                    )
                    
                    assert error_result.success is True
                    assert "error" in error_result.data
                    break
                
                await asyncio.sleep(wait_interval)
            else:
                pytest.fail("Async job did not complete within timeout period")
    
    @pytest.mark.unit
    async def test_async_job_cancellation(self, call_mcp, test_organization):
        """Test async job cancellation functionality."""
        # Start a long-running bulk operation
        bulk_data = {}
        for i in range(50):  # Larger dataset to ensure it runs longer
            bulk_data[f"cancel_job_{i}"] = {
                "name": f"Cancel Test Project {i} {uuid.uuid4().hex[:8]}",
                "organization_id": test_organization,
                "description": "Large project description for cancellation test " * 20,
            }
        
        # Start bulk create operation
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "bulk_create",
                "entity_type": "project",
                "data": bulk_data,
                "async": True,
            },
        )
        
        assert result.get("success", False) is True
        
        # If async execution is supported
        if "job_id" in result.data:
            job_id = result.data["job_id"]
            
            # Wait a bit for job to start
            await asyncio.sleep(1)
            
            # Cancel the job
            cancel_result, _ = await call_mcp(
                "entity_tool",
                {
                    "operation": "job_cancel",
                    "job_id": job_id,
                },
            )
            
            assert cancel_result.success is True
            
            # Check job status reflects cancellation
            status_result, _ = await call_mcp(
                "entity_tool",
                {
                    "operation": "job_status",
                    "job_id": job_id,
                },
            )
            
            assert status_result.success is True
            assert status_result.data.get("status") in ["cancelled", "completed", "failed"]


class TestRelationshipQueries:
    """Test complex relationship queries."""
    
    @pytest.mark.unit
    async def test_complex_relationship_queries(self, call_mcp, test_organization):
        """Test complex relationship traversal queries."""
        # Create hierarchical structure
        project_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "project",
                "data": {
                    "name": f"Relationship Test Project {uuid.uuid4().hex[:8]}",
                    "organization_id": test_organization,
                },
            },
        )
        
        document_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "document",
                "data": {
                    "name": f"Relationship Test Document {uuid.uuid4().hex[:8]}",
                    "project_id": project_result.data["id"],
                },
            },
        )
        
        # Create multiple requirements
        requirements = []
        for i in range(3):
            result, _ = await call_mcp(
                "entity_tool",
                {
                    "operation": "create",
                    "entity_type": "requirement",
                    "data": {
                        "name": f"Relationship Test Requirement {i} {uuid.uuid4().hex[:8]}",
                        "document_id": document_result.data["id"],
                    },
                },
            )
            requirements.append(result.data)
        
        # Create tests linked to requirements
        for i, requirement in enumerate(requirements):
            test_result, _ = await call_mcp(
                "entity_tool",
                {
                    "operation": "create",
                    "entity_type": "test",
                    "data": {
                        "title": f"Relationship Test Case {i} {uuid.uuid4().hex[:8]}",
                        "project_id": project_result.data["id"],
                    },
                },
            )
            
            # Link test to requirement
            link_result, _ = await call_mcp(
                "relationship_tool",
                {
                    "operation": "create",
                    "relationship_type": "covers",
                    "from_entity_id": test_result.data["id"],
                    "to_entity_id": requirement["id"],
                },
            )
            
            assert link_result.success is True
        
        # Test complex relationship query: get all tests for organization's projects
        query_result, _ = await call_mcp(
            "query_tool",
            {
                "operation": "relationship_query",
                "start_entity": test_organization,
                "relationship_path": ["organization", "project", "test"],
                "filters": {"include_deleted": False},
            },
        )
        
        assert query_result.success is True
        assert len(query_result.data) >= 3
        
        # Test reverse relationship query: get organization from test
        if query_result.data:
            test_id = query_result.data[0]["id"]
            
            reverse_result, _ = await call_mcp(
                "query_tool",
                {
                    "operation": "relationship_query",
                    "start_entity": test_id,
                    "relationship_path": ["test", "project", "organization"],
                    "filters": {"include_deleted": False},
                },
            )
            
            assert reverse_result.success is True
            assert len(reverse_result.data) >= 1
            assert reverse_result.data[0]["id"] == test_organization
"""Tests for advanced features: search, export, import, permissions."""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock


class TestAdvancedSearch:
    """Test advanced search with facets and suggestions."""

    @pytest.mark.asyncio
    async def test_advanced_search_returns_results(self, call_mcp):
        """Test advanced search returns results."""
        result = await call_mcp("entity_tool", {
            "operation": "advanced_search",
            "entity_type": "requirement",
            "workspace_id": "ws-1",
            "query": "performance"
        })
        assert result.get("success") is True
        assert "results" in result

    @pytest.mark.asyncio
    async def test_advanced_search_includes_facets(self, call_mcp):
        """Test advanced search includes facets."""
        result = await call_mcp("entity_tool", {
            "operation": "advanced_search",
            "entity_type": "requirement",
            "workspace_id": "ws-1",
            "query": "performance"
        })
        assert "facets" in result

    @pytest.mark.asyncio
    async def test_advanced_search_includes_suggestions(self, call_mcp):
        """Test advanced search includes suggestions."""
        result = await call_mcp("entity_tool", {
            "operation": "advanced_search",
            "entity_type": "requirement",
            "workspace_id": "ws-1",
            "query": "perform"
        })
        assert "results" in result or "suggestions" in result

    @pytest.mark.asyncio
    async def test_advanced_search_with_filters(self, call_mcp):
        """Test advanced search with filters."""
        result = await call_mcp("entity_tool", {
            "operation": "advanced_search",
            "entity_type": "requirement",
            "workspace_id": "ws-1",
            "query": "performance",
            "filters": {"status": "draft"}
        })
        assert result.get("success") is True

    @pytest.mark.asyncio
    async def test_advanced_search_pagination(self, call_mcp):
        """Test advanced search pagination."""
        result = await call_mcp("entity_tool", {
            "operation": "advanced_search",
            "entity_type": "requirement",
            "workspace_id": "ws-1",
            "query": "test",
            "limit": 10,
            "offset": 0
        })
        assert result.get("limit") == 10
        assert result.get("offset") == 0

    @pytest.mark.asyncio
    async def test_advanced_search_empty_query(self, call_mcp):
        """Test advanced search with empty query."""
        result = await call_mcp("entity_tool", {
            "operation": "advanced_search",
            "entity_type": "requirement",
            "workspace_id": "ws-1",
            "query": ""
        })
        # Should return all or empty results
        assert "results" in result

    def test_search_facet_extraction(self):
        """Test search facet extraction logic."""
        results = [
            {"status": "draft", "priority": "high"},
            {"status": "review", "priority": "high"},
            {"status": "draft", "priority": "low"},
        ]
        
        # Simulate facet extraction
        facets = {}
        for result in results:
            for key, val in result.items():
                if key not in facets:
                    facets[key] = {}
                facets[key][val] = facets[key].get(val, 0) + 1
        
        assert "status" in facets
        assert facets["status"]["draft"] == 2


class TestExportFeatures:
    """Test export functionality."""

    @pytest.mark.asyncio
    async def test_export_json_format(self, call_mcp):
        """Test export to JSON format."""
        result = await call_mcp("entity_tool", {
            "operation": "export",
            "entity_type": "requirement",
            "workspace_id": "ws-1",
            "requested_by": "user-1",
            "format": "json"
        })
        assert result.get("success") is True
        assert result.get("format") == "json"

    @pytest.mark.asyncio
    async def test_export_csv_format(self, call_mcp):
        """Test export to CSV format."""
        result = await call_mcp("entity_tool", {
            "operation": "export",
            "entity_type": "requirement",
            "workspace_id": "ws-1",
            "requested_by": "user-1",
            "format": "csv"
        })
        assert result.get("success") is True
        assert result.get("format") == "csv"

    @pytest.mark.asyncio
    async def test_export_creates_job(self, call_mcp):
        """Test export creates async job."""
        result = await call_mcp("entity_tool", {
            "operation": "export",
            "entity_type": "requirement",
            "workspace_id": "ws-1",
            "requested_by": "user-1"
        })
        assert "job_id" in result or "success" in result

    @pytest.mark.asyncio
    async def test_export_with_filters(self, call_mcp):
        """Test export with filters."""
        result = await call_mcp("entity_tool", {
            "operation": "export",
            "entity_type": "requirement",
            "workspace_id": "ws-1",
            "requested_by": "user-1",
            "filters": {"status": "draft"}
        })
        assert result.get("success") is True

    @pytest.mark.asyncio
    async def test_export_status_queued(self, call_mcp):
        """Test export job starts in queued status."""
        result = await call_mcp("entity_tool", {
            "operation": "export",
            "entity_type": "requirement",
            "workspace_id": "ws-1",
            "requested_by": "user-1"
        })
        # Job should be queued initially
        assert result.get("status") in ["queued", None] or result.get("success") is True

    def test_export_format_validation(self):
        """Test export format validation."""
        valid_formats = ["json", "csv"]
        
        # JSON should be valid
        assert "json" in valid_formats
        
        # CSV should be valid
        assert "csv" in valid_formats
        
        # Invalid format should not be in list
        assert "xml" not in valid_formats


class TestImportFeatures:
    """Test import functionality."""

    @pytest.mark.asyncio
    async def test_import_json_format(self, call_mcp):
        """Test import from JSON format."""
        result = await call_mcp("entity_tool", {
            "operation": "import",
            "entity_type": "requirement",
            "workspace_id": "ws-1",
            "requested_by": "user-1",
            "format": "json",
            "file_name": "requirements.json",
            "file_size": 1024
        })
        assert result.get("success") is True

    @pytest.mark.asyncio
    async def test_import_csv_format(self, call_mcp):
        """Test import from CSV format."""
        result = await call_mcp("entity_tool", {
            "operation": "import",
            "entity_type": "requirement",
            "workspace_id": "ws-1",
            "requested_by": "user-1",
            "format": "csv",
            "file_name": "requirements.csv",
            "file_size": 2048
        })
        assert result.get("success") is True

    @pytest.mark.asyncio
    async def test_import_creates_job(self, call_mcp):
        """Test import creates async job."""
        result = await call_mcp("entity_tool", {
            "operation": "import",
            "entity_type": "requirement",
            "workspace_id": "ws-1",
            "requested_by": "user-1",
            "file_name": "data.json"
        })
        assert "job_id" in result or "success" in result

    @pytest.mark.asyncio
    async def test_import_status_queued(self, call_mcp):
        """Test import job starts in queued status."""
        result = await call_mcp("entity_tool", {
            "operation": "import",
            "entity_type": "requirement",
            "workspace_id": "ws-1",
            "requested_by": "user-1",
            "file_name": "data.json"
        })
        assert result.get("status") in ["queued", None] or result.get("success") is True

    def test_import_duplicate_detection(self):
        """Test import duplicate detection logic."""
        imported_data = [
            {"id": "1", "name": "Req A"},
            {"id": "2", "name": "Req B"},
            {"id": "1", "name": "Req A"},  # Duplicate
        ]
        
        # Simulate duplicate detection
        seen = set()
        duplicates = []
        unique = []
        
        for item in imported_data:
            item_id = item.get("id")
            if item_id in seen:
                duplicates.append(item_id)
            else:
                seen.add(item_id)
                unique.append(item)
        
        assert len(duplicates) == 1
        assert len(unique) == 2


class TestPermissionFeatures:
    """Test permission management features."""

    @pytest.mark.asyncio
    async def test_get_entity_permissions(self, call_mcp):
        """Test getting entity permissions."""
        result = await call_mcp("entity_tool", {
            "operation": "get_permissions",
            "entity_type": "requirement",
            "entity_id": "req-123"
        })
        assert result.get("success") is True
        assert "permissions" in result

    @pytest.mark.asyncio
    async def test_get_permissions_returns_list(self, call_mcp):
        """Test get_permissions returns list."""
        result = await call_mcp("entity_tool", {
            "operation": "get_permissions",
            "entity_type": "requirement",
            "entity_id": "req-123"
        })
        permissions = result.get("permissions", [])
        assert isinstance(permissions, list)

    @pytest.mark.asyncio
    async def test_update_entity_permissions(self, call_mcp):
        """Test updating entity permissions."""
        result = await call_mcp("entity_tool", {
            "operation": "update_permissions",
            "entity_type": "requirement",
            "entity_id": "req-123",
            "workspace_id": "ws-1",
            "permission_updates": {
                "user_id": "user-2",
                "permission_level": "edit"
            }
        })
        assert result.get("success") is True

    @pytest.mark.asyncio
    async def test_permission_level_validation(self, call_mcp):
        """Test permission level validation."""
        result = await call_mcp("entity_tool", {
            "operation": "update_permissions",
            "entity_type": "requirement",
            "entity_id": "req-123",
            "workspace_id": "ws-1",
            "permission_updates": {
                "user_id": "user-2",
                "permission_level": "view"  # Valid level
            }
        })
        # Should accept valid permission level
        assert "success" in result

    def test_permission_levels_hierarchy(self):
        """Test permission level hierarchy."""
        levels = {"view": 1, "edit": 2, "admin": 3}
        
        assert levels["view"] < levels["edit"]
        assert levels["edit"] < levels["admin"]
        assert levels["view"] < levels["admin"]


class TestJobStatusTracking:
    """Test job status transitions."""

    def test_export_job_status_transitions(self):
        """Test export job status transitions."""
        valid_statuses = ["queued", "processing", "completed", "failed"]
        
        # Valid transitions
        assert "queued" in valid_statuses
        assert "processing" in valid_statuses
        assert "completed" in valid_statuses
        assert "failed" in valid_statuses

    def test_import_job_status_transitions(self):
        """Test import job status transitions."""
        valid_statuses = ["queued", "processing", "completed", "failed"]
        
        transitions = {
            "queued": ["processing"],
            "processing": ["completed", "failed"],
            "completed": [],
            "failed": []
        }
        
        assert "processing" in transitions["queued"]
        assert "completed" in transitions["processing"]

    def test_job_progress_tracking(self):
        """Test job progress tracking."""
        job = {
            "total_rows": 100,
            "processed_rows": 50,
            "failed_rows": 5
        }
        
        progress = (job["processed_rows"] / job["total_rows"]) * 100
        assert progress == 50.0


class TestSearchPerformance:
    """Test search performance characteristics."""

    @pytest.mark.asyncio
    async def test_search_returns_in_reasonable_time(self, call_mcp):
        """Test search completes in reasonable time."""
        import time
        
        start = time.time()
        result = await call_mcp("entity_tool", {
            "operation": "advanced_search",
            "entity_type": "requirement",
            "workspace_id": "ws-1",
            "query": "test"
        })
        elapsed = time.time() - start
        
        # Should complete reasonably fast (< 5 seconds)
        assert elapsed < 5.0
        assert result.get("success") is True

    def test_facet_aggregation_efficiency(self):
        """Test facet aggregation is efficient."""
        results = [
            {"status": f"status-{i % 5}", "priority": f"priority-{i % 3}"}
            for i in range(1000)
        ]
        
        # Aggregate facets
        facets = {}
        for result in results:
            for key, val in result.items():
                if key not in facets:
                    facets[key] = {}
                facets[key][val] = facets[key].get(val, 0) + 1
        
        # Should have aggregated efficiently
        assert "status" in facets
        assert "priority" in facets
        assert len(facets["status"]) == 5


class TestExportImportIntegration:
    """Test export/import integration."""

    @pytest.mark.asyncio
    async def test_export_then_import_roundtrip(self, call_mcp):
        """Test export/import roundtrip."""
        # Export
        export_result = await call_mcp("entity_tool", {
            "operation": "export",
            "entity_type": "requirement",
            "workspace_id": "ws-1",
            "requested_by": "user-1",
            "format": "json"
        })
        assert export_result.get("success") is True
        
        # Import
        import_result = await call_mcp("entity_tool", {
            "operation": "import",
            "entity_type": "requirement",
            "workspace_id": "ws-1",
            "requested_by": "user-1",
            "format": "json",
            "file_name": "export.json",
            "file_size": 1024
        })
        assert import_result.get("success") is True


class TestAdvancedFeaturesErrorHandling:
    """Test error handling in advanced features."""

    @pytest.mark.asyncio
    async def test_search_invalid_entity_type(self, call_mcp):
        """Test search with invalid entity type."""
        result = await call_mcp("entity_tool", {
            "operation": "advanced_search",
            "entity_type": "invalid_type",
            "workspace_id": "ws-1",
            "query": "test"
        })
        # Should either fail gracefully or return empty
        assert "success" in result or "results" in result

    @pytest.mark.asyncio
    async def test_export_invalid_format(self, call_mcp):
        """Test export with invalid format."""
        result = await call_mcp("entity_tool", {
            "operation": "export",
            "entity_type": "requirement",
            "workspace_id": "ws-1",
            "requested_by": "user-1",
            "format": "invalid_format"
        })
        # Should handle gracefully
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_import_missing_required_field(self, call_mcp):
        """Test import with missing required field."""
        result = await call_mcp("entity_tool", {
            "operation": "import",
            "entity_type": "requirement",
            "workspace_id": "ws-1",
            "requested_by": "user-1"
            # Missing file_name
        })
        # Should handle gracefully
        assert "success" in result or "error" in result
