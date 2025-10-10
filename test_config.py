#!/usr/bin/env python3
"""Test atoms_mcp-old configuration."""

import os
import sys
from pathlib import Path

# Colors
GREEN = '\033[0;32m'
RED = '\033[0;31m'
BLUE = '\033[0;34m'
NC = '\033[0m'

def check(condition, message):
    """Check a condition and print result."""
    if condition:
        print(f"{GREEN}✓{NC} {message}")
        return True
    else:
        print(f"{RED}✗{NC} {message}")
        return False

def main():
    print(f"{BLUE}======================================{NC}")
    print(f"{BLUE}  Atoms MCP Configuration Test{NC}")
    print(f"{BLUE}======================================{NC}")
    print()

    # Load .env
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

    passed = 0
    total = 0

    # Test 1: .env file exists
    total += 1
    if check(env_file.exists(), ".env file exists"):
        passed += 1

    # Test 2: Port configuration - check both PORT and ATOMS_FASTMCP_PORT
    total += 1
    port = os.environ.get('PORT') or os.environ.get('ATOMS_FASTMCP_PORT', '')
    if check(port == '50002', f"PORT=50002 (found: {port})"):
        passed += 1

    # Test 3: Public URL configuration
    total += 1
    public_url = os.environ.get('PUBLIC_URL', '')
    if check(public_url == 'https://atomcp.kooshapari.com', f"PUBLIC_URL correct (found: {public_url})"):
        passed += 1

    # Test 4: SRVC configuration
    total += 1
    srvc = os.environ.get('SRVC', '')
    if check(srvc == 'atoms-mcp', f"SRVC=atoms-mcp (found: {srvc})"):
        passed += 1

    # Test 5: CloudFlare config exists
    total += 1
    tunnel_config = Path.home() / ".cloudflared" / "config-atomcp.yml"
    if check(tunnel_config.exists(), "CloudFlare tunnel config exists"):
        passed += 1
        
        # Test 6: Tunnel config has correct port
        total += 1
        with open(tunnel_config) as f:
            config_content = f.read()
            if check('127.0.0.1:50002' in config_content, "Tunnel config uses port 50002"):
                passed += 1

    # Test 7: SmartInfraManager exists
    total += 1
    smart_infra = Path("utils/smart_infra.py")
    if check(smart_infra.exists(), "SmartInfraManager exists"):
        passed += 1

    # Test 8: Server can be imported
    total += 1
    try:
        # Set PORT (canonical) and ATOMS_FASTMCP_PORT (backward compatibility)
        os.environ['PORT'] = '50002'
        os.environ['ATOMS_FASTMCP_PORT'] = '50002'
        from server import create_consolidated_server
        if check(True, "Server module imports successfully"):
            passed += 1
    except Exception as e:
        check(False, f"Server module import failed: {e}")

    # Test 9: startup script exists
    total += 1
    if check(Path("start_atoms.sh").exists(), "start_atoms.sh exists"):
        passed += 1

    # Test 10: startup script is executable
    total += 1
    start_script = Path("start_atoms.sh")
    if start_script.exists():
        if check(os.access(start_script, os.X_OK), "start_atoms.sh is executable"):
            passed += 1

    # Summary
    print()
    print(f"{BLUE}======================================{NC}")
    print(f"  Results: {GREEN}{passed}/{total}{NC} tests passed")
    print(f"{BLUE}======================================{NC}")

    if passed == total:
        print(f"\n{GREEN}✓ All tests passed! Configuration is correct.{NC}")
        print(f"\nTo start the server:")
        print(f"  ./start_atoms.sh")
        return 0
    else:
        print(f"\n{RED}✗ Some tests failed. Please review the configuration.{NC}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
