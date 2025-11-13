#!/usr/bin/env python3
"""Remove @pytest.mark.asyncio from sync test functions (def, not async def)."""

import sys
from pathlib import Path

def process_file(file_path: Path) -> bool:
    """Remove @pytest.mark.asyncio from sync test functions.
    
    Returns True if file was modified.
    """
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)
        return False
    
    lines = content.split('\n')
    modified = False
    new_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check if this line has @pytest.mark.asyncio
        if '@pytest.mark.asyncio' in line:
            # Look ahead to see if the next non-empty, non-decorator line is 'def' (not 'async def')
            j = i + 1
            found_def = False
            is_async = False
            
            # Look ahead up to 10 lines (to handle multiple decorators)
            while j < len(lines) and j < i + 10:
                next_line = lines[j].strip()
                if not next_line:
                    j += 1
                    continue
                
                # Skip other decorators
                if next_line.startswith('@'):
                    j += 1
                    continue
                
                # Check if it's a function definition
                if next_line.startswith('def '):
                    found_def = True
                    is_async = False
                    break
                elif next_line.startswith('async def '):
                    found_def = True
                    is_async = True
                    break
                else:
                    # Not a function definition, so this asyncio marker might be for something else
                    break
            
            # If we found a sync def, remove the asyncio marker line
            if found_def and not is_async:
                modified = True
                # Skip this line (don't add it to new_lines)
                i += 1
                continue
        
        new_lines.append(line)
        i += 1
    
    if modified:
        file_path.write_text('\n'.join(new_lines), encoding='utf-8')
        print(f"Modified: {file_path}")
        return True
    
    return False

def main():
    """Process all test files."""
    root = Path(__file__).parent.parent
    test_dirs = [
        root / 'tests' / 'e2e',
        root / 'tests' / 'integration',
        root / 'tests' / 'performance',
    ]
    
    modified_count = 0
    for test_dir in test_dirs:
        if not test_dir.exists():
            continue
        
        for py_file in test_dir.rglob('*.py'):
            if process_file(py_file):
                modified_count += 1
    
    print(f"\nTotal files modified: {modified_count}")

if __name__ == '__main__':
    main()
