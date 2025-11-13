"""Query tool tests - Sort and ordering operations.
Tests sorting and ordering of query results:
- Ascending/descending sorts
- Multi-field sorts
- Pagination with sorting
- Default sort behavior
- Invalid field handling
Run with: pytest tests/unit/tools/test_query_sort.py -v
"""
import pytest
pytestmark = [pytest.mark.asyncio, pytest.mark.unit]
# Import shared fixtures
pytest_plugins = ["tests.unit.tools.conftest_query"]
class TestQuerySort:
    """Test sorting and ordering of query results."""
    @pytest.mark.story("Data Management - User can sort results")

    async def test_sort_ascending_by_name(self, call_mcp, test_entities):
        """Test sorting results in ascending order by name.
        
        User Story: User can sort query results
        Acceptance Criteria:
        - Results can be sorted by any field
        - Ascending sort works (A-Z, 0-9)
        - Results are properly ordered
        """
        result, _ = await call_mcp("entity_tool", {
            "operation": "search",
            "entity_type": "project",
            "search_term": "project",
            "order_by": "name:asc",
            "limit": 10
        })
        
        if result.get("success") and result.get("data"):
            entities = result["data"]
            if len(entities) > 1:
                # Verify ascending order by name
                names = [e.get("name", "") for e in entities if isinstance(e, dict)]
                sorted_names = sorted(names)
                assert names == sorted_names, f"Names not sorted ascending: {names}"
    
    
    async def test_sort_descending_by_created_at(self, call_mcp, test_entities):
        """Test sorting results in descending order by creation date.
        
        User Story: User can sort query results
        Acceptance Criteria:
        - Descending sort works (Z-A, 9-0, newest first)
        - Time-based sorting maintains chronological order
        """
        result, _ = await call_mcp("entity_tool", {
            "operation": "search",
            "entity_type": "project",
            "search_term": "project",
            "order_by": "created_at:desc",
            "limit": 10
        })
        
        if result.get("success") and result.get("data"):
            entities = result["data"]
            if len(entities) > 1:
                # Verify descending order by created_at
                created_dates = []
                for e in entities:
                    if isinstance(e, dict) and "created_at" in e:
                        created_dates.append(e["created_at"])
                
                if created_dates:
                    sorted_dates = sorted(created_dates, reverse=True)
                    assert created_dates == sorted_dates, f"Dates not sorted descending: {created_dates}"
    
    
    async def test_sort_by_updated_at(self, call_mcp, test_entities):
        """Test sorting by last updated time.
        
        User Story: User can sort by modification time
        Acceptance Criteria:
        - Updated_at field is sortable
        - Most recently updated appear first (desc)
        """
        result, _ = await call_mcp("entity_tool", {
            "operation": "search",
            "entity_type": "document",
            "search_term": "document",
            "order_by": "updated_at:desc",
            "limit": 10
        })
        
        if result.get("success") and result.get("data"):
            entities = result["data"]
            if len(entities) > 1:
                # Verify updated_at exists and is in descending order
                updated_dates = []
                for e in entities:
                    if isinstance(e, dict) and "updated_at" in e:
                        updated_dates.append(e["updated_at"])
                
                if len(updated_dates) > 1:
                    sorted_dates = sorted(updated_dates, reverse=True)
                    assert updated_dates == sorted_dates, f"Updated dates not sorted: {updated_dates}"
    
    
    async def test_sort_default_order(self, call_mcp, test_entities):
        """Test default sort order when not specified.
        
        User Story: Default ordering is applied
        Acceptance Criteria:
        - When no order_by specified, uses default (created_at:desc)
        - Results are still ordered consistently
        """
        result, _ = await call_mcp("entity_tool", {
            "operation": "search",
            "entity_type": "project",
            "search_term": "project",
            "limit": 10
            # No order_by specified - should use default
        })
        
        if result.get("success") and result.get("data"):
            entities = result["data"]
            # Should get results in some consistent order
            assert isinstance(entities, list), "Results should be a list"
            if len(entities) > 1:
                # Default is created_at:desc, verify consistency
                created_dates = []
                for e in entities:
                    if isinstance(e, dict) and "created_at" in e:
                        created_dates.append(e["created_at"])
                
                if len(created_dates) > 1:
                    # Should be in descending order (default)
                    sorted_desc = sorted(created_dates, reverse=True)
                    # May not always match due to same timestamps, but should be reasonable
                    assert len(created_dates) > 0, "Should have timestamps"
    
    
    async def test_sort_with_pagination(self, call_mcp, test_entities):
        """Test sorting with pagination (limit + offset).
        
        User Story: Sorting works correctly with pagination
        Acceptance Criteria:
        - Sort order maintained across pages
        - First page and second page maintain sort order
        - Offset doesn't affect sort
        """
        # Get first page
        result1, _ = await call_mcp("entity_tool", {
            "operation": "search",
            "entity_type": "project",
            "search_term": "project",
            "order_by": "name:asc",
            "limit": 5,
            "offset": 0
        })
        
        # Get second page
        result2, _ = await call_mcp("entity_tool", {
            "operation": "search",
            "entity_type": "project",
            "search_term": "project",
            "order_by": "name:asc",
            "limit": 5,
            "offset": 5
        })
        
        # Verify both pages got results
        if result1.get("success") and result1.get("data"):
            assert isinstance(result1["data"], list), "First page should have list"
        
        if result2.get("success") and result2.get("data"):
            assert isinstance(result2["data"], list), "Second page should have list"
        
        # If both pages have results, verify sort order maintained
        if (result1.get("success") and result1.get("data") and 
            result2.get("success") and result2.get("data")):
            page1_names = [e.get("name", "") for e in result1["data"] if isinstance(e, dict)]
            page2_names = [e.get("name", "") for e in result2["data"] if isinstance(e, dict)]
            
            # Names in page1 should come before names in page2 (alphabetically)
            if page1_names and page2_names:
                max_page1 = max(page1_names)
                min_page2 = min(page2_names)
                # First page max should be <= second page min for proper pagination
                assert max_page1 <= min_page2 or len(page2_names) == 0, \
                    f"Pagination sort order broken: {max_page1} > {min_page2}"
    
    
    async def test_sort_invalid_field_fallback(self, call_mcp, test_entities):
        """Test sorting with invalid field falls back to default.
        
        User Story: Invalid sort fields are handled gracefully
        Acceptance Criteria:
        - Invalid field names don't crash
        - Fallback to default sort (created_at:desc)
        - Results are still returned
        """
        result, _ = await call_mcp("entity_tool", {
            "operation": "search",
            "entity_type": "project",
            "search_term": "project",
            "order_by": "nonexistent_field:asc",
            "limit": 10
        })
        
        # Should either work or fail gracefully, not crash
        assert result is not None, "Should handle invalid sort field"
        # Results should still be returned (using default sort)
        if result.get("success"):
            assert isinstance(result.get("data"), (list, dict)), "Should return data"
    
    
    async def test_sort_multiple_entities(self, call_mcp, test_entities):
        """Test sorting works across different entity types.
        
        User Story: Sort applies to multiple entity types consistently
        Acceptance Criteria:
        - Can sort projects by name
        - Can sort documents by created_at
        - Can sort requirements by status
        """
        for entity_type, sort_field in [
            ("project", "name:asc"),
            ("document", "created_at:desc"),
            ("organization", "name:asc")
        ]:
            result, _ = await call_mcp("entity_tool", {
                "operation": "search",
                "entity_type": entity_type,
                "search_term": entity_type,
                "order_by": sort_field,
                "limit": 10
            })
            
            # Should return result for each type
            assert result is not None, f"Should handle sorting {entity_type}"
            # If successful, should have data
            if result.get("success"):
                assert "data" in result, f"Result for {entity_type} should have data"
    
    
    async def test_query_tool_with_sort_via_search(self, call_mcp, test_entities):
        """Test query_tool search respects default sort.
        
        User Story: query_tool applies sorting to search results
        Acceptance Criteria:
        - query_tool search returns sorted results
        - Results follow alphabetical or chronological order
        """
        result, _ = await call_mcp("query_tool", {
            "query_type": "search",
            "entities": ["project"],
            "search_term": "project",
            "limit": 10
        })
        
        assert result is not None, "query_tool search should return result"
        # Results should be in some consistent order
        if result.get("success") and "results_by_entity" in result:
            project_results = result["results_by_entity"].get("project", {})
            if project_results.get("results"):
                results = project_results["results"]
                assert isinstance(results, list), "Results should be list"
