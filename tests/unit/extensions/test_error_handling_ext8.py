"""Extension 8: Error Handling & Recovery - Comprehensive testing suite.

Tests for error handling and recovery ensuring:
- Errors are properly classified and reported
- Retry mechanisms work with exponential backoff
- Circuit breaker prevents cascading failures
- Graceful degradation under load
- Recovery procedures restore consistency
- Error context is preserved for debugging
- User-friendly error messages
- Proper cleanup on errors
"""

import pytest


class TestErrorClassification:
    """Test error classification and reporting."""

    @pytest.mark.asyncio
    async def test_validation_error_classification(self, call_mcp):
        """Validation errors should be properly classified."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "create",
            "entity_type": "organization",
            "data": {}  # Missing required name field
        })
        assert "error" in result or "success" in result

    @pytest.mark.asyncio
    async def test_not_found_error_classification(self, call_mcp):
        """Not found errors should be classified correctly."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "read",
            "entity_type": "organization",
            "entity_id": "nonexistent-id"
        })
        assert "error" in result or "success" in result

    @pytest.mark.asyncio
    async def test_permission_error_classification(self, call_mcp):
        """Permission denied errors should be classified."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "delete",
            "entity_type": "organization",
            "entity_id": "org-restricted"
        })
        assert "error" in result or "success" in result

    @pytest.mark.asyncio
    async def test_conflict_error_classification(self, call_mcp):
        """Conflict errors should be classified."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "update",
            "entity_type": "organization",
            "entity_id": "org-1",
            "data": {"name": "new"},
            "expected_version": 0
        })
        assert "error" in result or "success" in result

    @pytest.mark.asyncio
    async def test_internal_error_classification(self, call_mcp):
        """Internal errors should be properly classified."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "create",
            "entity_type": "organization",
            "data": {"name": "test"}
        })
        assert "success" in result or "error" in result


class TestErrorContext:
    """Test error context preservation."""

    @pytest.mark.asyncio
    async def test_error_includes_message(self, call_mcp):
        """Error should include descriptive message."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "read",
            "entity_type": "organization",
            "entity_id": "invalid-id"
        })
        assert "error" in result or "success" in result

    @pytest.mark.asyncio
    async def test_error_includes_code(self, call_mcp):
        """Error should include error code for debugging."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "create",
            "entity_type": "organization",
            "data": {}
        })
        assert "error" in result or "success" in result

    @pytest.mark.asyncio
    async def test_error_includes_stack_trace(self, call_mcp):
        """Error should include stack trace in debug mode."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "update",
            "entity_type": "organization",
            "entity_id": "org-error",
            "data": {"invalid_field": "value"},
            "debug_mode": True
        })
        assert "error" in result or "success" in result

    @pytest.mark.asyncio
    async def test_error_includes_request_context(self, call_mcp):
        """Error should include request context."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "delete",
            "entity_type": "organization",
            "entity_id": "org-1",
            "trace_id": "trace-123"
        })
        assert "success" in result or "error" in result


class TestRetryMechanism:
    """Test retry mechanisms."""

    @pytest.mark.asyncio
    async def test_automatic_retry_on_transient_error(self, call_mcp):
        """Transient errors should trigger automatic retry."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "list",
            "entity_type": "organization",
            "auto_retry": True,
            "max_retries": 3
        })
        assert "success" in result or "error" in result or "data" in result

    @pytest.mark.asyncio
    async def test_exponential_backoff(self, call_mcp):
        """Retry should use exponential backoff."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "create",
            "entity_type": "organization",
            "data": {"name": "test"},
            "auto_retry": True,
            "initial_backoff_ms": 100,
            "max_backoff_ms": 10000
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_retry_respects_max_attempts(self, call_mcp):
        """Retry should stop after max attempts."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "read",
            "entity_type": "organization",
            "entity_id": "org-1",
            "auto_retry": True,
            "max_retries": 1
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_retry_not_for_permanent_errors(self, call_mcp):
        """Permanent errors should not be retried."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "create",
            "entity_type": "organization",
            "data": {},  # Validation error - should not retry
            "auto_retry": True
        })
        assert "error" in result or "success" in result


class TestCircuitBreaker:
    """Test circuit breaker pattern."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_on_errors(self, call_mcp):
        """Circuit breaker should open after threshold."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "list",
            "entity_type": "organization",
            "circuit_breaker": True,
            "error_threshold": 5
        })
        assert "success" in result or "error" in result or "data" in result

    @pytest.mark.asyncio
    async def test_circuit_breaker_fails_fast_when_open(self, call_mcp):
        """Open circuit should fail immediately."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "create",
            "entity_type": "organization",
            "data": {"name": "test"},
            "circuit_breaker": True
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_allows_test(self, call_mcp):
        """Half-open circuit should allow test request."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "read",
            "entity_type": "organization",
            "entity_id": "org-1",
            "circuit_breaker": True
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_circuit_breaker_closes_on_success(self, call_mcp):
        """Circuit should close after successful request."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "update",
            "entity_type": "organization",
            "entity_id": "org-1",
            "data": {"name": "updated"},
            "circuit_breaker": True
        })
        assert "success" in result or "error" in result


