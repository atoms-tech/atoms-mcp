"""
MCP Tool Monitoring Example

Demonstrates how to monitor MCP tool executions with comprehensive
observability including metrics, logging, and performance tracking.

Author: Atoms MCP Platform
"""

import asyncio
from typing import Any, Dict, List

from lib.atoms.observability import (
    observe_tool,
    get_logger,
    LogContext,
    record_tool_execution,
    measure_performance,
    webhook_manager,
    AlertSeverity,
)

logger = get_logger(__name__)


# ============================================================================
# Example MCP Tools with Observability
# ============================================================================

@observe_tool("search_repository", track_performance=True, log_inputs=True)
async def search_repository(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Search code repository with automatic monitoring.

    The @observe_tool decorator provides:
    - Automatic metric collection
    - Input/output logging
    - Performance tracking
    - Error handling
    """
    logger.info(f"Searching repository with query: {query}")

    # Simulate search operation
    await asyncio.sleep(0.5)

    results = [
        {
            "file": "main.py",
            "line": 42,
            "content": f"Match for: {query}"
        }
    ]

    return results


@observe_tool("execute_code", track_performance=True, log_outputs=False)
async def execute_code(code: str, language: str = "python") -> Dict[str, Any]:
    """
    Execute code with monitoring.

    Outputs are not logged for security (log_outputs=False).
    """
    logger.info(f"Executing {language} code")

    # Simulate code execution
    await asyncio.sleep(1.0)

    return {
        "status": "success",
        "output": "Code executed successfully",
        "execution_time_ms": 1000
    }


@observe_tool("analyze_file", track_performance=True)
@measure_performance("file_analysis", threshold_warning_ms=2000)
async def analyze_file(file_path: str) -> Dict[str, Any]:
    """
    Analyze file with performance thresholds.

    Combined decorators provide both tool monitoring and
    performance measurement with custom thresholds.
    """
    logger.info(f"Analyzing file: {file_path}")

    # Simulate file analysis
    await asyncio.sleep(1.5)

    analysis = {
        "lines": 150,
        "functions": 12,
        "complexity": 8
    }

    return analysis


# ============================================================================
# Manual Tool Monitoring (without decorators)
# ============================================================================

async def manual_tool_monitoring_example():
    """
    Example of manual tool monitoring for cases where
    decorators can't be used.
    """
    import time

    tool_name = "custom_tool"
    start_time = time.perf_counter()

    try:
        # Execute tool logic
        result = await perform_custom_operation()

        # Calculate duration
        duration = time.perf_counter() - start_time

        # Record success
        record_tool_execution(tool_name, duration, success=True)

        logger.info(
            f"Tool {tool_name} completed",
            extra_fields={
                "duration_ms": duration * 1000,
                "status": "success"
            }
        )

        return result

    except Exception as e:
        # Calculate duration
        duration = time.perf_counter() - start_time

        # Record failure
        record_tool_execution(tool_name, duration, success=False)

        logger.error(
            f"Tool {tool_name} failed",
            extra_fields={
                "duration_ms": duration * 1000,
                "error_type": type(e).__name__,
                "error_message": str(e)
            },
            exc_info=True
        )

        raise


async def perform_custom_operation():
    """Placeholder for custom operation."""
    await asyncio.sleep(0.3)
    return {"status": "completed"}


# ============================================================================
# Tool Chain Monitoring
# ============================================================================

async def monitored_tool_chain(user_query: str):
    """
    Monitor a chain of tool executions.

    Demonstrates how to track multiple tools in a workflow
    with proper context propagation.
    """
    # Set context for entire chain
    with LogContext(correlation_id=f"chain_{user_query[:8]}"):
        logger.info("Starting tool chain", extra_fields={"query": user_query})

        try:
            # Step 1: Search repository
            search_results = await search_repository(user_query)

            # Step 2: Analyze first result
            if search_results:
                first_file = search_results[0]["file"]
                analysis = await analyze_file(first_file)

                # Step 3: Execute some code based on analysis
                if analysis["complexity"] > 5:
                    code = "print('Complex file detected')"
                    execution_result = await execute_code(code)

                    logger.info(
                        "Tool chain completed successfully",
                        extra_fields={
                            "steps": 3,
                            "complexity": analysis["complexity"]
                        }
                    )

                    return {
                        "search_results": search_results,
                        "analysis": analysis,
                        "execution": execution_result
                    }

            return {"search_results": search_results}

        except Exception as e:
            logger.error("Tool chain failed", exc_info=True)

            # Send alert for chain failure
            await webhook_manager.send_error_alert(
                error_type=type(e).__name__,
                error_message=f"Tool chain failed: {str(e)}",
                source="tool_chain",
                metadata={"query": user_query}
            )

            raise


# ============================================================================
# Performance-Critical Tool
# ============================================================================

@observe_tool("real_time_analysis", track_performance=True)
@measure_performance("real_time", threshold_warning_ms=100, threshold_critical_ms=500)
async def real_time_analysis(data: List[float]) -> Dict[str, float]:
    """
    Performance-critical tool with strict thresholds.

    Warnings are logged if execution exceeds 100ms.
    Critical alerts if execution exceeds 500ms.
    """
    # Simulate real-time analysis
    await asyncio.sleep(0.05)

    return {
        "mean": sum(data) / len(data),
        "min": min(data),
        "max": max(data)
    }


# ============================================================================
# Error-Prone Tool with Monitoring
# ============================================================================

@observe_tool("unreliable_api_call", track_performance=True)
async def unreliable_api_call(endpoint: str, retry_count: int = 0) -> Dict[str, Any]:
    """
    Tool that might fail - monitoring captures errors.
    """
    logger.info(f"Calling API: {endpoint} (retry: {retry_count})")

    # Simulate API call that might fail
    import random
    if random.random() < 0.3:  # 30% failure rate
        raise Exception("API connection timeout")

    await asyncio.sleep(0.2)

    return {"status": "success", "data": "response"}


# ============================================================================
# Main Demo
# ============================================================================

async def main():
    """Run tool monitoring examples."""

    print("=== MCP Tool Monitoring Examples ===\n")

    # Example 1: Simple tool execution
    print("1. Simple tool execution with monitoring:")
    results = await search_repository("TODO", max_results=5)
    print(f"   Search results: {len(results)} items\n")

    # Example 2: Tool chain
    print("2. Tool chain with context propagation:")
    chain_result = await monitored_tool_chain("find_bugs")
    print(f"   Chain completed with {len(chain_result)} results\n")

    # Example 3: Performance-critical tool
    print("3. Performance-critical tool:")
    data = [1.0, 2.0, 3.0, 4.0, 5.0]
    analysis = await real_time_analysis(data)
    print(f"   Analysis: mean={analysis['mean']:.2f}\n")

    # Example 4: Manual monitoring
    print("4. Manual tool monitoring:")
    custom_result = await manual_tool_monitoring_example()
    print(f"   Custom tool: {custom_result}\n")

    # Example 5: Error handling with monitoring
    print("5. Error-prone tool with retries:")
    max_retries = 3
    for retry in range(max_retries):
        try:
            result = await unreliable_api_call("/api/data", retry_count=retry)
            print(f"   API call succeeded on attempt {retry + 1}\n")
            break
        except Exception as e:
            if retry == max_retries - 1:
                print(f"   API call failed after {max_retries} attempts\n")
            else:
                print(f"   Retry {retry + 1} failed, retrying...")
                await asyncio.sleep(0.5)

    print("=== All examples completed ===")


if __name__ == "__main__":
    asyncio.run(main())
