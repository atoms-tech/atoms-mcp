#!/bin/bash
#
# Setup tunneling for atoms-mcp and morph-mcp using pheno-sdk
#
# Usage: ./setup_tunnels.sh
#
# Sets up:
# - atoms-mcp → ai.kooshapari.com
# - morph-mcp → morph.kooshapari.com

set -e

echo "================================================================================"
echo "Atoms & Morph MCP Tunnel Setup"
echo "Using pheno-sdk infrastructure libraries"
echo "================================================================================"

# Detect project roots
ATOMS_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$ATOMS_ROOT")"
MORPH_ROOT="$PROJECT_ROOT/morph"

echo ""
echo "Project roots detected:"
echo "  atoms-mcp: $ATOMS_ROOT"
echo "  morph-mcp: $MORPH_ROOT"
echo ""

# Function to setup tunnel using pheno-sdk
setup_tunnel() {
    local service=$1
    local domain=$2
    local local_port=$3
    local project_root=$4

    echo "================================================================================"
    echo "Setting up $service tunnel to $domain"
    echo "================================================================================"

    cd "$project_root"

    # Check if pheno-sdk is available
    if ! python -c "from pheno.infra.kinfra import SmartInfraManager" 2>/dev/null; then
        echo "⚠ Installing pheno-sdk infrastructure libraries..."
        pip install pheno-sdk kinfra >/dev/null 2>&1
    fi

    # Setup using pheno CLI if available
    if command -v pheno &> /dev/null; then
        echo "✓ Using pheno CLI for tunnel setup"
        pheno infra tunnel setup \
            --service "$service" \
            --domain "$domain" \
            --local-port "$local_port" \
            --protocol https \
            --auto-start
    else
        echo "✓ Using Python infrastructure setup"
        python -c "
import asyncio
from pheno.infra.kinfra import SmartInfraManager

async def setup():
    infra = SmartInfraManager(
        project_name='${service}',
        domain='${domain}',
        local_port=${local_port},
    )
    config = infra.get_project_config()
    print(f'  Local:  http://localhost:${local_port}')
    print(f'  Remote: https://${domain}')
    print(f'  Status: configured')
    return config

asyncio.run(setup())
"
    fi

    echo ""
    echo "✓ Tunnel configured for $service"
    echo ""
}

# Setup atoms-mcp tunnel
setup_tunnel "atoms-mcp" "ai.kooshapari.com" "8000" "$ATOMS_ROOT"

# Setup morph-mcp tunnel
setup_tunnel "morph-mcp" "morph.kooshapari.com" "8001" "$MORPH_ROOT"

# Display summary
echo "================================================================================"
echo "Tunnel Setup Summary"
echo "================================================================================"
echo ""
echo "✓ atoms-mcp tunneling:"
echo "  Local:  http://localhost:8000"
echo "  Remote: https://ai.kooshapari.com"
echo ""
echo "✓ morph-mcp tunneling:"
echo "  Local:  http://localhost:8001"
echo "  Remote: https://morph.kooshapari.com"
echo ""
echo "Next steps:"
echo ""
echo "1. Start atoms-mcp:"
echo "   cd $ATOMS_ROOT"
echo "   ./atoms start"
echo ""
echo "2. Start morph-mcp:"
echo "   cd $MORPH_ROOT"
echo "   ./morph start"
echo ""
echo "3. Access via tunnels:"
echo "   atoms-mcp: https://ai.kooshapari.com"
echo "   morph-mcp: https://morph.kooshapari.com"
echo ""
echo "================================================================================"
echo ""
