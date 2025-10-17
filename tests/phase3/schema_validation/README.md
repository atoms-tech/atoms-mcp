# Phase 3 Schema Validation Test Suite

Comprehensive test suite for validating Pydantic schema synchronization with Supabase database schema.

## Overview

This test suite contains **45 production-ready tests** across 5 test files, achieving 100% coverage of schema validation requirements:

- **12 tests** in `test_pydantic_sync.py` - Pydantic to Supabase table mapping
- **12 tests** in `test_field_types.py` - Field type validation and constraints
- **10 tests** in `test_constraints.py` - Database constraint validation
- **8 tests** in `test_drift_detection.py` - Schema drift detection
- **3 tests** in `test_enum_sync.py` - Enum synchronization

## Test Files

### 1. test_pydantic_sync.py

Validates that all 78 Supabase tables have corresponding Pydantic models with correct field mappings.

**Tests:**
- `test_all_tables_have_pydantic_models` - Ensures all tables are mapped
- `test_field_names_match` - Validates field name consistency (accounting for aliases)
- `test_primary_key_fields` - Checks primary key definitions
- `test_foreign_key_fields` - Validates foreign key types
- `test_timestamp_fields` - Ensures timestamp field types are correct
- `test_model_inheritance_structure` - Validates inheritance from CustomModel
- `test_insert_update_models_exist` - Checks for Insert/Update model variants
- `test_json_fields_properly_typed` - Validates JSONB column typing
- `test_enum_fields_properly_typed` - Ensures enums use proper Enum types
- `test_nullable_fields_properly_optional` - Validates Optional[] type usage
- `test_array_fields_properly_typed` - Checks list[] type usage
- `test_model_completeness_summary` - Generates comprehensive sync status summary

### 2. test_field_types.py

Validates field type mappings and type coercion behavior.

**Tests:**
- `test_uuid_fields_validation` - UUID4 type validation and coercion
- `test_string_fields_validation` - String type enforcement and unicode support
- `test_integer_fields_validation` - Integer type validation and constraints
- `test_boolean_fields_validation` - Boolean type validation and coercion
- `test_datetime_fields_validation` - Datetime parsing and timezone handling
- `test_enum_fields_validation` - Enum value validation
- `test_json_fields_validation` - JSON/JSONB field validation
- `test_array_fields_validation` - Array field type validation
- `test_optional_fields_behavior` - Optional field defaults and behavior
- `test_field_aliases` - Alias functionality (e.g., type -> field_type)
- `test_type_coercion_edge_cases` - Edge case type coercion
- `test_field_type_summary` - Field type validation summary

### 3. test_constraints.py

Validates database constraints are enforced in Pydantic models.

**Tests:**
- `test_not_null_constraints_enforced` - NOT NULL constraint enforcement
- `test_nullable_fields_allow_null` - NULL value handling for optional fields
- `test_unique_constraints_documented` - UNIQUE constraint identification
- `test_check_constraints_identified` - CHECK constraint detection
- `test_default_values_identified` - DEFAULT value identification
- `test_pydantic_field_defaults` - Pydantic field default values
- `test_foreign_key_constraints` - Foreign key constraint identification
- `test_version_field_constraints` - Version field validation
- `test_soft_delete_constraints` - Soft delete field validation
- `test_constraint_validation_summary` - Constraint validation summary

### 4. test_drift_detection.py

Validates schema drift detection between database and Pydantic models.

**Tests:**
- `test_no_drift_baseline` - Baseline drift detection (should be minimal)
- `test_detect_new_table_addition` - Detects new tables in database
- `test_detect_table_removal` - Detects removed tables
- `test_detect_column_addition` - Detects new columns in existing tables
- `test_detect_column_removal` - Detects removed columns
- `test_detect_type_changes` - Detects column type changes via schema hash
- `test_schema_hash_calculation` - Validates hash calculation consistency
- `test_drift_detection_summary` - Comprehensive drift analysis summary

### 5. test_enum_sync.py

Validates enum synchronization between database and Pydantic.

**Tests:**
- `test_all_enums_have_pydantic_classes` - Ensures all 28 database enums have Pydantic classes
- `test_enum_values_match` - Validates enum values match exactly
- `test_enum_serialization` - Tests enum serialization and model integration + generates summary

## Running the Tests

### Run All Schema Validation Tests

```bash
pytest tests/phase3/schema_validation/ -v --mode=hot
```

### Run Specific Test File

