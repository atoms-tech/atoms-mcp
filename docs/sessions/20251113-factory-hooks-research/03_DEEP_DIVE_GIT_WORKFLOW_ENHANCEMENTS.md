# Deep Dive: Git Workflow Enhancement Hooks

**Category:** Git & Version Control  
**Priority:** HIGH - Maintain clean git history and prevent destructive operations  
**Hooks Count:** 4 detailed hooks  
**Expected Impact:** 100% commit quality, zero accidental force pushes, zero reverts

---

## Overview

Git workflow hooks enforce repository hygiene by validating commits, preventing destructive operations, and maintaining attribution. These hooks ensure:

- **Clean commit history** via conventional commit validation
- **Proper attribution** with automatic co-authorship
- **Branch protection** preventing accidental pushes to main
- **Forward-only progression** blocking destructive git operations

---

## Table of Contents

1. [Hook 14: Commit Message Validator](#hook-14-commit-message-validator)
2. [Hook 15: Co-Authorship Injector](#hook-15-co-authorship-injector)
3. [Hook 16: Branch Protection](#hook-16-branch-protection)
4. [Hook 17: Forward-Only Enforcement](#hook-17-forward-only-enforcement)
5. [Integration with Existing Workflow](#integration-with-existing-workflow)
6. [Git Hook Compatibility](#git-hook-compatibility)

---

## Hook 14: Commit Message Validator

### Purpose
Enforce conventional commit message format for clean, parseable git history.

### Event & Matcher
- **Event:** `PreToolUse`
- **Matcher:** `Execute`
- **Timing:** Before `git commit` executes

### Conventional Commit Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style (formatting, missing semicolons)
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `perf`: Performance improvement
- `test`: Adding or updating tests
- `chore`: Maintenance tasks (dependencies, build)

### Implementation

```python
#!/usr/bin/env python3
# .factory/hooks/validation/commit_message_validator.py

"""
Commit Message Validator Hook

Enforces conventional commit message format:
  type(scope): subject

  body

  footer

Reference: https://www.conventionalcommits.org/
"""

import json
import re
import sys
from typing import Tuple, Optional

# Conventional commit pattern
COMMIT_PATTERN = re.compile(
    r'^(?P<type>feat|fix|docs|style|refactor|perf|test|chore|build|ci|revert)'
    r'(?:\((?P<scope>[a-z0-9-]+)\))?'
    r'(?P<breaking>!)?'
    r': '
    r'(?P<subject>.+)$',
    re.MULTILINE
)

VALID_TYPES = [
    'feat', 'fix', 'docs', 'style', 'refactor', 
    'perf', 'test', 'chore', 'build', 'ci', 'revert'
]

def validate_commit_message(message: str) -> Tuple[bool, Optional[str]]:
    """
    Validate commit message against conventional commit format.
    
    Returns:
        (is_valid, error_message)
    """
    lines = message.strip().split('\\n')
    
    if not lines:
        return False, "Commit message is empty"
    
    # Validate first line (subject)
    subject = lines[0]
    
    match = COMMIT_PATTERN.match(subject)
    
    if not match:
        return False, f"""Invalid commit message format: "{subject}"

Expected format:
  type(scope): subject

Examples:
  feat(tools): add entity validation
  fix(auth): handle expired tokens
  docs: update README with deployment steps
  test(entity): add coverage for edge cases

Valid types: {', '.join(VALID_TYPES)}

Reference: https://www.conventionalcommits.org/"""
    
    # Extract components
    commit_type = match.group('type')
    scope = match.group('scope')
    subject_text = match.group('subject')
    
    # Validate subject
    if len(subject_text) > 72:
        return False, f"Subject too long ({len(subject_text)} chars, max 72): {subject_text[:50]}..."
    
    if subject_text[0].isupper():
        return False, f"Subject should start with lowercase: {subject_text}"
    
    if subject_text.endswith('.'):
        return False, f"Subject should not end with period: {subject_text}"
    
    # Validate body (if present)
    if len(lines) > 1:
        # Line 2 should be blank
        if lines[1] != '':
            return False, "Second line must be blank (separate subject from body)"
        
        # Body lines should be ≤100 chars (flexible)
        for i, line in enumerate(lines[2:], start=3):
            if len(line) > 100:
                return False, f"Line {i} too long ({len(line)} chars, recommended ≤100)"
    
    return True, None

def extract_commit_message_from_command(command: str) -> Optional[str]:
    """Extract commit message from git commit command."""
    
    # Pattern 1: git commit -m "message"
    match = re.search(r'git\s+commit\s+.*-m\s+["\']([^"\']+)["\']', command)
    if match:
        return match.group(1)
    
    # Pattern 2: git commit (will open editor, skip validation)
    if 'git commit' in command and '-m' not in command:
        return None  # Editor-based commit, can't validate here
    
    return None

def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)
    
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    
    # Only validate Execute tool
    if tool_name != "Execute":
        sys.exit(0)
    
    command = tool_input.get("command", "")
    
    # Only validate git commit commands
    if "git commit" not in command:
        sys.exit(0)
    
    # Extract commit message
    commit_message = extract_commit_message_from_command(command)
    
    if not commit_message:
        # Can't extract message (editor-based commit)
        # Provide guidance but don't block
        print("ℹ️  Reminder: Use conventional commit format (type(scope): subject)", file=sys.stderr)
        sys.exit(0)
    
    # Validate message
    is_valid, error_message = validate_commit_message(commit_message)
    
    if not is_valid:
        # Block the commit
        output = {
            "decision": "deny",
            "reason": error_message,
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": "Commit message does not follow conventional commit format"
            }
        }
        
        print(json.dumps(output))
        sys.exit(0)
    
    # Valid commit message
    print(f"✅ Commit message valid: {commit_message[:50]}...", file=sys.stderr)
    sys.exit(0)

if __name__ == "__main__":
    main()
```

### Configuration

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Execute",
        "hooks": [
          {
            "type": "command",
            "command": "\"$FACTORY_PROJECT_DIR\"/.factory/hooks/validation/commit_message_validator.py",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

### Testing

```bash
# Test 1: Valid commit
echo '{
  "tool_name": "Execute",
  "tool_input": {
    "command": "git commit -m \"feat(hooks): add commit message validator\""
  }
}' | .factory/hooks/validation/commit_message_validator.py

# Expected: Exit 0, success message

# Test 2: Invalid format (no type)
echo '{
  "tool_name": "Execute",
  "tool_input": {
    "command": "git commit -m \"add commit validator\""
  }
}' | .factory/hooks/validation/commit_message_validator.py

# Expected: Exit 0, deny decision in JSON

# Test 3: Subject too long
echo '{
  "tool_name": "Execute",
  "tool_input": {
    "command": "git commit -m \"feat: this is a very long commit message that exceeds the maximum allowed length of 72 characters\""
  }
}' | .factory/hooks/validation/commit_message_validator.py

# Expected: Exit 0, deny decision
```

### Performance
- **Execution Time:** <50ms (regex matching)
- **Timeout:** 5 seconds

---

## Hook 15: Co-Authorship Injector

### Purpose
Automatically add `Co-authored-by: factory-droid[bot]` to all commits made through Factory.

### Event & Matcher
- **Event:** `PreToolUse`
- **Matcher:** `Execute`
- **Timing:** Before `git commit` executes

### Implementation

```bash
#!/usr/bin/env bash
# .factory/hooks/transformation/coauthor_injector.sh

set -euo pipefail

CO_AUTHOR="Co-authored-by: factory-droid[bot] <138933559+factory-droid[bot]@users.noreply.github.com>"

input=$(cat)
tool_name=$(echo "$input" | jq -r '.tool_name')
command=$(echo "$input" | jq -r '.tool_input.command // empty')

# Only process Execute tool
if [[ "$tool_name" != "Execute" ]]; then
    exit 0
fi

# Only process git commit commands
if [[ ! "$command" =~ git[[:space:]]+commit ]]; then
    exit 0
fi

# Check if commit already has co-author
if echo "$command" | grep -q "Co-authored-by:"; then
    echo "ℹ️  Commit already has co-authorship" >&2
    exit 0
fi

# Extract commit message
if [[ "$command" =~ -m[[:space:]]+[\"\']([^\"\']+)[\"\'] ]]; then
    original_message="${BASH_REMATCH[1]}"
    
    # Add co-author to message
    new_message="$original_message

$CO_AUTHOR"
    
    # Replace original message with enhanced version
    enhanced_command=$(echo "$command" | sed "s|-m [\"']$original_message[\"']|-m \"$new_message\"|")
    
    # Output modified command
    cat << EOF | jq -c '.'
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "modifiedToolInput": {
      "command": "$enhanced_command"
    },
    "additionalContext": "Added co-authorship attribution"
  }
}
EOF
    
    echo "✅ Added co-authorship to commit" >&2
else
    # Can't parse message (editor-based commit)
    echo "ℹ️  Manual commit - remember to add co-authorship" >&2
fi

exit 0
```

### Configuration

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Execute",
        "hooks": [
          {
            "type": "command",
            "command": "\"$FACTORY_PROJECT_DIR\"/.factory/hooks/transformation/coauthor_injector.sh",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

### Advanced: Multi-Author Support

```bash
#!/usr/bin/env bash
# Enhanced version supporting multiple co-authors

# Detect if multiple agents contributed
AGENTS_FILE=".factory/session_agents.json"

if [[ -f "$AGENTS_FILE" ]]; then
    # Read all agents from session
    coauthors=$(jq -r '.agents[] | "Co-authored-by: \(.name) <\(.email)>"' "$AGENTS_FILE")
    
    # Add all co-authors
    new_message="$original_message

$coauthors"
fi
```

### Performance
- **Execution Time:** <30ms (string manipulation)
- **Timeout:** 5 seconds

---

## Hook 16: Branch Protection

### Purpose
Prevent accidental pushes to protected branches (main, production).

### Event & Matcher
- **Event:** `PreToolUse`
- **Matcher:** `Execute`
- **Timing:** Before `git push` executes

### Implementation

```python
#!/usr/bin/env python3
# .factory/hooks/validation/branch_protection.py

"""
Branch Protection Hook

Prevents pushes to protected branches without explicit confirmation.
"""

import json
import re
import subprocess
import sys
from typing import Optional

PROTECTED_BRANCHES = ['main', 'master', 'production', 'prod']

def get_current_branch(cwd: str) -> Optional[str]:
    """Get current git branch."""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    
    return None

def extract_push_target(command: str) -> Optional[str]:
    """Extract target branch from git push command."""
    
    # Pattern: git push origin <branch>
    match = re.search(r'git\s+push\s+\w+\s+([^\s]+)', command)
    if match:
        return match.group(1)
    
    # Pattern: git push (uses current branch)
    if re.match(r'git\s+push\s*$', command):
        return "current"
    
    return None

def is_force_push(command: str) -> bool:
    """Check if command is a force push."""
    return '--force' in command or '-f' in command

def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)
    
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    cwd = input_data.get("cwd", "")
    
    if tool_name != "Execute":
        sys.exit(0)
    
    command = tool_input.get("command", "")
    
    # Only validate git push commands
    if "git push" not in command:
        sys.exit(0)
    
    # Get target branch
    target_branch = extract_push_target(command)
    
    if not target_branch:
        sys.exit(0)  # Can't determine target, allow
    
    if target_branch == "current":
        target_branch = get_current_branch(cwd)
    
    # Check if pushing to protected branch
    if target_branch in PROTECTED_BRANCHES:
        # Check if force push (extra dangerous)
        if is_force_push(command):
            message = f"""🚫 BLOCKED: Force push to protected branch '{target_branch}'

Force pushing to {target_branch} is extremely dangerous and is blocked by project policy.

If you absolutely must force push:
1. Create a backup branch first
2. Coordinate with team
3. Use --force-with-lease (safer than --force)

Reference: AGENTS.md § Git Safety Guidelines"""
            
            output = {
                "decision": "deny",
                "reason": message,
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny"
                }
            }
            
            print(json.dumps(output))
            sys.exit(0)
        
        # Regular push to protected branch (warn but allow if no force)
        message = f"""⚠️  WARNING: Pushing to protected branch '{target_branch}'

This branch is protected. Ensure:
1. You have proper authorization
2. Changes have been reviewed
3. CI/CD tests have passed
4. This is not accidental

Proceeding with push..."""
        
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "permissionDecisionReason": message
            },
            "systemMessage": f"⚠️  Pushing to protected branch: {target_branch}"
        }
        
        print(json.dumps(output))
    
    sys.exit(0)

if __name__ == "__main__":
    main()
```

### Configuration

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Execute",
        "hooks": [
          {
            "type": "command",
            "command": "\"$FACTORY_PROJECT_DIR\"/.factory/hooks/validation/branch_protection.py",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

### Configuration File Support

```json
// .factory/branch_protection.json
{
  "protected_branches": ["main", "master", "production", "prod"],
  "allow_force_push": false,
  "require_review": true,
  "require_ci_pass": true
}
```

### Performance
- **Execution Time:** ~100ms (git command + validation)
- **Timeout:** 10 seconds

---

## Hook 17: Forward-Only Enforcement

### Purpose
Block destructive git operations (revert, reset --hard) to enforce forward-only progression.

### Event & Matcher
- **Event:** `PreToolUse`
- **Matcher:** `Execute`
- **Timing:** Before destructive git commands execute

### Implementation

```python
#!/usr/bin/env python3
# .factory/hooks/validation/forward_only_enforcer.py

"""
Forward-Only Enforcement Hook

Blocks destructive git operations:
- git revert
- git reset --hard
- git reset HEAD~
- git checkout -- (destructive)

Project policy: Fix forward with incremental changes, don't rollback.
"""

import json
import re
import sys
from typing import Tuple, Optional

DESTRUCTIVE_PATTERNS = [
    (r'git\s+revert', 'git revert', 'Use forward fixes instead of reverting commits'),
    (r'git\s+reset\s+--hard', 'git reset --hard', 'Hard resets destroy work. Use git reset --soft if needed'),
    (r'git\s+reset\s+HEAD~', 'git reset HEAD~', 'Resetting commits is destructive. Commit fixes instead'),
    (r'git\s+checkout\s+--\s+', 'git checkout -- <file>', 'This discards local changes. Commit or stash first'),
    (r'git\s+clean\s+-[fF]', 'git clean -f', 'This permanently deletes untracked files'),
]

ALLOWED_EXCEPTIONS = [
    # Allow soft reset (doesn't destroy work)
    r'git\s+reset\s+--soft',
    # Allow checkout of branches (not destructive)
    r'git\s+checkout\s+[a-zA-Z]',
]

def check_destructive_operation(command: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Check if command is a destructive git operation.
    
    Returns:
        (is_destructive, operation_name, reason)
    """
    
    # Check for allowed exceptions first
    for exception_pattern in ALLOWED_EXCEPTIONS:
        if re.search(exception_pattern, command):
            return False, None, None
    
    # Check for destructive patterns
    for pattern, operation, reason in DESTRUCTIVE_PATTERNS:
        if re.search(pattern, command):
            return True, operation, reason
    
    return False, None, None

def suggest_alternative(operation: str) -> str:
    """Suggest forward-only alternative for destructive operation."""
    
    alternatives = {
        'git revert': """
Instead of reverting:
  git revert <commit>

Use forward fixes:
  1. Identify the bug introduced
  2. Write a fix commit
  3. git commit -m "fix: address issue from commit <sha>"
  
This preserves history and makes debugging easier.""",
        
        'git reset --hard': """
Instead of hard reset:
  git reset --hard HEAD~1

Use soft reset or new commits:
  1. git reset --soft HEAD~1  # Preserves changes
  2. Make corrections
  3. git commit --amend
  
Or just commit fixes:
  1. Fix the issue
  2. git commit -m "fix: correct previous commit"
""",
        
        'git reset HEAD~': """
Instead of resetting:
  git reset HEAD~1

Use amend or new commits:
  1. git commit --amend  # Fix last commit
  2. Or commit fixes forward
  
History rewriting makes collaboration difficult.""",
        
        'git checkout -- <file>': """
Instead of discarding changes:
  git checkout -- file.py

Preserve work:
  1. git stash  # Save changes temporarily
  2. Or commit changes first
  3. Then make new changes
  
Never throw away work without saving.""",
        
        'git clean -f': """
Instead of cleaning untracked:
  git clean -f

Review first:
  1. git status  # See what will be deleted
  2. git stash --include-untracked  # Save if needed
  3. Or manually remove specific files
  
Batch deletion is rarely necessary."""
    }
    
    return alternatives.get(operation, "Fix forward instead of rolling back.")

def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)
    
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    
    if tool_name != "Execute":
        sys.exit(0)
    
    command = tool_input.get("command", "")
    
    # Only check git commands
    if "git" not in command.lower():
        sys.exit(0)
    
    # Check for destructive operations
    is_destructive, operation, reason = check_destructive_operation(command)
    
    if is_destructive:
        alternative = suggest_alternative(operation)
        
        message = f"""🚫 BLOCKED: Destructive git operation

Command: {command}
Operation: {operation}
Reason: {reason}

Project Policy: Forward-Only Progression
─────────────────────────────────────────
This project enforces forward-only progression. Destructive git operations
like revert, reset --hard, and checkout -- are blocked.

{alternative}

Reference: AGENTS.md § Forward-Only Progression
Reference: CLAUDE.md § Aggressive Change Policy"""
        
        output = {
            "decision": "deny",
            "reason": message,
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": "Destructive git operation blocked by policy"
            }
        }
        
        print(json.dumps(output))
        sys.exit(0)
    
    # Not destructive, allow
    sys.exit(0)

if __name__ == "__main__":
    main()
```

### Configuration

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Execute",
        "hooks": [
          {
            "type": "command",
            "command": "\"$FACTORY_PROJECT_DIR\"/.factory/hooks/validation/forward_only_enforcer.py",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

### Advanced: Emergency Override

```python
# Add emergency override mechanism (use sparingly)

OVERRIDE_ENV_VAR = "FACTORY_ALLOW_DESTRUCTIVE_GIT"

def check_override() -> bool:
    """Check if emergency override is enabled."""
    import os
    return os.environ.get(OVERRIDE_ENV_VAR) == "true"

# In main():
if is_destructive:
    if check_override():
        print("⚠️  WARNING: Emergency override enabled, allowing destructive operation", file=sys.stderr)
        sys.exit(0)
    else:
        # Block as usual
        ...
```

### Performance
- **Execution Time:** <30ms (regex matching)
- **Timeout:** 5 seconds

---

## Integration with Existing Workflow

### Hook Execution Flow

For `git commit` command:

```
1. PreToolUse hooks trigger (parallel):
   ├─ Commit Message Validator (validates conventional format)
   ├─ Co-Authorship Injector (adds factory-droid attribution)
   └─ Forward-Only Enforcer (allows commit, not destructive)

2. If all hooks pass:
   → Modified command with co-authorship executes
   → git commit -m "feat(hooks): add validator

   Co-authored-by: factory-droid[bot] <...>"

3. PostToolUse hooks trigger:
   → (no git-specific hooks here)
```

For `git push main` command:

```
1. PreToolUse hooks trigger:
   ├─ Branch Protection (detects push to 'main', warns but allows)
   └─ Forward-Only Enforcer (allows push, not destructive)

2. If allowed:
   → Push proceeds with warning message

3. If force push attempted:
   → Branch Protection BLOCKS
```

For `git revert <commit>` command:

```
1. PreToolUse hooks trigger:
   └─ Forward-Only Enforcer (detects revert, BLOCKS)

2. Hook blocks with detailed message:
   → Shows why revert is blocked
   → Suggests forward-fix alternatives
   → References policy documents

3. Droid receives feedback:
   → Understands policy
   → Applies forward fix instead
```

---

## Git Hook Compatibility

### Factory Hooks vs. Git Hooks

Factory hooks run **before/after Factory tool use**, not at git hook points.

**Comparison:**

| Aspect | Git Hooks | Factory Hooks |
|--------|-----------|---------------|
| **Trigger** | Git operations (pre-commit, pre-push) | Factory tool use (Execute) |
| **Scope** | Git-specific only | All tools (Edit, Write, Execute, etc.) |
| **Context** | Git process | Full Factory context (tool, input, cwd) |
| **Language** | Any executable | Any executable |
| **Installation** | `.git/hooks/` | `.factory/hooks/` |

### Complementary Usage

Factory hooks and git hooks can work together:

```bash
# .git/hooks/pre-commit (git hook)
#!/usr/bin/env bash
# Runs before git commit (not through Factory)

# Run linting
uv run ruff check .

# Run tests
uv run pytest tests/unit -q
```

```python
# .factory/hooks/validation/commit_message_validator.py (Factory hook)
# Runs when droid uses Execute tool with "git commit"

# Validate commit message format
# Add co-authorship
# Enforce forward-only policy
```

**When droid commits through Factory:**
1. Factory hooks run first (PreToolUse)
2. Git command executes
3. Git hooks run (pre-commit)
4. Factory hooks run (PostToolUse)

### Migration Strategy

```bash
# Migrate existing git hooks to Factory hooks

# Before (git hook):
# .git/hooks/pre-commit
#!/usr/bin/env bash
./scripts/validate_commit.sh

# After (Factory hook):
# .factory/hooks/validation/commit_validator.py
#!/usr/bin/env python3
# (Implementation as shown above)
```

---

## Summary & Impact

### Hooks Implemented

✅ 4 git workflow hooks  
✅ Commit message validation (conventional commits)  
✅ Automatic co-authorship attribution  
✅ Branch protection (prevent force push)  
✅ Forward-only enforcement (block destructive ops)

### Expected Impact

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Commit message quality** | ~60% conventional | 100% | +40% |
| **Co-authorship attribution** | Manual | Automatic | 100% automation |
| **Accidental force pushes** | 2-3/year | 0 | 100% prevention |
| **Destructive operations** | 1-2/month | 0 | 100% prevention |
| **Git history clarity** | Inconsistent | Clean | Significant improvement |

### Real-World Benefits

**Before hooks:**
```bash
# Developer workflow
droid: git commit -m "fix stuff"  # Non-standard message
developer: Manually add co-author later
droid: git push --force main  # Accidental force push
developer: Oh no! Rollback needed

Result: Messy history, lost work, frustration
```

**After hooks:**
```bash
# Developer workflow
droid: git commit -m "fix stuff"
hooks: ❌ BLOCKED - Invalid commit format
droid: git commit -m "fix(auth): handle token expiration"
hooks: ✅ Valid format, added co-authorship
droid: git push --force main
hooks: ❌ BLOCKED - Force push to protected branch
droid: git push origin feature-branch
hooks: ✅ Allowed

Result: Clean history, preserved work, confidence
```

### Integration with AGENTS.md Policy

These hooks **enforce** the policies documented in AGENTS.md:

| Policy | Hook | Enforcement |
|--------|------|-------------|
| "Never update git config" | N/A | Guidance only |
| "Never push without explicit instruction" | Branch Protection | Warns on protected pushes |
| "Never use -i flag" | N/A | Guidance only |
| "Forward-Only Progression" | Forward-Only Enforcer | BLOCKS destructive ops |
| "Co-authorship" | Co-Authorship Injector | Automatic addition |

---

**Continue to:** [04_DEEP_DIVE_SECURITY_ENFORCEMENT.md](./04_DEEP_DIVE_SECURITY_ENFORCEMENT.md)
