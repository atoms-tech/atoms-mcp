"""Rich error classification system - transforms test failures into actionable diagnostics.

Classifies errors as:
- INFRASTRUCTURE: DB, API, service connectivity issues
- PRODUCT: Business logic bugs, implementation gaps
- TEST_DATA: Invalid fixtures, missing test data
- ASSERTION: Test expectation mismatches
"""

import re
from typing import Optional, Tuple
from enum import Enum
from dataclasses import dataclass


@dataclass
class ErrorDiagnostic:
    """Rich diagnostic report for a test failure."""
    
    category: str  # "INFRASTRUCTURE" | "PRODUCT" | "TEST_DATA" | "ASSERTION"
    root_cause: str
    detailed_explanation: str
    fix_suggestions: list
    code_snippet: Optional[str] = None
    
    def __post_init__(self):
        """Ensure category is always a string for serialization."""
        if isinstance(self.category, Category):
            self.category = str(self.category.value)
    
    def to_string(self) -> str:
        """Format diagnostic as readable error report."""
        emoji = {
            "INFRASTRUCTURE": "🔴",
            "PRODUCT": "🟠",
            "TEST_DATA": "🟡",
            "ASSERTION": "🟢"
        }.get(self.category, "⚪")
        
        report = f"""
{emoji} {self.category} ERROR

Root Cause: {self.root_cause}

What went wrong:
{self.detailed_explanation}

How to fix it:
"""
        for i, suggestion in enumerate(self.fix_suggestions, 1):
            report += f"{i}. {suggestion}\n"
        
        if self.code_snippet:
            report += f"\nCode to add/fix:\n{self.code_snippet}\n"
        
        return report


class Category(str, Enum):
    """String enum for better serialization with pytest-xdist."""
    INFRASTRUCTURE = "INFRASTRUCTURE"
    PRODUCT = "PRODUCT"
    TEST_DATA = "TEST_DATA"
    ASSERTION = "ASSERTION"

