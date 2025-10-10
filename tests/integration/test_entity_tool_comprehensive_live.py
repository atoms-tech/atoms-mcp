#!/usr/bin/env python3
"""
Comprehensive live test of mcp__Atoms__entity_tool

Tests ALL operations:
1. List entities
2. Create a test entity
3. Get the created entity details
4. Update the entity
5. Search entities
6. Delete the entity

Documents every result with:
- Operation name
- Input parameters
- Output/response
- Success/failure status
- Any errors encountered
"""

import os
import json
import uuid
import time
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any

import httpx
from supabase import create_client

# Configuration
MCP_BASE_URL = os.getenv("ATOMS_FASTMCP_BASE_URL", "http://127.0.0.1:8000")
MCP_PATH = os.getenv("ATOMS_FASTMCP_HTTP_PATH", "/api/mcp")
TEST_EMAIL = os.getenv("ATOMS_TEST_EMAIL", "kooshapari@kooshapari.com")
TEST_PASSWORD = os.getenv("ATOMS_TEST_PASSWORD", "118118")


class TestReport:
    """Collects and formats test results."""

    def __init__(self):
        self.tests = []
        self.start_time = datetime.now(timezone.utc)

    def add_test(self, operation: str, entity_type: str, input_params: Dict[str, Any],
                 output: Any, success: bool, duration_ms: float, error: str = None):
        """Add a test result."""
        self.tests.append({
            "operation": operation,
            "entity_type": entity_type,
            "input_params": input_params,
            "output": output,
            "success": success,
            "duration_ms": duration_ms,
            "error": error,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    def generate_report(self) -> str:
        """Generate comprehensive test report."""
        total_tests = len(self.tests)
        passed = sum(1 for t in self.tests if t["success"])
        failed = total_tests - passed

        report = []
        report.append("=" * 100)
        report.append("COMPREHENSIVE ENTITY TOOL TEST REPORT")
        report.append("=" * 100)
        report.append(f"\nGenerated: {datetime.now(timezone.utc).isoformat()}")
        report.append(f"Test Duration: {(datetime.now(timezone.utc) - self.start_time).total_seconds():.2f}s")
        report.append("\nSUMMARY:")
        report.append(f"  Total Tests: {total_tests}")
        report.append(f"  Passed: {passed} ({passed/total_tests*100:.1f}%)")
        report.append(f"  Failed: {failed} ({failed/total_tests*100:.1f}%)")
        report.append("\n" + "=" * 100)

        # Detailed results
        for i, test in enumerate(self.tests, 1):
            report.append(f"\n\nTEST {i}: {test['operation'].upper()} - {test['entity_type']}")
            report.append("-" * 100)
            report.append(f"Status: {'✅ PASSED' if test['success'] else '❌ FAILED'}")
            report.append(f"Duration: {test['duration_ms']:.2f}ms")
            report.append(f"Timestamp: {test['timestamp']}")

            report.append("\nInput Parameters:")
            report.append(json.dumps(test['input_params'], indent=2))

            if test['error']:
                report.append(f"\nError: {test['error']}")

            report.append("\nOutput/Response:")
            if isinstance(test['output'], (dict, list)):
                # Truncate large outputs
                output_str = json.dumps(test['output'], indent=2)
                if len(output_str) > 2000:
                    output_str = output_str[:2000] + "\n... (truncated)"
                report.append(output_str)
            else:
                report.append(str(test['output']))

        report.append("\n\n" + "=" * 100)
        report.append("END OF REPORT")
        report.append("=" * 100)

        return "\n".join(report)

    def save_json_report(self, filepath: str):
        """Save test results as JSON."""
        with open(filepath, 'w') as f:
            json.dump({
                "summary": {
                    "total": len(self.tests),
                    "passed": sum(1 for t in self.tests if t["success"]),
                    "failed": sum(1 for t in self.tests if not t["success"]),
                    "start_time": self.start_time.isoformat(),
                    "end_time": datetime.now(timezone.utc).isoformat()
                },
                "tests": self.tests
            }, f, indent=2)


async def get_auth_token() -> str:
    """Authenticate and get JWT token."""
    supabase_url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

    if not supabase_url or not supabase_key:
        raise ValueError("Supabase credentials not configured")

    client = create_client(supabase_url, supabase_key)
    auth_response = client.auth.sign_in_with_password({
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })

    session = getattr(auth_response, "session", None)
    if not session or not getattr(session, "access_token", None):
        raise ValueError("Could not obtain Supabase JWT")

    return session.access_token


async def call_entity_tool(auth_token: str, operation: str, entity_type: str,
                          **kwargs) -> tuple[Dict[str, Any], float]:
    """Call the entity_tool via MCP HTTP API."""
    base_url = f"{MCP_BASE_URL.rstrip('/')}{MCP_PATH}"
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json",
    }

    # Build parameters
    params = {
        "operation": operation,
        "entity_type": entity_type,
    }
    params.update(kwargs)

    payload = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "tools/entity_tool",
        "params": params,
    }

    start_time = time.perf_counter()

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(base_url, json=payload, headers=headers)

        duration_ms = (time.perf_counter() - start_time) * 1000

        if response.status_code != 200:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text}"
            }, duration_ms

        body = response.json()
        if "result" in body:
            return body["result"], duration_ms

        return {
            "success": False,
            "error": body.get("error", "Unknown error")
        }, duration_ms

    except Exception as e:
        duration_ms = (time.perf_counter() - start_time) * 1000
        return {"success": False, "error": str(e)}, duration_ms


