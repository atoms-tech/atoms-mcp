"""
Production-ready webhook notifications for observability.

This module provides webhook integrations for:
- Vercel deployment notifications
- Error/warning alerts
- Health degradation alerts
- Custom event notifications
- Retry logic and failure handling

Author: Atoms MCP Platform
Version: 1.0.0
"""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import aiohttp

from .health import HealthStatus
from .logging import get_logger

logger = get_logger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class WebhookEventType(str, Enum):
    """Types of webhook events."""
    DEPLOYMENT_STARTED = "deployment.started"
    DEPLOYMENT_COMPLETED = "deployment.completed"
    DEPLOYMENT_FAILED = "deployment.failed"
    ERROR_OCCURRED = "error.occurred"
    WARNING_OCCURRED = "warning.occurred"
    HEALTH_DEGRADED = "health.degraded"
    HEALTH_RECOVERED = "health.recovered"
    PERFORMANCE_DEGRADED = "performance.degraded"
    CUSTOM_EVENT = "custom.event"


@dataclass
class WebhookPayload:
    """Webhook notification payload."""
    event_type: WebhookEventType
    severity: AlertSeverity
    title: str
    message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)
    source: str = "atoms-mcp"
    environment: str = "production"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "event_type": self.event_type.value,
            "severity": self.severity.value,
            "title": self.title,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "source": self.source,
            "environment": self.environment
        }


@dataclass
class WebhookConfig:
    """Configuration for a webhook endpoint."""
    url: str
    name: str
    enabled: bool = True
    event_types: list[WebhookEventType] = field(default_factory=list)
    retry_attempts: int = 3
    retry_delay_seconds: float = 1.0
    timeout_seconds: float = 10.0
    headers: dict[str, str] = field(default_factory=dict)

    def should_send_event(self, event_type: WebhookEventType) -> bool:
        """Check if this webhook should receive the event."""
        if not self.enabled:
            return False
        if not self.event_types:  # Empty list means all events
            return True
        return event_type in self.event_types


class WebhookClient:
    """
    Client for sending webhook notifications with retry logic.

    Features:
    - Automatic retries with exponential backoff
    - Timeout handling
    - Error logging
    - Custom headers support
    """

    def __init__(self, config: WebhookConfig):
        self.config = config

    async def send(self, payload: WebhookPayload) -> bool:
        """
        Send webhook notification.

        Args:
            payload: The webhook payload to send

        Returns:
            True if successful, False otherwise
        """
        if not self.config.should_send_event(payload.event_type):
            logger.debug(
                f"Skipping webhook {self.config.name} for event {payload.event_type.value}"
            )
            return False

        # Prepare request
        url = self.config.url
        headers = {
            "Content-Type": "application/json",
            **self.config.headers
        }
        data = json.dumps(payload.to_dict())

        # Attempt sending with retries
        for attempt in range(self.config.retry_attempts):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        url,
                        data=data,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds)
                    ) as response:
                        if response.status >= 200 and response.status < 300:
                            logger.info(
                                f"Webhook sent successfully: {self.config.name}",
                                extra_fields={
                                    "webhook_name": self.config.name,
                                    "event_type": payload.event_type.value,
                                    "status_code": response.status,
                                    "attempt": attempt + 1
                                }
                            )
                            return True
                        else:
                            response_text = await response.text()
                            logger.warning(
                                f"Webhook failed with status {response.status}: {self.config.name}",
                                extra_fields={
                                    "webhook_name": self.config.name,
                                    "event_type": payload.event_type.value,
                                    "status_code": response.status,
                                    "response": response_text,
                                    "attempt": attempt + 1
                                }
                            )

            except TimeoutError:
                logger.warning(
                    f"Webhook timeout: {self.config.name}",
                    extra_fields={
                        "webhook_name": self.config.name,
                        "event_type": payload.event_type.value,
                        "attempt": attempt + 1,
                        "timeout_seconds": self.config.timeout_seconds
                    }
                )

            except Exception as e:
                logger.error(
                    f"Webhook error: {self.config.name}",
                    extra_fields={
                        "webhook_name": self.config.name,
                        "event_type": payload.event_type.value,
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        "attempt": attempt + 1
                    },
                    exc_info=True
                )

            # Wait before retry (exponential backoff)
            if attempt < self.config.retry_attempts - 1:
                delay = self.config.retry_delay_seconds * (2 ** attempt)
                await asyncio.sleep(delay)

        logger.error(
            f"Webhook failed after {self.config.retry_attempts} attempts: {self.config.name}",
            extra_fields={
                "webhook_name": self.config.name,
                "event_type": payload.event_type.value,
                "retry_attempts": self.config.retry_attempts
            }
        )
        return False


