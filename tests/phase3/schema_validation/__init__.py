"""Phase 3 Schema Validation Test Suite.

This module contains comprehensive tests for validating Pydantic schema
synchronization with Supabase database schema, including:

- Pydantic to Supabase table mapping validation
- Field type validation and constraint checking
- Schema drift detection
- Enum synchronization
- Database constraint validation

All tests use the Phase 2 test infrastructure with:
- @harmful decorator for cleanup
- @cascade_flow for test ordering
- Test modes (hot/cold/dry)
"""

__all__ = [
    "test_pydantic_sync",
    "test_field_types",
    "test_constraints",
    "test_drift_detection",
    "test_enum_sync",
]
