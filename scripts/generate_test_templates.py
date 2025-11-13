#!/usr/bin/env python3
"""
Test Template Generator

Automatically generates test templates for uncovered code paths based on coverage analysis.
This script analyzes Python files and generates pytest test templates to achieve 100% coverage.
"""

import ast
import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple


class CodeAnalyzer(ast.NodeVisitor):
    """Analyzes Python code to extract functions, classes, and code paths."""
    
    def __init__(self):
        self.functions: List[Dict] = []
        self.classes: List[Dict] = []
        self.current_class = None
        self.branches: List[Tuple] = []
        
    def visit_FunctionDef(self, node):
        """Extract function definitions."""
        func_info = {
            "name": node.name,
            "line": node.lineno,
            "args": [arg.arg for arg in node.args.args],
            "is_async": isinstance(node, ast.AsyncFunctionDef),
            "decorators": [self._get_decorator_name(d) for d in node.decorator_list],
            "class": self.current_class,
        }
        
        # Check for branches (if/elif/else, try/except)
        self._analyze_branches(node)
        
        if self.current_class:
            func_info["full_name"] = f"{self.current_class}.{node.name}"
        else:
            func_info["full_name"] = node.name
            
        self.functions.append(func_info)
        self.generic_visit(node)
    
    def visit_ClassDef(self, node):
        """Extract class definitions."""
        old_class = self.current_class
        self.current_class = node.name
        
        class_info = {
            "name": node.name,
            "line": node.lineno,
            "bases": [self._get_base_name(b) for b in node.bases],
            "methods": [],
        }
        
        self.generic_visit(node)
        self.classes.append(class_info)
        self.current_class = old_class
    
    def _get_decorator_name(self, node):
        """Get decorator name."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_attr_name(node)}"
        return "unknown"
    
    def _get_attr_name(self, node):
        """Get attribute name."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_attr_name(node.value)}.{node.attr}"
        return "unknown"
    
    def _get_base_name(self, node):
        """Get base class name."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return self._get_attr_name(node)
        return "unknown"
    
    def _analyze_branches(self, node):
        """Analyze branches in function."""
        for child in ast.walk(node):
            if isinstance(child, ast.If):
                self.branches.append(("if", child.lineno))
            elif isinstance(child, ast.Try):
                self.branches.append(("try", child.lineno))
            elif isinstance(child, ast.ExceptHandler):
                self.branches.append(("except", child.lineno))


class TestTemplateGenerator:
    """Generates test templates for Python modules."""
    
    def __init__(self, module_path: str, output_path: str = None):
        self.module_path = Path(module_path)
        self.module_name = self.module_path.stem
        self.output_path = Path(output_path) if output_path else self._get_output_path()
        self.analyzer = CodeAnalyzer()
        
    def _get_output_path(self) -> Path:
        """Get output path for test file."""
        # Convert tools/entity.py -> tests/test_coverage_entity_complete.py
        # Convert infrastructure/factory.py -> tests/test_coverage_factory_complete.py
        
        parts = self.module_path.parts
        if len(parts) > 1:
            # Remove 'tools', 'infrastructure', 'services' prefix
            test_name = parts[-1].replace('.py', '')
            return Path("tests") / f"test_coverage_{test_name}_complete.py"
        return Path("tests") / f"test_coverage_{self.module_name}_complete.py"
    
    def analyze(self):
        """Analyze the module and extract code structure."""
        with open(self.module_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        try:
            tree = ast.parse(content, filename=str(self.module_path))
            self.analyzer.visit(tree)
        except SyntaxError as e:
            print(f"Error parsing {self.module_path}: {e}")
            return
    
    def generate_test_file(self):
        """Generate test file with templates."""
        self.analyze()
        
        test_content = self._generate_header()
        test_content += self._generate_imports()
        test_content += self._generate_test_classes()
        
        # Write to file
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_path, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        print(f"✅ Generated test template: {self.output_path}")
        print(f"   Found {len(self.analyzer.functions)} functions")
        print(f"   Found {len(self.analyzer.classes)} classes")
        print(f"   Found {len(self.analyzer.branches)} branches")
    
    def _generate_header(self) -> str:
        """Generate file header."""
        module_rel_path = str(self.module_path).replace('\\', '/')
        
        return f'''"""
