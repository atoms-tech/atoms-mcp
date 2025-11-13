"""
Test Matrix Visualization

Generates ASCII matrix views for architects and PMs.
"""

from collections import defaultdict
from typing import Dict, List, Optional


class TestResult:
    """Individual test result."""
    
    def __init__(
        self,
        name: str,
        layer: str,
        mode: str,
        outcome: str,
        duration: float = 0.0,
        story: str = None
    ):
        self.name = name
        self.layer = layer  # tools, infrastructure, services, auth
        self.mode = mode    # unit, integration, e2e
        self.outcome = outcome  # passed, failed, skipped
        self.duration = duration
        self.story = story  # User story this test covers (from @pytest.mark.story)


class MatrixCollector:
    """Collects test results for matrix visualization."""
    
    def __init__(self):
        # Results by layer and mode
        self.results: Dict[str, Dict[str, List[TestResult]]] = {
            "tools": {"unit": [], "integration": [], "e2e": []},
            "infrastructure": {"unit": [], "integration": [], "e2e": []},
            "services": {"unit": [], "integration": [], "e2e": []},
            "auth": {"unit": [], "integration": [], "e2e": []},
        }
        
        # Coverage by layer
        self.coverage: Dict[str, float] = {}
        
        # Error categories
        self.errors_by_category: Dict[str, List[str]] = defaultdict(list)
        
        # Story tracking: story_name -> list of TestResult
        self.stories: Dict[str, List[TestResult]] = defaultdict(list)
    
    def add_result(self, result: TestResult):
        """Add a test result."""
        if result.layer in self.results and result.mode in self.results[result.layer]:
            self.results[result.layer][result.mode].append(result)
        
        # Track story if this test has one
        if result.story:
            self.stories[result.story].append(result)
    
    def set_coverage(self, layer: str, coverage: float):
        """Set coverage percentage for a layer."""
        self.coverage[layer] = coverage
    
    def add_error(self, category: str, test_name: str):
        """Add an error to a category."""
        self.errors_by_category[category].append(test_name)
    
    def compute_layer_status(self, layer: str) -> Dict[str, str]:
        """
        Compute aggregate status for a layer.
        
        Returns:
            Dict with keys "unit", "integration", "e2e" and values:
            - "✓" = all passed
            - "✗" = all failed
            - "?" = mixed/skipped
            - "-" = no tests
        """
        statuses = {}
        
        for mode in ["unit", "integration", "e2e"]:
            results = self.results[layer][mode]
            
            if not results:
                statuses[mode] = "-"
            else:
                passed = sum(1 for r in results if r.outcome == "passed")
                failed = sum(1 for r in results if r.outcome == "failed")
                total = len(results)
                
                if passed == total:
                    statuses[mode] = "✓"
                elif failed == total:
                    statuses[mode] = "✗"
                else:
                    statuses[mode] = "?"
        
        return statuses
    
    def is_test_passing(self, test_pattern: str) -> bool:
        """
        Check if tests matching a pattern are passing.
        
        Supports:
        - Class names: "TestEntityCreate"
        - Function patterns: "test_create_entity"
        - Wildcards: "test_entity_" matches any test starting with it
        """
        for layer_results in self.results.values():
            for mode_results in layer_results.values():
                for result in mode_results:
                    # Direct match
                    if test_pattern in result.name:
                        if result.outcome == "passed":
                            return True
                    # Wildcard pattern match (e.g., "test_search_" matches "test_search_organizations")
                    elif test_pattern.endswith("_") and test_pattern[:-1] in result.name:
                        if result.outcome == "passed":
                            return True
        return False
    
    def is_story_passing(self, story: str) -> bool:
        """
        Check if a user story is passing.
        
        A story is passing if:
        - It has tests AND
        - At least one test is passing
        """
        if story not in self.stories:
            return False
        
        tests = self.stories[story]
        return any(t.outcome == "passed" for t in tests)
    
    def get_story_status(self, story: str) -> tuple[bool, str]:
        """
        Get detailed status of a story.
        
        Returns:
            (is_passing, reason) tuple
        """
        if story not in self.stories:
            return False, "No tests found"
        
        tests = self.stories[story]
        passed = sum(1 for t in tests if t.outcome == "passed")
        failed = sum(1 for t in tests if t.outcome == "failed")
        skipped = sum(1 for t in tests if t.outcome == "skipped")
        
        total = len(tests)
        
        if passed > 0:
            if failed > 0:
                return True, f"{passed}/{total} passing"
            elif skipped > 0:
                return True, f"{passed}/{total} passing"
            else:
                return True, ""
        elif failed > 0:
            return False, f"{failed}/{total} failing"
        elif skipped > 0:
            return False, f"{skipped}/{total} skipped"
        else:
            return False, "No tests"
    
    def get_all_stories(self) -> List[str]:
        """Get all user stories found in tests."""
        return sorted(list(self.stories.keys()))


