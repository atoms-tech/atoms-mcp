"""Simple test script for the consolidated tools."""

import asyncio
import os
from typing import Dict, Any

# Set test environment
os.environ["ATOMS_BACKEND_TYPE"] = "supabase"
os.environ["FASTMCP_DEMO_USER"] = "test@example.com"
os.environ["FASTMCP_DEMO_PASS"] = "testpass"

from tools.workspace import workspace_operation
from tools.entity import entity_operation
from tools.relationship import relationship_operation


async def test_auth_validation():
    """Test authentication validation."""
    print("Testing authentication...")
    
    # Test with invalid token
    try:
        result = await workspace_operation(
            auth_token="invalid_token",
            operation="get_context"
        )
        print(f"❌ Expected auth error, got: {result}")
    except Exception as e:
        print(f"✅ Auth validation working: {e}")
    
    # Test with demo credentials (this would need to be adapted for real auth)
    print("Authentication test completed.\n")


async def test_workspace_operations():
    """Test workspace context management."""
    print("Testing workspace operations...")
    
    # Mock token for testing (in real usage, this would come from authentication)
    mock_token = "demo_session_token"
    
    try:
        # Test get context
        result = await workspace_operation(
            auth_token=mock_token,
            operation="get_context"
        )
        print(f"✅ Get context: {result.get('success', False)}")
        
        # Test list workspaces  
        result = await workspace_operation(
            auth_token=mock_token,
            operation="list_workspaces"
        )
        print(f"✅ List workspaces: {result.get('success', False)}")
        
    except Exception as e:
        print(f"❌ Workspace operations error: {e}")
    
    print("Workspace operations test completed.\n")


async def test_entity_operations():
    """Test entity CRUD operations."""
    print("Testing entity operations...")
    
    mock_token = "demo_session_token"
    
    try:
        # Test entity search (should work even without real data)
        result = await entity_operation(
            auth_token=mock_token,
            operation="search",
            entity_type="organization",
            filters={"is_deleted": False},
            limit=5
        )
        print(f"✅ Entity search: {result.get('success', False)}")
        
        # Test entity list
        result = await entity_operation(
            auth_token=mock_token,
            operation="list",
            entity_type="project",
            limit=3
        )
        print(f"✅ Entity list: {result.get('success', False)}")
        
    except Exception as e:
        print(f"❌ Entity operations error: {e}")
    
    print("Entity operations test completed.\n")


async def test_relationship_operations():
    """Test relationship management."""
    print("Testing relationship operations...")
    
    mock_token = "demo_session_token"
    
    try:
        # Test relationship list (should work even without real data)
        result = await relationship_operation(
            auth_token=mock_token,
            operation="list",
            relationship_type="member",
            source={"type": "organization", "id": "test_org"}
        )
        print(f"✅ Relationship list: {result.get('success', False)}")
        
    except Exception as e:
        print(f"❌ Relationship operations error: {e}")
    
    print("Relationship operations test completed.\n")


def test_adapter_factory():
    """Test adapter factory functionality."""
    print("Testing adapter factory...")
    
    try:
        from infrastructure.factory import get_adapters, get_adapter_factory
        
        # Get factory
        factory = get_adapter_factory()
        print(f"✅ Factory created: {factory.get_backend_type()}")
        
        # Get adapters
        adapters = get_adapters()
        expected_adapters = ["auth", "database", "storage", "realtime"]
        
        for adapter_name in expected_adapters:
            if adapter_name in adapters:
                print(f"✅ {adapter_name} adapter available")
            else:
                print(f"❌ {adapter_name} adapter missing")
        
    except Exception as e:
        print(f"❌ Adapter factory error: {e}")
    
    print("Adapter factory test completed.\n")


def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    
    try:
        # Test infrastructure imports
        from infrastructure.factory import get_adapters
        from infrastructure.adapters import AuthAdapter, DatabaseAdapter
        print("✅ Infrastructure imports successful")
        
        # Test auth imports
        from auth import SupabaseAuthProvider
        print("✅ Auth imports successful")
        
        # Test tools imports
        from tools import workspace_operation, entity_operation
        print("✅ Tools imports successful")
        
        # Test server imports
        from new_server import create_consolidated_server
        print("✅ Server imports successful")
        
        # Test legacy imports
        from legacy import create_legacy_wrapper_server
        print("✅ Legacy imports successful")
        
    except Exception as e:
        print(f"❌ Import error: {e}")
    
    print("Import test completed.\n")


async def main():
    """Run all tests."""
    print("🚀 Starting atoms_fastmcp consolidated tools tests...\n")
    
    # Test imports first
    test_imports()
    
    # Test adapter factory
    test_adapter_factory()
    
    # Test auth (basic validation)
    await test_auth_validation()
    
    # Test operations (these will mostly test the structure)
    await test_workspace_operations()
    await test_entity_operations() 
    await test_relationship_operations()
    
    print("🎉 All tests completed!")
    print("\nTo use the new consolidated server:")
    print("1. Set ATOMS_FASTMCP_MODE=consolidated")
    print("2. Configure Supabase environment variables")
    print("3. Run: python -m atoms_fastmcp.server")


if __name__ == "__main__":
    asyncio.run(main())