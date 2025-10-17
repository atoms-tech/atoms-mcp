"""Phase 3 database migration tests.

This package provides comprehensive testing for the database migration system including:
- Migration runner functionality
- Rollback mechanisms
- Version tracking and management
- Idempotency guarantees

All tests support both HOT (real database) and COLD (mocked) modes.
"""

__all__ = [
    "test_migration_runner",
    "test_rollback",
    "test_versioning",
    "test_idempotency",
]
