"""
Complete Atoms MCP Observability Integration Example

This example demonstrates a fully integrated application with:
- All middleware configured
- Health checks registered
- Webhooks configured
- Monitored tools
- Custom metrics
- Full observability coverage

This is a production-ready template you can use as a starting point.

Author: Atoms MCP Platform
"""

import asyncio
import os

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

# Observability imports
from lib.atoms.observability import (
    ComponentType,
    ContextPropagationMiddleware,
    CustomHealthCheck,
    ErrorTrackingMiddleware,
    LogContext,
    PerformanceTrackingMiddleware,
    # Middleware
    RequestTrackingMiddleware,
    WebhookEventType,
    # Webhooks
    configure_vercel_webhook,
    # Logging
    get_logger,
    log_operation,
    measure_performance,
    # Decorators
    observe_tool,
    record_error,
    # Health checks
    register_health_check,
    # Metrics
    registry,
    track_database_operation,
    webhook_manager,
)
from lib.atoms.observability import (
    # Endpoints
    router as observability_router,
)

# Initialize logger
logger = get_logger(__name__)

# ============================================================================
# Application Configuration
# ============================================================================

class Config:
    """Application configuration."""

    APP_NAME = "Atoms MCP Complete Example"
    APP_VERSION = "1.0.0"
    APP_ENVIRONMENT = os.getenv("APP_ENVIRONMENT", "development")

    # Observability
    VERCEL_WEBHOOK_URL = os.getenv("VERCEL_WEBHOOK_URL")
    ENABLE_WEBHOOKS = APP_ENVIRONMENT == "production"
    ENABLE_HEALTH_CHECKS = True

    # Performance thresholds
    SLOW_REQUEST_THRESHOLD = 1.0  # seconds
    VERY_SLOW_REQUEST_THRESHOLD = 5.0  # seconds


config = Config()

# ============================================================================
# FastAPI Application Setup
# ============================================================================

app = FastAPI(
    title=config.APP_NAME,
    version=config.APP_VERSION,
    description="Complete observability integration example"
)

# ============================================================================
# Middleware Configuration (Order matters - add in reverse order of execution)
# ============================================================================

logger.info("Configuring middleware")

# Context propagation (runs last, returns first)
app.add_middleware(ContextPropagationMiddleware)

# Request tracking (correlation IDs, metrics)
app.add_middleware(RequestTrackingMiddleware)

# Error tracking
app.add_middleware(ErrorTrackingMiddleware)

# Performance tracking
app.add_middleware(
    PerformanceTrackingMiddleware,
    slow_request_threshold_seconds=config.SLOW_REQUEST_THRESHOLD,
    very_slow_request_threshold_seconds=config.VERY_SLOW_REQUEST_THRESHOLD
)

logger.info("Middleware configured successfully")

# ============================================================================
# Health Checks Registration
# ============================================================================

if config.ENABLE_HEALTH_CHECKS:
    logger.info("Registering health checks")

    # Example: Database health check
    async def check_database_async() -> bool:
        """Check database connectivity."""
        try:
            # In production, replace with actual database check
            # Example: await db.execute("SELECT 1")
            await asyncio.sleep(0.01)  # Simulate check
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    def check_database() -> bool:
        """Sync wrapper for database health check."""
        try:
            return asyncio.run(check_database_async())
        except Exception as e:
            logger.error(f"Database health check wrapper failed: {e}")
            return False

    register_health_check(
        CustomHealthCheck(
            name="database",
            component_type=ComponentType.DATABASE,
            check_func=check_database,
            timeout_seconds=5.0,
            critical=True  # Critical component
        )
    )

    # Example: Cache health check
    async def check_cache_async() -> bool:
        """Check cache (Redis) connectivity."""
        try:
            # In production, replace with actual cache check
            # Example: await redis.ping()
            await asyncio.sleep(0.01)  # Simulate check
            return True
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return False

    def check_cache() -> bool:
        """Sync wrapper for cache health check."""
        try:
            return asyncio.run(check_cache_async())
        except Exception as e:
            logger.error(f"Cache health check wrapper failed: {e}")
            return False

    register_health_check(
        CustomHealthCheck(
            name="cache",
            component_type=ComponentType.CACHE,
            check_func=check_cache,
            timeout_seconds=3.0,
            critical=False  # Non-critical
        )
    )

    # Example: External API health check
    async def check_external_api_async() -> bool:
        """Check external API availability."""
        try:
            # In production, replace with actual API check
            # Example:
            # async with httpx.AsyncClient() as client:
            #     response = await client.get("https://api.example.com/health")
            #     return response.status_code == 200
            await asyncio.sleep(0.05)  # Simulate check
            return True
        except Exception as e:
            logger.error(f"External API health check failed: {e}")
            return False

    def check_external_api() -> bool:
        """Sync wrapper for external API health check."""
        try:
            return asyncio.run(check_external_api_async())
        except Exception as e:
            logger.error(f"External API health check wrapper failed: {e}")
            return False

    register_health_check(
        CustomHealthCheck(
            name="external_api",
            component_type=ComponentType.EXTERNAL_API,
            check_func=check_external_api,
            timeout_seconds=5.0,
            critical=True
        )
    )

    logger.info("Health checks registered successfully")

# ============================================================================
# Webhook Configuration
# ============================================================================

