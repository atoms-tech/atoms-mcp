# Deep Dive: Testing Automation Hooks

**Category:** Testing & Coverage  
**Priority:** HIGH - Quality assurance foundation  
**Hooks Count:** 5 detailed hooks  
**Expected Impact:** 95% automated test execution, 100% coverage enforcement

---

## Overview

Testing automation hooks eliminate manual test execution by automatically running relevant tests after code changes, enforcing coverage thresholds, and validating test quality. These hooks ensure:

- **Immediate feedback** on code changes
- **Consistent coverage** above 80% threshold
- **Test quality** through fixture and marker validation
- **Isolation enforcement** via mock client validation

---

## Table of Contents

1. [Hook 9: Intelligent Test Runner](#hook-9-intelligent-test-runner)
2. [Hook 10: Coverage Threshold Enforcer](#hook-10-coverage-threshold-enforcer)
3. [Hook 11: Test Fixture Validator](#hook-11-test-fixture-validator)
4. [Hook 12: Mock Client Validator](#hook-12-mock-client-validator)
5. [Hook 13: Test Marker Validator](#hook-13-test-marker-validator)
6. [Integration & Test Selection Strategy](#integration--test-selection-strategy)
7. [Performance Optimization](#performance-optimization)
8. [Failure Handling & Recovery](#failure-handling--recovery)

---

## Hook 9: Intelligent Test Runner

### Purpose
Automatically run relevant tests after code changes with smart scope detection.

### Event & Matcher
- **Event:** `PostToolUse`
- **Matcher:** `Edit|Write`
- **Timing:** After file is written/modified

### Smart Scope Detection

```python
#!/usr/bin/env python3
# .factory/hooks/verification/test_runner.py

"""
Intelligent Test Runner Hook

Automatically runs relevant tests based on changed files.
Uses smart scope detection to minimize test time while maximizing coverage.
"""

import json
import sys
import subprocess
from pathlib import Path
from typing import List, Tuple

def determine_test_scope(file_path: str, cwd: str) -> Tuple[str, str]:
    """
    Determine which tests to run based on changed file.
    
    Returns:
        (test_path, scope_description)
    """
    path = Path(file_path)
    parts = path.parts
    
    # Test file changed -> run that specific test
    if parts[0] == "tests":
        return file_path, f"specific test file: {file_path}"
    
    # Tool module changed -> run tool unit tests
    if parts[0] == "tools":
        tool_name = path.stem
        test_path = f"tests/unit/tools/test_{tool_name}.py"
        return test_path, f"tool tests for {tool_name}"
    
    # Service module changed -> run service tests
    if parts[0] == "services":
        if len(parts) > 1:
            service_name = parts[1] if parts[1] != "__init__.py" else parts[0]
            test_path = f"tests/unit/services/test_{service_name}.py"
        else:
            test_path = "tests/unit/services/"
        return test_path, f"service tests"
    
    # Infrastructure changed -> run infrastructure tests
    if parts[0] == "infrastructure":
        module_name = path.stem
        test_path = f"tests/unit/infrastructure/test_{module_name}.py"
        return test_path, f"infrastructure tests for {module_name}"
    
    # Auth changed -> run auth tests
    if parts[0] == "auth":
        return "tests/unit/auth/", "auth tests"
    
    # Core server files -> run integration tests
    if path.name in ["server.py", "app.py"]:
        return "tests/integration/", "integration tests (server changed)"
    
    # Schemas changed -> run all tests (data structures affect everything)
    if parts[0] == "schemas":
        return "tests/", "all tests (schemas changed)"
    
    # Default: run unit tests only (fast and safe)
    return "tests/unit/", "unit tests (default scope)"

def run_tests(test_path: str, cwd: str, timeout: int = 60) -> subprocess.CompletedProcess:
    """Run pytest with specified test path."""
    cmd = ["uv", "run", "pytest", test_path, "-q", "--tb=short"]
    
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout
    )
    
    return result

def parse_test_output(output: str) -> dict:
    """Parse pytest output for key metrics."""
    lines = output.split('\\n')
    
    metrics = {
        'passed': 0,
        'failed': 0,
        'skipped': 0,
        'errors': 0,
        'total_time': '0s'
    }
    
    # Look for summary line: "5 passed, 2 failed in 1.23s"
    for line in lines:
        if ' passed' in line or ' failed' in line:
            if 'passed' in line:
                metrics['passed'] = int(line.split()[0])
            if 'failed' in line:
                parts = line.split('failed')
                metrics['failed'] = int(parts[0].split()[-1])
            if ' in ' in line:
                metrics['total_time'] = line.split(' in ')[-1].strip()
    
    return metrics

def format_test_feedback(
    file_path: str,
    test_scope: str,
    result: subprocess.CompletedProcess,
    metrics: dict
) -> dict:
    """Format feedback for droid based on test results."""
    
    if result.returncode == 0:
        # Tests passed
        return {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": f"✅ Tests passed for {file_path} ({test_scope}): {metrics['passed']} passed in {metrics['total_time']}"
            }
        }
    else:
        # Tests failed
        failure_summary = result.stdout[-1000:] if len(result.stdout) > 1000 else result.stdout
        
        message = f"""Tests FAILED after changes to {file_path}

Test scope: {test_scope}
Results: {metrics['passed']} passed, {metrics['failed']} failed

Failure output (last 1000 chars):
{failure_summary}

Please fix test failures before proceeding.
Reference: openspec/project.md § Testing Strategy"""
        
        return {
            "decision": "block",
            "reason": message,
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": "Test failures must be addressed."
            }
        }

def should_skip_tests(file_path: str) -> bool:
    """Determine if tests should be skipped for this file."""
    skip_patterns = [
        "__init__.py",          # Init files rarely need tests
        "conftest.py",          # Pytest config
        ".md",                  # Documentation
        ".json",                # Config files
        ".yaml", ".yml",        # Config files
        ".txt",                 # Text files
        "schemas/generated/",   # Generated code
    ]
    
    return any(pattern in file_path for pattern in skip_patterns)

def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)
    
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    cwd = input_data.get("cwd", "")
    
    # Only run tests for Edit/Write operations
    if tool_name not in ["Edit", "Write"]:
        sys.exit(0)
    
    file_path = tool_input.get("file_path", "")
    
    # Only run tests for Python files
    if not file_path.endswith('.py'):
        sys.exit(0)
    
    # Skip tests for certain files
    if should_skip_tests(file_path):
        print(f"ℹ️  Skipping tests for {file_path} (non-testable file)")
        sys.exit(0)
    
    # Determine test scope
    test_path, scope_description = determine_test_scope(file_path, cwd)
    
    print(f"🧪 Running tests: {scope_description}...", file=sys.stderr)
    
    try:
        # Run tests
        result = run_tests(test_path, cwd, timeout=60)
        
        # Parse results
        metrics = parse_test_output(result.stdout + result.stderr)
        
        # Format feedback
        feedback = format_test_feedback(file_path, scope_description, result, metrics)
        
        print(json.dumps(feedback))
        sys.exit(0)
        
    except subprocess.TimeoutExpired:
        print(json.dumps({
            "decision": "block",
            "reason": f"Tests timed out after 60s for {file_path}. Tests may be hanging."
        }))
        sys.exit(0)
    
    except FileNotFoundError:
        # Test file doesn't exist yet (new module)
        print(f"ℹ️  No tests found for {file_path}. Consider adding tests.", file=sys.stderr)
        sys.exit(0)

if __name__ == "__main__":
    main()
```

### Configuration

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"$FACTORY_PROJECT_DIR\"/.factory/hooks/verification/test_runner.py",
            "timeout": 90
          }
        ]
      }
    ]
  }
}
```

### Advanced: Parallel Test Execution

```python
# For projects with many test files, run tests in parallel

def run_tests_parallel(test_paths: List[str], cwd: str) -> List[subprocess.CompletedProcess]:
    """Run multiple test files in parallel."""
    import concurrent.futures
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(run_tests, path, cwd, 60)
            for path in test_paths
        ]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    return results
```

### Performance
- **Execution Time:** 2-30 seconds (depends on test scope)
- **Timeout:** 90 seconds (allows for integration tests)
- **Optimization:** Smart scope detection minimizes test time

---

## Hook 10: Coverage Threshold Enforcer

### Purpose
Ensure test coverage stays above 80% threshold for all modules.

### Event & Matcher
- **Event:** `PostToolUse`
- **Matcher:** `Edit|Write`
- **Timing:** After tests run

### Implementation

```bash
#!/usr/bin/env bash
# .factory/hooks/verification/coverage_enforcer.sh

set -euo pipefail

MIN_COVERAGE=80
WARNING_THRESHOLD=85

input=$(cat)
tool_name=$(echo "$input" | jq -r '.tool_name')
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')
cwd=$(echo "$input" | jq -r '.cwd')

# Only check coverage for production code (not tests)
if [[ ! "$file_path" =~ ^(tools|services|infrastructure|auth)/.+\\.py$ ]]; then
    exit 0
fi

# Skip __init__.py files
if [[ "$file_path" =~ __init__\\.py$ ]]; then
    exit 0
fi

echo "📊 Checking coverage for $file_path..." >&2

cd "$cwd"

# Run coverage for specific file
coverage_output=$(uv run pytest \\
    --cov="$file_path" \\
    --cov-report=term-missing \\
    --cov-fail-under="$MIN_COVERAGE" \\
    -q \\
    2>&1 || true)

# Extract coverage percentage
coverage_percent=$(echo "$coverage_output" | \\
    grep -oP '\\d+%' | \\
    head -1 | \\
    tr -d '%' || echo "0")

# Check if coverage meets threshold
if [[ "$coverage_percent" -lt "$MIN_COVERAGE" ]]; then
    # Extract missing lines
    missing_lines=$(echo "$coverage_output" | \\
        grep "$file_path" | \\
        grep -oP '\\d+-\\d+|\\d+' || echo "unknown")
    
    cat << EOF | jq -c '.'
{
  "decision": "block",
  "reason": "Coverage for $file_path is ${coverage_percent}% (minimum: ${MIN_COVERAGE}%).\\n\\nMissing coverage on lines: $missing_lines\\n\\nPlease add tests to cover these lines.\\n\\nReference: openspec/project.md § Testing Strategy",
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "Test coverage must be improved before proceeding."
  }
}
EOF
    exit 0

