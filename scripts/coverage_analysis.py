#!/usr/bin/env python3
"""
Coverage Analysis Script

Identifies modules that need test coverage for 100% coverage goal.
"""

import ast
from pathlib import Path


def find_python_modules(root_dir: Path) -> dict[str, list[str]]:
    """Find all Python modules and their functions/classes."""
    modules = {}

    for py_file in root_dir.rglob("*.py"):
        if py_file.name.startswith("_") or "test" in py_file.name:
            continue

        relative_path = py_file.relative_to(root_dir.parent)
        module_name = str(relative_path.with_suffix("")).replace("/", ".")

        try:
            with open(py_file, encoding="utf-8") as f:
                tree = ast.parse(f.read())

            functions = []
            classes = []

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append(node.name)
                elif isinstance(node, ast.ClassDef):
                    classes.append(node.name)

            modules[module_name] = {
                "file": py_file,
                "functions": functions,
                "classes": classes,
                "lines": len(py_file.read_text().splitlines())
            }
        except Exception as e:
            print(f"Error parsing {py_file}: {e}")

    return modules

def find_existing_tests(tests_dir: Path) -> dict[str, set[str]]:
    """Find existing test coverage by module."""
    test_coverage = {}

    for test_file in tests_dir.rglob("test_*.py"):
        try:
            with open(test_file, encoding="utf-8") as f:
                content = f.read()

            # Extract module being tested from imports and calls
            lines = content.splitlines()
            tested_items = set()

            for line in lines:
                line = line.strip()
                if "import " in line and ("lib" in line or "tools" in line or "server" in line):
                    tested_items.add(line)
                elif "def test_" in line:
                    test_name = line.split("def test_")[1].split("(")[0].strip()
                    tested_items.add(f"test_{test_name}")

            test_coverage[test_file.name] = tested_items
        except Exception as e:
            print(f"Error parsing test file {test_file}: {e}")

    return test_coverage

def analyze_coverage()
    """Analyze current coverage and identify gaps."""
    project_root = Path()

    # Find all modules
    lib_modules = find_python_modules(project_root / "lib")
    server_modules = find_python_modules(project_root / "server")
    tools_modules = find_python_modules(project_root / "tools")
    config_modules = find_python_modules(project_root / "config")
    schemas_modules = find_python_modules(project_root / "schemas")
    utils_modules = find_python_modules(project_root / "utils")

    # Find existing tests
    find_existing_tests(project_root / "tests")

    print("=== Coverage Analysis ===\n")

    all_modules = {
        "lib": lib_modules,
        "server": server_modules,
        "tools": tools_modules,
        "config": config_modules,
        "schemas": schemas_modules,
        "utils": utils_modules,
    }

    total_modules = 0
    total_functions = 0
    total_classes = 0

    for category, modules in all_modules.items():
        print(f"\n{category.upper()} MODULES:")
        print("=" * 50)

        category_modules = 0
        category_functions = 0
        category_classes = 0

        for module_name, module_info in modules.items():
            print(f"\n📦 {module_name}")
            print(f"   📄 File: {module_info['file']}")
            print(f"   📊 Lines: {module_info['lines']}")
            print(f"   🔧 Functions: {len(module_info['functions'])}")
            print(f"   🏗️  Classes: {len(module_info['classes'])}")

            if module_info["functions"]:
                print(f"   Functions: {', '.join(module_info['functions'][:5])}")
                if len(module_info["functions"]) > 5:
                    print(f"               ... and {len(module_info['functions']) - 5} more")

            if module_info["classes"]:
                print(f"   Classes: {', '.join(module_info['classes'][:5])}")
                if len(module_info["classes"]) > 5:
                    print(f"              ... and {len(module_info['classes']) - 5} more")

            category_modules += 1
            category_functions += len(module_info["functions"])
            category_classes += len(module_info["classes"])

        print(f"\n📈 {category.upper()} SUMMARY:")
        print(f"   Modules: {category_modules}")
        print(f"   Functions: {category_functions}")
        print(f"   Classes: {category_classes}")

        total_modules += category_modules
        total_functions += category_functions
        total_classes += category_classes

    print("\n📊 OVERALL PROJECT SUMMARY:")
    print(f"   Total Modules: {total_modules}")
    print(f"   Total Functions: {total_functions}")
    print(f"   Total Classes: {total_classes}")

    print("\n🎯 COVERAGE RECOMMENDATIONS:")
    print("1. Create unit tests for each function")
    print("2. Test class methods and properties")
    print("3. Test edge cases and error conditions")
    print("4. Test imports and exports")
    print("5. Test configuration and settings")
    print("6. Test database operations")
    print("7. Test API endpoints")
    print("8. Test authentication and authorization")

if __name__ == "__main__":
    analyze_coverage()
