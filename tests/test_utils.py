"""
Test Utilities

Common utilities for testing.
"""

import time
from typing import Any


class AssertionHelpers:
    """Helper functions for test assertions."""

    @staticmethod
    def assert_response_success(response: dict[str, Any]) -> bool:
        """Assert that a response indicates success.

        Args:
            response: The response to check

        Returns:
            True if response indicates success
        """
        if not isinstance(response, dict):
            return False

        # Check for success field
        if "success" in response:
            return bool(response["success"])

        # Check for error field (absence indicates success)
        if "error" in response:
            return not bool(response["error"])

        return True

    @staticmethod
    def assert_has_required_fields(data: dict[str, Any], required_fields: list[str]) -> bool:
        """Assert that data has all required fields.

        Args:
            data: The data to check
            required_fields: List of required field names

        Returns:
            True if all required fields are present
        """
        return all(field in data for field in required_fields)

    @staticmethod
    def assert_field_type(data: dict[str, Any], field_name: str, expected_type: type) -> bool:
        """Assert that a field has the expected type.

        Args:
            data: The data to check
            field_name: Name of the field to check
            expected_type: Expected type of the field

        Returns:
            True if field has expected type
        """
        if field_name not in data:
            return False
        return isinstance(data[field_name], expected_type)



class PerformanceAnalyzer:
    """Analyzer for test performance metrics."""

    def __init__(self):
        self.metrics: dict[str, list[float]] = {}
        self.start_times: dict[str, float] = {}

    def start_timer(self, operation: str) -> None:
        """Start timing an operation.

        Args:
            operation: Name of the operation to time
        """
        self.start_times[operation] = time.time()

    def end_timer(self, operation: str) -> float:
        """End timing an operation and record the duration.

        Args:
            operation: Name of the operation to time

        Returns:
            Duration in seconds
        """
        if operation not in self.start_times:
            return 0.0

        duration = time.time() - self.start_times[operation]

        if operation not in self.metrics:
            self.metrics[operation] = []

        self.metrics[operation].append(duration)
        del self.start_times[operation]

        return duration

    def get_average_time(self, operation: str) -> float:
        """Get average time for an operation.

        Args:
            operation: Name of the operation

        Returns:
            Average time in seconds
        """
        if operation not in self.metrics or not self.metrics[operation]:
            return 0.0

        return sum(self.metrics[operation]) / len(self.metrics[operation])

    def get_total_time(self, operation: str) -> float:
        """Get total time for an operation.

        Args:
            operation: Name of the operation

        Returns:
            Total time in seconds
        """
        if operation not in self.metrics:
            return 0.0

        return sum(self.metrics[operation])

    def get_metrics_summary(self) -> dict[str, dict[str, float]]:
        """Get summary of all performance metrics.

        Returns:
            Dictionary with metrics summary
        """
        summary = {}
        for operation, times in self.metrics.items():
            if times:
                summary[operation] = {
                    "count": len(times),
                    "total": sum(times),
                    "average": sum(times) / len(times),
                    "min": min(times),
                    "max": max(times)
                }
        return summary

    def reset(self) -> None:
        """Reset all metrics."""
        self.metrics.clear()
        self.start_times.clear()