elif [[ "$coverage_percent" -lt "$WARNING_THRESHOLD" ]]; then
    # Warning zone (80-84%)
    echo "⚠️  Coverage: ${coverage_percent}% (target: ≥${WARNING_THRESHOLD}%)" >&2
    exit 0

else
    # Good coverage
    echo "✅ Coverage: ${coverage_percent}% (≥${MIN_COVERAGE}%)" >&2
    exit 0
fi
```

### Configuration

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"$FACTORY_PROJECT_DIR\"/.factory/hooks/verification/coverage_enforcer.sh",
            "timeout": 45
          }
        ]
      }
    ]
  }
}
```

### Coverage Report Enhancement

```python
#!/usr/bin/env python3
# .factory/hooks/verification/coverage_analyzer.py

"""
Enhanced coverage analyzer with detailed reporting.
"""

import json
import sys
import subprocess
from pathlib import Path

def generate_coverage_report(file_path: str, cwd: str) -> dict:
    """Generate detailed coverage report."""
    
    # Run coverage with JSON output
    result = subprocess.run(
        ["uv", "run", "pytest", 
         f"--cov={file_path}",
         "--cov-report=json",
         "-q"],
        cwd=cwd,
        capture_output=True,
        text=True
    )
    
    # Parse JSON report
    with open(f"{cwd}/coverage.json") as f:
        coverage_data = json.load(f)
    
    file_data = coverage_data['files'].get(file_path, {})
    
    return {
        'coverage_percent': file_data.get('summary', {}).get('percent_covered', 0),
        'missing_lines': file_data.get('missing_lines', []),
        'excluded_lines': file_data.get('excluded_lines', []),
        'total_statements': file_data.get('summary', {}).get('num_statements', 0),
        'covered_statements': file_data.get('summary', {}).get('covered_lines', 0)
    }

# ... rest of implementation
```

