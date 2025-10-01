# Atoms MCP Server - Troubleshooting Documentation

## 🎯 Quick Navigation

### 🚨 I Have an Error Right Now!

**Start here**: [`QUICK_FIX.md`](QUICK_FIX.md) - 5-minute fix for common issues

### 📊 I Want to Understand What's Wrong

**Start here**: [`ERROR_ANALYSIS.md`](ERROR_ANALYSIS.md) - Detailed breakdown of your errors

### ✅ I Want to Verify My Setup

**Start here**: [`VERIFICATION_CHECKLIST.md`](VERIFICATION_CHECKLIST.md) - Step-by-step testing

### 📚 I Want Complete Documentation

**Start here**: [`INDEX.md`](INDEX.md) - Complete documentation index

---

## 🔥 Most Common Issues

### Issue 1: AuthKit Domain Returns 404 ❌

**Error**: `https://authkit-01k4cgw2j1fgwzyzjdmvwgqzbd.authkit.app/.well-known/openid-configuration` returns 404

**Fix**: 
1. Find your actual AuthKit domain in WorkOS Dashboard
2. Test it: `curl https://YOUR-DOMAIN/.well-known/openid-configuration`
3. Update `.env` with correct domain
4. Restart server

**Time**: 5 minutes

**See**: [`QUICK_FIX.md`](QUICK_FIX.md) - Step 1

---

### Issue 2: CORS Headers Missing ✅

**Error**: `No 'Access-Control-Allow-Origin' header is present`

**Status**: **ALREADY FIXED** in code!

**Fix**: Just restart the server

**Time**: 1 minute

**See**: [`QUICK_FIX.md`](QUICK_FIX.md) - Step 3

---

### Issue 3: Client Registration Fails ❌

**Error**: `Cannot transition from step: client_registration`

**Fix**:
1. Go to WorkOS Dashboard
2. Enable Dynamic Client Registration
3. Add redirect URIs
4. Save

**Time**: 2 minutes

**See**: [`QUICK_FIX.md`](QUICK_FIX.md) - Step 2

---

## 📖 Documentation Overview

### Quick Reference (5-10 minutes)

| Document | Purpose | When to Use |
|----------|---------|-------------|
| [`SUMMARY.md`](SUMMARY.md) | Overview of fixes | Start here for context |
| [`QUICK_FIX.md`](QUICK_FIX.md) | Fast fixes | You have errors now |
| [`ERROR_ANALYSIS.md`](ERROR_ANALYSIS.md) | Error breakdown | Understand specific errors |

### Detailed Guides (15-30 minutes)

| Document | Purpose | When to Use |
|----------|---------|-------------|
| [`CORS_TROUBLESHOOTING.md`](CORS_TROUBLESHOOTING.md) | CORS deep dive | CORS issues persist |
| [`authkit_setup_guide.md`](authkit_setup_guide.md) | Complete OAuth setup | Setting up from scratch |
| [`OAUTH_FLOW_DIAGRAM.md`](OAUTH_FLOW_DIAGRAM.md) | Visual OAuth flow | Understand the process |

### Verification (10-20 minutes)

| Document | Purpose | When to Use |
|----------|---------|-------------|
| [`VERIFICATION_CHECKLIST.md`](VERIFICATION_CHECKLIST.md) | Step-by-step tests | Verify your setup |

### Reference

| Document | Purpose | When to Use |
|----------|---------|-------------|
| [`INDEX.md`](INDEX.md) | Complete index | Find specific info |
| [`oauth_setup_guide.md`](oauth_setup_guide.md) | OAuth 2.0 guide | OAuth reference |
| [`supabase_workos_setup_guide.md`](supabase_workos_setup_guide.md) | Integration guide | Supabase + WorkOS |

---

## 🎯 Recommended Reading Order

### Path 1: Quick Fix (15 minutes)

Perfect if you just want to fix the errors and move on.

1. ✅ [`SUMMARY.md`](SUMMARY.md) - 2 min - Understand what's wrong
2. ✅ [`QUICK_FIX.md`](QUICK_FIX.md) - 8 min - Follow the fixes
3. ✅ [`VERIFICATION_CHECKLIST.md`](VERIFICATION_CHECKLIST.md) - 5 min - Verify it works

**Success rate**: 90% if you follow all steps

---

### Path 2: Deep Understanding (1 hour)

Perfect if you want to understand OAuth and CORS thoroughly.

1. ✅ [`SUMMARY.md`](SUMMARY.md) - 2 min
2. ✅ [`ERROR_ANALYSIS.md`](ERROR_ANALYSIS.md) - 10 min
3. ✅ [`OAUTH_FLOW_DIAGRAM.md`](OAUTH_FLOW_DIAGRAM.md) - 10 min
4. ✅ [`CORS_TROUBLESHOOTING.md`](CORS_TROUBLESHOOTING.md) - 15 min
5. ✅ [`authkit_setup_guide.md`](authkit_setup_guide.md) - 20 min
6. ✅ [`VERIFICATION_CHECKLIST.md`](VERIFICATION_CHECKLIST.md) - 10 min

**Outcome**: Complete understanding of the system

---

### Path 3: Complete Setup (2 hours)

Perfect if you're setting up from scratch or want to rebuild.

1. ✅ [`authkit_setup_guide.md`](authkit_setup_guide.md) - 30 min
2. ✅ [`oauth_setup_guide.md`](oauth_setup_guide.md) - 20 min
3. ✅ [`supabase_workos_setup_guide.md`](supabase_workos_setup_guide.md) - 20 min
4. ✅ [`CORS_TROUBLESHOOTING.md`](CORS_TROUBLESHOOTING.md) - 15 min
5. ✅ [`VERIFICATION_CHECKLIST.md`](VERIFICATION_CHECKLIST.md) - 20 min
6. ✅ [`../examples/mcp_oauth_dcr_flow.md`](../examples/mcp_oauth_dcr_flow.md) - 15 min

