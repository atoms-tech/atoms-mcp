"""Smart assertion helpers with rich, descriptive error messages.

Instead of generic AssertionError, these provide context-aware feedback
that helps developers understand exactly what failed and why.
"""

from typing import Any, Dict, List, Optional


class SmartAssert:
    """Assertions with descriptive, context-aware error messages."""
    
    @staticmethod
    def response_ok(response: Any, message: str = ""):
        """Assert HTTP response is successful (200-299)."""
        if not (200 <= response.status_code < 300):
            raise AssertionError(f"""
❌ HTTP Response Error

Expected: HTTP 200-299 (success)
Got: HTTP {response.status_code}

{f'Message: {message}' if message else ''}
Response body: {getattr(response, 'data', getattr(response, 'text', 'N/A'))}

How to debug:
1. Check MCP server logs: docker logs atoms_mcp
2. Verify endpoint exists and is working
3. Check authentication/authorization
4. Verify request payload is valid
""")
    
    @staticmethod
    def has_id(obj: Any, entity_type: str = "entity"):
        """Assert object has a valid ID."""
        if not hasattr(obj, 'id') or not obj.id:
            raise AssertionError(f"""
❌ Missing {entity_type} ID

Expected: {entity_type} with valid ID field
Got: {obj}

This usually means:
- {entity_type} creation failed silently
- Database insert didn't return ID
- Response parsing is broken

How to fix:
1. Check tool implementation: tools/*.py
2. Verify database is accessible
3. Check response format matches spec
""")
    
    @staticmethod
    def field_equals(obj: Any, field: str, expected: Any, obj_name: str = "response"):
        """Assert object field equals expected value with context."""
        actual = getattr(obj, field, "FIELD_NOT_FOUND")
        if actual != expected:
            raise AssertionError(f"""
❌ Field Value Mismatch

Field: {obj_name}.{field}
Expected: {expected!r}
Got: {actual!r}

Object: {obj}

Why this matters:
- {field} has wrong value
- May indicate business logic error
- Could be data transformation issue

How to debug:
1. Print full object: print({obj_name})
2. Check tool implementation for field assignment
3. Verify transformation logic
4. Check for type conversion issues
""")
    
    @staticmethod
    def list_contains(items: List[Any], expected_count: Optional[int] = None,
                     item_type: str = "items", min_count: int = 0):
        """Assert list has items with helpful context."""
        actual_count = len(items)
        
        if actual_count < min_count:
            raise AssertionError(f"""
❌ List Does Not Contain Enough Items

Expected: ≥ {min_count} {item_type}
Got: {actual_count} {item_type}

Items: {items}

Why this matters:
- Query returned empty/incomplete results
- Data not created or filtered incorrectly
- Service may be failing silently

How to debug:
1. Check data exists: `SELECT COUNT(*) FROM {item_type}s`
2. Verify filter logic
3. Check service logging
4. Run query directly against database
""")
        
        if expected_count is not None and actual_count != expected_count:
            raise AssertionError(f"""
❌ List Item Count Mismatch

Expected: {expected_count} {item_type}
Got: {actual_count} {item_type}

Items: {items}

How to debug:
1. Check filtering is correct
2. Verify pagination offset/limit
3. Check for duplicates
4. Trace query building logic
""")
    
    @staticmethod
    def field_not_null(obj: Any, field: str, obj_name: str = "response"):
        """Assert field is not null with context."""
        value = getattr(obj, field, "FIELD_NOT_FOUND")
        
        if value is None or value == "FIELD_NOT_FOUND":
            raise AssertionError(f"""
❌ Required Field is Null/Missing

Field: {obj_name}.{field}
Expected: Non-null value
Got: {value!r}

Object: {obj}

Why this matters:
- {field} is required but wasn't set
- Tool implementation missing this field
- Database constraint violated

How to fix:
1. Check tool sets this field: grep -n "{field}" tools/*.py
2. Verify database schema has column
3. Check ORM/mapper includes this field
4. Add field to response if missing

Example fix:
    result['{field}'] = generated_value  # Add this line
""")
    
    @staticmethod
    def no_error(result: Any, error_field: str = "error"):
        """Assert result contains no error."""
        error = getattr(result, error_field, None)
        if error:
            raise AssertionError(f"""
❌ Unexpected Error in Response

Error: {error}
Full response: {result}

This indicates:
- Tool implementation threw exception
- Business logic validation failed
- Database constraint violated

How to debug:
1. Check MCP tool logs for stack trace
2. Review business validation logic
3. Check database constraints
4. Run tool directly: curl -X POST /mcp ...
""")
    
    @staticmethod
    def entity_created(response: Any, entity_type: str = "entity"):
        """Assert entity was successfully created."""
        SmartAssert.response_ok(response, f"{entity_type} creation")
        SmartAssert.has_id(response, entity_type)
        SmartAssert.field_not_null(response, "created_at", entity_type)
    
    @staticmethod
    def entity_deleted(response: Any, entity_type: str = "entity"):
        """Assert entity was successfully deleted."""
        SmartAssert.response_ok(response, f"{entity_type} deletion")
        
        # Check for soft-delete flag
        if hasattr(response, "is_deleted"):
            if not response.is_deleted:
                raise AssertionError(f"""
❌ Entity Not Marked as Deleted

Expected: is_deleted = True
Got: is_deleted = {response.is_deleted}

This indicates:
- Delete endpoint didn't set is_deleted flag
- Soft-delete logic not implemented
- Tool not updating database correctly

How to fix:
1. Check tools/entity.py delete_entity() implementation
2. Ensure UPDATE query sets is_deleted = True
3. Verify timestamp updated: deleted_at = NOW()

Example fix:
    async def delete_entity(self, entity_id: str):
        return await self.db.update(
            "entities",
            {"is_deleted": True, "deleted_at": now()},
            {"id": entity_id}
        )
""")
    
    @staticmethod
    def query_returns_results(response: Any, item_type: str = "items"):
        """Assert query returned results."""
        SmartAssert.response_ok(response, f"query for {item_type}")
        
        items = getattr(response, "data", [])
        if not items:
            raise AssertionError(f"""
❌ Query Returned No Results

Expected: At least 1 {item_type}
Got: 0 {item_type}
Response: {response}

Why this matters:
- Data was created but query can't find it
- Filter logic is too restrictive
- Search service not working
- RLS/permissions hiding results

How to debug:
1. Check data exists: SELECT * FROM {item_type}s LIMIT 5
2. Verify WHERE clause in query
3. Check RLS policies allow access
4. Test search separately: pytest tests/unit/tools/test_query.py -v
""")
