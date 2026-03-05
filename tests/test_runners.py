"""
Test runners for different execution modes (HOT, COLD, DRY).

This module contains:
- HotTestRunner: Real HTTP MCP client with Playwright auth
- ColdTestRunner: Real auth via API + in-memory fastmcp client
- DryTestRunner: Mock auth + in-memory fastmcp client
- ComprehensiveTestEvolutionRunner: Main orchestrator
"""

import time

from test_definitions import (
    ALL_TESTS,
    FASTMCP_AVAILABLE,
    PHENO_AVAILABLE,
    AuthKit,
    Client,
    InMemoryTransport,
    PlaywrightOAuthAdapter,
    RemoteTransport,
    TestResult,
    get_credential_broker,
)


class HotTestRunner:
    """HOT tests - Fully live with real HTTP MCP client and Playwright auth."""

    def __init__(self):
        self.playwright_adapter = PlaywrightOAuthAdapter()
        self.credential_broker = get_credential_broker() if PHENO_AVAILABLE else None

    async def run_hot_tests(self, _environment: str) -> TestResult:
        """Run HOT tests with real authentication and HTTP client."""
        if not PHENO_AVAILABLE or not FASTMCP_AVAILABLE:
            return TestResult(
                mode="HOT",
                total_tests=0,
                passed_tests=0,
                failed_tests=1,
                duration_seconds=0.0,
                details={"error": "Pheno SDK or FastMCP not available"}
            )

        start_time = time.time()

        try:
            # 1. Real auth via Playwright
            print("  🔐 Initializing real authentication via Playwright...")

            # Get atoms credentials from broker
            atoms_creds = await self.credential_broker.get_credential(
                "atoms_auth",
                default={"username": "test", "password": "test"}
            )

            # Real authentication with Playwright browser automation
            auth_result = await self.playwright_adapter.authenticate("atoms", atoms_creds)

            if not auth_result.get("success"):
                raise Exception(f"Authentication failed: {auth_result}")

            print("  ✅ Real authentication successful")

            # 2. Create real HTTP MCP client
            print("  🌐 Creating real HTTP MCP client...")

            # For HOT tests, we'd connect to actual MCP server
            # Using remote transport for real HTTP communication
            transport = RemoteTransport(url="https://atoms-mcp-prod.vercel.app/mcp")
            client = Client(transport)

            # Connect with real auth token
            await client.connect(auth_token=auth_result["tokens"]["access_token"])
            print("  ✅ Real HTTP MCP client connected")

            # 3. Run comprehensive test suite
            print("  🛠️  Executing comprehensive test suite...")

            results = []
            test_categories = ["entity", "query", "relationship", "workflow", "workspace", "error"]

            for category in test_categories:
                print(f"    📋 Running {category} tests...")
                category_tests = ALL_TESTS.get(category, [])

                for tool_name, params in category_tests:
                    try:
                        result = await client.call_tool(tool_name, params)
                        success = result.get("success", False)

                        results.append({
                            "category": category,
                            "tool": tool_name,
                            "params": params,
                            "success": success,
                            "result": result
                        })

                        if success:
                            print(f"      ✅ {tool_name}: Success")
                        # For error tests, failure is expected
                        elif category == "error":
                            print(f"      ✅ {tool_name}: Error handled correctly")
                            results[-1]["success"] = True
                        else:
                            print(f"      ❌ {tool_name}: {result.get('error', 'Unknown error')}")

                    except Exception as e:
                        # For error tests, exceptions are expected
                        if category == "error":
                            results.append({
                                "category": category,
                                "tool": tool_name,
                                "params": params,
                                "success": True,
                                "result": {"error": str(e), "expected": True}
                            })
                            print(f"      ✅ {tool_name}: Exception handled correctly")
                        else:
                            results.append({
                                "category": category,
                                "tool": tool_name,
                                "params": params,
                                "success": False,
                                "result": {"error": str(e)}
                            })
                            print(f"      ❌ {tool_name}: {e}")

            # 4. Cleanup
            print("  🧹 Cleaning up real connections...")
            await client.disconnect()
            await self.playwright_adapter.close()

            duration = time.time() - start_time

            # Calculate results
            total_tests = len(results)
            passed_tests = sum(1 for r in results if r["success"])
            failed_tests = total_tests - passed_tests

            # Group results by category
            category_results = {}
            for result in results:
                category = result["category"]
                if category not in category_results:
                    category_results[category] = {"total": 0, "passed": 0}
                category_results[category]["total"] += 1
                if result["success"]:
                    category_results[category]["passed"] += 1

            return TestResult(
                mode="HOT",
                total_tests=total_tests,
                passed_tests=passed_tests,
                failed_tests=failed_tests,
                duration_seconds=duration,
                details={
                    "auth_success": auth_result["success"],
                    "client_type": "real_http",
                    "categories": category_results,
                    "tools_tested": total_tests,
                    "results": results
                }
            )

        except Exception as e:
            duration = time.time() - start_time
            print(f"  ❌ HOT test failed: {e}")

            return TestResult(
                mode="HOT",
                total_tests=0,
                passed_tests=0,
                failed_tests=1,
                duration_seconds=duration,
                details={"error": str(e), "phase": "hot_test_execution"}
            )


