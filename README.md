Atoms FastMCP Server (Python)

Overview
- FastMCP 2.12 server with 1:1 coverage of the core atoms API domains, plus Supabase wiring.
- Auth is explicit: login(username, password) returns a session_token; all other tools require session_token.
- Transports: STDIO (default) or HTTP. HTTP path defaults to `/api/mcp`.

Install
- Python 3.10+
- Dependencies are listed at the repo root in `requirements.txt`:
  - fastmcp>=2.12
  - supabase>=2.5.0

Run
- STDIO (default):
  `python -m atoms_fastmcp`

- HTTP transport:
  `ATOMS_FASTMCP_TRANSPORT=http ATOMS_FASTMCP_HOST=127.0.0.1 ATOMS_FASTMCP_PORT=3001 python -m atoms_fastmcp`
  - HTTP MCP endpoint path: `/api/mcp` (override with `ATOMS_FASTMCP_HTTP_PATH`)
  - Health check: `GET /health`

Auth and Env
- Required for real data access via Supabase:
  - `NEXT_PUBLIC_SUPABASE_URL`
  - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- Optional local/demo auth gate:
  - `FASTMCP_DEMO_USER`, `FASTMCP_DEMO_PASS` (if set, login must match these)

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

Notes
- Session storage is in-memory for dev; replace with your preferred auth/session backend if needed.
- No external ASGI server required; FastMCP runs HTTP internally.
- Tool names are snake_case. If you prefer names that mirror atoms-api exactly (e.g., `organizations.getById`), these can be aliased/renamed.
