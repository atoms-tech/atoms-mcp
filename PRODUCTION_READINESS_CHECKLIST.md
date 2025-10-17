# Production Readiness Checklist for Atoms MCP Server

## Executive Summary

This comprehensive checklist ensures the Atoms MCP Server is production-ready across all Phase 2-5 implementations. Each section includes verification steps, performance baselines, and validation criteria.

---

## Table of Contents

1. [Environment Setup](#environment-setup)
2. [Dependencies Installation](#dependencies-installation)
3. [Database Configuration](#database-configuration)
4. [Authentication Setup](#authentication-setup)
5. [Vercel Deployment Configuration](#vercel-deployment-configuration)
6. [Health Check Verification](#health-check-verification)
7. [Performance Baselines](#performance-baselines)
8. [Security Checklist](#security-checklist)
9. [Monitoring Setup](#monitoring-setup)
10. [Backup and Recovery](#backup-and-recovery)

---

## 1. Environment Setup

### 1.1 Required Environment Variables

```bash
# Core Configuration
□ ATOMS_FASTMCP_TRANSPORT=http
□ ATOMS_FASTMCP_HTTP_PATH=/api/mcp
□ ATOMS_FASTMCP_HTTP_AUTH_MODE=required
□ ATOMS_FASTMCP_AUTH_MODE=supabase_jwt
□ PRODUCTION=true
□ LOG_LEVEL=INFO

# Public URLs
□ FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL=https://atomcp.kooshapari.com
□ PUBLIC_URL=https://atomcp.kooshapari.com
□ MCP_ENDPOINT=https://atomcp.kooshapari.com/api/mcp

# WorkOS AuthKit Configuration
□ FASTMCP_SERVER_AUTH=fastmcp.server.auth.providers.workos.AuthKitProvider
□ FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN=https://decent-hymn-17.authkit.app
□ FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_REQUIRED_SCOPES=openid,profile,email
□ WORKOS_API_KEY=<production_key>
□ WORKOS_CLIENT_ID=<production_client_id>

# Supabase Configuration
□ SUPABASE_SERVICE_ROLE_KEY=<service_role_key>
□ NEXT_PUBLIC_SUPABASE_ANON_KEY=<anon_key>
□ NEXT_PUBLIC_SUPABASE_URL=https://<project>.supabase.co
□ SUPABASE_JWT_SECRET=<jwt_secret>

# Google Cloud Configuration (for embeddings)
□ GOOGLE_CLOUD_PROJECT=<project_id>
□ GOOGLE_CLOUD_LOCATION=us-central1
□ VERTEX_EMBEDDINGS_MODEL=text-embedding-004

# Session Management
□ MCP_SESSION_TTL_HOURS=24
□ SESSION_CLEANUP_INTERVAL_MINUTES=30
□ MAX_SESSIONS_PER_USER=10

# Rate Limiting
□ RATE_LIMIT_ENABLED=true
□ RATE_LIMIT_REQUESTS_PER_MINUTE=60
□ RATE_LIMIT_BURST_SIZE=100

# Cache Configuration
□ CACHE_ENABLED=true
□ CACHE_TTL_SECONDS=300
□ CACHE_MAX_SIZE_MB=100
```

### 1.2 Environment Validation Script

```python
#!/usr/bin/env python3
"""Environment validation script - run before deployment"""

import os
import sys
from typing import List, Dict, Tuple

REQUIRED_VARS = {
    'production': [
        'ATOMS_FASTMCP_TRANSPORT',
        'ATOMS_FASTMCP_HTTP_PATH',
        'WORKOS_API_KEY',
        'WORKOS_CLIENT_ID',
        'SUPABASE_SERVICE_ROLE_KEY',
        'NEXT_PUBLIC_SUPABASE_URL',
    ],
    'optional': [
        'LOG_LEVEL',
        'CACHE_ENABLED',
        'RATE_LIMIT_ENABLED',
    ]
}

def validate_environment() -> Tuple[bool, List[str]]:
    """Validate environment variables"""
    missing = []
    warnings = []

    for var in REQUIRED_VARS['production']:
        if not os.getenv(var):
            missing.append(var)

    for var in REQUIRED_VARS['optional']:
        if not os.getenv(var):
            warnings.append(f"Optional variable {var} not set, using defaults")

    return len(missing) == 0, missing, warnings

if __name__ == "__main__":
    valid, missing, warnings = validate_environment()

    for warning in warnings:
        print(f"⚠️  {warning}")

    if not valid:
        print("❌ Missing required environment variables:")
        for var in missing:
            print(f"   - {var}")
        sys.exit(1)
    else:
        print("✅ All required environment variables are set")
        sys.exit(0)
```

---

## 2. Dependencies Installation

### 2.1 Python Dependencies

```bash
# Production dependencies
□ uv export --no-dev --format requirements --no-hashes --frozen > requirements-prod.txt

# Verify critical packages
□ fastmcp>=2.12.2
□ fastapi>=0.104.0
□ uvicorn[standard]>=0.24.0
□ supabase>=2.5.0
□ psycopg2-binary>=2.9.9
□ python-dotenv>=1.0.1
□ google-cloud-aiplatform>=1.49.0
□ workos>=1.0.0
□ PyJWT>=2.8.0
□ cryptography>=41.0.0
□ pydantic[email]>=2.11.7
□ httpx>=0.28.1
```

### 2.2 System Dependencies

```bash
# Ubuntu/Debian
□ sudo apt-get update
□ sudo apt-get install -y \
    python3.11 \
    python3.11-venv \
    postgresql-client \
    redis-tools \
    curl \
    jq

# macOS (for local development)
□ brew install python@3.11
□ brew install postgresql
□ brew install redis
□ brew install jq
```

### 2.3 Dependency Verification Script

```python
#!/usr/bin/env python3
"""Verify all dependencies are installed correctly"""

import subprocess
import sys
import importlib
from typing import Dict, List

REQUIRED_PACKAGES = {
    'fastmcp': '2.12.2',
    'fastapi': '0.104.0',
    'uvicorn': '0.24.0',
    'supabase': '2.5.0',
    'psycopg2': '2.9.9',
    'workos': '1.0.0',
    'pydantic': '2.11.7',
    'jwt': '2.8.0',
}

def check_package(package: str, min_version: str) -> bool:
    """Check if package is installed with minimum version"""
    try:
        module = importlib.import_module(package.replace('-', '_'))
        if hasattr(module, '__version__'):
            installed_version = module.__version__
            return installed_version >= min_version
        return True
    except ImportError:
        return False

def verify_dependencies() -> Tuple[bool, List[str]]:
    """Verify all dependencies"""
    missing = []

    for package, version in REQUIRED_PACKAGES.items():
        if not check_package(package, version):
            missing.append(f"{package}>={version}")

    return len(missing) == 0, missing

if __name__ == "__main__":
    valid, missing = verify_dependencies()

    if not valid:
        print("❌ Missing or outdated packages:")
        for package in missing:
            print(f"   - {package}")
        print("\nRun: uv export --no-dev --format requirements --no-hashes --frozen > requirements-prod.txt")
        sys.exit(1)
    else:
        print("✅ All dependencies are installed correctly")
        sys.exit(0)
```

---

## 3. Database Configuration

### 3.1 Supabase Setup

```sql
-- Required database tables
□ CREATE TABLE atoms_users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

□ CREATE TABLE atoms_workspaces (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    owner_id UUID REFERENCES atoms_users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

□ CREATE TABLE atoms_entities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES atoms_workspaces(id),
    type TEXT NOT NULL,
    name TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

□ CREATE TABLE atoms_relationships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id UUID REFERENCES atoms_entities(id),
    target_id UUID REFERENCES atoms_entities(id),
    type TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

□ CREATE TABLE atoms_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES atoms_users(id),
    token_hash TEXT NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Required indexes
□ CREATE INDEX idx_sessions_user_id ON atoms_sessions(user_id);
□ CREATE INDEX idx_sessions_token_hash ON atoms_sessions(token_hash);
□ CREATE INDEX idx_sessions_expires_at ON atoms_sessions(expires_at);
□ CREATE INDEX idx_entities_workspace_id ON atoms_entities(workspace_id);
□ CREATE INDEX idx_entities_type ON atoms_entities(type);
□ CREATE INDEX idx_relationships_source ON atoms_relationships(source_id);
□ CREATE INDEX idx_relationships_target ON atoms_relationships(target_id);
```

### 3.2 Database Health Check

```python
#!/usr/bin/env python3
"""Database health check script"""

import asyncio
import os
from supabase import create_client, Client

async def check_database_health():
    """Check Supabase database connectivity and tables"""
    url = os.getenv('NEXT_PUBLIC_SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

    if not url or not key:
        print("❌ Missing Supabase credentials")
        return False

    try:
        supabase: Client = create_client(url, key)

        # Test tables exist
        tables = [
            'atoms_users',
            'atoms_workspaces',
            'atoms_entities',
            'atoms_relationships',
            'atoms_sessions'
        ]

        for table in tables:
            result = supabase.table(table).select("id").limit(1).execute()
            print(f"✅ Table {table} is accessible")

        return True
    except Exception as e:
        print(f"❌ Database health check failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(check_database_health())
```

---

## 4. Authentication Setup

### 4.1 WorkOS AuthKit Configuration

```bash
# WorkOS Dashboard Setup
□ Create production application at https://dashboard.workos.com
□ Configure OAuth redirect URLs:
  - https://atomcp.kooshapari.com/auth/callback
  - https://atomcp.kooshapari.com/auth/complete
□ Enable required scopes: openid, profile, email
□ Configure session duration: 24 hours
□ Enable MFA (optional but recommended)
□ Set up webhook endpoints for security events
```

### 4.2 JWT Configuration

```python
# JWT validation settings
□ JWT_ALGORITHM = "RS256"
□ JWT_ISSUER = "https://decent-hymn-17.authkit.app"
□ JWT_AUDIENCE = "atomcp.kooshapari.com"
□ JWT_LEEWAY_SECONDS = 30
□ JWT_MAX_AGE_SECONDS = 86400  # 24 hours
```

### 4.3 Authentication Test Script

```python
#!/usr/bin/env python3
"""Test authentication flow"""

import httpx
import asyncio
import os
from typing import Optional

async def test_auth_flow():
    """Test complete authentication flow"""
    base_url = os.getenv('PUBLIC_URL', 'https://atomcp.kooshapari.com')

    async with httpx.AsyncClient() as client:
        # Test health endpoint (no auth required)
        response = await client.get(f"{base_url}/health")
        assert response.status_code == 200
        print("✅ Health endpoint accessible")

        # Test auth-required endpoint
        response = await client.get(f"{base_url}/api/mcp/tools")
        assert response.status_code == 401
        print("✅ Auth enforcement working")

        # Test CORS headers
        response = await client.options(f"{base_url}/api/mcp")
        assert 'access-control-allow-origin' in response.headers
        print("✅ CORS headers configured")

if __name__ == "__main__":
    asyncio.run(test_auth_flow())
```

---

## 5. Vercel Deployment Configuration

### 5.1 vercel.json Configuration

```json
{
  "version": 2,
  "builds": [
    {
      "src": "app.py",
      "use": "@vercel/python",
      "config": {
        "maxLambdaSize": "50mb",
        "runtime": "python3.11"
      }
    }
  ],
  "routes": [
    {
      "src": "/health",
      "dest": "app.py",
      "headers": {
        "cache-control": "no-cache, no-store, must-revalidate"
      }
    },
    {
      "src": "/api/mcp/(.*)",
      "dest": "app.py",
      "headers": {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization"
      }
    },
    {
      "src": "/auth/(.*)",
      "dest": "app.py"
    },
    {
      "src": "/.well-known/(.*)",
      "dest": "app.py"
    }
  ],
  "env": {
    "ATOMS_FASTMCP_TRANSPORT": "http",
    "ATOMS_FASTMCP_HTTP_PATH": "/api/mcp",
    "PYTHONPATH": "pheno_vendor:.",
    "PRODUCTION": "true"
  },
  "regions": ["iad1"],
  "functions": {
    "app.py": {
      "memory": 1024,
      "maxDuration": 30
    }
  }
}
```

### 5.2 Deployment Commands

```bash
# Install Vercel CLI
□ npm install -g vercel

# Login to Vercel
□ vercel login

# Link project
□ vercel link

# Set environment variables
□ vercel env add WORKOS_API_KEY production
□ vercel env add WORKOS_CLIENT_ID production
□ vercel env add SUPABASE_SERVICE_ROLE_KEY production
□ vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY production
□ vercel env add NEXT_PUBLIC_SUPABASE_URL production

# Deploy to production
□ vercel --prod

# Verify deployment
□ curl https://atomcp.kooshapari.com/health
```

### 5.3 Pre-deployment Checklist

```bash
#!/bin/bash
# Pre-deployment validation script

echo "🔍 Running pre-deployment checks..."

# Check Python version
python_version=$(python3 --version | cut -d' ' -f2)
if [[ "$python_version" < "3.11" ]]; then
    echo "❌ Python 3.11+ required (found $python_version)"
    exit 1
fi
echo "✅ Python version: $python_version"

# Check for required files
required_files=(
    "app.py"
    "vercel.json"
    "requirements.txt"
    "pyproject.toml"
    ".env.production"
)

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Missing required file: $file"
        exit 1
    fi
    echo "✅ Found: $file"
done

# Check for syntax errors
python3 -m py_compile app.py
if [ $? -ne 0 ]; then
    echo "❌ Python syntax errors found"
    exit 1
fi
echo "✅ No syntax errors"

# Run tests
pytest tests/unit -v --tb=short
if [ $? -ne 0 ]; then
    echo "❌ Unit tests failed"
    exit 1
fi
echo "✅ All tests passed"

echo "🎉 Pre-deployment checks complete!"
```

---

## 6. Health Check Verification

### 6.1 Health Endpoint Requirements

```python
# Health check response structure
{
    "status": "healthy",
    "timestamp": "2025-10-16T12:00:00Z",
    "version": "1.0.0",
    "checks": {
        "database": "healthy",
        "cache": "healthy",
        "auth": "healthy",
        "rate_limiter": "healthy"
    },
    "metrics": {
        "uptime_seconds": 3600,
        "request_count": 12345,
        "active_sessions": 42,
        "cache_hit_rate": 0.85
    }
}
```

### 6.2 Health Check Script

```python
#!/usr/bin/env python3
"""Comprehensive health check script"""

import httpx
import asyncio
import json
from datetime import datetime
from typing import Dict, Any

async def run_health_checks(base_url: str) -> Dict[str, Any]:
    """Run comprehensive health checks"""
    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Basic health check
        try:
            response = await client.get(f"{base_url}/health")
            results["checks"]["basic"] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "status_code": response.status_code,
                "response_time_ms": response.elapsed.total_seconds() * 1000
            }
        except Exception as e:
            results["checks"]["basic"] = {
                "status": "unhealthy",
                "error": str(e)
            }

        # API endpoint check
        try:
            response = await client.get(f"{base_url}/api/mcp/tools")
            results["checks"]["api"] = {
                "status": "healthy" if response.status_code in [200, 401] else "unhealthy",
                "status_code": response.status_code
            }
        except Exception as e:
            results["checks"]["api"] = {
                "status": "unhealthy",
                "error": str(e)
            }

        # CORS check
        try:
            response = await client.options(f"{base_url}/api/mcp")
            results["checks"]["cors"] = {
                "status": "healthy" if "access-control-allow-origin" in response.headers else "unhealthy",
                "headers_present": "access-control-allow-origin" in response.headers
            }
        except Exception as e:
            results["checks"]["cors"] = {
                "status": "unhealthy",
                "error": str(e)
            }

    return results

if __name__ == "__main__":
    import sys
    base_url = sys.argv[1] if len(sys.argv) > 1 else "https://atomcp.kooshapari.com"
    results = asyncio.run(run_health_checks(base_url))

    print(json.dumps(results, indent=2))

    # Exit with error if any check failed
    all_healthy = all(
        check.get("status") == "healthy"
        for check in results["checks"].values()
    )
    sys.exit(0 if all_healthy else 1)
```

---

## 7. Performance Baselines

### 7.1 Expected Performance Metrics

```yaml
# Response Time Targets (95th percentile)
health_endpoint: < 50ms
auth_endpoints: < 200ms
api_list_tools: < 100ms
api_execute_tool: < 500ms
database_query: < 100ms
cache_hit: < 10ms

# Throughput Targets
requests_per_second: 1000
concurrent_connections: 500
websocket_connections: 100

# Resource Usage Targets
cpu_usage: < 70%
memory_usage: < 512MB
database_connections: < 20
cache_memory: < 100MB

# Error Rate Targets
error_rate: < 0.1%
timeout_rate: < 0.01%
5xx_errors: < 0.05%
```

### 7.2 Performance Test Script

```python
#!/usr/bin/env python3
"""Performance baseline testing"""

import asyncio
import httpx
import time
import statistics
from typing import List, Dict
import json

async def measure_endpoint(
    client: httpx.AsyncClient,
    url: str,
    n_requests: int = 100
) -> Dict[str, float]:
    """Measure endpoint performance"""
    response_times = []
    errors = 0

    for _ in range(n_requests):
        start = time.time()
        try:
            response = await client.get(url)
            response_times.append((time.time() - start) * 1000)
            if response.status_code >= 500:
                errors += 1
        except Exception:
            errors += 1

    return {
        "min_ms": min(response_times) if response_times else 0,
        "max_ms": max(response_times) if response_times else 0,
        "mean_ms": statistics.mean(response_times) if response_times else 0,
        "p50_ms": statistics.median(response_times) if response_times else 0,
        "p95_ms": statistics.quantiles(response_times, n=20)[18] if len(response_times) > 20 else 0,
        "p99_ms": statistics.quantiles(response_times, n=100)[98] if len(response_times) > 100 else 0,
        "error_rate": errors / n_requests
    }

async def run_performance_tests(base_url: str):
    """Run performance baseline tests"""
    endpoints = [
        "/health",
        "/api/mcp/tools",
    ]

    results = {}

    async with httpx.AsyncClient(timeout=30.0) as client:
        for endpoint in endpoints:
            print(f"Testing {endpoint}...")
            results[endpoint] = await measure_endpoint(
                client,
                f"{base_url}{endpoint}",
                n_requests=100
            )

    print("\nPerformance Results:")
    print(json.dumps(results, indent=2))

    # Check against baselines
    baselines = {
        "/health": 50,
        "/api/mcp/tools": 100,
    }

    all_passed = True
    for endpoint, baseline_ms in baselines.items():
        if endpoint in results:
            p95 = results[endpoint]["p95_ms"]
            if p95 > baseline_ms:
                print(f"⚠️  {endpoint} p95 ({p95:.2f}ms) exceeds baseline ({baseline_ms}ms)")
                all_passed = False
            else:
                print(f"✅ {endpoint} p95 ({p95:.2f}ms) within baseline ({baseline_ms}ms)")

    return all_passed

if __name__ == "__main__":
    import sys
    base_url = sys.argv[1] if len(sys.argv) > 1 else "https://atomcp.kooshapari.com"
    passed = asyncio.run(run_performance_tests(base_url))
    sys.exit(0 if passed else 1)
```

---

## 8. Security Checklist

### 8.1 Security Configuration

```bash
# HTTPS/TLS
□ Force HTTPS for all endpoints
□ TLS 1.2+ only
□ Strong cipher suites
□ HSTS header enabled

# Authentication
□ JWT signature verification enabled
□ Token expiration enforced
□ Refresh token rotation
□ Session timeout configured

# Authorization
□ Role-based access control (RBAC)
□ Row-level security (RLS) in database
□ API key rotation policy
□ Principle of least privilege

# Input Validation
□ Request size limits
□ Rate limiting enabled
□ Input sanitization
□ SQL injection prevention

# Headers
□ Content-Security-Policy
□ X-Content-Type-Options: nosniff
□ X-Frame-Options: DENY
□ X-XSS-Protection: 1; mode=block

# Monitoring
□ Failed authentication logging
□ Suspicious activity alerts
□ Security event webhook configured
□ Audit trail enabled
```

### 8.2 Security Scan Script

```python
#!/usr/bin/env python3
"""Security configuration verification"""

import httpx
import asyncio
from typing import Dict, List

async def check_security_headers(base_url: str) -> Dict[str, bool]:
    """Check for required security headers"""
    required_headers = {
        'strict-transport-security': 'HSTS',
        'x-content-type-options': 'nosniff',
        'x-frame-options': 'DENY or SAMEORIGIN',
        'content-security-policy': 'CSP',
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{base_url}/health")

        results = {}
        for header, description in required_headers.items():
            results[description] = header in response.headers
            if header in response.headers:
                print(f"✅ {description}: {response.headers[header]}")
            else:
                print(f"❌ Missing {description} header")

    return results

async def test_rate_limiting(base_url: str) -> bool:
    """Test rate limiting is active"""
    async with httpx.AsyncClient() as client:
        # Send many requests quickly
        responses = []
        for _ in range(100):
            response = await client.get(f"{base_url}/health")
            responses.append(response.status_code)

        # Check if any were rate limited
        rate_limited = any(status == 429 for status in responses)
        if rate_limited:
            print("✅ Rate limiting is active")
        else:
            print("⚠️  Rate limiting may not be configured")

        return rate_limited

if __name__ == "__main__":
    import sys
    base_url = sys.argv[1] if len(sys.argv) > 1 else "https://atomcp.kooshapari.com"

    asyncio.run(check_security_headers(base_url))
    asyncio.run(test_rate_limiting(base_url))
```

---

## 9. Monitoring Setup

### 9.1 Metrics to Monitor

```yaml
# Application Metrics
- Request rate (req/s)
- Response time (p50, p95, p99)
- Error rate (4xx, 5xx)
- Active sessions
- Cache hit rate
- Database connection pool

# Infrastructure Metrics
- CPU usage
- Memory usage
- Disk I/O
- Network I/O
- Lambda cold starts
- Lambda duration

# Business Metrics
- Active users
- API calls per user
- Tool usage statistics
- Authentication success rate
```

### 9.2 Monitoring Configuration

```python
# Logging configuration
import logging
import json
from datetime import datetime

class StructuredLogger:
    """Structured JSON logging for monitoring"""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        handler = logging.StreamHandler()
        handler.setFormatter(self.JsonFormatter())
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    class JsonFormatter(logging.Formatter):
        def format(self, record):
            log_obj = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno
            }
            if hasattr(record, 'extra'):
                log_obj.update(record.extra)
            return json.dumps(log_obj)

    def info(self, message: str, **kwargs):
        self.logger.info(message, extra=kwargs)

    def error(self, message: str, **kwargs):
        self.logger.error(message, extra=kwargs)

    def warning(self, message: str, **kwargs):
        self.logger.warning(message, extra=kwargs)

# Usage
logger = StructuredLogger(__name__)
logger.info("API request", endpoint="/api/mcp/tools", method="GET", user_id="123")
```

### 9.3 Alert Configuration

```yaml
# Alert Rules
alerts:
  - name: high_error_rate
    condition: error_rate > 1%
    duration: 5m
    severity: critical
    action: page_oncall

  - name: high_response_time
    condition: p95_response_time > 1000ms
    duration: 10m
    severity: warning
    action: slack_notification

  - name: low_cache_hit_rate
    condition: cache_hit_rate < 70%
    duration: 15m
    severity: info
    action: email_team

  - name: database_connection_pool_exhausted
    condition: available_connections < 2
    duration: 1m
    severity: critical
    action: page_oncall
```

---

## 10. Backup and Recovery

### 10.1 Backup Strategy

```bash
# Database Backups
□ Daily automated backups
□ Point-in-time recovery enabled
□ Cross-region backup replication
□ Backup retention: 30 days
□ Monthly backup archives: 12 months

# Configuration Backups
□ Environment variables backed up
□ Vercel configuration in git
□ Secrets in secure vault
□ Infrastructure as code

# Code Backups
□ Git repository with tags for releases
□ Multiple remote repositories
□ Automated deployment from git
```

### 10.2 Recovery Procedures

```bash
#!/bin/bash
# Disaster recovery script

set -e

echo "🚨 Starting disaster recovery..."

# 1. Restore database
echo "Restoring database..."
supabase db restore --backup-id $BACKUP_ID

# 2. Verify database
echo "Verifying database..."
python3 scripts/verify_database.py

# 3. Restore environment variables
echo "Restoring environment variables..."
vercel env pull .env.production

# 4. Deploy application
echo "Deploying application..."
vercel --prod --force

# 5. Run health checks
echo "Running health checks..."
python3 scripts/health_check.py https://atomcp.kooshapari.com

# 6. Validate functionality
echo "Validating core functionality..."
python3 scripts/smoke_tests.py

echo "✅ Recovery complete!"
```

### 10.3 Rollback Procedures

```bash
#!/bin/bash
# Rollback to previous version

set -e

PREVIOUS_VERSION=$1

if [ -z "$PREVIOUS_VERSION" ]; then
    echo "Usage: ./rollback.sh <version>"
    exit 1
fi

echo "🔄 Rolling back to version $PREVIOUS_VERSION..."

# 1. Checkout previous version
git checkout $PREVIOUS_VERSION

# 2. Deploy previous version
vercel --prod --force

# 3. Verify rollback
curl -s https://atomcp.kooshapari.com/health | jq '.version'

echo "✅ Rollback complete!"
```

---

## Final Verification Checklist

### Pre-Production Verification

```bash
□ All environment variables configured
□ Dependencies installed and verified
□ Database migrations completed
□ Authentication flow tested
□ Health checks passing
□ Performance baselines met
□ Security headers configured
□ Monitoring alerts set up
□ Backup procedures tested
□ Documentation updated
```

### Post-Deployment Verification

```bash
□ Application accessible at production URL
□ Health endpoint returning 200 OK
□ Authentication working correctly
□ API endpoints responding
□ No errors in logs
□ Metrics being collected
□ Alerts configured and tested
□ Performance within baselines
□ SSL certificate valid
□ DNS configured correctly
```

### Sign-off Checklist

```bash
□ Engineering team approval
□ Security team review
□ Operations team ready
□ Support team briefed
□ Documentation published
□ Rollback plan tested
□ Communication sent to stakeholders
□ Monitoring dashboard shared
□ On-call schedule updated
□ Launch metrics defined
```

---

## Appendix A: Troubleshooting Common Issues

### Issue: Lambda Cold Starts

```python
# Mitigation: Keep Lambda warm
import asyncio
import httpx

async def keep_warm():
    """Keep Lambda functions warm"""
    while True:
        async with httpx.AsyncClient() as client:
            await client.get("https://atomcp.kooshapari.com/health")
        await asyncio.sleep(300)  # Every 5 minutes
```

### Issue: Database Connection Errors

```python
# Solution: Connection retry logic
import time
from functools import wraps

def retry_on_connection_error(max_retries=3, delay=1):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except ConnectionError as e:
                    if attempt == max_retries - 1:
                        raise
                    await asyncio.sleep(delay * (2 ** attempt))
            return None
        return wrapper
    return decorator
```

### Issue: Rate Limiting False Positives

```python
# Solution: Implement sliding window rate limiting
from collections import deque
from datetime import datetime, timedelta

class SlidingWindowRateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window = timedelta(seconds=window_seconds)
        self.requests = deque()

    def is_allowed(self, user_id: str) -> bool:
        now = datetime.utcnow()
        # Remove old requests
        while self.requests and self.requests[0][0] < now - self.window:
            self.requests.popleft()

        # Check if allowed
        user_requests = sum(1 for _, uid in self.requests if uid == user_id)
        if user_requests >= self.max_requests:
            return False

        self.requests.append((now, user_id))
        return True
```

---

## Appendix B: Emergency Contacts

```yaml
on_call:
  primary: "+1-555-0100"
  secondary: "+1-555-0101"
  escalation: "+1-555-0102"

teams:
  engineering:
    slack: "#atoms-engineering"
    email: "engineering@atoms.tech"

  operations:
    slack: "#atoms-ops"
    email: "ops@atoms.tech"

  security:
    slack: "#atoms-security"
    email: "security@atoms.tech"

vendors:
  vercel:
    support: "https://vercel.com/support"
    status: "https://www.vercel-status.com"

  supabase:
    support: "https://supabase.com/support"
    status: "https://status.supabase.com"

  workos:
    support: "https://workos.com/support"
    status: "https://status.workos.com"
```

---

## Document Version

- **Version**: 1.0.0
- **Last Updated**: October 16, 2025
- **Authors**: Atoms Engineering Team
- **Review Cycle**: Monthly
- **Next Review**: November 16, 2025

---

*This document is maintained in the atoms-mcp-prod repository. For updates or corrections, please submit a pull request.*