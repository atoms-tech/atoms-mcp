"""Base functionality for consolidated tools."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

# Support both package and standalone imports
try:
    from ..infrastructure.factory import get_adapters
    from ..errors import normalize_error
except ImportError:
    from infrastructure.factory import get_adapters
    from errors import normalize_error

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
        """Validate authentication token and return user info.

        Also sets user's JWT on database adapter for proper RLS context.
        """
        # No fallback - require valid authentication
        if auth_token == "oauth-session" or not auth_token:
            raise ValueError("Authentication required: user_id not found in token claims")

        try:
            adapters = self._get_adapters()
            user_info = await adapters["auth"].validate_token(auth_token)

            # ✅ Set user's access token on database adapter for RLS
            # This ensures auth.uid() returns the correct user ID in database queries
            if access_token := user_info.get("access_token"):
                adapters["database"].set_access_token(access_token)

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
    
    @property
    def supabase(self):
        """Get Supabase client from adapters."""
        try:
            adapters = self._get_adapters()
            db_adapter = adapters["database"]
            # Use the _get_client method from SupabaseDatabaseAdapter
            return db_adapter._get_client()
        except Exception:
            # Fallback: try to get it directly from supabase_client module
            try:
                from supabase_client import get_supabase
                return get_supabase()
            except Exception as e:
                raise RuntimeError(f"Could not get Supabase client: {e}")
    
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
    
    def _sanitize_entity(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """Remove large fields from entity to prevent token overflow.

        Strips out embedding vectors, large text fields, and nested structures
        while preserving essential identifying information.
        """
        if not entity:
            return {}

        # Fields to always exclude (commonly large or redundant)
        exclude_fields = {
            'embedding',  # Vector embeddings are huge (768 floats)
            'properties',  # Can contain arbitrary large nested data
            'metadata',  # Can be recursive
            'blocks',  # Large nested structures
            'requirements',  # Large arrays
            'tests',  # Large arrays
            'trace_links',  # Large arrays
            'ai_analysis',  # Can be very large with history
        }

        # Keep only essential fields
        sanitized = {}
        for key, value in entity.items():
            if key in exclude_fields:
                continue

            # Skip None values
            if value is None:
                continue

            # Include primitives and small values
            if isinstance(value, (str, int, float, bool)):
                # Limit string length
                if isinstance(value, str) and len(value) > 200:
                    sanitized[key] = value[:200] + "..."
                else:
                    sanitized[key] = value
            elif isinstance(value, dict) and len(str(value)) < 500:
                sanitized[key] = value
            elif isinstance(value, list) and len(value) < 10:
                sanitized[key] = value

        return sanitized

    def _format_result(self, data: Any, format_type: str = "detailed") -> Dict[str, Any]:
        """Format result data based on requested format."""
        # Always sanitize data before formatting to prevent token overflow
        if isinstance(data, list):
            data = [self._sanitize_entity(item) if isinstance(item, dict) else item for item in data]
        elif isinstance(data, dict):
            data = self._sanitize_entity(data)

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
