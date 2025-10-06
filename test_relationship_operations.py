#!/usr/bin/env python3
"""
Comprehensive test script for relationship_tool via MCP server.
Tests all operations with detailed reporting.

Run with: python test_relationship_operations.py
"""

import os
import sys
import json
import uuid
import asyncio
from typing import Any, Dict, Optional
from datetime import datetime

import httpx
from supabase import create_client

# Configuration
MCP_BASE_URL = os.getenv("ATOMS_FASTMCP_BASE_URL", "http://127.0.0.1:8000")
MCP_PATH = os.getenv("ATOMS_FASTMCP_HTTP_PATH", "/api/mcp")
TEST_EMAIL = os.getenv("ATOMS_TEST_EMAIL", "kooshapari@kooshapari.com")
TEST_PASSWORD = os.getenv("ATOMS_TEST_PASSWORD", "118118")

# Test results storage
test_results = []


class TestResult:
    """Store test operation results."""

    def __init__(self, operation: str, params: Dict[str, Any],
                 success: bool, response: Dict[str, Any],
                 error: Optional[str] = None):
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
            "timestamp": self.timestamp
        }


async def get_supabase_jwt() -> str:
    """Authenticate with Supabase and get JWT token."""
    url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    key = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

    if not url or not key:
        raise ValueError("Supabase credentials not configured")

    client = create_client(url, key)
    auth_response = client.auth.sign_in_with_password({
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })

    session = getattr(auth_response, "session", None)
    if not session or not getattr(session, "access_token", None):
        raise ValueError("Could not obtain Supabase JWT")

    return session.access_token


async def call_mcp(tool_name: str, params: Dict[str, Any], jwt_token: str) -> Dict[str, Any]:
    """Call an MCP tool via HTTP."""
    base_url = f"{MCP_BASE_URL.rstrip('/')}{MCP_PATH}"
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json",
    }

    payload = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": f"tools/{tool_name}",
        "params": params,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(base_url, json=payload, headers=headers)

    if response.status_code != 200:
        return {
            "success": False,
            "error": f"HTTP {response.status_code}: {response.text}"
        }

    body = response.json()
    if "result" in body:
        return body["result"]
    return {"success": False, "error": body.get("error", "Unknown error")}


