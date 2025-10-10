"""Atoms-specific extensions for the shared pheno-sdk test runner."""

import sys
import time
import traceback
from collections.abc import Awaitable, Callable
from typing import Any

from mcp_qa.core.base import BaseTestRunner

try:
    from mcp_qa.integration.workflows import WorkflowTester as TestWorkflowManager
except ImportError:
    # Fallback: create a simple workflow manager
    class TestWorkflowManager:
        def __init__(self, concurrency=4):
            self.concurrency = concurrency

        async def run_test(self, test_name, callback, metadata=None):
            import time
            start = time.time()
            result = await callback()
            duration = time.time() - start
            return {
                "result": result,
                "metadata": metadata or {},
                "duration": duration,
            }


class AtomsTestRunner(BaseTestRunner):
    """Test runner that layers workflow-kit orchestration atop the base runner."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.workflow_manager = TestWorkflowManager(concurrency=self.parallel_workers)

    def _get_metadata(self) -> dict[str, Any]:
        """Attach Atoms-specific metadata to reports."""
        return {
            "endpoint": getattr(self.client_adapter, "endpoint", "unknown"),
            "project": "atoms",
            "environment": "production",
            "adapter_type": "AtomsMCPClientAdapter",
        }

    def _get_category_order(self) -> list[str]:
        """Preferred execution order for Atoms test categories."""
        return ["core", "entity", "query", "relationship", "workflow", "integration"]

    async def _run_single_test(
        self,
        test_name: str,
        test_info: dict[str, Any],
        pbar: Any | None = None,
        worker_id: int | None = None,
    ) -> None:
        """Override to route execution through the workflow manager."""

        if self.workflow_manager is None:  # Defensive fallback
            await super()._run_single_test(test_name, test_info, pbar, worker_id=worker_id)
            return

        test_func: Callable[[Any], Awaitable[Any]] = test_info["func"]
        tool_name = test_info["tool_name"]

        if self.cache_instance:
            cached_result = self.cache_instance.cache.get(test_name, {})
            if cached_result.get("status") == "passed":
                result = {
                    "test_name": test_name,
                    "tool_name": tool_name,
                    "success": True,
                    "cached": True,
                    "skipped": False,
                    "duration_ms": 0,
                    "error": None,
                    "worker_id": worker_id,
                    "workflow_metadata": cached_result.get("metadata", {}),
                }
                with self._results_lock:
                    self.results.append(result)
                if pbar:
                    pbar.update(1)
                return

        async def _invoke() -> Any:
            return await test_func(self.client_adapter)

        try:
            workflow_payload = await self.workflow_manager.run_test(
                test_name=test_name,
                callback=_invoke,
                metadata={"tool_name": tool_name, "worker_id": worker_id},
            )
            test_result = workflow_payload["result"]
            duration_ms = workflow_payload["duration"] * 1000

            if isinstance(test_result, dict):
                success = test_result.get("success", False)
                error = test_result.get("error")
                skipped = test_result.get("skipped", False)
            else:
                success = bool(test_result)
                error = None
                skipped = False

            # Ensure failed tests have an error message
            if not success and not skipped and not error:
                error = "Test failed without error message (assertion failed)"

            result = {
                "test_name": test_name,
                "tool_name": tool_name,
                "success": success,
                "cached": False,
                "skipped": skipped,
                "duration_ms": duration_ms,
                "error": error,
                "worker_id": worker_id,
                "workflow_metadata": workflow_payload.get("metadata", {}),
            }

            if self.cache_instance and not skipped:
                status = "passed" if success else "failed"
                self.cache_instance.cache[test_name] = {
                    "status": status,
                    "timestamp": time.time(),
                    "tool_name": tool_name,
                    "metadata": result.get("workflow_metadata", {}),
                }
                self.cache_instance.record(test_name, tool_name, status, duration_ms / 1000, error)

            with self._results_lock:
                self.results.append(result)

            if pbar:
                pbar.update(1)
                if not success and not skipped:
                    error_msg = f": {error[:80]}" if error else ""
                    print(f"FAILED: {test_name} ({duration_ms:.2f}ms){error_msg}")
            elif not success and not skipped:
                error_msg = f": {error[:80]}" if error else ""
                print(f"FAILED: {test_name} ({duration_ms:.2f}ms){error_msg}")

        except Exception as exc:
            duration_ms = 0.0
            exc_type, exc_value, exc_tb = sys.exc_info()
            tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))

            # Extract meaningful error message from exception
            error_msg = str(exc)

            # For AssertionError, format it properly to show the assertion message
            if exc_type and exc_type.__name__ == "AssertionError":
                if error_msg:
                    error = f"AssertionError: {error_msg}"
                else:
                    error = "AssertionError: (assertion failed without message)"
            else:
                # For other exceptions, use the exception message or type name
                error = error_msg if error_msg and error_msg.strip() else f"{exc_type.__name__}: (no error message)"

            result = {
                "test_name": test_name,
                "tool_name": tool_name,
                "success": False,
                "cached": False,
                "skipped": False,
                "duration_ms": duration_ms,
                "error": error,
                "traceback": tb_str,
                "worker_id": worker_id,
                "workflow_metadata": {"tool_name": tool_name},
            }

            if self.cache_instance:
                self.cache_instance.cache[test_name] = {
                    "status": "error",
                    "timestamp": time.time(),
                    "tool_name": tool_name,
                }

            with self._results_lock:
                self.results.append(result)

            worker_tag = f" [W{worker_id}]" if worker_id is not None else ""
            # Display full error message in console, not just first 50 chars
            error_display = error if len(error) <= 200 else f"{error[:200]}..."
            verbose = getattr(self, "verbose", False)

            if pbar:
                pbar.update(1)
                pbar.write(f"ERROR: {test_name} - {error_display}{worker_tag}")
                # Show traceback in verbose mode
                if verbose:
                    pbar.write(tb_str)
            else:
                print(f"ERROR: {test_name} - {error_display}{worker_tag}")
                # Show traceback in verbose mode
                if verbose:
                    print(tb_str)


__all__ = ["AtomsTestRunner"]