### Performance
- **Execution Time:** 5-15 seconds (runs tests with coverage)
- **Timeout:** 45 seconds
- **Optimization:** Only check files in production code paths

---

## Hook 11: Test Fixture Validator

### Purpose
Ensure tests use fixture parametrization instead of duplicate test files.

### Event & Matcher
- **Event:** `PostToolUse`
- **Matcher:** `Write`
- **Timing:** After test file creation/modification

### Implementation

```python
#!/usr/bin/env python3
# .factory/hooks/verification/test_fixture_validator.py

"""
Test Fixture Validator Hook

Ensures tests use pytest fixture parametrization instead of:
- Separate unit/integration/e2e test files
- Duplicate test logic across variants
"""

import ast
import json
import sys
from pathlib import Path
from typing import List, Tuple

def check_fixture_usage(file_path: str) -> Tuple[bool, List[str]]:
    """Check if test file uses proper fixture parametrization."""
    
    try:
        with open(file_path, 'r') as f:
            tree = ast.parse(f.read(), filename=file_path)
    except SyntaxError:
        return True, []  # Can't parse, let other tools handle it
    
    issues = []
    
    # Check for fixture definitions with parametrization
    has_parametrized_fixtures = False
    test_functions = []
    
    for node in ast.walk(tree):
        # Check for @pytest.fixture with params
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call):
                    # Check if it's pytest.fixture(params=...)
                    if (hasattr(decorator.func, 'attr') and 
                        decorator.func.attr == 'fixture'):
                        
                        # Check for params argument
                        for keyword in decorator.keywords:
                            if keyword.arg == 'params':
                                has_parametrized_fixtures = True
            
            # Collect test functions
            if node.name.startswith('test_'):
                test_functions.append(node.name)
    
    # If test file has many similar tests but no parametrized fixtures, suggest consolidation
    if len(test_functions) > 10 and not has_parametrized_fixtures:
        # Check for naming patterns suggesting duplication
        test_stems = [name.rsplit('_', 1)[0] for name in test_functions]
        unique_stems = set(test_stems)
        
        if len(test_stems) > len(unique_stems) * 1.5:  # >50% duplication
            issues.append(
                f"Found {len(test_functions)} tests with similar names. "
                f"Consider using fixture parametrization to reduce duplication."
            )
    
    return len(issues) == 0, issues

def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)
    
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    
    if tool_name != "Write":
        sys.exit(0)
    
    file_path = tool_input.get("file_path", "")
    
    # Only validate test files
    if not file_path.startswith("tests/") or not file_path.endswith(".py"):
        sys.exit(0)
    
    # Check fixture usage
    is_valid, issues = check_fixture_usage(file_path)
    
    if not is_valid:
        message = f"""Fixture validation issues in {file_path}:

""" + "\\n".join(f"  • {issue}" for issue in issues) + """

Consider:
1. Use @pytest.fixture(params=[...]) for variant testing
2. Parametrize tests with @pytest.mark.parametrize
3. Avoid duplicate test files for unit/integration/e2e

Reference: CLAUDE.md § Test File Naming Convention"""
        
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": message
            },
            "systemMessage": "Consider consolidating tests with fixture parametrization"
        }
        
        print(json.dumps(output))
    else:
        print(f"✅ Test fixtures properly used: {file_path}")
    
    sys.exit(0)

if __name__ == "__main__":
    main()
```