class ArchitectView:
    """Renders test matrix for architects."""
    
    def __init__(self, collector: MatrixCollector):
        self.collector = collector
    
    def render(self) -> str:
        """Generate architect view ASCII art."""
        lines = []
        
        # Header
        lines.append("╔" + "═"*68 + "╗")
        lines.append("║" + "ATOMS MCP - ARCHITECT VIEW".center(68) + "║")
        lines.append("║" + "Test Matrix by Layer".center(68) + "║")
        lines.append("╠" + "═"*68 + "╣")
        
        # Column headers
        lines.append("║ Layer            │ Unit  │ Integration │  E2E  │ Coverage │ Status║")
        lines.append("╠" + "─"*18 + "┼" + "─"*7 + "┼" + "─"*13 + "┼" + "─"*7 + "┼" + "─"*10 + "┼" + "─"*7 + "╣")
        
        # Data rows
        for layer in ["tools", "infrastructure", "services", "auth"]:
            layer_display = layer.capitalize()
            statuses = self.collector.compute_layer_status(layer)
            coverage = self.collector.coverage.get(layer, 0)
            
            # Count tests
            unit_count = len(self.collector.results[layer]["unit"])
            int_count = len(self.collector.results[layer]["integration"])
            e2e_count = len(self.collector.results[layer]["e2e"])
            
            # Format counts with status
            unit_str = f"{unit_count} {statuses['unit']}" if unit_count else "-"
            int_str = f"{int_count} {statuses['integration']}" if int_count else "-"
            e2e_str = f"{e2e_count} {statuses['e2e']}" if e2e_count else "-"
            
            # Coverage with warning if below threshold
            cov_str = f"{coverage:.0f}%"
            if coverage < 80:
                cov_str += " ⚠️"
            
            # Overall status (based on unit tests primarily)
            overall = statuses["unit"] if unit_count else "-"
            
            # Format row
            line = (
                f"║ {layer_display:<16} │ {unit_str:>5} │ {int_str:>11} │ "
                f"{e2e_str:>5} │ {cov_str:>8} │ {overall:>5} ║"
            )
            lines.append(line)
        
        # Footer
        lines.append("╠" + "─"*68 + "╣")
        lines.append("║ Legend: ✓=Pass  ✗=Fail  ?=Skipped  ⚠️=Below Threshold" + " "*14 + "║")
        lines.append("║" + " "*68 + "║")
        
        # Error distribution
        if self.collector.errors_by_category:
            lines.append("║ Error Distribution:" + " "*48 + "║")
            
            category_icons = {
                "INFRA": "🔧",
                "PRODUCT": "🐛",
                "TRANSIENT": "⏱️",
                "CONFIG": "⚙️",
                "DATA": "📊",
            }
            
            for category, errors in self.collector.errors_by_category.items():
                if errors:
                    icon = category_icons.get(category, "❓")
                    text = f"   {icon} {category}: {len(errors)} errors"
                    line = f"║{text}" + " "*(69 - len(text)) + "║"
                    lines.append(line)
        
        lines.append("╚" + "═"*68 + "╝")
        
        return "\n".join(lines)


