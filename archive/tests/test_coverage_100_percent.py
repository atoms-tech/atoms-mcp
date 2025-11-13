"""
Comprehensive tests to achieve 100% code coverage for tools, services, and infrastructure.

This test suite systematically covers all code paths that are currently uncovered.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock



# ============================================================================
# TOOLS/BASE.PY - 100% Coverage
# ============================================================================

class TestToolBaseComplete:
    """Complete coverage tests for tools/base.py."""

    @pytest.mark.asyncio
    @pytest.mark.mock_only
    async def test_validate_auth_oauth_session(self):
        """Test _validate_auth with oauth-session token."""
        from tools.base import ToolBase
        
        tool = ToolBase()
        
        with pytest.raises(ValueError, match="Authentication required"):
            await tool._validate_auth("oauth-session")

    @pytest.mark.asyncio
    @pytest.mark.mock_only
    async def test_validate_auth_empty_token(self):
        """Test _validate_auth with empty token."""
        from tools.base import ToolBase
        
        tool = ToolBase()
        
        with pytest.raises(ValueError, match="Authentication required"):
            await tool._validate_auth("")

    @pytest.mark.asyncio
    @pytest.mark.mock_only
    async def test_validate_auth_success_with_access_token(self):
        """Test _validate_auth success with access_token."""
        from tools.base import ToolBase
        
        tool = ToolBase()
        
        mock_auth_adapter = AsyncMock()
        mock_auth_adapter.validate_token = AsyncMock(return_value={
            "user_id": "user-123",
            "access_token": "token-123"
        })
        
        mock_db_adapter = MagicMock()
        mock_db_adapter.set_access_token = MagicMock()
        
        with patch('tools.base.get_adapters', return_value={
            "auth": mock_auth_adapter,
            "database": mock_db_adapter
        }):
            result = await tool._validate_auth("valid-token")
            
            assert result["user_id"] == "user-123"
            mock_db_adapter.set_access_token.assert_called_once_with("token-123")

    @pytest.mark.asyncio
    @pytest.mark.mock_only
    async def test_validate_auth_success_without_access_token(self):
        """Test _validate_auth success without access_token."""
        from tools.base import ToolBase
        
        tool = ToolBase()
        
        mock_auth_adapter = AsyncMock()
        mock_auth_adapter.validate_token = AsyncMock(return_value={
            "user_id": "user-123"
        })
        
        mock_db_adapter = MagicMock()
        
        with patch('tools.base.get_adapters', return_value={
            "auth": mock_auth_adapter,
            "database": mock_db_adapter
        }):
            result = await tool._validate_auth("valid-token")
            
            assert result["user_id"] == "user-123"
            # set_access_token should not be called
            assert not hasattr(mock_db_adapter.set_access_token, 'call_count') or mock_db_adapter.set_access_token.call_count == 0

    @pytest.mark.asyncio
    @pytest.mark.mock_only
    async def test_validate_auth_exception(self):
        """Test _validate_auth with exception."""
        from tools.base import ToolBase
        
        tool = ToolBase()
        
        mock_auth_adapter = AsyncMock()
        mock_auth_adapter.validate_token = AsyncMock(side_effect=Exception("Auth error"))
        
        with patch('tools.base.get_adapters', return_value={
            "auth": mock_auth_adapter,
            "database": MagicMock()
        }):
            with pytest.raises(Exception):
                await tool._validate_auth("invalid-token")

    @pytest.mark.mock_only
    def test_get_user_id(self):
        """Test _get_user_id."""
        from tools.base import ToolBase
        
        tool = ToolBase()
        tool._user_context = {"user_id": "user-123"}
        
        assert tool._get_user_id() == "user-123"

    @pytest.mark.mock_only
    def test_get_user_id_empty(self):
        """Test _get_user_id with empty context."""
        from tools.base import ToolBase
        
        tool = ToolBase()
        
        assert tool._get_user_id() == ""

    @pytest.mark.mock_only
    def test_get_username(self):
        """Test _get_username."""
        from tools.base import ToolBase
        
        tool = ToolBase()
        tool._user_context = {"username": "testuser"}
        
        assert tool._get_username() == "testuser"

    @pytest.mark.mock_only
    def test_get_username_empty(self):
        """Test _get_username with empty context."""
        from tools.base import ToolBase
        
        tool = ToolBase()
        
        assert tool._get_username() == ""

    @pytest.mark.mock_only
    def test_supabase_property_success(self):
        """Test supabase property success path."""
        from tools.base import ToolBase
        
        tool = ToolBase()
        
        mock_client = MagicMock()
        mock_db_adapter = MagicMock()
        mock_db_adapter._get_client = MagicMock(return_value=mock_client)
        
        with patch('tools.base.get_adapters', return_value={
            "database": mock_db_adapter
        }):
            result = tool.supabase
            assert result == mock_client

    @pytest.mark.mock_only
    def test_supabase_property_fallback(self):
        """Test supabase property fallback path."""
        from tools.base import ToolBase
        
        tool = ToolBase()
        
        mock_db_adapter = MagicMock()
        mock_db_adapter._get_client = MagicMock(side_effect=Exception("No client"))
        
        mock_supabase = MagicMock()
        
        with patch('tools.base.get_adapters', return_value={
            "database": mock_db_adapter
        }):
            with patch('supabase_client.get_supabase', return_value=mock_supabase):
                result = tool.supabase
                assert result == mock_supabase

    @pytest.mark.mock_only
    def test_supabase_property_fallback_failure(self):
        """Test supabase property fallback failure."""
        from tools.base import ToolBase
        
        tool = ToolBase()
        
        mock_db_adapter = MagicMock()
        mock_db_adapter._get_client = MagicMock(side_effect=Exception("No client"))
        
        with patch('tools.base.get_adapters', return_value={
            "database": mock_db_adapter
        }):
            with patch('supabase_client.get_supabase', side_effect=Exception("Import error")):
                with pytest.raises(RuntimeError, match="Could not get Supabase client"):
                    _ = tool.supabase

    @pytest.mark.asyncio
    @pytest.mark.mock_only
    async def test_db_query_success(self):
        """Test _db_query success."""
        from tools.base import ToolBase
        
        tool = ToolBase()
        
        mock_db_adapter = AsyncMock()
        mock_db_adapter.query = AsyncMock(return_value=[{"id": "1"}])
        
        with patch('tools.base.get_adapters', return_value={
            "database": mock_db_adapter
        }):
            result = await tool._db_query("test_table", filters={"id": "1"})
            assert result == [{"id": "1"}]

    @pytest.mark.asyncio
    @pytest.mark.mock_only
    async def test_db_query_exception(self):
        """Test _db_query with exception."""
        from tools.base import ToolBase
        
        tool = ToolBase()
        
        mock_db_adapter = AsyncMock()
        mock_db_adapter.query = AsyncMock(side_effect=Exception("DB error"))
        
        with patch('tools.base.get_adapters', return_value={
            "database": mock_db_adapter
        }):
            with pytest.raises(Exception):
                await tool._db_query("test_table")

    @pytest.mark.asyncio
    @pytest.mark.mock_only
    async def test_db_get_single_success(self):
        """Test _db_get_single success."""
        from tools.base import ToolBase
        
        tool = ToolBase()
        
        mock_db_adapter = AsyncMock()
        mock_db_adapter.get_single = AsyncMock(return_value={"id": "1"})
        
        with patch('tools.base.get_adapters', return_value={
            "database": mock_db_adapter
        }):
            result = await tool._db_get_single("test_table", filters={"id": "1"})
            assert result == {"id": "1"}

    @pytest.mark.asyncio
    @pytest.mark.mock_only
    async def test_db_get_single_exception(self):
        """Test _db_get_single with exception."""
        from tools.base import ToolBase
        
        tool = ToolBase()
        
        mock_db_adapter = AsyncMock()
        mock_db_adapter.get_single = AsyncMock(side_effect=Exception("DB error"))
        
        with patch('tools.base.get_adapters', return_value={
            "database": mock_db_adapter
        }):
            with pytest.raises(Exception):
                await tool._db_get_single("test_table")

    @pytest.mark.asyncio
    @pytest.mark.mock_only
    async def test_db_insert_success(self):
        """Test _db_insert success."""
        from tools.base import ToolBase
        
        tool = ToolBase()
        
        mock_db_adapter = AsyncMock()
        mock_db_adapter.insert = AsyncMock(return_value={"id": "1"})
        
        with patch('tools.base.get_adapters', return_value={
            "database": mock_db_adapter
        }):
            result = await tool._db_insert("test_table", {"name": "test"})
            assert result == {"id": "1"}

    @pytest.mark.asyncio
    @pytest.mark.mock_only
    async def test_db_insert_exception(self):
        """Test _db_insert with exception."""
        from tools.base import ToolBase
        
        tool = ToolBase()
        
        mock_db_adapter = AsyncMock()
        mock_db_adapter.insert = AsyncMock(side_effect=Exception("DB error"))
        
        with patch('tools.base.get_adapters', return_value={
            "database": mock_db_adapter
        }):
            with pytest.raises(Exception):
                await tool._db_insert("test_table", {"name": "test"})

    @pytest.mark.asyncio
    @pytest.mark.mock_only
    async def test_db_update_success(self):
        """Test _db_update success."""
        from tools.base import ToolBase
        
        tool = ToolBase()
        
        mock_db_adapter = AsyncMock()
        mock_db_adapter.update = AsyncMock(return_value={"id": "1"})
        
        with patch('tools.base.get_adapters', return_value={
            "database": mock_db_adapter
        }):
            result = await tool._db_update("test_table", {"name": "test"}, {"id": "1"})
            assert result == {"id": "1"}

    @pytest.mark.asyncio
    @pytest.mark.mock_only
    async def test_db_update_exception(self):
        """Test _db_update with exception."""
        from tools.base import ToolBase
        
        tool = ToolBase()
        
        mock_db_adapter = AsyncMock()
        mock_db_adapter.update = AsyncMock(side_effect=Exception("DB error"))
        
        with patch('tools.base.get_adapters', return_value={
            "database": mock_db_adapter
        }):
            with pytest.raises(Exception):
                await tool._db_update("test_table", {"name": "test"}, {"id": "1"})

    @pytest.mark.asyncio
    @pytest.mark.mock_only
    async def test_db_delete_success(self):
        """Test _db_delete success."""
        from tools.base import ToolBase
        
        tool = ToolBase()
        
        mock_db_adapter = AsyncMock()
        mock_db_adapter.delete = AsyncMock(return_value=1)
        
        with patch('tools.base.get_adapters', return_value={
            "database": mock_db_adapter
        }):
            result = await tool._db_delete("test_table", {"id": "1"})
            assert result == 1

    @pytest.mark.asyncio
    @pytest.mark.mock_only
    async def test_db_delete_exception(self):
        """Test _db_delete with exception."""
        from tools.base import ToolBase
        
        tool = ToolBase()
        
        mock_db_adapter = AsyncMock()
        mock_db_adapter.delete = AsyncMock(side_effect=Exception("DB error"))
        
        with patch('tools.base.get_adapters', return_value={
            "database": mock_db_adapter
        }):
            with pytest.raises(Exception):
                await tool._db_delete("test_table", {"id": "1"})

    @pytest.mark.asyncio
    @pytest.mark.mock_only
    async def test_db_count_success(self):
        """Test _db_count success."""
        from tools.base import ToolBase
        
        tool = ToolBase()
        
        mock_db_adapter = AsyncMock()
        mock_db_adapter.count = AsyncMock(return_value=10)
        
        with patch('tools.base.get_adapters', return_value={
            "database": mock_db_adapter
        }):
            result = await tool._db_count("test_table", {"is_deleted": False})
            assert result == 10

    @pytest.mark.asyncio
    @pytest.mark.mock_only
    async def test_db_count_no_filters(self):
        """Test _db_count without filters."""
        from tools.base import ToolBase
        
        tool = ToolBase()
        
        mock_db_adapter = AsyncMock()
        mock_db_adapter.count = AsyncMock(return_value=10)
        
        with patch('tools.base.get_adapters', return_value={
            "database": mock_db_adapter
        }):
            result = await tool._db_count("test_table")
            assert result == 10

    @pytest.mark.asyncio
    @pytest.mark.mock_only
    async def test_db_count_exception(self):
        """Test _db_count with exception."""
        from tools.base import ToolBase
        
        tool = ToolBase()
        
        mock_db_adapter = AsyncMock()
        mock_db_adapter.count = AsyncMock(side_effect=Exception("DB error"))
        
        with patch('tools.base.get_adapters', return_value={
            "database": mock_db_adapter
        }):
            with pytest.raises(Exception):
                await tool._db_count("test_table")

    @pytest.mark.mock_only
    def test_resolve_entity_table_all_types(self):
        """Test _resolve_entity_table for all entity types."""
        from tools.base import ToolBase
        
        tool = ToolBase()
        
        test_cases = [
            ("organization", "organizations"),
            ("project", "projects"),
            ("document", "documents"),
            ("requirement", "requirements"),
            ("test", "test_req"),
            ("property", "properties"),
            ("block", "blocks"),
            ("column", "columns"),
            ("trace_link", "trace_links"),
            ("assignment", "assignments"),
            ("audit_log", "audit_logs"),
            ("notification", "notifications"),
            ("external_document", "external_documents"),
            ("test_matrix_view", "test_matrix_views"),
            ("organization_member", "organization_members"),
            ("project_member", "project_members"),
            ("organization_invitation", "organization_invitations"),
            ("requirement_test", "requirement_tests"),
            ("profile", "profiles"),
            ("user", "profiles"),  # user maps to profiles
        ]
        
        for entity_type, expected_table in test_cases:
            result = tool._resolve_entity_table(entity_type)
            assert result == expected_table
        
        # Test case-insensitive
        assert tool._resolve_entity_table("ORGANIZATION") == "organizations"
        
        # Test unknown type
        with pytest.raises(ValueError, match="Unknown entity type"):
            tool._resolve_entity_table("unknown_type")

    @pytest.mark.mock_only
    def test_sanitize_entity_empty(self):
        """Test _sanitize_entity with empty entity."""
        from tools.base import ToolBase
        
        tool = ToolBase()
        
        result = tool._sanitize_entity({})
        assert result == {}
        
        result = tool._sanitize_entity(None)
        assert result == {}

    @pytest.mark.mock_only
    def test_sanitize_entity_excludes_large_fields(self):
        """Test _sanitize_entity excludes large fields."""
        from tools.base import ToolBase
        
        tool = ToolBase()
        
        entity = {
            "id": "123",
            "name": "Test",
            "embedding": [0.1] * 768,  # Large field
            "properties": {"large": "data" * 1000},  # Large field
            "content": "x" * 10000,  # Large field
            "description": "y" * 200,  # Large field
        }
        
        result = tool._sanitize_entity(entity)
        
        assert "id" in result
        assert "name" in result
        assert "embedding" not in result
        assert "properties" not in result
        assert "content" not in result
        assert "description" not in result

    @pytest.mark.mock_only
    def test_sanitize_entity_truncates_long_strings(self):
        """Test _sanitize_entity truncates long strings."""
        from tools.base import ToolBase
        
        tool = ToolBase()
        
        entity = {
            "id": "123",
            "name": "A" * 100,  # > 80 chars
        }
        
        result = tool._sanitize_entity(entity)
        
        assert len(result["name"]) == 83  # 80 + "..."
        assert result["name"].endswith("...")

    @pytest.mark.mock_only
    def test_sanitize_entity_keeps_small_dicts(self):
        """Test _sanitize_entity keeps small dicts."""
        from tools.base import ToolBase
        
        tool = ToolBase()
        
        entity = {
            "id": "123",
            "small_dict": {"key": "value"},  # Small dict
        }
        
        result = tool._sanitize_entity(entity)
        
        assert "small_dict" in result

    @pytest.mark.mock_only
    def test_sanitize_entity_keeps_small_lists(self):
        """Test _sanitize_entity keeps small lists."""
        from tools.base import ToolBase
        
        tool = ToolBase()
        
        entity = {
            "id": "123",
            "small_list": [1, 2],  # Small list
        }
        
        result = tool._sanitize_entity(entity)
        
        assert "small_list" in result

    @pytest.mark.mock_only
    def test_sanitize_entity_skips_none(self):
        """Test _sanitize_entity skips None values."""
        from tools.base import ToolBase
        
        tool = ToolBase()
        
        entity = {
            "id": "123",
            "name": "Test",
            "null_field": None,
        }
        
        result = tool._sanitize_entity(entity)
        
        assert "null_field" not in result

    @pytest.mark.mock_only
    def test_add_timing_metrics(self):
        """Test _add_timing_metrics."""
        from tools.base import ToolBase
        
        tool = ToolBase()
        
        result_dict = {"data": "test"}
        timings = {
            "query_time": 0.1,
            "process_time": 0.2,
            "metadata": "info"
        }
        
        result = tool._add_timing_metrics(result_dict, timings)
        
        assert "_performance" in result
        assert "timings_ms" in result["_performance"]
        assert result["_performance"]["timings_ms"]["query_time"] == 100.0
        assert result["_performance"]["timings_ms"]["process_time"] == 200.0
        assert "metadata" in result["_performance"]
        assert result["_performance"]["metadata"] == "info"

    @pytest.mark.mock_only
    def test_format_result_raw(self):
        """Test _format_result with raw format."""
        from tools.base import ToolBase
        
        tool = ToolBase()
        tool._user_context = {"user_id": "user-123"}
        
        data = {"id": "1", "name": "Test"}
        result = tool._format_result(data, "raw")
        
        assert "data" in result
        assert result["data"] == data

    @pytest.mark.mock_only
    def test_format_result_summary_list(self):
        """Test _format_result with summary format for list."""
        from tools.base import ToolBase
        
        tool = ToolBase()
        
        data = [{"id": str(i)} for i in range(5)]
        result = tool._format_result(data, "summary")
        
        assert "count" in result
        assert result["count"] == 5
        assert "items" in result
        assert len(result["items"]) == 3  # First 3
        assert result["truncated"] is True

    @pytest.mark.mock_only
    def test_format_result_summary_dict(self):
        """Test _format_result with summary format for dict."""
        from tools.base import ToolBase
        
        tool = ToolBase()
        
        data = {"id": "1", "name": "Test"}
        result = tool._format_result(data, "summary")
        
        assert "summary" in result

    @pytest.mark.mock_only
    def test_format_result_detailed_list_small(self):
        """Test _format_result with detailed format for small list."""
        from tools.base import ToolBase
        
        tool = ToolBase()
        tool._user_context = {"user_id": "user-123"}
        
        data = [{"id": str(i)} for i in range(5)]
        result = tool._format_result(data, "detailed")
        
        assert "success" in result
        assert "data" in result
        assert len(result["data"]) == 5
        assert result["count"] == 5
        assert "user_id" in result

    @pytest.mark.mock_only
    def test_format_result_detailed_list_large(self):
        """Test _format_result with detailed format for large list."""
        from tools.base import ToolBase
        
        tool = ToolBase()
        tool._user_context = {"user_id": "user-123"}
        
        data = [{"id": str(i)} for i in range(15)]
        result = tool._format_result(data, "detailed")
        
        assert "success" in result
        assert "data" in result
        assert len(result["data"]) == 10  # Truncated to 10
        assert result["count"] == 15
        assert result["truncated"] is True
        assert "hint" in result

    @pytest.mark.mock_only
    def test_format_result_detailed_dict(self):
        """Test _format_result with detailed format for dict."""
        from tools.base import ToolBase
        
        tool = ToolBase()
        tool._user_context = {"user_id": "user-123"}
        
        data = {"id": "1", "name": "Test"}
        result = tool._format_result(data, "detailed")
        
        assert "success" in result
        assert "data" in result
        assert result["count"] == 1
        assert "user_id" in result


# ============================================================================
# TOOLS/ENTITY_RESOLVER.PY - 100% Coverage
# ============================================================================

class TestEntityResolverComplete:
    """Complete coverage tests for tools/entity_resolver.py."""

    @pytest.mark.asyncio
    @pytest.mark.mock_only
    async def test_resolve_entity_id_uuid_exact_match(self):
        """Test resolve_entity_id with UUID exact match."""
        from tools.entity_resolver import EntityResolver
        
        mock_db = AsyncMock()
        # Use a valid UUID format
        valid_uuid = "123e4567-e89b-12d3-a456-426614174000"
        mock_db.get_single = AsyncMock(return_value={"id": valid_uuid, "name": "Test"})
        
        resolver = EntityResolver(mock_db)
        
        with patch('tools.entity_resolver._entity_manager') as mock_em:
            mock_em._resolve_entity_table = MagicMock(return_value="organizations")
            with patch('tools.entity_resolver.EntityResolver._is_uuid', return_value=True):
                result = await resolver.resolve_entity_id("organization", valid_uuid)
                
                assert result["success"] is True
                assert result["entity_id"] == valid_uuid
                assert result["match_type"] == "exact_uuid"

    @pytest.mark.asyncio
    @pytest.mark.mock_only
    async def test_resolve_entity_id_uuid_not_found(self):
        """Test resolve_entity_id with UUID not found."""
        from tools.entity_resolver import EntityResolver
        
        mock_db = AsyncMock()
        mock_db.get_single = AsyncMock(return_value=None)
        mock_db.query = AsyncMock(return_value=[])
        
        resolver = EntityResolver(mock_db)
        
        result = await resolver.resolve_entity_id("organization", "uuid-123")
        
        assert result["success"] is False

    @pytest.mark.asyncio
    @pytest.mark.mock_only
    async def test_resolve_entity_id_exact_name_match(self):
        """Test resolve_entity_id with exact name match."""
        from tools.entity_resolver import EntityResolver
        
        mock_db = AsyncMock()
        mock_db.get_single = AsyncMock(return_value=None)
        mock_db.query = AsyncMock(return_value=[
            {"id": "1", "name": "Test Org", "created_at": "2024-01-01"}
        ])
        
        resolver = EntityResolver(mock_db)
        
        result = await resolver.resolve_entity_id("organization", "Test Org")
        
        assert result["success"] is True
        assert result["match_type"] == "exact_name"

    @pytest.mark.asyncio
    @pytest.mark.mock_only
    async def test_resolve_entity_id_fuzzy_match_single(self):
        """Test resolve_entity_id with fuzzy match single result."""
        from tools.entity_resolver import EntityResolver
        
        mock_db = AsyncMock()
        mock_db.get_single = AsyncMock(return_value=None)
        mock_db.query = AsyncMock(return_value=[
            {"id": "1", "name": "Test Organization", "created_at": "2024-01-01"},
            {"id": "2", "name": "Other Org", "created_at": "2024-01-01"}
        ])
        
        resolver = EntityResolver(mock_db)
        
        # Mock rapidfuzz if available
        with patch('tools.entity_resolver.RAPIDFUZZ_AVAILABLE', True):
            with patch('tools.entity_resolver.process.extract', return_value=[
                ("Test Organization", 95.0, None)
            ]):
                result = await resolver.resolve_entity_id("organization", "Test Org")
                
                assert result["success"] is True
                assert result["match_type"] == "fuzzy"

    @pytest.mark.asyncio
    @pytest.mark.mock_only
    async def test_resolve_entity_id_fuzzy_match_multiple_with_suggestions(self):
        """Test resolve_entity_id with fuzzy match multiple results with suggestions."""
        from tools.entity_resolver import EntityResolver
        
        mock_db = AsyncMock()
        mock_db.get_single = AsyncMock(return_value=None)
        mock_db.query = AsyncMock(return_value=[
            {"id": "1", "name": "Test Org 1", "created_at": "2024-01-01"},
            {"id": "2", "name": "Test Org 2", "created_at": "2024-01-01"}
        ])
        
        resolver = EntityResolver(mock_db)
        
        with patch('tools.entity_resolver.RAPIDFUZZ_AVAILABLE', True):
            with patch('tools.entity_resolver.process.extract', return_value=[
                ("Test Org 1", 90.0, None),
                ("Test Org 2", 85.0, None)
            ]):
                result = await resolver.resolve_entity_id("organization", "Test", return_suggestions=True)
                
                assert result["success"] is False
                assert "suggestions" in result
                assert result["ambiguous"] is True

    @pytest.mark.asyncio
    @pytest.mark.mock_only
    async def test_resolve_entity_id_fuzzy_match_multiple_auto_select(self):
        """Test resolve_entity_id with fuzzy match multiple results auto-select."""
        from tools.entity_resolver import EntityResolver
        
        mock_db = AsyncMock()
        mock_db.get_single = AsyncMock(return_value=None)
        mock_db.query = AsyncMock(return_value=[
            {"id": "1", "name": "Test Org 1", "created_at": "2024-01-01"},
            {"id": "2", "name": "Test Org 2", "created_at": "2024-01-01"}
        ])
        
        resolver = EntityResolver(mock_db)
        
        with patch('tools.entity_resolver.RAPIDFUZZ_AVAILABLE', True):
            with patch('tools.entity_resolver.process.extract', return_value=[
                ("Test Org 1", 90.0, None),
                ("Test Org 2", 85.0, None)
            ]):
                result = await resolver.resolve_entity_id("organization", "Test", return_suggestions=False)
                
                assert result["success"] is True
                assert result["match_type"] == "fuzzy_best"
                assert "note" in result

    @pytest.mark.asyncio
    @pytest.mark.mock_only
    async def test_resolve_entity_id_fuzzy_match_no_rapidfuzz(self):
        """Test resolve_entity_id with fuzzy match without rapidfuzz."""
        from tools.entity_resolver import EntityResolver
        
        mock_db = AsyncMock()
        mock_db.get_single = AsyncMock(return_value=None)
        mock_db.query = AsyncMock(return_value=[
            {"id": "1", "name": "Test Organization", "created_at": "2024-01-01"}
        ])
        
        resolver = EntityResolver(mock_db)
        
        mock_entity_manager = MagicMock()
        mock_entity_manager._resolve_entity_table = MagicMock(return_value="organizations")
        
        with patch('tools.entity_resolver._entity_manager', mock_entity_manager):
            with patch('tools.entity_resolver.RAPIDFUZZ_AVAILABLE', False):
                with patch.object(resolver, '_is_uuid', return_value=False):
                    result = await resolver.resolve_entity_id("organization", "Test", threshold=50)
                    
                    assert result["success"] is True

    @pytest.mark.asyncio
    @pytest.mark.mock_only
    async def test_resolve_entity_id_no_matches(self):
        """Test resolve_entity_id with no matches."""
        from tools.entity_resolver import EntityResolver
        
        mock_db = AsyncMock()
        mock_db.get_single = AsyncMock(return_value=None)
        mock_db.query = AsyncMock(return_value=[])
        
        resolver = EntityResolver(mock_db)
        
        result = await resolver.resolve_entity_id("organization", "NonExistent")
        
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    @pytest.mark.mock_only
    async def test_resolve_entity_id_exception(self):
        """Test resolve_entity_id with exception."""
        from tools.entity_resolver import EntityResolver
        
        mock_db = AsyncMock()
        mock_db.get_single = AsyncMock(side_effect=Exception("DB error"))
        
        resolver = EntityResolver(mock_db)
        
        result = await resolver.resolve_entity_id("organization", "test")
        
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.mock_only
    def test_is_uuid(self):
        """Test _is_uuid method."""
        from tools.entity_resolver import EntityResolver
        
        resolver = EntityResolver(Mock())
        
        assert resolver._is_uuid("123e4567-e89b-12d3-a456-426614174000") is True
        assert resolver._is_uuid("123E4567-E89B-12D3-A456-426614174000") is True
        assert resolver._is_uuid("not-a-uuid") is False
        assert resolver._is_uuid("123") is False


# Continue with more test classes for other modules...
# This is a comprehensive start. Due to length, I'll create additional test files
# for the remaining modules.