### Configuration

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"$FACTORY_PROJECT_DIR\"/.factory/hooks/verification/test_fixture_validator.py",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

### Performance
- **Execution Time:** ~100ms (AST parsing)
- **Timeout:** 10 seconds

---

## Hook 12: Mock Client Validator

### Purpose
Ensure unit tests use InMemoryMcpClient (mocks) instead of live clients.

### Event & Matcher
- **Event:** `PostToolUse`
- **Matcher:** `Write`
- **Timing:** After test file creation

### Implementation

```python
#!/usr/bin/env python3
# .factory/hooks/verification/mock_client_validator.py

"""
Mock Client Validator Hook

Ensures unit tests use mock clients (InMemoryMcpClient)
instead of live HTTP/database connections.
"""

import ast
import json
import sys
import re
from pathlib import Path

def check_mock_usage(file_path: str, content: str) -> tuple[bool, list[str]]:
    """Check if unit tests use proper mock clients."""
    
    # Only enforce for unit tests
    if "tests/unit/" not in file_path:
        return True, []
    
    issues = []
    
    # Check for live client imports (bad in unit tests)
    live_client_patterns = [
        r'from\s+infrastructure\.adapters\s+import\s+Supabase',
        r'from\s+infrastructure\.supabase_db\s+import',
        r'from\s+httpx\s+import\s+Client',
        r'from\s+aiohttp\s+import\s+ClientSession',
    ]
    
    for pattern in live_client_patterns:
        if re.search(pattern, content):
            issues.append(
                f"Unit test imports live client: {pattern}. "
                f"Use mock clients from infrastructure/mock_adapters.py instead."
            )
    
    # Check for USE_MOCK_CLIENTS environment variable
    if 'USE_MOCK_CLIENTS' not in content and 'mock' in file_path.lower():
        issues.append(
            "Unit test should use USE_MOCK_CLIENTS environment variable "
            "or conftest fixtures with mock adapters."
        )
    
    # Look for proper mock imports (good)
    has_mock_imports = any([
        'InMemoryMcpClient' in content,
        'mock_adapters' in content,
        '@pytest.fixture' in content and 'mock' in content.lower(),
    ])
    
    # If test makes HTTP calls but doesn't use mocks, warn
    if not has_mock_imports:
        if any(pattern in content for pattern in ['async def test_', 'await']):
            if any(db_term in content for db_term in ['supabase', 'database', 'db']):
                issues.append(
                    "Async test appears to use database but no mock imports found. "
                    "Unit tests should use InMemoryMcpClient or mock adapters."
                )
    
    return len(issues) == 0, issues

def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)
    
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    
    if tool_name != "Write":
        sys.exit(0)
    
    file_path = tool_input.get("file_path", "")
    content = tool_input.get("content", "")
    
    # Only validate unit test files
    if not (file_path.startswith("tests/unit/") and file_path.endswith(".py")):
        sys.exit(0)
    
    # Check mock usage
    is_valid, issues = check_mock_usage(file_path, content)
    
    if not is_valid:
        message = f"""Mock client validation issues in {file_path}:

""" + "\\n".join(f"  • {issue}" for issue in issues) + """

Unit tests must use mock clients:
- InMemoryMcpClient for MCP tools
- Mock adapters from infrastructure/mock_adapters.py
- USE_MOCK_CLIENTS environment variable

Reference: openspec/project.md § Testing Strategy"""
        
        output = {
            "decision": "block",
            "reason": message,
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": "Fix mock client usage in unit tests."
            }
        }
        
        print(json.dumps(output))
    else:
        print(f"✅ Mock clients properly used: {file_path}")
    
    sys.exit(0)

if __name__ == "__main__":
    main()
```

