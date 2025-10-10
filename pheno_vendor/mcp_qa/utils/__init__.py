"""
MCP QA Utilities Package

Provides shared utilities for MCP testing including health checks, helpers,
validators, data generators, logging, configuration, database, auth, and metrics.
Unified from Zen and Atoms frameworks.
"""

# Existing utilities
from .health_checks import HealthChecker, HealthCheckResult
from .helpers import (
    DataGenerator,
    FieldValidator,
    PerformanceTracker,
    ResponseValidator,
    TimeoutManager,
    WaitStrategy,
    is_connection_error,
    timeout_wrapper,
)

# New consolidated utilities
from .logging_utils import (
    configure_logging,
    get_logger,
    quiet_library_loggers,
    set_verbose_mode,
    LoggerContext,
    QuietLogger,
)

from .config_utils import (
    get_env,
    get_env_config,
    load_env_file,
    load_yaml,
    save_yaml,
    ConfigBase,
    ConfigManager,
    DatabaseConfig,
    ServerConfig,
    AuthConfig,
)

from .database_utils import (
    QueryFilter,
    QueryCache,
    DatabaseAdapter,
    SupabaseDatabaseAdapter,
)

from .auth_utils import (
    decode_jwt,
    extract_user_from_jwt,
    is_token_expired,
    TokenSet,
    TokenManager,
    CredentialStore,
    SessionManager,
)

from .metrics_utils import (
    MetricValue,
    Counter,
    Gauge,
    Histogram,
    MetricsCollector,
    MetricsAggregator,
    MetricsReporter,
)

__all__ = [
    # Health Checks
    "HealthChecker",
    "HealthCheckResult",
    # Data Generation
    "DataGenerator",
    # Validation
    "ResponseValidator",
    "FieldValidator",
    # Timeout Management
    "TimeoutManager",
    "timeout_wrapper",
    # Retry Strategies
    "WaitStrategy",
    "is_connection_error",
    # Performance
    "PerformanceTracker",
    # Logging
    "configure_logging",
    "get_logger",
    "quiet_library_loggers",
    "set_verbose_mode",
    "LoggerContext",
    "QuietLogger",
    # Config
    "get_env",
    "get_env_config",
    "load_env_file",
    "load_yaml",
    "save_yaml",
    "ConfigBase",
    "ConfigManager",
    "DatabaseConfig",
    "ServerConfig",
    "AuthConfig",
    # Database
    "QueryFilter",
    "QueryCache",
    "DatabaseAdapter",
    "SupabaseDatabaseAdapter",
    # Auth
    "decode_jwt",
    "extract_user_from_jwt",
    "is_token_expired",
    "TokenSet",
    "TokenManager",
    "CredentialStore",
    "SessionManager",
    # Metrics
    "MetricValue",
    "Counter",
    "Gauge",
    "Histogram",
    "MetricsCollector",
    "MetricsAggregator",
    "MetricsReporter",
]

__version__ = "2.0.0"
