"""
Error Classification Framework

Classifies test failures into categories for better debugging and triage.
"""

import re
from enum import Enum
from typing import Optional, Pattern, Union


class ErrorCategory(Enum):
    """Categories of test failures."""
    
    INFRA = "infrastructure"          # DB, network, external services
    PRODUCT = "product"                # Business logic bugs
    TRANSIENT = "transient"            # Temporary failures, retry-able
    CONFIG = "configuration"           # Env vars, secrets, deployment config
    DATA = "test_data"                 # Test fixtures, seed data issues
    UNKNOWN = "unknown"                # Unable to classify


class ErrorClassifier:
    """Classifies exceptions into error categories."""
    
    # Infrastructure error patterns
    INFRA_PATTERNS = [
        (ConnectionRefusedError, "Service connection refused"),
        (ConnectionResetError, "Connection reset by peer"),
        (TimeoutError, "Service timeout"),
        (r"permission denied.*42501", "Database permission denied (RLS policy)"),
        (r"connection pool exhausted", "Database connection pool exhausted"),
        (r"network unreachable", "Network infrastructure issue"),
        (r"row-level security policy", "RLS policy blocking access"),
        (r"could not connect to server", "Database server unreachable"),
        (r"SSL connection has been closed unexpectedly", "SSL/TLS connection failed"),
        (r"no route to host", "Network routing issue"),
        (r"name resolution failed", "DNS resolution failed"),
        # Atoms MCP specific infrastructure patterns
        (r"MissingSupabaseConfig", "Supabase configuration missing"),
        (r"NEXT_PUBLIC_SUPABASE_URL.*not set", "Supabase URL not configured"),
        (r"SUPABASE_SERVICE_ROLE_KEY.*not set", "Supabase service key missing"),
        (r"TABLE_ACCESS_RESTRICTED", "Table access restricted (RLS or GRANT)"),
        (r"Vertex AI.*not configured", "Vertex AI embedding service not configured"),
        (r"Redis.*connection.*failed", "Redis/Upstash connection failed"),
        (r"rate limit.*upstash", "Upstash rate limit exceeded"),
    ]
    
    # Product/business logic error patterns
    PRODUCT_PATTERNS = [
        (AssertionError, "Business logic assertion failed"),
        (r"validation.*failed", "Input validation error"),
        (r"invalid.*state", "Invalid application state"),
        (r"constraint.*violated", "Business rule constraint violated"),
        (r"expected.*but got", "Unexpected behavior (logic bug)"),
        (ValueError, "Invalid value (likely business logic)"),
        (KeyError, "Missing expected data key"),
        # Atoms MCP specific product patterns
        (r"ApiError.*UNAUTHORIZED_ORG_ACCESS", "Organization membership validation failed"),
        (r"ApiError.*DUPLICATE_ENTRY", "Duplicate entity creation attempt"),
        (r"ApiError.*INVALID_REFERENCE", "Foreign key reference validation failed"),
        (r"entity.*type.*not supported", "Unsupported entity type"),
        (r"workspace.*context.*missing", "Workspace context not set"),
        (r"embedding.*generation.*failed", "Embedding generation logic error"),
    ]
    
    # Transient error patterns (retry-able)
    TRANSIENT_PATTERNS = [
        (r"429.*rate limit", "Rate limit exceeded"),
        (r"503.*service unavailable", "Service temporarily unavailable"),
        (r"deadlock detected", "Database deadlock (transient)"),
        (r"lock wait timeout", "Lock timeout (transient)"),
        (r"connection.*temporarily unavailable", "Temporary connection issue"),
        (r"too many connections", "Connection pool temporarily full"),
        (r"retry", "Explicit retry condition"),
    ]
    
    # Configuration error patterns
    CONFIG_PATTERNS = [
        (r"environment variable.*not (set|found)", "Missing environment variable"),
        (r"secret.*not found", "Missing secret/credential"),
        (r"invalid.*configuration", "Invalid configuration value"),
        (r"(NEXT_PUBLIC_SUPABASE_URL|SUPABASE_SERVICE_ROLE_KEY).*not set", "Missing Supabase config"),
        (r"auth.*not configured", "Authentication not configured"),
        (r"missing.*required.*setting", "Missing required setting"),
        # Atoms MCP specific config patterns
        (r"ATOMS_SERVICE_MODE.*not set", "Service mode not configured (mock/live)"),
        (r"WORKOS_.*not set", "WorkOS authentication config missing"),
        (r"GOOGLE_CLOUD_PROJECT.*not set", "GCP project not configured"),
        (r"UPSTASH_REDIS_.*not set", "Upstash Redis config missing"),
        (r"mock.*mode.*enabled", "Running in mock mode (not an error, but notable)"),
    ]
    
    # Test data error patterns
    DATA_PATTERNS = [
        (r"fixture.*not found", "Missing test fixture"),
        (r"seed data.*failed", "Test seed data issue"),
        (r"factory.*error", "Test data factory error"),
        (r"mock.*setup.*failed", "Mock configuration issue"),
    ]
    
    @classmethod
    def classify(
        cls,
        exception: Exception,
        test_context: Optional[dict] = None
    ) -> tuple[ErrorCategory, str]:
        """
        Classify an exception into an error category.
        
        Args:
            exception: The exception to classify
            test_context: Optional context about the test (markers, path, etc.)
        
        Returns:
            Tuple of (ErrorCategory, human-readable reason)
        """
        exc_str = str(exception)
        exc_type = type(exception)
        
        # Check infrastructure patterns
        for pattern, reason in cls.INFRA_PATTERNS:
            if cls._matches_pattern(exception, exc_str, pattern):
                return ErrorCategory.INFRA, reason
        
        # Check transient patterns (before product, as they're more specific)
        for pattern, reason in cls.TRANSIENT_PATTERNS:
            if cls._matches_pattern(exception, exc_str, pattern):
                return ErrorCategory.TRANSIENT, reason
        
        # Check configuration patterns
        for pattern, reason in cls.CONFIG_PATTERNS:
            if cls._matches_pattern(exception, exc_str, pattern):
                return ErrorCategory.CONFIG, reason
        
        # Check test data patterns
        for pattern, reason in cls.DATA_PATTERNS:
            if cls._matches_pattern(exception, exc_str, pattern):
                return ErrorCategory.DATA, reason
        
        # Check product patterns (last, as they're more generic)
        for pattern, reason in cls.PRODUCT_PATTERNS:
            if cls._matches_pattern(exception, exc_str, pattern):
                return ErrorCategory.PRODUCT, reason
        
        # Unable to classify
        return ErrorCategory.UNKNOWN, f"Unclassified: {exc_type.__name__}: {exc_str[:100]}"
    
    @staticmethod
    def _matches_pattern(
        exception: Exception,
        exc_str: str,
        pattern: Union[type, str]
    ) -> bool:
        """Check if exception matches a pattern (type or regex)."""
        if isinstance(pattern, type):
            return isinstance(exception, pattern)
        elif isinstance(pattern, str):
            return bool(re.search(pattern, exc_str, re.IGNORECASE))
        return False
    
    @staticmethod
    def get_icon(category: ErrorCategory) -> str:
        """Get emoji icon for error category."""
        icons = {
            ErrorCategory.INFRA: "🔧",
            ErrorCategory.PRODUCT: "🐛",
            ErrorCategory.TRANSIENT: "⏱️",
            ErrorCategory.CONFIG: "⚙️",
            ErrorCategory.DATA: "📊",
            ErrorCategory.UNKNOWN: "❓",
        }
        return icons.get(category, "❓")
    
    @staticmethod
    def get_action(category: ErrorCategory) -> str:
        """Get recommended action for error category."""
        actions = {
            ErrorCategory.INFRA: "Contact ops team; check infrastructure",
            ErrorCategory.PRODUCT: "Fix code; review business logic",
            ErrorCategory.TRANSIENT: "Retry test; check service health",
            ErrorCategory.CONFIG: "Update environment variables; check deployment",
            ErrorCategory.DATA: "Fix test fixtures; regenerate seed data",
            ErrorCategory.UNKNOWN: "Manual investigation required",
        }
        return actions.get(category, "Unknown")