class ErrorClassifier:
    """Classifies test failures and generates rich diagnostics."""
    
    # Infrastructure error patterns
    INFRA_PATTERNS = [
        (r"ConnectionError|Connection.*refused|Connection.*timeout", "Database connection failed"),
        (r"asyncio|await|async", "Async/event loop issue"),
        (r"timeout|timed out|TimeoutError", "Service timeout"),
        (r"404.*not found|endpoint.*not found", "API endpoint not found"),
        (r"500|Internal Server Error|gateway", "Server error"),
        (r"FAILED.*conftest|fixture.*not found", "Test fixture missing"),
        (r"ImportError|ModuleNotFoundError", "Import/dependency issue"),
    ]
    
    # Product error patterns
    PRODUCT_PATTERNS = [
        (r"NotImplementedError|not implemented", "Feature not implemented"),
        (r"assert.*None|returned None|is None", "Missing return value"),
        (r"KeyError|key.*not found", "Missing field/key"),
        (r"TypeError|type.*mismatch", "Type mismatch"),
        (r"ValidationError|invalid.*payload", "Validation failed"),
        (r"RLS|row.*level.*security|permission denied", "RLS/permission issue"),
    ]
    
    # Test data patterns
    TEST_DATA_PATTERNS = [
        (r"factory|fixture.*missing|undefined.*fixture", "Fixture not defined"),
        (r"required.*field|missing.*required", "Required test data missing"),
        (r"invalid.*payload|malformed.*data", "Test data format invalid"),
        (r"constraint.*violation|unique.*constraint", "Data constraint violated"),
    ]
    
    @staticmethod
    def classify(error_msg: str, error_type: str = None):
        """Classify error into category based on message.
        Accepts any exception or message-like object; coerces to safe string.
        """
        try:
            # Coerce to string first, then lowercase safely
            error_text = str(error_msg) if error_msg is not None else ""
            error_lower = error_text.lower()
        except Exception:
            error_lower = ""
        
        # Check infrastructure patterns
        for pattern, reason in ErrorClassifier.INFRA_PATTERNS:
            if re.search(pattern, error_lower, re.IGNORECASE):
                return (Category.INFRASTRUCTURE, reason)
        
        # Check test data patterns
        for pattern, reason in ErrorClassifier.TEST_DATA_PATTERNS:
            if re.search(pattern, error_lower, re.IGNORECASE):
                return (Category.TEST_DATA, reason)
        
        # Check product patterns
        for pattern, reason in ErrorClassifier.PRODUCT_PATTERNS:
            if re.search(pattern, error_lower, re.IGNORECASE):
                return (Category.PRODUCT, reason)
        
        # Default to assertion
        return (Category.ASSERTION, "Assertion mismatch or unclassified error")

    @staticmethod
    def get_icon(category):
        mapping = {
            Category.INFRASTRUCTURE: "🔴",
            Category.PRODUCT: "🟠",
            Category.TEST_DATA: "🟡",
            Category.ASSERTION: "🟢",
        }
        return mapping.get(category, "⚪")
    
    @staticmethod
    def get_root_cause(error_msg: str, category: str) -> str:
        """Extract specific root cause from error message.
        Handles non-string messages robustly.
        """
        try:
            error_lower = (str(error_msg) if error_msg is not None else "").lower()
        except Exception:
            error_lower = ""
        
        patterns = {
            "INFRASTRUCTURE": ErrorClassifier.INFRA_PATTERNS,
            "PRODUCT": ErrorClassifier.PRODUCT_PATTERNS,
            "TEST_DATA": ErrorClassifier.TEST_DATA_PATTERNS,
        }
        
        for pattern, description in patterns.get(category, []):
            if re.search(pattern, error_lower, re.IGNORECASE):
                return description
        
        return error_msg[:100]
    
    @staticmethod
    def diagnose(exception: Exception, test_name: str) -> ErrorDiagnostic:
        """Generate rich diagnostic for exception."""
        error_msg = str(exception)
        error_type = type(exception).__name__
        category = ErrorClassifier.classify(error_msg, error_type)
        root_cause = ErrorClassifier.get_root_cause(error_msg, category)
        
        # Generate category-specific diagnostics
        if category == "INFRASTRUCTURE":
            return ErrorClassifier._diagnose_infra(error_msg, test_name, root_cause)
        elif category == "PRODUCT":
            return ErrorClassifier._diagnose_product(error_msg, test_name, root_cause)
        elif category == "TEST_DATA":
            return ErrorClassifier._diagnose_test_data(error_msg, test_name, root_cause)
        else:
            return ErrorClassifier._diagnose_assertion(error_msg, test_name, root_cause)
    
    @staticmethod
    def _diagnose_infra(error_msg: str, test_name: str, root_cause: str) -> ErrorDiagnostic:
        """Diagnose infrastructure errors."""
        suggestions = [
            "Check service health: `docker ps` or `systemctl status atoms-mcp`",
            "Verify database connection: Check SUPABASE_URL and SUPABASE_KEY env vars",
            "Check logs: `docker logs atoms_mcp` or `journalctl -u atoms-mcp`",
            "Run health check: `pytest tests/unit/infrastructure/test_adapters.py -v`",
            "Increase timeout: Some services need more time, retry with `--timeout=30`",
        ]
        
        return ErrorDiagnostic(
            category="INFRASTRUCTURE",
            root_cause=root_cause,
            detailed_explanation=f"Test '{test_name}' failed due to infrastructure issue: {error_msg[:200]}",
            fix_suggestions=suggestions,
        )
    
    @staticmethod
    def _diagnose_product(error_msg: str, test_name: str, root_cause: str) -> ErrorDiagnostic:
        """Diagnose product/business logic errors."""
        suggestions = [
            "Review business logic implementation",
            "Check if feature is complete: Look for NotImplementedError or TODO comments",
            "Verify API contract matches test expectations",
            "Review recent commits that may have broken this feature",
            "Check tool implementation in tools/*.py",
        ]
        
        # Extract tool name from test name
        tool = "entity"
        if "organization" in test_name.lower():
            tool = "organization"
        elif "project" in test_name.lower():
            tool = "project"
        elif "relationship" in test_name.lower():
            tool = "relationship"
        
        code_snippet = f"""
# Check if {tool} tool is fully implemented:
grep -n "NotImplementedError\\|TODO.*{tool}" tools/{tool}.py

# If feature is missing, implement it before running test
"""
        
        return ErrorDiagnostic(
            category="PRODUCT",
            root_cause=root_cause,
            detailed_explanation=f"Business logic or implementation gap: {error_msg[:200]}",
            fix_suggestions=suggestions,
            code_snippet=code_snippet.strip(),
        )
    
    @staticmethod
    def _diagnose_test_data(error_msg: str, test_name: str, root_cause: str) -> ErrorDiagnostic:
        """Diagnose test data/fixture errors."""
        suggestions = [
            "Verify test fixture is defined in conftest.py",
            "Check fixture parameters match test requirements",
            "Review test factory methods: tests/framework/data_generators.py",
            "Ensure test data meets all constraints (required fields, unique values, etc.)",
            "Run with verbose logging: pytest -vv --log-level=DEBUG",
        ]
        
        return ErrorDiagnostic(
            category="TEST_DATA",
            root_cause=root_cause,
            detailed_explanation=f"Test data or fixture issue: {error_msg[:200]}",
            fix_suggestions=suggestions,
        )
    
    @staticmethod
    def _diagnose_assertion(error_msg: str, test_name: str, root_cause: str) -> ErrorDiagnostic:
        """Diagnose assertion/expectation mismatches."""
        suggestions = [
            "Review test expectations vs actual behavior",
            "Print debug info: Add `print(result)` before assertion",
            "Check if business logic recently changed",
            "Verify test is checking the right thing",
            "Compare with passing tests to see pattern",
        ]
        
        return ErrorDiagnostic(
            category="ASSERTION",
            root_cause=root_cause,
            detailed_explanation=f"Test expectation mismatch: {error_msg[:200]}",
            fix_suggestions=suggestions,
        )


