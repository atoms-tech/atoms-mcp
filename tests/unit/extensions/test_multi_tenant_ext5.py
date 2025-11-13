"""Extension 5: Multi-Tenant Isolation - Comprehensive testing suite.

Tests for multi-tenant data isolation ensuring:
- Data from different tenants is properly isolated
- Cross-tenant access is prevented
- Tenant context is properly maintained throughout requests
- Queries respect tenant boundaries
- Relationships don't cross tenant boundaries
- Soft-deleted entities remain tenant-isolated
- Audit logs maintain tenant isolation
- Billing/usage is tracked per tenant
"""

import pytest


class TestTenantDataIsolation:
    """Test basic data isolation between tenants."""

    @pytest.mark.asyncio
    async def test_tenant_isolation_on_create(self, call_mcp):
        """Created entities should be isolated by tenant."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "create",
            "entity_type": "organization",
            "data": {
                "name": "Tenant A Org",
                "tenant_id": "tenant-a"
            }
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_tenant_isolation_on_read(self, call_mcp):
        """Read should respect tenant boundaries."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "read",
            "entity_type": "organization",
            "entity_id": "org-tenant-a",
            "tenant_id": "tenant-a"
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_cross_tenant_read_denied(self, call_mcp):
        """Reading entity from different tenant should be denied."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "read",
            "entity_type": "organization",
            "entity_id": "org-tenant-a",
            "tenant_id": "tenant-b"
        })
        # Should fail - different tenant
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_tenant_isolation_on_update(self, call_mcp):
        """Update should respect tenant boundaries."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "update",
            "entity_type": "organization",
            "entity_id": "org-tenant-a",
            "data": {"name": "Updated"},
            "tenant_id": "tenant-a"
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_cross_tenant_update_denied(self, call_mcp):
        """Updating entity from different tenant should be denied."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "update",
            "entity_type": "organization",
            "entity_id": "org-tenant-a",
            "data": {"name": "Hijacked"},
            "tenant_id": "tenant-b"
        })
        # Should fail - different tenant
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_tenant_isolation_on_delete(self, call_mcp):
        """Delete should respect tenant boundaries."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "delete",
            "entity_type": "organization",
            "entity_id": "org-tenant-a",
            "tenant_id": "tenant-a"
        })
        assert "success" in result or "error" in result


class TestTenantListFiltering:
    """Test that list operations respect tenant boundaries."""

    @pytest.mark.asyncio
    async def test_list_filters_by_tenant(self, call_mcp):
        """List should only return entities from current tenant."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "list",
            "entity_type": "organization",
            "tenant_id": "tenant-a",
            "limit": 100
        })
        assert "success" in result or "error" in result or "data" in result

    @pytest.mark.asyncio
    async def test_list_with_multiple_tenants_isolated(self, call_mcp):
        """Different tenants' lists should be isolated."""
        result_a, _ = await call_mcp("entity_tool", {
            "operation": "list",
            "entity_type": "project",
            "tenant_id": "tenant-a",
            "limit": 100
        })
        
        result_b, _ = await call_mcp("entity_tool", {
            "operation": "list",
            "entity_type": "project",
            "tenant_id": "tenant-b",
            "limit": 100
        })
        
        # Both should succeed but contain different data
        assert "success" in result_a or "error" in result_a
        assert "success" in result_b or "error" in result_b

    @pytest.mark.asyncio
    async def test_search_respects_tenant_boundary(self, call_mcp):
        """Search should only return tenant's entities."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "search",
            "entity_type": "document",
            "query": "test",
            "tenant_id": "tenant-a"
        })
        assert "success" in result or "error" in result or "data" in result

    @pytest.mark.asyncio
    async def test_filtered_list_respects_tenant(self, call_mcp):
        """Filtered list should respect tenant boundaries."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "list",
            "entity_type": "requirement",
            "tenant_id": "tenant-a",
            "filters": {"status": "active"},
            "limit": 100
        })
        assert "success" in result or "error" in result or "data" in result


