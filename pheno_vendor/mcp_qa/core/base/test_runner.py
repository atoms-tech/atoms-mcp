"""
Base Test Runner for MCP Testing

Abstract base class providing common test execution infrastructure.
Projects extend this to implement project-specific test execution logic.

Provides:
- Parallel/sequential execution with worker isolation
- Progress tracking (tqdm)
- Cache integration
- Reporter coordination
- Auto-discovery via decorators
- Detailed error capturing for debugging
- Configurable concurrency limits
- Worker-specific environment isolation
- Thread-safe test execution with asyncio.gather()
- Semaphore for concurrency control
- Worker ID assignment for debugging
- Progress tracking across workers
- Error isolation (one worker failure doesn't crash all)
- Result aggregation from parallel runs

Example:
    class MyProjectRunner(BaseTestRunner):
        def _get_adapter_class(self):
            return MyProjectClientAdapter
        
        def _get_metadata(self) -> Dict[str, Any]:
            return {
                "endpoint": self.client_adapter.endpoint,
                "project": "my-project"
            }
"""

import asyncio
import os
import sys
import threading
import time
import traceback
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

# Import logging utilities
try:
    from mcp_qa.testing.logging_config import QuietLogger
except ImportError:
    # Fallback if logging_config not available
    class QuietLogger:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass

# Import from mcp_qa.core (shared components)
try:
    from ..cache import TestCache
    from ..test_registry import get_test_registry
    from mcp_qa.reporters import ConsoleReporter, TestReporter
except ImportError:
    # Fallback imports for standalone use
    from mcp_qa.core.cache import TestCache
    from mcp_qa.core.test_registry import get_test_registry
    from mcp_qa.reporters import ConsoleReporter, TestReporter


