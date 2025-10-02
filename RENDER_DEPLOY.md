# Deploy Atoms MCP Server to Render

This guide will help you deploy the Atoms MCP server to Render's free tier.

## Why Render?

✅ **Persistent server** - In-memory OAuth sessions work perfectly
✅ **No cold starts** - Always-on process
✅ **Simple deployment** - Git push to deploy
✅ **Free tier** - 750 hours/month (enough for 24/7 with sleep)
✅ **Full logs** - Easy debugging

## Prerequisites

1. **GitHub account** - Your code needs to be in a Git repository
2. **Render account** - Sign up at https://render.com (free)
3. **Environment variables** - Get these from your existing deployment

## Step 1: Push Code to GitHub

```bash
# If not already in a Git repo
git init
git add .
git commit -m "Prepare for Render deployment"

# Create repo on GitHub and push
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

## Step 2: Create Render Web Service

1. Go to https://dashboard.render.com
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure:
   - **Name**: `atoms-mcp-server` (or your choice)
   - **Region**: Choose closest to you
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python server.py`
   - **Plan**: `Free`

## Step 3: Add Environment Variables

In the Render dashboard, go to **Environment** tab and add:

### Required Variables

```
ATOMS_FASTMCP_TRANSPORT=http
ATOMS_FASTMCP_PORT=8000
ATOMS_FASTMCP_HOST=0.0.0.0
ATOMS_FASTMCP_HTTP_PATH=/api/mcp
```

### Supabase Variables

Copy from your `.env.local`:

```
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
```

### WorkOS/AuthKit Variables

Copy from your `.env.local`:

```
FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN=https://xxx.authkit.app
WORKOS_API_KEY=sk_...
```

### Public URL (Add AFTER first deployment)

After your first deploy, Render will give you a URL like `https://atoms-mcp-server.onrender.com`

Add this variable:

```
ATOMS_FASTMCP_PUBLIC_BASE_URL=https://your-app.onrender.com
```

Then **redeploy** (Render dashboard → Manual Deploy → Deploy latest commit)

## Step 4: Deploy

Click **"Create Web Service"**

Render will:
1. Clone your repository
2. Install dependencies
3. Start your server
4. Give you a URL like `https://atoms-mcp-server.onrender.com`

⏱️ First deployment takes ~5 minutes

## Step 5: Verify Deployment

Test your endpoints:

```bash
# Health check
curl https://your-app.onrender.com/health

# Should return: {"status": "healthy", "service": "atoms-mcp-server", "transport": "http"}
```

## Step 6: Update WorkOS Redirect URIs

In WorkOS dashboard, add your Render URL to allowed redirects:

```
https://your-app.onrender.com/api/mcp/auth/callback
```

## Step 7: Connect MCP Client

Update your MCP client configuration:

```json
{
  "mcpServers": {
    "atoms": {
      "url": "https://your-app.onrender.com/api/mcp"
    }
  }
}
```

## Free Tier Limitations

⚠️ **Important**: Render free tier services **sleep after 15 minutes of inactivity**

- First request after sleep takes ~30 seconds to wake up
- After that, responses are instant
- Service stays awake as long as you use it

**Workaround**: Use a free uptime monitoring service (like UptimeRobot) to ping your `/health` endpoint every 14 minutes.

## Monitoring & Logs

### View Logs
- Render Dashboard → Your Service → Logs
- Real-time logs of all requests and errors

### Metrics
- Render Dashboard → Your Service → Metrics
- CPU, memory, bandwidth usage

### Shell Access
- Render Dashboard → Your Service → Shell
- SSH into your running container

## Troubleshooting

### Deployment Failed

Check build logs in Render dashboard. Common issues:

1. **Missing dependencies**: Update `requirements.txt`
2. **Wrong Python version**: Render uses Python 3.11 by default
3. **Port binding**: Make sure `ATOMS_FASTMCP_HOST=0.0.0.0` (not 127.0.0.1)

### OAuth Not Working

1. Check environment variables are set correctly
2. Verify `ATOMS_FASTMCP_PUBLIC_BASE_URL` matches your Render URL
3. Update WorkOS redirect URIs to include Render URL

### Service Sleeping Too Often

Upgrade to paid plan ($7/month) for always-on service, or use uptime monitoring.

## Cost Comparison

| Plan | Price | Always-On | Support |
|------|-------|-----------|---------|
| Free | $0 | No (sleeps after 15min) | Community |
| Starter | $7/mo | Yes | Email |
| Standard | $25/mo | Yes | Priority |

## Migration from Vercel

Your code is **already compatible**! The session persistence code we added won't be used (but doesn't hurt).

Key differences:
- ✅ No more stateless worries
- ✅ OAuth works out of the box
- ✅ No 10-second timeout
- ⚠️ Service sleeps on free tier (Vercel doesn't)

## Next Steps

1. **Test all MCP tools** work correctly
2. **Set up uptime monitoring** if on free tier
3. **Configure custom domain** (optional, available on all plans)
4. **Add SSL certificate** (automatic with custom domain)

## Support

- Render Docs: https://render.com/docs
- Render Community: https://community.render.com
- FastMCP Docs: https://docs.fastmcp.com

---

**You're done!** 🎉

Your MCP server is now running on a persistent server where OAuth sessions just work.