class ErrorReport:
    """Accumulates error diagnostics during test session."""
    
    def __init__(self):
        self.errors_by_category = {
            Category.INFRASTRUCTURE: [],
            Category.PRODUCT: [],
            Category.TEST_DATA: [],
            Category.ASSERTION: [],
        }
        self.total_errors = 0
    
    def add_error(self, test_name=None, exception: Exception = None, category=None, reason: str = ""):
        """Add classified error to report (conftest-compatible signature)."""
        cat_enum = category if isinstance(category, Category) else Category(str(category)) if category else Category.ASSERTION
        # Ensure category is stored as string for serialization
        cat_str = str(cat_enum.value) if hasattr(cat_enum, 'value') else str(cat_enum)
        diag = ErrorDiagnostic(
            category=cat_str,
            root_cause=reason or (str(exception)[:100] if exception else ""),
            detailed_explanation=f"{str(exception)[:200] if exception else ''}",
            fix_suggestions=[],
        )
        self.errors_by_category[cat_enum].append(diag)
        self.total_errors += 1
    
    def summary(self) -> str:
        """Generate summary of all errors by category."""
        report = "\n╔════════════════════════════════════════════════════════════╗\n"
        report += "║              TEST ERROR SUMMARY BY CATEGORY                 ║\n"
        report += "╠════════════════════════════════════════════════════════════╣\n"
        
        emojis = {
            Category.INFRASTRUCTURE: "🔴",
            Category.PRODUCT: "🟠",
            Category.TEST_DATA: "🟡",
            Category.ASSERTION: "🟢"
        }
        
        for category in [Category.INFRASTRUCTURE, Category.PRODUCT, Category.TEST_DATA, Category.ASSERTION]:
            count = len(self.errors_by_category[category])
            emoji = emojis[category]
            report += f"║ {emoji} {category.value:20} │ {count:3} error(s) ║\n"
        
        report += f"║                                                            ║\n"
        report += f"║ Total: {self.total_errors} error(s)                                         ║\n"
        report += "╚════════════════════════════════════════════════════════════╝\n"
        
        return report

    # Backwards-compatible alias expected by conftest
    def generate_summary(self) -> str:
        return self.summary()
