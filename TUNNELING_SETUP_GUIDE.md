# Tunneling Setup Guide - Atoms MCP & Morph MCP

**Setup Date**: October 16, 2025
**Purpose**: Configure public tunnels for both atoms-mcp and morph-mcp services
**Infrastructure**: pheno-sdk kinfra SmartInfraManager

---

## 🎯 Overview

This guide sets up secure tunneling for:
- **atoms-mcp** → `ai.kooshapari.com` (port 8000)
- **morph-mcp** → `morph.kooshapari.com` (port 8001)

Both services will be accessible via HTTPS with automatic certificate management.

---

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)

```bash
# Setup both tunnels automatically
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/atoms-mcp-prod
./setup_tunnels.sh
```

### Option 2: Python Setup

```bash
# Setup using Python infrastructure
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/atoms-mcp-prod
python setup_tunneling.py
```

### Option 3: Manual Setup Using Pheno CLI

```bash
# Install pheno-sdk
pip install pheno-sdk kinfra

# Setup atoms-mcp tunnel
pheno infra tunnel setup \
  --service atoms-mcp \
  --domain ai.kooshapari.com \
  --local-port 8000 \
  --protocol https \
  --auto-start

# Setup morph-mcp tunnel
pheno infra tunnel setup \
  --service morph-mcp \
  --domain morph.kooshapari.com \
  --local-port 8001 \
  --protocol https \
  --auto-start
```

---

## 📋 Prerequisites

### System Requirements
- Python 3.8+
- pheno-sdk installed: `pip install pheno-sdk kinfra`
- DNS configured for:
  - `ai.kooshapari.com`
  - `morph.kooshapari.com`

### Environment Variables
```bash
# Optional: Set tunnel authentication
export TUNNEL_AUTH_TOKEN=your_auth_token
export TUNNEL_SECRET_KEY=your_secret_key

# Optional: Configure proxy settings
export TUNNEL_PROXY_HOST=proxy.example.com
export TUNNEL_PROXY_PORT=8080
```

---

## 🔧 Architecture

### Tunnel Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      Public Internet                            │
│  https://ai.kooshapari.com         https://morph.kooshapari.com│
└────────────┬────────────────────────────────────┬───────────────┘
             │                                    │
             │ pheno-sdk tunnel (encrypted)       │
             │                                    │
     ┌───────▼──────────────┐          ┌─────────▼──────────────┐
     │   Tunnel Ingress     │          │   Tunnel Ingress       │
     │   (Load Balancer)    │          │   (Load Balancer)      │
     └───────┬──────────────┘          └─────────┬──────────────┘
             │                                    │
             │ Local TCP (encrypted)              │
             │                                    │
     ┌───────▼──────────────┐          ┌─────────▼──────────────┐
     │  localhost:8000      │          │  localhost:8001        │
     │  atoms-mcp service   │          │  morph-mcp service     │
     └──────────────────────┘          └────────────────────────┘
```

### Certificate Management
- **Automatic**: Certificates managed by pheno-sdk
- **Auto-Renewal**: Certificates auto-renew 30 days before expiry
- **Type**: Let's Encrypt (via pheno-sdk)

### Security Features
- **Encryption**: TLS 1.3 for all tunnel traffic
- **Authentication**: Optional token-based auth
- **Isolation**: Each service gets isolated tunnel
- **Monitoring**: Built-in tunnel health checks

---

## 📊 Configuration

### atoms-mcp Tunnel Config

**Location**: `/Users/kooshapari/temp-PRODVERCEL/485/kush/atoms-mcp-prod/.tunnel_config.json`

```json
{
  "service": "atoms-mcp",
  "local_port": 8000,
  "domain": "ai.kooshapari.com",
  "tunnel_url": "https://ai.kooshapari.com",
  "status": "active",
  "created_at": "2025-10-16T00:00:00Z",
  "certificate_expires": "2026-10-16T00:00:00Z"
}
```

### morph-mcp Tunnel Config

**Location**: `/Users/kooshapari/temp-PRODVERCEL/485/kush/morph/.tunnel_config.json`

```json
{
  "service": "morph-mcp",
  "local_port": 8001,
  "domain": "morph.kooshapari.com",
  "tunnel_url": "https://morph.kooshapari.com",
  "status": "active",
  "created_at": "2025-10-16T00:00:00Z",
  "certificate_expires": "2026-10-16T00:00:00Z"
}
```

---

## ✅ Starting Services

### Step 1: Setup Tunnels

```bash
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/atoms-mcp-prod
./setup_tunnels.sh
```

### Step 2: Start atoms-mcp

```bash
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/atoms-mcp-prod
uv sync --group dev  # Install dependencies
./atoms start        # Start service
```

### Step 3: Start morph-mcp

```bash
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/morph
./morph start        # Start service
```

### Step 4: Verify Tunnels

```bash
# Test atoms-mcp tunnel
curl https://ai.kooshapari.com/health

# Test morph-mcp tunnel
curl https://morph.kooshapari.com/health