async def run_comprehensive_tests():
    """Run all comprehensive tests."""
    report = TestReport()

    print("🚀 Starting Comprehensive Entity Tool Tests...")
    print(f"MCP Server: {MCP_BASE_URL}{MCP_PATH}")
    print(f"Test User: {TEST_EMAIL}")
    print("=" * 100)

    # Authenticate
    print("\n🔐 Authenticating...")
    try:
        auth_token = await get_auth_token()
        print("✅ Authentication successful")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return

    # Test entity types
    entity_types = ["organization", "project", "document"]

    for entity_type in entity_types:
        print(f"\n\n{'='*100}")
        print(f"Testing {entity_type.upper()}")
        print(f"{'='*100}")

        created_entity_id = None
        test_org_id = None

        # If testing project/document, create an organization first
        if entity_type in ["project", "document"]:
            print(f"\n📦 Creating test organization for {entity_type} tests...")
            org_data = {
                "name": f"Test Org for {entity_type} {uuid.uuid4().hex[:8]}",
                "slug": f"test-org-{entity_type}-{uuid.uuid4().hex[:8]}",
                "type": "team"
            }
            result, duration = await call_entity_tool(
                auth_token, "create", "organization", data=org_data
            )
            if result.get("success"):
                test_org_id = result["data"]["id"]
                print(f"✅ Created test organization: {test_org_id}")
            else:
                print(f"❌ Failed to create test organization: {result.get('error')}")
                continue

        # 1. LIST ENTITIES
        print(f"\n\n1️⃣  LIST {entity_type}s")
        print("-" * 100)
        input_params = {"limit": 5}
        result, duration = await call_entity_tool(
            auth_token, "list", entity_type, **input_params
        )
        print(f"   Duration: {duration:.2f}ms")
        print(f"   Success: {result.get('success')}")
        if result.get("success"):
            count = len(result.get("data", []))
            print(f"   Found {count} {entity_type}(s)")
        else:
            print(f"   Error: {result.get('error')}")

        report.add_test(
            "list", entity_type, input_params, result,
            result.get("success", False), duration, result.get("error")
        )

        # 2. CREATE ENTITY
        print(f"\n\n2️⃣  CREATE {entity_type}")
        print("-" * 100)

        # Prepare create data based on entity type
        if entity_type == "organization":
            create_data = {
                "name": f"Comprehensive Test Org {uuid.uuid4().hex[:8]}",
                "slug": f"comprehensive-test-org-{uuid.uuid4().hex[:8]}",
                "description": "Created by comprehensive entity tool test",
                "type": "team"
            }
        elif entity_type == "project":
            create_data = {
                "name": f"Comprehensive Test Project {uuid.uuid4().hex[:8]}",
                "organization_id": test_org_id,
                "description": "Created by comprehensive entity tool test"
            }
        elif entity_type == "document":
            # Create a project first
            print("   Creating test project for document...")
            project_data = {
                "name": f"Test Project for Doc {uuid.uuid4().hex[:8]}",
                "organization_id": test_org_id
            }
            proj_result, _ = await call_entity_tool(
                auth_token, "create", "project", data=project_data
            )
            if proj_result.get("success"):
                test_proj_id = proj_result["data"]["id"]
                print(f"   ✅ Created test project: {test_proj_id}")
                create_data = {
                    "name": f"Comprehensive Test Doc {uuid.uuid4().hex[:8]}",
                    "project_id": test_proj_id,
                    "description": "Created by comprehensive entity tool test"
                }
            else:
                print(f"   ❌ Failed to create test project: {proj_result.get('error')}")
                continue

        input_params = {"data": create_data}
        result, duration = await call_entity_tool(
            auth_token, "create", entity_type, **input_params
        )
        print(f"   Duration: {duration:.2f}ms")
        print(f"   Success: {result.get('success')}")

        if result.get("success"):
            created_entity_id = result["data"]["id"]
            print(f"   Created {entity_type} ID: {created_entity_id}")
            print(f"   Name: {result['data'].get('name')}")
        else:
            print(f"   Error: {result.get('error')}")

        report.add_test(
            "create", entity_type, input_params, result,
            result.get("success", False), duration, result.get("error")
        )

        if not created_entity_id:
            print(f"\n⚠️  Skipping remaining tests for {entity_type} - creation failed")
            continue

        # 3. READ ENTITY (GET DETAILS)
        print(f"\n\n3️⃣  READ {entity_type} (Get Details)")
        print("-" * 100)
        input_params = {"entity_id": created_entity_id, "include_relations": False}
        result, duration = await call_entity_tool(
            auth_token, "read", entity_type, **input_params
        )
        print(f"   Duration: {duration:.2f}ms")
        print(f"   Success: {result.get('success')}")

        if result.get("success"):
            print(f"   Name: {result['data'].get('name')}")
            print(f"   ID: {result['data'].get('id')}")
            print(f"   Created: {result['data'].get('created_at')}")
        else:
            print(f"   Error: {result.get('error')}")

        report.add_test(
            "read", entity_type, input_params, result,
            result.get("success", False), duration, result.get("error")
        )

        # 4. READ ENTITY WITH RELATIONS
        print(f"\n\n4️⃣  READ {entity_type} (With Relations)")
        print("-" * 100)
        input_params = {"entity_id": created_entity_id, "include_relations": True}
        result, duration = await call_entity_tool(
            auth_token, "read", entity_type, **input_params
        )
        print(f"   Duration: {duration:.2f}ms")
        print(f"   Success: {result.get('success')}")

        if result.get("success"):
            data = result['data']
            print(f"   Name: {data.get('name')}")
            # Check for relation-specific fields
            if entity_type == "organization":
                print(f"   Member Count: {data.get('member_count', 'N/A')}")
                print(f"   Recent Projects: {len(data.get('recent_projects', []))}")
            elif entity_type == "project":
                print(f"   Document Count: {data.get('document_count', 'N/A')}")
                print(f"   Members: {len(data.get('members', []))}")
            elif entity_type == "document":
                print(f"   Requirement Count: {data.get('requirement_count', 'N/A')}")
                print(f"   Blocks: {len(data.get('blocks', []))}")
        else:
            print(f"   Error: {result.get('error')}")

        report.add_test(
            "read_with_relations", entity_type, input_params, result,
            result.get("success", False), duration, result.get("error")
        )

        # 5. UPDATE ENTITY
        print(f"\n\n5️⃣  UPDATE {entity_type}")
        print("-" * 100)
        update_data = {
            "description": f"Updated by comprehensive test at {datetime.now(timezone.utc).isoformat()}"
        }
        input_params = {"entity_id": created_entity_id, "data": update_data}
        result, duration = await call_entity_tool(
            auth_token, "update", entity_type, **input_params
        )
        print(f"   Duration: {duration:.2f}ms")
        print(f"   Success: {result.get('success')}")

        if result.get("success"):
            print(f"   Updated Description: {result['data'].get('description')}")
            print(f"   Updated At: {result['data'].get('updated_at')}")
            print(f"   Updated By: {result['data'].get('updated_by')}")
        else:
            print(f"   Error: {result.get('error')}")

        report.add_test(
            "update", entity_type, input_params, result,
            result.get("success", False), duration, result.get("error")
        )

        # 6. SEARCH ENTITIES
        print(f"\n\n6️⃣  SEARCH {entity_type}s")
        print("-" * 100)
        input_params = {"search_term": "Comprehensive", "limit": 10}
        result, duration = await call_entity_tool(
            auth_token, "search", entity_type, **input_params
        )
        print(f"   Duration: {duration:.2f}ms")
        print(f"   Success: {result.get('success')}")

        if result.get("success"):
            count = len(result.get("data", []))
            print(f"   Found {count} matching {entity_type}(s)")
            # Check if our created entity is in the results
            found_our_entity = any(
                item.get("id") == created_entity_id
                for item in result.get("data", [])
            )
            print(f"   Our created entity in results: {found_our_entity}")
        else:
            print(f"   Error: {result.get('error')}")

        report.add_test(
            "search", entity_type, input_params, result,
            result.get("success", False), duration, result.get("error")
        )

        # 7. SEARCH WITH FILTERS
        print(f"\n\n7️⃣  SEARCH {entity_type}s (With Filters)")
        print("-" * 100)
        filters = {"is_deleted": False}
        if entity_type == "organization":
            filters["type"] = "team"
        input_params = {"filters": filters, "limit": 5}
        result, duration = await call_entity_tool(
            auth_token, "search", entity_type, **input_params
        )
        print(f"   Duration: {duration:.2f}ms")
        print(f"   Success: {result.get('success')}")

        if result.get("success"):
            count = len(result.get("data", []))
            print(f"   Found {count} filtered {entity_type}(s)")
        else:
            print(f"   Error: {result.get('error')}")

        report.add_test(
            "search_filtered", entity_type, input_params, result,
            result.get("success", False), duration, result.get("error")
        )

        # 8. DELETE ENTITY (SOFT DELETE)
        print(f"\n\n8️⃣  DELETE {entity_type} (Soft Delete)")
        print("-" * 100)
        input_params = {"entity_id": created_entity_id, "soft_delete": True}
        result, duration = await call_entity_tool(
            auth_token, "delete", entity_type, **input_params
        )
        print(f"   Duration: {duration:.2f}ms")
        print(f"   Success: {result.get('success')}")

        if result.get("success"):
            print(f"   Soft deleted {entity_type}: {created_entity_id}")
        else:
            print(f"   Error: {result.get('error')}")

        report.add_test(
            "delete_soft", entity_type, input_params, result,
            result.get("success", False), duration, result.get("error")
        )

        # 9. VERIFY SOFT DELETE (Should not appear in list)
        print("\n\n9️⃣  VERIFY Soft Delete")
        print("-" * 100)
        input_params = {"limit": 20}
        result, duration = await call_entity_tool(
            auth_token, "list", entity_type, **input_params
        )
        print(f"   Duration: {duration:.2f}ms")
        print(f"   Success: {result.get('success')}")

        if result.get("success"):
            # Check if soft-deleted entity is NOT in the list
            found_deleted = any(
                item.get("id") == created_entity_id
                for item in result.get("data", [])
            )
            print(f"   Soft-deleted entity in list: {found_deleted} (should be False)")
            verification_success = not found_deleted
        else:
            print(f"   Error: {result.get('error')}")
            verification_success = False

        report.add_test(
            "verify_soft_delete", entity_type, input_params, result,
            verification_success, duration, result.get("error")
        )

        # Cleanup: Delete test org if we created one
        if test_org_id and entity_type in ["project", "document"]:
            print(f"\n🧹 Cleaning up test organization: {test_org_id}")
            await call_entity_tool(
                auth_token, "delete", "organization",
                entity_id=test_org_id, soft_delete=True
            )

    # Generate and display report
    print("\n\n")
    print("=" * 100)
    print("GENERATING FINAL REPORT...")
    print("=" * 100)

    report_text = report.generate_report()
    print(report_text)

    # Save reports
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    text_report_path = f"/Users/kooshapari/temp-PRODVERCEL/485/clean/atoms_mcp-old/entity_tool_comprehensive_report_{timestamp}.txt"
    with open(text_report_path, 'w') as f:
        f.write(report_text)
    print(f"\n📄 Text report saved to: {text_report_path}")

    json_report_path = f"/Users/kooshapari/temp-PRODVERCEL/485/clean/atoms_mcp-old/entity_tool_comprehensive_report_{timestamp}.json"
    report.save_json_report(json_report_path)
    print(f"📄 JSON report saved to: {json_report_path}")

    return report


if __name__ == "__main__":
    asyncio.run(run_comprehensive_tests())
