"""Test Traceability Report Generator

Extends existing story marker system to provide comprehensive traceability
linking tests to requirements, features, and user stories.

Usage:
    pytest tests/ --traceability-report
    
This generates a report showing:
- Tests organized by user story
- Test layer (unit/integration/e2e)
- Test status (passed/failed/skipped)
- Coverage by epic
"""

from typing import Dict, List, Set
from collections import defaultdict


class TraceabilityReport:
    """Generate traceability reports from test results."""
    
    def __init__(self):
        self.tests_by_story: Dict[str, List[Dict]] = defaultdict(list)
        self.tests_by_layer: Dict[str, List[Dict]] = defaultdict(list)
        self.tests_by_epic: Dict[str, List[Dict]] = defaultdict(list)
        self.coverage_by_story: Dict[str, Dict] = {}
    
    def add_test_result(self, test_name: str, story: str, layer: str, 
                       epic: str, status: str):
        """Add test result to traceability report."""
        result = {
            "name": test_name,
            "layer": layer,
            "status": status,
        }
        
        if story:
            self.tests_by_story[story].append(result)
        if epic:
            self.tests_by_epic[epic].append(result)
        self.tests_by_layer[layer].append(result)
    
    def generate_coverage_report(self) -> str:
        """Generate coverage report by story."""
        report = "\n📊 TEST TRACEABILITY REPORT\n"
        report += "=" * 60 + "\n\n"
        
        # Coverage by story
        report += "📖 COVERAGE BY USER STORY\n"
        report += "-" * 60 + "\n"
        
        for story, tests in sorted(self.tests_by_story.items()):
            passed = sum(1 for t in tests if t["status"] == "passed")
            failed = sum(1 for t in tests if t["status"] == "failed")
            skipped = sum(1 for t in tests if t["status"] == "skipped")
            total = len(tests)
            
            status_icon = "✅" if failed == 0 else "❌"
            report += f"\n{status_icon} {story}\n"
            report += f"   Total: {total} | Passed: {passed} | Failed: {failed} | Skipped: {skipped}\n"
            
            # Show tests by layer
            by_layer = defaultdict(list)
            for test in tests:
                by_layer[test["layer"]].append(test)
            
            for layer in ["unit", "integration", "e2e"]:
                if layer in by_layer:
                    layer_tests = by_layer[layer]
                    layer_passed = sum(1 for t in layer_tests if t["status"] == "passed")
                    report += f"   {layer}: {layer_passed}/{len(layer_tests)}\n"
        
        return report
    
    def generate_layer_report(self) -> str:
        """Generate report by test layer."""
        report = "\n🏗️  COVERAGE BY TEST LAYER\n"
        report += "-" * 60 + "\n"
        
        for layer in ["unit", "integration", "e2e"]:
            if layer in self.tests_by_layer:
                tests = self.tests_by_layer[layer]
                passed = sum(1 for t in tests if t["status"] == "passed")
                failed = sum(1 for t in tests if t["status"] == "failed")
                skipped = sum(1 for t in tests if t["status"] == "skipped")
                total = len(tests)
                
                pct = (passed / total * 100) if total > 0 else 0
                report += f"\n{layer.upper()}: {passed}/{total} ({pct:.1f}%)\n"
                report += f"   Passed: {passed} | Failed: {failed} | Skipped: {skipped}\n"
        
        return report