# Check tunnel status
pheno infra tunnel status --service atoms-mcp
pheno infra tunnel status --service morph-mcp
```

---

## 🔍 Monitoring & Troubleshooting

### Check Tunnel Status

```bash
# View all tunnels
pheno infra tunnel list

# Check specific tunnel
pheno infra tunnel status --service atoms-mcp

# View tunnel logs
pheno infra tunnel logs --service atoms-mcp --tail 100
```

### Common Issues

#### Issue 1: Certificate Errors
```bash
# Regenerate certificate
pheno infra tunnel cert-renew --service atoms-mcp

# Check certificate expiry
pheno infra tunnel cert-info --service atoms-mcp
```

#### Issue 2: Connection Refused
```bash
# Verify service is running locally
curl http://localhost:8000/health  # atoms-mcp
curl http://localhost:8001/health  # morph-mcp

# Restart tunnel
pheno infra tunnel restart --service atoms-mcp
```

#### Issue 3: DNS Not Resolving
```bash
# Verify DNS records
nslookup ai.kooshapari.com
nslookup morph.kooshapari.com

# Check DNS configuration
pheno infra dns check --service atoms-mcp
```

---

## 🔐 Security Best Practices

### 1. Authentication
```bash
# Enable token authentication
pheno infra tunnel auth enable --service atoms-mcp
export TUNNEL_AUTH_TOKEN=$(pheno infra tunnel auth-token --generate)
```

### 2. IP Whitelisting
```bash
# Restrict access to specific IPs
pheno infra tunnel ip-whitelist add \
  --service atoms-mcp \
  --ip "203.0.113.0/24"
```

### 3. Rate Limiting
```bash
# Enable rate limiting
pheno infra tunnel rate-limit enable \
  --service atoms-mcp \
  --requests-per-minute 1000
```

### 4. SSL/TLS Settings
```bash
# Enforce minimum TLS version
pheno infra tunnel tls-version \
  --service atoms-mcp \
  --minimum "1.3"
```

---

## 📈 Performance Optimization

### 1. Connection Pooling
```bash
# Enable connection pooling
export TUNNEL_CONNECTION_POOL_SIZE=100
export TUNNEL_CONNECTION_TIMEOUT=30
```

### 2. Caching
```bash
# Enable caching for GET requests
pheno infra tunnel cache enable \
  --service atoms-mcp \
  --ttl 3600
```

### 3. Compression
```bash
# Enable response compression
pheno infra tunnel compression enable \
  --service atoms-mcp \
  --threshold 1024
```

---

## 🔄 Maintenance

### Daily Health Check
```bash
# Check tunnel health
pheno infra tunnel health-check --all

# View metrics
pheno infra tunnel metrics --service atoms-mcp
```

### Weekly Maintenance
```bash
# Check certificate expiry
pheno infra tunnel cert-info --all

# Review access logs
pheno infra tunnel logs --service atoms-mcp --since 7d
```

### Monthly Tasks
- [ ] Review tunnel configuration
- [ ] Check certificate renewal status
- [ ] Review access logs for anomalies
- [ ] Update DNS records if needed
- [ ] Test failover procedures

---

## 📞 Support

### Command Reference

```bash
# View all available commands
pheno infra tunnel --help

# Get detailed help for a command
pheno infra tunnel setup --help

# View tunnel documentation
pheno infra tunnel docs
```

### Useful Links
- pheno-sdk docs: https://pheno.dev/docs
- kinfra docs: https://kinfra.kooshapari.com
- DNS management: https://dns.kooshapari.com

---

## ✨ Key Features

### Automatic Features
- ✅ Automatic certificate provisioning
- ✅ Auto-renewal 30 days before expiry
- ✅ Automatic load balancing
- ✅ Automatic failover
- ✅ Automatic health checking
- ✅ Automatic log rotation

### Optional Features
- 🔧 Custom domain mapping
- 🔧 Basic authentication
- 🔧 IP whitelisting
- 🔧 Rate limiting
- 🔧 Response caching
- 🔧 Response compression
- 🔧 Custom error pages

---

## 🎉 Success Indicators

Once setup is complete, you should see:

✅ **atoms-mcp accessible at**: https://ai.kooshapari.com
✅ **morph-mcp accessible at**: https://morph.kooshapari.com
✅ **Both services return**: `{"status": "healthy"}`
✅ **Certificates**: Valid and auto-renewing
✅ **Logs**: No errors or warnings

---

## 🚀 Next Steps

1. ✅ Run tunnel setup: `./setup_tunnels.sh`
2. ✅ Start atoms-mcp service
3. ✅ Start morph-mcp service
4. ✅ Access both services via public URLs
5. ✅ Monitor tunnel health
6. ✅ Configure monitoring and alerting

---

## 📝 Files Created

- `setup_tunneling.py` - Python-based tunnel setup
- `setup_tunnels.sh` - Bash-based tunnel setup
- `TUNNELING_SETUP_GUIDE.md` - This guide
- `.tunnel_config.json` - Tunnel configuration (created after setup)

---

**Last Updated**: October 16, 2025
**Status**: 🟢 Ready for deployment
**Next**: Run `./setup_tunnels.sh` to begin
