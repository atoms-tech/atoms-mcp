"""
Alert management system.

Provides alert lifecycle management, notification routing, and alert history.
"""

import logging
from typing import Any, Callable, Dict, List, Optional

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    httpx = None
    HTTPX_AVAILABLE = False

from datetime import datetime, timezone

from .alerts import Alert, AlertSeverity, AlertState

logger = logging.getLogger(__name__)


class AlertManager:
    """
    Manages alert lifecycle and notifications.

    Features:
    - Alert registration and tracking
    - Alert state management
    - Notification routing
    - Alert filtering and querying
    - Multi-tenant alert isolation

    Example:
        manager = AlertManager()

        # Register an alert
        alert = manager.register_alert(
            name="high_cpu",
            description="CPU usage > 90%",
            severity=AlertSeverity.HIGH,
            condition="cpu_usage > 0.9",
            threshold=0.9,
        )

        # Trigger the alert
        manager.trigger_alert(alert.alert_id, current_value=0.95)

        # Send notifications
        await manager.send_notifications(alert.alert_id)
    """

    def __init__(
        self,
        webhook_url: Optional[str] = None,
        notification_timeout: int = 10,
    ):
        """
        Initialize alert manager.

        Args:
            webhook_url: Optional webhook URL for notifications
            notification_timeout: Timeout for notification requests
        """
        self.webhook_url = webhook_url
        self.notification_timeout = notification_timeout

        # Alert storage
        self.alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []

        # Notification handlers
        self.notification_handlers: Dict[str, Callable] = {}

        # Filtering
        self.alert_filters: List[Callable[[Alert], bool]] = []

    def register_alert(
        self,
        name: str,
        description: str,
        severity: AlertSeverity | str,
        condition: str,
        threshold: float,
        alert_id: Optional[str] = None,
        **kwargs,
    ) -> Alert:
        """
        Register a new alert.

        Args:
            name: Alert name
            description: Alert description
            severity: Alert severity
            condition: Condition description
            threshold: Threshold value
            alert_id: Optional specific alert ID
            **kwargs: Additional alert parameters

        Returns:
            Created Alert instance
        """
        from .alerts import create_alert

        alert = create_alert(
            name=name,
            description=description,
            severity=severity,
            condition=condition,
            threshold=threshold,
            alert_id=alert_id,
            **kwargs,
        )

        self.alerts[alert.alert_id] = alert
        logger.info(f"Registered alert: {name} ({alert.alert_id})")

        return alert

    def get_alert(self, alert_id: str) -> Optional[Alert]:
        """Get alert by ID."""
        return self.alerts.get(alert_id)

    def trigger_alert(
        self,
        alert_id: str,
        current_value: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Trigger an alert.

        Args:
            alert_id: Alert ID to trigger
            current_value: Current metric value
            metadata: Additional metadata

        Returns:
            True if alert was triggered, False otherwise
        """
        alert = self.alerts.get(alert_id)
        if not alert:
            logger.warning(f"Alert not found: {alert_id}")
            return False

        # Check if already active
        if alert.is_active:
            logger.debug(f"Alert already active: {alert_id}")
            return False

        # Trigger the alert
        alert.trigger(current_value)

        if metadata:
            alert.metadata.update(metadata)

        logger.warning(
            f"ALERT TRIGGERED: {alert.name} - {alert.description} "
            f"(severity: {alert.severity.value}, value: {current_value})"
        )

        return True

    def resolve_alert(
        self,
        alert_id: str,
        current_value: Optional[float] = None,
    ) -> bool:
        """
        Resolve an alert.

        Args:
            alert_id: Alert ID to resolve
            current_value: Current metric value

        Returns:
            True if alert was resolved, False otherwise
        """
        alert = self.alerts.get(alert_id)
        if not alert:
            logger.warning(f"Alert not found: {alert_id}")
            return False

        # Check if active
        if not alert.is_active:
            logger.debug(f"Alert not active: {alert_id}")
            return False

        # Resolve the alert
        alert.resolve(current_value)

        # Add to history
        self.alert_history.append(alert)

        logger.info(f"ALERT RESOLVED: {alert.name}")

        return True

    def acknowledge_alert(
        self,
        alert_id: str,
        user: Optional[str] = None,
    ) -> bool:
        """
        Acknowledge an alert.

        Args:
            alert_id: Alert ID to acknowledge
            user: User acknowledging the alert

        Returns:
            True if alert was acknowledged, False otherwise
        """
        alert = self.alerts.get(alert_id)
        if not alert:
            logger.warning(f"Alert not found: {alert_id}")
            return False

        alert.acknowledge(user)
        logger.info(f"Alert acknowledged: {alert.name} by {user or 'unknown'}")

        return True

    def silence_alert(self, alert_id: str) -> bool:
        """
        Silence an alert (suppress notifications).

        Args:
            alert_id: Alert ID to silence

        Returns:
            True if alert was silenced, False otherwise
        """
        alert = self.alerts.get(alert_id)
        if not alert:
            logger.warning(f"Alert not found: {alert_id}")
            return False

        alert.silence()
        logger.info(f"Alert silenced: {alert.name}")

        return True

    def get_active_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        tenant_id: Optional[str] = None,
    ) -> List[Alert]:
        """
        Get active alerts.

        Args:
            severity: Optional severity filter
            tenant_id: Optional tenant filter

        Returns:
            List of active alerts
        """
        alerts = [a for a in self.alerts.values() if a.is_active]

        # Apply filters
        if severity:
            alerts = [a for a in alerts if a.severity == severity]

        if tenant_id:
            alerts = [a for a in alerts if a.tenant_id == tenant_id]

        # Apply custom filters
        for filter_func in self.alert_filters:
            alerts = [a for a in alerts if filter_func(a)]

        return alerts

    def get_alert_history(
        self,
        limit: int = 100,
        severity: Optional[AlertSeverity] = None,
        tenant_id: Optional[str] = None,
    ) -> List[Alert]:
        """
        Get alert history.

        Args:
            limit: Maximum number of alerts to return
            severity: Optional severity filter
            tenant_id: Optional tenant filter

        Returns:
            List of historical alerts
        """
        history = list(self.alert_history)

        # Apply filters
        if severity:
            history = [a for a in history if a.severity == severity]

        if tenant_id:
            history = [a for a in history if a.tenant_id == tenant_id]

        return history[-limit:]

    def add_notification_handler(
        self,
        channel: str,
        handler: Callable[[Alert], Any],
    ) -> None:
        """
        Add a notification handler.

        Args:
            channel: Channel name (email, slack, webhook, etc.)
            handler: Async function to handle notifications
        """
        self.notification_handlers[channel] = handler
        logger.info(f"Added notification handler for channel: {channel}")

    def add_filter(self, filter_func: Callable[[Alert], bool]) -> None:
        """
        Add an alert filter.

        Args:
            filter_func: Function that returns True to include alert
        """
        self.alert_filters.append(filter_func)

    async def send_notifications(
        self,
        alert_id: str,
        force: bool = False,
    ) -> Dict[str, bool]:
        """
        Send notifications for an alert.

        Args:
            alert_id: Alert ID
            force: Force send even if already sent

        Returns:
            Dictionary of channel -> success status
        """
        alert = self.alerts.get(alert_id)
        if not alert:
            logger.warning(f"Alert not found: {alert_id}")
            return {}

        # Check if already sent
        if alert.notification_sent and not force:
            logger.debug(f"Notification already sent for alert: {alert_id}")
            return {}

        # Check if silenced
        if alert.state == AlertState.SILENCED:
            logger.debug(f"Alert is silenced: {alert_id}")
            return {}

        results = {}

        # Send to configured channels
        channels = alert.notification_channels or ["webhook"]

        for channel in channels:
            handler = self.notification_handlers.get(channel)

            if handler:
                try:
                    await handler(alert)
                    results[channel] = True
                except Exception as e:
                    logger.error(f"Failed to send notification via {channel}: {e}")
                    results[channel] = False
            else:
                # Default to webhook if no handler
                if channel == "webhook" and self.webhook_url:
                    results[channel] = await self._send_webhook_notification(alert)
                else:
                    logger.warning(f"No handler for channel: {channel}")
                    results[channel] = False

        # Mark as sent if any succeeded
        if any(results.values()):
            alert.mark_notification_sent()

        return results

    async def _send_webhook_notification(self, alert: Alert) -> bool:
        """Send webhook notification."""
        if not self.webhook_url:
            return False

        if not HTTPX_AVAILABLE:
            logger.warning("httpx not available for webhook notifications")
            return False

        try:
            async with httpx.AsyncClient(timeout=self.notification_timeout) as client:
                payload = {
                    "alert": alert.to_dict(),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

                response = await client.post(self.webhook_url, json=payload)
                response.raise_for_status()

                logger.debug(f"Sent webhook notification for alert: {alert.name}")
                return True

        except Exception as e:
            logger.error(f"Failed to send webhook notification: {e}")
            return False

    async def check_and_notify(
        self,
        alert_id: str,
        current_value: float,
        trigger_if_exceeded: bool = True,
    ) -> bool:
        """
        Check alert condition and send notifications if triggered.

        Args:
            alert_id: Alert ID
            current_value: Current metric value
            trigger_if_exceeded: Trigger if value exceeds threshold

        Returns:
            True if alert was triggered and notified
        """
        alert = self.alerts.get(alert_id)
        if not alert:
            return False

        # Check condition
        should_trigger = (
            current_value > alert.threshold if trigger_if_exceeded
            else current_value < alert.threshold
        )

        if should_trigger and not alert.is_active:
            # Trigger alert
            self.trigger_alert(alert_id, current_value)

            # Send notifications
            await self.send_notifications(alert_id)

            return True

        elif not should_trigger and alert.is_active:
            # Resolve alert
            self.resolve_alert(alert_id, current_value)

        return False


# Global alert manager instance
_alert_manager: Optional[AlertManager] = None


def get_alert_manager() -> AlertManager:
    """Get the global alert manager instance."""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager
