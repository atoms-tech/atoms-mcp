# Web-Facing Documentation Structure
## Complete Template for Agent-Focused Documentation

---

## 📁 Directory Structure

```
docs/
├── README.md                          # Main index
├── SUITE_OVERVIEW.md                  # Documentation overview
├── mkdocs.yml                         # MkDocs configuration
│
├── 01-agent-demonstrations/
│   ├── index.md
│   ├── 01_what_agents_can_do.md
│   ├── 02_creating_entities.md
│   ├── 03_searching_and_linking.md
│   ├── 04_complex_workflows.md
│   ├── 05_error_handling.md
│   └── 06_real_world_examples.md
│
├── 02-getting-started/
│   ├── index.md
│   ├── 01_quick_start.md
│   ├── 02_connect_claude.md
│   ├── 03_connect_cursor.md
│   ├── 04_custom_agent.md
│   └── 05_first_interaction.md
│
├── 03-tool-reference/
│   ├── index.md
│   ├── 01_workspace_operation.md
│   ├── 02_entity_operation.md
│   ├── 03_relationship_operation.md
│   ├── 04_workflow_execute.md
│   └── 05_data_query.md
│
├── 04-advanced-patterns/
│   ├── index.md
│   ├── 01_multi_step_workflows.md
│   ├── 02_error_recovery.md
│   ├── 03_performance_optimization.md
│   └── 04_custom_strategies.md
│
├── 05-developer-setup/
│   ├── index.md
│   ├── 01_local_development.md
│   ├── 02_extending_tools.md
│   └── 03_custom_tools.md
│
└── assets/
    ├── demos/
    │   ├── create_entity.gif
    │   ├── search_entity.gif
    │   ├── create_relationship.gif
    │   ├── workflow_execution.gif
    │   └── error_handling.gif
    ├── scripts/
    │   ├── demo_create.tape
    │   ├── demo_search.tape
    │   └── ...
    └── images/
        ├── architecture.png
        ├── oauth_flow.png
        └── ...
```

---

## 📄 docs/README.md

```markdown
# Atoms MCP Server Documentation

Welcome to Atoms MCP Server documentation. This guide helps you integrate
Atoms into your AI agents (Claude, Cursor, or custom).

## What is Atoms MCP?

Atoms MCP is a Model Context Protocol server that provides AI agents with
access to the Atoms knowledge management platform.

## Quick Links

- **New to MCP?** → [What is MCP?](01-agent-demonstrations/01_what_agents_can_do.md)
- **Want to get started?** → [Quick Start](02-getting-started/01_quick_start.md)
- **Using Claude?** → [Claude Integration](02-getting-started/02_connect_claude.md)
- **Using Cursor?** → [Cursor Integration](02-getting-started/03_connect_cursor.md)
- **Need tool reference?** → [Tool Reference](03-tool-reference/index.md)

## Learning Paths

### Path 1: I'm New to MCP (30 minutes)
1. [What is MCP?](01-agent-demonstrations/01_what_agents_can_do.md)
2. [Quick Start](02-getting-started/01_quick_start.md)
3. [First Interaction](02-getting-started/05_first_interaction.md)

### Path 2: I'm Using Claude (1 hour)
1. [What is MCP?](01-agent-demonstrations/01_what_agents_can_do.md)
2. [Claude Integration](02-getting-started/02_connect_claude.md)
3. [Tool Reference](03-tool-reference/index.md)
4. [Examples](01-agent-demonstrations/06_real_world_examples.md)

### Path 3: I'm Using Cursor (1 hour)
1. [What is MCP?](01-agent-demonstrations/01_what_agents_can_do.md)
2. [Cursor Integration](02-getting-started/03_connect_cursor.md)
3. [Tool Reference](03-tool-reference/index.md)
4. [Examples](01-agent-demonstrations/06_real_world_examples.md)

## Documentation Sections

### 1. Agent Demonstrations (40%)
See what agents can do with Atoms MCP through live demonstrations.

### 2. Getting Started (20%)
Quick setup guides for Claude, Cursor, and custom agents.

### 3. Tool Reference (20%)
Complete reference for all 5 Atoms MCP tools.

### 4. Advanced Patterns (15%)
Complex workflows, error handling, and optimization.

### 5. Developer Setup (5%)
For developers extending Atoms MCP.

## Search

Use the search box (top right) to find what you need.

## Support

- **Questions?** Check [FAQ](02-getting-started/01_quick_start.md#faq)
- **Issues?** See [Troubleshooting](02-getting-started/01_quick_start.md#troubleshooting)
- **Contact**: support@atoms.io
```

---

## 📄 docs/SUITE_OVERVIEW.md

