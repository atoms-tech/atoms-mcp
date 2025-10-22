"""
Basic FastAPI integration example for Atoms MCP Observability.

This example demonstrates:
- Setting up observability middleware
- Registering health checks
- Configuring webhooks
- Using decorators for monitoring
- Exposing observability endpoints

Author: Atoms MCP Platform
"""

import asyncio

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from lib.atoms.observability import (
    ComponentType,
    CustomHealthCheck,
    ErrorTrackingMiddleware,
    LogContext,
    PerformanceTrackingMiddleware,
    # Middleware
    RequestTrackingMiddleware,
    get_logger,
    log_operation,
    measure_performance,
    # Decorators
    observe_tool,
    # Health checks
    register_health_check,
)
from lib.atoms.observability import (
    # Endpoints
    router as observability_router,
)

# Initialize FastAPI app
app = FastAPI(
    title="Atoms MCP API",
    version="1.0.0",
    description="API with comprehensive observability"
)

# Get logger
logger = get_logger(__name__)

# ============================================================================
# Middleware Configuration
# ============================================================================

# Add observability middleware (order matters - add in reverse order)
app.add_middleware(RequestTrackingMiddleware)
app.add_middleware(ErrorTrackingMiddleware)
app.add_middleware(
    PerformanceTrackingMiddleware,
    slow_request_threshold_seconds=1.0,
    very_slow_request_threshold_seconds=5.0
)

# ============================================================================
# Health Check Configuration
# ============================================================================

# Example: Supabase health check
# Uncomment and configure with your Supabase client
# from supabase import create_client
# supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
# register_health_check(SupabaseHealthCheck(supabase, timeout_seconds=5.0))

# Example: Custom Redis health check
async def check_redis_health_async() -> bool:
    """Check Redis connectivity."""
    try:
        # Implement your Redis check here
        # return await redis_client.ping()
        return True  # Placeholder
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return False

def check_redis_health() -> bool:
    """Sync wrapper for Redis health check."""
    import asyncio
    try:
        return asyncio.run(check_redis_health_async())
    except Exception as e:
        logger.error(f"Redis health check wrapper failed: {e}")
        return False

register_health_check(
    CustomHealthCheck(
        name="redis",
        component_type=ComponentType.CACHE,
        check_func=check_redis_health,
        timeout_seconds=3.0,
        critical=False  # Non-critical - won't affect overall health
    )
)

# Example: External API health check
async def check_external_api_async() -> bool:
    """Check external API availability."""
    try:
        # Implement your API check here
        # async with httpx.AsyncClient() as client:
        #     response = await client.get("https://api.example.com/health")
        #     return response.status_code == 200
        return True  # Placeholder
    except Exception as e:
        logger.error(f"External API health check failed: {e}")
        return False

def check_external_api() -> bool:
    """Sync wrapper for external API health check."""
    import asyncio
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
        critical=True  # Critical - affects overall health
    )
)

# ============================================================================
# Webhook Configuration
# ============================================================================

# Configure Vercel webhook for deployment and error notifications
# Uncomment and configure with your webhook URL
# configure_vercel_webhook(
#     webhook_url="https://hooks.vercel.com/your-webhook-id",
#     event_types=[
#         WebhookEventType.DEPLOYMENT_STARTED,
#         WebhookEventType.DEPLOYMENT_COMPLETED,
#         WebhookEventType.DEPLOYMENT_FAILED,
#         WebhookEventType.ERROR_OCCURRED,
#         WebhookEventType.HEALTH_DEGRADED,
#     ]
# )

# ============================================================================
# Business Logic with Observability
# ============================================================================

@observe_tool("create_user", track_performance=True, log_inputs=True)
async def create_user(username: str, email: str) -> dict:
    """
    Create a new user with automatic monitoring.

    The @observe_tool decorator automatically:
    - Records execution metrics
    - Logs input/output
    - Tracks performance
    - Handles errors
    """
    logger.info(f"Creating user: {username}")

    # Simulate database operation
    await asyncio.sleep(0.1)

    user = {
        "id": "user_123",
        "username": username,
        "email": email
    }

    return user


@log_operation("process_payment", log_level="INFO")
@measure_performance("payment_processing", threshold_warning_ms=500)
async def process_payment(amount: float, user_id: str) -> dict:
    """
    Process a payment with logging and performance monitoring.

    The decorators automatically:
    - Log operation start/completion
    - Measure execution time
    - Warn if thresholds exceeded
    """
    logger.info(f"Processing payment of ${amount} for user {user_id}")

    # Simulate payment processing
    await asyncio.sleep(0.3)

    result = {
        "transaction_id": "txn_456",
        "amount": amount,
        "status": "completed"
    }

    return result


# ============================================================================
# API Endpoints
# ============================================================================

@app.post("/api/users")
async def api_create_user(username: str, email: str):
    """Create a new user."""
    try:
        user = await create_user(username, email)
        return JSONResponse(content=user, status_code=201)
    except Exception as e:
        logger.error(f"Failed to create user: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create user")


@app.post("/api/payments")
async def api_process_payment(amount: float, user_id: str):
    """Process a payment."""
    try:
        # Use LogContext to add additional context
        with LogContext(user_id=user_id):
            result = await process_payment(amount, user_id)
            return JSONResponse(content=result, status_code=200)
    except Exception as e:
        logger.error(f"Payment processing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Payment processing failed")


@app.get("/api/users/{user_id}")
async def api_get_user(user_id: str):
    """Get user information."""
    logger.info(f"Fetching user: {user_id}")

    # Simulate database query
    await asyncio.sleep(0.05)

    user = {
        "id": user_id,
        "username": "john_doe",
        "email": "john@example.com"
    }

    return JSONResponse(content=user)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Atoms MCP API with Observability",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "dashboard": "/api/observability/dashboard"
        }
    }


# ============================================================================
# Include Observability Endpoints
# ============================================================================

# This adds all observability endpoints:
# - GET /metrics - Prometheus metrics
# - GET /health - Health check
# - GET /health/live - Liveness probe
# - GET /health/ready - Readiness probe
# - GET /api/observability/dashboard - Dashboard data
# - GET /api/observability/metrics/snapshot - JSON metrics
app.include_router(observability_router)


# ============================================================================
# Application Lifecycle
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Application startup tasks."""
    logger.info("Application starting up")

    # Send deployment started notification
    # Uncomment if webhooks are configured
    # from lib.atoms.observability import webhook_manager
    # await webhook_manager.send_deployment_started(
    #     deployment_id="deploy_123",
    #     environment="production"
    # )


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks."""
    logger.info("Application shutting down")


# ============================================================================
# Run the application
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    logger.info("Starting Atoms MCP API server")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
