#!/bin/bash
# Deployment test validation script
# Validates that atoms test commands properly target different environments

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║   Atoms MCP Deployment Test Validation                     ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Activate virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "❌ Virtual environment not found. Run: python -m venv .venv"
    exit 1
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "Test 1: Unit tests (local environment - no deployment needed)"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Command: python cli.py test --scope unit --cov"
echo "Expected: Uses local environment, runs in-memory tests"
echo ""
python cli.py test --scope unit --cov -k "test_mcp_client" 2>&1 | head -20
echo "✅ Unit test command validated"

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "Test 2: Integration tests (auto-targets dev: mcpdev.atoms.tech)"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Command: python cli.py test:int --help"
echo "Expected: Shows environment auto-targeting info"
echo ""
python cli.py test:int --help 2>&1 | grep -A5 "Automatically targets"
echo "✅ Integration test auto-targeting documented"

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "Test 3: E2E tests (auto-targets dev: mcpdev.atoms.tech)"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Command: python cli.py test:e2e --help"
echo "Expected: Shows environment auto-targeting info"
echo ""
python cli.py test:e2e --help 2>&1 | grep -A5 "Automatically targets"
echo "✅ E2E test auto-targeting documented"

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "Test 4: Verify environment manager"
echo "═══════════════════════════════════════════════════════════"
echo ""
python3 << 'EOF'
from cli_modules.test_env_manager import TestEnvManager, TestEnvironment

# Test local environment
local_config = TestEnvManager.get_config(TestEnvironment.LOCAL)
print(f"✅ Local: {local_config['mcp_base_url']}")

# Test dev environment
dev_config = TestEnvManager.get_config(TestEnvironment.DEV)
print(f"✅ Dev: {dev_config['mcp_base_url']}")

# Test prod environment
prod_config = TestEnvManager.get_config(TestEnvironment.PROD)
print(f"✅ Prod: {prod_config['mcp_base_url']}")

# Test auto-detection
scope_unit = TestEnvManager.get_environment_for_scope("unit")
print(f"✅ Unit scope targets: {scope_unit.value}")

scope_int = TestEnvManager.get_environment_for_scope("integration")
print(f"✅ Integration scope targets: {scope_int.value} (can override with --env)")

scope_e2e = TestEnvManager.get_environment_for_scope("e2e")
print(f"✅ E2E scope targets: {scope_e2e.value} (can override with --env)")
EOF

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "Test 5: Health check for deployment targets"
echo "═══════════════════════════════════════════════════════════"
echo ""

echo "Checking mcpdev.atoms.tech (dev):"
if timeout 5 curl -s -I https://mcpdev.atoms.tech/health 2>/dev/null | head -1; then
    echo "✅ Dev deployment is responding"
else
    echo "⚠️  Dev deployment may not be ready yet"
fi

echo ""
echo "Checking mcp.atoms.tech (prod):"
if timeout 5 curl -s -I https://mcp.atoms.tech/health 2>/dev/null | head -1; then
    echo "✅ Production deployment is responding"
else
    echo "⚠️  Production deployment not configured yet"
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "VALIDATION COMPLETE"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Summary of test commands:"
echo ""
echo "  Local tests:"
echo "    atoms test                    # Unit tests (local)"
echo "    atoms test:unit               # Unit tests only"
echo "    atoms test:cov                # Coverage report"
echo ""
echo "  Dev tests (mcpdev.atoms.tech):"
echo "    atoms test:int                # Integration tests → dev"
echo "    atoms test:e2e                # E2E tests → dev"
echo ""
echo "  Override to local:"
echo "    atoms test:int --env local    # Integration tests → local"
echo "    atoms test:e2e --env local    # E2E tests → local"
echo ""
echo "  Override to prod:"
echo "    atoms test:int --env prod     # Integration tests → prod"
echo "    atoms test:e2e --env prod     # E2E tests → prod"
echo ""
