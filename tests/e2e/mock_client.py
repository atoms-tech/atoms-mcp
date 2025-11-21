"""Mock MCP client for harness-based E2E testing.

This module provides a mock implementation of the MCP client for testing
complex workflows without requiring real HTTP connections or a deployed server.
"""

from typing import Any, Dict, List, Optional
from unittest.mock import Mock, AsyncMock
import uuid
import asyncio
from datetime import datetime


class MockMcpClient:
    """Mock MCP client for testing complex workflows.
    
    This client simulates the MCP server behavior for testing parallel
    operations, error recovery, and complex state transitions.
    """
    
    def __init__(self):
        """Initialize mock client with empty state."""
        self.entities = {}  # Store created entities by ID
        self.relationships = []  # Store relationships
        self.operation_count = 0
        self.error_count = 0
        self.success_count = 0
        
    async def call_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Mock tool call handler.
        
        Args:
            tool_name: Name of the tool to call (entity_tool, relationship_tool)
            args: Arguments for the tool call
            
        Returns:
            Result dictionary with success status and data
        """
        self.operation_count += 1
        
        try:
            if tool_name == "entity_tool":
                return await self._handle_entity_operation(args)
            elif tool_name == "relationship_tool":
                return await self._handle_relationship_operation(args)
            elif tool_name == "workspace_tool":
                return await self._handle_workspace_operation(args)
            elif tool_name == "data_query":
                return await self._handle_data_query(args)
            elif tool_name == "workflow_execute":
                return await self._handle_workflow(args)
            else:
                self.error_count += 1
                return {"success": False, "error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            self.error_count += 1
            return {"success": False, "error": str(e)}
    
    async def _handle_entity_operation(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle entity CRUD operations.
        
        Supports: create, read, update, delete, list
        """
        operation = args.get("operation")
        entity_type = args.get("entity_type")
        data = args.get("data", {})
        entity_id = args.get("entity_id") or data.get("id")
        
        # Simulate some latency
        await asyncio.sleep(0.01)
        
        if operation == "create":
            entity_id = str(uuid.uuid4())
            entity = {
                "id": entity_id,
                "type": entity_type,
                "created_at": datetime.utcnow().isoformat(),
                **data
            }
            self.entities[entity_id] = entity
            self.success_count += 1
            return {
                "success": True,
                "data": entity
            }
        
        elif operation == "read":
            if entity_id in self.entities:
                self.success_count += 1
                return {
                    "success": True,
                    "data": self.entities[entity_id]
                }
            self.error_count += 1
            return {"success": False, "error": "Entity not found"}
        
        elif operation == "update":
            if entity_id in self.entities:
                updated_entity = self.entities[entity_id].copy()
                updated_entity.update(data)
                updated_entity["updated_at"] = datetime.utcnow().isoformat()
                self.entities[entity_id] = updated_entity
                self.success_count += 1
                return {
                    "success": True,
                    "data": updated_entity
                }
            self.error_count += 1
            return {"success": False, "error": "Entity not found"}
        
        elif operation == "delete":
            if entity_id in self.entities:
                deleted = self.entities.pop(entity_id)
                self.success_count += 1
                return {
                    "success": True,
                    "data": {"id": entity_id, "deleted": True}
                }
            self.error_count += 1
            return {"success": False, "error": "Entity not found"}
        
        elif operation == "list":
            entity_type_filter = data.get("entity_type") or entity_type
            results = [
                e for e in self.entities.values()
                if not entity_type_filter or e.get("type") == entity_type_filter
            ]
            self.success_count += 1
            return {
                "success": True,
                "data": results,
                "count": len(results)
            }
        
        self.error_count += 1
        return {"success": False, "error": f"Unknown operation: {operation}"}
    
    async def _handle_relationship_operation(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle relationship operations.
        
        Supports: create, read, delete, list
        """
        operation = args.get("operation")
        
        if operation == "create":
            rel_id = str(uuid.uuid4())
            relationship = {
                "id": rel_id,
                "created_at": datetime.utcnow().isoformat(),
                **args
            }
            self.relationships.append(relationship)
            self.success_count += 1
            return {
                "success": True,
                "data": relationship
            }
        
        elif operation == "read":
            rel_id = args.get("id")
            for rel in self.relationships:
                if rel.get("id") == rel_id:
                    self.success_count += 1
                    return {
                        "success": True,
                        "data": rel
                    }
            self.error_count += 1
            return {"success": False, "error": "Relationship not found"}
        
        elif operation == "delete":
            rel_id = args.get("id")
            for i, rel in enumerate(self.relationships):
                if rel.get("id") == rel_id:
                    self.relationships.pop(i)
                    self.success_count += 1
                    return {
                        "success": True,
                        "data": {"id": rel_id, "deleted": True}
                    }
            self.error_count += 1
            return {"success": False, "error": "Relationship not found"}
        
        elif operation == "list":
            source_type = args.get("source_type")
            results = [
                r for r in self.relationships
                if not source_type or r.get("source_type") == source_type
            ]
            self.success_count += 1
            return {
                "success": True,
                "data": results
            }
        
        self.error_count += 1
        return {"success": False, "error": f"Unknown operation: {operation}"}

    async def _handle_workspace_operation(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Provide basic workspace context/default responses."""
        operation = args.get("operation")
        context_type = args.get("context_type") or "organization"
        entity_id = args.get("entity_id")

        if operation == "get_context":
            return {
                "success": True,
                "data": {
                    "context_type": context_type,
                    "entity_id": entity_id or str(uuid.uuid4()),
                    "context": {
                        "organization": {
                            "id": entity_id or str(uuid.uuid4()),
                            "name": f"Mock {context_type.title()}"
                        }
                    }
                }
            }
        elif operation == "set_context":
            return {
                "success": True,
                "data": {
                    "context_type": context_type,
                    "entity_id": entity_id
                }
            }
        elif operation == "get_defaults":
            return {
                "success": True,
                "data": {
                    "context_type": context_type,
                    "defaults": {
                        "view_mode": "hierarchy",
                        "limit": 25,
                        "filters": {}
                    }
                }
            }
        elif operation == "list_workspaces":
            return {
                "success": True,
                "data": [
                    {
                        "id": str(uuid.uuid4()),
                        "type": "organization",
                        "name": "Mock Org"
                    },
                    {
                        "id": str(uuid.uuid4()),
                        "type": "project",
                        "name": "Mock Project"
                    }
                ]
            }

        return {"success": True, "data": {}}

    async def _handle_data_query(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Return deterministic mock data for search and aggregation tests."""
        operation = args.get("operation") or "search"
        limit = args.get("limit", 10)

        if operation == "aggregate":
            return {
                "success": True,
                "data": [{"label": "mock", "count": limit}],
                "count": limit
            }

        if operation == "count_all":
            return {"success": True, "data": {"count": limit}}

        if operation == "find_similar":
            return {
                "success": True,
                "data": [
                    {"id": str(uuid.uuid4()), "score": 0.91 - i * 0.02}
                    for i in range(min(limit, 5))
                ]
            }

        # Default search response
        return {
            "success": True,
            "data": [
                {
                    "id": str(uuid.uuid4()),
                    "title": f"Mock Result {i+1}",
                    "score": 0.8 - i * 0.05
                }
                for i in range(min(limit, 5))
            ]
        }

    async def _handle_workflow(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate workflow execution."""
        workflow_name = args.get("workflow_name", "workflow")
        return {
            "success": True,
            "data": {
                "workflow": workflow_name,
                "status": "completed",
                "steps_executed": args.get("operations") or args.get("steps") or []
            }
        }

    async def entity_tool(self, **kwargs) -> Dict[str, Any]:
        return await self.call_tool("entity_tool", kwargs)

    async def relationship_tool(self, **kwargs) -> Dict[str, Any]:
        return await self.call_tool("relationship_tool", kwargs)

    async def workspace_tool(self, **kwargs) -> Dict[str, Any]:
        return await self.call_tool("workspace_tool", kwargs)

    async def data_query(self, **kwargs) -> Dict[str, Any]:
        return await self.call_tool("data_query", kwargs)

    async def workflow_execute(self, **kwargs) -> Dict[str, Any]:
        return await self.call_tool("workflow_execute", kwargs)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get operation statistics."""
        return {
            "total_operations": self.operation_count,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "total_entities": len(self.entities),
            "total_relationships": len(self.relationships),
            "success_rate": (
                self.success_count / self.operation_count
                if self.operation_count > 0 else 0
            )
        }
    
    def reset(self):
        """Reset client state for next test."""
        self.entities = {}
        self.relationships = []
        self.operation_count = 0
        self.error_count = 0
        self.success_count = 0
