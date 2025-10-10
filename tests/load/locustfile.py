"""
Load testing with Locust.

Run with: locust -f tests/load/locustfile.py --host=http://localhost:50003
"""

from locust import HttpUser, between, task


class AtomsUser(HttpUser):
    """Simulated user for load testing."""

    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks

    @task(10)
    def health_check(self):
        """Health check endpoint (most common)."""
        self.client.get("/health")

    @task(5)
    def list_tools(self):
        """List available tools."""
        self.client.post(
            "/mcp/v1/tools/list",
            json={},
            headers={"Content-Type": "application/json"}
        )

    @task(3)
    def call_tool(self):
        """Call a tool."""
        self.client.post(
            "/mcp/v1/tools/call",
            json={
                "name": "get_requirements",
                "arguments": {}
            },
            headers={"Content-Type": "application/json"}
        )

    @task(1)
    def list_resources(self):
        """List resources."""
        self.client.post(
            "/mcp/v1/resources/list",
            json={},
            headers={"Content-Type": "application/json"}
        )

    def on_start(self):
        """Called when a simulated user starts."""
        # Optional: Perform login or setup

    def on_stop(self):
        """Called when a simulated user stops."""
        # Optional: Perform cleanup


class AdminUser(HttpUser):
    """Admin user with different behavior."""

    wait_time = between(5, 10)

    @task
    def admin_health_check(self):
        """Admin health check."""
        self.client.get("/health")

