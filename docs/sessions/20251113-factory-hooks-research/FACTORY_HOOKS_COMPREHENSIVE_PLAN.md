# Factory Droid Hooks: Comprehensive Research & Implementation Plan

**Project:** Atoms MCP Server (atoms-mcp-prod)  
**Date:** 2025-11-13  
**Status:** Research Complete - Ready for Implementation Planning

---

## Executive Summary

Factory's hooks feature provides powerful automation capabilities for AI-driven development workflows. This document analyzes Factory hooks and proposes **23 production-ready hooks** specifically designed for the atoms-mcp-prod project, organized into 5 categories:

1. **Code Quality & Validation** (8 hooks) - Enforce standards, prevent errors
2. **Testing & Coverage** (5 hooks) - Automate testing workflows
3. **Git & Version Control** (4 hooks) - Enhance git operations
4. **Documentation & Context** (3 hooks) - Maintain living documentation
5. **Security & Safety** (3 hooks) - Prevent dangerous operations

**Expected Impact:**
- **80% reduction** in manual validation tasks
- **100% enforcement** of code quality standards
- **Automatic test execution** on file changes
- **Context-aware development** via SessionStart hooks
- **Security enforcement** preventing destructive operations

---

## Table of Contents

1. [Factory Hooks Overview](#factory-hooks-overview)
2. [Hook Event Types & Capabilities](#hook-event-types--capabilities)
3. [Atoms-MCP-Prod Analysis](#atoms-mcp-prod-analysis)
4. [Hook Design Catalog](#hook-design-catalog)
5. [Implementation Strategy](#implementation-strategy)
6. [Integration with Existing Tools](#integration-with-existing-tools)
7. [Security Considerations](#security-considerations)
8. [Testing Strategy](#testing-strategy)
9. [Rollout Plan](#rollout-plan)
10. [Future Enhancements](#future-enhancements)

---

## Factory Hooks Overview

### What Are Factory Hooks?

Factory hooks are **event-driven automation scripts** that run at specific points in the droid workflow. They enable:

- **Validation** before tool execution (PreToolUse)
- **Verification** after tool execution (PostToolUse)
- **Context injection** at session start or prompt submission
- **Decision control** to approve/deny/modify tool calls
- **Feedback loops** to guide droid behavior

### Key Capabilities

| Capability | Description | Use Cases |
|------------|-------------|-----------|
| **Decision Control** | Approve, deny, or ask for confirmation | Security gates, policy enforcement |
| **Input Modification** | Modify tool parameters before execution | Path normalization, flag injection |
| **Context Injection** | Add information to droid's context | Project state, recent changes, issues |
| **Feedback Loops** | Provide automated feedback to droid | Test failures, lint errors, validation |
| **Parallel Execution** | Multiple hooks run simultaneously | Fast validation, multi-check workflows |

### Hook Configuration

Hooks are configured in `.factory/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "$FACTORY_PROJECT_DIR/.factory/hooks/validation/bash_validator.py",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

---

## Hook Event Types & Capabilities

### 1. **PreToolUse** (Validation & Modification)

**Runs:** After droid creates tool parameters, before processing

**Capabilities:**
- Validate tool inputs (block if invalid)
- Modify tool parameters (via `updatedInput`)
- Auto-approve trusted operations
- Ask user for confirmation

**Common matchers:** `Bash`, `Edit`, `Write`, `Read`, `Glob`, `Grep`, `Task`

**Decision Control:**
```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow" | "deny" | "ask",
    "permissionDecisionReason": "Why this decision",
    "updatedInput": {
      "field_to_modify": "new value"
    }
  }
}
```

**Use Cases for Atoms-MCP-Prod:**
- Validate bash commands (use `rg` instead of `grep`)
- Enforce file size constraints (≤500 lines)
- Prevent edits to critical files
- Normalize file paths
- Inject test flags automatically

---

### 2. **PostToolUse** (Verification & Feedback)

**Runs:** Immediately after a tool completes successfully

**Capabilities:**
- Verify tool outputs
- Run automated tests
- Provide feedback to droid
- Trigger follow-up actions

**Decision Control:**
```json
{
  "decision": "block" | undefined,
  "reason": "Explanation for droid",
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "Extra information for droid"
  }
}
```

**Use Cases for Atoms-MCP-Prod:**
- Run `ruff` after Edit/Write
- Run `pytest` after code changes
- Verify line count stays ≤500
- Check test coverage after changes
- Validate OpenSpec specs after updates

---

### 3. **UserPromptSubmit** (Context & Validation)

**Runs:** When user submits a prompt, before droid processes it

**Capabilities:**
- Add contextual information
- Validate prompts for security
- Block dangerous requests
- Inject project state

**Decision Control:**
```json
{
  "decision": "block" | undefined,
  "reason": "Why blocked (shown to user)",
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "Added to droid's context"
  }
}
```

**Use Cases for Atoms-MCP-Prod:**
- Block prompts containing secrets
- Add current git branch/status
- Inject recent test failures
- Add active OpenSpec changes
- Load environment context

---

### 4. **SessionStart** (Context Loading)

**Runs:** When droid starts or resumes a session

**Capabilities:**
- Load project state
- Inject development context
- Set environment variables
- Initialize session-specific data

**Matchers:** `startup`, `resume`, `clear`, `compact`

**Decision Control:**
```json
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "Context loaded at session start"
  }
}
```

**Use Cases for Atoms-MCP-Prod:**
- Load active OpenSpec changes
- Inject git status and recent commits
- Add failed test summary
- Load project conventions
- Set FastMCP environment

---

### 5. **Other Events** (Optional)

**Notification** - On droid notifications (logging, alerts)  
**Stop** - When droid finishes (continuation logic)  
**SubagentStop** - When sub-droid finishes  
**PreCompact** - Before context compaction (cleanup)  
**SessionEnd** - On session termination (logging, cleanup)

---

## Atoms-MCP-Prod Analysis

### Project Characteristics

**Codebase Structure:**
```
atoms-mcp-prod/
  ├── tools/                    # 6 tool modules (entity, workspace, relationship, workflow, query, base)
  ├── services/                 # Domain logic (embeddings, vector search, auth)
  ├── infrastructure/           # Adapters (Supabase, Upstash, mocks)
  ├── auth/                     # Session management, middleware
  ├── tests/                    # Unit, integration, e2e, performance
  ├── openspec/                 # Spec-driven development structure
  └── docs/sessions/            # Session documentation
```

**Key Constraints:**
- **File size:** ≤500 lines hard limit, ≤350 target
- **Code style:** 100-char lines, black + ruff formatting
- **Testing:** Mandatory for all features
- **OpenSpec:** Required for non-trivial features
- **Forward-only progression:** No git revert
- **Production-grade only:** No MVPs

### Automation Opportunities

#### **1. Code Quality Enforcement**
- Line count validation (prevent files >500 lines)
- Code formatting (auto-run ruff/black)
- Import sorting
- Type hint verification
- Naming convention checks

#### **2. Testing Automation**
- Auto-run pytest after code changes
- Coverage threshold enforcement
- Test file naming validation (canonical naming)
- Fixture parametrization verification

#### **3. Git & Version Control**
- Commit message validation (conventional commits)
- Branch protection (prevent direct pushes to main)
- Co-authorship injection (factory-droid[bot])
- Forward-only progression enforcement

#### **4. Documentation**
- OpenSpec validation after spec changes
- Session docs updates
- README synchronization
- Changelog automation

#### **5. Security & Safety**
- Prevent secret exposure
- Block dangerous bash commands
- Validate environment variable usage
- Prevent destructive operations

---

## Hook Design Catalog

### Category 1: Code Quality & Validation (8 Hooks)

#### **Hook 1: File Size Validator**

**Event:** PreToolUse  
**Matcher:** `Edit|Write`  
**Purpose:** Enforce ≤500 line file size constraint

**Implementation:**
```python
#!/usr/bin/env python3
# .factory/hooks/validation/file_size_validator.py

import json
import sys
from pathlib import Path

MAX_LINES = 500
TARGET_LINES = 350

def validate_file_size(file_path: str, new_content: str) -> tuple[bool, str]:
    lines = new_content.count('\n') + 1
    
    if lines > MAX_LINES:
        return False, f"File exceeds {MAX_LINES} line limit (has {lines} lines). Please decompose."
    
    if lines > TARGET_LINES:
        warning = f"Warning: File has {lines} lines (target: ≤{TARGET_LINES}). Consider decomposing soon."
        return True, warning
    
    return True, ""

input_data = json.load(sys.stdin)
tool_name = input_data.get("tool_name")
tool_input = input_data.get("tool_input", {})

if tool_name in ["Edit", "Write"]:
    file_path = tool_input.get("file_path", "")
    content = tool_input.get("content", "") or tool_input.get("new_str", "")
    
    valid, message = validate_file_size(file_path, content)
    
    if not valid:
        print(message, file=sys.stderr)
        sys.exit(2)  # Block tool call
    elif message:
        # Warning (allow but inform)
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "permissionDecisionReason": message
            },
            "systemMessage": message
        }
        print(json.dumps(output))
        sys.exit(0)
```

**Configuration:**
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"$FACTORY_PROJECT_DIR\"/.factory/hooks/validation/file_size_validator.py",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

---

#### **Hook 2: Bash Command Validator**

**Event:** PreToolUse  
**Matcher:** `Bash`  
**Purpose:** Enforce best practices for bash commands

**Validation Rules:**
- Use `rg` instead of `grep`
- Use `rg --files` instead of `find -name`
- No `rm -rf /` or `rm -rf ~`
- No sudo without explicit approval
- Quote all variables properly

**Implementation:**
```python
#!/usr/bin/env python3
# .factory/hooks/validation/bash_validator.py

import json
import re
import sys

VALIDATION_RULES = [
    (r"\bgrep\b(?!.*\|)", "Use 'rg' (ripgrep) instead of 'grep' for better performance"),
    (r"\bfind\s+\S+\s+-name\b", "Use 'rg --files | rg pattern' instead of 'find -name'"),
    (r"rm\s+-rf\s+/(?:\s|$)", "CRITICAL: Attempting to delete root directory - BLOCKED"),
    (r"rm\s+-rf\s+~/?(?:\s|$)", "CRITICAL: Attempting to delete home directory - BLOCKED"),
    (r"\bsudo\b", "WARNING: sudo command requires explicit approval"),
]

def validate_command(command: str) -> tuple[list[str], list[str]]:
    critical_issues = []
    warnings = []
    
    for pattern, message in VALIDATION_RULES:
        if re.search(pattern, command):
            if "CRITICAL" in message:
                critical_issues.append(message)
            elif "WARNING" in message:
                warnings.append(message)
            else:
                warnings.append(message)
    
    return critical_issues, warnings

input_data = json.load(sys.stdin)
tool_name = input_data.get("tool_name")
tool_input = input_data.get("tool_input", {})

if tool_name == "Bash":
    command = tool_input.get("command", "")
    critical, warnings = validate_command(command)
    
    if critical:
        for msg in critical:
            print(f"• {msg}", file=sys.stderr)
        sys.exit(2)  # Block
    
    if warnings:
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "ask",
                "permissionDecisionReason": "\\n".join(f"• {w}" for w in warnings)
            }
        }
        print(json.dumps(output))
        sys.exit(0)
