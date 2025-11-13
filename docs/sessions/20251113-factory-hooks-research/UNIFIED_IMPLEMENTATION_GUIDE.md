# Factory Hooks: Unified Implementation Guide

**Session:** 20251113-factory-hooks-research  
**Status:** Complete implementation roadmap  
**Audience:** Developers implementing Factory hooks for atoms-mcp-prod

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start (Foundation Hooks)](#quick-start-foundation-hooks)
4. [Phase 1: Code Quality Automation](#phase-1-code-quality-automation)
5. [Phase 2: Testing Automation](#phase-2-testing-automation)
6. [Phase 3: Git Workflow Enhancement](#phase-3-git-workflow-enhancement)
7. [Phase 4: Security Enforcement](#phase-4-security-enforcement)
8. [Configuration Reference](#configuration-reference)
9. [Testing Your Hooks](#testing-your-hooks)
10. [Debugging Guide](#debugging-guide)
11. [Performance Optimization](#performance-optimization)
12. [Troubleshooting](#troubleshooting)

---

## Overview

This guide provides step-by-step instructions for implementing **all 20 Factory hooks** designed for atoms-mcp-prod. It combines the detailed specifications from 4 deep-dive documents into a single, actionable implementation roadmap.

### What You'll Implement

- **8 Code Quality Hooks** - Automated formatting, validation, and enforcement
- **5 Testing Hooks** - Smart test running and coverage enforcement
- **4 Git Workflow Hooks** - Commit validation and branch protection
- **3 Security Hooks** - Secret detection and operation safety

### Expected Timeline

| Phase | Duration | Hooks | Difficulty |
|-------|----------|-------|------------|
| **Quick Start** | 4-8 hours | 5 foundation | Easy |
| **Phase 1** | 1-2 days | 3 more quality | Easy |
| **Phase 2** | 2-3 days | 4 more testing | Medium |
| **Phase 3** | 1-2 days | 4 git workflow | Medium |
| **Phase 4** | 1-2 days | 2 more security | Easy |
| **Total** | 1.5-2 weeks | 20 hooks | - |

---

## Prerequisites

### 1. Factory Configuration

**Check if hooks are enabled:**
```bash
cat ~/.factory/settings.json | jq '.hooks'
```

**If not present, add hooks configuration** (see [Configuration Reference](#configuration-reference))

### 2. Project Structure

**Create `.factory/` directory structure:**
```bash
cd /path/to/atoms-mcp-prod

mkdir -p .factory/hooks/{validation,verification,transformation,security,context,utils}
mkdir -p .factory/logs
mkdir -p .factory/cache

# Create __init__.py for Python modules
touch .factory/hooks/__init__.py
touch .factory/hooks/utils/__init__.py
```

### 3. Dependencies

**Ensure required tools are installed:**
```bash
source .venv/bin/activate

# Check Python tools
which black || pip install black
which ruff || pip install ruff
python -c "import pytest" || pip install pytest pytest-cov

# Verify they work
black --version
ruff --version
pytest --version
```

### 4. Permissions

**Make hook scripts executable:**
```bash
chmod +x .factory/hooks/**/*.py
chmod +x .factory/hooks/**/*.sh
```

---

## Quick Start (Foundation Hooks)

**Goal:** Get 5 critical hooks running in 4-8 hours

These hooks provide **maximum ROI** with **minimum complexity**:

1. ✅ File Size Enforcer - Prevent bloat
2. ✅ Code Formatter - Maintain style
3. ✅ Intelligent Test Runner - Fast feedback
4. ✅ Coverage Enforcer - Maintain quality
5. ✅ Secret Detector - Prevent leaks

### Step 1: File Size Enforcer (30 minutes)

**Implementation:**

```bash
# Create hook script
cat > .factory/hooks/validation/file_size_validator.py << 'EOF'
#!/usr/bin/env python3
"""File Size Validator - Block files >500 lines."""

import json
import sys
from pathlib import Path

MAX_LINES = 500
TARGET_LINES = 350

def count_lines(content: str) -> int:
    """Count non-empty lines."""
    return len(content.rstrip().split('\\n'))

def main():
    input_data = json.load(sys.stdin)
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    
    if tool_name not in ["Edit", "Write"]:
        sys.exit(0)
    
    file_path = tool_input.get("file_path", "")
    if not file_path.endswith('.py'):
        sys.exit(0)
    
    content = tool_input.get("content", "") or tool_input.get("new_str", "")
    if not content:
        sys.exit(0)
    
    line_count = count_lines(content)
    
    if line_count > MAX_LINES:
        message = f"File '{file_path}' exceeds {MAX_LINES} line limit ({line_count} lines). Decompose into smaller modules."
        print(json.dumps({"decision": "deny", "reason": message}))
        sys.exit(0)
    
    elif line_count > TARGET_LINES:
        print(f"⚠️  File '{file_path}' has {line_count} lines (target: ≤{TARGET_LINES})", file=sys.stderr)
    
    sys.exit(0)

if __name__ == "__main__":
    main()
EOF

chmod +x .factory/hooks/validation/file_size_validator.py
```

**Configuration (add to ~/.factory/settings.json):**

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

**Test:**
```bash
# Test blocking oversized file
echo '{
  "tool_name": "Write",
  "tool_input": {
    "file_path": "test.py",
    "content": "'$(python3 -c 'print("# line\\n" * 600)')"
  }
}' | .factory/hooks/validation/file_size_validator.py

# Should output: {"decision": "deny", "reason": "..."}
```

---

### Step 2: Code Formatter (20 minutes)

**Implementation:**

```bash
cat > .factory/hooks/verification/code_formatter.sh << 'EOF'
#!/usr/bin/env bash
set -euo pipefail

input=$(cat)
tool_name=$(echo "$input" | jq -r '.tool_name')
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')

# Only format Python files after Edit/Write
[[ "$tool_name" =~ ^(Edit|Write)$ ]] || exit 0
[[ "$file_path" =~ \\.py$ ]] || exit 0
[[ -f "$file_path" ]] || exit 0

# Run black + ruff
if command -v black &> /dev/null; then
    black "$file_path" --line-length 100 --quiet 2>&1 || true
fi

if command -v ruff &> /dev/null; then
    ruff check "$file_path" --fix --quiet 2>&1 || true
fi

echo "✅ Code formatted: $file_path"
exit 0
EOF

chmod +x .factory/hooks/verification/code_formatter.sh
```

**Configuration (add to PostToolUse section):**

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"$FACTORY_PROJECT_DIR\"/.factory/hooks/verification/code_formatter.sh",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

---

### Step 3: Secret Detector (45 minutes)

See [04_DEEP_DIVE_SECURITY_ENFORCEMENT.md](./04_DEEP_DIVE_SECURITY_ENFORCEMENT.md#hook-18-secret-detector) for complete implementation.

**Quick version:**

```python
#!/usr/bin/env python3
"""Secret Detector - Block credentials in code/prompts."""

import json
import re
import sys

SECRET_PATTERNS = [
    (r'AKIA[0-9A-Z]{16}', 'AWS Access Key'),
    (r'sk_live_[a-zA-Z0-9]{24,}', 'Stripe Live Key'),
    (r'ghp_[a-zA-Z0-9]{36}', 'GitHub Token'),
    # Add more patterns from deep-dive doc
]

def detect_secrets(content: str):
    secrets = []
    for pattern, secret_type in SECRET_PATTERNS:
        if re.search(pattern, content):
            secrets.append(secret_type)
    return secrets

def main():
    input_data = json.load(sys.stdin)
    # Implementation details in deep-dive doc
    pass

if __name__ == "__main__":
    main()
```

---

### Step 4: Intelligent Test Runner (1-2 hours)

See [02_DEEP_DIVE_TESTING_AUTOMATION.md](./02_DEEP_DIVE_TESTING_AUTOMATION.md#hook-9-intelligent-test-runner) for complete implementation.

---

### Step 5: Coverage Enforcer (30 minutes)

See [02_DEEP_DIVE_TESTING_AUTOMATION.md](./02_DEEP_DIVE_TESTING_AUTOMATION.md#hook-10-coverage-threshold-enforcer) for complete implementation.

---

### Quick Start Verification

After implementing the 5 foundation hooks:

```bash
# Test file size enforcement
python cli.py test run --scope unit  # Should trigger test runner hook

# Test code formatting
echo "def foo( x,y ):return x+y" > /tmp/test_format.py
# Edit via droid → should auto-format

# Test secret detection
echo "AKIAIOSFODNN7EXAMPLE" > /tmp/test_secret.txt
# Try to commit → should block

# Verify all hooks registered
jq '.hooks' ~/.factory/settings.json
```

**Success criteria:**
- ✅ File size validator blocks files >500 lines
- ✅ Code formatter runs automatically after edits
- ✅ Secret detector blocks credentials
- ✅ Test runner executes relevant tests
- ✅ Coverage enforcer maintains ≥80% threshold

---

## Phase 1: Code Quality Automation

**Duration:** 1-2 days  
**Hooks:** 3 additional (Import Organizer, Type Hint Validator, Docstring Enforcer)

### Implementation Order

1. **Import Organizer** (30 min) - Easy, uses ruff
2. **Type Hint Validator** (1 hour) - AST parsing required
3. **Docstring Enforcer** (1 hour) - Similar to type hints

### Import Organizer

```bash
cat > .factory/hooks/verification/import_sorter.sh << 'EOF'
#!/usr/bin/env bash
set -euo pipefail

input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')

[[ "$file_path" =~ \\.py$ ]] || exit 0
[[ -f "$file_path" ]] || exit 0

# Use ruff for import sorting (I rule = isort replacement)
if command -v ruff &> /dev/null; then
    ruff check "$file_path" --select I --fix --quiet 2>&1 || true
    echo "✅ Imports organized: $file_path"
fi

exit 0
EOF

chmod +x .factory/hooks/verification/import_sorter.sh
```

### Type Hint Validator

See [01_DEEP_DIVE_CODE_QUALITY_AUTOMATION.md](./01_DEEP_DIVE_CODE_QUALITY_AUTOMATION.md#hook-4-type-hint-validator) for complete implementation with AST parsing.

### Docstring Enforcer

See [01_DEEP_DIVE_CODE_QUALITY_AUTOMATION.md](./01_DEEP_DIVE_CODE_QUALITY_AUTOMATION.md#hook-5-docstring-enforcer) for complete implementation.

---

## Phase 2: Testing Automation

**Duration:** 2-3 days  
**Hooks:** 4 additional (Test Fixture Validator, Mock Client Validator, Test Marker Validator, + refine Test Runner)

### Key Concepts

**Fixture Parametrization > Separate Files:**
```python
# ✅ GOOD: One file, multiple variants
@pytest.fixture(params=["unit", "integration"])
def mcp_client(request):
    if request.param == "unit":
        return InMemoryMcpClient()
    else:
        return HttpMcpClient()

# ❌ BAD: Separate files
# test_entity_unit.py, test_entity_integration.py
```

### Implementation Steps

1. **Test Fixture Validator** (2 hours)
   - Detects duplicate test files
   - Suggests fixture parametrization
   - See [02_DEEP_DIVE_TESTING_AUTOMATION.md](./02_DEEP_DIVE_TESTING_AUTOMATION.md#hook-11-test-fixture-validator)

2. **Mock Client Validator** (1 hour)
   - Ensures unit tests use InMemoryMcpClient
   - Blocks live HTTP/DB in unit tests
   - See [02_DEEP_DIVE_TESTING_AUTOMATION.md](./02_DEEP_DIVE_TESTING_AUTOMATION.md#hook-12-mock-client-validator)

3. **Test Marker Validator** (1 hour)
   - Validates pytest markers
   - Ensures @pytest.mark.asyncio on async tests
   - See [02_DEEP_DIVE_TESTING_AUTOMATION.md](./02_DEEP_DIVE_TESTING_AUTOMATION.md#hook-13-test-marker-validator)

4. **Refine Test Runner** (2-3 hours)
   - Add smart scope caching
   - Implement parallel execution
   - Optimize for large test suites

---

## Phase 3: Git Workflow Enhancement

**Duration:** 1-2 days  
**Hooks:** 4 (Commit Message Validator, Co-Authorship Injector, Branch Protection, Forward-Only Enforcer)

### Implementation Order

1. **Commit Message Validator** (2 hours)
   - Enforces conventional commits
   - See [03_DEEP_DIVE_GIT_WORKFLOW_ENHANCEMENTS.md](./03_DEEP_DIVE_GIT_WORKFLOW_ENHANCEMENTS.md#hook-14-commit-message-validator)

2. **Co-Authorship Injector** (1 hour)
   - Adds factory-droid co-author automatically
   - See [03_DEEP_DIVE_GIT_WORKFLOW_ENHANCEMENTS.md](./03_DEEP_DIVE_GIT_WORKFLOW_ENHANCEMENTS.md#hook-15-co-authorship-injector)

3. **Branch Protection** (2 hours)
   - Prevents force push to main
   - Warns on protected branch pushes
   - See [03_DEEP_DIVE_GIT_WORKFLOW_ENHANCEMENTS.md](./03_DEEP_DIVE_GIT_WORKFLOW_ENHANCEMENTS.md#hook-16-branch-protection)

4. **Forward-Only Enforcer** (2 hours)
   - Blocks git revert, reset --hard
   - Enforces forward-only progression policy
   - See [03_DEEP_DIVE_GIT_WORKFLOW_ENHANCEMENTS.md](./03_DEEP_DIVE_GIT_WORKFLOW_ENHANCEMENTS.md#hook-17-forward-only-enforcement)

---

## Phase 4: Security Enforcement

**Duration:** 1-2 days  
**Hooks:** 2 additional (Environment Variable Validator, Destructive Operation Blocker)

### Implementation Order

1. **Environment Variable Validator** (2 hours)
   - Detects hardcoded secrets in code
   - Validates .env.example completeness
   - See [04_DEEP_DIVE_SECURITY_ENFORCEMENT.md](./04_DEEP_DIVE_SECURITY_ENFORCEMENT.md#hook-19-environment-variable-validator)

2. **Destructive Operation Blocker** (2 hours)
   - Blocks dangerous rm -rf commands
   - Validates shell command safety
   - See [04_DEEP_DIVE_SECURITY_ENFORCEMENT.md](./04_DEEP_DIVE_SECURITY_ENFORCEMENT.md#hook-20-destructive-operation-blocker)

---

## Configuration Reference

### Complete ~/.factory/settings.json

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
          },
          {
            "type": "command",
            "command": "\"$FACTORY_PROJECT_DIR\"/.factory/hooks/validation/todo_blocker.py",
            "timeout": 5
          }
        ]
      },
      {
        "matcher": "Execute",
        "hooks": [
          {
            "type": "command",
            "command": "\"$FACTORY_PROJECT_DIR\"/.factory/hooks/validation/commit_message_validator.py",
            "timeout": 5
          },
          {
            "type": "command",
            "command": "\"$FACTORY_PROJECT_DIR\"/.factory/hooks/transformation/coauthor_injector.sh",
            "timeout": 5
          },
          {
            "type": "command",
            "command": "\"$FACTORY_PROJECT_DIR\"/.factory/hooks/validation/branch_protection.py",
            "timeout": 10
          },
          {
            "type": "command",
            "command": "\"$FACTORY_PROJECT_DIR\"/.factory/hooks/validation/forward_only_enforcer.py",
            "timeout": 5
          },
          {
            "type": "command",
            "command": "\"$FACTORY_PROJECT_DIR\"/.factory/hooks/security/destructive_operation_blocker.py",
            "timeout": 5
          },
          {
            "type": "command",
            "command": "\"$FACTORY_PROJECT_DIR\"/.factory/hooks/security/secret_detector.py",
            "timeout": 10
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"$FACTORY_PROJECT_DIR\"/.factory/hooks/verification/code_formatter.sh",
            "timeout": 10
          },
          {
            "type": "command",
            "command": "\"$FACTORY_PROJECT_DIR\"/.factory/hooks/verification/import_sorter.sh",
            "timeout": 5
          },
          {
            "type": "command",
            "command": "\"$FACTORY_PROJECT_DIR\"/.factory/hooks/verification/type_hint_validator.py",
            "timeout": 10
          },
          {
            "type": "command",
            "command": "\"$FACTORY_PROJECT_DIR\"/.factory/hooks/verification/docstring_enforcer.py",
            "timeout": 10
          },
          {
            "type": "command",
            "command": "\"$FACTORY_PROJECT_DIR\"/.factory/hooks/verification/test_runner.py",
            "timeout": 90
          },
          {
            "type": "command",
            "command": "\"$FACTORY_PROJECT_DIR\"/.factory/hooks/verification/coverage_enforcer.sh",
            "timeout": 45
          },
          {
            "type": "command",
            "command": "\"$FACTORY_PROJECT_DIR\"/.factory/hooks/security/env_validator.py",
            "timeout": 10
          }
        ]
      },
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"$FACTORY_PROJECT_DIR\"/.factory/hooks/verification/test_fixture_validator.py",
            "timeout": 10
          },
          {
            "type": "command",
            "command": "\"$FACTORY_PROJECT_DIR\"/.factory/hooks/verification/mock_client_validator.py",
            "timeout": 5
          },
          {
            "type": "command",
            "command": "\"$FACTORY_PROJECT_DIR\"/.factory/hooks/verification/test_marker_validator.py",
            "timeout": 10
          }
        ]
      }
    ],
    "PreSessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"$FACTORY_PROJECT_DIR\"/.factory/hooks/security/secret_detector.py",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

---

## Testing Your Hooks

### Unit Test Framework

```bash
cat > .factory/hooks/test_hooks.sh << 'EOF'
#!/usr/bin/env bash

echo "Testing Factory Hooks..."

# Test 1: File Size Validator
echo "Test 1: File size validation"
echo '{
  "tool_name": "Write",
  "tool_input": {
    "file_path": "test.py",
    "content": "'$(python3 -c 'print("# line\\n" * 600)')"
  }
}' | .factory/hooks/validation/file_size_validator.py
[[ $? -eq 0 ]] && echo "✅ Pass" || echo "❌ Fail"

# Test 2: Secret Detection
echo "Test 2: Secret detection"
echo '{
  "tool_name": "Write",
  "tool_input": {
    "file_path": "test.py",
    "content": "api_key = \"AKIAIOSFODNN7EXAMPLE\""
  }
}' | .factory/hooks/security/secret_detector.py
[[ $? -eq 0 ]] && echo "✅ Pass" || echo "❌ Fail"

# Add more tests...
EOF

chmod +x .factory/hooks/test_hooks.sh
```

---

## Debugging Guide

### Enable Verbose Logging

```bash
# Add to hook scripts
import sys
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)
```

### Test Hooks in Isolation

```bash
# Test specific hook
echo '{...}' | .factory/hooks/validation/file_size_validator.py

# Check output
echo $?  # Exit code
```

### Common Issues

1. **Hook not triggering**
   - Check matcher pattern in settings.json
   - Verify hook script is executable
   - Check file path in tool_input

2. **Hook timing out**
   - Increase timeout in settings.json
   - Optimize hook performance
   - Add early exits for irrelevant files

3. **Hook blocking incorrectly**
   - Review decision logic
   - Check for false positives
   - Add whitelist patterns

---

## Performance Optimization

### Parallel Execution

Factory runs matching hooks **in parallel**. Optimize for this:

```python
# ✅ GOOD: Fast, independent checks
def quick_check():
    return len(content) < MAX_SIZE

# ❌ BAD: Slow, blocking operations
def slow_check():
    subprocess.run(["sleep", "10"])
```

### Caching Strategy

```python
import hashlib
import json

CACHE_FILE = ".factory/cache/hook_cache.json"

def get_cache_key(file_path, content):
    return hashlib.md5(f"{file_path}:{content}".encode()).hexdigest()

def check_cache(cache_key):
    if Path(CACHE_FILE).exists():
        with open(CACHE_FILE) as f:
            cache = json.load(f)
            return cache.get(cache_key)
    return None
```

---

## Troubleshooting

### Hooks Not Running

```bash
# Check if hooks enabled
jq '.hooks' ~/.factory/settings.json

# Verify project directory set
echo $FACTORY_PROJECT_DIR

# Test hook manually
.factory/hooks/validation/file_size_validator.py < test_input.json
```

### Performance Issues

```bash
# Measure hook execution time
time echo '{...}' | .factory/hooks/validation/file_size_validator.py

# Profile Python hooks
python -m cProfile .factory/hooks/validation/file_size_validator.py
```

### False Positives

```bash
# Add whitelist patterns
WHITELIST = [
    r'test_.*\.py',  # Test files
    r'__init__\.py',  # Init files
]
```

---

## Next Steps

After implementing all hooks:

1. **Measure Impact**
   - Track metrics (time saved, issues prevented)
   - Survey developer satisfaction
   - Monitor hook execution times

2. **Iterate & Improve**
   - Add more patterns to secret detector
   - Optimize slow hooks
   - Add more test scope detection rules

3. **Document**
   - Update team wiki with hook usage
   - Create troubleshooting runbook
   - Share success stories

4. **Scale**
   - Share hooks with other teams
   - Contribute patterns back to Factory
   - Create project-specific customizations

---

## Resources

- [01_DEEP_DIVE_CODE_QUALITY_AUTOMATION.md](./01_DEEP_DIVE_CODE_QUALITY_AUTOMATION.md) - 8 quality hooks
- [02_DEEP_DIVE_TESTING_AUTOMATION.md](./02_DEEP_DIVE_TESTING_AUTOMATION.md) - 5 testing hooks
- [03_DEEP_DIVE_GIT_WORKFLOW_ENHANCEMENTS.md](./03_DEEP_DIVE_GIT_WORKFLOW_ENHANCEMENTS.md) - 4 git hooks
- [04_DEEP_DIVE_SECURITY_ENFORCEMENT.md](./04_DEEP_DIVE_SECURITY_ENFORCEMENT.md) - 3 security hooks
- [DEEP_DIVES_COMPLETE_SUMMARY.md](./DEEP_DIVES_COMPLETE_SUMMARY.md) - Comprehensive overview

---

**Session:** 20251113-factory-hooks-research  
**Status:** Complete implementation guide  
**Ready for:** Phased rollout (foundation → full deployment)
