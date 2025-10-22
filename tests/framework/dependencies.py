"""pytest-dependency cascade flow patterns for test ordering.

This module provides automatic test dependency ordering with predefined cascade patterns
for common test flows like CRUD operations, hierarchical relationships, and workflows.

Key Features:
- FlowPattern enum with predefined patterns (CRUD, hierarchical, workflow, etc.)
- @cascade_flow decorator for automatic test ordering
- @depends_on decorator for explicit dependencies
- @flow_stage decorator with data requirement validation
- TestResultRegistry for sharing data between tests
- Graphviz visualization support

Usage:
    @cascade_flow("crud", entity_type="project")
    class TestProjectCRUD:
        async def test_list(self, store_result): ...
        async def test_create(self, store_result): ...  # Auto depends on test_list
        async def test_read(self, test_results): ...    # Auto depends on test_create
        async def test_update(self, test_results): ... # Auto depends on test_read
        async def test_delete(self, test_results): ... # Auto depends on test_update
        async def test_verify(self, test_results): ... # Auto depends on test_delete
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import pytest

logger = logging.getLogger(__name__)


class FlowPattern(Enum):
    """Predefined test flow patterns."""

    CRUD = "crud"  # list -> create -> read -> update -> delete -> verify
    HIERARCHICAL = "hierarchical"  # Parent -> children -> interactions -> cleanup
    WORKFLOW = "workflow"  # Setup -> execute -> verify -> cleanup
    SIMPLE = "simple"  # Sequential test ordering
    MINIMAL_CRUD = "minimal_crud"  # create -> read -> delete


# Flow pattern definitions
FLOW_DEFINITIONS = {
    FlowPattern.CRUD: {
        "stages": ["list", "create", "read", "update", "delete", "verify"],
        "dependencies": {
            "list": [],
            "create": ["list"],
            "read": ["create"],
            "update": ["read"],
            "delete": ["update"],
            "verify": ["delete"],
        },
    },
    FlowPattern.HIERARCHICAL: {
        "stages": ["setup_parent", "create_children", "interact", "cleanup"],
        "dependencies": {
            "setup_parent": [],
            "create_children": ["setup_parent"],
            "interact": ["create_children"],
            "cleanup": ["interact"],
        },
    },
    FlowPattern.WORKFLOW: {
        "stages": ["setup", "execute", "verify", "cleanup"],
        "dependencies": {
            "setup": [],
            "execute": ["setup"],
            "verify": ["execute"],
            "cleanup": ["verify"],
        },
    },
    FlowPattern.SIMPLE: {
        "stages": ["test_a", "test_b", "test_c"],
        "dependencies": {
            "test_a": [],
            "test_b": ["test_a"],
            "test_c": ["test_b"],
        },
    },
    FlowPattern.MINIMAL_CRUD: {
        "stages": ["create", "read", "delete"],
        "dependencies": {
            "create": [],
            "read": ["create"],
            "delete": ["read"],
        },
    },
}


@dataclass
class TestResult:
    """Result from a test in a flow."""

    test_name: str
    passed: bool
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


class TestResultRegistry:
    """Registry for sharing results between tests in a flow."""

    def __init__(self):
        self.results: dict[str, TestResult] = {}
        self.shared_data: dict[str, Any] = {}

    def store_result(self, test_name: str, passed: bool, data: dict = None, error: str = None) -> TestResult:
        """Store result of a test."""
        result = TestResult(test_name=test_name, passed=passed, data=data or {}, error=error)
        self.results[test_name] = result
        if data:
            self.shared_data.update(data)
        logger.debug(f"Stored result for {test_name}: passed={passed}")
        return result

    def get_result(self, test_name: str) -> TestResult | None:
        """Get result of a previous test."""
        return self.results.get(test_name)

    def get_data(self, key: str, default: Any = None) -> Any:
        """Get shared data from previous tests."""
        return self.shared_data.get(key, default)

    def get_all_results(self) -> dict[str, TestResult]:
        """Get all test results."""
        return self.results.copy()

    def get_all_data(self) -> dict[str, Any]:
        """Get all shared data."""
        return self.shared_data.copy()

    def clear(self) -> None:
        """Clear all results and data."""
        self.results.clear()
        self.shared_data.clear()


# Global result registry
_result_registry = TestResultRegistry()


def get_result_registry() -> TestResultRegistry:
    """Get the global test result registry."""
    return _result_registry


@pytest.fixture
def test_results() -> TestResultRegistry:
    """Provide test result registry to tests."""
    return _result_registry


@pytest.fixture
def store_result():
    """Fixture to store test results."""

    def _store(test_name: str, passed: bool, data: dict = None, error: str = None) -> TestResult:
        return _result_registry.store_result(test_name, passed, data, error)

    return _store


def depends_on(*test_names: str) -> Callable:
    """Decorator to mark explicit test dependencies.

    Usage:
        @depends_on("test_create")
        async def test_read(test_results):
            result = test_results.get_result("test_create")
            assert result.passed
    """

    def decorator(func: Callable) -> Callable:
        func._depends_on = test_names
        return func

    return decorator


def flow_stage(
    stage_name: str, entity_type: str = "", required_data: list[str] = None
) -> Callable:
    """Decorator for a stage in a flow.

    Args:
        stage_name: Name of the stage in the flow
        entity_type: Type of entity being tested (for documentation)
        required_data: List of data keys required from previous stages

    Usage:
        @flow_stage("create", entity_type="project", required_data=[])
        async def test_create(store_result):
            result = await client.create_project(...)
            store_result("test_create", True, {"project_id": result["id"]})
    """

    def decorator(func: Callable) -> Callable:
        func._flow_stage = stage_name
        func._entity_type = entity_type
        func._required_data = required_data or []
        return func

    return decorator


def cascade_flow(pattern: str = "crud", entity_type: str = "") -> Callable:
    """Decorator for automatically ordering tests in a flow.

    Args:
        pattern: Flow pattern (crud, hierarchical, workflow, simple, minimal_crud)
        entity_type: Type of entity being tested

    Usage:
        @cascade_flow("crud", entity_type="project")
        class TestProjectCRUD:
            async def test_list(self, store_result): ...
            async def test_create(self, store_result): ...
            async def test_read(self, test_results): ...
            async def test_update(self, test_results): ...
            async def test_delete(self, test_results): ...
            async def test_verify(self, test_results): ...
    """

    def decorator(cls: type) -> type:
        # Store flow information
        flow_pattern_enum = FlowPattern[pattern.upper()]
        flow_def = FLOW_DEFINITIONS[flow_pattern_enum]

        # Inject pytest.mark.dependency markers
        for stage_name in flow_def["stages"]:
            test_method_name = f"test_{stage_name}" if not stage_name.startswith("test_") else stage_name

            if hasattr(cls, test_method_name):
                test_method = getattr(cls, test_method_name)

                # Get dependencies for this stage
                depends_on_stages = flow_def["dependencies"].get(stage_name, [])
                depends_on_tests = [
                    f"{stage}" if stage.startswith("test_") else f"test_{stage}"
                    for stage in depends_on_stages
                ]

                # Mark with pytest.mark.dependency
                for test_name in depends_on_tests:
                    test_method = pytest.mark.dependency(depends=test_name)(test_method)

                setattr(cls, test_method_name, test_method)

        # Store metadata
        cls._cascade_flow = True
        cls._flow_pattern = flow_pattern_enum
        cls._entity_type = entity_type

        return cls

    return decorator


class FlowVisualizer:
    """Visualize test flow dependencies using Graphviz."""

    @staticmethod
    def visualize(flow_pattern: FlowPattern, output_file: str = "flow.png") -> None:
        """Generate a visualization of the flow pattern.

        Requires: graphviz package

        Args:
            flow_pattern: Pattern to visualize
            output_file: Output file path (supports .png, .pdf, .svg)
        """
        try:
            from graphviz import Digraph
        except ImportError:
            logger.warning("graphviz package not installed, skipping visualization")
            return

        flow_def = FLOW_DEFINITIONS[flow_pattern]
        g = Digraph(comment=f"{flow_pattern.value} Flow")
        g.attr(rankdir="LR")

        # Add nodes
        for stage in flow_def["stages"]:
            g.node(stage, label=stage.replace("_", " ").title())

        # Add edges
        for stage, dependencies in flow_def["dependencies"].items():
            for dep in dependencies:
                g.edge(dep, stage)

        # Render
        output_name = output_file.rsplit(".", 1)[0]
        format_type = output_file.rsplit(".", 1)[-1] if "." in output_file else "png"
        g.render(output_name, format=format_type, cleanup=True)
        logger.info(f"Flow visualization saved to {output_file}")

    @staticmethod
    def visualize_all(output_dir: str = ".") -> None:
        """Visualize all flow patterns."""
        for pattern in FlowPattern:
            output_file = f"{output_dir}/flow_{pattern.value}.png"
            FlowVisualizer.visualize(pattern, output_file)


class FlowTestGenerator:
    """Programmatically generate tests for a flow pattern."""

    @staticmethod
    def create_flow_tests(
        pattern: FlowPattern,
        entity_type: str,
        test_implementations: dict[str, Callable],
    ) -> dict[str, Callable]:
        """Create test functions from a flow pattern.

        Args:
            pattern: Flow pattern to use
            entity_type: Type of entity being tested
            test_implementations: Dict of {stage_name: implementation_function}

        Returns:
            Dict of {test_name: test_function} for use in a test class

        Usage:
            implementations = {
                "create": async def test_create_impl(client):
                    return await client.create_entity(...)
                "read": async def test_read_impl(client, test_results):
                    result = test_results.get_result("test_create")
                    return await client.read_entity(result.data["id"])
            }
            tests = FlowTestGenerator.create_flow_tests(
                FlowPattern.MINIMAL_CRUD,
                "project",
                implementations
            )
        """
        flow_def = FLOW_DEFINITIONS[pattern]
        generated_tests = {}

        for stage in flow_def["stages"]:
            stage_name = stage if stage.startswith("test_") else f"test_{stage}"
            dependencies = flow_def["dependencies"].get(stage, [])

            if stage in test_implementations:
                impl = test_implementations[stage]

                # Create wrapper that handles dependencies
                async def create_test_wrapper(impl_func, deps):
                    async def test_wrapper(store_result, test_results):
                        # Verify dependencies passed
                        for dep in deps:
                            dep_test = dep if dep.startswith("test_") else f"test_{dep}"
                            result = test_results.get_result(dep_test)
                            if result and not result.passed:
                                pytest.skip(f"Dependency {dep_test} failed")

                        # Run implementation
                        try:
                            result = await impl_func(store_result, test_results)
                            store_result(stage_name, True, data=result or {})
                            return result
                        except Exception as e:
                            store_result(stage_name, False, error=str(e))
                            raise

                    return test_wrapper

                generated_tests[stage_name] = create_test_wrapper(impl, dependencies)

        return generated_tests


__all__ = [
    "FlowPattern",
    "FLOW_DEFINITIONS",
    "TestResult",
    "TestResultRegistry",
    "depends_on",
    "flow_stage",
    "cascade_flow",
    "FlowVisualizer",
    "FlowTestGenerator",
    "get_result_registry",
    "test_results",
    "store_result",
]