class ColdTestRunner:
    """COLD tests - Real auth via API + in-memory fastmcp client."""

    def __init__(self):
        self.auth_kit = AuthKit(
            base_url="https://auth.atoms.tech",
            client_id="atoms-mcp-client"
        ) if PHENO_AVAILABLE else None

    async def run_cold_tests(self, _environment: str) -> TestResult:
        """Run COLD tests with AuthKit API and in-memory client."""
        if not PHENO_AVAILABLE or not FASTMCP_AVAILABLE:
            return TestResult(
                mode="COLD",
                total_tests=0,
                passed_tests=0,
                failed_tests=1,
                duration_seconds=0.0,
                details={"error": "Pheno SDK or FastMCP not available"}
            )

        start_time = time.time()

        try:
            # 1. Real auth via AuthKit API
            print("  🔐 Initializing real authentication via AuthKit API...")

            auth_result = await self.auth_kit.login_standalone_connect()

            if not auth_result.get("success"):
                raise Exception(f"Authentication failed: {auth_result}")

            print("  ✅ Real authentication successful")

            # 2. Create in-memory MCP client
            print("  💾 Creating in-memory MCP client...")

            transport = InMemoryTransport()
            client = Client(transport)

            # Connect with real auth token
            await client.connect(auth_token=auth_result["access_token"])
            print("  ✅ In-memory MCP client connected")

            # 3. Run comprehensive test suite
            print("  🛠️  Executing comprehensive test suite...")

            results = []
            test_categories = ["entity", "query", "relationship", "workflow", "workspace", "error"]

            for category in test_categories:
                print(f"    📋 Running {category} tests...")
                category_tests = ALL_TESTS.get(category, [])

                for tool_name, params in category_tests:
                    try:
                        result = await client.call_tool(tool_name, params)
                        success = result.get("success", False)

                        results.append({
                            "category": category,
                            "tool": tool_name,
                            "params": params,
                            "success": success,
                            "result": result
                        })

                        if success:
                            print(f"      ✅ {tool_name}: Success")
                        elif category == "error":
                            print(f"      ✅ {tool_name}: Error handled correctly")
                            results[-1]["success"] = True
                        else:
                            print(f"      ❌ {tool_name}: {result.get('error', 'Unknown error')}")

                    except Exception as e:
                        if category == "error":
                            results.append({
                                "category": category,
                                "tool": tool_name,
                                "params": params,
                                "success": True,
                                "result": {"error": str(e), "expected": True}
                            })
                            print(f"      ✅ {tool_name}: Exception handled correctly")
                        else:
                            results.append({
                                "category": category,
                                "tool": tool_name,
                                "params": params,
                                "success": False,
                                "result": {"error": str(e)}
                            })
                            print(f"      ❌ {tool_name}: {e}")

            # 4. Cleanup
            print("  🧹 Cleaning up connections...")
            await client.disconnect()
            await self.auth_kit.close()

            duration = time.time() - start_time

            # Calculate results
            total_tests = len(results)
            passed_tests = sum(1 for r in results if r["success"])
            failed_tests = total_tests - passed_tests

            # Group results by category
            category_results = {}
            for result in results:
                category = result["category"]
                if category not in category_results:
                    category_results[category] = {"total": 0, "passed": 0}
                category_results[category]["total"] += 1
                if result["success"]:
                    category_results[category]["passed"] += 1

            return TestResult(
                mode="COLD",
                total_tests=total_tests,
                passed_tests=passed_tests,
                failed_tests=failed_tests,
                duration_seconds=duration,
                details={
                    "auth_success": auth_result["success"],
                    "client_type": "in_memory",
                    "categories": category_results,
                    "tools_tested": total_tests,
                    "results": results
                }
            )

        except Exception as e:
            duration = time.time() - start_time
            print(f"  ❌ COLD test failed: {e}")

            return TestResult(
                mode="COLD",
                total_tests=0,
                passed_tests=0,
                failed_tests=1,
                duration_seconds=duration,
                details={"error": str(e), "phase": "cold_test_execution"}
            )


