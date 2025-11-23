"""Fuzzy matching utility for error suggestions and entity lookup.

Provides fuzzy matching capabilities to suggest similar entity IDs or names
when an invalid ID is provided, improving error recovery experience.
"""

from difflib import SequenceMatcher
from typing import List, Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class FuzzyMatcher:
    """Fuzzy matching utility for entity suggestions."""

    @staticmethod
    def similarity_ratio(a: str, b: str) -> float:
        """Calculate similarity ratio between two strings (0.0 to 1.0).
        
        Args:
            a: First string
            b: Second string
            
        Returns:
            Similarity ratio (0.0 = no match, 1.0 = exact match)
        """
        if not a or not b:
            return 0.0
        
        # Normalize strings for comparison
        a_lower = str(a).lower().strip()
        b_lower = str(b).lower().strip()
        
        # Exact match
        if a_lower == b_lower:
            return 1.0
        
        # Use SequenceMatcher for fuzzy matching
        return SequenceMatcher(None, a_lower, b_lower).ratio()

    @staticmethod
    def find_similar(
        query: str,
        candidates: List[str],
        threshold: float = 0.6,
        limit: int = 3
    ) -> List[Tuple[str, float]]:
        """Find similar strings from candidates.
        
        Args:
            query: String to match
            candidates: List of candidate strings
            threshold: Minimum similarity ratio (0.0 to 1.0)
            limit: Maximum number of results
            
        Returns:
            List of (candidate, similarity_ratio) tuples, sorted by similarity
        """
        if not query or not candidates:
            return []
        
        # Calculate similarity for each candidate
        matches = []
        for candidate in candidates:
            ratio = FuzzyMatcher.similarity_ratio(query, candidate)
            if ratio >= threshold:
                matches.append((candidate, ratio))
        
        # Sort by similarity (descending) and return top N
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:limit]

    @staticmethod
    def find_similar_entities(
        invalid_id: str,
        entities: List[Dict[str, Any]],
        threshold: float = 0.6,
        limit: int = 3,
        search_fields: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Find similar entities by ID or name.
        
        Args:
            invalid_id: Invalid ID that was provided
            entities: List of entity dictionaries
            threshold: Minimum similarity ratio
            limit: Maximum number of results
            search_fields: Fields to search (default: ["id", "name"])
            
        Returns:
            List of similar entities with similarity scores
        """
        if not invalid_id or not entities:
            return []
        
        if search_fields is None:
            search_fields = ["id", "name"]
        
        # Collect all searchable values
        candidates = []
        for entity in entities:
            for field in search_fields:
                value = entity.get(field)
                if value:
                    candidates.append({
                        "value": str(value),
                        "entity": entity,
                        "field": field
                    })
        
        # Find similar candidates
        matches = []
        for candidate in candidates:
            ratio = FuzzyMatcher.similarity_ratio(invalid_id, candidate["value"])
            if ratio >= threshold:
                matches.append({
                    "entity": candidate["entity"],
                    "field": candidate["field"],
                    "matched_value": candidate["value"],
                    "similarity": ratio
                })
        
        # Sort by similarity and return top N
        matches.sort(key=lambda x: x["similarity"], reverse=True)
        return matches[:limit]

    @staticmethod
    def format_suggestions(
        invalid_id: str,
        suggestions: List[Dict[str, Any]]
    ) -> List[str]:
        """Format suggestions for display in error messages.
        
        Args:
            invalid_id: Invalid ID that was provided
            suggestions: List of suggestion dictionaries
            
        Returns:
            List of formatted suggestion strings
        """
        formatted = []
        for i, suggestion in enumerate(suggestions, 1):
            entity = suggestion.get("entity", {})
            field = suggestion.get("field", "id")
            matched_value = suggestion.get("matched_value", "")
            similarity = suggestion.get("similarity", 0.0)
            
            # Format: "Entity Name (ID: entity-123) - 95% match"
            entity_name = entity.get("name", "Unknown")
            entity_id = entity.get("id", "unknown")
            similarity_pct = int(similarity * 100)
            
            formatted_str = f"{entity_name} (ID: {entity_id}) - {similarity_pct}% match"
            formatted.append(formatted_str)
        
        return formatted


def get_fuzzy_matcher() -> FuzzyMatcher:
    """Get FuzzyMatcher instance (singleton pattern)."""
    return FuzzyMatcher()