```bash
pytest tests/phase3/schema_validation/test_pydantic_sync.py -v --mode=hot
pytest tests/phase3/schema_validation/test_field_types.py -v --mode=hot
pytest tests/phase3/schema_validation/test_constraints.py -v --mode=hot
pytest tests/phase3/schema_validation/test_drift_detection.py -v --mode=hot
pytest tests/phase3/schema_validation/test_enum_sync.py -v --mode=hot
```

### Run Specific Test

```bash
pytest tests/phase3/schema_validation/test_pydantic_sync.py::TestPydanticSync::test_all_tables_have_pydantic_models -v
```

### Run with Different Modes

```bash
# Hot mode (real database connections)
pytest tests/phase3/schema_validation/ -v --mode=hot

# Cold mode (mocked adapters - not applicable for these tests)
pytest tests/phase3/schema_validation/ -v --mode=cold

# Dry mode (full simulation - not applicable for these tests)
pytest tests/phase3/schema_validation/ -v --mode=dry
```

## Test Infrastructure

All tests use the Phase 2 test infrastructure:

### Decorators

- **@cascade_flow** - Automatic test ordering and dependency management
- **@harmful** - Automatic cleanup (though these tests don't create entities)
- **@pytest.mark.hot** - Marks tests for HOT mode execution

### Fixtures

- **schema_sync** - SchemaSync instance with database connection
- **pydantic_models** - All Pydantic BaseSchema models
- **pydantic_enums** - All Pydantic enum classes
- **store_result** - Store test results for cascade flow
- **test_results** - Access results from previous tests

## Coverage Breakdown

### Tables (78 total)
- All tables have Pydantic BaseSchema models
- Field names match (accounting for aliases)
- Primary keys validated
- Foreign keys validated
- Timestamps validated

### Enums (28 total)
- All enums have Pydantic enum classes
- Enum values match database
- Serialization works correctly

### Field Types
- UUID4 validation
- String validation
- Integer validation
- Boolean validation
- Datetime validation
- Enum validation
- JSON/JSONB validation
- Array validation
- Optional field handling
- Type coercion edge cases

### Constraints
- NOT NULL enforcement
- UNIQUE identification
- CHECK constraints
- DEFAULT values
- Foreign keys
- Version fields
- Soft delete fields

### Drift Detection
- New table detection
- Table removal detection
- Column addition detection
- Column removal detection
- Type change detection
- Schema hash validation

## Expected Results

When all tests pass, you should see:

```
=== Schema Synchronization Summary ===
Database Tables: 78
Pydantic Models: 78
Coverage: 100.0%
Tests Passed: 12/12

=== Field Type Validation Summary ===
Tests Passed: 12/12
Categories Tested: 11

=== Constraint Validation Summary ===
Tests Passed: 10/10
Constraint Types: 8

=== Schema Drift Detection Summary ===
Tests Passed: 8/8
Current Drift: 0-5 differences
Remediation Needed: false

=== Enum Synchronization Summary ===
Tests Passed: 3/3
Total Enums Validated: 28
Serialization Success Rate: 100.0%
```

## Troubleshooting

### Database Connection Issues

If you see errors like "Cannot connect to database":

1. Check your `.env` file has correct credentials:
   ```
   DB_URL=postgresql://...
   # or
   SUPABASE_DB_PASSWORD=your_password
   ```

2. Ensure you have network access to Supabase

3. Verify psycopg2 is installed:
   ```bash
   pip install psycopg2-binary
   ```

### Schema Drift Detected

If drift detection tests show differences:

1. Review the drift report in test output
2. Run schema sync to update:
   ```bash
   python scripts/sync_schema.py --regenerate
   ```
3. Re-run tests

### Enum Mismatches

If enum values don't match:

1. Check if database has new enum values
2. Run schema regeneration
3. Verify enum definitions in `schema_public_latest.py`

## Integration with CI/CD

These tests are designed for CI/CD integration:

```yaml
# .github/workflows/schema-validation.yml
name: Schema Validation

on: [push, pull_request]

jobs:
  validate-schema:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          uv sync
      - name: Run schema validation tests
        run: |
          pytest tests/phase3/schema_validation/ -v --mode=hot
        env:
          DB_URL: ${{ secrets.DB_URL }}
```

## Contributing

When adding new tests:

1. Follow the existing pattern (Given-When-Then)
2. Use appropriate decorators (@cascade_flow, @harmful)
3. Store results for summary tests
4. Add comprehensive error logging
5. Update this README

## Author

QA Engineering Team
Date: 2025-10-16

## License

Internal use only - Atoms MCP Project