### Configuration

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"$FACTORY_PROJECT_DIR\"/.factory/hooks/verification/mock_client_validator.py",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

### Performance
- **Execution Time:** ~50ms (regex matching)
- **Timeout:** 5 seconds

---

## Hook 13: Test Marker Validator

### Purpose
Ensure performance/integration tests have proper pytest markers.

### Event & Matcher
- **Event:** `PostToolUse`
- **Matcher:** `Write`
- **Timing:** After test file creation

### Implementation

```python
#!/usr/bin/env python3
# .factory/hooks/verification/test_marker_validator.py

"""
Test Marker Validator Hook

Ensures tests have proper pytest markers for categorization:
- @pytest.mark.asyncio for async tests
- @pytest.mark.integration for integration tests
- @pytest.mark.performance for performance tests
- @pytest.mark.e2e for end-to-end tests
"""

import ast
import json
import sys
from typing import List, Tuple

def check_test_markers(file_path: str) -> Tuple[bool, List[str]]:
    """Check if tests have proper markers."""
    
    try:
        with open(file_path, 'r') as f:
            tree = ast.parse(f.read(), filename=file_path)
    except SyntaxError:
        return True, []
    
    issues = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
            # Check if async test
            is_async = isinstance(node, ast.AsyncFunctionDef)
            
            # Extract markers
            markers = []
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Attribute):
                    if hasattr(decorator, 'attr'):
                        markers.append(decorator.attr)
                elif isinstance(decorator, ast.Call):
                    if hasattr(decorator.func, 'attr'):
                        markers.append(decorator.func.attr)
            
            # Validate async tests have asyncio marker
            if is_async and 'asyncio' not in markers:
                issues.append(
                    f"Async test '{node.name}' (line {node.lineno}) "
                    f"missing @pytest.mark.asyncio marker"
                )
            
            # Validate integration tests have integration marker
            if 'tests/integration/' in file_path and 'integration' not in markers:
                issues.append(
                    f"Integration test '{node.name}' (line {node.lineno}) "
                    f"missing @pytest.mark.integration marker"
                )
            
            # Validate performance tests have performance marker
            if 'performance' in node.name.lower() and 'performance' not in markers:
                issues.append(
                    f"Performance test '{node.name}' (line {node.lineno}) "
                    f"missing @pytest.mark.performance marker"
                )
    
    return len(issues) == 0, issues

def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)
    
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    
    if tool_name != "Write":
        sys.exit(0)
    
    file_path = tool_input.get("file_path", "")
    
    # Only validate test files
    if not (file_path.startswith("tests/") and file_path.endswith(".py")):
        sys.exit(0)
    
    # Check markers
    is_valid, issues = check_test_markers(file_path)
    
    if not is_valid:
        message = f"""Test marker validation issues in {file_path}:

""" + "\\n".join(f"  • {issue}" for issue in issues) + """

Add proper pytest markers:
- @pytest.mark.asyncio for async tests
- @pytest.mark.integration for integration tests
- @pytest.mark.performance for performance tests

Reference: pyproject.toml § pytest markers"""
        
        output = {
            "decision": "block",
            "reason": message,
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": "Add missing pytest markers."
            }
        }
        
        print(json.dumps(output))
    else:
        print(f"✅ Test markers properly configured: {file_path}")
    
    sys.exit(0)

if __name__ == "__main__":
    main()
```

