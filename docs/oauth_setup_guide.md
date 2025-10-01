# WorkOS OAuth 2.0 PKCE + DCR Setup Guide

## Overview

This guide explains how to configure WorkOS AuthKit to provide OAuth 2.0 PKCE (Proof Key for Code Exchange) with Dynamic Client Registration (DCR) for MCP servers while maintaining existing user data in Supabase.

## Architecture

- **WorkOS AuthKit**: OAuth 2.0 authorization server with PKCE and DCR support
- **Supabase Auth**: User credential storage and validation
- **MCP Server**: OAuth-compliant server with proxy authentication

## WorkOS Setup

### 1. Create WorkOS Account

1. Sign up at [WorkOS Dashboard](https://dashboard.workos.com)
2. Create a new project/application

### 2. Configure Authentication Methods

Enable the same authentication methods you use in Supabase:
- **Email/Password**: Enable in WorkOS User Management
- **GitHub OAuth**: Configure GitHub provider
- **Google OAuth**: Configure Google provider

### 3. Get API Credentials

From the WorkOS Dashboard, get:
- **API Key**: Found in API Keys section
- **Client ID**: Found in Configuration section

### 4. Configure Redirect URIs in WorkOS Dashboard

**IMPORTANT**: Before testing, configure these redirect URIs in your WorkOS Dashboard under "Redirects":

- **Development**: `http://localhost:8000/oauth/callback`
- **Production**: `https://your-production-domain.com/oauth/callback`

### 5. Environment Variables (Already Configured)

```bash
# WorkOS Configuration for OAuth 2.0 PKCE + DCR
WORKOS_API_KEY=sk_test_a2V5XzAxSzRDR1cyMjJXSlFXQlI1RDdDUFczUUM3LGxDdWJmN2tNTDBjaHlRNjhUaEtsalQ0ZTMu
WORKOS_CLIENT_ID=client_01K4CGW2J1FGWZYZJDMVWGQZBD
WORKOS_API_URL=https://api.workos.com
```

## OAuth Flow for MCP Clients

### 1. Dynamic Client Registration (DCR)

```python
# Register OAuth client
client_data = {
    "redirect_uris": ["http://localhost:3000/oauth/callback"],
    "client_name": "My MCP Client",
    "grant_types": ["authorization_code"],
    "response_types": ["code"],
    "token_endpoint_auth_method": "none"  # PKCE only
}

response = mcp_client.call_tool("oauth_register_client", {"client_data": client_data})
client_id = response["client_id"]
```

### 2. PKCE Challenge Generation

```python
import secrets
import hashlib
import base64

# Generate PKCE parameters
code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
code_challenge = base64.urlsafe_b64encode(
    hashlib.sha256(code_verifier.encode('utf-8')).digest()
).decode('utf-8').rstrip('=')
```

### 3. Authorization Request

```python
# Start OAuth flow
auth_response = mcp_client.call_tool("oauth_authorize", {
    "client_id": client_id,
    "redirect_uri": "http://localhost:3000/oauth/callback",
    "state": "random_state_value",
    "code_challenge": code_challenge,
    "code_challenge_method": "S256"
})

challenge_id = auth_response["challenge_id"]
```

### 4. User Authentication

```python
# Authenticate with existing Supabase credentials
auth_result = mcp_client.call_tool("oauth_authenticate", {
    "challenge_id": challenge_id,
    "username": "user@example.com",
    "password": "user_password"
})

authorization_code = auth_result["code"]
```

### 5. Token Exchange

```python
# Exchange code for access token
token_response = mcp_client.call_tool("oauth_token", {
    "grant_type": "authorization_code",
    "code": authorization_code,
    "client_id": client_id,
    "code_verifier": code_verifier
})

access_token = token_response["access_token"]
```

## Supported Authentication Methods

### Email/Password Authentication

Users authenticate with their existing Supabase email/password:

```python
auth_result = mcp_client.call_tool("oauth_authenticate", {
    "challenge_id": challenge_id,
    "username": "user@example.com",
    "password": "password123"
})
```

### GitHub OAuth Authentication

For users who signed up via GitHub:

```python
# User completes GitHub OAuth flow first, then:
auth_result = mcp_client.call_tool("oauth_authenticate", {
    "challenge_id": challenge_id,
    "provider": "github",
    "oauth_code": "github_oauth_code"
})
```

### Google OAuth Authentication

For users who signed up via Google:

```python
# User completes Google OAuth flow first, then:
auth_result = mcp_client.call_tool("oauth_authenticate", {
    "challenge_id": challenge_id,
    "provider": "google",
    "oauth_code": "google_oauth_code"
})
```

## Development Setup

### Install Dependencies

```bash
pip install workos>=1.0.0
```

### Configure Environment

```bash
# Copy example environment
cp .env.example .env

# Add WorkOS credentials
echo "WORKOS_API_KEY=sk_test_your_key" >> .env
echo "WORKOS_CLIENT_ID=client_your_id" >> .env
```

### Test OAuth Flow

```bash
# Start MCP server
python -m atoms_mcp-old.server

# Test DCR endpoint
curl -X POST http://localhost:8000/api/mcp \
  -H "Content-Type: application/json" \
  -d '{"method": "oauth_register_client", "params": {"client_data": {"redirect_uris": ["http://localhost:3000/callback"]}}}'
```

## Security Considerations

1. **PKCE Required**: All OAuth flows must use PKCE for security
2. **State Parameter**: Always include state parameter for CSRF protection
3. **Redirect URI Validation**: Registered redirect URIs are strictly validated
4. **Token Expiration**: Access tokens expire in 1 hour
5. **Credential Isolation**: Supabase credentials never leave the proxy service

## Troubleshooting

### Common Issues

1. **Invalid Client Error**: Ensure client_id is registered via DCR
2. **PKCE Verification Failed**: Check code_verifier matches code_challenge
3. **Supabase Auth Failed**: Verify user exists and credentials are correct
4. **WorkOS API Error**: Check API key and client ID configuration

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
python -m atoms_mcp-old.server
```

## Migration Notes

- **No User Migration Required**: All user data remains in Supabase
- **Backward Compatibility**: Existing authentication methods continue to work
- **Gradual Rollout**: OAuth can be enabled alongside existing auth
- **Zero Downtime**: No service interruption during setup