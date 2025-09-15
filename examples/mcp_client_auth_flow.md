# MCP Client Authentication Flow

## 🎯 The Real MCP Authentication Process

When MCP clients (like Claude Code, MCP Inspector, etc.) connect to your FastMCP server, here's what **actually** happens:

### 1. Client Connection
```
MCP Client → FastMCP Server (HTTP/STDIO)
Server: "Authentication required"
Client: Shows "Authenticate" button to user
```

### 2. User Clicks "Authenticate"
```
User clicks button → Client needs to get a token
```

**❌ Problem with Bearer-only auth**: No way for client to get a token!
**✅ Solution**: Provide `/auth/login` endpoint

### 3. Login Flow (Simple Auth Mode)
```
MCP Client → POST /auth/login
{
  "email": "user@example.com",
  "password": "password"
}

FastMCP Server → Supabase Auth API
Server validates credentials

Server → Client
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "message": "Login successful"
}
```

### 4. Authenticated Tool Calls
```
MCP Client → FastMCP Server
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...

{
  "tool": "entity_tool",
  "arguments": {
    "auth_token": "eyJhbGciOiJIUzI1NiIs...",
    "operation": "list",
    "entity_type": "project"
  }
}
```

## 🔧 Implementation Details

### Server Setup (Simple Auth Mode)

```bash
# Default: Simple auth with login endpoint
ATOMS_FASTMCP_AUTH_MODE=simple
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key

# Start server
python -m atoms_fastmcp.new_server
```

### Available Endpoints

1. **POST /auth/login** - MCP client authentication
   ```json
   Request:
   {
     "email": "user@example.com",
     "password": "password"
   }
   
   Response:
   {
     "access_token": "jwt_token",
     "token_type": "bearer", 
     "message": "Login successful"
   }
   ```

2. **GET /auth/status** - Check authentication status
   ```
   Headers: Authorization: Bearer <token>
   
   Response:
   {
     "authenticated": true,
     "user": {
       "id": "user-uuid",
       "email": "user@example.com"
     }
   }
   ```

3. **MCP Tool Endpoints** - Protected tool calls
   ```
   POST /api/mcp/tools/call
   Headers: Authorization: Bearer <token>
   ```

## 🔀 Authentication Modes Comparison

### Simple Auth (Recommended for MCP)
- ✅ **MCP Client Compatible**: Provides `/auth/login` endpoint
- ✅ **User Experience**: One-click authentication in MCP clients
- ✅ **Supabase Integration**: Uses Supabase auth API directly
- ✅ **Security**: Returns actual Supabase JWTs
- 🟡 **Setup**: Requires username/password credentials

### Bearer Auth (For Existing Tokens)
- ❌ **MCP Client Issue**: No way for client to obtain token
- ✅ **Frontend Integration**: Perfect for web apps with existing auth
- ✅ **Security**: Validates tokens via Supabase
- 🟢 **Setup**: No additional endpoints needed

### JWT Auth (Alternative)
- ❌ **MCP Client Issue**: No way for client to obtain token
- ✅ **Performance**: Validates JWTs locally via JWKS
- ✅ **Offline**: Works without calling Supabase for each request
- 🟢 **Setup**: No additional endpoints needed

## 🚀 MCP Client Examples

### Claude Code Integration
```
1. User configures Claude Code with server URL
2. Claude Code connects, sees authentication required
3. User clicks "Authenticate" in Claude Code
4. Claude Code prompts for email/password
5. Claude Code calls /auth/login endpoint
6. Claude Code stores returned JWT
7. All subsequent tool calls include JWT
```

### MCP Inspector Integration
```
1. Load server in MCP Inspector
2. Inspector shows "Authenticate" button
3. User clicks, enters credentials
4. Inspector calls /auth/login
5. Inspector now shows authenticated status
6. User can call tools normally
```

### Custom MCP Client
```javascript
class MCPClient {
  async authenticate(email, password) {
    const response = await fetch(`${this.serverUrl}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    })
    
    if (response.ok) {
      const { access_token } = await response.json()
      this.authToken = access_token
      return true
    }
    return false
  }
  
  async callTool(tool, arguments) {
    return fetch(`${this.serverUrl}/api/mcp/tools/call`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ tool, arguments: { 
        auth_token: this.authToken,
        ...arguments 
      }})
    })
  }
}
```

## 🔐 Security Considerations

1. **Supabase Integration**: All authentication goes through Supabase
2. **JWT Tokens**: Returns real Supabase JWTs (not custom tokens)
3. **Token Validation**: Each request validates token with Supabase
4. **User Context**: Tools receive full user information
5. **Session Management**: Tokens expire per Supabase settings

## 🔄 Relationship to Frontend Auth

**Frontend Auth** (your web app):
- User logs in via Supabase in browser
- Frontend gets JWT from session
- Frontend calls your API directly

**MCP Client Auth** (Claude Code, etc.):
- MCP client calls `/auth/login` endpoint
- Gets same Supabase JWT
- Calls MCP tools with JWT
- **Completely separate** from frontend auth

Both approaches end up with the same Supabase JWT, but the acquisition method is different based on the client type.