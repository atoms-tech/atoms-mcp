"""Advanced Search for Atoms MCP - Full-text and advanced search capabilities.

Provides advanced search filters, full-text search, and search optimization.
"""

import logging
import re
from typing import Dict, Any, List, Optional, Set
from datetime import datetime

logger = logging.getLogger(__name__)


class AdvancedSearch:
    """Advanced search engine for entities."""

    def __init__(self):
        """Initialize advanced search."""
        self.search_index = {}

    def full_text_search(
        self,
        entities: List[Dict[str, Any]],
        query: str,
        fields: Optional[List[str]] = None,
        case_sensitive: bool = False
    ) -> List[Dict[str, Any]]:
        """Perform full-text search on entities.
        
        Args:
            entities: List of entities to search
            query: Search query
            fields: Fields to search in (default: all)
            case_sensitive: Whether search is case-sensitive
            
        Returns:
            List of matching entities
        """
        if not query:
            return []

        search_query = query if case_sensitive else query.lower()
        results = []

        for entity in entities:
            if self._matches_full_text(entity, search_query, fields, case_sensitive):
                results.append(entity)

        return results

    def filter_search(
        self,
        entities: List[Dict[str, Any]],
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Filter entities by multiple criteria.
        
        Args:
            entities: List of entities to filter
            filters: Filter criteria dict
            
        Returns:
            List of matching entities
        """
        results = entities

        for field, value in filters.items():
            results = [
                e for e in results
                if self._matches_filter(e, field, value)
            ]

        return results

    def combined_search(
        self,
        entities: List[Dict[str, Any]],
        query: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Perform combined full-text and filter search.
        
        Args:
            entities: List of entities to search
            query: Full-text search query
            filters: Filter criteria
            limit: Result limit
            offset: Result offset
            
        Returns:
            Search results dict
        """
        results = entities

        # Apply full-text search
        if query:
            results = self.full_text_search(results, query)

        # Apply filters
        if filters:
            results = self.filter_search(results, filters)

        # Apply pagination
        total = len(results)
        paginated = results[offset:offset + limit]

        return {
            "results": paginated,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_next": offset + limit < total,
            "has_previous": offset > 0
        }

    def faceted_search(
        self,
        entities: List[Dict[str, Any]],
        facet_fields: List[str],
        query: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Perform faceted search.
        
        Args:
            entities: List of entities to search
            facet_fields: Fields to facet on
            query: Full-text search query
            filters: Filter criteria
            
        Returns:
            Faceted search results dict
        """
        # Apply search
        results = entities

        if query:
            results = self.full_text_search(results, query)

        if filters:
            results = self.filter_search(results, filters)

        # Build facets
        facets = {}
        for field in facet_fields:
            facets[field] = self._build_facet(results, field)

        return {
            "results": results,
            "facets": facets,
            "total": len(results)
        }

    def suggest(
        self,
        entities: List[Dict[str, Any]],
        prefix: str,
        field: str = "name",
        limit: int = 10
    ) -> List[str]:
        """Get search suggestions based on prefix.
        
        Args:
            entities: List of entities
            prefix: Search prefix
            field: Field to suggest from
            limit: Maximum suggestions
            
        Returns:
            List of suggestions
        """
        suggestions = set()
        prefix_lower = prefix.lower()

        for entity in entities:
            value = entity.get(field, "")
            if isinstance(value, str) and value.lower().startswith(prefix_lower):
                suggestions.add(value)

        return sorted(list(suggestions))[:limit]

    def _matches_full_text(
        self,
        entity: Dict[str, Any],
        query: str,
        fields: Optional[List[str]],
        case_sensitive: bool
    ) -> bool:
        """Check if entity matches full-text query.
        
        Args:
            entity: Entity to check
            query: Search query
            fields: Fields to search
            case_sensitive: Case sensitivity
            
        Returns:
            True if matches
        """
        search_fields = fields or entity.keys()

        for field in search_fields:
            value = entity.get(field, "")
            if isinstance(value, str):
                text = value if case_sensitive else value.lower()
                if query in text:
                    return True

        return False

    def _matches_filter(
        self,
        entity: Dict[str, Any],
        field: str,
        value: Any
    ) -> bool:
        """Check if entity matches filter.
        
        Args:
            entity: Entity to check
            field: Field to filter on
            value: Filter value
            
        Returns:
            True if matches
        """
        entity_value = entity.get(field)

        if isinstance(value, list):
            return entity_value in value
        elif isinstance(value, dict):
            # Range filter
            if "min" in value and entity_value < value["min"]:
                return False
            if "max" in value and entity_value > value["max"]:
                return False
            return True
        else:
            return entity_value == value

    def _build_facet(
        self,
        entities: List[Dict[str, Any]],
        field: str
    ) -> Dict[str, int]:
        """Build facet for field.
        
        Args:
            entities: List of entities
            field: Field to facet on
            
        Returns:
            Facet dict with counts
        """
        facet = {}

        for entity in entities:
            value = entity.get(field)
            if value is not None:
                facet[str(value)] = facet.get(str(value), 0) + 1

        return facet


# Global advanced search instance
_advanced_search = None


def get_advanced_search() -> AdvancedSearch:
    """Get global advanced search instance."""
    global _advanced_search
    if _advanced_search is None:
        _advanced_search = AdvancedSearch()
    return _advanced_search

