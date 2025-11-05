#!/usr/bin/env python3
"""Check Python files for syntax errors."""
import ast
import sys
from pathlib import Path


def check_syntax(file_path):
    """Check a single Python file for syntax errors."""
    try:
        with open(file_path, encoding="utf-8") as f:
            code = f.read()
        ast.parse(code, filename=str(file_path))
        return None
    except SyntaxError as e:
        return {
            "file": str(file_path),
            "line": e.lineno,
            "offset": e.offset,
            "msg": e.msg,
            "text": e.text
        }
    except Exception as e:
        return {
            "file": str(file_path),
            "error": str(e)
        }

def main():
    """Check all Python files in the project."""
    root = Path("/Users/kooshapari/temp-PRODVERCEL/485/kush/atoms-mcp-prod")
    errors = []

    # Exclude patterns
    exclude_patterns = {".venv", "venv", ".tox", "build", "dist", "__pycache__", ".git", "node_modules"}

    for py_file in root.rglob("*.py"):
        # Skip excluded directories
        if any(pattern in py_file.parts for pattern in exclude_patterns):
            continue

        error = check_syntax(py_file)
        if error:
            errors.append(error)

    if errors:
        print(f"Found {len(errors)} files with syntax errors:\n")
        for error in errors:
            print(f"File: {error['file']}")
            if "line" in error:
                print(f"  Line {error['line']}, Column {error['offset']}")
                print(f"  Error: {error['msg']}")
                if error["text"]:
                    print(f"  Text: {error['text'].strip()}")
            else:
                print(f"  Error: {error.get('error', 'Unknown error')}")
            print()
        return 1
    print("No syntax errors found!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
