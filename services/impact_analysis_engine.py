"""Impact Analysis Engine for Atoms MCP - Scenario modeling and what-if analysis.

Provides scenario modeling, impact propagation, what-if analysis, risk assessment,
and mitigation planning.
"""

import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


class ImpactAnalysisEngine:
    """Engine for analyzing impact of changes and scenarios."""

    def __init__(self):
        """Initialize impact analysis engine."""
        self.scenarios = {}
        self.impact_cache = {}
        self.risk_assessments = {}

    def analyze_impact(
        self,
        change_scenario: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze impact of a change scenario.
        
        Args:
            change_scenario: Scenario dict with entity_id, change_type, etc.
            
        Returns:
            Impact analysis result
        """
        entity_id = change_scenario.get("entity_id")
        change_type = change_scenario.get("change_type", "modification")

        analysis = {
            "scenario_id": f"scenario-{datetime.now().timestamp()}",
            "entity_id": entity_id,
            "change_type": change_type,
            "affected_entities": [],
            "impact_level": "low",
            "risk_score": 0.0,
            "mitigation_actions": [],
            "analysis_timestamp": datetime.now().isoformat()
        }

        # Simulate impact propagation
        affected = self._propagate_impact(entity_id, change_type)
        analysis["affected_entities"] = affected
        analysis["impact_level"] = self._calculate_impact_level(len(affected))
        analysis["risk_score"] = self._calculate_risk_score(len(affected), change_type)
        analysis["mitigation_actions"] = self._suggest_mitigations(change_type, len(affected))

        self.scenarios[analysis["scenario_id"]] = analysis
        return analysis

    def propagate_impact(
        self,
        entity_id: str,
        change_type: str,
        depth: int = 3
    ) -> Dict[str, Any]:
        """Propagate impact through dependency chain.
        
        Args:
            entity_id: Entity ID
            change_type: Type of change
            depth: Propagation depth
            
        Returns:
            Impact propagation result
        """
        propagation = {
            "entity_id": entity_id,
            "change_type": change_type,
            "depth": depth,
            "levels": []
        }

        current_level = {entity_id}

        for level in range(depth):
            next_level = set()

            for entity in current_level:
                # Simulate finding dependent entities
                dependents = self._find_dependents(entity)
                next_level.update(dependents)

            if not next_level:
                break

            propagation["levels"].append({
                "level": level + 1,
                "entities": list(next_level),
                "count": len(next_level)
            })

            current_level = next_level

        return propagation

    def what_if_analysis(
        self,
        scenario: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform what-if analysis for scenario.
        
        Args:
            scenario: Scenario dict
            
        Returns:
            What-if analysis result
        """
        analysis = {
            "scenario": scenario,
            "outcomes": [],
            "best_case": None,
            "worst_case": None,
            "most_likely": None
        }

        # Simulate different outcomes
        outcomes = [
            {
                "outcome": "best_case",
                "probability": 0.2,
                "impact": "low",
                "affected_count": 5,
                "recovery_time_hours": 2
            },
            {
                "outcome": "most_likely",
                "probability": 0.6,
                "impact": "medium",
                "affected_count": 15,
                "recovery_time_hours": 8
            },
            {
                "outcome": "worst_case",
                "probability": 0.2,
                "impact": "high",
                "affected_count": 50,
                "recovery_time_hours": 24
            }
        ]

        analysis["outcomes"] = outcomes
        analysis["best_case"] = outcomes[0]
        analysis["most_likely"] = outcomes[1]
        analysis["worst_case"] = outcomes[2]

        return analysis

    def assess_risk(
        self,
        change: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess risk of a change.
        
        Args:
            change: Change dict
            
        Returns:
            Risk assessment result
        """
        entity_id = change.get("entity_id")
        change_type = change.get("change_type", "modification")
        affected_count = change.get("affected_count", 0)

        risk_assessment = {
            "entity_id": entity_id,
            "change_type": change_type,
            "risk_level": self._calculate_risk_level(affected_count, change_type),
            "risk_score": self._calculate_risk_score(affected_count, change_type),
            "risk_factors": self._identify_risk_factors(change_type, affected_count),
            "assessment_timestamp": datetime.now().isoformat()
        }

        self.risk_assessments[entity_id] = risk_assessment
        return risk_assessment

    def suggest_mitigations(
        self,
        impact: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Suggest mitigations for impact.
        
        Args:
            impact: Impact analysis result
            
        Returns:
            List of mitigation suggestions
        """
        change_type = impact.get("change_type", "modification")
        affected_count = impact.get("affected_count", 0)

        mitigations = self._suggest_mitigations(change_type, affected_count)

        return [
            {
                "action": m,
                "priority": self._calculate_priority(m, affected_count),
                "estimated_effort_hours": self._estimate_effort(m)
            }
            for m in mitigations
        ]

    def _propagate_impact(
        self,
        entity_id: str,
        change_type: str
    ) -> List[str]:
        """Propagate impact through dependencies.
        
        Args:
            entity_id: Entity ID
            change_type: Type of change
            
        Returns:
            List of affected entities
        """
        affected = []

        # Simulate finding affected entities
        if change_type == "deletion":
            affected = [f"dependent-{i}" for i in range(5)]
        elif change_type == "modification":
            affected = [f"dependent-{i}" for i in range(3)]
        else:
            affected = [f"dependent-{i}" for i in range(1)]

        return affected

    def _find_dependents(self, entity_id: str) -> Set[str]:
        """Find dependent entities.
        
        Args:
            entity_id: Entity ID
            
        Returns:
            Set of dependent entities
        """
        # Simulate finding dependents
        return {f"{entity_id}-dep-{i}" for i in range(2)}

    def _calculate_impact_level(self, affected_count: int) -> str:
        """Calculate impact level.
        
        Args:
            affected_count: Number of affected entities
            
        Returns:
            Impact level
        """
        if affected_count == 0:
            return "low"
        elif affected_count <= 5:
            return "medium"
        elif affected_count <= 20:
            return "high"
        else:
            return "critical"

    def _calculate_risk_level(self, affected_count: int, change_type: str) -> str:
        """Calculate risk level.
        
        Args:
            affected_count: Number of affected entities
            change_type: Type of change
            
        Returns:
            Risk level
        """
        if change_type == "deletion":
            base_level = 2
        elif change_type == "modification":
            base_level = 1
        else:
            base_level = 0

        risk_level = base_level + (affected_count // 10)

        if risk_level >= 3:
            return "critical"
        elif risk_level >= 2:
            return "high"
        elif risk_level >= 1:
            return "medium"
        else:
            return "low"

    def _calculate_risk_score(self, affected_count: int, change_type: str) -> float:
        """Calculate risk score.
        
        Args:
            affected_count: Number of affected entities
            change_type: Type of change
            
        Returns:
            Risk score (0.0-1.0)
        """
        base_score = affected_count / 100.0

        if change_type == "deletion":
            base_score *= 2.0
        elif change_type == "modification":
            base_score *= 1.5

        return min(base_score, 1.0)

    def _identify_risk_factors(self, change_type: str, affected_count: int) -> List[str]:
        """Identify risk factors.
        
        Args:
            change_type: Type of change
            affected_count: Number of affected entities
            
        Returns:
            List of risk factors
        """
        factors = []

        if change_type == "deletion":
            factors.append("Data loss risk")
            factors.append("Dependency breakage")

        if affected_count > 10:
            factors.append("High impact scope")
            factors.append("Complex rollback")

        if affected_count > 20:
            factors.append("Critical system impact")

        return factors

    def _suggest_mitigations(self, change_type: str, affected_count: int) -> List[str]:
        """Suggest mitigations.
        
        Args:
            change_type: Type of change
            affected_count: Number of affected entities
            
        Returns:
            List of mitigation suggestions
        """
        mitigations = []

        if change_type == "deletion":
            mitigations.append("Create backup before deletion")
            mitigations.append("Notify dependent system owners")

        if affected_count > 5:
            mitigations.append("Implement gradual rollout")
            mitigations.append("Prepare rollback plan")

        if affected_count > 20:
            mitigations.append("Schedule maintenance window")
            mitigations.append("Increase monitoring")

        return mitigations

    def _calculate_priority(self, action: str, affected_count: int) -> str:
        """Calculate priority for mitigation action.
        
        Args:
            action: Action description
            affected_count: Number of affected entities
            
        Returns:
            Priority level
        """
        if "backup" in action.lower() or "rollback" in action.lower():
            return "critical"
        elif affected_count > 20:
            return "high"
        else:
            return "medium"

    def _estimate_effort(self, action: str) -> float:
        """Estimate effort for mitigation action.
        
        Args:
            action: Action description
            
        Returns:
            Estimated effort in hours
        """
        if "backup" in action.lower():
            return 2.0
        elif "notify" in action.lower():
            return 1.0
        elif "rollout" in action.lower():
            return 8.0
        elif "rollback" in action.lower():
            return 4.0
        else:
            return 3.0


# Global impact analysis engine instance
_impact_analysis_engine = None


def get_impact_analysis_engine() -> ImpactAnalysisEngine:
    """Get global impact analysis engine instance."""
    global _impact_analysis_engine
    if _impact_analysis_engine is None:
        _impact_analysis_engine = ImpactAnalysisEngine()
    return _impact_analysis_engine

