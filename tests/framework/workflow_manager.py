"""Workflow helpers for coordinated test execution."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import Any

from workflow_kit.task import Worker, task


class TestWorkflowManager:
    """Manage test execution through workflow-kit workers."""

    def __init__(self, concurrency: int = 4, test_timeout: float = 60.0, warning_threshold: float = 10.0):
        self.worker = Worker(concurrency=concurrency)
        self.worker.register(self._execute_test_task)
        self._started = False
        self.test_timeout = test_timeout  # Maximum time for test execution
        self.warning_threshold = warning_threshold  # Warn if test takes longer than this

    async def run_test(
        self,
        *,
        test_name: str,
        callback: Callable[[], Awaitable[Any]],
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute a callback via the workflow worker."""
        await self._ensure_started()
        context = dict(metadata or {})
        context.setdefault("test_name", test_name)
        return await self._execute_test_task(callback, context)

    async def _ensure_started(self) -> None:
        if not self._started:
            await self.worker.start()
            self._started = True

    @task()
    async def _execute_test_task(
        self,
        callback: Callable[[], Awaitable[Any]],
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        start = time.time()
        test_name = metadata.get("test_name", "unknown")
        warning_printed = False

        async def warning_task():
            """Background task to warn about slow tests."""
            nonlocal warning_printed
            await asyncio.sleep(self.warning_threshold)
            if not warning_printed:
                print(f"\n⚠️  Test {test_name} is taking longer than expected (>{self.warning_threshold}s)")
                warning_printed = True

        # Start warning task in background
        warning_handle = asyncio.create_task(warning_task())

        try:
            # Execute test with timeout
            result = await asyncio.wait_for(callback(), timeout=self.test_timeout)
            duration = time.time() - start

            # Cancel warning task if still running
            if not warning_handle.done():
                warning_handle.cancel()
                try:
                    await warning_handle
                except asyncio.CancelledError:
                    pass

            return {
                "result": result,
                "metadata": metadata,
                "duration": duration,
            }

        except TimeoutError:
            # Cancel warning task
            if not warning_handle.done():
                warning_handle.cancel()
                try:
                    await warning_handle
                except asyncio.CancelledError:
                    pass

            duration = time.time() - start
            # Return timeout error as test result
            return {
                "result": {
                    "success": False,
                    "error": f"Test timeout after {self.test_timeout}s",
                    "skipped": False,
                },
                "metadata": metadata,
                "duration": duration,
            }

        except Exception:
            # Cancel warning task
            if not warning_handle.done():
                warning_handle.cancel()
                try:
                    await warning_handle
                except asyncio.CancelledError:
                    pass
            raise


__all__ = ["TestWorkflowManager"]
