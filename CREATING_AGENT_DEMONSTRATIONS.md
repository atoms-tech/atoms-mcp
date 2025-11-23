# Creating Agent Demonstrations for MCP Docs
## Tools, Techniques, and Examples

---

## 🎬 Demonstration Types & Tools

### 1. VHS Terminal Recordings

**What**: Record terminal interactions as GIFs
**Tool**: `vhs` (charmbracelet)
**Output**: Shareable GIFs, embeddable in docs

**Installation**:
```bash
brew install charmbracelet/tap/vhs
```

**Example: Creating an Entity**
```bash
# demo.tape
Output: create_entity.gif
Set FontSize 16
Set Width 1200
Set Height 600
Set TypingSpeed 50ms

Type "python3"
Enter
Sleep 500ms

Type "from atoms_mcp import AtomsMCP"
Enter
Sleep 500ms

Type "client = AtomsMCP()"
Enter
Sleep 500ms

Type "result = await client.call_tool('entity_operation', {'operation': 'create', 'entity_type': 'document', 'properties': {'title': 'My Doc'}})"
Enter
Sleep 1s

Type "print(result)"
Enter
Sleep 500ms
```

**Run**:
```bash
vhs < demo.tape
# Output: create_entity.gif
```

**Embed in docs**:
```markdown
![Creating an entity](../assets/demos/create_entity.gif)
```

---

### 2. Asciinema Terminal Recordings

**What**: Record terminal interactions as videos
**Tool**: `asciinema`
**Output**: Playable videos, shareable links

**Installation**:
```bash
brew install asciinema
```

**Record**:
```bash
asciinema rec demo.cast
# ... do stuff ...
# Press Ctrl+D to stop
```

**Play**:
```bash
asciinema play demo.cast
```

**Share**:
```bash
asciinema upload demo.cast
# Get shareable link
```

---

### 3. Cursor Agent Recording

**What**: Record Cursor agent using Atoms MCP
**Setup**: 
1. Connect Cursor to Atoms MCP
2. Enable agent mode
3. Record terminal/screen

**Example workflow**:
```
1. Open Cursor
2. Attach Atoms MCP
3. Ask agent: "Create 5 documents"
4. Record terminal output
5. Capture agent reasoning
```

**Tools**:
- `asciinema` - Terminal recording
- `ffmpeg` - Screen recording
- `obs` - Screen recording

---

### 4. Claude Agent Recording

**What**: Record Claude using Atoms MCP
**Setup**:
1. Connect Claude to Atoms MCP
2. Start conversation
3. Record interaction

**Example**:
```
User: "Create a document about MCP"
Claude: [uses entity_operation tool]
Claude: "Created document with ID ent_123"

User: "Link it to requirements"
Claude: [uses relationship_operation tool]
Claude: "Linked to 3 requirements"
```

---

### 5. Code Examples with REPL Output

**What**: Show code + actual output
**Format**: Markdown with code blocks

**Example**:
```python
# Create entity
>>> from atoms_mcp import AtomsMCP
>>> client = AtomsMCP()
>>> result = await client.call_tool(
...     "entity_operation",
...     {
...         "operation": "create",
...         "entity_type": "document",
...         "properties": {"title": "My Doc"}
...     }
... )
>>> print(result)
{
    "success": true,
    "data": {
        "id": "ent_123",
        "title": "My Doc",
        "created_at": "2025-11-23T10:00:00Z"
    }
}
```

---

### 6. Agent Reasoning Traces

**What**: Show how agents think
**Format**: Structured text with reasoning steps

**Example**:
```
Agent Reasoning:
  1. User wants to create entities
  2. I need to use entity_operation tool
  3. Parameters needed:
     - operation: "create"
     - entity_type: "document"
     - properties: {"title": "..."}
  4. Calling tool...

Tool Response:
  {
    "success": true,
    "data": {"id": "ent_123"}
  }

Agent Response:
  "Created document with ID ent_123"
```

---

## 📋 Documentation Page Structure

### Example: "Creating Entities"

```markdown
# Creating Entities with Agents

## Overview
Learn how agents use the entity_operation tool to create entities.

## Quick Demonstration
![Creating an entity](../assets/demos/create_entity.gif)

## What's Happening
1. Agent receives user request
2. Agent calls entity_operation tool
3. Tool returns entity ID
4. Agent confirms to user

## Multi-Turn Conversation
User: "Create 3 documents"
Agent: [creates 3 entities]
Agent: "Created 3 documents"

User: "Tag them as 'draft'"
Agent: [updates all 3]
Agent: "Tagged all as 'draft'"

## Code Example
```python
result = await client.call_tool(
    "entity_operation",
    {"operation": "create", "entity_type": "document"}
)
```

## Agent Reasoning
Agent: "User wants to create entities"
Agent: "I'll use entity_operation tool"
Agent: [calls tool]
Agent: "Success!"

## Real-World Example
[vhs recording of complex workflow]

## Error Handling
What happens if creation fails?
[vhs recording of error recovery]
```

