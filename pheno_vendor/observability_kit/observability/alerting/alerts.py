"""
Alert definitions and types.

Provides core alert data structures and severity levels.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional


class AlertSeverity(str, Enum):
    """Alert severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertState(str, Enum):
    """Alert state."""

    ACTIVE = "active"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"
    SILENCED = "silenced"


@dataclass
class Alert:
    """
    Alert definition and state.

    Represents an alert condition that has been triggered
    or is being monitored.

    Example:
        alert = Alert(
            alert_id="alert-123",
            name="high_error_rate",
            description="Error rate exceeded 5%",
            severity=AlertSeverity.HIGH,
            condition="error_rate > 0.05",
            threshold=0.05,
            current_value=0.12,
        )
    """

    # Identity
    alert_id: str
    name: str
    description: str

    # Severity and condition
    severity: AlertSeverity
    condition: str  # Human-readable condition description
    threshold: float

    # State
    state: AlertState = AlertState.ACTIVE
    triggered_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None

    # Current values
    current_value: Optional[float] = None
    previous_value: Optional[float] = None

    # Notification tracking
    notification_sent: bool = False
    notification_count: int = 0
    last_notification_at: Optional[datetime] = None

    # Additional data
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: Dict[str, str] = field(default_factory=dict)
    tenant_id: Optional[str] = None  # For multi-tenant support

    # Routing
    notification_channels: list[str] = field(default_factory=list)
    assigned_to: Optional[str] = None

    def __post_init__(self):
        """Set defaults after initialization."""
        if not self.triggered_at and self.state == AlertState.ACTIVE:
            self.triggered_at = datetime.now(timezone.utc)

    @property
    def is_active(self) -> bool:
        """Check if alert is active."""
        return self.state == AlertState.ACTIVE

    @property
    def is_resolved(self) -> bool:
        """Check if alert is resolved."""
        return self.state == AlertState.RESOLVED

    @property
    def is_acknowledged(self) -> bool:
        """Check if alert has been acknowledged."""
        return self.state == AlertState.ACKNOWLEDGED

    @property
    def duration_seconds(self) -> Optional[float]:
        """Get alert duration in seconds."""
        if not self.triggered_at:
            return None

        end_time = self.resolved_at or datetime.now(timezone.utc)
        return (end_time - self.triggered_at).total_seconds()

    def trigger(self, current_value: Optional[float] = None) -> None:
        """
        Trigger the alert.

        Args:
            current_value: Current metric value that triggered the alert
        """
        self.state = AlertState.ACTIVE
        self.triggered_at = datetime.now(timezone.utc)
        self.resolved_at = None

        if current_value is not None:
            self.previous_value = self.current_value
            self.current_value = current_value

    def resolve(self, current_value: Optional[float] = None) -> None:
        """
        Resolve the alert.

        Args:
            current_value: Current metric value when resolved
        """
        self.state = AlertState.RESOLVED
        self.resolved_at = datetime.now(timezone.utc)

        if current_value is not None:
            self.previous_value = self.current_value
            self.current_value = current_value

    def acknowledge(self, user: Optional[str] = None) -> None:
        """
        Acknowledge the alert.

        Args:
            user: User who acknowledged the alert
        """
        self.state = AlertState.ACKNOWLEDGED
        self.acknowledged_at = datetime.now(timezone.utc)
        if user:
            self.assigned_to = user

    def silence(self) -> None:
        """Silence the alert (suppress notifications)."""
        self.state = AlertState.SILENCED

    def mark_notification_sent(self) -> None:
        """Mark that a notification has been sent."""
        self.notification_sent = True
        self.notification_count += 1
        self.last_notification_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary."""
        return {
            "alert_id": self.alert_id,
            "name": self.name,
            "description": self.description,
            "severity": self.severity.value,
            "condition": self.condition,
            "threshold": self.threshold,
            "state": self.state.value,
            "triggered_at": self.triggered_at.isoformat() if self.triggered_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "current_value": self.current_value,
            "previous_value": self.previous_value,
            "duration_seconds": self.duration_seconds,
            "notification_sent": self.notification_sent,
            "notification_count": self.notification_count,
            "last_notification_at": self.last_notification_at.isoformat() if self.last_notification_at else None,
            "metadata": self.metadata,
            "tags": self.tags,
            "tenant_id": self.tenant_id,
            "notification_channels": self.notification_channels,
            "assigned_to": self.assigned_to,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Alert":
        """Create alert from dictionary."""
        # Parse datetime fields
        for field_name in ["triggered_at", "resolved_at", "acknowledged_at", "last_notification_at"]:
            if data.get(field_name):
                data[field_name] = datetime.fromisoformat(data[field_name])

        # Parse enums
        if "severity" in data:
            data["severity"] = AlertSeverity(data["severity"])
        if "state" in data:
            data["state"] = AlertState(data["state"])

        return cls(**data)


def create_alert(
    name: str,
    description: str,
    severity: AlertSeverity | str,
    condition: str,
    threshold: float,
    **kwargs,
) -> Alert:
    """
    Create a new alert.

    Args:
        name: Alert name
        description: Alert description
        severity: Alert severity (CRITICAL, HIGH, MEDIUM, LOW, INFO)
        condition: Condition description
        threshold: Threshold value
        **kwargs: Additional alert fields

    Returns:
        New Alert instance
    """
    # Convert string severity to enum
    if isinstance(severity, str):
        severity = AlertSeverity(severity.lower())

    return Alert(
        alert_id=kwargs.pop("alert_id", str(uuid.uuid4())),
        name=name,
        description=description,
        severity=severity,
        condition=condition,
        threshold=threshold,
        **kwargs,
    )
