"""Manual test script for entity_tool via MCP server.

This script tests all CRUD operations for the entity_tool and documents results.

Run with: python test_entity_tool_manual.py
"""

import asyncio
import json
import os
import uuid
from datetime import UTC, datetime
from typing import Any

import httpx

# Configuration
MCP_BASE_URL = os.getenv("ATOMS_FASTMCP_BASE_URL", "http://127.0.0.1:8000")
MCP_PATH = os.getenv("ATOMS_FASTMCP_HTTP_PATH", "/api/mcp")
TEST_EMAIL = os.getenv("ATOMS_TEST_EMAIL", "kooshapari@kooshapari.com")
TEST_PASSWORD = os.getenv("ATOMS_TEST_PASSWORD", "118118")


class EntityToolTester:
    """Comprehensive tester for entity_tool MCP operations."""

    def __init__(self):
        self.results = []
        self.auth_token = None
        self.test_entities = {}

    async def authenticate(self):
        """Authenticate and get Supabase JWT."""
        from supabase import create_client

        url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

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

        self.auth_token = session.access_token
        print("✅ Authenticated successfully")

    async def call_entity_tool(self, operation: str, entity_type: str, **kwargs) -> dict[str, Any]:
        """Call entity_tool via MCP HTTP interface."""
        base_url = f"{MCP_BASE_URL.rstrip('/')}{MCP_PATH}"
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json",
        }

        params = {
            "operation": operation,
            "entity_type": entity_type,
            **kwargs
        }

        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/entity_tool",
            "params": params,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(base_url, json=payload, headers=headers)

            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }

            response_data = response.json()

            if "result" in response_data:
                return response_data["result"]
            if "error" in response_data:
                return {
                    "success": False,
                    "error": response_data["error"].get("message", str(response_data["error"]))
                }
            return {"success": False, "error": "Invalid response format"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def record_result(self, operation: str, entity_type: str, success: bool,
                     response: dict[str, Any], notes: str = ""):
        """Record test result."""
        result = {
            "operation": operation,
            "entity_type": entity_type,
            "success": success,
            "timestamp": datetime.now(UTC).isoformat(),
            "notes": notes,
            "response_keys": list(response.keys()) if isinstance(response, dict) else [],
            "error": response.get("error") if not success else None
        }
        self.results.append(result)

        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {operation.upper()} {entity_type}: {notes}")
        if not success and "error" in response:
            print(f"   Error: {response['error']}")

    async def test_create_entity(self):
        """Test 1: CREATE operation."""
        print("\n" + "="*60)
        print("TEST 1: CREATE ENTITY")
        print("="*60)

        # Create a test entity
        test_data = {
            "name": f"Test Entity {uuid.uuid4().hex[:8]}",
            "type": "test_entity",
            "description": "Testing entity_tool create operation",
            "status": "active",
            "properties": {
                "test_mode": True,
                "created_by": "entity_tool_tester"
            }
        }

        response = await self.call_entity_tool(
            operation="create",
            entity_type="test_entity",
            data=test_data
        )

        success = response.get("success", True) and "id" in response
        if success and "id" in response:
            self.test_entities["test_entity"] = response["id"]
            notes = f"Created entity with ID: {response['id']}"
        else:
            notes = "Failed to create entity"

        self.record_result("create", "test_entity", success, response, notes)

        print("\nResponse Structure:")
        print(json.dumps(response, indent=2, default=str))

        return response

    async def test_read_entity(self, entity_id: str):
        """Test 2: READ operation."""
        print("\n" + "="*60)
        print("TEST 2: READ ENTITY")
        print("="*60)

        # Test without relations
        response = await self.call_entity_tool(
            operation="read",
            entity_type="test_entity",
            entity_id=entity_id,
            include_relations=False
        )

        success = response.get("success", True) and response.get("id") == entity_id
        notes = f"Retrieved entity {entity_id}" if success else "Failed to retrieve"

        self.record_result("read", "test_entity", success, response, notes)

        print("\nResponse Structure:")
        print(json.dumps(response, indent=2, default=str))

        # Test with relations
        response_with_relations = await self.call_entity_tool(
            operation="read",
            entity_type="test_entity",
            entity_id=entity_id,
            include_relations=True
        )

        success_rel = response_with_relations.get("success", True)
        notes_rel = "Retrieved with relations" if success_rel else "Failed with relations"

        self.record_result("read_with_relations", "test_entity", success_rel,
                          response_with_relations, notes_rel)

        return response

    async def test_list_entities(self):
        """Test 3: LIST operation."""
        print("\n" + "="*60)
        print("TEST 3: LIST ENTITIES")
        print("="*60)

        # Test basic list
        response = await self.call_entity_tool(
            operation="list",
            entity_type="test_entity",
            limit=10
        )

        success = response.get("success", True) and isinstance(response.get("data"), list)
        count = len(response.get("data", [])) if success else 0
        notes = f"Listed {count} entities" if success else "Failed to list"

        self.record_result("list", "test_entity", success, response, notes)

        print("\nResponse Structure:")
        print(f"Count: {count}")
        if count > 0:
            print(f"Sample entity keys: {list(response['data'][0].keys())}")

        return response

    async def test_search_entities(self):
        """Test 4: SEARCH operation."""
        print("\n" + "="*60)
        print("TEST 4: SEARCH ENTITIES")
        print("="*60)

        # Search with filters
        response = await self.call_entity_tool(
            operation="search",
            entity_type="test_entity",
            filters={"status": "active"},
            limit=10
        )

        success = response.get("success", True) and isinstance(response.get("data"), list)
        count = len(response.get("data", [])) if success else 0
        notes = f"Found {count} entities with filter" if success else "Search failed"

        self.record_result("search", "test_entity", success, response, notes)

        # Search with term
        response_term = await self.call_entity_tool(
            operation="search",
            entity_type="test_entity",
            search_term="test",
            limit=10
        )

        success_term = response_term.get("success", True)
        count_term = len(response_term.get("data", [])) if success_term else 0
        notes_term = f"Found {count_term} entities with search term"

        self.record_result("search_with_term", "test_entity", success_term,
                          response_term, notes_term)

        print(f"\nFilter Search: {count} results")
        print(f"Term Search: {count_term} results")

        return response

    async def test_update_entity(self, entity_id: str):
        """Test 5: UPDATE operation."""
        print("\n" + "="*60)
        print("TEST 5: UPDATE ENTITY")
        print("="*60)

        update_data = {
            "name": f"Updated Test Entity {uuid.uuid4().hex[:8]}",
            "status": "updated",
            "properties": {
                "test_mode": True,
                "updated_by": "entity_tool_tester",
                "update_count": 1
            }
        }

        response = await self.call_entity_tool(
            operation="update",
            entity_type="test_entity",
            entity_id=entity_id,
            data=update_data
        )

        success = response.get("success", True) and response.get("id") == entity_id
        notes = f"Updated entity {entity_id}" if success else "Update failed"

        self.record_result("update", "test_entity", success, response, notes)

        print("\nResponse Structure:")
        print(json.dumps(response, indent=2, default=str))

        return response

    async def test_delete_entity(self, entity_id: str):
        """Test 6: DELETE operation."""
        print("\n" + "="*60)
        print("TEST 6: DELETE ENTITY")
        print("="*60)

        # Test soft delete
        response = await self.call_entity_tool(
            operation="delete",
            entity_type="test_entity",
            entity_id=entity_id,
            soft_delete=True
        )

        success = response.get("success", False)
        notes = f"Soft deleted entity {entity_id}" if success else "Soft delete failed"

        self.record_result("delete_soft", "test_entity", success, response, notes)

        print("\nResponse Structure:")
        print(json.dumps(response, indent=2, default=str))

        return response

    async def run_all_tests(self):
        """Run all entity_tool tests."""
        print("\n" + "="*80)
        print(" ENTITY_TOOL COMPREHENSIVE TEST SUITE")
        print("="*80)

        try:
            # Authenticate
            await self.authenticate()

            # Test 1: Create
            create_result = await self.test_create_entity()

            if "id" in create_result:
                entity_id = create_result["id"]

                # Test 2: Read
                await self.test_read_entity(entity_id)

                # Test 3: List
                await self.test_list_entities()

                # Test 4: Search
                await self.test_search_entities()

                # Test 5: Update
                await self.test_update_entity(entity_id)

                # Test 6: Delete
                await self.test_delete_entity(entity_id)
            else:
                print("\n⚠️ Skipping remaining tests - entity creation failed")

            # Generate report
            self.generate_report()

        except Exception as e:
            print(f"\n❌ Test suite failed with error: {e}")
            import traceback
            traceback.print_exc()

    def generate_report(self):
        """Generate comprehensive test report."""
        print("\n" + "="*80)
        print(" TEST REPORT")
        print("="*80)

        total = len(self.results)
        passed = sum(1 for r in self.results if r["success"])
        failed = total - passed

        print("\nSummary:")
        print(f"  Total Tests: {total}")
        print(f"  Passed: {passed} ✅")
        print(f"  Failed: {failed} ❌")
        print(f"  Pass Rate: {(passed/total*100) if total > 0 else 0:.1f}%")

        print("\n\nDetailed Results:")
        print("-" * 80)

        for result in self.results:
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"\n{status} - {result['operation'].upper()} ({result['entity_type']})")
            print(f"  Timestamp: {result['timestamp']}")
            print(f"  Notes: {result['notes']}")
            if result["error"]:
                print(f"  Error: {result['error']}")
            print(f"  Response Keys: {', '.join(result['response_keys'])}")

        print("\n" + "="*80)

        # Save to file
        report_file = f"entity_tool_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, "w") as f:
            json.dump({
                "summary": {
                    "total": total,
                    "passed": passed,
                    "failed": failed,
                    "pass_rate": (passed/total*100) if total > 0 else 0
                },
                "results": self.results
            }, f, indent=2, default=str)

        print(f"\n📝 Full report saved to: {report_file}")


async def main():
    """Run the comprehensive entity_tool test suite."""
    tester = EntityToolTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
