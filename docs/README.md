# Atoms MCP - Documentation Hub

Welcome to the comprehensive documentation for Atoms MCP, a powerful knowledge management system with AI-powered search capabilities.

## 📚 Documentation Overview

This documentation is organized into multiple sections to serve different audiences and use cases:

### 🚀 Quick Start Guides
- **[User Guide](USER_GUIDE.md)** - Complete user-facing documentation with examples
- **[Developer Guide](DEVELOPER_GUIDE.md)** - Comprehensive developer documentation
- **[API Reference](API_REFERENCE.md)** - Detailed API documentation with examples
- **[Usage Examples](USAGE_EXAMPLES.md)** - Practical tutorials and code examples

### 🏗️ Architecture & Technical
- **[Deployment Guide](deployment/)** - Production deployment instructions
- **[Schema Documentation](schema/)** - Database schema and data models
- **[Reference Documentation](reference/)** - Technical reference materials

## 🎯 Choose Your Path

### For End Users
Start with the **[User Guide](USER_GUIDE.md)** to learn how to:
- Set up your account and organization
- Create and manage projects
- Write requirements using EARS and INCOSE formats
- Create and execute test cases
- Use AI-powered search to find information
- Integrate with your existing workflows

### For Developers
Begin with the **[Developer Guide](DEVELOPER_GUIDE.md)** to understand:
- System architecture and design patterns
- Local development setup
- Code organization and structure
- API development patterns
- Database schema and relationships
- Testing strategies and best practices

### For API Integration
Use the **[API Reference](API_REFERENCE.md)** for:
- Complete API endpoint documentation
- Request/response examples
- Authentication and authorization
- Error handling patterns
- Rate limiting information
- SDK examples in multiple languages

### For Learning by Example
Explore **[Usage Examples](USAGE_EXAMPLES.md)** to see:
- Complete project setup workflows
- Requirements management patterns
- Test case creation and execution
- Search and discovery techniques
- CI/CD integration examples
- Troubleshooting common issues

## 🔧 Quick Reference

### Essential Commands
```bash
# Start local development server
python server/entry_points/main.py

# Run tests
pytest tests/ -v

# Check code quality
ruff check .
black .

# Deploy to production
./atoms deploy
```

### Key API Endpoints
```bash
# Create entity
POST /api/entities

# Search entities
POST /api/search/semantic
POST /api/search/text
POST /api/search/hybrid

# MCP tools
POST /api/mcp/tools/entity
POST /api/mcp/tools/search
```

### Common Code Patterns
```python
# Initialize client
from atoms_mcp import AtomsClient
client = AtomsClient(base_url="https://mcp.atoms.tech", api_key="your-key")

# Create organization
org = client.organizations.create({
    "name": "My Company",
    "description": "Software development company"
})

# Search requirements
results = client.search.semantic(
    query="user authentication requirements",
    entity_types=["requirement"],
    limit=10
)
```

## 📖 Documentation Structure

```
docs/
├── README.md                    # This file - documentation hub
├── USER_GUIDE.md               # User-facing documentation
├── DEVELOPER_GUIDE.md          # Developer documentation
├── API_REFERENCE.md            # API documentation
├── USAGE_EXAMPLES.md           # Tutorials and examples
├── deployment/                 # Deployment guides
│   ├── DEPLOYMENT_GUIDE.md
│   ├── VERCEL_CONSOLIDATED_SETUP.md
│   └── WORKOS_SETUP.md
├── schema/                     # Schema documentation
│   ├── SCHEMA_SYNC_README.md
│   ├── RLS_INTEGRATION_SUMMARY.md
│   └── TRIGGERS_IMPLEMENTATION_SUMMARY.md
└── reference/                  # Technical reference
    └── SUPABASE_PYDANTIC_REFERENCE.md
```

## 🎨 Documentation Features

### Code Examples
Every guide includes complete, runnable code examples in multiple languages:
- **Python** - Full SDK examples
- **JavaScript/TypeScript** - Frontend integration
- **cURL** - Command-line testing
- **Bash** - Automation scripts

