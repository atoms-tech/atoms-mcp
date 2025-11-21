# WorkOS + Supabase Third-Party Auth Setup

This guide outlines the steps to use WorkOS (AuthKit) as a Supabase [third-party auth provider](https://supabase.com/docs/guides/auth/third-party/overview). This allows you to authenticate users with AuthKit and use AuthKit access tokens to access Supabase's REST and GraphQL APIs.

## Overview

With this setup:
- ✅ Users authenticate via WorkOS AuthKit (OAuth 2.0 PKCE)
- ✅ AuthKit JWTs work directly with Supabase (no token exchange needed)
- ✅ Supabase RLS policies use the `role` claim from AuthKit JWTs
- ✅ Single authentication flow for both AuthKit and Supabase

## (1) Add WorkOS Third-Party Auth Integration

Configure a WorkOS integration in the [Supabase dashboard](https://supabase.com/dashboard/project/_/auth/third-party).

1. Go to your Supabase project dashboard
2. Navigate to **Authentication** → **Providers** → **Third-party providers**
3. Click **Add provider** and select **WorkOS**
4. Enter your WorkOS issuer URL:

```txt
https://api.workos.com/user_management/client_<YOUR_CLIENT_ID>
```

Replace `<YOUR_CLIENT_ID>` with your actual WorkOS Client ID (e.g., `client_123456789`).

**Note**: The issuer URL format is:
```
https://api.workos.com/user_management/client_<CLIENT_ID>
```

## (2) Set Up JWT Template in WorkOS

Supabase RLS policies expect a `role` claim in the access token that corresponds to a database role. WorkOS already adds a `role` claim corresponding to the user's role in an organization.

Set up a JWT template in the WorkOS dashboard:

1. Go to [WorkOS Dashboard](https://dashboard.workos.com) → **Authentication** → **Sessions**
2. Navigate to **JWT Templates**
3. Create a new template or edit the default template
4. Add the following claims:

```json
{
  "sub": "{{user.id}}",
  "email": "{{user.email}}",
  "name": "{{user.first_name}} {{user.last_name}}",
  "email_verified": true,
  "role": "authenticated",
  "user_role": "{{organization_membership.role}}"
}
```

**Key points:**
- `role`: Set to `"authenticated"` for Supabase RLS (required)
- `user_role`: Preserves the user's organization role for application logic
- `sub`: User ID (required for Supabase `auth.uid()`)
- `email`: User email (required for user identification)

## (3) Environment Variables

Ensure these environment variables are set:

```bash
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# WorkOS/AuthKit Configuration
WORKOS_API_KEY=sk_test_...
WORKOS_CLIENT_ID=client_123456789
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN=https://authkit.workos.com
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL=https://your-app.com
```

## (4) How It Works

### Authentication Flow

1. **User authenticates via AuthKit OAuth**
   - User goes through OAuth flow with WorkOS AuthKit
   - WorkOS returns an access token (JWT) with the configured claims

2. **JWT is passed to Supabase**
   - The AuthKit JWT is passed as `Authorization: Bearer <token>` header
   - Supabase validates the JWT using the WorkOS issuer configured in step 1
   - Supabase extracts the `role` claim for RLS policies

3. **RLS Policies Work Automatically**
   - Supabase's `auth.uid()` function returns the `sub` claim from the JWT
   - Supabase's `auth.role()` function returns the `role` claim from the JWT
   - Your RLS policies can use these functions as normal

### Code Implementation

The codebase already handles this automatically:

```python
# In supabase_client.py
def get_supabase(access_token: Optional[str] = None) -> Client:
    """Get Supabase client with AuthKit JWT for RLS context."""
    client = create_client(url, key)
    
    # Set the AuthKit JWT for RLS context
    if access_token:
        client.postgrest.auth(access_token)  # Supabase validates and uses the JWT
    
    return client
```

The AuthKit JWT is automatically:
- ✅ Validated by Supabase using the WorkOS issuer
- ✅ Used for RLS context (`auth.uid()` and `auth.role()`)
- ✅ Cached per-token for performance

## (5) Testing the Setup

### Verify JWT Claims

Check that your AuthKit JWTs include the required claims:

```python
import jwt

token = "your_authkit_jwt_token"
decoded = jwt.decode(token, options={"verify_signature": False})

# Required claims
assert "sub" in decoded  # User ID
assert "role" in decoded  # Should be "authenticated"
assert decoded.get("role") == "authenticated"  # For Supabase RLS
```

### Test Supabase RLS

Create a test RLS policy:

```sql
-- Example: Users can only read their own data
CREATE POLICY "Users can read own data"
ON your_table
FOR SELECT
USING (auth.uid() = user_id);

-- Example: Only authenticated users can insert
CREATE POLICY "Authenticated users can insert"
ON your_table
FOR INSERT
WITH CHECK (auth.role() = 'authenticated');
```

### Verify in Application

```python
from supabase_client import get_supabase

# Get Supabase client with AuthKit JWT
supabase = get_supabase(access_token=authkit_jwt_token)

# Query should respect RLS policies
result = supabase.table("your_table").select("*").execute()
# Only returns data allowed by RLS policies
```

## Troubleshooting

### Issue: RLS policies not working

**Solution**: Verify the JWT includes the `role` claim:
```python
decoded = jwt.decode(token, options={"verify_signature": False})
print(decoded.get("role"))  # Should be "authenticated"
```

### Issue: `auth.uid()` returns null

**Solution**: Ensure the JWT includes the `sub` claim with the user ID:
```python
decoded = jwt.decode(token, options={"verify_signature": False})
print(decoded.get("sub"))  # Should be the user ID
```

### Issue: Supabase rejects the JWT

**Solution**: Verify:
1. WorkOS issuer URL is correctly configured in Supabase dashboard
2. JWT issuer matches: `https://api.workos.com/user_management/client_<CLIENT_ID>`
3. JWT is not expired

### Issue: Role claim not recognized

**Solution**: 
1. Check JWT template in WorkOS dashboard includes `role: "authenticated"`
2. Verify the claim is in the JWT payload (not just header)
3. Ensure Supabase third-party provider is properly configured

## Additional Resources

- [Supabase Third-Party Auth Docs](https://supabase.com/docs/guides/auth/third-party/overview)
- [WorkOS AuthKit Documentation](https://workos.com/docs/user-management)
- [Supabase RLS Policies](https://supabase.com/docs/guides/auth/row-level-security)
