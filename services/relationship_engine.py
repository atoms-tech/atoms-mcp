"""Relationship Engine for Atoms MCP - Entity relationship traversal and analysis.

Provides relationship traversal, dependency graph building, impact analysis,
and circular dependency detection.
"""

import logging
from typing import Dict, Any, List, Optional, Set, Tuple
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class RelationshipEngine:
    """Engine for traversing and analyzing entity relationships."""

    def __init__(self):
        """Initialize relationship engine."""
        self.relationships = defaultdict(list)
        self.dependency_cache = {}

    def add_relationship(
        self,
        source_id: str,
        target_id: str,
        relationship_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add relationship between entities.
        
        Args:
            source_id: Source entity ID
            target_id: Target entity ID
            relationship_type: Type of relationship
            metadata: Additional metadata
        """
        relationship = {
            "source": source_id,
            "target": target_id,
            "type": relationship_type,
            "metadata": metadata or {}
        }
        self.relationships[source_id].append(relationship)
        self.dependency_cache.clear()  # Invalidate cache

    def traverse_relationships(
        self,
        entity_id: str,
        depth: int = 3,
        relationship_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Traverse relationships from entity.
        
        Args:
            entity_id: Starting entity ID
            depth: Maximum traversal depth
            relationship_type: Filter by relationship type
            
        Returns:
            Traversal result dict
        """
        visited = set()
        result = {
            "root": entity_id,
            "depth": depth,
            "nodes": {},
            "edges": []
        }

        queue = deque([(entity_id, 0)])

        while queue:
            current_id, current_depth = queue.popleft()

            if current_id in visited or current_depth >= depth:
                continue

            visited.add(current_id)
            result["nodes"][current_id] = {
                "id": current_id,
                "depth": current_depth
            }

            # Get relationships
            for rel in self.relationships.get(current_id, []):
                if relationship_type and rel["type"] != relationship_type:
                    continue

                target_id = rel["target"]
                result["edges"].append({
                    "source": current_id,
                    "target": target_id,
                    "type": rel["type"],
                    "metadata": rel["metadata"]
                })

                if target_id not in visited:
                    queue.append((target_id, current_depth + 1))

        return result

    def build_dependency_graph(
        self,
        entity_id: str
    ) -> Dict[str, Any]:
        """Build dependency graph for entity.
        
        Args:
            entity_id: Entity ID
            
        Returns:
            Dependency graph dict
        """
        if entity_id in self.dependency_cache:
            return self.dependency_cache[entity_id]

        graph = {
            "root": entity_id,
            "dependencies": [],
            "dependents": [],
            "circular": []
        }

        # Find dependencies (outgoing)
        visited = set()
        self._find_dependencies(entity_id, graph["dependencies"], visited)

        # Find dependents (incoming)
        visited = set()
        self._find_dependents(entity_id, graph["dependents"], visited)

        # Detect circular dependencies
        graph["circular"] = self.detect_circular_dependencies()

        self.dependency_cache[entity_id] = graph
        return graph

    def analyze_impact(
        self,
        entity_id: str,
        change_type: str = "modification"
    ) -> Dict[str, Any]:
        """Analyze impact of changes to entity.

        Args:
            entity_id: Entity ID
            change_type: Type of change (modification, deletion, etc.)

        Returns:
            Impact analysis dict
        """
        impact = {
            "entity_id": entity_id,
            "change_type": change_type,
            "affected_entities": [],
            "impact_level": "low",
            "risk_score": 0.0
        }

        # Find all entities that depend on this one
        affected = []
        self._find_dependents(entity_id, affected, set())

        impact["affected_entities"] = affected
        impact["impact_level"] = self._calculate_impact_level(len(affected))
        impact["risk_score"] = self._calculate_risk_score(entity_id, set(affected))

        return impact

    def detect_circular_dependencies(self) -> List[List[str]]:
        """Detect circular dependencies in graph.
        
        Returns:
            List of circular dependency chains
        """
        cycles = []
        visited = set()
        rec_stack = set()

        def dfs(node: str, path: List[str]) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for rel in self.relationships.get(node, []):
                target = rel["target"]

                if target not in visited:
                    dfs(target, path.copy())
                elif target in rec_stack:
                    # Found cycle
                    cycle_start = path.index(target)
                    cycle = path[cycle_start:] + [target]
                    cycles.append(cycle)

            rec_stack.remove(node)

        for node in self.relationships.keys():
            if node not in visited:
                dfs(node, [])

        return cycles

    def get_related_entities(
        self,
        entity_id: str,
        relationship_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get entities related to given entity.
        
        Args:
            entity_id: Entity ID
            relationship_type: Filter by relationship type
            
        Returns:
            List of related entities
        """
        related = []

        for rel in self.relationships.get(entity_id, []):
            if relationship_type and rel["type"] != relationship_type:
                continue

            related.append({
                "id": rel["target"],
                "relationship_type": rel["type"],
                "metadata": rel["metadata"]
            })

        return related

    def _find_dependencies(
        self,
        entity_id: str,
        result: List[str],
        visited: Set[str]
    ) -> None:
        """Find all dependencies of entity (recursive).
        
        Args:
            entity_id: Entity ID
            result: Result list
            visited: Visited set
        """
        if entity_id in visited:
            return

        visited.add(entity_id)

        for rel in self.relationships.get(entity_id, []):
            target = rel["target"]
            result.append(target)
            self._find_dependencies(target, result, visited)

    def _find_dependents(
        self,
        entity_id: str,
        result: List[str],
        visited: Set[str]
    ) -> None:
        """Find all entities that depend on given entity (recursive).
        
        Args:
            entity_id: Entity ID
            result: Result list
            visited: Visited set
        """
        if entity_id in visited:
            return

        visited.add(entity_id)

        # Find all relationships pointing to this entity
        for source_id, rels in self.relationships.items():
            for rel in rels:
                if rel["target"] == entity_id:
                    result.append(source_id)
                    self._find_dependents(source_id, result, visited)

    def _calculate_impact_level(self, affected_count: int) -> str:
        """Calculate impact level based on affected count.
        
        Args:
            affected_count: Number of affected entities
            
        Returns:
            Impact level (low, medium, high, critical)
        """
        if affected_count == 0:
            return "low"
        elif affected_count <= 5:
            return "medium"
        elif affected_count <= 20:
            return "high"
        else:
            return "critical"

    def _calculate_risk_score(
        self,
        entity_id: str,
        affected: Set[str]
    ) -> float:
        """Calculate risk score for change.
        
        Args:
            entity_id: Entity ID
            affected: Set of affected entities
            
        Returns:
            Risk score (0.0-1.0)
        """
        base_score = len(affected) / 100.0
        return min(base_score, 1.0)


# Global relationship engine instance
_relationship_engine = None


def get_relationship_engine() -> RelationshipEngine:
    """Get global relationship engine instance."""
    global _relationship_engine
    if _relationship_engine is None:
        _relationship_engine = RelationshipEngine()
    return _relationship_engine