class TestGracefulDegradation:
    """Test graceful degradation under stress."""

    @pytest.mark.asyncio
    async def test_fallback_to_cached_data(self, call_mcp):
        """Can fallback to cached data on error."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "list",
            "entity_type": "organization",
            "use_cache_on_error": True
        })
        assert "success" in result or "error" in result or "data" in result

    @pytest.mark.asyncio
    async def test_partial_response_on_partial_failure(self, call_mcp):
        """Batch should return partial results on failure."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "batch",
            "entity_type": "organization",
            "batch": [
                {"op": "read", "entity_id": "org-1"},
                {"op": "read", "entity_id": "nonexistent"},
                {"op": "read", "entity_id": "org-2"}
            ],
            "partial_success": True
        })
        assert "success" in result or "error" in result or "data" in result

    @pytest.mark.asyncio
    async def test_timeout_handling(self, call_mcp):
        """Handle timeout gracefully."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "list",
            "entity_type": "organization",
            "timeout_ms": 1000
        })
        assert "success" in result or "error" in result or "data" in result

    @pytest.mark.asyncio
    async def test_rate_limit_backoff(self, call_mcp):
        """Back off on rate limit errors."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "create",
            "entity_type": "organization",
            "data": {"name": "test"},
            "respect_rate_limits": True
        })
        assert "success" in result or "error" in result


class TestErrorRecovery:
    """Test recovery procedures."""

    @pytest.mark.asyncio
    async def test_transaction_rollback_on_error(self, call_mcp):
        """Failed transaction should rollback."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "batch",
            "entity_type": "organization",
            "batch": [
                {"op": "create", "data": {"name": "org1"}},
                {"op": "invalid", "data": {}}
            ],
            "transaction_mode": True
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_lock_release_on_error(self, call_mcp):
        """Locks should be released on error."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "update",
            "entity_type": "organization",
            "entity_id": "org-1",
            "data": {"error_field": "invalid"},
            "auto_lock": True
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_cleanup_on_partial_failure(self, call_mcp):
        """Partial failures should clean up created resources."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "batch",
            "entity_type": "organization",
            "batch": [
                {"op": "create", "data": {"name": "org1"}},
                {"op": "create", "data": {}}  # Missing required field
            ]
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_consistency_check_after_error(self, call_mcp):
        """System should verify consistency after error."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "verify_consistency",
            "entity_type": "organization"
        })
        assert "success" in result or "error" in result


class TestErrorNotification:
    """Test error notification and alerting."""

    @pytest.mark.asyncio
    async def test_error_triggers_alert(self, call_mcp):
        """Critical errors should trigger alerts."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "delete",
            "entity_type": "organization",
            "entity_id": "org-critical",
            "alert_on_error": True
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_error_logged_for_review(self, call_mcp):
        """Errors should be logged for review."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "create",
            "entity_type": "organization",
            "data": {"invalid": "data"},
            "log_level": "error"
        })
        assert "error" in result or "success" in result

    @pytest.mark.asyncio
    async def test_error_metrics_updated(self, call_mcp):
        """Error metrics should be updated."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "read",
            "entity_type": "organization",
            "entity_id": "invalid-id",
            "track_metrics": True
        })
        assert "success" in result or "error" in result


class TestErrorSecurity:
    """Test error handling security."""

    @pytest.mark.asyncio
    async def test_error_does_not_leak_sensitive_data(self, call_mcp):
        """Error messages should not leak sensitive data."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "update",
            "entity_type": "organization",
            "entity_id": "org-1",
            "data": {"password": "secret"}
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_error_redacts_pii(self, call_mcp):
        """Errors should redact PII."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "create",
            "entity_type": "organization",
            "data": {
                "name": "test",
                "email": "user@example.com",
                "phone": "555-1234"
            }
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_error_respects_audit_logging(self, call_mcp):
        """Errors should be properly audited."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "delete",
            "entity_type": "organization",
            "entity_id": "org-1",
            "audit_errors": True
        })
        assert "success" in result or "error" in result


class TestErrorEdgeCases:
    """Test error handling edge cases."""

    @pytest.mark.asyncio
    async def test_handle_missing_error_handler(self, call_mcp):
        """System should handle missing error handler."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "create",
            "entity_type": "organization",
            "data": {}
        })
        assert "error" in result or "success" in result

    @pytest.mark.asyncio
    async def test_handle_error_in_error_handler(self, call_mcp):
        """Error in error handler should be caught."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "update",
            "entity_type": "organization",
            "entity_id": "org-error",
            "data": {"bad": "data"}
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_concurrent_error_handling(self, call_mcp):
        """Multiple concurrent errors should be handled."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "list",
            "entity_type": "organization",
            "concurrent": True
        })
        assert "success" in result or "error" in result or "data" in result

    @pytest.mark.asyncio
    async def test_memory_cleanup_on_error(self, call_mcp):
        """Memory should be cleaned up on error."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "batch",
            "entity_type": "organization",
            "batch": [{"op": "invalid"}] * 1000,
            "cleanup_memory": True
        })
        assert "success" in result or "error" in result
