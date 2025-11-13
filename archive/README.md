Atoms FastMCP Server (Python)

## Overview
- FastMCP 2.12 server with 1:1 coverage of the core atoms API domains, plus Supabase wiring.
- Auth is explicit: login(username, password) returns a session_token; all other tools require session_token.
- Transports: STDIO (default) or HTTP. HTTP path defaults to `/api/mcp`.
- **OAuth 2.0 PKCE + DCR** support via WorkOS AuthKit for production deployments.

## 🚨 Troubleshooting

**Having CORS or OAuth issues?**

### 🆕 **UPDATED**: Based on Official WorkOS MCP Documentation

**Read first**: [`docs/UPDATED_GUIDANCE.md`](docs/UPDATED_GUIDANCE.md) - Key updates based on official WorkOS docs

**Important changes**:
- ✅ Use `/.well-known/oauth-authorization-server` (not `openid-configuration`) for MCP
- ✅ Dynamic Client Registration (DCR) is **required** for MCP
- ✅ Test with OAuth 2.0 endpoints, not OpenID Connect

### 📖 Complete Documentation: [`docs/INDEX.md`](docs/INDEX.md)

Complete documentation index with guides organized by:
- Error message
- Use case
- Task type
- Reading order

### 🚀 Quick Links

- **Quick Fix (5 min)**: [`docs/QUICK_FIX.md`](docs/QUICK_FIX.md) - Fix the most common issues
- **Error Analysis**: [`docs/ERROR_ANALYSIS.md`](docs/ERROR_ANALYSIS.md) - Detailed breakdown of your errors
- **Summary**: [`docs/SUMMARY.md`](docs/SUMMARY.md) - What's fixed and what needs fixing
- **Verification**: [`docs/VERIFICATION_CHECKLIST.md`](docs/VERIFICATION_CHECKLIST.md) - Step-by-step testing

### ⚡ Common Errors

| Error | Status | Fix |
|-------|--------|-----|
| `404 on /.well-known/openid-configuration` | ❌ Needs fix | Update AuthKit domain in `.env` |
| `Cannot transition from step: client_registration` | ❌ Needs fix | Enable DCR in WorkOS Dashboard |
| `No 'Access-Control-Allow-Origin' header` | ✅ Fixed | Restart server |
| `mcp-protocol-version is not allowed` | ✅ Fixed | Restart server |

**See [`docs/INDEX.md`](docs/INDEX.md) for complete documentation.**

## Install
- Python 3.10+
- Dependencies are listed at the repo root in `requirements.txt`:
  - fastmcp>=2.12
  - supabase>=2.5.0

## Run
- STDIO (default):
  `python -m atoms_fastmcp`

- HTTP transport:
  `ATOMS_FASTMCP_TRANSPORT=http ATOMS_FASTMCP_HOST=127.0.0.1 ATOMS_FASTMCP_PORT=3001 python -m atoms_fastmcp`
  - HTTP MCP endpoint path: `/api/mcp` (override with `ATOMS_FASTMCP_HTTP_PATH`)
  - Health check: `GET /health`

## Auth and Env

### Required for Supabase
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`

### Optional Development Auth
- `FASTMCP_DEMO_USER`, `FASTMCP_DEMO_PASS` (if set, login must match these)

### Required for OAuth (Production)
- `FASTMCP_SERVER_AUTH=fastmcp.server.auth.providers.workos.AuthKitProvider`
- `FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN` - Your AuthKit domain from WorkOS
- `FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL` - Your public server URL
- `FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_REQUIRED_SCOPES=openid,profile,email`
- `WORKOS_API_KEY` - Your WorkOS API key
- `WORKOS_CLIENT_ID` - Your WorkOS client ID

**⚠️ Important**: Make sure your `AUTHKIT_DOMAIN` is correct! Test it:
```bash
curl https://YOUR-AUTHKIT-DOMAIN/.well-known/openid-configuration
# Should return JSON, not 404
```

Key Domains/Tools (non‑exhaustive)
- auth: login, logout, get_profile, auth_get_by_email, auth_update_profile, auth_list_profiles, auth_set_approval
- organizations: list/get/bySlug/listForUser/listIdsByMembership/listWithFilters/getPersonalOrg/create/listMembers/removeMember/invite/addMember/setMemberRole/updateMemberCount
- projects: getById/listForUser/listMembers/listByOrg/listByMembershipForOrg/listWithFilters/create/update/softDelete/addMember/setMemberRole/removeMember
- documents: create/getById/listByProject/listWithFilters/update/softDelete/blocksAndRequirements/getBlockById/listBlocks/listColumnsByBlockIds/createBlock/updateBlock/softDeleteBlock/createColumn/deleteColumn
- requirements: getById/listWithFilters/listByProject/listByDocument/listByBlock/listByBlockIds/listByIds/create/update/softDelete
- properties: getById/listByOrg/listByDocument/listOrgBase/createMany/update/softDelete/updatePositions
- trace_links: create/createMany/softDelete/listBySource/listByTarget
- test_matrix_views: listByProject/insert/update/softDelete/getById/getDefault/getFirstActive/unsetDefaults
- assignments, audit_logs, notifications (including unreadCount), recent (documents/projects/requirements)
- diagrams: list/getById/updateName/delete/upsert
- storage: get_public_url
- external_documents: get_by_id/list_by_org/upload_base64/remove/update/get_public_url (uses Supabase storage `external_documents` bucket)

## 📚 Documentation Index

### Quick Start
- **[README.md](README.md)** - This file, overview and basic setup
- **[QUICK_FIX.md](docs/QUICK_FIX.md)** - 5-minute fix for common issues

### Troubleshooting Guides
- **[ERROR_ANALYSIS.md](docs/ERROR_ANALYSIS.md)** - Analysis of your current errors
- **[CORS_TROUBLESHOOTING.md](docs/CORS_TROUBLESHOOTING.md)** - Deep dive into CORS issues
- **[VERIFICATION_CHECKLIST.md](docs/VERIFICATION_CHECKLIST.md)** - Step-by-step verification

### Setup Guides
- **[authkit_setup_guide.md](docs/authkit_setup_guide.md)** - Complete OAuth setup with AuthKit
- **[oauth_setup_guide.md](docs/oauth_setup_guide.md)** - OAuth 2.0 PKCE + DCR guide
- **[supabase_workos_setup_guide.md](docs/supabase_workos_setup_guide.md)** - Supabase + WorkOS integration

### Examples
- **[login_flow.md](examples/login_flow.md)** - Basic login flow examples
- **[mcp_client_auth_flow.md](examples/mcp_client_auth_flow.md)** - MCP client authentication
- **[mcp_oauth_dcr_flow.md](examples/mcp_oauth_dcr_flow.md)** - OAuth DCR flow examples

## Notes
- Session storage is in-memory for dev; replace with your preferred auth/session backend if needed.
- No external ASGI server required; FastMCP runs HTTP internally.
- Tool names are snake_case. If you prefer names that mirror atoms-api exactly (e.g., `organizations.getById`), these can be aliased/renamed.
- **CORS fixes are already in the code** - just restart the server to apply them.
- **The main blocker is the AuthKit domain** - make sure it's correct in your `.env` file.
