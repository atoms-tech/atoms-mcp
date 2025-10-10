"""
Alerting module for observability-kit.

Provides:
- Alert definitions and severity levels
- Alert management and lifecycle
- Alert rules and conditions
- Alert routing and notifications
"""

from .alerts import (
    AlertSeverity,
    Alert,
    AlertState,
)
from .manager import (
    AlertManager,
    get_alert_manager,
)
from .rules import (
    AlertRule,
    AlertCondition,
    ThresholdCondition,
    RateCondition,
    ComponentHealthCondition,
)

__all__ = [
    # Core alert types
    "AlertSeverity",
    "Alert",
    "AlertState",
    # Manager
    "AlertManager",
    "get_alert_manager",
    # Rules and conditions
    "AlertRule",
    "AlertCondition",
    "ThresholdCondition",
    "RateCondition",
    "ComponentHealthCondition",
]
