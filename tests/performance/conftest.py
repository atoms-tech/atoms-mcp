"""
Performance test configuration and fixtures.
"""

import pytest


@pytest.fixture
def benchmark_config():
    """Benchmark configuration."""
    return {
        "rounds": 100,
        "warmup_rounds": 10,
        "iterations": 1000,
    }

