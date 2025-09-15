# Complete Login Flow Example

## Frontend Code (React/Next.js)

```javascript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
)

export default function LoginExample() {
  const [user, setUser] = useState(null)
  const [jwtToken, setJwtToken] = useState(null)

  // Handle login
  const handleLogin = async (email, password) => {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password
    })
    
    if (data.session) {
      setUser(data.user)
      setJwtToken(data.session.access_token)
      console.log('Login successful, JWT:', data.session.access_token)
    }
  }

  // Call MCP tool with JWT
  const callMCPTool = async () => {
    if (!jwtToken) {
      alert('Please login first')
      return
    }

    try {
      const response = await fetch('/api/mcp-proxy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tool: 'entity_tool',
          arguments: {
            auth_token: jwtToken,
            operation: 'list',
            entity_type: 'project'
          }
        })
      })
      
      const result = await response.json()
      console.log('MCP Result:', result)
    } catch (error) {
      console.error('MCP Error:', error)
    }
  }

  return (
    <div>
      {!user ? (
        <LoginForm onLogin={handleLogin} />
      ) : (
        <div>
          <p>Welcome, {user.email}!</p>
          <button onClick={callMCPTool}>
            Call MCP Tool
          </button>
        </div>
      )}
    </div>
  )
}
```

## Backend API Route (Next.js API route)

```javascript
// pages/api/mcp-proxy.js
export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' })
  }

  try {
    // Forward request to FastMCP server
    const mcpResponse = await fetch('http://localhost:8000/api/mcp/tools/call', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // JWT is passed through in the tool arguments
      },
      body: JSON.stringify(req.body)
    })

    const result = await mcpResponse.json()
    res.status(200).json(result)
  } catch (error) {
    res.status(500).json({ error: 'MCP request failed' })
  }
}
```

## Direct HTTP Call (if not using proxy)

```javascript
// Direct call to FastMCP server
const callMCPDirectly = async (jwtToken) => {
  const response = await fetch('http://localhost:8000/api/mcp/tools/call', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${jwtToken}`,  // JWT in Authorization header
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      tool: 'entity_tool',
      arguments: {
        auth_token: jwtToken,  // AND in tool arguments
        operation: 'list',
        entity_type: 'project'
      }
    })
  })
  
  return await response.json()
}
```

## Key Points

1. **No Login Endpoints**: FastMCP server has no `/login` or `/auth` endpoints
2. **Frontend-Only Auth**: All authentication happens in your existing frontend
3. **JWT Passing**: JWT is extracted from Supabase session and passed to MCP tools
4. **Server Validation**: FastMCP validates JWT by calling Supabase's `/auth/v1/user`
5. **User Context**: Server gets full user info (ID, email, metadata) for each request

## Error Handling

```javascript
const handleMCPCall = async () => {
  try {
    const result = await callMCPTool(jwtToken)
    
    if (result.error) {
      // Handle MCP-specific errors
      if (result.error.includes('Invalid or expired token')) {
        // Token expired, refresh session
        const { data } = await supabase.auth.refreshSession()
        if (data.session) {
          setJwtToken(data.session.access_token)
          // Retry the call
        } else {
          // Force re-login
          await supabase.auth.signOut()
          setUser(null)
          setJwtToken(null)
        }
      }
    }
  } catch (error) {
    console.error('Network or server error:', error)
  }
}
```

## Session Management

```javascript
// Listen for auth state changes
useEffect(() => {
  const { data: { subscription } } = supabase.auth.onAuthStateChange(
    (event, session) => {
      if (event === 'SIGNED_IN' && session) {
        setUser(session.user)
        setJwtToken(session.access_token)
      } else if (event === 'SIGNED_OUT') {
        setUser(null)
        setJwtToken(null)
      } else if (event === 'TOKEN_REFRESHED' && session) {
        setJwtToken(session.access_token)
      }
    }
  )

  return () => subscription.unsubscribe()
}, [])
```