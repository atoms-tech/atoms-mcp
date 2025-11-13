#!/usr/bin/env python3
"""Comprehensive test of all Atoms MCP tools."""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, Any

# Set up environment
os.environ["ENV"] = "dev"

# Import the tools directly
from tools import (
    workspace_operation,
    entity_operation,
    relationship_operation,
    workflow_execute,
    data_query,
)

# Get auth token from environment
AUTH_TOKEN = os.getenv("SUPABASE_SERVICE_ROLE_KEY")


async def test_workspace_tool() -> Dict[str, Any]:
    """Test all workspace_tool operations."""
    results = {}

    print("\n" + "="*60)
    print("TESTING WORKSPACE_TOOL")
    print("="*60)

    # Test 1: List workspaces
    print("\n1. Testing 'list' operation...")
    try:
        result = await workspace_operation(
            auth_token=AUTH_TOKEN,
            operation="list",
        )
        results["list"] = {"status": "✅", "data": result}
        print(f"   ✅ Success: {json.dumps(result, indent=2)[:200]}...")
    except Exception as e:
        results["list"] = {"status": "❌", "error": str(e)}
        print(f"   ❌ Error: {e}")

    # Test 2: Get context
    print("\n2. Testing 'get_context' operation...")
    try:
        result = await workspace_operation(
            auth_token=AUTH_TOKEN,
            operation="get_context",
        )
        results["get_context"] = {"status": "✅", "data": result}
        print(f"   ✅ Success: {json.dumps(result, indent=2)[:200]}...")
    except Exception as e:
        results["get_context"] = {"status": "❌", "error": str(e)}
        print(f"   ❌ Error: {e}")

    # Test 3: Get defaults
    print("\n3. Testing 'get_defaults' operation...")
    try:
        result = await workspace_operation(
            auth_token=AUTH_TOKEN,
            operation="get_defaults",
        )
        results["get_defaults"] = {"status": "✅", "data": result}
        print(f"   ✅ Success: {json.dumps(result, indent=2)[:200]}...")
    except Exception as e:
        results["get_defaults"] = {"status": "❌", "error": str(e)}
        print(f"   ❌ Error: {e}")

    return results


async def test_entity_tool() -> Dict[str, Any]:
    """Test all entity_tool operations."""
    results = {}
    test_entity_id = None

    print("\n" + "="*60)
    print("TESTING ENTITY_TOOL")
    print("="*60)

    # Test 1: List entities
    print("\n1. Testing 'list' operation...")
    try:
        result = await entity_operation(
            auth_token=AUTH_TOKEN,
            operation="list",
            entity_type="project",
            limit=5,
        )
        results["list"] = {"status": "✅", "data": result}
        print(f"   ✅ Success: Found {result.get('data', {}).get('count', 0)} projects")
    except Exception as e:
        results["list"] = {"status": "❌", "error": str(e)}
        print(f"   ❌ Error: {e}")

    # Test 2: Create entity
    print("\n2. Testing 'create' operation...")
    try:
        result = await entity_operation(
            auth_token=AUTH_TOKEN,
            operation="create",
            entity_type="project",
            data={
                "name": f"Test Project {datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "description": "Automated test project",
            },
        )
        results["create"] = {"status": "✅", "data": result}
        if result.get("success") and result.get("data"):
            test_entity_id = result["data"].get("id")
        print(f"   ✅ Success: Created project with ID {test_entity_id}")
    except Exception as e:
        results["create"] = {"status": "❌", "error": str(e)}
        print(f"   ❌ Error: {e}")

    # Test 3: Read entity
    if test_entity_id:
        print(f"\n3. Testing 'read' operation with ID {test_entity_id}...")
        try:
            result = await entity_operation(
                auth_token=AUTH_TOKEN,
                operation="read",
                entity_type="project",
                entity_id=test_entity_id,
            )
            results["read"] = {"status": "✅", "data": result}
            print(f"   ✅ Success: Read project {result.get('data', {}).get('name')}")
        except Exception as e:
            results["read"] = {"status": "❌", "error": str(e)}
            print(f"   ❌ Error: {e}")

    # Test 4: Update entity
    if test_entity_id:
        print("\n4. Testing 'update' operation...")
        try:
            result = await entity_operation(
                auth_token=AUTH_TOKEN,
                operation="update",
                entity_type="project",
                entity_id=test_entity_id,
                data={"description": "Updated test project"},
            )
            results["update"] = {"status": "✅", "data": result}
            print("   ✅ Success: Updated project")
        except Exception as e:
            results["update"] = {"status": "❌", "error": str(e)}
            print(f"   ❌ Error: {e}")

    # Test 5: Search entities
    print("\n5. Testing 'search' operation...")
    try:
        result = await entity_operation(
            auth_token=AUTH_TOKEN,
            operation="search",
            entity_type="project",
            search_term="Test",
            limit=5,
        )
        results["search"] = {"status": "✅", "data": result}
        print(f"   ✅ Success: Found {len(result.get('data', {}).get('results', []))} matches")
    except Exception as e:
        results["search"] = {"status": "❌", "error": str(e)}
        print(f"   ❌ Error: {e}")

    # Test 6: Delete entity
    if test_entity_id:
        print("\n6. Testing 'delete' operation...")
        try:
            result = await entity_operation(
                auth_token=AUTH_TOKEN,
                operation="delete",
                entity_type="project",
                entity_id=test_entity_id,
                soft_delete=True,
            )
            results["delete"] = {"status": "✅", "data": result}
            print("   ✅ Success: Deleted project")
        except Exception as e:
            results["delete"] = {"status": "❌", "error": str(e)}
            print(f"   ❌ Error: {e}")

    return results