class ErrorReport:
    """Generates categorized error reports."""
    
    def __init__(self):
        self.errors_by_category = {cat: [] for cat in ErrorCategory}
    
    def add_error(
        self,
        test_name: str,
        exception: Exception,
        category: ErrorCategory,
        reason: str
    ):
        """Add an error to the report."""
        self.errors_by_category[category].append({
            "test": test_name,
            "exception": exception,
            "reason": reason,
        })
    
    def generate_summary(self) -> str:
        """Generate a text summary of errors by category."""
        lines = []
        lines.append("\n" + "="*70)
        lines.append("ERROR CLASSIFICATION REPORT")
        lines.append("="*70)
        
        total_errors = sum(len(errors) for errors in self.errors_by_category.values())
        if total_errors == 0:
            lines.append("\n✅ No errors detected!")
            lines.append("="*70)
            return "\n".join(lines)
        
        for category in ErrorCategory:
            errors = self.errors_by_category[category]
            if not errors:
                continue
            
            icon = ErrorClassifier.get_icon(category)
            action = ErrorClassifier.get_action(category)
            
            lines.append(f"\n{icon} {category.name} ERRORS ({len(errors)}):")
            lines.append(f"   Action: {action}")
            lines.append("")
            
            # Show first 3 errors
            for error in errors[:3]:
                lines.append(f"   • {error['test']}")
                lines.append(f"     → {error['reason']}")
            
            if len(errors) > 3:
                lines.append(f"   ... and {len(errors)-3} more")
        
        lines.append("\n" + "="*70)
        return "\n".join(lines)
    
    def get_distribution(self) -> dict[str, int]:
        """Get error count by category."""
        return {
            cat.name: len(errors)
            for cat, errors in self.errors_by_category.items()
            if errors
        }
