"""
PyDevKit - Python Development Toolkit

A comprehensive collection of utilities for Python development including:
- HTTP utilities (client, retries, headers, auth)
- Configuration management (env, YAML/JSON, validation)
- Security utilities (hashing, encryption, JWT)
- Data structures (LRU cache, priority queue, bloom filter)
- String utilities (slugify, sanitize, templating)
- Date/time utilities (parsing, formatting, timezones)
- File utilities (path handling, temp files, locks)
- Async utilities (event bus, task queue, semaphores)
- Validation utilities (email, URL, phone, custom)
- Functional utilities (compose, pipe, curry, memoize)
- Rate limiting (token bucket, sliding window)
- Structured error handling and API errors
- Concurrency utilities with Redis/in-memory locking
- Tracing and observability
- Monitoring and performance analytics
"""

from . import (
    async_utils,
    concurrency,
    config,
    correlation_id,
    data_structures,
    errors,
    fs,
    functional,
    http,
    monitoring,
    performance,
    rate_limiting,
    security,
    strings,
    tracing,
    validation,
)
from . import (
    datetime as dt,
)
from . import (
    logging as logging_utils,
)

# Concurrency
from .concurrency import (
    acquire_repo_lock,
    acquire_wd_lock,
    release_repo_lock,
    release_wd_lock,
)

# Config
from .config import ConfigManager, EnvLoader, get_config, load_env_file

# Correlation IDs
from .correlation_id import (
    clear_correlation_id,
    correlation_context,
    get_correlation_id,
    get_or_create_correlation_id,
    set_correlation_id,
)

# Data Structures
from .data_structures import BloomFilter, LRUCache, PriorityQueue

# Errors
from .errors import (
    ApiError,
    AuthenticationError,
    ConfigurationError,
    ErrorHandler,
    ErrorSeverity,
    NetworkError,
    RetryConfig,
    StructuredError,
    ValidationError,
    ZenMCPError,
    normalize_error,
)

# Functional
from .functional import compose, curry, memoize, pipe

# HTTP
from .http import HTTPClient, RetryStrategy, exponential_backoff

# Logging
from .logging import (
    ProgressLogger,
    console,
    get_logger,
    print_banner,
    print_error,
    print_info,
    print_status,
    print_success,
    print_warning,
    quiet_mode,
    setup_logging,
)

# Performance
from .performance import CompressionResult, MemoryMonitor, MemoryStats, PerformanceMonitor

# Rate Limiting
from .rate_limiting import RateLimiter, SlidingWindowRateLimiter

# Security
from .security import PIIScanner, create_jwt, hash_password, verify_jwt, verify_password

# Strings
from .strings import Template, sanitize_html, slugify

# Validation
from .validation import Validator, is_email, is_url

__version__ = "0.1.0"
__all__ = [
    # Modules
    "http",
    "config",
    "security",
    "data_structures",
    "strings",
    "dt",
    "fs",
    "async_utils",
    "validation",
    "functional",
    "rate_limiting",
    "errors",
    "tracing",
    "monitoring",
    "concurrency",
    "performance",
    "correlation_id",
    "logging_utils",
    # Key exports
    "HTTPClient",
    "RetryStrategy",
    "exponential_backoff",
    "ConfigManager",
    "get_config",
    "EnvLoader",
    "load_env_file",
    "hash_password",
    "verify_password",
    "create_jwt",
    "verify_jwt",
    "PIIScanner",
    "LRUCache",
    "PriorityQueue",
    "BloomFilter",
    "slugify",
    "sanitize_html",
    "Template",
    "is_email",
    "is_url",
    "Validator",
    "compose",
    "pipe",
    "curry",
    "memoize",
    "RateLimiter",
    "SlidingWindowRateLimiter",
    "acquire_wd_lock",
    "release_wd_lock",
    "acquire_repo_lock",
    "release_repo_lock",
    "MemoryMonitor",
    "MemoryStats",
    "CompressionResult",
    "PerformanceMonitor",
    "ApiError",
    "normalize_error",
    "ZenMCPError",
    "NetworkError",
    "AuthenticationError",
    "ValidationError",
    "ConfigurationError",
    "StructuredError",
    "ErrorSeverity",
    "RetryConfig",
    "ErrorHandler",
    "get_correlation_id",
    "get_or_create_correlation_id",
    "set_correlation_id",
    "clear_correlation_id",
    "correlation_context",
    "setup_logging",
    "get_logger",
    "ProgressLogger",
    "print_banner",
    "print_status",
    "print_error",
    "print_success",
    "print_warning",
    "print_info",
    "quiet_mode",
    "console",
]
