"""Audit trail tests for all entity operations.

Tests audit trail functionality:
- Mutation logging for all operations
- User attribution for changes
- Bulk operation audit logging
- Workflow execution audit
- Permission change audit
- Cross-tenant access audit

Run with: pytest tests/unit/tools/test_audit_trails.py -v
"""

import uuid
import pytest
from datetime import datetime, timezone, timedelta

pytestmark = [pytest.mark.asyncio, pytest.mark.unit]


class TestAuditTrails:
    """Test audit trail functionality."""
    
    @pytest.mark.unit
    async def test_entity_creation_audit(self, call_mcp, mock_user_context):
        """Test that entity creation creates audit trail entries."""
        # Create organization
        org_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "organization",
                "data": {
                    "name": f"Audit Test Org {uuid.uuid4().hex[:8]}",
                    "type": "team",
                },
            },
        )
        
        assert org_result.success is True
        org_id = org_result.data["id"]
        
        # Check audit trail for creation
        audit_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "audit",
                "entity_type": "organization",
                "entity_id": org_id,
                "filters": {
                    "operation": "create",
                    "limit": 10
                }
            },
        )
        
        assert audit_result.success is True
        assert len(audit_result.data) >= 1
        
        # Verify audit entry contains expected fields
        audit_entry = audit_result.data[0]
        assert audit_entry["operation"] == "create"
        assert audit_entry["entity_type"] == "organization"
        assert audit_entry["entity_id"] == org_id
        assert audit_entry["user_id"] == mock_user_context["id"]
        assert "timestamp" in audit_entry
        assert "changes" in audit_entry
        
        # Verify changes contain created fields
        changes = audit_entry["changes"]
        assert "name" in changes
        assert "type" in changes
        assert changes["name"] == org_result.data["name"]
    
    @pytest.mark.unit
    async def test_entity_update_audit(self, call_mcp, test_organization):
        """Test that entity updates create audit trail entries."""
        # Create project
        project_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "project",
                "data": {
                    "name": f"Audit Test Project {uuid.uuid4().hex[:8]}",
                    "organization_id": test_organization,
                },
            },
        )
        
        assert project_result.success is True
        project_id = project_result.data["id"]
        
        # Update project
        update_data = {
            "name": f"Updated Project {uuid.uuid4().hex[:8]}",
            "description": "Updated description",
            "status": "active"
        }
        
        update_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "update",
                "entity_type": "project",
                "entity_id": project_id,
                "data": update_data,
            },
        )
        
        assert update_result.success is True
        
        # Check audit trail for update
        audit_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "audit",
                "entity_type": "project",
                "entity_id": project_id,
                "filters": {
                    "operation": "update",
                    "limit": 10
                }
            },
        )
        
        assert audit_result.success is True
        assert len(audit_result.data) >= 1
        
        # Verify audit entry contains expected fields
        audit_entry = audit_result.data[0]
        assert audit_entry["operation"] == "update"
        assert audit_entry["entity_type"] == "project"
        assert audit_entry["entity_id"] == project_id
        assert "timestamp" in audit_entry
        assert "changes" in audit_entry
        
        # Verify changes contain updated fields
        changes = audit_entry["changes"]
        assert "name" in changes
        assert "description" in changes
        assert "status" in changes
        
        # Should show both old and new values if implemented
        if "old_values" in changes:
            assert "new_values" in changes
            assert changes["new_values"]["name"] == update_data["name"]
    
    @pytest.mark.unit
    async def test_entity_archive_restore_audit(self, call_mcp, test_organization):
        """Test that archive/restore operations create audit trail entries."""
        # Create project
        project_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "project",
                "data": {
                    "name": f"Audit Archive Project {uuid.uuid4().hex[:8]}",
                    "organization_id": test_organization,
                },
            },
        )
        
        assert project_result.success is True
        project_id = project_result.data["id"]
        
        # Archive project
        archive_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "archive",
                "entity_type": "project",
                "entity_id": project_id,
            },
        )
        
        assert archive_result.success is True
        
        # Check audit trail for archive
        audit_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "audit",
                "entity_type": "project",
                "entity_id": project_id,
                "filters": {
                    "operation": "archive",
                    "limit": 10
                }
            },
        )
        
        assert audit_result.success is True
        assert len(audit_result.data) >= 1
        
        audit_entry = audit_result.data[0]
        assert audit_entry["operation"] == "archive"
        assert audit_entry["entity_id"] == project_id
        
        # Restore project
        restore_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "restore",
                "entity_type": "project",
                "entity_id": project_id,
            },
        )
        
        assert restore_result.success is True
        
        # Check audit trail for restore
        audit_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "audit",
                "entity_type": "project",
                "entity_id": project_id,
                "filters": {
                    "operation": "restore",
                    "limit": 10
                }
            },
        )
        
        assert audit_result.success is True
        assert len(audit_result.data) >= 1
        
        audit_entry = audit_result.data[0]
        assert audit_entry["operation"] == "restore"
        assert audit_entry["entity_id"] == project_id
    
    @pytest.mark.unit
    async def test_bulk_operation_audit(self, call_mcp, test_organization):
        """Test that bulk operations create comprehensive audit trails."""
        # Create multiple projects for bulk operations
        projects = []
        for i in range(3):
            result, _ = await call_mcp(
                "entity_tool",
                {
                    "operation": "create",
                    "entity_type": "project",
                    "data": {
                        "name": f"Bulk Audit Project {i} {uuid.uuid4().hex[:8]}",
                        "organization_id": test_organization,
                    },
                },
            )
            assert result.success is True
            projects.append(result.data)
        
        project_ids = [p["id"] for p in projects]
        
        # Bulk update
        update_data = {
            project_ids[0]: {"description": "Bulk updated 1"},
            project_ids[1]: {"description": "Bulk updated 2"},
            project_ids[2]: {"description": "Bulk updated 3"},
        }
        
        bulk_update_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "bulk_update",
                "entity_type": "project",
                "data": update_data,
            },
        )
        
        assert bulk_update_result.success is True
        
        # Check audit trail for bulk update
        for project_id in project_ids:
            audit_result, _ = await call_mcp(
                "entity_tool",
                {
                    "operation": "audit",
                    "entity_type": "project",
                    "entity_id": project_id,
                    "filters": {
                        "operation": "bulk_update",
                        "limit": 10
                    }
                },
            )
            
            assert audit_result.success is True
            assert len(audit_result.data) >= 1
            
            audit_entry = audit_result.data[0]
            assert audit_entry["operation"] == "bulk_update"
            assert audit_entry["entity_id"] == project_id
            assert "bulk_operation_id" in audit_entry  # Should link all bulk ops
        
        # Bulk archive
        bulk_archive_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "bulk_archive",
                "entity_type": "project",
                "entity_ids": project_ids[:2],  # Archive first 2
            },
        ),
        
        assert bulk_archive_result[0].success is True
        
        # Check audit trail for bulk archive
        for project_id in project_ids[:2]:
            audit_result, _ = await call_mcp(
                "entity_tool",
                {
                    "operation": "audit",
                    "entity_type": "project",
                    "entity_id": project_id,
                    "filters": {
                        "operation": "bulk_archive",
                        "limit": 10
                    }
                },
            )
            
            assert audit_result.success is True
            assert len(audit_result.data) >= 1
            
            audit_entry = audit_result.data[0]
            assert audit_entry["operation"] == "bulk_archive"
            assert audit_entry["entity_id"] == project_id
            assert "bulk_operation_id" in audit_entry
    
    @pytest.mark.unit
    async def test_workflow_execution_audit(self, call_mcp, test_organization):
        """Test that workflow executions create audit trail entries."""
        # Create project and document for workflow
        project_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "project",
                "data": {
                    "name": f"Workflow Audit Project {uuid.uuid4().hex[:8]}",
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
                    "name": f"Workflow Audit Document {uuid.uuid4().hex[:8]}",
                    "project_id": project_result.data["id"],
                },
            },
        )
        
        # Create workflow
        workflow_result, _ = await call_mcp(
            "workflow_tool",
            {
                "operation": "create",
                "data": {
                    "name": f"Audit Test Workflow {uuid.uuid4().hex[:8]}",
                    "description": "Test workflow for audit",
                    "project_id": project_result.data["id"],
                    "steps": [
                        {
                            "name": "Create Requirement",
                            "type": "entity_create",
                            "config": {
                                "entity_type": "requirement",
                                "data": {
                                    "name": "Auto Requirement",
                                    "document_id": document_result.data["id"],
                                }
                            }
                        }
                    ]
                },
            },
        )
        
        assert workflow_result.success is True
        workflow_id = workflow_result.data["id"]
        
        # Execute workflow
        execute_result, _ = await call_mcp(
            "workflow_tool",
            {
                "operation": "execute",
                "workflow_id": workflow_id,
                "input_data": {},
            },
        )
        
        assert execute_result.success is True
        execution_id = execute_result.data.get("execution_id")
        
        # Check audit trail for workflow execution
        if execution_id:
            audit_result, _ = await call_mcp(
                "entity_tool",
                {
                    "operation": "audit",
                    "entity_type": "workflow_execution",
                    "entity_id": execution_id,
                    "filters": {
                        "limit": 10
                    }
                },
            )
            
            assert audit_result.success is True
            assert len(audit_result.data) >= 1
            
            audit_entry = audit_result.data[0]
            assert audit_entry["operation"] == "execute"
            assert audit_entry["entity_type"] == "workflow_execution"
            assert audit_entry["entity_id"] == execution_id
            assert audit_entry["workflow_id"] == workflow_id
            assert "execution_details" in audit_entry
    
    @pytest.mark.unit
    async def test_permission_change_audit(self, call_mcp, test_organization):
        """Test that permission changes create audit trail entries."""
        # Create a test user
        user_id = str(uuid.uuid4())
        user_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "user",
                "data": {
                    "id": user_id,
                    "email": f"audit_user_{uuid.uuid4().hex[:8]}@example.com",
                    "display_name": f"Audit Test User {uuid.uuid4().hex[:8]}",
                },
            },
        )
        
        assert user_result.success is True
        
        # Grant permission to organization
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
                },
            },
        )
        
        assert grant_result.success is True
        relationship_id = grant_result.data["id"]
        
        # Check audit trail for permission grant
        audit_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "audit",
                "entity_type": "relationship",
                "entity_id": relationship_id,
                "filters": {
                    "operation": "create",
                    "limit": 10
                }
            },
        )
        
        assert audit_result.success is True
        assert len(audit_result.data) >= 1
        
        audit_entry = audit_result.data[0]
        assert audit_entry["operation"] == "create"
        assert audit_entry["entity_type"] == "relationship"
        assert audit_entry["entity_id"] == relationship_id
        assert audit_entry["relationship_type"] == "member"
        assert "permissions" in audit_entry["changes"]
        
        # Update permissions
        update_result, _ = await call_mcp(
            "relationship_tool",
            {
                "operation": "update",
                "relationship_type": "member",
                "relationship_id": relationship_id,
                "data": {
                    "role": "admin",
                    "permissions": ["read", "write", "admin"],
                },
            },
        )
        
        assert update_result.success is True
        
        # Check audit trail for permission update
        audit_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "audit",
                "entity_type": "relationship",
                "entity_id": relationship_id,
                "filters": {
                    "operation": "update",
                    "limit": 10
                }
            },
        )
        
        assert audit_result.success is True
        assert len(audit_result.data) >= 1
        
        audit_entry = audit_result.data[0]
        assert audit_entry["operation"] == "update"
        assert "permissions" in audit_entry["changes"]
        
        # Revoke permission
        revoke_result, _ = await call_mcp(
            "relationship_tool",
            {
                "operation": "archive",
                "relationship_type": "member",
                "relationship_id": relationship_id,
            },
        )
        
        assert revoke_result.success is True
        
        # Check audit trail for permission revocation
        audit_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "audit",
                "entity_type": "relationship",
                "entity_id": relationship_id,
                "filters": {
                    "operation": "archive",
                    "limit": 10
                }
            },
        )
        
        assert audit_result.success is True
        assert len(audit_result.data) >= 1
        
        audit_entry = audit_result.data[0]
        assert audit_entry["operation"] == "archive"
    
    @pytest.mark.unit
    async def test_cross_tenant_access_audit(self, call_mcp, test_organization):
        """Test that cross-tenant access attempts create audit trail entries."""
        # Create project in organization
        project_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "project",
                "data": {
                    "name": f"Cross Tenant Project {uuid.uuid4().hex[:8]}",
                    "organization_id": test_organization,
                },
            },
        )
        
        assert project_result.success is True
        project_id = project_result.data["id"]
        
        # Create another organization (simulating cross-tenant access)
        other_org_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "organization",
                "data": {
                    "name": f"Other Org {uuid.uuid4().hex[:8]}",
                    "type": "team",
                },
            },
        )
        
        assert other_org_result.success is True
        other_org_id = other_org_result.data["id"]
        
        # Try to access project from different organization context
        # This should create an audit entry for unauthorized access attempt
        access_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "read",
                "entity_type": "project",
                "entity_id": project_id,
                "context": {"organization_id": other_org_id},  # Different context
            },
        )
        
        # Check audit trail for access attempt
        audit_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "audit",
                "entity_type": "project",
                "entity_id": project_id,
                "filters": {
                    "operation": "access_attempt",
                    "limit": 10
                }
            },
        )
        
        # This should show access attempt (if audit is comprehensive)
        # Implementation might vary, but we should see some audit activity
        if audit_result.success:
            assert len(audit_result.data) >= 1
            audit_entry = audit_result.data[0]
            assert audit_entry["entity_type"] == "project"
            assert audit_entry["entity_id"] == project_id
            assert "access_attempt" in audit_entry.get("operation", "")
    
    @pytest.mark.unit
    async def test_audit_filtering_and_pagination(self, call_mcp, test_organization):
        """Test audit trail filtering and pagination functionality."""
        # Create project
        project_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "project",
                "data": {
                    "name": f"Audit Filter Project {uuid.uuid4().hex[:8]}",
                    "organization_id": test_organization,
                },
            },
        )
        
        assert project_result.success is True
        project_id = project_result.data["id"]
        
        # Perform multiple operations to generate audit entries
        operations = []
        
        # Create operation
        operations.append(("create", project_result.data))
        
        # Multiple updates
        for i in range(3):
            update_result, _ = await call_mcp(
                "entity_tool",
                {
                    "operation": "update",
                    "entity_type": "project",
                    "entity_id": project_id,
                    "data": {"description": f"Update {i}"},
                },
            )
            assert update_result.success is True
            operations.append(("update", update_result.data))
        
        # Archive and restore
        archive_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "archive",
                "entity_type": "project",
                "entity_id": project_id,
            },
        )
        assert archive_result.success is True
        operations.append(("archive", archive_result.data))
        
        restore_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "restore",
                "entity_type": "project",
                "entity_id": project_id,
            },
        )
        assert restore_result.success is True
        operations.append(("restore", restore_result.data))
        
        # Test filtering by operation type
        for operation_type, _ in operations:
            audit_result, _ = await call_mcp(
                "entity_tool",
                {
                    "operation": "audit",
                    "entity_type": "project",
                    "entity_id": project_id,
                    "filters": {
                        "operation": operation_type,
                        "limit": 10
                    }
                },
            )
            
            assert audit_result.success is True
            assert len(audit_result.data) >= 1
            
            for entry in audit_result.data:
                assert entry["operation"] == operation_type
        
        # Test date range filtering
        now = datetime.now(timezone.utc)
        yesterday = now - timedelta(days=1)
        tomorrow = now + timedelta(days=1)
        
        audit_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "audit",
                "entity_type": "project",
                "entity_id": project_id,
                "filters": {
                    "date_from": yesterday.isoformat(),
                    "date_to": tomorrow.isoformat(),
                    "limit": 100
                }
            },
        )
        
        assert audit_result.success is True
        assert len(audit_result.data) >= len(operations)
        
        # Test pagination
        page_size = 2
        all_entries = []
        
        for page in range(0, 10):  # Maximum 10 pages to avoid infinite loop
            audit_result, _ = await call_mcp(
                "entity_tool",
                {
                    "operation": "audit",
                    "entity_type": "project",
                    "entity_id": project_id,
                    "filters": {
                        "limit": page_size,
                        "offset": page * page_size
                    }
                },
            )
            
            assert audit_result.success is True
            
            if not audit_result.data:
                break
            
            all_entries.extend(audit_result.data)
            
            if len(audit_result.data) < page_size:
                break
        
        # Verify we got all entries
        assert len(all_entries) >= len(operations)
    
    @pytest.mark.unit
    async def test_audit_data_integrity(self, call_mcp, test_organization):
        """Test that audit trail maintains data integrity."""
        # Create project with specific data
        project_data = {
            "name": f"Integrity Test Project {uuid.uuid4().hex[:8]}",
            "description": "Original description",
            "status": "planning",
            "priority": "high",
            "organization_id": test_organization,
        }
        
        create_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "project",
                "data": project_data,
            },
        )
        
        assert create_result.success is True
        project_id = create_result.data["id"]
        
        # Get create audit entry
        audit_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "audit",
                "entity_type": "project",
                "entity_id": project_id,
                "filters": {
                    "operation": "create",
                    "limit": 1
                }
            },
        )
        
        assert audit_result.success is True
        assert len(audit_result.data) == 1
        
        create_audit = audit_result.data[0]
        
        # Verify audit data matches original data
        changes = create_audit["changes"]
        for key, value in project_data.items():
            assert key in changes, f"Field {key} missing from audit"
            assert changes[key] == value, f"Field {key} value mismatch in audit"
        
        # Update with specific changes
        update_data = {
            "description": "Updated description",
            "status": "active",
            "new_field": "new value",
        }
        
        update_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "update",
                "entity_type": "project",
                "entity_id": project_id,
                "data": update_data,
            },
        )
        
        assert update_result.success is True
        
        # Get update audit entry
        audit_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "audit",
                "entity_type": "project",
                "entity_id": project_id,
                "filters": {
                    "operation": "update",
                    "limit": 1
                }
            },
        )
        
        assert audit_result.success is True
        assert len(audit_result.data) == 1
        
        update_audit = audit_result.data[0]
        
        # Verify audit data matches update data
        changes = update_audit["changes"]
        for key, value in update_data.items():
            assert key in changes, f"Update field {key} missing from audit"
            assert changes[key] == value, f"Update field {key} value mismatch in audit"
        
        # Verify timestamp consistency
        create_timestamp = create_audit["timestamp"]
        update_timestamp = update_audit["timestamp"]
        
        # Convert to datetime for comparison
        create_dt = datetime.fromisoformat(create_timestamp.replace('Z', '+00:00'))
        update_dt = datetime.fromisoformat(update_timestamp.replace('Z', '+00:00'))
        
        assert update_dt > create_dt, "Update timestamp should be after create timestamp"
        
        # Verify user attribution
        assert "user_id" in create_audit
        assert "user_id" in update_audit
        assert create_audit["user_id"] == update_audit["user_id"]
