"""Workflow execution tool for complex multi-step operations."""

from __future__ import annotations

import asyncio
from typing import Any, NoReturn

from utils.logging_setup import get_logger

try:
    from .base import ToolBase
except ImportError:
    from tools.base import ToolBase

try:
    from .entity import _entity_manager
    from .relationship import _relationship_manager
    from .workspace import _workspace_manager
except ImportError:
    from tools.entity import _entity_manager
    from tools.relationship import _relationship_manager
    from tools.workspace import _workspace_manager

logger = get_logger(__name__)


class WorkflowExecutor(ToolBase):
    """Executes complex workflows with multiple steps."""

    def __init__(self):
        super().__init__()

    async def _setup_project_workflow(self, params: dict[str, Any]) -> dict[str, Any]:
        """Setup a new project with initial structure."""
        results = []
        logger.info("🚀 Starting setup_project workflow")

        self._require_params(params, ["name", "organization_id"])
        org_id = params["organization_id"]
        await self._get_validated_organization(org_id)

        project = await self._create_project_entity(
            {
                "name": params["name"],
                "description": params.get("description", ""),
                "organization_id": org_id,
            },
            step_name="create_project",
            start_message="📝 Step 1: Creating project...",
            success_message="✅ Step 1: Project created - {project_id}",
            failure_message="❌ Step 1 failed",
            results=results,
        )

        if params.get("add_creator_as_admin", True):
            await self._link_creator_member(
                target_type="project",
                target_id=project["id"],
                metadata={"role": "admin"},
                context_description="adding creator as project admin",
                step_name="add_creator_member",
                start_message="👤 Step 2: Adding creator as admin...",
                success_message="✅ Step 2: Creator added as admin",
                failure_message="❌ Step 2 failed",
                results=results,
                source_context=org_id,
            )

        await self._create_initial_documents_step(
            project_id=project["id"],
            document_names=params.get("initial_documents"),
            results=results,
        )

        await self._set_workspace_context_step(
            context_type="project",
            entity_id=project["id"],
            step_name="set_workspace_context",
            success_message="✅ Step 4: Workspace context set",
            failure_message="❌ Step 4 failed",
            results=results,
        )

        logger.info("🎉 Workflow complete: %s steps executed", len(results))

        return {
            "workflow": "setup_project",
            "project_id": project["id"],
            "steps_completed": len(results),
            "steps_successful": len([r for r in results if r.get("status") == "success"]),
            "results": results,
        }

    async def _import_requirements_workflow(self, params: dict[str, Any]) -> dict[str, Any]:
        """Import requirements from external source."""
        results = []
        logger.info("🚀 Starting import_requirements workflow")

        self._require_params(params, ["document_id", "requirements"])

        document_id = params["document_id"]
        requirements_data = params["requirements"]

        if not isinstance(requirements_data, list) or len(requirements_data) == 0:
            raise ValueError("'requirements' must be a non-empty list")

        # Validate document exists
        logger.info("📋 Validating document: %s", document_id)
        try:
            document = await _entity_manager.read_entity("document", document_id)
        except Exception:
            logger.exception("❌ Document validation failed")
            raise

        if not document:
            raise ValueError(f"Document {document_id} not found")
        logger.info("✅ Document validated: %s", document["name"])

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
                logger.exception("❌ Requirement %s failed", i)
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
            requirements: list[dict[str, Any]] = []
            for reqs in doc_requirements:
                if not isinstance(reqs, Exception) and isinstance(reqs, list):
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
            elif isinstance(result, dict):
                results.append({
                    "step": f"update_{entity_ids[i]}",
                    "result": str(result)
                })
            else:
                results.append({
                    "step": f"update_{entity_ids[i]}",
                    "error": f"Unexpected result type: {type(result)}"
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
        results = []
        logger.info("🚀 Starting organization_onboarding workflow")

        self._require_params(params, ["name"])

        org = await self._create_organization_step(params, results)

        await self._link_creator_member(
            target_type="organization",
            target_id=org["id"],
            metadata={"role": "admin", "status": "active"},
            context_description="adding creator as organization admin",
            step_name="add_admin_member",
            start_message="👤 Step 2: Adding creator as admin...",
            success_message="✅ Step 2: Creator added as admin",
            failure_message="❌ Step 2 failed",
            results=results,
        )

        if params.get("create_starter_project", True):
            project = await self._create_project_entity(
                {
                    "name": "Getting Started",
                    "description": "Starter project for new organization",
                    "organization_id": org["id"],
                },
                step_name="create_starter_project",
                start_message="📁 Step 3: Creating starter project...",
                success_message="✅ Step 3a: Starter project created - {project_id}",
                failure_message="❌ Step 3 failed",
                results=results,
                raise_on_failure=False,
            )

            if project:
                await self._link_creator_member(
                    target_type="project",
                    target_id=project["id"],
                    metadata={"role": "admin", "status": "active"},
                    context_description="adding creator as project admin",
                    step_name="add_project_admin",
                    start_message="👤 Step 3b: Adding creator as project admin...",
                    success_message="✅ Step 3b: Added as project admin",
                    failure_message="❌ Step 3 failed",
                    results=results,
                    source_context=org["id"],
                )

        await self._set_workspace_context_step(
            context_type="organization",
            entity_id=org["id"],
            step_name="set_workspace_context",
            success_message="✅ Step 4: Workspace context set",
            failure_message="❌ Step 4 failed",
            results=results,
        )

        logger.info("🎉 Onboarding complete: %s steps executed", len(results))

        return {
            "workflow": "organization_onboarding",
            "organization_id": org["id"],
            "steps_completed": len(results),
            "steps_successful": len([r for r in results if r.get("status") == "success"]),
            "results": results,
        }

    # Helper methods -------------------------------------------------

    @staticmethod
    def _require_params(params: dict[str, Any], required_params: list[str]) -> None:
        missing = [param for param in required_params if param not in params]
        if missing:
            raise ValueError(f"Missing required parameters: {missing}")

    def _require_user_id(self, context: str) -> str:
        user_id = self._get_user_id()
        if not user_id:
            raise ValueError(f"User ID not available in context for {context}")
        return user_id

    async def _get_validated_organization(self, org_id: str) -> dict[str, Any]:
        try:
            org = await self._db_get_single("organizations", filters={"id": org_id, "is_deleted": False})
        except Exception as exc:
            logger.exception("❌ Organization validation failed")
            raise ValueError(f"Cannot access organization: {exc}") from exc

        if not org:
            raise ValueError(f"Organization '{org_id}' not found")

        logger.info("✅ Validated organization: %s", org.get("name", org_id))
        return org

    async def _create_project_entity(
        self,
        project_data: dict[str, Any],
        *,
        step_name: str,
        start_message: str,
        success_message: str,
        failure_message: str,
        results: list[dict[str, Any]],
        raise_on_failure: bool = True,
    ) -> dict[str, Any] | None:
        logger.info(start_message)
        try:
            project = await _entity_manager.create_entity("project", project_data)
        except Exception as exc:
            logger.exception(failure_message)
            results.append({"step": step_name, "status": "failed", "error": str(exc)})
            if raise_on_failure:
                raise
            return None

        results.append({"step": step_name, "status": "success", "result": project})
        logger.info(success_message.format(project_id=project.get("id"), project=project))
        return project

    async def _link_creator_member(
        self,
        *,
        target_type: str,
        target_id: str,
        metadata: dict[str, Any],
        context_description: str,
        step_name: str,
        start_message: str,
        success_message: str,
        failure_message: str,
        results: list[dict[str, Any]],
        source_context: str | None = None,
    ) -> None:
        logger.info(start_message)
        try:
            user_id = self._require_user_id(context_description)
            member_result = await _relationship_manager.link_entities(
                "member",
                {"type": target_type, "id": target_id},
                {"type": "user", "id": user_id},
                metadata,
                source_context=source_context,
            )
        except Exception as exc:
            logger.exception(failure_message)
            results.append({"step": step_name, "status": "failed", "error": str(exc)})
            return

        results.append({"step": step_name, "status": "success", "result": member_result})
        logger.info(success_message)

    async def _create_initial_documents_step(
        self,
        *,
        project_id: str,
        document_names: list[str] | None,
        results: list[dict[str, Any]],
    ) -> None:
        if not document_names:
            return

        logger.info("📄 Step 3: Creating %d documents...", len(document_names))
        try:
            doc_tasks = [
                _entity_manager.create_entity(
                    "document",
                    {
                        "name": doc_name,
                        "project_id": project_id,
                        "description": f"Initial {doc_name.lower()} document",
                    },
                )
                for doc_name in document_names
            ]
            docs = await asyncio.gather(*doc_tasks, return_exceptions=True)
        except Exception as exc:
            logger.exception("❌ Step 3 failed")
            results.append({"step": "create_documents", "status": "failed", "error": str(exc)})
            return

        for index, doc in enumerate(docs):
            doc_name = document_names[index]
            if isinstance(doc, Exception):
                step_key = f"create_document_{doc_name}"
                logger.error("❌ Document '%s' failed: %s", doc_name, doc)
                results.append({"step": step_key, "status": "failed", "error": str(doc)})
            elif isinstance(doc, dict):
                step_key = f"create_document_{doc.get('name', doc_name)}"
                logger.info("✅ Document created: %s", doc.get("name", "unknown"))
                results.append({"step": step_key, "status": "success", "result": doc})
            else:
                step_key = f"create_document_{doc_name}"
                logger.error("❌ Document '%s' returned unexpected type: %s", doc_name, type(doc))
                results.append({"step": step_key, "status": "failed", "error": f"Unexpected type: {type(doc)}"})

    async def _set_workspace_context_step(
        self,
        *,
        context_type: str,
        entity_id: str,
        step_name: str,
        success_message: str,
        failure_message: str,
        results: list[dict[str, Any]],
    ) -> None:
        logger.info("🎯 Setting %s workspace context...", context_type)
        try:
            user_id = self._require_user_id(f"setting workspace context for {context_type}")
            await _workspace_manager.set_context(user_id, context_type, entity_id)
        except Exception as exc:
            logger.exception(failure_message)
            results.append({"step": step_name, "status": "failed", "error": str(exc)})
            return

        results.append({"step": step_name, "status": "success", "result": "context_set"})
        logger.info(success_message)

    async def _create_organization_step(
        self,
        params: dict[str, Any],
        results: list[dict[str, Any]],
    ) -> dict[str, Any]:
        logger.info("🏢 Step 1: Creating organization...")
        org_data = {
            "name": params["name"],
            "slug": params.get("slug", params["name"].lower().replace(" ", "-")),
            "type": params.get("type", "team"),
            "description": params.get("description", ""),
        }

        try:
            org = await _entity_manager.create_entity("organization", org_data)
        except Exception as exc:
            logger.exception("❌ Step 1 failed")
            results.append({"step": "create_organization", "status": "failed", "error": str(exc)})
            raise

        results.append({"step": "create_organization", "status": "success", "result": org})
        logger.info("✅ Step 1: Organization created - %s", org.get("id"))
        return org


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
    def _raise_unknown_workflow(requested_workflow: str) -> NoReturn:
        raise ValueError(f"Unknown workflow: {requested_workflow}")

    workflow_handlers = {
        "setup_project": _workflow_executor._setup_project_workflow,
        "import_requirements": _workflow_executor._import_requirements_workflow,
        "setup_test_matrix": _workflow_executor._setup_test_matrix_workflow,
        "bulk_status_update": _workflow_executor._bulk_status_update_workflow,
        "organization_onboarding": _workflow_executor._organization_onboarding_workflow,
    }

    try:
        # Validate authentication
        await _workflow_executor._validate_auth(auth_token)

        handler = workflow_handlers.get(workflow)
        if not handler:
            _raise_unknown_workflow(workflow)

        result = await handler(parameters)
        return _workflow_executor._format_result(result, format_type)

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "workflow": workflow,
            "transaction_mode": transaction_mode
        }
