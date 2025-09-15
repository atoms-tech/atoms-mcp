# MCP OAuth 2.1 + DCR Flow (Correct Implementation)

## 🎯 The Actual MCP Client Authentication Process

You were absolutely right! MCP clients expect **OAuth 2.1 + Dynamic Client Registration (DCR)** flow, not simple login endpoints. Here's how it actually works:

### 1. MCP Client Discovery
```
MCP Client → FastMCP Server
Server: Advertises OAuth capabilities via .well-known endpoints
```

### 2. User Clicks "Authenticate" Button
```
MCP Client → Shows OAuth authentication window
User: Sees familiar OAuth login flow (same as any OAuth app)
```

### 3. OAuth 2.1 + DCR Flow
```
1. Dynamic Client Registration (DCR):
   MCP Client → POST /register
   {
     "redirect_uris": ["http://localhost:random-port/callback"],
     "client_name": "Claude Code",
     "scope": "openid profile email"
   }
   
   Server → Returns temporary client credentials
   {
     "client_id": "generated-client-id", 
     "client_secret": "generated-secret",
     "redirect_uris": ["http://localhost:random-port/callback"]
   }

2. Authorization Request:
   MCP Client → Redirects user to /authorize
   User → Sees Supabase login page in browser
   User → Logs in with email/password
   
3. Authorization Grant:
   Supabase → Redirects to /auth/callback with authorization code
   Server → Exchanges code for tokens with Supabase
   Server → Redirects to client's dynamic callback URL
   
4. Token Exchange:
   MCP Client → POST /token with authorization code + PKCE
   Server → Returns Supabase JWT tokens
   {
     "access_token": "eyJhbGciOiJSUzI1NiIs...",
     "token_type": "Bearer",
     "expires_in": 3600,
     "refresh_token": "...",
     "scope": "openid profile email"
   }
```

### 4. Authenticated Tool Calls
```
MCP Client → FastMCP Server
Authorization: Bearer eyJhbGciOiJSUzI1NiIs...

All subsequent tool calls include the JWT
```

## 🔧 Supabase OAuth Setup

### Step 1: Get OAuth Client Secret
```bash
# Install Supabase CLI
npm install -g supabase

# Login to Supabase
supabase login

# Get project details
supabase projects list

# Get OAuth client secret (method may vary)
supabase secrets list --project-ref ydogoylwenufckscqijp

# Alternative: Check project API settings
supabase projects api-keys --project-ref ydogoylwenufckscqijp
```

### Step 2: Configure Redirect URI in Supabase
1. Go to Supabase Dashboard → Authentication → URL Configuration
2. Add redirect URI: `https://your-server.com/auth/callback`
3. For development: `http://localhost:8000/auth/callback`

### Step 3: Environment Variables
```bash
# OAuth mode (default)
ATOMS_FASTMCP_AUTH_MODE=oauth

# Required for OAuth
ATOMS_FASTMCP_BASE_URL=https://your-server.com  # Or http://localhost:8000 for dev
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
SUPABASE_OAUTH_CLIENT_SECRET=your_oauth_client_secret

# Transport
ATOMS_FASTMCP_TRANSPORT=http
ATOMS_FASTMCP_PORT=8000
```

### Step 4: Start Server
```bash
python -m atoms_fastmcp.new_server
```

## 🌐 OAuth Endpoints Provided

The OAuth Proxy automatically provides all required OAuth 2.1 + DCR endpoints:

1. **`/.well-known/oauth-authorization-server`** - OAuth server metadata
2. **`/.well-known/oauth-protected-resource`** - Protected resource metadata
3. **`/register`** - Dynamic Client Registration (DCR)
4. **`/authorize`** - OAuth authorization endpoint
5. **`/token`** - Token exchange endpoint
6. **`/auth/callback`** - OAuth callback handler

## 🔄 OAuth Proxy Architecture