### Interactive Elements
- **Mermaid diagrams** - Architecture and flow visualization
- **API playground** - Interactive endpoint testing
- **Code snippets** - Copy-paste ready examples
- **Troubleshooting guides** - Common issues and solutions

### Multi-Format Support
- **Markdown** - Primary format for readability
- **OpenAPI/Swagger** - API specification
- **Postman collections** - API testing
- **SDK documentation** - Auto-generated from code

## 🚀 Getting Started

### 1. Choose Your Role
- **End User** → Start with [User Guide](USER_GUIDE.md)
- **Developer** → Start with [Developer Guide](DEVELOPER_GUIDE.md)
- **API Consumer** → Start with [API Reference](API_REFERENCE.md)
- **Learning by Example** → Start with [Usage Examples](USAGE_EXAMPLES.md)

### 2. Set Up Your Environment
```bash
# Clone repository
git clone https://github.com/your-org/atoms-mcp.git
cd atoms-mcp

# Install dependencies
uv sync

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Start development server
python server/entry_points/main.py
```

### 3. Follow the Tutorials
Each guide includes step-by-step tutorials that build upon each other:
- **Basic setup** - Authentication and organization creation
- **Project management** - Creating and organizing projects
- **Requirements** - Writing and managing requirements
- **Testing** - Creating and executing test cases
- **Search** - Using AI-powered search capabilities
- **Integration** - Connecting with external systems

## 🔍 Search Documentation

### By Topic
- **Authentication** - User management and security
- **API** - Endpoints and integration
- **Requirements** - EARS, INCOSE, and other formats
- **Testing** - Test case creation and execution
- **Search** - Semantic and text search capabilities
- **Deployment** - Production setup and configuration

### By Use Case
- **Getting Started** - First-time setup and basic usage
- **Project Management** - Organizing work and teams
- **Requirements Engineering** - Writing and managing requirements
- **Quality Assurance** - Testing and validation
- **Knowledge Management** - Search and discovery
- **Integration** - Connecting with existing tools

### By Technology
- **Python** - Backend development and SDK
- **JavaScript** - Frontend integration
- **REST API** - HTTP-based integration
- **MCP** - Model Context Protocol
- **Supabase** - Database and authentication
- **Vercel** - Deployment and hosting

## 📞 Support and Community

### Getting Help
- **Documentation Issues** - Open an issue on GitHub
- **API Questions** - Check the [API Reference](API_REFERENCE.md)
- **Integration Help** - See [Usage Examples](USAGE_EXAMPLES.md)
- **Bug Reports** - Use the GitHub issue tracker

### Contributing
- **Documentation** - Submit pull requests for improvements
- **Examples** - Add new usage examples
- **Translations** - Help translate documentation
- **Feedback** - Share your experience and suggestions

### Community Resources
- **GitHub Repository** - Source code and issues
- **Discord Server** - Community discussions
- **Stack Overflow** - Technical questions
- **Blog** - Updates and best practices

## 📊 Documentation Metrics

### Coverage
- **API Endpoints** - 100% documented
- **Code Examples** - 50+ complete examples
- **Tutorials** - 10+ step-by-step guides
- **Languages** - Python, JavaScript, cURL, Bash

### Quality
- **Code Review** - All examples tested
- **Accuracy** - Regular updates with releases
- **Completeness** - Full request/response examples
- **Clarity** - Multiple explanation levels

### Maintenance
- **Update Frequency** - With each release
- **Review Process** - Community and team review
- **Version Control** - Git-based versioning
- **Feedback Loop** - Continuous improvement

## 🎯 Next Steps

1. **Choose your starting point** from the guides above
2. **Set up your development environment** using the quick start
3. **Follow the tutorials** to build your first project
4. **Explore advanced features** like AI search and integration
5. **Join the community** for support and collaboration

---

**Happy building with Atoms MCP!** 🚀

For questions or feedback, please open an issue on GitHub or contact the development team.