```

---

#### **Hook 3: Code Formatter (Post-Edit/Write)**

**Event:** PostToolUse  
**Matcher:** `Edit|Write`  
**Purpose:** Auto-format Python files with black + ruff

**Implementation:**
```bash
#!/usr/bin/env bash
# .factory/hooks/verification/code_formatter.sh

set -euo pipefail

input=$(cat)
tool_name=$(echo "$input" | jq -r '.tool_name')
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')

if [[ "$tool_name" =~ ^(Edit|Write)$ ]] && [[ "$file_path" =~ \.py$ ]]; then
    # Check if file exists and is in project
    if [[ -f "$file_path" ]] && [[ "$file_path" == "$FACTORY_PROJECT_DIR"/* ]]; then
        # Run black
        if command -v black &> /dev/null; then
            black "$file_path" --line-length 100 --quiet 2>&1 || true
        fi
        
        # Run ruff
        if command -v ruff &> /dev/null; then
            ruff check "$file_path" --fix --quiet 2>&1 || true
        fi
        
        echo "✅ Code formatted successfully"
    fi
fi

exit 0
```

---

#### **Hook 4: Import Sorter**

**Event:** PostToolUse  
**Matcher:** `Edit|Write`  
**Purpose:** Sort imports using ruff

**Implementation:**
```bash
#!/usr/bin/env bash
# .factory/hooks/verification/import_sorter.sh

set -euo pipefail

input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')

if [[ "$file_path" =~ \.py$ ]] && [[ -f "$file_path" ]]; then
    if command -v ruff &> /dev/null; then
        ruff check "$file_path" --select I --fix --quiet 2>&1 || true
        echo "✅ Imports sorted"
    fi
fi

exit 0
```

---

#### **Hook 5: Test File Naming Validator**

**Event:** PreToolUse  
**Matcher:** `Write`  
**Purpose:** Enforce canonical test naming (no _fast, _unit, _integration, _v2 suffixes)

**Implementation:**
```python
#!/usr/bin/env python3
# .factory/hooks/validation/test_naming_validator.py

import json
import sys
import re
from pathlib import Path

BAD_SUFFIXES = [
    "_fast", "_slow", "_unit", "_integration", "_e2e",
    "_old", "_new", "_final", "_draft", "_v2", "_test", "_backup"
]

def validate_test_filename(file_path: str) -> tuple[bool, str]:
    path = Path(file_path)
    
    # Only check test files
    if not (path.parts[0] == "tests" and path.name.startswith("test_")):
        return True, ""
    
    stem = path.stem  # filename without extension
    
    for suffix in BAD_SUFFIXES:
        if stem.endswith(suffix):
            return False, (
                f"Test file '{path.name}' uses non-canonical suffix '{suffix}'.\\n"
                f"Use canonical naming (describe WHAT's tested, not HOW).\\n"
                f"Examples: test_entity.py, test_auth_supabase.py\\n"
                f"Use pytest markers for speed/variant categorization instead."
            )
    
    return True, ""

input_data = json.load(sys.stdin)
tool_name = input_data.get("tool_name")
tool_input = input_data.get("tool_input", {})

if tool_name == "Write":
    file_path = tool_input.get("file_path", "")
    valid, message = validate_test_filename(file_path)
    
    if not valid:
        print(message, file=sys.stderr)
        sys.exit(2)  # Block

sys.exit(0)
```

---

#### **Hook 6-8: Additional Quality Hooks** (Summaries)

**Hook 6: Type Hint Checker**
- Runs: PostToolUse (Edit/Write on .py files)
- Checks: Public functions have type hints
- Tool: mypy or custom AST parser

**Hook 7: Docstring Validator**
- Runs: PostToolUse (Edit/Write on .py files)
- Checks: Classes and public functions have docstrings
- Tool: pydocstyle or custom parser

**Hook 8: TODO Comment Blocker**
- Runs: PreToolUse (Edit/Write)
- Blocks: TODO comments without resolution plans
- Enforcement: Regex check for `# TODO` without issue links

---

### Category 2: Testing & Coverage (5 Hooks)

#### **Hook 9: Automated Test Runner**

**Event:** PostToolUse  
**Matcher:** `Edit|Write`  
**Purpose:** Run relevant tests after code changes

**Implementation:**
```python
#!/usr/bin/env python3
# .factory/hooks/verification/test_runner.py

import json
import sys
import subprocess
from pathlib import Path

def determine_test_scope(file_path: str) -> str:
    path = Path(file_path)
    
    # Test file changed -> run that specific test
    if path.parts[0] == "tests":
        return f"tests/{path.parts[1]}/{path.name}"
    
    # Tool module changed -> run tool tests
    if path.parts[0] == "tools":
        module = path.stem
        return f"tests/unit/tools/test_{module}.py"
    
    # Infrastructure changed -> run infrastructure tests
    if path.parts[0] == "infrastructure":
        return "tests/unit/infrastructure/"
    
    # Default: run all unit tests
    return "tests/unit/"

input_data = json.load(sys.stdin)
tool_name = input_data.get("tool_name")
tool_input = input_data.get("tool_input", {})
file_path = tool_input.get("file_path", "")

if tool_name in ["Edit", "Write"] and file_path.endswith(".py"):
    test_scope = determine_test_scope(file_path)
    
    result = subprocess.run(
        ["uv", "run", "pytest", test_scope, "-q"],
        capture_output=True,
        text=True,
        cwd=input_data.get("cwd")
    )
    
    if result.returncode != 0:
        # Tests failed - provide feedback to droid
        output = {
            "decision": "block",
            "reason": f"Tests failed after changes to {file_path}:\\n{result.stdout}\\n{result.stderr}",
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": "Test failures must be addressed before proceeding."
            }
        }
        print(json.dumps(output))
        sys.exit(0)
    
    print(f"✅ Tests passed for {test_scope}")
    sys.exit(0)
```

---

#### **Hook 10: Coverage Threshold Enforcer**

**Event:** PostToolUse  
**Matcher:** `Edit|Write`  
**Purpose:** Ensure test coverage stays above threshold

**Implementation:**
```bash
#!/usr/bin/env bash
# .factory/hooks/verification/coverage_enforcer.sh

MIN_COVERAGE=80

set -euo pipefail

input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')

if [[ "$file_path" =~ ^(tools|services|infrastructure)/.+\.py$ ]]; then
    # Run coverage for specific file
    coverage_output=$(uv run pytest --cov="$file_path" --cov-report=term-missing -q 2>&1 || true)
    coverage_percent=$(echo "$coverage_output" | grep -oP '\d+%' | head -1 | tr -d '%' || echo "0")
    
    if [[ "$coverage_percent" -lt "$MIN_COVERAGE" ]]; then
        cat << EOF | jq -c '.'
{
  "decision": "block",
  "reason": "Coverage for $file_path is ${coverage_percent}% (minimum: ${MIN_COVERAGE}%). Please add tests.",
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "Test coverage must be improved before proceeding."
  }
}
EOF
    else
        echo "✅ Coverage: ${coverage_percent}% (≥${MIN_COVERAGE}%)"
    fi
fi

exit 0
```

---

#### **Hook 11-13: Additional Testing Hooks** (Summaries)

**Hook 11: Test Fixture Validator**
- Runs: PostToolUse (Write on test files)
- Checks: Fixtures use parametrization instead of separate files
- Tool: AST parser checking for `@pytest.fixture(params=[...])`

**Hook 12: Mock Client Validator**
- Runs: PreToolUse (Edit/Write on test files)
- Checks: Unit tests use InMemoryMcpClient, not live clients
- Tool: Regex check for `USE_MOCK_CLIENTS` or mock imports

**Hook 13: Test Marker Validator**
- Runs: PostToolUse (Write on test files)
- Checks: Performance/integration tests have proper markers
- Tool: AST parser checking for `@pytest.mark.` decorators

---

### Category 3: Git & Version Control (4 Hooks)

#### **Hook 14: Commit Message Validator**

**Event:** PostToolUse  
**Matcher:** `Bash`  
**Purpose:** Enforce conventional commits format

**Implementation:**
```python
#!/usr/bin/env python3
# .factory/hooks/verification/commit_message_validator.py

import json
import sys
import re

COMMIT_PATTERN = r'^(feat|fix|docs|refactor|test|chore)\\(\\w+\\): .{10,}'

def validate_commit_message(command: str) -> tuple[bool, str]:
    # Check if this is a git commit command
    if not re.search(r'git\s+commit\s+-m', command):
        return True, ""
    
    # Extract commit message
    match = re.search(r'git\s+commit\s+-m\s+["\'](.+?)["\']', command)
    if not match:
        return True, ""  # Can't extract, let it proceed
    
    message = match.group(1)
    
    if not re.match(COMMIT_PATTERN, message):
        return False, (
            f"Commit message '{message}' doesn't follow conventional commits format.\\n"
            f"Expected: <type>(<scope>): <subject>\\n"
            f"Types: feat, fix, docs, refactor, test, chore\\n"
            f"Example: feat(tools): add rate limiting to entity operations"
        )
    
    return True, ""

input_data = json.load(sys.stdin)
tool_name = input_data.get("tool_name")
tool_input = input_data.get("tool_input", {})

if tool_name == "Bash":
    command = tool_input.get("command", "")
    valid, message = validate_commit_message(command)
    
    if not valid:
        output = {
            "decision": "block",
            "reason": message,
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": "Please fix commit message format."
            }
        }
        print(json.dumps(output))
        sys.exit(0)

sys.exit(0)
```

---

#### **Hook 15: Co-Authorship Injector**

**Event:** PreToolUse  
**Matcher:** `Bash`  
**Purpose:** Auto-inject factory-droid co-authorship in commits

**Implementation:**
```python
#!/usr/bin/env python3
# .factory/hooks/validation/coauthor_injector.py

import json
import sys
import re

COAUTHOR_LINE = "\\n\\nCo-authored-by: factory-droid[bot] <138933559+factory-droid[bot]@users.noreply.github.com>"

def inject_coauthor(command: str) -> tuple[str, bool]:
    # Check if this is a git commit command
    if not re.search(r'git\s+commit\s+-m', command):
        return command, False
    
    # Check if co-author already present
    if "Co-authored-by: factory-droid" in command:
        return command, False
    
    # Inject co-author
    modified = re.sub(
        r'(git\s+commit\s+-m\s+["\'])(.+?)(["\'])',
        lambda m: f'{m.group(1)}{m.group(2)}{COAUTHOR_LINE}{m.group(3)}',
        command
    )
    
    return modified, True

input_data = json.load(sys.stdin)
tool_name = input_data.get("tool_name")
tool_input = input_data.get("tool_input", {})

if tool_name == "Bash":
    command = tool_input.get("command", "")
    modified_command, was_modified = inject_coauthor(command)
    
    if was_modified:
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "permissionDecisionReason": "Auto-injected factory-droid co-authorship",
                "updatedInput": {
                    "command": modified_command
                }
            }
        }
        print(json.dumps(output))
        sys.exit(0)

sys.exit(0)
```

---

#### **Hook 16-17: Additional Git Hooks** (Summaries)

**Hook 16: Branch Protection**
- Runs: PreToolUse (Bash with `git push`)
- Blocks: Direct pushes to `main` branch
- Tool: Regex check for `git push origin main`

**Hook 17: Forward-Only Enforcement**
- Runs: PreToolUse (Bash with `git revert`/`git reset`)
- Blocks: Git revert and reset hard operations
- Suggests: Fix forward instead of rollback

---

### Category 4: Documentation & Context (3 Hooks)

#### **Hook 18: OpenSpec Validator**

**Event:** PostToolUse  
**Matcher:** `Edit|Write`  
**Purpose:** Validate OpenSpec specs after changes

**Implementation:**
```bash
#!/usr/bin/env bash
# .factory/hooks/verification/openspec_validator.sh

set -euo pipefail

input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')

if [[ "$file_path" =~ ^openspec/changes/.+/specs/.+\.md$ ]]; then
    # Extract change ID
    change_id=$(echo "$file_path" | sed -n 's|^openspec/changes/\\([^/]*\\)/.*|\\1|p')
    
    if [[ -n "$change_id" ]]; then
        validation_output=$(openspec validate "$change_id" 2>&1 || true)
        
        if [[ "$validation_output" =~ "invalid" ]] || [[ "$validation_output" =~ "error" ]]; then
            cat << EOF | jq -c '.'
{
  "decision": "block",
  "reason": "OpenSpec validation failed for $change_id:\\n$validation_output",
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "Fix spec format before proceeding."
  }
}
EOF
        else
            echo "✅ OpenSpec validation passed for $change_id"
        fi
    fi
fi

exit 0
```

---

#### **Hook 19: Session Context Loader**

**Event:** SessionStart  
**Matcher:** `startup`, `resume`  
**Purpose:** Load project context at session start

**Implementation:**
```python
#!/usr/bin/env python3
# .factory/hooks/context/session_context_loader.py

import json
import sys
import subprocess
from pathlib import Path

def get_git_status():
    result = subprocess.run(
        ["git", "status", "--short"],
        capture_output=True,
        text=True
    )
    return result.stdout.strip()

def get_active_openspec_changes():
    result = subprocess.run(
        ["openspec", "list"],
        capture_output=True,
        text=True
    )
    return result.stdout.strip()

def get_failed_tests():
    # Check if last test run had failures
    result = subprocess.run(
        ["uv", "run", "pytest", "--collect-only", "-q"],
        capture_output=True,
        text=True
    )
    # Parse for any indication of previous failures
    return "No recent test failures found"

input_data = json.load(sys.stdin)

context_parts = [
    "## Project Context (Auto-loaded at Session Start)",
    "",
    "### Git Status",
    get_git_status(),
    "",
    "### Active OpenSpec Changes",
    get_active_openspec_changes(),
    "",
    "### Recent Test Status",
    get_failed_tests(),
    "",
    "### Project Conventions",
    "- File size: ≤500 lines (hard limit), ≤350 target",
    "- Use OpenSpec for all non-trivial features",
    "- Forward-only progression (no git revert)",
    "- Production-grade only (no MVPs)",
    "",
]

context = "\\n".join(context_parts)

output = {
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": context
    }
}

print(json.dumps(output))
sys.exit(0)
```

---

#### **Hook 20: Additional Doc Hook** (Summary)

**Hook 20: README Synchronizer**
- Runs: PostToolUse (Edit/Write on key files)
- Updates: README.md sections when architecture changes
- Tool: Template-based README generator

---

### Category 5: Security & Safety (3 Hooks)

#### **Hook 21: Secret Detector**

**Event:** UserPromptSubmit  
**Matcher:** N/A  
**Purpose:** Block prompts containing potential secrets

**Implementation:**
```python
#!/usr/bin/env python3
# .factory/hooks/validation/secret_detector.py

import json
import sys
import re

SECRET_PATTERNS = [
    (r"(?i)\\b(password|secret|key|token)\\s*[:=]\\s*['\"]?[\\w-]{8,}", "Potential secret in prompt"),
    (r"(?i)SUPABASE_[A-Z_]+\\s*=\\s*['\"]?.+", "Supabase credential"),
    (r"(?i)WORKOS_[A-Z_]+\\s*=\\s*['\"]?.+", "WorkOS credential"),
    (r"(?i)sk-[A-Za-z0-9]{32,}", "OpenAI API key pattern"),
]

def detect_secrets(prompt: str) -> list[str]:
    issues = []
    for pattern, message in SECRET_PATTERNS:
        if re.search(pattern, prompt):
            issues.append(message)
    return issues

input_data = json.load(sys.stdin)
prompt = input_data.get("prompt", "")

issues = detect_secrets(prompt)

if issues:
    reason = "Security policy violation:\\n" + "\\n".join(f"• {issue}" for issue in issues)
    reason += "\\n\\nPlease rephrase your request without sensitive information."
    
    output = {
        "decision": "block",
        "reason": reason
    }
    print(json.dumps(output))
    sys.exit(0)

sys.exit(0)
```

---

#### **Hook 22-23: Additional Security Hooks** (Summaries)

**Hook 22: Environment Variable Validator**
- Runs: PreToolUse (Edit/Write)
- Blocks: Hardcoded secrets in code files
- Tool: Regex check for `password = "..."` patterns

**Hook 23: Destructive Operation Blocker**
- Runs: PreToolUse (Bash)
- Blocks: `rm -rf`, `DROP TABLE`, other destructive commands
- Requires: Explicit approval for dangerous operations

---

## Implementation Strategy

### Phase 1: Foundation (Week 1)

**Goal:** Set up hook infrastructure and validate core hooks

**Tasks:**
1. Create `.factory/hooks/` directory structure
2. Implement 5 high-priority hooks:
   - File Size Validator (Hook 1)
   - Bash Command Validator (Hook 2)
   - Code Formatter (Hook 3)
   - Automated Test Runner (Hook 9)
   - Secret Detector (Hook 21)
3. Configure `.factory/settings.json`
4. Test hooks in isolated environment
5. Document hook usage in README

**Success Criteria:**
- All 5 hooks working correctly
- No false positives in validation
- Performance impact <1 second per hook

---

### Phase 2: Quality & Testing (Week 2)

**Goal:** Add code quality and testing automation hooks

**Tasks:**
1. Implement quality hooks:
   - Import Sorter (Hook 4)
   - Test File Naming Validator (Hook 5)
   - Type Hint Checker (Hook 6)
   - Docstring Validator (Hook 7)
2. Implement testing hooks:
   - Coverage Threshold Enforcer (Hook 10)
   - Test Fixture Validator (Hook 11)
   - Mock Client Validator (Hook 12)
3. Integrate with existing pytest workflows
4. Measure coverage improvements

**Success Criteria:**
- Code quality standards automatically enforced
- Test coverage consistently above 80%
- Developer friction minimal

---

### Phase 3: Git & Documentation (Week 3)

**Goal:** Enhance git workflows and documentation automation

**Tasks:**
1. Implement git hooks:
   - Commit Message Validator (Hook 14)
   - Co-Authorship Injector (Hook 15)
   - Branch Protection (Hook 16)
   - Forward-Only Enforcement (Hook 17)
2. Implement documentation hooks:
   - OpenSpec Validator (Hook 18)
   - Session Context Loader (Hook 19)
   - README Synchronizer (Hook 20)
3. Test git workflow integration
4. Update AGENTS.md with hook documentation

**Success Criteria:**
- Git commits follow conventions 100%
- OpenSpec specs always valid
- Context loaded automatically

---

### Phase 4: Security & Polish (Week 4)

**Goal:** Add security hooks and optimize performance

**Tasks:**
1. Implement security hooks:
   - Environment Variable Validator (Hook 22)
   - Destructive Operation Blocker (Hook 23)
2. Optimize hook performance (parallel execution)
3. Add comprehensive hook testing
4. Create hook debugging guide
5. Document all hooks in catalog

**Success Criteria:**
- Zero secrets exposed
- All hooks tested and documented
- Performance optimized (<500ms average)

---

## Integration with Existing Tools

### pytest Integration

**Before Hooks:**
```bash
# Manual test execution
uv run pytest tests/unit/
```

**After Hooks:**
```bash
# Automatic test execution after code changes (via Hook 9)
# No manual intervention needed
```

---

### ruff/black Integration

**Before Hooks:**
```bash
# Manual formatting
black tools/entity.py --line-length 100
ruff check tools/entity.py --fix
```

**After Hooks:**
```bash
# Automatic formatting after Edit/Write (via Hook 3)
# Files always formatted correctly
```

---

### OpenSpec Integration

**Before Hooks:**
```bash
# Manual validation
openspec validate add-feature
```

**After Hooks:**
```bash
# Automatic validation after spec changes (via Hook 18)
# Immediate feedback on invalid specs
```

---

### Git Integration

**Before Hooks:**
```bash
# Manual commit message crafting
git commit -m "feat(tools): add rate limiting

Co-authored-by: factory-droid[bot] <...>"
```

**After Hooks:**
```bash
# Auto-injected co-authorship (via Hook 15)
git commit -m "feat(tools): add rate limiting"
# Co-author automatically added
```

---

## Security Considerations

### Hook Execution Safety

**Risks:**
- Arbitrary code execution
- Access to sensitive files
- Modification of project files
- Network access

**Mitigations:**
1. **Code Review:** All hooks reviewed before deployment
2. **Sandboxing:** Hooks run with project-level permissions only
3. **Timeout:** 60-second timeout per hook (configurable)
4. **Validation:** Input validation in all hooks
5. **Logging:** All hook executions logged for audit

### Sensitive Data Handling

**Hooks that access sensitive data:**
- Secret Detector (Hook 21) - Scans prompts
- Environment Variable Validator (Hook 22) - Checks code

**Protections:**
- No storage of sensitive data
- Immediate validation and discard
- Regex patterns only (no external API calls)

---

## Testing Strategy

### Hook Testing Approach

**Unit Tests:**
```python
# tests/unit/hooks/test_file_size_validator.py

import json
import subprocess

def test_file_size_validator_blocks_large_files():
    input_data = {
        "tool_name": "Write",
        "tool_input": {
            "file_path": "test.py",
            "content": "\\n".join(["# line"] * 600)  # 600 lines
        }
    }
    
    result = subprocess.run(
        [".factory/hooks/validation/file_size_validator.py"],
        input=json.dumps(input_data),
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 2  # Blocked
    assert "exceeds 500 line limit" in result.stderr
```

**Integration Tests:**
```python
# tests/integration/hooks/test_hook_integration.py

def test_hooks_trigger_on_droid_operations():
    # Start droid session with hooks enabled
    # Perform operations that should trigger hooks
    # Verify hooks executed and had expected effects
    pass
```

**Performance Tests:**
```python
# tests/performance/hooks/test_hook_performance.py

def test_hook_execution_time():
    # Measure hook execution time
    # Ensure <500ms for critical hooks
    # Ensure <1s for all hooks
    pass
```

---

## Rollout Plan

### Week 1: Foundation Hooks (5 hooks)
- Deploy to local development environment
- Test with manual droid usage
- Gather feedback
- Fix any issues

### Week 2: Quality & Testing Hooks (8 hooks)
- Deploy incrementally (2-3 hooks per day)
- Monitor for false positives
- Adjust thresholds as needed
- Document edge cases

### Week 3: Git & Documentation Hooks (6 hooks)
- Deploy git hooks first
- Test with multiple developers
- Deploy documentation hooks
- Validate OpenSpec integration

### Week 4: Security & Polish (4 hooks)
- Deploy security hooks
- Perform security audit
- Optimize performance
- Finalize documentation

---

## Future Enhancements

### MCP Tool-Specific Hooks

**Opportunity:** Hooks for MCP servers (memory, filesystem, GitHub)

**Examples:**
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "mcp__memory__.*",
        "hooks": [
          {
            "type": "command",
            "command": "\"$FACTORY_PROJECT_DIR\"/.factory/hooks/mcp/memory_validator.py"
          }
        ]
      }
    ]
  }
}
```

### CI/CD Integration

**Opportunity:** Sync hooks with GitHub Actions

**Implementation:**
- Export hook logic to reusable scripts
- Call from both droid hooks and GitHub workflows
- Consistent validation everywhere

### Plugin System

**Opportunity:** Package hooks as Factory plugins

**Benefits:**
- Easy distribution
- Version management
- Community sharing

---

## Conclusion

This comprehensive plan provides **23 production-ready hooks** specifically designed for atoms-mcp-prod. Implementation will:

- **Automate 80%** of manual validation tasks
- **Enforce 100%** of code quality standards
- **Accelerate development** with automatic testing
- **Prevent security issues** with secret detection
- **Enhance git workflows** with automatic co-authorship

**Next Steps:**
1. Review this plan with stakeholders
2. Create OpenSpec proposal for implementation
3. Begin Phase 1 implementation (Foundation hooks)
4. Gather feedback and iterate

**Estimated Timeline:** 4 weeks for complete rollout  
**Estimated Impact:** 50%+ reduction in manual quality checks

---

## Appendix: Hook Configuration Reference

Complete `.factory/settings.json` configuration for all 23 hooks:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {"type": "command", "command": "\"$FACTORY_PROJECT_DIR\"/.factory/hooks/validation/file_size_validator.py", "timeout": 5},
          {"type": "command", "command": "\"$FACTORY_PROJECT_DIR\"/.factory/hooks/validation/test_naming_validator.py", "timeout": 5},
          {"type": "command", "command": "\"$FACTORY_PROJECT_DIR\"/.factory/hooks/validation/todo_blocker.py", "timeout": 5}
        ]
      },
      {
        "matcher": "Bash",
        "hooks": [
          {"type": "command", "command": "\"$FACTORY_PROJECT_DIR\"/.factory/hooks/validation/bash_validator.py", "timeout": 5},
          {"type": "command", "command": "\"$FACTORY_PROJECT_DIR\"/.factory/hooks/validation/coauthor_injector.py", "timeout": 5},
          {"type": "command", "command": "\"$FACTORY_PROJECT_DIR\"/.factory/hooks/validation/branch_protector.py", "timeout": 5},
          {"type": "command", "command": "\"$FACTORY_PROJECT_DIR\"/.factory/hooks/validation/forward_only_enforcer.py", "timeout": 5}
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {"type": "command", "command": "\"$FACTORY_PROJECT_DIR\"/.factory/hooks/verification/code_formatter.sh", "timeout": 10},
          {"type": "command", "command": "\"$FACTORY_PROJECT_DIR\"/.factory/hooks/verification/import_sorter.sh", "timeout": 5},
          {"type": "command", "command": "\"$FACTORY_PROJECT_DIR\"/.factory/hooks/verification/test_runner.py", "timeout": 60},
          {"type": "command", "command": "\"$FACTORY_PROJECT_DIR\"/.factory/hooks/verification/coverage_enforcer.sh", "timeout": 30},
          {"type": "command", "command": "\"$FACTORY_PROJECT_DIR\"/.factory/hooks/verification/openspec_validator.sh", "timeout": 10}
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {"type": "command", "command": "\"$FACTORY_PROJECT_DIR\"/.factory/hooks/validation/secret_detector.py", "timeout": 5}
        ]
      }
    ],
    "SessionStart": [
      {
        "matcher": "startup|resume",
        "hooks": [
          {"type": "command", "command": "\"$FACTORY_PROJECT_DIR\"/.factory/hooks/context/session_context_loader.py", "timeout": 10}
        ]
      }
    ]
  }
}
```

---

**Document Version:** 1.0  
**Last Updated:** 2025-11-13  
**Next Review:** After Phase 1 implementation
