"""
Production-ready observability middleware.

This module provides middleware for:
- Request tracking and correlation IDs
- Response time measurement
- Error tracking and logging
- Context propagation
- Automatic metric collection

Author: Atoms MCP Platform
Version: 1.0.0
"""

import time
import traceback
from typing import Callable, Optional
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from .logging import (
    LogContext,
    get_logger,
    set_correlation_id,
    set_request_path,
    set_user_context,
)
from .metrics import (
    active_connections,
    http_request_duration_seconds,
    http_requests_total,
    record_error,
)

logger = get_logger(__name__)


class RequestTrackingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for tracking requests with correlation IDs and metrics.

    Features:
    - Generates/propagates correlation IDs
    - Tracks request duration
    - Records metrics
    - Injects logging context
    - Handles errors with proper logging
    """

    def __init__(
        self,
        app: ASGIApp,
        correlation_id_header: str = "X-Correlation-ID",
        user_id_header: str = "X-User-ID",
        session_id_header: str = "X-Session-ID"
    ):
        super().__init__(app)
        self.correlation_id_header = correlation_id_header
        self.user_id_header = user_id_header
        self.session_id_header = session_id_header

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with tracking and metrics."""
        start_time = time.perf_counter()

        # Extract or generate correlation ID
        correlation_id = request.headers.get(
            self.correlation_id_header,
            str(uuid4())
        )

        # Extract user context if available
        user_id = request.headers.get(self.user_id_header)
        session_id = request.headers.get(self.session_id_header)

        # Set logging context
        with LogContext(
            correlation_id=correlation_id,
            user_id=user_id,
            session_id=session_id,
            request_path=request.url.path
        ):
            # Track active connections
            active_connections.inc(labels={"type": "http"})

            try:
                # Log request start
                logger.info(
                    f"Request started: {request.method} {request.url.path}",
                    extra_fields={
                        "method": request.method,
                        "path": request.url.path,
                        "query_params": dict(request.query_params),
                        "client_host": request.client.host if request.client else None,
                    }
                )

                # Process request
                response = await call_next(request)

                # Calculate duration
                duration = time.perf_counter() - start_time

                # Add correlation ID to response headers
                response.headers[self.correlation_id_header] = correlation_id

                # Record metrics
                http_requests_total.inc(
                    labels={
                        "method": request.method,
                        "path": request.url.path,
                        "status": str(response.status_code)
                    }
                )

                http_request_duration_seconds.observe(
                    duration,
                    labels={
                        "method": request.method,
                        "path": request.url.path,
                        "status": str(response.status_code)
                    }
                )

                # Log request completion
                logger.info(
                    f"Request completed: {request.method} {request.url.path}",
                    extra_fields={
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": response.status_code,
                        "duration_ms": duration * 1000,
                    }
                )

                return response

            except Exception as e:
                # Calculate duration even on error
                duration = time.perf_counter() - start_time

                # Record error metrics
                record_error(
                    error_type=type(e).__name__,
                    source="middleware"
                )

                # Log error with full context
                logger.error(
                    f"Request failed: {request.method} {request.url.path}",
                    extra_fields={
                        "method": request.method,
                        "path": request.url.path,
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        "duration_ms": duration * 1000,
                        "traceback": traceback.format_exc(),
                    },
                    exc_info=True
                )

                # Re-raise to let error handlers deal with it
                raise

            finally:
                # Track active connections
                active_connections.dec(labels={"type": "http"})


class ErrorTrackingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for comprehensive error tracking.

    Catches and logs all unhandled exceptions with full context.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with error tracking."""
        try:
            response = await call_next(request)

            # Check for error status codes
            if response.status_code >= 400:
                logger.warning(
                    f"Error response: {request.method} {request.url.path}",
                    extra_fields={
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": response.status_code,
                    }
                )

            return response

        except Exception as e:
            # Log the error
            logger.exception(
                f"Unhandled exception in {request.method} {request.url.path}",
                extra_fields={
                    "method": request.method,
                    "path": request.url.path,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                }
            )

            # Record error metric
            record_error(
                error_type=type(e).__name__,
                source="unhandled_exception"
            )

            # Re-raise to let error handlers create proper response
            raise


class PerformanceTrackingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for tracking request performance.

    Monitors slow requests and logs performance warnings.
    """

    def __init__(
        self,
        app: ASGIApp,
        slow_request_threshold_seconds: float = 1.0,
        very_slow_request_threshold_seconds: float = 5.0
    ):
        super().__init__(app)
        self.slow_threshold = slow_request_threshold_seconds
        self.very_slow_threshold = very_slow_request_threshold_seconds

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with performance tracking."""
        start_time = time.perf_counter()

        response = await call_next(request)

        duration = time.perf_counter() - start_time

        # Check for slow requests
        if duration >= self.very_slow_threshold:
            logger.warning(
                f"Very slow request detected: {request.method} {request.url.path}",
                extra_fields={
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration * 1000,
                    "threshold": "very_slow",
                }
            )
        elif duration >= self.slow_threshold:
            logger.warning(
                f"Slow request detected: {request.method} {request.url.path}",
                extra_fields={
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration * 1000,
                    "threshold": "slow",
                }
            )

        # Add performance header
        response.headers["X-Response-Time-Ms"] = str(int(duration * 1000))

        return response


class ContextPropagationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for propagating context across service boundaries.

    Ensures correlation IDs and user context are maintained across
    internal service calls.
    """

    def __init__(
        self,
        app: ASGIApp,
        propagate_headers: Optional[list] = None
    ):
        super().__init__(app)
        self.propagate_headers = propagate_headers or [
            "X-Correlation-ID",
            "X-User-ID",
            "X-Session-ID",
            "X-Request-ID",
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with context propagation."""
        # Extract headers to propagate
        propagated_context = {}
        for header in self.propagate_headers:
            value = request.headers.get(header)
            if value:
                propagated_context[header] = value

        # Store in request state for downstream use
        request.state.propagated_context = propagated_context

        response = await call_next(request)

        # Add propagated headers to response
        for header, value in propagated_context.items():
            if header not in response.headers:
                response.headers[header] = value

        return response


def get_propagated_headers(request: Request) -> dict:
    """
    Extract headers that should be propagated to downstream services.

    Args:
        request: The current request

    Returns:
        Dictionary of headers to propagate
    """
    if hasattr(request.state, "propagated_context"):
        return request.state.propagated_context
    return {}