---

## 🛠️ Workflow for Creating Demonstrations

### Step 1: Plan the Demonstration
- What should the agent do?
- What tools will it use?
- What's the expected outcome?

### Step 2: Create the Script
```bash
# demo.tape
Output: demo.gif
Set FontSize 16
Set Width 1200
Set Height 600

# Your commands here
```

### Step 3: Record
```bash
vhs < demo.tape
```

### Step 4: Embed in Docs
```markdown
![Demo](../assets/demos/demo.gif)
```

### Step 5: Add Explanation
- What's happening
- Why it matters
- How to use it

---

## 📊 Demonstration Examples

### Example 1: Creating Entities
```bash
# demo_create.tape
Output: create_entity.gif
Set FontSize 16
Set Width 1200
Set Height 600

Type "python3"
Enter
Sleep 500ms

Type "from atoms_mcp import AtomsMCP"
Enter
Sleep 500ms

Type "client = AtomsMCP()"
Enter
Sleep 500ms

Type "result = await client.call_tool('entity_operation', {'operation': 'create', 'entity_type': 'document', 'properties': {'title': 'My Doc'}})"
Enter
Sleep 1s

Type "print(result)"
Enter
```

### Example 2: Searching Entities
```bash
# demo_search.tape
Output: search_entity.gif
Set FontSize 16
Set Width 1200
Set Height 600

Type "python3"
Enter
Sleep 500ms

Type "from atoms_mcp import AtomsMCP"
Enter
Sleep 500ms

Type "client = AtomsMCP()"
Enter
Sleep 500ms

Type "result = await client.call_tool('data_query', {'operation': 'search', 'query': 'authentication', 'limit': 10})"
Enter
Sleep 1s

Type "print(result)"
Enter
```

### Example 3: Creating Relationships
```bash
# demo_relationship.tape
Output: create_relationship.gif
Set FontSize 16
Set Width 1200
Set Height 600

Type "python3"
Enter
Sleep 500ms

Type "from atoms_mcp import AtomsMCP"
Enter
Sleep 500ms

Type "client = AtomsMCP()"
Enter
Sleep 500ms

Type "result = await client.call_tool('relationship_operation', {'operation': 'create', 'source_id': 'ent_1', 'target_id': 'ent_2', 'relationship_type': 'links_to'})"
Enter
Sleep 1s

Type "print(result)"
Enter
```

---

## 🎯 Best Practices

### 1. Keep Demonstrations Short
- 30 seconds max
- Focus on one task
- Clear beginning and end

### 2. Use Clear Typing Speed
- Not too fast (hard to read)
- Not too slow (boring)
- ~50ms per character

### 3. Add Pauses
- After commands (500ms)
- Before output (1s)
- Between steps (500ms)

### 4. Show Actual Output
- Real tool responses
- Real error messages
- Real agent reasoning

### 5. Explain What's Happening
- Add narration
- Explain reasoning
- Show next steps

---

## 📁 File Organization

```
docs/
├── assets/
│   ├── demos/
│   │   ├── create_entity.gif
│   │   ├── search_entity.gif
│   │   ├── create_relationship.gif
│   │   ├── workflow_execution.gif
│   │   └── error_handling.gif
│   ├── scripts/
│   │   ├── demo_create.tape
│   │   ├── demo_search.tape
│   │   ├── demo_relationship.tape
│   │   └── demo_workflow.tape
│   └── recordings/
│       ├── cursor_agent.cast
│       ├── claude_agent.cast
│       └── complex_workflow.cast
│
└── 01-agent-demonstrations/
    ├── 01_creating_entities.md
    ├── 02_searching_entities.md
    ├── 03_creating_relationships.md
    ├── 04_executing_workflows.md
    └── 05_error_handling.md
```

---

## 🚀 Automation

### Generate All Demos
```bash
#!/bin/bash
# generate_demos.sh

for tape in assets/scripts/*.tape; do
    vhs < "$tape"
done
```

### Embed in Docs
```bash
#!/bin/bash
# embed_demos.sh

for gif in assets/demos/*.gif; do
    name=$(basename "$gif" .gif)
    echo "![${name}](../assets/demos/${gif})" >> docs/01-agent-demonstrations/${name}.md
done
```

---

## ✨ Why This Matters

**Demonstrations show**:
- ✅ What agents can actually do
- ✅ How agents reason
- ✅ Real multi-turn interactions
- ✅ Error handling
- ✅ Performance
- ✅ Real-world workflows

**Better than API docs because**:
- ✅ Visual learning
- ✅ Shows actual behavior
- ✅ Demonstrates reasoning
- ✅ More engaging
- ✅ Easier to understand