class PMView:
    """Renders feature status for product managers."""
    
    # Map feature areas to test patterns (based on actual Atoms MCP tests)
    FEATURE_MAPPING = {
        "Entity CRUD": [
            "TestEntityCreate", "TestEntityRead", "TestEntityUpdate", 
            "TestEntityDelete", "TestEntityList", "TestEntitySearch",
            "TestBatchOperations", "TestFormatTypes", "TestErrorCases",
            "TestEntityReadParam", "TestEntitySearchParam", "TestEntityPaginationParam",
        ],
        "Workspace Mgmt": [
            "TestWorkspaceGetContext", "TestWorkspaceSetContext",
            "TestWorkspaceListWorkspaces", "TestWorkspaceGetDefaults",
            "TestWorkspaceEdgeCases", "TestWorkspaceSequential", "TestWorkspaceFormats",
        ],
        "Relationship Ops": [
            "TestRelationshipLink", "TestRelationshipUnlink", "TestRelationshipList",
            "TestRelationshipCheck", "TestRelationshipUpdate", 
            "TestRelationshipEdgeCases", "TestRelationshipFormats", "TestRelationshipContext",
        ],
        "Query & Search": [
            "TestQuerySearch", "TestQueryAggregate", "TestQueryRAGSearch",
            "TestQueryAnalyze", "TestQueryRelationships", "TestQuerySimilarity",
            "TestQueryFormatTypes", "TestQueryEdgeCases", "TestQueryIntegration",
        ],
        "Workflow Execution": [
            "TestWorkflowBasic", "TestWorkflowTransactionMode", 
            "TestWorkflowFormatTypes", "TestWorkflowEdgeCases",
            "TestWorkflowComplexParameters", "TestWorkflowCombinations",
        ],
        "Auth & Permissions": [
            "TestAuthKitAuthentication", "TestSupabaseAuthIntegration",
            "test_auth_adapter", "test_token_cache",
        ],
    }
    
    def __init__(self, collector: MatrixCollector):
        self.collector = collector
    
    def render(self) -> str:
        """Generate PM view ASCII art."""
        lines = []
        
        # Header
        lines.append("╔" + "═"*68 + "╗")
        lines.append("║" + "ATOMS MCP - PM VIEW".center(68) + "║")
        lines.append("║" + "User Story Completion Status".center(68) + "║")
        lines.append("╠" + "═"*68 + "╣")
        
        # Column headers
        lines.append("║ Feature Area      │ Stories │ Complete │ In Progress │ Status     ║")
        lines.append("╠" + "─"*19 + "┼" + "─"*9 + "┼" + "─"*10 + "┼" + "─"*13 + "┼" + "─"*12 + "╣")
        
        total_stories = 0
        total_complete = 0
        
        # Data rows
        for feature, test_patterns in self.FEATURE_MAPPING.items():
            story_count = len(test_patterns)
            
            # Count how many tests are passing
            complete = sum(
                1 for pattern in test_patterns
                if self.collector.is_test_passing(pattern)
            )
            in_progress = story_count - complete
            
            total_stories += story_count
            total_complete += complete
            
            # Status indicator
            completion_pct = complete / story_count if story_count else 0
            if completion_pct == 1.0:
                status = "✓✓✓"
            elif completion_pct >= 0.7:
                status = "✓✓○"
            elif completion_pct > 0:
                status = "✓○○"
            else:
                status = "○○○"
            
            # Format row
            line = (
                f"║ {feature:<17} │ {story_count:>7} │ {complete:>8} │ "
                f"{in_progress:>11} │ {status:>10} ║"
            )
            lines.append(line)
        
        # Summary
        lines.append("╠" + "─"*68 + "╣")
        pct = int(total_complete / total_stories * 100) if total_stories else 0
        summary = f"Overall Progress: {total_complete}/{total_stories} stories complete ({pct}%)"
        lines.append("║ " + summary + " "*(67 - len(summary)) + "║")
        lines.append("║" + " "*68 + "║")
        
        # Blockers (if any critical features are incomplete)
        blockers = []
        for feature, test_patterns in self.FEATURE_MAPPING.items():
            complete = sum(
                1 for pattern in test_patterns
                if self.collector.is_test_passing(pattern)
            )
            if complete == 0:
                blockers.append(feature)
        
        if blockers:
            lines.append("║ Blockers:" + " "*58 + "║")
            for blocker in blockers[:2]:  # Show first 2
                text = f"   • {blocker} requires attention"
                lines.append("║ " + text + " "*(67 - len(text)) + "║")
        
        lines.append("╚" + "═"*68 + "╝")
        
        return "\n".join(lines)


def extract_layer_from_path(test_path: str) -> str:
    """Extract layer from test path."""
    if "/tools/" in test_path:
        return "tools"
    elif "/infrastructure/" in test_path:
        return "infrastructure"
    elif "/services/" in test_path:
        return "services"
    elif "/auth/" in test_path:
        return "auth"
    return "unknown"


def extract_mode_from_markers(markers: list) -> str:
    """Extract mode (unit/integration/e2e) from pytest markers."""
    marker_names = [m.name for m in markers]
    
    if "unit" in marker_names:
        return "unit"
    elif "integration" in marker_names:
        return "integration"
    elif "e2e" in marker_names:
        return "e2e"
    
    return "unit"  # Default to unit if not specified
