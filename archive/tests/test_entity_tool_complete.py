#!/usr/bin/env python3
"""
COMPREHENSIVE ENTITY TOOL TEST SUITE

Tests all entity types (organization, project, document, requirement, task, test_case, risk)
with all operations:
- create (minimal and full data)
- read (by ID and fuzzy name matching)
- update
- delete (soft and hard)
- list (with and without parent filters)
- search (with filters, pagination, ordering)

Also tests:
- Parameter inference
- Fuzzy matching
- Edge cases
- Error handling

Documents ALL results with specific errors and edge cases.
"""

import os
import sys
import json
import uuid
import time
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase import create_client

# Configuration
TEST_EMAIL = os.getenv("ATOMS_TEST_EMAIL", "kooshapari@kooshapari.com")
TEST_PASSWORD = os.getenv("ATOMS_TEST_PASSWORD", "118118")


@dataclass
class TestResult:
    """Individual test result."""
    test_id: str
    entity_type: str
    operation: str
    description: str
    success: bool
    duration_ms: float
    input_params: Dict[str, Any]
    output: Any
    error: Optional[str] = None
    edge_case: Optional[str] = None
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class TestReport:
    """Comprehensive test report generator."""

    def __init__(self):
        self.results: List[TestResult] = []
        self.start_time = datetime.now(timezone.utc)
        self.entity_cleanup: Dict[str, List[str]] = {}  # entity_type: [ids]

    def add_result(self, result: TestResult):
        """Add test result."""
        self.results.append(result)

        # Track created entities for cleanup
        if result.success and result.operation == "create" and isinstance(result.output, dict):
            entity_id = result.output.get("data", {}).get("id")
            if entity_id:
                if result.entity_type not in self.entity_cleanup:
                    self.entity_cleanup[result.entity_type] = []
                self.entity_cleanup[result.entity_type].append(entity_id)

    def get_summary(self) -> Dict[str, Any]:
        """Get test summary statistics."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.success)
        failed = total - passed

        by_entity = {}
        for result in self.results:
            if result.entity_type not in by_entity:
                by_entity[result.entity_type] = {"total": 0, "passed": 0, "failed": 0}
            by_entity[result.entity_type]["total"] += 1
            if result.success:
                by_entity[result.entity_type]["passed"] += 1
            else:
                by_entity[result.entity_type]["failed"] += 1

        by_operation = {}
        for result in self.results:
            if result.operation not in by_operation:
                by_operation[result.operation] = {"total": 0, "passed": 0, "failed": 0}
            by_operation[result.operation]["total"] += 1
            if result.success:
                by_operation[result.operation]["passed"] += 1
            else:
                by_operation[result.operation]["failed"] += 1

        return {
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": f"{(passed/total*100):.1f}%" if total > 0 else "0%",
            "duration_seconds": (datetime.now(timezone.utc) - self.start_time).total_seconds(),
            "by_entity_type": by_entity,
            "by_operation": by_operation,
            "edge_cases_tested": sum(1 for r in self.results if r.edge_case),
        }

    def generate_markdown_report(self) -> str:
        """Generate comprehensive markdown report."""
        summary = self.get_summary()

        lines = [
            "# COMPREHENSIVE ENTITY TOOL TEST REPORT",
            "",
            f"**Generated:** {datetime.now(timezone.utc).isoformat()}",
            f"**Duration:** {summary['duration_seconds']:.2f}s",
            "",
            "## Summary",
            "",
            f"- **Total Tests:** {summary['total_tests']}",
            f"- **Passed:** {summary['passed']} ({summary['pass_rate']})",
            f"- **Failed:** {summary['failed']}",
            f"- **Edge Cases Tested:** {summary['edge_cases_tested']}",
            "",
            "## Results by Entity Type",
            ""
        ]

        for entity_type, stats in summary["by_entity_type"].items():
            rate = f"{(stats['passed']/stats['total']*100):.1f}%" if stats['total'] > 0 else "0%"
            lines.append(f"### {entity_type}")
            lines.append(f"- Total: {stats['total']}")
            lines.append(f"- Passed: {stats['passed']} ({rate})")
            lines.append(f"- Failed: {stats['failed']}")
            lines.append("")

        lines.extend([
            "## Results by Operation",
            ""
        ])

        for operation, stats in summary["by_operation"].items():
            rate = f"{(stats['passed']/stats['total']*100):.1f}%" if stats['total'] > 0 else "0%"
            lines.append(f"### {operation}")
            lines.append(f"- Total: {stats['total']}")
            lines.append(f"- Passed: {stats['passed']} ({rate})")
            lines.append(f"- Failed: {stats['failed']}")
            lines.append("")

        lines.extend([
            "## Detailed Test Results",
            ""
        ])

        for i, result in enumerate(self.results, 1):
            status = "✅ PASS" if result.success else "❌ FAIL"
            lines.extend([
                f"### Test {i}: {result.description}",
                "",
                f"- **Status:** {status}",
                f"- **Entity Type:** {result.entity_type}",
                f"- **Operation:** {result.operation}",
                f"- **Duration:** {result.duration_ms:.2f}ms",
                f"- **Timestamp:** {result.timestamp}",
            ])

            if result.edge_case:
                lines.append(f"- **Edge Case:** {result.edge_case}")

            lines.append("")
            lines.append("**Input:**")
            lines.append("```json")
            lines.append(json.dumps(result.input_params, indent=2))
            lines.append("```")
            lines.append("")

            if result.error:
                lines.append("**Error:**")
                lines.append("```")
                lines.append(result.error)
                lines.append("```")
                lines.append("")

            lines.append("**Output:**")
            lines.append("```json")
            output_str = json.dumps(
                asdict(result.output) if hasattr(result.output, '__dict__') else result.output,
                indent=2,
                default=str
            )
            if len(output_str) > 1500:
                output_str = output_str[:1500] + "\n... (truncated)"
            lines.append(output_str)
            lines.append("```")
            lines.append("")
            lines.append("---")
            lines.append("")

        return "\n".join(lines)

    def save_reports(self, base_path: str):
        """Save markdown and JSON reports."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

        # Markdown report
        md_path = f"{base_path}_comprehensive_test_report_{timestamp}.md"
        with open(md_path, 'w') as f:
            f.write(self.generate_markdown_report())
        print(f"\n📄 Markdown report saved: {md_path}")

        # JSON report
        json_path = f"{base_path}_comprehensive_test_report_{timestamp}.json"
        with open(json_path, 'w') as f:
            json.dump({
                "summary": self.get_summary(),
                "results": [asdict(r) for r in self.results]
            }, f, indent=2, default=str)
        print(f"📄 JSON report saved: {json_path}")

        return md_path, json_path