class BaseTestRunner(ABC):
    """
    Abstract base class for MCP test runners.
    
    Provides common infrastructure for test execution while allowing
    projects to customize specific behaviors.
    
    Projects must implement:
    - _get_adapter_class(): Return the project's client adapter class
    - _get_metadata(): Return project-specific metadata for reports
    """

    def __init__(
        self,
        client_adapter: Any,  # BaseClientAdapter or subclass
        cache: bool = True,
        parallel: bool = False,
        parallel_workers: int = None,
        reporters: Optional[List[TestReporter]] = None,
        use_optimizations: bool = True,
        verbose: bool = False,  # Enable verbose logging
    ):
        self.client_adapter = client_adapter
        self.use_cache = cache
        self.parallel = parallel
        self.use_optimizations = use_optimizations
        self.verbose = verbose

        # Auto-detect optimal workers if not specified
        if parallel_workers is None and parallel:
            try:
                import os
                parallel_workers = os.cpu_count() or 4
                if verbose:
                    print(f"🔧 Auto-detected optimal workers: {parallel_workers}")
            except Exception:
                parallel_workers = 4

        self.parallel_workers = max(1, parallel_workers or 4)
        self.cache_instance = TestCache() if cache else None
        self.reporters = reporters or [ConsoleReporter()]
        self.test_registry = get_test_registry()
        self.results: List[Dict[str, Any]] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

        # Connection pooling
        self.connection_pool = None
        self.response_cache = None

        # Initialize optimizations
        if use_optimizations:
            try:
                from ..optimizations import PooledMCPClient, ResponseCacheLayer
                # Will be initialized when tests start
                self._pool_class = PooledMCPClient
                self._cache_class = ResponseCacheLayer
            except (ImportError, ValueError):
                # Import might fail if optimizations not available yet
                self._pool_class = None
                self._cache_class = None

        # Worker management for parallel execution
        self._worker_lock = threading.Lock()
        self._active_workers: Set[int] = set()
        self._worker_errors: Dict[int, List[str]] = {}
        self._results_lock = threading.Lock()  # Thread-safe result aggregation
        self._semaphore: Optional[asyncio.Semaphore] = None  # Concurrency control
        self._worker_envs: Dict[int, Dict[str, str]] = {}  # Worker-specific environments

    def _get_worker_id(self) -> int:
        """Get unique worker ID for the current thread/task."""
        try:
            # Try to get asyncio task name (if running in async context)
            task = asyncio.current_task()
            if task:
                return hash(task) % 10000
        except RuntimeError:
            pass

        # Fall back to thread ID
        return threading.get_ident() % 10000

    def _setup_worker_environment(self, worker_id: int) -> None:
        """Set up worker-specific environment isolation."""
        with self._worker_lock:
            if worker_id not in self._worker_envs:
                # Create worker-specific environment variables
                self._worker_envs[worker_id] = {
                    "TEST_WORKER_ID": str(worker_id),
                    "TEST_WORKER_TEMP": f"/tmp/test_worker_{worker_id}",
                }
                self._active_workers.add(worker_id)
                self._worker_errors[worker_id] = []

                # Apply environment variables (thread-local)
                for key, value in self._worker_envs[worker_id].items():
                    os.environ[f"{key}_{worker_id}"] = value

    def _cleanup_worker_environment(self, worker_id: int) -> None:
        """Clean up worker-specific environment."""
        with self._worker_lock:
            if worker_id in self._worker_envs:
                # Remove worker-specific environment variables
                for key in self._worker_envs[worker_id].keys():
                    os.environ.pop(f"{key}_{worker_id}", None)

                self._active_workers.discard(worker_id)
                del self._worker_envs[worker_id]

    async def _initialize_connection_pool(self):
        """Initialize connection pool for parallel execution."""
        if not self.parallel or not self.use_optimizations:
            return
        
        if not self._pool_class or not self._cache_class:
            return  # Optimizations not available

        try:
            # Extract base URL from client
            base_url = self._extract_base_url()
            
            # Create connection pool with base URL
            self.connection_pool = self._pool_class(
                base_url=base_url,
                min_connections=self.parallel_workers,
                max_connections=self.parallel_workers * 2,
            )

            await self.connection_pool.initialize()

            # Initialize response cache
            self.response_cache = self._cache_class(max_size=1000, default_ttl=60)

            print("✅ Performance optimizations active")
            print(f"   Connection pool: {self.parallel_workers}-{self.parallel_workers * 2} clients")
            print("   Response cache: LRU (1000 entries, 60s TTL)")

        except Exception as e:
            print(f"⚠️  Connection pool initialization failed: {e}")
            print("   Falling back to single client (will be slower)")
    
    def _extract_base_url(self) -> str:
        """Extract base URL from client (overridable by projects)."""
        client = self.client_adapter.client
        if hasattr(client, 'mcp_url'):
            return client.mcp_url
        elif hasattr(client, '_client') and hasattr(client._client, 'mcp_url'):
            return client._client.mcp_url
        elif hasattr(client, 'url'):
            return client.url
        else:
            return getattr(client, 'base_url', 'http://localhost:8000')

    async def run_all(self, categories: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Run all registered tests.

        Args:
            categories: Optional list of categories to run (e.g., ["core", "entity"])

        Returns:
            {
                "total": int,
                "passed": int,
                "failed": int,
                "skipped": int,
                "cached": int,
                "duration_seconds": float,
                "results": List[Dict],
                "worker_stats": Dict (if parallel mode)
            }
        """
        self.start_time = datetime.now()
        self.results = []

        # Initialize connection pool FIRST for parallel execution
        if self.parallel:
            await self._initialize_connection_pool()
            self._semaphore = asyncio.Semaphore(self.parallel_workers)

        # Get tests to run
        if categories:
            tests_to_run = {}
            for cat in categories:
                tests_to_run.update(self.test_registry.get_tests(cat))
        else:
            tests_to_run = self.test_registry.get_tests()

        if not tests_to_run:
            print("⚠️  No tests found")
            return {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "cached": 0,
                "duration_seconds": 0,
                "results": [],
            }

        # Group tests by category
        by_category: Dict[str, List] = {}
        for test_name, test_info in tests_to_run.items():
            category = test_info["category"]
            by_category.setdefault(category, []).append((test_name, test_info))

        # Sort categories by priority (can be overridden by projects)
        category_order = self._get_category_order()
        sorted_categories = sorted(
            by_category.items(), key=lambda x: category_order.index(x[0]) if x[0] in category_order else 999
        )

        total_tests = len(tests_to_run)

        # Display parallel execution info
        if self.parallel:
            print(f"🔄 Parallel execution enabled: {self.parallel_workers} workers")

        # Use enhanced progress display
        try:
            from .progress_display import ComprehensiveProgressDisplay

            progress_display = ComprehensiveProgressDisplay(
                total_tests=total_tests,
                categories=list(by_category.keys()),
                parallel=self.parallel,
                workers=self.parallel_workers,
            )
            use_enhanced_progress = True
            
            # Disable ConsoleReporter live progress (enhanced display will handle it)
            for reporter in self.reporters:
                if hasattr(reporter, 'show_running'):
                    reporter.show_running = False
        except ImportError:
            use_enhanced_progress = False
            # Fallback to tqdm
            if HAS_TQDM:
                pbar = tqdm(
                    total=total_tests,
                    desc="Running tests",
                    unit="test",
                    bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]",
                )
            else:
                pbar = None

        try:
            # Start enhanced progress display
            if use_enhanced_progress:
                with progress_display as prog:
                    # Set category totals
                    for category, tests in by_category.items():
                        prog.set_category_total(category, len(tests))

                    # Run tests
                    await self._run_with_enhanced_progress(sorted_categories, prog)
            else:
                # Use tqdm or basic output
                await self._run_with_basic_progress(sorted_categories, pbar)

        finally:
            if not use_enhanced_progress and pbar:
                pbar.close()
        
        # Mark end time
        self.end_time = datetime.now()

        # Generate reports
        metadata = self._get_metadata()
        metadata.update({
            "auth_status": "authenticated",
            "duration_seconds": (self.end_time - self.start_time).total_seconds(),
            "parallel_mode": self.parallel,
            "parallel_workers": self.parallel_workers if self.parallel else 1,
        })

        for reporter in self.reporters:
            reporter.report(self.results, metadata)

        # Return summary
        passed = sum(1 for r in self.results if r.get("success") and not r.get("skipped"))
        failed = sum(1 for r in self.results if not r.get("success") and not r.get("skipped"))
        skipped = sum(1 for r in self.results if r.get("skipped"))
        cached = sum(1 for r in self.results if r.get("cached"))

        summary = {
            "total": len(self.results),
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "cached": cached,
            "duration_seconds": (self.end_time - self.start_time).total_seconds(),
            "results": self.results,
        }

        # Add worker statistics for parallel runs
        if self.parallel:
            summary["worker_stats"] = {
                "workers_used": len(self._worker_errors),
                "worker_errors": {wid: len(errs) for wid, errs in self._worker_errors.items()},
            }

        return summary

    async def _run_with_enhanced_progress(self, sorted_categories, progress_display):
        """Run tests with enhanced progress display."""
        for category, tests in sorted_categories:
            progress_display.write(f"\n📋 {category.upper()} Tests")

            if self.parallel:
                # Parallel execution
                tasks = [
                    self._run_single_test_with_worker_enhanced(test_name, test_info, category, progress_display)
                    for test_name, test_info in tests
                ]
                await asyncio.gather(*tasks, return_exceptions=True)
            else:
                # Sequential execution
                for test_name, test_info in tests:
                    await self._run_single_test_enhanced(test_name, test_info, category, progress_display)

    async def _run_with_basic_progress(self, sorted_categories, pbar):
        """Run tests with basic tqdm progress."""
        try:
            for category, tests in sorted_categories:
                if pbar:
                    pbar.write(f"\n📋 {category.upper()} Tests")
                else:
                    print(f"\n📋 {category.upper()} Tests")

                # ALWAYS use parallel execution for speed
                if self.parallel and len(tests) > 1:
                    # Parallel execution with worker pool
                    print(f"   🔄 Running {len(tests)} tests in parallel across {self.parallel_workers} workers...")

                    tasks = [
                        self._run_single_test_with_worker(test_name, test_info, pbar)
                        for test_name, test_info in tests
                    ]

                    # Execute all tests in parallel
                    results = await asyncio.gather(*tasks, return_exceptions=True)

                    # Log any worker exceptions
                    for i, result in enumerate(results):
                        if isinstance(result, Exception):
                            test_name, test_info = tests[i]
                            error_msg = str(result)

                            # Check if it's a lock error or connection issue
                            if "not holding this lock" in error_msg or "RuntimeError" in str(type(result)) or "530" in error_msg or "502" in error_msg:
                                print("\n⚠️  Connection/lock issue detected in worker")
                                print("   Treating as connection loss - cache invalidated")

                                # Clear cache
                                if self.cache_instance:
                                    self.cache_instance.clear()

                                if pbar:
                                    pbar.write(f"⚠️  {test_name} - Connection issue (will retry next run)")
                                else:
                                    print(f"⚠️  {test_name} - Connection issue (will retry next run)")
                            else:
                                # Show full error for debugging import issues
                                if "ModuleNotFoundError" in error_msg or "ImportError" in error_msg:
                                    print(f"\n❌ {test_name} - Import Error:")
                                    print(f"   {error_msg}")
                                    import traceback
                                    if hasattr(result, '__traceback__'):
                                        traceback.print_exception(type(result), result, result.__traceback__)
                                elif pbar:
                                    pbar.write(f"❌ {test_name} - Worker failed: {error_msg[:100]}")
                                else:
                                    print(f"❌ {test_name} - Worker failed: {error_msg[:100]}")
                else:
                    # Sequential fallback for single test or if parallel disabled
                    for test_name, test_info in tests:
                        await self._run_single_test(test_name, test_info, pbar)

        finally:
            if pbar:
                pbar.close()

            # Cleanup all worker environments
            for worker_id in list(self._active_workers):
                self._cleanup_worker_environment(worker_id)

    async def _run_single_test_enhanced(self, test_name: str, test_info: Dict[str, Any], category: str, progress_display, worker_id: Optional[int] = None):
        """Run single test with enhanced progress display."""
        tool_name = test_info["tool_name"]

        # Set current test in progress display (before execution)
        progress_display.set_current_test(
            test_name=test_name,
            tool_name=tool_name,
            category=category,
            worker_id=worker_id,
        )

        # Run test (reuse existing logic)
        await self._run_single_test(test_name, test_info, None, worker_id=worker_id)

        # Get last result and update progress display
        if self.results:
            result = self.results[-1]
            progress_display.update(
                test_name=test_name,
                tool_name=tool_name,
                category=category,
                success=result.get("success", False),
                duration_ms=result.get("duration_ms", 0),
                cached=result.get("cached", False),
                skipped=result.get("skipped", False),
                worker_id=worker_id,
            )

    async def _run_single_test_with_worker_enhanced(self, test_name: str, test_info: Dict[str, Any], category: str, progress_display):
        """Run single test with worker + enhanced progress."""
        # Acquire semaphore
        async with self._semaphore:
            worker_id = self._get_worker_id()
            self._setup_worker_environment(worker_id)

            try:
                await self._run_single_test_enhanced(test_name, test_info, category, progress_display, worker_id=worker_id)
            except Exception as e:
                with self._worker_lock:
                    self._worker_errors[worker_id].append(str(e))
                raise

    async def _run_single_test_with_worker(
        self, test_name: str, test_info: Dict[str, Any], pbar: Optional[Any] = None
    ) -> None:
        """Run a single test with worker isolation and dedicated MCP client."""
        # Acquire semaphore to limit concurrent execution
        async with self._semaphore:
            # Get worker ID and setup environment
            worker_id = self._get_worker_id()
            self._setup_worker_environment(worker_id)

            # Get dedicated client from ParallelClientManager
            worker_client = None
            if hasattr(self, 'client_manager') and self.client_manager:
                try:
                    worker_client = await self.client_manager.acquire(timeout=10.0)
                except Exception as e:
                    print(f"⚠️  Worker {worker_id} couldn't acquire client: {e}")

            try:
                # Create adapter with worker's dedicated client
                if worker_client:
                    from .adapters import AtomsMCPClientAdapter
                    worker_adapter = AtomsMCPClientAdapter(worker_client, verbose_on_fail=True)

                    # Temporarily swap adapter for this test
                    original_adapter = self.client_adapter
                    self.client_adapter = worker_adapter

                    try:
                        await self._run_single_test(test_name, test_info, pbar, worker_id=worker_id)
                    finally:
                        # Restore original adapter
                        self.client_adapter = original_adapter
                else:
                    # Fallback to shared client (sequential mode)
                    await self._run_single_test(test_name, test_info, pbar, worker_id=worker_id)

            except Exception as e:
                # Log worker error
                error_msg = f"Test {test_name} failed in worker {worker_id}: {str(e)}"
                with self._worker_lock:
                    self._worker_errors[worker_id].append(error_msg)
                raise
            finally:
                # Return client to pool
                if worker_client and hasattr(self, 'client_manager') and self.client_manager:
                    await self.client_manager.release(worker_client)

    async def _run_single_test(
        self, test_name: str, test_info: Dict[str, Any], pbar: Optional[Any] = None, worker_id: Optional[int] = None
    ) -> None:
        """Run a single test with caching, timing, and error handling."""
        test_func = test_info["func"]
        tool_name = test_info["tool_name"]

        # Check cache
        if self.cache_instance and self.cache_instance.should_skip(test_name, tool_name):
            result = {
                "test_name": test_name,
                "tool_name": tool_name,
                "success": True,
                "cached": True,
                "skipped": False,
                "duration_ms": 0,
                "error": None,
                "worker_id": worker_id,
            }

            # Thread-safe result aggregation
            with self._results_lock:
                self.results.append(result)

            # Silent for cached tests - just update progress
            if pbar:
                pbar.update(1)
            # No output for cached tests
            return

        # Notify reporters that test is starting
        for reporter in self.reporters:
            if hasattr(reporter, 'on_test_start'):
                try:
                    reporter.on_test_start(test_name, test_info)
                except Exception:
                    pass  # Ignore reporter errors
        
        # Run test
        start = time.time()
        test_timeout = 60.0  # 60 second timeout per test
        warning_threshold = 10.0  # Warn after 10 seconds

        async def warning_task():
            """Background task to warn about slow tests."""
            await asyncio.sleep(warning_threshold)
            print(f"\n⚠️  Test {test_name} is taking longer than expected (>{warning_threshold}s)")

        # Start warning task in background
        warning_handle = asyncio.create_task(warning_task())

        try:
            # Call test function with client adapter
            # Use QuietLogger to suppress logs unless verbose mode is enabled
            if self.verbose:
                test_result = await asyncio.wait_for(test_func(self.client_adapter), timeout=test_timeout)
            else:
                with QuietLogger():
                    test_result = await asyncio.wait_for(test_func(self.client_adapter), timeout=test_timeout)

            duration_ms = (time.time() - start) * 1000

            # Cancel warning task if still running
            if not warning_handle.done():
                warning_handle.cancel()
                try:
                    await warning_handle
                except asyncio.CancelledError:
                    pass

            # Parse result
            if isinstance(test_result, dict):
                success = test_result.get("success", False)
                error = test_result.get("error")
                skipped = test_result.get("skipped", False)
            else:
                # If test returned None and didn't raise exception, it passed
                # (tests using assert statements return None on success)
                success = True if test_result is None else bool(test_result)
                error = None
                skipped = False

            result = {
                "test_name": test_name,
                "tool_name": tool_name,
                "success": success,
                "cached": False,
                "skipped": skipped,
                "duration_ms": duration_ms,
                "error": error,
                "worker_id": worker_id,
            }

            # Update cache
            if self.cache_instance and not skipped:
                status = "passed" if success else "failed"
                self.cache_instance.record(test_name, tool_name, status, duration_ms / 1000, error)

            # Thread-safe result aggregation
            with self._results_lock:
                self.results.append(result)
            
            # Notify reporters that test completed
            for reporter in self.reporters:
                if hasattr(reporter, 'on_test_complete'):
                    try:
                        reporter.on_test_complete(test_name, result)
                    except Exception:
                        pass  # Ignore reporter errors

            # Output: ONLY failures, suppress success/skip/cached
            if pbar:
                pbar.update(1)
                if not success and not skipped:  # Only print failures
                    print(f"❌ {test_name} ({duration_ms:.2f}ms)")
            elif not success and not skipped:
                print(f"❌ {test_name} ({duration_ms:.2f}ms)")

        except asyncio.TimeoutError:
            # Cancel warning task
            if not warning_handle.done():
                warning_handle.cancel()
                try:
                    await warning_handle
                except asyncio.CancelledError:
                    pass

            duration_ms = (time.time() - start) * 1000
            error = f"Test timeout after {test_timeout}s"

            result = {
                "test_name": test_name,
                "tool_name": tool_name,
                "success": False,
                "cached": False,
                "skipped": False,
                "duration_ms": duration_ms,
                "error": error,
                "worker_id": worker_id,
            }

            if self.cache_instance:
                self.cache_instance.record(test_name, tool_name, "timeout", duration_ms / 1000, error)

            # Thread-safe result aggregation
            with self._results_lock:
                self.results.append(result)

            worker_tag = f" [W{worker_id}]" if worker_id is not None else ""
            if pbar:
                pbar.update(1)
                pbar.write(f"⏱️  {test_name} - TIMEOUT ({test_timeout}s){worker_tag}")
            else:
                print(f"⏱️  {test_name} - TIMEOUT ({test_timeout}s){worker_tag}")

        except Exception as e:
            # Cancel warning task
            if not warning_handle.done():
                warning_handle.cancel()
                try:
                    await warning_handle
                except asyncio.CancelledError:
                    pass

            duration_ms = (time.time() - start) * 1000

            # Capture detailed error information
            exc_type, exc_value, exc_tb = sys.exc_info()

            # Check if this is a pytest.skip exception
            is_skip = exc_type and exc_type.__name__ in ('Skipped', 'SkipTest', 'TestSkipped')

            if is_skip:
                # Treat as skipped test, not failure
                result = {
                    "test_name": test_name,
                    "tool_name": tool_name,
                    "success": True,  # Skip is not a failure
                    "cached": False,
                    "skipped": True,
                    "duration_ms": duration_ms,
                    "error": None,
                    "skip_reason": str(e),
                    "worker_id": worker_id,
                }
                
                # Thread-safe result aggregation
                with self._results_lock:
                    self.results.append(result)
                
                # Update progress without printing
                if pbar:
                    pbar.update(1)
                return

            tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))

            # Format error message based on exception type
            error_msg = str(e)
            if exc_type and exc_type.__name__ == 'AssertionError':
                # For AssertionError, show the assertion message clearly
                if error_msg:
                    error = f"AssertionError: {error_msg}"
                else:
                    error = "AssertionError: (assertion failed without message)"
            else:
                # For other exceptions, use the exception message
                error = error_msg if error_msg and error_msg.strip() else f"{exc_type.__name__ if exc_type else 'Exception'}: (no error message)"

            # Try to capture local variables from the test function frame
            locals_data = {}
            if exc_tb:
                frame = exc_tb.tb_frame
                # Get locals from the frame where the exception occurred
                try:
                    locals_data = {k: v for k, v in frame.f_locals.items() if not k.startswith("_") and k != "self"}
                except Exception:
                    pass

            result = {
                "test_name": test_name,
                "tool_name": tool_name,
                "success": False,
                "cached": False,
                "skipped": False,
                "duration_ms": duration_ms,
                "error": error,
                "traceback": tb_str,
                "locals": locals_data,
                "worker_id": worker_id,
            }

            # Try to extract request/response if available from locals
            if "result" in locals_data and isinstance(locals_data["result"], dict):
                result["response"] = locals_data["result"].get("response")

            # Try to extract request parameters
            if "data" in locals_data:
                result["request_params"] = {
                    "entity_type": locals_data.get("entity_type"),
                    "operation": locals_data.get("operation"),
                    "data": locals_data.get("data"),
                }

            if self.cache_instance:
                self.cache_instance.record(test_name, tool_name, "error", duration_ms / 1000, error)

            # Thread-safe result aggregation
            with self._results_lock:
                self.results.append(result)

            worker_tag = f" [W{worker_id}]" if worker_id is not None else ""
            if pbar:
                pbar.update(1)
                pbar.write(f"❌ {test_name} - {error[:50]}{worker_tag}")
            else:
                print(f"❌ {test_name} - {error[:50]}{worker_tag}")


    # ============================================================================
    # ABSTRACT METHODS - Projects must implement these
    # ============================================================================
    
    @abstractmethod
    def _get_metadata(self) -> Dict[str, Any]:
        """
        Get project-specific metadata for test reports.
        
        Returns:
            Dict with metadata like endpoint, project name, etc.
            
        Example:
            return {
                "endpoint": self.client_adapter.endpoint,
                "project": "atoms",
                "environment": "production"
            }
        """
        pass
    
    def _get_category_order(self) -> List[str]:
        """
        Get test category execution order (overridable).
        
        Returns:
            List of category names in execution order
        """
        return ["core", "entity", "query", "relationship", "workflow", "integration"]
    
    def _get_adapter_class(self):
        """
        Get the project client adapter class (optional override).
        
        Returns:
            Client adapter class (e.g., AtomsMCPClientAdapter)
        """
        return None


__all__ = ["BaseTestRunner"]

