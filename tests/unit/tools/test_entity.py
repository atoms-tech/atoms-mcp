"""Entity tool tests - Main entry point.

This module re-exports all entity-specific tests for backwards compatibility.
Tests are now organized by entity type in separate modules:

- test_entity_core.py          - Parametrized tests across all entity types
- test_entity_organization.py  - Organization-specific tests
- test_entity_project.py       - Project-specific tests  
- test_entity_document.py      - Document-specific tests
- test_entity_requirement.py   - Requirement-specific tests
- test_entity_test.py          - Test case entity tests

Run all entity tests:
    pytest tests/unit/tools/test_entity*.py -v

Run specific entity tests:
    pytest tests/unit/tools/test_entity_organization.py -v

Organization rationale:
- Each file is now <500 lines (target <350)
- Tests are grouped by domain concern (entity type)
- Aligns with user story epics
- Easier to maintain and locate specific tests
- Follows canonical naming paradigm from AGENTS.md
"""

# Re-export key test classes and fixtures for backwards compatibility
# This allows existing imports to continue working

# Import from core module
from tests.unit.tools.test_entity_core import (
    TestResults,
    test_results,
    TestEntityCreateParametrized,
    TestEntityReadParametrized,
    TestEntitySearchParametrized,
    TestBatchOperations,
    TestFormatTypes,
    TestErrorCases,
)

# Import organization tests
from tests.unit.tools.test_entity_organization import (
    TestOrganizationCRUD,
    TestOrganizationList,
    TestOrganizationPagination,
)

# Import project tests
from tests.unit.tools.test_entity_project import (
    TestProjectCRUD,
    TestProjectList,
    TestProjectBatch,
)

# Import document tests
from tests.unit.tools.test_entity_document import (
    TestDocumentCRUD,
    TestDocumentList,
)

# Import requirement tests
from tests.unit/tools.test_entity_requirement import (
    TestRequirementCRUD,
    TestRequirementSearch,
)

# Import test case tests
from tests.unit.tools.test_entity_test import (
    TestTestEntityCRUD,
)


__all__ = [
    # Core
    "TestResults",
    "test_results",
    "TestEntityCreateParametrized",
    "TestEntityReadParametrized",
    "TestEntitySearchParametrized",
    "TestBatchOperations",
    "TestFormatTypes",
    "TestErrorCases",
    # Organization
    "TestOrganizationCRUD",
    "TestOrganizationList",
    "TestOrganizationPagination",
    # Project
    "TestProjectCRUD",
    "TestProjectList",
    "TestProjectBatch",
    # Document
    "TestDocumentCRUD",
    "TestDocumentList",
    # Requirement
    "TestRequirementCRUD",
    "TestRequirementSearch",
    # Test
    "TestTestEntityCRUD",
]


# Module-level marker
import pytest
pytestmark = [pytest.mark.asyncio, pytest.mark.unit]
