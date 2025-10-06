#!/usr/bin/env python3
"""Hardcoded test cases for Atoms MCP tools.

This module contains predefined test cases for all Atoms MCP operations.
No LLM inference - all inputs are hardcoded for reproducible testing.
"""

from typing import Dict, List, Any
from datetime import datetime


class TestCases:
    """Comprehensive test cases for all Atoms MCP tools."""

    # Will be populated with actual IDs during test run
    created_org_id: str | None = None
    created_project_id: str | None = None
    created_document_id: str | None = None
    created_requirement_id: str | None = None

    @staticmethod
    def workspace_tool_cases() -> List[Dict[str, Any]]:
        """Test cases for workspace_tool."""
        return [
            {
                "name": "List workspaces",
                "tool": "workspace_tool",
                "params": {
                    "operation": "list_workspaces"
                },
                "expected": {
                    "has_organizations": None,  # Could be 0 or more
                    "has_context": True
                }
            },
            {
                "name": "Get current context",
                "tool": "workspace_tool",
                "params": {
                    "operation": "get_context"
                },
                "expected": {
                    "has_active_org": None,  # May or may not have
                    "has_recent_items": True
                }
            },
        ]

    @staticmethod
    def entity_tool_cases() -> List[Dict[str, Any]]:
        """Test cases for entity_tool."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        return [
            # LIST operations
            {
                "name": "List organizations",
                "tool": "entity_tool",
                "params": {
                    "entity_type": "organization",
                    "operation": "list"
                },
                "expected": {
                    "success": True,
                    "has_data": True
                }
            },
            {
                "name": "List projects",
                "tool": "entity_tool",
                "params": {
                    "entity_type": "project",
                    "operation": "list"
                },
                "expected": {
                    "success": True,
                    "has_data": None  # May have projects
                }
            },
            {
                "name": "List documents",
                "tool": "entity_tool",
                "params": {
                    "entity_type": "document",
                    "operation": "list"
                },
                "expected": {
                    "success": True,
                    "has_data": None
                }
            },
            {
                "name": "List requirements",
                "tool": "entity_tool",
                "params": {
                    "entity_type": "requirement",
                    "operation": "list"
                },
                "expected": {
                    "success": True,
                    "has_data": None
                }
            },
            # CREATE operations
            {
                "name": "Create organization (known RLS issue)",
                "tool": "entity_tool",
                "params": {
                    "entity_type": "organization",
                    "operation": "create",
                    "data": {
                        "name": f"Test Org {timestamp}",
                        "slug": f"test-org-{timestamp}",
                        "description": "Created by headless MCP test client"
                    }
                },
                "expected": {
                    "success": False,  # Known RLS issue
                    "error_contains": "permission"
                },
                "known_issue": True
            },
        ]

    @staticmethod
    def query_tool_cases() -> List[Dict[str, Any]]:
        """Test cases for query_tool."""
        return [
            # SEARCH operations
            {
                "name": "Keyword search for 'vehicle'",
                "tool": "query_tool",
                "params": {
                    "query_type": "search",
                    "entities": ["project", "document", "requirement"],
                    "search_term": "vehicle"
                },
                "expected": {
                    "success": True,
                    "has_results": None  # May find results
                }
            },
            {
                "name": "Keyword search for 'safety'",
                "tool": "query_tool",
                "params": {
                    "query_type": "search",
                    "entities": ["requirement", "document"],
                    "search_term": "safety"
                },
                "expected": {
                    "success": True,
                    "has_results": None
                }
            },
            # AGGREGATE operations
            {
                "name": "Aggregate stats for projects and documents",
                "tool": "query_tool",
                "params": {
                    "query_type": "aggregate",
                    "entities": ["organization", "project", "document"]
                },
                "expected": {
                    "success": True,
                    "has_stats": True
                }
            },
            # RAG SEARCH operations
            {
                "name": "RAG semantic search (known embedding error)",
                "tool": "query_tool",
                "params": {
                    "query_type": "rag_search",
                    "entities": ["requirement"],
                    "search_term": "safety system requirements",
                    "rag_mode": "semantic"
                },
                "expected": {
                    "success": False,  # Known embedding error
                    "error_contains": "NoneType"
                },
                "known_issue": True
            },
            {
                "name": "RAG keyword search",
                "tool": "query_tool",
                "params": {
                    "query_type": "rag_search",
                    "entities": ["document"],
                    "search_term": "testing procedures",
                    "rag_mode": "keyword"
                },
                "expected": {
                    "success": True,
                    "has_results": None
                }
            },
            {
                "name": "RAG hybrid search",
                "tool": "query_tool",
                "params": {
                    "query_type": "rag_search",
                    "entities": ["requirement", "document"],
                    "search_term": "performance requirements",
                    "rag_mode": "hybrid"
                },
                "expected": {
                    "success": True,
                    "has_results": None
                }
            },
        ]

    @staticmethod
    def relationship_tool_cases() -> List[Dict[str, Any]]:
        """Test cases for relationship_tool."""
        return [
            {
                "name": "List member relationships",
                "tool": "relationship_tool",
                "params": {
                    "operation": "list",
                    "relationship_type": "member",
                    "source": {
                        "type": "organization",
                        "id": "test-org-id"  # Will be replaced if org created
                    }
                },
                "expected": {
                    "success": None,  # Depends on org existence
                    "has_relationships": None
                },
                "skip_if_no_org": True
            },
        ]

    @staticmethod
    def workflow_tool_cases() -> List[Dict[str, Any]]:
        """Test cases for workflow_tool."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        return [
            {
                "name": "Setup project workflow (needs org_id)",
                "tool": "workflow_tool",
                "params": {
                    "workflow": "setup_project",
                    "parameters": {
                        "name": f"Test Workflow Project {timestamp}",
                        "description": "Created by workflow test",
                        "organization_id": "test-org-id"  # Will fail without org
                    }
                },
                "expected": {
                    "success": False,  # Will fail without valid org_id
                    "error_contains": "organization"
                },
                "skip_if_no_org": True
            },
        ]

    @classmethod
    def all_test_cases(cls) -> List[Dict[str, Any]]:
        """Get all test cases for all tools."""
        return (
            cls.workspace_tool_cases() +
            cls.entity_tool_cases() +
            cls.query_tool_cases() +
            cls.relationship_tool_cases() +
            cls.workflow_tool_cases()
        )

    @classmethod
    def get_cases_by_tool(cls, tool_name: str) -> List[Dict[str, Any]]:
        """Get test cases for a specific tool."""
        method_map = {
            "workspace_tool": cls.workspace_tool_cases,
            "entity_tool": cls.entity_tool_cases,
            "query_tool": cls.query_tool_cases,
            "relationship_tool": cls.relationship_tool_cases,
            "workflow_tool": cls.workflow_tool_cases,
        }

        method = method_map.get(tool_name)
        if not method:
            raise ValueError(f"Unknown tool: {tool_name}")

        return method()
