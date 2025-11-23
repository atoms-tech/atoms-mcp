"""Unit tests for Phase 4 Week 3: Compliance Engine.

Tests safety-critical tracking, certification status, quality metrics,
gap analysis, and compliance reporting.
"""

import pytest
from services.compliance_engine import get_compliance_engine


class TestComplianceEnginePhase4:
    """Test Phase 4 compliance engine."""

    @pytest.fixture
    def engine(self):
        """Get compliance engine instance."""
        engine = get_compliance_engine()
        engine.safety_critical.clear()
        engine.certifications.clear()
        engine.quality_metrics.clear()
        engine.compliance_status.clear()
        return engine

    # ========== Safety-Critical Tracking Tests ==========

    def test_track_safety_critical(self, engine):
        """Test tracking safety-critical classification."""
        record = engine.track_safety_critical(
            "req-1",
            "critical",
            severity="high"
        )

        assert record["entity_id"] == "req-1"
        assert record["classification"] == "critical"
        assert record["severity"] == "high"

    def test_get_safety_critical_requirements(self, engine):
        """Test getting safety-critical requirements."""
        engine.track_safety_critical("req-1", "critical")
        engine.track_safety_critical("req-2", "high")
        engine.track_safety_critical("req-3", "medium")

        critical = engine.get_safety_critical_requirements("critical")

        assert len(critical) == 1
        assert critical[0]["entity_id"] == "req-1"

    def test_get_all_safety_critical(self, engine):
        """Test getting all safety-critical requirements."""
        engine.track_safety_critical("req-1", "critical")
        engine.track_safety_critical("req-2", "high")

        all_safety = engine.get_safety_critical_requirements()

        assert len(all_safety) == 2

    # ========== Certification Tracking Tests ==========

    def test_track_certification(self, engine):
        """Test tracking certification."""
        record = engine.track_certification(
            "req-1",
            "ISO 26262",
            "approved",
            expiry_date="2026-12-31"
        )

        assert record["entity_id"] == "req-1"
        assert record["certification_type"] == "ISO 26262"
        assert record["status"] == "approved"

    def test_get_certification_status(self, engine):
        """Test getting certification status."""
        engine.track_certification("req-1", "ISO 26262", "approved")
        engine.track_certification("req-1", "FDA", "pending")

        certs = engine.get_certification_status("req-1")

        assert len(certs) == 2

    def test_get_certification_by_type(self, engine):
        """Test getting certification by type."""
        engine.track_certification("req-1", "ISO 26262", "approved")
        engine.track_certification("req-1", "FDA", "pending")

        iso_certs = engine.get_certification_status("req-1", "ISO 26262")

        assert len(iso_certs) == 1
        assert iso_certs[0]["certification_type"] == "ISO 26262"

    # ========== Quality Metrics Tests ==========

    def test_calculate_quality_metrics(self, engine):
        """Test calculating quality metrics."""
        metrics = engine.calculate_quality_metrics(
            "req-1",
            test_coverage=85.0,
            documentation_completeness=90.0,
            defect_density=0.5
        )

        assert metrics["entity_id"] == "req-1"
        assert metrics["test_coverage"] == 85.0
        assert metrics["overall_score"] == 87.5
        assert metrics["quality_level"] == "good"

    def test_quality_level_calculation(self, engine):
        """Test quality level calculation."""
        # Excellent
        metrics1 = engine.calculate_quality_metrics("req-1", 95, 95, 0.1)
        assert metrics1["quality_level"] == "excellent"

        # Good
        metrics2 = engine.calculate_quality_metrics("req-2", 80, 80, 0.5)
        assert metrics2["quality_level"] == "good"

        # Fair
        metrics3 = engine.calculate_quality_metrics("req-3", 65, 65, 1.0)
        assert metrics3["quality_level"] == "fair"

        # Poor
        metrics4 = engine.calculate_quality_metrics("req-4", 50, 50, 2.0)
        assert metrics4["quality_level"] == "poor"

    def test_get_quality_metrics(self, engine):
        """Test getting quality metrics."""
        engine.calculate_quality_metrics("req-1", 85, 90, 0.5)

        metrics = engine.get_quality_metrics("req-1")

        assert metrics is not None
        assert metrics["test_coverage"] == 85

    # ========== Gap Analysis Tests ==========

    def test_analyze_gaps(self, engine):
        """Test gap analysis."""
        engine.calculate_quality_metrics("mod-1-req-1", 70, 80, 0.5)
        engine.calculate_quality_metrics("mod-1-req-2", 60, 70, 1.0)

        gaps = engine.analyze_gaps("mod-1", required_coverage=80.0)

        assert gaps["module_id"] == "mod-1"
        assert len(gaps["gaps"]) > 0

    def test_analyze_gaps_no_gaps(self, engine):
        """Test gap analysis with no gaps."""
        engine.calculate_quality_metrics("mod-1-req-1", 90, 90, 0.1)
        engine.calculate_quality_metrics("mod-1-req-2", 85, 85, 0.2)

        gaps = engine.analyze_gaps("mod-1", required_coverage=80.0)

        assert len(gaps["gaps"]) == 0

    # ========== Compliance Report Tests ==========

    def test_generate_compliance_report_all(self, engine):
        """Test generating compliance report."""
        engine.track_safety_critical("req-1", "critical")
        engine.track_certification("req-2", "ISO 26262", "approved")
        engine.calculate_quality_metrics("req-3", 85, 90, 0.5)

        report = engine.generate_compliance_report("all")

        assert report["scope"] == "all"
        assert "summary" in report
        assert "details" in report

    def test_generate_safety_critical_report(self, engine):
        """Test generating safety-critical report."""
        engine.track_safety_critical("req-1", "critical")
        engine.track_safety_critical("req-2", "high")

        report = engine.generate_compliance_report("safety-critical")

        assert report["summary"]["safety_critical_count"] == 2

    def test_generate_certified_report(self, engine):
        """Test generating certified report."""
        engine.track_certification("req-1", "ISO 26262", "approved")
        engine.track_certification("req-2", "FDA", "pending")

        report = engine.generate_compliance_report("certified")

        assert report["summary"]["certified_count"] == 2

    # ========== Review Tracking Tests ==========

    def test_get_entities_needing_review(self, engine):
        """Test getting entities needing review."""
        from datetime import datetime, timedelta

        old_date = (datetime.now() - timedelta(days=200)).isoformat()

        engine.compliance_status["req-1"] = {"last_review": old_date}
        engine.compliance_status["req-2"] = {"last_review": datetime.now().isoformat()}

        needing_review = engine.get_entities_needing_review(days_since_review=180)

        assert len(needing_review) >= 1

    # ========== Integration Tests ==========

    def test_complete_compliance_workflow(self, engine):
        """Test complete compliance workflow."""
        # Track safety-critical
        engine.track_safety_critical("req-1", "critical")

        # Track certification
        engine.track_certification("req-1", "ISO 26262", "approved")

        # Calculate quality metrics
        engine.calculate_quality_metrics("req-1", 85, 90, 0.5)

        # Generate report
        report = engine.generate_compliance_report("all")

        assert report["summary"]["safety_critical_count"] == 1
        assert report["summary"]["certified_count"] == 1

