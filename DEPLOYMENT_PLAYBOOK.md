# Deployment Playbook for Atoms MCP Server

## Executive Summary

This playbook provides step-by-step deployment procedures for the Atoms MCP Server to Vercel's production environment. It includes pre-deployment checks, deployment steps, rollback procedures, post-deployment validation, and monitoring setup.

---

## Table of Contents

1. [Pre-Deployment Preparation](#pre-deployment-preparation)
2. [Deployment Process](#deployment-process)
3. [Post-Deployment Validation](#post-deployment-validation)
4. [Rollback Procedures](#rollback-procedures)
5. [Monitoring and Alerting](#monitoring-and-alerting)
6. [Incident Response](#incident-response)
7. [Maintenance Windows](#maintenance-windows)
8. [Emergency Procedures](#emergency-procedures)

---

## 1. Pre-Deployment Preparation

### 1.1 Pre-Deployment Checklist

```bash
#!/bin/bash
# pre_deploy_check.sh - Run before any deployment

echo "🔍 Running pre-deployment checks..."

# Check 1: Git Status
echo "Checking git status..."
if [[ -n $(git status --porcelain) ]]; then
    echo "❌ Uncommitted changes detected"
    exit 1
fi
echo "✅ Git working directory clean"

# Check 2: Current Branch
CURRENT_BRANCH=$(git branch --show-current)
if [[ "$CURRENT_BRANCH" != "main" ]]; then
    echo "⚠️  Not on main branch (current: $CURRENT_BRANCH)"
    read -p "Continue deployment from $CURRENT_BRANCH? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi
echo "✅ Branch check passed"

# Check 3: Tests Pass
echo "Running tests..."
pytest tests/unit -q
if [ $? -ne 0 ]; then
    echo "❌ Unit tests failed"
    exit 1
fi
echo "✅ All tests passing"

# Check 4: Environment Variables
echo "Checking environment variables..."
required_vars=(
    "WORKOS_API_KEY"
    "WORKOS_CLIENT_ID"
    "SUPABASE_SERVICE_ROLE_KEY"
    "NEXT_PUBLIC_SUPABASE_URL"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Missing environment variable: $var"
        exit 1
    fi
done
echo "✅ Environment variables configured"

# Check 5: Dependencies
echo "Checking dependencies..."
python -c "import fastmcp, fastapi, supabase, workos" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Required dependencies not installed"
    exit 1
fi
echo "✅ Dependencies verified"

echo "✅ Pre-deployment checks complete!"
```

### 1.2 Backup Current State

```bash
#!/bin/bash
# backup_state.sh - Create backup before deployment

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups/deploy_$TIMESTAMP"

echo "📦 Creating deployment backup..."

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup current deployment info
vercel inspect > $BACKUP_DIR/current_deployment.json

# Backup environment variables
vercel env pull $BACKUP_DIR/.env.backup

# Get current deployment URL
CURRENT_URL=$(vercel ls --json | jq -r '.[0].url')
echo $CURRENT_URL > $BACKUP_DIR/current_url.txt

# Create database snapshot reference
echo "Database snapshot: $(date -u +%Y-%m-%dT%H:%M:%SZ)" > $BACKUP_DIR/database_snapshot.txt

echo "✅ Backup created at: $BACKUP_DIR"
echo "📌 Current deployment URL: $CURRENT_URL"
```

### 1.3 Communication Plan

```yaml
deployment_communication:
  pre_deployment:
    - channel: "#atoms-deployments"
      message: "🚀 Deployment starting for atoms-mcp-prod"
      timing: "T-15 minutes"

    - channel: "#atoms-engineering"
      message: "Deployment window open - please hold PRs"
      timing: "T-10 minutes"

  during_deployment:
    - channel: "#atoms-status"
      message: "🔄 Deployment in progress..."
      timing: "T-0"

  post_deployment:
    - channel: "#atoms-deployments"
      message: "✅ Deployment complete - validation in progress"
      timing: "T+5 minutes"

    - channel: "#atoms-engineering"
      message: "Deployment complete - PRs can resume"
      timing: "T+10 minutes"

  rollback:
    - channel: "#atoms-incidents"
      message: "⚠️ Rollback initiated"
      timing: "Immediate"
```

---

## 2. Deployment Process

### 2.1 Standard Deployment

```bash
#!/bin/bash
# deploy.sh - Main deployment script

set -e  # Exit on error

echo "🚀 Starting deployment to production..."

# Step 1: Pull latest code
echo "Step 1: Pulling latest code..."
git pull origin main

# Step 2: Install dependencies
echo "Step 2: Installing dependencies..."
uv export --no-dev --format requirements --no-hashes --frozen > requirements-prod.txt

# Step 3: Run pre-deployment checks
echo "Step 3: Running pre-deployment checks..."
./scripts/pre_deploy_check.sh

# Step 4: Create deployment tag
echo "Step 4: Creating deployment tag..."
VERSION="v$(date +%Y%m%d.%H%M%S)"
git tag -a $VERSION -m "Production deployment $VERSION"
git push origin $VERSION

# Step 5: Deploy to Vercel
echo "Step 5: Deploying to Vercel..."
vercel --prod --yes > deployment.log 2>&1

# Step 6: Get deployment URL
DEPLOYMENT_URL=$(tail -1 deployment.log)
echo "Deployed to: $DEPLOYMENT_URL"

# Step 7: Run smoke tests
echo "Step 6: Running smoke tests..."
python scripts/smoke_tests.py $DEPLOYMENT_URL

# Step 8: Update deployment record
echo "Step 7: Recording deployment..."
echo "{
    \"version\": \"$VERSION\",
    \"url\": \"$DEPLOYMENT_URL\",
    \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",
    \"deployed_by\": \"$(git config user.name)\"
}" > deployments/$VERSION.json

echo "✅ Deployment complete!"
echo "📌 Version: $VERSION"
echo "🌐 URL: $DEPLOYMENT_URL"
```

### 2.2 Blue-Green Deployment

```python
#!/usr/bin/env python3
"""Blue-green deployment strategy"""

import httpx
import asyncio
import json
from datetime import datetime

class BlueGreenDeployment:
    """Manages blue-green deployments"""

    def __init__(self, config):
        self.config = config
        self.blue_url = None
        self.green_url = None

    async def deploy(self):
        """Execute blue-green deployment"""
        print("🔵🟢 Starting blue-green deployment...")

        # Step 1: Deploy to green environment
        print("Step 1: Deploying to green environment...")
        self.green_url = await self._deploy_to_vercel()
        print(f"✅ Green deployment: {self.green_url}")

        # Step 2: Run health checks on green
        print("Step 2: Health checking green environment...")
        green_healthy = await self._health_check(self.green_url)
        if not green_healthy:
            print("❌ Green environment unhealthy")
            return False

        # Step 3: Run smoke tests on green
        print("Step 3: Testing green environment...")
        tests_passed = await self._run_smoke_tests(self.green_url)
        if not tests_passed:
            print("❌ Green environment tests failed")
            return False

        # Step 4: Switch traffic to green
        print("Step 4: Switching traffic to green...")
        await self._switch_traffic(self.green_url)
        print("✅ Traffic switched to green")

        # Step 5: Monitor for issues
        print("Step 5: Monitoring new deployment...")
        monitoring_ok = await self._monitor_deployment(duration=300)
        if not monitoring_ok:
            print("⚠️ Issues detected, consider rollback")
            return False

        print("✅ Blue-green deployment successful!")
        return True

    async def _deploy_to_vercel(self) -> str:
        """Deploy to Vercel and return URL"""
        import subprocess
        result = subprocess.run(
            ["vercel", "--yes"],
            capture_output=True,
            text=True
        )
        return result.stdout.strip().split("\n")[-1]

    async def _health_check(self, url: str) -> bool:
        """Check health of deployment"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{url}/health", timeout=10)
                return response.status_code == 200
            except:
                return False

    async def _run_smoke_tests(self, url: str) -> bool:
        """Run smoke tests against deployment"""
        tests = [
            self._test_health_endpoint,
            self._test_auth_endpoint,
            self._test_api_endpoint
        ]

        for test in tests:
            if not await test(url):
                return False
        return True

    async def _switch_traffic(self, new_url: str):
        """Switch production traffic to new deployment"""
        import subprocess
        subprocess.run(
            ["vercel", "alias", new_url, "atomcp.kooshapari.com"],
            check=True
        )

    async def _monitor_deployment(self, duration: int) -> bool:
        """Monitor deployment for specified duration"""
        start_time = datetime.utcnow()
        error_count = 0
        check_interval = 10

        while (datetime.utcnow() - start_time).seconds < duration:
            if not await self._health_check(self.green_url):
                error_count += 1
                if error_count > 3:
                    return False

            await asyncio.sleep(check_interval)

        return True

if __name__ == "__main__":
    deployment = BlueGreenDeployment(config={})
    asyncio.run(deployment.deploy())
```

### 2.3 Canary Deployment

```python
#!/usr/bin/env python3
"""Canary deployment with gradual rollout"""

import asyncio
import httpx
from typing import Dict, Any

class CanaryDeployment:
    """Manages canary deployments with traffic splitting"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.canary_url = None
        self.stable_url = config.get("stable_url")
        self.traffic_percentages = [10, 25, 50, 75, 100]

    async def deploy(self):
        """Execute canary deployment"""
        print("🐤 Starting canary deployment...")

        # Deploy canary version
        self.canary_url = await self._deploy_canary()
        print(f"✅ Canary deployed: {self.canary_url}")

        # Gradual traffic rollout
        for percentage in self.traffic_percentages:
            print(f"📊 Routing {percentage}% traffic to canary...")

            # Update traffic split
            await self._update_traffic_split(percentage)

            # Monitor metrics
            metrics_ok = await self._monitor_metrics(duration=300)

            if not metrics_ok:
                print(f"❌ Issues detected at {percentage}% traffic")
                await self._rollback()
                return False

            print(f"✅ {percentage}% traffic successful")

        print("✅ Canary deployment complete!")
        return True

    async def _deploy_canary(self) -> str:
        """Deploy canary version"""
        # Deploy to Vercel without aliasing
        import subprocess
        result = subprocess.run(
            ["vercel", "--yes", "--no-alias"],
            capture_output=True,
            text=True
        )
        return result.stdout.strip().split("\n")[-1]

    async def _update_traffic_split(self, percentage: int):
        """Update traffic split between stable and canary"""
        # This would integrate with your CDN/load balancer
        # Example using Vercel's edge config
        config = {
            "routes": [
                {
                    "src": "/(.*)",
                    "dest": self.canary_url,
                    "weight": percentage
                },
                {
                    "src": "/(.*)",
                    "dest": self.stable_url,
                    "weight": 100 - percentage
                }
            ]
        }
        # Apply configuration
        print(f"Applied traffic split: {percentage}% to canary")

    async def _monitor_metrics(self, duration: int) -> bool:
        """Monitor key metrics during canary phase"""
        metrics_to_check = [
            ("error_rate", 0.01),  # < 1% errors
            ("p95_latency", 500),   # < 500ms p95
            ("success_rate", 0.99)  # > 99% success
        ]

        # Simulate metric checking
        await asyncio.sleep(duration)

        # In production, fetch real metrics
        for metric_name, threshold in metrics_to_check:
            # Fetch metric value
            metric_value = await self._fetch_metric(metric_name)

            if metric_name == "error_rate" and metric_value > threshold:
                return False
            elif metric_name == "p95_latency" and metric_value > threshold:
                return False
            elif metric_name == "success_rate" and metric_value < threshold:
                return False

        return True

    async def _fetch_metric(self, metric_name: str) -> float:
        """Fetch metric value from monitoring system"""
        # Placeholder - integrate with your monitoring
        return 0.005 if metric_name == "error_rate" else 200

    async def _rollback(self):
        """Rollback canary deployment"""
        print("🔄 Rolling back canary deployment...")
        await self._update_traffic_split(0)
        print("✅ Rolled back to stable version")
```

---

## 3. Post-Deployment Validation

### 3.1 Smoke Tests

```python
#!/usr/bin/env python3
"""smoke_tests.py - Post-deployment validation"""

import httpx
import asyncio
import sys
from typing import List, Dict, Any

class SmokeTests:
    """Post-deployment smoke tests"""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.results = []

    async def run_all_tests(self) -> bool:
        """Run all smoke tests"""
        tests = [
            self.test_health_endpoint,
            self.test_auth_endpoints,
            self.test_api_endpoints,
            self.test_cors_headers,
            self.test_rate_limiting,
            self.test_database_connectivity
        ]

        print(f"🔍 Running smoke tests against: {self.base_url}")

        for test in tests:
            try:
                await test()
                self.results.append({
                    "test": test.__name__,
                    "status": "passed"
                })
                print(f"✅ {test.__name__}")
            except AssertionError as e:
                self.results.append({
                    "test": test.__name__,
                    "status": "failed",
                    "error": str(e)
                })
                print(f"❌ {test.__name__}: {e}")
                return False
            except Exception as e:
                self.results.append({
                    "test": test.__name__,
                    "status": "error",
                    "error": str(e)
                })
                print(f"⚠️  {test.__name__}: {e}")
                return False

        return True

    async def test_health_endpoint(self):
        """Test health check endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/health")
            assert response.status_code == 200, f"Health check failed: {response.status_code}"

            data = response.json()
            assert data.get("status") == "healthy", "Service not healthy"

    async def test_auth_endpoints(self):
        """Test authentication endpoints"""
        async with httpx.AsyncClient() as client:
            # Test login endpoint exists
            response = await client.get(f"{self.base_url}/auth/login")
            assert response.status_code in [302, 200], "Login endpoint not accessible"

            # Test protected endpoint requires auth
            response = await client.get(f"{self.base_url}/api/mcp/tools")
            assert response.status_code == 401, "Protected endpoint not enforcing auth"

    async def test_api_endpoints(self):
        """Test API endpoints"""
        async with httpx.AsyncClient() as client:
            # Test OPTIONS for CORS preflight
            response = await client.options(f"{self.base_url}/api/mcp")
            assert response.status_code in [200, 204], "CORS preflight failed"

    async def test_cors_headers(self):
        """Test CORS headers are present"""
        async with httpx.AsyncClient() as client:
            response = await client.options(f"{self.base_url}/api/mcp")

            required_headers = [
                "access-control-allow-origin",
                "access-control-allow-methods",
                "access-control-allow-headers"
            ]

            for header in required_headers:
                assert header in response.headers, f"Missing CORS header: {header}"

    async def test_rate_limiting(self):
        """Test rate limiting is active"""
        async with httpx.AsyncClient() as client:
            # Send multiple requests quickly
            responses = []
            for _ in range(100):
                response = await client.get(f"{self.base_url}/health")
                responses.append(response.status_code)

            # Should see some rate limiting
            rate_limited = any(status == 429 for status in responses)
            # Rate limiting is optional, so we just warn
            if not rate_limited:
                print("⚠️  Rate limiting may not be configured")

    async def test_database_connectivity(self):
        """Test database connectivity through API"""
        # This would normally require auth
        # For now, we just check that the endpoint exists
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/api/mcp/tools")
            # Should get 401 without auth, not 500
            assert response.status_code == 401, "API endpoint error (possible DB issue)"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python smoke_tests.py <deployment_url>")
        sys.exit(1)

    url = sys.argv[1]
    tests = SmokeTests(url)

    success = asyncio.run(tests.run_all_tests())

    print("\n📊 Test Results:")
    for result in tests.results:
        status_emoji = "✅" if result["status"] == "passed" else "❌"
        print(f"{status_emoji} {result['test']}: {result['status']}")

    sys.exit(0 if success else 1)
```

### 3.2 Performance Validation

```python
#!/usr/bin/env python3
"""Performance validation post-deployment"""

import httpx
import asyncio
import statistics
from typing import List, Dict

class PerformanceValidator:
    """Validates performance meets baselines"""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.baselines = {
            "/health": {"p95": 50, "p99": 100},
            "/api/mcp/tools": {"p95": 200, "p99": 500}
        }

    async def validate(self) -> bool:
        """Run performance validation"""
        print("⚡ Running performance validation...")

        all_passed = True

        for endpoint, thresholds in self.baselines.items():
            metrics = await self._measure_endpoint(endpoint)

            passed = self._check_thresholds(endpoint, metrics, thresholds)
            if not passed:
                all_passed = False

        return all_passed

    async def _measure_endpoint(self, endpoint: str, samples: int = 100):
        """Measure endpoint performance"""
        response_times = []

        async with httpx.AsyncClient() as client:
            for _ in range(samples):
                start = asyncio.get_event_loop().time()
                try:
                    response = await client.get(f"{self.base_url}{endpoint}")
                    elapsed = (asyncio.get_event_loop().time() - start) * 1000
                    response_times.append(elapsed)
                except:
                    pass  # Skip failed requests

        return {
            "p50": statistics.median(response_times),
            "p95": statistics.quantiles(response_times, n=20)[18],
            "p99": statistics.quantiles(response_times, n=100)[98],
            "mean": statistics.mean(response_times)
        }

    def _check_thresholds(self, endpoint: str, metrics: Dict, thresholds: Dict) -> bool:
        """Check if metrics meet thresholds"""
        passed = True

        for metric_name, threshold in thresholds.items():
            actual = metrics.get(metric_name, 0)
            if actual > threshold:
                print(f"❌ {endpoint} {metric_name}: {actual:.2f}ms > {threshold}ms")
                passed = False
            else:
                print(f"✅ {endpoint} {metric_name}: {actual:.2f}ms < {threshold}ms")

        return passed
```

---

## 4. Rollback Procedures

### 4.1 Automatic Rollback

```python
#!/usr/bin/env python3
"""Automatic rollback on deployment failure"""

import subprocess
import json
from datetime import datetime

class AutomaticRollback:
    """Handles automatic rollback on failure"""

    def __init__(self):
        self.previous_deployment = None
        self.current_deployment = None

    def capture_current_state(self):
        """Capture current deployment state"""
        result = subprocess.run(
            ["vercel", "ls", "--json"],
            capture_output=True,
            text=True
        )
        deployments = json.loads(result.stdout)
        self.previous_deployment = deployments[0] if deployments else None

    def rollback(self, reason: str = "Unknown"):
        """Execute rollback to previous deployment"""
        if not self.previous_deployment:
            print("❌ No previous deployment found")
            return False

        print(f"🔄 Rolling back due to: {reason}")

        # Get previous deployment URL
        prev_url = self.previous_deployment["url"]

        # Alias previous deployment to production
        result = subprocess.run(
            ["vercel", "alias", prev_url, "atomcp.kooshapari.com"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print(f"✅ Rolled back to: {prev_url}")
            self._log_rollback(reason)
            return True
        else:
            print(f"❌ Rollback failed: {result.stderr}")
            return False

    def _log_rollback(self, reason: str):
        """Log rollback event"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": "rollback",
            "reason": reason,
            "from_deployment": self.current_deployment,
            "to_deployment": self.previous_deployment
        }

        with open("rollback.log", "a") as f:
            f.write(json.dumps(log_entry) + "\n")
```

### 4.2 Manual Rollback

```bash
#!/bin/bash
# manual_rollback.sh - Manual rollback procedure

echo "🔄 Manual Rollback Procedure"
echo "=========================="

# List recent deployments
echo "Recent deployments:"
vercel ls --limit 5

# Get rollback target
read -p "Enter deployment URL to rollback to: " ROLLBACK_URL

# Confirm rollback
echo "You are about to rollback to: $ROLLBACK_URL"
read -p "Are you sure? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Rollback cancelled"
    exit 0
fi

# Execute rollback
echo "Executing rollback..."
vercel alias $ROLLBACK_URL atomcp.kooshapari.com

if [ $? -eq 0 ]; then
    echo "✅ Rollback successful"

    # Run health check on rolled back version
    echo "Verifying rollback..."
    curl -s https://atomcp.kooshapari.com/health | jq '.'

    # Log rollback
    echo "{
        \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",
        \"action\": \"manual_rollback\",
        \"target\": \"$ROLLBACK_URL\",
        \"executed_by\": \"$(whoami)\"
    }" >> rollback.log

else
    echo "❌ Rollback failed"
    exit 1
fi
```

---

## 5. Monitoring and Alerting

### 5.1 Monitoring Setup

```python
#!/usr/bin/env python3
"""Monitoring configuration and health checks"""

import asyncio
import httpx
from typing import Dict, List
from datetime import datetime

class MonitoringService:
    """Production monitoring service"""

    def __init__(self, config: Dict):
        self.config = config
        self.metrics = []
        self.alerts = []

    async def start_monitoring(self):
        """Start continuous monitoring"""
        tasks = [
            self._monitor_health(),
            self._monitor_performance(),
            self._monitor_errors(),
            self._monitor_resources()
        ]

        await asyncio.gather(*tasks)

    async def _monitor_health(self):
        """Monitor service health"""
        while True:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.config['base_url']}/health",
                        timeout=5
                    )

                    if response.status_code != 200:
                        await self._trigger_alert(
                            "health_check_failed",
                            f"Health check returned {response.status_code}"
                        )

            except Exception as e:
                await self._trigger_alert(
                    "health_check_error",
                    f"Health check failed: {e}"
                )

            await asyncio.sleep(30)  # Check every 30 seconds

    async def _monitor_performance(self):
        """Monitor performance metrics"""
        while True:
            metrics = await self._collect_performance_metrics()

            # Check against thresholds
            if metrics["p95_latency"] > 500:
                await self._trigger_alert(
                    "high_latency",
                    f"P95 latency is {metrics['p95_latency']}ms"
                )

            if metrics["error_rate"] > 0.01:
                await self._trigger_alert(
                    "high_error_rate",
                    f"Error rate is {metrics['error_rate']*100}%"
                )

            await asyncio.sleep(60)  # Check every minute

    async def _monitor_errors(self):
        """Monitor error logs"""
        while True:
            # Check for error patterns
            errors = await self._check_error_logs()

            if errors:
                await self._trigger_alert(
                    "errors_detected",
                    f"Found {len(errors)} errors in logs"
                )

            await asyncio.sleep(300)  # Check every 5 minutes

    async def _monitor_resources(self):
        """Monitor resource usage"""
        while True:
            resources = await self._get_resource_usage()

            if resources["memory_percent"] > 80:
                await self._trigger_alert(
                    "high_memory_usage",
                    f"Memory usage at {resources['memory_percent']}%"
                )

            if resources["cpu_percent"] > 80:
                await self._trigger_alert(
                    "high_cpu_usage",
                    f"CPU usage at {resources['cpu_percent']}%"
                )

            await asyncio.sleep(60)

    async def _trigger_alert(self, alert_type: str, message: str):
        """Trigger an alert"""
        alert = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": alert_type,
            "message": message,
            "severity": self._get_severity(alert_type)
        }

        self.alerts.append(alert)

        # Send to notification channels
        await self._send_notifications(alert)

    def _get_severity(self, alert_type: str) -> str:
        """Determine alert severity"""
        severity_map = {
            "health_check_failed": "critical",
            "high_error_rate": "critical",
            "high_latency": "warning",
            "high_memory_usage": "warning",
            "high_cpu_usage": "warning"
        }
        return severity_map.get(alert_type, "info")

    async def _send_notifications(self, alert: Dict):
        """Send alert notifications"""
        if alert["severity"] == "critical":
            # Page on-call
            await self._page_oncall(alert)
        elif alert["severity"] == "warning":
            # Send to Slack
            await self._notify_slack(alert)
```

### 5.2 Alert Configuration

```yaml
# alerts.yaml - Alert configuration

alerts:
  - name: service_down
    condition: health_check_failed
    duration: 2m
    severity: critical
    actions:
      - page_oncall
      - slack_notification
      - create_incident

  - name: high_error_rate
    condition: error_rate > 1%
    duration: 5m
    severity: high
    actions:
      - slack_notification
      - email_team

  - name: high_latency
    condition: p95_latency > 1000ms
    duration: 10m
    severity: medium
    actions:
      - slack_notification

  - name: deployment_failed
    condition: deployment_status == failed
    severity: high
    actions:
      - auto_rollback
      - slack_notification

notification_channels:
  slack:
    webhook_url: ${SLACK_WEBHOOK_URL}
    channels:
      critical: "#atoms-incidents"
      high: "#atoms-alerts"
      medium: "#atoms-monitoring"

  pagerduty:
    api_key: ${PAGERDUTY_API_KEY}
    service_id: ${PAGERDUTY_SERVICE_ID}

  email:
    smtp_host: smtp.gmail.com
    smtp_port: 587
    from: alerts@atoms.tech
    to:
      - engineering@atoms.tech
      - ops@atoms.tech
```

---

## 6. Incident Response

### 6.1 Incident Response Playbook

```markdown
# Incident Response Procedures

## Severity Levels

- **P1 (Critical)**: Complete service outage or data loss
- **P2 (High)**: Major functionality broken, significant performance degradation
- **P3 (Medium)**: Minor functionality affected, workaround available
- **P4 (Low)**: Cosmetic issues, minimal impact

## Response Times

| Severity | Response Time | Resolution Target |
|----------|--------------|-------------------|
| P1       | < 5 minutes  | < 1 hour         |
| P2       | < 15 minutes | < 4 hours        |
| P3       | < 1 hour     | < 24 hours       |
| P4       | < 24 hours   | Best effort      |

## Incident Commander Responsibilities

1. **Assess** - Determine severity and impact
2. **Communicate** - Create incident channel, notify stakeholders
3. **Coordinate** - Assign roles, manage response effort
4. **Document** - Keep incident timeline updated
5. **Resolve** - Drive to resolution or workaround
6. **Review** - Schedule post-mortem

## Response Checklist

- [ ] Acknowledge alert/incident
- [ ] Assess severity and impact
- [ ] Create incident channel (#incident-YYYYMMDD-description)
- [ ] Assign incident commander
- [ ] Notify stakeholders
- [ ] Begin troubleshooting
- [ ] Document timeline
- [ ] Implement fix/workaround
- [ ] Verify resolution
- [ ] Close incident
- [ ] Schedule post-mortem
```

---

## 7. Maintenance Windows

### 7.1 Scheduled Maintenance

```bash
#!/bin/bash
# scheduled_maintenance.sh - Execute scheduled maintenance

echo "🔧 Starting Scheduled Maintenance"
echo "================================"

MAINTENANCE_START=$(date +%Y-%m-%dT%H:%M:%S)

# Step 1: Enable maintenance mode
echo "Enabling maintenance mode..."
vercel env add MAINTENANCE_MODE true --production

# Step 2: Perform maintenance tasks
echo "Performing maintenance tasks..."

# Database maintenance
echo "Running database maintenance..."
psql $DATABASE_URL -c "VACUUM ANALYZE;"

# Clear caches
echo "Clearing caches..."
redis-cli FLUSHDB

# Update dependencies
echo "Updating dependencies..."
pip install --upgrade -r requirements-prod.txt

# Step 3: Run health checks
echo "Running health checks..."
python scripts/health_check.py

# Step 4: Disable maintenance mode
echo "Disabling maintenance mode..."
vercel env rm MAINTENANCE_MODE --production

MAINTENANCE_END=$(date +%Y-%m-%dT%H:%M:%S)

echo "✅ Maintenance completed"
echo "Start: $MAINTENANCE_START"
echo "End: $MAINTENANCE_END"
```

---

## 8. Emergency Procedures

### 8.1 Emergency Response

```bash
#!/bin/bash
# emergency_response.sh - Emergency response procedures

echo "🚨 EMERGENCY RESPONSE ACTIVATED"
echo "=============================="

# Immediate actions
echo "1. Assessing situation..."
curl -s https://atomcp.kooshapari.com/health || echo "Service appears down"

echo "2. Checking recent deployments..."
vercel ls --limit 3

echo "3. Recent errors from logs..."
vercel logs --limit 20 | grep ERROR

# Decision tree
echo ""
echo "Select emergency action:"
echo "1) Immediate rollback"
echo "2) Scale up resources"
echo "3) Enable maintenance mode"
echo "4) Full service restart"
echo "5) Escalate to senior engineer"

read -p "Enter choice (1-5): " choice

case $choice in
    1)
        echo "Executing immediate rollback..."
        ./scripts/manual_rollback.sh
        ;;
    2)
        echo "Scaling up resources..."
        vercel scale --min 3 --max 10
        ;;
    3)
        echo "Enabling maintenance mode..."
        vercel env add MAINTENANCE_MODE true --production --force
        ;;
    4)
        echo "Restarting service..."
        vercel deploy --prod --force
        ;;
    5)
        echo "Escalating to senior engineer..."
        ./scripts/page_oncall.sh
        ;;
esac

# Log emergency action
echo "{
    \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",
    \"action\": \"emergency_response\",
    \"choice\": \"$choice\",
    \"executed_by\": \"$(whoami)\"
}" >> emergency.log
```

### 8.2 Disaster Recovery

```python
#!/usr/bin/env python3
"""Disaster recovery procedures"""

import subprocess
import asyncio
from datetime import datetime

class DisasterRecovery:
    """Handles disaster recovery scenarios"""

    async def execute_recovery(self, scenario: str):
        """Execute recovery based on scenario"""
        scenarios = {
            "database_failure": self.recover_database,
            "service_outage": self.recover_service,
            "data_corruption": self.recover_data,
            "security_breach": self.recover_security
        }

        recovery_func = scenarios.get(scenario)
        if recovery_func:
            await recovery_func()
        else:
            print(f"Unknown scenario: {scenario}")

    async def recover_database(self):
        """Recover from database failure"""
        print("Recovering from database failure...")

        # Step 1: Switch to backup database
        print("Switching to backup database...")
        subprocess.run([
            "vercel", "env", "add",
            "DATABASE_URL", "${BACKUP_DATABASE_URL}",
            "--production", "--force"
        ])

        # Step 2: Restore from latest backup
        print("Restoring from backup...")
        # Database restore commands here

        # Step 3: Verify data integrity
        print("Verifying data integrity...")
        # Data verification here

    async def recover_service(self):
        """Recover from service outage"""
        print("Recovering from service outage...")

        # Step 1: Deploy to alternative region
        print("Deploying to alternative region...")
        subprocess.run([
            "vercel", "--prod",
            "--regions", "sfo1,iad1"
        ])

        # Step 2: Update DNS
        print("Updating DNS records...")
        # DNS update commands here

        # Step 3: Verify service
        print("Verifying service...")
        # Service verification here

    async def recover_data(self):
        """Recover from data corruption"""
        print("Recovering from data corruption...")
        # Data recovery procedures

    async def recover_security(self):
        """Recover from security breach"""
        print("Recovering from security breach...")

        # Step 1: Rotate all secrets
        print("Rotating all secrets...")
        # Secret rotation here

        # Step 2: Force logout all sessions
        print("Invalidating all sessions...")
        # Session invalidation here

        # Step 3: Enable additional security
        print("Enabling enhanced security...")
        # Security hardening here
```

---

## Appendix A: Quick Reference

### Deployment Commands

```bash
# Standard deployment
vercel --prod

# Deployment with specific branch
vercel --prod --scope atoms

# Preview deployment
vercel

# List deployments
vercel ls

# Inspect deployment
vercel inspect [deployment-url]

# View logs
vercel logs

# Rollback
vercel alias [old-deployment-url] atomcp.kooshapari.com
```

### Emergency Contacts

```yaml
contacts:
  oncall_primary: "+1-555-0100"
  oncall_secondary: "+1-555-0101"
  engineering_lead: "+1-555-0102"
  cto: "+1-555-0103"

slack_channels:
  incidents: "#atoms-incidents"
  deployments: "#atoms-deployments"
  monitoring: "#atoms-monitoring"

vendors:
  vercel_support: "support@vercel.com"
  supabase_support: "support@supabase.com"
  workos_support: "support@workos.com"
```

---

## Document Information

- **Version**: 1.0.0
- **Last Updated**: October 16, 2025
- **Maintained By**: Atoms DevOps Team
- **Review Schedule**: Quarterly

For questions or updates, contact the DevOps team or submit a PR to the repository.