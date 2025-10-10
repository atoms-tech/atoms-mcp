#!/usr/bin/env python3
"""
Comprehensive direct test of relationship_tool operations.
Tests all operations by directly calling the relationship_operation function.

This bypasses the MCP server and tests the tool logic directly.
"""

import os
import sys
import json
import uuid
import asyncio
from typing import Any, Dict, Optional
from datetime import datetime
from unittest.mock import AsyncMock, patch

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.relationship import relationship_operation

# Test configuration
TEST_USER_ID = "test-user-" + str(uuid.uuid4())
TEST_ORG_ID = str(uuid.uuid4())
TEST_PROJECT_ID = str(uuid.uuid4())

# Test results storage
test_results = []


class TestResult:
    """Store test operation results."""

    def __init__(
        self,
        operation: str,
        params: Dict[str, Any],
        success: bool,
        response: Dict[str, Any],
        error: Optional[str] = None,
    ):
        self.operation = operation
        self.params = params
        self.success = success
        self.response = response
        self.error = error
        self.timestamp = datetime.now().isoformat()

    def to_dict(self):
        return {
            "operation": self.operation,
            "parameters": self.params,
            "success": self.success,
            "response_data": self.response,
            "error": self.error,
            "timestamp": self.timestamp,
        }


def print_section(title: str, char: str = "="):
    """Print a section header."""
    print()
    print(char * 80)
    print(title)
    print(char * 80)
    print()


def print_subsection(title: str):
    """Print a subsection header."""
    print()
    print(title)
    print("-" * 80)


