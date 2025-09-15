"""Base functionality for consolidated tools."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from ..infrastructure.factory import get_adapters
from ..errors import normalize_error

logger = logging.getLogger(__name__)


class ToolBase:
    """Base class for consolidated tools with common functionality."""
    
    def __init__(self):
        self._adapters = None
        self._user_context = {}
    
    def _get_adapters(self) -> Dict[str, Any]:
        """Get adapters, cached."""
        if self._adapters is None:
            self._adapters = get_adapters()
        return self._adapters
    
    async def _validate_auth(self, auth_token: str) -> Dict[str, Any]:
        """Validate authentication token and return user info."""
        try:
            adapters = self._get_adapters()
            user_info = await adapters["auth"].validate_token(auth_token)
            
            # Cache user context for this operation
            self._user_context = user_info
            return user_info
            
        except Exception as e:
            raise normalize_error(e, "Authentication failed")
    
    def _get_user_id(self) -> str:
        """Get current user ID from context."""
        return self._user_context.get("user_id", "")
    
    def _get_username(self) -> str:
        """Get current username from context."""
        return self._user_context.get("username", "")
    
    async def _db_query(self, table: str, **kwargs) -> list:
        """Execute database query."""
        try:
            adapters = self._get_adapters()
            return await adapters["database"].query(table, **kwargs)
        except Exception as e:
            raise normalize_error(e, f"Database query failed for table {table}")
    
    async def _db_get_single(self, table: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Get single record from database."""
        try:
            adapters = self._get_adapters()
            return await adapters["database"].get_single(table, **kwargs)
        except Exception as e:
            raise normalize_error(e, f"Database get_single failed for table {table}")
    
    async def _db_insert(self, table: str, data: Any, **kwargs) -> Any:
        """Insert record(s) into database."""
        try:
            adapters = self._get_adapters()
            return await adapters["database"].insert(table, data, **kwargs)
        except Exception as e:
            raise normalize_error(e, f"Database insert failed for table {table}")
    
    async def _db_update(self, table: str, data: Dict[str, Any], filters: Dict[str, Any], **kwargs) -> Any:
        """Update record(s) in database."""
        try:
            adapters = self._get_adapters()
            return await adapters["database"].update(table, data, filters, **kwargs)
        except Exception as e:
            raise normalize_error(e, f"Database update failed for table {table}")
    
    async def _db_delete(self, table: str, filters: Dict[str, Any]) -> int:
        """Delete record(s) from database."""
        try:
            adapters = self._get_adapters()
            return await adapters["database"].delete(table, filters)
        except Exception as e:
            raise normalize_error(e, f"Database delete failed for table {table}")
    
    async def _db_count(self, table: str, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records in database table."""
        try:
            adapters = self._get_adapters()
            return await adapters["database"].count(table, filters)
        except Exception as e:
            raise normalize_error(e, f"Database count failed for table {table}")
    
    def _resolve_entity_table(self, entity_type: str) -> str:
        """Map entity type to database table name."""
        entity_table_map = {
            "organization": "organizations",
            "project": "projects", 
            "document": "documents",
            "requirement": "requirements",
            "test": "test_req",
            "property": "properties",
            "block": "blocks",
            "column": "columns",
            "trace_link": "trace_links",
            "assignment": "assignments",
            "audit_log": "audit_logs",
            "notification": "notifications",
            "external_document": "external_documents",
            "test_matrix_view": "test_matrix_views",
            "organization_member": "organization_members",
            "project_member": "project_members",
            "organization_invitation": "organization_invitations",
            "requirement_test": "requirement_tests",
            "profile": "profiles"
        }
        
        table = entity_table_map.get(entity_type.lower())
        if not table:
            raise ValueError(f"Unknown entity type: {entity_type}")
        return table
    
    def _format_result(self, data: Any, format_type: str = "detailed") -> Dict[str, Any]:
        """Format result data based on requested format."""
        if format_type == "raw":
            return {"data": data}
        elif format_type == "summary":
            if isinstance(data, list):
                return {
                    "count": len(data),
                    "items": data[:3] if len(data) > 3 else data,
                    "truncated": len(data) > 3
                }
            else:
                return {"summary": str(data)[:200] + "..." if len(str(data)) > 200 else str(data)}
        else:  # detailed
            return {
                "success": True,
                "data": data,
                "count": len(data) if isinstance(data, list) else 1,
                "user_id": self._get_user_id(),
                "timestamp": __import__("datetime").datetime.utcnow().isoformat() + "Z"
            }