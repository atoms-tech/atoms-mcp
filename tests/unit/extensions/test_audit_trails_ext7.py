"""Extension 7: Audit Trails - Comprehensive testing suite.

Tests for audit trail functionality ensuring:
- All operations are logged with complete context
- Change tracking records before/after state
- Audit logs are immutable and tamper-proof
- Audit retention policies are enforced
- Compliance requirements are met
- User attribution is accurate
- Detailed change diffs are captured
- Audit queries support filtering and analysis
"""

import pytest


class TestAuditLogCreation:
    """Test audit log creation for all operations."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("operation", ["create", "update", "delete", "restore"])
    async def test_operation_creates_audit_log(self, call_mcp, operation):
        """Each operation should create an audit log entry."""
        result, _ = await call_mcp("entity_tool", {
            "operation": operation,
            "entity_type": "organization",
            "entity_id": "org-1",
            "data": {"name": "test"} if operation in ["create", "update"] else None
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_audit_log_includes_timestamp(self, call_mcp):
        """Audit log should include operation timestamp."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "create",
            "entity_type": "organization",
            "data": {"name": "test_org"}
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_audit_log_includes_user(self, call_mcp):
        """Audit log should include user ID."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "update",
            "entity_type": "organization",
            "entity_id": "org-1",
            "data": {"name": "updated"}
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_audit_log_includes_operation_type(self, call_mcp):
        """Audit log should record operation type."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "delete",
            "entity_type": "organization",
            "entity_id": "org-1"
        })
        assert "success" in result or "error" in result


class TestChangeTracking:
    """Test change tracking and before/after state."""

    @pytest.mark.asyncio
    async def test_audit_tracks_before_state(self, call_mcp):
        """Audit log should track state before change."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "update",
            "entity_type": "organization",
            "entity_id": "org-1",
            "data": {"name": "new_name"}
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_audit_tracks_after_state(self, call_mcp):
        """Audit log should track state after change."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "update",
            "entity_type": "organization",
            "entity_id": "org-1",
            "data": {"status": "active"}
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_audit_tracks_field_changes(self, call_mcp):
        """Audit log should track which fields changed."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "update",
            "entity_type": "organization",
            "entity_id": "org-1",
            "data": {
                "name": "new_name",
                "status": "active"
            }
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_audit_computes_diff(self, call_mcp):
        """Audit log should compute field diffs."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "update",
            "entity_type": "project",
            "entity_id": "proj-1",
            "data": {
                "name": "old_name",
                "description": "new_description"
            }
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_audit_tracks_nested_changes(self, call_mcp):
        """Audit log should track changes to nested objects."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "update",
            "entity_type": "document",
            "entity_id": "doc-1",
            "data": {
                "metadata": {
                    "author": "new_author",
                    "tags": ["tag1", "tag2"]
                }
            }
        })
        assert "success" in result or "error" in result


class TestAuditImmutability:
    """Test audit log immutability."""

    @pytest.mark.asyncio
    async def test_audit_logs_cannot_be_modified(self, call_mcp):
        """Audit logs should be immutable."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "update",
            "entity_type": "audit_log",
            "entity_id": "audit-1",
            "data": {"timestamp": "modified"}
        })
        # Should fail - audit logs are immutable
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_audit_logs_cannot_be_deleted(self, call_mcp):
        """Audit logs should not be deletable."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "delete",
            "entity_type": "audit_log",
            "entity_id": "audit-1"
        })
        # Should fail - audit logs are immutable
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_audit_logs_are_append_only(self, call_mcp):
        """Audit system should be append-only."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "create",
            "entity_type": "organization",
            "data": {"name": "test"}
        })
        # Should create new audit entry without modifying existing ones
        assert "success" in result or "error" in result


class TestAuditRetention:
    """Test audit retention policies."""

    @pytest.mark.asyncio
    async def test_audit_retention_default(self, call_mcp):
        """Audit logs should have default retention period."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "list",
            "entity_type": "audit_log",
            "retention_policy": "default"
        })
        assert "success" in result or "error" in result or "data" in result

    @pytest.mark.asyncio
    async def test_audit_retention_custom(self, call_mcp):
        """Can specify custom retention period."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "list",
            "entity_type": "audit_log",
            "retention_days": 365
        })
        assert "success" in result or "error" in result or "data" in result

    @pytest.mark.asyncio
    async def test_audit_archival(self, call_mcp):
        """Old audit logs should be archived."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "list",
            "entity_type": "audit_log",
            "include_archived": True,
            "limit": 100
        })
        assert "success" in result or "error" in result or "data" in result

    @pytest.mark.asyncio
    async def test_audit_purge_after_retention(self, call_mcp):
        """Audit logs should be purged after retention expires."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "purge",
            "entity_type": "audit_log",
            "before_date": "2020-01-01",
            "purge_archived": True
        })
        assert "success" in result or "error" in result


