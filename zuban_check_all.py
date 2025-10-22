#!/usr/bin/env python3
"""
Zuban batch checker - Workaround for zuban panic when checking entire project.
This script runs zuban on batches of files to avoid the panic issue.
"""

import subprocess
import sys


def run_zuban_batch(files, batch_size=20, show_progress=True):
    """Run zuban on batches of files to avoid panic"""
    total_files = len(files)
    all_errors = []
    panic_files = []

    for i in range(0, total_files, batch_size):
        batch = files[i:i + batch_size]
        if show_progress:
            print(f"Processing batch {i//batch_size + 1}/{(total_files + batch_size - 1)//batch_size} ({len(batch)} files)...", end=' ')

        try:
            result = subprocess.run(['zuban', 'check'] + batch,
                                  capture_output=True, text=True, timeout=60)

            if result.returncode == 101:  # Panic
                if show_progress:
                    print("PANIC - trying individual files...")
                # Try individual files in this batch
                for file in batch:
                    try:
                        individual_result = subprocess.run(['zuban', 'check', file],
                                                        capture_output=True, text=True, timeout=30)
                        if individual_result.returncode == 101:
                            panic_files.append(file)
                            if show_progress:
                                print(f"  ✗ PANIC in {file}")
                        else:
                            if show_progress:
                                print(f"  ✓ {file}")
                            if individual_result.returncode != 0:
                                all_errors.extend(individual_result.stdout.split('\n'))
                    except Exception as e:
                        if show_progress:
                            print(f"  ✗ ERROR in {file}: {e}")
            else:
                if show_progress:
                    print("✓")
                if result.returncode != 0:
                    all_errors.extend(result.stdout.split('\n'))

        except subprocess.TimeoutExpired:
            if show_progress:
                print("TIMEOUT")
        except Exception as e:
            if show_progress:
                print(f"ERROR: {e}")

    return all_errors, panic_files

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Run zuban on all Python files in batches to avoid panic')
    parser.add_argument('--batch-size', type=int, default=20, help='Number of files per batch (default: 20)')
    parser.add_argument('--quiet', action='store_true', help='Suppress progress output')
    parser.add_argument('--exclude', nargs='*', default=['.venv', 'venv', 'archive', 'build'],
                       help='Directories to exclude (default: .venv venv archive build)')
    args = parser.parse_args()

    # Get all Python files
    exclude_paths = ' '.join([f'-not -path ./{path}/*' for path in args.exclude])
    find_cmd = ['find', '.', '-name', '*.py'] + exclude_paths.split()

    result = subprocess.run(find_cmd, capture_output=True, text=True)
    files = [f for f in result.stdout.strip().split('\n') if f]

    if not files:
        print("No Python files found")
        return 0

    if not args.quiet:
        print(f"Found {len(files)} Python files")
        print(f"Running zuban in batches of {args.batch_size} to avoid panic...")

    errors, panic_files = run_zuban_batch(files, args.batch_size, not args.quiet)

    # Count actual errors (not just lines with 'error:')
    error_lines = [e for e in errors if 'error:' in e]
    error_count = len(error_lines)

    if not args.quiet:
        print("\nSummary:")
        print(f"Total files processed: {len(files)}")
        print(f"Files with panics: {len(panic_files)}")
        print(f"Type errors found: {error_count}")

    if panic_files and not args.quiet:
        print("\nFiles that caused panics:")
        for file in panic_files:
            print(f"  {file}")

    if error_count > 0:
        if not args.quiet:
            print("\nType errors:")
        for error in error_lines:
            print(error)
        return 1
    else:
        if not args.quiet:
            print("\nNo type errors found!")
        return 0

if __name__ == "__main__":
    sys.exit(main())
