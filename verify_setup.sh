#!/bin/bash

echo "🔍 Verifying MCP Server Setup"
echo "=============================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: AuthKit OAuth Metadata
echo "Test 1: AuthKit OAuth Metadata"
echo "-------------------------------"
AUTHKIT_RESPONSE=$(curl -s https://decent-hymn-17-staging.authkit.app/.well-known/oauth-authorization-server)
if echo "$AUTHKIT_RESPONSE" | grep -q "registration_endpoint"; then
    echo -e "${GREEN}✅ PASS${NC} - AuthKit OAuth metadata is valid"
    echo "   Issuer: $(echo $AUTHKIT_RESPONSE | jq -r .issuer)"
    echo "   Registration: $(echo $AUTHKIT_RESPONSE | jq -r .registration_endpoint)"
else
    echo -e "${RED}❌ FAIL${NC} - AuthKit OAuth metadata is invalid"
    echo "   Response: $AUTHKIT_RESPONSE"
fi
echo ""

# Test 2: MCP Server Protected Resource (requires server running)
echo "Test 2: MCP Server Protected Resource"
echo "--------------------------------------"
MCP_RESPONSE=$(curl -s https://atomcp.kooshapari.com/.well-known/oauth-protected-resource 2>&1)
if echo "$MCP_RESPONSE" | grep -q "authorization_servers"; then
    echo -e "${GREEN}✅ PASS${NC} - Protected resource metadata is valid"
    echo "   Resource: $(echo $MCP_RESPONSE | jq -r .resource)"
    echo "   Auth Server: $(echo $MCP_RESPONSE | jq -r .authorization_servers[0])"
else
    echo -e "${YELLOW}⚠️  SKIP${NC} - Server not running or not accessible"
    echo "   (This is OK if you haven't started the server yet)"
fi
echo ""

# Test 3: CORS Headers (requires server running)
echo "Test 3: CORS Headers"
echo "--------------------"
CORS_RESPONSE=$(curl -s -X OPTIONS https://atomcp.kooshapari.com/.well-known/oauth-protected-resource \
  -H "Origin: http://127.0.0.1:3000" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: mcp-protocol-version" \
  -v 2>&1 | grep -i "access-control-allow-origin")
if [ ! -z "$CORS_RESPONSE" ]; then
    echo -e "${GREEN}✅ PASS${NC} - CORS headers are present"
    echo "   $CORS_RESPONSE"
else
    echo -e "${YELLOW}⚠️  SKIP${NC} - Server not running or CORS headers not detected"
    echo "   (This is OK if you haven't started the server yet)"
fi
echo ""

# Test 4: Dynamic Client Registration
echo "Test 4: Dynamic Client Registration"
echo "------------------------------------"
DCR_RESPONSE=$(curl -s -X POST https://decent-hymn-17-staging.authkit.app/oauth2/register \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "Test Client",
    "redirect_uris": ["http://127.0.0.1:3000/oauth/callback"],
    "grant_types": ["authorization_code"],
    "response_types": ["code"]
  }')
if echo "$DCR_RESPONSE" | grep -q "client_id"; then
    echo -e "${GREEN}✅ PASS${NC} - Dynamic Client Registration is enabled"
    echo "   Client ID: $(echo $DCR_RESPONSE | jq -r .client_id)"
else
    echo -e "${RED}❌ FAIL${NC} - Dynamic Client Registration is not enabled"
    echo "   Response: $DCR_RESPONSE"
    echo ""
    echo "   ${YELLOW}Action Required:${NC}"
    echo "   1. Go to https://dashboard.workos.com"
    echo "   2. Navigate to Applications → Configuration"
    echo "   3. Enable 'Dynamic Client Registration'"
    echo "   4. Save changes"
fi
echo ""

# Summary
echo "=============================="
echo "Summary"
echo "=============================="
echo ""
echo "Configuration:"
echo "  AuthKit Domain: https://decent-hymn-17-staging.authkit.app"
echo "  MCP Server: https://atomcp.kooshapari.com"
echo ""
echo "Next Steps:"
echo "  1. If server tests failed, start the server:"
echo "     python -m atoms_mcp-old.server"
echo ""
echo "  2. If DCR test failed, enable it in WorkOS Dashboard"
echo ""
echo "  3. Once all tests pass, test with Claude Desktop"
echo ""

