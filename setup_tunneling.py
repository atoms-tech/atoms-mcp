#!/usr/bin/env python3
"""Create public tunnels for atoms-mcp and morph-mcp services."""

from __future__ import annotations

import asyncio
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import httpx

PHENO_SRC = Path(__file__).resolve().parent.parent / "pheno-sdk" / "src"
if PHENO_SRC.exists():
    sys.path.insert(0, str(PHENO_SRC))

from pheno.infra.tunneling import (  # noqa: E402
    TunnelConfig,
    TunnelManager,
    TunnelProtocol,
    TunnelType,
)

BASE_DIR = Path(__file__).parent


@dataclass(slots=True)
class TunnelTarget:
    service: str
    domain: str
    local_port: int
    config_path: Path


TARGETS = [
    TunnelTarget(
        service="atoms-mcp",
        domain="ai.kooshapari.com",
        local_port=8000,
        config_path=BASE_DIR / ".tunnel_atoms.json",
    ),
    TunnelTarget(
        service="morph-mcp",
        domain="morph.kooshapari.com",
        local_port=8001,
        config_path=BASE_DIR.parent / "morph" / ".tunnel_morph.json",
    ),
]


async def establish_tunnel(target: TunnelTarget) -> dict[str, str]:
    print("\n" + "=" * 80)
    print(f"Creating tunnel for {target.service} → {target.domain}")
    print("=" * 80)

    config = TunnelConfig(
        name=target.domain,
        tunnel_type=TunnelType.CLOUDFLARE,
        protocol=TunnelProtocol.HTTPS,
        local_host="127.0.0.1",
        local_port=target.local_port,
        metadata={"service": target.service},
    )

    manager = TunnelManager(
        {
            "domain": config.name,
            "local_host": config.local_host,
            "local_port": config.local_port,
            "protocol": config.protocol.value,
            "tunnel_type": config.tunnel_type.value,
        }
    )

    info = await manager.establish()

    payload = {
        "service": target.service,
        "domain": target.domain,
        "local_host": config.local_host,
        "local_port": config.local_port,
        "tunnel_url": info.public_url,
        "status": "active",
    }

    target.config_path.write_text(json.dumps(payload, indent=2))
    print(f"✓ Saved configuration to {target.config_path}")
    return payload


async def verify_tunnel(tunnel: dict[str, str]) -> None:
    url = f"https://{tunnel['domain']}/health"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                print(f"✓ {tunnel['service']} tunnel healthy ({url})")
            else:
                print(f"⚠ {tunnel['service']} tunnel returned status {response.status_code} ({url})")
    except Exception as exc:  # pragma: no cover - network validation
        print(f"⚠ {tunnel['service']} tunnel verification failed: {exc}")


async def main() -> bool:
    tunnels = []
    for target in TARGETS:
        try:
            tunnels.append(await establish_tunnel(target))
        except Exception as exc:
            print(f"❌ Failed to create tunnel for {target.service}: {exc}")
            return False

    print("\n" + "=" * 80)
    print("Verifying tunnels")
    print("=" * 80)
    await asyncio.gather(*(verify_tunnel(tunnel) for tunnel in tunnels))
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    print("\n" + "=" * 80)
    if success:
        print("✅ Tunnel provisioning complete")
    else:
        print("❌ Tunnel provisioning failed")
    print("=" * 80)
