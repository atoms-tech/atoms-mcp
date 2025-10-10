"""Workflow execution tool for complex multi-step operations."""

from __future__ import annotations

import asyncio
from typing import Any

from utils.logging_setup import get_logger

try:
    from .base import ToolBase
except ImportError:
    from tools.base import ToolBase

logger = get_logger(__name__)


class WorkflowExecutor(ToolBase):
    """Executes complex workflows with multiple steps."""

    def __init__(self):
        super().__init__()

    async def _setup_project_workflow(self, params: dict[str, Any]) -> dict[str, Any]:
        """Setup a new project with initial structure."""
        try:
            from .entity import _entity_manager
        except ImportError:
            from tools.entity import _entity_manager
        try:
            from .relationship import _relationship_manager
        except ImportError:
            from tools.relationship import _relationship_manager

        results = []
        logger.info("🚀 Starting setup_project workflow")

        # Validate required parameters
        required_params = ["name", "organization_id"]
        missing = [p for p in required_params if p not in params]
        if missing:
            raise ValueError(f"Missing required parameters: {missing}")

        # Verify user has access to organization
        org_id = params["organization_id"]
        try:
            org = await self._db_get_single("organizations", filters={"id": org_id, "is_deleted": False})
            if not org:
                raise ValueError(f"Organization '{org_id}' not found")
            logger.info(f"✅ Validated organization: {org['name']}")
        except Exception as e:
            logger.error(f"❌ Organization validation failed: {e}")
            raise ValueError(f"Cannot access organization: {e}")

        # Step 1: Create project
        logger.info("📝 Step 1: Creating project...")
        try:
            project_data = {
                "name": params["name"],
                "description": params.get("description", ""),
                "organization_id": org_id
            }

            project = await _entity_manager.create_entity("project", project_data)
            results.append({"step": "create_project", "status": "success", "result": project})
            logger.info(f"✅ Step 1: Project created - {project['id']}")
        except Exception as e:
            logger.error(f"❌ Step 1 failed: {e}")
            results.append({"step": "create_project", "status": "failed", "error": str(e)})
            raise

        # Step 2: Add creator as project admin
        if params.get("add_creator_as_admin", True):
            logger.info("👤 Step 2: Adding creator as admin...")
            try:
                user_id = self._get_user_id()
                if not user_id:
                    raise ValueError("User ID not available in context for adding creator as admin")
                member_result = await _relationship_manager.link_entities(
                    "member",
                    {"type": "project", "id": project["id"]},
                    {"type": "user", "id": user_id},
                    {"role": "admin"},
                    source_context=org_id
                )
                results.append({"step": "add_creator_member", "status": "success", "result": member_result})
                logger.info("✅ Step 2: Creator added as admin")
            except Exception as e:
                logger.error(f"❌ Step 2 failed: {e}")
                results.append({"step": "add_creator_member", "status": "failed", "error": str(e)})
                # Non-critical - continue

        # Step 3: Create initial documents (parallel execution)
        if params.get("initial_documents"):
            logger.info(f"📄 Step 3: Creating {len(params['initial_documents'])} documents...")
            try:
                doc_tasks = []
                for doc_name in params["initial_documents"]:
                    doc_data = {
                        "name": doc_name,
                        "project_id": project["id"],
                        "description": f"Initial {doc_name.lower()} document"
                    }
                    doc_tasks.append(_entity_manager.create_entity("document", doc_data))

                # Execute in parallel
                docs = await asyncio.gather(*doc_tasks, return_exceptions=True)

                for i, doc in enumerate(docs):
                    if isinstance(doc, Exception):
                        logger.error(f"❌ Document '{params['initial_documents'][i]}' failed: {doc}")
                        results.append({"step": f"create_document_{params['initial_documents'][i]}", "status": "failed", "error": str(doc)})
                    else:
                        logger.info(f"✅ Document created: {doc['name']}")
                        results.append({"step": f"create_document_{doc['name']}", "status": "success", "result": doc})
            except Exception as e:
                logger.error(f"❌ Step 3 failed: {e}")
                results.append({"step": "create_documents", "status": "failed", "error": str(e)})

        # Step 4: Set up project workspace context
        logger.info("🎯 Step 4: Setting workspace context...")
        try:
            try:
                from .workspace import _workspace_manager
            except ImportError:
                from tools.workspace import _workspace_manager

            user_id = self._get_user_id()
            if not user_id:
                raise ValueError("User ID not available in context for setting workspace context")
            await _workspace_manager.set_context(
                user_id, "project", project["id"]
            )
            results.append({"step": "set_workspace_context", "status": "success", "result": "context_set"})
            logger.info("✅ Step 4: Workspace context set")
        except Exception as e:
            logger.error(f"❌ Step 4 failed: {e}")
            results.append({"step": "set_workspace_context", "status": "failed", "error": str(e)})
            # Non-critical - continue

        logger.info(f"🎉 Workflow complete: {len(results)} steps executed")

        return {
            "workflow": "setup_project",
            "project_id": project["id"],
            "steps_completed": len(results),
            "steps_successful": len([r for r in results if r.get("status") == "success"]),
            "results": results
        }

    async def _import_requirements_workflow(self, params: dict[str, Any]) -> dict[str, Any]:
        """Import requirements from external source."""
        try:
            from .entity import _entity_manager
        except ImportError:
            from tools.entity import _entity_manager

        results = []
        logger.info("🚀 Starting import_requirements workflow")

        # Validate required parameters
        required_params = ["document_id", "requirements"]
        missing = [p for p in required_params if p not in params]
        if missing:
            raise ValueError(f"Missing required parameters: {missing}")

        document_id = params["document_id"]
        requirements_data = params["requirements"]

        if not isinstance(requirements_data, list) or len(requirements_data) == 0:
            raise ValueError("'requirements' must be a non-empty list")

        # Validate document exists
        logger.info(f"📋 Validating document: {document_id}")
        try:
            document = await _entity_manager.read_entity("document", document_id)
            if not document:
                raise ValueError(f"Document {document_id} not found")
            logger.info(f"✅ Document validated: {document['name']}")
        except Exception as e:
            logger.error(f"❌ Document validation failed: {e}")
            raise

        # Import requirements in batch (with parallel execution)
        logger.info(f"📝 Importing {len(requirements_data)} requirements...")
        created_requirements = []

        for i, req_data in enumerate(requirements_data, 1):
            req_data["document_id"] = document_id
            req_data.setdefault("status", "active")
            req_data.setdefault("priority", "medium")

            try:
                req = await _entity_manager.create_entity("requirement", req_data)
                created_requirements.append(req)
                results.append({"step": f"import_requirement_{i}", "status": "success", "result": req})
                logger.info(f"✅ Requirement {i}/{len(requirements_data)}: {req_data.get('name', 'Unnamed')}")
            except Exception as e:
                logger.error(f"❌ Requirement {i} failed: {e}")
                results.append({"step": f"import_requirement_{i}", "status": "failed", "error": str(e)})

        logger.info(f"🎉 Import complete: {len(created_requirements)}/{len(requirements_data)} successful")

        return {
            "workflow": "import_requirements",
            "document_id": document_id,
            "total_requirements": len(requirements_data),
            "imported_count": len(created_requirements),
            "failed_count": len(requirements_data) - len(created_requirements),
            "results": results
        }

    async def _setup_test_matrix_workflow(self, params: dict[str, Any]) -> dict[str, Any]:
        """Set up test matrix for a project."""
        from .entity import _entity_manager
        from .relationship import _relationship_manager

        results = []
        project_id = params["project_id"]

        # Step 1: Get all requirements for the project (via documents)
        # First get all documents for the project
        documents = await _entity_manager.search_entities(
            "document",
            filters={"project_id": project_id, "is_deleted": False}
        )

        # Then get requirements from all documents in parallel
        if documents:
            req_tasks = [
                _entity_manager.search_entities(
                    "requirement",
                    filters={"document_id": doc["id"], "is_deleted": False}
                )
                for doc in documents
            ]
            doc_requirements = await asyncio.gather(*req_tasks, return_exceptions=True)

            # Flatten results
            requirements = []
            for reqs in doc_requirements:
                if not isinstance(reqs, Exception):
                    requirements.extend(reqs)
        else:
            requirements = []

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

    async def _bulk_status_update_workflow(self, params: dict[str, Any]) -> dict[str, Any]:
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

    async def _organization_onboarding_workflow(self, params: dict[str, Any]) -> dict[str, Any]:
        """Complete organization onboarding process."""
        try:
            from .entity import _entity_manager
            from .relationship import _relationship_manager
            from .workspace import _workspace_manager
        except ImportError:
            from tools.entity import _entity_manager
            from tools.relationship import _relationship_manager
            from tools.workspace import _workspace_manager

        results = []
        logger.info("🚀 Starting organization_onboarding workflow")

        # Validate required parameters
        if "name" not in params:
            raise ValueError("Missing required parameter: name")

        # Step 1: Create organization
        logger.info("🏢 Step 1: Creating organization...")
        try:
            org_data = {
                "name": params["name"],
                "slug": params.get("slug", params["name"].lower().replace(" ", "-")),
                "type": params.get("type", "team"),
                "description": params.get("description", "")
            }

            org = await _entity_manager.create_entity("organization", org_data)
            results.append({"step": "create_organization", "status": "success", "result": org})
            logger.info(f"✅ Step 1: Organization created - {org['id']}")
        except Exception as e:
            logger.error(f"❌ Step 1 failed: {e}")
            results.append({"step": "create_organization", "status": "failed", "error": str(e)})
            raise

        # Step 2: Add creator as admin
        logger.info("👤 Step 2: Adding creator as admin...")
        try:
            user_id = self._get_user_id()
            if not user_id:
                raise ValueError("User ID not available in context for adding creator as admin")
            member_result = await _relationship_manager.link_entities(
                "member",
                {"type": "organization", "id": org["id"]},
                {"type": "user", "id": user_id},
                {"role": "admin", "status": "active"}
            )
            results.append({"step": "add_admin_member", "status": "success", "result": member_result})
            logger.info("✅ Step 2: Creator added as admin")
        except Exception as e:
            logger.error(f"❌ Step 2 failed: {e}")
            results.append({"step": "add_admin_member", "status": "failed", "error": str(e)})
            # Non-critical - continue

        # Step 3: Create starter project
        if params.get("create_starter_project", True):
            logger.info("📁 Step 3: Creating starter project...")
            try:
                project_data = {
                    "name": "Getting Started",
                    "description": "Starter project for new organization",
                    "organization_id": org["id"]
                }
                project = await _entity_manager.create_entity("project", project_data)
                results.append({"step": "create_starter_project", "status": "success", "result": project})
                logger.info(f"✅ Step 3a: Starter project created - {project['id']}")

                # Add creator as project admin
                user_id = self._get_user_id()
                if not user_id:
                    raise ValueError("User ID not available in context for adding project admin")
                project_member = await _relationship_manager.link_entities(
                    "member",
                    {"type": "project", "id": project["id"]},
                    {"type": "user", "id": user_id},
                    {"role": "admin", "status": "active"},
                    source_context=org["id"]
                )
                results.append({"step": "add_project_admin", "status": "success", "result": project_member})
                logger.info("✅ Step 3b: Added as project admin")
            except Exception as e:
                logger.error(f"❌ Step 3 failed: {e}")
                results.append({"step": "create_starter_project", "status": "failed", "error": str(e)})
                # Non-critical - continue

        # Step 4: Set workspace context
        logger.info("🎯 Step 4: Setting workspace context...")
        try:
            user_id = self._get_user_id()
            if not user_id:
                raise ValueError("User ID not available in context for setting workspace context")
            await _workspace_manager.set_context(
                user_id, "organization", org["id"]
            )
            results.append({"step": "set_workspace_context", "status": "success", "result": "context_set"})
            logger.info("✅ Step 4: Workspace context set")
        except Exception as e:
            logger.error(f"❌ Step 4 failed: {e}")
            results.append({"step": "set_workspace_context", "status": "failed", "error": str(e)})

        logger.info(f"🎉 Onboarding complete: {len(results)} steps executed")

        return {
            "workflow": "organization_onboarding",
            "organization_id": org["id"],
            "steps_completed": len(results),
            "steps_successful": len([r for r in results if r.get("status") == "success"]),
            "results": results
        }


# Global executor instance
_workflow_executor = WorkflowExecutor()


async def workflow_execute(
    auth_token: str,
    workflow: str,
    parameters: dict[str, Any],
    transaction_mode: bool = True,
    format_type: str = "detailed"
) -> dict[str, Any]:
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
