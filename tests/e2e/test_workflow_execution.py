"""
Entry point for end-to-end tests.

This file imports and aggregates all e2e test modules to ensure pytest
discovers all tests when running tests from the e2e directory.
"""

# Import all test modules to ensure they're discoverable
# This allows pytest to collect tests from this file without duplication
