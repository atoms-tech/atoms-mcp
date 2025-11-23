"""Composition Engine for Atoms MCP - Entity and relationship composition.

Provides entity composition, relationship composition, and composition caching.
"""

import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
import hashlib

logger = logging.getLogger(__name__)


class CompositionEngine:
    """Engine for composing entities and relationships."""

    def __init__(self, cache_ttl_seconds: int = 3600):
        """Initialize composition engine.
        
        Args:
            cache_ttl_seconds: Cache time-to-live in seconds
        """
        self.cache_ttl = cache_ttl_seconds
        self.composition_cache = {}
        self.cache_timestamps = {}

    def compose_entity(
        self,
        entity: Dict[str, Any],
        include_relations: bool = True,
        include_metadata: bool = True,
        depth: int = 1
    ) -> Dict[str, Any]:
        """Compose entity with related data.
        
        Args:
            entity: Base entity
            include_relations: Include related entities
            include_metadata: Include metadata
            depth: Composition depth (1-3)
            
        Returns:
            Composed entity dict
        """
        if depth < 1 or depth > 3:
            depth = 1

        # Check cache
        cache_key = self._get_cache_key(entity, depth)
        if self._is_cached(cache_key):
            return self.composition_cache[cache_key]

        composed = {
            "id": entity.get("id"),
            "type": entity.get("type"),
            "data": entity.copy()
        }

        if include_relations:
            composed["relations"] = self._compose_relations(entity, depth - 1)

        if include_metadata:
            composed["metadata"] = {
                "composed_at": datetime.now().isoformat(),
                "depth": depth,
                "cached": False
            }

        # Cache result
        self.composition_cache[cache_key] = composed
        self.cache_timestamps[cache_key] = datetime.now()

        return composed

    def compose_relationship(
        self,
        source: Dict[str, Any],
        target: Dict[str, Any],
        relationship_type: str,
        include_context: bool = True
    ) -> Dict[str, Any]:
        """Compose relationship with context.
        
        Args:
            source: Source entity
            target: Target entity
            relationship_type: Type of relationship
            include_context: Include context data
            
        Returns:
            Composed relationship dict
        """
        composed = {
            "id": f"{source.get('id')}-{target.get('id')}",
            "type": relationship_type,
            "source": {
                "id": source.get("id"),
                "type": source.get("type")
            },
            "target": {
                "id": target.get("id"),
                "type": target.get("type")
            },
            "created_at": datetime.now().isoformat()
        }

        if include_context:
            composed["context"] = {
                "source_data": source,
                "target_data": target
            }

        return composed

    def compose_batch(
        self,
        entities: List[Dict[str, Any]],
        include_relations: bool = True,
        depth: int = 1
    ) -> List[Dict[str, Any]]:
        """Compose multiple entities.
        
        Args:
            entities: List of entities
            include_relations: Include related entities
            depth: Composition depth
            
        Returns:
            List of composed entities
        """
        return [
            self.compose_entity(entity, include_relations, depth=depth)
            for entity in entities
        ]

    def clear_cache(self) -> None:
        """Clear composition cache."""
        self.composition_cache.clear()
        self.cache_timestamps.clear()
        logger.info("Composition cache cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Cache stats dict
        """
        return {
            "total_entries": len(self.composition_cache),
            "cache_size_bytes": sum(
                len(str(v).encode()) for v in self.composition_cache.values()
            ),
            "ttl_seconds": self.cache_ttl
        }

    def _compose_relations(
        self,
        entity: Dict[str, Any],
        remaining_depth: int
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Compose entity relations.
        
        Args:
            entity: Entity to compose relations for
            remaining_depth: Remaining composition depth
            
        Returns:
            Relations dict
        """
        if remaining_depth <= 0:
            return {}

        # Placeholder for relation composition
        # In real implementation, would fetch related entities
        return {
            "incoming": [],
            "outgoing": []
        }

    def _get_cache_key(
        self,
        entity: Dict[str, Any],
        depth: int
    ) -> str:
        """Get cache key for entity.
        
        Args:
            entity: Entity
            depth: Composition depth
            
        Returns:
            Cache key
        """
        key_str = f"{entity.get('id')}-{entity.get('type')}-{depth}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def _is_cached(self, cache_key: str) -> bool:
        """Check if cache entry is valid.
        
        Args:
            cache_key: Cache key
            
        Returns:
            True if cached and not expired
        """
        if cache_key not in self.composition_cache:
            return False

        timestamp = self.cache_timestamps.get(cache_key)
        if timestamp is None:
            return False

        age = datetime.now() - timestamp
        if age > timedelta(seconds=self.cache_ttl):
            # Expired, remove from cache
            del self.composition_cache[cache_key]
            del self.cache_timestamps[cache_key]
            return False

        return True


# Global composition engine instance
_composition_engine = None


def get_composition_engine() -> CompositionEngine:
    """Get global composition engine instance."""
    global _composition_engine
    if _composition_engine is None:
        _composition_engine = CompositionEngine()
    return _composition_engine

