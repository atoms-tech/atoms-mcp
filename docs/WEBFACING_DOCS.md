# Atoms MCP Server - Documentation Implementation
## MkDocs + Material + Sphinx Stack

---

## 🏗️ Directory Structure

```
docs/
├── mkdocs.yml                    # MkDocs configuration
├── docs/
│   ├── index.md                 # Home page
│   ├── 01-mcp-fundamentals/
│   │   ├── index.md
│   │   ├── 01_what_is_mcp.md
│   │   ├── 02_mcp_architecture.md
│   │   ├── 03_tool_discovery.md
│   │   ├── 04_authentication_overview.md
│   │   └── 05_transport_modes.md
│   │
│   ├── 02-getting-started/
│   │   ├── index.md
│   │   ├── 10_quick_start.md
│   │   ├── 11_installation.md
│   │   ├── 12_first_tool_call.md
│   │   ├── 13_common_patterns.md
│   │   ├── 14_troubleshooting.md
│   │   └── 15_faq.md
│   │
│   ├── 03-the-5-tools/
│   │   ├── index.md
│   │   ├── 20_workspace_operation.md
│   │   ├── 21_entity_operation.md
│   │   ├── 22_relationship_operation.md
│   │   ├── 23_workflow_execute.md
│   │   └── 24_data_query.md
│   │
│   ├── 04-integration-guides/
│   │   ├── index.md
│   │   ├── 30_claude_integration.md
│   │   ├── 31_cursor_integration.md
│   │   ├── 32_custom_mcp_client.md
│   │   ├── 33_oauth_pkce_flow.md
│   │   ├── 34_hybrid_auth.md
│   │   └── 35_session_management.md
│   │
│   ├── 05-advanced-topics/
│   │   ├── index.md
│   │   ├── 40_semantic_search.md
│   │   ├── 41_vector_search_tuning.md
│   │   ├── 42_rate_limiting.md
│   │   ├── 43_caching_strategies.md
│   │   ├── 44_error_handling.md
│   │   ├── 45_performance_optimization.md
│   │   ├── 46_security_hardening.md
│   │   └── 47_monitoring_observability.md
│   │
│   ├── 06-deployment/
│   │   ├── index.md
│   │   ├── 50_deployment_overview.md
│   │   ├── 51_vercel_deployment.md
│   │   ├── 52_gcp_deployment.md
│   │   ├── 53_aws_deployment.md
│   │   ├── 54_self_hosted.md
│   │   ├── 55_environment_config.md
│   │   ├── 56_monitoring_setup.md
│   │   └── 57_troubleshooting_deployment.md
│   │
│   ├── 07-reference/
│   │   ├── index.md
│   │   ├── 60_api_reference.md
│   │   ├── 61_error_codes.md
│   │   ├── 62_data_model.md
│   │   ├── 63_examples_basic.md
│   │   ├── 64_examples_advanced.md
│   │   ├── 65_curl_examples.md
│   │   ├── 66_python_sdk.md
│   │   └── 67_changelog.md
│   │
│   ├── assets/
│   │   ├── images/
│   │   │   ├── mcp-architecture.png
│   │   │   ├── oauth-flow.png
│   │   │   └── tool-discovery.png
│   │   ├── css/
│   │   │   └── custom.css
│   │   └── js/
│   │       └── custom.js
│   │
│   └── api/
│       ├── index.md
│       └── reference.md (auto-generated)
│
├── scripts/
│   ├── generate_api_docs.py      # Extract from docstrings
│   ├── generate_error_codes.py   # Extract from errors.py
│   ├── generate_changelog.py     # Parse git tags
│   └── validate_examples.py      # Test all code examples
│
├── .github/workflows/
│   └── docs.yml                  # CI/CD pipeline
│
└── requirements.txt
    ├── mkdocs==1.5.3
    ├── mkdocs-material==9.4.10
    ├── sphinx==7.2.6
    ├── sphinx-rtd-theme==2.0.0
    └── pymdown-extensions==10.5
```

---

