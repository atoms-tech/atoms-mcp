"""Pytest plugin for atoms test mode support.

Integrates test modes with pytest for automatic marker registration,
test filtering, and duration validation.

Usage:
    pytest --mode hot|cold|dry|all --mode-strict --mode-validate
"""

import logging
from typing import Any

import pytest

from .test_modes import TestMode, TestModeConfig, TestModeValidator, set_test_mode

logger = logging.getLogger(__name__)


def pytest_addoption(parser: Any) -> None:
    """Add pytest command-line options for test modes."""
    group = parser.getgroup("atoms test modes")

    group.addoption(
        "--mode",
        action="store",
        default="hot",
        choices=["hot", "cold", "dry", "all"],
        help="Test execution mode (default: hot)",
    )

    group.addoption(
        "--mode-strict",
        action="store_true",
        help="Fail if tests have conflicting mode markers",
    )

    group.addoption(
        "--mode-validate",
        action="store_true",
        help="Validate test mode configuration and duration limits",
    )


def pytest_configure(config: Any) -> None:
    """Register custom markers for test modes."""
    config.addinivalue_line("markers", "hot: marks tests for HOT mode (real dependencies)")
    config.addinivalue_line("markers", "cold: marks tests for COLD mode (mocked adapters)")
    config.addinivalue_line("markers", "dry: marks tests for DRY mode (full simulation)")
    config.addinivalue_line("markers", "mode_strict: marks test with strict mode requirements")


def pytest_sessionstart(session: Any) -> None:
    """Initialize test mode at session start."""
    mode_str = session.config.option.mode.upper()
    mode = TestMode[mode_str] if mode_str != "ALL" else TestMode.HOT

    logger.info(f"Starting test session in {mode.value} mode")
    set_test_mode(mode)

    # Store mode in config for access in fixtures
    session.config._atoms_mode = mode
    session.config._atoms_mode_config = TestModeConfig.for_mode(mode)


def pytest_collection_modifyitems(session: Any, config: Any, items: list[Any]) -> None:
    """Filter tests based on mode and validate configuration."""
    mode = config._atoms_mode
    mode_config = config._atoms_mode_config
    strict_mode = config.option.mode_strict
    validate_mode = config.option.mode_validate

    logger.info(f"Filtering tests for {mode.value} mode (strict={strict_mode}, validate={validate_mode})")

    items_to_remove = []

    for item in items:
        # Check mode markers
        has_hot = item.get_closest_marker("hot") is not None
        has_cold = item.get_closest_marker("cold") is not None
        has_dry = item.get_closest_marker("dry") is not None

        # Validate marker consistency
        marker_count = sum([has_hot, has_cold, has_dry])
        if marker_count > 1:
            if strict_mode:
                raise ValueError(f"Test {item.name} has conflicting mode markers")
            else:
                logger.warning(f"Test {item.name} has multiple mode markers, using first one")

        # Filter based on mode
        if mode == TestMode.ALL:
            # Run all tests regardless of markers
            continue
        elif mode == TestMode.HOT:
            # HOT mode: run tests marked as hot, or unmarked tests (default to hot)
            if has_cold or has_dry:
                items_to_remove.append(item)
        elif mode == TestMode.COLD:
            # COLD mode: run tests marked as cold, or unmarked tests (default to cold)
            if has_hot or has_dry:
                items_to_remove.append(item)
        elif mode == TestMode.DRY:
            # DRY mode: run tests marked as dry
            if has_hot or has_cold:
                items_to_remove.append(item)

        # Validate mode configuration
        if validate_mode:
            if not TestModeValidator.validate_mode_config(mode_config):
                logger.warning(f"Test mode configuration validation failed for {item.name}")

    # Remove filtered items
    for item in items_to_remove:
        logger.debug(f"Filtering out test {item.name} (not applicable to {mode.value} mode)")
        items.remove(item)

    logger.info(f"Running {len(items)} tests in {mode.value} mode")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item: Any, call: Any) -> Any:
    """Hook to capture and validate test duration."""
    outcome = yield
    report = outcome.get_result()

    if report.when == "call":
        # Get test mode config
        mode_config = item.config._atoms_mode_config

        # Validate duration
        if hasattr(report, "duration") and mode_config:
            if not TestModeValidator.validate_test_duration(report.duration, mode_config):
                if item.config.option.mode_validate:
                    logger.warning(
                        f"Test {item.name} exceeded duration limit for {mode_config.mode.value} mode: "
                        f"{report.duration:.2f}s > {mode_config.max_duration_seconds:.2f}s"
                    )


def pytest_runtest_setup(item: Any) -> None:
    """Setup for each test - inject mode config."""
    mode_config = item.config._atoms_mode_config
    item._atoms_mode_config = mode_config


@pytest.fixture(scope="session")
def atoms_mode_config(request: Any) -> TestModeConfig:
    """Provide test mode configuration to tests."""
    return request.config._atoms_mode_config


@pytest.fixture
def atoms_test_mode(request: Any) -> TestMode:
    """Provide current test mode to tests."""
    return request.config._atoms_mode


# Conditionally register hot, cold, dry markers
def pytest_generate_tests(metafunc: Any) -> None:
    """Generate test variants based on mode markers."""
    # This hook can be used to parametrize tests based on mode
    # Currently just used for validation
    pass


__all__ = [
    "pytest_addoption",
    "pytest_configure",
    "pytest_sessionstart",
    "pytest_collection_modifyitems",
    "pytest_runtest_makereport",
    "pytest_runtest_setup",
    "pytest_generate_tests",
    "atoms_mode_config",
    "atoms_test_mode",
]
