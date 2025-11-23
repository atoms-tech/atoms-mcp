"""Unit tests for Phase 4 Week 4: Impact Analysis Engine.

Tests scenario modeling, impact propagation, what-if analysis, risk assessment,
and mitigation planning.
"""

import pytest
from services.impact_analysis_engine import get_impact_analysis_engine


class TestImpactAnalysisEnginePhase4:
    """Test Phase 4 impact analysis engine."""

    @pytest.fixture
    def engine(self):
        """Get impact analysis engine instance."""
        engine = get_impact_analysis_engine()
        engine.scenarios.clear()
        engine.impact_cache.clear()
        engine.risk_assessments.clear()
        return engine

    # ========== Impact Analysis Tests ==========

    def test_analyze_impact_modification(self, engine):
        """Test analyzing impact of modification."""
        scenario = {
            "entity_id": "req-1",
            "change_type": "modification"
        }

        analysis = engine.analyze_impact(scenario)

        assert analysis["entity_id"] == "req-1"
        assert analysis["change_type"] == "modification"
        assert "affected_entities" in analysis
        assert "impact_level" in analysis

    def test_analyze_impact_deletion(self, engine):
        """Test analyzing impact of deletion."""
        scenario = {
            "entity_id": "req-1",
            "change_type": "deletion"
        }

        analysis = engine.analyze_impact(scenario)

        assert analysis["change_type"] == "deletion"
        assert len(analysis["affected_entities"]) > 0

    def test_analyze_impact_creation(self, engine):
        """Test analyzing impact of creation."""
        scenario = {
            "entity_id": "req-1",
            "change_type": "creation"
        }

        analysis = engine.analyze_impact(scenario)

        assert analysis["change_type"] == "creation"

    # ========== Impact Propagation Tests ==========

    def test_propagate_impact(self, engine):
        """Test impact propagation."""
        propagation = engine.propagate_impact("req-1", "modification", depth=3)

        assert propagation["entity_id"] == "req-1"
        assert propagation["depth"] == 3
        assert "levels" in propagation

    def test_propagate_impact_depth(self, engine):
        """Test impact propagation depth."""
        propagation = engine.propagate_impact("req-1", "modification", depth=2)

        assert propagation["depth"] == 2

    # ========== What-If Analysis Tests ==========

    def test_what_if_analysis(self, engine):
        """Test what-if analysis."""
        scenario = {
            "entity_id": "req-1",
            "change_type": "deletion"
        }

        analysis = engine.what_if_analysis(scenario)

        assert "outcomes" in analysis
        assert "best_case" in analysis
        assert "worst_case" in analysis
        assert "most_likely" in analysis
        assert len(analysis["outcomes"]) == 3

    def test_what_if_outcomes(self, engine):
        """Test what-if outcomes."""
        scenario = {"entity_id": "req-1", "change_type": "deletion"}

        analysis = engine.what_if_analysis(scenario)

        best = analysis["best_case"]
        worst = analysis["worst_case"]

        assert best["probability"] <= worst["probability"]
        assert best["affected_count"] <= worst["affected_count"]

    # ========== Risk Assessment Tests ==========

    def test_assess_risk_low(self, engine):
        """Test risk assessment for low impact."""
        change = {
            "entity_id": "req-1",
            "change_type": "modification",
            "affected_count": 2
        }

        assessment = engine.assess_risk(change)

        assert assessment["entity_id"] == "req-1"
        assert "risk_level" in assessment
        assert "risk_score" in assessment

    def test_assess_risk_high(self, engine):
        """Test risk assessment for high impact."""
        change = {
            "entity_id": "req-1",
            "change_type": "deletion",
            "affected_count": 25
        }

        assessment = engine.assess_risk(change)

        assert assessment["risk_level"] in ["high", "critical"]
        assert assessment["risk_score"] >= 0.5

    def test_assess_risk_factors(self, engine):
        """Test risk factor identification."""
        change = {
            "entity_id": "req-1",
            "change_type": "deletion",
            "affected_count": 30
        }

        assessment = engine.assess_risk(change)

        assert len(assessment["risk_factors"]) > 0

    # ========== Mitigation Suggestion Tests ==========

    def test_suggest_mitigations(self, engine):
        """Test mitigation suggestions."""
        impact = {
            "change_type": "deletion",
            "affected_count": 10
        }

        mitigations = engine.suggest_mitigations(impact)

        assert len(mitigations) > 0
        assert all("action" in m for m in mitigations)
        assert all("priority" in m for m in mitigations)

    def test_mitigation_priority(self, engine):
        """Test mitigation priority calculation."""
        impact = {
            "change_type": "deletion",
            "affected_count": 30
        }

        mitigations = engine.suggest_mitigations(impact)

        # Should have high priority mitigations
        high_priority = [m for m in mitigations if m["priority"] in ["high", "critical"]]
        assert len(high_priority) > 0

    def test_mitigation_effort(self, engine):
        """Test mitigation effort estimation."""
        impact = {
            "change_type": "deletion",
            "affected_count": 10
        }

        mitigations = engine.suggest_mitigations(impact)

        # All mitigations should have effort estimates
        assert all("estimated_effort_hours" in m for m in mitigations)
        assert all(m["estimated_effort_hours"] > 0 for m in mitigations)

    # ========== Integration Tests ==========

    def test_complete_impact_analysis_workflow(self, engine):
        """Test complete impact analysis workflow."""
        # Analyze impact
        scenario = {
            "entity_id": "req-1",
            "change_type": "deletion"
        }

        analysis = engine.analyze_impact(scenario)

        # Perform what-if analysis
        what_if = engine.what_if_analysis(scenario)

        # Assess risk
        risk = engine.assess_risk({
            "entity_id": "req-1",
            "change_type": "deletion",
            "affected_count": len(analysis["affected_entities"])
        })

        # Suggest mitigations
        mitigations = engine.suggest_mitigations(analysis)

        assert analysis is not None
        assert what_if is not None
        assert risk is not None
        assert len(mitigations) > 0

    def test_scenario_storage(self, engine):
        """Test scenario storage."""
        scenario = {
            "entity_id": "req-1",
            "change_type": "modification"
        }

        analysis = engine.analyze_impact(scenario)

        assert analysis["scenario_id"] in engine.scenarios
        assert engine.scenarios[analysis["scenario_id"]] == analysis

