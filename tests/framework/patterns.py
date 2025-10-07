"""
Test Patterns for Common Test Scenarios

Provides reusable test patterns from Zen framework:
- Tool testing pattern (single tool validation)
- User story pattern (multi-step workflow)
- Integration pattern (multi-tool coordination)
"""

import time
from typing import Any, Callable, Dict, List

from .adapters import AtomsMCPClientAdapter


class TestPattern:
    """Base class for test patterns."""

    async def execute(self, client_adapter: AtomsMCPClientAdapter, *args, **kwargs) -> Dict[str, Any]:
        """Execute test pattern. Returns standardized result."""
        raise NotImplementedError


class ToolTestPattern(TestPattern):
    """Pattern for testing individual MCP tools with field validation."""

    def __init__(self, tool_name: str, expected_fields: List[str]):
        self.tool_name = tool_name
        self.expected_fields = expected_fields

    async def execute(self, client_adapter: AtomsMCPClientAdapter, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute tool test pattern.

        Returns:
            {
                "success": bool,
                "result": Any,
                "duration_ms": float,
                "validation": {
                    "has_expected_fields": bool,
                    "missing_fields": List[str],
                    "extra_fields": List[str]
                }
            }
        """
        # Call tool
        result = await client_adapter.call_tool(self.tool_name, params)

        # Validate expected fields
        validation = self._validate_response(result.get("response"))

        return {
            "success": result["success"] and validation["has_expected_fields"],
            "result": result["response"],
            "duration_ms": result["duration_ms"],
            "error": result.get("error"),
            "validation": validation,
        }

    def _validate_response(self, response: Any) -> Dict[str, Any]:
        """Validate response has expected fields."""
        if not self.expected_fields:
            return {"has_expected_fields": True, "missing_fields": [], "extra_fields": []}

        if not isinstance(response, dict):
            return {
                "has_expected_fields": False,
                "missing_fields": self.expected_fields,
                "extra_fields": [],
            }

        missing = [field for field in self.expected_fields if field not in response]
        extra = [field for field in response.keys() if field not in self.expected_fields]

        return {
            "has_expected_fields": len(missing) == 0,
            "missing_fields": missing,
            "extra_fields": extra,
        }


class UserStoryPattern(TestPattern):
    """Pattern for multi-step user story testing with shared context."""

    def __init__(self, story_name: str, steps: List[Dict[str, Any]]):
        """
        Initialize user story pattern.

        Args:
            story_name: Name of the user story
            steps: List of steps [
                {
                    "tool": "tool_name",
                    "params": {...},
                    "validation": Callable[[result, context], bool],
                    "description": "Step description",
                    "save_to_context": "key_name"  # Optional: save result to context
                },
                ...
            ]
        """
        self.story_name = story_name
        self.steps = steps

    async def execute(self, client_adapter: AtomsMCPClientAdapter) -> Dict[str, Any]:
        """
        Execute user story pattern.

        Returns:
            {
                "success": bool,
                "story_name": str,
                "steps_completed": int,
                "steps_total": int,
                "step_results": List[Dict],
                "duration_ms": float,
                "context": Dict  # Shared context between steps
            }
        """
        start = time.perf_counter()
        step_results = []
        context = {}  # Shared context between steps

        for i, step in enumerate(self.steps):
            step_start = time.perf_counter()

            # Resolve params with context variables
            params = self._resolve_params(step["params"], context)

            # Call tool
            result = await client_adapter.call_tool(step["tool"], params)

            step_duration = (time.perf_counter() - step_start) * 1000

            # Validate if validator provided
            validation_passed = True
            validation_error = None
            if "validation" in step and callable(step["validation"]):
                try:
                    validation_passed = step["validation"](result, context)
                except Exception as e:
                    validation_passed = False
                    validation_error = f"Validation error: {e}"

            step_result = {
                "step_number": i + 1,
                "description": step.get("description", f"Step {i+1}"),
                "tool": step["tool"],
                "success": result["success"] and validation_passed,
                "duration_ms": step_duration,
                "result": result.get("response"),
                "error": result.get("error") or validation_error,
            }

            step_results.append(step_result)

            # Stop on failure
            if not step_result["success"]:
                break

            # Save to context if specified
            if "save_to_context" in step and result.get("response"):
                context[step["save_to_context"]] = result["response"]

        total_duration = (time.perf_counter() - start) * 1000
        steps_completed = sum(1 for s in step_results if s["success"])

        return {
            "success": steps_completed == len(self.steps),
            "story_name": self.story_name,
            "steps_completed": steps_completed,
            "steps_total": len(self.steps),
            "step_results": step_results,
            "duration_ms": total_duration,
            "context": context,
        }

    def _resolve_params(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve context variables in parameters."""
        resolved = {}
        for key, value in params.items():
            if isinstance(value, str) and value.startswith("$context."):
                # Extract from context
                context_key = value.replace("$context.", "")
                resolved[key] = context.get(context_key)
            else:
                resolved[key] = value
        return resolved


class IntegrationPattern(TestPattern):
    """Pattern for integration testing across multiple tools."""

    def __init__(self, tools: List[str], workflow: Callable):
        """
        Initialize integration pattern.

        Args:
            tools: List of tools involved
            workflow: Async function(client_adapter) -> Dict[str, Any]
        """
        self.tools = tools
        self.workflow = workflow

    async def execute(self, client_adapter: AtomsMCPClientAdapter) -> Dict[str, Any]:
        """
        Execute integration pattern.

        Returns:
            {
                "success": bool,
                "tools_used": List[str],
                "result": Any,
                "duration_ms": float
            }
        """
        start = time.perf_counter()

        try:
            result = await self.workflow(client_adapter)
            duration = (time.perf_counter() - start) * 1000

            return {
                "success": result.get("success", True),
                "tools_used": self.tools,
                "result": result,
                "duration_ms": duration,
            }

        except Exception as e:
            duration = (time.perf_counter() - start) * 1000

            return {
                "success": False,
                "tools_used": self.tools,
                "result": None,
                "error": str(e),
                "duration_ms": duration,
            }