async def main():
    """Execute all relationship tool tests."""
    print("=" * 80)
    print("ATOMS MCP RELATIONSHIP_TOOL COMPREHENSIVE TEST")
    print("=" * 80)
    print()

    # Get authentication token
    print("🔐 Authenticating with Supabase...")
    try:
        jwt_token = await get_supabase_jwt()
        print("✅ Authentication successful")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return

    print()

    # Test entity IDs (to be populated)
    test_entities = {}
    relationship_id = None

    # ========================================================================
    # OPERATION 1: Create two test entities to link together
    # ========================================================================
    print("📦 OPERATION 1: Creating two test entities")
    print("-" * 80)

    # Create first entity (requirement)
    req_params = {
        "operation": "create",
        "entity_type": "requirement",
        "data": {
            "name": f"Test Requirement {uuid.uuid4().hex[:8]}",
            "description": "Test requirement for relationship testing",
            "document_id": "auto"  # Will use context
        }
    }

    print(f"Creating requirement...")
    print(f"Parameters: {json.dumps(req_params, indent=2)}")

    req_result = await call_mcp("entity_tool", req_params, jwt_token)

    if req_result.get("success"):
        test_entities["requirement"] = req_result["data"]["id"]
        print(f"✅ Requirement created: {test_entities['requirement']}")
        test_results.append(TestResult(
            "create_entity_requirement",
            req_params,
            True,
            req_result
        ))
    else:
        print(f"❌ Failed to create requirement: {req_result.get('error')}")
        test_results.append(TestResult(
            "create_entity_requirement",
            req_params,
            False,
            req_result,
            req_result.get('error')
        ))

    print()

    # Create second entity (test)
    test_params = {
        "operation": "create",
        "entity_type": "test",
        "data": {
            "name": f"Test Case {uuid.uuid4().hex[:8]}",
            "description": "Test case for relationship testing",
            "project_id": "auto"  # Will use context
        }
    }

    print(f"Creating test case...")
    print(f"Parameters: {json.dumps(test_params, indent=2)}")

    test_result = await call_mcp("entity_tool", test_params, jwt_token)

    if test_result.get("success"):
        test_entities["test"] = test_result["data"]["id"]
        print(f"✅ Test case created: {test_entities['test']}")
        test_results.append(TestResult(
            "create_entity_test",
            test_params,
            True,
            test_result
        ))
    else:
        print(f"❌ Failed to create test case: {test_result.get('error')}")
        test_results.append(TestResult(
            "create_entity_test",
            test_params,
            False,
            test_result,
            test_result.get('error')
        ))

    print()

    # ========================================================================
    # OPERATION 2: Create a relationship between these entities
    # ========================================================================
    print("🔗 OPERATION 2: Creating relationship between entities")
    print("-" * 80)

    if "requirement" in test_entities and "test" in test_entities:
        link_params = {
            "operation": "link",
            "relationship_type": "requirement_test",
            "source": {
                "type": "requirement",
                "id": test_entities["requirement"]
            },
            "target": {
                "type": "test",
                "id": test_entities["test"]
            },
            "metadata": {
                "relationship_type": "tests",
                "coverage_level": "full",
                "priority": "high"
            }
        }

        print(f"Linking requirement to test...")
        print(f"Parameters: {json.dumps(link_params, indent=2)}")

        link_result = await call_mcp("relationship_tool", link_params, jwt_token)

        if link_result.get("success"):
            relationship_id = link_result["data"].get("id")
            print(f"✅ Relationship created successfully")
            print(f"Relationship ID: {relationship_id}")
            print(f"Response data: {json.dumps(link_result['data'], indent=2)}")
            test_results.append(TestResult(
                "link_relationship",
                link_params,
                True,
                link_result
            ))
        else:
            print(f"❌ Failed to create relationship: {link_result.get('error')}")
            test_results.append(TestResult(
                "link_relationship",
                link_params,
                False,
                link_result,
                link_result.get('error')
            ))
    else:
        print("⚠️  Skipping: Required entities not created")

    print()

    # ========================================================================
    # OPERATION 3: Get the relationship by ID (using check operation)
    # ========================================================================
    print("🔍 OPERATION 3: Getting relationship by ID (check operation)")
    print("-" * 80)

    if "requirement" in test_entities and "test" in test_entities:
        check_params = {
            "operation": "check",
            "relationship_type": "requirement_test",
            "source": {
                "type": "requirement",
                "id": test_entities["requirement"]
            },
            "target": {
                "type": "test",
                "id": test_entities["test"]
            }
        }

        print(f"Checking if relationship exists...")
        print(f"Parameters: {json.dumps(check_params, indent=2)}")

        check_result = await call_mcp("relationship_tool", check_params, jwt_token)

        if check_result.get("exists"):
            print(f"✅ Relationship exists")
            print(f"Relationship data: {json.dumps(check_result.get('relationship'), indent=2)}")
            test_results.append(TestResult(
                "check_relationship",
                check_params,
                True,
                check_result
            ))
        else:
            print(f"❌ Relationship not found or error: {check_result}")
            test_results.append(TestResult(
                "check_relationship",
                check_params,
                False,
                check_result,
                "Relationship not found"
            ))
    else:
        print("⚠️  Skipping: Required entities not created")

    print()

    # ========================================================================
    # OPERATION 4: List relationships for one of the entities
    # ========================================================================
    print("📋 OPERATION 4: Listing relationships for requirement")
    print("-" * 80)

    if "requirement" in test_entities:
        list_params = {
            "operation": "list",
            "relationship_type": "requirement_test",
            "source": {
                "type": "requirement",
                "id": test_entities["requirement"]
            },
            "limit": 10,
            "offset": 0
        }

        print(f"Listing relationships...")
        print(f"Parameters: {json.dumps(list_params, indent=2)}")

        list_result = await call_mcp("relationship_tool", list_params, jwt_token)

        if list_result.get("success"):
            relationships = list_result.get("data", [])
            print(f"✅ Found {len(relationships)} relationship(s)")
            for i, rel in enumerate(relationships, 1):
                print(f"  {i}. {json.dumps(rel, indent=4)}")
            test_results.append(TestResult(
                "list_relationships",
                list_params,
                True,
                list_result
            ))
        else:
            print(f"❌ Failed to list relationships: {list_result.get('error')}")
            test_results.append(TestResult(
                "list_relationships",
                list_params,
                False,
                list_result,
                list_result.get('error')
            ))
    else:
        print("⚠️  Skipping: Required entities not created")

    print()

    # ========================================================================
    # OPERATION 5: Query relationships with filters
    # ========================================================================
    print("🔎 OPERATION 5: Querying relationships with filters")
    print("-" * 80)

    if "requirement" in test_entities:
        filter_params = {
            "operation": "list",
            "relationship_type": "requirement_test",
            "source": {
                "type": "requirement",
                "id": test_entities["requirement"]
            },
            "filters": {
                "coverage_level": "full",
                "priority": "high"
            },
            "limit": 10
        }

        print(f"Querying with filters...")
        print(f"Parameters: {json.dumps(filter_params, indent=2)}")

        filter_result = await call_mcp("relationship_tool", filter_params, jwt_token)

        if filter_result.get("success"):
            filtered_rels = filter_result.get("data", [])
            print(f"✅ Found {len(filtered_rels)} filtered relationship(s)")
            for i, rel in enumerate(filtered_rels, 1):
                print(f"  {i}. Coverage: {rel.get('coverage_level')}, Priority: {rel.get('priority')}")
            test_results.append(TestResult(
                "query_relationships_with_filters",
                filter_params,
                True,
                filter_result
            ))
        else:
            print(f"❌ Failed to query with filters: {filter_result.get('error')}")
            test_results.append(TestResult(
                "query_relationships_with_filters",
                filter_params,
                False,
                filter_result,
                filter_result.get('error')
            ))
    else:
        print("⚠️  Skipping: Required entities not created")

    print()

    # ========================================================================
    # OPERATION 6: Update the relationship metadata
    # ========================================================================
    print("✏️  OPERATION 6: Updating relationship metadata")
    print("-" * 80)

    if "requirement" in test_entities and "test" in test_entities:
        update_params = {
            "operation": "update",
            "relationship_type": "requirement_test",
            "source": {
                "type": "requirement",
                "id": test_entities["requirement"]
            },
            "target": {
                "type": "test",
                "id": test_entities["test"]
            },
            "metadata": {
                "coverage_level": "partial",
                "priority": "medium",
                "notes": "Updated via test script"
            }
        }

        print(f"Updating relationship metadata...")
        print(f"Parameters: {json.dumps(update_params, indent=2)}")

        update_result = await call_mcp("relationship_tool", update_params, jwt_token)

        if update_result.get("success"):
            print(f"✅ Relationship updated successfully")
            print(f"Updated data: {json.dumps(update_result['data'], indent=2)}")
            test_results.append(TestResult(
                "update_relationship",
                update_params,
                True,
                update_result
            ))
        else:
            print(f"❌ Failed to update relationship: {update_result.get('error')}")
            test_results.append(TestResult(
                "update_relationship",
                update_params,
                False,
                update_result,
                update_result.get('error')
            ))
    else:
        print("⚠️  Skipping: Required entities not created")

    print()

    # ========================================================================
    # OPERATION 7: Delete the relationship
    # ========================================================================
    print("🗑️  OPERATION 7: Deleting relationship")
    print("-" * 80)

    if "requirement" in test_entities and "test" in test_entities:
        delete_params = {
            "operation": "unlink",
            "relationship_type": "requirement_test",
            "source": {
                "type": "requirement",
                "id": test_entities["requirement"]
            },
            "target": {
                "type": "test",
                "id": test_entities["test"]
            },
            "soft_delete": True
        }

        print(f"Deleting relationship (soft delete)...")
        print(f"Parameters: {json.dumps(delete_params, indent=2)}")

        delete_result = await call_mcp("relationship_tool", delete_params, jwt_token)

        if delete_result.get("success"):
            print(f"✅ Relationship deleted successfully")
            print(f"Response: {json.dumps(delete_result, indent=2)}")
            test_results.append(TestResult(
                "delete_relationship",
                delete_params,
                True,
                delete_result
            ))
        else:
            print(f"❌ Failed to delete relationship: {delete_result.get('error')}")
            test_results.append(TestResult(
                "delete_relationship",
                delete_params,
                False,
                delete_result,
                delete_result.get('error')
            ))
    else:
        print("⚠️  Skipping: Required entities not created")

    print()

    # ========================================================================
    # OPERATION 8: Clean up test entities
    # ========================================================================
    print("🧹 OPERATION 8: Cleaning up test entities")
    print("-" * 80)

    for entity_type in ["test", "requirement"]:
        if entity_type in test_entities:
            cleanup_params = {
                "operation": "delete",
                "entity_type": entity_type,
                "entity_id": test_entities[entity_type],
                "soft_delete": True
            }

            print(f"Deleting {entity_type}: {test_entities[entity_type]}")

            cleanup_result = await call_mcp("entity_tool", cleanup_params, jwt_token)

            if cleanup_result.get("success"):
                print(f"✅ {entity_type.capitalize()} deleted")
                test_results.append(TestResult(
                    f"cleanup_{entity_type}",
                    cleanup_params,
                    True,
                    cleanup_result
                ))
            else:
                print(f"❌ Failed to delete {entity_type}: {cleanup_result.get('error')}")
                test_results.append(TestResult(
                    f"cleanup_{entity_type}",
                    cleanup_params,
                    False,
                    cleanup_result,
                    cleanup_result.get('error')
                ))

    print()

    # ========================================================================
    # GENERATE COMPREHENSIVE REPORT
    # ========================================================================
    print("=" * 80)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 80)
    print()

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
            "total_operations": total_tests,
            "successful": successful_tests,
            "failed": failed_tests,
            "success_rate": f"{(successful_tests/total_tests*100):.1f}%",
            "timestamp": datetime.now().isoformat()
        },
        "operations": [r.to_dict() for r in test_results]
    }

    with open(report_file, 'w') as f:
        json.dump(report_data, f, indent=2)

    print(f"📄 Full report saved to: {report_file}")
    print()

    print("=" * 80)
    print("✅ TESTING COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
