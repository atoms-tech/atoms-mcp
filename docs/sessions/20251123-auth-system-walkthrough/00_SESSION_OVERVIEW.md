# Auth System Walkthrough: Secondary Token Verifier & Bearer Auth

## Session Goals

1. **Document your complete auth system architecture** - explain how tokens flow from frontend (AuthKit) → MCP server
2. **Support multiple auth methods** - WorkOS User Management, AuthKit OAuth, frontend forwarded tokens, and RemoteOAuth
3. **Implement comprehensive logging** - full debug trail for token verification and user context
4. **Guide frontend integration** - show how your Next.js + AuthKit + Supabase pattern works with the MCP server

## Key Decisions

- **Your frontend pattern**: Next.js uses AuthKit (WorkOS) for auth, retrieves tokens via `authkit.getAccessToken()`, forwards to Supabase with JWT context
- **Your atoms agent**: Similar pattern - receives user token from frontend, verifies it, passes to MCP tools
- **Your MCP server**: Must support:
  - AuthKit OAuth (full flow)
  - Bearer tokens from frontend/backend (JWT tokens)
  - WorkOS User Management tokens (from `authenticate_with_password`)
  - RemoteOAuth (for other OAuth providers)
  - Full debug logging throughout the chain

## Session Structure

- **01_RESEARCH.md** - Auth architecture, token flows, token types
- **02_SPECIFICATIONS.md** - Requirements, auth methods, logging spec
- **03_DAG_WBS.md** - Implementation breakdown by component
- **04_IMPLEMENTATION_STRATEGY.md** - Enhanced logging, token verification, frontend patterns
- **05_KNOWN_ISSUES.md** - Current gaps, workarounds, future work

## Success Criteria

- ✅ Clear documentation of token flow from frontend → MCP → database
- ✅ All 4 auth methods working with detailed logging
- ✅ Frontend integration guide (Next.js + AuthKit pattern shown)
- ✅ Debug logs answer: "What happened to my token?"

## Key References

- Frontend pattern: `import { getAccessToken } from '@workos-inc/authkit-nextjs'`
- Token flow: Frontend JWT → Bearer header → Hybrid auth provider → tools validation
- Logging: Every step from header parsing through RLS context setting