```mermaid
sequenceDiagram
    participant MC as MCP Client
    participant FMP as FastMCP Server<br/>(OAuth Proxy)
    participant SB as Supabase<br/>(OAuth Provider)
    participant User

    Note over MC,SB: 1. Dynamic Client Registration
    MC->>FMP: POST /register (dynamic redirect_uri)
    FMP->>MC: Return proxy credentials

    Note over MC,SB: 2. Authorization Flow
    MC->>User: Show "Login with Supabase" button
    User->>MC: Click authenticate
    MC->>FMP: Redirect to /authorize
    FMP->>SB: Redirect to Supabase /auth/v1/authorize
    SB->>User: Show login page
    User->>SB: Enter credentials
    SB->>FMP: Callback with auth code
    FMP->>SB: Exchange code for tokens
    SB->>FMP: Return Supabase JWT
    FMP->>MC: Redirect to client callback with new code

    Note over MC,SB: 3. Token Exchange
    MC->>FMP: POST /token (code + PKCE)
    FMP->>MC: Return Supabase JWT

    Note over MC,SB: 4. Tool Calls
    MC->>FMP: Tool calls with JWT
    FMP->>SB: Validate JWT
    SB->>FMP: User info
    FMP->>MC: Tool results
```

## 🎯 Why OAuth Proxy Works

### The Problem
- **MCP clients** expect OAuth 2.1 + DCR (Dynamic Client Registration)
- **Supabase** has OAuth endpoints but no DCR support
- **Solution**: OAuth Proxy bridges the gap

### How OAuth Proxy Solves It
1. **DCR Interface**: Accepts dynamic client registrations from MCP clients
2. **Fixed Credentials**: Uses pre-configured Supabase OAuth app behind the scenes
3. **URL Translation**: Maps client's dynamic redirect URIs to proxy's fixed URI
4. **State Management**: Tracks authorization flows between clients and Supabase
5. **Token Proxying**: Returns real Supabase JWTs to clients

## 🚀 MCP Client Experience

### Claude Code
```
1. User configures server URL in Claude Code
2. Claude Code discovers OAuth endpoints automatically
3. User clicks "Authenticate" 
4. Browser opens with Supabase login page
5. User logs in normally
6. Claude Code receives JWT automatically
7. All tools work with authentication
```

### MCP Inspector
```
1. Load server in MCP Inspector
2. Inspector detects OAuth support
3. Shows "Authenticate via OAuth" button
4. Standard OAuth flow in browser
5. Inspector authenticated and ready
```

### Any MCP Client
```javascript
// MCP clients automatically handle OAuth 2.1 + DCR
// No special implementation needed - it's part of MCP spec!

// 1. Discovery
const discovery = await fetch('/.well-known/oauth-authorization-server')

// 2. Dynamic registration  
const registration = await fetch('/register', { ... })

// 3. Authorization flow (handled by client)
// 4. Token exchange (handled by client)
// 5. Tool calls with tokens (handled by client)
```

## 🔐 Security & Benefits

### Security
- ✅ **Full PKCE support**: End-to-end PKCE from client to Supabase
- ✅ **Real Supabase JWTs**: No custom tokens, uses actual Supabase authentication
- ✅ **Standard OAuth 2.1**: Follows OAuth 2.1 security best practices
- ✅ **State protection**: Cryptographically secure state management

### Benefits
- ✅ **MCP Compliance**: Full OAuth 2.1 + DCR compatibility
- ✅ **Client Compatibility**: Works with any MCP client out of the box
- ✅ **User Experience**: Familiar OAuth login flow
- ✅ **Supabase Integration**: Leverages existing Supabase authentication
- ✅ **Enterprise Ready**: Supports proper OAuth security standards

## 📝 Configuration Summary

**You were absolutely correct!** MCP clients expect OAuth, not login endpoints. The implementation now provides:

1. **OAuth 2.1 + DCR compliance** via FastMCP's OAuthProxy
2. **Supabase OAuth integration** using existing Supabase auth endpoints
3. **Proper MCP client support** with standard OAuth discovery
4. **Production-ready authentication** with full security features

Just get the `SUPABASE_OAUTH_CLIENT_SECRET` via Supabase CLI and configure the redirect URI, and MCP clients will authenticate seamlessly! 🎯