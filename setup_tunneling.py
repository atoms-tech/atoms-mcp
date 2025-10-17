#!/usr/bin/env python3
"""
Setup tunneling for atoms-mcp and morph-mcp using pheno-sdk infrastructure.

This script configures tunneling to:
- atoms-mcp → ai.kooshapari.com
- morph-mcp → morph.kooshapari.com

Uses pheno-sdk's kinfra SmartInfraManager for automatic tunnel configuration.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project roots to path
atoms_root = Path(__file__).parent
morph_root = atoms_root.parent / "morph"
router_root = atoms_root.parent / "router"

for root in [atoms_root, morph_root, router_root]:
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

# Import pheno-sdk infrastructure
try:
    from pheno.infra.kinfra import SmartInfraManager
    from pheno.infra.networking.tunnel_setup import TunnelConfig, TunnelManager
    print("✓ Pheno-SDK infrastructure libraries loaded")
except ImportError as e:
    print(f"⚠ Pheno-SDK not fully available: {e}")
    print("Attempting fallback installation...")
    os.system("pip install pheno-sdk kinfra")
    from pheno.infra.kinfra import SmartInfraManager
    from pheno.infra.networking.tunnel_setup import TunnelConfig, TunnelManager


async def setup_atoms_mcp_tunnel():
    """Setup tunneling for atoms-mcp to ai.kooshapari.com"""
    print("\n" + "="*80)
    print("Setting up atoms-mcp tunnel to ai.kooshapari.com")
    print("="*80)

    try:
        # Initialize infrastructure manager
        infra = SmartInfraManager(
            project_name="atoms_mcp",
            domain="ai.kooshapari.com",
            local_port=8000,
            app_port=8000,
        )

        # Configure tunnel
        tunnel_config = TunnelConfig(
            local_port=8000,
            remote_host="ai.kooshapari.com",
            protocol="https",
            auth_enabled=True,
        )

        # Start tunnel
        tunnel_manager = TunnelManager(infra.config)
        tunnel_info = await tunnel_manager.setup_tunnel(tunnel_config)

        print(f"\n✓ Tunnel configured:")
        print(f"  Local:    http://localhost:8000")
        print(f"  Remote:   https://{tunnel_info.get('remote_url', 'ai.kooshapari.com')}")
        print(f"  Status:   {tunnel_info.get('status', 'active')}")

        # Save configuration
        config_file = atoms_root / ".tunnel_config.json"
        import json
        with open(config_file, "w") as f:
            json.dump({
                "service": "atoms-mcp",
                "local_port": 8000,
                "domain": "ai.kooshapari.com",
                "tunnel_url": tunnel_info.get('remote_url'),
                "status": "active",
            }, f, indent=2)

        print(f"\n✓ Configuration saved to {config_file}")
        return True

    except Exception as e:
        print(f"✗ Error setting up atoms-mcp tunnel: {e}")
        return False


async def setup_morph_mcp_tunnel():
    """Setup tunneling for morph-mcp to morph.kooshapari.com"""
    print("\n" + "="*80)
    print("Setting up morph-mcp tunnel to morph.kooshapari.com")
    print("="*80)

    try:
        # Initialize infrastructure manager
        infra = SmartInfraManager(
            project_name="morph_mcp",
            domain="morph.kooshapari.com",
            local_port=8001,
            app_port=8001,
        )

        # Configure tunnel
        tunnel_config = TunnelConfig(
            local_port=8001,
            remote_host="morph.kooshapari.com",
            protocol="https",
            auth_enabled=True,
        )

        # Start tunnel
        tunnel_manager = TunnelManager(infra.config)
        tunnel_info = await tunnel_manager.setup_tunnel(tunnel_config)

        print(f"\n✓ Tunnel configured:")
        print(f"  Local:    http://localhost:8001")
        print(f"  Remote:   https://{tunnel_info.get('remote_url', 'morph.kooshapari.com')}")
        print(f"  Status:   {tunnel_info.get('status', 'active')}")

        # Save configuration
        config_file = morph_root / ".tunnel_config.json"
        import json
        with open(config_file, "w") as f:
            json.dump({
                "service": "morph-mcp",
                "local_port": 8001,
                "domain": "morph.kooshapari.com",
                "tunnel_url": tunnel_info.get('remote_url'),
                "status": "active",
            }, f, indent=2)

        print(f"\n✓ Configuration saved to {config_file}")
        return True

    except Exception as e:
        print(f"✗ Error setting up morph-mcp tunnel: {e}")
        return False


async def verify_tunnels():
    """Verify both tunnels are working"""
    print("\n" + "="*80)
    print("Verifying tunnel connectivity")
    print("="*80)

    import httpx

    # Test atoms-mcp tunnel
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("https://ai.kooshapari.com/health")
            if response.status_code == 200:
                print("✓ atoms-mcp tunnel: ACTIVE")
            else:
                print(f"⚠ atoms-mcp tunnel: Status {response.status_code}")
    except Exception as e:
        print(f"⚠ atoms-mcp tunnel check failed: {e}")

    # Test morph-mcp tunnel
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("https://morph.kooshapari.com/health")
            if response.status_code == 200:
                print("✓ morph-mcp tunnel: ACTIVE")
            else:
                print(f"⚠ morph-mcp tunnel: Status {response.status_code}")
    except Exception as e:
        print(f"⚠ morph-mcp tunnel check failed: {e}")


async def main():
    """Main setup function"""
    print("\n" + "="*80)
    print("Atoms & Morph MCP Tunnel Setup")
    print("Using pheno-sdk infrastructure libraries")
    print("="*80)

    # Setup both tunnels
    atoms_ok = await setup_atoms_mcp_tunnel()
    morph_ok = await setup_morph_mcp_tunnel()

    # Verify connectivity
    if atoms_ok or morph_ok:
        await verify_tunnels()

    # Summary
    print("\n" + "="*80)
    print("Setup Summary")
    print("="*80)
    print(f"✓ atoms-mcp → ai.kooshapari.com: {'✓ Ready' if atoms_ok else '✗ Failed'}")
    print(f"✓ morph-mcp → morph.kooshapari.com: {'✓ Ready' if morph_ok else '✗ Failed'}")
    print("\nNext steps:")
    print("1. Start atoms-mcp:  ./atoms start")
    print("2. Start morph-mcp:  cd ../morph && ./morph start")
    print("3. Access tunnels:")
    print("   - atoms-mcp: https://ai.kooshapari.com")
    print("   - morph-mcp: https://morph.kooshapari.com")
    print("="*80 + "\n")

    return atoms_ok and morph_ok


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
