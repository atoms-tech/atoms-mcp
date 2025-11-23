"""Compliance Engine for Atoms MCP - Safety-critical and quality tracking.

Provides safety-critical tracking, certification status, quality metrics,
gap analysis, and compliance reporting.
"""

import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


class ComplianceEngine:
    """Engine for tracking compliance and quality metrics."""

    def __init__(self):
        """Initialize compliance engine."""
        self.safety_critical = {}
        self.certifications = defaultdict(list)
        self.quality_metrics = {}
        self.compliance_status = {}

    def track_safety_critical(
        self,
        entity_id: str,
        classification: str,
        severity: str = "high",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Track safety-critical classification.
        
        Args:
            entity_id: Entity ID
            classification: Safety classification (critical, high, medium, low)
            severity: Severity level
            metadata: Additional metadata
            
        Returns:
            Safety tracking record
        """
        record = {
            "entity_id": entity_id,
            "classification": classification,
            "severity": severity,
            "tracked_at": datetime.now().isoformat(),
            "metadata": metadata or {}
        }

        self.safety_critical[entity_id] = record
        logger.info(f"Safety-critical tracked: {entity_id} ({classification})")
        return record

    def get_safety_critical_requirements(
        self,
        classification: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get safety-critical requirements.
        
        Args:
            classification: Filter by classification
            
        Returns:
            List of safety-critical requirements
        """
        results = list(self.safety_critical.values())

        if classification:
            results = [r for r in results if r["classification"] == classification]

        return results

    def track_certification(
        self,
        entity_id: str,
        certification_type: str,
        status: str,
        expiry_date: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Track certification status.
        
        Args:
            entity_id: Entity ID
            certification_type: Type of certification (ISO, FDA, etc.)
            status: Certification status (approved, pending, rejected)
            expiry_date: Expiry date ISO string
            metadata: Additional metadata
            
        Returns:
            Certification record
        """
        record = {
            "entity_id": entity_id,
            "certification_type": certification_type,
            "status": status,
            "expiry_date": expiry_date,
            "tracked_at": datetime.now().isoformat(),
            "metadata": metadata or {}
        }

        self.certifications[entity_id].append(record)
        logger.info(f"Certification tracked: {entity_id} ({certification_type})")
        return record

    def get_certification_status(
        self,
        entity_id: str,
        certification_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get certification status for entity.
        
        Args:
            entity_id: Entity ID
            certification_type: Filter by certification type
            
        Returns:
            List of certification records
        """
        certs = self.certifications.get(entity_id, [])

        if certification_type:
            certs = [c for c in certs if c["certification_type"] == certification_type]

        return certs

    def calculate_quality_metrics(
        self,
        entity_id: str,
        test_coverage: float,
        documentation_completeness: float,
        defect_density: float
    ) -> Dict[str, Any]:
        """Calculate quality metrics for entity.
        
        Args:
            entity_id: Entity ID
            test_coverage: Test coverage percentage (0-100)
            documentation_completeness: Documentation completeness (0-100)
            defect_density: Defects per 1000 lines
            
        Returns:
            Quality metrics record
        """
        overall_score = (test_coverage + documentation_completeness) / 2
        quality_level = self._calculate_quality_level(overall_score)

        record = {
            "entity_id": entity_id,
            "test_coverage": test_coverage,
            "documentation_completeness": documentation_completeness,
            "defect_density": defect_density,
            "overall_score": overall_score,
            "quality_level": quality_level,
            "calculated_at": datetime.now().isoformat()
        }

        self.quality_metrics[entity_id] = record
        return record

    def get_quality_metrics(
        self,
        entity_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get quality metrics for entity.
        
        Args:
            entity_id: Entity ID
            
        Returns:
            Quality metrics or None
        """
        return self.quality_metrics.get(entity_id)

    def analyze_gaps(
        self,
        module_id: str,
        required_coverage: float = 80.0
    ) -> Dict[str, Any]:
        """Analyze coverage gaps in module.
        
        Args:
            module_id: Module ID
            required_coverage: Required coverage percentage
            
        Returns:
            Gap analysis result
        """
        gaps = {
            "module_id": module_id,
            "required_coverage": required_coverage,
            "gaps": [],
            "total_gap": 0.0
        }

        for entity_id, metrics in self.quality_metrics.items():
            if module_id in entity_id or entity_id.startswith(module_id):
                coverage = metrics["test_coverage"]

                if coverage < required_coverage:
                    gap = required_coverage - coverage
                    gaps["gaps"].append({
                        "entity_id": entity_id,
                        "current_coverage": coverage,
                        "required_coverage": required_coverage,
                        "gap": gap
                    })
                    gaps["total_gap"] += gap

        return gaps

    def generate_compliance_report(
        self,
        scope: str = "all"
    ) -> Dict[str, Any]:
        """Generate compliance report.
        
        Args:
            scope: Report scope (all, safety-critical, certified)
            
        Returns:
            Compliance report
        """
        report = {
            "scope": scope,
            "generated_at": datetime.now().isoformat(),
            "summary": {},
            "details": {}
        }

        if scope in ["all", "safety-critical"]:
            safety_reqs = self.get_safety_critical_requirements()
            report["summary"]["safety_critical_count"] = len(safety_reqs)
            report["details"]["safety_critical"] = safety_reqs

        if scope in ["all", "certified"]:
            certified_count = sum(len(certs) for certs in self.certifications.values())
            report["summary"]["certified_count"] = certified_count
            report["details"]["certifications"] = dict(self.certifications)

        if scope in ["all", "quality"]:
            avg_coverage = (
                sum(m["test_coverage"] for m in self.quality_metrics.values()) /
                len(self.quality_metrics)
                if self.quality_metrics else 0
            )
            report["summary"]["average_test_coverage"] = avg_coverage
            report["details"]["quality_metrics"] = self.quality_metrics

        return report

    def get_entities_needing_review(
        self,
        days_since_review: int = 180
    ) -> List[Dict[str, Any]]:
        """Get entities needing review.
        
        Args:
            days_since_review: Days since last review
            
        Returns:
            List of entities needing review
        """
        entities_needing_review = []

        for entity_id, record in self.compliance_status.items():
            last_review = record.get("last_review")

            if last_review:
                from datetime import timedelta
                review_time = datetime.fromisoformat(last_review)
                days_old = (datetime.now() - review_time).days

                if days_old > days_since_review:
                    entities_needing_review.append({
                        "entity_id": entity_id,
                        "last_review": last_review,
                        "days_since_review": days_old
                    })

        return entities_needing_review

    def _calculate_quality_level(self, score: float) -> str:
        """Calculate quality level from score.
        
        Args:
            score: Quality score (0-100)
            
        Returns:
            Quality level (excellent, good, fair, poor)
        """
        if score >= 90:
            return "excellent"
        elif score >= 75:
            return "good"
        elif score >= 60:
            return "fair"
        else:
            return "poor"


# Global compliance engine instance
_compliance_engine = None


def get_compliance_engine() -> ComplianceEngine:
    """Get global compliance engine instance."""
    global _compliance_engine
    if _compliance_engine is None:
        _compliance_engine = ComplianceEngine()
    return _compliance_engine

