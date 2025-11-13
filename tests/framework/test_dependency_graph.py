"""
Test script to visualize and validate dependency graph.

Run with: pytest tests/framework/test_dependency_graph.py -v -s
"""

import pytest
from tests.framework.dependencies import TestDependencies


def test_dependency_graph_valid():
    """Validate that the dependency graph has no errors."""
    errors = TestDependencies.validate_dependencies()
    
    if errors:
        print("\n❌ DEPENDENCY GRAPH ERRORS:")
        for error in errors:
            print(f"   • {error}")
        pytest.fail(f"Dependency graph has {len(errors)} error(s)")
    else:
        print("\n✅ Dependency graph is valid (no circular dependencies or missing refs)")


def test_show_dependency_graph():
    """Display the complete dependency graph."""
    graph = TestDependencies.get_dependency_graph()
    print("\n" + graph)


def test_show_execution_order():
    """Display the recommended test execution order."""
    try:
        order = TestDependencies.get_execution_order()
        print("\n" + "="*70)
        print("RECOMMENDED TEST EXECUTION ORDER")
        print("="*70)
        for i, test_name in enumerate(order, 1):
            all_deps = TestDependencies.get_all_dependencies()
            test_info = all_deps.get(test_name, {})
            description = test_info.get("description", "No description")
            print(f"{i:3}. {test_name}")
            print(f"     → {description}")
        print("="*70)
    except ValueError as e:
        print(f"\n❌ Cannot determine execution order: {e}")
        pytest.fail(str(e))


def test_show_layer_breakdown():
    """Show tests grouped by layer."""
    print("\n" + "="*70)
    print("TESTS BY LAYER")
    print("="*70)
    
    all_deps = TestDependencies.get_all_dependencies()
    
    layers = {}
    for test_name, test_info in all_deps.items():
        layer = test_info.get("layer", "unknown")
        if layer not in layers:
            layers[layer] = []
        layers[layer].append(test_name)
    
    for layer in ["unit", "integration", "e2e"]:
        if layer in layers:
            tests = layers[layer]
            print(f"\n{layer.upper()} ({len(tests)} tests):")
            for test in sorted(tests):
                deps = TestDependencies.get_dependencies_for_test(test)
                if deps:
                    print(f"  • {test} (depends on {len(deps)} tests)")
                else:
                    print(f"  • {test} (no dependencies)")
    
    print("="*70)


def test_show_statistics():
    """Show dependency graph statistics."""
    all_deps = TestDependencies.get_all_dependencies()
    
    # Count by layer
    layer_counts = {}
    total_deps = 0
    max_deps = 0
    
    for test_info in all_deps.values():
        layer = test_info.get("layer", "unknown")
        layer_counts[layer] = layer_counts.get(layer, 0) + 1
        
        deps = test_info.get("depends_on", [])
        total_deps += len(deps)
        max_deps = max(max_deps, len(deps))
    
    print("\n" + "="*70)
    print("DEPENDENCY GRAPH STATISTICS")
    print("="*70)
    print(f"Total tests defined: {len(all_deps)}")
    print(f"Total dependencies: {total_deps}")
    print(f"Average dependencies per test: {total_deps / len(all_deps):.1f}")
    print(f"Maximum dependencies for a single test: {max_deps}")
    print("\nTests by layer:")
    for layer, count in sorted(layer_counts.items()):
        print(f"  • {layer}: {count}")
    print("="*70)


if __name__ == "__main__":
    # Run all tests when executed directly
    pytest.main([__file__, "-v", "-s"])