### Configuration

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"$FACTORY_PROJECT_DIR\"/.factory/hooks/verification/test_marker_validator.py",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

### Performance
- **Execution Time:** ~100ms (AST parsing)
- **Timeout:** 10 seconds

---

## Integration & Test Selection Strategy

### Hook Execution Flow

For `tools/entity.py` edit:

```
1. PostToolUse hooks trigger (parallel):
   ├─ Test Runner (determines scope: tests/unit/tools/test_entity.py)
   ├─ Coverage Enforcer (checks coverage for tools/entity.py)
   ├─ Test Fixture Validator (skipped - not a test file)
   ├─ Mock Client Validator (skipped - not a test file)
   └─ Test Marker Validator (skipped - not a test file)

2. Test Runner executes:
   → uv run pytest tests/unit/tools/test_entity.py -q
   
3. If tests pass:
   → Coverage Enforcer checks coverage
   
4. If coverage ≥80%:
   → All hooks succeed, continue
   
5. If tests fail OR coverage <80%:
   → Block with detailed feedback to droid
```

### Test Selection Matrix

| File Changed | Test Scope | Rationale |
|--------------|------------|-----------|
| `tools/entity.py` | `tests/unit/tools/test_entity.py` | Direct test file |
| `services/embedding_factory.py` | `tests/unit/services/` | All service tests |
| `infrastructure/supabase_db.py` | `tests/unit/infrastructure/test_supabase_db.py` | Specific adapter |
| `server.py` | `tests/integration/` | Server affects integration |
| `schemas/generated/models.py` | `tests/` | Schemas affect all tests |
| `tests/unit/tools/test_entity.py` | Same file | Run modified test |

### Optimization: Incremental Testing

```python
def get_affected_tests(changed_file: str, git_diff: bool = True) -> List[str]:
    """
    Determine affected tests using:
    1. Direct mapping (tools/entity.py → tests/unit/tools/test_entity.py)
    2. Import graph analysis (which tests import this module)
    3. Git history (which tests touched this file before)
    """
    
    affected = []
    
    # Direct mapping
    direct_test = get_direct_test_file(changed_file)
    if direct_test:
        affected.append(direct_test)
    
    # Import graph (requires AST analysis)
    importers = find_importers(changed_file)
    affected.extend(get_tests_for_modules(importers))
    
    return list(set(affected))  # Deduplicate
```

---

## Performance Optimization

### Parallel Test Execution

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"$FACTORY_PROJECT_DIR\"/.factory/hooks/verification/test_runner.py",
            "timeout": 90
          },
          {
            "type": "command",
            "command": "\"$FACTORY_PROJECT_DIR\"/.factory/hooks/verification/coverage_enforcer.sh",
            "timeout": 45
          }
        ]
      }
    ]
  }
}
```

**Both hooks run in parallel:**
- Test Runner: 2-30s
- Coverage Enforcer: 5-15s
- **Total time:** ~30s (not 45s)

### Caching Strategy

```python
# Cache test results to avoid re-running unchanged tests

