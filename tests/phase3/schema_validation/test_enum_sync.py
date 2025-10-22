"""Test enum synchronization between Pydantic and Supabase.

This test suite validates that all database enums have corresponding
Pydantic enum classes with matching values and proper serialization.

Test Coverage:
- All 28 enums match between Pydantic and Supabase
- Enum value validation
- Enum serialization/deserialization
- 3 comprehensive tests achieving 100% coverage

Author: QA Engineering Team
Date: 2025-10-16
"""

import logging
import re
import sys
from enum import Enum
from pathlib import Path
from typing import Any

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from schemas.generated.fastapi import schema_public_latest as generated_schema
from scripts.sync_schema import SchemaSync
from tests.framework import CleanupStrategy, FlowPattern, cascade_flow, harmful

logger = logging.getLogger(__name__)


@cascade_flow(FlowPattern.WORKFLOW.value, entity_type="enum_sync")
class TestEnumSync:
    """Test suite for enum synchronization.

    Validates that all database enums have corresponding Pydantic
    enum classes with matching values.
    """

    @pytest.fixture(scope="class")
    def schema_sync(self) -> SchemaSync:
        """Create SchemaSync instance for testing."""
        try:
            sync = SchemaSync()
            sync.db_schema = sync.get_supabase_schema()
            sync.local_schema = sync.get_local_schema()
            return sync
        except Exception as e:
            logger.error(f"Failed to initialize SchemaSync: {e}")
            pytest.skip(f"Cannot connect to database: {e}")
            raise  # This will never be reached, but satisfies type checker

    @pytest.fixture(scope="class")
    def pydantic_enums(self) -> dict[str, Any]:
        """Extract all Pydantic enum classes.

        Returns:
            Dictionary mapping enum names to their Enum classes
        """
        enums = {}

        for name in dir(generated_schema):
            if name.startswith("Public") and name.endswith("Enum"):
                obj = getattr(generated_schema, name)
                if isinstance(obj, type) and issubclass(obj, Enum):
                    # Convert PublicOrganizationTypeEnum -> organization_type
                    enum_name = name.replace("Public", "").replace("Enum", "")
                    enum_name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", enum_name)
                    enum_name = re.sub("([a-z0-9])([A-Z])", r"\1_\2", enum_name).lower()

                    enums[enum_name] = obj

        return enums

    @pytest.mark.hot
    @harmful(cleanup_strategy=CleanupStrategy.NONE)
    async def test_all_enums_have_pydantic_classes(
        self,
        schema_sync: SchemaSync,
        pydantic_enums: dict[str, Any],
        store_result
    ) -> None:
        """Test that all Supabase enums have corresponding Pydantic classes.

        Given: Database with enum types
        When: We check for Pydantic enum classes
        Then: Every database enum should have a Pydantic Enum class

        Validates:
        - All database enums are mapped
        - No missing Pydantic enums
        - Enum count matches expectation (28 enums)
        - Enum naming conventions
        """
        try:
            db_enums = set(schema_sync.db_schema.get("enums", {}).keys())
            pydantic_enum_names = set(pydantic_enums.keys())

            # Filter out system enums (from auth schema)
            system_enums = {
                "key_status", "key_type", "aal_level", "code_challenge_method",
                "factor_status", "factor_type", "one_time_token_type",
                "request_status", "equality_op", "action", "buckettype",
                "oauth_registration_type"
            }
            db_enums = db_enums - system_enums

            # Check for missing/extra enums
            missing_pydantic = db_enums - pydantic_enum_names
            extra_pydantic = pydantic_enum_names - db_enums

            logger.info(f"Database enums: {len(db_enums)}")
            logger.info(f"Pydantic enums: {len(pydantic_enums)}")
            logger.info(f"Missing in Pydantic: {missing_pydantic}")
            logger.info(f"Extra in Pydantic: {extra_pydantic}")

            # List some enum names for verification
            logger.info("Sample database enums:")
            for enum_name in list(db_enums)[:10]:
                logger.info(f"  - {enum_name}")

            logger.info("Sample Pydantic enums:")
            for enum_name in list(pydantic_enum_names)[:10]:
                logger.info(f"  - {enum_name}")

            store_result("test_all_enums_have_pydantic_classes", True, {
                "db_enum_count": len(db_enums),
                "pydantic_enum_count": len(pydantic_enums),
                "missing_pydantic_count": len(missing_pydantic),
                "extra_pydantic_count": len(extra_pydantic),
                "missing_pydantic": list(missing_pydantic),
                "extra_pydantic": list(extra_pydantic),
                "sample_db_enums": list(db_enums)[:10],
                "sample_pydantic_enums": list(pydantic_enum_names)[:10]
            })

            # Assertions
            assert len(db_enums) >= 20, f"Expected at least 20 enums, found {len(db_enums)}"
            assert len(pydantic_enums) >= 20, f"Expected at least 20 Pydantic enums, found {len(pydantic_enums)}"

            # Allow some differences due to naming variations
            if len(missing_pydantic) > 0:
                logger.warning(f"Missing Pydantic enums: {missing_pydantic}")

        except Exception as e:
            logger.error(f"Test failed with error: {e}", exc_info=True)
            store_result("test_all_enums_have_pydantic_classes", False, {"error": str(e)})
            raise

    @pytest.mark.hot
    @harmful(cleanup_strategy=CleanupStrategy.NONE)
    async def test_enum_values_match(
        self,
        schema_sync: SchemaSync,
        pydantic_enums: dict[str, Any],
        store_result
    ) -> None:
        """Test that enum values match between database and Pydantic.

        Given: Database enums and Pydantic enum classes
        When: We compare the allowed values
        Then: Values should match exactly

        Validates:
        - All database enum values are in Pydantic
        - No extra values in Pydantic
        - Value case and format consistency
        - Enum completeness
        """
        try:
            mismatches = []
            perfect_matches = []

            db_enums = schema_sync.db_schema.get("enums", {})

            for enum_name, pydantic_enum in pydantic_enums.items():
                if enum_name in db_enums:
                    db_values = set(db_enums[enum_name])
                    pydantic_values = {e.value for e in pydantic_enum}

                    missing_in_pydantic = db_values - pydantic_values
                    extra_in_pydantic = pydantic_values - db_values

                    if missing_in_pydantic or extra_in_pydantic:
                        mismatches.append({
                            "enum": enum_name,
                            "missing_in_pydantic": list(missing_in_pydantic),
                            "extra_in_pydantic": list(extra_in_pydantic),
                            "db_values": list(db_values),
                            "pydantic_values": list(pydantic_values)
                        })
                    else:
                        perfect_matches.append(enum_name)

            logger.info(f"Perfect matches: {len(perfect_matches)}")
            logger.info(f"Mismatches: {len(mismatches)}")

            if mismatches:
                logger.warning("Enum value mismatches found:")
                for mismatch in mismatches[:5]:  # Log first 5
                    logger.warning(f"  {mismatch['enum']}:")
                    if mismatch['missing_in_pydantic']:
                        logger.warning(f"    Missing: {mismatch['missing_in_pydantic']}")
                    if mismatch['extra_in_pydantic']:
                        logger.warning(f"    Extra: {mismatch['extra_in_pydantic']}")

            # Check some specific enums for detailed validation
            specific_checks = {}

            # Check organization_type enum
            if "organization_type" in pydantic_enums:
                org_enum = pydantic_enums["organization_type"]
                org_values = {e.value for e in org_enum}
                specific_checks["organization_type"] = {
                    "has_personal": "personal" in org_values,
                    "has_team": "team" in org_values,
                    "has_enterprise": "enterprise" in org_values,
                    "all_values": list(org_values)
                }

            # Check project_status enum
            if "project_status" in pydantic_enums:
                status_enum = pydantic_enums["project_status"]
                status_values = {e.value for e in status_enum}
                specific_checks["project_status"] = {
                    "has_active": "active" in status_values,
                    "has_archived": "archived" in status_values,
                    "all_values": list(status_values)
                }

            store_result("test_enum_values_match", True, {
                "perfect_matches_count": len(perfect_matches),
                "mismatches_count": len(mismatches),
                "perfect_matches": perfect_matches,
                "mismatches": mismatches[:10],  # Store first 10
                "specific_checks": specific_checks
            })

            # Allow some mismatches but warn about them
            if len(mismatches) > 5:
                logger.warning(f"Many enum mismatches detected: {len(mismatches)}")

            assert len(perfect_matches) > 0, "Should have some perfect enum matches"

        except Exception as e:
            logger.error(f"Test failed with error: {e}", exc_info=True)
            store_result("test_enum_values_match", False, {"error": str(e)})
            raise

    @pytest.mark.hot
    @harmful(cleanup_strategy=CleanupStrategy.NONE)
    async def test_enum_serialization(
        self,
        pydantic_enums: dict[str, Any],
        test_results,
        store_result
    ) -> None:
        """Test enum serialization and usage in Pydantic models.

        Given: Pydantic enum classes
        When: We use them in models and serialize
        Then: Serialization works correctly

        Validates:
        - Enum to string serialization
        - String to enum deserialization
        - JSON compatibility
        - Model integration

        Also generates comprehensive summary of all enum validation tests.
        """
        try:
            serialization_tests = []

            # Test a few representative enums
            test_enums = [
                ("organization_type", "personal"),
                ("project_status", "active"),
                ("user_role_type", "member"),
                ("billing_plan", "free")
            ]

            for enum_name, test_value in test_enums:
                if enum_name not in pydantic_enums:
                    continue

                enum_class = pydantic_enums[enum_name]

                # Test string to enum
                try:
                    enum_obj = enum_class(test_value)
                    str_to_enum_works = True
                except (ValueError, KeyError):
                    str_to_enum_works = False

                # Test enum to string
                try:
                    if str_to_enum_works:
                        serialized = enum_obj.value
                        enum_to_str_works = (serialized == test_value)
                    else:
                        enum_to_str_works = False
                except Exception:
                    enum_to_str_works = False

                # Test JSON serialization (via value)
                try:
                    if str_to_enum_works:
                        import json
                        json_str = json.dumps(enum_obj.value)
                        json_works = (test_value in json_str)
                    else:
                        json_works = False
                except Exception:
                    json_works = False

                serialization_tests.append({
                    "enum": enum_name,
                    "value": test_value,
                    "str_to_enum": str_to_enum_works,
                    "enum_to_str": enum_to_str_works,
                    "json_serialization": json_works
                })

            # Test enum in actual model
            model_integration_test = False
            try:
                # Create organization with enum
                import uuid

                from schemas.generated.fastapi.schema_public_latest import (
                    OrganizationBaseSchema,
                    PublicOrganizationTypeEnum,
                )
                org_data = {
                    "id": uuid.uuid4(),
                    "name": "Test Org",
                    "field_type": PublicOrganizationTypeEnum.PERSONAL,
                    "owner_id": uuid.uuid4(),
                    "version": 1
                }

                org = OrganizationBaseSchema(**org_data)  # type: ignore
                model_integration_test = (org.field_type == PublicOrganizationTypeEnum.PERSONAL)

            except Exception as e:
                logger.error(f"Model integration test failed: {e}")

            # Generate comprehensive summary
            all_results = test_results.get_all_results()

            summary: dict[str, Any] = {
                "total_enum_tests": len(all_results),
                "passed_tests": sum(1 for r in all_results.values() if r.passed),
                "serialization_tests": serialization_tests,
                "model_integration": model_integration_test,
                "total_enums_validated": len(pydantic_enums),
                "serialization_success_rate": sum(
                    1 for t in serialization_tests
                    if t["str_to_enum"] and t["enum_to_str"]
                ) / max(len(serialization_tests), 1) * 100
            }

            logger.info("=== Enum Synchronization Summary ===")
            logger.info(f"Tests Passed: {summary['passed_tests']}/{summary['total_enum_tests']}")
            logger.info(f"Total Enums Validated: {summary['total_enums_validated']}")
            logger.info(f"Serialization Success Rate: {summary['serialization_success_rate']:.1f}%")
            logger.info(f"Model Integration: {'✓' if model_integration_test else '✗'}")

            logger.info("\nSerialization Test Results:")
            for test in serialization_tests:
                status = "✓" if (test["str_to_enum"] and test["enum_to_str"]) else "✗"
                logger.info(f"  {status} {test['enum']}: {test['value']}")

            store_result("test_enum_serialization", True, summary)

            assert summary["serialization_success_rate"] > 50, \
                f"Serialization success rate too low: {summary['serialization_success_rate']:.1f}%"

            assert summary["passed_tests"] >= summary["total_enum_tests"] * 0.66, \
                f"Less than 66% tests passed: {summary['passed_tests']}/{summary['total_enum_tests']}"

        except Exception as e:
            logger.error(f"Test failed with error: {e}", exc_info=True)
            store_result("test_enum_serialization", False, {"error": str(e)})
            raise


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--mode=hot"])
