# Atoms MCP Server Documentation

Complete documentation for the Atoms MCP Server project.

## Quick Links

### For Users
- [Getting Started Guide](#getting-started) (Coming Soon)
- [User Guides](#user-guides) (Coming Soon)
- [Common Tasks](#common-tasks) (Coming Soon)

### For Developers
- [Testing Guide](TESTING.md) - Complete testing documentation
- [Authentication Guide](AUTH_SYSTEM_COMPLETE_GUIDE.md) - Auth system walkthrough
- [Auth Quick Reference](AUTH_QUICK_REFERENCE.md) - Quick auth reference
- [Project History](PROJECT_HISTORY.md) - Major milestones and achievements
- [Web-Facing Docs Plan](WEBFACING_DOCS.md) - Documentation structure plan

### For Operators
- [Deployment Guides](#deployment) (Coming Soon)
- [Monitoring & Observability](#monitoring) (Coming Soon)
- [Troubleshooting](#troubleshooting) (Coming Soon)

---

## Core Documentation

### Testing
- **[TESTING.md](TESTING.md)** - Complete testing guide
  - Test governance framework
  - Test organization and execution
  - E2E testing guide
  - Test history and achievements
  - Test fixes and improvements

### Authentication
- **[AUTH_SYSTEM_COMPLETE_GUIDE.md](AUTH_SYSTEM_COMPLETE_GUIDE.md)** - Complete auth system walkthrough
  - Frontend to MCP token flow
  - 4-layer auth architecture
  - Supported auth methods
  - Token verification flow
  - Troubleshooting guide

- **[AUTH_QUICK_REFERENCE.md](AUTH_QUICK_REFERENCE.md)** - Quick auth reference
  - Token flow diagram
  - JWT claims reference
  - Common issues & solutions
  - Configuration guide
  - API reference

### Project History
- **[PROJECT_HISTORY.md](PROJECT_HISTORY.md)** - Complete project history
  - 100% pass rate achievement
  - Comprehensive QOL enhancements
  - Test suite foundation
  - Authentication system
  - Session summaries

### Documentation Planning
- **[WEBFACING_DOCS.md](WEBFACING_DOCS.md)** - Web-facing documentation plan
  - Documentation architecture
  - Implementation roadmap
  - Directory structure
  - Success metrics

---

## Session Documentation

All session-specific documentation is organized in `docs/sessions/`:

```
docs/sessions/
├── 20251122-test-suite-foundation/
│   └── Session-specific docs
├── 20251123-qol-enhancements/
│   └── Phase completion summaries
└── 20251123-db-review-mcp-enhancements/
    └── Database review docs
```

See individual session folders for detailed session documentation.

---

## Documentation Structure

### Canonical Documentation (Persistent)
These documents live in `docs/` root and persist across sessions:
- `README.md` - This file (main entry point)
- `TESTING.md` - Testing guide
- `AUTH_SYSTEM_COMPLETE_GUIDE.md` - Auth system documentation
- `AUTH_QUICK_REFERENCE.md` - Auth quick reference
- `PROJECT_HISTORY.md` - Project history
- `WEBFACING_DOCS.md` - Documentation plan

### Session Documentation (Temporary)
Session-specific work artifacts are in `docs/sessions/<session-id>/`:
- `00_SESSION_OVERVIEW.md` - Goals, decisions
- `01_RESEARCH.md` - Research findings
- `02_SPECIFICATIONS.md` - Feature specifications
- `03_DAG_WBS.md` - Dependencies, work breakdown
- `04_IMPLEMENTATION_STRATEGY.md` - Technical approach
- `05_KNOWN_ISSUES.md` - Bugs, workarounds
- `06_TESTING_STRATEGY.md` - Test plan

---

## Contributing

When adding new documentation:

1. **Session-specific** → Place in `docs/sessions/<session-id>/`
2. **Canonical/Architectural** → Place in `docs/` root
3. **Update this README** → Add links to new canonical docs
4. **Follow naming conventions** → See [WEBFACING_DOCS.md](WEBFACING_DOCS.md) for structure

---

## Maintenance

- **Quarterly Review** - Update for new features
- **Issue Tracking** - Link to GitHub issues
- **Version Sync** - Keep with code releases
- **User Feedback** - Incorporate suggestions

---

**Last Updated:** 2025-11-23  
**Status:** Active Development  
**Maintainer:** Project Team