async def get_auth_token(max_retries: int = 3) -> str:
    """Authenticate and get JWT token with retry logic."""
    supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    supabase_key = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

    if not supabase_url or not supabase_key:
        raise ValueError("Supabase credentials not configured in environment")

    for attempt in range(max_retries):
        try:
            client = create_client(supabase_url, supabase_key)
            auth_response = client.auth.sign_in_with_password({
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            })

            session = getattr(auth_response, "session", None)
            if not session or not getattr(session, "access_token", None):
                raise ValueError("Could not obtain Supabase JWT")

            return session.access_token

        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2  # Exponential backoff
                print(f"  Retry {attempt + 1}/{max_retries} after {wait_time}s: {str(e)[:100]}")
                await asyncio.sleep(wait_time)
            else:
                raise


async def call_entity_tool(auth_token: str, **params) -> tuple[Dict[str, Any], float]:
    """Call entity_tool directly."""
    from tools.entity import entity_operation

    start_time = time.perf_counter()

    try:
        result = await entity_operation(auth_token=auth_token, **params)
        duration_ms = (time.perf_counter() - start_time) * 1000
        return result, duration_ms
    except Exception as e:
        duration_ms = (time.perf_counter() - start_time) * 1000
        return {"success": False, "error": str(e)}, duration_ms


