#!/usr/bin/env python3
"""
Comprehensive Atoms MCP Functionality Matrix Test
Tests all tools and operations without authentication (shows API structure)
"""

import json
from datetime import datetime

# Tool definitions from server.py
TOOLS = {
    "workspace_tool": {
        "description": "Manage workspace context and get smart defaults",
        "operations": [
            {
                "name": "get_context",
                "params": {"operation": "get_context"},
                "description": "Get current workspace context"
            },
            {
                "name": "set_context",
                "params": {"operation": "set_context", "context_type": "project", "entity_id": "<id>"},
                "description": "Set active organization/project/document"
            },
            {
                "name": "list_workspaces",
                "params": {"operation": "list_workspaces"},
                "description": "List available workspaces"
            },
            {
                "name": "get_defaults",
                "params": {"operation": "get_defaults"},
                "description": "Get smart default values for operations"
            }
        ],
        "parameters": [
            "operation (required)",
            "context_type (optional)",
            "entity_id (optional)",
            "format_type (optional, default='detailed')"
        ],
        "auth_required": True
    },

    "entity_tool": {
        "description": "Unified CRUD operations with smart parameter inference and fuzzy matching",
        "operations": [
            {
                "name": "create",
                "params": {"entity_type": "project", "data": {"name": "..."}},
                "description": "Create new entity (operation auto-inferred from data param)"
            },
            {
                "name": "read",
                "params": {"entity_type": "project", "entity_id": "..."},
                "description": "Read entity by ID or name (fuzzy matching)"
            },
            {
                "name": "update",
                "params": {"entity_type": "project", "entity_id": "...", "data": {"description": "..."}},
                "description": "Update entity (operation auto-inferred)"
            },
            {
                "name": "delete",
                "params": {"entity_type": "project", "entity_id": "...", "operation": "delete"},
                "description": "Delete entity (soft delete by default)"
            },
            {
                "name": "list",
                "params": {"entity_type": "project", "parent_type": "organization", "parent_id": "..."},
                "description": "List entities with filters"
            },
            {
                "name": "search",
                "params": {"entity_type": "project", "search_term": "..."},
                "description": "Search entities (operation auto-inferred)"
            },
            {
                "name": "batch",
                "params": {"entity_type": "project", "batch": [{"operation": "create", "data": {}}]},
                "description": "Batch operations on multiple entities"
            }
        ],
        "entity_types": [
            "organization", "project", "document", "requirement",
            "test_case", "task", "user"
        ],
        "parameters": [
            "entity_type (required)",
            "operation (optional - auto-inferred)",
            "data (optional)",
            "filters (optional)",
            "entity_id (optional - supports fuzzy matching)",
            "include_relations (bool)",
            "batch (optional)",
            "search_term (optional)",
            "parent_type (optional)",
            "parent_id (optional)",
            "limit (optional, default=100)",
            "offset (optional)",
            "order_by (optional)",
            "soft_delete (bool, default=True)",
            "format_type (optional)"
        ],
        "features": [
            "Smart operation inference",
            "Fuzzy ID matching (70%+ similarity)",
            "Partial name matching",
            "Auto UUID resolution",
            "Batch operations",
            "Relation includes"
        ],
        "auth_required": True
    },

    "relationship_tool": {
        "description": "Manage relationships between entities",
        "operations": [
            {
                "name": "link",
                "params": {
                    "operation": "link",
                    "relationship_type": "member",
                    "source": {"type": "organization", "id": "..."},
                    "target": {"type": "user", "id": "..."},
                    "metadata": {"role": "admin"}
                },
                "description": "Create relationship between entities"
            },
            {
                "name": "unlink",
                "params": {
                    "operation": "unlink",
                    "relationship_type": "member",
                    "source": {"type": "organization", "id": "..."},
                    "target": {"type": "user", "id": "..."}
                },
                "description": "Remove relationship"
            },
            {
                "name": "list",
                "params": {
                    "operation": "list",
                    "relationship_type": "member",
                    "source": {"type": "project", "id": "..."}
                },
                "description": "List relationships"
            },
            {
                "name": "check",
                "params": {
                    "operation": "check",
                    "relationship_type": "member",
                    "source": {"type": "organization", "id": "..."},
                    "target": {"type": "user", "id": "..."}
                },
                "description": "Check if relationship exists"
            },
            {
                "name": "update",
                "params": {
                    "operation": "update",
                    "relationship_type": "member",
                    "source": {"type": "organization", "id": "..."},
                    "target": {"type": "user", "id": "..."},
                    "metadata": {"role": "viewer"}
                },
                "description": "Update relationship metadata"
            }
        ],
        "relationship_types": [
            "member (Organization/project members)",
            "assignment (Task assignments)",
            "trace_link (Requirement traceability)",
            "requirement_test (Test coverage)",
            "invitation (Organization invitations)"
        ],
        "parameters": [
            "operation (required)",
            "relationship_type (required)",
            "source (dict with type/id, required)",
            "target (dict with type/id, optional)",
            "metadata (optional)",
            "filters (optional)",
            "source_context (optional)",
            "soft_delete (bool, default=True)",
            "limit (optional, default=100)",
            "offset (optional)",
            "format_type (optional)"
        ],
        "auth_required": True
    },

    "workflow_tool": {
        "description": "Execute complex multi-step workflows",
        "workflows": [
            {
                "name": "setup_project",
                "params": {
                    "name": "My Project",
                    "organization_id": "org_123",
                    "initial_documents": ["Requirements", "Design"]
                },
                "description": "Create project with initial structure"
            },
            {
                "name": "import_requirements",
                "params": {
                    "document_id": "doc_123",
                    "requirements": [{"name": "REQ-1", "description": "..."}]
                },
                "description": "Import requirements from external source"
            },
            {
                "name": "setup_test_matrix",
                "params": {
                    "project_id": "proj_123"
                },
                "description": "Set up test matrix for a project"
            },
            {
                "name": "bulk_status_update",
                "params": {
                    "entity_type": "requirement",
                    "entity_ids": ["req_1", "req_2"],
                    "new_status": "approved"
                },
                "description": "Update status for multiple entities"
            },
            {
                "name": "organization_onboarding",
                "params": {
                    "organization_name": "My Org",
                    "admin_email": "admin@example.com"
                },
                "description": "Complete organization setup"
            }
        ],
        "parameters": [
            "workflow (required - workflow name)",
            "parameters (dict - workflow-specific params)",
            "transaction_mode (bool, default=True)",
            "format_type (optional)"
        ],
        "features": [
            "Atomic transactions",
            "Multi-step orchestration",
            "Rollback on failure",
            "Idempotent operations"
        ],
        "auth_required": True
    },

    "query_tool": {
        "description": "Query and analyze data across multiple entity types with RAG capabilities",
        "query_types": [
            {
                "name": "search",
                "params": {
                    "query_type": "search",
                    "entities": ["project", "document"],
                    "search_term": "api"
                },
                "description": "Cross-entity text search"
            },
            {
                "name": "aggregate",
                "params": {
                    "query_type": "aggregate",
                    "entities": ["organization", "project"]
                },
                "description": "Summary statistics and counts"
            },
            {
                "name": "analyze",
                "params": {
                    "query_type": "analyze",
                    "entities": ["requirement"],
                    "conditions": {"status": "approved"}
                },
                "description": "Deep analysis with relationships"
            },
            {
                "name": "relationships",
                "params": {
                    "query_type": "relationships",
                    "entities": ["project"],
                    "conditions": {"entity_id": "..."}
                },
                "description": "Relationship analysis"
            },
            {
                "name": "rag_search",
                "params": {
                    "query_type": "rag_search",
                    "entities": ["requirement"],
                    "search_term": "user authentication flow",
                    "rag_mode": "semantic"
                },
                "description": "AI-powered semantic search with Vertex AI embeddings"
            },
            {
                "name": "similarity",
                "params": {
                    "query_type": "similarity",
                    "content": "Login system requirements",
                    "entity_type": "requirement"
                },
                "description": "Find content similar to provided text"
            }
        ],
        "rag_modes": [
            "auto (Automatically choose best mode)",
            "semantic (Vector similarity with embeddings)",
            "keyword (Traditional keyword search)",
            "hybrid (Combination of semantic + keyword)"
        ],
        "parameters": [
            "query_type (required)",
            "entities (list, required)",
            "conditions (dict, optional)",
            "projections (list, optional)",
            "search_term (optional)",
            "limit (optional)",
            "format_type (optional)",
            "rag_mode (optional, default='auto')",
            "similarity_threshold (float, default=0.7)",
            "content (optional - for similarity search)",
            "entity_type (optional)",
            "exclude_id (optional)"
        ],
        "features": [
            "Cross-entity search",
            "RAG semantic search",
            "Vector embeddings (Vertex AI)",
            "Hybrid search modes",
            "Similarity matching",
            "Aggregations",
            "Relationship traversal"
        ],
        "auth_required": True
    }
}


