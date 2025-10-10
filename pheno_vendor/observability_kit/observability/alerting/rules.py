"""
Alert rules and conditions.

Provides reusable alert conditions and rule definitions.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from .alerts import Alert, AlertSeverity, create_alert

logger = logging.getLogger(__name__)


class AlertCondition(ABC):
    """
    Base class for alert conditions.

    Alert conditions evaluate metrics/state and determine
    if an alert should be triggered.
    """

    @abstractmethod
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """
        Evaluate the condition.

        Args:
            context: Context dictionary with metrics/state

        Returns:
            True if condition is met (alert should trigger)
        """
        pass

    @abstractmethod
    def get_description(self) -> str:
        """Get human-readable condition description."""
        pass


class ThresholdCondition(AlertCondition):
    """
    Simple threshold-based condition.

    Triggers when a metric exceeds or falls below a threshold.

    Example:
        condition = ThresholdCondition(
            metric_name="cpu_usage",
            threshold=0.9,
            operator=">"
        )
    """

    def __init__(
        self,
        metric_name: str,
        threshold: float,
        operator: str = ">",
    ):
        """
        Initialize threshold condition.

        Args:
            metric_name: Name of metric to check
            threshold: Threshold value
            operator: Comparison operator (>, <, >=, <=, ==, !=)
        """
        self.metric_name = metric_name
        self.threshold = threshold
        self.operator = operator

        # Map operators to functions
        self.operators = {
            ">": lambda a, b: a > b,
            "<": lambda a, b: a < b,
            ">=": lambda a, b: a >= b,
            "<=": lambda a, b: a <= b,
            "==": lambda a, b: a == b,
            "!=": lambda a, b: a != b,
        }

    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evaluate threshold condition."""
        value = context.get(self.metric_name)

        if value is None:
            logger.warning(f"Metric not found in context: {self.metric_name}")
            return False

        try:
            op_func = self.operators.get(self.operator)
            if not op_func:
                logger.error(f"Invalid operator: {self.operator}")
                return False

            return op_func(float(value), self.threshold)

        except (ValueError, TypeError) as e:
            logger.error(f"Error evaluating threshold condition: {e}")
            return False

    def get_description(self) -> str:
        """Get condition description."""
        return f"{self.metric_name} {self.operator} {self.threshold}"


class RateCondition(AlertCondition):
    """
    Rate-based condition.

    Triggers when a rate (e.g., error rate, request rate) exceeds threshold.

    Example:
        condition = RateCondition(
            numerator_metric="errors",
            denominator_metric="total_requests",
            threshold=0.05,  # 5% error rate
        )
    """

    def __init__(
        self,
        numerator_metric: str,
        denominator_metric: str,
        threshold: float,
        min_denominator: float = 1.0,
    ):
        """
        Initialize rate condition.

        Args:
            numerator_metric: Numerator metric (e.g., errors)
            denominator_metric: Denominator metric (e.g., total requests)
            threshold: Rate threshold (0.0 to 1.0)
            min_denominator: Minimum denominator value to consider
        """
        self.numerator_metric = numerator_metric
        self.denominator_metric = denominator_metric
        self.threshold = threshold
        self.min_denominator = min_denominator

    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evaluate rate condition."""
        numerator = context.get(self.numerator_metric, 0)
        denominator = context.get(self.denominator_metric, 0)

        if denominator < self.min_denominator:
            logger.debug(
                f"Denominator below minimum: {denominator} < {self.min_denominator}"
            )
            return False

        try:
            rate = float(numerator) / float(denominator)
            return rate > self.threshold

        except (ValueError, TypeError, ZeroDivisionError) as e:
            logger.error(f"Error evaluating rate condition: {e}")
            return False

    def get_description(self) -> str:
        """Get condition description."""
        return (
            f"{self.numerator_metric}/{self.denominator_metric} > {self.threshold}"
        )


class ComponentHealthCondition(AlertCondition):
    """
    Component health-based condition.

    Triggers when a component's health status matches criteria.

    Example:
        condition = ComponentHealthCondition(
            component_name="database",
            unhealthy_statuses=["critical", "unavailable"]
        )
    """

    def __init__(
        self,
        component_name: str,
        unhealthy_statuses: List[str],
    ):
        """
        Initialize component health condition.

        Args:
            component_name: Name of component to check
            unhealthy_statuses: List of statuses considered unhealthy
        """
        self.component_name = component_name
        self.unhealthy_statuses = [s.lower() for s in unhealthy_statuses]

    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evaluate component health condition."""
        components = context.get("components", {})
        component = components.get(self.component_name, {})

        if not component:
            logger.warning(f"Component not found: {self.component_name}")
            return False

        status = component.get("status", "unknown").lower()
        return status in self.unhealthy_statuses

    def get_description(self) -> str:
        """Get condition description."""
        return (
            f"{self.component_name} status in {self.unhealthy_statuses}"
        )