```markdown
# Documentation Suite Overview

This document explains the entire Atoms MCP documentation suite.

## Three Documentation Layers

### 1. Web-Facing Documentation (This Site)
For agents and developers using Atoms MCP.

**Sections**:
- Agent Demonstrations
- Getting Started
- Tool Reference
- Advanced Patterns
- Developer Setup

**Audience**: Agents, developers, integrators

### 2. Internal Developer Documentation
For Atoms development team.

**Documents**:
- DEVELOPMENT.md - Development guide
- ARCHITECTURE.md - System architecture
- Module READMEs - Module documentation

**Audience**: Internal developers only

### 3. Codebase Documentation
Embedded in source code.

**Components**:
- Module docstrings
- Function docstrings
- Class docstrings
- Inline comments

**Audience**: Developers reading code

## Navigation

### By Role

**I'm an Agent Developer**
→ Start with [Getting Started](02-getting-started/index.md)

**I'm an Internal Developer**
→ See DEVELOPMENT.md in repository root

**I'm Reading Code**
→ Look for docstrings in source files

### By Task

**I want to integrate Atoms into Claude**
→ [Claude Integration](02-getting-started/02_connect_claude.md)

**I want to see what agents can do**
→ [Agent Demonstrations](01-agent-demonstrations/index.md)

**I need to understand a tool**
→ [Tool Reference](03-tool-reference/index.md)

**I want to build something complex**
→ [Advanced Patterns](04-advanced-patterns/index.md)

## Search Tips

- Search for tool names: "entity_operation"
- Search for tasks: "create entity"
- Search for concepts: "authentication"
- Search for errors: "permission denied"

## Feedback

Found an issue? Have a suggestion?
→ Contact: docs@atoms.io
```

---

## 📄 Section Index Templates

### docs/01-agent-demonstrations/index.md

```markdown
# Agent Demonstrations

See what agents can do with Atoms MCP through live demonstrations.

## Demonstrations

1. [What Agents Can Do](01_what_agents_can_do.md)
   - Overview of agent capabilities
   - Real-world use cases

2. [Creating Entities](02_creating_entities.md)
   - Creating single entities
   - Bulk entity creation
   - Error handling

3. [Searching and Linking](03_searching_and_linking.md)
   - Searching entities
   - Creating relationships
   - Building knowledge graphs

4. [Complex Workflows](04_complex_workflows.md)
   - Multi-step workflows
   - Conditional logic
   - Error recovery

5. [Error Handling](05_error_handling.md)
   - Common errors
   - Recovery strategies
   - Best practices

6. [Real-World Examples](06_real_world_examples.md)
   - Complete workflows
   - Production patterns
   - Performance tips

## Learning Path

1. Start with [What Agents Can Do](01_what_agents_can_do.md)
2. Watch demonstrations
3. Try examples
4. Build your own
```

### docs/02-getting-started/index.md

```markdown
# Getting Started

Quick setup guides for integrating Atoms MCP with your agent.

## Guides

1. [Quick Start](01_quick_start.md) - 5 minutes
   - Prerequisites
   - Installation
   - First interaction

2. [Claude Integration](02_connect_claude.md) - 10 minutes
   - Add Atoms MCP to Claude
   - Configure authentication
   - First query

3. [Cursor Integration](03_connect_cursor.md) - 10 minutes
   - Add Atoms MCP to Cursor
   - Configure authentication
   - First query

4. [Custom Agent](04_custom_agent.md) - 30 minutes
   - Build custom MCP client
   - Connect to Atoms MCP
   - Implement tool calling

5. [First Interaction](05_first_interaction.md) - 5 minutes
   - Make your first tool call
   - Understand responses
   - Next steps

## Quick Links

- [Tool Reference](../03-tool-reference/index.md)
- [Examples](../01-agent-demonstrations/06_real_world_examples.md)
- [Troubleshooting](01_quick_start.md#troubleshooting)
```

### docs/03-tool-reference/index.md

```markdown
# Tool Reference

Complete reference for all 5 Atoms MCP tools.

## Tools

1. [workspace_operation](01_workspace_operation.md)
   - Manage workspace context
   - Set active project/team
   - List workspaces

2. [entity_operation](02_entity_operation.md)
   - Create, read, update, delete entities
   - Search entities
   - Bulk operations

3. [relationship_operation](03_relationship_operation.md)
   - Create relationships
   - Query relationships
   - Delete relationships

4. [workflow_execute](04_workflow_execute.md)
   - Execute workflows
   - Multi-step operations
   - Transaction support

5. [data_query](05_data_query.md)
   - Search entities
   - Semantic search
   - Aggregation

## Quick Reference

| Tool | Purpose | Common Use |
|------|---------|-----------|
| workspace_operation | Manage context | Set active project |
| entity_operation | CRUD entities | Create documents |
| relationship_operation | Link entities | Create relationships |
| workflow_execute | Run workflows | Multi-step operations |
| data_query | Search data | Find entities |

## Examples

See [Real-World Examples](../01-agent-demonstrations/06_real_world_examples.md)
for complete workflows using these tools.
```

---

## 📄 Page Template

```markdown
# Page Title

Brief one-line description.

## Overview

Longer description of what this page covers.

## Quick Example

[vhs recording or code example]

## Detailed Explanation

Detailed explanation of the topic.

### Subtopic 1
Content

### Subtopic 2
Content

## Code Examples

### Example 1: Basic Usage
```python
# Code example
```

### Example 2: Advanced Usage
```python
# Code example
```

## Error Handling

Common errors and how to handle them.

## Best Practices

Tips and best practices.

## See Also

- [Related Page 1](link)
- [Related Page 2](link)

## FAQ

**Q: Common question?**
A: Answer

**Q: Another question?**
A: Answer
```