if config.ENABLE_WEBHOOKS and config.VERCEL_WEBHOOK_URL:
    logger.info("Configuring webhooks")

    configure_vercel_webhook(
        webhook_url=config.VERCEL_WEBHOOK_URL,
        event_types=[
            WebhookEventType.DEPLOYMENT_STARTED,
            WebhookEventType.DEPLOYMENT_COMPLETED,
            WebhookEventType.DEPLOYMENT_FAILED,
            WebhookEventType.ERROR_OCCURRED,
            WebhookEventType.WARNING_OCCURRED,
            WebhookEventType.HEALTH_DEGRADED,
        ]
    )

    logger.info("Webhooks configured successfully")

# ============================================================================
# Custom Metrics
# ============================================================================

# Register custom business metrics
user_signups_total = registry.register_counter(
    "user_signups_total",
    "Total user signups",
    labels=["source"]
)

active_users_gauge = registry.register_gauge(
    "active_users",
    "Number of active users"
)

api_latency_histogram = registry.register_histogram(
    "api_latency_seconds",
    "API endpoint latency",
    labels=["endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

# ============================================================================
# Business Logic with Observability
# ============================================================================

@observe_tool("user_registration", track_performance=True, log_inputs=True)
@measure_performance("user_registration", threshold_warning_ms=500, threshold_critical_ms=2000)
async def register_user(username: str, email: str, source: str = "web") -> dict:
    """
    Register a new user with full observability.

    This function demonstrates:
    - Tool execution monitoring
    - Performance measurement
    - Custom metrics
    - Logging with context
    """
    logger.info(f"Registering user: {username}")

    try:
        # Simulate user creation
        await asyncio.sleep(0.2)

        # Record custom metric
        user_signups_total.inc(labels={"source": source})

        # Update active users gauge
        active_users_gauge.inc()

        user = {
            "id": "user_123",
            "username": username,
            "email": email,
            "source": source
        }

        logger.info(
            f"User registered successfully: {username}",
            extra_fields={"user_id": user["id"], "source": source}
        )

        return user

    except Exception as e:
        logger.error(f"User registration failed: {e}", exc_info=True)
        record_error("UserRegistrationError", "user_service")

        # Send webhook alert in production
        if config.ENABLE_WEBHOOKS:
            await webhook_manager.send_error_alert(
                error_type="UserRegistrationError",
                error_message=f"Failed to register user {username}: {str(e)}",
                source="user_service",
                metadata={"username": username, "email": email}
            )

        raise


@track_database_operation("select")
@log_operation("get_user_profile")
async def get_user_profile(user_id: str) -> dict:
    """
    Get user profile with database tracking.

    Demonstrates:
    - Database operation tracking
    - Operation logging
    """
    logger.info(f"Fetching user profile: {user_id}")

    # Simulate database query
    await asyncio.sleep(0.05)

    return {
        "id": user_id,
        "username": "john_doe",
        "email": "john@example.com",
        "created_at": "2025-01-01T00:00:00Z"
    }


@observe_tool("search_users", track_performance=True)
async def search_users(query: str, limit: int = 10) -> list[dict]:
    """
    Search users with monitoring.

    Demonstrates:
    - Tool execution monitoring
    - Query parameter logging
    """
    logger.info(f"Searching users: query={query}, limit={limit}")

    # Simulate search
    await asyncio.sleep(0.15)

    return [
        {"id": f"user_{i}", "username": f"user{i}", "relevance": 0.9 - (i * 0.1)}
        for i in range(min(limit, 3))
    ]


# ============================================================================
# API Endpoints
# ============================================================================

@app.post("/api/users/register")
async def api_register_user(username: str, email: str, source: str = "web"):
    """Register a new user."""
    try:
        # Use LogContext to add request-specific context
        with LogContext(user_id=None):  # Will be set after creation
            user = await register_user(username, email, source)
            return JSONResponse(content=user, status_code=201)

    except Exception as e:
        logger.error(f"Registration endpoint failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Registration failed")


@app.get("/api/users/{user_id}")
async def api_get_user(user_id: str):
    """Get user profile."""
    try:
        with LogContext(user_id=user_id):
            profile = await get_user_profile(user_id)

            # Record API latency
            with api_latency_histogram.time(labels={"endpoint": "/api/users/{id}"}):
                return JSONResponse(content=profile)

    except Exception as e:
        logger.error(f"Get user endpoint failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch user")


@app.get("/api/users/search")
async def api_search_users(q: str, limit: int = 10):
    """Search users."""
    try:
        results = await search_users(q, limit)
        return JSONResponse(content={"results": results, "count": len(results)})

    except Exception as e:
        logger.error(f"Search endpoint failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Search failed")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": config.APP_NAME,
        "version": config.APP_VERSION,
        "environment": config.APP_ENVIRONMENT,
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "dashboard": "/api/observability/dashboard",
            "docs": "/docs"
        }
    }


# ============================================================================
# Include Observability Endpoints
# ============================================================================

app.include_router(observability_router)

# ============================================================================
# Application Lifecycle Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Application startup tasks."""
    logger.info(
        "Application starting",
        extra_fields={
            "app_name": config.APP_NAME,
            "version": config.APP_VERSION,
            "environment": config.APP_ENVIRONMENT
        }
    )

    # Send deployment started notification
    if config.ENABLE_WEBHOOKS:
        await webhook_manager.send_deployment_started(
            deployment_id=f"deploy_{config.APP_VERSION}",
            environment=config.APP_ENVIRONMENT,
            metadata={"version": config.APP_VERSION}
        )

    logger.info("Application started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks."""
    logger.info("Application shutting down")

    # Clean up resources
    # Close database connections, etc.

    logger.info("Application shutdown complete")


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    logger.info(
        "Starting server",
        extra_fields={
            "host": "0.0.0.0",
            "port": 8000,
            "environment": config.APP_ENVIRONMENT
        }
    )

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