class DryTestRunner:
    """DRY tests - Mock auth + in-memory fastmcp client."""

    def __init__(self):
        pass

    def _create_mock_auth(self):
        """Create mock authentication result."""
        return {
            "success": True,
            "access_token": "mock_dry_token",
            "refresh_token": "mock_refresh_token",
            "user_info": {"email": "test@example.com", "user_id": "dry_user_123"}
        }

    async def run_dry_tests(self, _environment: str) -> TestResult:
        """Run DRY tests with mock authentication and in-memory client."""
        if not FASTMCP_AVAILABLE:
            return TestResult(
                mode="DRY",
                total_tests=0,
                passed_tests=0,
                failed_tests=1,
                duration_seconds=0.0,
                details={"error": "FastMCP not available"}
            )

        start_time = time.time()

        try:
            # 1. Mock authentication
            print("  🔐 Using mock authentication...")

            auth_result = self._create_mock_auth()
            print("  ✅ Mock authentication successful")

            # 2. Create in-memory MCP client
            print("  💾 Creating in-memory MCP client...")

            transport = InMemoryTransport()
            client = Client(transport)

            # Connect with mock auth token
            await client.connect(auth_token=auth_result["access_token"])
            print("  ✅ In-memory MCP client connected")

            # 3. Run comprehensive test suite
            print("  🛠️  Executing comprehensive test suite...")

            results = []
            test_categories = ["entity", "query", "relationship", "workflow", "workspace", "error"]

            for category in test_categories:
                print(f"    📋 Running {category} tests...")
                category_tests = ALL_TESTS.get(category, [])

                for tool_name, params in category_tests:
                    try:
                        result = await client.call_tool(tool_name, params)
                        success = result.get("success", False)

                        results.append({
                            "category": category,
                            "tool": tool_name,
                            "params": params,
                            "success": success,
                            "result": result
                        })

                        if success:
                            print(f"      ✅ {tool_name}: Success")
                        elif category == "error":
                            print(f"      ✅ {tool_name}: Error handled correctly")
                            results[-1]["success"] = True
                        else:
                            print(f"      ❌ {tool_name}: {result.get('error', 'Unknown error')}")

                    except Exception as e:
                        if category == "error":
                            results.append({
                                "category": category,
                                "tool": tool_name,
                                "params": params,
                                "success": True,
                                "result": {"error": str(e), "expected": True}
                            })
                            print(f"      ✅ {tool_name}: Exception handled correctly")
                        else:
                            results.append({
                                "category": category,
                                "tool": tool_name,
                                "params": params,
                                "success": False,
                                "result": {"error": str(e)}
                            })
                            print(f"      ❌ {tool_name}: {e}")

            # 4. Cleanup
            print("  🧹 Cleaning up connections...")
            await client.disconnect()

            duration = time.time() - start_time

            # Calculate results
            total_tests = len(results)
            passed_tests = sum(1 for r in results if r["success"])
            failed_tests = total_tests - passed_tests

            # Group results by category
            category_results = {}
            for result in results:
                category = result["category"]
                if category not in category_results:
                    category_results[category] = {"total": 0, "passed": 0}
                category_results[category]["total"] += 1
                if result["success"]:
                    category_results[category]["passed"] += 1

            return TestResult(
                mode="DRY",
                total_tests=total_tests,
                passed_tests=passed_tests,
                failed_tests=failed_tests,
                duration_seconds=duration,
                details={
                    "auth_success": auth_result["success"],
                    "client_type": "in_memory_mock",
                    "categories": category_results,
                    "tools_tested": total_tests,
                    "results": results
                }
            )

        except Exception as e:
            duration = time.time() - start_time
            print(f"  ❌ DRY test failed: {e}")

            return TestResult(
                mode="DRY",
                total_tests=0,
                passed_tests=0,
                failed_tests=1,
                duration_seconds=duration,
                details={"error": str(e), "phase": "dry_test_execution"}
            )
