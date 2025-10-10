"""Enhanced error handling with structured responses, retry logic, and fallback strategies.

This module provides:
- Structured error responses with detailed context
- Exponential backoff retry logic
- Provider fallback strategies
- Circuit breaker pattern for failing services
- Error categorization and recovery suggestions
- Comprehensive error logging and monitoring
"""

import asyncio
import functools
import logging
import random
import time
import traceback
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, TypeVar

from pydevkit.correlation_id import get_correlation_id

logger = logging.getLogger(__name__)

T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])


class ErrorCategory(Enum):
    """Categories of errors for structured handling."""

    # Network and connectivity errors
    NETWORK_ERROR = "network_error"
    CONNECTION_TIMEOUT = "connection_timeout"
    DNS_RESOLUTION = "dns_resolution"

    # Authentication and authorization
    AUTH_ERROR = "auth_error"
    PERMISSION_DENIED = "permission_denied"
    API_KEY_INVALID = "api_key_invalid"
    RATE_LIMITED = "rate_limited"

    # Provider-specific errors
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    MODEL_NOT_FOUND = "model_not_found"
    CONTEXT_LENGTH_EXCEEDED = "context_length_exceeded"
    CONTENT_FILTERED = "content_filtered"

    # Resource and capacity errors
    QUOTA_EXCEEDED = "quota_exceeded"
    RESOURCE_EXHAUSTED = "resource_exhausted"
    SERVICE_OVERLOADED = "service_overloaded"

    # Data and validation errors
    INVALID_REQUEST = "invalid_request"
    MALFORMED_RESPONSE = "malformed_response"
    VALIDATION_ERROR = "validation_error"

    # System errors
    INTERNAL_ERROR = "internal_error"
    CONFIGURATION_ERROR = "configuration_error"
    DEPENDENCY_ERROR = "dependency_error"

    # Unknown or unclassified
    UNKNOWN_ERROR = "unknown_error"


class ErrorSeverity(Enum):
    """Severity levels for errors."""

    LOW = "low"  # Minor issues, recoverable
    MEDIUM = "medium"  # Significant issues, may impact functionality
    HIGH = "high"  # Critical issues, major functionality affected
    CRITICAL = "critical"  # System-wide failures


@dataclass
class ErrorContext:
    """Context information for errors."""

    # Basic error info
    error_id: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    original_exception: Exception | None = None

    # Request context
    correlation_id: str | None = None
    provider_name: str | None = None
    model_name: str | None = None
    operation_name: str | None = None

    # Timing information
    timestamp: datetime = field(default_factory=datetime.now)
    retry_attempt: int = 0
    total_attempts: int = 1

    # Additional context
    user_message: str = ""
    technical_details: dict[str, Any] = field(default_factory=dict)
    recovery_suggestions: list[str] = field(default_factory=list)

    # Metadata
    stack_trace: str | None = None
    request_data: dict[str, Any] = field(default_factory=dict)
    response_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class RetryConfig:
    """Configuration for retry logic."""

    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_categories: list[ErrorCategory] = field(
        default_factory=lambda: [
            ErrorCategory.NETWORK_ERROR,
            ErrorCategory.CONNECTION_TIMEOUT,
            ErrorCategory.SERVICE_OVERLOADED,
            ErrorCategory.RATE_LIMITED,
            ErrorCategory.RESOURCE_EXHAUSTED,
        ]
    )


class StructuredError(Exception):
    """Structured error with detailed context."""

    def __init__(self, context: ErrorContext):
        self.context = context
        super().__init__(context.message)

    def to_dict(self) -> dict[str, Any]:
        """Convert error to dictionary format."""
        return {
            "error_id": self.context.error_id,
            "category": self.context.category.value,
            "severity": self.context.severity.value,
            "message": self.context.message,
            "user_message": self.context.user_message,
            "correlation_id": self.context.correlation_id,
            "provider_name": self.context.provider_name,
            "model_name": self.context.model_name,
            "operation_name": self.context.operation_name,
            "timestamp": self.context.timestamp.isoformat(),
            "retry_attempt": self.context.retry_attempt,
            "total_attempts": self.context.total_attempts,
            "technical_details": self.context.technical_details,
            "recovery_suggestions": self.context.recovery_suggestions,
            "stack_trace": self.context.stack_trace,
        }