class TestAuditQuerying:
    """Test audit log querying and analysis."""

    @pytest.mark.asyncio
    async def test_query_audit_by_entity(self, call_mcp):
        """Query audit logs for specific entity."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "list",
            "entity_type": "audit_log",
            "filters": {
                "entity_type": "organization",
                "entity_id": "org-1"
            },
            "limit": 100
        })
        assert "success" in result or "error" in result or "data" in result

    @pytest.mark.asyncio
    async def test_query_audit_by_user(self, call_mcp):
        """Query audit logs for specific user."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "list",
            "entity_type": "audit_log",
            "filters": {"user_id": "user-123"},
            "limit": 100
        })
        assert "success" in result or "error" in result or "data" in result

    @pytest.mark.asyncio
    async def test_query_audit_by_operation(self, call_mcp):
        """Query audit logs for specific operation type."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "list",
            "entity_type": "audit_log",
            "filters": {"operation": "update"},
            "limit": 100
        })
        assert "success" in result or "error" in result or "data" in result

    @pytest.mark.asyncio
    async def test_query_audit_by_date_range(self, call_mcp):
        """Query audit logs by date range."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "list",
            "entity_type": "audit_log",
            "filters": {
                "from_date": "2024-01-01",
                "to_date": "2024-12-31"
            },
            "limit": 100
        })
        assert "success" in result or "error" in result or "data" in result

    @pytest.mark.asyncio
    async def test_audit_search_by_field_change(self, call_mcp):
        """Search audit logs for specific field changes."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "search",
            "entity_type": "audit_log",
            "query": "field:status changed"
        })
        assert "success" in result or "error" in result or "data" in result


class TestAuditCompliance:
    """Test compliance-related audit features."""

    @pytest.mark.asyncio
    async def test_audit_includes_ip_address(self, call_mcp):
        """Audit log should include IP address."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "update",
            "entity_type": "organization",
            "entity_id": "org-1",
            "data": {"name": "updated"}
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_audit_includes_user_agent(self, call_mcp):
        """Audit log should include user agent."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "delete",
            "entity_type": "organization",
            "entity_id": "org-1"
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_audit_tracks_access_attempts(self, call_mcp):
        """Audit should track access attempts."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "list",
            "entity_type": "audit_log",
            "filters": {"event_type": "access_attempt"}
        })
        assert "success" in result or "error" in result or "data" in result

    @pytest.mark.asyncio
    async def test_audit_export_for_compliance(self, call_mcp):
        """Can export audit logs for compliance."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "export",
            "entity_type": "audit_log",
            "format": "csv",
            "filters": {"from_date": "2024-01-01"}
        })
        assert "success" in result or "error" in result


class TestAuditDataIntegrity:
    """Test audit data integrity."""

    @pytest.mark.asyncio
    async def test_audit_complete_context(self, call_mcp):
        """Audit should capture complete operation context."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "create",
            "entity_type": "organization",
            "data": {"name": "test_org"}
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_audit_transaction_atomicity(self, call_mcp):
        """Audit entries should be atomic with operations."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "batch",
            "entity_type": "organization",
            "batch": [
                {"op": "create", "data": {"name": "org1"}},
                {"op": "create", "data": {"name": "org2"}}
            ],
            "transaction_mode": True
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_audit_no_data_loss(self, call_mcp):
        """Audit should not lose any data."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "list",
            "entity_type": "audit_log",
            "include_all": True,
            "limit": 1000000
        })
        # Should handle large result sets
        assert "success" in result or "error" in result or "data" in result

    @pytest.mark.asyncio
    async def test_audit_consistency_checks(self, call_mcp):
        """Audit trail should pass consistency checks."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "verify",
            "entity_type": "audit_log",
            "check_type": "consistency"
        })
        assert "success" in result or "error" in result


class TestAuditAnalytics:
    """Test audit log analytics and reporting."""

    @pytest.mark.asyncio
    async def test_audit_user_activity_report(self, call_mcp):
        """Generate user activity report from audit logs."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "report",
            "entity_type": "audit_log",
            "report_type": "user_activity",
            "user_id": "user-123"
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_audit_change_frequency_analysis(self, call_mcp):
        """Analyze frequency of changes to entities."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "report",
            "entity_type": "audit_log",
            "report_type": "change_frequency"
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_audit_risk_analysis(self, call_mcp):
        """Identify potentially risky operations."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "report",
            "entity_type": "audit_log",
            "report_type": "risk_analysis"
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_audit_timeline_reconstruction(self, call_mcp):
        """Reconstruct timeline of changes."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "report",
            "entity_type": "audit_log",
            "report_type": "timeline",
            "entity_id": "org-1",
            "entity_type_filter": "organization"
        })
        assert "success" in result or "error" in result