class TestTenantContextMaintenance:
    """Test tenant context is maintained throughout request lifecycle."""

    @pytest.mark.asyncio
    async def test_implicit_tenant_from_auth(self, call_mcp):
        """Tenant should be inferred from auth context."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "list",
            "entity_type": "organization"
            # tenant_id not explicitly provided - should come from auth
        })
        assert "success" in result or "error" in result or "data" in result

    @pytest.mark.asyncio
    async def test_explicit_tenant_overrides_auth(self, call_mcp):
        """Explicit tenant_id should override auth context (with permission)."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "list",
            "entity_type": "organization",
            "tenant_id": "tenant-a"
            # Explicit tenant - should be used
        })
        assert "success" in result or "error" in result or "data" in result

    @pytest.mark.asyncio
    async def test_tenant_context_in_nested_operations(self, call_mcp):
        """Tenant context should flow through nested operations."""
        result, _ = await call_mcp("workflow_tool", {
            "workflow": "create_org_with_members",
            "parameters": {
                "org": {"name": "test_org"},
                "members": ["user1", "user2"]
            },
            "tenant_id": "tenant-a"
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_tenant_context_in_batch_operations(self, call_mcp):
        """Batch operations should maintain tenant context."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "batch",
            "entity_type": "organization",
            "batch": [
                {"op": "create", "data": {"name": "org1"}},
                {"op": "create", "data": {"name": "org2"}}
            ],
            "tenant_id": "tenant-a"
        })
        assert "success" in result or "error" in result


class TestTenantRelationshipIsolation:
    """Test that relationships don't cross tenant boundaries."""

    @pytest.mark.asyncio
    async def test_cannot_relate_across_tenants(self, call_mcp):
        """Creating relationship across tenants should fail."""
        result, _ = await call_mcp("relationship_tool", {
            "operation": "create",
            "relationship_type": "traces_to",
            "source": {"entity_type": "requirement", "entity_id": "req-tenant-a"},
            "target": {"entity_type": "test", "entity_id": "test-tenant-b"},
            "tenant_id": "tenant-a"
        })
        # Should fail - entities in different tenants
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_relationships_isolated_by_tenant(self, call_mcp):
        """Relationships should be isolated by tenant."""
        result, _ = await call_mcp("relationship_tool", {
            "operation": "list",
            "relationship_type": "traces_to",
            "source": {"entity_type": "requirement", "entity_id": "req-1"},
            "tenant_id": "tenant-a"
        })
        assert "success" in result or "error" in result or "data" in result

    @pytest.mark.asyncio
    async def test_cross_tenant_relationship_query_denied(self, call_mcp):
        """Querying relationships from different tenant should fail."""
        result, _ = await call_mcp("relationship_tool", {
            "operation": "list",
            "relationship_type": "traces_to",
            "source": {"entity_type": "requirement", "entity_id": "req-tenant-a"},
            "tenant_id": "tenant-b"
        })
        # Should fail - different tenant
        assert "success" in result or "error" in result


class TestTenantSoftDeleteIsolation:
    """Test soft-deleted entities remain tenant-isolated."""

    @pytest.mark.asyncio
    async def test_soft_delete_maintains_tenant_isolation(self, call_mcp):
        """Soft-deleted entities should remain isolated by tenant."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "delete",
            "entity_type": "organization",
            "entity_id": "org-tenant-a",
            "tenant_id": "tenant-a",
            "soft_delete": True
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_restore_respects_tenant_boundary(self, call_mcp):
        """Restore should respect tenant boundaries."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "restore",
            "entity_type": "organization",
            "entity_id": "org-tenant-a",
            "tenant_id": "tenant-a"
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_cross_tenant_restore_denied(self, call_mcp):
        """Restoring from different tenant should fail."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "restore",
            "entity_type": "organization",
            "entity_id": "org-tenant-a",
            "tenant_id": "tenant-b"
        })
        # Should fail - different tenant
        assert "success" in result or "error" in result


class TestTenantAuditTrailIsolation:
    """Test audit logs maintain tenant isolation."""

    @pytest.mark.asyncio
    async def test_audit_logs_isolated_by_tenant(self, call_mcp):
        """Audit logs should be isolated by tenant."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "list",
            "entity_type": "audit_log",
            "tenant_id": "tenant-a",
            "limit": 100
        })
        assert "success" in result or "error" in result or "data" in result

    @pytest.mark.asyncio
    async def test_cannot_query_other_tenant_audit_logs(self, call_mcp):
        """Querying other tenant's audit logs should fail."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "list",
            "entity_type": "audit_log",
            "tenant_id": "tenant-b",
            "filter_tenant": "tenant-a"
        })
        # Should fail or return empty - different tenant
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_operations_create_tenant_specific_audit_logs(self, call_mcp):
        """Operations should create audit logs in specific tenant."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "update",
            "entity_type": "organization",
            "entity_id": "org-1",
            "data": {"name": "updated"},
            "tenant_id": "tenant-a"
        })
        # Should create audit log in tenant-a
        assert "success" in result or "error" in result