class CircuitBreaker:
    """Circuit breaker for failing services."""

    def __init__(
        self, failure_threshold: int = 5, recovery_timeout: int = 60, expected_exception: type[Exception] = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        # State tracking
        self.failure_count = 0
        self.last_failure_time: datetime | None = None
        self.state = "closed"  # closed, open, half-open

    def _should_attempt_call(self) -> bool:
        """Check if we should attempt the call."""
        if self.state == "closed":
            return True

        if self.state == "open":
            # Check if we should move to half-open
            if self.last_failure_time and datetime.now() - self.last_failure_time > timedelta(
                seconds=self.recovery_timeout
            ):
                self.state = "half-open"
                return True
            return False

        # half-open state
        return True

    def _record_success(self):
        """Record a successful call."""
        self.failure_count = 0
        self.state = "closed"

    def _record_failure(self):
        """Record a failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.failure_threshold:
            self.state = "open"

    def __call__(self, func: Callable) -> Callable:
        """Decorator to apply circuit breaker."""

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not self._should_attempt_call():
                raise StructuredError(
                    ErrorContext(
                        error_id=f"circuit_breaker_{id(self)}",
                        category=ErrorCategory.SERVICE_OVERLOADED,
                        severity=ErrorSeverity.HIGH,
                        message="Service circuit breaker is open",
                        user_message="Service is temporarily unavailable due to repeated failures",
                        technical_details={"state": self.state, "failure_count": self.failure_count},
                    )
                )

            try:
                result = func(*args, **kwargs)
                self._record_success()
                return result
            except self.expected_exception:
                self._record_failure()
                raise

        return wrapper


class ErrorHandler:
    """Centralized error handling with categorization and recovery."""

    def __init__(self):
        self.error_stats: dict[str, int] = {}
        self.circuit_breakers: dict[str, CircuitBreaker] = {}

    def categorize_error(self, exception: Exception, context: dict[str, Any] = None) -> ErrorCategory:
        """Categorize an error based on its type and message."""
        context = context or {}
        error_message = str(exception).lower()
        error_type = type(exception).__name__

        # Network-related errors
        if any(
            keyword in error_message
            for keyword in ["connection", "network", "timeout", "unreachable", "dns", "resolve"]
        ) or error_type in ["ConnectionError", "TimeoutError", "ConnectTimeout"]:
            if "timeout" in error_message:
                return ErrorCategory.CONNECTION_TIMEOUT
            elif "dns" in error_message or "resolve" in error_message:
                return ErrorCategory.DNS_RESOLUTION
            else:
                return ErrorCategory.NETWORK_ERROR

        # Authentication errors
        if any(
            keyword in error_message
            for keyword in ["unauthorized", "forbidden", "api key", "authentication", "invalid key"]
        ) or error_type in ["AuthenticationError", "PermissionError"]:
            if "rate limit" in error_message or "quota" in error_message:
                return ErrorCategory.RATE_LIMITED
            elif "api key" in error_message:
                return ErrorCategory.API_KEY_INVALID
            elif "forbidden" in error_message:
                return ErrorCategory.PERMISSION_DENIED
            else:
                return ErrorCategory.AUTH_ERROR

        # Provider-specific errors
        if any(keyword in error_message for keyword in ["model not found", "invalid model", "unsupported model"]):
            return ErrorCategory.MODEL_NOT_FOUND

        if any(
            keyword in error_message for keyword in ["context length", "token limit", "too long", "input too large"]
        ):
            return ErrorCategory.CONTEXT_LENGTH_EXCEEDED

        if any(
            keyword in error_message for keyword in ["content filtered", "policy violation", "inappropriate content"]
        ):
            return ErrorCategory.CONTENT_FILTERED

        # Resource errors
        if any(keyword in error_message for keyword in ["quota exceeded", "limit exceeded", "usage limit"]):
            return ErrorCategory.QUOTA_EXCEEDED

        if any(keyword in error_message for keyword in ["overloaded", "capacity", "too many requests"]):
            return ErrorCategory.SERVICE_OVERLOADED

        # Validation errors
        if error_type in ["ValueError", "ValidationError", "TypeError"]:
            return ErrorCategory.VALIDATION_ERROR

        if any(keyword in error_message for keyword in ["invalid request", "bad request", "malformed"]):
            return ErrorCategory.INVALID_REQUEST

        # System errors
        if error_type in ["SystemError", "OSError", "MemoryError"]:
            return ErrorCategory.INTERNAL_ERROR

        # Default to unknown
        return ErrorCategory.UNKNOWN_ERROR

    def determine_severity(self, category: ErrorCategory, context: dict[str, Any] = None) -> ErrorSeverity:
        """Determine error severity based on category and context."""
        context = context or {}

        # Critical errors that affect system functionality
        if category in [
            ErrorCategory.INTERNAL_ERROR,
            ErrorCategory.CONFIGURATION_ERROR,
            ErrorCategory.DEPENDENCY_ERROR,
        ]:
            return ErrorSeverity.CRITICAL

        # High severity errors that significantly impact functionality
        if category in [
            ErrorCategory.API_KEY_INVALID,
            ErrorCategory.PROVIDER_UNAVAILABLE,
            ErrorCategory.QUOTA_EXCEEDED,
        ]:
            return ErrorSeverity.HIGH

        # Medium severity errors that may impact functionality
        if category in [
            ErrorCategory.MODEL_NOT_FOUND,
            ErrorCategory.CONTEXT_LENGTH_EXCEEDED,
            ErrorCategory.RATE_LIMITED,
            ErrorCategory.SERVICE_OVERLOADED,
        ]:
            return ErrorSeverity.MEDIUM

        # Low severity errors that are typically recoverable
        return ErrorSeverity.LOW

    def generate_recovery_suggestions(self, category: ErrorCategory, context: dict[str, Any] = None) -> list[str]:
        """Generate recovery suggestions based on error category."""
        context = context or {}
        suggestions = []

        if category == ErrorCategory.NETWORK_ERROR:
            suggestions.extend(
                [
                    "Check your internet connection",
                    "Verify the service endpoint is reachable",
                    "Try again after a short delay",
                ]
            )

        elif category == ErrorCategory.CONNECTION_TIMEOUT:
            suggestions.extend(
                [
                    "Increase timeout settings if possible",
                    "Check network latency to the service",
                    "Retry with exponential backoff",
                ]
            )

        elif category == ErrorCategory.API_KEY_INVALID:
            suggestions.extend(
                [
                    "Verify your API key is correct and active",
                    "Check if the API key has the required permissions",
                    "Regenerate your API key if necessary",
                ]
            )

        elif category == ErrorCategory.RATE_LIMITED:
            suggestions.extend(
                [
                    "Wait before making another request",
                    "Implement rate limiting in your application",
                    "Consider upgrading your service plan",
                ]
            )

        elif category == ErrorCategory.MODEL_NOT_FOUND:
            suggestions.extend(
                [
                    "Check if the model name is correct",
                    "Verify the model is available in your region",
                    "Use a fallback model if available",
                ]
            )

        elif category == ErrorCategory.CONTEXT_LENGTH_EXCEEDED:
            suggestions.extend(
                [
                    "Reduce the input length",
                    "Use a model with a larger context window",
                    "Split the input into smaller chunks",
                ]
            )

        elif category == ErrorCategory.SERVICE_OVERLOADED:
            suggestions.extend(["Retry after a delay", "Use exponential backoff", "Try a different provider or model"])

        elif category == ErrorCategory.QUOTA_EXCEEDED:
            suggestions.extend(
                ["Wait until your quota resets", "Upgrade your service plan", "Use a different provider"]
            )

        else:
            suggestions.extend(
                [
                    "Check the error message for specific details",
                    "Verify your request parameters",
                    "Try again after a short delay",
                ]
            )

        return suggestions

    def create_error_context(
        self,
        exception: Exception,
        provider_name: str = "",
        model_name: str = "",
        operation_name: str = "",
        request_data: dict[str, Any] = None,
    ) -> ErrorContext:
        """Create comprehensive error context."""
        import uuid

        category = self.categorize_error(exception)
        severity = self.determine_severity(category)
        recovery_suggestions = self.generate_recovery_suggestions(category)

        # Generate user-friendly message
        user_message = self._generate_user_message(category, str(exception))

        context = ErrorContext(
            error_id=str(uuid.uuid4()),
            category=category,
            severity=severity,
            message=str(exception),
            original_exception=exception,
            user_message=user_message,
            correlation_id=get_correlation_id(),
            provider_name=provider_name,
            model_name=model_name,
            operation_name=operation_name,
            recovery_suggestions=recovery_suggestions,
            stack_trace=traceback.format_exc(),
            request_data=request_data or {},
        )

        # Add technical details
        context.technical_details = {
            "exception_type": type(exception).__name__,
            "exception_module": getattr(type(exception), "__module__", "unknown"),
            "python_version": f"{__import__('sys').version_info.major}.{__import__('sys').version_info.minor}",
        }

        # Track error statistics
        error_key = f"{category.value}_{provider_name or 'unknown'}"
        self.error_stats[error_key] = self.error_stats.get(error_key, 0) + 1

        return context

    def _generate_user_message(self, category: ErrorCategory, technical_message: str) -> str:
        """Generate user-friendly error message."""
        user_messages = {
            ErrorCategory.NETWORK_ERROR: "Network connection issue. Please check your internet connection and try again.",
            ErrorCategory.CONNECTION_TIMEOUT: "The request timed out. Please try again in a moment.",
            ErrorCategory.API_KEY_INVALID: "Invalid API key. Please check your credentials.",
            ErrorCategory.RATE_LIMITED: "Too many requests. Please wait a moment before trying again.",
            ErrorCategory.MODEL_NOT_FOUND: "The requested model is not available. Please try a different model.",
            ErrorCategory.CONTEXT_LENGTH_EXCEEDED: "Your input is too long. Please shorten your request.",
            ErrorCategory.SERVICE_OVERLOADED: "The service is temporarily overloaded. Please try again shortly.",
            ErrorCategory.QUOTA_EXCEEDED: "You've reached your usage limit. Please wait or upgrade your plan.",
            ErrorCategory.CONTENT_FILTERED: "Your request was filtered due to content policy. Please modify your input.",
            ErrorCategory.PROVIDER_UNAVAILABLE: "The AI service is temporarily unavailable. Please try again later.",
        }

        return user_messages.get(category, "An unexpected error occurred. Please try again.")


def with_retry(config: RetryConfig = None, error_handler: ErrorHandler = None):
    """Decorator to add retry logic with exponential backoff."""
    config = config or RetryConfig()
    error_handler = error_handler or ErrorHandler()

    def decorator(func: F) -> F:
        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                last_error = None

                for attempt in range(config.max_retries + 1):
                    try:
                        return await func(*args, **kwargs)
                    except Exception as e:
                        last_error = e

                        # Create error context
                        context = error_handler.create_error_context(
                            e,
                            operation_name=func.__name__,
                            request_data={"args": str(args)[:100], "kwargs": str(kwargs)[:100]},
                        )
                        context.retry_attempt = attempt
                        context.total_attempts = config.max_retries + 1

                        # Check if error is retryable
                        if attempt >= config.max_retries or context.category not in config.retryable_categories:
                            logger.error(f"Max retries exceeded or non-retryable error: {e}")
                            raise StructuredError(context)

                        # Calculate delay with exponential backoff and jitter
                        delay = min(config.base_delay * (config.exponential_base**attempt), config.max_delay)

                        if config.jitter:
                            delay *= 0.5 + random.random() * 0.5  # Add 0-50% jitter

                        logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.1f}s")
                        await asyncio.sleep(delay)

                # Should never reach here, but just in case
                raise StructuredError(error_handler.create_error_context(last_error))

            return async_wrapper
        else:

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                last_error = None

                for attempt in range(config.max_retries + 1):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        last_error = e

                        # Create error context
                        context = error_handler.create_error_context(
                            e,
                            operation_name=func.__name__,
                            request_data={"args": str(args)[:100], "kwargs": str(kwargs)[:100]},
                        )
                        context.retry_attempt = attempt
                        context.total_attempts = config.max_retries + 1

                        # Check if error is retryable
                        if attempt >= config.max_retries or context.category not in config.retryable_categories:
                            logger.error(f"Max retries exceeded or non-retryable error: {e}")
                            raise StructuredError(context)

                        # Calculate delay with exponential backoff and jitter
                        delay = min(config.base_delay * (config.exponential_base**attempt), config.max_delay)

                        if config.jitter:
                            delay *= 0.5 + random.random() * 0.5  # Add 0-50% jitter

                        logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.1f}s")
                        time.sleep(delay)

                # Should never reach here, but just in case
                raise StructuredError(error_handler.create_error_context(last_error))

            return sync_wrapper

    return decorator


def with_fallback(fallback_providers: list[str], error_handler: ErrorHandler = None):
    """Decorator to add provider fallback logic."""
    error_handler = error_handler or ErrorHandler()

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            original_provider = kwargs.get("provider_name", "")
            providers_to_try = [original_provider] + [p for p in fallback_providers if p != original_provider]

            last_error = None
            for provider in providers_to_try:
                if not provider:
                    continue

                try:
                    kwargs["provider_name"] = provider
                    result = func(*args, **kwargs)

                    if provider != original_provider:
                        logger.info(f"Successfully failed over from {original_provider} to {provider}")

                    return result

                except Exception as e:
                    last_error = e
                    logger.warning(f"Provider {provider} failed: {e}")
                    continue

            # All providers failed
            context = error_handler.create_error_context(
                last_error, operation_name=func.__name__, request_data={"tried_providers": providers_to_try}
            )
            context.technical_details["fallback_providers"] = providers_to_try
            raise StructuredError(context)

        return wrapper

    return decorator


# Global error handler instance
_error_handler: ErrorHandler | None = None


def get_error_handler() -> ErrorHandler:
    """Get the global error handler instance."""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler
