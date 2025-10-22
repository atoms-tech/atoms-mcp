"""Test mode framework for hot/cold/dry test isolation and execution.

This module provides a comprehensive framework for running tests in different modes:
- HOT: Integration tests with real dependencies (live server, actual database)
- COLD: Unit tests with mocked adapters (no network, fast execution)
- DRY: Fully simulated tests (everything mocked, testing logic only)
- ALL: Run all tests

Key Features:
- TestMode enum with configuration per mode
- TestModeDetector for environment/CLI detection
- ConditionalFixture factory pattern
- Pytest markers for mode-specific tests
- Duration validation (COLD < 2s, DRY < 1s)

Usage:
    @pytest.mark.hot
    async def test_real_server_integration():
        pass  # Uses real dependencies

    @pytest.mark.cold
    async def test_unit_with_mocks():
        pass  # Uses mocked adapters

    @pytest.mark.dry
    async def test_fully_simulated():
        pass  # Uses simulated everything
"""

import logging
import os
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class TestMode(Enum):
    """Test execution modes."""

    HOT = "hot"  # Integration tests with real dependencies
    COLD = "cold"  # Unit tests with mocked adapters
    DRY = "dry"  # Fully simulated tests
    ALL = "all"  # Run all tests


@dataclass
class TestModeConfig:
    """Configuration for test mode execution."""

    mode: TestMode
    use_real_server: bool
    use_real_database: bool
    use_mocks: bool
    use_simulation: bool
    max_duration_seconds: float
    cleanup_after_test: bool
    parallel_execution: bool
    cache_fixtures: bool
    validate_results: bool

    @classmethod
    def for_mode(cls, mode: TestMode) -> "TestModeConfig":
        """Create configuration for a specific mode."""
        configs = {
            TestMode.HOT: TestModeConfig(
                mode=TestMode.HOT,
                use_real_server=True,
                use_real_database=True,
                use_mocks=False,
                use_simulation=False,
                max_duration_seconds=30.0,  # Integration tests can be slower
                cleanup_after_test=True,
                parallel_execution=False,  # Serial execution to avoid conflicts
                cache_fixtures=False,  # Always fresh data
                validate_results=True,
            ),
            TestMode.COLD: TestModeConfig(
                mode=TestMode.COLD,
                use_real_server=False,
                use_real_database=False,
                use_mocks=True,
                use_simulation=False,
                max_duration_seconds=2.0,  # Unit tests must be fast
                cleanup_after_test=True,
                parallel_execution=True,  # Can run in parallel
                cache_fixtures=True,  # Reuse fixtures
                validate_results=True,
            ),
            TestMode.DRY: TestModeConfig(
                mode=TestMode.DRY,
                use_real_server=False,
                use_real_database=False,
                use_mocks=False,
                use_simulation=True,
                max_duration_seconds=1.0,  # Simulated tests must be very fast
                cleanup_after_test=True,
                parallel_execution=True,  # Can run in parallel
                cache_fixtures=True,  # Reuse fixtures
                validate_results=False,  # Skip result validation in dry runs
            ),
        }
        return configs.get(mode, configs[TestMode.HOT])


class TestModeDetector:
    """Detects which test mode to use from environment or CLI."""

    @staticmethod
    def detect_mode() -> TestMode:
        """Detect test mode from environment variables and CLI arguments."""
        # Check environment variable first
        env_mode = os.getenv("TEST_MODE", "").lower()
        if env_mode in ("hot", "cold", "dry", "all"):
            logger.info(f"Test mode from environment: {env_mode}")
            return TestMode[env_mode.upper()]

        # Check for CLI markers (pytest will set these)
        # This is handled by the pytest plugin

        # Default to HOT mode
        return TestMode.HOT

    @staticmethod
    def detect_mode_from_markers(items: list[Any]) -> TestMode:
        """Detect mode from pytest markers in test items."""
        has_hot = any(item.get_closest_marker("hot") for item in items)
        has_cold = any(item.get_closest_marker("cold") for item in items)
        has_dry = any(item.get_closest_marker("dry") for item in items)

        if has_hot:
            return TestMode.HOT
        if has_cold:
            return TestMode.COLD
        if has_dry:
            return TestMode.DRY

        return TestMode.HOT


class ConditionalFixture:
    """Factory for creating conditional fixtures based on test mode."""

    def __init__(self, mode_config: TestModeConfig):
        self.mode_config = mode_config

    @staticmethod
    def create(
        mode_config: TestModeConfig,
        hot_impl: Callable,
        cold_impl: Callable,
        dry_impl: Callable,
        *args,
        **kwargs,
    ) -> Any:
        """Create a fixture implementation based on test mode.

        Args:
            mode_config: Test mode configuration
            hot_impl: Implementation for HOT mode
            cold_impl: Implementation for COLD mode
            dry_impl: Implementation for DRY mode
            *args: Arguments to pass to implementation
            **kwargs: Keyword arguments to pass to implementation

        Returns:
            Result of the appropriate implementation
        """
        if mode_config.mode == TestMode.HOT:
            return hot_impl(*args, **kwargs)
        elif mode_config.mode == TestMode.COLD:
            return cold_impl(*args, **kwargs)
        elif mode_config.mode == TestMode.DRY:
            return dry_impl(*args, **kwargs)
        else:
            # Default to COLD
            return cold_impl(*args, **kwargs)

    @staticmethod
    async def create_async(
        mode_config: TestModeConfig,
        hot_impl: Callable,
        cold_impl: Callable,
        dry_impl: Callable,
        *args,
        **kwargs,
    ) -> Any:
        """Create an async fixture implementation based on test mode.

        Args:
            mode_config: Test mode configuration
            hot_impl: Async implementation for HOT mode
            cold_impl: Async implementation for COLD mode
            dry_impl: Async implementation for DRY mode
            *args: Arguments to pass to implementation
            **kwargs: Keyword arguments to pass to implementation

        Returns:
            Result of the appropriate implementation
        """
        if mode_config.mode == TestMode.HOT:
            return await hot_impl(*args, **kwargs)
        elif mode_config.mode == TestMode.COLD:
            return await cold_impl(*args, **kwargs)
        elif mode_config.mode == TestMode.DRY:
            return await dry_impl(*args, **kwargs)
        else:
            # Default to COLD
            return await cold_impl(*args, **kwargs)


class TestModeValidator:
    """Validates test mode configuration and execution."""

    @staticmethod
    def validate_mode_config(mode_config: TestModeConfig) -> bool:
        """Validate that test mode configuration is consistent."""
        # HOT mode should use real dependencies
        if mode_config.mode == TestMode.HOT:
            if not mode_config.use_real_server or not mode_config.use_real_database:
                logger.warning("HOT mode should use real server and database")
                return False

        # COLD mode should use mocks, not real dependencies
        if mode_config.mode == TestMode.COLD:
            if mode_config.use_real_server or mode_config.use_real_database:
                logger.warning("COLD mode should use mocks, not real dependencies")
                return False
            if not mode_config.use_mocks:
                logger.warning("COLD mode should use mocks")
                return False

        # DRY mode should use simulation only
        if mode_config.mode == TestMode.DRY:
            if mode_config.use_real_server or mode_config.use_real_database or mode_config.use_mocks:
                logger.warning("DRY mode should use simulation only")
                return False
            if not mode_config.use_simulation:
                logger.warning("DRY mode should use simulation")
                return False

        return True

    @staticmethod
    def validate_test_duration(duration: float, mode_config: TestModeConfig) -> bool:
        """Validate that test duration is within mode limits."""
        if duration > mode_config.max_duration_seconds:
            logger.warning(
                f"Test duration {duration:.2f}s exceeds {mode_config.mode.value} mode limit "
                f"{mode_config.max_duration_seconds:.2f}s"
            )
            return False
        return True


class TestModeManager:
    """Manages test mode state during test execution."""

    def __init__(self):
        self.current_mode: TestMode | None = None
        self.current_config: TestModeConfig | None = None
        self.mode_history: list[tuple[TestMode, TestModeConfig]] = []

    def set_mode(self, mode: TestMode) -> TestModeConfig:
        """Set the current test mode."""
        self.current_mode = mode
        self.current_config = TestModeConfig.for_mode(mode)
        self.mode_history.append((mode, self.current_config))
        logger.info(f"Test mode set to: {mode.value}")
        return self.current_config

    def get_current_mode(self) -> TestMode | None:
        """Get the current test mode."""
        return self.current_mode

    def get_current_config(self) -> TestModeConfig | None:
        """Get the current test mode configuration."""
        return self.current_config

    def is_hot_mode(self) -> bool:
        """Check if currently in HOT mode."""
        return self.current_mode == TestMode.HOT

    def is_cold_mode(self) -> bool:
        """Check if currently in COLD mode."""
        return self.current_mode == TestMode.COLD

    def is_dry_mode(self) -> bool:
        """Check if currently in DRY mode."""
        return self.current_mode == TestMode.DRY


# Global mode manager
_mode_manager = TestModeManager()


def get_mode_manager() -> TestModeManager:
    """Get the global test mode manager."""
    return _mode_manager


def set_test_mode(mode: TestMode) -> TestModeConfig:
    """Set the global test mode."""
    return _mode_manager.set_mode(mode)


def get_test_mode() -> TestMode | None:
    """Get the current global test mode."""
    return _mode_manager.get_current_mode()


def get_test_mode_config() -> TestModeConfig | None:
    """Get the current global test mode configuration."""
    return _mode_manager.get_current_config()


__all__ = [
    "TestMode",
    "TestModeConfig",
    "TestModeDetector",
    "ConditionalFixture",
    "TestModeValidator",
    "TestModeManager",
    "get_mode_manager",
    "set_test_mode",
    "get_test_mode",
    "get_test_mode_config",
]
