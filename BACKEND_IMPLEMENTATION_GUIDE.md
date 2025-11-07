# Backend Implementation Guide (atomsAgent)

## Location
`/Users/kooshapari/temp-PRODVERCEL/485/kush/agentapi/atomsAgent`

## Changes Required

### 1. Update `src/atomsAgent/mcp/database.py`

#### Change 1: Update function signature (line ~202)

Find this function and add `user_token` parameter:

```python
def convert_db_server_to_mcp_config(
    server: dict[str, Any], 
    *, 
    oauth_token: str | None = None,
    user_token: str | None = None  # ADD THIS
) -> dict[str, Any]:
    """
    Convert database MCP server record to MCP server configuration format.

    Args:
        server: Database record from mcp_servers table
        oauth_token: Optional OAuth token to use for authentication
        user_token: Optional user token (AuthKit JWT) for internal MCPs  # ADD THIS

    Returns:
        MCP server configuration dict compatible with Claude Agent SDK
    """
```

#### Change 2: Add internal MCP handling (line ~250, BEFORE auth_type check)

Add this code RIGHT AFTER `config = {"url": server_url}` and BEFORE `auth_type = server.get("auth_type")`:

```python
        config = {
            "url": server_url,
        }

        # ADD THIS BLOCK START
        # Check if this is an internal MCP (Atoms)
        is_internal = server.get("is_internal", False)
        server_name = server.get("name", "")
        
        # Auto-detect Atoms MCP as internal
        if "atoms-mcp" in server_name.lower() or "atoms_mcp" in server_name.lower():
            is_internal = True
        
        # If internal MCP and user token provided, use it
        if is_internal and user_token:
            logger.info(f"Using user AuthKit JWT for internal MCP: {server_name}")
            config["headers"] = {
                "Authorization": f"Bearer {user_token}"
            }
            return config
        # ADD THIS BLOCK END

        # Add authentication from auth_config
        auth_type = server.get("auth_type")
        auth_config = server.get("auth_config") or {}
```

---

### 2. Find and Update Chat Endpoint

Look for your chat endpoint in `src/atomsAgent/api/` directory:

```bash
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/agentapi/atomsAgent
find src/atomsAgent/api -name "*.py" -exec grep -l "def chat\|@router.post.*chat" {} \;
```

#### Add Authorization header extraction

```python
from fastapi import Header
from typing import Optional

@router.post("/chat")  # or whatever your route is
async def chat(
    request: Request,
    authorization: Optional[str] = Header(None)  # ADD THIS
):
    body = await request.json()
    
    # ADD THIS BLOCK
    # Extract user token from Authorization header
    user_token = None
    if authorization and authorization.startswith("Bearer "):
        user_token = authorization.replace("Bearer ", "").strip()
        logger.info(f"Received AuthKit JWT for MCP request")
    # END BLOCK
    
    # ... rest of your function
```

#### Pass user_token when calling convert_db_server_to_mcp_config

Find where you call `convert_db_server_to_mcp_config` and add `user_token`:

```python
# BEFORE:
mcp_config = convert_db_server_to_mcp_config(server, oauth_token=oauth_token)

# AFTER:
mcp_config = convert_db_server_to_mcp_config(
    server, 
    oauth_token=oauth_token,
    user_token=user_token  # ADD THIS
)
```

---

### 3. Add Atoms MCP to Database

Connect to your Supabase database and run:

```sql
-- Add production Atoms MCP
INSERT INTO mcp_servers (
    name,
    url,
    transport_type,
    scope,
    is_internal,
    enabled
) VALUES (
    'atoms-mcp',
    'https://mcp.atoms.tech/api/mcp',
    'http',
    'system',
    true,
    true
) ON CONFLICT (name) DO UPDATE SET
    is_internal = true,
    url = 'https://mcp.atoms.tech/api/mcp',
    enabled = true;

-- Add dev Atoms MCP (optional)
INSERT INTO mcp_servers (
    name,
    url,
    transport_type,
    scope,
    is_internal,
    enabled
) VALUES (
    'atoms-mcp-dev',
    'https://mcpdev.atoms.tech/api/mcp',
    'http',
    'system',
    true,
    true
) ON CONFLICT (name) DO UPDATE SET
    is_internal = true,
    url = 'https://mcpdev.atoms.tech/api/mcp',
    enabled = true;
```

---

## Step-by-Step Implementation

### Step 1: Edit database.py

```bash
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/agentapi/atomsAgent
code src/atomsAgent/mcp/database.py  # or your editor
```

Make the two changes described above.

### Step 2: Find and edit chat endpoint

```bash
# Find the chat endpoint file
find src/atomsAgent/api -name "*.py" -exec grep -l "def chat" {} \;

# Edit it
code <filename>
```

Make the changes described above.

### Step 3: Test locally

```bash
# Test import
python -c "from atomsAgent.mcp.database import convert_db_server_to_mcp_config; print('✅ Import successful')"

# Run server
python -m atomsAgent.main  # or however you start it
```

### Step 4: Add to database

Use Supabase dashboard or psql to run the SQL above.

### Step 5: Test end-to-end

```bash
# Send test request with Authorization header
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-token" \
  -d '{"message": "test", "mcpId": "atoms"}'
```

Check logs for: "Using user AuthKit JWT for internal MCP: atoms-mcp"

---

## Verification Checklist

- [ ] `database.py` has `user_token` parameter
- [ ] `database.py` has internal MCP detection logic
- [ ] Chat endpoint extracts Authorization header
- [ ] Chat endpoint passes `user_token` to convert function
- [ ] Atoms MCP added to database with `is_internal=true`
- [ ] Local testing passes
- [ ] Logs show "Using user AuthKit JWT for internal MCP"

---

## Next: Frontend Implementation

After backend is complete, move to frontend (atoms.tech) implementation.

