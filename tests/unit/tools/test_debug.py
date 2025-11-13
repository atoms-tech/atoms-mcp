"""Debug test to see what error is happening with document creation."""
import asyncio
import pytest
import sys
sys.path.insert(0, '.')


@pytest.mark.asyncio
async def test_debug_document_creation(call_mcp, test_organization):
    """Debug document creation to see error."""
    # Create a project
    project_result, _ = await call_mcp(
        "entity_tool",
        {
            "operation": "create",
            "entity_type": "project",
            "data": {
                "name": f"Debug Project",
                "organization_id": test_organization,
            },
        },
    )
    print(f"Project result: {project_result}")
    project_id = project_result.get("data", {}).get("id")
    print(f"Project ID: {project_id}")

    # Create a document
    doc_result, _ = await call_mcp(
        "entity_tool",
        {
            "operation": "create",
            "entity_type": "document",
            "data": {
                "title": "Test Document",
                "content": "Test Content",
                "project_id": project_id,
            },
        },
    )
    print(f"Document result: {doc_result}")
    print(f"Document success: {doc_result.get('success')}")
    print(f"Document error: {doc_result.get('error')}")
    print(f"Document data: {doc_result.get('data')}")
    
    assert doc_result.get("success"), f"Document creation failed: {doc_result.get('error')}"
