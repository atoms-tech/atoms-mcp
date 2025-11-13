"""Fixtures for extension tests - inherits from unit/tools conftest."""

import pytest
import pytest_asyncio

# Re-export fixtures from unit/tools conftest for use in extensions
# This allows extension tests to use the same client and helper fixtures

pytest_plugins = ["tests.unit.tools.conftest"]