async def test_relationship_tool() -> Dict[str, Any]:
    """Test all relationship_tool operations."""
    results = {}

    print("\n" + "="*60)
    print("TESTING RELATIONSHIP_TOOL")
    print("="*60)

    # Test 1: List relationships
    print("\n1. Testing 'list' operation...")
    try:
        result = await relationship_operation(
            auth_token=AUTH_TOKEN,
            operation="list",
            relationship_type="member",
            source={"type": "organization"},
            limit=5,
        )
        results["list"] = {"status": "✅", "data": result}
        print("   ✅ Success: Found relationships")
    except Exception as e:
        results["list"] = {"status": "❌", "error": str(e)}
        print(f"   ❌ Error: {e}")

    # Test 2: Check relationship
    print("\n2. Testing 'check' operation...")
    try:
        result = await relationship_operation(
            auth_token=AUTH_TOKEN,
            operation="check",
            relationship_type="member",
            source={"type": "organization"},
            target={"type": "user"},
        )
        results["check"] = {"status": "✅", "data": result}
        print("   ✅ Success: Checked relationship")
    except Exception as e:
        results["check"] = {"status": "❌", "error": str(e)}
        print(f"   ❌ Error: {e}")

    return results


async def test_query_tool() -> Dict[str, Any]:
    """Test all query_tool operations."""
    results = {}

    print("\n" + "="*60)
    print("TESTING QUERY_TOOL")
    print("="*60)

    # Test 1: Search query
    print("\n1. Testing 'search' query...")
    try:
        result = await data_query(
            auth_token=AUTH_TOKEN,
            query_type="search",
            entities=["project"],
            search_term="test",
            limit=5,
        )
        results["search"] = {"status": "✅", "data": result}
        print("   ✅ Success: Search completed")
    except Exception as e:
        results["search"] = {"status": "❌", "error": str(e)}
        print(f"   ❌ Error: {e}")

    # Test 2: Aggregate query
    print("\n2. Testing 'aggregate' query...")
    try:
        result = await data_query(
            auth_token=AUTH_TOKEN,
            query_type="aggregate",
            entities=["project", "organization"],
        )
        results["aggregate"] = {"status": "✅", "data": result}
        print("   ✅ Success: Aggregation completed")
    except Exception as e:
        results["aggregate"] = {"status": "❌", "error": str(e)}
        print(f"   ❌ Error: {e}")

    # Test 3: RAG search
    print("\n3. Testing 'rag_search' query...")
    try:
        result = await data_query(
            auth_token=AUTH_TOKEN,
            query_type="rag_search",
            entities=["project"],
            search_term="test project",
            rag_mode="auto",
            limit=5,
        )
        results["rag_search"] = {"status": "✅", "data": result}
        print("   ✅ Success: RAG search completed")
    except Exception as e:
        results["rag_search"] = {"status": "❌", "error": str(e)}
        print(f"   ❌ Error: {e}")

    return results


async def test_workflow_tool() -> Dict[str, Any]:
    """Test workflow_tool operations."""
    results = {}

    print("\n" + "="*60)
    print("TESTING WORKFLOW_TOOL")
    print("="*60)

    # Test 1: Setup project workflow
    print("\n1. Testing 'setup_project' workflow...")
    try:
        result = await workflow_execute(
            auth_token=AUTH_TOKEN,
            workflow="setup_project",
            parameters={
                "name": f"Workflow Test {datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "description": "Test workflow project",
            },
        )
        results["setup_project"] = {"status": "✅", "data": result}
        print("   ✅ Success: Project setup completed")
    except Exception as e:
        results["setup_project"] = {"status": "❌", "error": str(e)}
        print(f"   ❌ Error: {e}")

    return results


async def main():
    """Run all tests and generate functionality matrix."""
    print("\n" + "="*80)
    print(" ATOMS MCP TOOLS COMPREHENSIVE FUNCTIONALITY TEST")
    print("="*80)

    all_results = {
        "workspace_tool": await test_workspace_tool(),
        "entity_tool": await test_entity_tool(),
        "relationship_tool": await test_relationship_tool(),
        "query_tool": await test_query_tool(),
        "workflow_tool": await test_workflow_tool(),
    }

    # Generate summary matrix
    print("\n\n" + "="*80)
    print(" FUNCTIONALITY MATRIX")
    print("="*80)

    for tool_name, operations in all_results.items():
        print(f"\n{tool_name.upper()}:")
        for op_name, result in operations.items():
            status = result.get("status", "❌")
            print(f"  {status} {op_name}")

    # Save results to file
    output_file = f"atoms_tools_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2, default=str)

    print(f"\n\n✅ Full results saved to: {output_file}")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