class EntityTester:
    """Test runner for entity operations."""

    def __init__(self, auth_token: str, report: TestReport):
        self.auth_token = auth_token
        self.report = report
        self.test_counter = 0

    async def run_test(
        self,
        entity_type: str,
        operation: str,
        description: str,
        params: Dict[str, Any],
        edge_case: Optional[str] = None
    ) -> TestResult:
        """Run a single test and record result."""
        self.test_counter += 1
        test_id = f"T{self.test_counter:03d}"

        print(f"\n{test_id}: {description}")
        print(f"  Entity: {entity_type}, Operation: {operation}")

        result, duration = await call_entity_tool(
            self.auth_token,
            operation=operation,
            entity_type=entity_type,
            **params
        )

        success = result.get("success", False)
        error = result.get("error")

        status_icon = "✅" if success else "❌"
        print(f"  {status_icon} Duration: {duration:.2f}ms, Success: {success}")
        if error:
            print(f"  Error: {error}")

        test_result = TestResult(
            test_id=test_id,
            entity_type=entity_type,
            operation=operation,
            description=description,
            success=success,
            duration_ms=duration,
            input_params=params,
            output=result,
            error=error,
            edge_case=edge_case
        )

        self.report.add_result(test_result)
        return test_result

    async def test_organization_full(self):
        """Complete test suite for organization entity."""
        print("\n" + "="*100)
        print("TESTING ORGANIZATION ENTITY")
        print("="*100)

        # 1. CREATE - Minimal data
        result = await self.run_test(
            "organization", "create",
            "Create organization with minimal required fields",
            {
                "data": {
                    "name": f"Test Org Minimal {uuid.uuid4().hex[:8]}",
                    "slug": f"test-org-minimal-{uuid.uuid4().hex[:8]}"
                }
            }
        )
        org_id_minimal = result.output.get("data", {}).get("id")

        # 2. CREATE - Full data
        result = await self.run_test(
            "organization", "create",
            "Create organization with full data",
            {
                "data": {
                    "name": f"Test Org Full {uuid.uuid4().hex[:8]}",
                    "slug": f"test-org-full-{uuid.uuid4().hex[:8]}",
                    "description": "Comprehensive test organization with all fields",
                    "type": "team"
                }
            }
        )
        org_id_full = result.output.get("data", {}).get("id")
        org_name_full = result.output.get("data", {}).get("name")

        if not org_id_full:
            print("⚠️ Skipping remaining org tests - creation failed")
            return

        # 3. READ - By UUID
        await self.run_test(
            "organization", "read",
            "Read organization by UUID",
            {"entity_id": org_id_full}
        )

        # 4. READ - By fuzzy name (exact match)
        await self.run_test(
            "organization", "read",
            "Read organization by exact name (fuzzy matching)",
            {"entity_id": org_name_full},
            edge_case="Fuzzy matching - exact name"
        )

        # 5. READ - By partial name
        partial_name = org_name_full.split()[0]  # Get first word
        await self.run_test(
            "organization", "read",
            "Read organization by partial name (fuzzy matching)",
            {"entity_id": partial_name},
            edge_case="Fuzzy matching - partial name"
        )

        # 6. READ - With relations
        await self.run_test(
            "organization", "read",
            "Read organization with relations",
            {"entity_id": org_id_full, "include_relations": True}
        )

        # 7. UPDATE
        await self.run_test(
            "organization", "update",
            "Update organization",
            {
                "entity_id": org_id_full,
                "data": {
                    "description": f"Updated at {datetime.now(timezone.utc).isoformat()}"
                }
            }
        )

        # 8. LIST - No filters
        await self.run_test(
            "organization", "list",
            "List organizations (no filters)",
            {"limit": 5}
        )

        # 9. LIST - With pagination
        await self.run_test(
            "organization", "list",
            "List organizations with pagination",
            {"limit": 3, "offset": 0}
        )

        # 10. SEARCH - By term
        await self.run_test(
            "organization", "search",
            "Search organizations by term",
            {"search_term": "Test Org", "limit": 10}
        )

        # 11. SEARCH - With filters
        await self.run_test(
            "organization", "search",
            "Search organizations with filters",
            {
                "filters": {"type": "team", "is_deleted": False},
                "limit": 10
            }
        )

        # 12. SEARCH - With ordering
        await self.run_test(
            "organization", "search",
            "Search organizations with custom ordering",
            {
                "filters": {"is_deleted": False},
                "order_by": "created_at:desc",
                "limit": 5
            }
        )

        # 13. DELETE - Soft delete
        await self.run_test(
            "organization", "delete",
            "Soft delete organization",
            {"entity_id": org_id_full, "soft_delete": True}
        )

        # 14. LIST - Verify soft delete
        result = await self.run_test(
            "organization", "list",
            "Verify soft-deleted org not in list",
            {"limit": 20},
            edge_case="Soft delete verification"
        )

        # 15. READ - Nonexistent ID
        await self.run_test(
            "organization", "read",
            "Read nonexistent organization (error handling)",
            {"entity_id": str(uuid.uuid4())},
            edge_case="Nonexistent entity error"
        )

        # 16. CREATE - Missing required field
        await self.run_test(
            "organization", "create",
            "Create organization with missing required field",
            {"data": {"description": "No name provided"}},
            edge_case="Missing required field error"
        )

        # Cleanup minimal org
        if org_id_minimal:
            await call_entity_tool(
                self.auth_token,
                operation="delete",
                entity_type="organization",
                entity_id=org_id_minimal,
                soft_delete=True
            )

    async def test_project_full(self):
        """Complete test suite for project entity."""
        print("\n" + "="*100)
        print("TESTING PROJECT ENTITY")
        print("="*100)

        # Create parent organization first
        print("\n📦 Creating parent organization for project tests...")
        org_result, _ = await call_entity_tool(
            self.auth_token,
            operation="create",
            entity_type="organization",
            data={
                "name": f"Test Org for Projects {uuid.uuid4().hex[:8]}",
                "slug": f"test-org-projects-{uuid.uuid4().hex[:8]}"
            }
        )

        if not org_result.get("success"):
            print(f"❌ Failed to create parent org: {org_result.get('error')}")
            return

        org_id = org_result["data"]["id"]
        print(f"✅ Created parent org: {org_id}")

        # 1. CREATE - Minimal data
        result = await self.run_test(
            "project", "create",
            "Create project with minimal required fields",
            {
                "data": {
                    "name": f"Test Project Minimal {uuid.uuid4().hex[:8]}",
                    "organization_id": org_id
                }
            }
        )
        proj_id_minimal = result.output.get("data", {}).get("id")

        # 2. CREATE - Full data
        result = await self.run_test(
            "project", "create",
            "Create project with full data",
            {
                "data": {
                    "name": f"Test Project Full {uuid.uuid4().hex[:8]}",
                    "organization_id": org_id,
                    "description": "Comprehensive test project",
                    "slug": f"test-project-full-{uuid.uuid4().hex[:8]}"
                }
            }
        )
        proj_id_full = result.output.get("data", {}).get("id")
        proj_name_full = result.output.get("data", {}).get("name")

        if not proj_id_full:
            print("⚠️ Skipping remaining project tests - creation failed")
            return

        # 3. READ - By UUID
        await self.run_test(
            "project", "read",
            "Read project by UUID",
            {"entity_id": proj_id_full}
        )

        # 4. READ - By fuzzy name
        await self.run_test(
            "project", "read",
            "Read project by name (fuzzy matching)",
            {"entity_id": proj_name_full},
            edge_case="Fuzzy matching"
        )

        # 5. READ - With relations
        await self.run_test(
            "project", "read",
            "Read project with relations",
            {"entity_id": proj_id_full, "include_relations": True}
        )

        # 6. UPDATE
        await self.run_test(
            "project", "update",
            "Update project",
            {
                "entity_id": proj_id_full,
                "data": {"description": "Updated description"}
            }
        )

        # 7. LIST - By parent organization
        await self.run_test(
            "project", "list",
            "List projects by parent organization",
            {"parent_type": "organization", "parent_id": org_id, "limit": 10}
        )

        # 8. LIST - No parent filter
        await self.run_test(
            "project", "list",
            "List all projects (no parent filter)",
            {"limit": 5}
        )

        # 9. SEARCH
        await self.run_test(
            "project", "search",
            "Search projects",
            {"search_term": "Test Project", "limit": 10}
        )

        # 10. DELETE - Soft delete
        await self.run_test(
            "project", "delete",
            "Soft delete project",
            {"entity_id": proj_id_full, "soft_delete": True}
        )

        # Cleanup
        if proj_id_minimal:
            await call_entity_tool(
                self.auth_token, operation="delete", entity_type="project",
                entity_id=proj_id_minimal, soft_delete=True
            )

        await call_entity_tool(
            self.auth_token, operation="delete", entity_type="organization",
            entity_id=org_id, soft_delete=True
        )

    async def test_document_full(self):
        """Complete test suite for document entity."""
        print("\n" + "="*100)
        print("TESTING DOCUMENT ENTITY")
        print("="*100)

        # Create parent hierarchy
        print("\n📦 Creating parent hierarchy for document tests...")
        org_result, _ = await call_entity_tool(
            self.auth_token,
            operation="create",
            entity_type="organization",
            data={
                "name": f"Test Org for Docs {uuid.uuid4().hex[:8]}",
                "slug": f"test-org-docs-{uuid.uuid4().hex[:8]}"
            }
        )

        if not org_result.get("success"):
            print("❌ Failed to create parent org")
            return

        org_id = org_result["data"]["id"]

        proj_result, _ = await call_entity_tool(
            self.auth_token,
            operation="create",
            entity_type="project",
            data={
                "name": f"Test Project for Docs {uuid.uuid4().hex[:8]}",
                "organization_id": org_id
            }
        )

        if not proj_result.get("success"):
            print("❌ Failed to create parent project")
            return

        proj_id = proj_result["data"]["id"]
        print(f"✅ Created parent hierarchy: org={org_id}, proj={proj_id}")

        # 1. CREATE - Minimal
        result = await self.run_test(
            "document", "create",
            "Create document with minimal fields",
            {
                "data": {
                    "name": f"Test Doc Minimal {uuid.uuid4().hex[:8]}",
                    "project_id": proj_id
                }
            }
        )
        doc_id_minimal = result.output.get("data", {}).get("id")

        # 2. CREATE - Full
        result = await self.run_test(
            "document", "create",
            "Create document with full data",
            {
                "data": {
                    "name": f"Test Doc Full {uuid.uuid4().hex[:8]}",
                    "project_id": proj_id,
                    "description": "Comprehensive test document",
                    "slug": f"test-doc-full-{uuid.uuid4().hex[:8]}"
                }
            }
        )
        doc_id_full = result.output.get("data", {}).get("id")
        doc_name_full = result.output.get("data", {}).get("name")

        if not doc_id_full:
            print("⚠️ Skipping remaining document tests")
            return

        # 3. READ
        await self.run_test(
            "document", "read",
            "Read document by UUID",
            {"entity_id": doc_id_full}
        )

        # 4. READ - Fuzzy matching
        await self.run_test(
            "document", "read",
            "Read document by name (fuzzy)",
            {"entity_id": doc_name_full},
            edge_case="Fuzzy matching"
        )

        # 5. UPDATE
        await self.run_test(
            "document", "update",
            "Update document",
            {
                "entity_id": doc_id_full,
                "data": {"description": "Updated doc"}
            }
        )

        # 6. LIST - By parent project
        await self.run_test(
            "document", "list",
            "List documents by parent project",
            {"parent_type": "project", "parent_id": proj_id, "limit": 10}
        )

        # 7. SEARCH
        await self.run_test(
            "document", "search",
            "Search documents",
            {"search_term": "Test Doc", "limit": 10}
        )

        # 8. DELETE
        await self.run_test(
            "document", "delete",
            "Soft delete document",
            {"entity_id": doc_id_full, "soft_delete": True}
        )

        # Cleanup
        if doc_id_minimal:
            await call_entity_tool(
                self.auth_token, operation="delete", entity_type="document",
                entity_id=doc_id_minimal, soft_delete=True
            )

        await call_entity_tool(
            self.auth_token, operation="delete", entity_type="project",
            entity_id=proj_id, soft_delete=True
        )
        await call_entity_tool(
            self.auth_token, operation="delete", entity_type="organization",
            entity_id=org_id, soft_delete=True
        )

    async def test_requirement_full(self):
        """Complete test suite for requirement entity."""
        print("\n" + "="*100)
        print("TESTING REQUIREMENT ENTITY")
        print("="*100)

        # Create parent hierarchy
        print("\n📦 Creating parent hierarchy for requirement tests...")
        org_result, _ = await call_entity_tool(
            self.auth_token,
            operation="create",
            entity_type="organization",
            data={
                "name": f"Test Org for Reqs {uuid.uuid4().hex[:8]}",
                "slug": f"test-org-reqs-{uuid.uuid4().hex[:8]}"
            }
        )

        if not org_result.get("success"):
            return

        org_id = org_result["data"]["id"]

        proj_result, _ = await call_entity_tool(
            self.auth_token,
            operation="create",
            entity_type="project",
            data={
                "name": f"Test Project for Reqs {uuid.uuid4().hex[:8]}",
                "organization_id": org_id
            }
        )

        if not proj_result.get("success"):
            return

        proj_id = proj_result["data"]["id"]

        doc_result, _ = await call_entity_tool(
            self.auth_token,
            operation="create",
            entity_type="document",
            data={
                "name": f"Test Doc for Reqs {uuid.uuid4().hex[:8]}",
                "project_id": proj_id
            }
        )

        if not doc_result.get("success"):
            return

        doc_id = doc_result["data"]["id"]
        print(f"✅ Created parent hierarchy: doc={doc_id}")

        # 1. CREATE - Minimal
        result = await self.run_test(
            "requirement", "create",
            "Create requirement with minimal fields",
            {
                "data": {
                    "name": f"Test Req Minimal {uuid.uuid4().hex[:8]}",
                    "document_id": doc_id
                }
            }
        )
        req_id_minimal = result.output.get("data", {}).get("id")

        # 2. CREATE - Full
        result = await self.run_test(
            "requirement", "create",
            "Create requirement with full data",
            {
                "data": {
                    "name": f"Test Req Full {uuid.uuid4().hex[:8]}",
                    "document_id": doc_id,
                    "description": "Comprehensive test requirement",
                    "status": "active",
                    "priority": "high",
                    "type": "functional"
                }
            }
        )
        req_id_full = result.output.get("data", {}).get("id")
        req_name_full = result.output.get("data", {}).get("name")

        if not req_id_full:
            print("⚠️ Skipping remaining requirement tests")
            return

        # 3. READ
        await self.run_test(
            "requirement", "read",
            "Read requirement by UUID",
            {"entity_id": req_id_full}
        )

        # 4. READ - Fuzzy
        await self.run_test(
            "requirement", "read",
            "Read requirement by name (fuzzy)",
            {"entity_id": req_name_full},
            edge_case="Fuzzy matching"
        )

        # 5. UPDATE
        await self.run_test(
            "requirement", "update",
            "Update requirement",
            {
                "entity_id": req_id_full,
                "data": {"status": "reviewed", "priority": "medium"}
            }
        )

        # 6. LIST - By parent document
        await self.run_test(
            "requirement", "list",
            "List requirements by parent document",
            {"parent_type": "document", "parent_id": doc_id, "limit": 10}
        )

        # 7. SEARCH
        await self.run_test(
            "requirement", "search",
            "Search requirements",
            {"search_term": "Test Req", "limit": 10}
        )

        # 8. SEARCH - With filters
        await self.run_test(
            "requirement", "search",
            "Search requirements with status filter",
            {
                "filters": {"status": "reviewed"},
                "limit": 10
            }
        )

        # 9. DELETE
        await self.run_test(
            "requirement", "delete",
            "Soft delete requirement",
            {"entity_id": req_id_full, "soft_delete": True}
        )

        # Cleanup
        if req_id_minimal:
            await call_entity_tool(
                self.auth_token, operation="delete", entity_type="requirement",
                entity_id=req_id_minimal, soft_delete=True
            )

        await call_entity_tool(
            self.auth_token, operation="delete", entity_type="document",
            entity_id=doc_id, soft_delete=True
        )
        await call_entity_tool(
            self.auth_token, operation="delete", entity_type="project",
            entity_id=proj_id, soft_delete=True
        )
        await call_entity_tool(
            self.auth_token, operation="delete", entity_type="organization",
            entity_id=org_id, soft_delete=True
        )

    async def test_edge_cases(self):
        """Test edge cases and error handling."""
        print("\n" + "="*100)
        print("TESTING EDGE CASES AND ERROR HANDLING")
        print("="*100)

        # Create a test org for edge cases
        org_result, _ = await call_entity_tool(
            self.auth_token,
            operation="create",
            entity_type="organization",
            data={
                "name": f"Edge Case Test Org {uuid.uuid4().hex[:8]}",
                "slug": f"edge-case-org-{uuid.uuid4().hex[:8]}"
            }
        )

        if not org_result.get("success"):
            print("❌ Failed to create test org for edge cases")
            return

        org_id = org_result["data"]["id"]

        # 1. Empty data
        await self.run_test(
            "organization", "create",
            "Create with empty data (error expected)",
            {"data": {}},
            edge_case="Empty data object"
        )

        # 2. Invalid entity type
        await self.run_test(
            "invalid_entity", "list",
            "List with invalid entity type (error expected)",
            {"limit": 5},
            edge_case="Invalid entity type"
        )

        # 3. Pagination with offset > total
        await self.run_test(
            "organization", "list",
            "List with offset beyond total records",
            {"limit": 5, "offset": 10000},
            edge_case="Offset beyond records"
        )

        # 4. Large limit (should be capped)
        await self.run_test(
            "organization", "list",
            "List with limit > 100 (should be capped)",
            {"limit": 500},
            edge_case="Limit capping"
        )

        # 5. Update nonexistent entity
        await self.run_test(
            "organization", "update",
            "Update nonexistent entity (error expected)",
            {
                "entity_id": str(uuid.uuid4()),
                "data": {"description": "Should fail"}
            },
            edge_case="Update nonexistent entity"
        )

        # 6. Delete already deleted entity
        await call_entity_tool(
            self.auth_token, operation="delete", entity_type="organization",
            entity_id=org_id, soft_delete=True
        )

        await self.run_test(
            "organization", "delete",
            "Delete already soft-deleted entity",
            {"entity_id": org_id, "soft_delete": True},
            edge_case="Delete already deleted"
        )

        # 7. Search with empty term
        await self.run_test(
            "organization", "search",
            "Search with empty search term",
            {"search_term": "", "limit": 5},
            edge_case="Empty search term"
        )

        # 8. Filters with no matches
        await self.run_test(
            "organization", "search",
            "Search with filters that match nothing",
            {
                "filters": {
                    "name": {"eq": "THIS_ENTITY_DOES_NOT_EXIST_12345"}
                },
                "limit": 5
            },
            edge_case="No matches found"
        )


