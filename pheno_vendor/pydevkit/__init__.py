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
    http,
    config,
    security,
    data_structures,
    strings,
    datetime as dt,
    fs,
    async_utils,
    validation,
    functional,
    rate_limiting,
    errors,
    tracing,
    monitoring,
    concurrency,
    performance,
    correlation_id,
    logging as logging_utils,
)

# HTTP
from .http import HTTPClient, RetryStrategy, exponential_backoff

# Config
from .config import ConfigManager, get_config, EnvLoader, load_env_file

# Security
from .security import hash_password, verify_password, create_jwt, verify_jwt, PIIScanner

# Data Structures
from .data_structures import LRUCache, PriorityQueue, BloomFilter

# Strings
from .strings import slugify, sanitize_html, Template

# Validation
from .validation import is_email, is_url, Validator

# Functional
from .functional import compose, pipe, curry, memoize

# Rate Limiting
from .rate_limiting import RateLimiter, SlidingWindowRateLimiter

# Concurrency
from .concurrency import (
    acquire_wd_lock,
    release_wd_lock,
    acquire_repo_lock,
    release_repo_lock,
)

# Performance
from .performance import MemoryMonitor, MemoryStats, CompressionResult, PerformanceMonitor

# Logging
from .logging import (
    setup_logging,
    get_logger,
    ProgressLogger,
    print_banner,
    print_status,
    print_error,
    print_success,
    print_warning,
    print_info,
    quiet_mode,
    console,
)

# Errors
from .errors import (
    ApiError,
    normalize_error,
    ZenMCPError,
    NetworkError,
    AuthenticationError,
    ValidationError,
    ConfigurationError,
    StructuredError,
    ErrorSeverity,
    RetryConfig,
    ErrorHandler,
)

# Correlation IDs
from .correlation_id import (
    get_correlation_id,
    get_or_create_correlation_id,
    set_correlation_id,
    clear_correlation_id,
    correlation_context,
)

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