class WebhookManager:
    """
    Manager for multiple webhook endpoints.

    Handles routing events to configured webhooks and parallel sending.
    """

    def __init__(self):
        self.webhooks: list[WebhookClient] = []

    def register_webhook(self, config: WebhookConfig) -> None:
        """Register a webhook endpoint."""
        client = WebhookClient(config)
        self.webhooks.append(client)
        logger.info(
            f"Registered webhook: {config.name}",
            extra_fields={
                "webhook_name": config.name,
                "url": config.url,
                "event_types": [et.value for et in config.event_types]
            }
        )

    async def send_notification(self, payload: WebhookPayload) -> dict[str, bool]:
        """
        Send notification to all applicable webhooks.

        Args:
            payload: The webhook payload to send

        Returns:
            Dictionary mapping webhook names to success status
        """
        if not self.webhooks:
            logger.debug("No webhooks registered, skipping notification")
            return {}

        # Send to all webhooks in parallel
        tasks = [
            webhook.send(payload)
            for webhook in self.webhooks
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Build results dict
        results_dict = {}
        for webhook, result in zip(self.webhooks, results):
            if isinstance(result, Exception):
                logger.error(
                    f"Webhook exception: {webhook.config.name}",
                    extra_fields={
                        "webhook_name": webhook.config.name,
                        "error": str(result)
                    }
                )
                results_dict[webhook.config.name] = False
            else:
                results_dict[webhook.config.name] = result

        return results_dict

    async def send_deployment_started(
        self,
        deployment_id: str,
        environment: str,
        metadata: dict[str, Any] | None = None
    ) -> dict[str, bool]:
        """Send deployment started notification."""
        payload = WebhookPayload(
            event_type=WebhookEventType.DEPLOYMENT_STARTED,
            severity=AlertSeverity.INFO,
            title="Deployment Started",
            message=f"Deployment {deployment_id} started in {environment}",
            environment=environment,
            metadata={
                "deployment_id": deployment_id,
                **(metadata or {})
            }
        )
        return await self.send_notification(payload)

    async def send_deployment_completed(
        self,
        deployment_id: str,
        environment: str,
        duration_seconds: float,
        metadata: dict[str, Any] | None = None
    ) -> dict[str, bool]:
        """Send deployment completed notification."""
        payload = WebhookPayload(
            event_type=WebhookEventType.DEPLOYMENT_COMPLETED,
            severity=AlertSeverity.INFO,
            title="Deployment Completed",
            message=f"Deployment {deployment_id} completed successfully in {duration_seconds:.2f}s",
            environment=environment,
            metadata={
                "deployment_id": deployment_id,
                "duration_seconds": duration_seconds,
                **(metadata or {})
            }
        )
        return await self.send_notification(payload)

    async def send_deployment_failed(
        self,
        deployment_id: str,
        environment: str,
        error: str,
        metadata: dict[str, Any] | None = None
    ) -> dict[str, bool]:
        """Send deployment failed notification."""
        payload = WebhookPayload(
            event_type=WebhookEventType.DEPLOYMENT_FAILED,
            severity=AlertSeverity.ERROR,
            title="Deployment Failed",
            message=f"Deployment {deployment_id} failed: {error}",
            environment=environment,
            metadata={
                "deployment_id": deployment_id,
                "error": error,
                **(metadata or {})
            }
        )
        return await self.send_notification(payload)

    async def send_error_alert(
        self,
        error_type: str,
        error_message: str,
        source: str,
        metadata: dict[str, Any] | None = None
    ) -> dict[str, bool]:
        """Send error alert notification."""
        payload = WebhookPayload(
            event_type=WebhookEventType.ERROR_OCCURRED,
            severity=AlertSeverity.ERROR,
            title=f"Error: {error_type}",
            message=error_message,
            metadata={
                "error_type": error_type,
                "source": source,
                **(metadata or {})
            }
        )
        return await self.send_notification(payload)

    async def send_warning_alert(
        self,
        warning_type: str,
        warning_message: str,
        source: str,
        metadata: dict[str, Any] | None = None
    ) -> dict[str, bool]:
        """Send warning alert notification."""
        payload = WebhookPayload(
            event_type=WebhookEventType.WARNING_OCCURRED,
            severity=AlertSeverity.WARNING,
            title=f"Warning: {warning_type}",
            message=warning_message,
            metadata={
                "warning_type": warning_type,
                "source": source,
                **(metadata or {})
            }
        )
        return await self.send_notification(payload)

    async def send_health_degraded(
        self,
        component_name: str,
        health_status: HealthStatus,
        message: str,
        metadata: dict[str, Any] | None = None
    ) -> dict[str, bool]:
        """Send health degradation alert."""
        severity = (
            AlertSeverity.CRITICAL if health_status == HealthStatus.UNHEALTHY
            else AlertSeverity.WARNING
        )

        payload = WebhookPayload(
            event_type=WebhookEventType.HEALTH_DEGRADED,
            severity=severity,
            title=f"Health Degraded: {component_name}",
            message=message,
            metadata={
                "component_name": component_name,
                "health_status": health_status.value,
                **(metadata or {})
            }
        )
        return await self.send_notification(payload)

    async def send_health_recovered(
        self,
        component_name: str,
        message: str,
        metadata: dict[str, Any] | None = None
    ) -> dict[str, bool]:
        """Send health recovery notification."""
        payload = WebhookPayload(
            event_type=WebhookEventType.HEALTH_RECOVERED,
            severity=AlertSeverity.INFO,
            title=f"Health Recovered: {component_name}",
            message=message,
            metadata={
                "component_name": component_name,
                **(metadata or {})
            }
        )
        return await self.send_notification(payload)

    async def send_performance_alert(
        self,
        operation: str,
        duration_ms: float,
        threshold_ms: float,
        metadata: dict[str, Any] | None = None
    ) -> dict[str, bool]:
        """Send performance degradation alert."""
        payload = WebhookPayload(
            event_type=WebhookEventType.PERFORMANCE_DEGRADED,
            severity=AlertSeverity.WARNING,
            title=f"Performance Degradation: {operation}",
            message=f"Operation {operation} took {duration_ms:.2f}ms (threshold: {threshold_ms}ms)",
            metadata={
                "operation": operation,
                "duration_ms": duration_ms,
                "threshold_ms": threshold_ms,
                **(metadata or {})
            }
        )
        return await self.send_notification(payload)

    async def send_custom_event(
        self,
        title: str,
        message: str,
        severity: AlertSeverity = AlertSeverity.INFO,
        metadata: dict[str, Any] | None = None
    ) -> dict[str, bool]:
        """Send custom event notification."""
        payload = WebhookPayload(
            event_type=WebhookEventType.CUSTOM_EVENT,
            severity=severity,
            title=title,
            message=message,
            metadata=metadata or {}
        )
        return await self.send_notification(payload)


# Global webhook manager instance
webhook_manager = WebhookManager()


def configure_vercel_webhook(
    webhook_url: str,
    event_types: list[WebhookEventType] | None = None
) -> None:
    """
    Configure Vercel webhook for notifications.

    Args:
        webhook_url: The Vercel webhook URL
        event_types: List of event types to send (None = all events)
    """
    config = WebhookConfig(
        url=webhook_url,
        name="vercel",
        enabled=True,
        event_types=event_types or [],
        retry_attempts=3,
        retry_delay_seconds=2.0,
        timeout_seconds=10.0
    )
    webhook_manager.register_webhook(config)
    logger.info("Configured Vercel webhook", extra_fields={"url": webhook_url})


def configure_custom_webhook(
    name: str,
    webhook_url: str,
    event_types: list[WebhookEventType] | None = None,
    headers: dict[str, str] | None = None
) -> None:
    """
    Configure a custom webhook endpoint.

    Args:
        name: Webhook name
        webhook_url: The webhook URL
        event_types: List of event types to send (None = all events)
        headers: Custom headers to include
    """
    config = WebhookConfig(
        url=webhook_url,
        name=name,
        enabled=True,
        event_types=event_types or [],
        retry_attempts=3,
        retry_delay_seconds=1.0,
        timeout_seconds=10.0,
        headers=headers or {}
    )
    webhook_manager.register_webhook(config)
    logger.info(f"Configured custom webhook: {name}", extra_fields={"url": webhook_url})
