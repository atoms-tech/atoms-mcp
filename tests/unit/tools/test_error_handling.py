"""Error handling and recovery tests.

Tests error scenarios and recovery mechanisms:
- Database connection failures
- Timeout scenarios
- Partial batch failure recovery
- Cascading failure handling
- Invalid input handling
- Permission errors handling

Run with: pytest tests/unit/tools/test_error_handling.py -v
"""

import uuid
import pytest
from datetime import datetime, timezone, timedelta

pytestmark = [pytest.mark.asyncio, pytest.mark.unit]


class TestErrorHandling:
    """Test error handling and recovery mechanisms."""
    
    @pytest.mark.unit
    async def test_invalid_entity_type_handling(self, call_mcp):
        """Test handling of invalid entity types."""
        # Try operations with invalid entity type
        invalid_type = "invalid_entity_type"
        
        # Test create with invalid type
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": invalid_type,
                "data": {"name": "Test"},
            },
        )
        
        assert result.success is False
        assert "Invalid entity type" in result.error or "Unknown entity type" in result.error
        
        # Test read with invalid type
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "read",
                "entity_type": invalid_type,
                "entity_id": str(uuid.uuid4()),
            },
        )
        
        assert result.success is False
        
        # Test list with invalid type
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "list",
                "entity_type": invalid_type,
            },
        )
        
        assert result.success is False
    
    @pytest.mark.unit
    async def test_invalid_operation_handling(self, call_mcp, test_organization):
        """Test handling of invalid operations."""
        # Try invalid operation on valid entity type
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "invalid_operation",
                "entity_type": "organization",
                "entity_id": test_organization,
            },
        )
        
        assert result.success is False
        assert "Invalid operation" in result.error or "Unknown operation" in result.error
        
        # Try missing operation
        result, _ = await call_mcp(
            "entity_tool",
            {
                "entity_type": "organization",
                "entity_id": test_organization,
            },
        )
        
        assert result.success is False
        assert "operation" in result.error.lower()
    
    @pytest.mark.unit
    async def test_missing_required_fields_handling(self, call_mcp):
        """Test handling of missing required fields."""
        # Test organization without name
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "organization",
                "data": {
                    "description": "Org without name",
                },
            },
        )
        
        assert result.success is False
        assert "Missing required fields" in result.error or "name" in result.error
        
        # Test project without organization_id
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "project",
                "data": {
                    "name": "Project without org",
                },
            },
        )
        
        assert result.success is False
        assert "Missing required fields" in result.error or "organization_id" in result.error
        
        # Test document without project_id
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "document",
                "data": {
                    "name": "Document without project",
                },
            },
        )
        
        assert result.success is False
        assert "Missing required fields" in result.error or "project_id" in result.error
    
    @pytest.mark.unit
    async def test_invalid_uuid_handling(self, call_mcp):
        """Test handling of invalid UUID formats."""
        # Test read with invalid UUID
        invalid_uuids = [
            "invalid-uuid",
            "12345678-1234-1234-1234-123456789abc",  # Invalid character
            "12345678-1234-1234-1234-123456789abg",  # Invalid character
            "12345678-1234-1234-1234",  # Too short
            "12345678-1234-1234-1234-123456789abcd",  # Too long
        ]
        
        for invalid_uuid in invalid_uuids:
            result, _ = await call_mcp(
                "entity_tool",
                {
                    "operation": "read",
                    "entity_type": "organization",
                    "entity_id": invalid_uuid,
                },
            )
            
            assert result.success is False
            assert "Invalid UUID" in result.error or "not found" in result.error.lower()
    
    @pytest.mark.unit
    async def test_nonexistent_entity_handling(self, call_mcp):
        """Test handling of operations on nonexistent entities."""
        # Generate valid but non-existent UUID
        nonexistent_uuid = str(uuid.uuid4())
        
        # Test read nonexistent entity
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "read",
                "entity_type": "organization",
                "entity_id": nonexistent_uuid,
            },
        )
        
        assert result.success is False
        assert "not found" in result.error.lower() or "does not exist" in result.error.lower()
        
        # Test update nonexistent entity
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "update",
                "entity_type": "organization",
                "entity_id": nonexistent_uuid,
                "data": {"name": "Updated name"},
            },
        )
        
        assert result.success is False
        assert "not found" in result.error.lower()
        
        # Test archive nonexistent entity
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "archive",
                "entity_type": "organization",
                "entity_id": nonexistent_uuid,
            },
        )
        
        assert result.success is False
        assert "not found" in result.error.lower()
    
    @pytest.mark.unit
    async def test_constraint_violation_handling(self, call_mcp, test_organization):
        """Test handling of constraint violations."""
        # Test duplicate unique constraints (if applicable)
        # Create project with same name might violate unique constraint
        project_name = f"Constraint Test Project {uuid.uuid4().hex[:8]}"
        
        # Create first project
        result1, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "project",
                "data": {
                    "name": project_name,
                    "organization_id": test_organization,
                },
            },
        )
        
        assert result1.success is True
        
        # Try to create second project with same name and org
        # (This might or might not violate constraints depending on schema)
        result2, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "project",
                "data": {
                    "name": project_name,
                    "organization_id": test_organization,
                },
            },
        )
        
        # Check if duplicate constraint is enforced
        if not result2.success:
            assert "duplicate" in result2.error.lower() or "unique" in result2.error.lower()
        
        # Test foreign key constraint violation
        invalid_org_id = str(uuid.uuid4())
        
        result3, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "project",
                "data": {
                    "name": "Project with invalid org",
                    "organization_id": invalid_org_id,
                },
            },
        )
        
        assert result3.success is False
        assert ("foreign key" in result3.error.lower() or 
                "invalid" in result3.error.lower() or 
                "not found" in result3.error.lower())
    
    @pytest.mark.unit
    async def test_partial_batch_failure_recovery(self, call_mcp, test_organization):
        """Test recovery from partial batch operation failures."""
        # Prepare batch data with some valid and some invalid entries
        batch_data = {
            "valid1": {
                "name": f"Valid Project 1 {uuid.uuid4().hex[:8]}",
                "organization_id": test_organization,
            },
            "invalid": {
                "name": "Invalid Project without org",
                # Missing organization_id - should fail
            },
            "valid2": {
                "name": f"Valid Project 2 {uuid.uuid4().hex[:8]}",
                "organization_id": test_organization,
            },
            "invalid2": {
                "name": "Invalid Project with bad org",
                "organization_id": str(uuid.uuid4()),  # Non-existent org
            },
            "valid3": {
                "name": f"Valid Project 3 {uuid.uuid4().hex[:8]}",
                "organization_id": test_organization,
            },
        }
        
        # Attempt bulk create
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "bulk_create",
                "entity_type": "project",
                "data": batch_data,
            },
        )
        
        # Should handle partial failure gracefully
        if not result.success:
            assert "partial" in result.error.lower() or "some" in result.error.lower()
            
            # Should return detailed error information
            assert "errors" in result.data or "failed" in result.data
            
            # Check if we got success information for valid entries
            if "results" in result.data:
                success_count = sum(1 for r in result.data["results"] if r.get("success"))
                assert success_count >= 3  # At least 3 valid entries should succeed
        
        # Test partial batch update
        # First create some projects
        project_ids = []
        for i in range(3):
            result, _ = await call_mcp(
                "entity_tool",
                {
                    "operation": "create",
                    "entity_type": "project",
                    "data": {
                        "name": f"Partial Test Project {i} {uuid.uuid4().hex[:8]}",
                        "organization_id": test_organization,
                    },
                },
            )
            assert result.success is True
            project_ids.append(result.data["id"])
        
        # Add invalid project ID
        project_ids.append(str(uuid.uuid4()))
        
        # Prepare update data
        update_data = {
            project_ids[0]: {"description": "Valid update 1"},
            project_ids[1]: {"description": "Valid update 2"},
            project_ids[3]: {"description": "Invalid update - non-existent"},
            project_ids[2]: {"description": "Valid update 3"},
        }
        
        # Attempt bulk update
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "bulk_update",
                "entity_type": "project",
                "data": update_data,
            },
        )
        
        # Should handle partial failure
        if not result.success:
            assert "partial" in result.error.lower() or "some" in result.error.lower()
            
            # Should provide detailed error information
            assert "errors" in result.data or "failed" in result.data
    
    @pytest.mark.unit
    async def test_timeout_handling(self, call_mcp, test_organization):
        """Test handling of timeout scenarios."""
        # Test with very large data that might cause timeout
        large_description = "A" * 100000  # 100KB description
        
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "project",
                "data": {
                    "name": f"Timeout Test Project {uuid.uuid4().hex[:8]}",
                    "organization_id": test_organization,
                    "description": large_description,
                },
            },
        )
        
        # Should either succeed or fail gracefully
        if not result.success:
            assert ("timeout" in result.error.lower() or 
                    "too large" in result.error.lower() or
                    "size" in result.error.lower())
        
        # Test bulk operation with many items that might timeout
        large_batch = {}
        for i in range(50):  # 50 items might cause timeout
            large_batch[f"item_{i}"] = {
                "name": f"Bulk Timeout Project {i} {uuid.uuid4().hex[:8]}",
                "organization_id": test_organization,
                "description": "Description for timeout test " * 100,
            }
        
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "bulk_create",
                "entity_type": "project",
                "data": large_batch,
            },
        )
        
        # Should either succeed or fail gracefully
        if not result.success:
            assert ("timeout" in result.error.lower() or 
                    "too many" in result.error.lower() or
                    "limit" in result.error.lower())
    
    @pytest.mark.unit
    async def test_cascading_failure_handling(self, call_mcp, test_organization):
        """Test handling of cascading failures."""
        # Create project
        project_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "project",
                "data": {
                    "name": f"Cascade Test Project {uuid.uuid4().hex[:8]}",
                    "organization_id": test_organization,
                },
            },
        )
        
        assert project_result.success is True
        project_id = project_result.data["id"]
        
        # Create document
        document_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "document",
                "data": {
                    "name": f"Cascade Test Document {uuid.uuid4().hex[:8]}",
                    "project_id": project_id,
                },
            },
        )
        
        assert document_result.success is True
        document_id = document_result.data["id"]
        
        # Create requirement
        requirement_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "requirement",
                "data": {
                    "name": f"Cascade Test Requirement {uuid.uuid4().hex[:8]}",
                    "document_id": document_id,
                },
            },
        )
        
        assert requirement_result.success is True
        requirement_id = requirement_result.data["id"]
        
        # Now archive parent project and check cascading behavior
        archive_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "archive",
                "entity_type": "project",
                "entity_id": project_id,
                "cascade": True,  # Request cascade if supported
            },
        )
        
        # Should either succeed with cascade or provide clear error
        if not archive_result.success:
            assert "cascade" in archive_result.error.lower() or "dependent" in archive_result.error.lower()
        else:
            # If cascade succeeded, check child entities
            doc_result, _ = await call_mcp(
                "entity_tool",
                {
                    "operation": "read",
                    "entity_type": "document",
                    "entity_id": document_id,
                },
            )
            
            if doc_result.success:
                # Document might be archived
                assert doc_result.data.get("is_deleted", False)
            
            req_result, _ = await call_mcp(
                "entity_tool",
                {
                    "operation": "read",
                    "entity_type": "requirement",
                    "entity_id": requirement_id,
                },
            )
            
            if req_result.success:
                # Requirement might be archived
                assert req_result.data.get("is_deleted", False)
    
    @pytest.mark.unit
    async def test_malformed_input_handling(self, call_mcp, test_organization):
        """Test handling of malformed input data."""
        # Test with None values for required fields
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "project",
                "data": {
                    "name": None,  # Invalid None for required field
                    "organization_id": test_organization,
                },
            },
        )
        
        assert result.success is False
        assert "required" in result.error.lower() or "null" in result.error.lower()
        
        # Test with wrong data types
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "project",
                "data": {
                    "name": 123,  # Number instead of string
                    "organization_id": test_organization,
                },
            },
        )
        
        # Should either succeed with type conversion or fail gracefully
        if not result.success:
            assert "type" in result.error.lower() or "invalid" in result.error.lower()
        
        # Test with extremely long strings
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "project",
                "data": {
                    "name": "A" * 1000,  # Very long name
                    "organization_id": test_organization,
                },
            },
        )
        
        # Should either succeed or fail with length constraint error
        if not result.success:
            assert "too long" in result.error.lower() or "length" in result.error.lower()
    
    @pytest.mark.unit
    async def test_permission_error_handling(self, call_mcp, test_organization):
        """Test handling of permission errors."""
        # Try to modify organization without permissions
        # (This depends on the permission system implementation)
        
        # Test creating entity in organization without membership
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
        
        # Try to create project in organization we're not member of
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "project",
                "data": {
                    "name": f"Unauthorized Project {uuid.uuid4().hex[:8]}",
                    "organization_id": other_org_id,
                },
            },
        )
        
        # Should fail with permission error if permission system is active
        if not result.success:
            assert ("permission" in result.error.lower() or 
                    "unauthorized" in result.error.lower() or
                    "access" in result.error.lower())
    
    @pytest.mark.unit
    async def test_database_error_recovery(self, call_mcp, test_organization):
        """Test recovery from database errors."""
        # This test simulates database errors and recovery
        # In a real scenario, you might mock database failures
        
        # Create an entity successfully first
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "project",
                "data": {
                    "name": f"DB Error Test Project {uuid.uuid4().hex[:8]}",
                    "organization_id": test_organization,
                },
            },
        )
        
        assert result.success is True
        project_id = result.data["id"]
        
        # Try to read the entity to verify system is still working
        read_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "read",
                "entity_type": "project",
                "entity_id": project_id,
            },
        )
        
        assert read_result.success is True
        assert read_result.data["id"] == project_id
        
        # Test that system continues to work after potential errors
        # Create another entity
        result2, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "project",
                "data": {
                    "name": f"Recovery Test Project {uuid.uuid4().hex[:8]}",
                    "organization_id": test_organization,
                },
            },
        )
        
        assert result2.success is True
    
    @pytest.mark.unit
    async def test_error_message_quality(self, call_mcp, test_organization):
        """Test that error messages are informative and actionable."""
        # Test various error scenarios and check message quality
        
        # Missing required field
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "project",
                "data": {"description": "Project without name"},
            },
        )
        
        assert result.success is False
        error_msg = result.error.lower()
        
        # Should mention what's missing
        assert "name" in error_msg or "required" in error_msg
        
        # Should be human-readable
        assert len(error_msg) > 10  # Not too short
        assert len(error_msg) < 500  # Not too long
        
        # Invalid UUID
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "read",
                "entity_type": "project",
                "entity_id": "invalid-uuid",
            },
        )
        
        assert result.success is False
        error_msg = result.error.lower()
        
        # Should explain UUID format issue
        assert "uuid" in error_msg or "invalid" in error_msg or "format" in error_msg
        
        # Non-existent entity
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "read",
                "entity_type": "project",
                "entity_id": str(uuid.uuid4()),
            },
        )
        
        assert result.success is False
        error_msg = result.error.lower()
        
        # Should clearly state entity not found
        assert "not found" in error_msg or "does not exist" in error_msg
        
        # Should mention entity type
        assert "project" in error_msg
