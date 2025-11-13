"""
Warning and Performance Analyzer

Analyzes test execution for warnings, slow tests, and performance issues.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class TestWarning:
    """Represents a test warning."""
    test_name: str
    warning_type: str  # 'slow', 'large_output', 'deprecated', 'config', 'flaky'
    message: str
    severity: str  # 'low', 'medium', 'high'


class WarningAnalyzer:
    """Analyzes tests for warnings and performance issues."""
    
    def __init__(self):
        self.warnings: List[TestWarning] = []
        self.slow_test_threshold = 1.0  # seconds
        self.very_slow_threshold = 5.0   # seconds
    
    def analyze_test_result(self, test_name: str, duration: float, outcome: str) -> List[TestWarning]:
        """Analyze a test result for warnings."""
        warnings = []
        
        # Slow test detection
        if duration > self.very_slow_threshold:
            warnings.append(TestWarning(
                test_name=test_name,
                warning_type='slow',
                message=f'Very slow: {duration:.2f}s (threshold: {self.very_slow_threshold}s)',
                severity='high'
            ))
        elif duration > self.slow_test_threshold:
            warnings.append(TestWarning(
                test_name=test_name,
                warning_type='slow',
                message=f'Slow: {duration:.2f}s (threshold: {self.slow_test_threshold}s)',
                severity='medium'
            ))
        
        # Flaky test detection (if it passed after retries)
        if outcome == "passed" and "retry" in test_name.lower():
            warnings.append(TestWarning(
                test_name=test_name,
                warning_type='flaky',
                message='Test passed after retry (potentially flaky)',
                severity='medium'
            ))
        
        return warnings
    
    def add_warning(self, warning: TestWarning):
        """Add a warning to the collection."""
        self.warnings.append(warning)
    
    def get_warnings_by_type(self, warning_type: str) -> List[TestWarning]:
        """Get all warnings of a specific type."""
        return [w for w in self.warnings if w.warning_type == warning_type]
    
    def get_warnings_by_severity(self, severity: str) -> List[TestWarning]:
        """Get all warnings of a specific severity."""
        return [w for w in self.warnings if w.severity == severity]
    
    def generate_report(self) -> str:
        """Generate a warning report."""
        if not self.warnings:
            return "\n✅ No warnings detected"
        
        lines = []
        lines.append("\n" + "="*70)
        lines.append("⚠️  TEST WARNINGS & PERFORMANCE ISSUES")
        lines.append("="*70)
        
        # Group by type
        by_type = {}
        for warning in self.warnings:
            if warning.warning_type not in by_type:
                by_type[warning.warning_type] = []
            by_type[warning.warning_type].append(warning)
        
        # Icons for warning types
        icons = {
            'slow': '🐌',
            'large_output': '📊',
            'deprecated': '⚠️',
            'config': '⚙️',
            'flaky': '🔄',
        }
        
        for warning_type, type_warnings in by_type.items():
            icon = icons.get(warning_type, '⚠️')
            lines.append(f"\n{icon} {warning_type.upper()} ({len(type_warnings)}):")
            
            # Show first 5 warnings of this type
            for warning in type_warnings[:5]:
                severity_icon = "🔴" if warning.severity == "high" else "🟡" if warning.severity == "medium" else "🟢"
                lines.append(f"  {severity_icon} {warning.test_name}")
                lines.append(f"     → {warning.message}")
            
            if len(type_warnings) > 5:
                lines.append(f"  ... and {len(type_warnings) - 5} more")
        
        # Summary
        lines.append("\n" + "-"*70)
        high = len(self.get_warnings_by_severity('high'))
        medium = len(self.get_warnings_by_severity('medium'))
        low = len(self.get_warnings_by_severity('low'))
        
        lines.append(f"Total Warnings: {len(self.warnings)}")
        lines.append(f"  🔴 High: {high}  🟡 Medium: {medium}  🟢 Low: {low}")
        
        lines.append("="*70)
        
        return "\n".join(lines)


class FailureAnalyzer:
    """Analyzes test failures to provide detailed explanations."""
    
    @staticmethod
    def analyze_failure(test_name: str, exception_info: Optional[str]) -> Dict[str, str]:
        """
        Analyze a test failure and provide explanation.
        
        Returns dict with:
        - cause: Brief description of failure cause
        - explanation: Detailed explanation
        - suggestion: Recommended action
        """
        if not exception_info:
            return {
                'cause': 'Unknown failure',
                'explanation': 'No exception information available',
                'suggestion': 'Check test logs for details'
            }
        
        exc_lower = exception_info.lower()
        
        # Dependency failures
        if 'depends' in exc_lower or 'dependency' in exc_lower:
            return {
                'cause': 'Dependency failure',
                'explanation': 'Test skipped because a prerequisite test failed',
                'suggestion': 'Fix the failing dependency test first'
            }
        
        # Connection errors
        if 'connection' in exc_lower or 'refused' in exc_lower:
            return {
                'cause': 'Connection error',
                'explanation': 'Unable to connect to required service (database, server, etc.)',
                'suggestion': 'Ensure service is running and accessible'
            }
        
        # Timeout errors
        if 'timeout' in exc_lower or 'timed out' in exc_lower:
            return {
                'cause': 'Timeout',
                'explanation': 'Test exceeded time limit',
                'suggestion': 'Check for slow operations or increase timeout'
            }
        
        # Assertion errors
        if 'assertion' in exc_lower or 'assert' in exc_lower:
            return {
                'cause': 'Assertion failed',
                'explanation': 'Test expectation was not met',
                'suggestion': 'Review test expectations and actual behavior'
            }
        
        # Permission errors
        if 'permission' in exc_lower or 'denied' in exc_lower:
            return {
                'cause': 'Permission denied',
                'explanation': 'Insufficient permissions to perform operation',
                'suggestion': 'Check RLS policies, grants, or authentication'
            }
        
        # Configuration errors
        if 'config' in exc_lower or 'not found' in exc_lower:
            return {
                'cause': 'Configuration error',
                'explanation': 'Missing or invalid configuration',
                'suggestion': 'Check environment variables and config files'
            }
        
        # Default
        return {
            'cause': 'Test failure',
            'explanation': exception_info[:200],
            'suggestion': 'Review full test output for details'
        }