Comprehensive tests for {module_rel_path} to achieve 100% coverage.

This file was auto-generated by generate_test_templates.py.
Add test implementations for each test method to achieve 100% coverage.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

'''
    
    def _generate_imports(self) -> str:
        """Generate imports based on module path."""
        # Convert path to import
        parts = self.module_path.parts
        if self.module_path.suffix == '.py':
            parts = parts[:-1] + (self.module_path.stem,)
        
        import_path = '.'.join(parts)
        
        return f'''# ============================================================================
# {self.module_path} - 100% Coverage
# ============================================================================

'''
    
    def _generate_test_classes(self) -> str:
        """Generate test classes for each class in the module."""
        content = ""
        
        # Group functions by class
        class_methods: Dict[str, List[Dict]] = {}
        standalone_functions: List[Dict] = []
        
        for func in self.analyzer.functions:
            if func["class"]:
                if func["class"] not in class_methods:
                    class_methods[func["class"]] = []
                class_methods[func["class"]].append(func)
            else:
                standalone_functions.append(func)
        
        # Generate test classes for each class
        for class_name, methods in class_methods.items():
            content += self._generate_test_class(class_name, methods)
            content += "\n\n"
        
        # Generate tests for standalone functions
        if standalone_functions:
            content += self._generate_standalone_tests(standalone_functions)
        
        return content
    
    def _generate_test_class(self, class_name: str, methods: List[Dict]) -> str:
        """Generate test class for a Python class."""
        test_class_name = f"Test{class_name}Complete"
        
        content = f'''class {test_class_name}:
    """Complete coverage tests for {self.module_path}::{class_name}."""\n\n'''
        
        for method in methods:
            content += self._generate_test_method(method, class_name)
            content += "\n\n"
        
        return content
    
    def _generate_test_method(self, method: Dict, class_name: str = None) -> str:
        """Generate test method template."""
        method_name = method["name"]
        test_name = f"test_{method_name}"
        is_async = method["is_async"]
        
        # Check for async decorator
        has_async_marker = "@pytest.mark.asyncio" if is_async else ""
        has_mock_marker = "@pytest.mark.mock_only"
        
        decorators = []
        if has_async_marker:
            decorators.append(has_async_marker)
        if has_mock_marker:
            decorators.append(has_mock_marker)
        
        decorator_str = "\n    ".join(decorators) + "\n    " if decorators else ""
        
        # Generate docstring
        docstring = f'"""Test {method_name} method."""'
        
        # Generate function signature
        if is_async:
            func_sig = f"    async def {test_name}(self):"
        else:
            func_sig = f"    def {test_name}(self):"
        
        # Generate test body template
        body = f'''        # TODO: Implement test for {method_name}
        # Args: {', '.join(method['args']) if method['args'] else 'None'}
        # Test cases to cover:
        # - Success path
        # - Error handling
        # - Edge cases
        # - Boundary conditions
        
        from {self._get_import_path()} import {class_name if class_name else self.module_name}
        
        # Example test structure:
        # instance = {class_name if class_name else self.module_name}()
        # result = {'await ' if is_async else ''}instance.{method_name}(...)
        # assert result is not None
        
        pytest.skip("Test not yet implemented")'''
        
        return f"    {decorator_str}{func_sig}\n        {docstring}\n{body}"
    
    def _generate_standalone_tests(self, functions: List[Dict]) -> str:
        """Generate tests for standalone functions."""
        content = f'''class TestStandaloneFunctions:
    """Tests for standalone functions in {self.module_path}."""\n\n'''
        
        for func in functions:
            content += self._generate_test_method(func)
            content += "\n\n"
        
        return content
    
    def _get_import_path(self) -> str:
        """Get import path for the module."""
        parts = list(self.module_path.parts)
        if parts[-1].endswith('.py'):
            parts[-1] = parts[-1][:-3]
        
        return '.'.join(parts)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python generate_test_templates.py <module_path> [output_path]")
        print("Example: python generate_test_templates.py tools/entity.py")
        sys.exit(1)
    
    module_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(module_path):
        print(f"Error: File not found: {module_path}")
        sys.exit(1)
    
    generator = TestTemplateGenerator(module_path, output_path)
    generator.generate_test_file()


if __name__ == "__main__":
    main()
