# AuthKit & FastMCP Integration

Secure your FastMCP server with WorkOS AuthKit while continuing to reuse AuthKit-issued JWTs for Supabase. Beginning with version 2.11.0, the FastMCP server ships with first-class support for WorkOS's remote OAuth pattern, allowing AuthKit to handle all user logins while the server validates the tokens it receives.

Standalone Connect is no longer required—the AuthKit provider now performs remote OAuth completion directly and keeps the Supabase flow unchanged.

The FastMCP side remains stateless: tokens are verified per request and Supabase-compatible JWTs are exposed through the standard FastMCP dependency (`get_access_token`).

## Configuration

### Prerequisites

1. A [WorkOS account](https://workos.com/) with an active project.
2. An [AuthKit](https://www.authkit.com/) instance configured in that project.
3. The base URL for your FastMCP server (for local development you can use `http://localhost:8000`).

### Step 1: Configure AuthKit

In the WorkOS Dashboard:

1. Go to **Applications → Configuration** and enable **Dynamic Client Registration**. This allows FastMCP clients to register automatically.
2. Note your **AuthKit domain**. It will look like `https://your-project-12345.authkit.app`; you will need it for both FastMCP and Supabase configuration.

![Enable Dynamic Client Registration](https://mintcdn.com/fastmcp/hUosZw7ujHZFemrG/integrations/images/authkit/enable_dcr.png?fit=max&auto=format&n=hUosZw7ujHZFemrG&q=85&s=5849352618ef89da08cf452c5dcf38a8)

### Step 2: Configure FastMCP

Create (or update) your FastMCP server to use the bundled `AuthKitProvider`. The provider discovers the WorkOS endpoints, validates JWTs, and exposes the `/auth/complete` hook required for remote OAuth.

```python
from fastmcp import FastMCP
from fastmcp.server.auth.providers.workos import AuthKitProvider

# AuthKitProvider performs remote OAuth completion and leaves the AuthKit JWT
# available for Supabase third-party authentication.
auth_provider = AuthKitProvider(
    authkit_domain="https://your-project-12345.authkit.app",
    base_url="http://localhost:8000"  # Replace with your FastMCP server URL
)

mcp = FastMCP(name="AuthKit Secured App", auth=auth_provider)
```

### Step 3: Validate the Flow

Run the server locally with the FastMCP CLI:

```bash
fastmcp run server.py --transport http --port 8000
```

Then confirm the OAuth handshake succeeds:

```python
from fastmcp import Client
import asyncio


async def main():
    async with Client("http://localhost:8000/mcp/", auth="oauth") as client:
        assert await client.ping()


if __name__ == "__main__":
    asyncio.run(main())
```

## Environment Variables

Starting in version 2.12.1 you can configure the provider entirely via environment variables instead of instantiating it in code.

### Provider Selection

Set `FASTMCP_SERVER_AUTH=fastmcp.server.auth.providers.workos.AuthKitProvider` to enable AuthKit automatically.

### AuthKit-Specific Settings

Configure the following environment variables for both manual and automatic provider setup:

- `FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN` (required): your AuthKit domain, e.g. `https://your-project-12345.authkit.app`.
- `FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL` (required): the public URL of your FastMCP server, such as `https://your-server.com` or `http://localhost:8000`.
- `FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_REQUIRED_SCOPES` (optional): comma-, space-, or JSON-separated scopes, for example `openid profile email` or `["openid", "profile", "email"]`.

Example `.env` snippet:

```bash
# Enable AuthKit authentication
FASTMCP_SERVER_AUTH=fastmcp.server.auth.providers.workos.AuthKitProvider

# AuthKit configuration
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN=https://your-project-12345.authkit.app
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL=https://your-server.com
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_REQUIRED_SCOPES=openid,profile,email
```

With these variables set your server code can simply rely on FastMCP to load the provider:

```python
from fastmcp import FastMCP


mcp = FastMCP(name="AuthKit Secured App")
```

This configuration keeps Supabase compatibility intact—the AuthKit JWT received from remote OAuth continues to be trusted by Supabase's third-party auth flow without any additional changes.

## Supabase Client Integration

To call Supabase directly from your application, initialize both the AuthKit
client and the Supabase client with the same access token. Supabase accepts the
AuthKit-issued JWT without any extra setup:

```javascript
import { createClient } from '@supabase/supabase-js';
import { createClient as createAuthKitClient } from '@workos-inc/authkit-js';

const authkit = await createAuthKitClient('<WORKOS_CLIENT_ID>', {
  apiHostname: '<WORKOS_AUTH_DOMAIN>',
});

const supabase = createClient(
  'https://<supabase-project>.supabase.co',
  '<SUPABASE_ANON_KEY>',
  {
    accessToken: async () => {
      return authkit.getAccessToken();
    },
  },
);
```

That's all that is required—Supabase trusts the AuthKit access token for
authenticated requests.