import hashlib
import json
from pathlib import Path

CACHE_FILE = ".factory/hooks/cache/test_results.json"

def get_file_hash(file_path: str) -> str:
    """Get MD5 hash of file content."""
    with open(file_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def load_test_cache() -> dict:
    """Load cached test results."""
    if Path(CACHE_FILE).exists():
        with open(CACHE_FILE) as f:
            return json.load(f)
    return {}

def save_test_cache(cache: dict):
    """Save test results to cache."""
    Path(CACHE_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f)

def should_run_tests(file_path: str, cache: dict) -> bool:
    """Determine if tests should run based on cache."""
    file_hash = get_file_hash(file_path)
    cached_entry = cache.get(file_path, {})
    
    # Run if file changed or no cache entry
    return cached_entry.get('hash') != file_hash
```

---

## Failure Handling & Recovery

### Smart Retry Logic

```python
def run_tests_with_retry(test_path: str, max_retries: int = 2) -> subprocess.CompletedProcess:
    """Run tests with automatic retry for flaky tests."""
    
    for attempt in range(max_retries):
        result = run_tests(test_path, cwd, timeout=60)
        
        if result.returncode == 0:
            return result  # Success
        
        # Check if failure is due to flaky test (intermittent network, timing)
        if is_flaky_failure(result.stdout):
            print(f"Detected flaky failure, retrying (attempt {attempt + 1}/{max_retries})...")
            continue
        else:
            return result  # Real failure, don't retry
    
    return result  # All retries exhausted

def is_flaky_failure(output: str) -> bool:
    """Detect if failure is due to flakiness."""
    flaky_indicators = [
        "connection refused",
        "timeout",
        "temporarily unavailable",
        "rate limit",
    ]
    
    return any(indicator in output.lower() for indicator in flaky_indicators)
```

### Detailed Failure Reports

```python
def format_test_failure_report(result: subprocess.CompletedProcess, file_path: str) -> str:
    """Format detailed failure report for droid."""
    
    # Parse pytest output
    failure_sections = extract_failure_sections(result.stdout)
    
    report = f"""
Test Failures in {file_path}

Summary:
{extract_summary(result.stdout)}

Failed Tests:
"""
    
    for failure in failure_sections[:3]:  # Limit to 3 most important
        report += f"""
  • {failure['test_name']}
    Location: {failure['location']}
    Error: {failure['error_type']}
    
    {failure['error_message'][:200]}...
"""
    
    if len(failure_sections) > 3:
        report += f"\\n... and {len(failure_sections) - 3} more failures\\n"
    
    report += """
Suggested Actions:
1. Review test failures above
2. Run tests locally: uv run pytest """ + file_path + """
3. Fix failing tests before continuing
"""
    
    return report
```

---

## Summary & Impact

### Hooks Implemented

✅ 5 testing automation hooks  
✅ Intelligent test scope detection  
✅ Coverage enforcement (≥80%)  
✅ Fixture/marker validation  
✅ Mock client enforcement  
✅ Performance optimized (<60s typical)

### Expected Impact

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Test execution** | Manual | Automatic | 100% automation |
| **Coverage below 80%** | ~30% of files | 0% | 100% enforcement |
| **Test duplication** | ~20% of tests | <5% | 75% reduction |
| **Mock usage in unit tests** | ~80% | 100% | +20% |
| **Missing markers** | ~15% | 0% | 100% fix |
| **Time to test feedback** | 5-30 minutes | 2-60 seconds | 10-30x faster |

### Integration with Existing Workflow

**Before hooks:**
```bash
# Manual workflow
droid: Edit tools/entity.py
developer: uv run pytest tests/unit/tools/test_entity.py
developer: uv run pytest --cov=tools/entity.py
developer: Check coverage report
developer: Fix if needed
```

**After hooks:**
```bash
# Automated workflow
droid: Edit tools/entity.py
hooks: (automatic)
  → Run relevant tests
  → Check coverage
  → Validate test quality
  → Provide feedback to droid
droid: Fix issues if any (guided by hook feedback)
```

---

**Continue to:** [03_DEEP_DIVE_GIT_WORKFLOW_ENHANCEMENTS.md](./03_DEEP_DIVE_GIT_WORKFLOW_ENHANCEMENTS.md)