## 📋 MkDocs Configuration

### mkdocs.yml
```yaml
site_name: Atoms MCP Server
site_description: Complete documentation for Atoms MCP
site_url: https://docs.atoms.io
repo_url: https://github.com/atoms-tech/atoms-mcp
repo_name: atoms-mcp

theme:
  name: material
  palette:
    - scheme: light
      primary: blue
      accent: blue
    - scheme: dark
      primary: blue
      accent: blue
  features:
    - navigation.instant
    - navigation.tracking
    - navigation.tabs
    - navigation.sections
    - navigation.expand
    - toc.follow
    - search.suggest
    - search.highlight
    - content.code.copy
    - content.code.annotate

plugins:
  - search
  - awesome-pages
  - minify

markdown_extensions:
  - pymdownx.highlight
  - pymdownx.superfences
  - pymdownx.tabbed
  - pymdownx.tasklist
  - pymdownx.emoji
  - tables
  - admonition
  - toc

nav:
  - Home: index.md
  - MCP Fundamentals:
    - 01-mcp-fundamentals/index.md
    - What is MCP?: 01-mcp-fundamentals/01_what_is_mcp.md
    - Architecture: 01-mcp-fundamentals/02_mcp_architecture.md
    - Tool Discovery: 01-mcp-fundamentals/03_tool_discovery.md
    - Authentication: 01-mcp-fundamentals/04_authentication_overview.md
    - Transport Modes: 01-mcp-fundamentals/05_transport_modes.md
  - Getting Started:
    - 02-getting-started/index.md
    - Quick Start: 02-getting-started/10_quick_start.md
    - Installation: 02-getting-started/11_installation.md
    - First Tool Call: 02-getting-started/12_first_tool_call.md
    - Common Patterns: 02-getting-started/13_common_patterns.md
    - Troubleshooting: 02-getting-started/14_troubleshooting.md
    - FAQ: 02-getting-started/15_faq.md
  - The 5 Tools:
    - 03-the-5-tools/index.md
    - workspace_operation: 03-the-5-tools/20_workspace_operation.md
    - entity_operation: 03-the-5-tools/21_entity_operation.md
    - relationship_operation: 03-the-5-tools/22_relationship_operation.md
    - workflow_execute: 03-the-5-tools/23_workflow_execute.md
    - data_query: 03-the-5-tools/24_data_query.md
  - Integration Guides:
    - 04-integration-guides/index.md
    - Claude: 04-integration-guides/30_claude_integration.md
    - Cursor: 04-integration-guides/31_cursor_integration.md
    - Custom Client: 04-integration-guides/32_custom_mcp_client.md
    - OAuth PKCE: 04-integration-guides/33_oauth_pkce_flow.md
    - Hybrid Auth: 04-integration-guides/34_hybrid_auth.md
    - Sessions: 04-integration-guides/35_session_management.md
  - Advanced Topics:
    - 05-advanced-topics/index.md
    - Semantic Search: 05-advanced-topics/40_semantic_search.md
    - Vector Tuning: 05-advanced-topics/41_vector_search_tuning.md
    - Rate Limiting: 05-advanced-topics/42_rate_limiting.md
    - Caching: 05-advanced-topics/43_caching_strategies.md
    - Error Handling: 05-advanced-topics/44_error_handling.md
    - Performance: 05-advanced-topics/45_performance_optimization.md
    - Security: 05-advanced-topics/46_security_hardening.md
    - Monitoring: 05-advanced-topics/47_monitoring_observability.md
  - Deployment:
    - 06-deployment/index.md
    - Overview: 06-deployment/50_deployment_overview.md
    - Vercel: 06-deployment/51_vercel_deployment.md
    - GCP: 06-deployment/52_gcp_deployment.md
    - AWS: 06-deployment/53_aws_deployment.md
    - Self-Hosted: 06-deployment/54_self_hosted.md
    - Configuration: 06-deployment/55_environment_config.md
    - Monitoring: 06-deployment/56_monitoring_setup.md
    - Troubleshooting: 06-deployment/57_troubleshooting_deployment.md
  - Reference:
    - 07-reference/index.md
    - API Reference: 07-reference/60_api_reference.md
    - Error Codes: 07-reference/61_error_codes.md
    - Data Model: 07-reference/62_data_model.md
    - Examples (Basic): 07-reference/63_examples_basic.md
    - Examples (Advanced): 07-reference/64_examples_advanced.md
    - Curl Examples: 07-reference/65_curl_examples.md
    - Python SDK: 07-reference/66_python_sdk.md
    - Changelog: 07-reference/67_changelog.md
```

