"""Fixtures for extension tests - inherits from unit/tools conftest."""

import pytest
import pytest_asyncio

# Import fixtures from unit/tools conftest for use in extensions
# This allows extension tests to use the same client and helper fixtures
from tests.unit.tools.conftest import *  # noqa: F401, F403
