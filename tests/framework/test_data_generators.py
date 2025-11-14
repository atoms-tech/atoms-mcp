"""Scenario-based Test Data Generator for Parametrized Tests

Provides data generation with scenario variations for comprehensive test coverage.
Used with pytest.mark.parametrize for reducing test duplication.
"""

from typing import Any, Dict
from tests.framework.data_generators import DataGenerator


class DataGeneratorHelper:
    """Generate test data with scenario-based approach."""

    def __init__(self):
        self.context_data: Dict[str, Any] = {}

    def create_entity_data(self, entity_type: str, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Create entity data based on type and scenario."""
        scenario_name = scenario.get("name", "basic")

        if entity_type == "organization":
            return self._create_organization_scenario(scenario_name)
        elif entity_type == "project":
            return self._create_project_scenario(scenario_name)
        elif entity_type == "document":
            return self._create_document_scenario(scenario_name)
        elif entity_type == "requirement":
            return self._create_requirement_scenario(scenario_name)
        elif entity_type == "test" or entity_type == "test_entity":
            return self._create_test_scenario(scenario_name)
        elif entity_type == "property":
            return self._create_property_scenario(scenario_name)
        else:
            raise ValueError(f"Unknown entity type: {entity_type}")

    def _create_organization_scenario(self, scenario_name: str) -> Dict[str, Any]:
        """Create organization data for specific scenario."""
        if scenario_name == "basic":
            return DataGenerator.organization_data()
        elif scenario_name == "with_explicit_id":
            organization_id = DataGenerator.uuid()
            return DataGenerator.organization_data(f"Explicit Org {organization_id[:8]}")
        else:
            return self._create_organization_scenario("basic")

    def _create_project_scenario(self, scenario_name: str) -> Dict[str, Any]:
        """Create project data for specific scenario."""
        if scenario_name == "basic":
            data = DataGenerator.project_data()
            # Add workspace_id for permission middleware
            data["workspace_id"] = DataGenerator.uuid()
            return data
        elif scenario_name == "with_auto_context":
            # For auto context, we need an organization ID - use a mock ID for now
            # In real tests, context should be set up via workspace_tool first
            # For unit tests, we'll use a mock ID instead of "auto" to avoid context dependency
            self.context_data = {}
            # Use explicit ID instead of "auto" for unit tests without context setup
            data = DataGenerator.project_data(organization_id=DataGenerator.uuid())
            # Add workspace_id for permission middleware
            data["workspace_id"] = DataGenerator.uuid()
            return data
        elif scenario_name == "with_explicit_id":
            organization_id = DataGenerator.uuid()
            data = DataGenerator.project_data(f"Explicit Project {organization_id[:8]}", organization_id)
            # Add workspace_id for permission middleware
            data["workspace_id"] = DataGenerator.uuid()
            return data
        else:
            return self._create_project_scenario("basic")

    def _create_document_scenario(self, scenario_name: str) -> Dict[str, Any]:
        """Create document data for specific scenario."""
        if scenario_name == "basic":
            data = DataGenerator.document_data()
            # Add workspace_id for permission middleware
            data["workspace_id"] = DataGenerator.uuid()
            return data
        elif scenario_name == "with_auto_context":
            self.context_data = {}
            data = DataGenerator.document_data(project_id="auto")
            # Add workspace_id for permission middleware
            data["workspace_id"] = DataGenerator.uuid()
            return data
        else:
            return self._create_document_scenario("basic")

    def _create_requirement_scenario(self, scenario_name: str) -> Dict[str, Any]:
        """Create requirement data for specific scenario."""
        if scenario_name == "basic":
            data = DataGenerator.requirement_data()
            # Add workspace_id for permission middleware
            data["workspace_id"] = DataGenerator.uuid()
            return data
        elif scenario_name == "with_auto_context":
            self.context_data = {}
            data = DataGenerator.requirement_data(document_id="auto")
            # Add workspace_id for permission middleware
            data["workspace_id"] = DataGenerator.uuid()
            return data
        elif scenario_name == "with_high_priority":
            data = DataGenerator.requirement_data()
            # Add workspace_id for permission middleware
            data["workspace_id"] = DataGenerator.uuid()
            data["priority"] = "high"
            return data
        else:
            return self._create_requirement_scenario("basic")

    def _create_test_scenario(self, scenario_name: str) -> Dict[str, Any]:
        """Create test data for specific scenario."""
        if scenario_name == "basic":
            data = DataGenerator.test_data()
            # Add workspace_id for permission middleware
            data["workspace_id"] = DataGenerator.uuid()
            return data
        elif scenario_name == "with_auto_context":
            self.context_data = {}
            data = DataGenerator.test_data(project_id="auto")
            # Add workspace_id for permission middleware
            data["workspace_id"] = DataGenerator.uuid()
            return data
        elif scenario_name == "with_high_priority":
            data = DataGenerator.test_data()
            # Add workspace_id for permission middleware
            data["workspace_id"] = DataGenerator.uuid()
            data["priority"] = "high"
            return data
        else:
            return self._create_test_scenario("basic")

    def _create_property_scenario(self, scenario_name: str) -> Dict[str, Any]:
        """Create property data for specific scenario."""
        if scenario_name == "basic":
            return {
                "name": f"Test Property {DataGenerator.unique_id()}",
                "value": "test_value",
                "workspace_id": DataGenerator.uuid()  # Add workspace_id for permission middleware
            }
        else:
            return self._create_property_scenario("basic")