---

## 🔄 CI/CD Pipeline

### .github/workflows/docs.yml
```yaml
name: Build & Deploy Docs
on:
  push:
    branches: [main]
    paths: ['docs/**', 'server.py', 'tools/**']
  schedule:
    - cron: '0 0 * * 0'  # Weekly

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install -r docs/requirements.txt
      
      - name: Generate API docs
        run: python docs/scripts/generate_api_docs.py
      
      - name: Generate error codes
        run: python docs/scripts/generate_error_codes.py
      
      - name: Validate examples
        run: python docs/scripts/validate_examples.py
      
      - name: Build docs
        run: mkdocs build
      
      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
```

---

## 🛠️ Automation Scripts

### generate_api_docs.py
```python
#!/usr/bin/env python3
"""Extract API docs from tool docstrings."""

import ast
import json
from pathlib import Path

def extract_tool_docs():
    """Extract docstrings from tools/."""
    tools_dir = Path("tools")
    api_docs = {}
    
    for tool_file in tools_dir.glob("*.py"):
        if tool_file.name.startswith("_"):
            continue
        
        with open(tool_file) as f:
            tree = ast.parse(f.read())
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                docstring = ast.get_docstring(node)
                if docstring:
                    api_docs[node.name] = {
                        "docstring": docstring,
                        "file": tool_file.name
                    }
    
    # Generate markdown
    output = Path("docs/07-reference/60_api_reference.md")
    with open(output, "w") as f:
        f.write("# API Reference\n\n")
        f.write("*Auto-generated from source code*\n\n")
        for name, info in sorted(api_docs.items()):
            f.write(f"## {name}\n\n")
            f.write(f"**File**: `{info['file']}`\n\n")
            f.write(f"{info['docstring']}\n\n")

if __name__ == "__main__":
    extract_tool_docs()
```

---

## 📊 Hosting & Deployment

### Option 1: Vercel (Recommended)
- Free tier: 100GB bandwidth/month
- Auto-deploy from git
- Custom domain
- Analytics included

### Option 2: Netlify
- Free tier: unlimited bandwidth
- Form handling
- Serverless functions
- Split testing

### Option 3: GitHub Pages
- Free tier: unlimited
- Built-in CI/CD
- Custom domain
- HTTPS automatic

---

## 🔍 Search Configuration

MkDocs Material includes built-in search:
- No external dependency
- Works offline
- Fast indexing
- Instant results

Optional: Add Meilisearch for advanced features
```yaml
plugins:
  - search:
      lang: en
      separator: '[\s\-\.]+'
```

---

## 📈 Analytics

### Plausible Analytics (Privacy-First)
```html
<script defer data-domain="docs.atoms.io" 
  src="https://plausible.io/js/script.js"></script>
```

Benefits:
- No cookies
- GDPR compliant
- Simple dashboard
- Free tier available

---

## ✅ Launch Checklist

- [ ] MkDocs configured
- [ ] Material theme installed
- [ ] Directory structure created
- [ ] CI/CD pipeline set up
- [ ] Hosting configured
- [ ] Custom domain set up
- [ ] SSL certificate installed
- [ ] Analytics enabled
- [ ] All 57 documents written
- [ ] All examples tested
- [ ] Cross-links verified
- [ ] Mobile tested
- [ ] Accessibility audit passed
- [ ] SEO optimized
- [ ] Sitemap generated
- [ ] robots.txt configured
- [ ] Launch announcement