**Outcome**: Production-ready setup

---

## 🔍 Find Documentation by Error

| Error Message | Document | Section |
|---------------|----------|---------|
| `No 'Access-Control-Allow-Origin' header` | [`ERROR_ANALYSIS.md`](ERROR_ANALYSIS.md) | Error 1 |
| `mcp-protocol-version is not allowed` | [`ERROR_ANALYSIS.md`](ERROR_ANALYSIS.md) | Error 2 |
| `404 on /.well-known/openid-configuration` | [`ERROR_ANALYSIS.md`](ERROR_ANALYSIS.md) | Error 3 |
| `Cannot transition from step: client_registration` | [`ERROR_ANALYSIS.md`](ERROR_ANALYSIS.md) | Error 4 |
| `Redirect is not allowed for a preflight request` | [`ERROR_ANALYSIS.md`](ERROR_ANALYSIS.md) | Error 5 |
| `The response redirected too many times` | [`ERROR_ANALYSIS.md`](ERROR_ANALYSIS.md) | Error 6 |

---

## 🛠️ Find Documentation by Task

| Task | Document | Time |
|------|----------|------|
| Fix AuthKit domain | [`QUICK_FIX.md`](QUICK_FIX.md) - Step 1 | 5 min |
| Enable DCR | [`QUICK_FIX.md`](QUICK_FIX.md) - Step 2 | 2 min |
| Restart server | [`QUICK_FIX.md`](QUICK_FIX.md) - Step 3 | 1 min |
| Test AuthKit | [`VERIFICATION_CHECKLIST.md`](VERIFICATION_CHECKLIST.md) - Test 1 | 1 min |
| Test CORS | [`VERIFICATION_CHECKLIST.md`](VERIFICATION_CHECKLIST.md) - Test 3 | 1 min |
| Configure Cloudflare | [`CORS_TROUBLESHOOTING.md`](CORS_TROUBLESHOOTING.md) - Fix 3 | 10 min |
| Complete setup | [`authkit_setup_guide.md`](authkit_setup_guide.md) | 30 min |

---

## 📊 Status Summary

### ✅ Fixed (Restart Server)

- CORS headers missing
- `mcp-protocol-version` header not allowed
- OPTIONS request handling

**Action**: Just restart the server to apply these fixes.

### ❌ Needs Fix (Your Action Required)

- AuthKit domain returns 404
- Dynamic Client Registration not enabled
- Redirect URIs not configured

**Action**: Follow [`QUICK_FIX.md`](QUICK_FIX.md) Steps 1-2.

### ⚠️ Optional (May Need Fix)

- HTTP→HTTPS redirects
- Cloudflare SSL configuration

**Action**: Only if you see redirect errors. See [`CORS_TROUBLESHOOTING.md`](CORS_TROUBLESHOOTING.md).

---

## 🎉 Success Criteria

You'll know everything is working when:

- ✅ `curl https://YOUR-AUTHKIT-DOMAIN/.well-known/openid-configuration` returns JSON
- ✅ `curl https://atomcp.kooshapari.com/.well-known/oauth-protected-resource` returns JSON
- ✅ CORS headers present in OPTIONS responses
- ✅ DCR endpoint works
- ✅ Claude Desktop connects successfully
- ✅ No errors in browser console

**See [`VERIFICATION_CHECKLIST.md`](VERIFICATION_CHECKLIST.md) for complete verification.**

---

## 🆘 Getting Help

### Step 1: Identify Your Issue

Look at your error message in the browser console or server logs.

### Step 2: Find the Right Document

Use the "Find Documentation by Error" table above.

### Step 3: Follow the Fix

Each document has clear, step-by-step instructions.

### Step 4: Verify

Use [`VERIFICATION_CHECKLIST.md`](VERIFICATION_CHECKLIST.md) to confirm it worked.

### Step 5: Still Stuck?

1. Read [`ERROR_ANALYSIS.md`](ERROR_ANALYSIS.md) for detailed error breakdown
2. Check [`CORS_TROUBLESHOOTING.md`](CORS_TROUBLESHOOTING.md) for CORS issues
3. Review [`authkit_setup_guide.md`](authkit_setup_guide.md) for setup issues
4. Enable debug logging (see [`SUMMARY.md`](SUMMARY.md))

---

## 📚 Additional Resources

### External Documentation

- **WorkOS AuthKit**: https://workos.com/docs/authkit
- **FastMCP**: https://github.com/jlowin/fastmcp
- **OAuth 2.0**: https://oauth.net/2/
- **CORS**: https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS

### Examples

- [`../examples/login_flow.md`](../examples/login_flow.md) - Basic login examples
- [`../examples/mcp_client_auth_flow.md`](../examples/mcp_client_auth_flow.md) - MCP client auth
- [`../examples/mcp_oauth_dcr_flow.md`](../examples/mcp_oauth_dcr_flow.md) - OAuth DCR examples

---

## 🎯 Next Steps

1. **Read** [`SUMMARY.md`](SUMMARY.md) to understand what's fixed and what needs fixing
2. **Follow** [`QUICK_FIX.md`](QUICK_FIX.md) to fix the critical issues
3. **Verify** with [`VERIFICATION_CHECKLIST.md`](VERIFICATION_CHECKLIST.md)
4. **Test** with Claude Desktop

**Total time: ~25 minutes**

**Good luck! 🚀**