def print_functionality_matrix():
    """Print comprehensive functionality matrix."""

    print("\n" + "="*100)
    print(" ATOMS MCP COMPREHENSIVE FUNCTIONALITY MATRIX")
    print("="*100)

    for tool_name, tool_info in TOOLS.items():
        print(f"\n{'='*100}")
        print(f"🔧 {tool_name.upper().replace('_', ' ')}")
        print(f"{'='*100}")

        print("\n📝 Description:")
        print(f"   {tool_info['description']}")

        print(f"\n🔐 Authentication: {'Required ✅' if tool_info.get('auth_required') else 'Optional ❌'}")

        if "operations" in tool_info:
            print("\n⚙️  Operations:")
            for op in tool_info["operations"]:
                print(f"\n   • {op['name'].upper()}")
                print(f"     └─ {op['description']}")
                params_str = json.dumps(op["params"], indent=11)
                # Skip the first opening brace and newline
                params_display = params_str.split("\n", 1)[1] if "\n" in params_str else params_str
                print(f"     └─ Example params: {params_display}")

        if "workflows" in tool_info:
            print("\n🔄 Workflows:")
            for wf in tool_info["workflows"]:
                print(f"\n   • {wf['name'].upper()}")
                print(f"     └─ {wf['description']}")
                params_str = json.dumps(wf["params"], indent=11)
                params_display = params_str.split("\n", 1)[1] if "\n" in params_str else params_str
                print(f"     └─ Example params: {params_display}")

        if "query_types" in tool_info:
            print("\n🔍 Query Types:")
            for qt in tool_info["query_types"]:
                print(f"\n   • {qt['name'].upper()}")
                print(f"     └─ {qt['description']}")
                params_str = json.dumps(qt["params"], indent=11)
                params_display = params_str.split("\n", 1)[1] if "\n" in params_str else params_str
                print(f"     └─ Example params: {params_display}")

        if "entity_types" in tool_info:
            print("\n📦 Supported Entity Types:")
            for et in tool_info["entity_types"]:
                print(f"   • {et}")

        if "relationship_types" in tool_info:
            print("\n🔗 Supported Relationship Types:")
            for rt in tool_info["relationship_types"]:
                print(f"   • {rt}")

        if "rag_modes" in tool_info:
            print("\n🤖 RAG Search Modes:")
            for mode in tool_info["rag_modes"]:
                print(f"   • {mode}")

        if "features" in tool_info:
            print("\n✨ Features:")
            for feat in tool_info["features"]:
                print(f"   • {feat}")

        print("\n📋 Parameters:")
        for param in tool_info["parameters"]:
            print(f"   • {param}")

    # Summary table
    print(f"\n\n{'='*100}")
    print(" SUMMARY TABLE")
    print(f"{'='*100}\n")

    print(f"{'Tool':<25} {'Operations':<15} {'Auth Required':<15} {'Key Features':<45}")
    print(f"{'-'*100}")

    for tool_name, tool_info in TOOLS.items():
        op_count = len(tool_info.get("operations", tool_info.get("workflows", tool_info.get("query_types", []))))
        auth = "Yes ✅" if tool_info.get("auth_required") else "No ❌"
        features = ", ".join(tool_info.get("features", ["N/A"])[:2])
        if len(features) > 42:
            features = features[:39] + "..."

        print(f"{tool_name:<25} {op_count:<15} {auth:<15} {features:<45}")

    print(f"\n{'='*100}")

    # Save to JSON
    output_file = f"atoms_functionality_matrix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, "w") as f:
        json.dump(TOOLS, f, indent=2)

    print(f"\n✅ Full matrix saved to: {output_file}")
    print(f"{'='*100}\n")


if __name__ == "__main__":
    print_functionality_matrix()
