#!/usr/bin/env python3
"""
Script to update test parameter names across all test files.

Replacements:
- format= -> format_type=
- query= -> search_term=
- type= -> context_type= (in workspace_tool set_context only)
- id= -> entity_id= (in workspace_tool set_context only)
- Remove fuzzy_match= and fuzzy= parameters
"""

import os
import re
from pathlib import Path

def fix_workspace_tool_set_context(content: str) -> str:
    """Fix type= and id= parameters in workspace_tool set_context calls."""

    # Pattern to match workspace_tool set_context blocks
    # We need to handle multi-line calls
    lines = content.split('\n')
    result_lines = []
    in_workspace_set_context = False
    brace_count = 0

    for i, line in enumerate(lines):
        # Check if we're entering a workspace_tool call
        if 'call_tool("workspace_tool"' in line or "call_tool('workspace_tool'" in line:
            in_workspace_set_context = False
            brace_count = line.count('{') - line.count('}')
            # Look ahead for set_context
            for j in range(i, min(i+5, len(lines))):
                if '"operation": "set_context"' in lines[j] or "'operation': 'set_context'" in lines[j]:
                    in_workspace_set_context = True
                    break

        # Track brace depth
        if '{' in line or '}' in line:
            brace_count += line.count('{') - line.count('}')

        # If we're in a set_context block, replace parameters
        if in_workspace_set_context and brace_count > 0:
            # Replace "type": with "context_type":
            line = re.sub(r'^(\s*)"type":\s*', r'\1"context_type": ', line)
            # Replace "id": with "entity_id":
            line = re.sub(r'^(\s*)"id":\s*', r'\1"entity_id": ', line)

        # Check if we've exited the block
        if brace_count == 0 and in_workspace_set_context:
            in_workspace_set_context = False

        result_lines.append(line)

    return '\n'.join(result_lines)

def fix_query_tool_parameters(content: str) -> str:
    """Fix query= -> search_term= in query tool calls."""
    # Replace query= with search_term= in query_tool calls
    content = re.sub(r'"query":\s*', '"search_term": ', content)
    content = re.sub(r"'query':\s*", "'search_term': ", content)
    return content

def fix_format_parameter(content: str) -> str:
    """Fix format= -> format_type=."""
    content = re.sub(r'"format":\s*', '"format_type": ', content)
    content = re.sub(r"'format':\s*", "'format_type': ", content)
    return content

def remove_fuzzy_parameters(content: str) -> str:
    """Remove fuzzy_match= and fuzzy= parameters."""
    # Remove lines with fuzzy_match or fuzzy parameters
    lines = content.split('\n')
    result_lines = []

    for line in lines:
        # Skip lines that only contain fuzzy parameters
        if re.match(r'^\s*"fuzzy(?:_match)?":\s*(?:True|False|true|false)\s*,?\s*$', line):
            continue
        if re.match(r"^\s*'fuzzy(?:_match)?':\s*(?:True|False|true|false)\s*,?\s*$", line):
            continue

        # Remove inline fuzzy parameters
        line = re.sub(r',\s*"fuzzy(?:_match)?":\s*(?:True|False|true|false)', '', line)
        line = re.sub(r",\s*'fuzzy(?:_match)?':\s*(?:True|False|true|false)", '', line)
        line = re.sub(r'"fuzzy(?:_match)?":\s*(?:True|False|true|false)\s*,\s*', '', line)
        line = re.sub(r"'fuzzy(?:_match)?':\s*(?:True|False|true|false)\s*,\s*", '', line)

        result_lines.append(line)

    return '\n'.join(result_lines)

def process_file(filepath: Path) -> tuple[bool, str]:
    """Process a single file and return (changed, message)."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            original_content = f.read()

        content = original_content

        # Apply all fixes
        content = fix_workspace_tool_set_context(content)
        content = fix_query_tool_parameters(content)
        content = fix_format_parameter(content)
        content = remove_fuzzy_parameters(content)

        # Check if content changed
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, f"Updated {filepath.name}"
        else:
            return False, f"No changes needed for {filepath.name}"

    except Exception as e:
        return False, f"Error processing {filepath.name}: {str(e)}"

def main():
    """Main function to process all test files."""
    tests_dir = Path('/Users/kooshapari/temp-PRODVERCEL/485/clean/atoms_mcp-old/tests')

    # Find all Python files
    py_files = list(tests_dir.rglob('*.py'))

    # Exclude the fix script itself
    py_files = [f for f in py_files if f.name != 'fix_parameters.py']

    print(f"Processing {len(py_files)} Python files...")
    print("-" * 60)

    changed_count = 0
    unchanged_count = 0
    error_count = 0

    for filepath in sorted(py_files):
        changed, message = process_file(filepath)
        if "Error" in message:
            error_count += 1
            print(f"❌ {message}")
        elif changed:
            changed_count += 1
            print(f"✓ {message}")
        else:
            unchanged_count += 1
            # Uncomment to see unchanged files
            # print(f"  {message}")

    print("-" * 60)
    print(f"\nSummary:")
    print(f"  Changed: {changed_count}")
    print(f"  Unchanged: {unchanged_count}")
    print(f"  Errors: {error_count}")
    print(f"  Total: {len(py_files)}")

    if changed_count > 0:
        print("\n✅ Parameter updates completed successfully!")
    else:
        print("\n✓ All files already have correct parameters.")

if __name__ == '__main__':
    main()