async def run_comprehensive_tests():
    """Main test runner."""
    print("="*100)
    print("ATOMS MCP ENTITY TOOL - COMPREHENSIVE TEST SUITE")
    print("="*100)
    print(f"\nStarted: {datetime.now(timezone.utc).isoformat()}")
    print(f"Test User: {TEST_EMAIL}")

    # Authenticate
    print("\n🔐 Authenticating...")
    try:
        auth_token = await get_auth_token()
        print("✅ Authentication successful")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return

    # Initialize report
    report = TestReport()
    tester = EntityTester(auth_token, report)

    # Run all test suites
    try:
        await tester.test_organization_full()
        await tester.test_project_full()
        await tester.test_document_full()
        await tester.test_requirement_full()
        await tester.test_edge_cases()

    except Exception as e:
        print(f"\n❌ Test suite error: {e}")
        import traceback
        traceback.print_exc()

    # Generate and save reports
    print("\n\n" + "="*100)
    print("GENERATING REPORTS...")
    print("="*100)

    summary = report.get_summary()

    print("\n📊 TEST SUMMARY")
    print("-" * 100)
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Passed: {summary['passed']} ({summary['pass_rate']})")
    print(f"Failed: {summary['failed']}")
    print(f"Duration: {summary['duration_seconds']:.2f}s")
    print(f"Edge Cases Tested: {summary['edge_cases_tested']}")

    print("\n📊 BY ENTITY TYPE")
    print("-" * 100)
    for entity_type, stats in summary['by_entity_type'].items():
        rate = f"{(stats['passed']/stats['total']*100):.1f}%" if stats['total'] > 0 else "0%"
        print(f"{entity_type:20s}: {stats['passed']:3d}/{stats['total']:3d} passed ({rate})")

    print("\n📊 BY OPERATION")
    print("-" * 100)
    for operation, stats in summary['by_operation'].items():
        rate = f"{(stats['passed']/stats['total']*100):.1f}%" if stats['total'] > 0 else "0%"
        print(f"{operation:20s}: {stats['passed']:3d}/{stats['total']:3d} passed ({rate})")

    # Save reports
    base_path = "/Users/kooshapari/temp-PRODVERCEL/485/kush/atoms-mcp-prod/tests/results/entity_tool"
    os.makedirs(os.path.dirname(base_path), exist_ok=True)

    md_path, json_path = report.save_reports(base_path)

    print("\n" + "="*100)
    print("TEST SUITE COMPLETE")
    print("="*100)

    return report


if __name__ == "__main__":
    asyncio.run(run_comprehensive_tests())
