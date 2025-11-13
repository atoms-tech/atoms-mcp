#!/usr/bin/env python3
"""
Apply dependency markers to all test files automatically.

This script analyzes test files and applies appropriate @pytest.mark.dependency
markers based on test naming patterns and file structure.

Usage:
    python scripts/apply_dependency_markers.py --dry-run  # Preview changes
    python scripts/apply_dependency_markers.py             # Apply changes
"""

import ast
import argparse
import re
from pathlib import Path
from typing import List, Dict, Tuple


class DependencyMarkerApplier:
    """Applies dependency markers to test files."""
    
    # Dependency rules based on test naming patterns
    DEPENDENCY_RULES = {
        # CRUD operations depend on each other
        "test_.*_create": {"name": "self", "depends": []},
        "test_.*_read": {"name": "self", "depends": [".*_create"]},
        "test_.*_update": {"name": "self", "depends": [".*_create", ".*_read"]},
        "test_.*_delete": {"name": "self", "depends": [".*_create", ".*_read"]},
        "test_.*_list": {"name": "self", "depends": [".*_create"]},
        "test_.*_search": {"name": "self", "depends": [".*_create"]},
        
        # Initialization tests are foundations
        "test_.*_initializ": {"name": "self", "depends": []},
        "test_.*_setup": {"name": "self", "depends": []},
        "test_.*_connection": {"name": "self", "depends": []},
        
        # Integration tests depend on unit tests
        "TestAPI.*": {"depends": ["unit_tests_pass"]},
        "test_api_.*": {"depends": ["unit_tests_pass"]},
        
        # E2E tests depend on integration
        "test_complete_.*": {"depends": ["integration_tests_pass"]},
        "test_end_to_end.*": {"depends": ["integration_tests_pass"]},
    }
    
    # Test class hierarchies
    CLASS_DEPENDENCIES = {
        "TestEntityRead": ["TestEntityCreate"],
        "TestEntityUpdate": ["TestEntityCreate", "TestEntityRead"],
        "TestEntityDelete": ["TestEntityCreate", "TestEntityRead"],
        "TestEntitySearch": ["TestEntityCreate"],
        "TestEntityList": ["TestEntityCreate"],
        
        "TestWorkspaceRead": ["TestWorkspaceCreate"],
        "TestWorkspaceUpdate": ["TestWorkspaceCreate"],
        "TestWorkspaceDelete": ["TestWorkspaceCreate"],
        
        "TestRelationshipRead": ["TestRelationshipCreate"],
        "TestRelationshipUpdate": ["TestRelationshipCreate"],
        "TestRelationshipDelete": ["TestRelationshipCreate"],
        
        "TestQueryExecute": ["TestEntityCreate"],
        "TestQueryFilter": ["TestQueryExecute"],
        
        "TestWorkflowExecute": ["TestWorkflowCreate"],
        "TestWorkflowStatus": ["TestWorkflowCreate", "TestWorkflowExecute"],
    }
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.changes = []
    
    def analyze_test_file(self, file_path: Path) -> Dict:
        """Analyze a test file and determine what markers to apply."""
        with open(file_path, 'r') as f:
            content = f.read()
        
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return {"error": "Failed to parse file"}
        
        analysis = {
            "file": str(file_path),
            "classes": [],
            "functions": [],
            "existing_markers": [],
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_info = self._analyze_class(node)
                analysis["classes"].append(class_info)
            elif isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                func_info = self._analyze_function(node)
                analysis["functions"].append(func_info)
        
        return analysis
    
    def _analyze_class(self, node: ast.ClassDef) -> Dict:
        """Analyze a test class."""
        has_dependency_marker = any(
            isinstance(dec, ast.Call) and 
            getattr(dec.func, 'attr', None) == 'dependency'
            for dec in node.decorator_list
        )
        
        # Determine dependencies based on class name
        dependencies = self.CLASS_DEPENDENCIES.get(node.name, [])
        
        return {
            "name": node.name,
            "line": node.lineno,
            "has_marker": has_dependency_marker,
            "suggested_dependencies": dependencies,
        }
    
    def _analyze_function(self, node: ast.FunctionDef) -> Dict:
        """Analyze a test function."""
        has_dependency_marker = any(
            isinstance(dec, ast.Call) and 
            getattr(dec.func, 'attr', None) == 'dependency'
            for dec in node.decorator_list
        )
        
        # Determine dependencies based on function name
        dependencies = []
        for pattern, rule in self.DEPENDENCY_RULES.items():
            if re.match(pattern, node.name):
                dependencies = rule.get("depends", [])
                break
        
        return {
            "name": node.name,
            "line": node.lineno,
            "has_marker": has_dependency_marker,
            "suggested_dependencies": dependencies,
        }
    
    def apply_markers(self, file_path: Path) -> bool:
        """Apply dependency markers to a file."""
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        analysis = self.analyze_test_file(file_path)
        
        # Track modifications
        modifications = []
        
        # Apply markers to classes
        for class_info in analysis["classes"]:
            if not class_info["has_marker"] and class_info["suggested_dependencies"]:
                line_num = class_info["line"] - 1
                indent = self._get_indent(lines[line_num])
                
                if class_info["suggested_dependencies"]:
                    deps_str = ', '.join(f'"{d}"' for d in class_info["suggested_dependencies"])
                    marker = f'{indent}@pytest.mark.dependency(depends=[{deps_str}])\n'
                else:
                    marker = f'{indent}@pytest.mark.dependency(name="{class_info["name"]}")\n'
                
                modifications.append((line_num, marker))
                self.changes.append({
                    "file": str(file_path),
                    "type": "class",
                    "name": class_info["name"],
                    "marker": marker.strip(),
                })
        
        # Apply modifications
        if modifications and not self.dry_run:
            # Sort in reverse order to maintain line numbers
            modifications.sort(reverse=True, key=lambda x: x[0])
            
            for line_num, marker in modifications:
                lines.insert(line_num, marker)
            
            with open(file_path, 'w') as f:
                f.writelines(lines)
            
            return True
        
        return False
    
    def _get_indent(self, line: str) -> str:
        """Get the indentation of a line."""
        return line[:len(line) - len(line.lstrip())]
    
    def process_all_tests(self, test_dir: Path):
        """Process all test files in a directory."""
        test_files = list(test_dir.rglob("test_*.py"))
        
        print(f"Found {len(test_files)} test files")
        
        for test_file in test_files:
            # Skip special files
            if test_file.name in ["conftest.py", "__init__.py"]:
                continue
            
            print(f"\nProcessing: {test_file.relative_to(test_dir.parent)}")
            
            if self.dry_run:
                analysis = self.analyze_test_file(test_file)
                for class_info in analysis["classes"]:
                    if not class_info["has_marker"] and class_info["suggested_dependencies"]:
                        print(f"  Would add marker to {class_info['name']}: depends={class_info['suggested_dependencies']}")
            else:
                modified = self.apply_markers(test_file)
                if modified:
                    print(f"  ✓ Modified")
                else:
                    print(f"  - No changes needed")
    
    def print_summary(self):
        """Print summary of changes."""
        if not self.changes:
            print("\n✓ No changes needed or made")
            return
        
        print(f"\n{'DRY RUN - ' if self.dry_run else ''}Summary of Changes:")
        print("=" * 70)
        
        by_file = {}
        for change in self.changes:
            file = change["file"]
            if file not in by_file:
                by_file[file] = []
            by_file[file].append(change)
        
        for file, changes in by_file.items():
            print(f"\n{file}:")
            for change in changes:
                print(f"  • {change['type']} {change['name']}")
                print(f"    {change['marker']}")
        
        print(f"\nTotal changes: {len(self.changes)}")


def main():
    parser = argparse.ArgumentParser(
        description="Apply dependency markers to test files"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying files"
    )
    parser.add_argument(
        "--test-dir",
        type=Path,
        default=Path("tests"),
        help="Test directory to process"
    )
    
    args = parser.parse_args()
    
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║        Dependency Marker Application Tool                         ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    
    if args.dry_run:
        print("\n⚠️  DRY RUN MODE - No files will be modified\n")
    
    applier = DependencyMarkerApplier(dry_run=args.dry_run)
    applier.process_all_tests(args.test_dir)
    applier.print_summary()
    
    if args.dry_run:
        print("\n💡 Run without --dry-run to apply changes")


if __name__ == "__main__":
    main()