async def main():
    """Execute all relationship tool tests."""
    print_section("ATOMS MCP RELATIONSHIP_TOOL COMPREHENSIVE TEST - DIRECT MODE")

    # Mock authentication token
    mock_auth_token = "mock-token-" + str(uuid.uuid4())

    # Test entity IDs
    test_requirement_id = str(uuid.uuid4())
    test_test_id = str(uuid.uuid4())
    created_relationship_id = None

    # ========================================================================
    # TEST 1: List relationships (empty state)
    # ========================================================================
    print_subsection("TEST 1: List relationships (empty state)")

    list_params = {
        "auth_token": mock_auth_token,
        "operation": "list",
        "relationship_type": "requirement_test",
        "source": {"type": "requirement", "id": test_requirement_id},
        "limit": 10,
        "offset": 0,
    }

    print("Operation: list")
    print(f"Parameters: {json.dumps({k: v for k, v in list_params.items() if k != 'auth_token'}, indent=2)}")

    # Mock the database calls
    with patch("tools.relationship.RelationshipManager._validate_auth", new_callable=AsyncMock) as mock_auth, \
         patch("tools.relationship.RelationshipManager._get_user_id", return_value=TEST_USER_ID), \
         patch("tools.relationship.RelationshipManager._db_query", new_callable=AsyncMock) as mock_query:

        mock_auth.return_value = None
        mock_query.return_value = []  # Empty list initially

        try:
            result = await relationship_operation(**list_params)

            if result.get("success"):
                print("✅ List operation successful (empty state)")
                print(f"Response: {json.dumps(result, indent=2)}")
                test_results.append(
                    TestResult("list_empty", list_params, True, result)
                )
            else:
                print(f"❌ List operation failed: {result.get('error')}")
                test_results.append(
                    TestResult("list_empty", list_params, False, result, result.get("error"))
                )
        except Exception as e:
            print(f"❌ Exception during list operation: {e}")
            test_results.append(
                TestResult("list_empty", list_params, False, {}, str(e))
            )

    # ========================================================================
    # TEST 2: Create a relationship (link)
    # ========================================================================
    print_subsection("TEST 2: Create a relationship (link)")

    link_params = {
        "auth_token": mock_auth_token,
        "operation": "link",
        "relationship_type": "requirement_test",
        "source": {"type": "requirement", "id": test_requirement_id},
        "target": {"type": "test", "id": test_test_id},
        "metadata": {
            "relationship_type": "tests",
            "coverage_level": "full",
            "priority": "high",
        },
    }

    print("Operation: link")
    print(f"Parameters: {json.dumps({k: v for k, v in link_params.items() if k != 'auth_token'}, indent=2)}")

    with patch("tools.relationship.RelationshipManager._validate_auth", new_callable=AsyncMock) as mock_auth, \
         patch("tools.relationship.RelationshipManager._get_user_id", return_value=TEST_USER_ID), \
         patch("tools.relationship.RelationshipManager._db_insert", new_callable=AsyncMock) as mock_insert:

        mock_auth.return_value = None
        created_relationship_id = str(uuid.uuid4())
        mock_insert.return_value = {
            "id": created_relationship_id,
            "requirement_id": test_requirement_id,
            "test_id": test_test_id,
            "relationship_type": "tests",
            "coverage_level": "full",
            "priority": "high",
            "created_at": datetime.now().isoformat(),
            "created_by": TEST_USER_ID,
        }

        try:
            result = await relationship_operation(**link_params)

            if result.get("success"):
                print("✅ Link operation successful")
                print(f"Relationship ID: {result.get('data', {}).get('id')}")
                print(f"Response: {json.dumps(result, indent=2)}")
                test_results.append(TestResult("link_create", link_params, True, result))
            else:
                print(f"❌ Link operation failed: {result.get('error')}")
                test_results.append(
                    TestResult("link_create", link_params, False, result, result.get("error"))
                )
        except Exception as e:
            print(f"❌ Exception during link operation: {e}")
            test_results.append(TestResult("link_create", link_params, False, {}, str(e)))

    # ========================================================================
    # TEST 3: Get the created relationship (check)
    # ========================================================================
    print_subsection("TEST 3: Get the created relationship (check)")

    check_params = {
        "auth_token": mock_auth_token,
        "operation": "check",
        "relationship_type": "requirement_test",
        "source": {"type": "requirement", "id": test_requirement_id},
        "target": {"type": "test", "id": test_test_id},
    }

    print("Operation: check")
    print(f"Parameters: {json.dumps({k: v for k, v in check_params.items() if k != 'auth_token'}, indent=2)}")

    with patch("tools.relationship.RelationshipManager._validate_auth", new_callable=AsyncMock) as mock_auth, \
         patch("tools.relationship.RelationshipManager._get_user_id", return_value=TEST_USER_ID), \
         patch("tools.relationship.RelationshipManager._db_query", new_callable=AsyncMock) as mock_query:

        mock_auth.return_value = None
        mock_query.return_value = [
            {
                "id": created_relationship_id,
                "requirement_id": test_requirement_id,
                "test_id": test_test_id,
                "relationship_type": "tests",
                "coverage_level": "full",
                "priority": "high",
                "created_at": datetime.now().isoformat(),
            }
        ]

        try:
            result = await relationship_operation(**check_params)

            if result.get("exists"):
                print("✅ Check operation successful - relationship exists")
                print(f"Response: {json.dumps(result, indent=2)}")
                test_results.append(TestResult("check_exists", check_params, True, result))
            else:
                print("❌ Check operation failed or relationship not found")
                test_results.append(
                    TestResult("check_exists", check_params, False, result, "Relationship not found")
                )
        except Exception as e:
            print(f"❌ Exception during check operation: {e}")
            test_results.append(TestResult("check_exists", check_params, False, {}, str(e)))

    # ========================================================================
    # TEST 4: Update the relationship
    # ========================================================================
    print_subsection("TEST 4: Update the relationship")

    update_params = {
        "auth_token": mock_auth_token,
        "operation": "update",
        "relationship_type": "requirement_test",
        "source": {"type": "requirement", "id": test_requirement_id},
        "target": {"type": "test", "id": test_test_id},
        "metadata": {
            "coverage_level": "partial",
            "priority": "medium",
            "notes": "Updated via comprehensive test",
        },
    }

    print("Operation: update")
    print(f"Parameters: {json.dumps({k: v for k, v in update_params.items() if k != 'auth_token'}, indent=2)}")

    with patch("tools.relationship.RelationshipManager._validate_auth", new_callable=AsyncMock) as mock_auth, \
         patch("tools.relationship.RelationshipManager._get_user_id", return_value=TEST_USER_ID), \
         patch("tools.relationship.RelationshipManager._db_update", new_callable=AsyncMock) as mock_update:

        mock_auth.return_value = None
        mock_update.return_value = {
            "id": created_relationship_id,
            "requirement_id": test_requirement_id,
            "test_id": test_test_id,
            "relationship_type": "tests",
            "coverage_level": "partial",
            "priority": "medium",
            "notes": "Updated via comprehensive test",
            "updated_at": datetime.now().isoformat(),
            "updated_by": TEST_USER_ID,
        }

        try:
            result = await relationship_operation(**update_params)

            if result.get("success"):
                print("✅ Update operation successful")
                print(f"Response: {json.dumps(result, indent=2)}")
                test_results.append(TestResult("update_relationship", update_params, True, result))
            else:
                print(f"❌ Update operation failed: {result.get('error')}")
                test_results.append(
                    TestResult("update_relationship", update_params, False, result, result.get("error"))
                )
        except Exception as e:
            print(f"❌ Exception during update operation: {e}")
            test_results.append(TestResult("update_relationship", update_params, False, {}, str(e)))

    # ========================================================================
    # TEST 5: Query relationships with filters
    # ========================================================================
    print_subsection("TEST 5: Query relationships with filters")

    query_params = {
        "auth_token": mock_auth_token,
        "operation": "list",
        "relationship_type": "requirement_test",
        "source": {"type": "requirement", "id": test_requirement_id},
        "filters": {"coverage_level": "partial", "priority": "medium"},
        "limit": 10,
    }

    print("Operation: list (with filters)")
    print(f"Parameters: {json.dumps({k: v for k, v in query_params.items() if k != 'auth_token'}, indent=2)}")

    with patch("tools.relationship.RelationshipManager._validate_auth", new_callable=AsyncMock) as mock_auth, \
         patch("tools.relationship.RelationshipManager._get_user_id", return_value=TEST_USER_ID), \
         patch("tools.relationship.RelationshipManager._db_query", new_callable=AsyncMock) as mock_query:

        mock_auth.return_value = None
        mock_query.return_value = [
            {
                "id": created_relationship_id,
                "requirement_id": test_requirement_id,
                "test_id": test_test_id,
                "relationship_type": "tests",
                "coverage_level": "partial",
                "priority": "medium",
                "notes": "Updated via comprehensive test",
                "created_at": datetime.now().isoformat(),
            }
        ]

        try:
            result = await relationship_operation(**query_params)

            if result.get("success"):
                print("✅ Query with filters successful")
                print(f"Found {len(result.get('data', []))} relationship(s)")
                print(f"Response: {json.dumps(result, indent=2)}")
                test_results.append(TestResult("query_with_filters", query_params, True, result))
            else:
                print(f"❌ Query with filters failed: {result.get('error')}")
                test_results.append(
                    TestResult("query_with_filters", query_params, False, result, result.get("error"))
                )
        except Exception as e:
            print(f"❌ Exception during query operation: {e}")
            test_results.append(TestResult("query_with_filters", query_params, False, {}, str(e)))

    # ========================================================================
    # TEST 6: Delete the relationship (unlink)
    # ========================================================================
    print_subsection("TEST 6: Delete the relationship (unlink)")

    unlink_params = {
        "auth_token": mock_auth_token,
        "operation": "unlink",
        "relationship_type": "requirement_test",
        "source": {"type": "requirement", "id": test_requirement_id},
        "target": {"type": "test", "id": test_test_id},
        "soft_delete": True,
    }

    print("Operation: unlink (soft delete)")
    print(f"Parameters: {json.dumps({k: v for k, v in unlink_params.items() if k != 'auth_token'}, indent=2)}")

    with patch("tools.relationship.RelationshipManager._validate_auth", new_callable=AsyncMock) as mock_auth, \
         patch("tools.relationship.RelationshipManager._get_user_id", return_value=TEST_USER_ID), \
         patch("tools.relationship.RelationshipManager._db_update", new_callable=AsyncMock) as mock_update:

        mock_auth.return_value = None
        mock_update.return_value = {
            "id": created_relationship_id,
            "is_deleted": True,
            "deleted_at": datetime.now().isoformat(),
            "deleted_by": TEST_USER_ID,
        }

        try:
            result = await relationship_operation(**unlink_params)

            if result.get("success"):
                print("✅ Unlink operation successful")
                print(f"Response: {json.dumps(result, indent=2)}")
                test_results.append(TestResult("unlink_soft_delete", unlink_params, True, result))
            else:
                print(f"❌ Unlink operation failed: {result.get('error')}")
                test_results.append(
                    TestResult("unlink_soft_delete", unlink_params, False, result, result.get("error"))
                )
        except Exception as e:
            print(f"❌ Exception during unlink operation: {e}")
            test_results.append(TestResult("unlink_soft_delete", unlink_params, False, {}, str(e)))

    # ========================================================================
    # TEST 7: Additional relationship types - member relationship
    # ========================================================================
    print_subsection("TEST 7: Additional relationship types - member relationship")

    member_params = {
        "auth_token": mock_auth_token,
        "operation": "link",
        "relationship_type": "member",
        "source": {"type": "organization", "id": TEST_ORG_ID},
        "target": {"type": "user", "id": TEST_USER_ID},
        "metadata": {"role": "admin", "status": "active"},
    }

    print("Operation: link (member relationship)")
    print(f"Parameters: {json.dumps({k: v for k, v in member_params.items() if k != 'auth_token'}, indent=2)}")

    with patch("tools.relationship.RelationshipManager._validate_auth", new_callable=AsyncMock) as mock_auth, \
         patch("tools.relationship.RelationshipManager._get_user_id", return_value=TEST_USER_ID), \
         patch("tools.relationship.RelationshipManager._db_insert", new_callable=AsyncMock) as mock_insert:

        mock_auth.return_value = None
        mock_insert.return_value = {
            "id": str(uuid.uuid4()),
            "organization_id": TEST_ORG_ID,
            "user_id": TEST_USER_ID,
            "role": "admin",
            "status": "active",
            "created_at": datetime.now().isoformat(),
        }

        try:
            result = await relationship_operation(**member_params)

            if result.get("success"):
                print("✅ Member link operation successful")
                print(f"Response: {json.dumps(result, indent=2)}")
                test_results.append(TestResult("link_member", member_params, True, result))
            else:
                print(f"❌ Member link operation failed: {result.get('error')}")
                test_results.append(
                    TestResult("link_member", member_params, False, result, result.get("error"))
                )
        except Exception as e:
            print(f"❌ Exception during member link operation: {e}")
            test_results.append(TestResult("link_member", member_params, False, {}, str(e)))

    # ========================================================================
    # TEST 8: Error handling - missing target for link
    # ========================================================================
    print_subsection("TEST 8: Error handling - missing target for link")

    error_params = {
        "auth_token": mock_auth_token,
        "operation": "link",
        "relationship_type": "requirement_test",
        "source": {"type": "requirement", "id": test_requirement_id},
        # Missing target
    }

    print("Operation: link (missing target - should fail)")
    print(f"Parameters: {json.dumps({k: v for k, v in error_params.items() if k != 'auth_token'}, indent=2)}")

    with patch("tools.relationship.RelationshipManager._validate_auth", new_callable=AsyncMock) as mock_auth, \
         patch("tools.relationship.RelationshipManager._get_user_id", return_value=TEST_USER_ID):

        mock_auth.return_value = None

        try:
            result = await relationship_operation(**error_params)

            if not result.get("success"):
                print("✅ Error handling successful - correctly rejected missing target")
                print(f"Error: {result.get('error')}")
                test_results.append(TestResult("error_missing_target", error_params, True, result))
            else:
                print("❌ Error handling failed - should have rejected missing target")
                test_results.append(
                    TestResult("error_missing_target", error_params, False, result, "Should have failed")
                )
        except Exception as e:
            print(f"✅ Exception correctly raised for missing target: {e}")
            test_results.append(TestResult("error_missing_target", error_params, True, {"error": str(e)}))

    # ========================================================================
    # GENERATE COMPREHENSIVE REPORT
    # ========================================================================
    print_section("TEST RESULTS SUMMARY")

    total_tests = len(test_results)
    successful_tests = sum(1 for r in test_results if r.success)
    failed_tests = total_tests - successful_tests

    print(f"Total operations: {total_tests}")
    print(f"Successful: {successful_tests} ✅")
    print(f"Failed: {failed_tests} ❌")
    print(f"Success rate: {(successful_tests/total_tests*100):.1f}%")
    print()

    # Detailed results
    print("DETAILED RESULTS:")
    print("-" * 80)
    for i, result in enumerate(test_results, 1):
        status = "✅" if result.success else "❌"
        print(f"{i}. {status} {result.operation}")
        if result.error:
            print(f"   Error: {result.error}")

    print()

    # Save results to JSON file
    report_file = f"relationship_tool_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_data = {
        "summary": {
            "test_mode": "direct",
            "total_operations": total_tests,
            "successful": successful_tests,
            "failed": failed_tests,
            "success_rate": f"{(successful_tests/total_tests*100):.1f}%",
            "timestamp": datetime.now().isoformat(),
        },
        "operations_tested": [
            "list (empty state)",
            "link (create relationship)",
            "check (verify existence)",
            "update (modify metadata)",
            "list (with filters)",
            "unlink (soft delete)",
            "link (member relationship)",
            "error handling (missing target)",
        ],
        "relationship_types_tested": [
            "requirement_test",
            "member",
        ],
        "operations": [r.to_dict() for r in test_results],
    }

    with open(report_file, "w") as f:
        json.dump(report_data, f, indent=2)

    print(f"📄 Full report saved to: {report_file}")
    print()

    print_section("TESTING COMPLETE")

    return report_data


if __name__ == "__main__":
    asyncio.run(main())
