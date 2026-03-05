"""
User Story Pattern for Test Framework

Provides a pattern for testing multi-step user workflows.
"""

from typing import Any


class UserStoryPattern:
    """Pattern for testing multi-step user workflows."""

    def __init__(self, story_name: str, steps: list[dict[str, Any]], context: dict[str, Any] | None = None):
        """Initialize a user story pattern.

        Args:
            story_name: Name of the user story
            steps: List of steps in the workflow
            context: Optional initial context
        """
        self.story_name = story_name
        self.steps = steps
        self.context = context or {}

    async def execute(self, client_adapter) -> dict[str, Any]:
        """Execute the user story pattern.

        Args:
            client_adapter: MCP client adapter for making calls

        Returns:
            Dictionary containing execution results
        """
        results = []
        current_context = self.context.copy()

        for i, step in enumerate(self.steps):
            try:
                # Resolve context variables in parameters
                params = self._resolve_context_variables(step.get("params", {}), current_context)

                # Execute the step
                result = await client_adapter.call_tool(step["tool"], params)

                # Store result
                step_result = {
                    "step": i + 1,
                    "tool": step["tool"],
                    "description": step.get("description", ""),
                    "result": result,
                    "success": result.get("success", False),
                }

                # Run validation if provided
                if "validation" in step:
                    validation_func = step["validation"]
                    if callable(validation_func):
                        try:
                            validation_result = validation_func(result, current_context)
                            step_result["validation_passed"] = bool(validation_result)
                        except Exception as e:
                            step_result["validation_passed"] = False
                            step_result["validation_error"] = str(e)

                # Save to context if specified
                if "save_to_context" in step:
                    context_key = step["save_to_context"]
                    current_context[context_key] = result

                results.append(step_result)

                # Stop execution if step failed and no error handling specified
                if not step_result["success"] and not step.get("continue_on_failure", False):
                    break

            except Exception as e:
                step_result = {
                    "step": i + 1,
                    "tool": step["tool"],
                    "description": step.get("description", ""),
                    "result": None,
                    "success": False,
                    "error": str(e),
                }
                results.append(step_result)
                break

        # Calculate overall success
        all_successful = all(step.get("success", False) for step in results)
        all_validations_passed = all(step.get("validation_passed", True) for step in results)

        return {
            "story_name": self.story_name,
            "success": all_successful and all_validations_passed,
            "steps": results,
            "context": current_context,
            "total_steps": len(self.steps),
            "completed_steps": len(results),
        }

    def _resolve_context_variables(self, params: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        """Resolve context variables in parameters.

        Args:
            params: Parameters that may contain context variables
            context: Current context with variable values

        Returns:
            Parameters with context variables resolved
        """
        resolved_params = {}

        for key, value in params.items():
            if isinstance(value, str) and value.startswith("$context."):
                # Extract context path (e.g., "$context.org.data.id" -> ["org", "data", "id"])
                context_path = value[9:].split(".")  # Remove "$context." prefix

                # Navigate through context
                resolved_value: Any = context
                try:
                    for path_part in context_path:
                        if isinstance(resolved_value, dict) and path_part in resolved_value:
                            resolved_value = resolved_value[path_part]
                        else:
                            resolved_value = value  # Keep original if path not found
                            break
                    resolved_params[key] = resolved_value
                except (KeyError, TypeError, AttributeError):
                    resolved_params[key] = value  # Keep original if resolution fails
            elif isinstance(value, dict):
                # Recursively resolve nested dictionaries
                resolved_params[key] = self._resolve_context_variables(value, context)
            else:
                resolved_params[key] = value

        return resolved_params
