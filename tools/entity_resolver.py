"""Fuzzy entity resolution for natural language-friendly tool inputs."""

from __future__ import annotations

import re
from typing import Any

from schemas.constants import TABLES_WITHOUT_SOFT_DELETE
from utils.logging_setup import get_logger

logger = get_logger(__name__)

# Try to import rapidfuzz, fall back to basic matching if not available
try:
    from rapidfuzz import fuzz, process
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    logger.warning("rapidfuzz not available - fuzzy matching will use basic string comparison")
    RAPIDFUZZ_AVAILABLE = False


class EntityResolver:
    """Resolves entity names/partial IDs to full entity IDs using fuzzy matching."""

    def __init__(self, db_adapter):
        """Initialize resolver with database adapter.

        Args:
            db_adapter: Database adapter for querying entities
        """
        self.db = db_adapter

    def _is_uuid(self, value: str) -> bool:
        """Check if string looks like a UUID."""
        uuid_pattern = re.compile(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
            re.IGNORECASE
        )
        return bool(uuid_pattern.match(value))

    async def resolve_entity_id(
        self,
        entity_type: str,
        identifier: str,
        filters: dict[str, Any] | None = None,
        threshold: int = 70,
        return_suggestions: bool = False
    ) -> dict[str, Any]:
        """Resolve partial name or ID to full entity.

        Args:
            entity_type: Type of entity to search
            identifier: UUID, exact name, or partial name
            filters: Additional filters to narrow search
            threshold: Minimum fuzzy match score (0-100)
            return_suggestions: If True, return top matches on ambiguity

        Returns:
            Dict with:
            - success: bool
            - entity_id: str (if single match)
            - entity: dict (if single match)
            - suggestions: list (if multiple matches or return_suggestions=True)
            - error: str (if no matches)
        """
        try:
            # Resolve table name
            from tools.entity import _entity_manager
            table = _entity_manager._resolve_entity_table(entity_type)

            # If it's a valid UUID, try direct lookup first
            if self._is_uuid(identifier):
                query_filters = filters.copy() if filters else {}
                query_filters["id"] = identifier

                # Skip is_deleted for tables without it
                if table not in TABLES_WITHOUT_SOFT_DELETE:
                    query_filters.setdefault("is_deleted", False)

                entity = await self.db.get_single(table, filters=query_filters)
                if entity:
                    return {
                        "success": True,
                        "entity_id": entity["id"],
                        "entity": entity,
                        "match_type": "exact_uuid"
                    }

            # Search by name (exact or fuzzy)
            search_filters = filters.copy() if filters else {}
            tables_without_soft_delete = {"test_req", "properties"}
            if table not in tables_without_soft_delete:
                search_filters.setdefault("is_deleted", False)

            # Get all matching entities
            entities = await self.db.query(
                table,
                select="id, name, created_at, updated_at",
                filters=search_filters,
                limit=100  # Reasonable limit for fuzzy matching
            )

            if not entities:
                return {
                    "success": False,
                    "error": f"No {entity_type} entities found matching filters"
                }

            # Try exact name match first
            exact_matches = [e for e in entities if e.get("name", "").lower() == identifier.lower()]
            if len(exact_matches) == 1:
                entity = exact_matches[0]
                return {
                    "success": True,
                    "entity_id": entity["id"],
                    "entity": entity,
                    "match_type": "exact_name"
                }

            # Fuzzy matching
            if RAPIDFUZZ_AVAILABLE:
                # Use RapidFuzz for high-performance fuzzy matching
                entity_names = [(e.get("name", ""), e) for e in entities]
                matches = process.extract(
                    identifier,
                    [name for name, _ in entity_names],
                    scorer=fuzz.WRatio,  # Weighted ratio for best overall performance
                    limit=5,
                    score_cutoff=threshold
                )

                # Convert to results with entities
                results = []
                for match_name, score, _ in matches:
                    entity = next(e for name, e in entity_names if name == match_name)
                    results.append({
                        "name": entity.get("name"),
                        "id": entity["id"],
                        "score": round(score, 1),
                        "created_at": entity.get("created_at")
                    })
            else:
                # Fallback: basic substring matching
                results = []
                identifier_lower = identifier.lower()
                for entity in entities:
                    name = entity.get("name", "")
                    if identifier_lower in name.lower():
                        # Simple scoring: length of match / total length
                        score = (len(identifier) / len(name)) * 100 if name else 0
                        if score >= threshold:
                            results.append({
                                "name": name,
                                "id": entity["id"],
                                "score": round(score, 1),
                                "created_at": entity.get("created_at")
                            })

                # Sort by score descending
                results.sort(key=lambda x: x["score"], reverse=True)
                results = results[:5]

            # Return results
            if len(results) == 1:
                return {
                    "success": True,
                    "entity_id": results[0]["id"],
                    "entity": results[0],
                    "match_type": "fuzzy",
                    "score": results[0]["score"]
                }
            if len(results) > 1:
                if return_suggestions:
                    return {
                        "success": False,
                        "error": "Multiple matches found - please be more specific",
                        "suggestions": results,
                        "ambiguous": True
                    }
                # Return best match
                return {
                    "success": True,
                    "entity_id": results[0]["id"],
                    "entity": results[0],
                    "match_type": "fuzzy_best",
                    "score": results[0]["score"],
                    "note": f"Auto-selected best match (score: {results[0]['score']}). {len(results)-1} other matches found."
                }
            return {
                "success": False,
                "error": f"No {entity_type} found matching '{identifier}' (threshold: {threshold}%)"
            }

        except Exception as e:
            logger.error(f"Entity resolution failed: {e}")
            return {
                "success": False,
                "error": f"Resolution error: {e!s}"
            }