class CompositeCondition(AlertCondition):
    """
    Composite condition combining multiple conditions.

    Supports AND/OR logic.

    Example:
        condition = CompositeCondition(
            conditions=[
                ThresholdCondition("cpu_usage", 0.9, ">"),
                ThresholdCondition("memory_usage", 0.9, ">"),
            ],
            logic="AND"
        )
    """

    def __init__(
        self,
        conditions: List[AlertCondition],
        logic: str = "AND",
    ):
        """
        Initialize composite condition.

        Args:
            conditions: List of conditions to combine
            logic: Logic operator ("AND" or "OR")
        """
        self.conditions = conditions
        self.logic = logic.upper()

        if self.logic not in ["AND", "OR"]:
            raise ValueError(f"Invalid logic operator: {logic}")

    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evaluate composite condition."""
        if not self.conditions:
            return False

        results = [c.evaluate(context) for c in self.conditions]

        if self.logic == "AND":
            return all(results)
        else:  # OR
            return any(results)

    def get_description(self) -> str:
        """Get condition description."""
        descriptions = [c.get_description() for c in self.conditions]
        return f" {self.logic} ".join(f"({d})" for d in descriptions)


@dataclass
class AlertRule:
    """
    Complete alert rule definition.

    Combines condition, alert metadata, and evaluation logic.

    Example:
        rule = AlertRule(
            name="high_cpu_usage",
            description="CPU usage exceeds 90%",
            severity=AlertSeverity.HIGH,
            condition=ThresholdCondition("cpu_usage", 0.9, ">"),
            threshold=0.9,
        )
    """

    name: str
    description: str
    severity: AlertSeverity
    condition: AlertCondition
    threshold: float

    # Optional metadata
    tags: Dict[str, str] = None
    notification_channels: List[str] = None
    cooldown_seconds: int = 300  # Prevent alert spam

    # Evaluation tracking
    _last_triggered: Optional[float] = None
    _evaluation_count: int = 0

    def __post_init__(self):
        """Initialize defaults."""
        if self.tags is None:
            self.tags = {}
        if self.notification_channels is None:
            self.notification_channels = []

    def evaluate(self, context: Dict[str, Any]) -> bool:
        """
        Evaluate the alert rule.

        Args:
            context: Context dictionary with metrics/state

        Returns:
            True if alert should be triggered
        """
        self._evaluation_count += 1
        return self.condition.evaluate(context)

    def create_alert(self, **kwargs) -> Alert:
        """
        Create an alert instance from this rule.

        Args:
            **kwargs: Additional alert parameters

        Returns:
            Alert instance
        """
        return create_alert(
            name=self.name,
            description=self.description,
            severity=self.severity,
            condition=self.condition.get_description(),
            threshold=self.threshold,
            tags=self.tags,
            notification_channels=self.notification_channels,
            **kwargs,
        )

    def should_cooldown(self, current_time: float) -> bool:
        """
        Check if alert is in cooldown period.

        Args:
            current_time: Current timestamp

        Returns:
            True if in cooldown
        """
        if self._last_triggered is None:
            return False

        return (current_time - self._last_triggered) < self.cooldown_seconds

    def mark_triggered(self, timestamp: float) -> None:
        """Mark rule as triggered at timestamp."""
        self._last_triggered = timestamp


# Predefined common rules
def create_high_error_rate_rule(threshold: float = 0.05) -> AlertRule:
    """Create a high error rate alert rule."""
    return AlertRule(
        name="high_error_rate",
        description=f"Error rate exceeds {threshold * 100}%",
        severity=AlertSeverity.HIGH,
        condition=RateCondition(
            numerator_metric="errors",
            denominator_metric="total_requests",
            threshold=threshold,
        ),
        threshold=threshold,
        tags={"type": "error_rate"},
    )


def create_high_resource_usage_rule(
    resource: str,
    threshold: float = 0.9,
) -> AlertRule:
    """Create a high resource usage alert rule."""
    return AlertRule(
        name=f"high_{resource}_usage",
        description=f"{resource.upper()} usage exceeds {threshold * 100}%",
        severity=AlertSeverity.HIGH,
        condition=ThresholdCondition(
            metric_name=f"{resource}_usage",
            threshold=threshold,
            operator=">",
        ),
        threshold=threshold,
        tags={"type": "resource_usage", "resource": resource},
    )


def create_component_down_rule(component_name: str) -> AlertRule:
    """Create a component down alert rule."""
    return AlertRule(
        name=f"{component_name}_down",
        description=f"{component_name} is unavailable",
        severity=AlertSeverity.CRITICAL,
        condition=ComponentHealthCondition(
            component_name=component_name,
            unhealthy_statuses=["critical", "unavailable"],
        ),
        threshold=1.0,
        tags={"type": "component_health", "component": component_name},
    )
