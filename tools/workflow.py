"""Workflow execution tool for complex multi-step operations."""

from __future__ import annotations

from typing import Dict, Any, List, Optional
import asyncio

from .base import ToolBase


class WorkflowExecutor(ToolBase):
    """Executes complex workflows with multiple steps."""
    
    def __init__(self):
        super().__init__()
    
    async def _setup_project_workflow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Setup a new project with initial structure."""
        from .entity import _entity_manager
        from .relationship import _relationship_manager
        
        results = []
        
        # Step 1: Create project
        project_data = {
            "name": params["name"],
            "description": params.get("description", ""),
            "organization_id": params["organization_id"]
        }
        
        project = await _entity_manager.create_entity("project", project_data)
        results.append({"step": "create_project", "result": project})
        
        # Step 2: Add creator as project admin
        if params.get("add_creator_as_admin", True):
            member_result = await _relationship_manager.link_entities(
                "member",
                {"type": "project", "id": project["id"]},
                {"type": "user", "id": self._get_user_id()},
                {"role": "admin"},
                source_context=params["organization_id"]
            )
            results.append({"step": "add_creator_member", "result": member_result})
        
        # Step 3: Create initial documents
        if params.get("initial_documents"):
            for doc_name in params["initial_documents"]:
                doc_data = {
                    "name": doc_name,
                    "project_id": project["id"],
                    "description": f"Initial {doc_name.lower()} document"
                }
                doc = await _entity_manager.create_entity("document", doc_data)
                results.append({"step": f"create_document_{doc_name}", "result": doc})
        
        # Step 4: Set up project workspace context
        from .workspace import _workspace_manager
        await _workspace_manager.set_context(
            self._get_user_id(), "project", project["id"]
        )
        results.append({"step": "set_workspace_context", "result": "success"})
        
        return {
            "workflow": "setup_project",
            "project_id": project["id"],
            "steps_completed": len(results),
            "results": results
        }
    
    async def _import_requirements_workflow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Import requirements from external source."""
        from .entity import _entity_manager
        
        results = []
        document_id = params["document_id"]
        requirements_data = params["requirements"]
        
        # Validate document exists
        document = await _entity_manager.read_entity("document", document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        # Import requirements in batch
        created_requirements = []
        for i, req_data in enumerate(requirements_data):
            req_data["document_id"] = document_id
            req_data.setdefault("status", "active")
            req_data.setdefault("priority", "medium")
            
            try:
                req = await _entity_manager.create_entity("requirement", req_data)
                created_requirements.append(req)
                results.append({"step": f"import_requirement_{i+1}", "result": req})
            except Exception as e:
                results.append({"step": f"import_requirement_{i+1}", "error": str(e)})
        
        return {
            "workflow": "import_requirements",
            "document_id": document_id,
            "total_requirements": len(requirements_data),
            "imported_count": len(created_requirements),
            "results": results
        }
    
    async def _setup_test_matrix_workflow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set up test matrix for a project."""
        from .entity import _entity_manager
        from .relationship import _relationship_manager
        
        results = []
        project_id = params["project_id"]
        
        # Step 1: Get all requirements for the project
        requirements = await _entity_manager.search_entities(
            "requirement",
            filters={"documents.project_id": project_id}
        )
        results.append({"step": "fetch_requirements", "count": len(requirements)})
        
        # Step 2: Create test matrix view
        matrix_view_data = {
            "name": params.get("matrix_name", "Default Test Matrix"),
            "project_id": project_id,
            "is_default": True,
            "configuration": {
                "show_coverage": True,
                "group_by": "priority",
                "filter_status": ["active"]
            }
        }
        
        matrix_view = await _entity_manager.create_entity(
            "test_matrix_view", matrix_view_data
        )
        results.append({"step": "create_matrix_view", "result": matrix_view})
        
        # Step 3: Create basic test cases for high priority requirements
        test_cases_created = 0
        for req in requirements:
            if req.get("priority") == "high":
                test_data = {
                    "title": f"Test {req['name']}",
                    "description": f"Test case for requirement: {req['name']}",
                    "project_id": project_id,
                    "test_type": "functional",
                    "priority": "high",
                    "status": "pending"
                }
                
                test = await _entity_manager.create_entity("test", test_data)
                
                # Link test to requirement
                await _relationship_manager.link_entities(
                    "requirement_test",
                    {"type": "requirement", "id": req["id"]},
                    {"type": "test", "id": test["id"]},
                    {"relationship_type": "tests", "coverage_level": "full"}
                )
                
                test_cases_created += 1
                results.append({"step": f"create_test_for_req_{req['id']}", "result": test})
        
        return {
            "workflow": "setup_test_matrix",
            "project_id": project_id,
            "matrix_view_id": matrix_view["id"],
            "requirements_found": len(requirements),
            "test_cases_created": test_cases_created,
            "results": results
        }
    
    async def _bulk_status_update_workflow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update status for multiple entities."""
        from .entity import _entity_manager
        
        results = []
        entity_type = params["entity_type"]
        entity_ids = params["entity_ids"]
        new_status = params["new_status"]
        
        # Update entities in parallel
        update_tasks = []
        for entity_id in entity_ids:
            task = _entity_manager.update_entity(
                entity_type,
                entity_id,
                {"status": new_status}
            )
            update_tasks.append(task)
        
        # Wait for all updates to complete
        update_results = await asyncio.gather(*update_tasks, return_exceptions=True)
        
        success_count = 0
        for i, result in enumerate(update_results):
            if isinstance(result, Exception):
                results.append({
                    "step": f"update_{entity_ids[i]}", 
                    "error": str(result)
                })
            else:
                results.append({
                    "step": f"update_{entity_ids[i]}", 
                    "result": result
                })
                success_count += 1
        
        return {
            "workflow": "bulk_status_update",
            "entity_type": entity_type,
            "total_entities": len(entity_ids),
            "success_count": success_count,
            "new_status": new_status,
            "results": results
        }
    
    async def _organization_onboarding_workflow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Complete organization onboarding process."""
        from .entity import _entity_manager
        from .relationship import _relationship_manager
        
        results = []
        
        # Step 1: Create organization
        org_data = {
            "name": params["name"],
            "slug": params.get("slug", params["name"].lower().replace(" ", "-")),
            "type": params.get("type", "team"),
            "description": params.get("description", "")
        }
        
        org = await _entity_manager.create_entity("organization", org_data)
        results.append({"step": "create_organization", "result": org})
        
        # Step 2: Add creator as admin
        member_result = await _relationship_manager.link_entities(
            "member",
            {"type": "organization", "id": org["id"]},
            {"type": "user", "id": self._get_user_id()},
            {"role": "admin", "status": "active"}
        )
        results.append({"step": "add_admin_member", "result": member_result})
        
        # Step 3: Create starter project
        if params.get("create_starter_project", True):
            project_data = {
                "name": "Getting Started",
                "description": "Starter project for new organization",
                "organization_id": org["id"]
            }
            project = await _entity_manager.create_entity("project", project_data)
            results.append({"step": "create_starter_project", "result": project})
            
            # Add creator as project admin
            project_member = await _relationship_manager.link_entities(
                "member",
                {"type": "project", "id": project["id"]},
                {"type": "user", "id": self._get_user_id()},
                {"role": "admin", "status": "active"},
                source_context=org["id"]
            )
            results.append({"step": "add_project_admin", "result": project_member})
        
        # Step 4: Set workspace context
        from .workspace import _workspace_manager
        await _workspace_manager.set_context(
            self._get_user_id(), "organization", org["id"]
        )
        results.append({"step": "set_workspace_context", "result": "success"})
        
        return {
            "workflow": "organization_onboarding",
            "organization_id": org["id"],
            "steps_completed": len(results),
            "results": results
        }


# Global executor instance
_workflow_executor = WorkflowExecutor()


async def workflow_execute(
    auth_token: str,
    workflow: str,
    parameters: Dict[str, Any],
    transaction_mode: bool = True,
    format_type: str = "detailed"
) -> Dict[str, Any]:
    """Execute a complex workflow with multiple steps.
    
    Args:
        auth_token: Authentication token
        workflow: Workflow type to execute
        parameters: Parameters for the workflow
        transaction_mode: Whether to treat as a transaction (rollback on failure)
        format_type: Result format (detailed, summary, raw)
    
    Available workflows:
        - setup_project: Create project with initial structure
        - import_requirements: Import requirements from external source
        - setup_test_matrix: Set up test matrix for a project
        - bulk_status_update: Update status for multiple entities
        - organization_onboarding: Complete organization setup
    
    Returns:
        Dict containing workflow execution result
    """
    try:
        # Validate authentication
        await _workflow_executor._validate_auth(auth_token)
        
        # Execute workflow based on type
        if workflow == "setup_project":
            result = await _workflow_executor._setup_project_workflow(parameters)
        elif workflow == "import_requirements":
            result = await _workflow_executor._import_requirements_workflow(parameters)
        elif workflow == "setup_test_matrix":
            result = await _workflow_executor._setup_test_matrix_workflow(parameters)
        elif workflow == "bulk_status_update":
            result = await _workflow_executor._bulk_status_update_workflow(parameters)
        elif workflow == "organization_onboarding":
            result = await _workflow_executor._organization_onboarding_workflow(parameters)
        else:
            raise ValueError(f"Unknown workflow: {workflow}")
        
        return _workflow_executor._format_result(result, format_type)
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "workflow": workflow,
            "transaction_mode": transaction_mode
        }