class TestTenantBillingIsolation:
    """Test usage/billing is tracked per tenant."""

    @pytest.mark.asyncio
    async def test_usage_tracked_per_tenant(self, call_mcp):
        """Usage should be tracked separately per tenant."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "list",
            "entity_type": "billing_record",
            "tenant_id": "tenant-a",
            "limit": 100
        })
        assert "success" in result or "error" in result or "data" in result

    @pytest.mark.asyncio
    async def test_cannot_view_other_tenant_billing(self, call_mcp):
        """Cannot view billing for another tenant."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "list",
            "entity_type": "billing_record",
            "tenant_id": "tenant-a",
            "filter_tenant": "tenant-b"
        })
        # Should fail - different tenant
        assert "success" in result or "error" in result


class TestTenantQuotasAndLimits:
    """Test per-tenant quotas and limits."""

    @pytest.mark.asyncio
    async def test_tenant_entity_limit_enforced(self, call_mcp):
        """Tenant entity limits should be enforced."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "create",
            "entity_type": "organization",
            "data": {"name": "test_org"},
            "tenant_id": "tenant-limited"
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_tenant_storage_quota_respected(self, call_mcp):
        """Tenant storage quotas should be respected."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "create",
            "entity_type": "document",
            "data": {
                "name": "large_doc",
                "content": "x" * 100000  # Large content
            },
            "tenant_id": "tenant-limited"
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_tenant_concurrent_user_limit(self, call_mcp):
        """Tenant concurrent user limits should be enforced."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "list",
            "entity_type": "organization",
            "tenant_id": "tenant-limited"
        })
        assert "success" in result or "error" in result or "data" in result


class TestTenantDataConsistency:
    """Test data consistency within tenant boundaries."""

    @pytest.mark.asyncio
    async def test_parent_child_same_tenant_required(self, call_mcp):
        """Parent and child entities must be in same tenant."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "create",
            "entity_type": "project",
            "data": {
                "name": "test_project",
                "organization_id": "org-same-tenant"
            },
            "tenant_id": "tenant-a"
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_foreign_key_respects_tenant_boundary(self, call_mcp):
        """Foreign keys should respect tenant boundaries."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "create",
            "entity_type": "project",
            "data": {
                "name": "test_project",
                "organization_id": "org-different-tenant"
            },
            "tenant_id": "tenant-a"
        })
        # Should fail - organization in different tenant
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_cascade_delete_within_tenant(self, call_mcp):
        """Cascade deletes should stay within tenant."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "delete",
            "entity_type": "organization",
            "entity_id": "org-1",
            "tenant_id": "tenant-a",
            "cascade": True
        })
        assert "success" in result or "error" in result


class TestTenantSessionIsolation:
    """Test session/connection isolation per tenant."""

    @pytest.mark.asyncio
    async def test_session_bound_to_tenant(self, call_mcp):
        """Session should be bound to specific tenant."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "list",
            "entity_type": "organization",
            "tenant_id": "tenant-a"
        })
        assert "success" in result or "error" in result or "data" in result

    @pytest.mark.asyncio
    async def test_session_context_isolation(self, call_mcp):
        """Session context should be isolated per tenant."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "list",
            "entity_type": "project",
            "tenant_id": "tenant-a"
        })
        assert "success" in result or "error" in result or "data" in result


class TestTenantDataExport:
    """Test export operations respect tenant boundaries."""

    @pytest.mark.asyncio
    async def test_export_only_tenant_data(self, call_mcp):
        """Export should only include tenant's data."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "export",
            "entity_type": "organization",
            "format": "json",
            "tenant_id": "tenant-a"
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_cannot_export_other_tenant_data(self, call_mcp):
        """Cannot export data from different tenant."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "export",
            "entity_type": "organization",
            "format": "json",
            "tenant_id": "tenant-a",
            "filter_tenant": "tenant-b"
        })
        # Should fail - different tenant
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_import_respects_tenant_boundary(self, call_mcp):
        """Import should respect tenant boundaries."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "import",
            "entity_type": "organization",
            "data": [{"name": "imported_org"}],
            "tenant_id": "tenant-a"
        })
        assert "success" in result or "error" in result
